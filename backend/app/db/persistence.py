"""
Session persistence layer for saving and loading GameSession state.

Handles serialization/deserialization of game sessions to/from database.
"""

import json
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GameModel
from app.db.repository import (
    GameRepository,
    PlayerRepository,
    RoundHistoryRepository,
    SnapshotRepository,
)
from app.game.rules import Card
from app.game.session import GameSession, HiddenTrumpMode, SessionState
from app.logging_config import get_logger
from app.models import PlayerInfo

logger = get_logger(__name__)


class SessionPersistence:
    """Handles saving and loading GameSession objects to/from database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.game_repo = GameRepository(db_session)
        self.player_repo = PlayerRepository(db_session)
        self.snapshot_repo = SnapshotRepository(db_session)
        self.round_history_repo = RoundHistoryRepository(db_session)

    async def save_session(
        self, session: GameSession, snapshot_reason: str = "manual"
    ) -> bool:
        """
        Save complete game session state to database.

        Creates/updates game record, player records, and creates a snapshot.
        """
        try:
            # Check if game exists
            existing_game = await self.game_repo.get_game(session.id)

            if existing_game:
                # Update existing game
                await self.game_repo.update_game_state(
                    game_id=session.id,
                    state=session.state.value,
                    phase_data=self._serialize_phase_data(session),
                )
            else:
                # Create new game
                await self.game_repo.create_game(
                    game_id=session.id,
                    short_code=session.short_code or "",
                    mode=session.mode,
                    seats=session.seats,
                    min_bid=session.min_bid,
                    hidden_trump_mode=session.hidden_trump_mode.value,
                    two_decks_for_56=session.two_decks_for_56,
                    state=session.state.value,
                )

            # Sync players (create/update) - do this on every save
            # Get existing players from database
            existing_players = await self.player_repo.get_players_for_game(session.id)
            existing_player_seats = {p.seat for p in existing_players}

            # Add any new players that aren't in the database yet
            for seat, player in session.players.items():
                if seat not in existing_player_seats:
                    await self.player_repo.add_player(
                        game_id=session.id,
                        player_id=player.player_id,
                        name=player.name,
                        seat=seat,
                        is_bot=player.is_bot,
                    )

            # Create snapshot of complete game state
            snapshot_data = self._serialize_full_state(session)
            await self.snapshot_repo.create_snapshot(
                game_id=session.id,
                snapshot_data=snapshot_data,
                state_phase=session.state.value,
                reason=snapshot_reason,
            )

            # Save any new rounds to database
            # Get count of rounds already saved
            saved_rounds_count = await self.round_history_repo.get_round_count(
                session.id
            )
            # Save any new rounds from session.rounds_history
            for round_data in session.rounds_history[saved_rounds_count:]:
                await self.round_history_repo.save_round(
                    game_id=session.id,
                    round_number=round_data["round_number"],
                    dealer=round_data["dealer"],
                    bid_winner=round_data.get("bid_winner"),
                    bid_value=round_data.get("bid_value"),
                    trump=round_data.get("trump"),
                    round_data=round_data,  # Entire round data dict
                )

            await self.db.commit()
            logger.info(
                "session_saved",
                game_id=session.id,
                state=session.state.value,
                reason=snapshot_reason,
            )
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("session_save_failed", game_id=session.id, error=str(e))
            return False

    async def load_session(self, game_id: str) -> Optional[GameSession]:
        """
        Load game session from database.

        Retrieves latest snapshot and reconstructs GameSession object.
        """
        try:
            # Get game record
            game = await self.game_repo.get_game(game_id)
            if not game:
                logger.warning("game_not_found", game_id=game_id)
                return None

            # Get latest snapshot
            snapshot = await self.snapshot_repo.get_latest_snapshot(game_id)
            if not snapshot:
                # No snapshot, create session from game metadata only
                logger.info("no_snapshot_found", game_id=game_id)
                session = await self._create_session_from_metadata(game)
            else:
                # Restore from snapshot
                snapshot_data = json.loads(snapshot.snapshot_data)
                session = self._deserialize_full_state(snapshot_data, game)

            # Get players
            players = await self.player_repo.get_players_for_game(game_id)
            for player_model in players:
                player_info = PlayerInfo(
                    player_id=player_model.player_id,
                    name=player_model.name,
                    seat=player_model.seat,
                    is_bot=player_model.is_bot,
                )
                session.players[player_model.seat] = player_info

            logger.info("session_loaded", game_id=game_id, state=session.state.value)
            return session

        except Exception as e:
            logger.error("session_load_failed", game_id=game_id, error=str(e))
            return None

    async def delete_session(self, game_id: str) -> bool:
        """Delete game session and all related data."""
        try:
            success = await self.game_repo.delete_game(game_id)
            if success:
                await self.db.commit()
                logger.info("session_deleted", game_id=game_id)
            return success
        except Exception as e:
            await self.db.rollback()
            logger.error("session_delete_failed", game_id=game_id, error=str(e))
            return False

    def _serialize_phase_data(self, session: GameSession) -> Dict:
        """Serialize lightweight phase-specific data for game record."""
        return {
            "leader": session.leader,
            "turn": session.turn,
            "current_highest": session.current_highest,
            "bid_winner": session.bid_winner,
            "bid_value": session.bid_value,
            "trump": session.trump,
            "trump_hidden": session.trump_hidden,
            "trump_owner": session.trump_owner,
        }

    def _serialize_full_state(self, session: GameSession) -> Dict:
        """Serialize complete game state for snapshot."""
        return {
            "game_id": session.id,
            "short_code": session.short_code,
            "mode": session.mode,
            "seats": session.seats,
            "hidden_trump_mode": session.hidden_trump_mode.value,
            "min_bid": session.min_bid,
            "two_decks_for_56": session.two_decks_for_56,
            "state": session.state.value,
            # Cards
            "deck": [self._card_to_dict(c) for c in session.deck],
            "kitty": [self._card_to_dict(c) for c in session.kitty],
            "hands": [[self._card_to_dict(c) for c in hand] for hand in session.hands],
            # Bidding
            "bids": session.bids,
            "bids_received": list(session._bids_received),
            "current_highest": session.current_highest,
            "bid_winner": session.bid_winner,
            "bid_value": session.bid_value,
            # Trump
            "trump": session.trump,
            "trump_hidden": session.trump_hidden,
            "trump_owner": session.trump_owner,
            # Play
            "leader": session.leader,
            "turn": session.turn,
            "current_trick": [
                [seat, self._card_to_dict(card)] for seat, card in session.current_trick
            ],
            "captured_tricks": [
                [winner, [[s, self._card_to_dict(c)] for s, c in trick]]
                for winner, trick in session.captured_tricks
            ],
            "points_by_seat": session.points_by_seat,
        }

    def _deserialize_full_state(self, data: Dict, game: GameModel) -> GameSession:
        """Reconstruct GameSession from snapshot data."""
        session = GameSession(
            game_id=data["game_id"],
            short_code=data.get("short_code") or game.short_code,
            mode=data["mode"],
            seats=data["seats"],
            hidden_trump_mode=HiddenTrumpMode(data["hidden_trump_mode"]),
            min_bid=data["min_bid"],
            two_decks_for_56=data["two_decks_for_56"],
        )

        # Restore state
        session.state = SessionState(data["state"])

        # Restore cards
        session.deck = [self._dict_to_card(c) for c in data["deck"]]
        session.kitty = [self._dict_to_card(c) for c in data["kitty"]]
        session.hands = [
            [self._dict_to_card(c) for c in hand] for hand in data["hands"]
        ]

        # Restore bidding
        session.bids = {int(k): v for k, v in data["bids"].items()}
        session._bids_received = set(data["bids_received"])
        session.current_highest = data["current_highest"]
        session.bid_winner = data["bid_winner"]
        session.bid_value = data["bid_value"]

        # Restore trump
        session.trump = data["trump"]
        session.trump_hidden = data["trump_hidden"]
        session.trump_owner = data["trump_owner"]

        # Restore play
        session.leader = data["leader"]
        session.turn = data["turn"]
        session.current_trick = [
            (seat, self._dict_to_card(card)) for seat, card in data["current_trick"]
        ]
        session.captured_tricks = [
            (winner, [(s, self._dict_to_card(c)) for s, c in trick])
            for winner, trick in data["captured_tricks"]
        ]
        session.points_by_seat = {int(k): v for k, v in data["points_by_seat"].items()}

        return session

    async def _create_session_from_metadata(self, game: GameModel) -> GameSession:
        """Create GameSession from game metadata only (no snapshot)."""
        session = GameSession(
            game_id=game.id,
            short_code=game.short_code,
            mode=game.mode,
            seats=game.seats,
            hidden_trump_mode=HiddenTrumpMode(game.hidden_trump_mode),
            min_bid=game.min_bid,
            two_decks_for_56=game.two_decks_for_56,
        )
        session.state = SessionState(game.state)

        # Parse current_phase_data if available
        if game.current_phase_data:
            phase_data = json.loads(game.current_phase_data)
            session.leader = phase_data.get("leader", 0)
            session.turn = phase_data.get("turn", 0)
            session.current_highest = phase_data.get("current_highest")
            session.bid_winner = phase_data.get("bid_winner")
            session.bid_value = phase_data.get("bid_value")
            session.trump = phase_data.get("trump")
            session.trump_hidden = phase_data.get("trump_hidden", True)
            session.trump_owner = phase_data.get("trump_owner")

        return session

    def _card_to_dict(self, card: Card) -> Dict:
        """Convert Card to dictionary."""
        return {"suit": card.suit, "rank": card.rank, "uid": card.uid}

    def _dict_to_card(self, data: Dict) -> Card:
        """Convert dictionary to Card."""
        return Card(suit=data["suit"], rank=data["rank"], uid=data["uid"])
