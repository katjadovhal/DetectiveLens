import { escapeHtml } from './api.js';

/**
 * Build HTML for one shop product card.
 * @param {{ id: string, name: string, price: number, image: string, alt: string }} item
 * @param {{ owned: boolean, busy: boolean }} options
 */
export function renderShopItemCard(item, { owned = false, busy = false } = {}) {
  const action = owned
    ? `<button type="button" class="btn btn-secondary shop-item-buy" disabled aria-disabled="true">Owned</button>`
    : `<button type="button" class="btn btn-primary shop-item-buy" data-item-id="${escapeHtml(item.id)}" ${
        busy ? 'disabled aria-busy="true"' : ''
      }>Buy</button>`;

  return `
    <article class="shop-item-card" data-shop-item="${escapeHtml(item.id)}">
      <div class="shop-item-image-wrap">
        <img
          class="shop-item-image"
          src="${escapeHtml(item.image)}"
          alt="${escapeHtml(item.alt)}"
          loading="lazy"
        />
      </div>
      <h3 class="shop-item-name">${escapeHtml(item.name)}</h3>
      <p class="shop-item-price">
        <span aria-hidden="true">💎</span>
        <span>${item.price} XP</span>
      </p>
      ${action}
    </article>
  `;
}
