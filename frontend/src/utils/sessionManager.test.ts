/**
 * Tests for sessionManager utility.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  saveSession,
  loadSession,
  clearSession,
  clearExpiredSessions,
  getAllSessions,
  type PlayerSession,
} from './sessionManager';

describe('sessionManager', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('saveSession', () => {
    it('saves session to localStorage', () => {
      const session: PlayerSession = {
        gameId: 'test-game-123',
        seat: 0,
        playerId: 'player-456',
        playerName: 'Alice',
        joinedAt: Date.now(),
      };

      saveSession(session);

      const stored = localStorage.getItem('thurup_session_test-game-123');
      expect(stored).toBeTruthy();
      expect(JSON.parse(stored!)).toEqual(session);
    });

    it('overwrites existing session', () => {
      const session1: PlayerSession = {
        gameId: 'game1',
        seat: 0,
        playerId: 'player1',
        playerName: 'Alice',
        joinedAt: Date.now(),
      };

      const session2: PlayerSession = {
        gameId: 'game1',
        seat: 1,
        playerId: 'player2',
        playerName: 'Bob',
        joinedAt: Date.now(),
      };

      saveSession(session1);
      saveSession(session2);

      const stored = localStorage.getItem('thurup_session_game1');
      const parsed = JSON.parse(stored!);
      expect(parsed.seat).toBe(1);
      expect(parsed.playerName).toBe('Bob');
    });

    it('handles localStorage errors gracefully', () => {
      // Mock localStorage to throw error
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Quota exceeded');
      });

      const session: PlayerSession = {
        gameId: 'test',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      };

      // Should not throw
      expect(() => saveSession(session)).not.toThrow();

      setItemSpy.mockRestore();
    });
  });

  describe('loadSession', () => {
    it('loads existing session', () => {
      const session: PlayerSession = {
        gameId: 'test-game-789',
        seat: 2,
        playerId: 'player-abc',
        playerName: 'Charlie',
        joinedAt: Date.now(),
      };

      saveSession(session);
      const loaded = loadSession('test-game-789');

      expect(loaded).toEqual(session);
    });

    it('returns null for non-existent session', () => {
      const loaded = loadSession('non-existent-game');
      expect(loaded).toBeNull();
    });

    it('returns null and removes expired session', () => {
      const expiredSession: PlayerSession = {
        gameId: 'expired-game',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now() - (25 * 60 * 60 * 1000), // 25 hours ago
      };

      localStorage.setItem('thurup_session_expired-game', JSON.stringify(expiredSession));

      const loaded = loadSession('expired-game');
      expect(loaded).toBeNull();

      // Verify it was removed
      expect(localStorage.getItem('thurup_session_expired-game')).toBeNull();
    });

    it('returns valid session within expiry', () => {
      const recentSession: PlayerSession = {
        gameId: 'recent-game',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now() - (1 * 60 * 60 * 1000), // 1 hour ago
      };

      saveSession(recentSession);
      const loaded = loadSession('recent-game');

      expect(loaded).not.toBeNull();
      expect(loaded?.gameId).toBe('recent-game');
    });

    it('handles corrupted JSON gracefully', () => {
      localStorage.setItem('thurup_session_corrupted', 'invalid json {');

      const loaded = loadSession('corrupted');
      expect(loaded).toBeNull();
    });
  });

  describe('clearSession', () => {
    it('removes session from localStorage', () => {
      const session: PlayerSession = {
        gameId: 'game-to-clear',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      };

      saveSession(session);
      expect(localStorage.getItem('thurup_session_game-to-clear')).toBeTruthy();

      clearSession('game-to-clear');
      expect(localStorage.getItem('thurup_session_game-to-clear')).toBeNull();
    });

    it('handles clearing non-existent session', () => {
      // Should not throw
      expect(() => clearSession('non-existent')).not.toThrow();
    });

    it('handles localStorage errors gracefully', () => {
      const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Should not throw
      expect(() => clearSession('test')).not.toThrow();

      removeItemSpy.mockRestore();
    });
  });

  describe('clearExpiredSessions', () => {
    it('removes expired sessions', () => {
      const expiredSession: PlayerSession = {
        gameId: 'expired',
        seat: 0,
        playerId: 'player1',
        playerName: 'Old',
        joinedAt: Date.now() - (30 * 60 * 60 * 1000), // 30 hours ago
      };

      const validSession: PlayerSession = {
        gameId: 'valid',
        seat: 1,
        playerId: 'player2',
        playerName: 'New',
        joinedAt: Date.now(),
      };

      saveSession(expiredSession);
      saveSession(validSession);

      clearExpiredSessions();

      expect(localStorage.getItem('thurup_session_expired')).toBeNull();
      expect(localStorage.getItem('thurup_session_valid')).toBeTruthy();
    });

    it('removes corrupted session entries', () => {
      localStorage.setItem('thurup_session_corrupted', 'invalid json');
      localStorage.setItem('thurup_session_valid', JSON.stringify({
        gameId: 'valid',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      }));

      clearExpiredSessions();

      expect(localStorage.getItem('thurup_session_corrupted')).toBeNull();
      expect(localStorage.getItem('thurup_session_valid')).toBeTruthy();
    });

    it('ignores non-session keys', () => {
      localStorage.setItem('other_key', 'some value');
      localStorage.setItem('thurup_session_game', JSON.stringify({
        gameId: 'game',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      }));

      clearExpiredSessions();

      expect(localStorage.getItem('other_key')).toBe('some value');
    });

    it('handles empty localStorage', () => {
      // Should not throw
      expect(() => clearExpiredSessions()).not.toThrow();
    });
  });

  describe('getAllSessions', () => {
    it('returns all active sessions', () => {
      const session1: PlayerSession = {
        gameId: 'game1',
        seat: 0,
        playerId: 'player1',
        playerName: 'Alice',
        joinedAt: Date.now(),
      };

      const session2: PlayerSession = {
        gameId: 'game2',
        seat: 1,
        playerId: 'player2',
        playerName: 'Bob',
        joinedAt: Date.now(),
      };

      saveSession(session1);
      saveSession(session2);

      const sessions = getAllSessions();

      expect(sessions).toHaveLength(2);
      expect(sessions.find(s => s.gameId === 'game1')).toBeTruthy();
      expect(sessions.find(s => s.gameId === 'game2')).toBeTruthy();
    });

    it('returns empty array when no sessions', () => {
      const sessions = getAllSessions();
      expect(sessions).toEqual([]);
    });

    it('skips corrupted entries', () => {
      localStorage.setItem('thurup_session_corrupted', 'invalid');
      localStorage.setItem('thurup_session_valid', JSON.stringify({
        gameId: 'valid',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      }));

      const sessions = getAllSessions();

      expect(sessions).toHaveLength(1);
      expect(sessions[0].gameId).toBe('valid');
    });

    it('ignores non-session keys', () => {
      localStorage.setItem('other_key', 'value');
      localStorage.setItem('thurup_session_game', JSON.stringify({
        gameId: 'game',
        seat: 0,
        playerId: 'player',
        playerName: 'Test',
        joinedAt: Date.now(),
      }));

      const sessions = getAllSessions();

      expect(sessions).toHaveLength(1);
    });

    it('includes expired sessions', () => {
      const expiredSession: PlayerSession = {
        gameId: 'expired',
        seat: 0,
        playerId: 'player',
        playerName: 'Old',
        joinedAt: Date.now() - (30 * 60 * 60 * 1000),
      };

      saveSession(expiredSession);
      const sessions = getAllSessions();

      // getAllSessions doesn't filter by expiry
      expect(sessions).toHaveLength(1);
      expect(sessions[0].gameId).toBe('expired');
    });
  });
});
