import { escapeHtml } from './api.js';
import { itemsForSlotCategory, SHOP_ITEMS_BY_ID } from './shop-items.js';

/**
 * Open slot item selector (side panel on desktop, bottom sheet on mobile).
 * @param {HTMLElement} host
 * @param {{
 *   slotId: string,
 *   category: string,
 *   slotLabel: string,
 *   ownedIds: Set<string>,
 *   totalXp: number,
 *   equippedItemId: string | null,
 *   previewItemId: string | null,
 *   onSelect: (itemId: string) => void,
 *   onRemove: () => void,
 *   onGoToShop: () => void,
 *   onClose: () => void,
 * }} options
 */
export function openHqItemSelector(host, options) {
  const {
    slotId,
    category,
    slotLabel,
    ownedIds,
    totalXp,
    equippedItemId,
    previewItemId,
    onSelect,
    onRemove,
    onGoToShop,
    onClose,
  } = options;

  let closed = false;
  const previouslyFocused = document.activeElement;
  const items = itemsForSlotCategory(category);

  const owned = items.filter((item) => ownedIds.has(item.id));
  const locked = items.filter((item) => !ownedIds.has(item.id));
  const sorted = [...owned, ...locked];

  const overlay = document.createElement('div');
  overlay.className = 'hq-selector-overlay';
  overlay.setAttribute('role', 'presentation');

  function close() {
    if (closed) return;
    closed = true;
    document.removeEventListener('keydown', onKeyDown, true);
    overlay.remove();
    if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
      previouslyFocused.focus();
    }
    onClose?.();
  }

  function renderItemRow(item) {
    const isOwned = ownedIds.has(item.id);
    const isEquipped = equippedItemId === item.id;
    const isPreview = previewItemId === item.id;
    const isLocked = !isOwned && totalXp < item.price;

    let statusText = '';
    if (isEquipped) statusText = 'Equipped';
    else if (isPreview) statusText = 'Previewing';
    else if (isOwned) statusText = 'Owned';
    else if (isLocked) statusText = `Locked · ${item.price} XP needed`;
    else statusText = `Unlocked · ${item.price} XP`;

    let action = '';
    if (isOwned) {
      const disabled = isEquipped ? 'disabled aria-disabled="true"' : '';
      action = `<button type="button" class="btn btn-primary hq-selector-equip" data-item-id="${escapeHtml(item.id)}" ${disabled}>${isEquipped ? 'Equipped' : 'Equip'}</button>`;
    } else if (isLocked) {
      action = `<button type="button" class="btn btn-secondary hq-selector-shop" data-item-id="${escapeHtml(item.id)}">Go to shop</button>`;
    } else {
      action = `<button type="button" class="btn btn-secondary hq-selector-shop" data-item-id="${escapeHtml(item.id)}">Go to shop</button>`;
    }

    return `
      <li class="hq-selector-item${isEquipped ? ' hq-selector-item--equipped' : ''}${isPreview ? ' hq-selector-item--preview' : ''}">
        <div class="hq-selector-item-thumb">
          <img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.alt)}" loading="lazy" />
        </div>
        <div class="hq-selector-item-body">
          <p class="hq-selector-item-name">${escapeHtml(item.name)}</p>
          <p class="hq-selector-item-status">
            ${isEquipped ? '<span aria-hidden="true">✓</span> ' : ''}${escapeHtml(statusText)}
          </p>
        </div>
        ${action}
      </li>
    `;
  }

  overlay.innerHTML = `
    <div
      class="hq-selector-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="hq-selector-title"
      tabindex="-1"
    >
      <div class="hq-selector-header">
        <h2 id="hq-selector-title" class="hq-selector-title">${escapeHtml(slotLabel)}</h2>
        <button type="button" class="hq-selector-close" aria-label="Close item list">×</button>
      </div>
      <p class="hq-selector-hint">Choose an owned item to preview. Save the room to keep changes.</p>
      <ul class="hq-selector-list" role="list">
        ${sorted.map(renderItemRow).join('')}
      </ul>
      ${
        equippedItemId || previewItemId
          ? `<button type="button" class="btn btn-outline hq-selector-clear">Remove from slot</button>`
          : ''
      }
    </div>
  `;

  const panel = overlay.querySelector('.hq-selector-panel');
  panel.addEventListener('click', (e) => e.stopPropagation());
  overlay.addEventListener('click', close);

  overlay.querySelector('.hq-selector-close').addEventListener('click', close);

  overlay.querySelectorAll('.hq-selector-equip').forEach((btn) => {
    btn.addEventListener('click', () => {
      const itemId = btn.getAttribute('data-item-id');
      if (!itemId || !ownedIds.has(itemId)) return;
      onSelect(itemId);
    });
  });

  overlay.querySelectorAll('.hq-selector-shop').forEach((btn) => {
    btn.addEventListener('click', () => {
      onGoToShop();
      close();
    });
  });

  const clearBtn = overlay.querySelector('.hq-selector-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      onRemove();
    });
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
    }
  }

  document.addEventListener('keydown', onKeyDown, true);
  host.appendChild(overlay);
  panel.focus();

  return { close };
}

export function getSlotLabel(slotId) {
  const labels = {
    desk: 'Desk',
    chair: 'Chair',
    deskDecoration: 'Desk decoration',
    cabinet: 'Cabinet',
  };
  return labels[slotId] || slotId;
}
