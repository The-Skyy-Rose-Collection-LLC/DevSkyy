#!/usr/bin/env node
// scripts/measurement/verify-all-grants.js
// Phase 0.5 deliverable — dispatcher stub.
// Intentionally fails loudly so the operator knows the verifiers haven't been built yet,
// instead of seeing "Cannot find module" and assuming an environment problem.
//
// See: scripts/measurement/README.md for the planned script set
// See: eval/measurement-access-requests.md for the access packet that calls this
// See: eval/silent-disable-audit.md instance S5 for why this stub exists

const VERIFIERS = [
  'verify-google-service-account.js',
  'verify-gsc.js',
  'verify-gtm.js',
  'verify-meta.js',
  'verify-sentry.js',
];

const message = `
============================================================
  PHASE 0.5 VERIFIERS NOT YET BUILT
============================================================

This dispatcher (scripts/measurement/verify-all-grants.js) was generated
in Phase 0 as a stub. The individual verify-*.js scripts it would run do
not exist yet — they are a Phase 0.5 deliverable per:

  - docs/SKYYROSE_WORDPRESS_PLAN.md §WP-0.5
  - docs/SKYYROSE_V2_MASTER_PLAN.md §5 Phase 0.5
  - eval/measurement-access-requests.md (the action packet)

Planned verifiers:
${VERIFIERS.map((v) => `  - scripts/measurement/${v}`).join('\n')}

What to do next:
  1. If you've completed the access packet (eval/measurement-access-requests.md),
     reply "access packet complete" and Phase 0.5 will start, which builds these
     scripts and runs them.
  2. If you want to run an individual check before Phase 0.5 starts, the schemas
     are documented in scripts/measurement/README.md.

Exiting with code 1 (intentional — Phase 0.5 has not started).
============================================================
`;

console.error(message);
process.exit(1);
