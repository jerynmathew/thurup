# Technical Debt & Refactoring Todo List

**Last Updated**: 2025-10-17
**Project**: Thurup Card Game
**Reference**: Based on `TECHNICAL_REVIEW.md` analysis

---

## 📊 Progress Overview

| Priority | Total | Not Started | In Progress | Completed | Blocked |
|----------|-------|-------------|-------------|-----------|---------|
| 🔴 High  | 4     | 3           | 0           | 1         | 0       |
| 🟡 Medium| 4     | 4           | 0           | 0         | 0       |
| 🔵 Low   | 4     | 4           | 0           | 0         | 0       |
| **Total**| **12**| **11**      | **0**       | **1**     | **0**   |

**Estimated Total Effort**: 8-12 days
**Completed Effort**: ~0.1 days (1 hour)

---

## 🔴 High Priority Tasks

### TD-001: Remove Dual WebSocket Tracking
- **Priority**: 🔴 High
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: High - Reduces complexity, eliminates duplication, prevents race conditions
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
Two overlapping systems track WebSocket connections causing maintenance burden and potential race conditions.

**Current State**:
- `router.py` has legacy `WS_CONNECTIONS` dict
- `connection_manager.py` has new `ConnectionManager` class
- Both systems updated simultaneously (double work)

**Solution**:
1. Remove `WS_CONNECTIONS` and `ws_connections_lock` from `router.py`
2. Update `broadcast.py` to use `ConnectionManager` directly
3. Update `websocket.py` to use `ConnectionManager` directly
4. Remove legacy sync code from `connection_manager.py`

**Files to Change**:
- `backend/app/api/v1/router.py` (remove globals)
- `backend/app/api/v1/connection_manager.py` (remove legacy sync)
- `backend/app/api/v1/broadcast.py` (use ConnectionManager)
- `backend/app/api/v1/websocket.py` (use ConnectionManager)

**Testing Checklist**:
- [ ] WebSocket connections establish correctly
- [ ] State broadcasts reach all connected clients
- [ ] Disconnections clean up properly
- [ ] No race conditions under load

---


### TD-003: Add WebSocket Message Validation
- **Priority**: 🔴 High
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: High - Prevents protocol errors, improves security
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
No runtime validation of WebSocket message structure. Typos in message types cause silent failures.

**Current State**:
```python
typ = data.get("type")  # No validation!
payload = data.get("payload", {})  # Trusts structure
```

**Solution**:
1. Create Pydantic models for all WebSocket message types
2. Add validation in WebSocket handler
3. Return typed error messages for validation failures

**Message Types to Validate**:
- `identify` - seat and player_id required
- `request_state` - no payload
- `place_bid` - seat and value required
- `choose_trump` - seat and suit required
- `play_card` - seat and card_id required

**Files to Update**:
- `backend/app/models.py` (add WebSocket message models)
- `backend/app/api/v1/websocket.py` (add validation logic)

**Testing Checklist**:
- [ ] Valid messages pass validation
- [ ] Invalid message types rejected with error
- [ ] Missing required fields rejected with error
- [ ] Invalid payload structure rejected with error
- [ ] Error messages are clear and actionable

---

### TD-004: Fix useGame Hook Dependencies
- **Priority**: 🔴 High
- **Status**: 📋 Not Started
- **Effort**: 2-3 hours
- **Impact**: Medium - Fixes potential bugs, removes stale closures
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: None
- **Blocked By**: -

**Description**:
React useEffect dependencies don't match actual dependencies, causing stale closures and unnecessary reconnections.

**Current State**:
```typescript
const connect = useCallback(() => {
    // Uses many dependencies
}, [gameId, seat, playerId, ...]);

useEffect(() => {
    connect();
    return () => disconnect();
}, [gameId, seat, playerId]); // ❌ Missing connect/disconnect
// eslint-disable-next-line react-hooks/exhaustive-deps
```

**Solution**:
1. Extract WebSocket logic to separate `useWebSocket.ts` hook
2. Simplify `useGame.ts` to use the new hook
3. Fix all dependency arrays
4. Remove eslint-disable comments

**Files to Create**:
- `frontend/src/hooks/useWebSocket.ts`

**Files to Update**:
- `frontend/src/hooks/useGame.ts` (refactor to use useWebSocket)

**Testing Checklist**:
- [ ] WebSocket connects on mount
- [ ] WebSocket reconnects when gameId changes
- [ ] WebSocket doesn't reconnect unnecessarily
- [ ] No eslint warnings
- [ ] Actions (placeBid, etc.) work correctly
- [ ] Cleanup happens on unmount

---

## 🟡 Medium Priority Tasks

### TD-005: Refactor GameSession God Class
- **Priority**: 🟡 Medium
- **Status**: 📋 Not Started
- **Effort**: 1-2 days
- **Impact**: High - Much better maintainability and testability
- **Created**: 2025-10-17
- **Completed**: -
- **Assigned**: -
- **Dependencies**: TD-006 recommended (GameServer encapsulation helps)
- **Blocked By**: -

**Description**:
GameSession class is 500+ lines and violates Single Responsibility Principle by handling state management, game logic, AI integration, serialization, and phase transitions.

**Current State**:
- Single massive class with 6 different responsibilities
- Hard to test individual concerns
- Tight coupling to AI module
- Difficult to extend

**Solution**:
1. Create `GameStateManager` class for pure state tracking
2. Expand `GameRules` class for validation logic
3. Create `PhaseManager` class for state machine transitions
4. Refactor `GameSession` to be thin coordinator

**Files to Create**:
- `backend/app/game/state_manager.py`
- `backend/app/game/phase_manager.py`

**Files to Update**:
- `backend/app/game/rules.py` (expand with validation methods)
- `backend/app/game/session.py` (refactor to delegate)

**Testing Checklist**:
- [ ] All existing tests still pass
- [ ] StateManager can be tested independently
- [ ] Rules can be tested independently
- [ ] PhaseManager can be tested independently
- [ ] GameSession coordinates correctly

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

_Last Updated: 2025-10-17_
_Next Review: After completing all High Priority tasks_
