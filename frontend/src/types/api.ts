/**
 * API response type definitions.
 * Matches backend REST API responses.
 */

import type { GameState, PlayerInfo } from './game';

// History API types
export interface GameSummary {
  game_id: string;
  mode: string;
  seats: number;
  state: string;
  players: PlayerInfo[];
  player_count: number;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
}

export interface SnapshotSummary {
  snapshot_id: number;
  game_id: string;
  state_phase: string;
  snapshot_reason: string;
  created_at: string;
}

export interface GameDetail {
  game: GameSummary;
  snapshots: SnapshotSummary[];
  total_snapshots: number;
}

export interface GameHistoryStats {
  total_games: number;
  completed_games: number;
  active_games: number;
  abandoned_games: number;
  total_players: number;
  total_bots: number;
}

export interface GameReplay {
  game_id: string;
  mode: string;
  seats: number;
  state: string;
  created_at: string;
  snapshots: Array<{
    snapshot_id: number;
    state_phase: string;
    snapshot_reason: string;
    created_at: string;
    data: GameState;
  }>;
  total_snapshots: number;
}

// Admin API types
export interface ServerHealth {
  status: 'healthy' | 'degraded';
  uptime_seconds: number;
  in_memory_sessions: number;
  total_connections: number;
  running_bot_tasks: number;
  database_connected: boolean;
}

export interface SessionInfo {
  game_id: string;
  mode: string;
  seats: number;
  state: string;
  player_count: number;
  connection_count: number;
  connected_seats: number[];
  has_bot_task: boolean;
}

export interface DatabaseStats {
  total_games: number;
  total_players: number;
  total_snapshots: number;
  db_size_bytes: number | null;
}

// Error response
export interface ApiError {
  detail: string | Record<string, any>;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  status: number;
}
