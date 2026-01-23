/**
 * Authentication Setup
 * ====================
 *
 * This file handles authentication state setup for E2E tests.
 * Authenticates once and saves state for all tests to use.
 *
 * Usage:
 * - Tests that need auth should use: test.use({ storageState: 'playwright/.auth/user.json' })
 * - Run setup: npx playwright test --project=setup
 */

import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../playwright/.auth/user.json');
const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

// Test credentials (dev mode allows any credentials on localhost)
const TEST_USER = {
  username: 'testuser@devskyy.com',
  password: 'TestPassword123!',
};

setup('authenticate', async ({ page, request }) => {
  console.log('Starting authentication setup...');

  // Navigate to home first to establish browser context
  await page.goto('/');
  await page.waitForLoadState('domcontentloaded');

  // Strategy 1: Try API-based authentication first
  try {
    const response = await request.post(`${API_BASE}/api/v1/auth/token`, {
      form: {
        username: TEST_USER.username,
        password: TEST_USER.password,
        grant_type: 'password',
      },
      timeout: 5000,
    });

    if (response.ok()) {
      const tokens = await response.json();
      console.log('API authentication successful');

      // Store tokens in localStorage
      await page.evaluate((data) => {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('token_type', data.token_type || 'bearer');
        document.cookie = `access_token=${data.access_token}; path=/; max-age=3600`;
      }, tokens);

      // Reload to apply authentication
      await page.reload();
      await page.waitForLoadState('networkidle');

      // Save storage state
      await page.context().storageState({ path: authFile });
      console.log('Auth state saved to:', authFile);
      return;
    }
  } catch (error) {
    console.log('API auth failed (backend may not be running), trying UI login...');
  }

  // Strategy 2: UI-based login fallback
  try {
    await page.goto('/login', { timeout: 10000 });
    await page.waitForLoadState('domcontentloaded');

    // Fill login form
    const usernameInput = page.locator('[data-testid="username"]').first();
    const passwordInput = page.locator('[data-testid="password"]').first();
    const submitButton = page.locator('[data-testid="login-submit"]').first();

    // Check if login form exists
    const hasLoginForm = await usernameInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasLoginForm) {
      await usernameInput.fill(TEST_USER.username);
      await passwordInput.fill(TEST_USER.password);
      await submitButton.click();

      // Wait for redirect after login (or stay on page if API fails)
      await page.waitForTimeout(2000);
      console.log('UI login submitted');
    } else {
      console.log('No login form found - app may not require auth');
    }
  } catch (error) {
    console.log('UI login skipped - page may not exist');
  }

  // Ensure we're on a valid page
  try {
    await page.goto('/');
    await page.waitForLoadState('networkidle', { timeout: 10000 });
  } catch {
    // Ignore if already on a page
  }

  // Save storage state
  await page.context().storageState({ path: authFile });
  console.log('Auth setup complete');
});

setup('authenticate as admin', async ({ page, request }) => {
  const adminAuthFile = path.join(__dirname, '../playwright/.auth/admin.json');

  console.log('Starting admin authentication setup...');

  const ADMIN_USER = {
    username: 'admin@devskyy.com',
    password: 'AdminPassword123!',
  };

  try {
    const response = await request.post(`${API_BASE}/api/v1/auth/token`, {
      form: {
        username: ADMIN_USER.username,
        password: ADMIN_USER.password,
        grant_type: 'password',
      },
    });

    if (response.ok()) {
      const tokens = await response.json();
      console.log('Admin API authentication successful');

      await page.goto('/');
      await page.waitForLoadState('domcontentloaded');

      await page.evaluate((data) => {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('token_type', data.token_type || 'bearer');
        localStorage.setItem('user_role', 'admin');
      }, tokens);

      await page.reload();
      await page.waitForLoadState('networkidle');

      await page.context().storageState({ path: adminAuthFile });
      console.log('Admin auth state saved to:', adminAuthFile);
    }
  } catch (error) {
    console.log('Admin auth setup failed:', error);
  }
});
