"""
REST HTTP endpoints for game management.

Handles:
- Game creation
- Player joining
- Game starting
- Bid placement
- Trump selection
- Card playing
"""

import traceback
import uuid

from fastapi import HTTPException

from app.api.v1.bot_runner import schedule_bot_runner
from app.api.v1.broadcast import broadcast_state
from app.api.v1.persistence_integration import load_game_from_db, save_game_state
from app.api.v1.router import SESSIONS, router, sessions_lock
from app.constants import ErrorMessage
from app.db.config import get_db
from app.db.repository import GameRepository
from app.game.session import GameSession, SessionState
from app.logging_config import get_logger
from app.utils import generate_short_code
from app.utils.game_resolution import resolve_game_identifier
from app.models import (
    BidCmd,
    ChooseTrumpCmd,
    CreateGameRequest,
    JoinGameRequest,
    PlayCardCmd,
    PlayerInfo,
    StartGameRequest,
)

logger = get_logger(__name__)


@router.post("/game/create")
async def create_game(request: CreateGameRequest):
    """Create a new game session with validation."""
    # Generate a unique short code
    existing_codes = {sess.short_code for sess in SESSIONS.values() if sess.short_code}
    short_code = generate_short_code(existing_codes)

    game = GameSession(mode=request.mode, seats=request.seats, short_code=short_code)
    SESSIONS[game.id] = game

    # Save initial game state
    await save_game_state(game.id, reason="create")

    logger.info("game_created", game_id=game.id, short_code=short_code, mode=request.mode, seats=request.seats)
    return {"game_id": game.id, "short_code": short_code}


@router.get("/game/{game_id_or_code}")
async def get_game(game_id_or_code: str):
    """
    Get game state by UUID or short code. Loads from database if not in memory.

    Supports both:
    - UUID: /game/ccb2e8af-aaf2-4dfe-9611-b146f6866461
    - Short code: /game/royal-turtle-65
    """
    # Resolve to actual game_id
    game_id = await resolve_game_identifier(game_id_or_code, SESSIONS, raise_on_not_found=True)

    if game_id in SESSIONS:
        sess = SESSIONS[game_id]
        return sess.get_public_state()

    # Try to load from database
    sess = await load_game_from_db(game_id)
    if not sess:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    # Add to memory
    async with sessions_lock:
        SESSIONS[game_id] = sess

    logger.info("game_restored_from_db", game_id=game_id)
    return sess.get_public_state()


@router.post("/game/{game_id_or_code}/join")
async def join_game(game_id_or_code: str, request: JoinGameRequest):
    """
    Join a game by UUID or short code.

    Supports both:
    - UUID: /game/ccb2e8af-aaf2-4dfe-9611-b146f6866461/join
    - Short code: /game/royal-turtle-65/join

    If after join the table is full and the session is in LOBBY, automatically start the round.
    If the player is a bot, schedule the bot runner.
    """
    # Resolve to actual game_id
    game_id = await resolve_game_identifier(game_id_or_code, SESSIONS, raise_on_not_found=True)

    if game_id not in SESSIONS:
        # Try to load from database
        sess = await load_game_from_db(game_id)
        if not sess:
            raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

        # Add to memory
        async with sessions_lock:
            SESSIONS[game_id] = sess

    sess = SESSIONS[game_id]
    player_id = str(uuid.uuid4())
    p = PlayerInfo(player_id=player_id, name=request.name, is_bot=request.is_bot)
    seat = await sess.add_player(p)

    # broadcast new lobby state
    await broadcast_state(game_id)

    # Save game state after player join
    await save_game_state(game_id, reason="player_join")

    # If the table is now full and still in lobby, auto-start
    try:
        if len(sess.players) >= sess.seats and sess.state == SessionState.LOBBY:
            logger.info(
                "auto_starting_game",
                game_id=game_id,
                player_count=len(sess.players),
                seats=sess.seats,
            )
            await sess.start_round(dealer=0)
            # broadcast updated state after start
            await broadcast_state(game_id)
            # schedule bots to run
            schedule_bot_runner(game_id)
    except Exception as e:
        # log error but do not fail join
        logger.error(
            "auto_start_failed",
            game_id=game_id,
            error=str(e),
            traceback=traceback.format_exc(),
        )

    # If this seat is a bot, ensure bot-runner runs
    if request.is_bot:
        schedule_bot_runner(game_id)

    logger.info(
        "player_joined",
        game_id=game_id,
        player_id=player_id,
        seat=seat,
        is_bot=request.is_bot,
    )
    return {"player_id": player_id, "seat": seat}


@router.post("/game/{game_id}/start")
async def start_game(game_id: str, request: StartGameRequest):
    """
    Start a game round with validation.

    If not all seats are filled, automatically add bots to fill empty seats
    before starting the game.
    """
    if game_id not in SESSIONS:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    sess = SESSIONS[game_id]

    # Auto-fill empty seats with bots
    bots_added = 0
    for seat_idx in range(sess.seats):
        if seat_idx not in sess.players:
            # Add a bot to this empty seat
            bot_id = str(uuid.uuid4())
            bot_name = f"Bot {seat_idx + 1}"
            bot_player = PlayerInfo(player_id=bot_id, name=bot_name, is_bot=True)
            await sess.add_player(bot_player)
            bots_added += 1
            logger.info("auto_added_bot", game_id=game_id, seat=seat_idx, bot_name=bot_name)

    if bots_added > 0:
        # Broadcast state with bots added before starting
        await broadcast_state(game_id)
        await save_game_state(game_id, reason="bots_added")

    await sess.start_round(dealer=request.dealer)
    await broadcast_state(game_id)

    # Save game state after round start
    await save_game_state(game_id, reason="round_start")

    # schedule bots if any
    schedule_bot_runner(game_id)

    logger.info("game_started", game_id=game_id, dealer=request.dealer, bots_added=bots_added)
    return {"ok": True, "bots_added": bots_added}


@router.post("/game/{game_id}/bid")
async def place_bid(game_id: str, seat: int, cmd: BidCmd):
    """Place a bid in the bidding phase."""
    if game_id not in SESSIONS:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    sess = SESSIONS[game_id]
    ok, msg = await sess.place_bid(seat, cmd)
    await broadcast_state(game_id)

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Save game state after bid
    await save_game_state(game_id, reason="bid")

    # schedule bots
    schedule_bot_runner(game_id)
    return {"ok": True, "msg": msg}


@router.post("/game/{game_id}/choose_trump")
async def choose_trump(game_id: str, seat: int, cmd: ChooseTrumpCmd):
    """Choose trump suit after winning the bid."""
    if game_id not in SESSIONS:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    sess = SESSIONS[game_id]
    ok, msg = await sess.choose_trump(seat, cmd)
    await broadcast_state(game_id)

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Save game state after trump choice
    await save_game_state(game_id, reason="choose_trump")

    schedule_bot_runner(game_id)
    return {"ok": True, "msg": msg}


@router.post("/game/{game_id}/play")
async def play_card(game_id: str, seat: int, cmd: PlayCardCmd):
    """Play a card during the play phase."""
    if game_id not in SESSIONS:
        raise HTTPException(status_code=404, detail=ErrorMessage.GAME_NOT_FOUND)

    sess = SESSIONS[game_id]
    ok, msg = await sess.play_card(seat, cmd)
    await broadcast_state(game_id)

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Save game state after card play
    await save_game_state(game_id, reason="play")

    # If round is over, compute scores
    if sess.state.value == SessionState.SCORING.value:
        scores = sess.compute_scores()
        await broadcast_state(game_id)
        await save_game_state(game_id, reason="scoring")
        return {"ok": True, "msg": msg, "scores": scores}

    schedule_bot_runner(game_id)
    return {"ok": True, "msg": msg}
