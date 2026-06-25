#!/usr/bin/env node
// scripts/measurement/verify-gsc.js
// Phase 0.5 verifier — confirms Search Console access on GSC_SITE_URL.
//
// API: POST https://searchconsole.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query
// siteUrl is URL-encoded; either "https://skyyrose.co/" or "sc-domain:skyyrose.co".
// Returns top 10 queries by clicks for the last 28 days (GSC's max range without daily-fresh constraints).

import { createJwtClient, readGaxiosError, SCOPES } from './_lib/google-jwt.js';
import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'gsc';

requireEnv(['GOOGLE_SERVICE_ACCOUNT_JSON', 'GSC_SITE_URL'], NAME, 'Step 3 (GSC) + Step 7 (GSC_SITE_URL)');

const siteUrl = process.env.GSC_SITE_URL;
const today = new Date();
const startDate = new Date(today);
startDate.setDate(startDate.getDate() - 28);
const iso = (d) => d.toISOString().slice(0, 10);

try {
  const client = createJwtClient(SCOPES.GSC);
  const url = `https://searchconsole.googleapis.com/webmasters/v3/sites/${encodeURIComponent(siteUrl)}/searchAnalytics/query`;
  const res = await client.fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      startDate: iso(startDate),
      endDate: iso(today),
      dimensions: ['query'],
      rowLimit: 10,
    }),
  });
  const rows = Array.isArray(res.data?.rows) ? res.data.rows : [];
  const topQuery = rows[0]?.keys?.[0] || '(no queries returned — site may be too new for search data)';
  pass(NAME, `${siteUrl} — ${rows.length} top queries returned (lead: "${topQuery}")`);
  process.exit(EXIT_PASS);
} catch (err) {
  const { status, data } = readGaxiosError(err);
  const detail = data?.error?.message || err.message;
  const hint =
    status === 403
      ? `service account lacks access on ${siteUrl} — re-do Step 3.4–3.7`
      : status === 404
      ? `property ${siteUrl} not found — check exact format (URL-prefix needs trailing slash)`
      : null;
  fail(NAME, `GSC searchAnalytics returned ${status || 'network error'}: ${detail}`, hint);
  process.exit(EXIT_FAIL);
}
