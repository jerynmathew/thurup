import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('displays the home page correctly', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Thurup/i);

    // Check main heading
    await expect(page.getByRole('heading', { name: /Thurup/i })).toBeVisible();

    // Check that Create Game and Join Game sections are visible
    await expect(page.getByText(/Create New Game/i)).toBeVisible();
    await expect(page.getByText(/Join Existing Game/i)).toBeVisible();
  });

  test('can create a new game', async ({ page }) => {
    // Fill in player name using placeholder
    await page.getByPlaceholder(/Enter your name/i).fill('TestPlayer');

    // Click Create Game button
    await page.getByRole('button', { name: /Create Game/i }).first().click();

    // Should navigate to game page
    await expect(page).toHaveURL(/\/game\/.+/, { timeout: 10000 });

    // Should see the player in the lobby
    await expect(page.getByText('TestPlayer').first()).toBeVisible();

    // Should see lobby state
    await expect(page.getByText(/Game Lobby/i)).toBeVisible();
  });

  test('validates player name on create game', async ({ page }) => {
    // Click Create Game without entering a name
    const createButton = page.getByRole('button', { name: /Create Game/i }).first();
    await createButton.click();

    // Should show a warning toast (check for toast or still be on home page)
    await expect(page).toHaveURL('/', { timeout: 2000 });
  });

  test('shows join game modal when join button clicked', async ({ page }) => {
    // Fill in game code using label
    await page.getByPlaceholder(/royal-turtle/i).fill('TEST-CODE');

    // Click Join Game button
    await page.getByRole('button', { name: /Join Game/i }).last().click();

    // Modal should appear asking for player name
    await expect(
      page.getByRole('dialog').or(page.getByText(/Enter your name/i))
    ).toBeVisible({
      timeout: 2000,
    });
  });

  test('game mode selection works', async ({ page }) => {
    // Mode is selected via buttons, not a select element
    const mode28Button = page.getByRole('button', { name: /28.*4 Players/i });
    const mode56Button = page.getByRole('button', { name: /56.*6 Players/i });

    await expect(mode28Button).toBeVisible();
    await expect(mode56Button).toBeVisible();

    // Click to change to 56 mode
    await mode56Button.click();

    // After clicking 56 mode, seats selection should appear
    await expect(page.getByRole('button', { name: /4 Seats/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /6 Seats/i })).toBeVisible();
  });

  test('displays quick links to other pages', async ({ page }) => {
    // Should have links to history and admin
    await expect(page.getByRole('button', { name: /Game History/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Admin Panel/i })).toBeVisible();
  });
});
