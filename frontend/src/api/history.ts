/**
 * History API service.
 */

import { apiClient } from './client';
import type { GameSummary, GameDetail, GameHistoryStats, GameReplay } from '../types';

const BASE_PATH = '/api/v1/history';

export const historyApi = {
  async listGames(params?: {
    state?: string;
    mode?: string;
    limit?: number;
    offset?: number;
  }): Promise<GameSummary[]> {
    const response = await apiClient.get<GameSummary[]>(`${BASE_PATH}/games`, { params });
    return response.data;
  },

  async getGameDetail(gameId: string): Promise<GameDetail> {
    const response = await apiClient.get<GameDetail>(`${BASE_PATH}/games/${gameId}`);
    return response.data;
  },

  async getSnapshot(gameId: string, snapshotId: number): Promise<any> {
    const response = await apiClient.get(`${BASE_PATH}/games/${gameId}/snapshots/${snapshotId}`);
    return response.data;
  },

  async getGameReplay(gameId: string): Promise<GameReplay> {
    const response = await apiClient.get<GameReplay>(`${BASE_PATH}/games/${gameId}/replay`);
    return response.data;
  },

  async getStats(): Promise<GameHistoryStats> {
    const response = await apiClient.get<GameHistoryStats>(`${BASE_PATH}/stats`);
    return response.data;
  },
};
