/**
 * Tests for gameStore.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useGameStore, selectIsMyTurn, selectMyHand, selectCanBid } from './gameStore';
import { mockGameState, mockCards } from '../test/mockData';

describe('gameStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useGameStore.getState().reset();
  });

  it('initializes with default values', () => {
    const state = useGameStore.getState();
    expect(state.gameId).toBeNull();
    expect(state.gameState).toBeNull();
    expect(state.seat).toBeNull();
    expect(state.playerId).toBeNull();
    expect(state.isConnected).toBe(false);
  });

  it('sets game information', () => {
    const { setGame } = useGameStore.getState();
    setGame('game-123', 0, 'player-456');

    const state = useGameStore.getState();
    expect(state.gameId).toBe('game-123');
    expect(state.seat).toBe(0);
    expect(state.playerId).toBe('player-456');
  });

  it('updates game state', () => {
    const { updateGameState } = useGameStore.getState();
    updateGameState(mockGameState);

    const state = useGameStore.getState();
    expect(state.gameState).toEqual(mockGameState);
  });

  it('sets connection state', () => {
    const { setConnectionState } = useGameStore.getState();
    setConnectionState('connected');

    const state = useGameStore.getState();
    expect(state.connectionState).toBe('connected');
    expect(state.isConnected).toBe(true);
  });

  it('sets connection state to disconnected', () => {
    const { setConnectionState } = useGameStore.getState();
    setConnectionState('disconnected');

    const state = useGameStore.getState();
    expect(state.connectionState).toBe('disconnected');
    expect(state.isConnected).toBe(false);
  });

  it('clears game information', () => {
    const { setGame, clearGame } = useGameStore.getState();
    setGame('game-123', 0, 'player-456');
    clearGame();

    const state = useGameStore.getState();
    expect(state.gameId).toBeNull();
    expect(state.gameState).toBeNull();
    expect(state.seat).toBeNull();
  });

  it('resets entire store', () => {
    const { setGame, updateGameState, reset } = useGameStore.getState();
    setGame('game-123', 0, 'player-456');
    updateGameState(mockGameState);
    reset();

    const state = useGameStore.getState();
    expect(state.gameId).toBeNull();
    expect(state.gameState).toBeNull();
    expect(state.seat).toBeNull();
    expect(state.playerId).toBeNull();
  });

  describe('Selectors', () => {
    beforeEach(() => {
      const { setGame, updateGameState } = useGameStore.getState();
      setGame('game-123', 0, 'player-456');
      updateGameState(mockGameState);
    });

    it('selectIsMyTurn returns true when it is my turn', () => {
      const state = useGameStore.getState();
      const isMyTurn = selectIsMyTurn(state);
      expect(isMyTurn).toBe(true); // turn is 0, seat is 0
    });

    it('selectIsMyTurn returns false when it is not my turn', () => {
      const { updateGameState } = useGameStore.getState();
      updateGameState({ ...mockGameState, turn: 1 });

      const state = useGameStore.getState();
      const isMyTurn = selectIsMyTurn(state);
      expect(isMyTurn).toBe(false);
    });

    it('selectMyHand returns owner_hand from game state', () => {
      const state = useGameStore.getState();
      const myHand = selectMyHand(state);
      expect(myHand).toEqual(mockCards);
    });

    it('selectMyHand returns empty array when no owner_hand', () => {
      const { updateGameState } = useGameStore.getState();
      updateGameState({ ...mockGameState, owner_hand: undefined });

      const state = useGameStore.getState();
      const myHand = selectMyHand(state);
      expect(myHand).toEqual([]);
    });

    it('selectCanBid returns true during bidding phase when it is my turn', () => {
      const { updateGameState } = useGameStore.getState();
      updateGameState({
        ...mockGameState,
        state: 'bidding',
        turn: 0,
      });

      const state = useGameStore.getState();
      const canBid = selectCanBid(state);
      expect(canBid).toBe(true);
    });

    it('selectCanBid returns false when not in bidding phase', () => {
      const { updateGameState } = useGameStore.getState();
      updateGameState({
        ...mockGameState,
        state: 'playing',
        turn: 0,
      });

      const state = useGameStore.getState();
      const canBid = selectCanBid(state);
      expect(canBid).toBe(false);
    });

    it('selectCanBid returns false when not my turn', () => {
      const { updateGameState } = useGameStore.getState();
      updateGameState({
        ...mockGameState,
        state: 'bidding',
        turn: 1,
      });

      const state = useGameStore.getState();
      const canBid = selectCanBid(state);
      expect(canBid).toBe(false);
    });
  });
});
