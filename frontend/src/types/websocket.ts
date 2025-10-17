/**
 * WebSocket message type definitions.
 * Matches backend WebSocket message types.
 */

import type { GameState, Suit } from './game';

// Message types sent from client to server
export type ClientMessage =
  | IdentifyMessage
  | RequestStateMessage
  | PlaceBidMessage
  | ChooseTrumpMessage
  | PlayCardMessage
  | RevealTrumpMessage;

export interface IdentifyMessage {
  type: 'identify';
  payload: {
    seat: number;
  };
}

export interface RequestStateMessage {
  type: 'request_state';
  payload?: Record<string, never>; // Empty payload
}

export interface PlaceBidMessage {
  type: 'place_bid';
  payload: {
    seat: number;
    value: number | null; // null or -1 for pass
  };
}

export interface ChooseTrumpMessage {
  type: 'choose_trump';
  payload: {
    seat: number;
    suit: Suit;
  };
}

export interface PlayCardMessage {
  type: 'play_card';
  payload: {
    seat: number;
    card_id: string;
  };
}

export interface RevealTrumpMessage {
  type: 'reveal_trump';
  payload: {
    seat: number;
  };
}

// Message types sent from server to client
export type ServerMessage =
  | StateSnapshotMessage
  | ActionOkMessage
  | ActionFailedMessage
  | ErrorMessage;

export interface StateSnapshotMessage {
  type: 'state_snapshot';
  payload: GameState;
}

export interface ActionOkMessage {
  type: 'action_ok';
  payload: {
    action: string;
    message: string;
  };
}

export interface ActionFailedMessage {
  type: 'action_failed';
  payload: {
    action: string;
    message: string;
  };
}

export interface ErrorMessage {
  type: 'error';
  payload: {
    message: string;
  };
}

// WebSocket connection states
export enum WSConnectionState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  FAILED = 'FAILED',
}

// WebSocket configuration
export const WS_CONFIG = {
  RECONNECT_INITIAL_DELAY: 1000, // 1 second
  RECONNECT_MAX_DELAY: 30000, // 30 seconds
  MAX_RECONNECT_ATTEMPTS: 5,
  RECEIVE_TIMEOUT: 120000, // 2 minutes
} as const;
