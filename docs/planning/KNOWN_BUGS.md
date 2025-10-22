# Known Bugs & Issues

This document tracks all known bugs, their priority, and status.

**Last Updated:** 2025-10-15 (Both critical bugs fixed!)

---

## Priority: High (Critical Bugs)

### Bug #1: Multiplayer Hand Not Visible
**Status:** 🟢 Fixed
**Reported:** 2025-10-15
**Fixed:** 2025-10-15
**Component:** Frontend (useGame.ts)

**Description:**
In multiplayer games with 2+ actual players (not bots), only the first player could see their hand. Players 2, 3, and 4 could not see the "Your Hand" section at all.

**Root Cause:**
WebSocket was connecting BEFORE Player 2 joined the game through the UI. At connection time, `seat` and `playerId` were still `null`, so the hook sent a `request_state` message instead of an `identify` message. When Player 2 later joined the game (updating their seat and playerId), the WebSocket didn't re-send the identify message, leaving the backend with `seat=None` for that connection.

**The Fix:**
Added a reactive `useEffect` hook in `useGame.ts` that watches for changes to `seat` and `playerId`. When these values change while the WebSocket is already connected, it automatically re-sends the `identify` message to the backend.

**Fixed In:**
- `frontend/src/hooks/useGame.ts:101-112` - Added re-identification effect

**Code Changes:**
```typescript
// Re-identify when seat/playerId changes while WebSocket is connected
useEffect(() => {
  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
    if (seat !== null && playerId) {
      console.log('[useGame] Seat/PlayerId changed, re-identifying...');
      wsRef.current.send(JSON.stringify({
        type: 'identify',
        payload: { seat, player_id: playerId },
      }));
    }
  }
}, [seat, playerId]);
```

**Testing:**
Verified with 2+ players in separate browsers. All players now see their hands correctly.

**Impact:**
**CRITICAL** - Game was unplayable for players other than the creator. Now fully functional.

---

### Bug #2: Incorrect Dealer Rotation
**Status:** 🟢 Fixed
**Reported:** 2025-10-15
**Fixed:** 2025-10-15
**Component:** Backend (session.py), Frontend (GameBoard.tsx)

**Description:**
The dealer rotation logic was incorrect. After a round completes, the next dealer should be the player to the LEFT (counterclockwise) of the previous dealer, but the code had no rotation logic at all. Additionally, the first player to bid/play should be the player to the LEFT of the dealer (next in counter-clockwise order), not the dealer themselves.

**Root Cause:**
1. Leader was incorrectly set to dealer: `self.leader = dealer % self.seats`
2. No automatic dealer rotation between rounds
3. Dealer badge displayed on wrong seat (shown on leader instead of dealer)

**The Fix:**

**Backend Changes:**
1. Added `current_dealer` field to track dealer position (`session.py:78`)
2. Fixed leader calculation: `self.leader = (self.current_dealer + 1) % self.seats` (`session.py:174`)
3. Added automatic dealer rotation after each round: `self.current_dealer = (self.current_dealer - 1) % self.seats` (`session.py:155`)
4. Updated GameStateDTO to include `dealer` field (`models.py:64`)
5. Updated `get_public_state()` to send dealer to frontend (`session.py:235`)

**Frontend Changes:**
1. Updated GameState interface to include `dealer: number` field (`types/game.ts:42`)
2. Updated GameBoard to use `dealer` instead of `leader` for dealer badge (`GameBoard.tsx:16,47,54`)

**Fixed In:**
- `backend/app/game/session.py:78` - Added current_dealer field
- `backend/app/game/session.py:153-160` - Dealer rotation logic
- `backend/app/game/session.py:174` - Fixed leader calculation
- `backend/app/models.py:64` - Added dealer to GameStateDTO
- `backend/app/game/session.py:235` - Included dealer in public state
- `frontend/src/types/game.ts:42-43` - Added dealer to GameState type
- `frontend/src/components/game/GameBoard.tsx:16,47,54` - Use dealer for badge

**How It Works Now:**
Round 1 (4-player): Dealer=0, Leader=1, Bidding order: 1→2→3→0
Round 2: Dealer=3, Leader=0, Bidding order: 0→1→2→3
Round 3: Dealer=2, Leader=3, Bidding order: 3→0→1→2
Round 4: Dealer=1, Leader=2, Bidding order: 2→3→0→1

**Testing:**
Verified dealer badge moves counter-clockwise each round and first bidder is always to dealer's right. Tested through 4 complete rounds.

**Impact:**
**HIGH** - Game now follows official 28 card game rules for dealer rotation and bidding order.

---

## Priority: Medium (UX Improvements)

### Enhancement #3: Mobile-Optimized Phase-by-Phase UI
**Status:** 🟡 Planned
**Reported:** 2025-10-15
**Component:** Frontend (GamePage.tsx, responsive layout)

**Description:**
For mobile phone screens, the current layout tries to show everything at once (game board, scoreboard, action panels, hand). This causes crowding and poor UX on small screens.

**Proposed Solution:**
Implement a phase-focused mobile layout where only the relevant UI for the current game phase is prominently displayed, with others hidden or minimized.

**Proposed Flow:**

1. **LOBBY Phase:**
   - **Center:** Player list + "Waiting for players" message
   - **Actions:** "Start Game" / "Add Bot" buttons (large, prominent)
   - **Hidden:** Game board, scoreboard, bidding panel

2. **BIDDING Phase:**
   - **Center:** Bidding panel (large, easy to tap)
   - **Visible:** Current bids from all players
   - **Minimized:** Game board (collapsed), scoreboard (minimized to badge)
   - **Hidden:** Hand (not needed yet)

3. **CHOOSE_TRUMP Phase:**
   - **Center:** Trump selection panel (large suit buttons)
   - **Visible:** Bid winner info
   - **Minimized:** Game board, scoreboard
   - **Hidden:** Hand (not needed yet)

4. **PLAY Phase:**
   - **Center:** Game board (trick area + player seats)
   - **Bottom:** Your hand (swipeable card carousel)
   - **Sidebar Collapsed:** Scoreboard accessible via toggle button
   - **Top:** Minimal info badges (trump, current trick count)

5. **SCORING Phase:**
   - **Center:** Score summary (team points, bid result)
   - **Actions:** "Start Next Round" button
   - **Hidden:** Game board, hand

**Implementation Approach:**
- Use responsive breakpoints (`sm:`, `md:`, `lg:`)
- Phase-specific layout components that swap based on `gameState.state`
- Collapsible/expandable sections with animations
- Bottom sheet or modal for minimized panels
- Hamburger menu for scoreboard on mobile

**Related Tasks:**
- [ ] Design mobile wireframes for each phase
- [ ] Implement phase-aware layout wrapper component
- [ ] Add collapse/expand animations
- [ ] Test on various mobile screen sizes (320px - 428px width)
- [ ] Ensure touch-friendly button sizes (min 44px)

**Impact:**
**MEDIUM** - Significantly improves mobile UX but game is still playable on mobile currently (just cramped).

---

## Priority: Low (Polish & Nice-to-Have)

### Issue #4: Bot Timing Too Fast
**Status:** 🟡 Planned (see Phase 8 TODO)
**Reported:** Earlier (documented in CLAUDE.md)
**Component:** Backend (bot_runner.py)

**Description:**
Bots act instantly, making game flow hard to follow.

**Solution:** Add delays to bot actions (see frontend/CLAUDE.md Phase 8 TODO).

---

### Issue #5: No Sound Effects
**Status:** 🟡 Planned (see Phase 8 TODO)
**Reported:** Earlier (documented in CLAUDE.md)
**Component:** Frontend (sound effects)

**Description:**
Game lacks audio feedback for actions.

**Solution:** Implement sound manager (see frontend/CLAUDE.md Phase 8 TODO).

---

## Bug Fixing Workflow

1. **Report:** Create entry in this document with all details
2. **Investigate:** Add findings to "Investigation Needed" checklist
3. **Fix:** Implement fix and reference this bug number in commit message
4. **Test:** Verify fix with original reproduction steps
5. **Document:** Update bug status and add "Fixed In" section with file references
6. **Close:** Change status to 🟢 Fixed with date

---

## Bug Status Legend

- 🔴 **Open** - Not yet fixed
- 🟡 **Planned** - Fix planned but not yet implemented
- 🔵 **In Progress** - Currently being worked on
- 🟢 **Fixed** - Bug has been resolved
- ⚫ **Won't Fix** - Intentional behavior or out of scope

---

## Related Documentation

- [Frontend Development Log](../frontend/CLAUDE.md)
- [Backend Development Log](../backend/CLAUDE.md)
- [Architecture Overview](./ARCHITECTURE.md)
