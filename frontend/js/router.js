import { renderHeader } from './header.js';
import { renderStart } from './pages/start.js';
import { renderOnboarding } from './pages/onboarding.js';
import { renderSelectUser } from './pages/select-user.js';
import { renderChallengeStaging } from './pages/challenge-staging.js';
import { renderChallenge } from './pages/challenge.js';
import { renderPlaceholder } from './pages/placeholder.js';

const PLACEHOLDERS = {
  '/progress/xp': {
    title: 'XP & Levels',
    description: 'Track your detective rank and points. Coming in Sprint 3.',
  },
  '/profile': {
    title: 'Profile',
    description: 'Customize your avatar and display name. Coming in Sprint 3.',
  },
  '/profile/statistics': {
    title: 'Statistics',
    description: 'View your total XP, challenges played, and accuracy. Coming in Sprint 3.',
  },
  '/profile/settings': {
    title: 'Settings',
    description: 'Notifications, sound, and privacy controls. Coming in Sprint 3.',
  },
  '/profile/help': {
    title: 'Help & Support',
    description: 'FAQ, contact, and feedback. Coming in Sprint 3.',
  },
};

function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

function matchRoute(path) {
  if (path === '/' || path === '') return { name: 'start' };
  if (path === '/onboarding') return { name: 'onboarding' };
  if (path === '/select-user') return { name: 'select-user' };
  if (path === '/challenge-staging') return { name: 'challenge-staging' };
  const challengeMatch = path.match(/^\/challenges\/fake-post\/(.+)$/);
  if (challengeMatch) return { name: 'challenge', params: { id: challengeMatch[1] } };
  if (PLACEHOLDERS[path]) return { name: 'placeholder', params: PLACEHOLDERS[path] };
  return { name: 'start' };
}

async function navigate(path, push = true) {
  const route = matchRoute(path);
  const main = document.getElementById('app-main');

  if (route.name === 'start') {
    await renderHeader(false);
    await renderStart(main);
  } else if (route.name === 'onboarding') {
    await renderHeader(false);
    await renderOnboarding(main);
  } else if (route.name === 'select-user') {
    await renderHeader(false);
    await renderSelectUser(main);
  } else if (route.name === 'challenge-staging') {
    const userId = getQueryParam('userId');
    if (!userId) {
      window.location.href = '/';
      return;
    }
    await renderHeader(true);
    await renderChallengeStaging(main, userId);
  } else {
    await renderHeader(true);
    if (route.name === 'challenge') {
      const userId = getQueryParam('userId');
      const mode = getQueryParam('mode');
      await renderChallenge(main, route.params.id, userId, mode);
    } else if (route.name === 'placeholder') {
      renderPlaceholder(main, route.params.title, route.params.description);
    }
  }

  if (push) {
    history.pushState({ path }, '', path);
  }
}

function handleLinkClick(event) {
  const link = event.target.closest('[data-link]');
  if (!link) return;
  const href = link.getAttribute('href');
  if (!href || href.startsWith('http')) return;
  event.preventDefault();
  navigate(href);
}

export async function initRouter() {
  document.addEventListener('click', handleLinkClick);
  window.addEventListener('popstate', (event) => {
    const path = event.state?.path ?? window.location.pathname;
    navigate(path, false);
  });

  let initialPath = window.location.pathname;

  // Default to start page
  navigate(initialPath || '/', false);
}
