# backend/tests/test_bidding.py
import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from app.game.enums import SessionState
from app.game.session import GameSession
from app.models import PlayerInfo, BidCmd


# helper awaited action that waits until it's seat's turn (with timeout), then calls sess.place_bid
async def act_when_turn(
    sess: GameSession, seat: int, bid_value: int, timeout_s: float = 2.0
):
    """
    Wait for sess.turn to equal `seat` and then place the bid.
    If sess.turn doesn't become seat within timeout_s, raise AssertionError.
    """
    deadline = datetime.now(timezone.utc) + timedelta(seconds=timeout_s)
    while datetime.now(timezone.utc) < deadline:
        # quick check under lock-free read (ok for tests)
        if (
            sess.turn == seat
            and sess.state == SessionState.BIDDING
            and sess.bids.get(seat) is None
        ):
            ok, msg = await sess.place_bid(seat, BidCmd(value=bid_value))
            return ok, msg
        await asyncio.sleep(0.01)
    raise AssertionError(
        f"Timeout waiting for seat {seat} to become turn (turn={sess.turn}, state={sess.state})"
    )


@pytest.mark.asyncio
async def test_sequential_bidding_order_and_transition():
    """
    Robust sequential bidding test:
      - starts a session, adds 4 players, starts round
      - drives bids by waiting for the current turn and then placing bids
      - asserts the game moves to CHOOSE_TRUMP when finished
    """
    sess = GameSession(mode="28", seats=4)
    # add players
    for i in range(4):
        p = PlayerInfo(player_id=f"p{i}", name=f"bot{i}")
        await sess.add_player(p)

    await sess.start_round(dealer=0)
    assert sess.state == SessionState.BIDDING
    # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
    assert sess.turn == 3  # Leader starts

    # sequence of bids we want to apply in seat order (will be applied when seat becomes turn)
    # Clockwise bidding order: 3 -> 2 -> 1 -> 0
    actions = {3: -1, 2: 18, 1: -1, 0: 20}  # seat 3 passes, seat 2 bids 18, seat 1 passes, seat 0 bids 20

    # Drive sequential bidding: for each seat in the natural order starting from leader,
    # wait for the seat to become turn then place its action.
    seats_to_act = list(range(sess.seats))
    for _ in seats_to_act:
        cur = sess.turn
        val = actions[cur]
        ok, msg = await act_when_turn(sess, cur, val, timeout_s=2.0)
        assert ok, f"seat {cur} action failed: {msg}"

    # After all seats acted we must be in CHOOSE_TRUMP
    assert (
        sess.state == SessionState.CHOOSE_TRUMP
    ), f"expected CHOOSE_TRUMP got {sess.state}"
    # bids recorded correctly (no None left)
    assert all(v is not None for v in sess.bids.values())
    for s, v in actions.items():
        assert sess.bids[s] == v


@pytest.mark.asyncio
async def test_all_pass_redeal_nonblocking():
    """
    All-pass redeal scenario driven safely:
      - start, then have each seat pass when it's their turn
      - assert that after all passed the session was redealt and bidding restarted
    """
    sess = GameSession(mode="28", seats=4)
    for i in range(4):
        p = PlayerInfo(player_id=f"p{i}", name=f"bot{i}")
        await sess.add_player(p)

    await sess.start_round(dealer=0)
    assert sess.state == SessionState.BIDDING
    # With dealer=0, leader=(0-1)%4=3 (clockwise direction)
    assert sess.turn == 3  # Leader starts

    # All seats pass in clockwise order: 3 -> 2 -> 1 -> 0
    for _ in range(sess.seats):
        cur = sess.turn
        ok, msg = await act_when_turn(sess, cur, -1, timeout_s=2.0)
        assert ok, f"pass by seat {cur} failed: {msg}"

    # After all passed the session should have restarted a new round and be in BIDDING
    assert (
        sess.state == SessionState.BIDDING
    ), f"expected BIDDING after redeal, got {sess.state}"
    # bids should have been reset to None for the new round
    assert all(
        v is None for v in sess.bids.values()
    ), "bids should be reset (None) after redeal"
    # hand sizes should match expected hand size for mode (basic sanity)
    from app.game.rules import hand_size_for

    expected_size = hand_size_for(sess.mode)
    assert all(
        len(h) == expected_size for h in sess.hands
    ), "wrong hand sizes after redeal"
