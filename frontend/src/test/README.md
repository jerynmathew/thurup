# Frontend Testing Documentation

This directory contains test utilities, mock data, and test configuration for the Thurup frontend.

## Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   └── Button.test.tsx       # Component tests
│   │   └── game/
│   │       ├── PlayingCard.tsx
│   │       └── PlayingCard.test.tsx  # Component tests
│   ├── stores/
│   │   ├── gameStore.ts
│   │   └── gameStore.test.ts         # Store tests
│   └── test/
│       ├── setup.ts                  # Test environment setup
│       ├── mockData.ts               # Mock data for tests
│       ├── testUtils.tsx             # Custom render functions
│       └── README.md                 # This file
├── vitest.config.ts                  # Vitest configuration
└── package.json                      # Test scripts
```

## Testing Stack

- **Vitest**: Fast unit test framework (Vite-native)
- **@testing-library/react**: React component testing utilities
- **@testing-library/user-event**: User interaction simulation
- **@testing-library/jest-dom**: Custom matchers for DOM testing
- **jsdom**: Browser environment simulation

## Running Tests

```bash
# Run tests in watch mode (development)
npm run test

# Run tests once
npm run test:run

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Files

### `setup.ts`
Global test configuration:
- Automatic cleanup after each test
- Mock `window.matchMedia`
- Mock `IntersectionObserver`
- Import jest-dom matchers

### `mockData.ts`
Predefined mock data for tests:
- `mockCard`: Single card
- `mockCards`: Array of cards
- `mockPlayers`: Player data
- `mockGameState`: Complete game state
- `mockLobbyGameState`: Lobby state
- `mockBiddingGameState`: Bidding phase state

### `testUtils.tsx`
Custom testing utilities:
- `renderWithRouter`: Render components with React Router
- `createMockFn`: Type-safe mock function creator

## Writing Tests

### Component Tests

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const onClick = vi.fn();
    render(<MyComponent onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

### Store Tests

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useMyStore } from './myStore';

describe('myStore', () => {
  beforeEach(() => {
    useMyStore.getState().reset();
  });

  it('updates state correctly', () => {
    const { setState } = useMyStore.getState();
    setState('new value');
    expect(useMyStore.getState().value).toBe('new value');
  });
});
```

### Tests with Router

```typescript
import { renderWithRouter } from '../test/testUtils';

it('navigates correctly', () => {
  renderWithRouter(<MyPage />, { route: '/game/123' });
  expect(screen.getByText('Game: 123')).toBeInTheDocument();
});
```

## Test Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| UI Components | 80% | ✅ 100% (Button) |
| Game Components | 70% | ✅ 100% (PlayingCard) |
| Stores | 90% | ✅ 100% (gameStore) |
| Pages | 60% | ⏳ 0% |
| API Services | 80% | ⏳ 0% |

## Current Test Statistics

- **Total Tests**: 42
  - Button: 13 tests
  - PlayingCard: 15 tests
  - gameStore: 14 tests
- **Test Files**: 3
- **All Passing**: ✅

## Best Practices

1. **Test Behavior, Not Implementation**
   - Focus on what users see and do
   - Avoid testing internal state directly
   - Use accessible queries (getByRole, getByText)

2. **Mock External Dependencies**
   - Use `vi.fn()` for functions
   - Mock API calls with proper responses
   - Mock WebSocket connections

3. **Clean Up**
   - Reset stores in `beforeEach`
   - Cleanup is automatic with @testing-library/react

4. **Descriptive Test Names**
   - Use "it should..." format
   - Describe expected behavior clearly
   - Group related tests with `describe`

5. **Test Edge Cases**
   - Empty states
   - Loading states
   - Error states
   - Disabled states
   - Invalid inputs

## Common Patterns

### Testing Async Operations

```typescript
it('loads data on mount', async () => {
  render(<MyComponent />);
  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument();
  });
});
```

### Testing User Interactions

```typescript
import userEvent from '@testing-library/user-event';

it('submits form', async () => {
  const user = userEvent.setup();
  render(<Form />);
  await user.type(screen.getByRole('textbox'), 'test');
  await user.click(screen.getByRole('button'));
  expect(onSubmit).toHaveBeenCalled();
});
```

### Testing Store Selectors

```typescript
it('selector returns correct value', () => {
  const { updateGameState } = useGameStore.getState();
  updateGameState(mockGameState);

  const state = useGameStore.getState();
  const result = mySelector(state);
  expect(result).toBe(expectedValue);
});
```

## Adding New Tests

1. Create test file next to the component/module:
   ```
   MyComponent.tsx
   MyComponent.test.tsx
   ```

2. Import necessary utilities:
   ```typescript
   import { describe, it, expect } from 'vitest';
   import { render, screen } from '@testing-library/react';
   ```

3. Write tests following the patterns above

4. Run tests to verify:
   ```bash
   npm run test:run
   ```

## Debugging Tests

```bash
# Run specific test file
npm run test -- Button.test.tsx

# Run tests matching pattern
npm run test -- --grep="renders correctly"

# Run with UI for debugging
npm run test:ui
```

## Future Enhancements

- [ ] Integration tests for page flows
- [ ] API service tests with MSW
- [ ] WebSocket hook tests
- [ ] E2E tests with Playwright
- [ ] Visual regression tests
- [ ] Performance tests

---

_Last Updated: 2025-10-13_
