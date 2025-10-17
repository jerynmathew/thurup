# API v1 Package Structure

Refactored from monolithic `v1.py` into a well-organized package with separation of concerns.

## Structure

```
app/api/v1/
├── __init__.py                # Package initialization, exports main router
├── README.md                  # This file
├── router.py                  # Main router and shared state (sessions, connections, locks)
├── broadcast.py               # Broadcasting utilities for state updates
├── bot_runner.py              # Bot AI automation logic
├── rest.py                    # REST HTTP endpoints
├── websocket.py               # WebSocket handler
├── connection_manager.py      # WebSocket connection lifecycle management
├── persistence_integration.py # Database save/load/restore integration
└── history.py                 # Game history and replay endpoints
```

## Module Descriptions

### `router.py`
**Purpose**: Centralized shared state and main router

**Exports**:
- `router` - FastAPI APIRouter instance (prefix: `/api/v1`)
- `SESSIONS` - In-memory game sessions store
- `WS_CONNECTIONS` - WebSocket connection registry
- `sessions_lock` - asyncio.Lock for session access
- `ws_connections_lock` - asyncio.Lock for WS connections
- `bot_tasks` - Registry of running bot tasks

**Usage**:
```python
from app.api.v1 import router  # Import in main.py
from app.api.v1.router import SESSIONS  # Access state in other modules
```

### `broadcast.py`
**Purpose**: Broadcasting game state to connected clients

**Functions**:
- `broadcast_state(game_id)` - Send state updates to all WebSocket clients

**Features**:
- Per-socket hand information (only for identified players)
- Graceful handling of disconnected sockets
- Automatic cleanup of failed connections

### `bot_runner.py`
**Purpose**: Automated bot decision-making and action execution

**Functions**:
- `schedule_bot_runner(game_id)` - Schedule bot task (prevents duplicates)
- `run_bots_for_game(game_id)` - Main bot loop handler

**Phase Handlers** (internal):
- `_handle_bidding_bot()` - Bot actions in BIDDING phase
- `_handle_choose_trump_bot()` - Bot actions in CHOOSE_TRUMP phase
- `_handle_play_bot()` - Bot actions in PLAY phase

**Features**:
- Sequential turn-based bot execution
- Configurable delay between actions
- Max cycle limit to prevent infinite loops
- Automatic cleanup of completed tasks

### `rest.py`
**Purpose**: REST HTTP endpoints for game management

**Endpoints**:
- `POST /api/v1/game/create` - Create new game
- `POST /api/v1/game/{game_id}/join` - Join game
- `POST /api/v1/game/{game_id}/start` - Start game round
- `POST /api/v1/game/{game_id}/bid` - Place bid
- `POST /api/v1/game/{game_id}/choose_trump` - Choose trump suit
- `POST /api/v1/game/{game_id}/play` - Play card

**Features**:
- Input validation with Pydantic models
- Automatic game start when lobby is full
- Bot runner scheduling after actions
- State broadcasting after changes

### `websocket.py`
**Purpose**: Real-time WebSocket communication

**Endpoint**:
- `WS /api/v1/ws/game/{game_id}` - WebSocket connection

**Message Types** (client → server):
- `identify` - Associate socket with player seat
- `request_state` - Request current game state
- `place_bid` - Place bid action
- `choose_trump` - Choose trump action
- `play_card` - Play card action

**Response Types** (server → client):
- `state_snapshot` - Full game state (with owner_hand if identified)
- `action_ok` - Action succeeded
- `action_failed` - Action rejected (with reason)
- `error` - Error occurred

**Features**:
- Automatic session creation if needed
- Connection lifecycle management
- Per-socket seat identification
- Graceful error handling and cleanup

### `connection_manager.py`
**Purpose**: WebSocket connection tracking and presence management

**Classes**:
- `ConnectionInfo` - Tracks individual connection details (seat, timestamps, activity)
- `ConnectionManager` - Manages all connections across games

**Key Methods**:
- `register(websocket, game_id, seat)` - Register new connection
- `identify(websocket, seat)` - Associate connection with player seat
- `unregister(websocket)` - Clean up on disconnect
- `get_present_seats(game_id)` - Get list of connected seats
- `is_player_connected(game_id, seat)` - Check player presence

**Features**:
- Activity timestamp tracking
- Idle connection detection
- Player presence tracking per game
- Integration with legacy WS_CONNECTIONS

### `persistence_integration.py`
**Purpose**: Database persistence integration for game sessions

**Functions**:
- `save_game_state(game_id, reason)` - Save session to database
- `load_game_from_db(game_id)` - Load session from database
- `restore_active_games()` - Restore all active games on startup
- `delete_game_from_db(game_id)` - Delete game and all related data

**Features**:
- Automatic save on all game actions
- Snapshot reasons for tracking (bid, trump, play, scoring)
- Server restart recovery
- Structured logging of persistence operations

### `history.py`
**Purpose**: Game history querying and replay functionality

**Endpoints**:
- `GET /api/v1/history/games` - List games with filters (state, mode, pagination)
- `GET /api/v1/history/games/{game_id}` - Get detailed game info with snapshots
- `GET /api/v1/history/games/{game_id}/snapshots/{snapshot_id}` - Get specific snapshot data
- `GET /api/v1/history/games/{game_id}/replay` - Get full game replay with all snapshots
- `GET /api/v1/history/stats` - Get overall statistics (total games, players, bots)

**Response Models**:
- `GameSummary` - Game metadata with players
- `GameDetail` - Detailed game with snapshot list
- `SnapshotSummary` - Snapshot metadata
- `GameHistoryStats` - Aggregate statistics

**Features**:
- Filter by game state (active/completed/abandoned)
- Filter by game mode (28/56)
- Pagination support
- Chronological replay functionality
- Complete snapshot data retrieval

## Dependencies Between Modules

```
router.py (core state)
    ↑
    ├── broadcast.py (uses SESSIONS, WS_CONNECTIONS, locks)
    ├── bot_runner.py (uses SESSIONS, bot_tasks, broadcasts)
    ├── rest.py (uses SESSIONS, WS_CONNECTIONS, router decorator)
    ├── websocket.py (uses all of the above + connection_manager)
    ├── connection_manager.py (uses WS_CONNECTIONS, ws_connections_lock)
    ├── persistence_integration.py (uses SESSIONS, sessions_lock, database)
    └── history.py (uses router decorator, database for queries)
```

## Shared State Management

### Sessions
```python
SESSIONS: Dict[str, GameSession]
```
Thread-safe access via `sessions_lock`

### WebSocket Connections
```python
WS_CONNECTIONS: Dict[str, Dict[WebSocket, Optional[int]]]
```
Structure: `game_id → (websocket → seat_or_none)`
Thread-safe access via `ws_connections_lock`

### Bot Tasks
```python
bot_tasks: Dict[str, asyncio.Task]
```
Ensures only one bot runner per game at a time

## Usage Examples

### Adding a New REST Endpoint
```python
# In rest.py
from app.api.v1.router import router, SESSIONS

@router.post("/game/{game_id}/custom_action")
async def custom_action(game_id: str, data: CustomRequest):
    sess = SESSIONS.get(game_id)
    if not sess:
        raise HTTPException(404, "Game not found")
    # ... your logic
    await broadcast_state(game_id)
    return {"ok": True}
```

### Adding a New WebSocket Message Type
```python
# In websocket.py
async def _handle_ws_message(websocket, game_id, data):
    typ = data.get("type")
    # ... existing types ...
    elif typ == "new_action":
        await _handle_new_action(websocket, sess, payload)
```

### Broadcasting Custom Events
```python
from app.api.v1.broadcast import broadcast_state

# After modifying game state
await broadcast_state(game_id)
```

## Testing

All endpoints and functionality are covered by existing tests in `tests/`:
- `test_bidding.py` - Bidding logic
- `test_phase1_fixes.py` - REST endpoint integration
- `test_persistence.py` - Database integration
- etc.

Run tests:
```bash
uv run pytest tests/ -v
```

## Migration Notes

The refactoring maintains 100% backward compatibility:
- All endpoints unchanged
- All WebSocket message formats unchanged
- Shared state behavior identical
- All 32 tests pass without modification

**Changes**:
- Import in `main.py` remains: `from app.api.v1 import router`
- Internal structure improved for maintainability
- Better separation of REST, WebSocket, and bot logic
