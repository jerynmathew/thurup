# backend/app/game/trick_manager.py
"""
Trick Manager - Encapsulates all logic for managing tricks in a card game.

This class consolidates trick state management, winner determination, and points
calculation that were previously scattered throughout the GameSession class.
"""

from typing import Dict, List, Optional, Tuple
from app.game.rules import Card, determine_trick_winner, trick_points


class TrickManager:
    """
    Manages trick state and operations for a game session.

    Responsibilities:
    - Track current trick being played
    - Track last completed trick
    - Track all captured tricks
    - Determine trick winners
    - Calculate trick points
    - Provide trick state for serialization
    """

    def __init__(self):
        """Initialize empty trick state."""
        self.current_trick: List[Tuple[int, Card]] = []
        self.last_trick: Optional[Tuple[int, List[Tuple[int, Card]]]] = None
        self.captured_tricks: List[Tuple[int, List[Tuple[int, Card]]]] = []

    def reset(self):
        """Reset all trick state (called when starting new round)."""
        self.current_trick = []
        self.last_trick = None
        self.captured_tricks = []

    def add_card_to_current_trick(self, seat: int, card: Card):
        """Add a card to the current trick."""
        self.current_trick.append((seat, card))

    def is_trick_complete(self, seats: int) -> bool:
        """Check if current trick has all cards played."""
        return len(self.current_trick) >= seats

    def get_lead_suit(self) -> Optional[str]:
        """Get the lead suit of current trick, or None if no trick started."""
        if not self.current_trick:
            return None
        return self.current_trick[0][1].suit

    def complete_trick(self, trump: Optional[str], points_by_seat: Dict[int, int]) -> int:
        """
        Complete the current trick: determine winner, award points, save trick.

        Args:
            trump: Trump suit (None if hidden)
            points_by_seat: Mutable dict to update with points

        Returns:
            Seat number of trick winner
        """
        if not self.current_trick:
            raise ValueError("No trick to complete")

        # Determine winner
        winner = determine_trick_winner(self.current_trick, trump)

        # Calculate points
        pts = trick_points(self.current_trick)
        points_by_seat[winner] = points_by_seat.get(winner, 0) + pts

        # Save completed trick
        self.last_trick = (winner, list(self.current_trick))
        self.captured_tricks.append((winner, list(self.current_trick)))

        # Clear current trick for next round
        self.current_trick = []

        return winner

    def get_current_trick_dict(self) -> Optional[Dict[int, Dict]]:
        """
        Get current trick as dict for API serialization.

        Returns:
            Dict mapping seat -> card dict, or None if no trick in progress
        """
        if not self.current_trick:
            return None
        return {seat: card.to_dict() for seat, card in self.current_trick}

    def get_last_trick_dict(self) -> Optional[Dict[str, any]]:
        """
        Get last completed trick as dict for API serialization.

        Returns:
            Dict with 'winner' and 'cards' keys, or None if no last trick
        """
        if not self.last_trick:
            return None

        winner, trick_cards = self.last_trick
        return {
            "winner": winner,
            "cards": {seat: card.to_dict() for seat, card in trick_cards}
        }

    def get_captured_tricks_for_serialization(self) -> List[Dict]:
        """
        Get all captured tricks in format suitable for database serialization.

        Returns:
            List of dicts with winner, cards, and points for each trick
        """
        result = []
        for winner_seat, trick_cards in self.captured_tricks:
            result.append({
                "winner": winner_seat,
                "cards": [{"seat": s, "card": c.to_dict()} for s, c in trick_cards],
                "points": trick_points(trick_cards)
            })
        return result

    def restore_from_state(
        self,
        current_trick: List[Tuple[int, Card]],
        last_trick: Optional[Tuple[int, List[Tuple[int, Card]]]],
        captured_tricks: List[Tuple[int, List[Tuple[int, Card]]]]
    ):
        """Restore trick state from saved game state."""
        self.current_trick = current_trick
        self.last_trick = last_trick
        self.captured_tricks = captured_tricks
