import { api } from '../api.js';
import { updateHeaderXp } from '../header.js';
import {
  resolveActiveUserId,
  setLastUserId,
  clearLastUserId,
  loadValidUser,
} from '../session.js';
import { getProgressSummary } from '../xp.js';
import { HQ_ASSETS } from '../shop-items.js';
import { openShopModal } from '../shop-modal.js';

/**
 * Detective HQ page — room view + shop entry.
 * @param {HTMLElement} container
 */
export async function renderDetectiveHQ(container) {
  const userId = resolveActiveUserId();
  if (!userId) {
    window.location.href = '/';
    return;
  }

  container.innerHTML = '<div class="loading">Loading Detective HQ...</div>';

  const loaded = await loadValidUser(userId, { api, includeHome: true });
  if (!loaded) {
    clearLastUserId();
    window.location.href = '/select-user';
    return;
  }

  setLastUserId(userId);
  const { profile, home } = loaded;
  const progress = getProgressSummary({ profile, home });

  const state = {
    totalXp: progress.totalXp,
    ownedIds: new Set(profile.hqOwnedItemIds || []),
  };

  container.innerHTML = `
    <div class="page-shell detective-hq-page">
      <h1 class="detective-hq-title">Detective HQ</h1>
      <div class="detective-hq-room">
        <img
          class="detective-hq-room-image"
          src="${HQ_ASSETS.roomDefault}"
          alt="Your detective headquarters room"
        />
        <button
          type="button"
          class="detective-hq-shop-btn"
          id="detective-hq-open-shop"
          aria-label="Open shop"
        >
          <img
            src="${HQ_ASSETS.shopButton}"
            alt="Shop"
            class="detective-hq-shop-btn-img"
          />
        </button>
      </div>
      <div id="detective-hq-modal-host"></div>
    </div>
  `;

  const openBtn = container.querySelector('#detective-hq-open-shop');
  const modalHost = container.querySelector('#detective-hq-modal-host');

  openBtn.addEventListener('click', () => {
    openShopModal(modalHost, {
      totalXp: state.totalXp,
      ownedIds: state.ownedIds,
      onBuy: async (itemId) => {
        try {
          const result = await api.purchaseHqItem(userId, itemId);
          state.totalXp = result.totalXp;
          (result.hqOwnedItemIds || []).forEach((id) => state.ownedIds.add(id));
          state.ownedIds.add(itemId);
          updateHeaderXp(state.totalXp);
          return {
            totalXp: state.totalXp,
            message: result.message || 'Purchase successful!',
          };
        } catch (err) {
          const msg = err?.message || 'Could not complete purchase';
          if (/not enough xp/i.test(msg)) {
            throw new Error('Not enough XP');
          }
          throw new Error(msg);
        }
      },
    });
  });
}
