/**
 * Tests for game API service.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { gameApi } from './game';
import { apiClient } from './client';

// Mock the apiClient
vi.mock('./client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('gameApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('createGame', () => {
    it('creates a 28 game with 4 seats', async () => {
      const mockResponse = {
        data: {
          game_id: 'test-game-id',
          short_code: 'test-code',
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.createGame('28', 4);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/game/create', {
        mode: '28',
        seats: 4,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('creates a 56 game with 6 seats', async () => {
      const mockResponse = {
        data: {
          game_id: 'test-game-id-56',
          short_code: 'test-code-56',
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.createGame('56', 6);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/game/create', {
        mode: '56',
        seats: 6,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('handles API errors', async () => {
      const mockError = new Error('Network error');
      (apiClient.post as any).mockRejectedValue(mockError);

      await expect(gameApi.createGame('28', 4)).rejects.toThrow('Network error');
    });
  });

  describe('getGame', () => {
    it('fetches game state successfully', async () => {
      const mockGameState = {
        game_id: 'test-game',
        mode: '28',
        seats: 4,
        state: 'lobby',
        players: [],
      };
      const mockResponse = { data: mockGameState };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await gameApi.getGame('test-game');

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/game/test-game');
      expect(result).toEqual(mockGameState);
    });

    it('handles non-existent game', async () => {
      (apiClient.get as any).mockRejectedValue({
        status: 404,
        message: 'Game not found',
      });

      await expect(gameApi.getGame('non-existent')).rejects.toMatchObject({
        status: 404,
      });
    });
  });

  describe('joinGame', () => {
    it('joins game as human player', async () => {
      const mockResponse = {
        data: {
          seat: 0,
          player_id: 'player-123',
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.joinGame('test-game', 'Alice', false);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/join',
        {
          name: 'Alice',
          is_bot: false,
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('joins game as bot player', async () => {
      const mockResponse = {
        data: {
          seat: 1,
          player_id: 'bot-456',
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.joinGame('test-game', 'Bot 1', true);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/join',
        {
          name: 'Bot 1',
          is_bot: true,
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('defaults to human player when isBot not specified', async () => {
      const mockResponse = {
        data: {
          seat: 2,
          player_id: 'player-789',
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      await gameApi.joinGame('test-game', 'Bob');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/join',
        {
          name: 'Bob',
          is_bot: false,
        }
      );
    });
  });

  describe('startGame', () => {
    it('starts game with default dealer', async () => {
      const mockResponse = { data: { ok: true } };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.startGame('test-game');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/start',
        {
          dealer: 0,
        }
      );
      expect(result).toEqual({ ok: true });
    });

    it('starts game with custom dealer', async () => {
      const mockResponse = { data: { ok: true } };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.startGame('test-game', 2);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/start',
        {
          dealer: 2,
        }
      );
      expect(result).toEqual({ ok: true });
    });
  });

  describe('placeBid', () => {
    it('places numerical bid', async () => {
      const mockResponse = {
        data: { ok: true, msg: 'Bid placed' },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.placeBid('test-game', 0, 15);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/bid',
        { value: 15 },
        { params: { seat: 0 } }
      );
      expect(result).toEqual({ ok: true, msg: 'Bid placed' });
    });

    it('places pass bid (null)', async () => {
      const mockResponse = {
        data: { ok: true, msg: 'Pass' },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.placeBid('test-game', 1, null);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/bid',
        { value: null },
        { params: { seat: 1 } }
      );
      expect(result).toEqual({ ok: true, msg: 'Pass' });
    });

    it('handles invalid bid', async () => {
      (apiClient.post as any).mockRejectedValue({
        status: 400,
        message: 'Bid out of range',
      });

      await expect(gameApi.placeBid('test-game', 0, 99)).rejects.toMatchObject({
        status: 400,
      });
    });
  });

  describe('chooseTrump', () => {
    it('chooses trump suit', async () => {
      const mockResponse = {
        data: { ok: true, msg: 'Trump set' },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.chooseTrump('test-game', 2, '♠');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/choose_trump',
        { suit: '♠' },
        { params: { seat: 2 } }
      );
      expect(result).toEqual({ ok: true, msg: 'Trump set' });
    });

    it('handles all suits', async () => {
      const suits = ['♠', '♥', '♦', '♣'] as const;
      const mockResponse = {
        data: { ok: true, msg: 'Trump set' },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      for (const suit of suits) {
        await gameApi.chooseTrump('test-game', 0, suit);
        expect(apiClient.post).toHaveBeenCalledWith(
          '/api/v1/game/test-game/choose_trump',
          { suit },
          { params: { seat: 0 } }
        );
      }
    });
  });

  describe('playCard', () => {
    it('plays card successfully', async () => {
      const mockResponse = {
        data: { ok: true, msg: 'Card played' },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.playCard('test-game', 0, 'A♠#1');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/game/test-game/play',
        { card_id: 'A♠#1' },
        { params: { seat: 0 } }
      );
      expect(result).toEqual({ ok: true, msg: 'Card played' });
    });

    it('returns scores when round completes', async () => {
      const mockResponse = {
        data: {
          ok: true,
          msg: 'Round complete',
          scores: { team_points: [15, 13] },
        },
      };
      (apiClient.post as any).mockResolvedValue(mockResponse);

      const result = await gameApi.playCard('test-game', 3, 'K♥');

      expect(result.scores).toBeDefined();
      expect(result.scores.team_points).toEqual([15, 13]);
    });

    it('handles invalid card play', async () => {
      (apiClient.post as any).mockRejectedValue({
        status: 400,
        message: 'Must follow suit',
      });

      await expect(gameApi.playCard('test-game', 0, 'A♣')).rejects.toMatchObject({
        status: 400,
      });
    });
  });
});
