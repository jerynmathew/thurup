"""
SQLModel database models for Thurup game persistence.

SQLModel combines SQLAlchemy and Pydantic for type-safe database models
with automatic validation and serialization.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class GameModel(SQLModel, table=True):
    """
    Represents a game session in the database.

    Stores core game metadata and serialized game state.
    """

    __tablename__ = "games"

    # Primary key
    id: str = Field(primary_key=True, max_length=36)

    # Short code for easy game identification (e.g., "brave-tiger-42")
    short_code: str = Field(unique=True, max_length=50, index=True, nullable=False)

    # Game configuration
    mode: str = Field(max_length=10, nullable=False)  # "28" or "56"
    seats: int = Field(nullable=False)
    min_bid: int = Field(nullable=False)
    hidden_trump_mode: str = Field(max_length=50, nullable=False)
    two_decks_for_56: bool = Field(nullable=False)

    # Game state
    state: str = Field(max_length=20, nullable=False)  # LOBBY, BIDDING, etc.
    current_phase_data: Optional[str] = Field(
        default=None, nullable=True
    )  # JSON string

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class PlayerModel(SQLModel, table=True):
    """
    Represents a player in a game session.

    Links players to games and stores their seat assignment.
    """

    __tablename__ = "players"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to game
    game_id: str = Field(
        foreign_key="games.id", index=True, max_length=36, nullable=False
    )

    # Player info
    player_id: str = Field(max_length=36, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    seat: int = Field(nullable=False)
    is_bot: bool = Field(nullable=False)

    # Timestamp
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class GameStateSnapshotModel(SQLModel, table=True):
    """
    Stores periodic snapshots of complete game state for recovery.

    This allows reconstructing the full game state including cards, bids, tricks, etc.
    """

    __tablename__ = "game_state_snapshots"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to game
    game_id: str = Field(
        foreign_key="games.id", index=True, max_length=36, nullable=False
    )

    # Snapshot data (JSON string of complete game state)
    snapshot_data: str = Field(nullable=False)  # Will use sa_column for Text type

    # Metadata
    state_phase: str = Field(max_length=20, nullable=False)
    snapshot_reason: str = Field(
        max_length=50, nullable=False
    )  # "periodic", "phase_change", "manual"

    # Timestamp
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


class RoundHistoryModel(SQLModel, table=True):
    """
    Stores completed round history for game replay and analysis.

    Each row represents one completed round with all the details:
    - Players and bids
    - Trump selection
    - All tricks played with cards
    - Points and team scores
    """

    __tablename__ = "round_history"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to game
    game_id: str = Field(
        foreign_key="games.id", index=True, max_length=36, nullable=False
    )

    # Round metadata
    round_number: int = Field(nullable=False)
    dealer: int = Field(nullable=False)  # Seat number
    bid_winner: Optional[int] = Field(default=None, nullable=True)  # Seat number
    bid_value: Optional[int] = Field(default=None, nullable=True)
    trump: Optional[str] = Field(default=None, max_length=1, nullable=True)  # Suit symbol

    # Round data (JSON string containing tricks, cards, points, scores)
    # Structure: {
    #   "captured_tricks": [...],
    #   "points_by_seat": {...},
    #   "team_scores": {...}
    # }
    round_data: str = Field(nullable=False)

    # Timestamp
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
