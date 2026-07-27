/**
 * Non-blocking toast with polite aria-live. No focus steal.
 */

let toastTimer = null;

function ensureHost() {
  let host = document.getElementById('app-toast-host');
  if (!host) {
    host = document.createElement('div');
    host.id = 'app-toast-host';
    host.className = 'app-toast-host';
    host.setAttribute('aria-live', 'polite');
    host.setAttribute('aria-relevant', 'additions text');
    host.setAttribute('role', 'status');
    document.body.appendChild(host);
  }
  return host;
}

/**
 * @param {string} message
 * @param {{ durationMs?: number }} [options]
 */
export function showToast(message, options = {}) {
  const host = ensureHost();
  const duration = options.durationMs ?? 4500;

  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }

  host.innerHTML = `
    <div class="app-toast" data-toast>
      <p class="app-toast-text">${escapeForToast(message)}</p>
      <button type="button" class="app-toast-dismiss" aria-label="Dismiss notification">Dismiss</button>
    </div>
  `;

  const dismiss = host.querySelector('.app-toast-dismiss');
  if (dismiss) {
    dismiss.addEventListener('click', () => {
      host.innerHTML = '';
      if (toastTimer) clearTimeout(toastTimer);
    });
  }

  toastTimer = setTimeout(() => {
    host.innerHTML = '';
    toastTimer = null;
  }, duration);
}

function escapeForToast(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

/**
 * Build toast copy for newly unlocked badges.
 * @param {Array<{ title?: string, message?: string }>} badges
 */
export function toastMessageForBadges(badges) {
  if (!Array.isArray(badges) || badges.length === 0) return '';
  if (badges.length === 1) {
    return badges[0].message || `You unlocked ${badges[0].title || 'a new badge'}.`;
  }
  return `You unlocked ${badges.length} new badges.`;
}
