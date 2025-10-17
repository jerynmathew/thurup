// src/hooks/useGameSocket.tsx
import { useEffect, useRef, useCallback } from "react";

const MAX_RECONNECT_ATTEMPTS = 5;
const INITIAL_RECONNECT_DELAY = 1000; // 1 second
const MAX_RECONNECT_DELAY = 30000; // 30 seconds

export function useGameSocket(gameId: string | null, onMessage: (msg: any) => void, seat: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const reconnectDelay = useRef<number>(INITIAL_RECONNECT_DELAY);

  // Stable callback for creating and setting up WebSocket
  const createWebSocket = useCallback(() => {
    if (!gameId) return null;

    // Construct WebSocket URL using relative path and current window location
    // This works with both local dev (Vite proxy) and Cloudflare Tunnel
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // includes port if present
    const url = `${protocol}//${host}/api/v1/ws/game/${encodeURIComponent(gameId)}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log("[useGameSocket] ws open", url);
      // Reset reconnect attempts on successful connection
      reconnectAttempts.current = 0;
      reconnectDelay.current = INITIAL_RECONNECT_DELAY;

      // identify if we know seat
      if (seat !== null) {
        ws.send(JSON.stringify({ type: "identify", payload: { seat } }));
      } else {
        // ask server for current state
        ws.send(JSON.stringify({ type: "request_state" }));
      }
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        onMessage(msg);
      } catch (e) {
        console.warn("invalid ws msg", e);
      }
    };

    ws.onclose = (ev) => {
      console.log("[useGameSocket] ws closed", ev.code, ev.reason);

      // cleanup ref if it's this socket
      if (wsRef.current === ws) {
        wsRef.current = null;
      }

      // Only attempt reconnect if we haven't exceeded max attempts and gameId is still valid
      if (gameId && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts.current += 1;

        if (reconnectTimer.current) {
          window.clearTimeout(reconnectTimer.current);
        }

        console.log(
          `[useGameSocket] Reconnecting attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS} in ${reconnectDelay.current}ms`
        );

        reconnectTimer.current = window.setTimeout(() => {
          if (!wsRef.current && gameId) {
            console.log("[useGameSocket] Attempting reconnect...");
            wsRef.current = createWebSocket();
          }
        }, reconnectDelay.current);

        // Exponential backoff with jitter
        reconnectDelay.current = Math.min(
          reconnectDelay.current * 2 + Math.random() * 1000,
          MAX_RECONNECT_DELAY
        );
      } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
        console.error("[useGameSocket] Max reconnect attempts reached. Giving up.");
      }
    };

    ws.onerror = (e) => {
      console.warn("[useGameSocket] ws error", e);
    };

    return ws;
  }, [gameId, onMessage, seat]);

  useEffect(() => {
    // if no gameId, close existing socket
    if (!gameId) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      reconnectAttempts.current = 0;
      reconnectDelay.current = INITIAL_RECONNECT_DELAY;
      return;
    }

    // do not open a new socket if one already for same game is open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // optionally send identify if seat available
      if (seat !== null) {
        wsRef.current.send(JSON.stringify({ type: "identify", payload: { seat } }));
      }
      return;
    }

    // Create new WebSocket if none exists or existing one is not open
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.CONNECTING) {
      wsRef.current = createWebSocket();
    }

    // cleanup when unmount or gameId changes
    return () => {
      if (reconnectTimer.current) {
        window.clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (er) {
          console.warn("[useGameSocket] Error closing WebSocket:", er);
        }
        wsRef.current = null;
      }
    };
  }, [gameId, seat, createWebSocket]);

  // expose nothing; this hook manages its own socket
  return null;
}
