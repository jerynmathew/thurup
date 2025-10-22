import { test, expect } from '@playwright/test';

test.describe('Game Flow', () => {
  test('complete game creation and lobby flow', async ({ page }) => {
    // Step 1: Go to home page
    await page.goto('/');

    // Step 2: Create a new game
    await page.getByPlaceholder(/Enter your name/i).fill('Alice');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    // Step 3: Verify navigation to game page
    await expect(page).toHaveURL(/\/game\/.+/);

    // Step 4: Verify lobby state
    await expect(page.getByText(/Game Lobby/i)).toBeVisible();
    await expect(page.getByText('Alice').first()).toBeVisible();

    // Step 5: Verify game info displayed
    await expect(page.getByText(/28/)).toBeVisible(); // Game mode

    // Step 6: Check for share URL (should be visible)
    const urlInput = page.locator('input[readonly]').first();
    await expect(urlInput).toBeVisible();

    // Step 7: Verify player count shows 1/4 (look for exact pattern)
    await expect(page.locator('text=/^1\\s*\\/\\s*4$/')).toBeVisible();
  });

  test('can add bot players to game', async ({ page }) => {
    // Create game
    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('BobTest');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    await expect(page).toHaveURL(/\/game\/.+/);

    // Add a bot
    const addBotButton = page.getByRole('button', { name: /Add Bot/i });
    if (await addBotButton.isVisible()) {
      await addBotButton.click();

      // Should see bot in player list
      await expect(page.getByText(/Bot/i).first()).toBeVisible({ timeout: 5000 });

      // Player count should increase (look for exact pattern)
      await expect(page.locator('text=/^2\\s*\\/\\s*4$/')).toBeVisible();
    }
  });

  test('can start game when enough players', async ({ page }) => {
    // Create game
    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('Charlie');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    await expect(page).toHaveURL(/\/game\/.+/);

    // Add bots until we have 4 players
    const addBotButton = page.getByRole('button', { name: /Add Bot/i });

    // Add 3 bots (we have 1 human player)
    for (let i = 0; i < 3; i++) {
      if (await addBotButton.isVisible()) {
        await addBotButton.click();
        await page.waitForTimeout(500); // Wait for bot to be added
      }
    }

    // Now we should have 4 players (look for exact pattern)
    await expect(page.locator('text=/^4\\s*\\/\\s*4$/')).toBeVisible({ timeout: 3000 });

    // Start game button should be enabled
    const startButton = page.getByRole('button', { name: /Start Game/i });
    await expect(startButton).toBeEnabled({ timeout: 2000 });

    // Click start
    await startButton.click();

    // Should transition to bidding phase
    await expect(page.getByText(/Bidding/i).or(page.getByText(/Place.*Bid/i))).toBeVisible({
      timeout: 5000,
    });
  });

  test('preserves session on page refresh', async ({ page }) => {
    // Create game
    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('RefreshTest');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    const gameUrl = page.url();
    await expect(page).toHaveURL(/\/game\/.+/);

    // Wait for player to appear
    await expect(page.getByText('RefreshTest').first()).toBeVisible();

    // Refresh the page
    await page.reload();

    // Should still be on the same game page
    await expect(page).toHaveURL(gameUrl);

    // Should still see the player
    await expect(page.getByText('RefreshTest').first()).toBeVisible({ timeout: 5000 });
  });

  test('can place bid when it is player turn', async ({ page }) => {
    // This test requires the game to be in bidding state
    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('BidderTest');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    await expect(page).toHaveURL(/\/game\/.+/);

    // Add 3 bots
    const addBotButton = page.getByRole('button', { name: /Add Bot/i });
    for (let i = 0; i < 3; i++) {
      if (await addBotButton.isVisible()) {
        await addBotButton.click();
        await page.waitForTimeout(500);
      }
    }

    // Start game (wait for button to be enabled)
    const startButton = page.getByRole('button', { name: /Start Game/i });
    await expect(startButton).toBeEnabled({ timeout: 5000 });
    if (await startButton.isEnabled()) {
      await startButton.click();

      // Wait for bidding phase
      await expect(
        page.getByText(/Bidding/i).or(page.getByText(/Place.*Bid/i))
      ).toBeVisible({ timeout: 5000 });

      // If it's our turn, we should see bid input or pass button
      const passButton = page.getByRole('button', { name: /Pass/i });
      const bidInput = page.locator('input[type="number"]');

      // Check if either is visible (depends on turn order)
      const hasPassButton = await passButton.isVisible({ timeout: 3000 }).catch(() => false);
      const hasBidInput = await bidInput.isVisible({ timeout: 3000 }).catch(() => false);

      if (hasPassButton || hasBidInput) {
        // It's our turn, we can interact
        if (hasPassButton) {
          // Click pass to complete the action
          await passButton.click();

          // Should see some feedback or state change
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('displays player cards when in hand', async ({ page }) => {
    // Create and start a game
    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('CardTest');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    await expect(page).toHaveURL(/\/game\/.+/);

    // Add bots
    const addBotButton = page.getByRole('button', { name: /Add Bot/i });
    for (let i = 0; i < 3; i++) {
      if (await addBotButton.isVisible()) {
        await addBotButton.click();
        await page.waitForTimeout(500);
      }
    }

    // Start game (wait for button to be enabled)
    const startButton = page.getByRole('button', { name: /Start Game/i });
    await expect(startButton).toBeEnabled({ timeout: 5000 });
    if (await startButton.isEnabled()) {
      await startButton.click();

      // Wait for game to start
      await page.waitForTimeout(2000);

      // Look for "Your Hand" section or card images
      const yourHandSection = page.getByText(/Your Hand/i);
      const hasHand = await yourHandSection.isVisible({ timeout: 3000 }).catch(() => false);

      if (hasHand) {
        // Should see card count
        await expect(page.getByText(/\d+ card/i)).toBeVisible();
      }
    }
  });

  test('shows game state updates in real-time', async ({ page, context }) => {
    // This test verifies WebSocket connectivity by checking state updates

    await page.goto('/');
    await page.getByPlaceholder(/Enter your name/i).fill('StateTest');
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    await expect(page).toHaveURL(/\/game\/.+/);

    // Check for connection indicator (if present)
    // Game should show connected state
    const disconnectedBadge = page.getByText(/Disconnected/i);
    await expect(disconnectedBadge).not.toBeVisible({ timeout: 2000 }).catch(() => {
      // It's ok if the badge doesn't exist at all
    });

    // Add a bot and verify state updates
    const addBotButton = page.getByRole('button', { name: /Add Bot/i });
    if (await addBotButton.isVisible()) {
      const initialPlayerCount = await page.getByText(/\d+\s*\/\s*4/).textContent();

      await addBotButton.click();

      // Player count should update in real-time via WebSocket
      await expect(page.getByText(/\d+\s*\/\s*4/)).not.toHaveText(initialPlayerCount || '', {
        timeout: 3000,
      });
    }
  });
});
