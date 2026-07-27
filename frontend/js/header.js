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
        avatarHtml = getAvatarMarkup(profile.avatarId || home.greeting?.avatarId, {
          className: 'avatar-img avatar-img--header',
        });
      }
      notifications = noteData.notifications || [];
      unreadCount = noteData.unreadCount || 0;
    } catch {
      /* keep defaults */
    }
  }

  paintHeaderShell({ userId, xp, avatarHtml, notifications, unreadCount });
}

function paintHeaderShell({ userId, xp, avatarHtml, notifications, unreadCount }) {
  const header = document.getElementById('app-header');
  if (!header) return;

  const unreadLabel =
    unreadCount > 0
      ? `${unreadCount} unread`
      : 'No unread notifications';

  header.innerHTML = `
    <div class="header-inner">
      <a href="${userId ? withUserId('/challenge-staging', userId) : '/'}" class="header-brand" data-link>
        <span class="header-brand-icon" aria-hidden="true">🕵️</span>
        DetectiveLens
      </a>
      <div class="header-actions">
        ${
          userId
            ? `<a href="${withUserId('/detective-hq', userId)}" class="header-nav-link" data-link>Detective HQ</a>`
            : ''
        }
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
            <div id="notification-list">${renderNotificationItems(notifications, userId)}</div>
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
  bindNotificationActions(userId);
}

function renderNotificationItems(notifications, userId) {
  if (!notifications.length) {
    return `<p class="dropdown-item notification-empty">You're all caught up! No new alerts.</p>`;
  }

  return notifications.map((note) => renderNotificationItem(note, userId)).join('');
}

function renderNotificationItem(note, userId) {
  const unread = !note.readAt;
  const badgeId = note.badgeId || '';
  const href =
    note.type === 'badge_unlocked' && badgeId
      ? `${withUserId('/profile', userId)}#badge-${encodeURIComponent(badgeId)}`
      : withUserId('/profile', userId);
  const icon = note.icon || (note.type === 'badge_unlocked' ? '🎖️' : '🔔');
  const timeLabel = formatRelativeTime(note.createdAt);

  return `
    <button
      type="button"
      class="dropdown-item notification-item${unread ? ' notification-item--unread' : ''}"
      role="menuitem"
      data-notification-id="${escapeHtml(note.id)}"
      data-notification-href="${href}"
    >
      <span class="notification-item-row">
        <span class="notification-item-icon" aria-hidden="true">${escapeHtml(icon)}</span>
        <span class="notification-item-copy">
          <span class="notification-item-title">${escapeHtml(note.title || 'Notification')}</span>
          <span class="notification-item-message">${escapeHtml(note.message || '')}</span>
          <span class="notification-item-meta">
            <span>${unread ? 'Unread' : 'Read'}</span>
            ${timeLabel ? `<span aria-hidden="true">·</span><span>${escapeHtml(timeLabel)}</span>` : ''}
          </span>
        </span>
      </span>
    </button>
  `;
}

function formatRelativeTime(iso) {
  if (!iso) return '';
  try {
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return '';
    const diffSec = Math.round((Date.now() - then) / 1000);
    if (diffSec < 60) return 'Just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} h ago`;
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '';
  }
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
  if (!wrapper) return;
  const menu = document.getElementById(menuId);
  const btn = wrapper.querySelector('button');
  if (!menu || !btn) return;

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

/**
 * Immediately reflect newly unlocked badge notifications in the bell/dropdown
 * without a full page refresh.
 * @param {Array<object>} unlocks from submit newlyUnlockedBadges
 */
export function ingestBadgeUnlockNotifications(unlocks) {
  if (!Array.isArray(unlocks) || unlocks.length === 0) return;

  const list = document.getElementById('notification-list');
  const bell = document.getElementById('notification-bell-btn');
  if (!list || !bell) return;

  const userId = resolveActiveUserId();
  const empty = list.querySelector('.notification-empty');
  if (empty) empty.remove();

  const nowIso = new Date().toISOString();
  const notes = unlocks.map((badge, index) => ({
    id: badge.notificationId || `local-badge-${badge.id || index}-${Date.now()}`,
    type: 'badge_unlocked',
    badgeId: badge.id,
    icon: badge.icon || '🎖️',
    title: 'New badge unlocked!',
    message: badge.message || `You earned the ${badge.title || 'badge'} badge.`,
    createdAt: badge.earnedAt || nowIso,
    readAt: null,
  }));

  const html = notes.map((note) => renderNotificationItem(note, userId)).join('');
  list.insertAdjacentHTML('afterbegin', html);
  bindNotificationActions(userId);

  const countText = bell.querySelector('.notification-count')?.textContent || '0';
  const currentUnread = countText === '9+' ? 10 : Number(countText) || 0;
  updateBellUnreadCount(currentUnread + notes.length);
}

function updateBellUnreadCount(unreadCount) {
  const bell = document.getElementById('notification-bell-btn');
  if (!bell) return;

  const unreadLabel =
    unreadCount > 0 ? `${unreadCount} unread` : 'No unread notifications';
  bell.setAttribute('aria-label', `Notifications, ${unreadLabel}`);

  let countEl = bell.querySelector('.notification-count');
  if (unreadCount <= 0) {
    if (countEl) countEl.remove();
    return;
  }
  if (!countEl) {
    countEl = document.createElement('span');
    countEl.className = 'notification-count';
    countEl.setAttribute('aria-hidden', 'true');
    bell.appendChild(countEl);
  }
  countEl.textContent = unreadCount > 9 ? '9+' : String(unreadCount);
}
