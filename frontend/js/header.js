import { api, escapeHtml } from './api.js';

const MENU_ITEMS = [
  { label: 'Profile', to: '/profile' },
  { label: 'Statistics', to: '/profile/statistics' },
  { label: 'Settings', to: '/profile/settings' },
  { label: 'Help & Support', to: '/profile/help' },
];

export async function renderHeader(show = true) {
  const header = document.getElementById('app-header');
  if (!show) {
    header.classList.add('hidden');
    return;
  }

  header.classList.remove('hidden');
  let xp = 320;
  try {
    const home = await api.getHome();
    xp = home.progress.totalXp;
  } catch {
    /* use default */
  }

  header.innerHTML = `
    <a href="/" class="header-brand" data-link>
      <span class="header-brand-icon">🕵️</span>
      DetectiveLens
      <span style="color: var(--color-diamond)">🔍</span>
    </a>
    <div class="header-actions">
      <a href="/progress/xp" class="xp-link" data-link title="View your XP and level">
        <span style="font-size: 1.5rem">💎</span>
        <span id="header-xp">${xp}</span>
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
          <span class="profile-avatar">🕵️</span>
          <span style="color: var(--color-gray-500)">▾</span>
        </button>
        <div class="dropdown-menu hidden" id="profile-menu">
          ${MENU_ITEMS.map(
            (item) =>
              `<a href="${item.to}" class="dropdown-item" data-link>${escapeHtml(item.label)}</a>`,
          ).join('')}
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
