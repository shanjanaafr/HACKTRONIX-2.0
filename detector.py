"""
detector.py
------------
Core AI detection module for the Ball Detection System.

Uses a pretrained YOLOv8 model (from the `ultralytics` library) to find balls
in a video frame. In the COCO dataset (which YOLOv8 is pretrained on),
"sports ball" is class id 32 - so we don't need to train our own model to
get started, which makes this beginner-friendly while still being a real
deep-learning object detector.

On top of the YOLO detection, this file adds a few extra beginner-friendly
touches:
    - Multi-ball detection toggle (keep all detected balls vs. just the
      single most confident one).
    - Optional colour-based filtering (e.g. only keep "orange" balls) using
      simple HSV masking with OpenCV - a nice classic-CV bonus feature that
      is easy to explain to judges.
    - FPS measurement for each frame so the UI can show live performance.
"""

import time
import cv2
import numpy as np
from ultralytics import YOLO

# In the COCO dataset used to pretrain YOLOv8, class 32 = "sports ball"
BALL_CLASS_ID = 32

# Simple HSV colour ranges for common ball colours.
# These are intentionally broad - good enough for a hackathon demo, not
# meant to be perfectly tuned for every lighting condition.
COLOR_RANGES = {
    "orange": [(5, 100, 100), (20, 255, 255)],
    "green": [(35, 80, 60), (85, 255, 255)],
    "yellow": [(20, 100, 100), (35, 255, 255)],
    "red": [(0, 120, 70), (10, 255, 255)],
}


class BallDetector:
    """Wraps a YOLOv8 model to detect balls in frames from a webcam or video."""

    def __init__(self, model_path="yolov8n.pt", conf_threshold=0.35):
        # yolov8n.pt = the "nano" YOLOv8 model. It's small and fast, which is
        # important for real-time FPS on a laptop CPU during a demo.
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.color_filter = None   # None, or one of COLOR_RANGES keys
        self.multi_ball = False    # False = only report the best detection

    # ------------------------------------------------------------------
    # Settings setters (called from the Flask settings API)
    # ------------------------------------------------------------------
    def set_confidence(self, conf):
        self.conf_threshold = float(conf)

    def set_color_filter(self, color):
        self.color_filter = color if color in COLOR_RANGES else None

    def set_multi_ball(self, enabled):
        self.multi_ball = bool(enabled)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _color_mask(self, frame, color):
        """Build a binary mask of pixels matching `color` in HSV space."""
        lower, upper = COLOR_RANGES[color]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, np.array(lower), np.array(upper))

    def _passes_color_filter(self, mask, bbox):
        """Check what fraction of the bounding box matches the colour mask."""
        if mask is None:
            return True
        x1, y1, x2, y2 = bbox
        roi = mask[max(y1, 0):max(y2, 0), max(x1, 0):max(x2, 0)]
        if roi.size == 0:
            return False
        match_ratio = float((roi > 0).sum()) / float(roi.size)
        return match_ratio >= 0.15  # at least 15% of the box should match

    # ------------------------------------------------------------------
    # Main detection entry point
    # ------------------------------------------------------------------
    def detect(self, frame):
        """
        Run ball detection on a single BGR frame (as returned by OpenCV).

        Returns:
            detections (list[dict]): one dict per detected ball with keys
                confidence, bbox [x1,y1,x2,y2], center [cx,cy], width, height
            annotated (np.ndarray): a copy of the frame with boxes drawn on it
            fps (float): 1 / inference_time for this single frame
        """
        start_time = time.time()

        # verbose=False keeps YOLO from spamming the console every frame
        results = self.model(frame, verbose=False, conf=self.conf_threshold)[0]

        mask = self._color_mask(frame, self.color_filter) if self.color_filter else None
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id != BALL_CLASS_ID:
                continue  # not a ball - ignore (this is how we "ignore false detections")

            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            bbox = [x1, y1, x2, y2]

            if not self._passes_color_filter(mask, bbox):
                continue

            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            detections.append({
                "confidence": round(confidence, 4),
                "bbox": bbox,
                "center": [cx, cy],
                "width": x2 - x1,
                "height": y2 - y1,
            })

        # If multi-ball mode is off, only keep the single most confident ball
        if not self.multi_ball and len(detections) > 1:
            detections = [max(detections, key=lambda d: d["confidence"])]

        annotated = self._draw_annotations(frame, detections)

        elapsed = time.time() - start_time
        fps = 1.0 / elapsed if elapsed > 0 else 0.0

        return detections, annotated, fps

    def _draw_annotations(self, frame, detections):
        """Draw bounding boxes, labels, and center points on a copy of the frame."""
        annotated = frame.copy()
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            cx, cy = d["center"]

            # Bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 120), 2)

            # Confidence label
            label = "Ball {:.1f}%".format(d["confidence"] * 100)
            label_y = max(y1 - 10, 15)
            cv2.putText(annotated, label, (x1, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 120), 2)

            # Center point crosshair
            cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

        return annotated
