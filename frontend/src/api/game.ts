/**
 * Game API service.
 * Handles all game-related HTTP requests.
 */

import { apiClient } from './client';
import type {
  GameState,
  CreateGameRequest,
  CreateGameResponse,
  JoinGameRequest,
  JoinGameResponse,
  StartGameRequest,
  BidCommand,
  ChooseTrumpCommand,
  PlayCardCommand,
  Suit,
} from '../types';

const BASE_PATH = '/api/v1';

export const gameApi = {
  /**
   * Create a new game
   */
  async createGame(mode: '28' | '56', seats: 4 | 6): Promise<CreateGameResponse> {
    const response = await apiClient.post<CreateGameResponse>(`${BASE_PATH}/game/create`, {
      mode,
      seats,
    } as CreateGameRequest);
    return response.data;
  },

  /**
   * Get game state
   */
  async getGame(gameId: string): Promise<GameState> {
    const response = await apiClient.get<GameState>(`${BASE_PATH}/game/${gameId}`);
    return response.data;
  },

  /**
   * Join a game
   */
  async joinGame(gameId: string, name: string, isBot: boolean = false): Promise<JoinGameResponse> {
    const response = await apiClient.post<JoinGameResponse>(
      `${BASE_PATH}/game/${gameId}/join`,
      {
        name,
        is_bot: isBot,
      } as JoinGameRequest
    );
    return response.data;
  },

  /**
   * Start a game round
   */
  async startGame(gameId: string, dealer: number = 0): Promise<{ ok: boolean }> {
    const response = await apiClient.post<{ ok: boolean }>(
      `${BASE_PATH}/game/${gameId}/start`,
      {
        dealer,
      } as StartGameRequest
    );
    return response.data;
  },

  /**
   * Place a bid
   */
  async placeBid(gameId: string, seat: number, value: number | null): Promise<{ ok: boolean; msg: string }> {
    const response = await apiClient.post<{ ok: boolean; msg: string }>(
      `${BASE_PATH}/game/${gameId}/bid`,
      {
        value,
      } as BidCommand,
      {
        params: { seat },
      }
    );
    return response.data;
  },

  /**
   * Choose trump suit
   */
  async chooseTrump(gameId: string, seat: number, suit: Suit): Promise<{ ok: boolean; msg: string }> {
    const response = await apiClient.post<{ ok: boolean; msg: string }>(
      `${BASE_PATH}/game/${gameId}/choose_trump`,
      {
        suit,
      } as ChooseTrumpCommand,
      {
        params: { seat },
      }
    );
    return response.data;
  },

  /**
   * Play a card
   */
  async playCard(gameId: string, seat: number, cardId: string): Promise<{ ok: boolean; msg: string; scores?: any }> {
    const response = await apiClient.post<{ ok: boolean; msg: string; scores?: any }>(
      `${BASE_PATH}/game/${gameId}/play`,
      {
        card_id: cardId,
      } as PlayCardCommand,
      {
        params: { seat },
      }
    );
    return response.data;
  },
};
