document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('#sidebar');
  document.querySelectorAll('[data-sidebar-toggle]').forEach((button) => button.addEventListener('click', () => sidebar?.classList.toggle('open')));
  document.querySelectorAll('[data-confirm]').forEach((form) => form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  }));
  document.querySelectorAll('[data-loading]').forEach((form) => form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.dataset.originalText = button.innerText; button.innerText = form.dataset.loading; }
  }));
  window.setTimeout(() => document.querySelectorAll('.flash').forEach((flash) => { flash.style.opacity = '0'; flash.style.transform = 'translateY(-3px)'; flash.style.transition = 'opacity .3s, transform .3s'; window.setTimeout(() => flash.remove(), 350); }), 5200);
});
