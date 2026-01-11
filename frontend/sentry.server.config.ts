/**
 * Sentry Server Configuration
 * Runs on the server (Node.js)
 */

import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: 'https://5ddc352ad3ae6cf5e0d4727a8deeacdb@o4510219313545216.ingest.us.sentry.io/4510487462608896',

  // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring.
  // We recommend adjusting this value in production
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

  // Note: if you want to override the automatic release value, do not set a
  // `release` value here - use the environment variable `SENTRY_RELEASE`, so
  // that it will also get attached to your source maps
  environment: process.env.NODE_ENV || 'development',
});
