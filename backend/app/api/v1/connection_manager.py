"""
WebSocket connection manager for tracking player connections and presence.

Handles:
- Connection registration and cleanup
- Player presence tracking
- Reconnection support
- Disconnect notifications
"""

import time
from typing import Dict, Optional, Set

from fastapi import WebSocket

from app.logging_config import get_logger

logger = get_logger(__name__)


class ConnectionInfo:
    """Information about a WebSocket connection."""

    def __init__(self, websocket: WebSocket, game_id: str, seat: Optional[int] = None):
        self.websocket = websocket
        self.game_id = game_id
        self.seat = seat
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.player_id: Optional[str] = None

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def is_idle(self, timeout_seconds: float = 300) -> bool:
        """Check if connection has been idle for too long."""
        return (time.time() - self.last_activity) > timeout_seconds


class ConnectionManager:
    """Manages WebSocket connections for all games."""

    def __init__(self):
        # Track detailed connection info: ws -> ConnectionInfo
        self._connection_details: Dict[WebSocket, ConnectionInfo] = {}

        # Track player presence: game_id -> set of connected seats
        self._player_presence: Dict[str, Set[int]] = {}

    async def register(
        self, websocket: WebSocket, game_id: str, seat: Optional[int] = None
    ):
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket instance
            game_id: Game ID
            seat: Player seat (if identified)
        """
        info = ConnectionInfo(websocket, game_id, seat)
        self._connection_details[websocket] = info

        # Update presence if seat is known
        if seat is not None:
            if game_id not in self._player_presence:
                self._player_presence[game_id] = set()
            self._player_presence[game_id].add(seat)

        logger.info(
            "ws_connection_registered",
            game_id=game_id,
            seat=seat,
            total_connections=len(self._connection_details),
        )

    async def identify(self, websocket: WebSocket, seat: int):
        """
        Associate a WebSocket with a player seat.

        Args:
            websocket: The WebSocket instance
            seat: Player seat number
        """
        info = self._connection_details.get(websocket)
        if not info:
            logger.warning("ws_identify_unknown_connection")
            return

        old_seat = info.seat
        info.seat = seat

        # Update presence
        if info.game_id not in self._player_presence:
            self._player_presence[info.game_id] = set()

        if old_seat is not None and old_seat in self._player_presence[info.game_id]:
            self._player_presence[info.game_id].remove(old_seat)

        self._player_presence[info.game_id].add(seat)

        logger.info("ws_connection_identified", game_id=info.game_id, seat=seat)

    async def unregister(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket instance
        """
        info = self._connection_details.pop(websocket, None)
        if not info:
            return

        # Update presence
        if info.seat is not None:
            if info.game_id in self._player_presence:
                self._player_presence[info.game_id].discard(info.seat)

        logger.info(
            "ws_connection_unregistered",
            game_id=info.game_id,
            seat=info.seat,
            duration_seconds=time.time() - info.connected_at,
        )

    def update_activity(self, websocket: WebSocket):
        """
        Update activity timestamp for a connection.

        Args:
            websocket: The WebSocket instance
        """
        info = self._connection_details.get(websocket)
        if info:
            info.update_activity()

    def get_connection_info(self, websocket: WebSocket) -> Optional[ConnectionInfo]:
        """Get connection info for a WebSocket."""
        return self._connection_details.get(websocket)

    def get_game_connections(self, game_id: str) -> list[WebSocket]:
        """Get all WebSocket connections for a game."""
        return [
            ws
            for ws, info in self._connection_details.items()
            if info.game_id == game_id
        ]

    def get_present_seats(self, game_id: str) -> Set[int]:
        """Get set of seat numbers with active connections."""
        return self._player_presence.get(game_id, set()).copy()

    def is_player_connected(self, game_id: str, seat: int) -> bool:
        """Check if a player seat has an active connection."""
        return seat in self._player_presence.get(game_id, set())

    def get_connection_count(self, game_id: str) -> int:
        """Get number of connections for a game."""
        return sum(
            1 for info in self._connection_details.values() if info.game_id == game_id
        )


# Global connection manager instance
connection_manager = ConnectionManager()
