import path from 'node:path';

import { defineConfig } from 'vitest/config';

// Scoped: the rest of the dashboard has no unit-test runner wired (see
// frontend/CLAUDE.md) — this config exists for framework-free lib modules
// that don't depend on Next.js-specific resolution: the WP-wiring modules
// (auth-policy, signature, throttle), which `lib/wp/client.ts` composes
// behind a `server-only` boundary vitest's default resolver can't satisfy,
// and lib/tripo/client.ts (fetch-only, no Next.js/server-only imports).
export default defineConfig({
  test: {
    environment: 'node',
    include: ['lib/wp/**/*.test.ts', 'lib/tripo/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
