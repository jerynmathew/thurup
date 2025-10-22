# Thurup - Testing Guide

Complete testing documentation for the Thurup card game application, covering both backend and frontend testing strategies.

## Overview

The Thurup project uses a comprehensive testing strategy with three levels of test coverage:

- **Unit Tests**: Fast, isolated tests for individual functions and classes
- **Integration Tests**: API and component integration tests with mocked dependencies
- **End-to-End (E2E) Tests**: Full system tests simulating real user interactions

### Test Statistics

**Backend (pytest)**:
- 331 tests passing
- 76% code coverage
- Test types: Unit (32), Integration (24), E2E (5 classes)

**Frontend (Vitest + Playwright)**:
- 253 component/unit tests passing
- 26.8% overall coverage (82.14% for API clients, 100% for UI components)
- 13 E2E scenarios (10 passing, 77% success rate)

---

## Quick Start

### Run All Tests

```bash
# Backend
cd backend
uv run pytest -v

# Frontend unit/component tests
cd frontend
npm test

# Frontend E2E tests (requires backend running)
cd frontend
npm run test:e2e
```

### Run with Coverage

```bash
# Backend
uv run pytest --cov=app --cov-report=html

# Frontend
npm run test:coverage
```

---

## Backend Testing

### Test Structure

```
backend/tests/
├── unit/              # Unit tests (isolated, fast, no external dependencies)
├── integration/       # Integration tests (API tests with TestClient)
├── e2e/              # End-to-end tests (full system, requires running server)
├── conftest.py       # Shared pytest fixtures
└── README.md         # This file
```

### Unit Tests

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (< 1 second total)
- No external dependencies
- Mock/stub external services
- Test single functions/classes

**Files**:
- `test_bidding.py` - Bidding logic and validation
- `test_hidden_trump.py` - Hidden trump reveal mechanics
- `test_rules.py` - Card game rules
- `test_scoring.py` - Score calculation
- `test_session.py` - GameSession class
- `test_phase1_fixes.py` - Phase 1 bug fixes
- `test_persistence.py` - Database persistence layer

**Run**:
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/test_bidding.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=app --cov-report=term-missing
```

### Integration Tests

**Purpose**: Test how components work together via APIs

**Characteristics**:
- Uses FastAPI TestClient (no server required)
- Tests REST and WebSocket endpoints
- In-memory database
- Tests full API flows

**Files**:
- `test_api_integration.py` - Complete API integration tests (24 tests)
  - REST endpoints
  - WebSocket communication
  - History endpoints
  - Admin endpoints
  - Persistence flows
  - End-to-end scenarios

**Run**:
```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific test class
uv run pytest tests/integration/test_api_integration.py::TestRESTIntegration -v
```

### End-to-End Tests

**Purpose**: Test the complete system as a user would

**Characteristics**:
- Requires running server
- Real HTTP requests
- Tests full user workflows
- Simulates production usage

**Files**:
- `test_complete_flow.py` - Complete game lifecycle tests
  - Full game flow (create → join → play → history)
  - Multiple concurrent games
  - Authentication security
  - Error handling

**Run**:
```bash
# Step 1: Start the server in one terminal
uv run uvicorn app.main:app --reload --port 8000

# Step 2: Run E2E tests in another terminal
uv run pytest tests/e2e/ -v -s

# With output visible
uv run pytest tests/e2e/test_complete_flow.py::TestCompleteGameFlow -v -s
```

### Writing Backend Tests

**Unit Test Template**:
```python
"""
Unit tests for [component name].
"""

import pytest
from app.game.session import GameSession


class TestMyComponent:
    """Test suite for MyComponent."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        session = GameSession(mode="28", seats=4)

        # Act
        result = session.some_method()

        # Assert
        assert result is not None
```

**Integration Test Template**:
```python
"""
Integration tests for [API endpoint].
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMyEndpoint:
    """Integration tests for my endpoint."""

    def test_endpoint_success(self, client):
        """Test successful endpoint call."""
        response = client.post("/api/v1/my/endpoint", json={"data": "value"})
        assert response.status_code == 200
```

---

## Frontend Testing

### Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── *.test.tsx         # Component tests
│   ├── api/
│   │   └── *.test.ts          # API client tests
│   └── utils/
│       └── *.test.ts          # Utility tests
├── tests/
│   └── e2e/
│       ├── home-page.spec.ts
│       └── game-flow.spec.ts
└── playwright.config.ts
```

### Unit & Component Tests (Vitest)

**Current Coverage**:
- ✅ All UI components (Badge, Button, Card, Modal, Select, Spinner) - 100%
- ✅ API clients (admin, client, game, history) - 82.14%
- ✅ Session manager utility - 95.23%
- ✅ Basic game components (PlayerHand, LobbyPanel)
- ✅ State management stores - 82.12%

**Run**:
```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- Badge.test.tsx
```

**Component Test Example**:
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders with correct text', () => {
    render(<Badge variant="success">Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });
});
```

---

## E2E Testing with Playwright

### Setup

**Prerequisites**:
- Backend must be running on port 18081
- Frontend must be running on port 5173

**Install Browsers**:
```bash
npx playwright install
```

### Running E2E Tests

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run with UI mode (recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test home-page.spec.ts

# Run specific test by name
npx playwright test --grep "can create a new game"
```

### Test Organization

**home-page.spec.ts** - Tests for home page functionality:
- Page rendering
- Game creation
- Join game modal
- Form validation
- Game mode selection

**game-flow.spec.ts** - Tests for complete game workflows:
- Full game creation flow
- Bot player management
- Starting games
- Session persistence on refresh
- Bidding interactions
- WebSocket real-time updates
- Card display

### Writing E2E Tests

**Test Structure**:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await page.goto('/some-page');

    // Act
    await page.getByRole('button', { name: /Click Me/i }).click();

    // Assert
    await expect(page.getByText('Success')).toBeVisible();
  });
});
```

### Best Practices

1. **Use accessible selectors**
   - Prefer `getByRole`, `getByText`, `getByLabel`
   - Avoid CSS selectors when possible

2. **Wait for elements properly**
   ```typescript
   await expect(page.getByText('Loading')).toBeVisible();
   await expect(page.getByText('Loaded')).toBeVisible({ timeout: 5000 });
   ```

3. **Use descriptive test names**
   - Start with "should" or action verb
   - Describe the expected behavior clearly

4. **Clean up after tests**
   - Tests should be independent
   - Don't rely on previous test state

5. **Handle async operations**
   - Always await promises
   - Use proper timeout values

### Common Patterns

**Navigation**:
```typescript
await page.goto('/');
await expect(page).toHaveURL(/\/game\/.+/);
```

**Form Interaction**:
```typescript
await page.locator('input[name="playerName"]').fill('TestUser');
await page.getByRole('button', { name: /Submit/i }).click();
```

**Waiting for State Changes**:
```typescript
// Wait for specific text
await expect(page.getByText('Success')).toBeVisible({ timeout: 3000 });

// Wait for URL change
await expect(page).toHaveURL(/\/new-page/);
```

**Multiple Contexts (Multi-user testing)**:
```typescript
test('multiple users can join same game', async ({ browser }) => {
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();

  const page1 = await context1.newPage();
  const page2 = await context2.newPage();

  // Player 1 creates game
  await page1.goto('/');
  // ...

  // Player 2 joins game
  await page2.goto('/');
  // ...

  await context1.close();
  await context2.close();
});
```

### Debugging E2E Tests

**Visual Debugging**:
```bash
# Run with UI mode to see test execution
npm run test:e2e:ui
```

**Debug Mode**:
```bash
# Step through tests with debugger
npm run test:e2e:debug
```

**Headed Mode**:
```bash
# See browser during test execution
npm run test:e2e:headed
```

**Screenshots and Traces**:
- Playwright automatically captures screenshots on failure (saved to `test-results/`)
- Traces on retry (viewable with `npx playwright show-trace`)

**View trace**:
```bash
npx playwright show-trace test-results/.../trace.zip
```

**Console Logs**:
```typescript
// Log page console messages
page.on('console', msg => console.log('Browser:', msg.text()));

// Log network requests
page.on('request', request => console.log('Request:', request.url()));
```

### Current E2E Test Coverage

- ✅ Home page rendering and navigation
- ✅ Game creation flow
- ✅ Join game modal
- ✅ Bot player management
- ✅ Game start with full lobby
- ✅ Session persistence on refresh
- ✅ WebSocket real-time updates
- ⏳ Full game playthrough (bidding → trump → play → scoring)
- ⏳ Admin panel functionality
- ⏳ Game history browsing
- ⏳ Multiple concurrent users

---

## Manual Testing Flows

### Test Flow 1: Create and Play a Game (Solo with Bots)

**1.1 Create a New Game**
1. Open the app: Navigate to http://localhost:5173
2. Fill in the form:
   - Your Name: Enter "Player 1"
   - Game Mode: Select "28 (4 Players)"
   - Click "Create Game" button
3. Expected: Success toast, redirect to game page

**1.2 Game Lobby**
1. Lobby shows game ID, mode, player count
2. Add 3 Bot Players (click "Add Bot Player" 3 times)
3. Click "Start Game"
4. Game state changes to "bidding"

**1.3 Bidding Phase**
1. Game board shows 4 player positions
2. Sidebar shows score board and bidding panel
3. When your turn: place a bid or pass
4. Wait for bots to bid automatically
5. Bidding completes when one player bids and others pass

**1.4 Trump Selection**
1. If you won the bidding: Trump Panel appears with 4 suit buttons
2. Choose trump suit
3. Game moves to "playing" phase

**1.5 Playing Phase**
1. Your hand appears at bottom with 8 cards
2. Click a playable card to play it
3. Bots play automatically in turn
4. Score Board updates after each trick
5. Play continues until all cards are played

**1.6 Game Completion**
1. Final scores displayed
2. Winner announced
3. "Start Next Round" button appears

### Test Flow 2: Multiplayer Game (Multiple Browser Windows)

1. **Browser Window 1**: Create game as "Alice"
2. **Copy Game URL** from Share section
3. **Incognito/Private Window**: Paste URL, join as "Bob"
4. Repeat for players 3 & 4 or add bots
5. All players see lobby update in real-time
6. Play together with synchronized state

### Test Flow 3: Game History & Replay

1. From Home Page, click "Game History"
2. Filter games: All / Completed / Active
3. Click on a completed game to view replay
4. Use timeline controls: play, pause, step, scrub
5. Watch auto-play with speed adjustment

### Test Flow 4: Admin Dashboard

1. From Home Page, click "Admin Panel"
2. Login with credentials (default: admin/admin)
3. View server health metrics (uptime, sessions, connections)
4. Browse active sessions with connection status
5. Force save or delete sessions
6. Trigger cleanup task
7. Logout when done

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# Backend tests
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run unit tests
        run: uv run pytest tests/unit/ -v
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3

# Frontend E2E tests
name: Frontend E2E
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Start backend
        run: cd backend && uv run uvicorn app.main:app &
      - name: Start frontend
        run: cd frontend && npm run dev &
      - name: Wait for servers
        run: sleep 10
      - name: Run E2E tests
        run: cd frontend && npm run test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Troubleshooting

### Backend

**"Server not running" error in E2E tests**
```bash
# Solution: Start server first
uv run uvicorn app.main:app --reload
```

**"Database locked" errors**
```bash
# Solution: Use separate test database or in-memory SQLite
# Already configured in tests/conftest.py
```

**Slow tests**
```bash
# Check if E2E tests are running (they're slower)
# Profile with:
uv run pytest --durations=10
```

**Import errors**
```bash
# Ensure you're in the backend directory
# Run: uv sync to install dependencies
```

### Frontend

**"Executable doesn't exist" error**
```bash
# Install Playwright browsers
npx playwright install
```

**Dev server not starting**
```bash
# Check that port 5173 is available
lsof -i :5173
```

**Tests timing out**
```typescript
// Increase timeout in test:
test('slow operation', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ...
});
```

**WebSocket connection issues**
- Ensure backend is running on expected port (check `baseURL` in config)
- Check browser console for connection errors
- Verify CORS settings in backend

### Debugging Tests

**Backend**:
```bash
# Run with print statements visible
uv run pytest -v -s

# Run single test
uv run pytest tests/unit/test_bidding.py::test_sequential_bidding -v

# Drop into debugger on failure
uv run pytest --pdb

# Show full traceback
uv run pytest --tb=long

# Run last failed tests
uv run pytest --lf
```

**Frontend**:
```bash
# Run in watch mode
npm run test:watch

# Run specific test
npm test -- Badge.test.tsx

# Debug E2E in UI mode
npm run test:e2e:ui
```

---

## Test Coverage Goals

### Backend
- Core game logic: ✅ Comprehensive
- API endpoints: ✅ All endpoints tested
- WebSocket: ✅ Connection, messages, broadcasting
- Persistence: ✅ Save, load, restore
- History: ✅ Query, replay, stats
- Admin: ✅ All admin operations
- **Target**: 80%+ overall coverage

### Frontend
- UI Components: ✅ 100% coverage
- API Clients: ✅ 82% coverage
- State Management: ✅ 82% coverage
- Game Components: ⏳ Basic coverage
- WebSocket Hooks: ⏳ Needs testing
- Page Components: ⏳ E2E coverage only
- **Target**: 70%+ overall coverage

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Assertions](https://playwright.dev/docs/test-assertions)

---

**Last Updated**: 2025-10-22

For more information:
- [API Reference](../development/API_REFERENCE.md) - Backend API documentation
- [Architecture](../development/ARCHITECTURE.md) - System design
- [Developer Guide](../development/DEVELOPER_GUIDE.md) - Development setup
