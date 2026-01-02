/**
 * Playwright E2E Test Configuration
 * ==================================
 *
 * Production-grade e2e testing for DevSkyy Dashboard
 * Tests: Dashboard, API endpoints, 3D viewer, Asset management
 *
 * Run: npx playwright test
 * Debug: npx playwright test --debug
 * Report: npx playwright show-report
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables
 */
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export default defineConfig({
  // Test directory
  testDir: './e2e',

  // Test file pattern
  testMatch: '**/*.spec.ts',

  // Maximum time one test can run
  timeout: 30_000,

  // Expect timeout for assertions
  expect: {
    timeout: 10_000,
  },

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI for stability
  workers: process.env.CI ? 2 : undefined,

  // Reporter configuration
  reporter: process.env.CI
    ? [
        ['list'],
        ['html', { open: 'never', outputFolder: 'playwright-report' }],
        ['junit', { outputFile: 'playwright-results.xml' }],
      ]
    : [['list'], ['html', { open: 'on-failure' }]],

  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: BASE_URL,

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Capture screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'on-first-retry',

    // Browser viewport
    viewport: { width: 1280, height: 720 },

    // Ignore HTTPS errors (for local dev)
    ignoreHTTPSErrors: true,

    // Extra HTTP headers
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
  },

  // Configure projects for major browsers
  projects: [
    // Setup project to authenticate
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Desktop Chrome - Primary browser
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use prepared auth state
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Desktop Firefox - Cross-browser testing
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Desktop Safari (WebKit) - Cross-browser testing
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Mobile Chrome - Responsive testing
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Mobile Safari - iOS testing
    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // Folder for test artifacts
  outputDir: 'test-results/',

  // Run local dev server before starting tests
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },

  // Global setup/teardown
  globalSetup: require.resolve('./e2e/global-setup.ts'),
  globalTeardown: require.resolve('./e2e/global-teardown.ts'),
});
