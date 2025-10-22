# End-to-End Tests with Playwright

This directory contains E2E tests for the Thurup frontend application using Playwright.

## Setup

Playwright is already installed. To install browser binaries:

```bash
npx playwright install
```

## Prerequisites

**IMPORTANT**: E2E tests require the backend API to be running!

```bash
# In a separate terminal, start the backend
cd ../backend
uv run uvicorn app.main:app --reload
```

The backend should be running on `http://localhost:8000` before running E2E tests.

## Running Tests

### Run all E2E tests (headless)
```bash
npm run test:e2e
```

### Run with UI mode (recommended for development)
```bash
npm run test:e2e:ui
```

### Run in headed mode (see browser)
```bash
npm run test:e2e:headed
```

### Run in debug mode
```bash
npm run test:e2e:debug
```

### Run specific test file
```bash
npx playwright test home-page.spec.ts
```

### Run specific test by name
```bash
npx playwright test --grep "can create a new game"
```

## Test Organization

- `home-page.spec.ts` - Tests for home page functionality
  - Page rendering
  - Game creation
  - Join game modal
  - Form validation
  - Game mode selection

- `game-flow.spec.ts` - Tests for complete game workflows
  - Full game creation flow
  - Bot player management
  - Starting games
  - Session persistence on refresh
  - Bidding interactions
  - WebSocket real-time updates
  - Card display

## Writing New Tests

### Test Structure

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

#### Navigation
```typescript
await page.goto('/');
await expect(page).toHaveURL(/\/game\/.+/);
```

#### Form Interaction
```typescript
await page.locator('input[name="playerName"]').fill('TestUser');
await page.getByRole('button', { name: /Submit/i }).click();
```

#### Waiting for State Changes
```typescript
// Wait for specific text
await expect(page.getByText('Success')).toBeVisible({ timeout: 3000 });

// Wait for URL change
await expect(page).toHaveURL(/\/new-page/);

// Custom wait
await page.waitForTimeout(1000); // Use sparingly
```

#### Multiple Contexts (Multi-user testing)
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

## Debugging Tests

### Visual Debugging
```bash
# Run with UI mode to see test execution
npm run test:e2e:ui
```

### Debug Mode
```bash
# Step through tests with debugger
npm run test:e2e:debug
```

### Headed Mode
```bash
# See browser during test execution
npm run test:e2e:headed
```

### Screenshots and Traces
Playwright automatically captures:
- Screenshots on failure (saved to `test-results/`)
- Traces on retry (viewable with `npx playwright show-trace`)

View trace:
```bash
npx playwright show-trace test-results/.../trace.zip
```

### Console Logs
```typescript
// Log page console messages
page.on('console', msg => console.log('Browser:', msg.text()));

// Log network requests
page.on('request', request => console.log('Request:', request.url()));
```

## CI/CD Integration

The tests are configured to run in CI with:
- Retries enabled (2 retries)
- Sequential execution
- HTML report generation

### GitHub Actions Example
```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npm run test:e2e

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Configuration

See `playwright.config.ts` for:
- Browser configuration
- Timeout settings
- Base URL
- Reporter settings
- WebServer auto-start

## Current Test Coverage

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

## Troubleshooting

### "Executable doesn't exist" error
```bash
npx playwright install
```

### Dev server not starting
Check that port 5173 is available:
```bash
lsof -i :5173
```

### Tests timing out
Increase timeout in test:
```typescript
test('slow operation', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ...
});
```

### WebSocket connection issues
Ensure backend is running on expected port (check `baseURL` in config).

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Selectors Guide](https://playwright.dev/docs/selectors)
- [Test Assertions](https://playwright.dev/docs/test-assertions)

---

Last Updated: 2025-10-19
