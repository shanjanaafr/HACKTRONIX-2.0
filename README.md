# 🏐 BallVision - AI Ball Detection System

A real-time, webcam-based ball detection web application built for a
hackathon. It uses **YOLOv8** for AI object detection, **OpenCV** for
video handling and colour-based filtering, **Flask** for the web server,
and **SQLite** for logging every detection - all wrapped in a modern
"AI monitoring dashboard" style UI.

---

## 📌 Problem Statement

Using a single RGB webcam, detect and localize a ball in real time while
maximizing **F1 score** (accuracy) and **FPS** (speed), working reliably
across different lighting conditions, backgrounds, ball sizes, and
movement speeds.

## ✨ Features

| Page | What it does |
|---|---|
| **Home** | Landing page with project overview, tech stack, and team info |
| **Live Detection** | Opens the webcam (or an uploaded video), draws a live bounding box around any detected ball, and shows confidence, FPS, bbox coordinates, and center point in real time |
| **History** | Every detection is logged to SQLite (timestamp, confidence, coordinates, thumbnail) and shown in a searchable table |
| **Gallery** | Visual grid of every captured detection frame with metadata |
| **Analytics** | Total detections, average/max confidence, detections per day, average FPS - visualized with Chart.js |
| **Settings** | Webcam selection, confidence threshold, colour filter, multi-ball toggle, image-saving toggle, dark/light theme |

### ⭐ Bonus features included
- **Live FPS graph** on the detection page (Chart.js line chart)
- **CSV export** of the full detection history
- **Multi-ball detection** toggle (detect more than one ball at once)
- **Colour-based filtering** (restrict detection to orange / green / yellow / red balls)
- **Webcam ↔ uploaded video** toggle

---

## 🧠 How Detection Works

1. OpenCV grabs a frame from the webcam (or a video file).
2. The frame is passed to a pretrained **YOLOv8-nano** model
   (`yolov8n.pt`, from the `ultralytics` package). YOLOv8 was pretrained
   on the COCO dataset, which already includes a **"sports ball"** class
   (class id `32`) - so no custom training is required to get a working
   detector immediately.
3. Detections are filtered by the class id, the confidence threshold set
   in **Settings**, and (optionally) an HSV colour mask for
   colour-based filtering.
4. The best (or all, in multi-ball mode) detection(s) are drawn onto the
   frame with a bounding box, label, and center-point crosshair.
5. The annotated frame is JPEG-encoded and streamed to the browser as an
   MJPEG stream (`/video_feed`) - the simplest way to show "live video"
   from Flask without extra dependencies like WebRTC.
6. In parallel, a small JSON API (`/api/status`) reports the latest
   confidence, FPS, bbox, and center coordinates, which the front-end
   polls twice a second to update the dashboard numbers.
7. About once a second (while detecting), a snapshot is saved to
   `captured_frames/` and logged into `database.db` (SQLite) - this
   feeds the History, Gallery, and Analytics pages.

---

## 🗂️ Project Structure

```
BallDetectionSystem/
│── app.py                 # Flask app: routes, video streaming, APIs
│── detector.py             # YOLOv8 + OpenCV ball detection logic
│── database.py              # SQLite schema + queries
│── requirements.txt
│── README.md
│── static/
│   ├── css/style.css        # Dashboard design system (glassmorphism, gradients)
│   └── js/
│       ├── main.js          # Theme toggle + mobile nav
│       ├── detection.js     # Live stream control + status polling + FPS chart
│       ├── history.js       # History table + search
│       ├── gallery.js       # Gallery grid
│       ├── analytics.js     # Chart.js dashboards
│       └── settings.js      # Settings load/save
│── templates/
│   ├── base.html            # Sidebar layout shared by every page
│   ├── index.html           # Home / landing page
│   ├── detection.html       # Live detection page
│   ├── history.html         # Detection history page
│   ├── gallery.html         # Gallery page
│   ├── analytics.html       # Analytics dashboard
│   └── settings.html        # Settings page
│── captured_frames/         # Saved detection thumbnails (created at runtime)
└── database.db               # SQLite database (created automatically on first run)
```

---

## 🚀 Installation Guide

### 1. Prerequisites
- Python 3.9 - 3.11 (recommended)
- A webcam connected to your machine
- pip (comes with Python)

### 2. Set up a virtual environment (recommended)
```bash
cd BallDetectionSystem
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```
> The first time you run detection, `ultralytics` will automatically
> download the `yolov8n.pt` model weights (~6 MB) - make sure you have
> an internet connection for that first run.

### 4. Run the app
```bash
python app.py
```

### 5. Open the dashboard
Go to **http://127.0.0.1:5000** in your browser, then click
**Start Detection** on the Home page or the Live Detection page.

---

## 🖥️ Usage Tips for the Demo

- Hold up any round ball (basketball, football, tennis ball, etc.) in
  front of the webcam - YOLOv8's "sports ball" class recognizes most
  common balls out of the box.
- If FPS looks low, make sure no other heavy application is using your
  CPU/GPU, and confirm you're using `yolov8n.pt` (the fastest YOLOv8
  variant) rather than a larger model.
- Use the **Colour Filter** in Settings if you want to demo detecting
  only, say, an orange ball in a cluttered scene.
- Toggle **Multi-Ball Detection** in Settings to show off detecting more
  than one ball simultaneously.
- Use **Upload Video** on the Live Detection page to demo the system
  without a live webcam (handy if the venue's lighting is inconsistent).

---

## 🔧 Tech Stack

- **Python** - core language
- **OpenCV** - video capture, frame processing, colour filtering, drawing
- **YOLOv8** (`ultralytics`) - pretrained deep-learning object detector
- **Flask** - web server + REST-style JSON APIs + MJPEG video streaming
- **SQLite** - lightweight embedded database for detection history
- **HTML5 / CSS3 / JavaScript** - front-end
- **Bootstrap 5** - layout/grid utilities
- **Chart.js** - analytics and live FPS charts

---

## 📈 Performance Notes

- `yolov8n.pt` (nano) is used specifically because it is small and fast,
  which is what makes 20+ FPS achievable on a typical laptop CPU.
- False positives are reduced by only accepting the COCO **"sports
  ball"** class (id 32) and by requiring a minimum confidence (adjustable
  in Settings).
- The optional colour filter further reduces false positives in scenes
  with multiple round objects, by requiring detected regions to actually
  match the expected ball colour in HSV space.

---

## 🙌 Team Information

**Team BallVision** — AI & DS Hackathon Submission
