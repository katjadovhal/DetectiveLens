import { api, escapeHtml } from '../api.js';
import { adaptiveMessageClass } from '../adaptive-presentation.js';
import { setLastUserId, withUserId } from '../session.js';
import { openShareModal } from '../share-modal.js';
import { showToast, toastMessageForBadges } from '../toast.js';
import { ingestBadgeUnlockNotifications } from '../header.js';

function renderSocialPost(post, selected, disabled) {
  return `
    <button type="button" class="social-post ${selected ? 'selected' : ''}" data-post-id="${post.id}" ${disabled ? 'disabled' : ''}>
      <span class="post-badge">${escapeHtml(post.id)}</span>
      ${post.imageUrl ? `<img class="post-image" src="${post.imageUrl}" alt="Image ${escapeHtml(post.id)}">` : ''}
      ${post.text ? `<p class="post-text">${escapeHtml(post.text)}</p>` : ''}
    </button>
  `;
}

function renderClueCard(clueState) {
  if (!clueState.first && clueState.status !== 'loading_first') return '';

  const active = clueState.stronger || clueState.first;
  const showStrongerBtn =
    clueState.first &&
    !clueState.strongerUsed &&
    clueState.status !== 'loading_stronger';

  const text =
    clueState.status === 'loading_stronger' && clueState.stronger
      ? `${escapeHtml(clueState.first.text)} ${escapeHtml(clueState.stronger.text)}`
      : clueState.stronger
        ? escapeHtml(clueState.stronger.text)
        : escapeHtml(clueState.first?.text || '');

  const presentationClass = adaptiveMessageClass(active?.presentation);

  return `
    <div class="detective-clue-card ${presentationClass}" role="region" aria-label="Detective clue">
      <h2 class="detective-clue-title">${escapeHtml(clueState.first?.title || 'Detective Clue')}</h2>
      <p class="detective-clue-text">${text}</p>
      ${
        showStrongerBtn
          ? `<button type="button" class="btn btn-outline" id="stronger-clue-btn" aria-label="Show a stronger detective clue">Show a stronger clue</button>`
          : ''
      }
    </div>
  `;
}

function renderInvestigationPanel(clueState) {
  const loading = clueState.status === 'loading_first' || clueState.status === 'loading_stronger';
  const showButton = !clueState.first && clueState.status !== 'loading_first';

  return `
    <div class="investigation-panel">
      <div id="clue-live" class="sr-only" aria-live="polite">${loading ? 'Loading detective clue…' : ''}</div>
      ${
        showButton
          ? `<button type="button" class="btn btn-outline" id="show-clue-btn" aria-label="Show a detective clue">Show a detective clue</button>`
          : ''
      }
      ${renderClueCard(clueState)}
      ${
        clueState.error
          ? `<p class="detective-clue-error" role="alert">${escapeHtml(clueState.error)}</p>
             <button type="button" class="btn btn-outline" id="retry-clue-btn">Try again</button>`
          : ''
      }
    </div>
  `;
}

function renderExplanationCard(explanation, loading) {
  if (loading) {
    return `<p class="explanation-loading" aria-live="polite">Loading explanation…</p>`;
  }
  if (!explanation) return '';
  const checklist =
    explanation.checklist?.length
      ? `<ul class="explanation-checklist">${explanation.checklist
          .map((item) => `<li>${escapeHtml(item)}</li>`)
          .join('')}</ul>`
      : '';
  const presentationClass = adaptiveMessageClass(explanation.presentation);
  return `
    <div class="explanation-card ${presentationClass}" role="region" aria-label="Why explanation">
      <h3 class="explanation-card-title">${escapeHtml(explanation.title || 'Why?')}</h3>
      <p class="explanation-card-text">${escapeHtml(explanation.text)}</p>
      ${checklist}
    </div>
  `;
}

function renderDetectiveTipBlock(tip, loading) {
  if (loading) {
    return `<p class="tip-loading" aria-live="polite">Loading detective tip…</p>`;
  }
  if (!tip) return '';

  const message = tip.message || tip.text;
  const checklist = tip.checklist || [];
  if (!message) return '';

  const presentationClass = adaptiveMessageClass(tip.presentation);

  return `
    <div class="tip-box ${presentationClass}">
      <span class="tip-icon" role="img" aria-label="Detective mascot">🐕</span>
      <div>
        <p class="tip-message">${escapeHtml(message)}</p>
        ${
          checklist.length
            ? `
          <p class="tip-checklist-label">Next time, remember to:</p>
          <ul class="tip-checklist">
            ${checklist.map((item) => `<li><span class="check-icon" aria-hidden="true">✓</span>${escapeHtml(item)}</li>`).join('')}
          </ul>`
            : ''
        }
      </div>
    </div>
  `;
}

function renderPracticeRecommendation(tip, userId) {
  const practice = tip?.practiceRecommendation || tip;
  const challengeId = practice?.recommendedChallengeId || tip?.recommendedChallengeId;
  if (!challengeId) return '';
  const href = withUserId(`/challenges/fake-post/${challengeId}`, userId);
  const text = practice?.text || 'This is a useful next practice area.';
  const presentationClass = adaptiveMessageClass(practice?.presentation);
  return `
    <div class="practice-recommendation ${presentationClass}">
      <p class="practice-recommendation-text">${escapeHtml(text)}</p>
      <a href="${href}" class="btn btn-secondary" data-link id="practice-skill-btn">Practise this skill</a>
    </div>
  `;
}

function renderFeedback(result, feedbackState) {
  const explanationBlock = renderExplanationCard(
    feedbackState.explanationContent,
    feedbackState.explanationLoading,
  );

  if (result.isCorrect) {
    return `
      <div class="feedback">
        <p class="feedback-title">You picked ${escapeHtml(result.selectedAnswer)}! That's the fake post.</p>
        <p class="feedback-emoji">🎉 ⭐ 🎊</p>
      </div>
    `;
  }

  return `
    <div class="feedback">
      <p class="feedback-title">Not quite!</p>
      <p class="feedback-sub">You selected ${escapeHtml(result.selectedAnswer)} as the fake post!</p>
      <p class="feedback-sub">The correct answer was ${escapeHtml(result.correctAnswer)}.</p>
      <div class="feedback-actions">
        <button
          type="button"
          class="btn btn-outline"
          id="why-btn"
          aria-expanded="${feedbackState.showExplanation ? 'true' : 'false'}"
          aria-controls="why-explanation-region"
        >Show why</button>
      </div>
      <div id="why-explanation-region">${explanationBlock}</div>
    </div>
  `;
}

function renderPlaying(challenge, state) {
  const content = challenge.content;
  const mascotText =
    state.clue.first?.text || 'Compare both images carefully before you choose.';

  return `
    <div class="container">
      <div class="challenge-header">
        <h1 class="page-title">${escapeHtml(challenge.title)}</h1>
        <p class="page-subtitle">${escapeHtml(challenge.instruction)}</p>
      </div>
      <div class="post-grid" id="post-grid">
        ${content.posts.map((post) => renderSocialPost(post, state.selected === post.id, state.submitting)).join('')}
      </div>
      <div id="investigation-panel">${renderInvestigationPanel(state.clue)}</div>
      <div class="mascot-row">
        <span class="mascot-icon" aria-hidden="true">🐕</span>
        <div class="speech-bubble">${escapeHtml(mascotText)}</div>
      </div>
    </div>
  `;
}

function renderFeedbackView(result, feedbackState, userId, mode, challengeId) {
  const isDailyMode = mode === 'daily';
  const nextLabel = isDailyMode ? 'Continue' : 'Next Challenge';
  const tipContent = feedbackState.detectiveTipContent || result.detectiveTip;

  return `
    <div class="container">
      <div id="feedback-area">${renderFeedback(result, feedbackState)}</div>
      ${renderDetectiveTipBlock(tipContent, feedbackState.tipLoading)}
      ${renderPracticeRecommendation(feedbackState.detectiveTipContent || {}, userId)}
      ${
        isDailyMode && result.isCorrect
          ? `
        <div class="daily-completion-message">
          <p class="daily-completion-text">🎉 Great job! You've completed today's daily challenge!</p>
          <p class="text-muted">Come back tomorrow for a new challenge.</p>
        </div>`
          : ''
      }
      <div class="actions-right">
        <button type="button" class="btn btn-primary" id="next-challenge-btn" data-mode="${mode}" data-user-id="${userId}" data-challenge-id="${challengeId}">
          ${nextLabel} ${result.xpEarned > 0 ? `(+${result.xpEarned} XP)` : ''}
        </button>
        ${
          isDailyMode
            ? `<button type="button" class="btn btn-outline btn-mt-md" id="share-btn">Share Challenge</button>`
            : ''
        }
      </div>
    </div>
  `;
}

export async function renderChallenge(container, challengeId, userId, mode = 'practice') {
  container.innerHTML = '<div class="loading">Loading challenge...</div>';

  if (!userId) {
    container.innerHTML = '<div class="error">Error: No user ID provided</div>';
    return;
  }

  setLastUserId(userId);

  const id = challengeId || 'monkey-001';

  try {
    const [{ challenge }, start] = await Promise.all([
      api.getChallenge(id),
      api.startChallenge(id, userId),
    ]);

    const state = {
      sessionId: start.sessionId,
      selected: null,
      hintsUsed: 0,
      submitting: false,
      phase: 'playing',
      result: null,
      clue: {
        status: 'idle',
        first: null,
        stronger: null,
        strongerUsed: false,
        error: null,
        pendingStage: null,
      },
      feedback: {
        showExplanation: false,
        explanationContent: null,
        explanationLoading: false,
        detectiveTipContent: null,
        tipLoading: false,
      },
    };

    async function requestClue(stage) {
      state.clue.error = null;
      state.clue.pendingStage = stage;
      state.clue.status = stage === 'stronger_hint' ? 'loading_stronger' : 'loading_first';
      paint();

      try {
        const response = await api.requestHint(id, {
          userId,
          sessionId: state.sessionId,
          stage,
          locale: 'en',
        });

        if (stage === 'pre_answer_hint') {
          state.clue.first = response;
        } else {
          state.clue.stronger = response;
          state.clue.strongerUsed = true;
        }
        state.hintsUsed = stage === 'stronger_hint' ? 2 : 1;
        state.clue.status = stage === 'stronger_hint' ? 'stronger_visible' : 'first_visible';
      } catch (err) {
        state.clue.error = err.message || 'Could not load clue';
        state.clue.status = 'error';
      } finally {
        state.clue.pendingStage = null;
        paint();
      }
    }

    async function loadDetectiveTip() {
      if (!state.result || state.result.isCorrect) return;
      state.feedback.tipLoading = true;
      paint();
      try {
        state.feedback.detectiveTipContent = await api.requestHint(id, {
          userId,
          sessionId: state.sessionId,
          stage: 'detective_tip',
          locale: 'en',
        });
      } catch {
        state.feedback.detectiveTipContent = state.result.detectiveTip
          ? {
              text: state.result.detectiveTip.message,
              checklist: state.result.detectiveTip.checklist,
            }
          : null;
      } finally {
        state.feedback.tipLoading = false;
        paint();
      }
    }

    function paint() {
      if (state.phase === 'feedback' && state.result) {
        container.innerHTML = renderFeedbackView(
          state.result,
          state.feedback,
          userId,
          mode,
          id,
        );
        bindFeedbackEvents();
        return;
      }
      container.innerHTML = renderPlaying(challenge, state);
      bindPlayingEvents();
    }

    function bindPlayingEvents() {
      container.querySelectorAll('[data-post-id]').forEach((btn) => {
        btn.addEventListener('click', () => handleSubmit(btn.dataset.postId));
      });

      const showClueBtn = container.querySelector('#show-clue-btn');
      if (showClueBtn) {
        showClueBtn.addEventListener('click', () => requestClue('pre_answer_hint'));
      }

      const strongerBtn = container.querySelector('#stronger-clue-btn');
      if (strongerBtn) {
        strongerBtn.addEventListener('click', () => requestClue('stronger_hint'));
      }

      const retryBtn = container.querySelector('#retry-clue-btn');
      if (retryBtn) {
        retryBtn.addEventListener('click', () => {
          const stage = state.clue.pendingStage || (state.clue.first ? 'stronger_hint' : 'pre_answer_hint');
          requestClue(stage);
        });
      }
    }

    function bindFeedbackEvents() {
      const whyBtn = container.querySelector('#why-btn');
      if (whyBtn) {
        whyBtn.addEventListener('click', async () => {
          if (state.feedback.showExplanation && state.feedback.explanationContent) return;
          state.feedback.explanationLoading = true;
          paint();
          try {
            const response = await api.requestHint(id, {
              userId,
              sessionId: state.sessionId,
              stage: 'answer_explanation',
              locale: 'en',
            });
            state.feedback.explanationContent = response;
            state.feedback.showExplanation = true;
          } catch (err) {
            state.feedback.explanationContent = {
              title: 'Why?',
              text: (state.result.explanation || []).join(' '),
              checklist: [],
            };
            state.feedback.showExplanation = true;
          } finally {
            state.feedback.explanationLoading = false;
            paint();
          }
        });
      }

      const nextBtn = container.querySelector('#next-challenge-btn');
      const shareBtn = container.querySelector('#share-btn');

      if (shareBtn) {
        shareBtn.addEventListener('click', () => {
          const shareUrl = `https://detectivelens.app/challenge/${id}?shared=true`;
          //alert(`Share this challenge with a friend:\n\n${shareUrl}`);
          openShareModal(shareUrl, {
            onCopyAndClose: () => {
              const params = new URLSearchParams({ userId });
              window.location.href = `/challenge-staging?${params.toString()}`;
            },
          });
        });
      }

      if (nextBtn) {
        nextBtn.addEventListener('click', async () => {
          const nextUserId = nextBtn.dataset.userId;
          const nextMode = nextBtn.dataset.mode;
          const leveledUp = Boolean(state.result?.leveledUp);

          if (nextMode === 'practice' && leveledUp) {
            const params = new URLSearchParams({ userId: nextUserId, levelUp: '1' });
            window.location.href = `/challenge-staging?${params.toString()}`;
            return;
          }

          if (nextMode === 'practice') {
            try {
              nextBtn.disabled = true;
              const practiceData = await api.getNextPracticeChallenge(nextUserId);

              if (practiceData?.status === 'all_challenges_completed') {
                const params = new URLSearchParams({ userId: nextUserId });
                const route = practiceData.nextRoute || '/detective-hq';
                window.location.href = `${route}?${params.toString()}`;
                return;
              }

              if (practiceData.challenge?.id) {
                const params = new URLSearchParams({
                  userId: nextUserId,
                  mode: 'practice',
                });
                window.location.href = `/challenges/fake-post/${practiceData.challenge.id}?${params.toString()}`;
                return;
              }

              alert(practiceData.message || 'No more challenges available');
            } catch (err) {
              console.error('Error loading next practice challenge:', err);
              alert('Could not load practice challenge');
            } finally {
              nextBtn.disabled = false;
            }
            return;
          }

          const params = new URLSearchParams({ userId: nextUserId });
          if (leveledUp) {
            params.set('levelUp', '1');
          }
          window.location.href = `/challenge-staging?${params.toString()}`;
        });
      }
    }

    async function handleSubmit(postId) {
      if (!state.sessionId || state.submitting) return;
      state.selected = postId;
      state.submitting = true;
      paint();
      try {
        state.result = await api.submitFakePost(state.sessionId, {
          selectedPostId: postId,
          hintsUsed: state.hintsUsed,
        });
        state.phase = 'feedback';
        paint();
        const unlocked = state.result.newlyUnlockedBadges || [];
        if (unlocked.length) {
          showToast(toastMessageForBadges(unlocked));
          ingestBadgeUnlockNotifications(unlocked);
        }
        await loadDetectiveTip();
      } catch (err) {
        console.error(err);
        alert('Error submitting challenge: ' + err.message);
      } finally {
        state.submitting = false;
        if (state.phase !== 'feedback') paint();
      }
    }

    paint();
  } catch (err) {
    console.error('Error loading challenge:', err);
    container.innerHTML = '<div class="error">Error loading challenge</div>';
  }
}
