/**
 * TypeScript type definitions for game entities.
 * These types match the backend API models.
 */

// Card types
export type Suit = '♠' | '♥' | '♦' | '♣';
export type Rank = '7' | '8' | '9' | '10' | 'J' | 'Q' | 'K' | 'A';

export interface Card {
  suit: Suit;
  rank: Rank;
  id: string; // Unique identifier (e.g., "A♠" or "A♠#1" for 56-mode)
}

// Player types
export interface PlayerInfo {
  player_id?: string;
  name: string;
  seat: number;
  is_bot?: boolean;
}

// Game state types
export type GameMode = '28' | '56';
export type GamePhase =
  | 'lobby'
  | 'dealing'
  | 'bidding'
  | 'choose_trump'
  | 'play'
  | 'scoring'
  | 'round_end';

export interface GameState {
  game_id: string;
  short_code?: string; // User-friendly short code (e.g., "royal-turtle-65")
  mode: GameMode;
  seats: number;
  state: GamePhase;
  players: PlayerInfo[];
  dealer: number; // Current dealer position
  leader: number; // Player to dealer's right (first to bid/play)
  turn: number;
  trump: Suit | null;
  kitty: Card[];
  hand_sizes: Record<number, number>;
  bids: Record<number, number | null>;
  current_highest: number | null;
  bid_winner: number | null;
  bid_value: number | null;
  points_by_seat: Record<number, number>;

  // Optional fields (only sent when relevant)
  owner_hand?: Card[]; // Your hand (when identified)
  connected_seats?: number[]; // Seats with active connections
  current_trick?: Record<number, Card>; // Cards in current trick (seat -> card)
  lead_suit?: Suit | null; // Suit to follow in current trick
  last_trick?: { winner: number; cards: Record<number, Card> }; // Last completed trick
  tricks_won?: Record<number, number>; // Tricks won per seat
  rounds_history?: RoundHistory[]; // History of completed rounds
}

// Round history types
export interface RoundHistory {
  round_number: number;
  dealer: number;
  bid_winner: number | null;
  bid_value: number | null;
  trump: Suit | null;
  captured_tricks: CapturedTrick[];
  points_by_seat: Record<number, number>;
  team_scores: TeamScores;
}

export interface CapturedTrick {
  winner: number;
  cards: { seat: number; card: Card }[];
  points: number;
}

export interface TeamScores {
  team_points: { 0: number; 1: number };
  bid_outcome: {
    bid_winner: number;
    bid_value: number;
    winning_team: number;
    success: boolean;
  } | null;
}

// Game action command types
export interface BidCommand {
  value: number | null; // null or -1 for pass
}

export interface ChooseTrumpCommand {
  suit: Suit;
}

export interface PlayCardCommand {
  card_id: string;
}

// API request types
export interface CreateGameRequest {
  mode: GameMode;
  seats: number;
}

export interface JoinGameRequest {
  name: string;
  is_bot?: boolean;
}

export interface StartGameRequest {
  dealer: number;
}

// API response types
export interface CreateGameResponse {
  game_id: string;
  short_code: string;
}

export interface JoinGameResponse {
  player_id: string;
  seat: number;
}

// Game constants
export const MIN_BID = 14;
export const MAX_BID_28 = 28;
export const MAX_BID_56 = 56;
export const VALID_SEATS = [4, 6] as const;

// Helper types
export type BidValue = number | null | -1; // -1 = pass, null = not yet bid

// Team configuration
export const TEAM_0 = 0; // Even seats
export const TEAM_1 = 1; // Odd seats

export function getTeam(seat: number): number {
  return seat % 2 === 0 ? TEAM_0 : TEAM_1;
}

export function getSuitColor(suit: Suit): 'red' | 'black' {
  return (suit === '♥' || suit === '♦') ? 'red' : 'black';
}

export function getSuitName(suit: Suit): string {
  const names: Record<Suit, string> = {
    '♠': 'Spades',
    '♥': 'Hearts',
    '♦': 'Diamonds',
    '♣': 'Clubs'
  };
  return names[suit];
}

export function getRankName(rank: Rank): string {
  const names: Record<Rank, string> = {
    '7': 'Seven',
    '8': 'Eight',
    '9': 'Nine',
    '10': 'Ten',
    'J': 'Jack',
    'Q': 'Queen',
    'K': 'King',
    'A': 'Ace'
  };
  return names[rank];
}
