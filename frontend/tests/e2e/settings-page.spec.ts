import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('https://www.devskyy.app/admin/settings');

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display settings page header and description', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1')).toContainText('Settings');

    // Check description
    await expect(page.getByText('Configure your DevSkyy platform preferences')).toBeVisible();
  });

  test('should display all 5 settings tabs', async ({ page }) => {
    // Verify all tabs are present
    await expect(page.getByRole('tab', { name: /WordPress/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Vercel/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Autonomous/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /UI Preferences/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /System/i })).toBeVisible();
  });

  test('should have Save All button', async ({ page }) => {
    const saveButton = page.getByRole('button', { name: /Save All/i });
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();
  });

  test('WordPress tab - should display connection settings', async ({ page }) => {
    // Click WordPress tab (should be default)
    const wpTab = page.getByRole('tab', { name: /WordPress/i });
    await wpTab.click();

    // Check for WordPress URL input
    await expect(page.getByLabel(/WordPress URL/i)).toBeVisible();

    // Check for Consumer Key input
    await expect(page.getByLabel(/Consumer Key/i)).toBeVisible();

    // Check for Consumer Secret input
    await expect(page.getByLabel(/Consumer Secret/i)).toBeVisible();

    // Check for Auto-Sync toggle
    await expect(page.getByText(/Auto-Sync/i)).toBeVisible();
    await expect(page.getByText(/Automatically sync Round Table results to WordPress/i)).toBeVisible();
  });

  test('WordPress tab - should have show/hide buttons for secrets', async ({ page }) => {
    // Check that secret fields are password inputs by default
    const consumerKeyInput = page.getByLabel(/Consumer Key/i);
    await expect(consumerKeyInput).toHaveAttribute('type', 'password');

    const consumerSecretInput = page.getByLabel(/Consumer Secret/i);
    await expect(consumerSecretInput).toHaveAttribute('type', 'password');

    // Verify there are show/hide toggle buttons next to the secret fields
    // (These are the buttons with Eye/EyeOff icons)
    const toggleButtons = page.locator('button').filter({
      has: page.locator('svg')
    }).filter({
      hasNot: page.locator('text=/Save|Refresh/')
    });

    // Should have at least 2 toggle buttons (Consumer Key and Secret)
    await expect(toggleButtons.first()).toBeVisible();
  });

  test('Vercel tab - should display integration settings', async ({ page }) => {
    // Click Vercel tab
    await page.getByRole('tab', { name: /Vercel/i }).click();

    // Wait for tab content to load
    await page.waitForTimeout(500);

    // Check for Project ID input
    await expect(page.getByLabel(/Project ID/i)).toBeVisible();

    // Check for Organization ID input
    await expect(page.getByLabel(/Organization ID/i)).toBeVisible();

    // Check for API Token input
    await expect(page.getByLabel(/API Token/i)).toBeVisible();
  });

  test('Autonomous tab - should display agent configuration', async ({ page }) => {
    // Click Autonomous tab
    await page.getByRole('tab', { name: /Autonomous/i }).click();

    // Wait for tab content
    await page.waitForTimeout(500);

    // Check for Enable toggle
    await expect(page.getByText(/Enable Autonomous Operations/i)).toBeVisible();

    // Check for Circuit Breaker Threshold
    await expect(page.getByLabel(/Circuit Breaker Threshold/i)).toBeVisible();

    // Check for Retry Attempts
    await expect(page.getByLabel(/Retry Attempts/i)).toBeVisible();

    // Check for Retry Delay
    await expect(page.getByLabel(/Retry Delay/i)).toBeVisible();
  });

  test('UI Preferences tab - should display theme options', async ({ page }) => {
    // Click UI Preferences tab
    await page.getByRole('tab', { name: /UI Preferences/i }).click();

    // Wait for tab content
    await page.waitForTimeout(500);

    // Check for Theme select
    await expect(page.getByLabel(/Theme/i)).toBeVisible();

    // Check for Typography select
    await expect(page.getByLabel(/Typography/i)).toBeVisible();

    // Check for Accent Color input
    await expect(page.getByLabel(/Accent Color/i)).toBeVisible();
  });

  test('System tab - should display system configuration', async ({ page }) => {
    // Click System tab
    await page.getByRole('tab', { name: /System/i }).click();

    // Wait for tab content
    await page.waitForTimeout(500);

    // Check for API Timeout
    await expect(page.getByLabel(/API Timeout/i)).toBeVisible();

    // Check for Max Concurrent Requests
    await expect(page.getByLabel(/Max Concurrent Requests/i)).toBeVisible();

    // Check for Log Level
    await expect(page.getByLabel(/Log Level/i)).toBeVisible();
  });

  test('should allow switching between tabs', async ({ page }) => {
    // Start on WordPress tab
    await expect(page.getByLabel(/WordPress URL/i)).toBeVisible();

    // Switch to Vercel
    await page.getByRole('tab', { name: /Vercel/i }).click();
    await page.waitForTimeout(300);
    await expect(page.getByLabel(/Project ID/i)).toBeVisible();

    // Switch to Autonomous
    await page.getByRole('tab', { name: /Autonomous/i }).click();
    await page.waitForTimeout(300);
    await expect(page.getByLabel(/Circuit Breaker Threshold/i)).toBeVisible();

    // Switch to UI Preferences
    await page.getByRole('tab', { name: /UI Preferences/i }).click();
    await page.waitForTimeout(300);
    await expect(page.getByLabel(/Theme/i)).toBeVisible();

    // Switch to System
    await page.getByRole('tab', { name: /System/i }).click();
    await page.waitForTimeout(300);
    await expect(page.getByLabel(/API Timeout/i)).toBeVisible();

    // Switch back to WordPress
    await page.getByRole('tab', { name: /WordPress/i }).click();
    await page.waitForTimeout(300);
    await expect(page.getByLabel(/WordPress URL/i)).toBeVisible();
  });

  test('should allow entering values in WordPress settings', async ({ page }) => {
    // Enter WordPress URL
    const wpUrlInput = page.getByLabel(/WordPress URL/i);
    await wpUrlInput.fill('https://test.wordpress.com');
    await expect(wpUrlInput).toHaveValue('https://test.wordpress.com');

    // Enter Consumer Key
    const keyInput = page.getByLabel(/Consumer Key/i);
    await keyInput.fill('ck_test123456');
    await expect(keyInput).toHaveValue('ck_test123456');

    // Enter Consumer Secret
    const secretInput = page.getByLabel(/Consumer Secret/i);
    await secretInput.fill('cs_test123456');
    await expect(secretInput).toHaveValue('cs_test123456');
  });

  test('should show success message after saving', async ({ page }) => {
    // Enter some test data
    const wpUrlInput = page.getByLabel(/WordPress URL/i);
    await wpUrlInput.fill('https://test.wordpress.com');

    // Click Save All button
    const saveButton = page.getByRole('button', { name: /Save All/i });
    await saveButton.click();

    // Wait for save operation
    await page.waitForTimeout(1000);

    // Check for success indicator (button should show "Saved" or have success state)
    await expect(page.getByRole('button', { name: /Saved/i })).toBeVisible();
  });

  test('should have proper page styling with luxury theme', async ({ page }) => {
    // Check for luxury gradient in title
    const title = page.locator('h1');
    await expect(title).toHaveClass(/luxury-text-gradient/);

    // Check for proper font classes (from layout.tsx)
    const html = page.locator('html');
    await expect(html).toHaveClass(/playfair_display/);
    await expect(html).toHaveClass(/cormorant_garamond/);
  });
});
