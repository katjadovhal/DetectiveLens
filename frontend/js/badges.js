import { escapeHtml } from './api.js';

/**
 * Render the responsive badge catalogue (locked + unlocked).
 * @param {Array<object>} badges
 */
export function renderBadgeCatalogue(badges) {
  if (!Array.isArray(badges) || badges.length === 0) {
    return `
      <div class="badge-empty" role="status">
        <span class="badge-empty-icon" aria-hidden="true">📦</span>
        <p class="profile-empty-state">No badges in the catalogue yet.</p>
      </div>
    `;
  }

  return `
    <ul class="badge-grid" role="list">
      ${badges.map((badge) => renderBadgeCard(badge)).join('')}
    </ul>
  `;
}

function renderBadgeCard(badge) {
  const unlocked = badge.status === 'unlocked';
  const progress = Number(badge.progress) || 0;
  const target = Math.max(1, Number(badge.target) || 1);
  const percent = Math.min(100, Math.round((progress / target) * 100));
  const statusText = unlocked ? 'Unlocked' : 'Locked';
  const earned = unlocked && badge.earnedAt
    ? `<p class="badge-card-earned">Earned ${escapeHtml(formatDate(badge.earnedAt))}</p>`
    : '';
  const why = badge.whyItMatters
    ? `<p class="badge-card-why"><span class="badge-card-why-label">Why this matters:</span> ${escapeHtml(badge.whyItMatters)}</p>`
    : '';

  return `
    <li class="badge-card ${unlocked ? 'badge-card--unlocked' : 'badge-card--locked'}" tabindex="0">
      <div class="badge-card-header">
        <span class="badge-card-icon" aria-hidden="true">${escapeHtml(badge.icon || '🎖️')}</span>
        <span class="badge-card-status" aria-label="${statusText}">
          <span aria-hidden="true">${unlocked ? '✓' : '🔒'}</span>
          ${statusText}
        </span>
      </div>
      <h3 class="badge-card-title">${escapeHtml(badge.title || badge.id)}</h3>
      <p class="badge-card-description">${escapeHtml(badge.description || '')}</p>
      <div class="badge-card-progress">
        <div
          class="badge-progress-bar"
          role="progressbar"
          aria-valuemin="0"
          aria-valuemax="${target}"
          aria-valuenow="${progress}"
          aria-label="Progress ${progress} of ${target}"
        >
          <span class="badge-progress-fill" style="width: ${percent}%"></span>
        </div>
        <p class="badge-progress-text">${progress} of ${target}</p>
      </div>
      ${earned}
      ${why}
    </li>
  `;
}

function formatDate(iso) {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}
