/** Central avatar metadata for MVP (emoji). imageUrl reserved for future PNG assets. */

export const DEFAULT_AVATAR_ID = 'avatar-detective-1';

const AVATAR_ALIASES = {
  'detective-default': DEFAULT_AVATAR_ID,
};

export const AVATARS = [
  {
    id: 'avatar-detective-1',
    label: 'Detective 1',
    emoji: '🕵️‍♂️',
    imageUrl: null,
  },
  {
    id: 'avatar-detective-2',
    label: 'Detective 2',
    emoji: '🕵️‍♀️',
    imageUrl: null,
  },
  {
    id: 'avatar-detective-3',
    label: 'Detective 3',
    emoji: '👨‍🔬',
    imageUrl: null,
  },
  {
    id: 'avatar-detective-4',
    label: 'Detective 4',
    emoji: '👩‍🔬',
    imageUrl: null,
  },
];

const AVATAR_BY_ID = Object.fromEntries(AVATARS.map((avatar) => [avatar.id, avatar]));

export function normalizeAvatarId(avatarId) {
  if (!avatarId) return DEFAULT_AVATAR_ID;
  const aliased = AVATAR_ALIASES[avatarId] ?? avatarId;
  return AVATAR_BY_ID[aliased] ? aliased : DEFAULT_AVATAR_ID;
}

export function getAvatar(avatarId) {
  return AVATAR_BY_ID[normalizeAvatarId(avatarId)];
}

export function getAvatarEmoji(avatarId) {
  return getAvatar(avatarId).emoji;
}

export function getAvatarLabel(avatarId) {
  return getAvatar(avatarId).label;
}

/**
 * Shared avatar picker markup (onboarding + profile).
 * Selection is indicated by border, checkmark, and accessible text — not color alone.
 */
export function renderAvatarGridHtml(selectedId, { escapeHtml, compact = false } = {}) {
  const currentId = normalizeAvatarId(selectedId);
  return `
    <div class="avatar-grid${compact ? ' avatar-grid-compact' : ''}" role="radiogroup" aria-label="Choose your avatar">
      ${AVATARS.map((avatar) => {
        const selected = avatar.id === currentId;
        return `
          <button
            type="button"
            class="avatar-card avatar-card-circle${selected ? ' selected' : ''}"
            data-avatar-id="${avatar.id}"
            role="radio"
            aria-checked="${selected ? 'true' : 'false'}"
            aria-label="${escapeHtml(avatar.label)}${selected ? ', selected' : ''}"
          >
            <span class="avatar-emoji" aria-hidden="true">${avatar.emoji}</span>
            <span class="avatar-label">${escapeHtml(avatar.label)}</span>
            <span class="avatar-selected-indicator" aria-hidden="true">
              ${selected ? '<span class="avatar-check">✓</span><span class="avatar-selected-text">Selected</span>' : ''}
            </span>
          </button>
        `;
      }).join('')}
    </div>
  `;
}

export function bindAvatarGrid(container, getSelectedId, setSelectedId) {
  container.querySelectorAll('[data-avatar-id]').forEach((btn) => {
    btn.addEventListener('click', () => {
      setSelectedId(btn.dataset.avatarId);
      const selectedId = normalizeAvatarId(getSelectedId());
      container.querySelectorAll('.avatar-card').forEach((card) => {
        const isSelected = card.dataset.avatarId === selectedId;
        card.classList.toggle('selected', isSelected);
        card.setAttribute('aria-checked', isSelected ? 'true' : 'false');
        const label = card.querySelector('.avatar-label')?.textContent ?? 'Avatar';
        card.setAttribute('aria-label', `${label}${isSelected ? ', selected' : ''}`);
        const indicator = card.querySelector('.avatar-selected-indicator');
        if (indicator) {
          indicator.innerHTML = isSelected
            ? '<span class="avatar-check">✓</span><span class="avatar-selected-text">Selected</span>'
            : '';
        }
      });
    });
  });
}
