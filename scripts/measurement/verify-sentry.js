#!/usr/bin/env node
// scripts/measurement/verify-sentry.js
// Phase 0.5 verifier — confirms SENTRY_AUTH_TOKEN_READ + SENTRY_ORG_SLUG can list the two expected projects.
//
// API: GET https://sentry.io/api/0/organizations/{org_slug}/projects/
// Auth: Bearer {token}
// Asserts both `skyyrose-co` and `devskyy-app` projects exist (the two from Step 6.3).

import { pass, fail, requireEnv, EXIT_PASS, EXIT_FAIL } from './_lib/format.js';

const NAME = 'sentry';
const EXPECTED_PROJECTS = ['skyyrose-co', 'devskyy-app'];

requireEnv(
  ['SENTRY_AUTH_TOKEN_READ', 'SENTRY_ORG_SLUG'],
  NAME,
  'Step 6 (Sentry) + Step 7 (SENTRY_ORG_SLUG)'
);

const orgSlug = process.env.SENTRY_ORG_SLUG;
const url = `https://sentry.io/api/0/organizations/${encodeURIComponent(orgSlug)}/projects/`;

try {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${process.env.SENTRY_AUTH_TOKEN_READ}` },
  });
  if (!res.ok) {
    const body = await res.text();
    const hint =
      res.status === 401
        ? 'token rejected — confirm scopes include org:read and project:read'
        : res.status === 404
        ? `org "${orgSlug}" not found — verify the slug from your Sentry URL`
        : null;
    fail(NAME, `Sentry projects API returned ${res.status}: ${body.slice(0, 300)}`, hint);
    process.exit(EXIT_FAIL);
  }
  const projects = await res.json();
  const slugs = projects.map((p) => p.slug);
  const missingProjects = EXPECTED_PROJECTS.filter((p) => !slugs.includes(p));
  if (missingProjects.length > 0) {
    fail(
      NAME,
      `expected projects not found: ${missingProjects.join(', ')}`,
      `visible projects: ${slugs.join(', ') || '(none)'} — re-do Step 6.3 to create missing projects`
    );
    process.exit(EXIT_FAIL);
  }
  pass(
    NAME,
    `${orgSlug} — ${projects.length} project(s) visible, both required projects present (${EXPECTED_PROJECTS.join(', ')})`
  );
  process.exit(EXIT_PASS);
} catch (err) {
  fail(NAME, err.message);
  process.exit(EXIT_FAIL);
}
