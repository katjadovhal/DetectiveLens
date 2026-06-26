import { api, escapeHtml } from '../api.js';

function renderSocialPost(post, selected, disabled) {
  return `
    <button type="button" class="social-post ${selected ? 'selected' : ''}" data-post-id="${post.id}" ${disabled ? 'disabled' : ''}>
      <span class="post-badge">${escapeHtml(post.id)}</span>

      ${post.imageUrl ? `<img class="post-image" src="${post.imageUrl}" alt="Image ${escapeHtml(post.id)}">` : ''}

      ${post.text ? `<p class="post-text">${escapeHtml(post.text)}</p>` : ''}
    </button>
  `;
}

function renderDetectiveTip(tip) {
  if (!tip) return '';
  return `
    <div class="tip-box">
      <span class="tip-icon" role="img" aria-label="Detective mascot">🐕</span>
      <div>
        <p style="margin: 0 0 1rem; font-size: 1.25rem; font-weight: 700; color: var(--color-gray-800);">
          Detective Tip: ${escapeHtml(tip.message)}
        </p>
        <p style="margin: 0 0 0.75rem; font-size: 1.125rem; font-weight: 700; color: var(--color-gray-700);">
          Next time, remember to:
        </p>
        <ul class="tip-checklist">
          ${tip.checklist.map((item) => `<li><span class="check-icon">✓</span>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;
}

function renderFeedback(result, showExplanation) {
  const explanationHtml = showExplanation
    ? `<ul class="explanation-list">${result.explanation.map((b) => `<li>${escapeHtml(b)}</li>`).join('')}</ul>`
    : '';

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
      <div style="margin-top: 2rem">
        <button type="button" class="btn btn-outline" id="why-btn">Why?</button>
        ${explanationHtml}
      </div>
    </div>
  `;
}

function renderInvestigationPanel(hints, hintsUsed, activeHintIndex, expanded) {
  if (!expanded) {
    return `
      <div class="investigation-panel">
        <button type="button" class="btn btn-outline" id="expand-hints-btn">Need an investigation clue?</button>
      </div>
    `;
  }

  const activeHint = hints[activeHintIndex];
  return `
    <div class="investigation-panel">
      <div class="investigation-box">
        <p style="margin: 0 0 1.5rem; text-align: center; font-size: 1.5rem; font-weight: 700; color: var(--color-gray-700);">
          How would you like to examine this post?
        </p>
        <div style="margin-bottom: 1.5rem">
          ${hints
            .map(
              (hint, i) => `
            <button type="button" class="hint-btn ${i === activeHintIndex ? 'active' : ''}" data-hint-index="${i}">
              ${i + 1}. ${escapeHtml(hint.question)}
            </button>
          `,
            )
            .join('')}
        </div>
        ${
          activeHint
            ? `
          <div style="font-size: 1.125rem; color: var(--color-gray-700); line-height: 1.625">
            <p style="margin: 0 0 0.75rem">${escapeHtml(activeHint.content.body)}</p>
            <p style="margin: 0 0 0.5rem; font-size: 1.25rem; font-weight: 700">Ask yourself:</p>
            <ul style="padding-left: 1.25rem">
              ${activeHint.content.bulletQuestions.map((q) => `<li style="margin-bottom: 0.5rem">${escapeHtml(q)}</li>`).join('')}
            </ul>
          </div>`
            : ''
        }
      </div>
    </div>
  `;
}

function renderPlaying(challenge, state) {
  const content = challenge.content;
  return `
    <div class="container">
      <div class="challenge-header">
        <h1 class="page-title">${escapeHtml(challenge.title)}</h1>
        <p class="page-subtitle">${escapeHtml(challenge.instruction)}</p>
      </div>
      <div class="post-grid" id="post-grid">
        ${content.posts.map((post) => renderSocialPost(post, state.selected === post.id, state.submitting)).join('')}
      </div>
      <div id="investigation-panel">
        ${renderInvestigationPanel(challenge.hints ?? [], state.hintsUsed, state.activeHintIndex, state.hintsExpanded)}
      </div>
      <div class="mascot-row">
        <span class="mascot-icon">🐕</span>
        <div class="speech-bubble">Look closely! Not everything is what it seems!</div>
      </div>
    </div>
  `;
}

function renderFeedbackView(result, showExplanation, currentChallengeId) {
  const challengeOrder = ['monkey-001', 'road-001'];
  const currentIndex = challengeOrder.indexOf(currentChallengeId);
  const nextChallengeId = challengeOrder[currentIndex + 1];

  const nextHref = nextChallengeId
      ? `/challenges/fake-post/${nextChallengeId}`
      : '/';

  const nextLabel = nextChallengeId ? 'Next Challenge' : 'Finish';

  return `
    <div class="container">
      <div id="feedback-area">${renderFeedback(result, showExplanation)}</div>
      ${renderDetectiveTip(result.detectiveTip)}
      <div class="actions-right">
        <button type="button" class="btn btn-primary" id="next-challenge-btn" data-next-id="${nextChallengeId ?? ''}">
  ${nextLabel} ${result.xpEarned > 0 ? `(+${result.xpEarned} XP)` : ''}
</button>
      </div>
    </div>
  `;
}

export async function renderChallenge(container, challengeId) {
  container.innerHTML = '<div class="loading">Loading challenge...</div>';

  const id = challengeId || 'monkey-001';
  const [{ challenge }, start] = await Promise.all([api.getChallenge(id), api.startChallenge(id)]);

  const state = {
    sessionId: start.sessionId,
    selected: null,
    hintsUsed: 0,
    hintsExpanded: false,
    activeHintIndex: 0,
    submitting: false,
    phase: 'playing',
    result: null,
    showExplanation: false,
  };

  function paint() {
    if (state.phase === 'feedback' && state.result) {
      container.innerHTML = renderFeedbackView(state.result, state.showExplanation, id);
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

    const expandBtn = container.querySelector('#expand-hints-btn');
    if (expandBtn) {
      expandBtn.addEventListener('click', () => {
        state.hintsExpanded = true;
        paint();
      });
    }

    container.querySelectorAll('[data-hint-index]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const index = Number(btn.dataset.hintIndex);
        state.activeHintIndex = index;
        if (index >= state.hintsUsed) {
          state.hintsUsed = Math.min(index + 1, (challenge.hints?.length ?? 0));
        }
        paint();
      });
    });
  }

  function bindFeedbackEvents() {
    const nextBtn = container.querySelector('#next-challenge-btn');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const nextId = nextBtn.dataset.nextId;

        if (nextId) {
          window.location.href = `/challenges/fake-post/${nextId}`;
        } else {
          window.location.href = '/';
        }
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
    } catch (err) {
      console.error(err);
    } finally {
      state.submitting = false;
      paint();
    }
  }

  paint();
}
