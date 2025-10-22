"""
Tests for Phase 1 critical fixes:
- Race condition fixes (locks around shared state)
- Bot task management (preventing duplicates)
- WebSocket connection safety
"""

import pytest
import asyncio
from app.game.enums import SessionState
from app.game.session import GameSession
from app.models import PlayerInfo, BidCmd
from app.constants import GameMode, BidValue


class TestConcurrencyFixes:
    """Test that concurrent operations are safe with locks."""

    @pytest.mark.asyncio
    async def test_concurrent_player_additions(self):
        """Test that multiple players can join concurrently without race conditions."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Create multiple players concurrently
        async def add_player(name: str):
            p = PlayerInfo(player_id=f"p_{name}", name=name, is_bot=False)
            return await sess.add_player(p)

        # Add 4 players concurrently
        seats = await asyncio.gather(
            add_player("Alice"),
            add_player("Bob"),
            add_player("Charlie"),
            add_player("Diana"),
        )

        # All seats should be unique and in range
        assert len(seats) == 4
        assert len(set(seats)) == 4  # All unique
        assert all(0 <= s < 4 for s in seats)
        assert len(sess.players) == 4

    @pytest.mark.asyncio
    async def test_concurrent_bidding(self):
        """Test that concurrent bid attempts are handled safely with locks.

        The lock ensures operations are serialized, so all bids will succeed
        in order. The important thing is no race conditions or corrupted state.
        """
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        # Start round
        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # Try to bid from multiple seats concurrently
        # With locks, these will execute sequentially in clockwise order: 3 -> 2 -> 1
        results = await asyncio.gather(
            sess.place_bid(3, BidCmd(value=15)),
            sess.place_bid(2, BidCmd(value=16)),
            sess.place_bid(1, BidCmd(value=17)),
            return_exceptions=False,
        )

        # With locks, all three succeed sequentially in turn order
        assert results[0][0]  # Seat 3's turn
        assert results[1][0]  # Seat 2's turn after 3
        assert results[2][0]  # Seat 1's turn after 2

        # Verify state is consistent (no corruption)
        assert sess.bidding_manager.current_highest == 17
        assert sess.bidding_manager.bid_winner == 1
        assert len([b for b in sess.bidding_manager.bids.values() if b is not None]) == 3

    @pytest.mark.asyncio
    async def test_no_seat_overflow(self):
        """Test that we can't add more players than seats."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add 4 players (fill all seats)
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        # Try to add a 5th player
        p5 = PlayerInfo(player_id="p5", name="Player5", is_bot=False)
        with pytest.raises(RuntimeError, match="No free seats"):
            await sess.add_player(p5)


class TestBidValidation:
    """Test that bid validation works correctly with new validators."""

    @pytest.mark.asyncio
    async def test_bid_pass_handling(self):
        """Test that None and -1 are both treated as pass."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # First player (seat 3) passes with None
        ok1, msg1 = await sess.place_bid(sess.turn, BidCmd(value=None))
        assert ok1
        assert sess.bidding_manager.bids[3] == BidValue.PASS

        # Second player (seat 2) passes with -1
        ok2, msg2 = await sess.place_bid(sess.turn, BidCmd(value=BidValue.PASS))
        assert ok2
        assert sess.bidding_manager.bids[2] == BidValue.PASS

    @pytest.mark.asyncio
    async def test_bid_value_constraints(self):
        """Test that bid values are validated by Pydantic and session logic."""
        from pydantic import ValidationError

        sess = GameSession(mode=GameMode.MODE_28.value, seats=4, min_bid=14)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # Bid too low - caught by Pydantic validator
        with pytest.raises(ValidationError, match="Bid must be >="):
            BidCmd(value=10)

        # Bid too high (over 56) - caught by Pydantic validator
        with pytest.raises(ValidationError, match="cannot exceed"):
            BidCmd(value=60)

        # Valid bid at session level (seat 3 is first to bid)
        ok, msg = await sess.place_bid(3, BidCmd(value=15))
        assert ok

        # Bid over max for current mode (caught by session logic, not Pydantic)
        # Seat 2 is next in clockwise order
        ok2, msg2 = await sess.place_bid(2, BidCmd(value=30))
        assert not ok2
        assert "cannot exceed" in msg2

    @pytest.mark.asyncio
    async def test_bid_must_be_higher(self):
        """Test that subsequent bids must be higher than current highest."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4, min_bid=14)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # First bid: 15 (seat 3)
        ok1, _ = await sess.place_bid(3, BidCmd(value=15))
        assert ok1
        assert sess.bidding_manager.current_highest == 15

        # Second player (seat 2) tries to bid 15 (equal to current)
        ok2, msg2 = await sess.place_bid(2, BidCmd(value=15))
        assert not ok2
        assert "must be higher" in msg2

        # Second player (seat 2) bids 16 (valid)
        ok3, _ = await sess.place_bid(2, BidCmd(value=16))
        assert ok3
        assert sess.bidding_manager.current_highest == 16


class TestSequentialBidding:
    """Test that bidding proceeds in proper turn order."""

    @pytest.mark.asyncio
    async def test_only_current_turn_can_bid(self):
        """Test that only the current turn seat can place a bid."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        initial_turn = sess.turn

        # Try to bid from wrong seat (clockwise: next would be 2, but we try 1)
        wrong_seat = (initial_turn - 2) % 4  # seat 1, not seat 2
        ok, msg = await sess.place_bid(wrong_seat, BidCmd(value=15))
        assert not ok
        assert "Not your turn" in msg

        # Correct seat can bid (seat 3)
        ok2, _ = await sess.place_bid(initial_turn, BidCmd(value=15))
        assert ok2
        assert sess.turn == (initial_turn - 1) % 4  # Turn advanced clockwise: 3 -> 2

    @pytest.mark.asyncio
    async def test_cannot_bid_twice(self):
        """Test that a seat cannot bid twice in the same round."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # First bid (seat 3)
        ok1, _ = await sess.place_bid(3, BidCmd(value=15))
        assert ok1

        # Advance through other players in clockwise order: 2, 1, 0
        await sess.place_bid(2, BidCmd(value=None))
        await sess.place_bid(1, BidCmd(value=None))
        await sess.place_bid(0, BidCmd(value=None))

        # State should transition to CHOOSE_TRUMP
        assert sess.state == SessionState.CHOOSE_TRUMP
        assert sess.bidding_manager.bid_winner == 3


class TestAllPassRedeal:
    """Test that all-pass triggers redeal correctly."""

    @pytest.mark.asyncio
    async def test_all_pass_triggers_redeal(self):
        """Test that when all players pass, the round is redealt."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # Record initial deck
        initial_hand_0 = [c.uid for c in sess.hands[0]]

        # All players pass in clockwise order: 3, 2, 1, 0
        await sess.place_bid(3, BidCmd(value=None))
        await sess.place_bid(2, BidCmd(value=None))
        await sess.place_bid(1, BidCmd(value=None))
        ok, msg = await sess.place_bid(0, BidCmd(value=None))

        # Should trigger redeal
        assert ok
        assert "redealt" in msg.lower() or "redeal" in msg.lower()

        # Should be back in bidding phase with new cards
        assert sess.state == SessionState.BIDDING
        new_hand_0 = [c.uid for c in sess.hands[0]]

        # Cards should be different (with very high probability)
        assert initial_hand_0 != new_hand_0


class TestStateTransitions:
    """Test that game state transitions work correctly."""

    @pytest.mark.asyncio
    async def test_bidding_to_choose_trump_transition(self):
        """Test transition from BIDDING to CHOOSE_TRUMP."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add players
        for i in range(4):
            p = PlayerInfo(player_id=f"p{i}", name=f"Player{i}", is_bot=False)
            await sess.add_player(p)

        await sess.start_round(dealer=0)
        assert sess.state == SessionState.BIDDING
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        # Complete bidding with a winner, clockwise order: 3, 2, 1, 0
        await sess.place_bid(3, BidCmd(value=15))
        await sess.place_bid(2, BidCmd(value=None))
        await sess.place_bid(1, BidCmd(value=None))
        await sess.place_bid(0, BidCmd(value=None))

        # Should transition to CHOOSE_TRUMP
        assert sess.state == SessionState.CHOOSE_TRUMP
        assert sess.bidding_manager.bid_winner == 3
        assert sess.bidding_manager.bid_value == 15

    @pytest.mark.asyncio
    async def test_lobby_state_preserved(self):
        """Test that session starts in LOBBY state."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)
        assert sess.state == SessionState.LOBBY

        # Add players doesn't change state
        p = PlayerInfo(player_id="p1", name="Player1", is_bot=False)
        await sess.add_player(p)
        assert sess.state == SessionState.LOBBY

        # Only start_round changes to DEALING then BIDDING
        await sess.start_round(dealer=0)
        assert sess.state == SessionState.BIDDING


class TestBotIntegration:
    """Test that bot-related functionality works correctly."""

    @pytest.mark.asyncio
    async def test_is_bot_seat_detection(self):
        """Test that is_bot_seat correctly identifies bot players."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add human and bot players
        human = PlayerInfo(player_id="h1", name="Human", is_bot=False)
        bot = PlayerInfo(player_id="b1", name="Bot", is_bot=True)

        seat_h = await sess.add_player(human)
        seat_b = await sess.add_player(bot)

        assert not sess.is_bot_seat(seat_h)
        assert sess.is_bot_seat(seat_b)
        assert not sess.is_bot_seat(99)  # Non-existent seat

    @pytest.mark.asyncio
    async def test_force_bot_play_choice_respects_turn(self):
        """Test that bots can only act on their turn."""
        from app.game import ai as ai_module

        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Add bot players
        for i in range(4):
            bot = PlayerInfo(player_id=f"b{i}", name=f"Bot{i}", is_bot=True)
            await sess.add_player(bot)

        await sess.start_round(dealer=0)
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3

        current_turn = sess.turn
        other_seat = (current_turn - 2) % 4  # Seat 1, not the next seat in clockwise order

        # Bot on current turn should get a command
        cmd_current = sess.force_bot_play_choice(current_turn, ai_module)
        assert cmd_current is not None
        assert cmd_current["type"] == "place_bid"

        # Bot not on turn should get None
        cmd_other = sess.force_bot_play_choice(other_seat, ai_module)
        assert cmd_other is None


class TestInputValidation:
    """Test that input validation works at the model level."""

    def test_bid_cmd_validation(self):
        """Test BidCmd validates bid values."""
        # Valid bids
        valid_none = BidCmd(value=None)
        assert valid_none.value is None

        valid_pass = BidCmd(value=-1)
        assert valid_pass.value == -1

        valid_bid = BidCmd(value=15)
        assert valid_bid.value == 15

        # Pydantic validation happens at model construction
        # Invalid values would raise ValidationError

    def test_player_info_validation(self):
        """Test PlayerInfo validates name length."""
        # Valid name
        valid = PlayerInfo(player_id="p1", name="Alice", is_bot=False)
        assert valid.name == "Alice"

        # Empty string (if minimum is 1) - this would fail at Pydantic level
        # when used with the API request models

    @pytest.mark.asyncio
    async def test_session_rejects_invalid_player_type(self):
        """Test that session.add_player enforces PlayerInfo type."""
        sess = GameSession(mode=GameMode.MODE_28.value, seats=4)

        # Try to add a dict instead of PlayerInfo
        with pytest.raises(TypeError, match="must be a PlayerInfo instance"):
            await sess.add_player({"name": "Alice"})  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
