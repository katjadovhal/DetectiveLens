import { api, escapeHtml } from '../api.js';

export async function renderHome(container) {
  container.innerHTML = '<div class="loading">Loading dashboard...</div>';

  const home = await api.getHome();
  const xpMax = home.progress.totalXp + home.progress.xpToNextLevel;
  const pct = Math.min(100, Math.round((home.progress.totalXp / xpMax) * 100));

  container.innerHTML = `
    <div class="container-wide stack-lg">
      <div class="card card-greeting">
        <div class="avatar-large">🕵️</div>
        <div>
          <h1 class="page-title">Hi, ${escapeHtml(home.greeting.displayName)}!</h1>
          <p class="text-primary" style="margin-top: 0.5rem; font-size: 1.5rem; font-weight: 700;">
            ${escapeHtml(home.greeting.levelTitle)}
          </p>
        </div>
      </div>

      <div class="progress-wrap">
        <div class="progress-label">
          <span>Progress</span>
          <span>${home.progress.totalXp}/${xpMax} Points</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${pct}%"></div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card card-highlight">
          <h2 class="section-title">${escapeHtml(home.dailyMission.title)}</h2>
          <p style="margin-top: 0.75rem; font-size: 1.5rem; font-weight: 700; color: var(--color-gray-800);">
            ${escapeHtml(home.dailyMission.description)}
          </p>
          <p class="text-muted" style="margin-top: 0.5rem">+${home.dailyMission.xpBonus} Points</p>
          <a href="/challenges/fake-post/${escapeHtml(home.dailyMission.challengeId)}" data-link>
            <button type="button" class="btn btn-secondary btn-mt-lg">Play</button>
          </a>
        </div>
        ${
          home.continueLearning.challengeId
            ? `
        <div class="card">
          <h2 class="section-title-sm">Continue Learning</h2>
          <p class="text-muted" style="margin-top: 0.75rem; font-size: 1.25rem;">
            ${escapeHtml(home.continueLearning.title)}
          </p>
          <a href="/challenges/fake-post/${escapeHtml(home.continueLearning.challengeId)}" data-link>
            <button type="button" class="btn btn-outline btn-mt-md">Resume</button>
          </a>
        </div>`
            : ''
        }
      </div>
    </div>
  `;
}
