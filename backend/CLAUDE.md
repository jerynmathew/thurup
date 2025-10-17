# Thurup Backend - Development Log

This document tracks the development phases and major changes to the Thurup card game backend.

## Project Overview

Thurup is a FastAPI-based backend for the 28/56 card game variant. It features:
- Real-time game state management
- WebSocket support for live updates
- Bot AI opponents
- Structured logging
- Database persistence with SQLModel
- Async/await architecture

## Technology Stack

- **Framework**: FastAPI 0.115.0+
- **Database**: SQLite with async support (aiosqlite)
- **ORM**: SQLModel 0.0.22 (combines SQLAlchemy + Pydantic)
- **Migrations**: Alembic 1.14.0
- **Logging**: Structlog 24.4.0
- **Testing**: Pytest 8.4.0 with pytest-asyncio
- **Code Quality**: Ruff 0.8.0, Black 24.0.0

---

## Week 1: Core Game Logic & Code Quality (Completed)

### Objectives
Establish robust game rules, improve code quality, and add comprehensive testing.

### Changes Implemented

#### 1. Structured Logging
- **File**: `app/logging_config.py`
- Implemented structured logging with `structlog`
- JSON output for production, pretty-printed for development
- Request ID tracking via middleware
- Key-value pair logging for better observability

```python
logger.info("bid_placed", game_id=game_id, seat=seat, value=bid_value)
```

#### 2. Constants & Configuration
- **File**: `app/constants.py`
- Centralized all magic numbers and string literals
- Created enums for game modes, suits, card ranks
- Configuration classes for game rules, bots, network settings
- Timeout configurations for different game states

#### 3. Input Validation
- **Files**: `app/models.py`, `app/game/session.py`
- Pydantic models for all API inputs (`BidCmd`, `ChooseTrumpCmd`, `PlayCardCmd`)
- Type validation at API boundaries
- Seat range validation
- Player name length constraints

#### 4. Sequential Bidding Fix
- **File**: `app/game/session.py`
- Fixed race conditions in concurrent bidding
- Turn-based bidding with proper validation
- Prevents out-of-order bids
- Thread-safe using `asyncio.Lock`

#### 5. Comprehensive Testing
- **Files**: `tests/test_*.py`
- 24 test cases covering:
  - Bidding logic and validation
  - Hidden trump reveal mechanics
  - Concurrency and race conditions
  - State transitions
  - Bot integration
  - Card game rules
  - Scoring calculations

#### 6. Import Cleanup
- Converted all relative imports to absolute imports
- Removed unused imports across the codebase
- Consistent import ordering
- Verified with ruff linter

---

## Week 2: Persistence Layer (Completed)

### Objectives
Add database persistence for game sessions, enable game recovery, and implement cleanup tasks.

### Changes Implemented

#### 1. Package Updates
- **File**: `pyproject.toml`
- Updated to latest stable versions:
  - FastAPI: 0.115.0+
  - Pydantic: 2.10.0+
  - SQLModel: 0.0.22+
  - Alembic: 1.14.0+
  - Structlog: 24.4.0+
  - pytest-asyncio: 0.25.0+
- Added dev dependencies: ruff, black
- All packages use modern async patterns

#### 2. Database Models
- **File**: `app/db/models.py`
- Three SQLModel tables:
  - **GameModel**: Core game metadata and configuration
  - **PlayerModel**: Player information with seat assignments
  - **GameStateSnapshotModel**: Complete game state snapshots for recovery
- Foreign key relationships between tables
- Automatic timestamp tracking
- Index on game_id for fast lookups

#### 3. Database Configuration
- **File**: `app/db/config.py`
- Async SQLAlchemy engine with aiosqlite
- Session factory with proper lifecycle management
- `get_db()` dependency for FastAPI
- `init_db()` and `close_db()` lifecycle functions
- Environment-based configuration

#### 4. Repository Pattern
- **File**: `app/db/repository.py`
- Three repositories for clean data access:
  - **GameRepository**: CRUD operations for games, cleanup old games
  - **PlayerRepository**: Manage players in games
  - **SnapshotRepository**: Create and retrieve game state snapshots
- Async methods throughout
- Proper transaction handling

#### 5. Session Persistence
- **File**: `app/db/persistence.py`
- `SessionPersistence` class for save/load operations
- Serialization of complete game state including:
  - Card hands, deck, kitty
  - Bids and bidding state
  - Trump information
  - Current trick and captured tricks
  - Points per seat
- Restore game from latest snapshot
- Support for multiple snapshots per game

#### 6. Database Migrations
- **Tool**: Alembic
- **Directory**: `alembic/versions/`
- Initial migration: `22dbfa4b623f_initial_sqlmodel_migration.py`
- Creates all three tables with proper schema
- Configured for async operations
- SQLModel metadata integration

#### 7. Background Cleanup Task
- **File**: `app/db/cleanup.py`
- Periodic cleanup of old/stale games:
  - Lobby games: 1 hour timeout (configurable)
  - Active games: 2 hours no activity (configurable)
  - Completed games: 24 hours retention (configurable)
- Runs every 30 minutes
- Graceful start/stop with application lifecycle

#### 8. Application Lifecycle
- **File**: `app/main.py`
- FastAPI lifespan context manager
- Startup sequence:
  1. Initialize database (create tables)
  2. Start cleanup background task
- Shutdown sequence:
  1. Stop cleanup task
  2. Close database connections
- Proper async handling

#### 9. Persistence Tests
- **File**: `tests/test_persistence.py`
- 8 comprehensive test cases:
  - Save new session
  - Load existing session
  - Save with active game state
  - Update existing session
  - Delete session
  - Load nonexistent session
  - Card serialization/deserialization
  - Multiple snapshots
- In-memory SQLite for fast testing
- pytest-asyncio integration

### Database Schema

```sql
-- Games table
CREATE TABLE games (
    id VARCHAR(36) PRIMARY KEY,
    mode VARCHAR(10) NOT NULL,
    seats INTEGER NOT NULL,
    min_bid INTEGER NOT NULL,
    hidden_trump_mode VARCHAR(50) NOT NULL,
    two_decks_for_56 BOOLEAN NOT NULL,
    state VARCHAR(20) NOT NULL,
    current_phase_data TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_activity_at DATETIME NOT NULL
);

-- Players table
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id VARCHAR(36) NOT NULL REFERENCES games(id),
    player_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    seat INTEGER NOT NULL,
    is_bot BOOLEAN NOT NULL,
    joined_at DATETIME NOT NULL
);
CREATE INDEX ix_players_game_id ON players(game_id);

-- Game state snapshots table
CREATE TABLE game_state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id VARCHAR(36) NOT NULL REFERENCES games(id),
    snapshot_data TEXT NOT NULL,  -- JSON serialized complete state
    state_phase VARCHAR(20) NOT NULL,
    snapshot_reason VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL
);
CREATE INDEX ix_game_state_snapshots_game_id ON game_state_snapshots(game_id);
```

### Code Quality Metrics

- **Total Tests**: 32 (24 original + 8 persistence)
- **Test Coverage**: Core game logic, persistence layer, edge cases
- **Lint Status**: ✅ Clean (ruff check)
- **Format Status**: ✅ Formatted (black)
- **Type Safety**: Full Pydantic validation
- **Async Pattern**: Consistent throughout

---

## Architecture Patterns

### Repository Pattern
Abstracts database access behind clean interfaces:
```python
async def get_game(self, game_id: str) -> Optional[GameModel]:
    result = await self.session.execute(
        select(GameModel).where(GameModel.id == game_id)
    )
    return result.scalar_one_or_none()
```

### Dependency Injection
FastAPI dependencies for database sessions:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Async/Await Throughout
All I/O operations are async:
- Database queries
- Game state mutations
- API endpoints
- Background tasks

### Structured Logging
Key-value pairs for machine-readable logs:
```python
logger.info("game_created_in_db", game_id=game_id, mode=mode, seats=seats)
```

---

## Future Enhancements (Planned)

### Week 3: Real-time Features
- WebSocket connection management
- Live game state broadcasts
- Player presence/disconnection handling
- Reconnection with state recovery

### Week 4: Advanced Features
- Game history and replays
- Player statistics
- Tournament mode
- Advanced AI difficulty levels

### Week 5: Production Readiness
- PostgreSQL migration
- Redis caching
- Performance optimization
- Monitoring and alerting

---

## Development Commands

### Setup
```bash
# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Generate new migration
uv run alembic revision --autogenerate -m "description"
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_persistence.py -v
```

### Code Quality
```bash
# Check code with ruff
uv run ruff check app/ tests/

# Auto-fix issues
uv run ruff check --fix app/ tests/

# Format with black
uv run black app/ tests/
```

### Running
```bash
# Development server
uv run uvicorn app.main:app --reload

# Production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Key Files Reference

### Core Application
- `app/main.py` - FastAPI application with lifespan management
- `app/api/v1.py` - HTTP and WebSocket endpoints
- `app/middleware.py` - Request ID tracking
- `app/logging_config.py` - Structured logging setup

### Game Logic
- `app/game/session.py` - GameSession class, state machine
- `app/game/rules.py` - Card game rules and logic
- `app/game/ai.py` - Bot AI decision-making

### Database
- `app/db/models.py` - SQLModel table definitions
- `app/db/config.py` - Database configuration and session management
- `app/db/repository.py` - Data access repositories
- `app/db/persistence.py` - GameSession serialization/deserialization
- `app/db/cleanup.py` - Background cleanup task

### Configuration
- `app/constants.py` - Constants and enums
- `app/models.py` - Pydantic models for API
- `pyproject.toml` - Dependencies and project metadata
- `alembic.ini` - Database migration configuration

---

## Notes

- All timestamps use UTC
- Game IDs are UUIDs (string format)
- Card UIDs include deck number for 56-mode (e.g., "A♠#1", "A♠#2")
- Async locks prevent race conditions in concurrent operations
- Snapshots enable game recovery after server restarts
- Cleanup task prevents database bloat from abandoned games

---

## Week 3: API Completion & Testing (Completed)

### Objectives
Complete API endpoints for history, admin functionality, and comprehensive testing infrastructure.

### Changes Implemented

#### 1. Game History & Replay System
- **File**: `app/api/v1/history.py`
- Five new endpoints for game history:
  - `GET /api/v1/history/games` - List games with filters (state, mode, pagination)
  - `GET /api/v1/history/games/{game_id}` - Game detail with all snapshots
  - `GET /api/v1/history/games/{game_id}/snapshots/{snapshot_id}` - Specific snapshot
  - `GET /api/v1/history/games/{game_id}/replay` - Full replay data
  - `GET /api/v1/history/stats` - Game statistics
- Supports filtering by game state (lobby, active, completed)
- Pagination with limit/offset
- Returns complete snapshot history for replay

#### 2. Admin & Debug Endpoints
- **File**: `app/api/v1/admin.py`
- HTTP Basic Auth protection for all admin endpoints
- Configurable via environment variables (ADMIN_USERNAME, ADMIN_PASSWORD)
- Eight admin endpoints:
  - `GET /api/v1/admin/health` - Server health metrics
  - `GET /api/v1/admin/sessions` - List active sessions with connection status
  - `GET /api/v1/admin/sessions/{game_id}/detail` - Detailed session info
  - `GET /api/v1/admin/database/stats` - Database statistics
  - `POST /api/v1/admin/sessions/{game_id}/save` - Force save game state
  - `DELETE /api/v1/admin/sessions/{game_id}` - Delete session
  - `POST /api/v1/admin/maintenance/cleanup` - Trigger cleanup task
  - All endpoints log access for audit trail

#### 3. Integration Tests
- **File**: `tests/test_api_integration.py`
- 24 integration tests covering:
  - **REST endpoints** (4 tests): Game creation, joining, bidding, trump selection
  - **History endpoints** (5 tests): List games, detail, snapshots, replay, stats
  - **Admin endpoints** (8 tests): All admin functionality with auth validation
  - **WebSocket** (3 tests): Connection, identification, state requests
  - **Persistence** (2 tests): Save/load game state
  - **End-to-end** (2 tests): Complete game flows
- Uses pytest fixtures for test data
- In-memory database for fast execution

#### 4. Test Reorganization
- **Structure**: Organized into three test categories:
  - `tests/unit/` - 32 unit tests (game logic, rules, AI, bidding)
  - `tests/integration/` - 24 integration tests (API, database, WebSocket)
  - `tests/e2e/` - 4 E2E test classes (complete flows with running server)
- **File**: `tests/README.md` - Comprehensive testing documentation
- **File**: `tests/e2e/test_complete_flow.py` - End-to-end tests:
  - TestCompleteGameFlow: 15-step full game lifecycle
  - TestMultipleGames: Concurrent game handling
  - TestAuthenticationSecurity: Admin auth validation
  - TestErrorHandling: Error scenarios and edge cases

#### 5. Test Infrastructure
- E2E tests require running server (checked via fixture)
- Proper test isolation with separate database instances
- Comprehensive fixtures for common test scenarios
- All 60 tests pass (32 unit + 24 integration + 4 E2E)

### API Endpoints Summary

**Game Endpoints** (`/api/v1/game`):
- POST `/game/create` - Create new game
- GET `/game/{game_id}` - Get game state
- POST `/game/{game_id}/join` - Join game
- POST `/game/{game_id}/start` - Start round
- POST `/game/{game_id}/bid` - Place bid
- POST `/game/{game_id}/choose_trump` - Choose trump suit
- POST `/game/{game_id}/play` - Play card
- WebSocket `/ws/{game_id}` - Real-time updates

**History Endpoints** (`/api/v1/history`):
- GET `/history/games` - List games
- GET `/history/games/{game_id}` - Game detail
- GET `/history/games/{game_id}/snapshots/{snapshot_id}` - Snapshot
- GET `/history/games/{game_id}/replay` - Replay data
- GET `/history/stats` - Statistics

**Admin Endpoints** (`/api/v1/admin`) - Requires Basic Auth:
- GET `/admin/health` - Server health
- GET `/admin/sessions` - Active sessions
- GET `/admin/sessions/{game_id}/detail` - Session detail
- GET `/admin/database/stats` - DB stats
- POST `/admin/sessions/{game_id}/save` - Force save
- DELETE `/admin/sessions/{game_id}` - Delete session
- POST `/admin/maintenance/cleanup` - Trigger cleanup

### Testing Metrics

- **Total Tests**: 60 (32 unit + 24 integration + 4 E2E)
- **Test Coverage**: Complete API surface, game logic, persistence, WebSocket
- **Test Categories**: Unit, Integration, E2E with clear separation
- **Execution Time**: Fast (unit/integration < 5s, E2E requires running server)
- **Documentation**: Comprehensive README with examples

---

## Week 4: UX Improvements & Real-time Enhancements (In Progress)

### Objectives
Enhance user experience with better game state visibility, trick tracking, and real-time feedback.

### Changes Implemented

#### 1. Current Trick and Lead Suit Tracking
- **File**: `app/models.py` (lines 3, 73-75)
- **Changes**: Added three new fields to GameStateDTO:
  ```python
  current_trick: Optional[Dict[int, CardDTO]] = None  # seat -> card mapping
  lead_suit: Optional[str] = None  # suit to follow
  last_trick: Optional[Dict[str, Any]] = None  # {winner: int, cards: Dict[int, CardDTO]}
  ```
- **Purpose**: Enable frontend to display:
  - Cards currently being played in the trick
  - Which suit players must follow
  - The previous completed trick with winner

#### 2. Last Trick Persistence in GameSession
- **File**: `app/game/session.py` (lines 79, 138, 160-167, 412)
- **Changes**:
  - Added `self.last_trick: Optional[Tuple[int, List[Tuple[int, Card]]]] = None` field
  - Save completed trick before clearing current trick in `play_card()` method:
    ```python
    if len(self.current_trick) >= self.seats:
        winner = determine_trick_winner(...)
        pts = trick_points(self.current_trick)
        # Save the completed trick before clearing
        self.last_trick = (winner, list(self.current_trick))
        self.captured_tricks.append((winner, list(self.current_trick)))
        # ... rest of logic
    ```
  - Reset `last_trick` on new round start in `start_round()`
  - Build `last_trick_dict` in `get_public_state()` with winner and cards
- **Purpose**: Allow players to see which cards were played in the previous trick and who won it

#### 3. Current Trick and Lead Suit in Public State
- **File**: `app/game/session.py` (lines 152-167)
- **Changes**: Modified `get_public_state()` to build dictionaries:
  ```python
  # Build current_trick as dict mapping seat -> card
  current_trick_dict = None
  lead_suit = None
  if self.current_trick:
      current_trick_dict = {seat: card.to_dict() for seat, card in self.current_trick}
      lead_suit = self.current_trick[0][1].suit

  # Build last_trick with winner info
  last_trick_dict = None
  if self.last_trick:
      winner, trick_cards = self.last_trick
      last_trick_dict = {
          "winner": winner,
          "cards": {seat: card.to_dict() for seat, card in trick_cards}
      }
  ```
- **Purpose**: Convert internal data structures to frontend-friendly format

#### 4. Type Safety Fix
- **File**: `app/models.py` (line 3)
- **Fix**: Added missing `Any` import: `from typing import Any, Dict, List, Optional`
- **Problem**: Prevented backend from starting due to Pydantic schema generation error

### Frontend Integration Points

The backend now provides complete trick visibility through WebSocket state updates:
- **current_trick**: Shows cards being played right now (updates as each player plays)
- **lead_suit**: Indicates which suit must be followed (extracted from first card)
- **last_trick**: Shows completed trick with winner badge and all 4 cards

### User Experience Improvements

1. **Follow Suit Guidance**: Players can now see which suit they must play, reducing "follow suit" errors
2. **Trick History**: Last completed trick remains visible, helping players remember what was played
3. **Winner Feedback**: Clear indication of who won the previous trick
4. **Real-time Updates**: All connected clients see trick progression in real-time via WebSocket

### Technical Notes

- **Data Flow**: Backend internal `List[Tuple[int, Card]]` → DTO `Dict[int, CardDTO]` → Frontend `Record<number, Card>`
- **Memory Management**: Only last trick is stored separately (not all tricks)
- **State Transitions**: Last trick cleared on new round, current trick cleared when complete
- **WebSocket Broadcasting**: All state changes broadcast to connected clients automatically

---

## Week 5: WebSocket Session Management & Short Code Resolution (Completed)

### Objectives
Fix critical WebSocket connection bugs, enable short code support at WebSocket endpoint, and integrate with frontend session management.

### Changes Implemented

#### 1. WebSocket Short Code Resolution
- **File**: `app/api/v1/websocket.py` (lines 31-57)
- **Problem**: WebSocket endpoint `/ws/game/{game_id}` was treating short codes as literal UUID keys
- **Impact**: Connecting to `/ws/game/clever-newt-96` created a NEW empty game instead of resolving to existing game
- **Solution**: Added `_resolve_game_id_ws()` function to resolve identifiers before session lookup

```python
async def _resolve_game_id_ws(identifier: str) -> str:
    """Resolve game identifier (UUID or short code) to UUID for WebSocket."""
    # Check if it's already in memory
    if identifier in SESSIONS:
        return identifier

    # Check if any session has this short_code
    for game_id, session in SESSIONS.items():
        if session.short_code == identifier:
            return game_id

    # Check database by UUID
    async for db in get_db():
        repo = GameRepository(db)
        game = await repo.get_game(identifier)
        if game:
            return game.id

        # Check database by short code
        game = await repo.get_game_by_short_code(identifier)
        if game:
            return game.id
        break

    return identifier
```

**Resolution Order**:
1. Check in-memory sessions by UUID key
2. Check in-memory sessions by short_code attribute
3. Check database by UUID
4. Check database by short_code
5. Return original identifier if not found (will create new or fail)

#### 2. Database-backed WebSocket Connections
- **File**: `app/api/v1/websocket.py` (lines 82-95)
- **Enhancement**: WebSocket handler now loads games from database if not in memory
- **Flow**:
  ```python
  game_id = await _resolve_game_id_ws(game_id_or_code)

  async with sessions_lock:
      if game_id not in SESSIONS:
          # Try to load from database first
          sess = await load_game_from_db(game_id)
          if sess:
              SESSIONS[game_id] = sess
              logger.info("game_loaded_for_ws", game_id=game_id)
          else:
              # Create new session if not found
              SESSIONS[game_id] = GameSession(...)
              logger.info("new_game_created_for_ws", game_id=game_id)
  ```
- **Benefit**: Server restarts don't lose game state; connections restore from database

#### 3. WebSocket Endpoint Path Update
- **File**: `app/api/v1/websocket.py` (line 60)
- **Change**: Updated endpoint path to reflect dual-purpose:
  ```python
  @router.websocket("/ws/game/{game_id_or_code}")
  async def ws_game(websocket: WebSocket, game_id_or_code: str):
  ```
- **Supports**:
  - UUIDs: `ws://localhost:8000/api/v1/ws/game/ccb2e8af-aaf2-4dfe-9611-b146f6866461`
  - Short codes: `ws://localhost:8000/api/v1/ws/game/royal-turtle-65`

#### 4. Integration with Frontend Session Management
- **Purpose**: Frontend LocalStorage persistence works seamlessly with backend
- **Flow**:
  1. User joins game via REST API (receives seat + player_id)
  2. Frontend saves session to LocalStorage
  3. On page refresh, frontend restores session
  4. Frontend connects to WebSocket with short code or UUID
  5. Backend resolves identifier and loads from database if needed
  6. Frontend sends identify message with restored seat/playerId
  7. User sees their hand and can continue playing

### Bug Fix Details

#### Original Bug (Critical)
**Symptoms**:
- Tab 1 (game creator) shows all players and state correctly
- Tab 2 (player who joined) shows empty seats, no player names, LOBBY phase
- Console logs showed Tab 2 was identifying correctly but receiving wrong state

**Root Cause Investigation**:
Network logs revealed:
```json
// Tab 2 connected to: ws://localhost:18081/api/v1/ws/game/clever-newt-96
// But received state for:
{
  "game_id": "6da57fdf-61ef-4a5e-a8ab-1d65676b740d",  // Wrong UUID!
  "short_code": null,
  "players": []  // Empty!
}
```

**Why This Happened**:
```python
# Original buggy code
@router.websocket("/ws/game/{game_id}")
async def ws_game(websocket: WebSocket, game_id: str):
    # game_id = "clever-newt-96" (short code)

    if game_id not in SESSIONS:  # "clever-newt-96" not in sessions
        SESSIONS[game_id] = GameSession(...)  # Created NEW empty game!
```

The WebSocket handler was treating the short code as a literal key instead of resolving it to the actual UUID like the REST endpoints do.

**Fix Verification**:
After implementing `_resolve_game_id_ws()`, user testing confirmed:
- Tab 2 now shows all players correctly
- Both tabs receive same game state
- Page refresh works correctly
- Short codes work at WebSocket endpoint

### Technical Notes

**Short Code Resolution Performance**:
- In-memory checks are O(1) for UUID, O(n) for short code scan
- Database queries only triggered if not in memory
- Typical case: Game already loaded, UUID lookup is instant

**Race Condition Prevention**:
- `sessions_lock` ensures thread-safe session creation/loading
- Only one instance of GameSession per game_id in memory
- Database lookup happens inside lock to prevent duplicate loads

**Error Handling**:
- Invalid identifiers fall through to create new game (existing behavior)
- Database errors logged and handled gracefully
- WebSocket stays connected even if initial state send fails

**Logging**:
```python
logger.info("game_loaded_for_ws", game_id=game_id)
logger.info("new_game_created_for_ws", game_id=game_id)
```
Clear audit trail for debugging session lifecycle.

### Integration with Frontend

**Frontend Session Flow**:
1. User enters game via URL: `/game/royal-turtle-65`
2. Frontend checks LocalStorage for existing session
3. If found, restores seat/playerId from LocalStorage
4. WebSocket connects to: `ws://localhost:18081/api/v1/ws/game/royal-turtle-65`
5. Backend resolves "royal-turtle-65" → actual UUID
6. Backend loads game from database or uses in-memory session
7. Frontend sends identify message with restored seat/playerId
8. Backend sends state with owner_hand for that seat
9. User sees their cards and can play

**Session Expiry**:
- Frontend: 24-hour LocalStorage expiry with cleanup
- Backend: No session expiry on WebSocket (connection-based)
- Database: Cleanup task removes old games (configurable timeouts)

### Files Modified

- `/Users/kodiak/workspace/experiments/thurup/backend/app/api/v1/websocket.py`:
  - Added `_resolve_game_id_ws()` function (lines 31-57)
  - Updated endpoint path parameter name (line 60)
  - Added resolution call before session check (line 80)
  - Added database loading before creating new session (lines 82-95)

### User Experience Impact

**Before Fix**:
- Sharing game URLs resulted in empty game state
- Only the game creator could see players
- Refreshing page lost all state

**After Fix**:
- Short code URLs work perfectly at WebSocket endpoint
- All players see consistent game state
- Page refresh preserves session via LocalStorage
- Database persistence enables server restart recovery

---

## Week 6: Round History Persistence & Admin UI Enhancements (Completed)

### Objectives
Implement comprehensive round history tracking with database persistence, enhance admin panel with game history browsing, and improve data integrity for player persistence.

### Changes Implemented

#### 1. Round History Database Schema
- **File**: `alembic/versions/[migration_id]_add_round_history_table.py`
- **New Table**: `round_history`
  ```sql
  CREATE TABLE round_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      game_id VARCHAR(36) NOT NULL REFERENCES games(id) ON DELETE CASCADE,
      round_number INTEGER NOT NULL,
      dealer INTEGER NOT NULL,
      bid_winner INTEGER,
      bid_value INTEGER,
      trump VARCHAR(10),
      round_data TEXT NOT NULL,  -- Complete round snapshot as JSON
      created_at DATETIME NOT NULL
  );
  CREATE INDEX ix_round_history_game_id ON round_history(game_id);
  ```
- **Purpose**: Store complete history of every round played, including:
  - Dealer position and bid information
  - Trump suit for the round
  - All captured tricks with cards and points
  - Team scores and points by seat
  - Complete round data for replay/analysis

#### 2. Round History Repository
- **File**: `app/db/repository.py` (RoundHistoryRepository class)
- **Methods**:
  - `save_round()`: Save complete round data to database
  - `get_rounds_for_game()`: Retrieve all rounds for a game
  - `get_round_count()`: Count saved rounds (prevents duplicate saves)
- **Data Structure**: Each round saves:
  ```python
  {
      "round_number": 1,
      "dealer": 0,
      "bid_winner": 2,
      "bid_value": 15,
      "trump": "♠",
      "captured_tricks": [
          {
              "winner": 2,
              "cards": [{"seat": 0, "card": {...}}, ...],
              "points": 11
          },
          ...
      ],
      "points_by_seat": {0: 3, 1: 8, 2: 11, 3: 0},
      "team_scores": {"team_points": [11, 11], "bid_made": true}
  }
  ```

#### 3. Real-time Round Persistence in GameSession
- **File**: `app/game/session.py` (lines 510-541)
- **Critical Fix**: Rounds now save immediately when completed (SCORING state)
- **Previous Bug**: Rounds were only saved when starting the NEXT round, causing:
  - First/only round never being saved
  - Loss of data if game ended after one round
- **Solution**: Modified `play_card()` method to save round data when all hands are empty:
  ```python
  if all(len(h) == 0 for h in self.hands):
      self.state = SessionState.SCORING
      # Save completed round to history immediately
      round_data = {
          "round_number": len(self.rounds_history) + 1,
          "dealer": self.leader,
          "bid_winner": self.bid_winner,
          "bid_value": self.bid_value,
          "trump": self.trump,
          "captured_tricks": [...],
          "points_by_seat": dict(self.points_by_seat),
          "team_scores": self.compute_scores(),
      }
      self.rounds_history.append(round_data)
      logger.info("round_completed_and_saved", ...)
  ```
- **New Field**: Added `self.rounds_history: List[Dict[str, Any]] = []` to track all completed rounds in memory

#### 4. Persistence Layer Integration
- **File**: `app/db/persistence.py` (lines 94-109)
- **Enhancement**: `save_session()` now persists rounds to database
- **Logic**: Incremental save to prevent duplicates:
  ```python
  # Get count of rounds already saved
  saved_rounds_count = await self.round_history_repo.get_round_count(session.id)
  # Save any new rounds from session.rounds_history
  for round_data in session.rounds_history[saved_rounds_count:]:
      await self.round_history_repo.save_round(
          game_id=session.id,
          round_number=round_data["round_number"],
          dealer=round_data["dealer"],
          bid_winner=round_data.get("bid_winner"),
          bid_value=round_data.get("bid_value"),
          trump=round_data.get("trump"),
          round_data=round_data,  # Complete round data
      )
  ```
- **Automatic Saves**: Rounds persist to database after:
  - Every card play (through auto-save mechanism)
  - Manual "Save" button in admin panel
  - Game state transitions

#### 5. Admin API Enhancements
- **File**: `app/api/v1/admin.py`
- **New Endpoints**:
  - `GET /api/v1/admin/history/games` - List all games with metadata
  - `GET /api/v1/admin/history/games/{game_id}/rounds` - Get rounds with full details
- **Response Models**:
  ```python
  class GameSummary(BaseModel):
      game_id: str
      short_code: Optional[str]
      mode: str
      seats: int
      state: str
      rounds_played: int
      player_names: List[str]  # Extracted from players table
      created_at: datetime
      last_activity_at: datetime

  class GameWithRounds(BaseModel):
      game_id: str
      short_code: Optional[str]
      mode: str
      state: str
      total_rounds: int
      players: List[PlayerInfo]
      rounds: List[RoundDetail]  # Full round data with tricks
      created_at: datetime
  ```
- **Short Code Support**: Updated `SessionInfo` model to include `short_code` field (line 64-75)
- **Display**: Admin panel now shows short codes instead of UUIDs throughout

#### 6. Critical Player Persistence Bug Fix
- **File**: `app/db/persistence.py` (lines 69-83)
- **Original Bug**: Players were ONLY saved when creating new games, not on updates
- **Impact**: Games created before players joined had empty players tables forever
- **Symptoms**:
  - Admin history showed `"players": []` for existing games
  - Round history couldn't show player names (only "Seat #")
  - Frontend received empty player arrays
- **Root Cause**:
  ```python
  # BUGGY CODE - players only saved in else block
  if existing_game:
      # Update existing game (NO PLAYER SAVE!)
      await self.game_repo.update_game_state(...)
  else:
      # Create new game
      await self.game_repo.create_game(...)
      # Add players here (ONLY on first save!)
      for seat, player in session.players.items():
          await self.player_repo.add_player(...)
  ```
- **Fix**: Moved player-saving logic outside if/else block:
  ```python
  if existing_game:
      await self.game_repo.update_game_state(...)
  else:
      await self.game_repo.create_game(...)

  # Sync players (create/update) - do this on EVERY save
  existing_players = await self.player_repo.get_players_for_game(session.id)
  existing_player_seats = {p.seat for p in existing_players}

  # Add any new players that aren't in the database yet
  for seat, player in session.players.items():
      if seat not in existing_player_seats:
          await self.player_repo.add_player(...)
  ```
- **Result**: Players now persist correctly on every game save, enabling proper name display

#### 7. Frontend Round History UI (AdminGameHistoryPage)
- **File**: `frontend/src/pages/AdminGameHistoryPage.tsx`
- **Features**:
  - **Game List View**: Shows all games with metadata, player names, state badges
  - **Game Detail View**: Displays complete game info with round-by-round breakdown
  - **Round Cards**: Each round shows:
    - Dealer name, bid winner, bid value, trump suit
    - Team scores for both teams
    - All captured tricks with cards played
    - Trick winner with points earned
    - Player names instead of seat numbers (lines 60-63)
  - **Defensive Programming**: Handles both string names and player objects (lines 289-302):
    ```typescript
    const playerName = typeof nameOrPlayer === 'string'
        ? nameOrPlayer
        : nameOrPlayer.name;
    ```
- **Navigation**: "View Rounds" button on each game, back navigation
- **Styling**: Consistent with admin dashboard, uses Card and Badge components

#### 8. Multiple Rounds Support
- **File**: `frontend/src/pages/GamePage.tsx` (lines 332-346)
- **Enhancement**: Added "Start Next Round" button during SCORING phase
- **Flow**:
  1. Round completes → state transitions to SCORING
  2. Scores displayed to all players
  3. "Start Next Round" button appears
  4. Clicking button calls `/game/{game_id}/start` endpoint
  5. Backend calls `session.start_round()` → new round begins
  6. Previous round data remains in `rounds_history` and database
- **User Experience**: Enables playing multiple rounds in same game session without recreating game

#### 9. Admin Panel Navigation Fix
- **File**: `frontend/src/pages/AdminPage.tsx`
- **Bug**: `ReferenceError: navigate is not defined` when clicking "Game History" button
- **Cause**: `useNavigate()` hook was only in parent `AdminPage`, not child `AdminDashboard`
- **Fix**: Added `const navigate = useNavigate();` at line 97 in `AdminDashboard` component
- **Enhancement**: Updated session list to show short codes (lines 348-350)

### Bug Fixes

#### Bug #1: Empty Round History
- **Reported**: "I played 2 games, both show up empty" in game history
- **Investigation**: Database query showed 0 rounds despite games being played
- **Root Cause**: Rounds only saved when starting NEXT round (in `start_round()`), not when completing current round
- **Impact**: First/only round never persisted to database
- **Fix**: Save round data immediately in `play_card()` when transitioning to SCORING state
- **Verification**: User confirmed rounds now appear in admin history after playing

#### Bug #2: Player Names Not Displaying
- **Reported**: "Player names are still not shown only seat #" in round details
- **Investigation**: Console logs showed `players: []` - empty array in API response
- **Root Cause**: Players only saved during initial game creation (inside `else` block)
- **Impact**:
  - All existing games had empty players tables
  - Round history couldn't resolve seat numbers to names
  - Frontend displayed "Seat 0", "Seat 1" instead of actual names
- **Debug Process**:
  1. Added console logging to `getPlayerName()` helper
  2. User provided logs showing empty players array
  3. Traced API call chain: frontend → admin endpoint → repository → database
  4. Found players were never inserted for existing games
- **Fix**: Moved player persistence outside if/else block to run on every save
- **Side Effect**: Exposed new bug where API returned player objects instead of strings
- **Additional Fix**: Added defensive type checking in frontend to handle both formats

#### Bug #3: React Rendering Error
- **Reported**: "Objects are not valid as a React child" after player persistence fix
- **Symptom**: Error when rendering player names in game list
- **Root Cause**: After fixing player persistence, API started returning player objects with all fields
- **Frontend Expected**: Array of strings (player names)
- **Backend Returned**: Array of objects `{player_id, name, seat, is_bot, joined_at}`
- **Fix**: Updated frontend to handle both formats:
  ```typescript
  {game.player_names.map((nameOrPlayer: any, i: number) => {
    const playerName = typeof nameOrPlayer === 'string'
      ? nameOrPlayer
      : nameOrPlayer.name;
    return <span key={i}>{playerName}</span>;
  })}
  ```
- **Result**: Frontend resilient to API response format changes

### Data Integrity Improvements

1. **Incremental Round Saves**: Only new rounds saved to database (prevents duplicates)
2. **Player Deduplication**: Check existing players before inserting (prevents duplicate seats)
3. **Foreign Key Constraints**: CASCADE delete ensures orphaned records cleaned up
4. **Transaction Safety**: All persistence operations wrapped in try/catch with rollback
5. **Timestamp Tracking**: All records have creation timestamps for audit trail

### User Experience Improvements

1. **Complete Game History**: Browse all games ever played with full round details
2. **Player Name Display**: See actual player names throughout history (not "Seat #")
3. **Short Code Display**: Easier identification with short codes instead of UUIDs
4. **Round-by-Round Playback**: View complete trick history for analysis
5. **Multiple Rounds**: Play continuous games without recreating sessions
6. **Persistent State**: Games survive page refreshes and server restarts

### Testing & Verification

**Manual Testing by User**:
- Created and played 2-round game
- Verified rounds appear in admin history
- Confirmed player names display correctly
- Tested page refresh maintains session
- Verified "Start Next Round" button works

**Database Verification**:
```sql
-- User confirmed database contains correct data:
SELECT COUNT(*) FROM round_history WHERE game_id = '...';
-- Result: 2 rounds saved

SELECT * FROM players WHERE game_id = '...';
-- Result: 4 players with correct names and seats
```

### Technical Notes

**Round Save Timing**:
- Rounds save immediately when last card played (transition to SCORING)
- Auto-save mechanism triggers after every game action
- Manual "Save" button in admin also persists pending rounds

**Memory vs Database**:
- `GameSession.rounds_history` keeps rounds in memory for current session
- `RoundHistoryRepository` persists to database for historical queries
- On load, rounds restore from database (not from snapshots)

**Performance Considerations**:
- Round data includes full trick history (can be large for 56-mode games)
- JSON serialization for flexible schema evolution
- Indexed by game_id for fast queries
- Pagination recommended for games with many rounds

**Data Model Design**:
- Separate `round_history` table (not embedded in snapshots)
- Enables efficient queries: "Show me all games where player X won bidding"
- Complete round_data JSON preserves all context for future features
- Normalized player data prevents redundancy

### Files Modified

**Backend**:
- `app/db/models.py` - Added RoundHistoryModel
- `app/db/repository.py` - Added RoundHistoryRepository (3 methods)
- `app/db/persistence.py` - Lines 94-109 (round saving), lines 69-83 (player fix)
- `app/game/session.py` - Lines 79 (rounds_history field), lines 510-541 (round save logic)
- `app/api/v1/admin.py` - Added 2 history endpoints, updated SessionInfo model
- `alembic/versions/` - New migration for round_history table

**Frontend**:
- `frontend/src/pages/AdminGameHistoryPage.tsx` - New page with game list and round detail views
- `frontend/src/pages/AdminPage.tsx` - Line 97 (navigation fix), lines 348-350 (short codes)
- `frontend/src/pages/GamePage.tsx` - Lines 332-346 (Start Next Round button)
- `frontend/src/api/admin.ts` - Added 2 new API functions

### User Impact

**Before This Week**:
- No way to view game history or past rounds
- Player names not saved to database reliably
- Could only play single rounds
- Admin panel showed confusing UUIDs

**After This Week**:
- Complete browsable game history with round-by-round details
- All player information persists correctly
- Multi-round gameplay supported with UI
- User-friendly short codes throughout admin interface
- Full audit trail for every game and round played

---

## Week 7: Critical Bug Fixes - Dealer Rotation & Multiplayer Hands (Completed)

### Objectives
Fix two critical bugs preventing correct gameplay: incorrect dealer rotation logic and multiplayer players unable to see their hands.

### Changes Implemented

#### Bug #1: Multiplayer Hand Not Visible (CRITICAL - Fixed)

**Problem**: Only the first player could see their hand. Players 2, 3, and 4 couldn't see the "Your Hand" section.

**Root Cause**: WebSocket connected BEFORE Player 2 joined the game through UI. At connection time, `seat` and `playerId` were `null`, so the hook sent `request_state` instead of `identify`. When Player 2 later joined, the WebSocket didn't re-send the identify message, leaving backend with `seat=None`.

**Fix Location**: Frontend only - `frontend/src/hooks/useGame.ts:101-112`

**Solution**: Added reactive `useEffect` that re-identifies when seat/playerId changes while WebSocket is connected.

#### Bug #2: Incorrect Dealer Rotation (HIGH - Fixed)

**Problem**:
1. Leader incorrectly set to dealer (should be player to dealer's right)
2. No automatic dealer rotation between rounds
3. Dealer badge displayed on wrong seat

**Root Cause Analysis**:
Verified against official 28 card game rules (Pagat.com):
- Direction of play: Counter-clockwise
- First bidder/player: Player to dealer's RIGHT (next counter-clockwise)
- Dealer rotation: Follows direction of play (counter-clockwise)

**Backend Changes**:

1. **Added `current_dealer` field** (`app/game/session.py:78`):
   ```python
   self.current_dealer: int = 0  # tracks dealer position, rotates counter-clockwise
   self.leader: int = 0  # seat index of player to dealer's right (first to bid/play)
   ```

2. **Fixed leader calculation** (`app/game/session.py:174`):
   ```python
   # OLD (WRONG): self.leader = dealer % self.seats
   # NEW (CORRECT):
   self.leader = (self.current_dealer + 1) % self.seats
   ```
   Leader is now correctly set to player to dealer's RIGHT (next counter-clockwise).

3. **Added automatic dealer rotation** (`app/game/session.py:153-160`):
   ```python
   # Rotate dealer counter-clockwise for next round
   # In counter-clockwise games, next dealer is to the right (subtract 1)
   self.current_dealer = (self.current_dealer - 1) % self.seats
   logger.info("dealer_rotated", game_id=self.id, new_dealer=self.current_dealer)
   ```
   Dealer now rotates automatically after each round.

4. **Updated GameStateDTO** (`app/models.py:64-65`):
   ```python
   dealer: int  # current dealer position
   leader: int  # player to dealer's right (first to bid/play)
   ```
   Added `dealer` field to expose dealer position to frontend.

5. **Updated `get_public_state()`** (`app/game/session.py:235`):
   ```python
   dto = GameStateDTO(
       ...
       dealer=self.current_dealer,
       leader=self.leader,
       ...
   )
   ```

**Frontend Changes**:

1. **Updated GameState type** (`frontend/src/types/game.ts:42-43`):
   ```typescript
   dealer: number; // Current dealer position
   leader: number; // Player to dealer's right (first to bid/play)
   ```

2. **Updated GameBoard** (`frontend/src/components/game/GameBoard.tsx:16,47,54`):
   - Extract `dealer` from gameState
   - Use `dealer` instead of `leader` for "Dealer" badge
   - Updated `useMemo` dependencies to include `dealer`

### How Dealer Rotation Works Now

**Round 1** (4-player game):
- Dealer = Seat 0
- Leader = Seat 1 (dealer's RIGHT, first to bid)
- Bidding order: 1 → 2 → 3 → 0 (counter-clockwise)

**Round 2** (after round 1 completes):
- Dealer rotates to Seat 3: `(0 - 1) % 4 = 3`
- Leader = Seat 0: `(3 + 1) % 4 = 0`
- Bidding order: 0 → 1 → 2 → 3

**Round 3**:
- Dealer = Seat 2: `(3 - 1) % 4 = 2`
- Leader = Seat 3: `(2 + 1) % 4 = 3`
- Bidding order: 3 → 0 → 1 → 2

**Round 4**:
- Dealer = Seat 1: `(2 - 1) % 4 = 1`
- Leader = Seat 2: `(1 + 1) % 4 = 2`
- Bidding order: 2 → 3 → 0 → 1

After 4 rounds, dealer returns to Seat 0 (full circle).

### Files Modified

**Bug #1 - Multiplayer Hands**:
- `frontend/src/hooks/useGame.ts:101-112` - Added re-identification effect

**Bug #2 - Dealer Rotation**:
- `backend/app/game/session.py:78` - Added current_dealer field
- `backend/app/game/session.py:153-160` - Dealer rotation logic
- `backend/app/game/session.py:174` - Fixed leader calculation
- `backend/app/models.py:64` - Added dealer to GameStateDTO
- `backend/app/game/session.py:235` - Included dealer in public state
- `frontend/src/types/game.ts:42-43` - Added dealer to GameState type
- `frontend/src/components/game/GameBoard.tsx:16,47,54` - Use dealer for badge

### Testing & Verification

**Bug #1**: Tested with 2+ players in separate browsers. All players now see their hands correctly.

**Bug #2**: Tested through 4 complete rounds. Verified:
- Dealer badge moves counter-clockwise each round
- First bidder is always to dealer's right
- After 4 rounds, dealer returns to original seat

Backend logs confirm correct rotation:
```
dealer_rotated ... new_dealer=3
round_started ... dealer=3 leader=0
```

### Impact

**Before Fixes**:
- Game unplayable for non-creator players (couldn't see hands)
- Incorrect dealer rotation violated official 28 card game rules
- Bidding order was wrong

**After Fixes**:
- All players can see their hands and play normally
- Game follows official 28 card game rules for dealer rotation
- Correct bidding/playing order every round

### Documentation Updates

- Updated `docs/KNOWN_BUGS.md` - Marked Bug #1 and Bug #2 as 🟢 Fixed
- Added detailed root cause analysis and fix documentation
- Included code changes and testing verification

---

_Last Updated: 2025-10-15 (Week 7 - Critical Bug Fixes: Dealer Rotation & Multiplayer Hands)_
