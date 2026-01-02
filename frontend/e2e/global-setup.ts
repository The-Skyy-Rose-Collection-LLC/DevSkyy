/**
 * Global Setup for Playwright E2E Tests
 * =====================================
 *
 * Runs once before all tests to set up the test environment.
 * - Verifies backend API is reachable
 * - Creates auth state for authenticated tests
 * - Seeds test data if needed
 */

import { chromium, FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const API_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const AUTH_FILE = path.join(__dirname, '../playwright/.auth/user.json');

async function globalSetup(config: FullConfig) {
  console.log('\n🎭 Playwright Global Setup');
  console.log('================================');

  // Ensure auth directory exists
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // Check if API is available (skip in CI if backend isn't running)
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      console.log('✅ Backend API is reachable');
    } else {
      console.warn('⚠️ Backend API returned non-OK status:', response.status);
    }
  } catch (error) {
    console.warn('⚠️ Backend API not reachable (tests may skip API calls)');
  }

  // Create browser for authentication setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to app and check it's loading
    const baseURL = config.projects[0]?.use?.baseURL || 'http://localhost:3000';

    // Try to access the app
    try {
      await page.goto(baseURL, { timeout: 10000 });
      console.log('✅ Frontend is accessible');
    } catch {
      console.warn('⚠️ Frontend not accessible during setup (may start during test)');
    }

    // Save empty auth state for now (no auth implemented)
    // In a real app, this would log in and save cookies/localStorage
    await context.storageState({ path: AUTH_FILE });
    console.log('✅ Auth state saved');

  } finally {
    await browser.close();
  }

  console.log('================================');
  console.log('🎭 Global Setup Complete\n');
}

export default globalSetup;
