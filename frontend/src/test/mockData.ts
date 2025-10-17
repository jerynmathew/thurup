/**
 * Mock data for testing.
 */

import type { Card, GameState, PlayerInfo } from '../types';

export const mockCard: Card = {
  suit: '♠',
  rank: 'A',
  id: 'A♠',
};

export const mockCards: Card[] = [
  { suit: '♠', rank: 'A', id: 'A♠' },
  { suit: '♥', rank: 'K', id: 'K♥' },
  { suit: '♦', rank: 'Q', id: 'Q♦' },
  { suit: '♣', rank: 'J', id: 'J♣' },
  { suit: '♠', rank: '10', id: '10♠' },
];

export const mockPlayers: PlayerInfo[] = [
  { player_id: 'p1', name: 'Player 1', seat: 0, is_bot: false },
  { player_id: 'p2', name: 'Player 2', seat: 1, is_bot: false },
  { player_id: 'p3', name: 'Bot 1', seat: 2, is_bot: true },
  { player_id: 'p4', name: 'Bot 2', seat: 3, is_bot: true },
];

export const mockGameState: GameState = {
  game_id: 'test-game-123',
  mode: '28',
  seats: 4,
  state: 'play',
  players: mockPlayers,
  leader: 0,
  turn: 0,
  trump: '♠',
  kitty: [],
  hand_sizes: { 0: 5, 1: 5, 2: 5, 3: 5 },
  bids: { 0: 16, 1: -1, 2: 18, 3: -1 },
  current_highest: 18,
  bid_winner: 2,
  bid_value: 18,
  points_by_seat: { 0: 0, 1: 0, 2: 0, 3: 0 },
  owner_hand: mockCards,
  connected_seats: [0, 1, 2, 3],
  current_trick: [],
};

export const mockLobbyGameState: GameState = {
  game_id: 'test-game-lobby',
  mode: '28',
  seats: 4,
  state: 'lobby',
  players: [mockPlayers[0], mockPlayers[1]],
  leader: 0,
  turn: 0,
  trump: null,
  kitty: [],
  hand_sizes: {},
  bids: {},
  current_highest: null,
  bid_winner: null,
  bid_value: null,
  points_by_seat: {},
  connected_seats: [0, 1],
};

export const mockBiddingGameState: GameState = {
  ...mockGameState,
  state: 'bidding',
  turn: 0,
  bids: { 0: null, 1: null, 2: null, 3: null },
  current_highest: null,
  bid_winner: null,
  bid_value: null,
  trump: null,
};
