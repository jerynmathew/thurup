/**
 * Tests for admin API service.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { adminApi } from './admin';
import * as clientModule from './client';

// Mock the createAuthenticatedClient function
vi.mock('./client', () => ({
  createAuthenticatedClient: vi.fn(() => ({
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  })),
}));

describe('adminApi', () => {
  const mockUsername = 'admin';
  const mockPassword = 'password';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createClient', () => {
    it('creates authenticated client with credentials', () => {
      const createAuthSpy = vi.spyOn(clientModule, 'createAuthenticatedClient');

      adminApi.createClient(mockUsername, mockPassword);

      expect(createAuthSpy).toHaveBeenCalledWith(mockUsername, mockPassword);
    });
  });

  describe('getHealth', () => {
    it('fetches server health', async () => {
      const mockHealth = {
        status: 'healthy',
        uptime_seconds: 3600,
        active_sessions: 5,
        total_connections: 10,
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockHealth }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.getHealth(mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/admin/health');
      expect(result).toEqual(mockHealth);
    });
  });

  describe('listSessions', () => {
    it('fetches active sessions', async () => {
      const mockSessions = [
        { game_id: 'game1', mode: '28', state: 'playing' },
        { game_id: 'game2', mode: '56', state: 'lobby' },
      ];

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockSessions }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.listSessions(mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/admin/sessions');
      expect(result).toEqual(mockSessions);
    });
  });

  describe('getSessionDetail', () => {
    it('fetches session detail for game', async () => {
      const gameId = 'test-game-123';
      const mockDetail = {
        game_id: gameId,
        players: [],
        state: 'bidding',
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockDetail }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.getSessionDetail(gameId, mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith(`/api/v1/admin/sessions/${gameId}/detail`);
      expect(result).toEqual(mockDetail);
    });
  });

  describe('getDatabaseStats', () => {
    it('fetches database statistics', async () => {
      const mockStats = {
        total_games: 100,
        total_players: 400,
        total_snapshots: 500,
        database_size_mb: 15.5,
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockStats }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.getDatabaseStats(mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/admin/database/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('forceSave', () => {
    it('triggers manual save for game', async () => {
      const gameId = 'test-game-456';
      const mockResponse = { ok: true, message: 'Game saved' };

      const mockClient = {
        post: vi.fn().mockResolvedValue({ data: mockResponse }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.forceSave(gameId, mockUsername, mockPassword);

      expect(mockClient.post).toHaveBeenCalledWith(`/api/v1/admin/sessions/${gameId}/save`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteSession', () => {
    it('deletes game session', async () => {
      const gameId = 'test-game-789';
      const mockResponse = { ok: true };

      const mockClient = {
        delete: vi.fn().mockResolvedValue({ data: mockResponse }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.deleteSession(gameId, mockUsername, mockPassword);

      expect(mockClient.delete).toHaveBeenCalledWith(`/api/v1/admin/sessions/${gameId}`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('triggerCleanup', () => {
    it('triggers database cleanup', async () => {
      const mockResponse = { ok: true, deleted_games: 5 };

      const mockClient = {
        post: vi.fn().mockResolvedValue({ data: mockResponse }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.triggerCleanup(mockUsername, mockPassword);

      expect(mockClient.post).toHaveBeenCalledWith('/api/v1/admin/maintenance/cleanup');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('listGameHistory', () => {
    it('fetches game history with default pagination', async () => {
      const mockHistory = [
        { game_id: 'game1', created_at: '2025-01-01' },
        { game_id: 'game2', created_at: '2025-01-02' },
      ];

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockHistory }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.listGameHistory(mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/admin/games/history', {
        params: { limit: 50, offset: 0 },
      });
      expect(result).toEqual(mockHistory);
    });

    it('fetches game history with custom pagination', async () => {
      const mockHistory = [];

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockHistory }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      await adminApi.listGameHistory(mockUsername, mockPassword, 100, 50);

      expect(mockClient.get).toHaveBeenCalledWith('/api/v1/admin/games/history', {
        params: { limit: 100, offset: 50 },
      });
    });
  });

  describe('getGameRounds', () => {
    it('fetches rounds for specific game', async () => {
      const gameId = 'test-game-abc';
      const mockRounds = {
        game_id: gameId,
        rounds: [
          { round_number: 1, winner: 0 },
          { round_number: 2, winner: 2 },
        ],
      };

      const mockClient = {
        get: vi.fn().mockResolvedValue({ data: mockRounds }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      const result = await adminApi.getGameRounds(gameId, mockUsername, mockPassword);

      expect(mockClient.get).toHaveBeenCalledWith(`/api/v1/admin/games/${gameId}/rounds`);
      expect(result).toEqual(mockRounds);
    });
  });

  describe('error handling', () => {
    it('handles authentication errors', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue({
          status: 401,
          message: 'Unauthorized',
        }),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      await expect(adminApi.getHealth('wrong', 'credentials')).rejects.toMatchObject({
        status: 401,
      });
    });

    it('handles network errors', async () => {
      const mockClient = {
        get: vi.fn().mockRejectedValue(new Error('Network error')),
      };
      vi.spyOn(clientModule, 'createAuthenticatedClient').mockReturnValue(mockClient as any);

      await expect(adminApi.listSessions(mockUsername, mockPassword)).rejects.toThrow('Network error');
    });
  });
});
