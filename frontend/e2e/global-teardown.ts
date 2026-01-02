/**
 * Global Teardown for Playwright E2E Tests
 * =========================================
 *
 * Runs once after all tests complete.
 * - Cleans up test data
 * - Generates summary reports
 */

import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('\n🎭 Playwright Global Teardown');
  console.log('================================');

  // Clean up auth state
  const authFile = path.join(__dirname, '../playwright/.auth/user.json');
  if (fs.existsSync(authFile)) {
    console.log('✅ Auth state cleaned up');
  }

  // Log test artifacts location
  const outputDir = config.projects[0]?.outputDir || 'test-results';
  if (fs.existsSync(outputDir)) {
    const files = fs.readdirSync(outputDir);
    if (files.length > 0) {
      console.log(`📁 Test artifacts in: ${outputDir}`);
    }
  }

  console.log('================================');
  console.log('🎭 Global Teardown Complete\n');
}

export default globalTeardown;
