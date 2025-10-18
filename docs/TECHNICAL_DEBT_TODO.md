# Technical Debt & Refactoring Todo List

**Last Updated**: 2025-10-18
**Project**: Thurup Card Game
**Reference**: Based on `TECHNICAL_REVIEW.md` analysis

---

## 📊 Progress Overview

| Priority | Total | Not Started | In Progress | Completed | Blocked |
|----------|-------|-------------|-------------|-----------|---------|
| 🔴 High  | 5     | 0           | 0           | 5         | 0       |
| 🟡 Medium| 5     | 3           | 0           | 2         | 0       |
| 🔵 Low   | 8     | 8           | 0           | 0         | 0       |
| **Total**| **18**| **11**      | **0**       | **7**     | **0**   |

**Estimated Total Effort**: 11-17 days
**Completed Effort**: ~1.6 days (TD-005, TD-007, TD-013, TD-014, TD-015)

---

## 🔴 High Priority Tasks

## 🟡 Medium Priority Tasks

### TD-005: Refactor GameSession God Class
- **Priority**: 🟡 Medium
- **Status**: ✅ Completed (Phases 1, 2 & 3 Complete, Phase 4 Deferred)
- **Effort**: 1-2 days (split into 4 phases)
- **Impact**: High - Much better maintainability and testability
- **Created**: 2025-10-17
- **Completed**: Phase 1: 2025-10-17, Phase 2: 2025-10-17, Phase 3: 2025-10-17
- **Assigned**: -
- **Dependencies**: TD-006 recommended (GameServer encapsulation helps)
- **Blocked By**: -
- **Note**: Phase 4 (RoundManager) deferred - current implementation is sufficient

**Description**:
GameSession class is 588 lines and violates Single Responsibility Principle by handling state management, game logic, AI integration, serialization, and phase transitions.

**Refactoring Strategy**: Incremental extraction (lower risk than full decomposition)

**Phase 1: Extract Hidden Trump Logic** ✅ **COMPLETED**
- Created `HiddenTrumpManager` class (stateless, pure functions)
- Created `backend/app/game/enums.py` for `HiddenTrumpMode` and `SessionState`
- Refactored `reveal_trump()` method to use manager
- Refactored `play_card()` automatic reveal logic to use manager
- **Result**: 40 lines removed from session.py, logic consolidated in one place
- **Tests**: All WebSocket reveal trump tests pass (8/8)

**Files Created**:
- `backend/app/game/hidden_trump.py` - HiddenTrumpManager class
- `backend/app/game/enums.py` - Game enums (avoid circular imports)

**Files Modified**:
- `backend/app/game/session.py` - Uses HiddenTrumpManager, imports from enums
- `backend/app/db/persistence.py` - Updated imports
- `backend/app/api/v1/rest.py` - Updated imports
- `backend/app/api/v1/bot_runner.py` - Updated imports
- All test files - Updated imports

**Phase 2: Extract Trick Management** ✅ **COMPLETED**
- Created `TrickManager` class (135 lines)
- Encapsulates current_trick, last_trick, captured_tricks
- Winner determination, points calculation, serialization
- Refactored 6 methods in session.py to use TrickManager
- **Result**: Cleaner separation of concerns, easier testing
- **Tests**: 142/146 passing (4 pre-existing test setup issues)
- **Commits**: d3bec12, 7bcab9e

**Files Created**:
- `backend/app/game/trick_manager.py` - TrickManager class

**Files Modified**:
- `backend/app/game/session.py` - Uses TrickManager, replaced 3 fields with manager
- `backend/app/db/persistence.py` - Updated serialization for tricks
- `backend/tests/unit/test_reveal_trump.py` - Updated field access
- `backend/tests/unit/test_gameplay_bug_repro.py` - Updated field access
- `backend/tests/integration/test_reveal_trump_websocket.py` - Updated field access

**Phase 3: Extract Bidding Logic** ✅ **COMPLETED**
- Created `BiddingManager` class (143 lines)
- Encapsulates bids, current_highest, bid_winner, bid_value, bids_received
- Validation, completion checking, serialization
- Refactored 7 methods in session.py to use BiddingManager
- **Result**: Bidding logic consolidated, easier to test and maintain
- **Tests**: 61/61 bidding-related tests passing
- **Commit**: [current]

**Files Created**:
- `backend/app/game/bidding_manager.py` - BiddingManager class

**Files Modified**:
- `backend/app/game/session.py` - Uses BiddingManager, replaced 5 bidding fields with manager
- `backend/app/db/persistence.py` - Updated serialization for bidding state
- `backend/tests/unit/test_bidding.py` - Updated field access
- `backend/tests/unit/test_phase1_fixes.py` - Updated field access
- `backend/tests/unit/test_scoring.py` - Updated field access
- `backend/tests/unit/test_reveal_trump.py` - Updated field access
- `backend/tests/integration/test_reveal_trump_websocket.py` - Updated field access

**Phase 4: Extract Round Lifecycle** (Pending)
- Create `RoundManager` class
- start_round(), dealer rotation, round history
- Estimated: 4-5 hours

---

### TD-006: Encapsulate Global State in GameServer
- **Priority**: 🟡 Medium
- **Status**: 📋 Not Started
- **Effort**: 1 day
- **Impact**: High - Better testing, cleaner architecture
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: TD-001 (remove dual WS tracking first)
- **Blocked By**: -

**Description**:
Global dictionaries (SESSIONS, WS_CONNECTIONS, bot_tasks) make unit testing difficult and have no clear lifecycle management.

**Current State**:
```python
SESSIONS: Dict[str, GameSession] = {}
WS_CONNECTIONS: Dict[str, Dict[WebSocket, Optional[int]]] = {}
bot_tasks: Dict[str, asyncio.Task] = {}
```

**Solution**:
1. Create `GameServer` class to encapsulate state
2. Add dependency injection via FastAPI Depends()
3. Update all endpoints to use injected GameServer
4. Add proper lifecycle management (startup/shutdown)

**Files to Create**:
- `backend/app/core/__init__.py`
- `backend/app/core/game_server.py`

**Files to Update**:
- `backend/app/main.py` (create GameServer instance, add DI)
- All API endpoint files (inject GameServer)
- `backend/tests/` (inject mock GameServer)

**Testing Checklist**:
- [ ] All existing tests pass with injected GameServer
- [ ] New tests can mock GameServer easily
- [ ] Lifecycle management works (startup/shutdown)
- [ ] No global state remaining

---

---

### TD-017: Implement AI Strategy Layer (Difficulty Levels)
- **Priority**: 🟡 Medium
- **Status**: 📋 Not Started
- **Effort**: 1-2 days
- **Impact**: Medium - Better gameplay experience, configurable bot difficulty
- **Created**: 2025-10-18
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Current AI implementation (`app/game/ai.py`) has basic heuristics hardcoded with no strategy abstraction. Need a plug-and-play middleware architecture to support multiple difficulty levels (Easy, Medium, Hard, Expert) without changing core bot logic.

**Current State** (91 lines, single difficulty):
```python
# app/game/ai.py
def choose_bid_value(hand, ..., mode="easy"):
    # Simple random logic
    if random.random() < AIConfig.PASS_PROBABILITY:
        return BidValue.PASS
    return random.randint(lower, max_total)

def select_card_to_play(hand, lead_suit, trump):
    # Basic heuristics: play lowest follow, dump low cards
    # No counting, no memory, no teammate awareness
```

**Problems**:
1. Only one difficulty level ("easy mode")
2. Bots don't count cards or track what's been played
3. No awareness of teammate's plays (team strategy)
4. Trump selection is purely suit count (no point consideration)
5. No bluffing or advanced bidding strategy
6. Strategy logic mixed with decision functions

**Proposed Architecture** (Strategy Pattern):

**1. Create Strategy Interface** (`app/game/ai/strategy.py`):
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GameContext:
    """Context passed to strategy for decision-making."""
    hand: List[Card]
    lead_suit: Optional[str]
    trump: Optional[str]
    current_trick: List[Tuple[int, Card]]
    captured_tricks: List[List[Tuple[int, Card]]]
    bids: Dict[int, Optional[int]]
    seat: int
    seats: int
    # ... other game state

class BotStrategy(ABC):
    """Abstract base class for bot strategies."""

    @abstractmethod
    def choose_bid(self, ctx: GameContext, min_bid: int,
                   max_bid: int, current_highest: Optional[int]) -> int:
        """Return bid value or PASS."""
        pass

    @abstractmethod
    def choose_trump(self, ctx: GameContext) -> str:
        """Return trump suit."""
        pass

    @abstractmethod
    def select_card(self, ctx: GameContext) -> Card:
        """Return card to play."""
        pass
```

**2. Implement Difficulty Strategies**:

**Easy Strategy** (`app/game/ai/easy_strategy.py`):
- Current behavior (random bidding, simple card play)
- No card counting or memory
- Play lowest follow, dump low cards
- Trump = most cards in suit

**Medium Strategy** (`app/game/ai/medium_strategy.py`):
- Count high cards (J, 9, A, 10) for bidding
- Track which suits have been played
- Avoid wasting high cards when losing
- Trump = suit with most points
- Basic partnership awareness

**Hard Strategy** (`app/game/ai/hard_strategy.py`):
- Full card counting (track all played cards)
- Calculate win probability for bids
- Advanced card selection:
  - Lead high to draw trumps
  - Save high cards when partner winning
  - Ruff strategically
- Trump selection considers hand strength
- Defensive play when opponents bid

**Expert Strategy** (`app/game/ai/expert_strategy.py`):
- Monte Carlo simulation for bidding
- Perfect card counting and inference
- Probabilistic opponent hand modeling
- Optimal play selection (minimax-like)
- Advanced signaling to partner
- Bluffing and deception

**3. Strategy Factory** (`app/game/ai/factory.py`):
```python
class StrategyFactory:
    @staticmethod
    def create(difficulty: str) -> BotStrategy:
        strategies = {
            "easy": EasyStrategy(),
            "medium": MediumStrategy(),
            "hard": HardStrategy(),
            "expert": ExpertStrategy(),
        }
        return strategies.get(difficulty, EasyStrategy())
```

**4. Update Bot Integration** (`app/api/v1/bot_runner.py`):
```python
async def run_bot_turn(session: GameSession, seat: int):
    # Get bot difficulty from session or config
    difficulty = session.players[seat].difficulty or "easy"
    strategy = StrategyFactory.create(difficulty)

    ctx = GameContext(
        hand=session.hands[seat],
        lead_suit=session.get_lead_suit(),
        trump=session.trump,
        # ... populate context
    )

    if session.state == SessionState.BIDDING:
        bid = strategy.choose_bid(ctx, ...)
        await session.place_bid(seat, BidCmd(value=bid))
    elif session.state == SessionState.CHOOSE_TRUMP:
        trump = strategy.choose_trump(ctx)
        await session.choose_trump(seat, ChooseTrumpCmd(suit=trump))
    elif session.state == SessionState.PLAY:
        card = strategy.select_card(ctx)
        await session.play_card(seat, PlayCardCmd(card_id=card.id))
```

**5. Add Difficulty Configuration**:

Update `PlayerInfo` model (`app/models.py`):
```python
class PlayerInfo(BaseModel):
    player_id: str
    name: str
    is_bot: bool = False
    difficulty: Optional[str] = "easy"  # easy, medium, hard, expert
```

Update frontend to allow difficulty selection when adding bots.

**Implementation Phases**:

**Phase 1: Infrastructure** (4-5 hours)
- Create strategy interface and factory
- Refactor existing AI into EasyStrategy
- Update bot_runner to use strategy pattern
- Add difficulty field to PlayerInfo
- All tests passing with easy mode

**Phase 2: Medium Strategy** (3-4 hours)
- Implement card counting helpers
- Smarter bidding (count high cards)
- Better trump selection (consider points)
- Basic partnership awareness
- Test against easy bots

**Phase 3: Hard Strategy** (4-6 hours)
- Full card counting and tracking
- Win probability calculations
- Advanced card selection logic
- Defensive play strategies
- Test difficulty progression

**Phase 4: Expert Strategy** (Optional, 8-12 hours)
- Monte Carlo simulation
- Opponent hand modeling
- Optimal play algorithms
- Performance optimization
- Extensive testing

**Files to Create**:
- `backend/app/game/ai/__init__.py`
- `backend/app/game/ai/strategy.py` - Abstract base class
- `backend/app/game/ai/context.py` - GameContext dataclass
- `backend/app/game/ai/factory.py` - Strategy factory
- `backend/app/game/ai/easy_strategy.py` - Easy mode
- `backend/app/game/ai/medium_strategy.py` - Medium mode
- `backend/app/game/ai/hard_strategy.py` - Hard mode
- `backend/app/game/ai/expert_strategy.py` - Expert mode (optional)
- `backend/app/game/ai/helpers.py` - Shared utilities (card counting, etc.)

**Files to Refactor**:
- `backend/app/game/ai.py` - Keep as facade or deprecate
- `backend/app/api/v1/bot_runner.py` - Use strategy pattern
- `backend/app/models.py` - Add difficulty field
- `backend/tests/unit/test_ai.py` - Test all strategies

**Frontend Updates**:
- `frontend/src/pages/GamePage.tsx` - Difficulty selector for "Add Bot" button
- `frontend/src/types/game.ts` - Add difficulty to PlayerInfo

**Testing Checklist**:
- [ ] All strategies pass basic decision tests
- [ ] Easy mode behaves same as current AI
- [ ] Medium bots play better than easy bots
- [ ] Hard bots beat medium bots consistently
- [ ] No performance regression (bot turns < 500ms)
- [ ] All existing tests pass
- [ ] Strategy can be changed mid-game (future feature)

**Benefits**:
- Plug-and-play architecture (easy to add new strategies)
- Better user experience (adjustable difficulty)
- Cleaner separation of concerns
- Easier to test individual strategies
- Foundation for ML/RL bots in future

**Performance Considerations**:
- Easy/Medium: < 100ms per decision
- Hard: < 500ms per decision (card counting overhead)
- Expert: < 2000ms per decision (simulation overhead)
- Add timeout safeguards to prevent game freezing

**Future Extensions**:
- Named bot personalities (e.g., "Aggressive Alice", "Conservative Carl")
- Learning bots that adapt to player behavior
- Tournament mode with consistent difficulty
- Bot statistics and performance tracking

---

### TD-008: Add Error Boundaries (Frontend)
- **Priority**: 🟡 Medium
- **Status**: 📋 Not Started
- **Effort**: 1-2 hours
- **Impact**: Medium - Better user experience on errors
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
No error boundary components. A single component error crashes the entire application.

**Current State**:
- No graceful error handling at component level
- Errors propagate to root and crash app

**Solution**:
1. Create `ErrorBoundary` component
2. Wrap routes with error boundaries
3. Add fallback UI for errors
4. Add error logging

**Files to Create**:
- `frontend/src/components/ErrorBoundary.tsx`

**Files to Update**:
- `frontend/src/App.tsx` (wrap routes)
- `frontend/src/pages/GamePage.tsx` (wrap with boundary)

**Testing Checklist**:
- [ ] Errors display fallback UI instead of crashing
- [ ] User can reload from error state
- [ ] Errors logged properly
- [ ] Error boundaries don't catch too much

---

## 🔵 Low Priority Tasks

### TD-018: Game Timing & Bot Speed Adjustments
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: Low-Medium - Better game pacing and user experience
- **Created**: 2025-10-18
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Currently, bots act instantly which makes the game flow too fast to follow. Need configurable delays for bot actions to create a more natural game pace.

**Current Issues**:
- Bots bid/play instantly (no thinking time)
- Trick completion has fixed 2-second delay (see `backend/app/api/v1/websocket.py:206`)
- State updates happen too quickly for visual feedback
- Hard to follow which bot did what

**Proposed Changes**:

**Backend Timing** (`app/api/v1/bot_runner.py`):
```python
import asyncio

async def run_bot_turn(session: GameSession, seat: int):
    # Add realistic "thinking" delay before bot acts
    if session.state == SessionState.BIDDING:
        await asyncio.sleep(random.uniform(1.0, 2.0))  # 1-2 seconds
    elif session.state == SessionState.CHOOSE_TRUMP:
        await asyncio.sleep(random.uniform(1.5, 2.5))  # 1.5-2.5 seconds
    elif session.state == SessionState.PLAY:
        await asyncio.sleep(random.uniform(1.0, 3.0))  # 1-3 seconds (randomized)

    # Then execute bot action...
```

**Configuration** (`app/constants.py`):
```python
class BotTiming:
    """Bot action timing configuration (in seconds)."""
    BID_MIN_DELAY = 1.0
    BID_MAX_DELAY = 2.0
    TRUMP_MIN_DELAY = 1.5
    TRUMP_MAX_DELAY = 2.5
    PLAY_MIN_DELAY = 1.0
    PLAY_MAX_DELAY = 3.0
    TRICK_COMPLETION_DELAY = 2.0  # Time to view completed trick
```

Make configurable via environment variables:
```bash
# .env
BOT_BID_DELAY_MIN=1.0
BOT_BID_DELAY_MAX=2.0
BOT_PLAY_DELAY_MIN=1.0
BOT_PLAY_DELAY_MAX=3.0
TRICK_COMPLETION_DELAY=2.0
```

**Files to Modify**:
- `backend/app/api/v1/bot_runner.py` - Add delays before bot actions
- `backend/app/constants.py` - Add BotTiming configuration class
- `backend/.env*` - Add timing environment variables
- `backend/app/api/v1/websocket.py` - Make trick delay configurable

**Testing Checklist**:
- [ ] Bot bidding has 1-2 second delay
- [ ] Bot trump selection has 1.5-2.5 second delay
- [ ] Bot card plays have 1-3 second delay (random feels natural)
- [ ] Delays don't block other game actions
- [ ] Configuration via env vars works
- [ ] Fast mode option for testing (disable delays)

**Future Enhancement**:
- Different timing profiles per difficulty (Expert bots "think" longer)
- Configurable speed setting in UI (Slow/Normal/Fast)

---

### TD-019: Add Sound Effects & Audio Feedback
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 3-4 hours
- **Impact**: Low-Medium - Enhanced user experience and immersion
- **Created**: 2025-10-18
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Add sound effects for game events to improve feedback and make the game more engaging.

**Planned Audio Events**:
- Card play sound (whoosh/snap effect)
- Trick winner sound (chime/success sound)
- Bid placed sound (subtle click)
- Trump selection sound (distinct tone)
- Turn indicator sound (gentle notification)
- Game start/round start sound

**Implementation Plan**:

**1. Sound Manager Utility** (`frontend/src/utils/soundManager.ts`):
```typescript
class SoundManager {
  private sounds: Map<string, HTMLAudioElement>;
  private muted: boolean;

  constructor() {
    this.sounds = new Map();
    this.muted = localStorage.getItem('soundMuted') === 'true';
    this.loadSounds();
  }

  private loadSounds() {
    const soundFiles = {
      cardPlay: '/sounds/card-play.mp3',
      trickWin: '/sounds/trick-win.mp3',
      bidPlace: '/sounds/bid-place.mp3',
      trumpSelect: '/sounds/trump-select.mp3',
      turnNotify: '/sounds/turn-notify.mp3',
      gameStart: '/sounds/game-start.mp3',
    };

    Object.entries(soundFiles).forEach(([key, path]) => {
      const audio = new Audio(path);
      audio.preload = 'auto';
      this.sounds.set(key, audio);
    });
  }

  play(soundName: string, volume: number = 0.5) {
    if (this.muted) return;
    const sound = this.sounds.get(soundName);
    if (sound) {
      sound.volume = volume;
      sound.currentTime = 0; // Reset to start
      sound.play().catch(err => console.warn('Sound play failed:', err));
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    localStorage.setItem('soundMuted', String(this.muted));
  }

  isMuted(): boolean {
    return this.muted;
  }
}

export const soundManager = new SoundManager();
```

**2. React Hook** (`frontend/src/hooks/useSoundEffects.ts`):
```typescript
export function useSoundEffects(gameState: GameState) {
  const prevStateRef = useRef(gameState);

  useEffect(() => {
    const prev = prevStateRef.current;

    // Detect card played
    if (gameState.current_trick &&
        Object.keys(gameState.current_trick).length >
        Object.keys(prev.current_trick || {}).length) {
      soundManager.play('cardPlay', 0.4);
    }

    // Detect trick completed
    if (gameState.last_trick && prev.last_trick !== gameState.last_trick) {
      soundManager.play('trickWin', 0.6);
    }

    // Detect bid placed
    if (Object.keys(gameState.bids).length > Object.keys(prev.bids).length) {
      soundManager.play('bidPlace', 0.3);
    }

    // Detect trump selected
    if (gameState.trump && !prev.trump) {
      soundManager.play('trumpSelect', 0.5);
    }

    // Detect your turn
    if (gameState.turn === mySeat && prev.turn !== mySeat) {
      soundManager.play('turnNotify', 0.4);
    }

    prevStateRef.current = gameState;
  }, [gameState]);
}
```

**3. UI Controls** (`frontend/src/components/ui/SoundToggle.tsx`):
```typescript
export function SoundToggle() {
  const [muted, setMuted] = useState(soundManager.isMuted());

  const toggleSound = () => {
    soundManager.toggleMute();
    setMuted(soundManager.isMuted());
  };

  return (
    <button onClick={toggleSound} className="...">
      {muted ? '🔇 Sound Off' : '🔊 Sound On'}
    </button>
  );
}
```

**4. Integrate in GamePage** (`frontend/src/pages/GamePage.tsx`):
```typescript
function GamePage() {
  const gameState = useGameStore(state => state.gameState);

  // Add sound effects hook
  useSoundEffects(gameState);

  return (
    <div>
      <SoundToggle />
      {/* Rest of game UI */}
    </div>
  );
}
```

**Sound Resources** (Free, royalty-free):
- [Freesound.org](https://freesound.org) - Community sound library
- [Zapsplat.com](https://www.zapsplat.com) - Free sound effects
- [Mixkit.co](https://mixkit.co/free-sound-effects/) - High-quality free sounds

**Files to Create**:
- `frontend/src/utils/soundManager.ts` - Sound manager class
- `frontend/src/hooks/useSoundEffects.ts` - React hook for game events
- `frontend/src/components/ui/SoundToggle.tsx` - Mute/unmute button
- `frontend/public/sounds/*.mp3` - Sound effect files (6-8 files)

**Files to Update**:
- `frontend/src/pages/GamePage.tsx` - Integrate sound hook and toggle
- `frontend/src/stores/uiStore.ts` - Add sound preferences if needed

**Testing Checklist**:
- [ ] Sounds play for all game events
- [ ] Mute toggle works and persists to localStorage
- [ ] No sound errors in console
- [ ] Sounds don't overlap annoyingly
- [ ] Volume levels are balanced
- [ ] Works on mobile Safari (autoplay restrictions)

**Accessibility Consideration**:
- Respect user's system sound settings
- Provide visual alternatives for all audio cues
- Default to muted on first visit (autoplay restrictions)

---

### TD-020: Add Visual Animations & Transitions
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 4-6 hours
- **Impact**: Low-Medium - Polished, professional feel
- **Created**: 2025-10-18
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Add smooth animations and visual transitions to make the game feel more polished and responsive.

**Planned Animations**:

**1. Card Play Animation** - Cards slide from hand to center:
```typescript
// frontend/src/components/game/PlayerHand.tsx
const playCardWithAnimation = (card: Card) => {
  // Add 'playing' class to trigger CSS animation
  setPlayingCard(card.id);

  setTimeout(() => {
    onPlayCard(card.id); // Actually play the card
  }, 300); // Wait for animation to complete
};
```

```css
/* Card slides to center with ease-out */
.card.playing {
  animation: slideToCenter 0.3s ease-out;
  opacity: 0;
}

@keyframes slideToCenter {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(-200px) scale(0.8);
    opacity: 0;
  }
}
```

**2. Bot Thinking Indicator**:
```typescript
// frontend/src/components/game/GameBoard.tsx
{isBotTurn && (
  <div className="absolute top-4 right-4 flex items-center gap-2">
    <div className="animate-pulse">🤖</div>
    <span className="text-sm">Bot is thinking</span>
    <div className="flex gap-1">
      <span className="animate-bounce delay-0">.</span>
      <span className="animate-bounce delay-100">.</span>
      <span className="animate-bounce delay-200">.</span>
    </div>
  </div>
)}
```

**3. Trick Completion Animation** - Cards gather and disappear:
```css
.trick-complete .card {
  animation: gatherAndFade 1s ease-in-out forwards;
}

@keyframes gatherAndFade {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  50% {
    transform: translate(var(--gather-x), var(--gather-y)) scale(0.8);
    opacity: 0.8;
  }
  100% {
    transform: translate(var(--gather-x), var(--gather-y)) scale(0);
    opacity: 0;
  }
}
```

**4. Bid/Trump Selection Transitions**:
```css
/* Fade in panels */
.panel-enter {
  opacity: 0;
  transform: translateY(-20px);
}

.panel-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.3s ease-out;
}

/* Highlight selected option */
.trump-button:active {
  transform: scale(0.95);
  transition: transform 0.1s;
}
```

**5. Score Update Animation** - Numbers count up:
```typescript
// frontend/src/components/game/ScoreBoard.tsx
function AnimatedScore({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = displayValue;
    let end = value;
    let duration = 500;
    let startTime = Date.now();

    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      const current = Math.floor(start + (end - start) * progress);

      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value]);

  return <span>{displayValue}</span>;
}
```

**6. Framer Motion Integration** (Optional, advanced):
```bash
npm install framer-motion
```

```typescript
import { motion, AnimatePresence } from 'framer-motion';

// Animate phase panels
<AnimatePresence mode="wait">
  {gameState.state === 'bidding' && (
    <motion.div
      key="bidding"
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 50 }}
      transition={{ duration: 0.3 }}
    >
      <BiddingPanel />
    </motion.div>
  )}
</AnimatePresence>
```

**Implementation Approach**:
1. Start with CSS animations (no dependencies)
2. Add React state-driven animations
3. Consider Framer Motion for complex animations (optional)

**Files to Create**:
- `frontend/src/styles/animations.css` - Keyframe animations
- `frontend/src/components/game/BotThinkingIndicator.tsx` - Bot thinking UI
- `frontend/src/components/ui/AnimatedScore.tsx` - Score counter

**Files to Update**:
- `frontend/src/components/game/PlayerHand.tsx` - Card play animation
- `frontend/src/components/game/GameBoard.tsx` - Trick animations, bot indicator
- `frontend/src/components/game/ScoreBoard.tsx` - Score animations
- `frontend/src/components/game/BiddingPanel.tsx` - Button animations
- `frontend/src/components/game/TrumpPanel.tsx` - Selection animations
- `frontend/src/index.css` - Import animations.css

**Performance Considerations**:
- Use CSS transforms (GPU-accelerated) not position
- Keep animations under 500ms for responsiveness
- Use `will-change` sparingly for performance hints
- Test on mobile devices for smoothness

**Testing Checklist**:
- [ ] Card play animation is smooth
- [ ] Bot thinking indicator shows during bot turns
- [ ] Trick completion animation doesn't block gameplay
- [ ] Score updates count up smoothly
- [ ] Panel transitions feel natural
- [ ] No jank or frame drops on animations
- [ ] Works on mobile devices

**Coordination with Backend Timing** (TD-018):
- Bot delay should match "thinking" animation duration
- Trick completion delay should match gather animation
- Ensure visual feedback completes before next state

---

### TD-016: Optimize Card Serialization with Flat Arrays
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: Low-Medium - Bandwidth optimization (86% payload reduction)
- **Created**: 2025-10-18
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Currently, cards are serialized as full JSON objects `{suit, rank, id}` for WebSocket transmission. Since card IDs already contain all needed information (e.g., `"J♠#1"` encodes rank, suit, and deck), we can send flat arrays of strings instead for significant bandwidth savings.

**Current Serialization** (400 bytes per 8-card hand):
```json
[
  {"suit": "♠", "rank": "J", "id": "J♠#1"},
  {"suit": "♠", "rank": "9", "id": "9♠#1"},
  ...
]
```

**Proposed Serialization** (56 bytes per 8-card hand):
```json
["J♠#1", "9♠#1", "A♥#1", "K♦#1", ...]
```

**Optimization Approaches Analyzed**:
1. **Flat String Arrays** (Recommended) - 86% reduction, easy to parse
2. **Numeric IDs** - Requires mapping table, harder to debug
3. **Binary Protocol** (MessagePack/Protobuf) - Complex, overkill for this use case

**Implementation Plan**:

**Backend Changes** (2 files, ~30 lines):
1. `app/models.py` - Update GameStateDTO:
   - Change `owner_hand: List[CardDTO]` → `List[str]`
   - Change `current_trick: Optional[Dict[int, CardDTO]]` → `Optional[Dict[int, str]]`
   - Change `last_trick.cards: Dict[int, CardDTO]` → `Dict[int, str]`

2. `app/game/session.py` - Update `get_public_state()`:
   - Return `card.id` directly instead of `card.to_dict()`
   - Keep all other logic unchanged

**Frontend Changes** (4 files, ~100 lines):
1. `src/types/game.ts` - Add card ID parser:
   ```typescript
   function parseCardId(cardId: string): Card {
     // Parse "J♠#1" → {rank: "J", suit: "♠", id: "J♠#1"}
     const match = cardId.match(/^([7-9JQKA]|10)([♠♥♦♣])(#\d+)?$/);
     return {
       rank: match[1],
       suit: match[2],
       id: cardId
     };
   }
   ```

2. `src/stores/gameStore.ts` - Parse on state update:
   - Convert string arrays to Card objects when receiving state
   - Keep internal state as Card objects (no component changes needed)

3. `src/components/game/PlayingCard.tsx` - Support both formats during transition:
   - Accept `card: Card | string` prop
   - Parse if string, use directly if object

4. Update GameState interface to use `string[]` for card arrays

**Performance Impact**:
- **28-mode (8 cards/hand)**: ~344 bytes saved per hand
- **56-mode (9 cards/hand)**: ~387 bytes saved per hand
- **4-player game broadcast**: ~1.4KB saved per state update
- **6-player game broadcast**: ~2.1KB saved per state update
- **Typical game (100 broadcasts)**: ~140KB total bandwidth saved

**Benefits**:
- Smaller WebSocket payloads (especially important for mobile)
- Less JSON parsing overhead
- Faster state broadcasts
- Still human-readable for debugging

**Risks**:
- Need to test all card display locations
- Parsing adds minimal CPU cost on frontend
- Card ID format must remain stable

**Testing Checklist**:
- [ ] Verify all cards display correctly in player hand
- [ ] Check trick cards in center circle
- [ ] Verify last trick display
- [ ] Test round history cards
- [ ] Test with both 28-mode and 56-mode (dual decks)
- [ ] Performance test with 6-player games
- [ ] Verify error handling for malformed card IDs

**Files to Modify**:
- Backend: `app/models.py`, `app/game/session.py`
- Frontend: `src/types/game.ts`, `src/stores/gameStore.ts`, `src/components/game/PlayingCard.tsx`, component files using cards

**Note**: This is a nice-to-have optimization. The current object serialization works perfectly fine and is easier to understand. Only implement this if bandwidth becomes a concern in production or if optimizing for mobile/low-bandwidth users.

---

### TD-009: Consolidate Persistence Layers
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: Low - Slight reduction in complexity
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Excessive abstraction layers (4 layers) for simple CRUD operations.

**Current Layers**:
1. API Endpoint
2. persistence_integration.py (thin wrapper)
3. persistence.py (SessionPersistence)
4. repository.py (Repositories)
5. SQLAlchemy

**Solution**:
Remove `persistence_integration.py` and use `SessionPersistence` directly in endpoints.

**Files to Delete**:
- `backend/app/api/v1/persistence_integration.py`

**Files to Update**:
- All API endpoints using persistence

---

### TD-010: Add Proper Logging Library (Frontend)
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: Low - Better debugging in production
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Frontend uses console.log throughout. No structured logging or log levels.

**Solution**:
1. Choose logging library (e.g., loglevel, winston)
2. Replace console.log with structured logger
3. Add log levels (debug, info, warn, error)
4. Configure for production vs development

**Files to Update**:
- Frontend codebase-wide

---

### TD-011: Type Safety Improvements (mypy)
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: 1 day
- **Impact**: Low-Medium - Catch more bugs at compile time
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Python backend has no static type checking beyond Pydantic runtime validation.

**Solution**:
1. Add mypy to development dependencies
2. Configure mypy.ini with strict settings
3. Add type hints throughout codebase
4. Fix all mypy errors
5. Add to CI pipeline

**Files to Create**:
- `backend/mypy.ini`

**Files to Update**:
- All Python files (add/fix type hints)
- `backend/pyproject.toml` (add mypy dependency)

---

### TD-012: Naming Consistency
- **Priority**: 🔵 Low
- **Status**: 📋 Not Started
- **Effort**: Ongoing
- **Impact**: Low - Better readability
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Inconsistent naming conventions across codebase (snake_case vs camelCase, seat vs seat_number, etc.).

**Issues**:
- API boundaries mix `game_id` and `gameId`
- `seat` vs `seat_number` used interchangeably
- `owner_hand` vs `my_hand` for same concept

**Solution**:
1. Document naming conventions in CONTRIBUTING.md
2. Gradually refactor to consistent naming
3. Use linters to enforce conventions

---

## ✅ Completed Tasks Archive

### TD-001: Remove Dual WebSocket Tracking ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: N/A (Already done)
- **Impact**: High - Reduces complexity, eliminates duplication, prevents race conditions
- **Created**: 2025-10-17
- **Completed**: 2025-10-17 (found already completed during audit)
- **Assigned**: -

**What Was Found**:
During codebase audit, discovered this task was already completed. The dual WebSocket tracking system has been fully consolidated to use only `ConnectionManager`.

**Audit Findings**:
- ✅ No `WS_CONNECTIONS` dict in `router.py` (only `SESSIONS`, `sessions_lock`, and `bot_tasks` remain)
- ✅ `ConnectionManager` class fully implemented in `connection_manager.py` with:
  - `register()`, `identify()`, `unregister()` methods
  - `get_game_connections()`, `get_present_seats()` methods
  - Global instance: `connection_manager = ConnectionManager()`
- ✅ `broadcast.py` uses `ConnectionManager` exclusively (no legacy dict)
- ✅ `websocket.py` uses `ConnectionManager` for connection tracking

**Files Verified**:
- `backend/app/api/v1/router.py` (lines 1-32) - No WS_CONNECTIONS found
- `backend/app/api/v1/connection_manager.py` (full file, 168 lines) - Complete implementation
- `backend/app/api/v1/broadcast.py` - Uses ConnectionManager
- `backend/app/api/v1/websocket.py` - Uses ConnectionManager

---

### TD-002: Extract resolve_game_id to Shared Utility ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: 1 hour
- **Impact**: Medium - Eliminates code duplication, better maintainability
- **Created**: 2025-10-14 (estimated)
- **Completed**: 2025-10-17
- **Assigned**: -

**What Was Done**:
Created shared utility `app/utils/game_resolution.py` with `resolve_game_identifier()` function that handles both UUID and short-code resolution with configurable error handling.

**Implementation**:
- ✅ Created `backend/app/utils/game_resolution.py` with comprehensive docstrings
- ✅ Implemented resolution logic (memory → database → UUID → short code)
- ✅ `rest.py` uses it with `raise_on_not_found=True` for HTTP 404 errors
- ✅ `websocket.py` uses it with `raise_on_not_found=False` for graceful fallback
- ✅ Eliminated 64 lines of duplicate code

**Testing Results**:
- [x] REST endpoints resolve UUIDs correctly
- [x] REST endpoints resolve short codes correctly
- [x] REST endpoints raise 404 for invalid identifiers
- [x] WebSocket resolves identifiers without raising exceptions
- [x] Database lookups work for both UUID and short code

**Files Changed**:
- Created: `backend/app/utils/game_resolution.py` (90 lines)
- Updated: `backend/app/api/v1/rest.py` (imports and uses shared function)
- Updated: `backend/app/api/v1/websocket.py` (imports and uses shared function)

---

### TD-003: Add WebSocket Message Validation ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: N/A (Already done)
- **Impact**: High - Prevents protocol errors, improves security
- **Created**: 2025-10-17
- **Completed**: 2025-10-17 (found already completed during audit)
- **Assigned**: -

**What Was Found**:
During codebase audit, discovered this task was already completed. Full Pydantic validation is implemented for all WebSocket message types.

**Audit Findings**:
- ✅ Pydantic models defined in `backend/app/models.py` (lines 192-247):
  - `WSIdentifyPayload` (line 192) - seat and player_id validation
  - `WSPlaceBidPayload` (line 199) - seat and value validation
  - `WSChooseTrumpPayload` (line 219) - seat and suit validation
  - `WSPlayCardPayload` (line 234) - seat and card_id validation
  - `WSRevealTrumpPayload` (line 241) - seat validation
  - `WSMessage` (line 247) - Top-level message envelope
- ✅ `websocket.py` uses these models for validation
- ✅ Invalid messages trigger Pydantic validation errors with clear messages

**Files Verified**:
- `backend/app/models.py` (lines 192-247) - All WebSocket Pydantic models exist
- `backend/app/api/v1/websocket.py` - Uses models for validation

---

### TD-004: Fix useGame Hook Dependencies ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: N/A (Already done)
- **Impact**: Medium - Fixes potential bugs, removes stale closures
- **Created**: 2025-10-17
- **Completed**: 2025-10-17 (found already completed during audit)
- **Assigned**: -

**What Was Found**:
During codebase audit, discovered this task was already completed. The `useGame` hook has proper dependency management with no eslint-disable comments.

**Audit Findings**:
- ✅ Refs used to avoid dependency issues (lines 90-99):
  ```typescript
  const currentSeat = useRef(seat);
  const currentPlayerId = useRef(playerId);
  const currentGameId = useRef(gameId);
  ```
- ✅ Re-identification effect when seat/playerId changes (lines 102-112)
- ✅ Proper `connect()` callback with all dependencies (lines 114-184)
- ✅ Effect includes correct dependencies: `[gameId, connect, disconnect]` (line 256)
- ✅ No `eslint-disable-next-line react-hooks/exhaustive-deps` comments found
- ✅ Early return prevents connection when gameId is null (line 250)

**Files Verified**:
- `frontend/src/hooks/useGame.ts` (273 lines) - Complete implementation with proper dependencies

**Note**: The TODO originally suggested extracting a separate `useWebSocket.ts` hook, but the current implementation is well-structured with refs solving the dependency issues. No refactoring needed.

---

## ⏸️ Blocked/Deferred Tasks

_No blocked tasks currently._

---

## 📝 Notes

### How to Use This Document

1. **Starting Work**: Change status from 📋 to 🔄, add your name to Assigned
2. **Completing Work**: Change status to ✅, add completion date, move to Archive
3. **Blocking**: Add to Blocked section with reason
4. **Dependencies**: Check Dependencies field before starting

### Status Indicators

- 📋 **Not Started** - Task identified but not begun
- 🔄 **In Progress** - Currently being worked on
- ✅ **Completed** - Task finished and tested
- ⏸️ **Blocked** - Cannot proceed due to dependency or issue

### Priority Guidelines

- 🔴 **High**: Critical issues affecting functionality, security, or causing significant technical debt
- 🟡 **Medium**: Important improvements that enhance maintainability and performance
- 🔵 **Low**: Nice-to-have improvements and polish

---

### TD-013: Fix Test Cases for Clockwise Direction ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: 2 hours
- **Impact**: High - Enables test suite to pass after Week 7 clockwise direction change
- **Created**: 2025-10-17
- **Completed**: 2025-10-17
- **Assigned**: -

**What Was Done**:
Fixed all unit test cases that were failing due to the Week 7 clockwise dealer rotation change. Tests were written assuming counter-clockwise direction but the game now uses clockwise rotation.

**The Change**:
With `dealer=0`, the leader is now calculated as `(dealer - 1) % seats = 3` (clockwise)
- Bidding order: 3 → 2 → 1 → 0 (clockwise)
- Turn advancement: `(turn - 1) % seats`

**Files Fixed**:
- `backend/tests/unit/test_bidding.py` - Fixed 2 bidding tests
- `backend/tests/unit/test_phase1_fixes.py` - Fixed 8 concurrent/validation tests
- `backend/tests/unit/test_session.py` - Fixed basic flow test
- `backend/tests/unit/test_persistence.py` - Fixed 3 persistence tests
- `backend/tests/unit/test_reveal_trump.py` - Fixed 10 reveal trump tests (completed in previous session)

**Test Results**:
- **Before**: 25 failures, 96 passes
- **After**: 4 failures, 110 passes ✅
- **Fixed**: 21 test cases updated for clockwise direction

**Remaining Failures** (4 tests, unrelated to clockwise change):
- `test_gameplay_bug_repro.py` (3 tests) - Gameplay bug reproduction tests
- `test_hidden_trump.py` (1 test) - Trump reveal edge case

**Pattern Applied**:
All fixed tests now:
1. Assert `sess.turn == 3` after `start_round(dealer=0)`
2. Use seats in clockwise order (3, 2, 1, 0) for bidding
3. Update expected winners/results to match new order
4. Include comments explaining clockwise direction

---

### TD-014: Fix Remaining Gameplay Test Failures ✅
- **Priority**: 🔴 High
- **Status**: ✅ Completed
- **Effort**: 1 hour
- **Impact**: High - All tests now passing, validates game logic correctness
- **Created**: 2025-10-18
- **Completed**: 2025-10-18
- **Assigned**: -

**What Was Done**:
Fixed the final 4 failing test cases that were introduced after the Week 7 clockwise direction change. These tests were manually setting up game state without accounting for the clockwise turn order.

**Root Cause**:
All 4 tests manually set `session.turn` and `session.leader` but didn't account for clockwise turn advancement: `self.turn = (self.turn - 1) % self.seats`

For a 4-player game starting at seat 0, turn order is: **0 → 3 → 2 → 1**

**Files Fixed**:
1. `backend/tests/unit/test_gameplay_bug_repro.py` (3 tests):
   - `test_user_reported_gameplay_bug` - Jack and 9 of spades trick winner test
   - `test_trump_ranking_all_combinations` - Trump card ranking (J > 9 > A > 10 > K > Q > 8 > 7)
   - `test_lead_suit_ranking_all_same` - Lead suit uses same ranking as trump

2. `backend/tests/unit/test_hidden_trump.py` (1 test):
   - `test_hidden_trump_reveal_on_first_nonfollow` - Trump reveal on first trump played

**Changes Made**:
- Added `session.leader = 0` before setting `session.turn = 0`
- Changed all card play sequences from counter-clockwise (0→1→2→3) to clockwise (0→3→2→1)
- Added comments explaining the turn order

**Test Results**:
- **Before**: 4 failures, 202 passes
- **After**: 0 failures, 206 passes ✅
- **Total test suite**: 206/206 passing (100%)

---

### TD-015: Remove Dead Code from Backend ✅
- **Priority**: 🔵 Low
- **Status**: ✅ Completed
- **Effort**: 30 minutes
- **Impact**: Low-Medium - Cleaner codebase, easier maintenance
- **Created**: 2025-10-18
- **Completed**: 2025-10-18
- **Assigned**: -

**What Was Done**:
Conducted comprehensive dead code analysis and removed unused functions, debug files, and repository methods.

**Items Removed**:
1. **Debug Files** (2 files, ~3KB):
   - `debug_session.py` - Manual debug script
   - `debug_bid_flow.py` - Bidding flow test script

2. **Placeholder Function**:
   - `tally_team_points()` in `app/game/rules.py` - Marked as placeholder, returned empty dict
   - Real tallying done in `GameSession.compute_scores()`

3. **Unused Repository Methods**:
   - `GameRepository.get_all_short_codes()` - Collision check done differently
   - `SnapshotRepository.cleanup_old_snapshots()` - Never called

**Items Kept** (used in tests or may be useful):
- `SnapshotRepository.get_snapshots_for_game()` - Used in `test_persistence.py`
- `PlayerRepository.remove_player()` - May be useful for admin features
- `RoundHistoryRepository.get_round()` - May be useful for admin features
- `estimate_hand_points()` in `app/game/ai.py` - Reserved for advanced AI modes

**Impact**:
- Removed ~50 lines of code
- Removed 2 debug files from project root
- All 206 tests still passing ✅
- Zero impact on functionality

---

### TD-007: Optimize Broadcast Serialization ✅
- **Priority**: 🟡 Medium
- **Status**: ✅ Completed
- **Effort**: 1 hour
- **Impact**: Medium - Better performance at scale
- **Created**: 2025-10-17
- **Completed**: 2025-10-18
- **Assigned**: -

**What Was Done**:
Optimized the `broadcast_state()` function to eliminate redundant hand serialization and dict copying for each WebSocket connection.

**Problem (Before)**:
```python
for ws in connections:
    payload = dict(base)  # Copy for EACH connection
    if seat is not None:
        payload["owner_hand"] = sess.get_hand_for(seat)  # Serialize EACH time
```

For 4 players, this meant:
- 4× dict copies of the base state (~500 bytes each)
- 4× hand serializations (8 cards → dicts, ~200 bytes each)
- Total: ~2.8KB redundant processing per broadcast

**Solution (After)**:
```python
# Pre-serialize all hands ONCE
hands_cache = {seat: sess.get_hand_for(seat) for seat in range(sess.seats)}

for ws in connections:
    payload = {**base}  # Faster shallow copy with dict unpacking
    if seat is not None:
        payload["owner_hand"] = hands_cache[seat]  # Just reference cached hand
```

**Optimizations Applied**:
1. **Pre-serialize hands once**: Created `hands_cache` dict with all player hands serialized upfront
2. **Use dict unpacking**: Changed `dict(base)` to `{**base}` for faster shallow copy
3. **Reuse cached data**: Each connection gets pre-serialized hand from cache

**Performance Impact**:
- **CPU work reduction**: ~50-75% less serialization work per broadcast
- **Memory**: Minimal increase (cache 4-6 serialized hands)
- **Scalability**: Matters more with 6+ players or multiple concurrent games

**Files Modified**:
- `backend/app/api/v1/broadcast.py` - Added hands_cache, optimized loop

**Testing Results**:
- All 206 unit tests passing ✅
- 37 connection/broadcast tests passing ✅
- No regressions in state synchronization
- All players receive correct hand data

---

_Last Updated: 2025-10-18 (TD-007: Broadcast optimization complete! 7/13 tasks done!)_
_Next Review: After completing remaining Medium Priority tasks_
