import { renderHeader } from './header.js';
import { renderWelcome } from './pages/welcome.js';
import { renderHome } from './pages/home.js';
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

function matchRoute(path) {
  if (path === '/onboarding/welcome') return { name: 'welcome' };
  if (path === '/') return { name: 'home' };
  const challengeMatch = path.match(/^\/challenges\/fake-post\/(.+)$/);
  if (challengeMatch) return { name: 'challenge', params: { id: challengeMatch[1] } };
  if (PLACEHOLDERS[path]) return { name: 'placeholder', params: PLACEHOLDERS[path] };
  return { name: 'welcome' };
}

async function navigate(path, push = true) {
  const route = matchRoute(path);
  const main = document.getElementById('app-main');

  if (route.name === 'welcome') {
    await renderHeader(false);
    await renderWelcome(main);
  } else {
    await renderHeader(true);
    if (route.name === 'home') {
      await renderHome(main);
    } else if (route.name === 'challenge') {
      await renderChallenge(main, route.params.id);
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

export function initRouter() {
  document.addEventListener('click', handleLinkClick);
  window.addEventListener('popstate', (event) => {
    const path = event.state?.path ?? window.location.pathname;
    navigate(path, false);
  });

  const initialPath = window.location.pathname || '/onboarding/welcome';
  navigate(initialPath, false);
}
