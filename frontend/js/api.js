const API_BASE = '/api/v1';

const MOCK_CHALLENGE = {
  id: 'monkey-001',
  slug: 'monkey-001',
  type: 'fake_post',
  difficulty: 'easy',
  title: 'Which image is AI-generated?',
  instruction: 'Click to choose',
  skillCategoryIds: ['content_authenticity'],
  xpReward: 100,
  isDailyEligible: true,
  content: {
    posts: [
      {
        id: 'A',
        imageUrl: '/assets/challenges/monkey/6a.jpg',
      },
      {
        id: 'B',
        imageUrl: '/assets/challenges/monkey/6.png',
      },
    ],
    correctPostId: 'B',
    explanation: {
      bullets: [
        'Image B was generated using AI.',
        'Image A is a real photograph.',
        'Look closely at the eyes, fur, and lighting. AI images can look cute, but sometimes small details feel too perfect or unnatural.',
      ],
    },
  },
  hints: [
    {
      id: 'hint-1',
      challengeId: 'monkey-001',
      order: 1,
      question: 'Look at the details',
      skillCategoryId: 'content_authenticity',
      content: {
        body: 'AI-generated images often have small visual clues, especially in eyes, fur, hands, shadows, or background details.',
        bulletQuestions: [
          'Do the eyes look too shiny or too perfect?',
          'Does the fur look natural everywhere?',
          'Does the background make sense?',
        ],
      },
    },
  ],
};

const MOCK_HOME = {
  greeting: {
    displayName: 'Alex',
    levelTitle: 'Internet Detective Level 1',
    avatarId: 'avatar-detective-1',
  },
  progress: {
    totalXp: 320,
    currentLevelXp: 320,
    xpToNextLevel: 180,
    levelXpRequired: 500,
    level: 1,
  },
  dailyMission: {
    challengeId: 'monkey-001',
    title: 'Daily Mission!',
    description: 'Spot the fake post',
    xpBonus: 100,
    completed: false,
  },
};

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    const detail = err.detail;
    const message =
      (typeof detail === 'string' && detail) ||
      detail?.message ||
      err.message ||
      res.statusText ||
      'Request failed';
    throw new Error(message);
  }
  return res.json();
}

function mockSubmitFakePost(body) {
  const correctPostId = 'A';
  const isCorrect = body.selectedPostId === correctPostId;
  return {
    attemptId: 'mock-session',
    isCorrect,
    selectedAnswer: body.selectedPostId,
    correctAnswer: correctPostId,
    explanation: MOCK_CHALLENGE.content.explanation.bullets,
    xpEarned: isCorrect ? Math.max(0, 100 - body.hintsUsed * 10) : 0,
    leveledUp: false,
    currentLevel: 1,
    detectiveTip: !isCorrect
      ? {
          id: 'general_visual_check',
          message:
            'A useful check for this kind of challenge is whether small details stay consistent across the whole picture.',
          checklist: [
            'Compare texture and edges in both posts',
            'Look for details that feel too perfect or inconsistent',
            'Ask whether the whole scene could work in real life',
          ],
        }
      : null,
  };
}

export const api = {
  getWelcome: async () => {
    try {
      return await request('/onboarding/welcome');
    } catch {
      return {
        title: 'Welcome to DetectiveLens!',
        subtitle: 'Some pictures lie. Learn to spot the cues and catch them all.',
        keyValue: '',
      };
    }
  },

  createUser: async (userData) => {
    try {
      return await request('/onboarding/create-user', {
        method: 'POST',
        body: JSON.stringify(userData),
      });
    } catch (err) {
      throw err;
    }
  },

  getUsers: async () => {
    try {
      return await request('/users');
    } catch {
      return { users: [] };
    }
  },

  getHome: async (userId) => {
    try {
      return await request(`/home/${userId}`);
    } catch {
      return MOCK_HOME;
    }
  },

  getProfile: async (userId) => {
    try {
      return await request(`/profiles/${userId}`);
    } catch {
      return {
        profile: {
          displayName: 'Detective',
          avatarId: 'avatar-detective-1',
          currentLevel: 1,
          totalXp: 0,
          currentLevelXp: 0,
          completedChallengeCount: 0,
          onboardingCompleted: false,
          colorBlindness: false,
        },
      };
    }
  },

  updateProfile: async (userId, body) => {
    return request(`/profiles/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },

  getChallenge: async (id) => {
    try {
      return await request(`/challenges/${id}`);
    } catch {
      return { challenge: { ...MOCK_CHALLENGE } };
    }
  },

  getDailyChallenge: async (userId) => {
    try {
      return await request(`/challenges/users/${userId}/daily`);
    } catch {
      return { challenge: { ...MOCK_CHALLENGE }, completed: false };
    }
  },

  getNextPracticeChallenge: async (userId) => {
    try {
      return await request(`/challenges/users/${userId}/next-practice`);
    } catch {
      return { challenge: { ...MOCK_CHALLENGE }, message: 'Error loading challenge' };
    }
  },

  startChallenge: async (id, userId) => {
    try {
      return await request(`/challenges/${id}/start/${userId}`, { method: 'POST' });
    } catch {
      return { sessionId: 'mock-session', challengeId: id };
    }
  },

  submitFakePost: async (sessionId, body) => {
    try {
      return await request(`/challenges/sessions/${sessionId}/submit`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
    } catch {
      return mockSubmitFakePost(body);
    }
  },

  requestHint: async (challengeId, body) => {
    return request(`/challenges/${challengeId}/hint`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
};

export function escapeHtml(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
