# Thurup - Manual Testing Guide

This guide walks you through testing all features of the Thurup card game application.

## Prerequisites

Make sure both servers are running:

```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Automated Testing

The project includes both automated unit/integration tests and end-to-end tests to ensure code quality and catch regressions early.

### Backend Tests (pytest)

**Run all backend tests:**
```bash
cd backend
uv run pytest -v
```

**Run with coverage:**
```bash
uv run pytest --cov=app --cov-report=html
```

**Current status:**
- 331 tests passing
- 76% code coverage
- Test files: `backend/tests/`

### Frontend E2E Tests (Playwright)

**Prerequisites:**
- Backend must be running on port 18081
- Frontend must be running on port 5173

**Run E2E tests:**
```bash
cd frontend
npm run test:e2e
```

**Run with UI mode (interactive):**
```bash
npm run test:e2e:ui
```

**Run specific test:**
```bash
npx playwright test tests/e2e/game-flow.spec.ts
```

**Current status:**
- 13 test scenarios
- 10 passing (77% success rate)
- 3 tests fail intermittently due to bot addition timing
- Test files: `frontend/tests/e2e/`

**Test scenarios covered:**
- ✅ Game creation and lobby flow
- ✅ Bot player addition
- ✅ Game start with full player count
- ✅ Session persistence on page refresh
- ✅ Bidding phase interactions
- ✅ Card display in hand
- ✅ Real-time WebSocket updates
- ⚠️ Rapid bot addition (timing issues)
- ⚠️ Complete game flow (timing issues)

**Known issues:**
- Bot addition tests need longer wait times (currently 2000ms)
- CI/CD environments may need adjusted timeouts
- WebSocket reconnection timing can cause flakiness

**Test reports:**
- HTML report: `frontend/playwright-report/index.html`
- Test results: `frontend/test-results/`

---

## Test Flow 1: Create and Play a Game (Solo with Bots)

### 1.1 Create a New Game

1. **Open the app**: Navigate to http://localhost:5173
2. **Home Page** should show:
   - Title: "Thurup"
   - Subtitle: "The classic 28/56 card game"
   - Create New Game form
   - Quick links to History and Admin

3. **Fill in the form:**
   - Your Name: Enter "Player 1"
   - Game Mode: Select "28 (4 Players)"
   - Click "Create Game" button

4. **Expected Result:**
   - Success toast message: "Game created!"
   - Redirect to game page: `/game/[game-id]`

### 1.2 Game Lobby

1. **Lobby Panel** should show:
   - Game ID (truncated)
   - Mode: 28
   - Players: 1 / 4
   - Your player card with:
     - Seat number: 0
     - Your name: "Player 1"
   - 3 empty seat placeholders

2. **Add 3 Bot Players:**
   - Click "Add Bot Player" button 3 times
   - After each click:
     - Player count should increment
     - New bot player card appears (Bot 1, Bot 2, Bot 3)
     - Bot indicator icon shown

3. **Start the Game:**
   - "Start Game" button should be enabled (requires 2+ players)
   - Click "Start Game"
   - Game state should change to "bidding"

### 1.3 Bidding Phase

1. **Game Board** should show:
   - Central play area
   - 4 player positions around the circle (bottom=you, top, left, right)
   - Player names and seat numbers

2. **Sidebar** shows:
   - Score Board with all players (0 points each)
   - Bidding Panel (if it's your turn)

3. **When it's YOUR turn:**
   - "Your Turn" badge appears (animated pulse)
   - Bidding Panel shows:
     - Minimum bid: 16
     - Quick bid buttons: 16, 20, 24, 28
     - Custom bid input (16-28)
     - Pass button (red)

4. **Place a Bid:**
   - Click "Bid 20" or enter custom bid
   - Success toast: "Bid placed"
   - Wait for bots to bid (they bid automatically)
   - Bidding continues around the table

5. **Bidding completes when:**
   - One player bids and all others pass, OR
   - Maximum bid (28) is reached

### 1.4 Trump Selection

1. **If you won the bidding:**
   - Trump Panel appears
   - Shows 4 suit buttons: ♠ Spades, ♥ Hearts, ♦ Diamonds, ♣ Clubs
   - Message: "You won the bidding! Choose your trump suit:"

2. **Choose Trump:**
   - Click any suit button
   - Trump suit is set
   - Game moves to "playing" phase

3. **If bot won:**
   - Trump Panel shows waiting message
   - Bot automatically chooses trump
   - You'll see the trump suit in the score board

### 1.5 Playing Phase

1. **Your Hand** appears at bottom:
   - Shows your 8 cards (for 28 mode)
   - Cards are displayed in a fan layout
   - Playable cards have green indicator dot

2. **Play Cards:**
   - Click a playable card to play it
   - Card moves to center trick area
   - Bots play automatically in turn
   - Trick winner collects cards

3. **Score Updates:**
   - Score Board updates after each trick
   - Shows points won by each team
   - Shows trump suit

4. **Game Progress:**
   - Play continues until all cards are played
   - Watch the bots make their moves
   - Final scores calculated

### 1.6 Game Completion

1. **Game ends:**
   - Final scores displayed
   - Winner announced
   - Game state changes to "completed"

---

## Test Flow 2: Multiplayer Game (Multiple Browser Windows)

### 2.1 Create Game (Player 1)

1. **Browser Window 1**: http://localhost:5173
2. Create game as "Alice"
3. **Copy the Game URL** from the Share section in Lobby Panel
   - Example: `http://localhost:5173/game/abc123...`

### 2.2 Join Game (Player 2)

1. **Open Incognito/Private Window** (or different browser)
2. **Paste the Game URL** you copied
3. Fill in name: "Bob"
4. Click "Join Game" if prompted, or it auto-joins

### 2.3 Join Game (Players 3 & 4)

1. Repeat for 2 more players or add bots
2. All players should see the lobby update in real-time (WebSocket)

### 2.4 Play Together

1. **Player 1** starts the game
2. **All browsers update simultaneously** (WebSocket sync)
3. Each player sees "Your Turn" indicator when it's their turn
4. Other players see "Waiting..." message
5. Cards appear only in your hand (hidden from others)
6. Played cards visible to all in center area

---

## Test Flow 3: Game History & Replay

### 3.1 View Game History

1. **From Home Page:** Click "Game History" button
2. **History Page** shows:
   - List of all games
   - Filter buttons: All Games, Completed, Active
   - Each game card shows:
     - Game ID
     - State badge (lobby/active/completed)
     - Mode badge (28/56)
     - Player count
     - Creation date
     - Player list (first 4 + count)
     - Replay/Join button

3. **Filter Games:**
   - Click "Completed" - shows only finished games
   - Click "Active" - shows ongoing games
   - Click "All Games" - shows everything

4. **Click on a Game Card:**
   - If completed: Navigate to Replay page
   - If active: Navigate to Game page (rejoin)

### 3.2 Watch Game Replay

1. **Click "Replay"** on a completed game
2. **Replay Page** shows:
   - Game board showing snapshot state
   - Score board
   - Timeline controls at bottom
   - Snapshot counter: "Snapshot X / Y"

3. **Timeline Controls:**
   - **⏮️ First Button**: Jump to first snapshot
   - **⏪ Previous Button**: Go back one snapshot
   - **▶️/⏸️ Play/Pause Button**: Auto-play through snapshots
   - **⏩ Next Button**: Go forward one snapshot
   - **⏭️ Last Button**: Jump to last snapshot
   - **Speed Button**: Toggle speed (0.5x → 1x → 2x)

4. **Scrub Timeline:**
   - Drag the slider to any point
   - Game board updates to show that state
   - Snapshot info updates (phase, reason, timestamp)

5. **Watch Auto-Play:**
   - Click Play button
   - Snapshots advance automatically (2 seconds per snapshot at 1x speed)
   - Adjust speed to 2x for faster replay
   - Pause at any time

6. **Snapshot Info Panel:**
   - Phase: bidding, trump_choice, playing, etc.
   - Reason: bid_placed, trump_chosen, card_played, etc.
   - Timestamp: When snapshot was created

---

## Test Flow 4: Admin Dashboard

### 4.1 Access Admin Panel

1. **From Home Page:** Click "Admin Panel" button
2. **Login Screen** appears:
   - Username field
   - Password field

3. **Login Credentials:**
   - Username: `admin` (default, or check your `.env`)
   - Password: `admin` (default, or check your `.env`)

4. **Click "Login"**
   - If credentials correct: Dashboard loads
   - If incorrect: Error message appears

### 4.2 Server Health Metrics

1. **Server Health Section** shows:
   - Status badge: "healthy" (green) or "degraded" (yellow)
   - 5 metric cards:
     - **Uptime**: Server uptime in hours/minutes
     - **Sessions**: Number of active game sessions in memory
     - **Connections**: Total WebSocket connections
     - **Bot Tasks**: Number of running bot tasks
     - **Database**: Connection status (✓ or ✗)

2. **Metrics auto-refresh** every 10 seconds

### 4.3 Database Statistics

1. **Database Stats Section** shows:
   - **Total Games**: All games in database
   - **Total Players**: All player records
   - **Snapshots**: Total game state snapshots
   - **DB Size**: Database file size in MB

2. **Trigger Cleanup Button:**
   - Click "Trigger Cleanup"
   - Confirmation dialog appears
   - Confirm to delete old/stale games
   - Alert shows: "Cleanup completed: X games deleted"
   - Stats refresh automatically

### 4.4 Active Sessions Management

1. **Active Sessions Section** shows:
   - Session count in header
   - List of all active game sessions

2. **Each Session Card** displays:
   - Game ID (truncated, monospace font)
   - State badge: lobby/bidding/playing/completed
   - Mode: 28 or 56
   - Player count / Seats
   - Connection count
   - Connected seats: [0, 1, 2, 3]
   - "Bot Active" indicator if bot is running
   - Action buttons: Save, Delete

3. **Save Button:**
   - Forces immediate save of game state to database
   - Useful for debugging or manual backups
   - Success message appears

4. **Delete Button:**
   - Confirmation dialog: "Are you sure?"
   - Deletes session from memory and database
   - Session removed from list

5. **Refresh Button:**
   - Manually refresh session list
   - Useful to see changes immediately

### 4.5 Logout

1. Click "Logout" button in header
2. Redirected to login screen
3. Credentials cleared

---

## Test Flow 5: Edge Cases & Error Handling

### 5.1 Network Disconnection

1. **During active game:**
   - Disconnect WiFi/network
   - "Disconnected" badge appears
   - WebSocket attempts reconnection (up to 5 times)
   - Reconnect network
   - Connection restored automatically
   - Game state syncs from server

### 5.2 Invalid Game ID

1. Navigate to: `http://localhost:5173/game/invalid-id-123`
2. Loading spinner appears
3. After timeout: Error state or redirect to home

### 5.3 Full Game (All Seats Taken)

1. Create game with 4 seats
2. Add 4 players (fill all seats)
3. Try to join with 5th player using game URL
4. Should show error: "Game is full"

### 5.4 Invalid Bids

1. During bidding, try to:
   - Bid below minimum (should be rejected)
   - Bid below current high bid (should be rejected)
   - Bid when not your turn (buttons disabled)

### 5.5 Invalid Card Plays

1. During playing phase:
   - Try to play card when not your turn (button disabled)
   - Try to play card that doesn't follow suit rules (should be non-playable)

---

## Test Flow 6: UI Components & Interactions

### 6.1 Toast Notifications

Watch for toasts appearing in various scenarios:
- Success toasts (green): Game created, bid placed, trump chosen
- Error toasts (red): Failed actions, invalid inputs
- Warning toasts (yellow): Network issues
- Info toasts (blue): General information
- Toasts auto-dismiss after 4 seconds

### 6.2 Loading States

Verify loading spinners appear:
- Creating game
- Loading game state
- Loading history
- Loading replay data
- Admin dashboard loading

### 6.3 Responsive Design

Test on different screen sizes:
1. **Desktop (1920x1080)**: Full layout with sidebar
2. **Tablet (768px)**: Grid layout adjusts
3. **Mobile (375px)**: Single column, stacked layout

### 6.4 Dark Theme

All pages use dark theme:
- Background: Dark slate gradient
- Cards: Semi-transparent dark with glassmorphism
- Text: White/light gray
- Accent: Primary color (blue/purple)

---

## Test Flow 7: Database Persistence

### 7.1 Game Recovery After Server Restart

1. **Create and start a game** (get to playing phase)
2. **Stop backend server** (Ctrl+C in backend terminal)
3. **Restart backend server**
4. **Refresh frontend** in browser
5. **Expected**: Game state restored from database
6. **Check**: All player hands, scores, trump suit preserved

### 7.2 Snapshot History

1. Play through a game
2. Go to Admin → Database Stats
3. Note snapshot count increasing
4. Go to History → View completed game replay
5. Verify all snapshots captured

---

## Test Flow 8: Bot Behavior

### 8.1 Bot Bidding

1. Create game with 3 bots
2. Start game
3. Watch bots bid automatically
4. Bots should:
   - Bid reasonable values
   - Pass when appropriate
   - Make decisions within ~1 second

### 8.2 Bot Card Play

1. During playing phase with bots
2. Bots should:
   - Play valid cards automatically
   - Follow suit rules
   - Play within ~1-2 seconds
   - Make strategic decisions

---

## Troubleshooting

### Frontend Won't Load

```bash
# Check if Vite is running
curl http://localhost:5173

# Restart frontend
cd frontend
npm run dev
```

### Backend Won't Respond

```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart backend
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### WebSocket Connection Failed

1. Check browser console for errors
2. Verify backend WebSocket endpoint: `ws://localhost:8000/api/v1/game/ws/{game_id}`
3. Check CORS settings in backend
4. Try clearing browser cache

### Database Issues

```bash
# Check database file exists
ls backend/thurup.db

# View recent logs
cd backend
uv run alembic history

# Reset database (WARNING: deletes all data)
rm backend/thurup.db
cd backend
uv run alembic upgrade head
```

---

## API Testing (Optional)

### Using Swagger UI

1. Navigate to: http://localhost:8000/docs
2. Interactive API documentation (Swagger/OpenAPI)
3. Test endpoints directly:
   - POST `/api/v1/game/create`
   - POST `/api/v1/game/{game_id}/join`
   - GET `/api/v1/history/games`
   - GET `/api/v1/admin/health` (requires auth)

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Create game
curl -X POST http://localhost:8000/api/v1/game/create \
  -H "Content-Type: application/json" \
  -d '{"mode": "28", "seats": 4}'

# Get game history
curl http://localhost:8000/api/v1/history/games

# Admin health (with auth)
curl -u admin:admin http://localhost:8000/api/v1/admin/health
```

---

## Success Criteria Checklist

Use this checklist to verify all features work:

### Core Gameplay
- [ ] Create game with player name
- [ ] Join game from shared URL
- [ ] Add bot players
- [ ] Start game (transition to bidding)
- [ ] Place bids (quick and custom)
- [ ] Pass on bidding
- [ ] Choose trump suit
- [ ] Play cards from hand
- [ ] See cards in trick area
- [ ] Score updates correctly
- [ ] Game completes successfully

### Multiplayer
- [ ] Multiple players can join
- [ ] Real-time updates via WebSocket
- [ ] Turn indicators work correctly
- [ ] Each player sees only their cards
- [ ] Disconnection/reconnection works

### History & Replay
- [ ] View game history list
- [ ] Filter by state (all/completed/active)
- [ ] Click to view replay
- [ ] Timeline controls work (play/pause/step)
- [ ] Scrub timeline with slider
- [ ] Speed adjustment works
- [ ] Snapshot info displays correctly

### Admin Dashboard
- [ ] Login with credentials
- [ ] Server health metrics display
- [ ] Database stats display
- [ ] Active sessions list
- [ ] Force save session
- [ ] Delete session
- [ ] Trigger cleanup
- [ ] Auto-refresh every 10s
- [ ] Logout works

### UI/UX
- [ ] Toast notifications appear
- [ ] Loading states display
- [ ] Error messages helpful
- [ ] Responsive on mobile/tablet
- [ ] Dark theme consistent
- [ ] Icons and badges clear
- [ ] Buttons disabled when appropriate

### Persistence
- [ ] Game survives server restart
- [ ] Snapshots saved correctly
- [ ] Database grows appropriately
- [ ] Cleanup deletes old games

---

## Known Limitations

1. **Browser Compatibility**: Tested on Chrome/Firefox/Safari (latest). IE not supported.
2. **Network Latency**: WebSocket updates may have slight delay on slow connections.
3. **Bot AI**: Uses simple random strategy, not advanced AI.
4. **Mobile**: Touch interactions work but optimized for desktop.
5. **Max Players**: 28 mode = 4 players, 56 mode = 4 or 6 players.

---

## Next Steps After Testing

1. **Report Issues**: If you find bugs, check browser console and backend logs
2. **Performance**: Monitor with large number of games in history
3. **Load Testing**: Test with multiple concurrent games
4. **Production**: Set up proper authentication (not just Basic Auth)
5. **Deployment**: Configure for production (environment variables, HTTPS, etc.)

---

**Happy Testing! 🎮**

For questions or issues, refer to:
- `docs/ARCHITECTURE.md` - Technical details
- `docs/PROJECT_LOG.md` - Development history
- `README.md` - Project overview
