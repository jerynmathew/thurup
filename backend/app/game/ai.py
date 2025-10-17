# backend/app/game/ai.py
from __future__ import annotations
import random
from typing import List, Optional

from app.constants import AIConfig, BidValue, GameConfig
from app.game.rules import CARD_POINTS, RANK_INDEX, Card


def choose_trump_suit(hand: List[Card]) -> str:
    """Pick the suit with the most cards in hand. Tie-break randomly."""
    counts = {}
    for c in hand:
        counts[c.suit] = counts.get(c.suit, 0) + 1
    # choose suit with max count; tie-breaker random
    best = max(counts.items(), key=lambda kv: (kv[1], random.random()))[0]
    return best


def select_card_to_play(
    hand: List[Card], lead_suit: Optional[str], trump: Optional[str]
) -> Card:
    """
    Play heuristic:
      - If lead_suit is present in hand: play lowest card of that suit.
      - Else if no lead_suit:
         - if have trump, play lowest trump to try win cheaply
         - otherwise play lowest overall (throwaway)
    """
    # sort helper: by rank index (low->high)
    hand_sorted = sorted(hand, key=lambda c: RANK_INDEX[c.rank])
    if lead_suit:
        follow = [c for c in hand_sorted if c.suit == lead_suit]
        if follow:
            return follow[0]
        # if can't follow and have trump, play lowest trump
        if trump:
            tr = [c for c in hand_sorted if c.suit == trump]
            if tr:
                return tr[0]
        # otherwise dump lowest
        return hand_sorted[0]
    else:
        # lead the trick: choose highest card to try to win or safe
        # but simple strategy: lead highest-point card (J/9/A/10), else highest rank
        def score_for_lead(card: Card):
            return (CARD_POINTS.get(card.rank, 0), RANK_INDEX[card.rank])

        best = max(hand_sorted, key=score_for_lead)
        return best


# A minimal estimate function kept for future use; easy mode ignores deep heuristics.
def estimate_hand_points(hand: List) -> int:
    """Lightweight heuristic (not used by easy mode bidding much)."""
    # hand is a list of Card-like objects with .rank; we give higher ranks small weights.
    rank_score = {
        "A": 4,
        "K": 3,
        "Q": 2,
        "J": 1,
        "10": 1,
        "9": 0,
        "8": 0,
        "7": 0,
    }
    s = 0
    for c in hand:
        r = getattr(c, "rank", None) or c.get("rank") if isinstance(c, dict) else None
        s += rank_score.get(r, 0)
    return s


def choose_bid_value(
    hand,
    min_bid: int = GameConfig.MIN_BID_DEFAULT,
    max_total: int = GameConfig.MAX_BID_28,
    current_highest: Optional[int] = None,
    mode: str = "easy",
) -> int:
    if current_highest is None:
        lower = min_bid
    else:
        lower = max(min_bid, current_highest + 1)
    if lower > max_total:
        return BidValue.PASS  # cannot outbid -> pass
    # easy: randomly either pass or bid in [lower, max_total]
    if random.random() < AIConfig.PASS_PROBABILITY:
        return BidValue.PASS
    return random.randint(lower, max_total)
