"""
Broadcasting utilities for sending game state updates to all connected clients.
"""

from app.api.v1.connection_manager import connection_manager
from app.core.game_server import get_game_server
from app.logging_config import get_logger

logger = get_logger(__name__)


async def broadcast_state(game_id: str):
    """
    Broadcast game state to all connected websockets for a game.

    Sends per-socket owner_hand if the socket has identified with a seat.
    Handles disconnected sockets gracefully by removing them from the connection pool.

    Performance optimization: Pre-serializes all player hands once to avoid
    redundant serialization for each connection.
    """
    server = get_game_server()
    sess = server.get_session(game_id)
    if not sess:
        return

    base = sess.get_public_state().model_dump()

    # Get all connections for this game
    connections = connection_manager.get_game_connections(game_id)
    if not connections:
        return

    # Performance optimization: Pre-serialize all hands once
    # This avoids calling get_hand_for() N times (once per connection)
    hands_cache = {seat: sess.get_hand_for(seat) for seat in range(sess.seats)}

    # Send messages to all connections
    remove = []
    for ws in connections:
        try:
            # Get connection info to determine seat
            conn_info = connection_manager.get_connection_info(ws)
            seat = conn_info.seat if conn_info else None

            # Debug logging to track seat identification
            logger.debug(
                "broadcast_to_connection",
                game_id=game_id,
                has_conn_info=conn_info is not None,
                seat=seat,
                will_send_hand=seat is not None
            )

            # Use dict unpacking for faster shallow copy
            payload = {**base}
            # attach owner_hand only for that socket if seat is known
            if seat is not None:
                # Use pre-serialized hand from cache (no redundant serialization)
                payload["owner_hand"] = hands_cache[seat]
                logger.debug(
                    "sending_hand_to_player",
                    game_id=game_id,
                    seat=seat,
                    hand_size=len(payload["owner_hand"])
                )
            await ws.send_json({"type": "state_snapshot", "payload": payload})
        except Exception as e:
            # Log the error for debugging
            logger.warning(
                "broadcast_failed",
                game_id=game_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            remove.append(ws)

    # Clean up failed connections
    for ws in remove:
        await connection_manager.unregister(ws)
