/*
 * main.js
 * Shared behaviour across every page: dark/light theme toggle (persisted
 * in localStorage) and the mobile sidebar toggle.
 */

(function () {
  const root = document.documentElement;
  const THEME_KEY = "ballvision_theme";

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    const icon = document.querySelector("#themeToggle i");
    if (icon) {
      icon.className = theme === "dark" ? "bi bi-moon-stars-fill" : "bi bi-sun-fill";
    }
  }

  // Load saved theme (default: dark, matching the "AI monitoring dashboard" look)
  const savedTheme = localStorage.getItem(THEME_KEY) || "dark";
  applyTheme(savedTheme);

  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);

      // best-effort sync to the backend so /api/settings reflects the choice
      fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme: next }),
      }).catch(() => {});
    });
  }

  // Mobile sidebar toggle
  const mobileToggle = document.getElementById("mobileNavToggle");
  const sidebar = document.querySelector(".sidebar");
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("mobile-open");
    });
  }
})();
