import { api, escapeHtml } from '../api.js?v=hints-3';
import { setLastUserId } from '../session.js?v=hints-3';

const HINT_STAGES = {
  1: { stage: 'pre_answer_hint', label: 'Investigation clue', hintLevel: 1 },
  2: { stage: 'stronger_hint', label: 'Stronger clue', hintLevel: 2 },
};

function renderSocialPost(post, selected, disabled) {
  return `
    <button type="button" class="social-post ${selected ? 'selected' : ''}" data-post-id="${post.id}" ${disabled ? 'disabled' : ''} aria-pressed="${selected ? 'true' : 'false'}">
      <span class="post-badge">${escapeHtml(post.id)}</span>
      ${post.imageUrl ? `<img class="post-image" src="${post.imageUrl}" alt="Image ${escapeHtml(post.id)}">` : ''}
      ${post.text ? `<p class="post-text">${escapeHtml(post.text)}</p>` : ''}
    </button>
  `;
}

function renderLiveRegion(message) {
  return `<div class="challenge-live" aria-live="polite" aria-atomic="true">${escapeHtml(message || '')}</div>`;
}

function renderDetectiveTip(tipText, personalizationMode, loading) {
  if (loading) {
    return `
      <div class="tip-box tip-box--loading" aria-busy="true">
        <span class="tip-icon" role="img" aria-label="Detective mascot">🐕</span>
        <p class="tip-loading">Loading detective tip…</p>
      </div>
    `;
  }
  if (!tipText) return '';
  const modeNote =
    personalizationMode === 'skill_practice'
      ? `<p class="tip-mode">Practice focus: a skill from this challenge</p>`
      : '';
  return `
    <div class="tip-box" role="region" aria-label="Detective tip">
      <span class="tip-icon" role="img" aria-label="Detective mascot">🐕</span>
      <div>
        <p class="tip-heading">Detective Tip</p>
        ${modeNote}
        <p class="tip-message">${escapeHtml(tipText)}</p>
      </div>
    </div>
  `;
}

function renderFeedback(result, state) {
  const explanationBlock = state.explanationLoading
    ? `<p class="explanation-loading" aria-busy="true">Loading explanation…</p>`
    : state.showExplanation && state.explanationText
      ? `<div class="explanation-prose" tabindex="-1" id="explanation-panel">${escapeHtml(state.explanationText)}</div>`
      : state.showExplanation && Array.isArray(result.explanation) && result.explanation.length
        ? `<ul class="explanation-list" id="explanation-panel">${result.explanation.map((b) => `<li>${escapeHtml(b)}</li>`).join('')}</ul>`
        : '';

  const whyLabel = result.isCorrect ? 'Show why' : 'Why?';
  const whyBtn =
    state.showExplanation
      ? ''
      : `<button type="button" class="btn btn-outline" id="why-btn">${whyLabel}</button>`;

  if (result.isCorrect) {
    return `
      <div class="feedback">
        <p class="feedback-title">You picked ${escapeHtml(result.selectedAnswer)}! That's the fake post.</p>
        <p class="feedback-emoji" aria-hidden="true">🎉 ⭐ 🎊</p>
        <div class="feedback-why">
          ${whyBtn}
          ${explanationBlock}
        </div>
      </div>
    `;
  }

  return `
    <div class="feedback">
      <p class="feedback-title">Not quite!</p>
      <p class="feedback-sub">You selected ${escapeHtml(result.selectedAnswer)} as the fake post!</p>
      <p class="feedback-sub">The correct answer was ${escapeHtml(result.correctAnswer)}.</p>
      <div class="feedback-why">
        ${whyBtn}
        ${explanationBlock}
      </div>
    </div>
  `;
}

function renderInvestigationPanel(state) {
  if (!state.hintsExpanded) {
    return `
      <div class="investigation-panel">
        <button type="button" class="btn btn-outline" id="expand-hints-btn" ${state.hintLoading ? 'disabled' : ''}>
          Need an investigation clue?
        </button>
      </div>
    `;
  }

  const level1 = state.hintTexts[1];
  const level2 = state.hintTexts[2];
  const canRequestStronger = Boolean(level1) && !level2 && !state.hintLoading;

  return `
    <div class="investigation-panel">
      <div class="investigation-box" role="region" aria-label="Investigation clues">
        <p class="investigation-title">Investigation clues</p>
        ${
          state.hintLoading && !level1
            ? `<p class="hint-status" aria-busy="true">Loading clue…</p>`
            : ''
        }
        ${
          level1
            ? `
          <div class="hint-card ${state.activeHintLevel === 1 ? 'hint-card--active' : ''}">
            <p class="hint-card-label">Clue 1</p>
            <p class="hint-card-body">${escapeHtml(level1)}</p>
          </div>`
            : ''
        }
        ${
          level2
            ? `
          <div class="hint-card ${state.activeHintLevel === 2 ? 'hint-card--active' : ''}">
            <p class="hint-card-label">Clue 2</p>
            <p class="hint-card-body">${escapeHtml(level2)}</p>
          </div>`
            : ''
        }
        ${
          canRequestStronger
            ? `
          <button type="button" class="btn btn-outline hint-stronger-btn" id="stronger-hint-btn">
            Need a stronger clue?
          </button>`
            : ''
        }
        ${
          state.hintLoading && level1 && !level2
            ? `<p class="hint-status" aria-busy="true">Loading stronger clue…</p>`
            : ''
        }
        ${state.hintError ? `<p class="hint-error" role="alert">${escapeHtml(state.hintError)}</p>` : ''}
      </div>
    </div>
  `;
}

function renderPlaying(challenge, state) {
  const content = challenge.content;
  return `
    <div class="container">
      ${renderLiveRegion(state.liveMessage)}
      <div class="challenge-header">
        <h1 class="page-title">${escapeHtml(challenge.title)}</h1>
        <p class="page-subtitle">${escapeHtml(challenge.instruction)}</p>
      </div>
      <div class="post-grid" id="post-grid">
        ${content.posts.map((post) => renderSocialPost(post, state.selected === post.id, state.submitting)).join('')}
      </div>
      <div id="investigation-panel">
        ${renderInvestigationPanel(state)}
      </div>
      <div class="mascot-row">
        <span class="mascot-icon" aria-hidden="true">🐕</span>
        <div class="speech-bubble">Look closely! Not everything is what it seems!</div>
      </div>
    </div>
  `;
}

function renderFeedbackView(result, state, userId, mode, challengeId) {
  const isDailyMode = mode === 'daily';
  const nextLabel = isDailyMode ? 'Share & Continue' : 'Next Challenge';

  return `
    <div class="container">
      ${renderLiveRegion(state.liveMessage)}
      <div id="feedback-area">${renderFeedback(result, state)}</div>
      ${renderDetectiveTip(state.detectiveTipText, state.detectiveTipMode, state.tipLoading)}
      ${
        isDailyMode && result.isCorrect
          ? `
        <div class="daily-completion-message">
          <p>Great job! You've completed today's daily challenge!</p>
          <p>Come back tomorrow for a new challenge.</p>
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

function bulletsToProse(bullets) {
  if (!Array.isArray(bullets) || !bullets.length) return '';
  return bullets.join(' ');
}

export async function renderChallenge(container, challengeId, userId, mode = 'practice') {
  container.innerHTML = '<div class="loading" role="status">Loading challenge...</div>';

  if (!userId) {
    container.innerHTML = '<div class="error" role="alert">Error: No user ID provided</div>';
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
      attemptNumber: start.attemptNumber ?? 1,
      selected: null,
      hintsUsed: 0,
      hintsExpanded: false,
      hintTexts: {},
      activeHintLevel: 0,
      hintLoading: false,
      hintError: null,
      submitting: false,
      phase: 'playing',
      result: null,
      showExplanation: false,
      explanationText: null,
      explanationLoading: false,
      detectiveTipText: null,
      detectiveTipMode: null,
      tipLoading: false,
      liveMessage: '',
    };

    function setLive(message) {
      state.liveMessage = message || '';
    }

    function paint() {
      if (state.phase === 'feedback' && state.result) {
        container.innerHTML = renderFeedbackView(state.result, state, userId, mode, id);
        bindFeedbackEvents();
        return;
      }
      container.innerHTML = renderPlaying(challenge, state);
      bindPlayingEvents();
    }

    async function fetchHint(level) {
      const meta = HINT_STAGES[level];
      if (!meta || state.hintTexts[level] || state.hintLoading) return;

      state.hintLoading = true;
      state.hintError = null;
      setLive(`Loading ${meta.label.toLowerCase()}…`);
      paint();

      try {
        const hint = await api.requestHint(id, {
          userId,
          stage: meta.stage,
          locale: 'en',
          hintLevel: meta.hintLevel,
        });
        state.hintTexts[level] = hint.text;
        state.activeHintLevel = level;
        state.hintsUsed = Math.max(state.hintsUsed, level);
        setLive(`${meta.label} ready.`);
      } catch (err) {
        state.hintError = err.message || 'Could not load clue.';
        setLive(state.hintError);
      } finally {
        state.hintLoading = false;
        paint();
      }
    }

    async function fetchExplanation() {
      if (state.explanationLoading || state.showExplanation) return;
      state.explanationLoading = true;
      state.showExplanation = true;
      setLive('Loading explanation…');
      paint();

      try {
        const hint = await api.requestHint(id, {
          userId,
          stage: 'answer_explanation',
          locale: 'en',
          attemptNumber: state.result?.attemptNumber ?? state.attemptNumber,
          selectedOption: state.result?.selectedAnswer,
        });
        state.explanationText = hint.text;
        setLive('Explanation ready.');
      } catch (err) {
        state.explanationText = bulletsToProse(state.result?.explanation) || err.message;
        setLive('Explanation ready.');
      } finally {
        state.explanationLoading = false;
        paint();
        const panel = container.querySelector('#explanation-panel');
        if (panel) panel.focus?.();
      }
    }

    async function fetchDetectiveTip() {
      state.tipLoading = true;
      setLive('Loading detective tip…');
      paint();
      try {
        const tip = await api.requestHint(id, {
          userId,
          stage: 'detective_tip',
          locale: 'en',
          attemptNumber: state.result?.attemptNumber ?? state.attemptNumber,
          selectedOption: state.result?.selectedAnswer,
        });
        state.detectiveTipText = tip.text;
        state.detectiveTipMode = tip.personalizationMode;
        setLive('Detective tip ready.');
      } catch {
        const legacy = state.result?.detectiveTip;
        if (legacy?.message) {
          state.detectiveTipText = legacy.message;
          state.detectiveTipMode = 'neutral';
          setLive('Detective tip ready.');
        } else {
          setLive('');
        }
      } finally {
        state.tipLoading = false;
        paint();
      }
    }

    function bindPlayingEvents() {
      container.querySelectorAll('[data-post-id]').forEach((btn) => {
        btn.addEventListener('click', () => handleSubmit(btn.dataset.postId));
      });

      const expandBtn = container.querySelector('#expand-hints-btn');
      if (expandBtn) {
        expandBtn.addEventListener('click', async () => {
          state.hintsExpanded = true;
          paint();
          await fetchHint(1);
        });
      }

      const strongerBtn = container.querySelector('#stronger-hint-btn');
      if (strongerBtn) {
        strongerBtn.addEventListener('click', () => fetchHint(2));
      }
    }

    function bindFeedbackEvents() {
      const whyBtn = container.querySelector('#why-btn');
      if (whyBtn) {
        whyBtn.addEventListener('click', () => fetchExplanation());
      }

      const nextBtn = container.querySelector('#next-challenge-btn');
      const shareBtn = container.querySelector('#share-btn');

      if (shareBtn) {
        shareBtn.addEventListener('click', () => {
          const shareUrl = `https://detectivelens.app/challenge/${id}?shared=true`;
          alert(`Share this challenge with a friend:\n\n${shareUrl}`);
        });
      }

      if (nextBtn) {
        nextBtn.addEventListener('click', async () => {
          const nextUserId = nextBtn.dataset.userId;
          const params = new URLSearchParams({ userId: nextUserId });
          if (state.result?.leveledUp) {
            params.set('levelUp', '1');
          }

          // Redirect to challenge staging
          window.location.href = `/challenge-staging?${params.toString()}`;
        });
      }
    }

    async function handleSubmit(postId) {
      if (!state.sessionId || state.submitting) return;
      state.selected = postId;
      state.submitting = true;
      setLive('Submitting your answer…');
      paint();
      try {
        state.result = await api.submitFakePost(state.sessionId, {
          selectedPostId: postId,
          hintsUsed: state.hintsUsed,
        });
        state.phase = 'feedback';
        setLive(
          state.result.isCorrect
            ? 'Correct! You spotted the fake post.'
            : 'Not quite. Review the feedback below.',
        );
        state.submitting = false;
        paint();
        // Tip is available after a verified attempt for both outcomes.
        await fetchDetectiveTip();
      } catch (err) {
        console.error(err);
        setLive('');
        alert('Error submitting challenge: ' + err.message);
        state.submitting = false;
        paint();
      }
    }

    paint();
  } catch (err) {
    console.error('Error loading challenge:', err);
    container.innerHTML = '<div class="error" role="alert">Error loading challenge</div>';
  }
}
