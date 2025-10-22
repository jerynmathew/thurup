# backend/app/game/enums.py
"""
Game enums - Separated to avoid circular imports.
"""

from enum import Enum


class HiddenTrumpMode(str, Enum):
    """Modes for when hidden trump is revealed."""
    ON_FIRST_NONFOLLOW = "on_first_nonfollow"
    ON_FIRST_TRUMP_PLAY = "on_first_trump_play"
    ON_BIDDER_NONFOLLOW = "on_bidder_nonfollow"
    OPEN_IMMEDIATELY = "open_immediately"


class SessionState(str, Enum):
    """Game session states."""
    LOBBY = "lobby"
    DEALING = "dealing"
    BIDDING = "bidding"
    CHOOSE_TRUMP = "choose_trump"
    PLAY = "play"
    SCORING = "scoring"
    ROUND_END = "round_end"
