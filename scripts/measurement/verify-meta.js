#!/usr/bin/env node
// scripts/measurement/verify-meta.js
// Phase 0.5 verifier — confirms META_SYSTEM_USER_TOKEN works and has the expected scopes.
//
// API: GET https://graph.facebook.com/v21.0/debug_token?input_token=...&access_token=...
// debug_token is Meta's canonical "validate this token" endpoint — it returns app_id, type, scopes,
// and expires_at without consuming any rate-limited resource. We assert:
//   - token is valid (data.is_valid === true)
//   - it's a System User token (data.type contains "SYSTEM_USER")
//   - required scopes are present (ads_read + business_management at minimum)
//
// Why we assert 2 of the 4 scopes the packet asks Corey to grant: ads_read + business_management
// are sufficient for THIS verifier (token validity + business linkage). The other two scopes
// (ads_management, pages_read_engagement) only get exercised by Phase 6.6 CAPI and Page-insights
// pulls, so the Phase 0.5 verifier intentionally has no coverage for them. Don't tighten this
// to require all four — that would block Phase 0.5 on a scope this script never actually uses.

import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'meta';
const REQUIRED_SCOPES = ['ads_read', 'business_management'];

requireEnv(['META_SYSTEM_USER_TOKEN'], NAME, 'Step 5 (Meta Business System User)');

const token = process.env.META_SYSTEM_USER_TOKEN;
const url = `https://graph.facebook.com/v21.0/debug_token?input_token=${encodeURIComponent(token)}&access_token=${encodeURIComponent(token)}`;

try {
  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok || !body?.data) {
    fail(NAME, `debug_token returned ${res.status}: ${JSON.stringify(body)}`, 're-generate token in Step 5.10–5.13');
    process.exit(EXIT_FAIL);
  }
  const { is_valid, type, scopes = [], expires_at, application } = body.data;
  if (!is_valid) {
    fail(NAME, `token is_valid=false (likely expired or revoked)`, 're-generate in Business Settings → System Users');
    process.exit(EXIT_FAIL);
  }
  const missingScopes = REQUIRED_SCOPES.filter((s) => !scopes.includes(s));
  if (missingScopes.length > 0) {
    fail(
      NAME,
      `token missing required scope(s): ${missingScopes.join(', ')}`,
      're-issue with all scopes from Step 5.12 checked'
    );
    process.exit(EXIT_FAIL);
  }
  const expiresLabel =
    expires_at === 0 ? 'never expires (long-lived system user token)' : new Date(expires_at * 1000).toISOString();
  pass(NAME, `valid ${type} token for app "${application}" — scopes: ${scopes.length}, expires: ${expiresLabel}`);
  process.exit(EXIT_PASS);
} catch (err) {
  fail(NAME, err.message);
  process.exit(EXIT_FAIL);
}
