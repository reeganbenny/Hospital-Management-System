/**
 * Show a Bootstrap toast notification.
 */

import Toast from 'bootstrap/js/dist/toast';

export function toast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const id = `toast-${Date.now()}`;
  const bg = type === 'error' ? 'bg-danger' : type === 'info' ? 'bg-info' : 'bg-success';
  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-white border-0 ${bg}`;
  toastEl.setAttribute('role', 'alert');
  toastEl.id = id;
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${escapeHtml(message)}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  container.appendChild(toastEl);
  const bsToast = new Toast(toastEl, { delay: 4000 });
  bsToast.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
