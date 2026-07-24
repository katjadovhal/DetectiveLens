/** Central avatar catalog — PNG characters with XP unlock gates. */

export const DEFAULT_AVATAR_ID = 'avatar-detective-1';

const AVATAR_ALIASES = {
  'detective-default': DEFAULT_AVATAR_ID,
};

const ASSET_BASE = '/public/assets/avatars';

export const AVATARS = [
  {
    id: 'avatar-detective-1',
    label: 'Detective 1',
    imageUrl: `${ASSET_BASE}/AvatarBoy.png`,
    unlockXp: 0,
  },
  {
    id: 'avatar-detective-2',
    label: 'Detective 2',
    imageUrl: `${ASSET_BASE}/AvatarGirl.png`,
    unlockXp: 0,
  },
  {
    id: 'avatar-detective-3',
    label: 'Dog',
    imageUrl: `${ASSET_BASE}/AvatarDog.png`,
    unlockXp: 400,
  },
  {
    id: 'avatar-detective-4',
    label: 'Cat',
    imageUrl: `${ASSET_BASE}/AvatarCat.png`,
    unlockXp: 600,
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

export function getAvatarLabel(avatarId) {
  return getAvatar(avatarId).label;
}

export function getAvatarImageUrl(avatarId) {
  return getAvatar(avatarId).imageUrl;
}

export function isAvatarUnlocked(avatarId, totalXp = 0) {
  const avatar = getAvatar(avatarId);
  return (Number(totalXp) || 0) >= (avatar.unlockXp || 0);
}

/** @deprecated Prefer getAvatarMarkup — kept so older call sites keep working briefly. */
export function getAvatarEmoji(avatarId) {
  return '';
}

export function getAvatarMarkup(avatarId, { className = 'avatar-img', alt } = {}) {
  const avatar = getAvatar(avatarId);
  const label = alt ?? avatar.label;
  return `<img class="${className}" src="${avatar.imageUrl}" alt="${label}" width="96" height="96" decoding="async" />`;
}

function avatarFaceHtml(avatar, { locked = false } = {}) {
  return `
    <span class="avatar-face${locked ? ' avatar-face--locked' : ''}" aria-hidden="true">
      <img class="avatar-img" src="${avatar.imageUrl}" alt="" width="96" height="96" decoding="async" />
      ${locked ? '<span class="avatar-lock" aria-hidden="true">🔒</span>' : ''}
    </span>
  `;
}

/**
 * Shared avatar picker markup (onboarding + profile).
 * Pass totalXp so locked characters stay disabled until unlocked.
 */
export function renderAvatarGridHtml(
  selectedId,
  { escapeHtml, compact = false, totalXp = 0, onlyUnlocked = false } = {},
) {
  const currentId = normalizeAvatarId(selectedId);
  const xp = Number(totalXp) || 0;
  const list = onlyUnlocked
    ? AVATARS.filter((avatar) => isAvatarUnlocked(avatar.id, xp))
    : AVATARS;

  return `
    <div class="avatar-grid${compact ? ' avatar-grid-compact' : ''}" role="radiogroup" aria-label="Choose your avatar">
      ${list
        .map((avatar) => {
          const unlocked = isAvatarUnlocked(avatar.id, xp);
          const selected = unlocked && avatar.id === currentId;
          const lockHint = unlocked
            ? ''
            : `Locked — unlock at ${avatar.unlockXp} XP`;
          const ariaLabel = unlocked
            ? `${avatar.label}${selected ? ', selected' : ''}`
            : `${avatar.label}, ${lockHint}`;
          return `
          <button
            type="button"
            class="avatar-card avatar-card-circle${selected ? ' selected' : ''}${unlocked ? '' : ' avatar-card--locked'}"
            data-avatar-id="${avatar.id}"
            data-unlocked="${unlocked ? 'true' : 'false'}"
            role="radio"
            aria-checked="${selected ? 'true' : 'false'}"
            aria-disabled="${unlocked ? 'false' : 'true'}"
            ${unlocked ? '' : 'disabled'}
            aria-label="${escapeHtml(ariaLabel)}"
          >
            ${avatarFaceHtml(avatar, { locked: !unlocked })}
            <span class="avatar-label">${escapeHtml(avatar.label)}</span>
            ${
              unlocked
                ? `<span class="avatar-selected-indicator" aria-hidden="true">
                    ${selected ? '<span class="avatar-check">✓</span><span class="avatar-selected-text">Selected</span>' : ''}
                  </span>`
                : `<span class="avatar-unlock-hint">${escapeHtml(String(avatar.unlockXp))} XP</span>`
            }
          </button>
        `;
        })
        .join('')}
    </div>
  `;
}

export function bindAvatarGrid(container, getSelectedId, setSelectedId, { totalXp = 0 } = {}) {
  const xp = Number(totalXp) || 0;
  container.querySelectorAll('[data-avatar-id]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.avatarId;
      if (!isAvatarUnlocked(id, xp)) return;
      setSelectedId(id);
      const selectedId = normalizeAvatarId(getSelectedId());
      container.querySelectorAll('.avatar-card').forEach((card) => {
        const cardId = card.dataset.avatarId;
        const unlocked = isAvatarUnlocked(cardId, xp);
        const isSelected = unlocked && cardId === selectedId;
        card.classList.toggle('selected', isSelected);
        card.setAttribute('aria-checked', isSelected ? 'true' : 'false');
        const label = card.querySelector('.avatar-label')?.textContent ?? 'Avatar';
        if (unlocked) {
          card.setAttribute('aria-label', `${label}${isSelected ? ', selected' : ''}`);
        }
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
