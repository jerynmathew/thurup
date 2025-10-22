"""
WebSocket handler for real-time game updates.

Handles:
- Client connections and disconnections
- Player identification
- State synchronization
- Real-time game actions (bid, choose trump, play card)
"""

import asyncio
import traceback

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.v1.bot_runner import schedule_bot_runner
from app.api.v1.broadcast import broadcast_state
from app.api.v1.connection_manager import connection_manager
from app.api.v1.persistence_integration import load_game_from_db
from app.api.v1.router import router
from app.constants import GameConfig, GameMode
from app.core.game_server import get_game_server
from app.db.config import get_db
from app.db.repository import GameRepository
from app.game.session import GameSession
from app.logging_config import get_logger
from app.models import (
    BidCmd,
    ChooseTrumpCmd,
    PlayCardCmd,
    RevealTrumpCmd,
    WSChooseTrumpPayload,
    WSIdentifyPayload,
    WSMessage,
    WSPlaceBidPayload,
    WSPlayCardPayload,
    WSRevealTrumpPayload,
)
from app.utils.game_resolution import resolve_game_identifier

logger = get_logger(__name__)


@router.websocket("/ws/game/{game_id_or_code}")
async def ws_game(websocket: WebSocket, game_id_or_code: str):
    """
    WebSocket handler for real-time game interaction.

    Supports both UUID and short code connections:
    - ws://localhost:8000/ws/game/ccb2e8af-aaf2-4dfe-9611-b146f6866461
    - ws://localhost:8000/ws/game/royal-turtle-65

    Flow:
    1. Accept connection
    2. Resolve short code to UUID if needed
    3. Register socket (initially with no seat)
    4. Send initial state
    5. Handle messages (identify, request_state, actions)
    6. Cleanup on disconnect
    """
    await websocket.accept()

    server = get_game_server()

    # Resolve short code to actual game_id
    game_id = await resolve_game_identifier(game_id_or_code, server.get_all_sessions(), raise_on_not_found=False)

    # Safely check and create/load session if needed
    async with server.lock():
        if not server.has_session(game_id):
            # Try to load from database first
            sess = await load_game_from_db(game_id)
            if sess:
                server.add_session(game_id, sess)
                logger.info("game_loaded_for_ws", game_id=game_id)
            else:
                # Create new session if not found
                sess = GameSession(
                    mode=GameMode.MODE_28.value, seats=GameConfig.MIN_SEATS
                )
                server.add_session(game_id, sess)
                logger.info("new_game_created_for_ws", game_id=game_id)

    # Register connection with manager
    await connection_manager.register(websocket, game_id)

    # Send initial state to this connection only (not broadcast)
    # They will get full state after identifying
    try:
        sess = server.get_session(game_id)
        await websocket.send_json({
            "type": "state_snapshot",
            "payload": sess.get_public_state().model_dump()
        })
    except Exception as e:
        logger.warning("initial_state_send_failed", game_id=game_id, error=str(e))
        # Connection may have closed immediately, cleanup will handle it
        return

    try:
        while True:
            # Receive message with error handling
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                # normal disconnect
                break
            except RuntimeError as e:
                # receive_json can raise RuntimeError if socket was closed/invalid
                logger.warning("websocket_receive_error", game_id=game_id, error=str(e))
                break
            except Exception as e:
                # unexpected error while reading
                logger.error(
                    "websocket_unexpected_error",
                    game_id=game_id,
                    error=str(e),
                    traceback=traceback.format_exc(),
                )
                try:
                    await websocket.send_json(
                        {"type": "error", "payload": {"message": str(e)}}
                    )
                except Exception:
                    pass
                break

            # Update activity timestamp
            connection_manager.update_activity(websocket)

            # Handle message
            await _handle_ws_message(websocket, game_id, data)

    finally:
        # Cleanup connection
        await _cleanup_ws_connection(websocket, game_id)


async def _handle_ws_message(websocket: WebSocket, game_id: str, data: dict):
    """Handle incoming WebSocket message with Pydantic validation."""

    # Validate message structure
    try:
        msg = WSMessage(**data)
    except ValidationError as e:
        logger.warning("ws_message_validation_failed", game_id=game_id, error=str(e))
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Invalid message format: {e}"}
        })
        return

    typ = msg.type
    payload = msg.payload
    server = get_game_server()
    sess = server.get_session(game_id)

    # Validate and handle each message type
    try:
        if typ == "identify":
            validated = WSIdentifyPayload(**payload)
            await _handle_identify(websocket, game_id, sess, validated)

        elif typ == "request_state":
            await _handle_request_state(websocket, game_id, sess)

        elif typ == "place_bid":
            validated = WSPlaceBidPayload(**payload)
            await _handle_place_bid(websocket, sess, validated)

        elif typ == "choose_trump":
            validated = WSChooseTrumpPayload(**payload)
            await _handle_choose_trump(websocket, sess, validated)

        elif typ == "play_card":
            validated = WSPlayCardPayload(**payload)
            await _handle_play_card(websocket, sess, validated)

        elif typ == "reveal_trump":
            validated = WSRevealTrumpPayload(**payload)
            await _handle_reveal_trump(websocket, sess, validated)

        else:
            await websocket.send_json(
                {"type": "error", "payload": {"message": f"unknown type {typ}"}}
            )
            return

    except ValidationError as e:
        logger.warning("ws_payload_validation_failed", game_id=game_id, msg_type=typ, error=str(e))
        await websocket.send_json({
            "type": "error",
            "payload": {"message": f"Invalid payload for {typ}: {e}"}
        })
        return

    # broadcast updated state to all clients
    await broadcast_state(game_id)

    # schedule bots after each client action
    schedule_bot_runner(game_id)


async def _handle_identify(websocket: WebSocket, game_id: str, sess, payload: WSIdentifyPayload):
    """Handle player identification message."""
    seat = payload.seat
    player_id = payload.player_id

    logger.info(
        "identify_request",
        game_id=game_id,
        seat=seat,
        player_id=player_id,
        seat_in_players=seat in sess.players if seat is not None else False,
        session_players=list(sess.players.keys())
    )

    if seat is not None and seat in sess.players:
        # Register this socket with the seat using connection manager
        await connection_manager.identify(websocket, int(seat))

        logger.info(
            "player_identified",
            game_id=game_id,
            seat=seat,
            hand_size=len(sess.get_hand_for(seat))
        )

        # Send state with owner's hand
        await websocket.send_json(
            {
                "type": "state_snapshot",
                "payload": {
                    **sess.get_public_state().model_dump(),
                    "owner_hand": sess.get_hand_for(seat),
                    "player_connected": True,
                },
            }
        )
    else:
        logger.warning(
            "identify_failed",
            game_id=game_id,
            seat=seat,
            reason="seat_not_in_players" if seat is not None else "seat_is_none",
            session_players=list(sess.players.keys())
        )
        # Send public state only
        await websocket.send_json(
            {"type": "state_snapshot", "payload": sess.get_public_state().model_dump()}
        )


async def _handle_request_state(websocket: WebSocket, game_id: str, sess):
    """Handle state request message."""
    # Get seat from connection manager
    conn_info = connection_manager.get_connection_info(websocket)
    seat = conn_info.seat if conn_info else None

    payload_out = sess.get_public_state().model_dump()

    if seat is not None:
        payload_out["owner_hand"] = sess.get_hand_for(seat)
        payload_out["player_connected"] = True

    # Add presence information
    payload_out["connected_seats"] = list(connection_manager.get_present_seats(game_id))

    await websocket.send_json({"type": "state_snapshot", "payload": payload_out})


async def _handle_place_bid(websocket: WebSocket, sess, payload: WSPlaceBidPayload):
    """Handle place_bid action."""
    try:
        ok, msg = await sess.place_bid(payload.seat, BidCmd(value=payload.value))
    except Exception as e:
        await websocket.send_json(
            {"type": "error", "payload": {"action": "place_bid", "message": str(e)}}
        )
        return

    if not ok:
        await websocket.send_json(
            {
                "type": "action_failed",
                "payload": {"action": "place_bid", "message": msg},
            }
        )
    else:
        await websocket.send_json(
            {"type": "action_ok", "payload": {"action": "place_bid", "message": msg}}
        )


async def _handle_choose_trump(websocket: WebSocket, sess, payload: WSChooseTrumpPayload):
    """Handle choose_trump action."""
    try:
        ok, msg = await sess.choose_trump(payload.seat, ChooseTrumpCmd(suit=payload.suit))
    except Exception as e:
        await websocket.send_json(
            {"type": "error", "payload": {"action": "choose_trump", "message": str(e)}}
        )
        return

    if not ok:
        await websocket.send_json(
            {
                "type": "action_failed",
                "payload": {"action": "choose_trump", "message": msg},
            }
        )
    else:
        await websocket.send_json(
            {"type": "action_ok", "payload": {"action": "choose_trump", "message": msg}}
        )


async def _handle_play_card(websocket: WebSocket, sess, payload: WSPlayCardPayload):
    """Handle play_card action."""
    try:
        ok, msg = await sess.play_card(payload.seat, PlayCardCmd(card_id=payload.card_id))
    except Exception as e:
        await websocket.send_json(
            {"type": "error", "payload": {"action": "play_card", "message": str(e)}}
        )
        return

    if not ok:
        await websocket.send_json(
            {
                "type": "action_failed",
                "payload": {"action": "play_card", "message": msg},
            }
        )
        return

    # Check if trick is complete
    trick_complete = msg == "TRICK_COMPLETE"

    if trick_complete:
        # Send acknowledgment
        await websocket.send_json(
            {"type": "action_ok", "payload": {"action": "play_card", "message": "Card played - trick complete"}}
        )

        # Complete the trick immediately (no backend delay - frontend handles UX timing)
        try:
            winner, pts = await sess.complete_current_trick()
            logger.info("trick_completed", game_id=sess.id, winner=winner, points=pts)
        except Exception as e:
            logger.error("trick_completion_failed", game_id=sess.id, error=str(e))
            return
    else:
        await websocket.send_json(
            {"type": "action_ok", "payload": {"action": "play_card", "message": msg}}
        )


async def _handle_reveal_trump(websocket: WebSocket, sess, payload: WSRevealTrumpPayload):
    """Handle reveal_trump action."""
    try:
        ok, msg = await sess.reveal_trump(payload.seat)
    except Exception as e:
        await websocket.send_json(
            {"type": "error", "payload": {"action": "reveal_trump", "message": str(e)}}
        )
        return

    if not ok:
        await websocket.send_json(
            {
                "type": "action_failed",
                "payload": {"action": "reveal_trump", "message": msg},
            }
        )
    else:
        await websocket.send_json(
            {"type": "action_ok", "payload": {"action": "reveal_trump", "message": msg}}
        )


async def _cleanup_ws_connection(websocket: WebSocket, game_id: str):
    """Cleanup WebSocket connection on disconnect."""
    try:
        await connection_manager.unregister(websocket)
    except Exception as e:
        logger.error("websocket_cleanup_failed", game_id=game_id, error=str(e))

    try:
        await websocket.close()
    except Exception:
        pass
