import { api, escapeHtml } from '../api.js';

const AVATARS = [
  { id: 'avatar-detective-1', label: 'Detective 1', emoji: '🕵️‍♂️' },
  { id: 'avatar-detective-2', label: 'Detective 2', emoji: '🕵️‍♀️' },
  { id: 'avatar-detective-3', label: 'Detective 3', emoji: '👨‍🔬' },
  { id: 'avatar-detective-4', label: 'Detective 4', emoji: '👩‍🔬' },
];

export async function renderOnboarding(container) {
  container.innerHTML = '<div class="loading">Loading...</div>';

  const state = {
    step: 1, // 1: form + reading statement, 2: avatar selection
    username: '',
    age: '',
    colorBlindness: false,
    readingConfirmed: false,
    avatarId: AVATARS[0].id,
  };

  function renderForm() {
    const needsReadingConfirmation = parseInt(state.age) < 7 && state.age;
    
    return `
      <div class="container-narrow">
        <h1 class="page-title">Create Your Profile</h1>
        <div class="onboarding-form">
          <div class="form-group">
            <label for="username">Your Name:</label>
            <input 
              type="text" 
              id="username" 
              class="form-input" 
              placeholder="Enter your name"
              value="${escapeHtml(state.username)}"
              maxlength="50"
            />
          </div>

          <div class="form-group">
            <label for="age">How old are you?</label>
            <input 
              type="number" 
              id="age" 
              class="form-input" 
              placeholder="Enter your age"
              value="${state.age}"
              min="1"
              max="120"
            />
          </div>

          <div class="form-group checkbox">
            <input 
              type="checkbox" 
              id="colorBlindness" 
              ${state.colorBlindness ? 'checked' : ''}
            />
            <label for="colorBlindness">I have color blindness</label>
          </div>

          ${needsReadingConfirmation ? `
            <div class="form-group reading-confirmation">
              <p style="margin-bottom: 1rem; font-weight: 600;">Yes, I can read by myself, or someone is here to help me read.</p>
              <div class="checkbox-large">
                <input 
                  type="checkbox" 
                  id="reading-confirm-check"
                  ${state.readingConfirmed ? 'checked' : ''}
                />
                <label for="reading-confirm-check">I confirm this statement</label>
              </div>
            </div>
          ` : ''}

          <button type="button" class="btn btn-primary btn-full" id="next-btn">
            Next
          </button>
        </div>
      </div>
    `;
  }

  function renderAvatarSelection() {
    return `
      <div class="container-narrow">
        <h1 class="page-title">Choose Your Avatar</h1>
        <p class="page-subtitle">Pick which detective you want to be!</p>
        <div class="avatar-grid">
          ${AVATARS.map(
            (avatar) => `
            <button 
              type="button" 
              class="avatar-card ${avatar.id === state.avatarId ? 'selected' : ''}" 
              data-avatar-id="${avatar.id}"
            >
              <div class="avatar-emoji">${avatar.emoji}</div>
              <div class="avatar-label">${escapeHtml(avatar.label)}</div>
            </button>
          `
          ).join('')}
        </div>
        <button type="button" class="btn btn-primary btn-full btn-mt-lg" id="complete-btn">
          Complete
        </button>
      </div>
    `;
  }

  function paint() {
    if (state.step === 1) {
      container.innerHTML = renderForm();
      bindFormEvents();
    } else if (state.step === 2) {
      container.innerHTML = renderAvatarSelection();
      bindAvatarEvents();
    }
  }

  function bindFormEvents() {
    const usernameInput = container.querySelector('#username');
    const ageInput = container.querySelector('#age');
    const colorBlindnessCheck = container.querySelector('#colorBlindness');
    const readingConfirmCheck = container.querySelector('#reading-confirm-check');
    const nextBtn = container.querySelector('#next-btn');

    usernameInput.addEventListener('input', (e) => {
      state.username = e.target.value;
    });

    ageInput.addEventListener('input', (e) => {
      state.age = e.target.value;
      paint(); // Rerender to show/hide reading confirmation
    });

    colorBlindnessCheck.addEventListener('change', (e) => {
      state.colorBlindness = e.target.checked;
    });

    if (readingConfirmCheck) {
      readingConfirmCheck.addEventListener('change', (e) => {
        state.readingConfirmed = e.target.checked;
      });
    }

    nextBtn.addEventListener('click', () => {
      if (!state.username.trim()) {
        alert('Please enter your name');
        return;
      }
      if (!state.age || state.age < 1) {
        alert('Please enter a valid age');
        return;
      }

      const needsReadingConfirmation = parseInt(state.age) < 7;
      if (needsReadingConfirmation && !state.readingConfirmed) {
        alert('Please confirm the reading statement');
        return;
      }

      state.step = 2; // Go to avatar selection
      paint();
    });
  }

  function bindAvatarEvents() {
    container.querySelectorAll('[data-avatar-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.avatarId = btn.dataset.avatarId;
        container.querySelectorAll('.avatar-card').forEach((card) => {
          card.classList.toggle('selected', card.dataset.avatarId === state.avatarId);
        });
      });
    });

    container.querySelector('#complete-btn').addEventListener('click', submitOnboarding);
  }

  async function submitOnboarding() {
    try {
      const response = await api.createUser({
        username: state.username,
        age: parseInt(state.age),
        colorBlindness: state.colorBlindness,
        avatarId: state.avatarId,
      });
      if (response.success && response.userId) {
        window.location.href = `/challenge-staging?userId=${response.userId}`;
      }
    } catch (err) {
      console.error('Error creating user:', err);
      alert('Error creating user: ' + err.message);
    }
  }

  paint();
}

