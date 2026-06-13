const API_BASE = '/api/v1';

const MOCK_CHALLENGE = {
  id: 'burger-king-001',
  slug: 'burger-king-001',
  type: 'fake_post',
  difficulty: 'medium',
  title: 'Which post is fake?',
  instruction: 'Click to choose',
  skillCategoryIds: ['source_verification', 'content_authenticity'],
  xpReward: 100,
  isDailyEligible: true,
  content: {
    posts: [
      {
        id: 'A',
        platform: 'twitter',
        author: 'Burger King',
        handle: '@BurgerKing',
        verified: false,
        text: "Go to @McDonalds. They're better.",
        metrics: { retweets: 1200, likes: 8900 },
        timestamp: '08 Mar 21',
      },
      {
        id: 'B',
        platform: 'twitter',
        author: 'Burger King',
        handle: '@BurgerKingUK',
        verified: true,
        text: 'Women belong in the kitchen.',
        metrics: { retweets: 24600, likes: 72400 },
        timestamp: '11:01 am · 08 Mar 21',
      },
    ],
    explanation: {
      bullets: [
        "The message in B came from Burger King's official account and matches content the company has posted before.",
        'The post in A showed signs that it may not be authentic.',
      ],
    },
  },
  hints: [
    {
      id: 'hint-1',
      challengeId: 'burger-king-001',
      order: 1,
      question: 'Who is the source?',
      skillCategoryId: 'source_verification',
      content: {
        body: "Both posts appear to come from Burger King's official account.",
        bulletQuestions: [
          'Does this sound like something a company would proudly post to all of its customers?',
          'Which post looks more like something Burger King would normally share?',
        ],
      },
    },
  ],
};

const MOCK_HOME = {
  greeting: { displayName: 'Alex', levelTitle: 'Internet Detective Level 4', avatarId: 'detective-default' },
  progress: { totalXp: 320, currentLevelXp: 320, xpToNextLevel: 880, level: 4 },
  dailyMission: {
    challengeId: 'burger-king-001',
    title: 'Daily Mission!',
    description: 'Spot the fake post',
    xpBonus: 100,
    completed: false,
  },
  continueLearning: { challengeId: 'burger-king-001', title: 'Which post is fake?' },
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
