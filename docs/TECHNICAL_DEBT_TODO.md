# Technical Debt & Refactoring Todo List

**Last Updated**: 2025-10-17
**Project**: Thurup Card Game
**Reference**: Based on `TECHNICAL_REVIEW.md` analysis

---

## 📊 Progress Overview

| Priority | Total | Not Started | In Progress | Completed | Blocked |
|----------|-------|-------------|-------------|-----------|---------|
| 🔴 High  | 4     | 0           | 0           | 4         | 0       |
| 🟡 Medium| 4     | 3           | 1           | 0         | 0       |
| 🔵 Low   | 4     | 4           | 0           | 0         | 0       |
| **Total**| **12**| **7**       | **1**       | **4**     | **0**   |

**Estimated Total Effort**: 8-12 days
**Completed Effort**: ~1 day (8 hours - Phases 1&2 of TD-005)

---

## 🔴 High Priority Tasks

## 🟡 Medium Priority Tasks

### TD-005: Refactor GameSession God Class
- **Priority**: 🟡 Medium
- **Status**: 🔄 In Progress (Phases 1, 2 & 3 Complete)
- **Effort**: 1-2 days (split into 4 phases)
- **Impact**: High - Much better maintainability and testability
- **Created**: 2025-10-17
- **Completed**: Phase 1: 2025-10-17, Phase 2: 2025-10-17, Phase 3: 2025-10-17
- **Assigned**: -
- **Dependencies**: TD-006 recommended (GameServer encapsulation helps)
- **Blocked By**: -

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

### TD-007: Optimize Broadcast Serialization
- **Priority**: 🟡 Medium
- **Status**: 📋 Not Started
- **Effort**: 1-2 hours
- **Impact**: Medium - Better performance at scale
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Broadcast function serializes hands N times for N connections causing performance degradation with many players.

**Current State**:
```python
for ws, seat in conn_snapshot:
    payload = dict(base)  # Copy for EACH connection
    if seat is not None:
        payload["owner_hand"] = sess.get_hand_for(seat)  # Serialize EACH time
```

**Solution**:
1. Pre-serialize all hands once
2. Reuse serialized hands for each connection
3. Minimize dict copying

**Files to Update**:
- `backend/app/api/v1/broadcast.py`

**Testing Checklist**:
- [ ] All players receive correct hand data
- [ ] Broadcast performance improves measurably
- [ ] No regressions in state synchronization

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

_Last Updated: 2025-10-17 (TD-013: Fixed all clockwise direction test cases - 110/114 tests passing!)_
_Next Review: After completing Medium Priority tasks_
