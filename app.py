"""
app.py
-------
Main Flask application for the Ball Detection System.

This file wires everything together:
    - Serves the web pages (home, live detection, history, gallery,
      analytics, settings) via Jinja2 templates.
    - Opens the webcam (or an uploaded video file) with OpenCV and streams
      annotated frames to the browser as an MJPEG stream (this is the
      simplest, most beginner-friendly way to show a "live" video feed
      from Flask - no WebRTC or extra servers needed).
    - Exposes small JSON APIs the front-end JavaScript polls for live
      stats (confidence, FPS, bounding box, etc.), settings, history,
      gallery, and analytics data.
    - Saves detection snapshots to SQLite + captured_frames/ so they can
      be browsed later in History / Gallery / exported as CSV.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import csv
import io
import time
from datetime import datetime

import cv2
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

import database as db
from detector import BallDetector

# ----------------------------------------------------------------------
# App setup
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURED_DIR = os.path.join(BASE_DIR, "captured_frames")
os.makedirs(CAPTURED_DIR, exist_ok=True)

app = Flask(__name__)

db.init_db()
detector = BallDetector(conf_threshold=0.35)

# `state` holds everything that can change at runtime via the Settings page.
# Kept as a simple dict for beginner-friendliness (no extra classes needed).
state = {
    "camera_index": 0,
    "video_source": None,     # path to an uploaded video, or None = use webcam
    "save_images": True,
    "confidence": 0.35,
    "color_filter": None,
    "multi_ball": False,
    "last_detection": {"detected": False, "fps": 0},
}

_capture = None  # the shared cv2.VideoCapture object


def get_capture():
    """(Re)open the video capture device/file if needed."""
    global _capture
    if _capture is None or not _capture.isOpened():
        source = state["video_source"] if state["video_source"] else state["camera_index"]
        _capture = cv2.VideoCapture(source)
    return _capture


def release_capture():
    global _capture
    if _capture is not None:
        _capture.release()
        _capture = None


# ----------------------------------------------------------------------
# Video streaming generator
# ----------------------------------------------------------------------
def gen_frames():
    """
    Continuously read frames from the camera/video, run detection, encode
    each annotated frame as JPEG, and yield it in the multipart format the
    browser expects for a live MJPEG stream (<img src="/video_feed">).
    """
    last_saved_at = 0.0
    min_seconds_between_saves = 1.0  # avoid flooding the DB / disk every frame

    while True:
        capture = get_capture()
        success, frame = capture.read()

        if not success:
            if state["video_source"]:
                # looped video file reached the end - restart it
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            # webcam failed to produce a frame - stop the stream
            break

        detections, annotated, fps = detector.detect(frame)

        if detections:
            best = detections[0]
            state["last_detection"] = {
                "detected": True,
                "confidence": round(best["confidence"], 3),
                "bbox": best["bbox"],
                "center": best["center"],
                "width": best["width"],
                "height": best["height"],
                "fps": round(fps, 1),
                "ball_count": len(detections),
            }

            now = time.time()
            if state["save_images"] and (now - last_saved_at) > min_seconds_between_saves:
                last_saved_at = now
                _save_snapshot(best, annotated, fps)
        else:
            state["last_detection"] = {"detected": False, "fps": round(fps, 1)}

        ok, buffer = cv2.imencode(".jpg", annotated)
        if not ok:
            continue
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


def _save_snapshot(detection, annotated_frame, fps):
    """Write a JPEG thumbnail to disk and log the detection to SQLite."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "ball_{}.jpg".format(datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    filepath = os.path.join(CAPTURED_DIR, filename)
    cv2.imwrite(filepath, annotated_frame)

    x1, y1, x2, y2 = detection["bbox"]
    db.save_detection({
        "timestamp": timestamp,
        "confidence": detection["confidence"],
        "center_x": detection["center"][0],
        "center_y": detection["center"][1],
        "bbox_x1": x1, "bbox_y1": y1, "bbox_x2": x2, "bbox_y2": y2,
        "bbox_width": detection["width"], "bbox_height": detection["height"],
        "fps": round(fps, 1),
        "image_path": filename,
    })


# ----------------------------------------------------------------------
# Page routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/detect")
def detect_page():
    return render_template("detection.html", state=state)


@app.route("/history")
def history_page():
    return render_template("history.html")


@app.route("/gallery")
def gallery_page():
    return render_template("gallery.html")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html", state=state)


# ----------------------------------------------------------------------
# Streaming + live status
# ----------------------------------------------------------------------
@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def api_status():
    return jsonify(state["last_detection"])


# ----------------------------------------------------------------------
# Settings API
# ----------------------------------------------------------------------
@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        data = request.get_json(force=True) or {}

        if "camera_index" in data:
            state["camera_index"] = int(data["camera_index"])
            state["video_source"] = None
            release_capture()

        if "confidence" in data:
            state["confidence"] = float(data["confidence"])
            detector.set_confidence(state["confidence"])

        if "save_images" in data:
            state["save_images"] = bool(data["save_images"])

        if "color_filter" in data:
            state["color_filter"] = data["color_filter"] or None
            detector.set_color_filter(state["color_filter"])

        if "multi_ball" in data:
            state["multi_ball"] = bool(data["multi_ball"])
            detector.set_multi_ball(state["multi_ball"])

        if "theme" in data:
            db.set_setting("theme", data["theme"])

        return jsonify({"status": "ok", "state": _public_state()})

    return jsonify(_public_state())


def _public_state():
    """A version of `state` safe to send to the client (no internal objects)."""
    return {
        "camera_index": state["camera_index"],
        "using_uploaded_video": bool(state["video_source"]),
        "save_images": state["save_images"],
        "confidence": state["confidence"],
        "color_filter": state["color_filter"],
        "multi_ball": state["multi_ball"],
        "theme": db.get_setting("theme", "dark"),
    }


@app.route("/api/upload_video", methods=["POST"])
def upload_video():
    """Switch the detection source to an uploaded video file (bonus feature)."""
    if "video" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    video_file = request.files["video"]
    safe_name = "uploaded_{}_{}".format(int(time.time()), video_file.filename)
    save_path = os.path.join(CAPTURED_DIR, safe_name)
    video_file.save(save_path)

    state["video_source"] = save_path
    release_capture()
    return jsonify({"status": "ok"})


@app.route("/api/use_webcam", methods=["POST"])
def use_webcam():
    """Switch back from an uploaded video to the live webcam."""
    state["video_source"] = None
    release_capture()
    return jsonify({"status": "ok"})


# ----------------------------------------------------------------------
# History API
# ----------------------------------------------------------------------
@app.route("/api/history")
def api_history():
    search = request.args.get("search", "").strip() or None
    return jsonify(db.get_history(search=search))


@app.route("/api/history/clear", methods=["POST"])
def api_history_clear():
    db.clear_history()
    return jsonify({"status": "ok"})


@app.route("/api/export_csv")
def export_csv():
    rows = db.get_history(limit=1_000_000)
    output = io.StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row.values())
    else:
        writer.writerow(["No detections recorded yet"])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=detection_history.csv"},
    )


# ----------------------------------------------------------------------
# Gallery API + serving saved images
# ----------------------------------------------------------------------
@app.route("/api/gallery")
def api_gallery():
    return jsonify(db.get_gallery())


@app.route("/captured_frames/<path:filename>")
def captured_frames(filename):
    return send_from_directory(CAPTURED_DIR, filename)


# ----------------------------------------------------------------------
# Analytics API
# ----------------------------------------------------------------------
@app.route("/api/analytics")
def api_analytics():
    return jsonify(db.get_analytics())


if __name__ == "__main__":
    # threaded=True lets the MJPEG stream and the JSON polling requests
    # be served at the same time.
    # Debug reloader is disabled here because it can cause unstable restarts
    # on this Windows/Python setup.
    app.run(debug=False, use_reloader=False, threaded=True, host="0.0.0.0", port=5000)
