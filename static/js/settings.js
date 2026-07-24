/*
 * settings.js
 * Loads current settings from /api/settings on page load, and pushes any
 * change back to the server immediately (auto-save, no "Save" button
 * needed - simpler UX for a hackathon demo).
 */

(function () {
  const cameraIndex = document.getElementById("cameraIndex");
  const confSlider = document.getElementById("confSlider");
  const confDisplay = document.getElementById("confDisplay");
  const colorFilter = document.getElementById("colorFilter");
  const multiBallToggle = document.getElementById("multiBallToggle");
  const saveImagesToggle = document.getElementById("saveImagesToggle");
  const saveStatus = document.getElementById("saveStatus");
  const settingsThemeToggle = document.getElementById("settingsThemeToggle");

  function pushSettings(partial) {
    fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(partial),
    })
      .then((r) => r.json())
      .then(() => {
        saveStatus.textContent = "Settings saved.";
        setTimeout(() => (saveStatus.textContent = "Settings sync automatically."), 1500);
      })
      .catch(() => {
        saveStatus.textContent = "Could not reach server.";
      });
  }

  // Load current state on page open
  fetch("/api/settings")
    .then((r) => r.json())
    .then((state) => {
      cameraIndex.value = state.camera_index ?? 0;
      confSlider.value = state.confidence ?? 0.35;
      confDisplay.textContent = confSlider.value;
      colorFilter.value = state.color_filter || "";
      multiBallToggle.checked = !!state.multi_ball;
      saveImagesToggle.checked = state.save_images !== false;
    })
    .catch(() => {});

  cameraIndex.addEventListener("change", () => pushSettings({ camera_index: cameraIndex.value }));

  confSlider.addEventListener("input", () => {
    confDisplay.textContent = confSlider.value;
  });
  confSlider.addEventListener("change", () => pushSettings({ confidence: confSlider.value }));

  colorFilter.addEventListener("change", () => pushSettings({ color_filter: colorFilter.value }));

  multiBallToggle.addEventListener("change", () => pushSettings({ multi_ball: multiBallToggle.checked }));

  saveImagesToggle.addEventListener("change", () => pushSettings({ save_images: saveImagesToggle.checked }));

  // The settings page has its own theme button too (mirrors the sidebar one)
  settingsThemeToggle.addEventListener("click", () => {
    document.getElementById("themeToggle")?.click();
  });
})();
