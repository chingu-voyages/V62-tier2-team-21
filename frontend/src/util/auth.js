const SESSION_STORAGE_KEY = "learning-path-session";

export function saveSession(session, { remember = true } = {}) {
  const store = remember ? localStorage : sessionStorage;
  const other = remember ? sessionStorage : localStorage;
  store.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  other.removeItem(SESSION_STORAGE_KEY);
}

export function getSession() {
  try {
    const raw =
      localStorage.getItem(SESSION_STORAGE_KEY) ??
      sessionStorage.getItem(SESSION_STORAGE_KEY);
    const session = JSON.parse(raw);
    if (!session?.session_token || !session?.expires_at) return null;
    if (new Date(session.expires_at) <= new Date()) {
      clearSession();
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
}

export function authHeader() {
  const session = getSession();
  return session ? { Authorization: `Bearer ${session.session_token}` } : {};
}
