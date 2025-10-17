/**
 * Game state management with Zustand.
 * Handles current game state, connection status, and game actions.
 */

import { create } from 'zustand';
import { clearSession } from '../utils/sessionManager';
import type { GameState } from '../types';

interface GameStore {
  // State
  gameId: string | null;
  gameState: GameState | null;
  seat: number | null;
  playerId: string | null;
  isConnected: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';
  error: string | null;

  // Actions
  setGame: (gameId: string, seat: number | null, playerId: string | null) => void;
  updateGameState: (state: GameState) => void;
  setConnectionState: (state: 'disconnected' | 'connecting' | 'connected' | 'reconnecting') => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;
  clearGame: () => void;
  reset: () => void;
}

const initialState = {
  gameId: null,
  gameState: null,
  seat: null,
  playerId: null,
  isConnected: false,
  connectionState: 'disconnected' as const,
  error: null,
};

export const useGameStore = create<GameStore>((set) => ({
  ...initialState,

  setGame: (gameId, seat, playerId) => {
    set({
      gameId,
      seat,
      playerId,
      error: null,
    });
  },

  updateGameState: (gameState) => {
    set({ gameState, error: null });
  },

  setConnectionState: (connectionState) => {
    set({
      connectionState,
      isConnected: connectionState === 'connected',
    });
  },

  setConnected: (isConnected) => {
    set({
      isConnected,
      connectionState: isConnected ? 'connected' : 'disconnected',
    });
  },

  setError: (error) => {
    set({ error });
  },

  clearGame: () => {
    const currentGameId = useGameStore.getState().gameId;

    // Clear localStorage session if gameId exists
    if (currentGameId) {
      clearSession(currentGameId);
    }

    set({
      gameId: null,
      gameState: null,
      seat: null,
      playerId: null,
      error: null,
    });
  },

  reset: () => {
    const currentGameId = useGameStore.getState().gameId;

    // Clear localStorage session if gameId exists
    if (currentGameId) {
      clearSession(currentGameId);
    }

    set(initialState);
  },
}));

// Constant empty array to avoid creating new references
const EMPTY_ARRAY: any[] = [];

// Selectors for commonly used derived state
// Note: For array/object returns, we must use the actual value or a constant to avoid creating new references
export const selectIsInGame = (state: GameStore) => state.gameId !== null;
export const selectIsMyTurn = (state: GameStore) =>
  state.gameState?.turn === state.seat;
export const selectMyHand = (state: GameStore) => state.gameState?.owner_hand || EMPTY_ARRAY;
export const selectCurrentPhase = (state: GameStore) => state.gameState?.state;
export const selectTrump = (state: GameStore) => state.gameState?.trump;
export const selectCanBid = (state: GameStore) =>
  state.gameState?.state === 'bidding' && state.gameState?.turn === state.seat;
