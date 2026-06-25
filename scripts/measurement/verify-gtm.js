#!/usr/bin/env node
// scripts/measurement/verify-gtm.js
// Phase 0.5 verifier — confirms Tag Manager access on GTM_CONTAINER_ID.
//
// API gotcha: the public `GTM-XXXXXXX` slug ≠ the numeric container ID the API uses in paths.
// We list containers under GTM_ACCOUNT_ID and match by publicId. Then fetch the latest version header.
// This means GTM_ACCOUNT_ID + GTM_CONTAINER_ID (public slug) are sufficient — no third "internal ID" needed.

import { createJwtClient, readGaxiosError, SCOPES } from './_lib/google-jwt.js';
import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'gtm';

requireEnv(
  ['GOOGLE_SERVICE_ACCOUNT_JSON', 'GTM_ACCOUNT_ID', 'GTM_CONTAINER_ID'],
  NAME,
  'Step 4 (GTM) + Step 7 (GTM_ACCOUNT_ID, GTM_CONTAINER_ID)'
);

const accountId = process.env.GTM_ACCOUNT_ID;
const publicId = process.env.GTM_CONTAINER_ID;

try {
  const client = createJwtClient(SCOPES.GTM);
  const listRes = await client.fetch(
    `https://tagmanager.googleapis.com/tagmanager/v2/accounts/${accountId}/containers`
  );
  const match = (listRes.data?.container || []).find((c) => c.publicId === publicId);
  if (!match) {
    const visible = (listRes.data?.container || []).map((c) => c.publicId).join(', ') || '(none)';
    fail(
      NAME,
      `no container with publicId="${publicId}" under account ${accountId}`,
      `containers visible to the service account: ${visible}`
    );
    process.exit(EXIT_FAIL);
  }
  let versionLabel = '(unpublished — no live version yet)';
  try {
    const versionRes = await client.fetch(
      `https://tagmanager.googleapis.com/tagmanager/v2/accounts/${accountId}/containers/${match.containerId}/version_headers:latest`
    );
    if (versionRes.data?.name) versionLabel = versionRes.data.name;
  } catch {
    // unpublished containers return 404 from version_headers:latest — fall through with the default label
  }
  pass(NAME, `${publicId} (account ${accountId}) — latest version: ${versionLabel}`);
  process.exit(EXIT_PASS);
} catch (err) {
  const { status, data } = readGaxiosError(err);
  const detail = data?.error?.message || err.message;
  const hint =
    status === 403
      ? `service account lacks access to account ${accountId} — re-do Step 4.4–4.8`
      : status === 404
      ? `account ${accountId} not found — check the numeric account ID from the GTM URL`
      : null;
  fail(NAME, `GTM API returned ${status || 'network error'}: ${detail}`, hint);
  process.exit(EXIT_FAIL);
}
