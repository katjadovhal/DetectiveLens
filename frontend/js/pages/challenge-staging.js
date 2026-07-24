import { api, escapeHtml } from '../api.js';
import { getAvatarMarkup } from '../avatars.js';
import { setLastUserId } from '../session.js';
import { getProgressSummary, renderXpBarHtml } from '../xp.js';

export async function renderChallengeStaging(container, userId) {
  container.innerHTML = '<div class="loading">Loading...</div>';
  setLastUserId(userId);

  try {
    const [homeData, profileData, dailyData] = await Promise.all([
      api.getHome(userId),
      api.getProfile(userId),
      api.getDailyChallenge(userId),
    ]);

    const greeting = homeData.greeting || {};
    const progress = getProgressSummary({
      profile: profileData.profile,
      home: homeData,
    });
    const dailyCompleted = dailyData.completed || false;

    container.innerHTML = `
      <div class="page-shell stack-lg">
        <div class="card card-greeting">
          <div class="avatar-large" aria-hidden="true">${getAvatarMarkup(greeting.avatarId || profileData.profile?.avatarId, { className: 'avatar-img avatar-img--large' })}</div>
          <div>
            <h1 class="page-title">Hi, ${escapeHtml(greeting.displayName)}!</h1>
            <p class="text-primary" style="margin-top: 0.5rem; font-size: 1.5rem; font-weight: 700;">
              ${escapeHtml(progress.levelTitle)}
            </p>
          </div>
        </div>

        ${renderXpBarHtml({ ...progress, label: 'Progress' })}

        <div class="grid-2">
          <div class="card ${dailyCompleted ? 'card-completed' : 'card-highlight'}">
            <h2 class="section-title">Daily Challenge</h2>
            ${dailyCompleted ? `
              <p style="margin-top: 0.75rem; font-size: 1.125rem; color: var(--color-text);">
                ✓ Challenge completed today!
              </p>
              <p class="text-muted" style="margin-top: 0.5rem">Come back tomorrow for a new challenge.</p>
              <button type="button" class="btn btn-secondary btn-mt-lg" id="share-btn">
                Share Challenge
              </button>
            ` : `
              <p style="margin-top: 0.75rem; font-size: 1.25rem; color: var(--color-text);">
                Spot the fake post
              </p>
              <p class="text-muted" style="margin-top: 0.5rem">+100 XP</p>
              <button type="button" class="btn btn-primary btn-mt-lg" id="daily-btn">
                Daily Challenge
              </button>
            `}
          </div>
          <div class="card">
            <h2 class="section-title-sm">Practice Mode</h2>
            <p class="text-muted" style="margin-top: 0.75rem; font-size: 1.125rem;">
              Improve your detective skills
            </p>
            <button type="button" class="btn btn-secondary btn-mt-md" id="practice-btn">
              Start Practice
            </button>
          </div>
        </div>
      </div>
    `;

    const dailyBtn = container.querySelector('#daily-btn');
    const shareBtn = container.querySelector('#share-btn');
    const practiceBtn = container.querySelector('#practice-btn');

    if (dailyBtn) {
      dailyBtn.addEventListener('click', async () => {
        try {
          if (dailyData.challenge) {
            window.location.href = `/challenges/fake-post/${dailyData.challenge.id}?userId=${userId}&mode=daily`;
          }
        } catch (err) {
          console.error('Error loading daily challenge:', err);
          alert('Could not load daily challenge');
        }
      });
    }

    if (shareBtn) {
      shareBtn.addEventListener('click', () => {
        const shareUrl = `https://detectivelens.app/challenge/${dailyData.challenge?.id}?shared=true`;
        alert(`Share this challenge with a friend:\n\n${shareUrl}`);
      });
    }

    if (practiceBtn) {
      practiceBtn.addEventListener('click', async () => {
        try {
          const practiceData = await api.getNextPracticeChallenge(userId);
          if (practiceData.challenge) {
            window.location.href = `/challenges/fake-post/${practiceData.challenge.id}?userId=${userId}&mode=practice`;
          } else {
            alert(practiceData.message || 'No more challenges available');
          }
        } catch (err) {
          console.error('Error loading practice challenge:', err);
          alert('Could not load practice challenge');
        }
      });
    }
  } catch (err) {
    console.error('Error loading challenge staging:', err);
    container.innerHTML = `
      <div class="container-narrow">
        <h1 class="page-title">Error</h1>
        <p>Could not load data. <a href="/" data-link>Go back</a></p>
      </div>
    `;
  }
}

