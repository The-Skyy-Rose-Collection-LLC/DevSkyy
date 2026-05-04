#!/usr/bin/env node
// scripts/measurement/verify-google-service-account.js
// Phase 0.5 verifier — confirms GOOGLE_SERVICE_ACCOUNT_JSON parses and can mint an access token.
//
// This is the cheapest of the Google verifiers — token issuance is local crypto + a single OAuth
// exchange, so it doesn't burn any per-API quota. Run this first; if it fails, the GA4/GSC/GTM
// verifiers will all fail for the same reason.

import { createJwtClient, getServiceAccountEmail, SCOPES } from './_lib/google-jwt.js';
import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'google-service-account';

requireEnv(['GOOGLE_SERVICE_ACCOUNT_JSON'], NAME, 'Step 1 (Google Cloud service account)');

try {
  const email = getServiceAccountEmail();
  const client = createJwtClient(SCOPES.GA4);
  const token = await client.getAccessToken();
  if (!token || !token.token) {
    fail(NAME, 'authorize() returned empty token', 'check that the service account is enabled in IAM');
    process.exit(EXIT_FAIL);
  }
  const expiresIn = token.res?.data?.expires_in ?? 3600;
  pass(NAME, `authed as ${email} (token expires in ${Math.round(expiresIn / 60)} min)`);
  process.exit(EXIT_PASS);
} catch (err) {
  fail(NAME, err.message, err.code === 'EBADJSON' ? 'see Step 7 — re-add the env var via shell redirection' : null);
  process.exit(EXIT_FAIL);
}
