/**
 * Circlo Main TypeScript Entrypoint
 * Powers browser interactivity for server-rendered Django templates.
 */

// Theme Controller
function initTheme(): void {
  const toggleBtn = document.getElementById('theme-toggle');
  const htmlElement = document.documentElement;

  // Retrieve saved theme or prefer dark mode as default
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

// Utility: get Django CSRF Cookie
export function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : null;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  console.log('Circlo interactive frontend initialized.');
});
