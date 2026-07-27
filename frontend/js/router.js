import { renderHeader } from './header.js?v=hq-5';
import { renderStart } from './pages/start.js?v=hq-1';
import { renderOnboarding } from './pages/onboarding.js?v=hq-1';
import { renderSelectUser } from './pages/select-user.js?v=hq-1';
import { renderChallengeStaging } from './pages/challenge-staging.js?v=hq-4';
import { renderChallenge } from './pages/challenge.js?v=hq-4';
import { renderProfile } from './pages/profile.js?v=hq-2';
import { renderSettings } from './pages/settings.js?v=hq-1';
import { renderDetectiveHQ } from './pages/detective-hq.js?v=hq-1';
import { resolveActiveUserId, setLastUserId, withUserId } from './session.js?v=hq-1';

function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

function matchRoute(path) {
  if (path === '/' || path === '') return { name: 'start' };
  if (path === '/onboarding') return { name: 'onboarding' };
  if (path === '/select-user') return { name: 'select-user' };
  if (path === '/challenge-staging') return { name: 'challenge-staging' };
  if (path === '/detective-hq') return { name: 'detective-hq' };
  if (path === '/profile') return { name: 'profile' };
  if (path === '/profile/settings') return { name: 'settings' };
  const challengeMatch = path.match(/^\/challenges\/fake-post\/(.+)$/);
  if (challengeMatch) return { name: 'challenge', params: { id: challengeMatch[1] } };
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
  } else if (route.name === 'detective-hq') {
    if (!userId) {
      window.location.href = '/';
      return;
    }
    setLastUserId(userId);
    await renderHeader(true);
    await renderDetectiveHQ(main);
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
  } else if (route.name === 'challenge') {
    await renderHeader(true);
    const mode = new URL(rawPath, window.location.origin).searchParams.get('mode') || getQueryParam('mode');
    if (userId) setLastUserId(userId);
    await renderChallenge(main, route.params.id, userId, mode);
  }

  if (push) {
    let urlPath = rawPath;
    if (
      userId &&
      (route.name === 'profile' ||
        route.name === 'challenge-staging' ||
        route.name === 'settings' ||
        route.name === 'detective-hq')
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
