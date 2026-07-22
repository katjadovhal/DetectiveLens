const LAST_USER_KEY = 'lastUserId';

export function getQueryUserId() {
  const params = new URLSearchParams(window.location.search);
  const userId = params.get('userId');
  return userId && userId.trim() ? userId.trim() : null;
}

export function getLastUserId() {
  try {
    const value = localStorage.getItem(LAST_USER_KEY);
    return value && value.trim() ? value.trim() : null;
  } catch {
    return null;
  }
}

export function setLastUserId(userId) {
  if (!userId) return;
  try {
    localStorage.setItem(LAST_USER_KEY, userId);
  } catch {
    /* ignore quota / private mode */
  }
}

export function clearLastUserId() {
  try {
    localStorage.removeItem(LAST_USER_KEY);
  } catch {
    /* ignore */
  }
}

/**
 * Resolve active user: URL query first, then localStorage.
 * Optional `pathOrUrl` lets the router resolve userId from a target href
 * before history.pushState updates window.location.
 * @param {string} [pathOrUrl]
 * @returns {string|null}
 */
export function resolveActiveUserId(pathOrUrl) {
  if (pathOrUrl) {
    try {
      const url = new URL(pathOrUrl, window.location.origin);
      const fromTarget = url.searchParams.get('userId');
      if (fromTarget && fromTarget.trim()) return fromTarget.trim();
    } catch {
      /* fall through */
    }
  }
  return getQueryUserId() ?? getLastUserId();
}

export function withUserId(path, userId) {
  if (!userId) return path;
  const url = new URL(path, window.location.origin);
  url.searchParams.set('userId', userId);
  return `${url.pathname}${url.search}`;
}

/**
 * Load profile for a user id. On failure, clear stale lastUserId when it matches.
 * @returns {Promise<{profile: object, home?: object}|null>}
 */
export async function loadValidUser(userId, { api, includeHome = false } = {}) {
  if (!userId || !api) return null;

  const invalidate = () => {
    if (getLastUserId() === userId) clearLastUserId();
    return null;
  };

  try {
    if (includeHome) {
      const [profileRes, home] = await Promise.all([
        api.getProfile(userId),
        api.getHome(userId),
      ]);
      const profile = profileRes?.profile;
      if (!profile || (!profile.userId && !profile.id)) return invalidate();
      return { profile, home };
    }

    const { profile } = await api.getProfile(userId);
    if (!profile || (!profile.userId && !profile.id)) return invalidate();
    return { profile };
  } catch {
    return invalidate();
  }
}
