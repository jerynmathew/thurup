"""
Admin and debug endpoints with basic authentication.

Provides:
- Session inspection and debugging
- Manual game state manipulation
- Connection monitoring
- Server health checks
- Database diagnostics
"""

import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from app.api.v1.connection_manager import connection_manager
from app.api.v1.persistence_integration import delete_game_from_db, save_game_state
from app.api.v1.router import SESSIONS, bot_tasks, router, sessions_lock
from app.db.config import AsyncSessionLocal
from app.db.models import GameModel, GameStateSnapshotModel, PlayerModel, RoundHistoryModel
from app.logging_config import get_logger
from sqlalchemy import func, select

logger = get_logger(__name__)

# Basic auth setup
security = HTTPBasic()

# Get admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Verify admin credentials using HTTP Basic Auth.

    Returns username if valid, raises HTTPException otherwise.
    """
    is_correct_username = credentials.username == ADMIN_USERNAME
    is_correct_password = credentials.password == ADMIN_PASSWORD

    if not (is_correct_username and is_correct_password):
        logger.warning(
            "admin_auth_failed",
            username=credentials.username,
            remote_addr="unknown",  # Would need request context
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info("admin_auth_success", username=credentials.username)
    return credentials.username


# Response models
class SessionInfo(BaseModel):
    """Information about an in-memory game session."""

    game_id: str
    short_code: Optional[str]
    mode: str
    seats: int
    state: str
    player_count: int
    connection_count: int
    connected_seats: List[int]
    has_bot_task: bool


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""

    game_id: str
    seat: Optional[int]
    connected_at: float
    last_activity: float
    idle_seconds: float


class ServerHealth(BaseModel):
    """Server health metrics."""

    status: str
    uptime_seconds: float
    in_memory_sessions: int
    total_connections: int
    running_bot_tasks: int
    database_connected: bool


class DatabaseStats(BaseModel):
    """Database statistics."""

    total_games: int
    total_players: int
    total_snapshots: int
    db_size_bytes: Optional[int]


@router.get("/admin/health", response_model=ServerHealth)
async def get_server_health(username: str = Depends(verify_admin)):
    """
    Get server health and status metrics.

    Requires admin authentication.
    """
    # Count connections across all games
    total_connections = len(connection_manager._connection_details)

    # Test database connection
    db_connected = False
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(1))
            db_connected = True
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))

    # Calculate uptime (would need startup timestamp in production)
    # For now, just return a placeholder
    uptime = 0.0

    health = ServerHealth(
        status="healthy" if db_connected else "degraded",
        uptime_seconds=uptime,
        in_memory_sessions=len(SESSIONS),
        total_connections=total_connections,
        running_bot_tasks=len(bot_tasks),
        database_connected=db_connected,
    )

    logger.info("health_check_performed", username=username, health=health.model_dump())
    return health


@router.get("/admin/sessions", response_model=List[SessionInfo])
async def list_sessions(username: str = Depends(verify_admin)):
    """
    List all in-memory game sessions with connection info.

    Requires admin authentication.
    """
    session_infos = []

    async with sessions_lock:
        for game_id, sess in SESSIONS.items():
            # Get connection info
            connection_count = connection_manager.get_connection_count(game_id)
            connected_seats = list(connection_manager.get_present_seats(game_id))
            has_bot_task = game_id in bot_tasks

            session_infos.append(
                SessionInfo(
                    game_id=game_id,
                    short_code=sess.short_code,
                    mode=sess.mode,
                    seats=sess.seats,
                    state=sess.state.value,
                    player_count=len(sess.players),
                    connection_count=connection_count,
                    connected_seats=connected_seats,
                    has_bot_task=has_bot_task,
                )
            )

    logger.info("sessions_listed", username=username, count=len(session_infos))
    return session_infos


@router.get("/admin/sessions/{game_id}/detail")
async def get_session_detail(game_id: str, username: str = Depends(verify_admin)):
    """
    Get detailed information about a specific session.

    Returns full session state including hands, bids, tricks, etc.
    Requires admin authentication.
    """
    sess = SESSIONS.get(game_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found in memory")

    # Get full state
    public_state = sess.get_public_state().model_dump()

    # Add all player hands (admin can see everything)
    hands = {seat: sess.get_hand_for(seat) for seat in sess.players.keys()}

    # Get connection info
    connection_count = connection_manager.get_connection_count(game_id)
    connected_seats = list(connection_manager.get_present_seats(game_id))

    detail = {
        "game_id": game_id,
        "public_state": public_state,
        "all_hands": hands,
        "connection_count": connection_count,
        "connected_seats": connected_seats,
        "has_bot_task": game_id in bot_tasks,
    }

    logger.info("session_detail_retrieved", username=username, game_id=game_id)
    return detail


@router.get("/admin/connections")
async def list_connections(username: str = Depends(verify_admin)):
    """
    List all active WebSocket connections.

    Requires admin authentication.
    """
    connections = []

    for ws, info in connection_manager._connection_details.items():
        idle_seconds = datetime.now(timezone.utc).timestamp() - info.last_activity

        connections.append(
            {
                "game_id": info.game_id,
                "seat": info.seat,
                "connected_at": info.connected_at,
                "last_activity": info.last_activity,
                "idle_seconds": idle_seconds,
            }
        )

    logger.info("connections_listed", username=username, count=len(connections))
    return {"connections": connections, "total": len(connections)}


@router.get("/admin/database/stats", response_model=DatabaseStats)
async def get_database_stats(username: str = Depends(verify_admin)):
    """
    Get database statistics.

    Requires admin authentication.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Count games
            games_result = await db.execute(select(func.count(GameModel.id)))
            total_games = games_result.scalar() or 0

            # Count players
            players_result = await db.execute(select(func.count(PlayerModel.id)))
            total_players = players_result.scalar() or 0

            # Count snapshots
            snapshots_result = await db.execute(
                select(func.count(GameStateSnapshotModel.id))
            )
            total_snapshots = snapshots_result.scalar() or 0

            stats = DatabaseStats(
                total_games=total_games,
                total_players=total_players,
                total_snapshots=total_snapshots,
                db_size_bytes=None,  # Would need OS-specific query
            )

            logger.info(
                "database_stats_retrieved", username=username, stats=stats.model_dump()
            )
            return stats

    except Exception as e:
        logger.error("database_stats_failed", username=username, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get database stats")


@router.post("/admin/sessions/{game_id}/save")
async def force_save_session(game_id: str, username: str = Depends(verify_admin)):
    """
    Manually trigger a save of a game session to database.

    Requires admin authentication.
    """
    sess = SESSIONS.get(game_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found in memory")

    success = await save_game_state(game_id, reason="admin_manual")

    if success:
        logger.info("session_saved_manually", username=username, game_id=game_id)
        return {"ok": True, "message": "Session saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save session")


@router.delete("/admin/sessions/{game_id}")
async def delete_session(game_id: str, username: str = Depends(verify_admin)):
    """
    Delete a game session from both memory and database.

    This is a destructive operation. Use with caution.
    Requires admin authentication.
    """
    # Remove from memory
    async with sessions_lock:
        sess = SESSIONS.pop(game_id, None)

    if not sess:
        logger.warning("session_delete_not_found", username=username, game_id=game_id)

    # Remove from database
    db_deleted = await delete_game_from_db(game_id)

    logger.info(
        "session_deleted",
        username=username,
        game_id=game_id,
        from_memory=sess is not None,
        from_database=db_deleted,
    )

    return {
        "ok": True,
        "deleted_from_memory": sess is not None,
        "deleted_from_database": db_deleted,
    }


@router.post("/admin/sessions/{game_id}/kill_bots")
async def kill_bot_task(game_id: str, username: str = Depends(verify_admin)):
    """
    Forcefully stop the bot runner task for a game.

    Useful for debugging bot issues or stopping runaway bot loops.
    Requires admin authentication.
    """
    task = bot_tasks.get(game_id)

    if not task:
        raise HTTPException(status_code=404, detail="No bot task running for this game")

    # Cancel the task
    task.cancel()

    # Clean up from registry
    bot_tasks.pop(game_id, None)

    logger.info("bot_task_killed", username=username, game_id=game_id)
    return {"ok": True, "message": "Bot task cancelled"}


@router.get("/admin/logs/recent")
async def get_recent_logs(limit: int = 50, username: str = Depends(verify_admin)):
    """
    Get recent log entries.

    Note: This is a placeholder. In production, you would query
    your logging backend (e.g., CloudWatch, Datadog, etc.).

    Requires admin authentication.
    """
    logger.info("recent_logs_requested", username=username, limit=limit)

    return {
        "message": "Log retrieval not implemented. Check your logging backend.",
        "note": "Configure LOG_JSON=true and pipe logs to your aggregation service.",
    }


@router.post("/admin/maintenance/cleanup")
async def trigger_cleanup(username: str = Depends(verify_admin)):
    """
    Manually trigger database cleanup of old games.

    Requires admin authentication.
    """
    try:
        async with AsyncSessionLocal() as db:
            from app.db.repository import GameRepository

            repo = GameRepository(db)
            deleted_count = await repo.cleanup_old_games()
            await db.commit()

        logger.info(
            "manual_cleanup_triggered", username=username, deleted_count=deleted_count
        )
        return {"ok": True, "deleted_games": deleted_count}

    except Exception as e:
        logger.error("manual_cleanup_failed", username=username, error=str(e))
        raise HTTPException(status_code=500, detail="Cleanup failed")


# ===== GAME HISTORY ENDPOINTS =====


class GameHistoryItem(BaseModel):
    """Summary information for a game in the history list."""

    game_id: str
    short_code: str
    mode: str
    seats: int
    state: str
    rounds_played: int
    created_at: datetime
    last_activity_at: datetime
    player_names: List[str]


@router.get("/admin/games/history", response_model=List[GameHistoryItem])
async def list_game_history(
    limit: int = 50, offset: int = 0, username: str = Depends(verify_admin)
):
    """
    List all games with basic info and round counts.

    Returns games ordered by last_activity_at descending (most recent first).
    Requires admin authentication.
    """
    try:
        async with AsyncSessionLocal() as db:
            from app.db.repository import GameRepository, PlayerRepository, RoundHistoryRepository

            game_repo = GameRepository(db)
            player_repo = PlayerRepository(db)
            round_repo = RoundHistoryRepository(db)

            # Get games ordered by last activity
            result = await db.execute(
                select(GameModel)
                .order_by(GameModel.last_activity_at.desc())
                .limit(limit)
                .offset(offset)
            )
            games = list(result.scalars().all())

            history_items = []
            for game in games:
                # Get player names
                players = await player_repo.get_players_for_game(game.id)
                player_names = [p.name for p in players]

                # Get round count
                rounds_count = await round_repo.get_round_count(game.id)

                history_items.append(
                    GameHistoryItem(
                        game_id=game.id,
                        short_code=game.short_code or "",
                        mode=game.mode,
                        seats=game.seats,
                        state=game.state,
                        rounds_played=rounds_count,
                        created_at=game.created_at,
                        last_activity_at=game.last_activity_at,
                        player_names=player_names,
                    )
                )

            logger.info(
                "game_history_listed",
                username=username,
                count=len(history_items),
                limit=limit,
                offset=offset,
            )
            return history_items

    except Exception as e:
        logger.error("game_history_list_failed", username=username, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list game history")


@router.get("/admin/games/{game_id}/rounds")
async def get_game_rounds(game_id: str, username: str = Depends(verify_admin)):
    """
    Get detailed game information including all rounds played.

    Returns:
    - Game metadata (short_code, mode, seats, state, etc.)
    - All players
    - Complete round history with tricks, cards, scores

    Requires admin authentication.
    """
    try:
        async with AsyncSessionLocal() as db:
            from app.db.repository import (
                GameRepository,
                PlayerRepository,
                RoundHistoryRepository,
            )

            game_repo = GameRepository(db)
            player_repo = PlayerRepository(db)
            round_repo = RoundHistoryRepository(db)

            # Get game
            game = await game_repo.get_game(game_id)
            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            # Get players
            players = await player_repo.get_players_for_game(game_id)
            player_list = [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "seat": p.seat,
                    "is_bot": p.is_bot,
                    "joined_at": p.joined_at.isoformat(),
                }
                for p in players
            ]

            # Get all rounds
            rounds = await round_repo.get_rounds_for_game(game_id)
            rounds_list = []
            for round_model in rounds:
                import json

                round_data = json.loads(round_model.round_data)
                rounds_list.append(
                    {
                        "round_number": round_model.round_number,
                        "dealer": round_model.dealer,
                        "bid_winner": round_model.bid_winner,
                        "bid_value": round_model.bid_value,
                        "trump": round_model.trump,
                        "created_at": round_model.created_at.isoformat(),
                        "round_data": round_data,  # Full round details
                    }
                )

            result = {
                "game_id": game.id,
                "short_code": game.short_code,
                "mode": game.mode,
                "seats": game.seats,
                "min_bid": game.min_bid,
                "hidden_trump_mode": game.hidden_trump_mode,
                "two_decks_for_56": game.two_decks_for_56,
                "state": game.state,
                "created_at": game.created_at.isoformat(),
                "updated_at": game.updated_at.isoformat(),
                "last_activity_at": game.last_activity_at.isoformat(),
                "players": player_list,
                "rounds": rounds_list,
                "total_rounds": len(rounds_list),
            }

            logger.info(
                "game_rounds_retrieved",
                username=username,
                game_id=game_id,
                rounds_count=len(rounds_list),
            )
            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("game_rounds_retrieval_failed", username=username, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve game rounds")
