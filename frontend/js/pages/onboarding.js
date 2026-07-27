import { api, escapeHtml } from '../api.js';
import {
  AVATARS,
  renderAvatarGridHtml,
  bindAvatarGrid,
  normalizeAvatarId,
} from '../avatars.js';
import { setLastUserId } from '../session.js';

const NAME_MIN = 2;
const NAME_MAX = 50;
const AGE_MIN = 5;
const AGE_MAX = 99;

function ageOptionsHtml(selectedAge) {
  const options = ['<option value="">Select age</option>'];
  for (let age = AGE_MIN; age <= AGE_MAX; age += 1) {
    const selected = String(selectedAge) === String(age) ? ' selected' : '';
    options.push(`<option value="${age}"${selected}>${age}</option>`);
  }
  return options.join('');
}

export async function renderOnboarding(container) {
  const state = {
    username: '',
    age: '',
    colorBlindness: false,
    readingConfirmed: false,
    avatarId: AVATARS[0].id,
    submitting: false,
    errors: {},
  };

  function needsReadingConfirmation() {
    const age = parseInt(state.age, 10);
    return Number.isFinite(age) && age < 7;
  }

  function validate() {
    const errors = {};
    const name = state.username.trim();
    if (!name) {
      errors.username = 'Please enter a display name.';
    } else if (name.length < NAME_MIN) {
      errors.username = `Name must be at least ${NAME_MIN} characters.`;
    } else if (name.length > NAME_MAX) {
      errors.username = `Name must be at most ${NAME_MAX} characters.`;
    }

    const age = parseInt(state.age, 10);
    if (state.age === '' || Number.isNaN(age)) {
      errors.age = 'Please select your age.';
    } else if (age < AGE_MIN || age > AGE_MAX) {
      errors.age = `Age must be between ${AGE_MIN} and ${AGE_MAX}.`;
    } else if (age < 7 && !state.readingConfirmed) {
      errors.reading = 'Please confirm that you can read or have help.';
    }

    state.errors = errors;
    return Object.keys(errors).length === 0;
  }

  function isFormReady() {
    const name = state.username.trim();
    const age = parseInt(state.age, 10);
    if (name.length < NAME_MIN || name.length > NAME_MAX) return false;
    if (!Number.isFinite(age) || age < AGE_MIN || age > AGE_MAX) return false;
    if (age < 7 && !state.readingConfirmed) return false;
    return true;
  }

  function paint() {
    const ready = isFormReady();
    const showReading = needsReadingConfirmation();

    container.innerHTML = `
      <div class="page-shell page-shell-centered">
        <section class="create-card panel-card" aria-labelledby="create-heading">
          <h1 id="create-heading" class="page-title">Create Your Profile</h1>
          <p class="page-subtitle">Tell us a bit about yourself and pick your detective avatar.</p>

          <div class="create-layout">
            <div class="create-form-col">
              <div class="field">
                <label for="username">Display Name</label>
                <input
                  type="text"
                  id="username"
                  class="form-input${state.errors.username ? ' input-invalid' : ''}"
                  placeholder="Enter your name"
                  value="${escapeHtml(state.username)}"
                  maxlength="${NAME_MAX}"
                  autocomplete="nickname"
                  aria-invalid="${state.errors.username ? 'true' : 'false'}"
                  aria-describedby="${state.errors.username ? 'username-error' : 'username-hint'}"
                />
                <p id="username-hint" class="field-hint">At least ${NAME_MIN} characters.</p>
                ${
                  state.errors.username
                    ? `<p id="username-error" class="field-error" role="alert">${escapeHtml(state.errors.username)}</p>`
                    : ''
                }
              </div>

              <div class="field">
                <label for="age">How old are you?</label>
                <select
                  id="age"
                  class="form-input form-select${state.errors.age ? ' input-invalid' : ''}"
                  aria-invalid="${state.errors.age ? 'true' : 'false'}"
                  aria-describedby="${state.errors.age ? 'age-error' : ''}"
                >
                  ${ageOptionsHtml(state.age)}
                </select>
                ${
                  state.errors.age
                    ? `<p id="age-error" class="field-error" role="alert">${escapeHtml(state.errors.age)}</p>`
                    : ''
                }
              </div>

              <label class="switch-check">
                <input type="checkbox" id="colorBlindness" ${state.colorBlindness ? 'checked' : ''} />
                <span class="switch-ui" aria-hidden="true"></span>
                <span class="switch-copy">
                  <span class="switch-title">I have color blindness</span>
                  <span class="switch-hint">We'll adjust some colors to make things easier to see.</span>
                </span>
              </label>

              ${
                showReading
                  ? `
                <label class="switch-check${state.errors.reading ? ' switch-invalid' : ''}">
                  <input type="checkbox" id="reading-confirm-check" ${state.readingConfirmed ? 'checked' : ''} />
                  <span class="switch-ui" aria-hidden="true"></span>
                  <span class="switch-copy">
                    <span class="switch-title">I can read by myself, or someone is helping me</span>
                  </span>
                </label>
                ${
                  state.errors.reading
                    ? `<p class="field-error" role="alert">${escapeHtml(state.errors.reading)}</p>`
                    : ''
                }
              `
                  : ''
              }
            </div>

            <div class="create-avatar-col">
              <h2 class="section-title">Choose Your Avatar</h2>
              <p class="field-hint">Dog and Cat unlock later with XP — you can change this in Profile.</p>
              ${renderAvatarGridHtml(state.avatarId, { escapeHtml, totalXp: 0 })}
            </div>
          </div>

          <button
            type="button"
            class="btn btn-primary btn-full btn-mt-lg"
            id="complete-btn"
            ${!ready || state.submitting ? 'disabled' : ''}
          >
            ${state.submitting ? 'Creating…' : 'Create Profile'}
          </button>
          <p class="create-footnote">You can change this later in your profile.</p>
        </section>
      </div>
    `;

    const usernameInput = container.querySelector('#username');
    const ageInput = container.querySelector('#age');
    const colorBlindnessCheck = container.querySelector('#colorBlindness');
    const readingConfirmCheck = container.querySelector('#reading-confirm-check');
    const completeBtn = container.querySelector('#complete-btn');

    usernameInput.addEventListener('input', (e) => {
      state.username = e.target.value;
      delete state.errors.username;
      updateReadyState();
    });

    ageInput.addEventListener('change', (e) => {
      const previousShow = showReading;
      state.age = e.target.value;
      delete state.errors.age;
      delete state.errors.reading;
      if (previousShow !== needsReadingConfirmation()) {
        paint();
      } else {
        updateReadyState();
      }
    });

    colorBlindnessCheck.addEventListener('change', (e) => {
      state.colorBlindness = e.target.checked;
    });

    if (readingConfirmCheck) {
      readingConfirmCheck.addEventListener('change', (e) => {
        state.readingConfirmed = e.target.checked;
        delete state.errors.reading;
        updateReadyState();
      });
    }

    bindAvatarGrid(
      container,
      () => state.avatarId,
      (id) => {
        state.avatarId = normalizeAvatarId(id);
      },
      { totalXp: 0 },
    );

    completeBtn.addEventListener('click', submit);

    function updateReadyState() {
      const btn = container.querySelector('#complete-btn');
      if (btn) btn.disabled = !isFormReady() || state.submitting;
    }
  }

  async function submit() {
    if (!validate()) {
      paint();
      return;
    }

    state.submitting = true;
    paint();

    try {
      const response = await api.createUser({
        username: state.username.trim(),
        age: parseInt(state.age, 10),
        colorBlindness: state.colorBlindness,
        avatarId: normalizeAvatarId(state.avatarId),
      });
      if (response.success && response.userId) {
        setLastUserId(response.userId);
        window.location.href = `/challenge-staging?userId=${encodeURIComponent(response.userId)}`;
        return;
      }
      state.errors.username = 'Could not create profile. Try another name.';
    } catch (err) {
      console.error('Error creating user:', err);
      state.errors.username = err.message || 'Could not create profile.';
    }

    state.submitting = false;
    paint();
  }

  paint();
}
