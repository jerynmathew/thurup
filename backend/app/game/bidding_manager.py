# backend/app/game/bidding_manager.py
"""
Bidding Manager - Encapsulates all logic for managing bidding in a card game.

This class consolidates bidding state management, validation, and winner determination
that were previously scattered throughout the GameSession class.
"""

from typing import Dict, Optional, Tuple

from app.constants import BidValue, GameConfig, GameMode


class BiddingManager:
    """
    Manages bidding state and operations for a game session.

    Responsibilities:
    - Track bids for each seat
    - Track which seats have bid
    - Determine highest bid and winner
    - Validate bid values
    - Provide bidding state for serialization
    """

    def __init__(self, seats: int):
        """Initialize bidding state for given number of seats."""
        self.seats = seats
        self.bids: Dict[int, Optional[int]] = {i: None for i in range(seats)}
        self.bids_received: set[int] = set()
        self.current_highest: Optional[int] = None
        self.bid_winner: Optional[int] = None
        self.bid_value: Optional[int] = None

    def reset(self):
        """Reset all bidding state (called when starting new round)."""
        self.bids = {i: None for i in range(self.seats)}
        self.bids_received = set()
        self.current_highest = None
        self.bid_winner = None
        self.bid_value = None

    def place_bid(self, seat: int, value: Optional[int]) -> Tuple[bool, str]:
        """
        Record a bid for a seat.

        Args:
            seat: Seat number placing bid
            value: Bid value (or None/-1 for pass)

        Returns:
            Tuple of (success, message)
        """
        # Check if seat already acted
        if self.bids.get(seat) is not None:
            return False, "Seat already acted"

        # Handle pass
        if value is None or value == BidValue.PASS:
            self.bids[seat] = BidValue.PASS
            self.bids_received.add(seat)
            return True, "Pass recorded"

        # Record numeric bid
        self.bids[seat] = value
        self.bids_received.add(seat)

        # Update highest bid if this is higher
        if self.current_highest is None or value > self.current_highest:
            self.current_highest = value
            self.bid_winner = seat
            self.bid_value = value

        return True, "Bid recorded"

    def validate_bid(
        self, seat: int, value: Optional[int], min_bid: int, mode: str
    ) -> Tuple[bool, str]:
        """
        Validate a bid value according to game rules.

        Args:
            seat: Seat placing bid
            value: Bid value to validate
            min_bid: Minimum allowed bid
            mode: Game mode (28 or 56)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if seat already bid
        if self.bids.get(seat) is not None:
            return False, "Seat already acted"

        # Pass is always valid
        if value is None or value == BidValue.PASS:
            return True, ""

        # Validate numeric bid
        if not isinstance(value, int):
            return False, "Bid must be integer (use -1 or None for pass)"

        if value < min_bid:
            return False, f"Bid must be >= {min_bid}"

        max_total = (
            GameConfig.MAX_BID_28 if mode == GameMode.MODE_28.value else GameConfig.MAX_BID_56
        )
        if value > max_total:
            return False, f"Bid cannot exceed {max_total}"

        if self.current_highest is not None and value <= self.current_highest:
            return False, "Bid must be higher than current highest"

        return True, ""

    def is_complete(self) -> bool:
        """Check if all seats have placed bids."""
        return all(v is not None for v in self.bids.values())

    def all_passed(self) -> bool:
        """Check if all seats passed (no valid bids)."""
        return all(v == BidValue.PASS for v in self.bids.values())

    def get_bids_dict(self) -> Dict[int, Optional[int]]:
        """Get bids as dict for API serialization."""
        return dict(self.bids)

    def restore_from_state(
        self,
        bids: Dict[int, Optional[int]],
        bids_received: set[int],
        current_highest: Optional[int],
        bid_winner: Optional[int],
        bid_value: Optional[int],
    ):
        """Restore bidding state from saved game state."""
        self.bids = bids
        self.bids_received = bids_received
        self.current_highest = current_highest
        self.bid_winner = bid_winner
        self.bid_value = bid_value
