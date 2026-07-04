import { api, escapeHtml } from '../api.js';

export async function renderSelectUser(container) {
  container.innerHTML = '<div class="loading">Loading users...</div>';

  try {
    const response = await api.getUsers();
    const users = response.users || [];

    if (users.length === 0) {
      window.location.href = '/onboarding';
      return;
    }

    container.innerHTML = `
      <div class="container-narrow">
        <h1 class="page-title">Select Your Profile</h1>
        <div class="user-list">
          ${users.map(
            (user) => `
            <button 
              type="button" 
              class="user-card" 
              data-user-id="${user.id}"
            >
              <span class="user-icon">👤</span>
              <span class="user-name">${escapeHtml(user.username)}</span>
            </button>
          `
          ).join('')}
        </div>
        <button type="button" class="btn btn-outline btn-full btn-mt-lg" id="create-new-btn">
          Create New User
        </button>
      </div>
    `;

    container.querySelectorAll('[data-user-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const userId = btn.dataset.userId;
        window.location.href = `/challenge-staging?userId=${userId}`;
      });
    });

    container.querySelector('#create-new-btn').addEventListener('click', () => {
      window.location.href = '/onboarding';
    });
  } catch (err) {
    console.error('Error loading users:', err);
    container.innerHTML = `
      <div class="container-narrow">
        <h1 class="page-title">Error</h1>
        <p>Could not load users. <a href="/" data-link>Go back</a></p>
      </div>
    `;
  }
}

