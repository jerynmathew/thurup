"""
Repository layer for database operations.

Implements the Repository pattern to abstract database access from business logic.
Provides async methods for CRUD operations on game data.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import GameConfig
from app.db.models import GameModel, GameStateSnapshotModel, PlayerModel, RoundHistoryModel
from app.logging_config import get_logger

logger = get_logger(__name__)


class GameRepository:
    """Repository for game-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_game(
        self,
        game_id: str,
        short_code: str,
        mode: str,
        seats: int,
        min_bid: int,
        hidden_trump_mode: str,
        two_decks_for_56: bool,
        state: str = "lobby",
    ) -> GameModel:
        """Create a new game in the database."""
        game = GameModel(
            id=game_id,
            short_code=short_code,
            mode=mode,
            seats=seats,
            min_bid=min_bid,
            hidden_trump_mode=hidden_trump_mode,
            two_decks_for_56=two_decks_for_56,
            state=state,
        )
        self.session.add(game)
        await self.session.flush()
        logger.info("game_created_in_db", game_id=game_id, short_code=short_code, mode=mode, seats=seats)
        return game

    async def get_game(self, game_id: str) -> Optional[GameModel]:
        """Retrieve a game by ID."""
        result = await self.session.execute(
            select(GameModel).where(GameModel.id == game_id)
        )
        return result.scalar_one_or_none()

    async def get_game_by_short_code(self, short_code: str) -> Optional[GameModel]:
        """Retrieve a game by short code."""
        result = await self.session.execute(
            select(GameModel).where(GameModel.short_code == short_code)
        )
        return result.scalar_one_or_none()

    async def get_all_short_codes(self) -> List[str]:
        """Get all existing short codes (for collision avoidance)."""
        result = await self.session.execute(
            select(GameModel.short_code)
        )
        return [row[0] for row in result.all()]

    async def update_game_state(
        self, game_id: str, state: str, phase_data: Optional[dict] = None
    ) -> bool:
        """Update game state and phase data."""
        game = await self.get_game(game_id)
        if not game:
            return False

        game.state = state
        if phase_data is not None:
            game.current_phase_data = json.dumps(phase_data)
        game.last_activity_at = datetime.now(timezone.utc)
        game.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
        logger.debug("game_state_updated", game_id=game_id, state=state)
        return True

    async def get_active_games(self) -> List[GameModel]:
        """Get all active games (not in terminal states)."""
        terminal_states = ["completed", "abandoned"]
        result = await self.session.execute(
            select(GameModel).where(GameModel.state.not_in(terminal_states))
        )
        return list(result.scalars().all())

    async def delete_game(self, game_id: str) -> bool:
        """Delete a game and all related data."""
        game = await self.get_game(game_id)
        if not game:
            return False

        # Delete related data first (cascade)
        await self.session.execute(
            delete(PlayerModel).where(PlayerModel.game_id == game_id)
        )
        await self.session.execute(
            delete(GameStateSnapshotModel).where(
                GameStateSnapshotModel.game_id == game_id
            )
        )

        # Delete game
        await self.session.delete(game)
        await self.session.flush()
        logger.info("game_deleted_from_db", game_id=game_id)
        return True

    async def cleanup_old_games(
        self,
        lobby_hours: int = GameConfig.LOBBY_TIMEOUT_HOURS,
        active_hours: int = GameConfig.ACTIVE_GAME_TIMEOUT_HOURS,
        completed_hours: int = GameConfig.COMPLETED_GAME_RETENTION_HOURS,
    ) -> int:
        """
        Clean up old games based on state and age.

        Returns number of games deleted.
        """
        now = datetime.now(timezone.utc)
        deleted_count = 0

        # Cleanup lobby games older than lobby_hours
        lobby_cutoff = now - timedelta(hours=lobby_hours)
        lobby_games = await self.session.execute(
            select(GameModel).where(
                GameModel.state == "lobby", GameModel.last_activity_at < lobby_cutoff
            )
        )
        for game in lobby_games.scalars():
            await self.delete_game(game.id)
            deleted_count += 1

        # Cleanup active games with no activity for active_hours
        active_cutoff = now - timedelta(hours=active_hours)
        active_states = ["bidding", "choose_trump", "play", "scoring"]
        active_games = await self.session.execute(
            select(GameModel).where(
                GameModel.state.in_(active_states),
                GameModel.last_activity_at < active_cutoff,
            )
        )
        for game in active_games.scalars():
            await self.delete_game(game.id)
            deleted_count += 1

        # Cleanup completed games older than completed_hours
        completed_cutoff = now - timedelta(hours=completed_hours)
        completed_games = await self.session.execute(
            select(GameModel).where(
                GameModel.state.in_(["completed", "abandoned"]),
                GameModel.last_activity_at < completed_cutoff,
            )
        )
        for game in completed_games.scalars():
            await self.delete_game(game.id)
            deleted_count += 1

        if deleted_count > 0:
            logger.info("old_games_cleaned_up", count=deleted_count)

        return deleted_count


class PlayerRepository:
    """Repository for player-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_player(
        self, game_id: str, player_id: str, name: str, seat: int, is_bot: bool
    ) -> PlayerModel:
        """Add a player to a game."""
        player = PlayerModel(
            game_id=game_id, player_id=player_id, name=name, seat=seat, is_bot=is_bot
        )
        self.session.add(player)
        await self.session.flush()
        logger.debug(
            "player_added_to_db", game_id=game_id, player_id=player_id, seat=seat
        )
        return player

    async def get_players_for_game(self, game_id: str) -> List[PlayerModel]:
        """Get all players for a game."""
        result = await self.session.execute(
            select(PlayerModel)
            .where(PlayerModel.game_id == game_id)
            .order_by(PlayerModel.seat)
        )
        return list(result.scalars().all())

    async def remove_player(self, game_id: str, player_id: str) -> bool:
        """Remove a player from a game."""
        result = await self.session.execute(
            delete(PlayerModel).where(
                PlayerModel.game_id == game_id, PlayerModel.player_id == player_id
            )
        )
        await self.session.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.debug("player_removed_from_db", game_id=game_id, player_id=player_id)
        return deleted


class SnapshotRepository:
    """Repository for game state snapshot operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_snapshot(
        self,
        game_id: str,
        snapshot_data: dict,
        state_phase: str,
        reason: str = "periodic",
    ) -> GameStateSnapshotModel:
        """Create a game state snapshot."""
        snapshot = GameStateSnapshotModel(
            game_id=game_id,
            snapshot_data=json.dumps(snapshot_data),
            state_phase=state_phase,
            snapshot_reason=reason,
        )
        self.session.add(snapshot)
        await self.session.flush()
        logger.debug(
            "snapshot_created", game_id=game_id, phase=state_phase, reason=reason
        )
        return snapshot

    async def get_latest_snapshot(
        self, game_id: str
    ) -> Optional[GameStateSnapshotModel]:
        """Get the most recent snapshot for a game."""
        result = await self.session.execute(
            select(GameStateSnapshotModel)
            .where(GameStateSnapshotModel.game_id == game_id)
            .order_by(GameStateSnapshotModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_snapshots_for_game(
        self, game_id: str, limit: int = 10
    ) -> List[GameStateSnapshotModel]:
        """Get recent snapshots for a game."""
        result = await self.session.execute(
            select(GameStateSnapshotModel)
            .where(GameStateSnapshotModel.game_id == game_id)
            .order_by(GameStateSnapshotModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cleanup_old_snapshots(self, game_id: str, keep_count: int = 5) -> int:
        """Keep only the N most recent snapshots for a game."""
        # Get snapshots to keep
        keep_snapshots = await self.session.execute(
            select(GameStateSnapshotModel.id)
            .where(GameStateSnapshotModel.game_id == game_id)
            .order_by(GameStateSnapshotModel.created_at.desc())
            .limit(keep_count)
        )
        keep_ids = [row[0] for row in keep_snapshots.all()]

        if not keep_ids:
            return 0

        # Delete old snapshots
        result = await self.session.execute(
            delete(GameStateSnapshotModel).where(
                GameStateSnapshotModel.game_id == game_id,
                GameStateSnapshotModel.id.not_in(keep_ids),
            )
        )
        deleted = result.rowcount
        if deleted > 0:
            logger.debug("old_snapshots_cleaned", game_id=game_id, deleted=deleted)
        return deleted


class RoundHistoryRepository:
    """Repository for round history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_round(
        self,
        game_id: str,
        round_number: int,
        dealer: int,
        bid_winner: Optional[int],
        bid_value: Optional[int],
        trump: Optional[str],
        round_data: dict,
    ) -> RoundHistoryModel:
        """Save a completed round to the database."""
        round_history = RoundHistoryModel(
            game_id=game_id,
            round_number=round_number,
            dealer=dealer,
            bid_winner=bid_winner,
            bid_value=bid_value,
            trump=trump,
            round_data=json.dumps(round_data),
        )
        self.session.add(round_history)
        await self.session.flush()
        logger.info(
            "round_saved_to_db",
            game_id=game_id,
            round_number=round_number,
            bid_winner=bid_winner,
            trump=trump,
        )
        return round_history

    async def get_rounds_for_game(self, game_id: str) -> List[RoundHistoryModel]:
        """Get all rounds for a game, ordered by round number."""
        result = await self.session.execute(
            select(RoundHistoryModel)
            .where(RoundHistoryModel.game_id == game_id)
            .order_by(RoundHistoryModel.round_number)
        )
        return list(result.scalars().all())

    async def get_round(self, game_id: str, round_number: int) -> Optional[RoundHistoryModel]:
        """Get a specific round by number."""
        result = await self.session.execute(
            select(RoundHistoryModel).where(
                RoundHistoryModel.game_id == game_id,
                RoundHistoryModel.round_number == round_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_round_count(self, game_id: str) -> int:
        """Get the total number of rounds played in a game."""
        result = await self.session.execute(
            select(RoundHistoryModel)
            .where(RoundHistoryModel.game_id == game_id)
        )
        return len(list(result.scalars().all()))
