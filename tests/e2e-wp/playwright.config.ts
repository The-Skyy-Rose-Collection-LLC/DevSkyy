import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for the SkyyRose WordPress theme (skyyrose.co).
 *
 * Distinct from frontend/playwright.config.ts which targets the Next.js
 * dashboard at devskyy.app. This suite runs against the customer storefront
 * — the WordPress theme deployed via scripts/deploy-theme.sh.
 *
 * Override target via BASE_URL env var (e.g. when running against a staging
 * mirror or a wp-now local instance).
 */
export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'https://skyyrose.co',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // No webServer — production target. To use wp-now locally, set BASE_URL
  // to http://localhost:8881 and run `npx @wordpress/wp-now start` separately.
});
