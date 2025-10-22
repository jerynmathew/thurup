# Thurup Product Requirements

## 1. Overview
**Thurup** is a real-time online version of the classic Indian card game “28” (and its 6-player variant “56”).  
It combines trick-taking, bidding, and trump-based gameplay.  
This document defines the **product rules** and **gameplay mechanics** used by the Thurup system.

---

## 2. Variants

### 2.1 28 Variant
| Attribute | Value |
|------------|--------|
| Players | 4 (2 teams of 2) |
| Cards | 32 (7,8,9,10,J,Q,K,A in each suit) |
| Cards per player | 8 |
| Minimum Bid | 14 |
| Total Points | 28 |
| Teams | Alternating seats (0 & 2 vs 1 & 3) |

**Card Values**
| Card | Points |
|------|---------|
| J | 3 |
| 9 | 2 |
| A | 1 |
| 10 | 1 |
| Others | 0 |

---

### 2.2 56 Variant
| Attribute | Value |
|------------|--------|
| Players | 6 (2 teams of 3) |
| Cards | 64 (two 28 decks combined) |
| Cards per player | 8 |
| Minimum Bid | 28 |
| Total Points | 56 |

**Rules and card values identical** to the 28 variant.

---

## 3. Game Phases

### 3.1 Lobby Phase
- Players join a created game session.
- Each seat is filled in order (0..N-1).
- Game auto-starts when table is full.

### 3.2 Bidding Phase
- Starts with player next to dealer.
- Players bid an integer higher than the current highest, or `PASS (-1)`.
- Turn proceeds sequentially by seat order.
- Bidding ends when:
  - All but one player have passed, or
  - All players pass → triggers **redeal**.

### 3.3 Trump Selection
- Highest bidder chooses a **trump suit** (`♠`, `♥`, `♦`, `♣`).
- Depending on “Hidden Trump Mode”, trump may not be visible to others initially.

### 3.4 Play Phase
- Players play cards in seat order.
- Must follow suit if possible.
- If unable to follow suit, may play any card (possibly trump).
- Trick winner determined by highest-ranked valid card.
- Winner leads the next trick.

### 3.5 Scoring
- When all cards are played:
  - Each team totals their trick points.
  - Bidder’s team must meet or exceed their bid.
- Outcome:
  - **Win:** Bidder team ≥ bid value.
  - **Loss:** Bidder team < bid value.
  - Opponent team gets 1 point if they break bidder’s target.

---

## 4. Hidden Trump Modes

| Mode | Description |
|------|--------------|
| `ON_FIRST_NONFOLLOW` | Trump revealed when first player fails to follow suit |
| `ON_FIRST_TRUMP_PLAY` | Revealed when first trump card played |
| `ON_BIDDER_NONFOLLOW` | Revealed when bidder cannot follow suit |
| `OPEN_IMMEDIATELY` | Trump visible from start of play |

Default: `ON_FIRST_NONFOLLOW`.

---

## 5. Special Rules
- Bids must be **integers**; `-1` represents PASS.
- Player cannot re-enter after passing.
- Sequential turn order enforced.
- All-pass results in automatic redeal.
- Game state transitions:
```
LOBBY → DEALING → BIDDING → CHOOSE_TRUMP → PLAY → SCORING → ROUND_END
```

---

## 6. Bot (AI) Requirements
**Easy Mode AI**
- Bids randomly between `(highest_bid + 1)` and safe upper limit.
- Occasionally passes (`-1`) with fixed probability.
- Trump suit chosen by majority cards in hand.
- Plays valid cards per rules (no deep strategy).

---

## 7. UI / UX Requirements
- Seat grid with:
  - Player name and bot indicator.
  - Highlighted border for current turn.
  - Current bid or “PASS”.
- Buttons for quick bids and “PASS”.
- Inline error banners instead of `alert()`.
- Simple toast notifications for actions.
- Shareable join link for existing games.

---

## 8. Non-functional Requirements
- Real-time via WebSocket.
- Backend state in-memory.
- Pydantic models for validation.
- REST for control actions; WS for live state.
- Responsive UI (desktop-first).
