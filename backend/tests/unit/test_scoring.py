# backend/tests/test_scoring.py
import pytest

from app.game.session import GameSession
from app.models import PlayerInfo


@pytest.mark.asyncio
async def test_scoring_bid_success_and_failure():
    # success case
    sess = GameSession(mode="28", seats=4)
    for i in range(4):
        await sess.add_player(PlayerInfo(player_id=f"p{i}", name=f"p{i}"))
    await sess.start_round(dealer=0)
    # give captured points artificially: seat0 wins two tricks totaling 18 points
    sess.points_by_seat = {0: 10, 1: 0, 2: 9, 3: 0}
    sess.bid_winner = 0
    sess.bid_value = 16
    scores = sess.compute_scores()
    assert scores["bid_outcome"]["success"] is True

    # failure case
    sess2 = GameSession(mode="28", seats=4)
    for i in range(4):
        await sess2.add_player(PlayerInfo(player_id=f"q{i}", name=f"q{i}"))
    await sess2.start_round(dealer=0)
    sess2.points_by_seat = {0: 5, 1: 0, 2: 6, 3: 0}  # team0 has 11
    sess2.bid_winner = 0
    sess2.bid_value = 14
    scores2 = sess2.compute_scores()
    assert scores2["bid_outcome"]["success"] is False
