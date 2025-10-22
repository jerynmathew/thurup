# Frontend Testing Roadmap

This document outlines the testing strategy for remaining untested code in the Thurup frontend application.

## Current Status

**Overall Coverage**: 26.8% (253 tests passing)

### Completed ✅
- ✅ All UI components (100% coverage)
- ✅ API clients (82.14% coverage)
- ✅ Session manager utility (95.23% coverage)
- ✅ Basic game components (PlayerHand, LobbyPanel, BiddingPanel, TrumpPanel)
- ✅ State management stores (82.12% coverage)

### Remaining Work 🔄

## 1. Page Components (0% coverage)

**Files to Test:**
- `src/pages/GamePage.tsx` (352 lines)
- `src/pages/HomePage.tsx` (253 lines)
- `src/pages/AdminPage.tsx` (396 lines)
- `src/pages/AdminGameHistoryPage.tsx` (322 lines)
- `src/pages/HistoryPage.tsx` (180 lines)
- `src/pages/ReplayPage.tsx` (268 lines)
- `src/pages/NotFoundPage.tsx` (27 lines)

### Recommended Approach: E2E Testing with Playwright

**Why E2E over Unit Tests:**
- Pages are integration points combining multiple components
- Heavy reliance on routing, navigation, and URL parameters
- Real WebSocket connections and API interactions
- User flows span multiple pages

**Setup:**
```bash
# Playwright is already installed
npm run test:e2e  # Will need to be configured
```

**Test Structure:**
```typescript
// tests/e2e/game-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Game Flow', () => {
  test('should create and join a game', async ({ page }) => {
    await page.goto('/');

    // Create game
    await page.fill('[name="playerName"]', 'Alice');
    await page.click('text=Create Game');

    // Wait for redirect to game page
    await expect(page).toHaveURL(/\/game\/.+/);

    // Verify lobby shows player
    await expect(page.locator('text=Alice')).toBeVisible();
  });

  test('should handle page refresh in game', async ({ page, context }) => {
    // Create game and join
    await page.goto('/');
    await page.fill('[name="playerName"]', 'Bob');
    await page.click('text=Create Game');

    const gameUrl = page.url();

    // Refresh page
    await page.reload();

    // Should restore session and show player
    await expect(page.locator('text=Bob')).toBeVisible();
  });
});
```

**Test Files to Create:**
1. `tests/e2e/home-page.spec.ts` - Create/join game flows
2. `tests/e2e/game-page.spec.ts` - Game lobby, bidding, playing, scoring
3. `tests/e2e/admin-page.spec.ts` - Admin dashboard, session management
4. `tests/e2e/history-page.spec.ts` - Game history browsing
5. `tests/e2e/replay-page.spec.ts` - Replay playback
6. `tests/e2e/navigation.spec.ts` - Routing, 404 handling

**Estimated Effort:** 2-3 days

---

## 2. WebSocket Hooks (0% coverage)

**Files to Test:**
- `src/hooks/useGame.ts` (278 lines)
- `src/hooks/useGameSocket.tsx` (142 lines)

### Recommended Approach: Integration Tests with Mock WebSocket Server

**Why Mock WebSocket:**
- WebSocket behavior is complex (connect, disconnect, reconnect, errors)
- Need to test message handling without real backend
- Can simulate network conditions and edge cases

**Setup:**
```bash
npm install -D vitest-websocket-mock
```

**Test Structure:**
```typescript
// src/hooks/useGame.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import WS from 'vitest-websocket-mock';
import { useGame } from './useGame';

describe('useGame', () => {
  let server: WS;

  beforeEach(() => {
    server = new WS('ws://localhost:8000/api/v1/ws/game/test-game');
  });

  afterEach(() => {
    WS.clean();
  });

  it('connects to WebSocket on mount', async () => {
    const { result } = renderHook(() => useGame({
      gameId: 'test-game',
      seat: 0,
      playerId: 'player-1',
    }));

    await server.connected;

    expect(result.current.isConnected).toBe(true);
  });

  it('sends identify message after connection', async () => {
    renderHook(() => useGame({
      gameId: 'test-game',
      seat: 0,
      playerId: 'player-1',
    }));

    await server.connected;

    const message = await server.nextMessage;
    expect(JSON.parse(message as string)).toEqual({
      type: 'identify',
      payload: { seat: 0, player_id: 'player-1' },
    });
  });

  it('handles state_snapshot messages', async () => {
    const onStateUpdate = vi.fn();

    renderHook(() => useGame({
      gameId: 'test-game',
      seat: 0,
      playerId: 'player-1',
    }));

    await server.connected;

    // Send state snapshot
    server.send(JSON.stringify({
      type: 'state_snapshot',
      payload: { game_id: 'test-game', state: 'lobby' },
    }));

    await waitFor(() => {
      // Verify state store was updated
      // Check via store selector or callback
    });
  });

  it('reconnects after disconnect with exponential backoff', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useGame({
      gameId: 'test-game',
      seat: 0,
      playerId: 'player-1',
    }));

    await server.connected;

    // Simulate disconnect
    server.close();

    // Should attempt reconnect after 1 second
    vi.advanceTimersByTime(1000);
    await server.connected;

    expect(result.current.isConnected).toBe(true);

    vi.useRealTimers();
  });

  it('places bid via WebSocket', async () => {
    const { result } = renderHook(() => useGame({
      gameId: 'test-game',
      seat: 0,
      playerId: 'player-1',
    }));

    await server.connected;
    await server.nextMessage; // consume identify

    result.current.placeBid(15);

    const message = await server.nextMessage;
    expect(JSON.parse(message as string)).toEqual({
      type: 'place_bid',
      payload: { seat: 0, value: 15 },
    });
  });
});
```

**Test Coverage Goals:**
- ✅ Connection establishment
- ✅ Re-identification when seat/playerId changes
- ✅ Message handling (state_snapshot, action_ok, action_failed, error)
- ✅ Reconnection logic with exponential backoff
- ✅ Max reconnection attempts
- ✅ Game actions (placeBid, chooseTrump, playCard, revealTrump)
- ✅ Disconnect cleanup
- ✅ Error handling

**Estimated Effort:** 1-2 days

---

## 3. Complex Game Components (0% coverage)

**Files to Test:**
- `src/components/game/GameBoard.tsx` (266 lines)
- `src/components/game/ScoreBoard.tsx` (249 lines)
- `src/components/game/RoundHistory.tsx` (205 lines)
- `src/components/game/JoinGameModal.tsx` (126 lines)

### Recommended Approach: Component Integration Tests

**Challenge:** These components are tightly coupled with game state and have complex rendering logic.

**Strategy:** Test with realistic game states, not isolated unit tests.

**Test Structure:**
```typescript
// src/components/game/GameBoard.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GameBoard } from './GameBoard';
import type { GameState } from '../../types';

describe('GameBoard', () => {
  it('renders 4 player seats correctly', () => {
    const gameState: GameState = {
      game_id: 'test',
      mode: '28',
      seats: 4,
      state: 'lobby',
      players: [
        { seat: 0, name: 'Alice', player_id: 'p1', is_bot: false },
        { seat: 1, name: 'Bob', player_id: 'p2', is_bot: false },
        { seat: 2, name: 'Charlie', player_id: 'p3', is_bot: false },
        { seat: 3, name: 'David', player_id: 'p4', is_bot: false },
      ],
      dealer: 0,
      leader: 1,
    };

    render(<GameBoard gameState={gameState} yourSeat={0} />);

    // Verify all players are displayed
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
    expect(screen.getByText('David')).toBeInTheDocument();
  });

  it('shows dealer badge on correct seat', () => {
    const gameState: GameState = {
      // ... (as above)
      dealer: 2,
    };

    const { container } = render(<GameBoard gameState={gameState} yourSeat={0} />);

    // Find dealer badge and verify it's on seat 2
    const dealerBadge = screen.getByText('Dealer');
    // Check parent contains Charlie's name
  });

  it('displays trick cards in center', () => {
    const gameState: GameState = {
      // ...
      state: 'play',
      current_trick: {
        0: { id: 'A♠', rank: 'A', suit: '♠' },
        1: { id: 'K♥', rank: 'K', suit: '♥' },
      },
    };

    render(<GameBoard gameState={gameState} yourSeat={0} />);

    // Verify trick cards are displayed
    expect(screen.getByAltText('A♠')).toBeInTheDocument();
    expect(screen.getByAltText('K♥')).toBeInTheDocument();
  });

  it('shows trump symbol when revealed', () => {
    const gameState: GameState = {
      // ...
      trump: '♠',
      hidden_trump_revealed: true,
    };

    render(<GameBoard gameState={gameState} yourSeat={0} />);

    expect(screen.getByText('♠')).toBeInTheDocument();
  });
});
```

**Test Files to Create:**
1. `src/components/game/GameBoard.test.tsx` - Player arrangement, trick display, trump indicator
2. `src/components/game/ScoreBoard.test.tsx` - Score display, team scoring, last trick
3. `src/components/game/RoundHistory.test.tsx` - Round list, trick details, player names
4. `src/components/game/JoinGameModal.test.tsx` - Form validation, submission, error states

**Estimated Effort:** 1-2 days

---

## 4. Utility Components (0% coverage)

**Files to Test:**
- `src/components/Banner.tsx` (7 lines)
- `src/components/ErrorBoundary.tsx` (158 lines)
- `src/components/Toasts.tsx` (13 lines)

### Recommended Approach: Targeted Unit Tests

**Test Structure:**
```typescript
// src/components/ErrorBoundary.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

const ThrowError = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Safe content')).toBeInTheDocument();
  });

  it('catches errors and shows fallback UI', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('logs error details', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
```

**Test Files to Create:**
1. `src/components/Banner.test.tsx` - Simple rendering test
2. `src/components/ErrorBoundary.test.tsx` - Error catching, fallback UI, reset
3. `src/components/Toasts.test.tsx` - Toast rendering from store

**Estimated Effort:** 0.5 days

---

## 5. Entry Points (0% coverage)

**Files to Test:**
- `src/main.tsx` (18 lines)
- `src/App.tsx` (49 lines)
- `src/router.tsx` (46 lines)

### Recommended Approach: Smoke Tests

**Why Smoke Tests:**
- Entry points are integration glue code
- Hard to unit test in isolation
- Main goal: ensure app renders without crashing

**Test Structure:**
```typescript
// src/App.test.tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

describe('App', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );

    expect(container).toBeInTheDocument();
  });

  it('renders home page by default', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    );

    // Basic smoke test - app should render
    expect(container.querySelector('main')).toBeInTheDocument();
  });
});
```

**Estimated Effort:** 0.5 days

---

## Testing Tools & Libraries

### Already Installed ✅
- **Vitest** - Fast unit test runner (Jest-compatible)
- **@testing-library/react** - Component testing utilities
- **@testing-library/user-event** - User interaction simulation
- **@testing-library/jest-dom** - Custom matchers
- **@playwright/test** - E2E testing framework
- **happy-dom** / **jsdom** - DOM environment for tests

### Need to Install 📦
```bash
# For WebSocket testing
npm install -D vitest-websocket-mock

# For advanced E2E scenarios (optional)
npm install -D @playwright/experimental-ct-react
```

---

## Execution Plan

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add utility component tests (Banner, ErrorBoundary, Toasts)
2. ✅ Add entry point smoke tests (main, App, router)
3. ✅ Add JoinGameModal tests

**Goal:** Increase coverage to ~35%

### Phase 2: Complex Components (2-3 days)
1. ✅ Add GameBoard tests
2. ✅ Add ScoreBoard tests
3. ✅ Add RoundHistory tests

**Goal:** Increase coverage to ~45%

### Phase 3: WebSocket Hooks (2-3 days)
1. ✅ Set up vitest-websocket-mock
2. ✅ Add useGame tests
3. ✅ Add useGameSocket tests

**Goal:** Increase coverage to ~55%

### Phase 4: E2E Testing (3-4 days)
1. ✅ Configure Playwright test suite
2. ✅ Add critical user flow tests
3. ✅ Add admin panel E2E tests
4. ✅ Add replay/history E2E tests

**Goal:** Comprehensive integration coverage, increase overall to ~70%+

---

## Success Metrics

**Target Coverage:**
- Overall: 70%+ (currently 26.8%)
- Branches: 90%+ (currently 84.95%)
- Functions: 80%+ (currently 63.3%)

**Quality Metrics:**
- All tests pass consistently
- No flaky tests (< 1% failure rate)
- Test execution time < 10 seconds (unit tests)
- E2E test execution time < 2 minutes

**Maintainability:**
- Tests are readable and well-documented
- Common test utilities extracted to helpers
- Mock data centralized in `src/test/mockData.ts`
- CI/CD integration with coverage reporting

---

## Notes

- **E2E tests** are critical for page components due to routing and API dependencies
- **WebSocket mocking** is essential for hook testing without backend
- **Component tests** should use realistic game states, not minimal props
- **Avoid over-mocking** - test behavior, not implementation
- **Prioritize user-facing functionality** over edge cases

---

Last Updated: 2025-10-19
