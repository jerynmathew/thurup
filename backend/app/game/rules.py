# backend/app/game/rules.py
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.constants import CardPoints, CardRank, GameConfig, GameMode, Suit

SUITS = [suit.value for suit in Suit]
RANKS_28 = [rank.value for rank in CardRank]

# Rank ordering for 28/56 card game:
# ALL cards use the same ranking: J (highest) > 9 > A > 10 > K > Q > 8 > 7 (lowest)
# Trump vs non-trump only affects WHICH cards compete (trump beats non-trump when revealed)
TRUMP_RANK_ORDER = ["7", "8", "Q", "K", "10", "A", "9", "J"]  # low to high
NON_TRUMP_RANK_ORDER = ["7", "8", "Q", "K", "10", "A", "9", "J"]  # low to high (same as trump)

# Build index mappings for quick lookup
TRUMP_RANK_INDEX = {r: i for i, r in enumerate(TRUMP_RANK_ORDER)}
NON_TRUMP_RANK_INDEX = {r: i for i, r in enumerate(NON_TRUMP_RANK_ORDER)}

# Backward compatibility for AI module (uses non-trump ranking for simple card sorting)
RANK_INDEX = NON_TRUMP_RANK_INDEX

# points per rank - use CardPoints helper
CARD_POINTS = {
    CardRank.JACK.value: CardPoints.JACK,
    CardRank.NINE.value: CardPoints.NINE,
    CardRank.ACE.value: CardPoints.ACE,
    CardRank.TEN.value: CardPoints.TEN,
    CardRank.KING.value: CardPoints.KING,
    CardRank.QUEEN.value: CardPoints.QUEEN,
    CardRank.EIGHT.value: CardPoints.EIGHT,
    CardRank.SEVEN.value: CardPoints.SEVEN,
}


@dataclass(frozen=True)
class Card:
    suit: str
    rank: str
    uid: str  # unique id across decks, e.g. "A♠#1"

    @property
    def id(self) -> str:
        return self.uid

    def points(self) -> int:
        return CARD_POINTS.get(self.rank, 0)

    def to_dict(self) -> dict:
        return {"suit": self.suit, "rank": self.rank, "id": self.uid}


def make_deck(
    mode: str = GameMode.MODE_28.value, two_decks_for_56: bool = True
) -> List[Card]:
    """
    Create deck for mode "28" (default) or "56".
    For 56-mode default we merge two 32-card decks (64 cards) and treat them as unique.
    """
    decks = 1
    if mode == GameMode.MODE_56.value and two_decks_for_56:
        decks = 2
    cards: List[Card] = []
    for d in range(decks):
        for s in SUITS:
            for r in RANKS_28:
                uid = f"{r}{s}#{d+1}"
                cards.append(Card(suit=s, rank=r, uid=uid))
    return cards


def shuffle_deck(deck: List[Card], rng: Optional[random.Random] = None) -> List[Card]:
    d = deck[:]
    if rng is None:
        random.shuffle(d)
    else:
        rng.shuffle(d)
    return d


def hand_size_for(mode: str, seats: int = GameConfig.MIN_SEATS) -> int:
    """
    Return number of cards per player's hand for this mode and seats.
    `seats` is optional and defaults to 4 for backward compatibility with tests.
    """
    # Example logic (adapt if your deck sizes differ):
    if mode == GameMode.MODE_28.value:
        # typical 28-card (8 per player for 4 players)
        # for 4 players -> 8; for 6 players -> 4 (or your rules)
        if seats == 4:
            return 8
        if seats == 6:
            # adapt to your intended 56-mode or custom rules; default to 8 to be safe
            return 8
        return 8
    elif mode == GameMode.MODE_56.value:
        # 56-card / 6-player variant; default to 9 for 6 players, else 8
        if seats == 6:
            return 9
        return 8
    else:
        # default fallback
        return 8


def deal(deck: List[Card], seats: int) -> Tuple[List[List[Card]], List[Card]]:
    """
    Round-robin deal: returns (hands, kitty).
    hands: list of seat->list[Card] length seats
    kitty: leftover cards (if deck not divisible by seats)
    """
    if seats <= 0:
        raise ValueError("seats must be > 0")
    hand_size = len(deck) // seats
    hands = [[] for _ in range(seats)]
    for i in range(hand_size * seats):
        hands[i % seats].append(deck[i])
    kitty = deck[hand_size * seats :]
    return hands, kitty


def get_rank_value(card: Card, is_trump: bool) -> int:
    """Get the rank value of a card (higher value = stronger card)."""
    if is_trump:
        return TRUMP_RANK_INDEX[card.rank]
    else:
        return NON_TRUMP_RANK_INDEX[card.rank]


def determine_trick_winner(trick: List[Tuple[int, Card]], trump: Optional[str]) -> int:
    """
    trick: list of tuples (seat, Card) in play order starting with leader.
    Return seat of winner.
    Algorithm:
      - If trump is known and any trump cards exist in trick, consider only trumps.
      - Else consider cards of lead suit.
      - Among candidates choose highest rank using 28/56 ranking.
      - If ranks equal (possible in merged decks), choose earliest played candidate.

    28/56 Ranking (ALL cards use same ranking):
      - J (highest) > 9 > A > 10 > K > Q > 8 > 7 (lowest)

    Trump vs Non-Trump:
      - When trump is revealed: trump cards beat all non-trump cards
      - When trump is hidden: only lead suit cards compete (trump has no special power)
    """
    if not trick:
        raise ValueError("empty trick")
    lead_suit = trick[0][1].suit
    candidates = []
    is_trump_trick = False

    # Check if there are trump cards in the trick
    if trump:
        trump_cards = [t for t in trick if t[1].suit == trump]
        if trump_cards:
            candidates = trump_cards
            is_trump_trick = True

    # If no trump cards, use lead suit cards
    if not candidates:
        candidates = [t for t in trick if t[1].suit == lead_suit]
        is_trump_trick = False

    # Find the highest ranked card among candidates
    winner = candidates[0]
    winner_rank_value = get_rank_value(winner[1], is_trump_trick)

    for entry in candidates[1:]:
        entry_rank_value = get_rank_value(entry[1], is_trump_trick)
        if entry_rank_value > winner_rank_value:
            winner = entry
            winner_rank_value = entry_rank_value

    return winner[0]


def trick_points(trick: List[Tuple[int, Card]]) -> int:
    return sum(c.points() for (_, c) in trick)
