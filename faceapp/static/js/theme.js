// Simple light/dark theme toggle, persisted in localStorage
(function () {
  const root = document.documentElement;
  const btn = document.getElementById('themeToggle');
  const icon = btn ? btn.querySelector('i') : null;

  function applyTheme(theme) {
    root.setAttribute('data-bs-theme', theme);
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
    }
  }

  const saved = localStorage.getItem('facex-theme') || 'dark';
  applyTheme(saved);

  if (btn) {
    btn.addEventListener('click', () => {
      const current = root.getAttribute('data-bs-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('facex-theme', next);
    });
  }
})();
