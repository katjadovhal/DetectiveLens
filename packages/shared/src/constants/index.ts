import type { SkillCategoryGroup, SkillCategoryId } from '../types/index.js';

export interface SkillCategoryDefinition {
  id: SkillCategoryId;
  name: string;
  parentGroup: SkillCategoryGroup;
  libraryTopicId: string | null;
}

export const SKILL_CATEGORIES: SkillCategoryDefinition[] = [
  {
    id: 'source_verification',
    name: 'Source Verification',
    parentGroup: 'misinformation',
    libraryTopicId: null,
  },
  {
    id: 'content_authenticity',
    name: 'Content Authenticity',
    parentGroup: 'misinformation',
    libraryTopicId: null,
  },
  {
    id: 'evidence_evaluation',
    name: 'Evidence Evaluation',
    parentGroup: 'media_literacy',
    libraryTopicId: null,
  },
  {
    id: 'faces',
    name: 'Faces',
    parentGroup: 'ai_artifacts',
    libraryTopicId: 'faces',
  },
  {
    id: 'hands',
    name: 'Hands',
    parentGroup: 'ai_artifacts',
    libraryTopicId: 'hands',
  },
  {
    id: 'backgrounds',
    name: 'Backgrounds',
    parentGroup: 'ai_artifacts',
    libraryTopicId: 'backgrounds',
  },
  {
    id: 'text',
    name: 'Text',
    parentGroup: 'ai_artifacts',
    libraryTopicId: 'text',
  },
  {
    id: 'lighting_shadows',
    name: 'Lighting & Shadows',
    parentGroup: 'ai_artifacts',
    libraryTopicId: 'lighting-shadows',
  },
];

export const XP_RULES = {
  CHALLENGE_CORRECT: 100,
  CHALLENGE_PARTIAL: 50,
  DAILY_MISSION_BONUS: 100,
  STREAK_BONUS: 25,
  HINT_PENALTY: 10,
} as const;

export const LEVELS = [
  { level: 1, title: 'Internet Detective Level 1', xpRequired: 0 },
  { level: 2, title: 'Internet Detective Level 2', xpRequired: 300 },
  { level: 3, title: 'Internet Detective Level 3', xpRequired: 700 },
  { level: 4, title: 'Internet Detective Level 4', xpRequired: 1200 },
  { level: 5, title: 'Internet Detective Level 5', xpRequired: 2000 },
] as const;

export const ROUTES = {
  HOME: '/',
  ONBOARDING_WELCOME: '/onboarding/welcome',
  ONBOARDING_ASSESSMENT: '/onboarding/assessment',
  ONBOARDING_RESULTS: '/onboarding/results',
  CHALLENGES: '/challenges',
  CHALLENGE_FAKE_POST: '/challenges/fake-post/:id',
  CHALLENGE_IS_IT_REAL: '/challenges/is-it-real/:id',
  CHALLENGE_FIND_CLUES: '/challenges/find-clues/:id',
  LIBRARY: '/library',
  LIBRARY_TOPIC: '/library/:topicId',
  SKILL_PROFILE: '/personalization/skill-profile',
  WEAK_AREAS: '/personalization/weak-areas',
  INSIGHTS: '/personalization/insights',
  XP_LEVELS: '/progress/xp',
  ACHIEVEMENTS: '/progress/achievements',
  HISTORY: '/progress/history',
  PROFILE: '/profile',
  SETTINGS: '/profile/settings',
  HELP: '/profile/help',
} as const;
