/*
 * detection.js
 * Controls the Live Detection page:
 *   - Start/Stop the MJPEG video stream (<img src="/video_feed">)
 *   - Poll /api/status every ~500ms to update confidence, FPS, bbox, center
 *   - Draw a rolling live FPS line chart with Chart.js
 *   - Handle "Use Webcam" / "Upload Video" source switching
 */

(function () {
  const videoStream = document.getElementById("videoStream");
  const videoPlaceholder = document.getElementById("videoPlaceholder");
  const startBtn = document.getElementById("startBtn");
  const stopBtn = document.getElementById("stopBtn");
  const useWebcamBtn = document.getElementById("useWebcamBtn");
  const videoUpload = document.getElementById("videoUpload");

  const statusPill = document.getElementById("statusPill");
  const confVal = document.getElementById("confVal");
  const fpsVal = document.getElementById("fpsVal");
  const bboxVal = document.getElementById("bboxVal");
  const centerVal = document.getElementById("centerVal");
  const countVal = document.getElementById("countVal");

  let pollTimer = null;
  let isRunning = false;

  // ---------------- Live FPS chart ----------------
  const MAX_POINTS = 30;
  const fpsData = { labels: [], values: [] };
  const ctx = document.getElementById("fpsChart");
  const fpsChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: fpsData.labels,
      datasets: [{
        label: "FPS",
        data: fpsData.values,
        borderColor: "#22e6a0",
        backgroundColor: "rgba(34,230,160,0.15)",
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: { beginAtZero: true, grid: { color: "rgba(128,128,128,0.15)" }, ticks: { color: "#8a93a8" } },
      },
    },
  });

  function pushFps(value) {
    fpsData.labels.push("");
    fpsData.values.push(value);
    if (fpsData.values.length > MAX_POINTS) {
      fpsData.labels.shift();
      fpsData.values.shift();
    }
    fpsChart.update("none");
  }

  // ---------------- Status polling ----------------
  function pollStatus() {
    fetch("/api/status")
      .then((r) => r.json())
      .then((data) => {
        fpsVal.textContent = (data.fps || 0).toFixed(1);
        pushFps(data.fps || 0);

        if (data.detected) {
          statusPill.textContent = "Ball Detected";
          statusPill.className = "pill pill-success";
          confVal.textContent = (data.confidence * 100).toFixed(1) + "%";
          bboxVal.textContent = data.bbox ? data.bbox.join(", ") : "--";
          centerVal.textContent = data.center ? `(${data.center[0]}, ${data.center[1]})` : "--";
          countVal.textContent = data.ball_count || 1;
        } else {
          statusPill.textContent = "Not Detected";
          statusPill.className = "pill pill-danger";
          confVal.textContent = "--";
          bboxVal.textContent = "--";
          centerVal.textContent = "--";
          countVal.textContent = "0";
        }
      })
      .catch(() => {});
  }

  // ---------------- Start / Stop ----------------
  function startDetection() {
    isRunning = true;
    videoPlaceholder.style.display = "none";
    videoStream.style.display = "block";
    // cache-bust so the browser opens a fresh MJPEG connection
    videoStream.src = "/video_feed?t=" + Date.now();

    startBtn.disabled = true;
    stopBtn.disabled = false;

    pollTimer = setInterval(pollStatus, 500);
  }

  function stopDetection() {
    isRunning = false;
    videoStream.src = "";
    videoStream.style.display = "none";
    videoPlaceholder.style.display = "block";

    startBtn.disabled = false;
    stopBtn.disabled = true;

    statusPill.textContent = "Idle";
    statusPill.className = "pill pill-neutral";
    confVal.textContent = "--";
    fpsVal.textContent = "--";
    bboxVal.textContent = "--";
    centerVal.textContent = "--";
    countVal.textContent = "--";

    if (pollTimer) clearInterval(pollTimer);
  }

  startBtn.addEventListener("click", startDetection);
  stopBtn.addEventListener("click", stopDetection);

  // ---------------- Source switching ----------------
  useWebcamBtn.addEventListener("click", () => {
    fetch("/api/use_webcam", { method: "POST" }).then(() => {
      if (isRunning) startDetection(); // restart stream against new source
    });
  });

  videoUpload.addEventListener("change", () => {
    const file = videoUpload.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("video", file);
    fetch("/api/upload_video", { method: "POST", body: formData }).then(() => {
      if (isRunning) startDetection();
    });
  });
})();
