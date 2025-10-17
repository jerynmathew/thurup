# backend/tests/test_session.py
import pytest
from app.game.session import GameSession
from app.models import BidCmd, ChooseTrumpCmd, PlayCardCmd, PlayerInfo


@pytest.mark.asyncio
async def test_start_and_basic_flow():
    sess = GameSession(mode="28", seats=4)
    # add 4 PlayerInfo players (Pydantic instances)
    for i in range(4):
        p = PlayerInfo(player_id=f"p{i}", name=f"bot{i}")
        seat = await sess.add_player(p)
        assert seat in range(4)

    await sess.start_round(dealer=0)
    # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
    assert sess.turn == 3

    # ensure hands dealt (8 cards each for 28-mode)
    assert all(len(h) == 8 for h in sess.hands)

    # place a valid bid (seat 3 is first to bid)
    ok, msg = await sess.place_bid(3, BidCmd(value=16))
    assert ok

    # other players pass in clockwise order: 2, 1, 0
    ok1, _ = await sess.place_bid(2, BidCmd(value=None))
    ok2, _ = await sess.place_bid(1, BidCmd(value=None))
    ok3, _ = await sess.place_bid(0, BidCmd(value=None))
    assert ok1 and ok2 and ok3

    # after all bids, should be in choose_trump state
    assert sess.state.value == "choose_trump"

    # bid winner (seat 3) chooses trump
    ok2, m2 = await sess.choose_trump(3, ChooseTrumpCmd(suit="♠"))
    assert ok2

    # play a legal card for the leader
    leader = sess.leader
    card = sess.hands[leader][0]
    ok3, m3 = await sess.play_card(leader, PlayCardCmd(card_id=card.uid))
    assert ok3
