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

  const lines = String(message || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  host.innerHTML = `
    <div class="app-toast" data-toast>
      <div class="app-toast-body">
        ${lines.map((line) => `<p class="app-toast-text">${escapeForToast(line)}</p>`).join('')}
      </div>
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
 * One badge → multi-line; multiple → single combined line.
 * @param {Array<{ title?: string, message?: string, reason?: string }>} badges
 */
export function toastMessageForBadges(badges) {
  if (!Array.isArray(badges) || badges.length === 0) return '';
  if (badges.length === 1) {
    const badge = badges[0];
    const title = badge.title || 'New badge';
    const reason = badge.reason || badge.message || '';
    return [`Badge unlocked!`, title, reason].filter(Boolean).join('\n');
  }
  return `You unlocked ${badges.length} new badges.`;
}
