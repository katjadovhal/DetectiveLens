/**
 * Central XP / level progress helpers.
 * totalXp is the single source of truth for the XP statistic and header.
 * Level bar uses backend currentLevelXp + levelXpRequired.
 */

export function getProgressSummary({ profile = {}, home = {} } = {}) {
  const totalXp = Number(profile.totalXp ?? home.progress?.totalXp ?? 0) || 0;
  const level = Number(profile.currentLevel ?? home.progress?.level ?? 1) || 1;
  const levelTitle =
    home.greeting?.levelTitle || `Internet Detective Level ${level}`;
  const currentLevelXp = Number(
    profile.currentLevelXp ?? home.progress?.currentLevelXp ?? 0,
  ) || 0;
  const xpToNext = home.progress?.xpToNextLevel;
  const rawRequired = home.progress?.levelXpRequired;
  const atMaxLevel = xpToNext === 0 && (rawRequired == null || Number(rawRequired) <= 1);

  let levelXpRequired = Number(rawRequired ?? currentLevelXp + (xpToNext ?? 0)) || 0;
  if (atMaxLevel) {
    levelXpRequired = Math.max(totalXp, currentLevelXp, 1);
  } else if (!levelXpRequired) {
    levelXpRequired = Math.max(currentLevelXp, 1);
  }

  const percent = atMaxLevel
    ? 100
    : levelXpRequired > 0
      ? Math.min(100, Math.round((currentLevelXp / levelXpRequired) * 100))
      : 0;

  return {
    totalXp,
    level,
    levelTitle,
    currentLevelXp: atMaxLevel ? totalXp : currentLevelXp,
    levelXpRequired: atMaxLevel ? Math.max(totalXp, 1) : levelXpRequired,
    percent,
    atMaxLevel,
    completedChallengeCount: Number(profile.completedChallengeCount ?? 0) || 0,
  };
}

export function renderXpBarHtml({
  currentLevelXp,
  levelXpRequired,
  percent,
  atMaxLevel = false,
  totalXp,
  label = 'XP progress',
}) {
  const valueLabel = atMaxLevel
    ? `${totalXp ?? currentLevelXp} XP · Max level`
    : `${currentLevelXp} / ${levelXpRequired} XP`;

  return `
    <div class="progress-wrap">
      <div class="progress-label">
        <span>${label}</span>
        <span>${valueLabel}</span>
      </div>
      <div
        class="progress-track"
        role="progressbar"
        aria-valuemin="0"
        aria-valuemax="${levelXpRequired}"
        aria-valuenow="${currentLevelXp}"
        aria-label="${label}"
      >
        <div class="progress-fill" style="width: ${percent}%"></div>
      </div>
    </div>
  `;
}
