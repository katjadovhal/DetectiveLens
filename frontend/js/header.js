import { api, escapeHtml } from './api.js';
import { getAvatarMarkup } from './avatars.js';
import { resolveActiveUserId, withUserId, clearLastUserId, getLastUserId } from './session.js';
import { getProgressSummary } from './xp.js';

function menuItems(userId) {
  return [
    { label: 'Profile', to: withUserId('/profile', userId) },
    { label: 'Statistics', to: withUserId('/profile/statistics', userId) },
    { label: 'Settings', to: withUserId('/profile/settings', userId) },
    { label: 'Help & Support', to: withUserId('/profile/help', userId) },
  ];
}

export async function renderHeader(show = true) {
  const header = document.getElementById('app-header');
  if (!show) {
    header.classList.add('hidden');
    return;
  }

  header.classList.remove('hidden');
  const userId = resolveActiveUserId();
  let xp = 0;
  let avatarHtml = getAvatarMarkup(null, { className: 'avatar-img avatar-img--header' });

  if (userId) {
    try {
      const [{ profile }, home] = await Promise.all([
        api.getProfile(userId),
        api.getHome(userId),
      ]);
      if (!profile?.userId && !profile?.id) {
        if (getLastUserId() === userId) clearLastUserId();
      } else {
        const progress = getProgressSummary({ profile, home });
        xp = progress.totalXp;
        avatarHtml = getAvatarMarkup(profile.avatarId || home.greeting?.avatarId, {
          className: 'avatar-img avatar-img--header',
        });
      }
    } catch {
      /* keep defaults */
    }
  }

  header.innerHTML = `
    <div class="header-inner">
      <a href="${userId ? withUserId('/challenge-staging', userId) : '/'}" class="header-brand" data-link>
        <span class="header-brand-icon" aria-hidden="true">🕵️</span>
        DetectiveLens
      </a>
      <div class="header-actions">
        <a href="${withUserId('/progress/xp', userId)}" class="xp-link" data-link title="View your XP and level">
          <span aria-hidden="true">💎</span>
          <span id="header-xp">${xp}</span>
          <span class="xp-link-label">XP</span>
        </a>
        <div class="dropdown" id="notification-dropdown">
          <button type="button" class="icon-btn" aria-label="Notifications" aria-expanded="false">🔔</button>
          <div class="dropdown-menu dropdown-menu-wide hidden" id="notification-menu">
            <p class="dropdown-title">Notifications</p>
            <p class="dropdown-item">You're all caught up! No new alerts.</p>
          </div>
        </div>
        <div class="dropdown" id="profile-dropdown">
          <button type="button" class="profile-btn" aria-label="Profile menu" aria-expanded="false">
            <span class="profile-avatar" aria-hidden="true">${avatarHtml}</span>
            <span aria-hidden="true">▾</span>
          </button>
          <div class="dropdown-menu hidden" id="profile-menu">
            ${menuItems(userId)
              .map(
                (item) =>
                  `<a href="${item.to}" class="dropdown-item" data-link>${escapeHtml(item.label)}</a>`,
              )
              .join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  setupDropdown('notification-dropdown', 'notification-menu');
  setupDropdown('profile-dropdown', 'profile-menu');
}

function setupDropdown(wrapperId, menuId) {
  const wrapper = document.getElementById(wrapperId);
  const menu = document.getElementById(menuId);
  const btn = wrapper.querySelector('button');

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !menu.classList.contains('hidden');
    closeAllDropdowns();
    if (!open) {
      menu.classList.remove('hidden');
      btn.setAttribute('aria-expanded', 'true');
    }
  });
}

function closeAllDropdowns() {
  document.querySelectorAll('.dropdown-menu').forEach((m) => m.classList.add('hidden'));
  document.querySelectorAll('.dropdown button[aria-expanded]').forEach((b) => {
    b.setAttribute('aria-expanded', 'false');
  });
}

document.addEventListener('click', closeAllDropdowns);

export function updateHeaderXp(xp) {
  const el = document.getElementById('header-xp');
  if (el) el.textContent = xp;
}
