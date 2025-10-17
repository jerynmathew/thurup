# backend/debug_session_state.py
import asyncio
import os
import sys
import time

# ensure backend package is importable
ROOT = os.path.join(os.path.dirname(__file__), "")
sys.path.insert(0, ROOT)

from app.api.v1 import SESSIONS

def dump_game(game_id):
    sess = SESSIONS.get(game_id)
    if not sess:
        print("no such session", game_id)
        return
    print("=== session dump ===")
    print("state:", sess.state)
    print("leader:", sess.leader, "turn:", sess.turn)
    print("players keys:", sorted(sess.players.keys()))
    for k, v in sess.players.items():
        print(" - seat", k, "player:", getattr(v, "name", None), "is_bot:", getattr(v, "is_bot", False))
    print("bids:", getattr(sess, "bids", None))
    print("_bids_received:", getattr(sess, "_bids_received", None))
    print("current_highest:", getattr(sess, "current_highest", None))
    print("bid_winner:", getattr(sess, "bid_winner", None))
    print("hand_sizes:", [len(h) for h in getattr(sess, "hands", [])] )
    print("====================")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("game_id", help="game id to inspect")
    args = p.parse_args()
    dump_game(args.game_id)
