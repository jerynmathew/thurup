# backend/app/models.py
from __future__ import annotations
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.constants import (
    BidValue,
    CardRank,
    ErrorMessage,
    GameConfig,
    GameMode,
    Suit,
)


class CardDTO(BaseModel):
    """Data transfer object for a playing card."""

    suit: str = Field(..., description="Card suit (♠, ♥, ♦, or ♣)")
    rank: str = Field(..., description="Card rank (7-10, J, Q, K, A)")
    id: str = Field(..., description="Unique card identifier")

    @field_validator("suit")
    @classmethod
    def validate_suit(cls, v: str) -> str:
        valid_suits = [s.value for s in Suit]
        if v not in valid_suits:
            raise ValueError(ErrorMessage.INVALID_SUIT)
        return v

    @field_validator("rank")
    @classmethod
    def validate_rank(cls, v: str) -> str:
        valid_ranks = [r.value for r in CardRank]
        if v not in valid_ranks:
            raise ValueError(f"Invalid rank (must be one of {', '.join(valid_ranks)})")
        return v


class PlayerInfo(BaseModel):
    """Information about a player in the game."""

    player_id: Optional[str] = Field(None, description="Unique player identifier")
    name: Optional[str] = Field(
        None,
        min_length=GameConfig.MIN_PLAYER_NAME_LENGTH,
        max_length=GameConfig.MAX_PLAYER_NAME_LENGTH,
        description="Player display name",
    )
    seat: Optional[int] = Field(
        None, ge=0, lt=GameConfig.MAX_SEATS, description="Player's seat number"
    )
    is_bot: bool = Field(False, description="Whether this player is a bot")


class GameStateDTO(BaseModel):
    game_id: str
    short_code: Optional[str] = None
    mode: str
    seats: int
    state: str
    players: List[PlayerInfo]
    dealer: int  # current dealer position
    leader: int  # player to dealer's right (first to bid/play)
    turn: int
    trump: Optional[str]
    kitty: List[CardDTO]
    hand_sizes: Dict[int, int]
    bids: Dict[int, Optional[int]]
    current_highest: Optional[int]
    bid_winner: Optional[int]
    bid_value: Optional[int]
    points_by_seat: Dict[int, int]
    current_trick: Optional[Dict[int, CardDTO]] = None  # seat -> card mapping
    lead_suit: Optional[str] = None  # suit to follow
    last_trick: Optional[Dict[str, Any]] = None  # {winner: int, cards: Dict[int, CardDTO]}
    rounds_history: List[Dict[str, Any]] = []  # History of completed rounds


# ============================================================================
# Command Models (for game actions)
# ============================================================================


class BidCmd(BaseModel):
    """Command to place a bid during bidding phase."""

    value: Optional[int] = Field(None, description="Bid value (None or -1 for pass)")

    @field_validator("value")
    @classmethod
    def validate_bid(cls, v: Optional[int]) -> Optional[int]:
        if v is None or v == BidValue.PASS:
            return v
        if not isinstance(v, int):
            raise ValueError("Bid must be an integer or None/−1 for pass")
        if v < GameConfig.MIN_BID_DEFAULT:
            raise ValueError(f"Bid must be >= {GameConfig.MIN_BID_DEFAULT}")
        if v > GameConfig.MAX_BID_56:  # use max possible bid
            raise ValueError(f"Bid cannot exceed {GameConfig.MAX_BID_56}")
        return v


class ChooseTrumpCmd(BaseModel):
    """Command to choose trump suit."""

    suit: str = Field(..., description="Trump suit (♠, ♥, ♦, or ♣)")

    @field_validator("suit")
    @classmethod
    def validate_suit(cls, v: str) -> str:
        valid_suits = [s.value for s in Suit]
        if v not in valid_suits:
            raise ValueError(ErrorMessage.INVALID_SUIT)
        return v


class PlayCardCmd(BaseModel):
    """Command to play a card."""

    card_id: str = Field(
        ..., min_length=1, description="Unique card identifier to play"
    )


class RevealTrumpCmd(BaseModel):
    """Command to manually reveal trump."""

    pass  # No parameters needed, seat comes from route/WebSocket payload


# ============================================================================
# Request Models (for REST API endpoints)
# ============================================================================


class CreateGameRequest(BaseModel):
    """Request to create a new game."""

    mode: str = Field(GameMode.MODE_28.value, description="Game mode (28 or 56)")
    seats: int = Field(GameConfig.MIN_SEATS, description="Number of player seats")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in (GameMode.MODE_28.value, GameMode.MODE_56.value):
            raise ValueError(ErrorMessage.INVALID_MODE)
        return v

    @field_validator("seats")
    @classmethod
    def validate_seats(cls, v: int) -> int:
        if v not in GameConfig.VALID_SEAT_COUNTS:
            raise ValueError(f"Seats must be one of {GameConfig.VALID_SEAT_COUNTS}")
        return v


class JoinGameRequest(BaseModel):
    """Request to join a game."""

    name: str = Field(
        ...,
        min_length=GameConfig.MIN_PLAYER_NAME_LENGTH,
        max_length=GameConfig.MAX_PLAYER_NAME_LENGTH,
        description="Player name",
    )
    is_bot: bool = Field(False, description="Whether this player is a bot")


class StartGameRequest(BaseModel):
    """Request to start a game round."""

    dealer: int = Field(
        0, ge=0, lt=GameConfig.MAX_SEATS, description="Dealer seat index"
    )


class GameActionRequest(BaseModel):
    """Base request for game actions that require a seat."""

    seat: int = Field(
        ..., ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number"
    )


# ============================================================================
# WebSocket Message Models
# ============================================================================


class WSIdentifyPayload(BaseModel):
    """Payload for WebSocket identify message."""

    seat: Optional[int] = Field(None, ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number")
    player_id: Optional[str] = Field(None, description="Player identifier")


class WSPlaceBidPayload(BaseModel):
    """Payload for WebSocket place_bid message."""

    seat: int = Field(..., ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number")
    value: Optional[int] = Field(None, description="Bid value (None or -1 for pass)")

    @field_validator("value")
    @classmethod
    def validate_bid(cls, v: Optional[int]) -> Optional[int]:
        if v is None or v == BidValue.PASS:
            return v
        if not isinstance(v, int):
            raise ValueError("Bid must be an integer or None/−1 for pass")
        if v < GameConfig.MIN_BID_DEFAULT:
            raise ValueError(f"Bid must be >= {GameConfig.MIN_BID_DEFAULT}")
        if v > GameConfig.MAX_BID_56:
            raise ValueError(f"Bid cannot exceed {GameConfig.MAX_BID_56}")
        return v


class WSChooseTrumpPayload(BaseModel):
    """Payload for WebSocket choose_trump message."""

    seat: int = Field(..., ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number")
    suit: str = Field(..., description="Trump suit (♠, ♥, ♦, or ♣)")

    @field_validator("suit")
    @classmethod
    def validate_suit(cls, v: str) -> str:
        valid_suits = [s.value for s in Suit]
        if v not in valid_suits:
            raise ValueError(ErrorMessage.INVALID_SUIT)
        return v


class WSPlayCardPayload(BaseModel):
    """Payload for WebSocket play_card message."""

    seat: int = Field(..., ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number")
    card_id: str = Field(..., min_length=1, description="Unique card identifier to play")


class WSRevealTrumpPayload(BaseModel):
    """Payload for WebSocket reveal_trump message."""

    seat: int = Field(..., ge=0, lt=GameConfig.MAX_SEATS, description="Player seat number")


class WSMessage(BaseModel):
    """WebSocket message wrapper with type and payload."""

    type: str = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
