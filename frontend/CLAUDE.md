# Thurup Frontend - Development Log

This document tracks the development phases and major changes to the Thurup card game frontend.

## Project Overview

Thurup Frontend is a React-based single-page application for the 28/56 card game variant. It features:
- Real-time gameplay with WebSocket communication
- Responsive UI that adapts to all screen sizes
- Interactive card game interface
- Team-based scoring and trick tracking
- State management with Zustand
- Type-safe development with TypeScript

## Technology Stack

- **Framework**: React 18.3+
- **Language**: TypeScript 5.6+
- **Build Tool**: Vite 5.4+
- **Styling**: TailwindCSS 3.4+
- **State Management**: Zustand 5.0+
- **Routing**: React Router 7.1+
- **HTTP Client**: Axios 1.7+
- **WebSocket**: Native WebSocket API

---

## Phase 1: Initial Setup & Core Components (Completed)

### Objectives
Establish project structure, core UI components, and basic game interface.

### Changes Implemented

#### 1. Project Structure
- **Directory Layout**:
  ```
  src/
  ├── api/          # API client and WebSocket handling
  ├── components/   # Reusable UI components
  │   ├── game/    # Game-specific components
  │   └── ui/      # Generic UI components (Button, Card, Badge)
  ├── hooks/       # Custom React hooks
  ├── pages/       # Route-level page components
  ├── stores/      # Zustand state stores
  ├── types/       # TypeScript type definitions
  └── utils/       # Utility functions
  ```

#### 2. UI Component Library
- **Files**: `src/components/ui/*.tsx`
- Built custom component library:
  - `Button` - Multiple variants (primary, secondary, danger, success)
  - `Card` - Container component with padding/border variants
  - `Badge` - Status indicators with color variants
  - `Loading` - Spinner component for loading states
- TailwindCSS utility-first styling
- Consistent design tokens and spacing

#### 3. Type Definitions
- **File**: `src/types/game.ts`
- Complete TypeScript interfaces matching backend models:
  - `Card`, `Suit`, `Rank`
  - `PlayerInfo`, `GameState`, `GamePhase`
  - `BidCommand`, `ChooseTrumpCommand`, `PlayCardCommand`
  - Helper functions: `getTeam()`, `getSuitColor()`, `getSuitName()`
- Strong type safety throughout application

#### 4. State Management
- **Files**: `src/stores/*.ts`
- Zustand stores for global state:
  - **gameStore** - Game state, player info, connection status
  - **uiStore** - Toast notifications, modal state
- Computed selectors for derived state
- Type-safe store hooks

---

## Phase 2: Real-time Communication (Completed)

### Objectives
Implement WebSocket connection, real-time state updates, and game actions.

### Changes Implemented

#### 1. WebSocket Integration
- **File**: `src/hooks/useGame.ts`
- Custom hook for WebSocket lifecycle:
  - Auto-connect on mount
  - Auto-reconnect with exponential backoff (max 5 attempts)
  - Player identification with seat and player ID
  - Message handling for different server message types
  - Graceful disconnect on unmount

#### 2. API Client
- **File**: `src/api/client.ts`
- Axios-based HTTP client:
  - Base URL configuration
  - Error handling and retries
  - Type-safe request/response types
  - Game CRUD operations (create, join, start)

#### 3. Game Actions
- **File**: `src/hooks/useGame.ts`
- Action methods returned from hook:
  - `placeBid(value)` - Submit bid during bidding phase
  - `chooseTrump(suit)` - Select trump suit
  - `playCard(cardId)` - Play card from hand
  - `requestState()` - Request current game state
- All actions check connection status before sending

---

## Phase 3: Game Components (Completed)

### Objectives
Build interactive game board, player hand, and game phase panels.

### Changes Implemented

#### 1. GameBoard Component
- **File**: `src/components/game/GameBoard.tsx`
- Circular player arrangement:
  - 4-player layout: bottom (you), left, top, right
  - 6-player layout: bottom (you), left sides, top, right sides
  - Dynamic positioning based on your seat
- Center circle shows:
  - Current trump (or hidden trump indicator)
  - Trick cards positioned around center
  - Visual feedback for dealer and current turn
- Player seat badges:
  - "You" badge for current player
  - "Dealer" badge for round dealer
  - "Bot" badge for AI players
  - Highlight ring for current turn

#### 2. PlayerHand Component
- **File**: `src/components/game/PlayerHand.tsx`
- Fan layout for cards in hand
- Hover effects (cards raise on hover)
- Playable card indicators
- Click handlers for card selection
- Card count display
- Disabled state when not player's turn

#### 3. PlayingCard Component
- **File**: `src/components/game/PlayingCard.tsx`
- Visual card representation:
  - Rank and suit display
  - Color coding (red for ♥♦, black for ♠♣)
  - Playable/disabled states
  - Hover and click animations

#### 4. Phase-specific Panels
- **BiddingPanel** - Bid input, pass button, min/max bid display
- **TrumpPanel** - Suit selection buttons with visual indicators
- **LobbyPanel** - Player list, start game, add bot buttons
- **ScoreBoard** - Team scores, game info, trick history

---

## Phase 4: UX Improvements & Responsiveness (Completed)

### Objectives
Enhance user experience with better visibility, responsive layout, and helpful feedback.

### Changes Implemented

#### 1. Responsive GameBoard Layout
- **File**: `src/components/game/GameBoard.tsx` (lines 57-125)
- **Problem**: Fixed pixel positioning caused seats to shift when window resized
- **Solution**:
  - Changed from fixed `min-h-[600px]` to responsive `aspect-square` container
  - Used percentage-based positioning instead of fixed pixels
  - Center circle: `w-2/5 aspect-square` (responsive relative sizing)
  - Seat positions: `5%`, `8%`, `25%`, `75%` (percentage-based)
  - Card trick positions: `25%` offset (percentage-based)
  - Responsive text sizing with Tailwind breakpoints: `text-xs sm:text-sm`, `text-4xl sm:text-6xl`
- **Result**: Layout maintains proportions at all screen sizes

#### 2. ScoreBoard Enhancements
- **File**: `src/components/game/ScoreBoard.tsx`
- **Team Scoring** (lines 103-184):
  - Replaced individual seat scores with team totals
  - Team 0 (even seats: 0, 2, 4) vs Team 1 (odd seats: 1, 3, 5)
  - Show seats belonging to each team
  - Highlight bidding team with ring
  - Display bid target for bidding team
  - Success/failure indicator during scoring phase

- **Lead Suit Indicator** (lines 45-51):
  - Show which suit must be followed during play
  - Highlighted box with suit symbol
  - Only visible during play phase when trick is in progress

- **Last Trick Display** (lines 53-82):
  - Shows previous completed trick
  - Winner badge with player name
  - All 4 cards in grid layout
  - Green ring highlight on winner's card
  - Color-coded suits for easy recognition

#### 3. Trump Reveal Feedback
- **File**: `src/components/game/GameBoard.tsx` (lines 76-84)
- **Hidden Trump Indicator**:
  - Shows 🎴 card face-down icon when trump is hidden
  - Context-aware hint text:
    - Bid winner sees: "Play trump to reveal"
    - Other players see: "Hidden until revealed"
  - Automatic reveal based on game rules (no manual button needed)

#### 4. TypeScript Type Updates
- **File**: `src/types/game.ts`
- Updated GameState interface:
  - `current_trick?: Record<number, Card>` - Cards in current trick (seat -> card)
  - `lead_suit?: Suit | null` - Suit that must be followed
  - `last_trick?: { winner: number; cards: Record<number, Card> }` - Previous trick
  - `tricks_won?: Record<number, number>` - Tricks won per seat

#### 5. Responsive Player Seats
- **File**: `src/components/game/GameBoard.tsx` (lines 136-165)
- Responsive padding and gaps: `px-3 sm:px-6 py-2 sm:py-3`
- Adaptive text sizing: `text-xs sm:text-base`
- Name truncation on small screens: `max-w-[80px] sm:max-w-none`
- Flex wrap for badges: `flex-wrap justify-center`
- Smaller pulse indicators on mobile: `w-2 h-2 sm:w-3 sm:h-3`

---

## Architecture Patterns

### Component Composition
Hierarchical component structure:
```
GamePage
├── GameBoard
│   ├── PlayerSeat (x4 or x6)
│   └── TrickCards
├── PlayerHand
│   └── PlayingCard (x8)
├── ScoreBoard
└── Phase-specific Panels
    ├── BiddingPanel
    ├── TrumpPanel
    └── LobbyPanel
```

### State Management Flow
```
WebSocket → useGame hook → Zustand store → React components
            ↑                                      ↓
            └────────── User actions ──────────────┘
```

### Responsive Design
- Mobile-first approach with `sm:`, `md:`, `lg:` breakpoints
- Percentage-based positioning for scalability
- Aspect-ratio containers for consistent proportions
- Flexible grid layouts with wrap for overflow

### Type Safety
- All props interfaces defined
- Backend DTO types matched in frontend
- Zustand stores fully typed
- No `any` types except for legacy code

---

## Key Files Reference

### Core Application
- `src/main.tsx` - Application entry point
- `src/App.tsx` - Router configuration
- `src/pages/GamePage.tsx` - Main game interface
- `src/pages/HomePage.tsx` - Landing page

### Game Components
- `src/components/game/GameBoard.tsx` - Circular game board layout
- `src/components/game/PlayerHand.tsx` - Player's card hand
- `src/components/game/PlayingCard.tsx` - Individual card component
- `src/components/game/ScoreBoard.tsx` - Scores and game info
- `src/components/game/BiddingPanel.tsx` - Bidding interface
- `src/components/game/TrumpPanel.tsx` - Trump selection
- `src/components/game/LobbyPanel.tsx` - Pre-game lobby

### State & Communication
- `src/hooks/useGame.ts` - WebSocket hook with reconnection
- `src/stores/gameStore.ts` - Game state management
- `src/stores/uiStore.ts` - UI state (toasts, modals)
- `src/api/client.ts` - HTTP API client
- `src/types/game.ts` - Type definitions

### UI Components
- `src/components/ui/Button.tsx` - Button component
- `src/components/ui/Card.tsx` - Card container
- `src/components/ui/Badge.tsx` - Status badges
- `src/components/ui/Loading.tsx` - Loading spinner

---

## Development Commands

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality
```bash
# Type checking
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

---

## WebSocket Message Protocol

### Client → Server Messages
```typescript
// Identify player
{ type: 'identify', payload: { seat: number, player_id: string } }

// Request current state
{ type: 'request_state' }

// Place bid
{ type: 'place_bid', payload: { seat: number, value: number | null } }

// Choose trump
{ type: 'choose_trump', payload: { seat: number, suit: Suit } }

// Play card
{ type: 'play_card', payload: { seat: number, card_id: string } }
```

### Server → Client Messages
```typescript
// State update
{ type: 'state_snapshot', payload: GameState }

// Action success
{ type: 'action_ok', payload: { message: string } }

// Action failed
{ type: 'action_failed', payload: { message: string } }

// Error
{ type: 'error', payload: { message: string } }
```

---

## User Experience Features

### Visual Feedback
- **Turn Indicator**: Pulsing ring on current player's seat
- **Playable Cards**: Highlighted when it's your turn
- **Trump Reveal**: Context-aware hint for bid winner
- **Lead Suit**: Clear indication of suit to follow
- **Last Trick**: Previous trick remains visible for reference
- **Team Scores**: Real-time score updates with bid targets

### Responsive Behavior
- **Mobile (< 640px)**: Compact layout, smaller text, truncated names
- **Tablet (640-1024px)**: Medium layout, readable text
- **Desktop (> 1024px)**: Full layout with sidebar, all details visible

### Error Handling
- **Connection Lost**: Yellow "Disconnected" badge
- **Reconnecting**: Auto-retry with exponential backoff
- **Action Failed**: Toast notification with error message
- **Max Retries**: Error toast after 5 failed reconnection attempts

---

## Technical Notes

- **Data Flow**: Server broadcasts full game state on every change; frontend is stateless and reactive
- **Reconnection**: WebSocket automatically reconnects with player identification
- **Card IDs**: Include deck number for 56-mode (e.g., "A♠#1", "A♠#2")
- **Trump Reveal**: Automatic based on server-side game rules (no manual control needed)
- **Team Formation**: Even seats (0, 2, 4) vs Odd seats (1, 3, 5)

---

## Phase 5: Session Management & Persistence (Completed)

### Objectives
Enable page refresh recovery, consistent join UX, and player session persistence across browser sessions.

### Changes Implemented

#### 1. Session Manager Utility
- **File**: `src/utils/sessionManager.ts`
- **Purpose**: LocalStorage-based player session persistence
- **Features**:
  - Save/load/clear session functions
  - 24-hour session expiry with automatic cleanup
  - `clearExpiredSessions()` runs on app init
- **Session Structure**:
  ```typescript
  interface PlayerSession {
    gameId: string;
    seat: number;
    playerId: string;
    playerName: string;
    joinedAt: number;
  }
  ```
- **Storage Key**: `thurup_session_{gameId}`

#### 2. JoinGameModal Component
- **File**: `src/components/game/JoinGameModal.tsx`
- **Purpose**: Reusable modal for consistent name input UX
- **Features**:
  - Player name validation (2-20 characters)
  - Game code display
  - Loading states and error handling
  - Enter key support for quick submission
- **Usage**: Used on both HomePage and GamePage for consistent UX

#### 3. GamePage Session Restoration
- **File**: `src/pages/GamePage.tsx` (lines 37-87)
- **Race Condition Fix**: Session check happens BEFORE WebSocket connection
- **Flow**:
  1. Check localStorage for existing session on mount
  2. If session found → restore seat/playerId → connect WebSocket with correct identity
  3. If not found → show JoinGameModal
  4. After join → save session to localStorage
  5. WebSocket connects only after session is checked (prevents race condition)
- **Key Addition**: `sessionChecked` state prevents WebSocket from connecting with null seat/playerId

#### 4. HomePage Modal Integration
- **File**: `src/pages/HomePage.tsx`
- **Changes**:
  - Removed inline player name input from Join Game section
  - Show JoinGameModal when "Join Game" button clicked
  - Save session to localStorage for both create and join flows
  - Consistent modal UX across all entry points

#### 5. GameStore localStorage Sync
- **File**: `src/stores/gameStore.ts` (lines 74-100)
- **Changes**:
  - `clearGame()` now clears localStorage session
  - `reset()` now clears localStorage session
  - Proper cleanup when leaving games

### User Experience Flow

**Create Game from HomePage:**
1. User enters name and clicks "Create Game"
2. Game created, player auto-joins
3. Session saved to localStorage
4. Navigate to GamePage → WebSocket connects with correct session

**Join via HomePage:**
1. User enters game code and clicks "Join Game"
2. JoinGameModal appears asking for player name
3. User enters name → joins game
4. Session saved to localStorage
5. Navigate to GamePage → WebSocket connects with correct session

**Share URL (Direct Link):**
1. User visits `/game/royal-turtle-65` directly
2. GamePage checks localStorage → no session found
3. JoinGameModal appears asking for player name
4. User enters name → joins game
5. Session saved to localStorage
6. WebSocket connects with player info

**Page Refresh:**
1. User refreshes page while in game
2. GamePage checks localStorage → session found
3. Session restored (seat, playerId)
4. WebSocket reconnects automatically with correct identity
5. Player sees their hand and can continue playing

### Key Files Reference

- `src/utils/sessionManager.ts` - Session persistence utility
- `src/components/game/JoinGameModal.tsx` - Modal for name input
- `src/pages/GamePage.tsx` - Session restoration logic
- `src/pages/HomePage.tsx` - Modal integration
- `src/stores/gameStore.ts` - localStorage sync on cleanup

### Technical Notes

- **Session Expiry**: 24 hours (configurable at `SESSION_EXPIRY_MS`)
- **Storage Isolation**: Each game has separate localStorage entry by gameId
- **Race Condition Prevention**: `sessionChecked` flag delays WebSocket connection
- **Error Resilience**: All localStorage operations wrapped in try-catch
- **Security**: Sessions stored client-side only; server validates on each action

---

## Phase 6: Visual Enhancements & Bug Fixes (Completed)

### Objectives
Polish visual presentation with card images, fix WebSocket connection issues, improve start game UX, and enhance scoreboard display.

### Changes Implemented

#### 1. Playing Card Images
- **File**: `src/components/game/PlayingCard.tsx`
- **Changes**:
  - Replaced text-based cards with actual card images from Deck of Cards API
  - CDN: `https://deckofcardsapi.com/static/img/`
  - Format: `{rank}{suit}.png` (e.g., AS.png for Ace of Spades)
  - Added `getCardImageCode()` helper to map suit symbols to API format (♠→S, ♥→H, ♦→D, ♣→C)
  - Added lazy loading with `loading="lazy"` attribute
  - Maintained all existing functionality (playability, hover, click handlers)

#### 2. WebSocket Connection Fix
- **File**: `src/hooks/useGame.ts` (lines 236-243)
- **Problem**: WebSocket wasn't connecting when GamePage initially rendered
- **Root Cause**: useEffect that calls `connect()` had dependencies `[connect, disconnect]` but `connect()` checked `currentGameId.current` which was updated in a separate useEffect, creating a race condition
- **Solution**: Added `gameId` to useEffect dependencies and early return if no gameId:
  ```typescript
  useEffect(() => {
    if (!gameId) return; // Don't connect if no gameId
    connect();
    return () => disconnect();
  }, [gameId, connect, disconnect]); // Added gameId dependency
  ```
- **Result**: WebSocket now connects reliably when session is restored

#### 3. ScoreBoard Player Names
- **File**: `src/components/game/ScoreBoard.tsx` (lines 80-82)
- **Changes**: Last trick display now shows player names instead of "Seat X"
- **Implementation**:
  ```typescript
  {gameState.players.find((p: any) => p.seat === Number(seat))?.name || `Seat ${Number(seat) + 1}`}
  ```
- **Result**: More readable trick history with actual player names

#### 4. CORS Configuration
- **Files**: `backend/.env`, `backend/.env.development`, `backend/.env.production`, `backend/.env.test`, `backend/.env.template`
- **Changes**:
  - Moved CORS origins from hardcoded to environment variables
  - Created separate .env files for different environments
  - Added `.env` files to `.gitignore`
  - Updated `app/main.py` to read `CORS_ORIGINS` from environment (comma-separated)
- **CORS Middleware Fix**: Moved CORS middleware registration BEFORE router inclusion (critical for FastAPI)

#### 5. Auto-fill Bots on Start Game
- **File**: `backend/app/api/v1/rest.py` (lines 161-201)
- **Problem**: Starting game with fewer than 4 players caused game to get stuck
- **Solution**: Auto-fill empty seats with bots when "Start Game" is clicked
- **Implementation**:
  ```python
  # Auto-fill empty seats with bots
  bots_added = 0
  for seat_idx in range(sess.seats):
      if seat_idx not in sess.players:
          bot_player = PlayerInfo(player_id=bot_id, name=f"Bot {seat_idx + 1}", is_bot=True)
          await sess.add_player(bot_player)
          bots_added += 1
  ```
- **Result**: Single-player mode now works seamlessly, no error messages

### Key Files Modified

- `frontend/src/components/game/PlayingCard.tsx` - Card images
- `frontend/src/hooks/useGame.ts` - WebSocket connection fix
- `frontend/src/components/game/ScoreBoard.tsx` - Player names in last trick
- `backend/app/main.py` - CORS middleware ordering and env vars
- `backend/app/api/v1/rest.py` - Auto-fill bots logic
- `backend/.env*` - Environment configuration files

### Technical Notes

- **Card Image CDN**: Free public API, reliable, no authentication required
- **WebSocket Race Condition**: Solved by making useEffect depend on actual gameId value
- **Bot Naming**: Bots named "Bot 1", "Bot 2", etc. based on their seat number
- **CORS Order**: In FastAPI, middleware must be added BEFORE router inclusion for it to apply to routes

---

## TODO: Next Session - Timing & Audio Enhancements

### Objectives for Tomorrow
Improve game pacing and add audio feedback for better user experience.

### Planned Improvements

#### 1. Game Timing Adjustments
**Current Issues:**
- Bots act instantly, making it hard to follow the game flow
- Trick completion has a fixed 2-second delay (see `backend/app/api/v1/websocket.py` line 206)
- State updates happen too quickly for visual feedback

**Proposed Changes:**
- Add configurable delays for bot actions:
  - Bot bidding: 1-2 second delay
  - Bot trump selection: 1-2 second delay
  - Bot card play: 1-3 second delay (random for realism)
- Add delay before clearing trick (currently 2 seconds, may need adjustment)
- Consider adding visual countdown or "thinking" indicator for bots

**Files to Modify:**
- `backend/app/api/v1/bot_runner.py` - Add delays before bot actions
- `backend/app/constants.py` - Add timing configuration constants
- `backend/.env` files - Make timing configurable via environment

#### 2. Sound Effects
**Planned Audio Events:**
- Card play sound (whoosh/snap effect)
- Trick winner sound (chime/success sound)
- Bid placed sound (subtle click)
- Trump selection sound (distinct tone)
- Turn indicator sound (gentle notification)

**Implementation Approach:**
- Use Web Audio API or HTML5 `<audio>` elements
- Create sound manager utility in `frontend/src/utils/soundManager.ts`
- Hook into game state changes in GamePage component
- Add mute/unmute toggle in UI
- Consider using free sound effects from:
  - [Freesound.org](https://freesound.org)
  - [Zapsplat.com](https://www.zapsplat.com)
  - [Mixkit.co](https://mixkit.co/free-sound-effects/)

**Files to Create/Modify:**
- `frontend/src/utils/soundManager.ts` - Sound management utility
- `frontend/src/hooks/useSoundEffects.ts` - React hook for sound events
- `frontend/public/sounds/` - Directory for sound files
- `frontend/src/pages/GamePage.tsx` - Integrate sound effects
- `frontend/src/stores/uiStore.ts` - Add sound preferences state

#### 3. Visual Timing Indicators
**Enhancements:**
- "Bot is thinking..." indicator with animated dots
- Card play animation (slide from hand to center)
- Countdown timer for trick completion
- Fade-in/fade-out for state changes

**Technical Considerations:**
- Coordinate backend delays with frontend animations
- Use CSS transitions for smooth visual effects
- Consider using Framer Motion for advanced animations
- Ensure timing doesn't impact game responsiveness

### Success Criteria
- [ ] Bot actions have realistic timing (not instant)
- [ ] Sound effects play for major game events
- [ ] Users can mute/unmute sounds
- [ ] Visual feedback matches audio timing
- [ ] Game feels smooth and polished
- [ ] Performance remains good (no lag)

### Resources
- Current trick delay: `backend/app/api/v1/websocket.py:206`
- Bot runner: `backend/app/api/v1/bot_runner.py`
- Card play component: `frontend/src/components/game/PlayingCard.tsx`

---

## Phase 7: Admin Panel & Round History Viewer (Completed)

### Objectives
Build comprehensive admin dashboard for server management and game history browsing with complete round-by-round playback.

### Changes Implemented

#### 1. Admin Page with Authentication
- **File**: `src/pages/AdminPage.tsx`
- **Features**:
  - HTTP Basic Auth login form
  - Protected admin dashboard
  - Server health metrics display
  - Active sessions list with connection status
  - Database statistics
  - Session management actions (save, delete)
  - Manual cleanup trigger
- **Authentication**:
  - Uses Zustand store: `src/stores/authStore.ts`
  - Credentials stored in memory during session
  - Login/logout functionality
  - Credentials passed to all admin API calls
- **Server Health Display** (lines 249-289):
  - Status badge (healthy/degraded)
  - Uptime, session count, connections
  - Bot task count, database status
- **Active Sessions List** (lines 324-391):
  - Shows short codes instead of UUIDs (line 348-350)
  - State badges (lobby/playing/scoring)
  - Player count and connected seats
  - Bot active indicator
  - Save and delete buttons per session
- **Database Stats** (lines 291-323):
  - Total games, players, snapshots
  - Database size in MB
  - Manual cleanup trigger button

#### 2. Game History Browser (AdminGameHistoryPage)
- **File**: `src/pages/AdminGameHistoryPage.tsx`
- **Purpose**: Browse all games with complete round history and trick-by-trick analysis

**Game List View** (lines 240-321):
- Displays all games from database
- Shows short codes for easy identification (lines 273-275)
- State and mode badges
- Round count and player count
- Creation and last activity timestamps
- Player names list with defensive type handling (lines 289-302)
- Click to view detailed round history

**Game Detail View** (lines 73-238):
- Complete game metadata and player roster (lines 95-131)
- Team scores for each round (lines 172-187)
- Round-by-round breakdown with:
  - Dealer name (not "Seat X") - line 148
  - Bid winner and value - lines 160-167
  - Trump suit with colored symbol - lines 152-159
  - All captured tricks with full details - lines 189-230

**Trick Display** (lines 196-227):
- Shows all 4 cards played in each trick
- Player names for each card (not seat numbers) - line 212
- Winner highlighted with green ring (lines 206-208)
- Points awarded displayed (line 223)
- Color-coded suits (♥♦ red, ♠♣ black) - lines 56-58, 214-216

**Helper Functions**:
- `getPlayerName(game, seat)` - Resolves seat number to player name (lines 60-63)
- `getSuitColor(suit)` - Returns Tailwind class for suit color (lines 56-58)
- `formatDate(dateString)` - Formats timestamps for display (lines 52-54)

**Navigation**:
- "Back to List" button when viewing game details (lines 80-85)
- "Back to Admin" button to return to admin dashboard (lines 90-92)
- "View Rounds" button on each game card (lines 305-313)

#### 3. Admin API Client
- **File**: `src/api/admin.ts`
- **Methods**:
  - `getHealth(username, password)` - Server health metrics
  - `listSessions(username, password)` - Active in-memory sessions
  - `getDatabaseStats(username, password)` - Database metrics
  - `forceSave(gameId, username, password)` - Trigger manual save
  - `deleteSession(gameId, username, password)` - Delete session
  - `triggerCleanup(username, password)` - Run cleanup task
  - `listGameHistory(username, password)` - Get all games from database
  - `getGameRounds(gameId, username, password)` - Get rounds for game
- **Authentication**: All methods accept username/password for HTTP Basic Auth
- **Error Handling**: Axios error responses parsed for user-friendly messages

#### 4. Auth State Management
- **File**: `src/stores/authStore.ts`
- **State**:
  - `username: string | null` - Current admin username
  - `password: string | null` - Current admin password (in memory only)
  - `isAuthenticated: boolean` - Auth status
- **Actions**:
  - `login(username, password)` - Authenticate and store credentials
  - `logout()` - Clear credentials and redirect to login

#### 5. Router Configuration
- **File**: `src/App.tsx`
- **New Routes**:
  - `/admin` - Admin dashboard with login
  - `/admin/history` - Game history browser
- **Protected Routes**: Admin routes redirect to login if not authenticated

#### 6. UI Components Used
- **Card** - Container for sections
- **Badge** - Status indicators (state, mode, health)
- **Button** - Actions (save, delete, cleanup, view rounds)
- **Loading** - Spinner for async operations

#### 7. Bug Fixes

**Navigation Error Fix** (`AdminPage.tsx` line 97):
- **Problem**: `ReferenceError: navigate is not defined` when clicking "Game History"
- **Cause**: `useNavigate()` hook missing in `AdminDashboard` component
- **Fix**: Added `const navigate = useNavigate();` at line 97
- **Result**: Navigation to `/admin/history` now works correctly

**Player Names Display Fix** (`AdminGameHistoryPage.tsx`):
- **Problem**: Round history showed "Seat 0", "Seat 1" instead of player names
- **Root Cause**: Backend bug where players weren't saved to database (see backend CLAUDE.md Week 6)
- **Frontend Fix**: Added `getPlayerName()` helper function (lines 60-63) that:
  - Looks up player by seat number in players array
  - Returns player name if found
  - Falls back to "Seat X" if not found (defensive programming)
- **Updated Locations**: Lines 148 (dealer), 164 (bid winner), 212 (trick cards), 223 (trick winner)

**React Rendering Error Fix** (`AdminGameHistoryPage.tsx` lines 289-302):
- **Problem**: "Objects are not valid as a React child" error when displaying player names
- **Cause**: API returned player objects instead of strings after backend persistence fix
- **Fix**: Added defensive type checking:
  ```typescript
  const playerName = typeof nameOrPlayer === 'string'
    ? nameOrPlayer
    : nameOrPlayer.name;
  ```
- **Result**: Frontend handles both string names and player objects gracefully

#### 8. Multiple Rounds Support
- **File**: `src/pages/GamePage.tsx` (lines 332-346)
- **Feature**: "Start Next Round" button appears during SCORING phase
- **Purpose**: Enable playing multiple rounds in same game session
- **Flow**:
  1. Round completes → SCORING phase
  2. Scores displayed to all players
  3. "Start Next Round" button shown
  4. Click triggers `/game/{game_id}/start` API call
  5. New round begins, previous round saved to history
- **User Experience**: No need to create new game for each round

### Integration with Backend

**Admin Endpoints Used**:
- `GET /api/v1/admin/health` - Server metrics
- `GET /api/v1/admin/sessions` - Active sessions
- `GET /api/v1/admin/database/stats` - DB stats
- `POST /api/v1/admin/sessions/{game_id}/save` - Force save
- `DELETE /api/v1/admin/sessions/{game_id}` - Delete session
- `POST /api/v1/admin/maintenance/cleanup` - Trigger cleanup
- `GET /api/v1/admin/history/games` - Game list
- `GET /api/v1/admin/history/games/{game_id}/rounds` - Round details

**Authentication Flow**:
1. User enters username/password on `/admin`
2. Frontend calls `/api/v1/admin/health` to validate credentials
3. If valid, store credentials in authStore and show dashboard
4. All subsequent admin API calls include credentials in Basic Auth header
5. Logout clears credentials from memory

### Key Files Reference

**New Files**:
- `src/pages/AdminPage.tsx` - Admin dashboard
- `src/pages/AdminGameHistoryPage.tsx` - Game history browser
- `src/api/admin.ts` - Admin API client
- `src/stores/authStore.ts` - Authentication state

**Modified Files**:
- `src/App.tsx` - Added admin routes
- `src/pages/GamePage.tsx` - Added "Start Next Round" button

### User Experience Improvements

**Before Phase 7**:
- No way to monitor server health
- No visibility into active sessions
- No game history browsing
- Could only play single rounds
- Manual database cleanup required

**After Phase 7**:
- Real-time server health dashboard
- Active session monitoring with connection status
- Complete game history with round-by-round playback
- Multi-round gameplay with "Start Next Round" button
- One-click cleanup trigger for maintenance
- Player names throughout history (not seat numbers)
- Short codes for easy game identification

### Security Considerations

- **Credentials in Memory**: Auth credentials stored in Zustand (memory only, not localStorage)
- **No Persistent Auth**: User must re-login after page refresh (intentional for security)
- **HTTP Basic Auth**: Simple but effective for admin-only endpoints
- **Backend Validation**: All admin endpoints validate credentials on server

### Technical Notes

**Auto-refresh**:
- Admin dashboard refreshes every 10 seconds (line 107)
- Keeps metrics up-to-date without manual reload

**Error Handling**:
- Try-catch blocks around all API calls
- User-friendly error messages in alerts
- Console logging for debugging

**Data Display**:
- Uptime formatted as "Xh Ym" (lines 195-199)
- Database size shown in MB (lines 201-205)
- Timestamps formatted with `toLocaleString()` (lines 52-54)
- Defensive programming for missing data (optional chaining, fallbacks)

**Performance**:
- Game list loads all games at once (pagination recommended for large datasets)
- Round details loaded on-demand (only when "View Rounds" clicked)
- Separate API calls prevent loading unnecessary data

---

## Week 7: Critical Bug Fixes - Multiplayer & Dealer Rotation (Completed)

### Objectives
Fix two critical bugs preventing correct gameplay: multiplayer players unable to see their hands, and incorrect dealer rotation/leader assignment.

### Changes Implemented

#### Bug #1: Multiplayer Hand Not Visible (CRITICAL - Fixed)

**Problem**: Only player 1 (game creator) could see their hand. Players 2, 3, and 4 couldn't see the "Your Hand" section at all.

**Investigation Process**:
1. Added debug logging to backend broadcast mechanism
2. User provided logs from 2 separate browser tabs
3. Backend logs showed hands being sent correctly to both seats
4. Frontend logs showed Player 2's WebSocket was identifying as seat 0 instead of seat 1

**Root Cause**: WebSocket timing race condition:
1. GamePage loads → WebSocket connects immediately
2. At connection time, `seat` and `playerId` are still `null` (not yet restored from localStorage)
3. WebSocket sends `request_state` message (not `identify`)
4. Later, localStorage session restores → `seat` and `playerId` updated in state
5. But WebSocket never re-sends `identify` message with new values
6. Backend keeps connection mapped to `seat=None`, never sends `owner_hand`

**Solution**: Added reactive `useEffect` to re-identify when seat/playerId changes.

**File**: `frontend/src/hooks/useGame.ts:101-112`

**Code Added**:
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

**How It Works**:
1. When `seat` or `playerId` changes (from `null` to actual values)
2. AND WebSocket is already connected
3. Automatically re-send `identify` message to backend
4. Backend updates connection mapping: `seat=None` → `seat=1`
5. Backend now sends `owner_hand` correctly to Player 2

**Testing**: User tested with 2+ players in separate browsers. All players now see their hands correctly.

**Impact**: **CRITICAL** - Game was completely unplayable for players other than the creator. Now fully functional.

---

#### Bug #2: Incorrect Dealer Rotation (HIGH - Fixed)

**Problem**:
1. First bidder/player was set to dealer (should be player to dealer's right)
2. No automatic dealer rotation between rounds
3. Dealer badge displayed on wrong seat (shown on leader instead of dealer)

**Investigation**: Researched official 28 card game rules via Pagat.com.

**Official Rules** (verified):
- **Direction of play**: Counter-clockwise
- **First bidder/player**: Player to dealer's RIGHT (next counter-clockwise position)
- **Dealer rotation**: Counter-clockwise (to the right)

**Frontend Changes**:

1. **Updated GameState interface** (`frontend/src/types/game.ts:42-43`):
   ```typescript
   dealer: number; // Current dealer position
   leader: number; // Player to dealer's right (first to bid/play)
   ```
   Backend now sends separate `dealer` field (previously only had `leader`).

2. **Updated GameBoard component** (`frontend/src/components/game/GameBoard.tsx:16,47,54`):
   - **Line 16**: Extract `dealer` from gameState props
   - **Line 47**: Use `dealer` for "Dealer" badge instead of `leader`:
     ```typescript
     isDealer: seatNumber === dealer,  // Was: seatNumber === leader
     ```
   - **Line 54**: Added `dealer` to `useMemo` dependencies

**Backend Changes** (for reference):
- Added `current_dealer` field to GameSession
- Fixed leader calculation: `(current_dealer + 1) % seats`
- Added automatic dealer rotation: `(current_dealer - 1) % seats`
- Updated GameStateDTO to include `dealer` field

**How Dealer Rotation Works**:

**Round 1** (4-player):
- Dealer = Seat 0
- Leader = Seat 1 (dealer's RIGHT, first to bid)
- Bidding order: 1 → 2 → 3 → 0 (counter-clockwise)

**Round 2**:
- Dealer = Seat 3 (rotated counter-clockwise)
- Leader = Seat 0
- Bidding order: 0 → 1 → 2 → 3

**Round 3**:
- Dealer = Seat 2
- Leader = Seat 3
- Bidding order: 3 → 0 → 1 → 2

**Round 4**:
- Dealer = Seat 1
- Leader = Seat 2
- Bidding order: 2 → 3 → 0 → 1

After 4 rounds, dealer returns to Seat 0 (full rotation).

**Testing**: User tested through 4 complete rounds. Verified dealer badge moves counter-clockwise each round and first bidder is always to dealer's right.

**Impact**: **HIGH** - Game now follows official 28 card game rules for dealer rotation and bidding order.

---

### Files Modified

**Bug #1 Fix**:
- `src/hooks/useGame.ts:101-112` - Added re-identification effect

**Bug #2 Fix**:
- `src/types/game.ts:42-43` - Added dealer field to GameState interface
- `src/components/game/GameBoard.tsx:16,47,54` - Use dealer instead of leader for badge

### User Experience Impact

**Before Fixes**:
- Game unplayable for non-creator players (couldn't see cards)
- Incorrect dealer rotation violated official game rules
- Bidding order was wrong

**After Fixes**:
- All players see their hands and can play normally
- Dealer rotation follows official 28 card game rules
- Correct bidding/playing order every round

### Technical Notes

**WebSocket Lifecycle Best Practice**:
The re-identification pattern is crucial for React apps where:
- WebSocket connects early in component lifecycle
- State updates happen asynchronously (localStorage restore, API calls)
- Need to re-synchronize WebSocket with updated state

**Pattern to Follow**:
```typescript
// Watch for state changes that affect WebSocket behavior
useEffect(() => {
  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
    // Re-send identification/subscription messages
    if (criticalState !== null) {
      wsRef.current.send(JSON.stringify({...}));
    }
  }
}, [criticalState]);
```

This pattern ensures WebSocket stays synchronized with React state even when state updates after connection.

---

## Week 7 Continued: Visual Enhancements - Trick Card Display (Completed)

### Objectives
Improve trick card visualization by using actual card images instead of text, with proper spacing from the center trump display.

### Changes Implemented

#### Trick Card SVG Images
- **File**: `src/components/game/GameBoard.tsx` (lines 9, 100-103, 208-226)
- **Problem**: Trick cards displayed as text (e.g., "A♠") in white boxes, inconsistent with player hand
- **Solution**: Use the same `PlayingCard` component with actual card images from Deck of Cards API

**Changes Made**:

1. **Imported PlayingCard component** (line 9):
   ```typescript
   import { PlayingCard } from './PlayingCard';
   ```

2. **Replaced text display with card images** (lines 100-103):
   ```typescript
   // OLD: Text-based display
   <div className="bg-white rounded-lg shadow-xl p-2 sm:p-3 border-2 border-gray-300">
     <span className={`text-xl sm:text-3xl font-bold ${getSuitColor(pos.trickCard.suit)}`}>
       {pos.trickCard.rank}{pos.trickCard.suit}
     </span>
   </div>

   // NEW: Actual card images
   <PlayingCard
     card={pos.trickCard}
     size="sm"
   />
   ```

3. **Adjusted card positioning** (lines 208-226):
   - Changed offset from `25%` to `15%` for better spacing
   - Keeps cards inside the circle boundary
   - Prevents overlap with center trump symbol
   - Positions cards between center and player seats

   ```typescript
   function getCardPositionStyle(
     position: 'bottom' | 'top' | 'left' | 'right',
     seats: number
   ): React.CSSProperties {
     // Position cards inside the circle, near the edge but not overlapping center
     const offset = '15%';

     switch (position) {
       case 'bottom':
         return { bottom: offset, left: '50%', transform: 'translateX(-50%)' };
       case 'top':
         return { top: offset, left: '50%', transform: 'translateX(-50%)' };
       case 'left':
         return { left: offset, top: '50%', transform: 'translateY(-50%)' };
       case 'right':
         return { right: offset, top: '50%', transform: 'translateY(-50%)' };
     }
   }
   ```

**Visual Improvements**:
- ✅ Trick cards now use actual playing card images (consistent with hand)
- ✅ Small size (`sm` = 16x24) keeps them compact and balanced
- ✅ Cards positioned inside circle with proper spacing from center
- ✅ Trump symbol remains clearly visible in center
- ✅ No transparency applied to played cards (full opacity)
- ✅ Consistent card styling throughout the game

**User Experience**:
- **Before**: Text-based cards ("A♠") in white boxes, sometimes overlapping center
- **After**: Professional card images positioned cleanly around trump display

**Technical Notes**:
- Uses same `PlayingCard` component for consistency
- No `disabled` prop, so cards display at full opacity
- Percentage-based positioning scales with screen size
- Cards are non-interactive (no onClick handler)

### Files Modified

- `src/components/game/GameBoard.tsx`:
  - Line 9: Added PlayingCard import
  - Lines 100-103: Replaced text display with PlayingCard component
  - Lines 208-226: Adjusted positioning offset to 15%

---

_Last Updated: 2025-10-15 (Week 7 - Critical Bug Fixes + Trick Card Visual Enhancements + Phase 7 - Admin Panel & Round History + TODO for Phase 8)_
