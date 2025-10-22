# Round History Feature - Implementation Guide

## Overview
This document provides step-by-step instructions to complete the round history persistence and admin viewing feature.

**Status**: Database layer complete (30% done). API and frontend remain.

---

## What's Already Done ✅

### 1. Database Schema
**File**: `backend/app/db/models.py`
- Added `RoundHistoryModel` class (lines 117-156)
- Fields: game_id, round_number, dealer, bid_winner, bid_value, trump, round_data (JSON)
- Migration created and applied: `e74120476dcd_add_round_history_table.py`

### 2. Repository Layer
**File**: `backend/app/db/repository.py`
- Added `RoundHistoryRepository` class (lines 301-363)
- Methods available:
  - `save_round()` - Save completed round
  - `get_rounds_for_game()` - Get all rounds for a game
  - `get_round()` - Get specific round
  - `get_round_count()` - Count rounds

### 3. In-Memory Tracking
**File**: `backend/app/game/session.py`
- `GameSession.rounds_history` field exists (line 90)
- `start_round()` already populates this list (lines 122-150)
- Data structure ready for persistence

---

## What Needs to Be Done 📋

### Step 1: Save Rounds to Database When They Complete

**Goal**: When a round ends and `start_round()` is called for a new round, save the completed round to the database.

**File to Modify**: `backend/app/api/v1/websocket.py` or create new persistence helper

**Current Situation**:
- `GameSession.start_round()` builds round data and appends to `self.rounds_history` (in-memory only)
- The WebSocket handler doesn't currently save this to the database

**Implementation Option A - Add to WebSocket Handler**:

Location: After any action that might trigger a new round (e.g., after scoring phase)

```python
# In websocket.py, after game state changes that complete a round
from app.db.config import get_db
from app.db.repository import RoundHistoryRepository

async def _save_completed_rounds(game_id: str, session: GameSession):
    """Save any new rounds to the database."""
    # Get count of rounds in DB
    async for db in get_db():
        round_repo = RoundHistoryRepository(db)
        db_round_count = await round_repo.get_round_count(game_id)

        # Save any rounds that aren't in the DB yet
        for round_data in session.rounds_history[db_round_count:]:
            await round_repo.save_round(
                game_id=game_id,
                round_number=round_data['round_number'],
                dealer=round_data['dealer'],
                bid_winner=round_data['bid_winner'],
                bid_value=round_data['bid_value'],
                trump=round_data['trump'],
                round_data={
                    'captured_tricks': round_data['captured_tricks'],
                    'points_by_seat': round_data['points_by_seat'],
                    'team_scores': round_data['team_scores'],
                }
            )
        break  # Exit after first iteration
```

Then call this function after state changes in the WebSocket message handler:
```python
# In handle_client_message(), after processing actions
if sess.state == 'round_end' or sess.rounds_history:
    await _save_completed_rounds(game_id, sess)
```

**Implementation Option B - Add to Persistence Layer**:

Modify `backend/app/db/persistence.py` to save rounds as part of `save_game()`:

```python
# In SessionPersistence.save_game()
from app.db.repository import RoundHistoryRepository

async def save_game(self, session: GameSession):
    # ... existing code ...

    # Save round history
    round_repo = RoundHistoryRepository(self.db_session)
    db_round_count = await round_repo.get_round_count(session.game_id)

    # Save any new rounds
    for round_data in session.rounds_history[db_round_count:]:
        await round_repo.save_round(
            game_id=session.game_id,
            round_number=round_data['round_number'],
            dealer=round_data['dealer'],
            bid_winner=round_data['bid_winner'],
            bid_value=round_data['bid_value'],
            trump=round_data['trump'],
            round_data={
                'captured_tricks': round_data['captured_tricks'],
                'points_by_seat': round_data['points_by_seat'],
                'team_scores': round_data['team_scores'],
            }
        )
```

**Recommended**: Option B is cleaner - centralize persistence logic.

---

### Step 2: Add Admin API Endpoints

**File to Modify**: `backend/app/api/v1/admin.py`

Add two new endpoints for viewing game history.

#### Endpoint 1: List All Games

```python
from app.db.repository import GameRepository, PlayerRepository, RoundHistoryRepository

@router.get("/games")
async def list_games(
    state: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """
    List all games with summary information.

    Query params:
    - state: Filter by game state (lobby, playing, completed, etc.)
    - limit: Max games to return (default 50)
    - offset: Pagination offset (default 0)
    """
    verify_admin_credentials(credentials)

    async for db in get_db():
        game_repo = GameRepository(db)
        player_repo = PlayerRepository(db)
        round_repo = RoundHistoryRepository(db)

        # Get all games (or filter by state)
        if state:
            result = await db.execute(
                select(GameModel)
                .where(GameModel.state == state)
                .order_by(GameModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            result = await db.execute(
                select(GameModel)
                .order_by(GameModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

        games = result.scalars().all()

        # Build response with summary data
        games_list = []
        for game in games:
            players = await player_repo.get_players_for_game(game.id)
            round_count = await round_repo.get_round_count(game.id)

            games_list.append({
                'game_id': game.id,
                'short_code': game.short_code,
                'mode': game.mode,
                'seats': game.seats,
                'state': game.state,
                'player_count': len(players),
                'players': [{'name': p.name, 'seat': p.seat, 'is_bot': p.is_bot} for p in players],
                'rounds_played': round_count,
                'created_at': game.created_at.isoformat(),
                'last_activity': game.last_activity_at.isoformat(),
            })

        return {'games': games_list, 'total': len(games_list)}
```

#### Endpoint 2: Get Game Detail with Rounds

```python
@router.get("/games/{game_id}")
async def get_game_detail(
    game_id: str,
    credentials: HTTPBasicCredentials = Depends(security),
):
    """
    Get detailed information about a specific game including all rounds.

    Returns:
    - Game metadata
    - All players
    - All completed rounds with full trick/card data
    """
    verify_admin_credentials(credentials)

    async for db in get_db():
        game_repo = GameRepository(db)
        player_repo = PlayerRepository(db)
        round_repo = RoundHistoryRepository(db)

        # Get game
        game = await game_repo.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Get players
        players = await player_repo.get_players_for_game(game_id)

        # Get all rounds
        rounds = await round_repo.get_rounds_for_game(game_id)

        # Parse round data from JSON
        rounds_data = []
        for round_model in rounds:
            round_data_parsed = json.loads(round_model.round_data)
            rounds_data.append({
                'round_number': round_model.round_number,
                'dealer': round_model.dealer,
                'bid_winner': round_model.bid_winner,
                'bid_value': round_model.bid_value,
                'trump': round_model.trump,
                'captured_tricks': round_data_parsed['captured_tricks'],
                'points_by_seat': round_data_parsed['points_by_seat'],
                'team_scores': round_data_parsed['team_scores'],
                'created_at': round_model.created_at.isoformat(),
            })

        return {
            'game': {
                'game_id': game.id,
                'short_code': game.short_code,
                'mode': game.mode,
                'seats': game.seats,
                'state': game.state,
                'created_at': game.created_at.isoformat(),
                'updated_at': game.updated_at.isoformat(),
                'last_activity': game.last_activity_at.isoformat(),
            },
            'players': [
                {
                    'player_id': p.player_id,
                    'name': p.name,
                    'seat': p.seat,
                    'is_bot': p.is_bot,
                    'joined_at': p.joined_at.isoformat(),
                }
                for p in players
            ],
            'rounds': rounds_data,
        }
```

Don't forget to add imports at the top:
```python
import json
from typing import Optional
from sqlalchemy import select
from app.db.models import GameModel
```

---

### Step 3: Frontend - Admin History Page

**Goal**: Create a new admin page that lists all games and allows clicking to view details.

#### 3.1: Create GameHistoryPage Component

**File to Create**: `frontend/src/pages/AdminGameHistoryPage.tsx`

```typescript
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { adminApi } from '../api';
import { useAuthStore } from '../stores';
import { Loading, Button, Badge, Card } from '../components/ui';

interface GameSummary {
  game_id: string;
  short_code: string;
  mode: string;
  seats: number;
  state: string;
  player_count: number;
  players: { name: string; seat: number; is_bot: boolean }[];
  rounds_played: number;
  created_at: string;
  last_activity: string;
}

export default function AdminGameHistoryPage() {
  const navigate = useNavigate();
  const { username, password, isAuthenticated } = useAuthStore();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState<string>('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/admin');
      return;
    }
    loadGames();
  }, [isAuthenticated, stateFilter]);

  const loadGames = async () => {
    setLoading(true);
    setError(null);
    try {
      // You'll need to add this method to adminApi
      const response = await fetch(
        `/api/v1/admin/games${stateFilter ? `?state=${stateFilter}` : ''}`,
        {
          headers: {
            'Authorization': `Basic ${btoa(`${username}:${password}`)}`,
          },
        }
      );

      if (!response.ok) throw new Error('Failed to load games');

      const data = await response.json();
      setGames(data.games);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <Loading text="Loading game history..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold">Game History</h1>
          <Button variant="secondary" onClick={() => navigate('/admin')}>
            Back to Dashboard
          </Button>
        </div>

        {/* Filters */}
        <div className="mb-6 flex gap-2">
          <Button
            variant={stateFilter === '' ? 'primary' : 'secondary'}
            onClick={() => setStateFilter('')}
          >
            All
          </Button>
          <Button
            variant={stateFilter === 'completed' ? 'primary' : 'secondary'}
            onClick={() => setStateFilter('completed')}
          >
            Completed
          </Button>
          <Button
            variant={stateFilter === 'play' ? 'primary' : 'secondary'}
            onClick={() => setStateFilter('play')}
          >
            Active
          </Button>
          <Button
            variant={stateFilter === 'lobby' ? 'primary' : 'secondary'}
            onClick={() => setStateFilter('lobby')}
          >
            Lobby
          </Button>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Games List */}
        <div className="space-y-4">
          {games.map((game) => (
            <Card
              key={game.game_id}
              padding="md"
              className="cursor-pointer hover:ring-2 hover:ring-primary-500 transition-all"
              onClick={() => navigate(`/admin/games/${game.game_id}`)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <code className="font-mono font-bold text-lg">
                      {game.short_code}
                    </code>
                    <Badge variant="info">{game.mode}</Badge>
                    <Badge variant={
                      game.state === 'completed' ? 'success' :
                      game.state === 'play' ? 'primary' : 'secondary'
                    }>
                      {game.state}
                    </Badge>
                  </div>
                  <div className="text-sm text-slate-400">
                    <span>{game.player_count}/{game.seats} players</span>
                    <span className="mx-2">•</span>
                    <span>{game.rounds_played} rounds</span>
                    <span className="mx-2">•</span>
                    <span>Created: {new Date(game.created_at).toLocaleString()}</span>
                  </div>
                  <div className="mt-2 flex gap-2">
                    {game.players.map((player, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2 py-1 bg-slate-700 rounded"
                      >
                        {player.name} {player.is_bot && '(Bot)'}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-primary-400">→</div>
              </div>
            </Card>
          ))}
        </div>

        {games.length === 0 && !loading && (
          <div className="text-center py-12 text-slate-400">
            No games found
          </div>
        )}
      </div>
    </div>
  );
}
```

#### 3.2: Create Game Detail Page

**File to Create**: `frontend/src/pages/AdminGameDetailPage.tsx`

```typescript
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useAuthStore } from '../stores';
import { Loading, Button, Card, Badge } from '../components/ui';

interface GameDetail {
  game: {
    game_id: string;
    short_code: string;
    mode: string;
    seats: number;
    state: string;
    created_at: string;
    updated_at: string;
    last_activity: string;
  };
  players: Array<{
    player_id: string;
    name: string;
    seat: number;
    is_bot: boolean;
    joined_at: string;
  }>;
  rounds: Array<{
    round_number: number;
    dealer: number;
    bid_winner: number | null;
    bid_value: number | null;
    trump: string | null;
    captured_tricks: Array<any>;
    points_by_seat: Record<number, number>;
    team_scores: any;
    created_at: string;
  }>;
}

export default function AdminGameDetailPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { username, password, isAuthenticated } = useAuthStore();
  const [gameDetail, setGameDetail] = useState<GameDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/admin');
      return;
    }
    loadGameDetail();
  }, [gameId, isAuthenticated]);

  const loadGameDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/admin/games/${gameId}`, {
        headers: {
          'Authorization': `Basic ${btoa(`${username}:${password}`)}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load game detail');

      const data = await response.json();
      setGameDetail(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPlayerName = (seat: number) => {
    const player = gameDetail?.players.find(p => p.seat === seat);
    return player?.name || `Seat ${seat + 1}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <Loading text="Loading game details..." />
      </div>
    );
  }

  if (error || !gameDetail) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Game not found'}</p>
          <Button onClick={() => navigate('/admin/history')}>
            Back to History
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">{gameDetail.game.short_code}</h1>
            <p className="text-slate-400 mt-1">Game Details</p>
          </div>
          <Button variant="secondary" onClick={() => navigate('/admin/history')}>
            Back to History
          </Button>
        </div>

        {/* Game Info */}
        <Card padding="md" className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Game Information</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-slate-400 text-sm">Mode</p>
              <p className="font-semibold">{gameDetail.game.mode}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">State</p>
              <Badge variant="info">{gameDetail.game.state}</Badge>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Seats</p>
              <p className="font-semibold">{gameDetail.game.seats}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Rounds Played</p>
              <p className="font-semibold">{gameDetail.rounds.length}</p>
            </div>
          </div>
        </Card>

        {/* Players */}
        <Card padding="md" className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Players</h2>
          <div className="space-y-2">
            {gameDetail.players.map((player) => (
              <div
                key={player.player_id}
                className="flex items-center justify-between bg-slate-700/50 rounded px-4 py-2"
              >
                <div>
                  <span className="font-semibold">{player.name}</span>
                  {player.is_bot && (
                    <Badge variant="secondary" className="ml-2">Bot</Badge>
                  )}
                </div>
                <span className="text-slate-400">Seat {player.seat + 1}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Rounds */}
        <Card padding="md">
          <h2 className="text-xl font-semibold mb-4">Round History</h2>
          {gameDetail.rounds.length === 0 ? (
            <p className="text-slate-400 text-center py-8">No rounds played yet</p>
          ) : (
            <div className="space-y-6">
              {gameDetail.rounds.map((round) => (
                <div
                  key={round.round_number}
                  className="border border-slate-700 rounded-lg p-4"
                >
                  {/* Round Header */}
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">
                      Round {round.round_number}
                    </h3>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-slate-400">
                        Dealer: {getPlayerName(round.dealer)}
                      </span>
                      {round.trump && (
                        <span className="text-2xl">{round.trump}</span>
                      )}
                    </div>
                  </div>

                  {/* Round Info */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-slate-400 text-sm">Bid Winner</p>
                      <p className="font-semibold">
                        {round.bid_winner !== null
                          ? getPlayerName(round.bid_winner)
                          : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-sm">Bid Value</p>
                      <p className="font-semibold">{round.bid_value ?? 'N/A'}</p>
                    </div>
                  </div>

                  {/* Team Scores */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-700/50 rounded px-4 py-3">
                      <p className="text-slate-400 text-sm">Team 1 Score</p>
                      <p className="text-2xl font-bold">
                        {round.team_scores.team_points[0]}
                      </p>
                    </div>
                    <div className="bg-slate-700/50 rounded px-4 py-3">
                      <p className="text-slate-400 text-sm">Team 2 Score</p>
                      <p className="text-2xl font-bold">
                        {round.team_scores.team_points[1]}
                      </p>
                    </div>
                  </div>

                  {/* Tricks */}
                  <div>
                    <p className="text-sm font-semibold mb-2">
                      Tricks Won: {round.captured_tricks.length}
                    </p>
                    <div className="space-y-2">
                      {round.captured_tricks.map((trick, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-700/30 rounded px-3 py-2 text-sm"
                        >
                          <div className="flex items-center justify-between">
                            <span>
                              #{idx + 1} - {getPlayerName(trick.winner)}
                            </span>
                            <Badge variant="success">{trick.points} pts</Badge>
                          </div>
                          <div className="mt-2 flex gap-2 flex-wrap">
                            {trick.cards.map((cardPlay: any, cardIdx: number) => (
                              <span
                                key={cardIdx}
                                className="text-xs px-2 py-1 bg-slate-600 rounded"
                              >
                                {getPlayerName(cardPlay.seat)}: {cardPlay.card.rank}{cardPlay.card.suit}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
```

#### 3.3: Add Routes

**File to Modify**: `frontend/src/App.tsx`

Add the new routes:
```typescript
import AdminGameHistoryPage from './pages/AdminGameHistoryPage';
import AdminGameDetailPage from './pages/AdminGameDetailPage';

// In your routes:
<Route path="/admin/history" element={<AdminGameHistoryPage />} />
<Route path="/admin/games/:gameId" element={<AdminGameDetailPage />} />
```

#### 3.4: Add Link in Admin Dashboard

**File to Modify**: `frontend/src/pages/AdminPage.tsx`

Add a "View Game History" button in the AdminDashboard component:

```typescript
<button
  onClick={() => onNavigateHistory()}
  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
>
  View Game History
</button>
```

And pass the handler:
```typescript
interface AdminDashboardProps {
  username: string;
  onLogout: () => void;
  onNavigateHome: () => void;
  onNavigateHistory: () => void; // Add this
}

// In AdminPage component:
<AdminDashboard
  username={username || ''}
  onLogout={logout}
  onNavigateHome={() => navigate('/')}
  onNavigateHistory={() => navigate('/admin/history')} // Add this
/>
```

---

## Testing Checklist

After implementing:

1. **Database Persistence**
   - [ ] Play a complete round
   - [ ] Check database: `SELECT * FROM round_history;`
   - [ ] Verify JSON data is complete
   - [ ] Play multiple rounds, ensure all saved

2. **API Endpoints**
   - [ ] Test `GET /api/v1/admin/games` with Postman/curl
   - [ ] Test with different state filters
   - [ ] Test `GET /api/v1/admin/games/{game_id}`
   - [ ] Verify all round data is returned

3. **Frontend**
   - [ ] Access `/admin/history`
   - [ ] See list of games
   - [ ] Click on a game
   - [ ] See full round details with cards
   - [ ] Verify all data displays correctly

---

## Files Reference

### Backend Files Modified/Created:
- ✅ `backend/app/db/models.py` - Added RoundHistoryModel
- ✅ `backend/app/db/repository.py` - Added RoundHistoryRepository
- ⏳ `backend/app/db/persistence.py` - Add round saving to save_game()
- ⏳ `backend/app/api/v1/admin.py` - Add two new endpoints

### Frontend Files Created:
- ⏳ `frontend/src/pages/AdminGameHistoryPage.tsx`
- ⏳ `frontend/src/pages/AdminGameDetailPage.tsx`
- ⏳ `frontend/src/App.tsx` - Add routes

### Frontend Files Modified:
- ⏳ `frontend/src/pages/AdminPage.tsx` - Add history button

---

## Notes

- The database schema supports trump as a single character (suit symbol)
- Round data is stored as JSON for flexibility
- The frontend displays rounds in chronological order
- Each trick shows which player won and what cards were played
- Team scores show the bid outcome (success/failure)

---

## Future Enhancements

Once this is working, you could add:
- Export game history to CSV/JSON
- Replay functionality (step through tricks)
- Statistics dashboard (win rates, average scores, etc.)
- Search/filter by player name
- Pagination for large game lists

---

**Status**: 30% Complete
**Next Steps**: Implement Step 1 (save rounds to DB), then Steps 2-3 (API + Frontend)
