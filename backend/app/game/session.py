# backend/app/game/session.py
from __future__ import annotations
import asyncio
import random
import uuid
from typing import Dict, List, Optional, Tuple

from app.constants import BidValue, ErrorMessage, GameConfig, GameMode, Suit
from app.game.enums import HiddenTrumpMode, SessionState
from app.game.rules import (
    Card,
    deal,
    make_deck,
    shuffle_deck,
    trick_points,
)
from app.game.hidden_trump import HiddenTrumpManager
from app.game.trick_manager import TrickManager
from app.logging_config import get_logger
from app.models import BidCmd, ChooseTrumpCmd, GameStateDTO, PlayCardCmd, PlayerInfo

logger = get_logger(__name__)


class GameSession:
    def __init__(
        self,
        game_id: Optional[str] = None,
        short_code: Optional[str] = None,
        mode: str = GameMode.MODE_28.value,
        seats: int = 4,
        hidden_trump_mode: HiddenTrumpMode = HiddenTrumpMode.ON_FIRST_NONFOLLOW,
        min_bid: int = GameConfig.MIN_BID_DEFAULT,
        two_decks_for_56: bool = True,
    ):
        self.id = game_id or str(uuid.uuid4())
        self.short_code = short_code
        self.mode = mode
        self.seats = seats
        self.hidden_trump_mode = hidden_trump_mode
        self.min_bid = min_bid
        self.two_decks_for_56 = two_decks_for_56

        self.deck: List[Card] = []
        self.kitty: List[Card] = []
        self.hands: List[List[Card]] = [[] for _ in range(seats)]
        self.players: Dict[int, PlayerInfo] = {}  # seat -> PlayerInfo
        self.state: SessionState = SessionState.LOBBY

        # bidding
        self.bids: Dict[int, Optional[int]] = {i: None for i in range(seats)}
        self.current_highest: Optional[int] = None
        self.bid_winner: Optional[int] = None
        self.bid_value: Optional[int] = None

        # trump
        self.trump: Optional[str] = None
        self.trump_hidden: bool = True
        self.trump_owner: Optional[int] = None

        # play/tricks
        self.current_dealer: int = 0  # tracks dealer position, rotates clockwise
        self.leader: int = 0  # seat index of player to dealer's left (first to bid/play)
        self.turn: int = 0
        self.trick_manager = TrickManager()

        # per-seat points captured (for convenience)
        self.points_by_seat: Dict[int, int] = {i: 0 for i in range(seats)}

        # round history - track completed rounds for replay/analysis
        self.rounds_history: List[Dict[str, any]] = []

        # track which seats have submitted bids in the current bidding round
        self._bids_received: set[int] = set()

        # locks
        self._lock = asyncio.Lock()

    async def add_player(self, player: PlayerInfo) -> int:
        """
        Assign seat automatically to the first free seat.
        Accepts ONLY a PlayerInfo instance (Pydantic model).
        Returns the assigned seat integer.
        """
        async with self._lock:
            if not isinstance(player, PlayerInfo):
                raise TypeError("player must be a PlayerInfo instance")

            for s in range(self.seats):
                if s not in self.players:
                    player.seat = s
                    self.players[s] = player
                    return s
            raise RuntimeError("No free seats")

    async def remove_player(self, seat: int):
        async with self._lock:
            self.players.pop(seat, None)

    async def start_round(self, dealer: int = 0):
        async with self._lock:
            # Save previous round to history before resetting (if there was one)
            if self.trick_manager.captured_tricks:  # If there was a previous round
                round_data = {
                    "round_number": len(self.rounds_history) + 1,
                    "dealer": self.current_dealer,  # Previous dealer
                    "bid_winner": self.bid_winner,
                    "bid_value": self.bid_value,
                    "trump": self.trump,
                    "captured_tricks": self.trick_manager.get_captured_tricks_for_serialization(),
                    "points_by_seat": dict(self.points_by_seat),
                    "team_scores": self.compute_scores(),
                }
                self.rounds_history.append(round_data)
                logger.info(
                    "round_saved_to_history",
                    game_id=self.id,
                    round_number=round_data["round_number"],
                    bid_winner=self.bid_winner,
                    team_scores=round_data["team_scores"],
                )

                # Rotate dealer clockwise for next round
                # In clockwise games, next dealer is to the left (add 1)
                self.current_dealer = (self.current_dealer + 1) % self.seats
                logger.info(
                    "dealer_rotated",
                    game_id=self.id,
                    new_dealer=self.current_dealer,
                )
            else:
                # First round: use the dealer parameter
                self.current_dealer = dealer

            self.state = SessionState.DEALING
            # build deck
            self.deck = shuffle_deck(
                make_deck(self.mode, self.two_decks_for_56), random.Random()
            )
            self.hands, self.kitty = deal(self.deck, self.seats)

            # Leader is the player to dealer's LEFT (next player clockwise)
            # In clockwise play, that's dealer - 1
            self.leader = (self.current_dealer - 1) % self.seats
            self.turn = self.leader

            logger.info(
                "round_started",
                game_id=self.id,
                dealer=self.current_dealer,
                leader=self.leader,
            )

            self.state = SessionState.BIDDING
            # reset bidding/tricks
            # track bids as a dict mapping seat -> Optional[int]
            self.bids = {i: None for i in range(self.seats)}
            # track which seats have actually submitted (pass or bid)
            self._bids_received = set()
            self.current_highest = None
            self.bid_winner = None
            self.bid_value = None
            self.trump = None
            self.trump_hidden = True
            self.trump_owner = None
            self.trick_manager.reset()
            self.points_by_seat = {i: 0 for i in range(self.seats)}
            return True

    def get_hand_for(self, seat: int) -> List[Dict]:
        return [c.to_dict() for c in self.hands[seat]]

    def get_public_state(self) -> GameStateDTO:
        # Compose a DTO with public info; individual hand info is not included here
        players_list = [
            p for _, p in sorted(self.players.items(), key=lambda kv: kv[0])
        ]

        # Get trick state from TrickManager
        current_trick_dict = self.trick_manager.get_current_trick_dict()
        lead_suit = self.trick_manager.get_lead_suit()
        last_trick_dict = self.trick_manager.get_last_trick_dict()

        dto = GameStateDTO(
            game_id=self.id,
            short_code=self.short_code,
            mode=self.mode,
            seats=self.seats,
            state=self.state.value,
            players=players_list,
            dealer=self.current_dealer,
            leader=self.leader,
            turn=self.turn,
            trump=None if self.trump_hidden else self.trump,
            kitty=[c.to_dict() for c in self.kitty],
            hand_sizes={s: len(self.hands[s]) for s in range(self.seats)},
            bids=self.bids,
            current_highest=self.current_highest,
            bid_winner=self.bid_winner,
            bid_value=self.bid_value,
            points_by_seat=self.points_by_seat,
            current_trick=current_trick_dict,
            lead_suit=lead_suit,
            last_trick=last_trick_dict,
            rounds_history=self.rounds_history,
        )
        return dto

    async def place_bid(self, seat: int, bid_cmd: BidCmd) -> Tuple[bool, str]:
        """
        Sequential bidding (safe):
        - Only current seat (self.turn) may bid.
        - Pass is represented internally as -1.
        - Accept either None or -1 from callers as pass (backwards compatible).
        - None in self.bids means "waiting to bid".
        - After every seat acts, advance self.turn to next seat.
        - When no None remains, transition to CHOOSE_TRUMP (or redeal if all -1).
        IMPORTANT: If a redeal is required, call start_round outside the lock to avoid deadlock.
        """
        need_redeal = False
        async with self._lock:
            if self.state != SessionState.BIDDING:
                return False, "Not in bidding phase"
            if seat not in self.players:
                return False, "Unknown seat"
            if seat != self.turn:
                return False, "Not your turn to bid"

            val = bid_cmd.value

            # Defensive: ensure seat hasn't acted yet
            if self.bids.get(seat) is not None:
                return False, "Seat already acted"

            # Treat both None and -1 as a pass from external callers
            if val is None or val == BidValue.PASS:
                # mark passed with internal sentinel
                self.bids[seat] = BidValue.PASS
                self._bids_received.add(seat)
            else:
                # validate numeric bid
                if not isinstance(val, int):
                    return False, "Bid must be integer (use -1 or None for pass)"
                if val < self.min_bid:
                    return False, f"Bid must be >= {self.min_bid}"
                max_total = (
                    GameConfig.MAX_BID_28
                    if self.mode == GameMode.MODE_28.value
                    else GameConfig.MAX_BID_56
                )
                if val > max_total:
                    return False, f"Bid cannot exceed {max_total}"
                if self.current_highest is not None and val <= self.current_highest:
                    return False, "Bid must be higher than current highest"
                self.bids[seat] = val
                self._bids_received.add(seat)
                if self.current_highest is None or val > self.current_highest:
                    self.current_highest = val
                    self.bid_winner = seat
                    self.bid_value = val

            # debug log
            logger.debug(
                "bid_placed",
                game_id=self.id,
                seat=seat,
                value=val,
                current_highest=self.current_highest,
                bids_received=sorted(self._bids_received),
                turn_before=self.turn,
            )

            # advance to next seat (clockwise)
            self.turn = (self.turn - 1) % self.seats

            # Check if bidding round complete (no None left)
            if all(v is not None for v in self.bids.values()):
                # if all passed, schedule redeal (but do not await start_round while holding lock)
                if all(v == BidValue.PASS for v in self.bids.values()):
                    need_redeal = True
                    result = (True, "All passed: will redeal")
                else:
                    self.state = SessionState.CHOOSE_TRUMP
                    result = (True, "Bid accepted; bidding complete")
            else:
                result = (True, "Bid accepted")

        # outside lock
        if need_redeal:
            try:
                await self.start_round()
                return True, "All passed: redealt"
            except Exception as e:
                return False, f"Redeal failed: {e}"

        return result

    async def choose_trump(self, seat: int, cmd: ChooseTrumpCmd) -> Tuple[bool, str]:
        async with self._lock:
            if self.state != SessionState.CHOOSE_TRUMP:
                return False, "Not waiting for trump"
            if seat != self.bid_winner:
                return False, "Only bid winner can choose trump"
            s = cmd.suit
            valid_suits = [suit.value for suit in Suit]
            if s not in valid_suits:
                return False, ErrorMessage.INVALID_SUIT
            self.trump = s
            self.trump_hidden = True
            self.trump_owner = seat
            self.state = SessionState.PLAY
            # play begins with leader (already set)
            self.turn = self.leader
            return True, "Trump chosen"

    async def reveal_trump(self, seat: int) -> Tuple[bool, str]:
        """
        Manually reveal hidden trump when player can't follow suit.

        Validation rules:
        - Must be in play phase
        - Must be the player's turn
        - Trump must be hidden
        - Must be during an active trick (not leading)
        - Player must not have cards matching the lead suit
        """
        async with self._lock:
            if self.state != SessionState.PLAY:
                return False, "Not in play phase"
            if seat not in self.players:
                return False, "Unknown seat"

            # Use HiddenTrumpManager for validation
            is_valid, error_msg = HiddenTrumpManager.validate_manual_reveal(
                trump_hidden=self.trump_hidden,
                player_seat=seat,
                current_turn=self.turn,
                current_trick=self.trick_manager.current_trick,
                player_hand=self.hands[seat],
            )

            if not is_valid:
                return False, error_msg

            # Reveal trump
            self.trump_hidden = False
            logger.info(
                "trump_revealed_manually",
                game_id=self.id,
                seat=seat,
                trump=self.trump,
            )
            return True, f"Trump revealed: {self.trump}"

    def _player_has_suit(self, seat: int, suit: str) -> bool:
        return any(c.suit == suit for c in self.hands[seat])

    def is_bot_seat(self, seat: int) -> bool:
        p = self.players.get(seat)
        return bool(p and getattr(p, "is_bot", False))

    def force_bot_play_choice(self, seat: int, ai_module):
        """
        Synchronous helper used by the API's async bot-runner:
        Returns commands as dicts: {"type": "bid"/"choose_trump"/"play_card", "payload": ...}
        """
        # For bidding phase
        if self.state == SessionState.BIDDING:
            # Only act if it's this seat's turn and it's still waiting (None)
            if seat != self.turn:
                return None
            if self.bids.get(seat) is not None:
                # already acted
                return None
            hand = self.hands[seat]
            # AI must return integer bid or -1 for pass
            bid_value = ai_module.choose_bid_value(
                hand,
                min_bid=self.min_bid,
                max_total=(
                    GameConfig.MAX_BID_28
                    if self.mode == GameMode.MODE_28.value
                    else GameConfig.MAX_BID_56
                ),
                current_highest=self.current_highest,
                mode="easy",
            )
            return {"type": "place_bid", "payload": {"seat": seat, "value": bid_value}}

        if self.state == SessionState.CHOOSE_TRUMP:
            if self.bid_winner != seat:
                return None
            hand = self.hands[seat]
            suit = ai_module.choose_trump_suit(hand)
            return {"type": "choose_trump", "payload": {"seat": seat, "suit": suit}}
        if self.state == SessionState.PLAY:
            # if it's not this seat's turn, nothing to do
            if seat != self.turn:
                return None
            hand = self.hands[seat]
            lead_suit = self.trick_manager.get_lead_suit()
            suit_for_trump = None if self.trump_hidden else self.trump
            card = ai_module.select_card_to_play(hand, lead_suit, suit_for_trump)
            return {"type": "play_card", "payload": {"seat": seat, "card_id": card.uid}}
        return None

    async def play_card(self, seat: int, cmd: PlayCardCmd) -> Tuple[bool, str]:
        """
        Validate and apply a play. If trick completes, resolve and award points.
        """
        async with self._lock:
            if self.state != SessionState.PLAY:
                return False, "Not in play phase"
            if seat != self.turn:
                return False, "Not your turn"
            # find card in player's hand
            card = None
            for c in self.hands[seat]:
                if c.uid == cmd.card_id:
                    card = c
                    break
            if card is None:
                return False, "Card not in hand"
            # must follow suit if lead exists and player has lead suit
            lead_suit = self.trick_manager.get_lead_suit()
            if lead_suit and self._player_has_suit(seat, lead_suit) and card.suit != lead_suit:
                # violation of follow-suit rule: reject
                return False, "Must follow suit if possible"

            # Save hand state before removing card (needed for reveal logic)
            hand_before_play = list(self.hands[seat])

            # remove card
            self.hands[seat].remove(card)
            self.trick_manager.add_card_to_current_trick(seat, card)

            # Check if trump should be revealed using HiddenTrumpManager
            # Get trick before this card was added (need to subtract 1 from length)
            trick_before_card = self.trick_manager.current_trick[:-1] if len(self.trick_manager.current_trick) > 0 else []
            should_reveal, reveal_reason = HiddenTrumpManager.should_reveal_trump(
                trump_hidden=self.trump_hidden,
                hidden_trump_mode=self.hidden_trump_mode,
                played_card=card,
                trump_suit=self.trump,
                trump_owner_seat=self.trump_owner,
                player_seat=seat,
                current_trick=trick_before_card,
                player_hand=hand_before_play,  # Hand before card was removed
            )

            if should_reveal:
                self.trump_hidden = False
                logger.info(
                    "trump_revealed_automatically",
                    game_id=self.id,
                    reason=reveal_reason,
                    trump=self.trump,
                )

            # advance turn (clockwise)
            self.turn = (self.turn - 1) % self.seats

            # if trick complete
            if self.trick_manager.is_trick_complete(self.seats):
                # Pass trump only if revealed; if hidden, pass None so no trump consideration
                winner = self.trick_manager.complete_trick(
                    self.trump if not self.trump_hidden else None,
                    self.points_by_seat
                )
                pts = self.points_by_seat[winner] - self.points_by_seat.get(winner, 0)  # Get points just awarded
                # set leader/turn to winner
                self.leader = winner
                self.turn = winner
                # check end of round: all hands empty
                if all(len(h) == 0 for h in self.hands):
                    self.state = SessionState.SCORING
                    # Save completed round to history
                    round_data = {
                        "round_number": len(self.rounds_history) + 1,
                        "dealer": self.leader,
                        "bid_winner": self.bid_winner,
                        "bid_value": self.bid_value,
                        "trump": self.trump,
                        "captured_tricks": self.trick_manager.get_captured_tricks_for_serialization(),
                        "points_by_seat": dict(self.points_by_seat),
                        "team_scores": self.compute_scores(),
                    }
                    self.rounds_history.append(round_data)
                    logger.info(
                        "round_completed_and_saved",
                        game_id=self.id,
                        round_number=round_data["round_number"],
                        bid_winner=self.bid_winner,
                        team_scores=round_data["team_scores"],
                    )
                    # scoring will be computed by caller
                return True, f"Trick complete. Winner: {winner} (+{pts} pts)"
            return True, "Card played"

    def compute_scores(self) -> Dict[str, any]:
        """
        Return structured scoring information: team points and bid outcome if any.
        teams: team0 = seats with even seat index, team1 = odd.
        """
        team_points = {0: 0, 1: 0}
        for seat, pts in self.points_by_seat.items():
            team_idx = 0 if seat % 2 == 0 else 1
            team_points[team_idx] += pts
        bid_outcome = None
        if self.bid_winner is not None and self.bid_value is not None:
            winning_team = 0 if self.bid_winner % 2 == 0 else 1
            success = team_points[winning_team] >= self.bid_value
            bid_outcome = {
                "bid_winner": self.bid_winner,
                "bid_value": self.bid_value,
                "winning_team": winning_team,
                "success": success,
            }
        return {"team_points": team_points, "bid_outcome": bid_outcome}
