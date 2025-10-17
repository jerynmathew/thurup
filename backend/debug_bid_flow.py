# debug_bid_flow.py  (run with: python backend/debug_bid_flow.py)
import asyncio
from app.game.session import GameSession
from app.models import PlayerInfo, BidCmd

async def debug():
    sess = GameSession(mode="28", seats=4)
    seats = []
    for i in range(4):
        p = PlayerInfo(player_id=f"p{i}", name=f"bot{i}")
        seat = await sess.add_player(p)
        seats.append(seat)
    print("players keys:", sorted(sess.players.keys()))
    print("initial state:", sess.state)

    await sess.start_round(dealer=0)
    print("after start_round state:", sess.state)
    print("hand sizes:", [len(h) for h in sess.hands])

    # seat 0 bids 16
    ok0, msg0 = await sess.place_bid(0, BidCmd(value=16))
    print("place_bid(0,16) ->", ok0, msg0)
    print("bids:", sess.bids, "current_highest:", sess.current_highest, "bid_winner:", sess.bid_winner)
    print("_bids_received:", getattr(sess, "_bids_received", None), "state:", sess.state)

    # seat 1 passes
    ok1, msg1 = await sess.place_bid(1, BidCmd(value=None))
    print("place_bid(1,None) ->", ok1, msg1)
    print("bids:", sess.bids, "_bids_received:", getattr(sess, "_bids_received", None), "state:", sess.state)

    # seat 2 passes
    ok2, msg2 = await sess.place_bid(2, BidCmd(value=None))
    print("place_bid(2,None) ->", ok2, msg2)
    print("bids:", sess.bids, "_bids_received:", getattr(sess, "_bids_received", None), "state:", sess.state)

    # seat 3 passes
    ok3, msg3 = await sess.place_bid(3, BidCmd(value=None))
    print("place_bid(3,None) ->", ok3, msg3)
    print("final bids:", sess.bids, "_bids_received:", getattr(sess, "_bids_received", None), "state:", sess.state)

asyncio.run(debug())
