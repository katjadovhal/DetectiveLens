/**
 * Animation utilities for level-ups and celebrations
 */

/**
 * Trigger a level-up celebration animation
 * Shows a glow effect on the progress bar and releases confetti
 */
export function triggerLevelUpAnimation() {
  // Find and animate the progress fill + track
  const progressFill = document.querySelector('.progress-fill');
  const progressTrack = document.querySelector('.progress-track');

  if (progressFill) {
    // Remove animation class if it exists
    progressFill.classList.remove('levelup-animation');
    // Trigger reflow to restart animation
    void progressFill.offsetWidth;
    // Add animation class
    progressFill.classList.add('levelup-animation');
  }

  if (progressTrack) {
    progressTrack.classList.remove('levelup-track-flash');
    void progressTrack.offsetWidth;
    progressTrack.classList.add('levelup-track-flash');
  }

  // Create and release confetti
  releaseConfetti();
}

/**
 * Create and animate confetti pieces
 */
function releaseConfetti() {
  const confettiCount = 64;
  const colors = [
    '#ff6b6b',
    '#4ecdc4',
    '#ffe66d',
    '#95e1d3',
    '#f38181',
    '#aa96da',
    '#fcbad3',
    '#a8e6cf',
    '#ffd3b6',
    '#ffaaa5',
  ];

  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';

    const size = 6 + Math.random() * 10;
    const duration = 1.6 + Math.random() * 1.3;
    const delay = Math.random() * 0.45;
    const startX = Math.random() * 100;
    const driftX = -120 + Math.random() * 240;
    const spin = -540 + Math.random() * 1080;
    const color = colors[Math.floor(Math.random() * colors.length)];

    confetti.style.width = `${size}px`;
    confetti.style.height = `${size * (0.6 + Math.random() * 0.8)}px`;
    confetti.style.left = `${startX}%`;
    confetti.style.background = color;
    confetti.style.borderRadius = Math.random() > 0.6 ? '999px' : '2px';
    confetti.style.setProperty('--confetti-drift-x', `${driftX}px`);
    confetti.style.setProperty('--confetti-spin', `${spin}deg`);
    confetti.style.animationDuration = `${duration}s`;

    // Add some randomness to the animation
    confetti.style.animationDelay = `${delay}s`;

    document.body.appendChild(confetti);

    // Remove confetti element after animation completes
    setTimeout(() => {
      confetti.remove();
    }, 3600);
  }
}

/**
 * Check if progress bar should reset (level up) based on old and new progress
 * @param {number} oldPercent - Previous progress percentage
 * @param {number} newPercent - New progress percentage
 * @returns {boolean} True if level up occurred
 */
export function detectLevelUp(oldPercent, newPercent) {
  // Level up if progress went from high to low (reset to new level)
  // or if we reached 100% and now starting a new level
  return oldPercent >= 80 && newPercent < oldPercent;
}


