"""
Game history and replay endpoints.

Provides:
- Query game history with filters
- Retrieve completed games
- Replay game from snapshots
- Game statistics and metrics
"""

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel

from app.api.v1.router import router
from app.db.config import AsyncSessionLocal
from app.db.models import GameModel, GameStateSnapshotModel, PlayerModel
from app.logging_config import get_logger
from sqlalchemy import func, select

logger = get_logger(__name__)


# Response models
class PlayerSummary(BaseModel):
    """Summary of a player in a game."""

    player_id: str
    name: str
    seat: int
    is_bot: bool
    joined_at: datetime


class GameSummary(BaseModel):
    """Summary of a game for history listing."""

    game_id: str
    mode: str
    seats: int
    state: str
    players: List[PlayerSummary]
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime


class SnapshotSummary(BaseModel):
    """Summary of a game state snapshot."""

    snapshot_id: int
    game_id: str
    state_phase: str
    snapshot_reason: str
    created_at: datetime


class GameDetail(BaseModel):
    """Detailed game information including snapshots."""

    game: GameSummary
    snapshots: List[SnapshotSummary]
    total_snapshots: int


class GameHistoryStats(BaseModel):
    """Statistics about game history."""

    total_games: int
    completed_games: int
    active_games: int
    abandoned_games: int
    total_players: int
    total_bots: int


@router.get("/history/games", response_model=List[GameSummary])
async def list_games(
    state: Optional[str] = Query(
        None, description="Filter by game state (completed, active, abandoned, etc.)"
    ),
    mode: Optional[str] = Query(None, description="Filter by game mode (28, 56)"),
    limit: int = Query(20, ge=1, le=100, description="Number of games to return"),
    offset: int = Query(0, ge=0, description="Number of games to skip"),
):
    """
    List games with optional filters.

    Returns games ordered by last_activity_at descending (most recent first).
    """
    try:
        async with AsyncSessionLocal() as db:
            # Build query
            query = select(GameModel)

            # Apply filters
            if state:
                if state == "active":
                    # Active means not in terminal states
                    terminal_states = ["completed", "abandoned"]
                    query = query.where(GameModel.state.not_in(terminal_states))
                else:
                    query = query.where(GameModel.state == state)

            if mode:
                query = query.where(GameModel.mode == mode)

            # Order and paginate
            query = (
                query.order_by(GameModel.last_activity_at.desc())
                .offset(offset)
                .limit(limit)
            )

            # Execute query
            result = await db.execute(query)
            games = result.scalars().all()

            # Build response with players
            game_summaries = []
            for game in games:
                # Get players for this game
                players_result = await db.execute(
                    select(PlayerModel)
                    .where(PlayerModel.game_id == game.id)
                    .order_by(PlayerModel.seat)
                )
                players = players_result.scalars().all()

                player_summaries = [
                    PlayerSummary(
                        player_id=p.player_id,
                        name=p.name,
                        seat=p.seat,
                        is_bot=p.is_bot,
                        joined_at=p.joined_at,
                    )
                    for p in players
                ]

                game_summaries.append(
                    GameSummary(
                        game_id=game.id,
                        mode=game.mode,
                        seats=game.seats,
                        state=game.state,
                        players=player_summaries,
                        created_at=game.created_at,
                        updated_at=game.updated_at,
                        last_activity_at=game.last_activity_at,
                    )
                )

            logger.info(
                "games_listed",
                count=len(game_summaries),
                state=state,
                mode=mode,
                limit=limit,
                offset=offset,
            )
            return game_summaries

    except Exception as e:
        logger.error("list_games_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list games")


@router.get("/history/games/{game_id}", response_model=GameDetail)
async def get_game_detail(game_id: str):
    """
    Get detailed information about a specific game including all snapshots.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Get game
            game_result = await db.execute(
                select(GameModel).where(GameModel.id == game_id)
            )
            game = game_result.scalar_one_or_none()

            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            # Get players
            players_result = await db.execute(
                select(PlayerModel)
                .where(PlayerModel.game_id == game_id)
                .order_by(PlayerModel.seat)
            )
            players = players_result.scalars().all()

            player_summaries = [
                PlayerSummary(
                    player_id=p.player_id,
                    name=p.name,
                    seat=p.seat,
                    is_bot=p.is_bot,
                    joined_at=p.joined_at,
                )
                for p in players
            ]

            # Get snapshots
            snapshots_result = await db.execute(
                select(GameStateSnapshotModel)
                .where(GameStateSnapshotModel.game_id == game_id)
                .order_by(GameStateSnapshotModel.created_at.asc())
            )
            snapshots = snapshots_result.scalars().all()

            snapshot_summaries = [
                SnapshotSummary(
                    snapshot_id=s.id,
                    game_id=s.game_id,
                    state_phase=s.state_phase,
                    snapshot_reason=s.snapshot_reason,
                    created_at=s.created_at,
                )
                for s in snapshots
            ]

            game_summary = GameSummary(
                game_id=game.id,
                mode=game.mode,
                seats=game.seats,
                state=game.state,
                players=player_summaries,
                created_at=game.created_at,
                updated_at=game.updated_at,
                last_activity_at=game.last_activity_at,
            )

            logger.info(
                "game_detail_retrieved",
                game_id=game_id,
                snapshot_count=len(snapshot_summaries),
            )

            return GameDetail(
                game=game_summary,
                snapshots=snapshot_summaries,
                total_snapshots=len(snapshot_summaries),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_game_detail_failed", game_id=game_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get game detail")


@router.get("/history/games/{game_id}/snapshots/{snapshot_id}")
async def get_snapshot_data(game_id: str, snapshot_id: int):
    """
    Get the full game state data for a specific snapshot.

    This returns the complete serialized game state for replay purposes.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Get snapshot
            snapshot_result = await db.execute(
                select(GameStateSnapshotModel).where(
                    GameStateSnapshotModel.id == snapshot_id,
                    GameStateSnapshotModel.game_id == game_id,
                )
            )
            snapshot = snapshot_result.scalar_one_or_none()

            if not snapshot:
                raise HTTPException(status_code=404, detail="Snapshot not found")

            # Parse snapshot data
            import json

            snapshot_data = json.loads(snapshot.snapshot_data)

            logger.info(
                "snapshot_data_retrieved",
                game_id=game_id,
                snapshot_id=snapshot_id,
                phase=snapshot.state_phase,
            )

            return {
                "snapshot_id": snapshot.id,
                "game_id": snapshot.game_id,
                "state_phase": snapshot.state_phase,
                "snapshot_reason": snapshot.snapshot_reason,
                "created_at": snapshot.created_at,
                "data": snapshot_data,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_snapshot_data_failed",
            game_id=game_id,
            snapshot_id=snapshot_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to get snapshot data")


@router.get("/history/stats", response_model=GameHistoryStats)
async def get_history_stats():
    """
    Get overall statistics about game history.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Count total games
            total_games_result = await db.execute(select(func.count(GameModel.id)))
            total_games = total_games_result.scalar()

            # Count by state
            completed_result = await db.execute(
                select(func.count(GameModel.id)).where(GameModel.state == "completed")
            )
            completed_games = completed_result.scalar()

            active_result = await db.execute(
                select(func.count(GameModel.id)).where(
                    GameModel.state.not_in(["completed", "abandoned"])
                )
            )
            active_games = active_result.scalar()

            abandoned_result = await db.execute(
                select(func.count(GameModel.id)).where(GameModel.state == "abandoned")
            )
            abandoned_games = abandoned_result.scalar()

            # Count players
            total_players_result = await db.execute(select(func.count(PlayerModel.id)))
            total_players = total_players_result.scalar()

            total_bots_result = await db.execute(
                select(func.count(PlayerModel.id)).where(PlayerModel.is_bot)
            )
            total_bots = total_bots_result.scalar()

            stats = GameHistoryStats(
                total_games=total_games or 0,
                completed_games=completed_games or 0,
                active_games=active_games or 0,
                abandoned_games=abandoned_games or 0,
                total_players=total_players or 0,
                total_bots=total_bots or 0,
            )

            logger.info("history_stats_retrieved", stats=stats.model_dump())
            return stats

    except Exception as e:
        logger.error("get_history_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get history stats")


@router.get("/history/games/{game_id}/replay")
async def get_game_replay(game_id: str):
    """
    Get a chronological replay of the game using all snapshots.

    Returns all snapshots in order, allowing a client to replay the game
    step-by-step from start to finish.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Verify game exists
            game_result = await db.execute(
                select(GameModel).where(GameModel.id == game_id)
            )
            game = game_result.scalar_one_or_none()

            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            # Get all snapshots in chronological order
            snapshots_result = await db.execute(
                select(GameStateSnapshotModel)
                .where(GameStateSnapshotModel.game_id == game_id)
                .order_by(GameStateSnapshotModel.created_at.asc())
            )
            snapshots = snapshots_result.scalars().all()

            if not snapshots:
                raise HTTPException(
                    status_code=404, detail="No snapshots available for replay"
                )

            # Parse all snapshot data
            import json

            replay_data = []
            for snapshot in snapshots:
                replay_data.append(
                    {
                        "snapshot_id": snapshot.id,
                        "state_phase": snapshot.state_phase,
                        "snapshot_reason": snapshot.snapshot_reason,
                        "created_at": snapshot.created_at,
                        "data": json.loads(snapshot.snapshot_data),
                    }
                )

            logger.info(
                "game_replay_retrieved",
                game_id=game_id,
                snapshot_count=len(replay_data),
            )

            return {
                "game_id": game_id,
                "mode": game.mode,
                "seats": game.seats,
                "state": game.state,
                "created_at": game.created_at,
                "snapshots": replay_data,
                "total_snapshots": len(replay_data),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_game_replay_failed", game_id=game_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get game replay")
