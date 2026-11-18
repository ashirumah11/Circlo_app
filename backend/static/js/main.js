/**
 * Circlo Main JavaScript Runtime
 */
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  const htmlElement = document.documentElement;

  const savedTheme = localStorage.getItem('circlo_theme') || 'dark';
  htmlElement.setAttribute('data-theme', savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = htmlElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      htmlElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('circlo_theme', newTheme);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  console.log('Circlo frontend initialized successfully.');
});
