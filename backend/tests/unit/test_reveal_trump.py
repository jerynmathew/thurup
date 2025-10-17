"""
Unit tests for manual trump reveal functionality.

Tests the GameSession.reveal_trump() method with various scenarios.
"""

import pytest

from app.constants import Suit
from app.game.rules import Card
from app.game.enums import SessionState
from app.game.session import GameSession
from app.models import ChooseTrumpCmd, PlayerInfo


@pytest.mark.asyncio
class TestRevealTrump:
    """Test cases for manual trump reveal feature."""

    async def setup_game_in_play(self) -> GameSession:
        """Helper to set up a game in play phase with hidden trump."""
        sess = GameSession(mode="28", seats=4)

        # Add players
        for i in range(4):
            player = PlayerInfo(
                player_id=f"player-{i}",
                name=f"Player {i}",
                seat=i,
                is_bot=False
            )
            await sess.add_player(player)

        # Start round
        await sess.start_round(dealer=0)

        # Skip bidding - manually set bid winner
        sess.state = SessionState.CHOOSE_TRUMP
        sess.bid_winner = 2
        sess.bid_value = 20

        # Choose trump (will be hidden)
        await sess.choose_trump(2, ChooseTrumpCmd(suit=Suit.HEARTS.value))

        assert sess.state == SessionState.PLAY
        assert sess.trump == Suit.HEARTS.value
        assert sess.trump_hidden is True
        # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
        assert sess.turn == 3  # Leader starts

        return sess

    async def test_reveal_trump_success(self):
        """Test successful trump reveal when player can't follow suit."""
        sess = await self.setup_game_in_play()

        # Player 3 leads (turn starts at 3 with dealer=0 in clockwise)
        # Ensure player 3 has a club to lead with
        lead_card = None
        for card in sess.hands[3]:
            if card.suit == Suit.CLUBS.value:
                lead_card = card
                break

        # If player 3 doesn't have a club, add one
        if lead_card is None:
            lead_card = Card(suit=Suit.CLUBS.value, rank="Q", uid="Q♣#1")
            sess.hands[3].append(lead_card)

        # Player 3 plays the club
        sess.hands[3].remove(lead_card)
        sess.trick_manager.current_trick.append((3, lead_card))
        # Clockwise: turn advances 3 -> 2
        sess.turn = 2

        # Remove all clubs from player 2's hand to force can't-follow-suit
        sess.hands[2] = [c for c in sess.hands[2] if c.suit != Suit.CLUBS.value]

        # Player 2 should be able to reveal trump
        ok, msg = await sess.reveal_trump(2)

        assert ok is True
        assert "revealed" in msg.lower()
        assert sess.trump_hidden is False

    async def test_reveal_trump_not_your_turn(self):
        """Test that revealing trump fails if it's not your turn."""
        sess = await self.setup_game_in_play()

        # Turn is 3 (player 3's turn), player 0 attempts to reveal
        ok, msg = await sess.reveal_trump(0)

        assert ok is False
        assert "not your turn" in msg.lower()
        assert sess.trump_hidden is True  # Trump should still be hidden

    async def test_reveal_trump_already_revealed(self):
        """Test that revealing trump fails if already revealed."""
        sess = await self.setup_game_in_play()

        # Manually reveal trump
        sess.trump_hidden = False

        # Try to reveal again (player 3 whose turn it is)
        ok, msg = await sess.reveal_trump(3)

        assert ok is False
        assert "already revealed" in msg.lower()

    async def test_reveal_trump_when_leading(self):
        """Test that revealing trump fails when leading (no current trick)."""
        sess = await self.setup_game_in_play()

        # Player 3 is leading, no trick yet
        assert len(sess.trick_manager.current_trick) == 0

        # Try to reveal trump (player 3 is leading)
        ok, msg = await sess.reveal_trump(3)

        assert ok is False
        assert "cannot reveal" in msg.lower() or "leading" in msg.lower()
        assert sess.trump_hidden is True

    async def test_reveal_trump_can_follow_suit(self):
        """Test that revealing trump fails when player can follow suit."""
        sess = await self.setup_game_in_play()

        # Ensure player 3 has a club to lead with
        lead_card = None
        for card in sess.hands[3]:
            if card.suit == Suit.CLUBS.value:
                lead_card = card
                break

        # If player 3 doesn't have a club, add one
        if lead_card is None:
            lead_card = Card(suit=Suit.CLUBS.value, rank="K", uid="K♣#1")
            sess.hands[3].append(lead_card)

        # Player 3 plays the club
        sess.hands[3].remove(lead_card)
        sess.trick_manager.current_trick.append((3, lead_card))
        sess.turn = 2  # Clockwise: 3 -> 2

        # Ensure player 2 HAS clubs (can follow suit)
        has_clubs = any(c.suit == Suit.CLUBS.value for c in sess.hands[2])
        if not has_clubs:
            # Add a club to player 2's hand
            sess.hands[2].append(Card(suit=Suit.CLUBS.value, rank="7", uid="7♣#1"))

        # Try to reveal trump
        ok, msg = await sess.reveal_trump(2)

        assert ok is False
        assert "can follow suit" in msg.lower() or "cannot reveal" in msg.lower()
        assert sess.trump_hidden is True

    async def test_reveal_trump_wrong_state(self):
        """Test that revealing trump fails if not in play phase."""
        sess = GameSession(mode="28", seats=4)

        # Add players
        for i in range(4):
            player = PlayerInfo(
                player_id=f"player-{i}",
                name=f"Player {i}",
                seat=i,
                is_bot=False
            )
            await sess.add_player(player)

        # Start round but stay in bidding
        await sess.start_round(dealer=0)
        assert sess.state == SessionState.BIDDING

        # Try to reveal trump in bidding phase
        ok, msg = await sess.reveal_trump(0)

        assert ok is False
        assert "not in play" in msg.lower()

    async def test_reveal_trump_unknown_seat(self):
        """Test that revealing trump fails for unknown seat."""
        sess = await self.setup_game_in_play()

        # Set turn to seat 99 first to get past turn check
        sess.turn = 99

        # Try to reveal with invalid seat number
        ok, msg = await sess.reveal_trump(99)

        assert ok is False
        assert "unknown seat" in msg.lower()

    async def test_reveal_trump_enforces_trump_play(self):
        """Test that after revealing trump, player must play trump if they have it."""
        sess = await self.setup_game_in_play()

        # Ensure player 3 has a club to lead with
        lead_card = None
        for card in sess.hands[3]:
            if card.suit == Suit.CLUBS.value:
                lead_card = card
                break

        # If player 3 doesn't have a club, add one
        if lead_card is None:
            lead_card = Card(suit=Suit.CLUBS.value, rank="9", uid="9♣#1")
            sess.hands[3].append(lead_card)

        # Player 3 leads with the club
        sess.hands[3].remove(lead_card)
        sess.trick_manager.current_trick.append((3, lead_card))
        sess.turn = 2  # Clockwise: 3 -> 2

        # Remove all clubs from player 2, but ensure they have hearts (trump)
        sess.hands[2] = [c for c in sess.hands[2] if c.suit != Suit.CLUBS.value]
        has_hearts = any(c.suit == Suit.HEARTS.value for c in sess.hands[2])
        if not has_hearts:
            sess.hands[2].append(Card(suit=Suit.HEARTS.value, rank="7", uid="7♥#1"))

        # Reveal trump
        ok, msg = await sess.reveal_trump(2)
        assert ok is True
        assert sess.trump_hidden is False

        # Now the frontend should enforce that only trump cards are playable
        # Backend's play_card already has follow-suit validation
        # This test verifies trump is now visible for such enforcement

    async def test_reveal_trump_no_trump_cards(self):
        """Test revealing trump when player has no trump cards (should still work)."""
        sess = await self.setup_game_in_play()

        # Ensure player 3 has a club to lead with
        lead_card = None
        for card in sess.hands[3]:
            if card.suit == Suit.CLUBS.value:
                lead_card = card
                break

        # If player 3 doesn't have a club, add one
        if lead_card is None:
            lead_card = Card(suit=Suit.CLUBS.value, rank="8", uid="8♣#1")
            sess.hands[3].append(lead_card)

        # Player 3 leads with the club
        sess.hands[3].remove(lead_card)
        sess.trick_manager.current_trick.append((3, lead_card))
        sess.turn = 2  # Clockwise: 3 -> 2

        # Remove all clubs AND hearts from player 2
        sess.hands[2] = [
            c for c in sess.hands[2]
            if c.suit not in [Suit.CLUBS.value, Suit.HEARTS.value]
        ]

        # Player 2 should still be able to reveal trump
        ok, msg = await sess.reveal_trump(2)

        assert ok is True
        assert sess.trump_hidden is False
        # Player can now play any card since they have no trump

    async def test_reveal_trump_multiple_players_scenario(self):
        """Test trump reveal in a multi-player trick scenario."""
        sess = await self.setup_game_in_play()

        # Ensure player 3 has a club to lead with
        lead_card = None
        for card in sess.hands[3]:
            if card.suit == Suit.CLUBS.value:
                lead_card = card
                break

        # If player 3 doesn't have a club, add one
        if lead_card is None:
            lead_card = Card(suit=Suit.CLUBS.value, rank="10", uid="10♣#1")
            sess.hands[3].append(lead_card)

        # Player 3 leads with the club
        sess.hands[3].remove(lead_card)
        sess.trick_manager.current_trick.append((3, lead_card))
        sess.turn = 2  # Clockwise: 3 -> 2

        # Player 2 follows suit (has clubs)
        follow_card = None
        for card in sess.hands[2]:
            if card.suit == Suit.CLUBS.value:
                follow_card = card
                break

        # Ensure player 2 has a club to follow with
        if follow_card is None:
            follow_card = Card(suit=Suit.CLUBS.value, rank="J", uid="J♣#1")
            sess.hands[2].append(follow_card)

        sess.hands[2].remove(follow_card)
        sess.trick_manager.current_trick.append((2, follow_card))
        sess.turn = 1  # Clockwise: 2 -> 1

        # Player 1 cannot follow suit
        sess.hands[1] = [c for c in sess.hands[1] if c.suit != Suit.CLUBS.value]

        # Player 1 reveals trump
        ok, msg = await sess.reveal_trump(1)

        assert ok is True
        assert sess.trump_hidden is False

        # Trump is now visible to all players for rest of the game
