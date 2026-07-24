import { api, escapeHtml } from '../api.js';
import { getAvatarMarkup } from '../avatars.js';
import {
  resolveActiveUserId,
  setLastUserId,
  clearLastUserId,
  withUserId,
  loadValidUser,
} from '../session.js';
import { getProgressSummary } from '../xp.js';

export async function renderSettings(container) {
  const userId = resolveActiveUserId();
  if (!userId) {
    window.location.href = '/';
    return;
  }

  container.innerHTML = '<div class="loading">Loading settings...</div>';

  const loaded = await loadValidUser(userId, { api, includeHome: true });
  if (!loaded) {
    clearLastUserId();
    window.location.href = '/select-user';
    return;
  }

  setLastUserId(userId);
  const { profile, home } = loaded;
  const progress = getProgressSummary({ profile, home });
  const name = profile.displayName || 'Detective';
  const backHref = withUserId('/challenge-staging', userId);
  const profileHref = withUserId('/profile', userId);

  container.innerHTML = `
    <div class="page-shell settings-page">
      <div class="profile-top-actions">
        <a href="${backHref}" class="btn btn-secondary" data-link>← Back to home</a>
      </div>

      <header class="page-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">Manage your account and switch profiles.</p>
      </header>

      <section class="panel-card settings-current" aria-label="Current account">
        <div class="settings-current-avatar" aria-hidden="true">${getAvatarMarkup(profile.avatarId, { className: 'avatar-img avatar-img--settings' })}</div>
        <div class="settings-current-copy">
          <p class="settings-current-kicker">Signed in as</p>
          <h2 class="settings-current-name">${escapeHtml(name)}</h2>
          <p class="settings-current-level">${escapeHtml(progress.levelTitle)}</p>
        </div>
      </section>

      <section class="panel-card settings-section" aria-labelledby="account-actions-heading">
        <h2 id="account-actions-heading" class="section-title">Account</h2>
        <div class="settings-action-list">
          <a href="${profileHref}" class="settings-action" data-link>
            <span class="settings-action-icon" aria-hidden="true">👤</span>
            <span class="settings-action-copy">
              <span class="settings-action-title">Edit profile</span>
              <span class="settings-action-desc">Change your name or avatar</span>
            </span>
            <span class="settings-action-chevron" aria-hidden="true">›</span>
          </a>

          <a href="${backHref}" class="settings-action" data-link>
            <span class="settings-action-icon" aria-hidden="true">🏠</span>
            <span class="settings-action-copy">
              <span class="settings-action-title">Back to home</span>
              <span class="settings-action-desc">Return to challenges and daily mission</span>
            </span>
            <span class="settings-action-chevron" aria-hidden="true">›</span>
          </a>

          <button type="button" class="settings-action" id="settings-welcome-btn">
            <span class="settings-action-icon" aria-hidden="true">👋</span>
            <span class="settings-action-copy">
              <span class="settings-action-title">Go to welcome page</span>
              <span class="settings-action-desc">See the start screen again (keeps your profile)</span>
            </span>
            <span class="settings-action-chevron" aria-hidden="true">›</span>
          </button>

          <button type="button" class="settings-action" id="settings-switch-btn">
            <span class="settings-action-icon" aria-hidden="true">🔄</span>
            <span class="settings-action-copy">
              <span class="settings-action-title">Switch account</span>
              <span class="settings-action-desc">Choose a different detective profile</span>
            </span>
            <span class="settings-action-chevron" aria-hidden="true">›</span>
          </button>

          <button type="button" class="settings-action" id="settings-create-btn">
            <span class="settings-action-icon" aria-hidden="true">➕</span>
            <span class="settings-action-copy">
              <span class="settings-action-title">Create new profile</span>
              <span class="settings-action-desc">Start fresh with a new detective</span>
            </span>
            <span class="settings-action-chevron" aria-hidden="true">›</span>
          </button>
        </div>
      </section>
    </div>
  `;

  container.querySelector('#settings-welcome-btn').addEventListener('click', () => {
    // Keep lastUserId so Welcome can show “Continue as …”
    window.location.href = '/';
  });

  container.querySelector('#settings-switch-btn').addEventListener('click', () => {
    window.location.href = '/select-user';
  });

  container.querySelector('#settings-create-btn').addEventListener('click', () => {
    window.location.href = '/onboarding';
  });
}
