#!/usr/bin/env node
// scripts/measurement/verify-all-grants.js
// Phase 0.5 dispatcher — runs every verify-*.js sequentially, aggregates results, exits accordingly.
//
// Exit codes (from _lib/format.js):
//   0 = PASS              — credentials work, resource readable
//   1 = FAIL              — credentials present but API call failed
//   2 = MISSING_ENV       — required env var not set
//
// Aggregator policy:
//   - All PASS → exit 0 ("access packet complete, baselines ready to capture")
//   - Any FAIL → exit 1 ("something is broken — see per-verifier output")
//   - Otherwise (some MISSING_ENV but no FAIL) → exit 2 ("packet partially actioned")
//
// Why sequential, not parallel: when one verifier fails (e.g. bad service account JSON), the
// next three Google verifiers will fail for the same reason. Sequential output makes the chain
// of dependencies obvious in the console; parallel output interleaves and obscures it.

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const VERIFIERS = [
  { name: 'google-service-account', file: 'verify-google-service-account.js' },
  { name: 'ga4', file: 'verify-ga4.js' },
  { name: 'gsc', file: 'verify-gsc.js' },
  { name: 'gtm', file: 'verify-gtm.js' },
  { name: 'meta', file: 'verify-meta.js' },
  { name: 'sentry', file: 'verify-sentry.js' },
];

const here = path.dirname(fileURLToPath(import.meta.url));

function runScript(file) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [path.join(here, file)], { stdio: 'inherit', env: process.env });
    child.on('close', (code) => resolve(code ?? 1));
    child.on('error', () => resolve(1));
  });
}

const results = [];
console.log('=== Phase 0.5 access verifier ===\n');
for (const v of VERIFIERS) {
  const code = await runScript(v.file);
  results.push({ ...v, code });
}

const PASS = results.filter((r) => r.code === 0);
const FAIL = results.filter((r) => r.code === 1);
const SKIP = results.filter((r) => r.code === 2);

console.log('\n=== Summary ===');
console.log(`PASS: ${PASS.length}/${results.length}`);
if (FAIL.length) console.log(`FAIL: ${FAIL.map((r) => r.name).join(', ')}`);
if (SKIP.length) console.log(`SKIP: ${SKIP.map((r) => r.name).join(', ')}  (env vars missing — finish access packet)`);

if (FAIL.length > 0) {
  console.error('\n→ One or more verifiers failed. Fix the FAIL rows above before proceeding to baseline capture.');
  process.exit(1);
}
if (SKIP.length > 0) {
  console.error(
    '\n→ Some grants not yet provisioned. Action eval/measurement-access-requests.md and re-run this script.'
  );
  process.exit(2);
}
console.log('\n→ All grants verified. Phase 0.5 baseline capture (pull-baselines.js) is unblocked.');
process.exit(0);
