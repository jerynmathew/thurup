/**
 * Admin API service.
 */

import { createAuthenticatedClient } from './client';
import type { ServerHealth, SessionInfo, DatabaseStats } from '../types';

const BASE_PATH = '/api/v1/admin';

export const adminApi = {
  createClient(username: string, password: string) {
    return createAuthenticatedClient(username, password);
  },

  async getHealth(username: string, password: string): Promise<ServerHealth> {
    const client = this.createClient(username, password);
    const response = await client.get<ServerHealth>(`${BASE_PATH}/health`);
    return response.data;
  },

  async listSessions(username: string, password: string): Promise<SessionInfo[]> {
    const client = this.createClient(username, password);
    const response = await client.get<SessionInfo[]>(`${BASE_PATH}/sessions`);
    return response.data;
  },

  async getSessionDetail(gameId: string, username: string, password: string): Promise<any> {
    const client = this.createClient(username, password);
    const response = await client.get(`${BASE_PATH}/sessions/${gameId}/detail`);
    return response.data;
  },

  async getDatabaseStats(username: string, password: string): Promise<DatabaseStats> {
    const client = this.createClient(username, password);
    const response = await client.get<DatabaseStats>(`${BASE_PATH}/database/stats`);
    return response.data;
  },

  async forceSave(gameId: string, username: string, password: string): Promise<{ ok: boolean; message: string }> {
    const client = this.createClient(username, password);
    const response = await client.post(`${BASE_PATH}/sessions/${gameId}/save`);
    return response.data;
  },

  async deleteSession(gameId: string, username: string, password: string): Promise<any> {
    const client = this.createClient(username, password);
    const response = await client.delete(`${BASE_PATH}/sessions/${gameId}`);
    return response.data;
  },

  async triggerCleanup(username: string, password: string): Promise<{ ok: boolean; deleted_games: number }> {
    const client = this.createClient(username, password);
    const response = await client.post(`${BASE_PATH}/maintenance/cleanup`);
    return response.data;
  },

  async listGameHistory(username: string, password: string, limit: number = 50, offset: number = 0): Promise<any[]> {
    const client = this.createClient(username, password);
    const response = await client.get(`${BASE_PATH}/games/history`, {
      params: { limit, offset },
    });
    return response.data;
  },

  async getGameRounds(gameId: string, username: string, password: string): Promise<any> {
    const client = this.createClient(username, password);
    const response = await client.get(`${BASE_PATH}/games/${gameId}/rounds`);
    return response.data;
  },
};
