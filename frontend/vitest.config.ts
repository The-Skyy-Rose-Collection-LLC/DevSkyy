import path from 'node:path';

import { defineConfig } from 'vitest/config';

// Scoped to lib/wp: the rest of the dashboard has no unit-test runner wired
// (see frontend/CLAUDE.md) — this config exists specifically for the
// framework-free WP-wiring modules (auth-policy, signature, throttle),
// which `lib/wp/client.ts` composes behind a `server-only` boundary that
// vitest's default resolver cannot satisfy.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['lib/wp/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
