import { api, escapeHtml } from '../api.js';
import { getAvatarMarkup } from '../avatars.js';
import { setLastUserId, withUserId } from '../session.js';
import { getProgressSummary, renderXpBarHtml } from '../xp.js';
import { triggerLevelUpAnimation } from '../animations.js';
import { openShareModal } from '../share-modal.js';

function isAllChallengesCompleted(completion) {
  return completion?.allChallengesCompleted === true;
}

function renderCompletionBanner(userId) {
  const hqHref = withUserId('/detective-hq', userId);
  return `
    <section class="completion-banner" aria-labelledby="completion-banner-heading">
      <span class="completion-banner-icon" aria-hidden="true">🎉</span>
      <div class="completion-banner-copy">
        <h2 id="completion-banner-heading" class="completion-banner-title">Congratulations!</h2>
        <p class="completion-banner-message">
          You have completed all challenges. Now head over to the Detective HQ to spend your XP!
        </p>
        <a href="${hqHref}" class="btn btn-primary" data-link id="completion-hq-btn">
          Go to Detective HQ
        </a>
      </div>
    </section>
  `;
}

function renderDailyCard({ allDone, dailyCompleted, dailyData }) {
  if (allDone) {
    return `
      <div class="card card-mode-locked" aria-labelledby="daily-mode-heading">
        <p class="mode-completed-icon" aria-hidden="true">✓</p>
        <h2 id="daily-mode-heading" class="section-title">Daily Challenge</h2>
        <p class="mode-locked-text">All daily challenges are complete.</p>
        <button type="button" class="btn btn-secondary btn-mt-lg" disabled aria-disabled="true">
          Completed
        </button>
      </div>
    `;
  }

  if (dailyCompleted) {
    return `
      <div class="card card-completed">
        <h2 class="section-title">Daily Challenge</h2>
        <p style="margin-top: 0.75rem; font-size: 1.125rem; color: var(--color-text);">
          ✓ Challenge completed today!
        </p>
        <p class="text-muted" style="margin-top: 0.5rem">Come back tomorrow for a new challenge.</p>
        <button type="button" class="btn btn-secondary btn-mt-lg" id="share-btn">
          Share Challenge
        </button>
      </div>
    `;
  }

  return `
    <div class="card card-highlight">
      <h2 class="section-title">Daily Challenge</h2>
      <p style="margin-top: 0.75rem; font-size: 1.25rem; color: var(--color-text);">
        Spot the fake post
      </p>
      <p class="text-muted" style="margin-top: 0.5rem">+100 XP</p>
      <button type="button" class="btn btn-primary btn-mt-lg" id="daily-btn" ${dailyData?.challenge ? '' : 'disabled'}>
        Daily Challenge
      </button>
    </div>
  `;
}

function renderPracticeCard(allDone) {
  if (allDone) {
    return `
      <div class="card card-mode-locked" aria-labelledby="practice-mode-heading">
        <p class="mode-completed-icon" aria-hidden="true">✓</p>
        <h2 id="practice-mode-heading" class="section-title-sm">Practice Mode</h2>
        <p class="mode-locked-text">All practice challenges are complete.</p>
        <button type="button" class="btn btn-secondary btn-mt-md" disabled aria-disabled="true">
          Completed
        </button>
      </div>
    `;
  }

  return `
    <div class="card">
      <h2 class="section-title-sm">Practice Mode</h2>
      <p class="text-muted" style="margin-top: 0.75rem; font-size: 1.125rem;">
        Improve your detective skills
      </p>
      <button type="button" class="btn btn-secondary btn-mt-md" id="practice-btn">
        Start Practice
      </button>
    </div>
  `;
}

export async function renderChallengeStaging(container, userId) {
  container.innerHTML = '<div class="loading">Loading...</div>';
  setLastUserId(userId);

  try {
    const [homeData, profileData] = await Promise.all([
      api.getHome(userId),
      api.getProfile(userId),
    ]);

    const completion = homeData.challengeCompletion || null;
    const allDone = isAllChallengesCompleted(completion);

    let dailyData = { challenge: null, completed: false };
    if (!allDone) {
      try {
        dailyData = await api.getDailyChallenge(userId);
        if (dailyData?.status === 'all_challenges_completed') {
          dailyData = { challenge: null, completed: false, status: dailyData.status };
        }
      } catch (err) {
        console.error('Error loading daily challenge:', err);
        throw err;
      }
    }

    const greeting = homeData.greeting || {};
    const progress = getProgressSummary({
      profile: profileData.profile,
      home: homeData,
    });
    const dailyCompleted = Boolean(dailyData.completed);

    const url = new URL(window.location.href);
    const shouldCelebrateFromQuery = url.searchParams.get('levelUp') === '1';
    const levelStorageKey = `level-last-seen:${userId}`;
    const lastSeenLevelRaw = window.sessionStorage.getItem(levelStorageKey);
    const lastSeenLevel = Number(lastSeenLevelRaw);
    const shouldCelebrateFromLevelDelta = Number.isFinite(lastSeenLevel)
      ? progress.level > lastSeenLevel
      : false;
    const shouldCelebrateLevelUp = shouldCelebrateFromQuery || shouldCelebrateFromLevelDelta;

    window.sessionStorage.setItem(levelStorageKey, String(progress.level));

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

        ${allDone ? renderCompletionBanner(userId) : ''}

        <div class="grid-2">
          ${renderDailyCard({ allDone, dailyCompleted, dailyData })}
          ${renderPracticeCard(allDone)}
        </div>
      </div>
    `;

    if (shouldCelebrateLevelUp) {
      setTimeout(() => {
        triggerLevelUpAnimation();
      }, 300);

      url.searchParams.delete('levelUp');
      window.history.replaceState({}, '', `${url.pathname}${url.search}`);
    }

    if (allDone) {
      return;
    }

    const dailyBtn = container.querySelector('#daily-btn');
    const shareBtn = container.querySelector('#share-btn');
    const practiceBtn = container.querySelector('#practice-btn');

    if (dailyBtn) {
      dailyBtn.addEventListener('click', async () => {
        try {
          if (isAllChallengesCompleted((await api.getHome(userId)).challengeCompletion)) {
            window.location.href = withUserId('/challenge-staging', userId);
            return;
          }
          const latestDaily = await api.getDailyChallenge(userId);
          if (latestDaily?.status === 'all_challenges_completed') {
            window.location.href = withUserId(
              latestDaily.nextRoute || '/challenge-staging',
              userId,
            );
            return;
          }
          if (latestDaily.challenge?.id) {
            window.location.href = `/challenges/fake-post/${latestDaily.challenge.id}?userId=${userId}&mode=daily`;
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
        openShareModal(shareUrl);
      });
    }

    if (practiceBtn) {
      practiceBtn.addEventListener('click', async () => {
        try {
          if (isAllChallengesCompleted((await api.getHome(userId)).challengeCompletion)) {
            window.location.href = withUserId('/challenge-staging', userId);
            return;
          }
          const practiceData = await api.getNextPracticeChallenge(userId);
          if (practiceData?.status === 'all_challenges_completed') {
            window.location.href = withUserId(
              practiceData.nextRoute || '/challenge-staging',
              userId,
            );
            return;
          }
          if (practiceData.challenge?.id) {
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
