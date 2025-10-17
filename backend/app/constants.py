"""
Constants and enums for the Thurup card game backend.

This module centralizes all magic numbers, string literals, and configuration
constants to improve code maintainability and avoid magic values.
"""

from enum import Enum


# ============================================================================
# Game Configuration
# ============================================================================


class GameMode(str, Enum):
    """Valid game modes."""

    MODE_28 = "28"
    MODE_56 = "56"


class Suit(str, Enum):
    """Card suits."""

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"


class GameConfig:
    """Game rules and limits."""

    # Bidding
    MIN_BID_DEFAULT = 14
    MAX_BID_28 = 28
    MAX_BID_56 = 56

    # Players
    MIN_SEATS = 4
    MAX_SEATS = 6
    VALID_SEAT_COUNTS = [4, 6]

    # Player names
    MIN_PLAYER_NAME_LENGTH = 1
    MAX_PLAYER_NAME_LENGTH = 50

    # Timeouts (in hours)
    LOBBY_TIMEOUT_HOURS = 1
    ACTIVE_GAME_TIMEOUT_HOURS = 2
    COMPLETED_GAME_RETENTION_HOURS = 24


# ============================================================================
# Bot Configuration
# ============================================================================


class BotConfig:
    """Bot behavior settings."""

    # Timing
    ACTION_DELAY_SECONDS = 0.12
    MAX_CYCLES_PER_RUN = 200

    # AI difficulty settings
    EASY_MODE_NAME = "easy"


class AIConfig:
    """AI decision-making parameters."""

    # Bidding behavior
    PASS_PROBABILITY = 0.45
    BID_RANDOMNESS_RANGE = 5

    # Card play
    PREFER_HIGH_CARD_PROBABILITY = 0.7


# ============================================================================
# Network Configuration
# ============================================================================


class NetworkConfig:
    """Network and WebSocket settings."""

    # WebSocket reconnection (frontend)
    WS_RECONNECT_INITIAL_DELAY_MS = 1000
    WS_RECONNECT_MAX_DELAY_MS = 30000
    WS_MAX_RECONNECT_ATTEMPTS = 5

    # Timeouts
    WS_RECEIVE_TIMEOUT_SECONDS = 120
    HTTP_REQUEST_TIMEOUT_SECONDS = 30


# ============================================================================
# WebSocket Message Types
# ============================================================================


class WSMessageType(str, Enum):
    """WebSocket message types for client-server communication."""

    # Client → Server
    IDENTIFY = "identify"
    REQUEST_STATE = "request_state"
    PLACE_BID = "place_bid"
    CHOOSE_TRUMP = "choose_trump"
    PLAY_CARD = "play_card"

    # Server → Client
    STATE_SNAPSHOT = "state_snapshot"
    ACTION_OK = "action_ok"
    ACTION_FAILED = "action_failed"
    ERROR = "error"


# ============================================================================
# Session State (already defined in session.py as enum, for reference)
# ============================================================================


class SessionPhase(str, Enum):
    """
    Game session phases (duplicated from session.py for reference).
    Note: The canonical definition is in game/session.py as SessionState.
    """

    LOBBY = "lobby"
    DEALING = "dealing"
    BIDDING = "bidding"
    CHOOSE_TRUMP = "choose_trump"
    PLAY = "play"
    SCORING = "scoring"
    ROUND_END = "round_end"


# ============================================================================
# HTTP Status Messages
# ============================================================================


class ErrorMessage:
    """Standard error messages."""

    GAME_NOT_FOUND = "Game not found"
    SEAT_OUT_OF_RANGE = "Seat number out of valid range"
    INVALID_SEAT = "Invalid seat number"
    NAME_REQUIRED = "Player name is required"
    INVALID_MODE = "Game mode must be '28' or '56'"
    INVALID_SUIT = "Invalid suit (must be ♠, ♥, ♦, or ♣)"
    NOT_YOUR_TURN = "Not your turn"
    NOT_IN_PHASE = "Action not allowed in current game phase"
    CARD_NOT_IN_HAND = "Card not in your hand"
    MUST_FOLLOW_SUIT = "Must follow suit if possible"


# ============================================================================
# Bid Values
# ============================================================================


class BidValue:
    """Special bid values."""

    PASS = -1  # Internal representation of a pass
    NO_BID = None  # Not yet bid


# ============================================================================
# Team Configuration
# ============================================================================


class TeamConfig:
    """Team assignment rules."""

    TEAM_COUNT = 2
    TEAM_0 = 0  # Even seats
    TEAM_1 = 1  # Odd seats

    @staticmethod
    def get_team(seat: int) -> int:
        """Get team index from seat number."""
        return 0 if seat % 2 == 0 else 1


# ============================================================================
# Card Ranks and Scoring
# ============================================================================


class CardRank(str, Enum):
    """Card ranks in order."""

    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class CardPoints:
    """Point values for cards."""

    JACK = 3
    NINE = 2
    ACE = 1
    TEN = 1
    KING = 0
    QUEEN = 0
    EIGHT = 0
    SEVEN = 0

    @staticmethod
    def get_points(rank: str) -> int:
        """Get point value for a rank."""
        return {
            "J": 3,
            "9": 2,
            "A": 1,
            "10": 1,
        }.get(rank, 0)
