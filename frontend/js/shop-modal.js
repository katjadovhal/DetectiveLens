import { escapeHtml } from './api.js';
import { SHOP_ITEMS } from './shop-items.js';
import { renderShopItemCard } from './shop-item-card.js';

/**
 * Accessible shop modal for Detective HQ (ShopModal).
 * @param {HTMLElement} host
 * @param {{
 *   totalXp: number,
 *   ownedIds: Iterable<string>,
 *   onClose?: () => void,
 *   onBuy: (itemId: string) => Promise<{ totalXp: number, message?: string }>,
 * }} options
 */
export function openShopModal(host, { totalXp, ownedIds, onClose, onBuy }) {
  const owned = new Set(ownedIds || []);
  let xp = Number(totalXp) || 0;
  let message = '';
  let messageTone = 'info';
  let busyId = null;
  let closed = false;
  const previousOverflow = document.body.style.overflow;
  const previouslyFocused = document.activeElement;

  document.body.style.overflow = 'hidden';

  const overlay = document.createElement('div');
  overlay.className = 'shop-modal-overlay';
  overlay.setAttribute('role', 'presentation');

  function getFocusable() {
    return [
      ...overlay.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ),
    ];
  }

  function close() {
    if (closed) return;
    closed = true;
    document.removeEventListener('keydown', onKeyDown, true);
    document.body.style.overflow = previousOverflow;
    overlay.remove();
    if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
      previouslyFocused.focus();
    }
    onClose?.();
  }

  function paint() {
    const grid = SHOP_ITEMS.map((item) =>
      renderShopItemCard(item, {
        owned: owned.has(item.id),
        busy: busyId === item.id,
      }),
    ).join('');

    overlay.innerHTML = `
      <div
        class="shop-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shop-modal-title"
        tabindex="-1"
      >
        <div class="shop-modal-header">
          <h2 id="shop-modal-title" class="shop-modal-title">Shop</h2>
          <button type="button" class="shop-modal-close" aria-label="Close shop">×</button>
        </div>
        <p class="shop-modal-xp" aria-live="polite">
          Your XP: <strong id="shop-modal-xp-value">${xp}</strong>
        </p>
        <p
          class="shop-modal-message shop-modal-message--${messageTone}${message ? '' : ' hidden'}"
          role="status"
          aria-live="polite"
        >${escapeHtml(message)}</p>
        <div class="shop-modal-grid">
          ${grid}
        </div>
      </div>
    `;

    const dialog = overlay.querySelector('.shop-modal');
    dialog.addEventListener('click', (e) => e.stopPropagation());
    overlay.querySelector('.shop-modal-close').addEventListener('click', close);

    overlay.querySelectorAll('.shop-item-buy[data-item-id]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const itemId = btn.getAttribute('data-item-id');
        if (!itemId || owned.has(itemId) || busyId) return;

        busyId = itemId;
        message = '';
        paint();

        try {
          const result = await onBuy(itemId);
          owned.add(itemId);
          if (typeof result?.totalXp === 'number') xp = result.totalXp;
          message = result?.message || 'Purchase successful!';
          messageTone = 'success';
        } catch (err) {
          message = err?.message || 'Could not complete purchase';
          messageTone = 'error';
        } finally {
          busyId = null;
          paint();
        }
      });
    });

    dialog.focus();
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
      return;
    }
    if (e.key !== 'Tab') return;
    const focusable = getFocusable();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  overlay.addEventListener('click', close);
  document.addEventListener('keydown', onKeyDown, true);
  host.appendChild(overlay);
  paint();

  return { close };
}
