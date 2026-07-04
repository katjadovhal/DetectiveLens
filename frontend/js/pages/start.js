import { api, escapeHtml } from '../api.js';

export async function renderStart(container) {
  container.innerHTML = '<div class="loading">Loading...</div>';

  try {
    const welcome = await api.getWelcome();

    // Try to show a quick level summary if there is at least one user
    let levelHtml = '';
    try {
      const usersResp = await api.getUsers();
      const firstUser = usersResp.users && usersResp.users[0];
      if (firstUser) {
        const home = await api.getHome(firstUser.id);
        const name = home.greeting?.displayName || firstUser.username || '';
        const levelTitle = home.greeting?.levelTitle || '';
        const totalXp = home.progress?.totalXp ?? 0;
        levelHtml = `
          <div class="level-banner">
            <div class="avatar-small">🕵️</div>
            <div>
              <div class="level-text">Hi, ${escapeHtml(name)} — ${escapeHtml(levelTitle)}</div>
              <div class="level-sub">You have ${totalXp} points</div>
            </div>
          </div>
        `;
      }
    } catch (e) {
      // ignore errors, show generic welcome
    }

    container.innerHTML = `
      <div class="welcome-page">
        <div class="container-narrow">
          <h1 class="page-title">${escapeHtml(welcome.title)}</h1>
          <p class="page-subtitle">${escapeHtml(welcome.subtitle)}</p>
          <div class="welcome-hero" role="img" aria-label="Detective character">🕵️‍♂️</div>
          ${levelHtml}
          <div class="welcome-panel">
            <div class="selection-list">
              <button type="button" class="selection-card btn-large" id="create-user-btn">
                <span class="selection-icon">➕</span>
                <span class="selection-label">Create New User</span>
              </button>
              <button type="button" class="selection-card btn-large" id="existing-user-btn">
                <span class="selection-icon">👤</span>
                <span class="selection-label">Proceed as Existing User</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    container.querySelector('#create-user-btn').addEventListener('click', () => {
      window.location.href = '/onboarding';
    });

    container.querySelector('#existing-user-btn').addEventListener('click', async () => {
      try {
        const response = await api.getUsers();
        if (response.users && response.users.length > 0) {
          // Redirect to user selection page
          window.location.href = '/select-user';
        } else {
          // No users, redirect to create new user
          window.location.href = '/onboarding';
        }
      } catch {
        window.location.href = '/onboarding';
      }
    });
  } catch (err) {
    console.error('Error loading start page:', err);
    container.innerHTML = '<div class="error">Error loading page</div>';
  }
}

