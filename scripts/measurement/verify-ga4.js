#!/usr/bin/env node
// scripts/measurement/verify-ga4.js
// Phase 0.5 verifier — confirms GA4 Data API access on GA4_PROPERTY_ID.
//
// API: POST https://analyticsdata.googleapis.com/v1beta/{property}:runReport
// Property format: "properties/123456789" (numeric ID, NOT the measurement ID `G-XXXXXX`)
// Returns last-30d sessions count as the baseline data point.

import { createJwtClient, readGaxiosError, SCOPES } from './_lib/google-jwt.js';
import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'ga4';

requireEnv(['GOOGLE_SERVICE_ACCOUNT_JSON', 'GA4_PROPERTY_ID'], NAME, 'Step 2 (GA4) + Step 7 (GA4_PROPERTY_ID)');

const propertyId = process.env.GA4_PROPERTY_ID.startsWith('properties/')
  ? process.env.GA4_PROPERTY_ID
  : `properties/${process.env.GA4_PROPERTY_ID}`;

try {
  const client = createJwtClient(SCOPES.GA4);
  const url = `https://analyticsdata.googleapis.com/v1beta/${propertyId}:runReport`;
  const res = await client.fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      dateRanges: [{ startDate: '30daysAgo', endDate: 'today' }],
      metrics: [{ name: 'sessions' }],
    }),
  });
  const sessions = Number(res.data?.rows?.[0]?.metricValues?.[0]?.value || 0);
  pass(NAME, `${propertyId} — ${sessions.toLocaleString()} sessions in last 30 days`);
  process.exit(EXIT_PASS);
} catch (err) {
  const { status, data } = readGaxiosError(err);
  const detail = data?.error?.message || err.message;
  const hint =
    status === 403
      ? `service account lacks Viewer on ${propertyId} — re-do Step 2.5–2.8`
      : status === 404
      ? `property ${propertyId} not found — confirm Property ID in GA4 Admin`
      : null;
  fail(NAME, `GA4 runReport returned ${status || 'network error'}: ${detail}`, hint);
  process.exit(EXIT_FAIL);
}
