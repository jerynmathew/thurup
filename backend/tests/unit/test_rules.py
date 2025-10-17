# backend/tests/test_rules.py
from app.game.rules import Card, deal, determine_trick_winner, make_deck, shuffle_deck


def test_make_deck_len():
    d = make_deck("28", two_decks_for_56=False)
    assert len(d) == 32


def test_shuffle_and_deal():
    d = make_deck("28", two_decks_for_56=False)
    sd = shuffle_deck(d)
    hands, kitty = deal(sd, 4)
    assert len(hands) == 4
    assert all(len(h) == 8 for h in hands)
    assert len(kitty) == 0


def test_trick_winner_simple():
    # create simple trick: seats 0..3
    c0 = Card("♠", "10", "10♠#1")
    c1 = Card("♠", "J", "J♠#1")
    c2 = Card("♥", "A", "A♥#1")
    c3 = Card("♠", "A", "A♠#1")
    trick = [(0, c0), (1, c1), (2, c2), (3, c3)]
    # trump none: winner should be seat 1 (J♠) - Jack beats Ace in all card ranking
    w = determine_trick_winner(trick, None)
    assert w == 1
    # if trump is hearts, play has heart played by seat2 so winner seat2
    w2 = determine_trick_winner(trick, "♥")
    assert w2 == 2
