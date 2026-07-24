import { renderHeader } from './header.js?v=hints-3';
import { renderStart } from './pages/start.js?v=hints-3';
import { renderOnboarding } from './pages/onboarding.js?v=hints-3';
import { renderSelectUser } from './pages/select-user.js?v=hints-3';
import { renderChallengeStaging } from './pages/challenge-staging.js?v=hints-3';
import { renderChallenge } from './pages/challenge.js?v=hints-3';
import { renderProfile } from './pages/profile.js?v=hints-3';
import { renderSettings } from './pages/settings.js?v=hints-3';
import { renderPlaceholder } from './pages/placeholder.js?v=hints-3';
import { resolveActiveUserId, setLastUserId, withUserId } from './session.js?v=hints-3';

const PLACEHOLDERS = {
  '/progress/xp': {
    title: 'XP & Levels',
    description: 'Track your detective rank and points. Coming in Sprint 3.',
  },
  '/profile/statistics': {
    title: 'Statistics',
    description: 'View your total XP, challenges played, and accuracy. Coming in Sprint 3.',
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
  if (path === '/profile') return { name: 'profile' };
  if (path === '/profile/settings') return { name: 'settings' };
  const challengeMatch = path.match(/^\/challenges\/fake-post\/(.+)$/);
  if (challengeMatch) return { name: 'challenge', params: { id: challengeMatch[1] } };
  if (PLACEHOLDERS[path]) return { name: 'placeholder', params: PLACEHOLDERS[path] };
  return { name: 'start' };
}

async function navigate(path, push = true) {
  const rawPath = path.startsWith('/') ? path : `/${path}`;
  const pathname = rawPath.split('?')[0];
  const route = matchRoute(pathname);
  const main = document.getElementById('app-main');
  const userId = resolveActiveUserId(rawPath);

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
    if (!userId) {
      window.location.href = '/';
      return;
    }
    setLastUserId(userId);
    await renderHeader(true);
    await renderChallengeStaging(main, userId);
  } else if (route.name === 'profile') {
    if (!userId) {
      window.location.href = '/';
      return;
    }
    setLastUserId(userId);
    await renderHeader(true);
    await renderProfile(main);
  } else if (route.name === 'settings') {
    if (!userId) {
      window.location.href = '/';
      return;
    }
    setLastUserId(userId);
    await renderHeader(true);
    await renderSettings(main);
  } else {
    await renderHeader(true);
    if (route.name === 'challenge') {
      const mode = new URL(rawPath, window.location.origin).searchParams.get('mode') || getQueryParam('mode');
      if (userId) setLastUserId(userId);
      await renderChallenge(main, route.params.id, userId, mode);
    } else if (route.name === 'placeholder') {
      renderPlaceholder(main, route.params.title, route.params.description);
    }
  }

  if (push) {
    let urlPath = rawPath;
    if (
      userId &&
      (route.name === 'profile' || route.name === 'challenge-staging' || route.name === 'settings')
    ) {
      urlPath = withUserId(pathname, userId);
    }
    history.pushState({ path: urlPath }, '', urlPath);
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
  window.addEventListener('popstate', () => {
    navigate(window.location.pathname + window.location.search, false);
  });

  const initialPath = window.location.pathname;
  const search = window.location.search || '';

  navigate((initialPath + search) || '/', false);
}
