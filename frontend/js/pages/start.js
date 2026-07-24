import { api, escapeHtml } from '../api.js';
import { getAvatarMarkup } from '../avatars.js';
import { getLastUserId, setLastUserId, loadValidUser, withUserId } from '../session.js';
import { getProgressSummary } from '../xp.js';

function renderMiniXp(progress) {
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

export async function renderStart(container) {
  container.innerHTML = '<div class="loading">Loading...</div>';

  try {
    const welcome = await api.getWelcome();
    let continueHtml = '';

    const lastUserId = getLastUserId();
    if (lastUserId) {
      const loaded = await loadValidUser(lastUserId, { api, includeHome: true });
      if (loaded) {
        const { profile, home } = loaded;
        const progress = getProgressSummary({ profile, home });
        const name = profile.displayName || home.greeting?.displayName || 'Detective';
        continueHtml = `
          <div class="hero-divider" role="separator"><span>or</span></div>
          <button type="button" class="continue-card" id="continue-as-btn">
            <span class="continue-avatar" aria-hidden="true">${getAvatarMarkup(profile.avatarId, { className: 'avatar-img avatar-img--continue' })}</span>
            <span class="continue-copy">
              <span class="continue-kicker">Continue as</span>
              <span class="continue-name">${escapeHtml(name)}</span>
              <span class="continue-level">${escapeHtml(progress.levelTitle)}</span>
              ${renderMiniXp(progress)}
            </span>
            <span class="continue-chevron" aria-hidden="true">›</span>
          </button>
        `;
      }
    }

    container.innerHTML = `
      <div class="page-shell page-shell-centered">
        <section class="hero-card panel-card" aria-labelledby="welcome-heading">
          <h1 id="welcome-heading" class="page-title">${escapeHtml(welcome.title)}</h1>
          <p class="page-subtitle">${escapeHtml(welcome.subtitle)}</p>
          <div class="hero-avatar" role="img" aria-label="Friendly detective">🕵️‍♂️</div>

          <div class="hero-actions">
            <button type="button" class="btn btn-primary btn-full" id="create-user-btn">
              + Create New Profile
            </button>
            <button type="button" class="btn btn-secondary btn-full" id="existing-user-btn">
              <span aria-hidden="true">👤</span> Choose Existing Profile
            </button>
          </div>

          ${continueHtml}
        </section>
      </div>
    `;

    container.querySelector('#create-user-btn').addEventListener('click', () => {
      window.location.href = '/onboarding';
    });

    container.querySelector('#existing-user-btn').addEventListener('click', async () => {
      try {
        const response = await api.getUsers();
        window.location.href =
          response.users && response.users.length > 0 ? '/select-user' : '/onboarding';
      } catch {
        window.location.href = '/onboarding';
      }
    });

    const continueBtn = container.querySelector('#continue-as-btn');
    if (continueBtn && lastUserId) {
      continueBtn.addEventListener('click', () => {
        setLastUserId(lastUserId);
        window.location.href = withUserId('/challenge-staging', lastUserId);
      });
    }
  } catch (err) {
    console.error('Error loading start page:', err);
    container.innerHTML = '<div class="error">Error loading page</div>';
  }
}
