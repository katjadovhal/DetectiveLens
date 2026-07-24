import { api, escapeHtml } from '../api.js';
import { getAvatarMarkup } from '../avatars.js';
import { setLastUserId, clearLastUserId, getLastUserId } from '../session.js';
import { getProgressSummary } from '../xp.js';

function renderCardXp(progress) {
  const label = progress.atMaxLevel
    ? `${progress.totalXp} XP · Max level`
    : `${progress.currentLevelXp} / ${progress.levelXpRequired} XP`;
  return `
    <div class="mini-xp">
      <div class="progress-track mini-xp-track" role="progressbar"
        aria-valuemin="0" aria-valuemax="${progress.levelXpRequired}"
        aria-valuenow="${progress.currentLevelXp}"
        aria-label="XP progress">
        <div class="progress-fill" style="width: ${progress.percent}%"></div>
      </div>
      <span class="mini-xp-label">${label}</span>
    </div>
  `;
}

export async function renderSelectUser(container) {
  container.innerHTML = '<div class="loading">Loading profiles...</div>';

  try {
    const response = await api.getUsers();
    const users = response.users || [];

    if (users.length === 0) {
      clearLastUserId();
      window.location.href = '/onboarding';
      return;
    }

    const cards = await Promise.all(
      users.map(async (user) => {
        try {
          const [{ profile }, home] = await Promise.all([
            api.getProfile(user.id),
            api.getHome(user.id),
          ]);
          if (!profile?.userId && !profile?.id) return null;
          const progress = getProgressSummary({ profile, home });
          return {
            id: user.id,
            name: profile.displayName || user.username || 'Detective',
            avatarId: profile.avatarId,
            progress,
          };
        } catch {
          return null;
        }
      }),
    );

    const profiles = cards.filter(Boolean);
    const lastId = getLastUserId();

    container.innerHTML = `
      <div class="page-shell select-page">
        <header class="page-header">
          <h1 class="page-title">Choose a Profile</h1>
          <p class="page-subtitle">Pick up where you left off.</p>
        </header>

        <div class="profile-card-grid" role="list">
          ${profiles
            .map((p) => {
              const selected = p.id === lastId;
              return `
              <button
                type="button"
                class="profile-pick-card${selected ? ' selected' : ''}"
                data-user-id="${p.id}"
                role="listitem"
                aria-label="${escapeHtml(p.name)}, ${escapeHtml(p.progress.levelTitle)}${selected ? ', last used' : ''}"
              >
                ${selected ? '<span class="pick-check" aria-hidden="true">✓</span><span class="visually-hidden">Last used</span>' : ''}
                <span class="pick-avatar" aria-hidden="true">${getAvatarMarkup(p.avatarId, { className: 'avatar-img avatar-img--pick' })}</span>
                <span class="pick-name">${escapeHtml(p.name)}</span>
                <span class="pick-level">${escapeHtml(p.progress.levelTitle)}</span>
                ${renderCardXp(p.progress)}
              </button>
            `;
            })
            .join('')}

          <button
            type="button"
            class="profile-pick-card profile-pick-create"
            id="create-profile-card"
            aria-label="Create New Profile"
          >
            <span class="pick-create-icon" aria-hidden="true">+</span>
            <span class="pick-name">Create New Profile</span>
          </button>
        </div>
      </div>
    `;

    container.querySelectorAll('[data-user-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const userId = btn.dataset.userId;
        setLastUserId(userId);
        window.location.href = `/challenge-staging?userId=${encodeURIComponent(userId)}`;
      });
    });

    container.querySelector('#create-profile-card').addEventListener('click', () => {
      window.location.href = '/onboarding';
    });
  } catch (err) {
    console.error('Error loading users:', err);
    container.innerHTML = `
      <div class="page-shell">
        <h1 class="page-title">Error</h1>
        <p class="page-subtitle">Could not load profiles. <a href="/" data-link>Go back</a></p>
      </div>
    `;
  }
}
