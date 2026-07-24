/*
 * history.js
 * Loads detection history from /api/history and renders it as a table.
 * Supports live text search (filtered server-side on the timestamp) and
 * a "clear history" action.
 */

(function () {
  const historyBody = document.getElementById("historyBody");
  const emptyState = document.getElementById("emptyState");
  const resultCount = document.getElementById("resultCount");
  const searchInput = document.getElementById("searchInput");
  const clearBtn = document.getElementById("clearHistoryBtn");

  let debounceTimer = null;

  function renderRows(rows) {
    historyBody.innerHTML = "";
    resultCount.textContent = `${rows.length} record${rows.length === 1 ? "" : "s"}`;

    if (rows.length === 0) {
      emptyState.style.display = "block";
      return;
    }
    emptyState.style.display = "none";

    rows.forEach((row) => {
      const tr = document.createElement("tr");

      const thumb = row.image_path
        ? `<img src="/captured_frames/${row.image_path}" style="width:56px;height:42px;object-fit:cover;border-radius:8px;">`
        : `<span class="text-body-secondary">--</span>`;

      tr.innerHTML = `
        <td>${thumb}</td>
        <td>${row.timestamp}</td>
        <td><span class="pill pill-success">${(row.confidence * 100).toFixed(1)}%</span></td>
        <td>(${row.center_x}, ${row.center_y})</td>
        <td>${row.bbox_x1}, ${row.bbox_y1}, ${row.bbox_x2}, ${row.bbox_y2}</td>
        <td>${row.fps != null ? row.fps.toFixed(1) : "--"}</td>
      `;
      historyBody.appendChild(tr);
    });
  }

  function loadHistory(search) {
    const url = search ? `/api/history?search=${encodeURIComponent(search)}` : "/api/history";
    fetch(url)
      .then((r) => r.json())
      .then(renderRows)
      .catch(() => renderRows([]));
  }

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => loadHistory(searchInput.value.trim()), 300);
  });

  clearBtn.addEventListener("click", () => {
    if (!confirm("This will permanently delete all detection history. Continue?")) return;
    fetch("/api/history/clear", { method: "POST" }).then(() => loadHistory());
  });

  loadHistory();
})();
