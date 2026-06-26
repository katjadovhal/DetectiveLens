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
    levelTitle: 'Internet Detective Level 4',
    avatarId: 'detective-default',
  },
  progress: {
    totalXp: 320,
    currentLevelXp: 320,
    xpToNextLevel: 880,
    level: 4,
  },
  dailyMission: {
    challengeId: 'monkey-001',
    title: 'Daily Mission!',
    description: 'Spot the AI-generated image',
    xpBonus: 100,
    completed: false,
  },
  continueLearning: {
    challengeId: 'monkey-001',
    title: 'Which image is AI-generated?',
  },
};

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? 'Request failed');
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
    detectiveTip: !isCorrect
      ? {
          id: 'trusts_familiar_brands',
          message:
            'You often trust posts from familiar brands without checking whether the content matches what they normally share.',
          checklist: [
            'Check if the message fits the source',
            'Look for unusual or surprising claims',
            "Ask whether the post supports the account's goals",
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
        title: 'Hey Detective!',
        subtitle: "The Internet is full of tricks. Let's learn how to spot them.",
        keyValue: '',
      };
    }
  },

  completeOnboarding: async (level) => {
    try {
      return await request('/onboarding/complete', {
        method: 'POST',
        body: JSON.stringify({ level }),
      });
    } catch {
      return { success: true, redirectTo: '/' };
    }
  },

  getHome: async () => {
    try {
      return await request('/home/demo-user-id');
    } catch {
      return MOCK_HOME;
    }
  },

  getChallenge: async (id) => {
    try {
      return await request(`/challenges/${id}`);
    } catch {
      return { challenge: { ...MOCK_CHALLENGE } };
    }
  },

  startChallenge: async (id) => {
    try {
      return await request(`/challenges/${id}/start`, { method: 'POST' });
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
};

export function escapeHtml(text) {
  return String(text)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}
