# CLAUDE_LEGACY.md

> **⚠️ LEGACY DOCUMENT - OUTDATED**
>
> This file contains historical project documentation that has been replaced by the new structured documentation system.
>
> **For current, up-to-date information, please see:**
> - [Getting Started Guide](../getting-started/QUICKSTART.md) - Quick setup and first game
> - [Installation Guide](../getting-started/INSTALLATION.md) - Detailed setup instructions
> - [Architecture Documentation](../development/ARCHITECTURE.md) - System design and structure
> - [Developer Guide](../development/DEVELOPER_GUIDE.md) - Development workflow
> - [API Reference](../development/API_REFERENCE.md) - Complete API documentation
> - [Testing Guide](../testing/TESTING_GUIDE.md) - Testing strategies and commands
> - [Contributing Guide](../development/CONTRIBUTING.md) - How to contribute
>
> This file is preserved for historical reference only and may contain outdated information.

---

# CLAUDE.md (Legacy)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Thurup is a real-time multiplayer card game (28/56 variant) with a FastAPI backend and React/TypeScript frontend. The game uses WebSockets for real-time state synchronization and REST endpoints for setup actions.

## Development Commands

### Backend

```bash
# From project root
cd backend

# Install dependencies (uv preferred)
uv sync

# Run development server (default port 18081)
uv run uvicorn app.main:app --reload --port 18081

# Run tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_bidding.py -v

# Run with coverage
uv run pytest --cov=app
```

### Frontend

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Run development server (default port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Full Stack (Docker)

```bash
# From project root
make dev          # Start both services with docker-compose
make backend      # Run backend only
make frontend     # Run frontend only
```

## Architecture

### State Machine Flow

The game follows this state progression:
`LOBBY → DEALING → BIDDING → CHOOSE_TRUMP → PLAY → SCORING → ROUND_END`

### Backend Structure

- `backend/app/main.py` - FastAPI entrypoint with CORS middleware and structured logging setup
- `backend/app/api/v1.py` - REST and WebSocket endpoints, bot orchestration with concurrency safety
- `backend/app/game/session.py` - Core game engine with async lock-based state management
- `backend/app/game/rules.py` - Card dealing, trick evaluation, scoring logic
- `backend/app/game/ai.py` - Bot decision-making (bidding, trump selection, card play)
- `backend/app/models.py` - Pydantic models with validators for all DTOs and requests
- `backend/app/constants.py` - Centralized enums and configuration constants
- `backend/app/logging_config.py` - Structured logging configuration with JSON support
- `backend/app/middleware.py` - Request ID tracking middleware for log correlation

### Frontend Structure

- `frontend/src/App.tsx` - Main game UI with seat layout, bid controls, state rendering
- `frontend/src/hooks/useGameSocket.tsx` - WebSocket lifecycle management with auto-reconnect
- `frontend/src/components/` - Reusable UI components (Banner, Toasts)

### Key Data Models

- `GameSession` - In-memory game state with async lock for concurrency safety
- `PlayerInfo` - Player metadata (name, seat, is_bot flag)
- `Card` - Immutable dataclass with suit, rank, unique ID (uid)
- `GameStateDTO` - Public state broadcast to clients (excludes private hand info)

### Concurrency and Locks

The backend uses multiple locks for thread safety:
- `GameSession._lock` - Protects game state mutations (bidding, card play, etc.)
- `_sessions_lock` in `v1.py` - Protects SESSIONS dictionary access
- `_ws_connections_lock` in `v1.py` - Protects WS_CONNECTIONS dictionary access

**Critical Rules:**
- Never call `start_round()` while holding `_lock` (causes deadlock)
- Acquire locks in consistent order to prevent deadlocks
- Release locks before performing I/O operations (e.g., WebSocket sends)
- Use `async with lock:` context managers for automatic cleanup

### Bot System

Bots are managed by `run_bots_for_game()` in `v1.py`:
- Runs sequentially for each phase (BIDDING, CHOOSE_TRUMP, PLAY)
- Only acts on the current turn/seat
- Uses `force_bot_play_choice()` to get AI decisions synchronously
- Automatically scheduled after player actions and round start
- **Task Management:** `_bot_tasks` dict prevents duplicate concurrent bot runners per game
- Bot tasks are cleaned up automatically via `add_done_callback()`

## Communication Protocol

### REST Endpoints (all under `/api/v1`)

All requests are validated using Pydantic models with proper constraints:

- `POST /game/create` - Create new game (body: `CreateGameRequest`)
  - `mode`: "28" or "56" (default: "28")
  - `seats`: 4 or 6 (default: 4)
- `POST /game/{id}/join` - Join game (body: `JoinGameRequest`)
  - `name`: 1-50 characters (required)
  - `is_bot`: boolean (default: false)
  - Auto-starts round if table is full and in LOBBY state
- `POST /game/{id}/start` - Manually start round (body: `StartGameRequest`)
  - `dealer`: seat index 0-5 (default: 0)
- `POST /game/{id}/bid?seat=0` - Place bid (body: `BidCmd`)
  - `value`: int (14-56) or null/-1 for pass
- `POST /game/{id}/choose_trump?seat=0` - Choose trump (body: `ChooseTrumpCmd`)
  - `suit`: one of "♠", "♥", "♦", "♣"
- `POST /game/{id}/play?seat=0` - Play card (body: `PlayCardCmd`)
  - `card_id`: string (non-empty)

### WebSocket Messages (at `/ws/game/{id}`)

**Client → Server:**
- `identify` - Bind socket to seat (payload: `{seat: int}`)
- `request_state` - Request current state snapshot
- `place_bid` - Place bid (payload: `{seat: int, value: int | null}`)
- `choose_trump` - Choose trump (payload: `{seat: int, suit: string}`)
- `play_card` - Play card (payload: `{seat: int, card_id: string}`)

**Server → Client:**
- `state_snapshot` - Full game state (includes `owner_hand` if socket identified)
- `action_ok` - Action succeeded (payload: `{action: string, message: string}`)
- `action_failed` - Action validation failed (payload: `{action: string, message: string}`)
- `error` - General error (payload: `{message: string}`)

### Private State Handling

- `owner_hand` is sent only to the specific socket identified with a seat
- WebSocket handler uses `WS_CONNECTIONS[game_id][websocket] = seat` mapping
- `broadcast_state()` customizes payload per socket based on seat ownership

## Game Rules (28/56)

### Deck Composition

- **28 mode:** Single 32-card deck (7-A in 4 suits), 8 cards per player (4 seats)
- **56 mode:** Two 32-card decks (64 cards total), 9 cards per player (6 seats), kitty with remainder

### Bidding

- Sequential turn-based bidding starting from leader
- Minimum bid: 14 (configurable via `min_bid`)
- Pass represented as `-1` internally (client can send `null` or `-1`)
- Bidding ends when all seats have acted (no `None` values left in `bids` dict)
- If all pass: automatic redeal

### Trump Selection

- Bid winner chooses trump suit from `["♠", "♥", "♦", "♣"]`
- Trump can be hidden based on `hidden_trump_mode` (default: reveal on first non-follow)

### Card Play

- Must follow lead suit if possible (enforced server-side)
- Trick winner determined by highest trump (if any) or highest lead suit card
- Winner leads next trick
- Round ends when all hands empty

### Scoring

- Points: J=3, 9=2, A=1, 10=1 (rest are 0)
- Teams: even seats vs odd seats
- Bid success: winning team's points >= bid value

## Testing Strategy

### Backend Tests

- `test_session.py` - Basic session lifecycle
- `test_bidding.py` - Sequential bidding logic, pass handling, redeal
- `test_rules.py` - Deck creation, dealing, trick evaluation
- `test_scoring.py` - Point calculation and team scoring
- `test_hidden_trump.py` - Trump reveal conditions
- `test_phase1_fixes.py` - **New:** Comprehensive tests for Week 1 improvements
  - Concurrency safety (locks, concurrent operations)
  - Input validation (Pydantic models)
  - Bot integration and task management
  - State transitions and sequential bidding

Tests use `pytest` with `pytest-asyncio` for async test support.
**Current coverage:**
- Backend: 331 tests passing, 76% coverage
- Frontend E2E: 13 tests (10 passing, 3 timing-related failures)

## Environment Variables

### Backend (.env or environment)

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 18081)
- `DEBUG` - Enable debug mode
- `CORS_ORIGINS` - Comma-separated allowed origins

### Frontend (.env)

- `VITE_API_BASE` - Backend URL (default: http://localhost:18081)

## Common Development Patterns

### Adding a New Game Phase

1. Add state to `SessionState` enum in `session.py`
2. Update state machine logic in relevant methods (`place_bid`, `play_card`, etc.)
3. Add corresponding WebSocket/REST handlers in `v1.py`
4. Update `broadcast_state()` to include new state info if needed
5. Write tests covering new phase transitions

### Debugging WebSocket Issues

- Use `GET /game/{id}/debug` to inspect internal session state
- Check browser console for WebSocket messages
- Verify socket identification with `identify` message
- Ensure `broadcast_state()` is called after state mutations

### Working with Bots

- Bot logic is in `backend/app/game/ai.py`
- `force_bot_play_choice()` returns commands as dicts with `type` and `payload`
- Bot runner only acts when it's the bot's turn in sequential phases
- To debug: add print statements in `run_bots_for_game()` and `force_bot_play_choice()`

## Coding Standards

This project follows strict coding principles:

### SOLID Principles
- **Single Responsibility** - Each class/function has one clear purpose (e.g., `GameSession` manages state, `rules.py` handles card logic)
- **Open/Closed** - Extend behavior without modifying existing code (e.g., new game phases via state machine)
- **Liskov Substitution** - Subtypes must be substitutable for base types
- **Interface Segregation** - Prefer specific interfaces over general ones (e.g., separate command DTOs)
- **Dependency Inversion** - Depend on abstractions, not concrete implementations

### DRY (Don't Repeat Yourself)
- Extract common patterns into reusable functions
- Example: `broadcast_state()` centralizes WebSocket state synchronization
- Avoid duplicating validation logic across REST and WebSocket handlers

### KISS (Keep It Simple)
- Prefer clarity over cleverness
- Use straightforward algorithms (e.g., sequential bidding vs complex auction systems)
- Avoid premature abstractions

### YAGNI (You Aren't Gonna Need It)
- Only implement features that are currently needed
- Avoid speculative generalization
- Example: In-memory sessions are sufficient before adding database persistence

### Testing Requirements
- **Maximum test coverage** - All new features must have corresponding tests
- Tests must remain synchronized with code changes
- Use `pytest --cov=app` to verify coverage
- Test edge cases (e.g., all-pass bidding, disconnect during play)

### Code Quality
- Keep tests up to date when refactoring
- Remove dead code and unused imports
- Prefer explicit error handling over silent failures
- Document complex logic (e.g., hidden trump reveal conditions)

## Important Constraints

- Never hold `GameSession._lock` when calling `start_round()` (causes deadlock)
- Bidding is strictly sequential (only `turn` seat can act)
- WebSocket disconnects must clean up `WS_CONNECTIONS` mapping
- Card UIDs must be unique across decks (format: `{rank}{suit}#{deck_num}`)
- All async state mutations should acquire `_lock` to prevent races
- Never use `print()` for logging - use structured logging via `get_logger(__name__)`
- All external inputs must be validated using Pydantic models
- Use constants from `constants.py` instead of magic numbers/strings

## Structured Logging

The backend uses `structlog` for structured, contextual logging:

### Usage

```python
from app.logging_config import get_logger

logger = get_logger(__name__)

# Log with structured context
logger.info("game_created", game_id=game_id, mode="28", seats=4)
logger.error("bid_failed", game_id=game_id, seat=0, error="Not your turn")
logger.debug("bot_action", game_id=game_id, seat=1, action="place_bid", value=15)
```

### Configuration

- **Development:** Pretty console output with colors (`LOG_JSON=false`)
- **Production:** JSON logs for structured parsing (`LOG_JSON=true`)
- **Log Level:** Set via `LOG_LEVEL` env var (default: INFO)

### Request Correlation

- `RequestIDMiddleware` adds unique `request_id` to all logs in a request
- Request ID is also returned in `X-Request-ID` response header
- WebSocket logs include `game_id` for correlation

### Best Practices

- Use event names as first argument (e.g., "game_created", "bid_placed")
- Include relevant context as kwargs (game_id, seat, action, etc.)
- Use appropriate log levels: debug, info, warning, error
- Never log sensitive data (passwords, tokens, etc.)

## Constants and Enums

All magic numbers and strings are centralized in `app/constants.py`:

### Available Constants

- **GameMode**: `MODE_28`, `MODE_56`
- **Suit**: `SPADES`, `HEARTS`, `DIAMONDS`, `CLUBS`
- **CardRank**: `SEVEN` through `ACE`
- **GameConfig**: `MIN_BID_DEFAULT`, `MAX_BID_28`, `MAX_BID_56`, `VALID_SEAT_COUNTS`, etc.
- **BotConfig**: `ACTION_DELAY_SECONDS`, `MAX_CYCLES_PER_RUN`
- **AIConfig**: `PASS_PROBABILITY`, `BID_RANDOMNESS_RANGE`
- **ErrorMessage**: Standardized error strings
- **BidValue**: `PASS` (-1), `NO_BID` (None)
- **TeamConfig**: Team assignment helpers

### Usage Example

```python
from app.constants import GameMode, GameConfig, ErrorMessage, BidValue

# Use enums instead of strings
if mode not in (GameMode.MODE_28.value, GameMode.MODE_56.value):
    raise ValueError(ErrorMessage.INVALID_MODE)

# Use constants instead of magic numbers
if bid_value < GameConfig.MIN_BID_DEFAULT:
    return False, f"Bid must be >= {GameConfig.MIN_BID_DEFAULT}"

# Use BidValue for pass handling
if value is None or value == BidValue.PASS:
    self.bids[seat] = BidValue.PASS
```

## Input Validation

All external inputs are validated using Pydantic models with field validators:

### Request Models

- **CreateGameRequest**: Validates mode and seat count
- **JoinGameRequest**: Validates player name length
- **StartGameRequest**: Validates dealer seat index
- **BidCmd**: Validates bid range and pass value
- **ChooseTrumpCmd**: Validates suit against allowed values
- **PlayCardCmd**: Validates card_id is non-empty

### Validation Benefits

1. **Type Safety**: Automatic type checking and coercion
2. **Error Messages**: Clear, standardized validation errors
3. **Documentation**: OpenAPI/Swagger schema auto-generation
4. **Security**: Prevents injection and malformed data
5. **Maintainability**: Single source of truth for constraints

### Adding New Validators

```python
from pydantic import BaseModel, Field, field_validator

class MyRequest(BaseModel):
    value: int = Field(..., ge=0, le=100)

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: int) -> int:
        if v % 2 != 0:
            raise ValueError("Must be even")
        return v
```

## Week 1 Refactoring Summary (Completed)

### Phase 1: Critical Security & Stability Fixes

1. **Race Condition Fixes** ✅
   - Added `_sessions_lock` for SESSIONS dictionary access
   - Added `_ws_connections_lock` for WS_CONNECTIONS dictionary access
   - Protected shared state with consistent locking patterns

2. **Bot Task Management** ✅
   - Implemented `_bot_tasks` dict to prevent duplicate bot runners
   - Added automatic cleanup via `add_done_callback()`
   - `schedule_bot_runner()` checks for existing tasks before creating new ones

3. **WebSocket Reconnection** ✅
   - Frontend: Fixed stale closure bug in `useGameSocket.tsx`
   - Implemented exponential backoff with jitter
   - Max 5 reconnection attempts with proper cleanup

4. **Security** ✅
   - Removed debug endpoint that exposed all player hands
   - Added proper error handling and validation

### Week 1: Code Quality & Validation

1. **Structured Logging** ✅
   - Replaced all 15+ `print()` statements with structured logging
   - Implemented `structlog` with JSON output support
   - Added `RequestIDMiddleware` for request correlation
   - Created `app/logging_config.py` with flexible configuration

2. **Constants & Enums** ✅
   - Created comprehensive `app/constants.py` module
   - Replaced magic numbers throughout codebase
   - Added enums for game modes, suits, ranks, etc.
   - Centralized configuration (bid limits, timeouts, etc.)

3. **Input Validation** ✅
   - Enhanced all Pydantic models with field validators
   - Created request models for REST endpoints
   - Added comprehensive validation for bids, suits, names, etc.
   - Updated API endpoints to use validated request models

4. **Testing** ✅
   - Created `test_phase1_fixes.py` with 16 new tests
   - Tests cover concurrency, validation, bot integration
   - All 24 tests passing
   - Test coverage increased significantly

### Files Modified/Created

**New Files:**
- `backend/app/logging_config.py` - Structured logging setup
- `backend/app/middleware.py` - Request ID middleware
- `backend/app/constants.py` - Centralized constants and enums
- `backend/tests/test_phase1_fixes.py` - Comprehensive Phase 1 tests

**Modified Files:**
- `backend/app/main.py` - Added logging and middleware setup
- `backend/app/api/v1.py` - Added locks, bot task management, logging, validation
- `backend/app/game/session.py` - Replaced magic numbers, added logging
- `backend/app/game/rules.py` - Replaced magic numbers with constants
- `backend/app/game/ai.py` - Replaced magic numbers with constants
- `backend/app/models.py` - Added validators and request models
- `backend/pyproject.toml` - Added structlog dependencies
- `frontend/src/hooks/useGameSocket.tsx` - Fixed reconnection logic

### E2E Testing & Project Maturity (Completed)

1. **Playwright E2E Test Suite** ✅
   - Implemented comprehensive E2E tests using Playwright
   - Test coverage: 13 test scenarios, 10 passing (77% success rate)
   - Test locations: `frontend/tests/e2e/game-flow.spec.ts`, `frontend/tests/e2e/home-page.spec.ts`
   - Configuration: `frontend/playwright.config.ts`

2. **Test Scenarios Covered** ✅
   - Complete game creation and lobby flow
   - Bot player addition and management
   - Game start with full player count
   - Session persistence on page refresh
   - Bidding phase interactions
   - Card display and hand management
   - Real-time WebSocket state updates

3. **Known Issues**
   - 3 tests fail intermittently due to bot addition timing
   - Tests require backend running on port 18081
   - Some timing adjustments needed for CI/CD environments

4. **Project Maturity Improvements** ✅
   - Added MIT License for open source distribution
   - Established professional git commit policy (no AI/tool references)
   - Updated .gitignore to exclude test artifacts (coverage, playwright reports)
   - Removed tracked test artifacts from repository

5. **Test Commands**
   ```bash
   # Run E2E tests
   cd frontend
   npm run test:e2e

   # Run E2E tests in UI mode
   npm run test:e2e:ui

   # Run specific test file
   npx playwright test tests/e2e/game-flow.spec.ts
   ```

### Git Workflow

**Branch Strategy:**
- **main**: Stable, production-ready branch with clear feature/bugfix commits
  - Only squash-merged features from play branch
  - Each commit represents a complete, tested feature set
  - Tagged releases (v0.1.0, v0.2.0, etc.)
- **play**: Development, iteration, and experimentation branch
  - All active development happens here
  - Detailed commit history preserved
  - Squash merge to main when features are stable

**Workflow Process:**
1. Work in `play` branch for all development and iteration
2. When feature is stable and tested, squash merge to `main`
3. Create annotated tag on `main` for significant releases
4. Continue development in `play` branch

**Example:**
```bash
# Work in play branch
git checkout play
# ... make changes, commit ...

# When ready to release
git checkout main
git merge --squash play
git commit -m "Add feature X with comprehensive tests

- Feature details
- Test coverage
- Documentation updates"

# Tag release
git tag -a v0.1.0 -m "Release v0.1.0 - Description"

# Continue work
git checkout play
```

### Next Steps: Week 2 (Persistence Layer)

- Implement SQLite persistence with SQLAlchemy
- Create Repository pattern for data access
- Add Alembic for database migrations
- Implement session persistence and recovery
- Support multiple concurrent game rooms
