import { api, escapeHtml } from '../api.js';
import {
  getAvatarEmoji,
  getAvatarLabel,
  normalizeAvatarId,
  renderAvatarGridHtml,
  bindAvatarGrid,
} from '../avatars.js';
import {
  resolveActiveUserId,
  setLastUserId,
  clearLastUserId,
  withUserId,
  loadValidUser,
} from '../session.js';
import { getProgressSummary, renderXpBarHtml } from '../xp.js';

export async function renderProfile(container) {
  const userId = resolveActiveUserId();
  if (!userId) {
    window.location.href = '/';
    return;
  }

  container.innerHTML = '<div class="loading">Loading profile...</div>';

  const loaded = await loadValidUser(userId, { api, includeHome: true });
  if (!loaded) {
    clearLastUserId();
    window.location.href = '/select-user';
    return;
  }

  setLastUserId(userId);
  const { profile, home } = loaded;
  const progress = getProgressSummary({ profile, home });
  const colorBlindness = Boolean(profile.colorBlindness);
  const backHref = withUserId('/challenge-staging', userId);

  const state = {
    displayName: profile.displayName || '',
    avatarId: normalizeAvatarId(profile.avatarId),
    saving: false,
    message: '',
    error: '',
    nameError: '',
  };

  function paint() {
    const emoji = getAvatarEmoji(state.avatarId);
    container.innerHTML = `
      <div class="page-shell profile-page${colorBlindness ? ' profile-colorblind' : ''}">
        <div class="profile-top-actions">
          <a href="${backHref}" class="btn btn-secondary" data-link>← Back to home</a>
        </div>

        <div class="profile-layout">
          <section class="panel-card profile-overview" aria-labelledby="profile-heading">
            <div class="avatar-large profile-hero-avatar" aria-hidden="true">${emoji}</div>
            <h1 id="profile-heading" class="page-title profile-display-name">${escapeHtml(state.displayName)}</h1>
            <p class="profile-level-badge">
              <span aria-hidden="true">🛡️</span>
              ${escapeHtml(progress.levelTitle)}
            </p>
            ${renderXpBarHtml(progress)}

            <div class="stat-chip-row" aria-label="Your stats">
              <div class="stat-chip">
                <span class="stat-chip-icon" aria-hidden="true">⭐</span>
                <span class="stat-chip-value">${progress.totalXp}</span>
                <span class="stat-chip-label">Total XP</span>
              </div>
              <div class="stat-chip">
                <span class="stat-chip-icon" aria-hidden="true">🎯</span>
                <span class="stat-chip-value">${progress.level}</span>
                <span class="stat-chip-label">Level</span>
              </div>
              <div class="stat-chip">
                <span class="stat-chip-icon" aria-hidden="true">🏆</span>
                <span class="stat-chip-value">${progress.completedChallengeCount}</span>
                <span class="stat-chip-label">Challenges</span>
              </div>
            </div>
          </section>

          <section class="panel-card profile-edit" aria-labelledby="edit-heading">
            <h2 id="edit-heading" class="section-title">Edit Your Profile</h2>

            <div class="field">
              <label for="profile-display-name">Display name</label>
              <input
                type="text"
                id="profile-display-name"
                class="form-input${state.nameError ? ' input-invalid' : ''}"
                maxlength="50"
                value="${escapeHtml(state.displayName)}"
                autocomplete="nickname"
                aria-invalid="${state.nameError ? 'true' : 'false'}"
                aria-describedby="${state.nameError ? 'profile-name-error' : ''}"
              />
              ${
                state.nameError
                  ? `<p id="profile-name-error" class="field-error" role="alert">${escapeHtml(state.nameError)}</p>`
                  : ''
              }
            </div>

            <h3 class="profile-avatar-heading">Choose your avatar</h3>
            <p class="field-hint">Current: ${escapeHtml(getAvatarLabel(state.avatarId))}</p>
            ${renderAvatarGridHtml(state.avatarId, { escapeHtml })}

            ${state.error ? `<p class="profile-feedback profile-feedback-error" role="alert">${escapeHtml(state.error)}</p>` : ''}
            ${state.message ? `<p class="profile-feedback profile-feedback-success" role="status">${escapeHtml(state.message)}</p>` : ''}

            <button type="button" class="btn btn-primary btn-full btn-mt-lg" id="profile-save-btn" ${state.saving ? 'disabled' : ''}>
              ${state.saving ? 'Saving…' : 'Save Changes'}
            </button>
          </section>
        </div>

        <section class="panel-card profile-badges" aria-labelledby="badges-heading">
          <h2 id="badges-heading" class="section-title">Badges</h2>
          <div class="badge-empty" role="status">
            <span class="badge-empty-icon" aria-hidden="true">📦</span>
            <p class="profile-empty-state">No badges yet. Keep playing challenges to earn your first badge!</p>
          </div>
        </section>
      </div>
    `;

    const nameInput = container.querySelector('#profile-display-name');
    nameInput.addEventListener('input', (e) => {
      state.displayName = e.target.value;
      state.nameError = '';
      const title = container.querySelector('.profile-display-name');
      if (title) title.textContent = e.target.value.trim() || 'Detective';
    });

    bindAvatarGrid(
      container,
      () => state.avatarId,
      (id) => {
        state.avatarId = normalizeAvatarId(id);
        const hero = container.querySelector('.profile-hero-avatar');
        if (hero) hero.textContent = getAvatarEmoji(state.avatarId);
        const hint = container.querySelector('.field-hint');
        if (hint) hint.textContent = `Current: ${getAvatarLabel(state.avatarId)}`;
      },
    );

    container.querySelector('#profile-save-btn').addEventListener('click', async () => {
      const name = state.displayName.trim();
      if (name.length < 2) {
        state.nameError = 'Please enter a display name (at least 2 characters).';
        state.message = '';
        state.error = '';
        paint();
        return;
      }

      state.saving = true;
      state.error = '';
      state.message = '';
      state.nameError = '';
      paint();

      try {
        await api.updateProfile(userId, {
          displayName: name,
          avatarId: normalizeAvatarId(state.avatarId),
        });
        state.displayName = name;
        state.message = 'Profile saved.';
      } catch (err) {
        state.error = err.message || 'Could not save profile.';
      } finally {
        state.saving = false;
        paint();
      }
    });
  }

  paint();
}
