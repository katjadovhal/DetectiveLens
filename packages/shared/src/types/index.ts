export type SelfReportedLevel = 'beginner' | 'somewhat' | 'pro';

export type ChallengeType = 'fake_post' | 'is_it_real' | 'find_clues';

export type Difficulty = 'easy' | 'medium' | 'hard';

export type SkillCategoryId =
  | 'source_verification'
  | 'content_authenticity'
  | 'evidence_evaluation'
  | 'faces'
  | 'hands'
  | 'backgrounds'
  | 'text'
  | 'lighting_shadows';

export type SkillCategoryGroup = 'misinformation' | 'ai_artifacts' | 'media_literacy';

export interface User {
  id: string;
  email: string | null;
  username: string;
  createdAt: string;
}

export interface Profile {
  id: string;
  userId: string;
  avatarId: string;
  displayName: string;
  selfReportedLevel: SelfReportedLevel;
  currentLevel: number;
  totalXp: number;
  currentLevelXp: number;
  dailyStreak: number;
  onboardingCompleted: boolean;
  lastChallengeId: string | null;
  settings: ProfileSettings;
}

export interface ProfileSettings {
  notifications: boolean;
  sound: boolean;
  privacy: boolean;
}

export interface SkillScore {
  categoryId: SkillCategoryId;
  score: number;
  attempts: number;
  correct: number;
}

export interface SocialPost {
  id: 'A' | 'B';
  platform: 'twitter' | 'instagram' | 'facebook';
  author: string;
  handle: string;
  verified: boolean;
  text: string;
  imageUrl?: string;
  metrics: {
    retweets?: number;
    quoteTweets?: number;
    likes?: number;
    replies?: number;
  };
  timestamp: string;
}

export interface FakePostChallengeContent {
  posts: [SocialPost, SocialPost];
  correctPostId: 'A' | 'B';
  explanation: { bullets: string[] };
}

export interface IsItRealChallengeContent {
  imageUrl: string;
  correctAnswer: 'real' | 'ai';
  explanation: { indicators: string[] };
}

export interface Hotspot {
  id: string;
  x: number;
  y: number;
  radius: number;
  category: SkillCategoryId;
  label: string;
}

export interface FindCluesChallengeContent {
  imageUrl: string;
  hotspots: Hotspot[];
  minCluesToFind: number;
  explanation: { whatToLookFor: string[] };
}

export type ChallengeContent =
  | FakePostChallengeContent
  | IsItRealChallengeContent
  | FindCluesChallengeContent;

/** Challenge content returned by API (answers stripped) */
export type PublicFakePostContent = Omit<FakePostChallengeContent, 'correctPostId'>;
export type PublicIsItRealContent = Omit<IsItRealChallengeContent, 'correctAnswer'>;
export type PublicFindCluesContent = Omit<FindCluesChallengeContent, 'hotspots'> & {
  hotspots: Array<Omit<Hotspot, 'category' | 'label'>>;
};
export type PublicChallengeContent =
  | PublicFakePostContent
  | PublicIsItRealContent
  | PublicFindCluesContent;

export interface PublicChallenge extends Omit<Challenge, 'content'> {
  content: PublicChallengeContent;
}

export interface Challenge {
  id: string;
  slug: string;
  type: ChallengeType;
  difficulty: Difficulty;
  title: string;
  instruction: string;
  content: ChallengeContent;
  skillCategoryIds: SkillCategoryId[];
  xpReward: number;
  isDailyEligible: boolean;
}

export interface ChallengeHint {
  id: string;
  challengeId: string;
  order: number;
  question: string;
  content: {
    body: string;
    bulletQuestions: string[];
  };
  skillCategoryId: SkillCategoryId;
}

export interface DetectiveTip {
  id: string;
  message: string;
  checklist: string[];
}

export interface ChallengeAttemptResult {
  attemptId: string;
  isCorrect: boolean;
  selectedAnswer: string;
  correctAnswer: string;
  explanation: string[];
  xpEarned: number;
  detectiveTip?: DetectiveTip;
}

export interface HomeDashboard {
  greeting: {
    displayName: string;
    levelTitle: string;
    avatarId: string;
  };
  progress: {
    totalXp: number;
    currentLevelXp: number;
    xpToNextLevel: number;
    level: number;
  };
  dailyMission: {
    challengeId: string;
    title: string;
    description: string;
    xpBonus: number;
    completed: boolean;
  };
  continueLearning: {
    challengeId: string | null;
    title: string | null;
  };
  recommendedChallenges: Array<{
    id: string;
    title: string;
    type: ChallengeType;
    reason: string;
  }>;
}

export interface LevelInfo {
  level: number;
  title: string;
  xpRequired: number;
}

export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
}
