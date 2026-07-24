/*
 * gallery.js
 * Loads all captured detection thumbnails from /api/gallery and renders
 * them as a responsive image grid with date/confidence/coordinate overlays.
 */

(function () {
  const grid = document.getElementById("galleryGrid");
  const emptyState = document.getElementById("galleryEmpty");

  fetch("/api/gallery")
    .then((r) => r.json())
    .then((items) => {
      if (!items.length) {
        emptyState.style.display = "block";
        return;
      }

      items.forEach((item) => {
        const card = document.createElement("div");
        card.className = "gallery-item";
        card.innerHTML = `
          <img src="/captured_frames/${item.image_path}" alt="Detected ball frame">
          <div class="gallery-meta">
            <strong>${item.timestamp}</strong>
            Confidence: ${(item.confidence * 100).toFixed(1)}% &middot;
            (${item.center_x}, ${item.center_y})
          </div>
        `;
        grid.appendChild(card);
      });
    })
    .catch(() => {
      emptyState.style.display = "block";
    });
})();
