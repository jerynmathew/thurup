# Thurup - System Architecture

This document provides a comprehensive overview of the Thurup card game system architecture, covering both backend and frontend implementations.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [API Design](#api-design)
5. [Data Flow](#data-flow)
6. [Database Schema](#database-schema)
7. [WebSocket Protocol](#websocket-protocol)
8. [Deployment Architecture](#deployment-architecture)

---

## System Overview

Thurup is a real-time multiplayer card game (28/56 variant) built with:
- **Backend**: FastAPI with WebSocket support, SQLite persistence, async/await
- **Frontend**: React 18 + TypeScript + Vite with Zustand state management
- **Communication**: REST API for game actions, WebSocket for real-time updates
- **Deployment**: Docker containerization with docker-compose orchestration

### Key Features

- Real-time multiplayer gameplay (4-6 players)
- Bot AI opponents with configurable difficulty
- Game state persistence and recovery
- Game history and replay system
- Admin dashboard with server management
- Comprehensive error handling and logging

---

## Backend Architecture

### Technology Stack

- **Framework**: FastAPI 0.115.0+
- **Database**: SQLite with async support (aiosqlite)
- **ORM**: SQLModel 0.0.22 (SQLAlchemy + Pydantic)
- **Migrations**: Alembic 1.14.0
- **Logging**: Structlog 24.4.0
- **Testing**: Pytest 8.4.0 with pytest-asyncio
- **Code Quality**: Ruff 0.8.0, Black 24.0.0

### Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── constants.py            # Game constants and configuration
│   ├── models.py               # Pydantic API models
│   ├── logging_config.py       # Structured logging setup
│   ├── middleware.py           # Request ID tracking
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # API router aggregation
│   │       ├── game.py         # Game REST endpoints
│   │       ├── history.py      # History/replay endpoints
│   │       └── admin.py        # Admin endpoints (with auth)
│   │
│   ├── game/
│   │   ├── session.py          # GameSession state machine
│   │   ├── rules.py            # Card game rules and logic
│   │   ├── ai.py               # Bot AI decision-making
│   │   └── connection_manager.py  # WebSocket connection handling
│   │
│   └── db/
│       ├── models.py           # SQLModel table definitions
│       ├── config.py           # Database configuration
│       ├── repository.py       # Data access repositories
│       ├── persistence.py      # Session serialization
│       └── cleanup.py          # Background cleanup task
│
├── tests/
│   ├── unit/                   # 32 unit tests
│   ├── integration/            # 24 integration tests
│   ├── e2e/                    # 4 E2E test classes
│   └── README.md               # Testing documentation
│
├── alembic/                    # Database migrations
├── pyproject.toml              # Dependencies and project config
└── CLAUDE.md                   # Development log
```

### Core Components

#### 1. FastAPI Application (`app/main.py`)

- Lifespan context manager for startup/shutdown
- Mounts API routers (game, history, admin)
- Initializes database and background tasks
- Handles CORS configuration
- Request ID middleware

#### 2. Game Session (`app/game/session.py`)

The GameSession class is the core game engine:

```python
class GameSession:
    # State machine with phases:
    # - LOBBY: Waiting for players
    # - BIDDING: Players bidding
    # - TRUMP_CHOICE: Winner chooses trump
    # - PLAYING: Trick-taking gameplay
    # - ROUND_END: Round completed
    # - GAME_END: Game completed

    async def place_bid(seat, value)
    async def choose_trump(seat, suit)
    async def play_card(seat, card_id)
    async def add_bot(name)
    async def start_round(dealer)
```

**Key Features**:
- Thread-safe with `asyncio.Lock`
- State machine pattern for game phases
- Automatic bot AI integration
- Complete state serialization for persistence
- Event-driven architecture (broadcasts state changes)

#### 3. Connection Manager (`app/game/connection_manager.py`)

Manages WebSocket connections per game:

```python
class ConnectionManager:
    # Tracks active WebSocket connections
    # Handles identification (seat assignment)
    # Broadcasts state updates to all clients
    # Manages disconnection/reconnection

    async def connect(websocket, game_id)
    async def disconnect(websocket, game_id)
    async def identify(websocket, game_id, seat, player_id)
    async def broadcast_state(game_id, state)
```

#### 4. Database Layer

**Repository Pattern** (`app/db/repository.py`):
- `GameRepository`: CRUD operations for games
- `PlayerRepository`: Manage players in games
- `SnapshotRepository`: Game state snapshots

**Persistence** (`app/db/persistence.py`):
- Serializes complete game state to JSON
- Stores snapshots for history/replay
- Enables game recovery after restarts

**Models** (`app/db/models.py`):
- `GameModel`: Game metadata and configuration
- `PlayerModel`: Player information with seat assignments
- `GameStateSnapshotModel`: Complete state snapshots

#### 5. API Endpoints

**Game API** (`app/api/v1/game.py`):
- POST `/game/create` - Create new game
- GET `/game/{game_id}` - Get game state
- POST `/game/{game_id}/join` - Join game
- POST `/game/{game_id}/start` - Start round
- POST `/game/{game_id}/bid` - Place bid
- POST `/game/{game_id}/choose_trump` - Choose trump
- POST `/game/{game_id}/play` - Play card
- WebSocket `/ws/{game_id}` - Real-time updates

**History API** (`app/api/v1/history.py`):
- GET `/history/games` - List games with filters
- GET `/history/games/{game_id}` - Game detail with snapshots
- GET `/history/games/{game_id}/snapshots/{id}` - Specific snapshot
- GET `/history/games/{game_id}/replay` - Replay data
- GET `/history/stats` - Game statistics

**Admin API** (`app/api/v1/admin.py`) - HTTP Basic Auth:
- GET `/admin/health` - Server health metrics
- GET `/admin/sessions` - Active sessions
- GET `/admin/database/stats` - DB statistics
- POST `/admin/sessions/{game_id}/save` - Force save
- DELETE `/admin/sessions/{game_id}` - Delete session
- POST `/admin/maintenance/cleanup` - Trigger cleanup

### Design Patterns

1. **Repository Pattern**: Clean separation of data access logic
2. **Dependency Injection**: FastAPI's dependency system for DB sessions
3. **State Machine**: GameSession phase transitions
4. **Observer Pattern**: WebSocket broadcasts for state changes
5. **Serialization**: JSON-based state persistence
6. **Background Tasks**: Periodic cleanup of old games

### Async Architecture

All I/O operations use async/await:
- Database queries (`asyncio` + `aiosqlite`)
- WebSocket communication (`starlette.websockets`)
- Game state mutations (async locks for thread safety)
- Background tasks (`asyncio.create_task`)

---

## Frontend Architecture

### Technology Stack

- **Framework**: React 18 + TypeScript + Vite
- **State Management**: Zustand 5.0.8
- **Styling**: TailwindCSS 4.1.14
- **HTTP Client**: Axios 1.12.2
- **Routing**: React Router 7.9.4
- **Icons**: Lucide React 0.545.0
- **Utilities**: clsx 2.1.1

### Directory Structure

```
frontend/
├── src/
│   ├── main.tsx                # Application entry point
│   ├── App.tsx                 # Root component with router
│   ├── router.tsx              # Route definitions
│   │
│   ├── types/
│   │   ├── game.ts             # Game state types
│   │   ├── websocket.ts        # WebSocket message types
│   │   ├── api.ts              # API response types
│   │   └── index.ts            # Type exports
│   │
│   ├── stores/
│   │   ├── gameStore.ts        # Game state management
│   │   ├── uiStore.ts          # UI state (toasts, modals)
│   │   ├── authStore.ts        # Admin authentication
│   │   └── index.ts            # Store exports
│   │
│   ├── api/
│   │   ├── client.ts           # Axios instance & interceptors
│   │   ├── game.ts             # Game API methods
│   │   ├── history.ts          # History API methods
│   │   ├── admin.ts            # Admin API methods
│   │   └── index.ts            # API exports
│   │
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   │   ├── Button.tsx      # Button with variants
│   │   │   ├── Card.tsx        # Card container
│   │   │   ├── Input.tsx       # Form input
│   │   │   ├── Select.tsx      # Dropdown select
│   │   │   ├── Modal.tsx       # Modal dialog
│   │   │   ├── Spinner.tsx     # Loading spinner
│   │   │   ├── Badge.tsx       # Status badge
│   │   │   └── index.ts        # UI exports
│   │   │
│   │   ├── game/               # Game-specific components (planned)
│   │   │   ├── GameBoard.tsx   # Main game board layout
│   │   │   ├── PlayerHand.tsx  # Player's card hand
│   │   │   ├── Trick.tsx       # Current trick display
│   │   │   ├── BiddingPanel.tsx # Bidding interface
│   │   │   └── TrumpDisplay.tsx # Trump suit indicator
│   │   │
│   │   └── layout/             # Layout components (planned)
│   │       ├── Header.tsx
│   │       └── Footer.tsx
│   │
│   ├── pages/
│   │   ├── HomePage.tsx        # Game creation/lobby
│   │   ├── GamePage.tsx        # Active game view
│   │   ├── HistoryPage.tsx     # Game history browser
│   │   ├── ReplayPage.tsx      # Game replay viewer
│   │   ├── AdminPage.tsx       # Admin dashboard
│   │   └── NotFoundPage.tsx    # 404 page
│   │
│   ├── hooks/
│   │   ├── useGameSocket.ts    # WebSocket connection hook (existing)
│   │   └── useGame.ts          # Game state hook (planned)
│   │
│   └── styles/
│       └── globals.css         # Global styles & Tailwind
│
├── public/                     # Static assets
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
├── postcss.config.js           # PostCSS configuration
├── tsconfig.json               # TypeScript configuration
└── package.json                # Dependencies
```

### State Management Architecture

#### Zustand Stores

**1. Game Store** (`stores/gameStore.ts`):
```typescript
interface GameStore {
  gameId: string | null;
  gameState: GameState | null;
  seat: number | null;
  playerId: string | null;
  isConnected: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

  setGame: (gameId, seat, playerId) => void;
  updateGameState: (state: GameState) => void;
  setConnectionState: (state) => void;
  clearGame: () => void;
  reset: () => void;
}
```

**Selectors**:
- `selectIsMyTurn`: Check if it's player's turn
- `selectMyHand`: Get player's current hand
- `selectCanBid`: Check if player can bid
- `selectCanPlay`: Check if player can play card

**2. UI Store** (`stores/uiStore.ts`):
```typescript
interface UIStore {
  toasts: Toast[];
  modal: ModalState | null;
  theme: 'light' | 'dark';
  soundEnabled: boolean;

  addToast: (message, type, duration?) => void;
  removeToast: (id) => void;
  showModal: (component, props) => void;
  closeModal: () => void;
  toggleTheme: () => void;
  toggleSound: () => void;
}
```

**Toast Helper**:
```typescript
// Outside component usage
toast.success('Game created!');
toast.error('Failed to join game');
```

**3. Auth Store** (`stores/authStore.ts`):
```typescript
interface AuthStore {
  isAuthenticated: boolean;
  username: string | null;

  login: (username, password) => Promise<void>;
  logout: () => void;
}
```

### Component Architecture

#### UI Components (`components/ui/`)

**Reusable, atomic components**:
- **Button**: 4 variants (primary, secondary, danger, ghost), 3 sizes, loading state
- **Card**: Glass morphism container with configurable padding
- **Input**: Form input with label and error states
- **Select**: Dropdown with label and error states
- **Modal**: Responsive dialog with backdrop, escape key, body scroll lock
- **Spinner**: Loading indicator with 4 sizes
- **Badge**: Status indicator with 6 variants

**Design System**:
- Consistent dark theme (slate-800 base)
- Primary color: #2b8aef (blue)
- Glass morphism effects with backdrop-blur
- Smooth transitions (200ms duration)
- Focus rings for accessibility
- Responsive spacing and sizing

#### Page Components (`pages/`)

**HomePage**:
- Game creation form
- Mode selection (28/56)
- Seats selection (4/6 for 56 mode)
- Quick links to history and admin

**GamePage** (in progress):
- Game board layout
- Player hand display
- Bidding interface
- Trump selection
- Trick display
- Score tracking

**HistoryPage** (planned):
- Game list with filters
- Pagination
- Game detail view
- Link to replay

**ReplayPage** (planned):
- Timeline scrubber
- Play/pause controls
- Step through snapshots
- Speed controls

**AdminPage**:
- Login form with basic auth
- Server health metrics
- Active sessions list
- Database statistics
- Session management (save, delete, cleanup)

### Type System

Complete TypeScript types matching backend API:

**Game Types** (`types/game.ts`):
```typescript
type Suit = '♠' | '♥' | '♦' | '♣';
type Rank = '7' | '8' | '9' | '10' | 'J' | 'Q' | 'K' | 'A';
type GameMode = '28' | '56';
type GamePhase = 'lobby' | 'bidding' | 'trump_choice' | 'playing' | 'round_end' | 'game_end';

interface Card {
  suit: Suit;
  rank: Rank;
  id: string;  // e.g., "A♠" or "A♠#1" for 56-mode
}

interface PlayerInfo {
  player_id: string;
  name: string;
  seat: number;
  is_bot: boolean;
}

interface GameState {
  game_id: string;
  mode: GameMode;
  seats: number;
  state: GamePhase;
  players: PlayerInfo[];
  turn: number | null;
  dealer: number | null;
  bids: Record<number, number>;
  bidding_winner: number | null;
  trump_suit: Suit | null;
  trump_chooser: number | null;
  current_trick: Record<number, Card>;
  points: Record<number, number>;
  owner_hand?: Card[];  // Only sent to identified player
  connected_seats?: number[];
}
```

**WebSocket Types** (`types/websocket.ts`):
```typescript
type ClientMessage =
  | { type: 'identify'; payload: { seat: number; player_id: string } }
  | { type: 'request_state' }
  | { type: 'bid'; payload: { value: number | null } }
  | { type: 'choose_trump'; payload: { suit: Suit } }
  | { type: 'play_card'; payload: { card_id: string } };

type ServerMessage =
  | { type: 'state_snapshot'; payload: GameState }
  | { type: 'action_ok'; payload: { action: string; message: string } }
  | { type: 'action_failed'; payload: { action: string; message: string } }
  | { type: 'error'; payload: { message: string } };
```

### API Service Layer

**Axios Client** (`api/client.ts`):
- Base URL configuration from environment
- 30-second timeout
- Global error handling interceptor
- WebSocket URL helper

**API Methods** (`api/game.ts`, `api/history.ts`, `api/admin.ts`):
```typescript
// Game API
export const gameApi = {
  createGame(mode, seats): Promise<CreateGameResponse>,
  getGame(gameId): Promise<GameState>,
  joinGame(gameId, name, isBot?): Promise<JoinGameResponse>,
  startGame(gameId, dealer?): Promise<{ok: boolean}>,
  placeBid(gameId, seat, value): Promise<{ok: boolean; msg: string}>,
  chooseTrump(gameId, seat, suit): Promise<{ok: boolean; msg: string}>,
  playCard(gameId, seat, cardId): Promise<{ok: boolean; msg: string; scores?: any}>
};

// History API
export const historyApi = {
  listGames(params?): Promise<GameSummary[]>,
  getGameDetail(gameId): Promise<GameDetail>,
  getSnapshot(gameId, snapshotId): Promise<any>,
  getGameReplay(gameId): Promise<GameReplay>,
  getStats(): Promise<GameHistoryStats>
};

// Admin API (requires credentials)
export const adminApi = {
  getHealth(username, password): Promise<ServerHealth>,
  listSessions(username, password): Promise<SessionInfo[]>,
  getDatabaseStats(username, password): Promise<DatabaseStats>,
  forceSave(gameId, username, password): Promise<{ok: boolean}>,
  deleteSession(gameId, username, password): Promise<any>,
  triggerCleanup(username, password): Promise<{ok: boolean; deleted_games: number}>
};
```

### Routing

React Router v7 with route definitions:

```typescript
const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/game/:gameId', element: <GamePage /> },
  { path: '/history', element: <HistoryPage /> },
  { path: '/replay/:gameId', element: <ReplayPage /> },
  { path: '/admin', element: <AdminPage /> },
  { path: '*', element: <NotFoundPage /> }
]);
```

### Design Principles

1. **Component Composition**: Small, reusable components
2. **Type Safety**: Complete TypeScript coverage
3. **State Management**: Centralized with Zustand, local where appropriate
4. **API Abstraction**: Clean service layer separating concerns
5. **Error Handling**: Global interceptors + local error states
6. **Accessibility**: Keyboard navigation, focus management, ARIA labels
7. **Responsive Design**: Mobile-first with Tailwind breakpoints
8. **Performance**: Code splitting, lazy loading, memoization

---

## API Design

### REST Principles

- **Resource-oriented URLs**: `/game/{id}`, `/history/games`
- **HTTP methods**: GET (read), POST (create/actions), DELETE (remove)
- **Status codes**: 200 (success), 400 (bad request), 401 (unauthorized), 404 (not found), 500 (server error)
- **JSON payloads**: All requests and responses use JSON
- **Pagination**: `limit` and `offset` query parameters
- **Filtering**: Query parameters for state, mode, etc.

### WebSocket Protocol

**Connection**: `ws://localhost:8000/api/v1/ws/{game_id}`

**Client → Server Messages**:
```json
// Identify (required first message)
{"type": "identify", "payload": {"seat": 0, "player_id": "uuid"}}

// Request current state
{"type": "request_state"}

// Game actions
{"type": "bid", "payload": {"value": 16}}
{"type": "choose_trump", "payload": {"suit": "♠"}}
{"type": "play_card", "payload": {"card_id": "A♠"}}
```

**Server → Client Messages**:
```json
// State update (broadcast to all)
{"type": "state_snapshot", "payload": {...GameState}}

// Action success
{"type": "action_ok", "payload": {"action": "bid", "message": "Bid placed"}}

// Action failure
{"type": "action_failed", "payload": {"action": "bid", "message": "Not your turn"}}

// Error
{"type": "error", "payload": {"message": "Invalid game ID"}}
```

### Authentication

**Admin endpoints** use HTTP Basic Auth:
- Header: `Authorization: Basic base64(username:password)`
- Configured via environment: `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- Default credentials: `admin` / `changeme`

---

## Data Flow

### Game Creation Flow

1. **Frontend**: User clicks "Create Game" → calls `gameApi.createGame(mode, seats)`
2. **Backend**:
   - Creates GameSession in memory
   - Saves GameModel to database
   - Returns game_id
3. **Frontend**: Navigates to `/game/{game_id}`

### Join Game Flow

1. **Frontend**: User enters name → calls `gameApi.joinGame(gameId, name)`
2. **Backend**:
   - Adds player to GameSession
   - Saves PlayerModel to database
   - Returns seat and player_id
3. **Frontend**:
   - Stores seat and player_id in gameStore
   - Establishes WebSocket connection
   - Sends `identify` message with seat and player_id

### Real-time Game Flow

1. **Frontend**: Player takes action (bid, trump, play) → sends WebSocket message
2. **Backend**:
   - Validates action (turn, rules, etc.)
   - Updates GameSession state
   - Saves snapshot to database
   - Broadcasts `state_snapshot` to all connected clients
3. **Frontend**: All clients receive state update → update gameStore → re-render

### State Persistence Flow

1. **Automatic**: After each significant action (bid, trump, play)
2. **Snapshot**: Complete game state serialized to JSON
3. **Storage**: Saved to `game_state_snapshots` table
4. **Recovery**: On server restart, games can be restored from latest snapshot

---

## Database Schema

```sql
-- Games table
CREATE TABLE games (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    mode VARCHAR(10) NOT NULL,            -- '28' or '56'
    seats INTEGER NOT NULL,               -- 4 or 6
    min_bid INTEGER NOT NULL,             -- 16 for 28, 32 for 56
    hidden_trump_mode VARCHAR(50) NOT NULL,
    two_decks_for_56 BOOLEAN NOT NULL,
    state VARCHAR(20) NOT NULL,           -- lobby, active, completed
    current_phase_data TEXT,              -- JSON serialized phase info
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    last_activity_at DATETIME NOT NULL
);

-- Players table
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id VARCHAR(36) NOT NULL REFERENCES games(id),
    player_id VARCHAR(36) NOT NULL,       -- UUID
    name VARCHAR(100) NOT NULL,
    seat INTEGER NOT NULL,                -- 0-5
    is_bot BOOLEAN NOT NULL,
    joined_at DATETIME NOT NULL
);
CREATE INDEX ix_players_game_id ON players(game_id);

-- Game state snapshots table
CREATE TABLE game_state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id VARCHAR(36) NOT NULL REFERENCES games(id),
    snapshot_data TEXT NOT NULL,          -- JSON serialized GameState
    state_phase VARCHAR(20) NOT NULL,     -- Phase when snapshot taken
    snapshot_reason VARCHAR(50) NOT NULL, -- 'bid', 'trump', 'play', 'round_end'
    created_at DATETIME NOT NULL
);
CREATE INDEX ix_game_state_snapshots_game_id ON game_state_snapshots(game_id);
```

### Indexes

- `game_id` indexed in players and snapshots for fast joins
- Primary keys automatically indexed

### Cleanup Rules

- **Lobby games**: Deleted after 1 hour of inactivity
- **Active games**: Deleted after 2 hours of inactivity
- **Completed games**: Deleted after 24 hours
- Runs every 30 minutes via background task

---

## WebSocket Protocol

### Connection Lifecycle

1. **Connect**: Client opens WebSocket to `/ws/{game_id}`
2. **Identify**: Client sends `identify` message with seat and player_id
3. **Active**: Client receives state updates, can send actions
4. **Disconnect**: Connection closes (network, browser close, etc.)
5. **Reconnect**: Client can reconnect and re-identify to same seat

### Message Types

**Client Messages**:
- `identify`: Required first message, associates connection with seat
- `request_state`: Request full state snapshot
- `bid`, `choose_trump`, `play_card`: Game actions

**Server Messages**:
- `state_snapshot`: Full game state (broadcast to all)
- `action_ok`: Action succeeded
- `action_failed`: Action failed with reason
- `error`: Connection or protocol error

### Connection Manager

- Maintains `Dict[game_id, Dict[WebSocket, seat]]` mapping
- Broadcasts state to all connections for a game
- Handles identification and seat ownership
- Cleans up on disconnect

---

## Deployment Architecture

### Docker Setup

**Backend Container** (`Dockerfile.backend`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Container** (`Dockerfile.frontend`):
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/thurup.db
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=changeme
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
```

### Environment Variables

**Backend**:
- `DATABASE_URL`: Database connection string (default: SQLite)
- `ADMIN_USERNAME`: Admin panel username (default: "admin")
- `ADMIN_PASSWORD`: Admin panel password (default: "changeme")
- `LOG_LEVEL`: Logging level (default: "INFO")

**Frontend**:
- `VITE_API_BASE`: Backend API URL (default: "http://localhost:8000")

### Production Considerations

1. **Database**: Migrate to PostgreSQL for production
2. **Caching**: Add Redis for session caching
3. **Load Balancing**: Nginx reverse proxy with multiple backend instances
4. **WebSocket Scaling**: Consider Redis pub/sub for distributed WebSocket
5. **Monitoring**: Add Prometheus metrics and Grafana dashboards
6. **Logging**: Centralized logging with ELK stack
7. **SSL/TLS**: HTTPS/WSS with Let's Encrypt certificates
8. **Secrets**: Use secret management (e.g., AWS Secrets Manager)

---

## Development Progress

### Backend Status: ✅ Complete (Week 1-3)

- ✅ Core game logic and rules
- ✅ Database persistence with SQLModel
- ✅ REST API endpoints (game, history, admin)
- ✅ WebSocket real-time updates
- ✅ Bot AI opponents
- ✅ Structured logging
- ✅ Comprehensive testing (60 tests)
- ✅ Admin endpoints with authentication
- ✅ Game history and replay system

### Frontend Status: 🚧 In Progress (50% complete)

**Completed**:
- ✅ Project setup (React + TypeScript + Vite)
- ✅ TailwindCSS styling system
- ✅ TypeScript type definitions
- ✅ Zustand state management
- ✅ API service layer
- ✅ React Router configuration
- ✅ Base UI components library
- ✅ Page scaffolding (Home, Game, History, Replay, Admin, 404)

**In Progress**:
- 🚧 Game board layout
- 🚧 Card game components (Hand, Trick, Bidding, Trump)
- 🚧 Enhanced WebSocket hook
- 🚧 Lobby screens
- 🚧 History and replay implementations
- 🚧 Admin dashboard features

**Planned**:
- ⏳ Sound effects
- ⏳ Animations and transitions
- ⏳ Responsive mobile layout
- ⏳ Accessibility improvements
- ⏳ End-to-end tests

---

## Future Enhancements

### Short Term
- Complete frontend game interface
- Mobile responsive design
- Sound effects and animations
- User preferences (theme, sound)

### Medium Term
- Player accounts and profiles
- Persistent player statistics
- Leaderboards
- Chat system
- Game invitations

### Long Term
- Tournament system
- Advanced AI difficulty levels
- Spectator mode
- Replay analysis tools
- Social features (friends, challenges)
- Multiple game variants

---

_Last Updated: 2025-10-13_
_Backend: Week 3 Complete | Frontend: Phase 1 Complete (50%)_
