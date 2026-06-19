import { api, escapeHtml } from '../api.js';

const LEVELS = [
  { level: 'beginner', label: 'Beginner', icon: '⭐' },
  { level: 'somewhat', label: 'Somewhat', icon: '😊' },
  { level: 'pro', label: 'Pro', icon: '🚀' },
];

export async function renderWelcome(container) {
  container.innerHTML = '<div class="loading">Loading...</div>';

  const welcome = await api.getWelcome();
  let selected = 'beginner';

  container.innerHTML = `
    <div class="welcome-page">
      <div class="container-narrow">
        <h1 class="page-title">${escapeHtml(welcome.title)}</h1>
        <p class="page-subtitle">${escapeHtml(welcome.subtitle)}</p>
        <div class="welcome-hero" role="img" aria-label="Detective character">🕵️‍♂️</div>
        <div class="welcome-panel">
          <div class="selection-list" id="level-list">
            ${LEVELS.map(
              (item) => `
              <button type="button" class="selection-card ${item.level === selected ? 'selected' : ''}" data-level="${item.level}">
                <span class="selection-icon">${item.icon}</span>
                <span class="selection-label">${escapeHtml(item.label)}</span>
              </button>
            `,
            ).join('')}
          </div>
          <button type="button" class="btn btn-primary btn-full btn-mt-lg" id="start-btn">Let's Go!</button>
        </div>
      </div>
    </div>
  `;

  container.querySelectorAll('[data-level]').forEach((btn) => {
    btn.addEventListener('click', () => {
      selected = btn.dataset.level;
      container.querySelectorAll('.selection-card').forEach((card) => {
        card.classList.toggle('selected', card.dataset.level === selected);
      });
    });
  });

  container.querySelector('#start-btn').addEventListener('click', async () => {
    const startBtn = container.querySelector('#start-btn');
    startBtn.disabled = true;
    startBtn.textContent = 'Loading...';
    try {
      await api.completeOnboarding(selected);
    } catch {
      /* continue to home */
    }
    window.location.href = '/';
  });
}
