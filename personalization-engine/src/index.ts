import type { ChallengeType, DetectiveTip, SkillCategoryId, SkillScore } from '@detectivelens/shared';
import { LEVELS, XP_RULES } from '@detectivelens/shared';

export function updateSkillScore(
  current: number,
  isCorrect: boolean,
  difficulty: 'easy' | 'medium' | 'hard' = 'medium',
): number {
  const weight = difficulty === 'easy' ? 8 : difficulty === 'hard' ? 4 : 6;
  const delta = isCorrect ? weight : -weight;
  return Math.max(0, Math.min(100, current + delta));
}

export function getWeakAreas(scores: SkillScore[], threshold = 60): SkillScore[] {
  return [...scores]
    .filter((s) => s.score < threshold || s.attempts === 0)
    .sort((a, b) => a.score - b.score);
}

export function getLevelFromXp(totalXp: number) {
  let current: (typeof LEVELS)[number] = LEVELS[0];
  for (const level of LEVELS) {
    if (totalXp >= level.xpRequired) current = level;
  }
  const next = LEVELS.find((l) => l.level === current.level + 1);
  return {
    level: current.level,
    title: current.title,
    xpRequired: current.xpRequired,
    xpToNext: next ? next.xpRequired - totalXp : 0,
  };
}

export function calculateXpEarned(
  baseReward: number,
  isCorrect: boolean,
  hintsUsed: number,
): number {
  if (!isCorrect) return 0;
  return Math.max(0, baseReward - hintsUsed * XP_RULES.HINT_PENALTY);
}

interface DetectiveTipInput {
  isCorrect: boolean;
  selectedAnswer: string;
  correctAnswer: string;
  challengeType: ChallengeType;
}

export function getDetectiveTip(input: DetectiveTipInput): DetectiveTip | undefined {
  if (input.isCorrect || input.challengeType !== 'fake_post') return undefined;

  if (input.selectedAnswer === 'B' && input.correctAnswer === 'A') {
    return {
      id: 'trusts_familiar_brands',
      message:
        'You often trust posts from familiar brands without checking whether the content matches what they normally share.',
      checklist: [
        'Check if the message fits the source',
        'Look for unusual or surprising claims',
        'Ask whether the post supports the account\'s goals',
      ],
    };
  }

  return {
    id: 'general_source_check',
    message: 'Remember: even verified accounts can share surprising content. Always check if it fits the source.',
    checklist: [
      'Who posted this?',
      'Does the tone match the account?',
      'Would you expect this message from them?',
    ],
  };
}

export function getRecommendedCategoryIds(weakAreas: SkillScore[]): SkillCategoryId[] {
  return getWeakAreas(weakAreas).slice(0, 3).map((s) => s.categoryId);
}
