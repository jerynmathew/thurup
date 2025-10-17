/**
 * Enhanced game hook that integrates WebSocket, API calls, and game store.
 * Provides a complete interface for game interactions.
 */

import { useEffect, useCallback, useRef } from 'react';
import { useGameStore } from '../stores';
import { getWebSocketUrl } from '../api/client';
import type { ClientMessage, ServerMessage, Suit } from '../types';
import { toast } from '../stores/uiStore';

interface UseGameOptions {
  gameId: string;
  seat: number | null;
  playerId: string | null;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
}

export function useGame({ gameId, seat, playerId, onConnect, onDisconnect, onError }: UseGameOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectDelay = useRef(1000);

  const MAX_RECONNECT_ATTEMPTS = 5;
  const MAX_RECONNECT_DELAY = 30000;

  // Get store actions directly (these are stable in Zustand)
  const updateGameState = useCallback((state: any) => {
    useGameStore.getState().updateGameState(state);
  }, []);

  const setConnectionState = useCallback((state: any) => {
    useGameStore.getState().setConnectionState(state);
  }, []);

  const setError = useCallback((error: string | null) => {
    useGameStore.getState().setError(error);
  }, []);

  // Send a message to the WebSocket
  const sendMessage = useCallback((message: ClientMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('[useGame] Cannot send message: WebSocket not open');
    return false;
  }, []);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: ServerMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'state_snapshot':
            updateGameState(message.payload);
            break;

          case 'action_ok':
            toast.success(message.payload.message || 'Action successful');
            break;

          case 'action_failed':
            toast.error(message.payload.message || 'Action failed');
            break;

          case 'error':
            const errorMsg = message.payload.message || 'An error occurred';
            setError(errorMsg);
            toast.error(errorMsg);
            onError?.(errorMsg);
            break;

          default:
            console.warn('[useGame] Unknown message type:', message);
        }
      } catch (error) {
        console.error('[useGame] Failed to parse message:', error);
      }
    },
    [updateGameState, setError, onError]
  );

  // Create WebSocket connection - use ref for current values to avoid dependency issues
  const currentSeat = useRef(seat);
  const currentPlayerId = useRef(playerId);
  const currentGameId = useRef(gameId);

  // Update refs when props change
  useEffect(() => {
    currentSeat.current = seat;
    currentPlayerId.current = playerId;
    currentGameId.current = gameId;
  }, [seat, playerId, gameId]);

  // Re-identify when seat/playerId changes while WebSocket is connected
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (seat !== null && playerId) {
        console.log('[useGame] Seat/PlayerId changed, re-identifying with seat:', seat, 'playerId:', playerId);
        wsRef.current.send(JSON.stringify({
          type: 'identify',
          payload: { seat, player_id: playerId },
        }));
      }
    }
  }, [seat, playerId]);

  const connect = useCallback(() => {
    if (!currentGameId.current) return;

    const wsUrl = getWebSocketUrl();
    const url = `${wsUrl}/api/v1/ws/game/${currentGameId.current}`;

    console.log('[useGame] Connecting to:', url);
    setConnectionState('connecting');

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('[useGame] Connected');
      setConnectionState('connected');
      reconnectAttempts.current = 0;
      reconnectDelay.current = 1000;

      // Identify with seat and player ID
      if (currentSeat.current !== null && currentPlayerId.current) {
        console.log('[useGame] Sending identify message with seat:', currentSeat.current, 'playerId:', currentPlayerId.current);
        ws.send(JSON.stringify({
          type: 'identify',
          payload: { seat: currentSeat.current, player_id: currentPlayerId.current },
        }));
      } else {
        // Request current state
        console.log('[useGame] Sending request_state (no seat/playerId)');
        ws.send(JSON.stringify({ type: 'request_state' }));
      }

      onConnect?.();
    };

    ws.onmessage = handleMessage;

    ws.onclose = (event) => {
      console.log('[useGame] Disconnected:', event.code, event.reason);
      setConnectionState('disconnected');
      wsRef.current = null;
      onDisconnect?.();

      // Attempt reconnect if not exceeded max attempts
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current++;
        console.log(
          `[useGame] Reconnecting in ${reconnectDelay.current}ms (attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`
        );

        setConnectionState('reconnecting');

        reconnectTimer.current = setTimeout(() => {
          connect();
        }, reconnectDelay.current);

        // Exponential backoff
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
      } else {
        const error = 'Max reconnection attempts reached';
        setError(error);
        toast.error(error);
        onError?.(error);
      }
    };

    ws.onerror = (error) => {
      console.error('[useGame] WebSocket error:', error);
      setError('Connection error');
    };

    wsRef.current = ws;
  }, [handleMessage, setConnectionState, setError, onConnect, onDisconnect, onError]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionState('disconnected');
  }, [setConnectionState]);

  // Game actions - use ref for seat to avoid recreating callbacks
  const placeBid = useCallback(
    (value: number | null) => {
      if (currentSeat.current === null) return false;
      return sendMessage({
        type: 'place_bid',
        payload: { seat: currentSeat.current, value },
      });
    },
    [sendMessage]
  );

  const chooseTrump = useCallback(
    (suit: Suit) => {
      if (currentSeat.current === null) return false;
      return sendMessage({
        type: 'choose_trump',
        payload: { seat: currentSeat.current, suit },
      });
    },
    [sendMessage]
  );

  const playCard = useCallback(
    (cardId: string) => {
      if (currentSeat.current === null) return false;
      return sendMessage({
        type: 'play_card',
        payload: { seat: currentSeat.current, card_id: cardId },
      });
    },
    [sendMessage]
  );

  const revealTrump = useCallback(() => {
    if (currentSeat.current === null) return false;
    return sendMessage({
      type: 'reveal_trump',
      payload: { seat: currentSeat.current },
    });
  }, [sendMessage]);

  const requestState = useCallback(() => {
    return sendMessage({ type: 'request_state' });
  }, [sendMessage]);

  // Connect on mount, disconnect on unmount
  // Depend on gameId directly to ensure connection happens after gameId is set
  useEffect(() => {
    if (!gameId) return; // Don't connect if no gameId

    connect();
    return () => {
      disconnect();
    };
  }, [gameId, connect, disconnect]);

  return {
    // Connection state
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,

    // Actions
    placeBid,
    chooseTrump,
    playCard,
    revealTrump,
    requestState,

    // Connection management
    reconnect: connect,
    disconnect,
  };
}
