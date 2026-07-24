"""
camera_manager.py
------------------
Runs the webcam + MediaPipe face detection loop in a background thread so
that both the MJPEG video stream and the JSON /api/stats endpoint can share
a single camera device.

Distance formula:   Z = (f * W) / w_px
Angle formula:       theta = arctan((x - cx) / f)   -> converted to degrees
"""

import os
import json
import time
import threading
from datetime import datetime
from math import atan, degrees

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceDetector, FaceDetectorOptions, RunningMode

import database

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
THUMB_DIR = os.path.join(BASE_DIR, "static", "thumbnails")
MODEL_PATH = os.path.join(BASE_DIR, "models", "blaze_face_short_range.tflite")

REAL_FACE_WIDTH_M = 0.15          # average human face width in meters
DEFAULT_FOCAL_LENGTH = 600.0      # fallback focal length (px) before calibration
CENTER_ANGLE_THRESHOLD = 6.0      # degrees within which we call it "Center"
SAVE_INTERVAL_SECONDS = 1.5       # throttle how often we write to SQLite


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"focal_length": DEFAULT_FOCAL_LENGTH, "calibrated": False}


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


class CameraManager:
    def __init__(self):
        self.cap = None
        self.thread = None
        self.running = False
        self.lock = threading.Lock()

        self.latest_frame_jpeg = None
        self.latest_stats = {"face_detected": False}
        self._last_save_time = 0.0

        cfg = load_config()
        self.focal_length = cfg.get("focal_length", DEFAULT_FOCAL_LENGTH)
        self.calibrated = cfg.get("calibrated", False)
        self._frame_timestamp_ms = 0

        options = FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            min_detection_confidence=0.5,
        )
        self.face_detection = FaceDetector.create_from_options(options)

        os.makedirs(THUMB_DIR, exist_ok=True)

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def start(self):
        with self.lock:
            if self.running:
                return True
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
                return False
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            return True

    def stop(self):
        with self.lock:
            self.running = False
        if self.thread is not None:
            self.thread.join(timeout=2)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.latest_frame_jpeg = None
        self.latest_stats = {"face_detected": False}

    def is_running(self):
        return self.running

    # ------------------------------------------------------------------ #
    # calibration
    # ------------------------------------------------------------------ #
    def calibrate(self, known_distance_m=1.0):
        """Use the most recently detected face width to compute focal length."""
        stats = self.latest_stats
        if not stats.get("face_detected"):
            return {"success": False, "message": "No face detected. Stand in front of the camera."}

        w_px = stats.get("face_width_px")
        if not w_px or w_px <= 0:
            return {"success": False, "message": "Invalid face width, try again."}

        f = (w_px * known_distance_m) / REAL_FACE_WIDTH_M
        self.focal_length = f
        self.calibrated = True
        save_config({"focal_length": f, "calibrated": True})
        return {"success": True, "focal_length": round(f, 2)}

    # ------------------------------------------------------------------ #
    # main loop
    # ------------------------------------------------------------------ #
    def _loop(self):
        prev_time = time.time()

        while True:
            with self.lock:
                if not self.running:
                    break
            ok, frame = self.cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)  # mirror for natural webcam feel
            h, w, _ = frame.shape
            cx = w / 2.0

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            self._frame_timestamp_ms += max(1, int((time.time() - prev_time) * 1000))
            results = self.face_detection.detect_for_video(
                mp_image, self._frame_timestamp_ms
            )

            now = time.time()
            fps = 1.0 / (now - prev_time) if now > prev_time else 0.0
            prev_time = now

            stats = {"face_detected": False, "fps": round(fps, 1)}

            if results.detections:
                # pick the largest detection by bounding-box width
                detection = max(
                    results.detections,
                    key=lambda d: d.bounding_box.width,
                )
                box = detection.bounding_box
                x1 = max(int(box.origin_x), 0)
                y1 = max(int(box.origin_y), 0)
                bw = int(box.width)
                bh = int(box.height)
                x2, y2 = min(x1 + bw, w), min(y1 + bh, h)

                confidence = float(detection.categories[0].score) if detection.categories else 0.0
                face_center_x = x1 + bw / 2.0

                distance_m = None
                if bw > 0:
                    distance_m = (self.focal_length * REAL_FACE_WIDTH_M) / bw

                angle_deg = degrees(atan((face_center_x - cx) / self.focal_length))

                if angle_deg < -CENTER_ANGLE_THRESHOLD:
                    position = "Left"
                elif angle_deg > CENTER_ANGLE_THRESHOLD:
                    position = "Right"
                else:
                    position = "Center"

                # --- draw overlays -------------------------------------------------
                color = (0, 210, 120)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.line(frame, (int(cx), 0), (int(cx), h), (255, 255, 255), 1)
                label = f"{distance_m:.2f} m | {angle_deg:.1f} deg | {position}"
                cv2.putText(frame, label, (x1, max(y1 - 12, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(frame, f"conf {confidence:.2f}", (x1, y2 + 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)

                stats.update({
                    "face_detected": True,
                    "distance_m": round(distance_m, 3) if distance_m else None,
                    "angle_deg": round(angle_deg, 2),
                    "face_width_px": bw,
                    "confidence": round(confidence, 3),
                    "position": position,
                    "calibrated": self.calibrated,
                    "focal_length": round(self.focal_length, 1),
                })

                # throttle DB writes + thumbnail saving
                if now - self._last_save_time >= SAVE_INTERVAL_SECONDS:
                    self._last_save_time = now
                    self._save_detection(frame, x1, y1, x2, y2, distance_m, angle_deg,
                                          confidence, bw, position)
            else:
                cv2.putText(frame, "No face detected", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                stats.update({"calibrated": self.calibrated,
                              "focal_length": round(self.focal_length, 1)})

            self.latest_stats = stats

            ok2, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok2:
                self.latest_frame_jpeg = buffer.tobytes()

            time.sleep(0.01)

    def _save_detection(self, frame, x1, y1, x2, y2, distance_m, angle_deg,
                         confidence, face_width, position):
        try:
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                thumb_name = None
            else:
                face_crop = cv2.resize(face_crop, (120, 120))
                thumb_name = f"face_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                cv2.imwrite(os.path.join(THUMB_DIR, thumb_name), face_crop)

            database.insert_detection(
                distance=distance_m,
                angle=angle_deg,
                confidence=confidence,
                face_width=face_width,
                position=position,
                thumbnail_filename=thumb_name,
            )
        except Exception as e:
            print("Failed to save detection:", e)

    # ------------------------------------------------------------------ #
    # accessors used by Flask routes
    # ------------------------------------------------------------------ #
    def get_jpeg_frame(self):
        return self.latest_frame_jpeg

    def get_stats(self):
        return self.latest_stats


# single shared instance used by app.py
camera_manager = CameraManager()
