"""
app.py
------
Flask application entry point. Defines all page routes, the MJPEG video
stream, and the small JSON API used by the frontend JavaScript.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import time
from flask import Flask, render_template, Response, jsonify, request

import database
from camera_manager import camera_manager

app = Flask(__name__)

# Team information removed (frontend no longer shows team cards)


# ---------------------------------------------------------------------- #
# Page routes
# ---------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/detection")
def detection():
    return render_template("detection.html")


@app.route("/history")
def history():
    rows = database.fetch_history(limit=200)
    return render_template("history.html", rows=rows)


@app.route("/gallery")
def gallery():
    rows = database.fetch_gallery(limit=300)
    return render_template("gallery.html", rows=rows)


@app.route("/analytics")
def analytics():
    stats = database.compute_stats()
    return render_template("analytics.html", stats=stats)


@app.route("/calibration")
def calibration():
    return render_template("calibration.html")


# ---------------------------------------------------------------------- #
# Camera control API
# ---------------------------------------------------------------------- #
@app.route("/api/start_camera", methods=["POST"])
def api_start_camera():
    ok = camera_manager.start()
    if not ok:
        return jsonify({"success": False, "message": "Could not open webcam."}), 500
    return jsonify({"success": True})


@app.route("/api/stop_camera", methods=["POST"])
def api_stop_camera():
    camera_manager.stop()
    return jsonify({"success": True})


def gen_frames():
    # Make sure the camera is running before we start streaming
    if not camera_manager.is_running():
        camera_manager.start()

    while True:
        frame = camera_manager.get_jpeg_frame()
        if frame is not None:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.03)


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/stats")
def api_stats():
    return jsonify(camera_manager.get_stats())


@app.route("/api/calibrate", methods=["POST"])
def api_calibrate():
    result = camera_manager.calibrate(known_distance_m=1.0)
    return jsonify(result)


# ---------------------------------------------------------------------- #
# Data APIs for history / gallery / analytics pages
# ---------------------------------------------------------------------- #
@app.route("/api/analytics_data")
def api_analytics_data():
    return jsonify(database.fetch_chart_data(limit=50))


@app.route("/api/clear_history", methods=["POST"])
def api_clear_history():
    database.clear_history()
    return jsonify({"success": True})


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, threaded=True, host="127.0.0.1", port=5000)
