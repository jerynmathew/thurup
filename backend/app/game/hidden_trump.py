# backend/app/game/hidden_trump.py
"""
Hidden Trump Manager - Encapsulates all logic for revealing hidden trump cards.

This class consolidates the various trump reveal rules that were previously
scattered throughout the GameSession class, making the logic easier to test
and maintain.
"""

from typing import List, Optional, Tuple
from app.game.enums import HiddenTrumpMode
from app.game.rules import Card
from app.logging_config import get_logger

logger = get_logger(__name__)


class HiddenTrumpManager:
    """
    Manages the hidden trump reveal logic for a game session.

    This class is stateless and pure - it doesn't store game state,
    but rather evaluates whether trump should be revealed based on
    the current game situation.
    """

    @staticmethod
    def should_reveal_trump(
        trump_hidden: bool,
        hidden_trump_mode: HiddenTrumpMode,
        played_card: Card,
        trump_suit: Optional[str],
        trump_owner_seat: Optional[int],
        player_seat: int,
        current_trick: List[Tuple[int, Card]],
        player_hand: List[Card],
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if trump should be revealed based on the card played.

        Args:
            trump_hidden: Whether trump is currently hidden
            hidden_trump_mode: The reveal mode being used
            played_card: The card that was just played
            trump_suit: The trump suit (if known)
            trump_owner_seat: Seat of the player who chose trump
            player_seat: Seat of the player who played the card
            current_trick: List of (seat, card) tuples for current trick
            player_hand: Remaining cards in player's hand (before card was removed)

        Returns:
            Tuple of (should_reveal: bool, reason: Optional[str])
            reason is provided for logging/debugging purposes
        """
        # Already revealed - nothing to do
        if not trump_hidden:
            return False, None

        # No trump set yet - can't reveal
        if trump_suit is None:
            return False, None

        # Check each reveal mode
        if hidden_trump_mode == HiddenTrumpMode.OPEN_IMMEDIATELY:
            return True, "open_immediately_mode"

        if hidden_trump_mode == HiddenTrumpMode.ON_FIRST_TRUMP_PLAY:
            if played_card.suit == trump_suit:
                return True, f"first_trump_played_by_seat_{player_seat}"

        if hidden_trump_mode == HiddenTrumpMode.ON_FIRST_NONFOLLOW:
            if current_trick and len(current_trick) >= 1:
                lead_suit = current_trick[0][1].suit
                # Check if player had lead suit but didn't follow
                player_has_lead = any(c.suit == lead_suit for c in player_hand)
                if player_has_lead and played_card.suit != lead_suit:
                    return True, f"nonfollow_by_seat_{player_seat}"

        if hidden_trump_mode == HiddenTrumpMode.ON_BIDDER_NONFOLLOW:
            if player_seat == trump_owner_seat:
                if current_trick:
                    lead_suit = current_trick[0][1].suit
                    # Check if bidder had lead suit but didn't follow
                    player_has_lead = any(c.suit == lead_suit for c in player_hand)
                    if player_has_lead and played_card.suit != lead_suit:
                        return True, f"bidder_nonfollow_seat_{player_seat}"

        # No reveal condition met
        return False, None

    @staticmethod
    def validate_manual_reveal(
        trump_hidden: bool,
        player_seat: int,
        current_turn: int,
        current_trick: List[Tuple[int, Card]],
        player_hand: List[Card],
    ) -> Tuple[bool, str]:
        """
        Validate if a player can manually reveal trump.

        Args:
            trump_hidden: Whether trump is currently hidden
            player_seat: Seat attempting to reveal
            current_turn: Current turn (who can act)
            current_trick: Current trick cards
            player_hand: Player's current hand

        Returns:
            Tuple of (is_valid: bool, error_message: str)
            error_message is empty string if valid
        """
        if not trump_hidden:
            return False, "Trump already revealed"

        if player_seat != current_turn:
            return False, "Not your turn"

        # Must be during an active trick (not leading)
        if not current_trick:
            return False, "Cannot reveal trump when leading"

        # Verify player can't follow suit
        lead_suit = current_trick[0][1].suit
        if any(c.suit == lead_suit for c in player_hand):
            return False, "You can follow suit, cannot reveal trump"

        return True, ""
