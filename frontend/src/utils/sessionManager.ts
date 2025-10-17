/**
 * Session Manager - LocalStorage-based player session persistence
 *
 * Manages player session data to enable:
 * - Page refresh recovery
 * - Auto-rejoin after disconnect
 * - Session cleanup
 */

export interface PlayerSession {
  gameId: string;
  seat: number;
  playerId: string;
  playerName: string;
  joinedAt: number; // timestamp
}

const STORAGE_KEY_PREFIX = 'thurup_session_';
const SESSION_EXPIRY_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Save player session to localStorage
 */
export function saveSession(session: PlayerSession): void {
  try {
    const key = `${STORAGE_KEY_PREFIX}${session.gameId}`;
    localStorage.setItem(key, JSON.stringify(session));
  } catch (error) {
    console.error('[SessionManager] Failed to save session:', error);
  }
}

/**
 * Load player session from localStorage
 * Returns null if not found or expired
 */
export function loadSession(gameId: string): PlayerSession | null {
  try {
    const key = `${STORAGE_KEY_PREFIX}${gameId}`;
    const data = localStorage.getItem(key);

    if (!data) {
      return null;
    }

    const session: PlayerSession = JSON.parse(data);

    // Check if session is expired
    const age = Date.now() - session.joinedAt;
    if (age > SESSION_EXPIRY_MS) {
      console.log('[SessionManager] Session expired, removing');
      clearSession(gameId);
      return null;
    }

    return session;
  } catch (error) {
    console.error('[SessionManager] Failed to load session:', error);
    return null;
  }
}

/**
 * Clear session for a specific game
 */
export function clearSession(gameId: string): void {
  try {
    const key = `${STORAGE_KEY_PREFIX}${gameId}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.error('[SessionManager] Failed to clear session:', error);
  }
}

/**
 * Clear all expired sessions
 * Call this periodically or on app init
 */
export function clearExpiredSessions(): void {
  try {
    const keys = Object.keys(localStorage);
    const now = Date.now();

    for (const key of keys) {
      if (!key.startsWith(STORAGE_KEY_PREFIX)) {
        continue;
      }

      try {
        const data = localStorage.getItem(key);
        if (!data) continue;

        const session: PlayerSession = JSON.parse(data);
        const age = now - session.joinedAt;

        if (age > SESSION_EXPIRY_MS) {
          localStorage.removeItem(key);
          console.log('[SessionManager] Removed expired session:', session.gameId);
        }
      } catch {
        // Invalid JSON, remove it
        localStorage.removeItem(key);
      }
    }
  } catch (error) {
    console.error('[SessionManager] Failed to clear expired sessions:', error);
  }
}

/**
 * Get all active sessions (for debugging/admin)
 */
export function getAllSessions(): PlayerSession[] {
  const sessions: PlayerSession[] = [];

  try {
    const keys = Object.keys(localStorage);

    for (const key of keys) {
      if (!key.startsWith(STORAGE_KEY_PREFIX)) {
        continue;
      }

      try {
        const data = localStorage.getItem(key);
        if (!data) continue;

        const session: PlayerSession = JSON.parse(data);
        sessions.push(session);
      } catch {
        // Skip invalid entries
      }
    }
  } catch (error) {
    console.error('[SessionManager] Failed to get all sessions:', error);
  }

  return sessions;
}
