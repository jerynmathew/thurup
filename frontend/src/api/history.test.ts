/**
 * Tests for history API service.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { historyApi } from './history';
import { apiClient } from './client';

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('historyApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listGames', () => {
    it('fetches game list without filters', async () => {
      const mockGames = [
        { game_id: 'game1', mode: '28', state: 'completed' },
        { game_id: 'game2', mode: '56', state: 'lobby' },
      ];
      (apiClient.get as any).mockResolvedValue({ data: mockGames });

      const result = await historyApi.listGames();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/games', { params: undefined });
      expect(result).toEqual(mockGames);
    });

    it('fetches games with state filter', async () => {
      const mockGames = [{ game_id: 'game1', state: 'completed' }];
      (apiClient.get as any).mockResolvedValue({ data: mockGames });

      await historyApi.listGames({ state: 'completed' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/games', {
        params: { state: 'completed' },
      });
    });

    it('fetches games with mode filter', async () => {
      const mockGames = [{ game_id: 'game1', mode: '28' }];
      (apiClient.get as any).mockResolvedValue({ data: mockGames });

      await historyApi.listGames({ mode: '28' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/games', {
        params: { mode: '28' },
      });
    });

    it('fetches games with pagination', async () => {
      const mockGames = [];
      (apiClient.get as any).mockResolvedValue({ data: mockGames });

      await historyApi.listGames({ limit: 10, offset: 20 });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/games', {
        params: { limit: 10, offset: 20 },
      });
    });

    it('fetches games with all filters', async () => {
      const mockGames = [];
      (apiClient.get as any).mockResolvedValue({ data: mockGames });

      await historyApi.listGames({
        state: 'playing',
        mode: '56',
        limit: 50,
        offset: 0,
      });

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/games', {
        params: {
          state: 'playing',
          mode: '56',
          limit: 50,
          offset: 0,
        },
      });
    });
  });

  describe('getGameDetail', () => {
    it('fetches game detail', async () => {
      const gameId = 'test-game-123';
      const mockDetail = {
        game_id: gameId,
        mode: '28',
        players: [],
        snapshots: [],
      };
      (apiClient.get as any).mockResolvedValue({ data: mockDetail });

      const result = await historyApi.getGameDetail(gameId);

      expect(apiClient.get).toHaveBeenCalledWith(`/api/v1/history/games/${gameId}`);
      expect(result).toEqual(mockDetail);
    });

    it('handles non-existent game', async () => {
      (apiClient.get as any).mockRejectedValue({
        status: 404,
        message: 'Game not found',
      });

      await expect(historyApi.getGameDetail('non-existent')).rejects.toMatchObject({
        status: 404,
      });
    });
  });

  describe('getSnapshot', () => {
    it('fetches specific snapshot', async () => {
      const gameId = 'test-game-456';
      const snapshotId = 5;
      const mockSnapshot = {
        snapshot_id: snapshotId,
        game_state: {},
        created_at: '2025-01-01',
      };
      (apiClient.get as any).mockResolvedValue({ data: mockSnapshot });

      const result = await historyApi.getSnapshot(gameId, snapshotId);

      expect(apiClient.get).toHaveBeenCalledWith(
        `/api/v1/history/games/${gameId}/snapshots/${snapshotId}`
      );
      expect(result).toEqual(mockSnapshot);
    });

    it('handles invalid snapshot ID', async () => {
      (apiClient.get as any).mockRejectedValue({
        status: 404,
        message: 'Snapshot not found',
      });

      await expect(historyApi.getSnapshot('game1', 999)).rejects.toMatchObject({
        status: 404,
      });
    });
  });

  describe('getGameReplay', () => {
    it('fetches game replay data', async () => {
      const gameId = 'test-game-789';
      const mockReplay = {
        game_id: gameId,
        snapshots: [
          { state: 'lobby', timestamp: '2025-01-01' },
          { state: 'bidding', timestamp: '2025-01-02' },
        ],
      };
      (apiClient.get as any).mockResolvedValue({ data: mockReplay });

      const result = await historyApi.getGameReplay(gameId);

      expect(apiClient.get).toHaveBeenCalledWith(`/api/v1/history/games/${gameId}/replay`);
      expect(result).toEqual(mockReplay);
    });

    it('handles games with no replay data', async () => {
      (apiClient.get as any).mockRejectedValue({
        status: 404,
        message: 'No replay data available',
      });

      await expect(historyApi.getGameReplay('no-replay')).rejects.toMatchObject({
        status: 404,
      });
    });
  });

  describe('getStats', () => {
    it('fetches game history statistics', async () => {
      const mockStats = {
        total_games: 150,
        games_by_mode: { '28': 100, '56': 50 },
        games_by_state: { completed: 120, abandoned: 30 },
        total_rounds_played: 500,
      };
      (apiClient.get as any).mockResolvedValue({ data: mockStats });

      const result = await historyApi.getStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/history/stats');
      expect(result).toEqual(mockStats);
    });

    it('handles empty statistics', async () => {
      const mockStats = {
        total_games: 0,
        games_by_mode: {},
        games_by_state: {},
        total_rounds_played: 0,
      };
      (apiClient.get as any).mockResolvedValue({ data: mockStats });

      const result = await historyApi.getStats();

      expect(result.total_games).toBe(0);
    });
  });

  describe('error handling', () => {
    it('handles network errors', async () => {
      (apiClient.get as any).mockRejectedValue(new Error('Network error'));

      await expect(historyApi.listGames()).rejects.toThrow('Network error');
    });

    it('handles API errors', async () => {
      (apiClient.get as any).mockRejectedValue({
        status: 500,
        message: 'Internal server error',
      });

      await expect(historyApi.getStats()).rejects.toMatchObject({
        status: 500,
      });
    });
  });
});
