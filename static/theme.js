document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  let theme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  function applyTheme() {
    document.body.classList.toggle('dark-mode', theme === 'dark');
    btn.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
  }
  btn.addEventListener('click', () => {
    theme = theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', theme);
    applyTheme();
  });
  applyTheme();
});
