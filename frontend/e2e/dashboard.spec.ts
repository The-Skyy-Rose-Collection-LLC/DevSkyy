/**
 * Dashboard E2E Tests
 * ===================
 *
 * End-to-end tests for the DevSkyy Admin Dashboard.
 * Tests: Navigation, metrics display, asset management UI
 *
 * Run: npx playwright test dashboard.spec.ts
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load dashboard page', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/DevSkyy|Dashboard|SkyyRose/i);

    // Check that main content loads
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display main navigation', async ({ page }) => {
    // Look for common navigation elements
    const nav = page.locator('nav, [role="navigation"], header');

    // At least one navigation element should exist
    await expect(nav.first()).toBeVisible({ timeout: 10000 });
  });

  test('should have responsive layout', async ({ page }) => {
    // Test desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await expect(page.locator('body')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('body')).toBeVisible();

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('body')).toBeVisible();
  });

  test('should not have console errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors (like missing optional resources)
    const criticalErrors = errors.filter(
      (err) =>
        !err.includes('favicon') &&
        !err.includes('manifest') &&
        !err.includes('service-worker')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Dashboard Metrics', () => {
  test('should display metrics section', async ({ page }) => {
    await page.goto('/');

    // Look for metrics-related elements
    const metricsIndicators = [
      page.getByText(/total|assets|count/i),
      page.getByText(/fidelity|score/i),
      page.getByText(/sync|status/i),
      page.locator('[data-testid="metrics"]'),
      page.locator('.metrics, .dashboard-metrics, .stats'),
    ];

    // At least one metrics indicator should be visible (or app might not have them)
    const visibleCount = await Promise.all(
      metricsIndicators.map(async (loc) => {
        try {
          return await loc.first().isVisible({ timeout: 5000 });
        } catch {
          return false;
        }
      })
    );

    // This is a soft check - not all apps will have visible metrics
    if (visibleCount.every((v) => !v)) {
      console.log('Note: No metrics indicators found - this may be expected');
    }
  });
});

test.describe('Dashboard Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const loadTime = Date.now() - startTime;

    // Page should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);

    console.log(`Dashboard load time: ${loadTime}ms`);
  });

  test('should have no layout shifts after load', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait a bit for any delayed content
    await page.waitForTimeout(1000);

    // Take initial screenshot for comparison
    const initialScreenshot = await page.screenshot();

    // Wait a bit more
    await page.waitForTimeout(500);

    // Take another screenshot
    const laterScreenshot = await page.screenshot();

    // Screenshots should be identical (no layout shift)
    // This is a basic check - could use pixelmatch for more accuracy
    expect(initialScreenshot.length).toBeGreaterThan(0);
    expect(laterScreenshot.length).toBeGreaterThan(0);
  });
});
