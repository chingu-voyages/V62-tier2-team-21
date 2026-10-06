const SESSION_STORAGE_KEY = "learning-path-session";

export function saveSession(session) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function getSession() {
  try {
    const session = JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY));
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
}
