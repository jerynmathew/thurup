"""
Reproduce the exact gameplay bug reported by user.

Scenario:
- User's team (seats 0 and 2) played Jack of Spades and 9 of Spades
- Game incorrectly awarded the trick to the opposing team (seats 1 and 3)
- This should test the full game flow, not just the trick winner logic
"""

import pytest
from app.game.session import GameSession
from app.game.rules import Card


@pytest.mark.asyncio
async def test_user_reported_gameplay_bug():
    """
    Reproduce the exact bug: Jack and 9 of spades (same team) should win,
    but game awarded to opposing team.

    We'll simulate a full game up to the point where this trick is played.
    """
    # Create a 4-player game
    session = GameSession(seats=4, mode="28")

    # Add players
    from app.models import PlayerInfo
    await session.add_player(PlayerInfo(player_id="p0", name="User", is_bot=False))  # Seat 0
    await session.add_player(PlayerInfo(player_id="p1", name="Bot 1", is_bot=True))  # Seat 1
    await session.add_player(PlayerInfo(player_id="p2", name="Bot 2", is_bot=True))  # Seat 2 (User's teammate)
    await session.add_player(PlayerInfo(player_id="p3", name="Bot 3", is_bot=True))  # Seat 3

    # Start the round and manually set up the game state
    await session.start_round()

    # Force specific cards in hands for testing
    # User (seat 0) has Jack of Spades
    # Bot 2 (seat 2) has 9 of Spades
    jack_spades = Card(suit="♠", rank="J", uid="J♠#1")
    nine_spades = Card(suit="♠", rank="9", uid="9♠#1")
    king_hearts = Card(suit="♥", rank="K", uid="K♥#1")
    queen_diamonds = Card(suit="♦", rank="Q", uid="Q♦#1")

    # Set hands (clearing existing random hands)
    session.hands[0] = [jack_spades, Card(suit="♥", rank="7", uid="7♥#1")]
    session.hands[1] = [king_hearts, Card(suit="♦", rank="8", uid="8♦#1")]
    session.hands[2] = [nine_spades, Card(suit="♣", rank="10", uid="10♣#1")]
    session.hands[3] = [Card(suit="♠", rank="8", uid="8♠#1"), queen_diamonds]  # Seat 3 has 8♠ (trump)

    # Skip bidding phase - manually set bid winner and trump
    from app.game.enums import SessionState
    session.state = SessionState.PLAY
    session.bidding_manager.bid_winner = 0
    session.trump = "♠"  # Spades is trump
    session.trump_hidden = True  # FIRST ROUND - Trump is hidden!
    session.leader = 0  # Set leader to seat 0
    session.turn = 0  # User starts

    print("\n=== Game State ===")
    print(f"Trump: {session.trump}")
    print(f"Current turn: {session.turn}")
    print(f"Hands:")
    for seat, hand in enumerate(session.hands):
        print(f"  Seat {seat}: {[f'{c.rank}{c.suit}' for c in hand]}")

    # Play the trick
    print("\n=== Playing Trick ===")

    # Turn order is CLOCKWISE: 0 → 3 → 2 → 1
    # User (seat 0) leads with Jack of Spades
    from app.models import PlayCardCmd
    result = await session.play_card(seat=0, cmd=PlayCardCmd(card_id="J♠#1"))
    print(f"Seat 0 (User) plays J♠: {result}")
    print(f"Current trick: {[(s, f'{c.rank}{c.suit}') for s, c in session.trick_manager.current_trick]}")

    # Bot 3 (seat 3) plays 8 of Spades (clockwise next)
    result = await session.play_card(seat=3, cmd=PlayCardCmd(card_id="8♠#1"))
    print(f"Seat 3 (Bot 3) plays 8♠: {result}")
    print(f"Current trick: {[(s, f'{c.rank}{c.suit}') for s, c in session.trick_manager.current_trick]}")

    # Bot 2 (seat 2) plays 9 of Spades (User's teammate)
    result = await session.play_card(seat=2, cmd=PlayCardCmd(card_id="9♠#1"))
    print(f"Seat 2 (Bot 2) plays 9♠: {result}")
    print(f"Current trick: {[(s, f'{c.rank}{c.suit}') for s, c in session.trick_manager.current_trick]}")

    # Bot 1 (seat 1) plays King of Hearts (last to play)
    ok, msg = await session.play_card(seat=1, cmd=PlayCardCmd(card_id="K♥#1"))
    print(f"Seat 1 (Bot 1) plays K♥: ({ok}, {msg})")

    # Trick completes automatically in the original code
    print("\n=== Trick Result ===")
    assert ok, f"Failed to play card: {msg}"
    assert "Trick complete" in msg, f"Expected trick to complete, got: {msg}"

    # Trick is already complete - winner info is in last_trick
    winner, trick_cards = session.trick_manager.last_trick
    print(f"Winner: Seat {winner}")

    # Verify the winner
    # Jack of Spades (seat 0) should beat 9 of Spades (seat 2)
    # Both are on team 0 (even seats)
    assert winner == 0, f"Jack of Spades (seat 0) should win, but seat {winner} won!"

    # Check points were awarded to correct team
    # Team 0 = seats 0, 2
    # Team 1 = seats 1, 3
    team_0_points = session.points_by_seat.get(0, 0) + session.points_by_seat.get(2, 0)
    team_1_points = session.points_by_seat.get(1, 0) + session.points_by_seat.get(3, 0)

    print(f"\nTeam 0 (seats 0, 2) points: {team_0_points}")
    print(f"Team 1 (seats 1, 3) points: {team_1_points}")

    # Jack = 3 points, 9 = 2 points, K = 0, 8 = 0
    # Total = 5 points, should go to team 0
    expected_points = 3 + 2  # J + 9
    assert team_0_points == expected_points, \
        f"Team 0 should have {expected_points} points, but has {team_0_points}"

    print(f"\n✅ Test passed! Jack of Spades correctly won the trick.")


@pytest.mark.asyncio
async def test_trump_ranking_all_combinations():
    """
    Test all possible trump card combinations to ensure ranking is correct.
    Trump ranking should be: J > 9 > A > 10 > K > Q > 8 > 7
    """
    session = GameSession(seats=4, mode="28")

    # Add players
    from app.models import PlayerInfo
    for i in range(4):
        await session.add_player(PlayerInfo(player_id=f"p{i}", name=f"Player {i}", is_bot=True))

    await session.start_round()

    # Set up game state
    from app.game.enums import SessionState
    session.state = SessionState.PLAY
    session.trump = "♠"
    session.trump_hidden = False
    session.leader = 0
    session.turn = 0

    # Test cases: (card1, card2, expected_winner_card)
    trump_battles = [
        ("J", "9", "J"),   # Jack beats 9
        ("J", "A", "J"),   # Jack beats Ace
        ("J", "10", "J"),  # Jack beats 10
        ("9", "A", "9"),   # 9 beats Ace
        ("9", "10", "9"),  # 9 beats 10
        ("A", "10", "A"),  # Ace beats 10
        ("A", "K", "A"),   # Ace beats King
        ("10", "K", "10"), # 10 beats King
        ("K", "Q", "K"),   # King beats Queen
        ("Q", "8", "Q"),   # Queen beats 8
        ("8", "7", "8"),   # 8 beats 7
    ]

    print("\n=== Testing Trump Card Rankings ===")
    for rank1, rank2, expected_winner_rank in trump_battles:
        # Reset game state for each test
        session.trick_manager.current_trick = []
        session.state = SessionState.PLAY  # Reset to PLAY state after previous trick completed
        session.turn = 0

        # Create cards with unique UIDs for each iteration
        import random
        uid_suffix = random.randint(1000, 9999)
        card1 = Card(suit="♠", rank=rank1, uid=f"{rank1}♠#{uid_suffix}a")
        card2 = Card(suit="♠", rank=rank2, uid=f"{rank2}♠#{uid_suffix}b")
        card3 = Card(suit="♥", rank="7", uid=f"7♥#{uid_suffix}c")  # Non-trump throwaway
        card4 = Card(suit="♦", rank="7", uid=f"7♦#{uid_suffix}d")  # Non-trump throwaway

        # Set hands
        session.hands[0] = [card1]
        session.hands[1] = [card2]
        session.hands[2] = [card3]
        session.hands[3] = [card4]

        # Play the trick in clockwise order: 0 → 3 → 2 → 1
        from app.models import PlayCardCmd
        await session.play_card(seat=0, cmd=PlayCardCmd(card_id=card1.uid))
        await session.play_card(seat=3, cmd=PlayCardCmd(card_id=card4.uid))
        await session.play_card(seat=2, cmd=PlayCardCmd(card_id=card3.uid))
        ok, msg = await session.play_card(seat=1, cmd=PlayCardCmd(card_id=card2.uid))

        # Trick completes automatically
        assert ok and "Trick complete" in msg, f"Expected trick completion, got: ({ok}, {msg})"

        # Get winner from last_trick (trick already completed)
        winner, _ = session.trick_manager.last_trick
        winner_card = card1 if winner == 0 else card2

        print(f"{rank1}♠ vs {rank2}♠ → Winner: {winner_card.rank}♠ (expected: {expected_winner_rank}♠)")

        assert winner_card.rank == expected_winner_rank, \
            f"{rank1}♠ vs {rank2}♠: Expected {expected_winner_rank}♠ to win, but {winner_card.rank}♠ won!"

    print("\n✅ All trump ranking tests passed!")


@pytest.mark.asyncio
async def test_lead_suit_ranking_all_same():
    """
    Test that lead suit cards (when no trump played) use same ranking as trump: J > 9 > A > 10 > K > Q > 8 > 7
    This is critical: ALL cards use the same ranking regardless of suit.
    """
    session = GameSession(seats=4, mode="28")

    # Add players
    from app.models import PlayerInfo
    for i in range(4):
        await session.add_player(PlayerInfo(player_id=f"p{i}", name=f"Player {i}", is_bot=True))

    await session.start_round()

    # Set up game state with spades as trump (but hearts will be lead)
    from app.game.enums import SessionState
    session.state = SessionState.PLAY
    session.trump = "♠"
    session.trump_hidden = False
    session.leader = 0
    session.turn = 0

    # Test lead suit hearts ranking (same as trump ranking!)
    lead_suit_battles = [
        ("J", "9", "J"),   # Jack beats 9
        ("J", "A", "J"),   # Jack beats Ace
        ("9", "A", "9"),   # 9 beats Ace
        ("A", "10", "A"),  # Ace beats 10
        ("10", "K", "10"), # 10 beats King
        ("K", "Q", "K"),   # King beats Queen
        ("Q", "8", "Q"),   # Queen beats 8
        ("8", "7", "8"),   # 8 beats 7
    ]

    print("\n=== Testing Lead Suit Card Rankings (Hearts lead, Trump is Spades) ===")
    for rank1, rank2, expected_winner_rank in lead_suit_battles:
        # Reset game state
        session.trick_manager.current_trick = []
        session.state = SessionState.PLAY  # Reset to PLAY state after previous trick completed
        session.turn = 0

        # Create lead suit cards (hearts) with unique UIDs
        import random
        uid_suffix = random.randint(1000, 9999)
        card1 = Card(suit="♥", rank=rank1, uid=f"{rank1}♥#{uid_suffix}a")
        card2 = Card(suit="♥", rank=rank2, uid=f"{rank2}♥#{uid_suffix}b")
        card3 = Card(suit="♦", rank="7", uid=f"7♦#{uid_suffix}c")
        card4 = Card(suit="♣", rank="7", uid=f"7♣#{uid_suffix}d")

        # Set hands
        session.hands[0] = [card1]
        session.hands[1] = [card2]
        session.hands[2] = [card3]
        session.hands[3] = [card4]

        # Play the trick in clockwise order: 0 → 3 → 2 → 1
        from app.models import PlayCardCmd
        await session.play_card(seat=0, cmd=PlayCardCmd(card_id=card1.uid))
        await session.play_card(seat=3, cmd=PlayCardCmd(card_id=card4.uid))
        await session.play_card(seat=2, cmd=PlayCardCmd(card_id=card3.uid))
        ok, msg = await session.play_card(seat=1, cmd=PlayCardCmd(card_id=card2.uid))

        # Trick completes automatically
        assert ok and "Trick complete" in msg, f"Expected trick completion, got: ({ok}, {msg})"

        # Get winner from last_trick (trick already completed)
        winner, _ = session.trick_manager.last_trick
        winner_card = card1 if winner == 0 else card2

        print(f"{rank1}♥ vs {rank2}♥ → Winner: {winner_card.rank}♥ (expected: {expected_winner_rank}♥)")

        assert winner_card.rank == expected_winner_rank, \
            f"{rank1}♥ vs {rank2}♥: Expected {expected_winner_rank}♥ to win, but {winner_card.rank}♥ won!"

    print("\n✅ All lead suit ranking tests passed!")
