# FaceX — Real-Time Face Distance & Angle Estimation

A beginner-friendly, single-webcam computer vision project built as a demo.
It estimates how far a face is from the camera (depth) and how far off-center it
is (horizontal angle), using MediaPipe Face Detection and simple pinhole-camera
geometry — no depth sensor, no cloud, no heavy frameworks.

## Tech stack
Python · OpenCV · MediaPipe · NumPy · Flask · SQLite · HTML/CSS/JS (Bootstrap 5 + Chart.js)

## 1. Setup

```bash
cd faceapp
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser. The webcam is only opened once you
click "Start" on the Live Detection or Calibration page (grant camera permission
if your OS prompts you).

## 3. Calibrate (do this first!)

1. Go to the **Calibration** page.
2. Click **Start Camera**.
3. Stand exactly **1 meter** from the laptop, facing the camera.
4. Click **Capture & Calibrate**. This computes your webcam's focal length
   (`f = w_px * 1m / 0.15m`) and saves it to `config.json`, so it's reused on
   every future run.

Without calibration, the app uses a rough default focal length (600px) and
shows a warning banner on the Live Detection page.

## 4. Use the app

- **Live Detection** — real-time bounding box, distance, angle, face width,
  confidence, FPS, and Left/Center/Right position.
- **History** — every detection is logged to SQLite (`face_data.db`) with a
  face thumbnail, viewable as a table.
- **Gallery** — visual grid of all captured face thumbnails with metadata.
- **Analytics** — total detections, average/closest/farthest distance, and
  Chart.js line charts of distance & angle over time.

## Project structure

```
faceapp/
├── app.py                # Flask routes
├── camera_manager.py     # Webcam capture + MediaPipe detection thread
├── database.py           # SQLite helpers
├── config.json           # Saved focal length (created after calibration)
├── face_data.db           # SQLite DB (created automatically)
├── requirements.txt
├── templates/            # Jinja2 HTML pages
└── static/
    ├── css/style.css
    ├── js/*.js
    └── thumbnails/        # Saved face crops
```

## Formulas

**Distance (depth):**
`Z = (f × W) / w_px`  where `W = 0.15 m` (average face width), `f` = calibrated
focal length, `w_px` = detected face width in pixels.

**Horizontal angle:**
`θ = arctan((x - cx) / f)`  where `x` = face center x-coordinate, `cx` = frame
center x-coordinate, converted to degrees.

## Notes for the demo

  CDN assets (Bootstrap/Chart.js) are cached once.
  single shared background thread (`camera_manager.py`).
