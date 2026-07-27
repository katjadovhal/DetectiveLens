import { api, escapeHtml } from './api.js';
import { getAvatarEmoji } from './avatars.js';
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
  let avatarEmoji = '🕵️';
  let notifications = [];
  let unreadCount = 0;

  if (userId) {
    try {
      const [{ profile }, home, noteData] = await Promise.all([
        api.getProfile(userId),
        api.getHome(userId),
        api.getNotifications(userId).catch(() => ({ notifications: [], unreadCount: 0 })),
      ]);
      if (!profile?.userId && !profile?.id) {
        if (getLastUserId() === userId) clearLastUserId();
      } else {
        const progress = getProgressSummary({ profile, home });
        xp = progress.totalXp;
        avatarEmoji = getAvatarEmoji(profile.avatarId || home.greeting?.avatarId);
      }
      notifications = noteData.notifications || [];
      unreadCount = noteData.unreadCount || 0;
    } catch {
      /* keep defaults */
    }
  }

  const unreadLabel =
    unreadCount > 0 ? `${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}` : 'No unread notifications';

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
          <button
            type="button"
            class="icon-btn"
            id="notification-bell-btn"
            aria-label="Notifications, ${unreadLabel}"
            aria-expanded="false"
            aria-haspopup="true"
          >
            <span aria-hidden="true">🔔</span>
            ${
              unreadCount > 0
                ? `<span class="notification-count" aria-hidden="true">${unreadCount > 9 ? '9+' : unreadCount}</span>`
                : ''
            }
          </button>
          <div class="dropdown-menu dropdown-menu-wide hidden" id="notification-menu" role="menu">
            <p class="dropdown-title">Notifications</p>
            ${renderNotificationItems(notifications, userId)}
          </div>
        </div>
        <div class="dropdown" id="profile-dropdown">
          <button type="button" class="profile-btn" aria-label="Profile menu" aria-expanded="false">
            <span class="profile-avatar" aria-hidden="true">${avatarEmoji}</span>
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
  bindNotificationActions(userId);
}

function renderNotificationItems(notifications, userId) {
  if (!notifications.length) {
    return `<p class="dropdown-item notification-empty">You're all caught up! No new alerts.</p>`;
  }

  return notifications
    .map((note) => {
      const unread = !note.readAt;
      const href =
        note.type === 'badge_unlocked'
          ? `${withUserId('/profile', userId)}#profile-badges`
          : withUserId('/profile', userId);
      return `
        <button
          type="button"
          class="dropdown-item notification-item${unread ? ' notification-item--unread' : ''}"
          role="menuitem"
          data-notification-id="${escapeHtml(note.id)}"
          data-notification-href="${href}"
        >
          <span class="notification-item-title">${escapeHtml(note.title || 'Notification')}</span>
          <span class="notification-item-message">${escapeHtml(note.message || '')}</span>
          <span class="notification-item-meta">${unread ? 'Unread' : 'Read'}</span>
        </button>
      `;
    })
    .join('');
}

function bindNotificationActions(userId) {
  if (!userId) return;
  document.querySelectorAll('[data-notification-id]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const notificationId = btn.getAttribute('data-notification-id');
      const href = btn.getAttribute('data-notification-href');
      try {
        await api.markNotificationRead(userId, notificationId);
      } catch {
        /* still navigate */
      }
      if (href) {
        window.location.href = href;
      }
    });
  });
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
