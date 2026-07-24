/*
 * analytics.js
 * Fetches aggregate stats from /api/analytics and renders:
 *   - 4 headline stat cards (total, avg confidence, max confidence, avg FPS)
 *   - A bar chart of detections per day
 *   - A donut chart comparing average vs max confidence
 */

(function () {
  fetch("/api/analytics")
    .then((r) => r.json())
    .then((data) => {
      document.getElementById("statTotal").textContent = data.total;
      document.getElementById("statAvgConf").textContent = (data.avg_confidence * 100).toFixed(1) + "%";
      document.getElementById("statMaxConf").textContent = (data.max_confidence * 100).toFixed(1) + "%";
      document.getElementById("statAvgFps").textContent = data.avg_fps;

      renderPerDayChart(data.per_day);
      renderConfidenceChart(data.avg_confidence, data.max_confidence);
    })
    .catch(() => {});

  function renderPerDayChart(perDay) {
    const ctx = document.getElementById("perDayChart");
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: perDay.map((d) => d.day),
        datasets: [{
          label: "Detections",
          data: perDay.map((d) => d.c),
          backgroundColor: "rgba(34,230,160,0.55)",
          borderColor: "#22e6a0",
          borderWidth: 1,
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#8a93a8" } },
          y: { beginAtZero: true, grid: { color: "rgba(128,128,128,0.15)" }, ticks: { color: "#8a93a8" } },
        },
      },
    });
  }

  function renderConfidenceChart(avgConf, maxConf) {
    const ctx = document.getElementById("confidenceChart");
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Average Confidence", "Headroom to Max"],
        datasets: [{
          data: [avgConf, Math.max(maxConf - avgConf, 0)],
          backgroundColor: ["#4f8bff", "rgba(128,128,128,0.2)"],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { color: "#8a93a8", boxWidth: 12 } } },
        cutout: "68%",
      },
    });
  }
})();
