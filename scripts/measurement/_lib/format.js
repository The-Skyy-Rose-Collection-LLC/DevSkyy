// scripts/measurement/_lib/format.js
// Shared exit-code conventions and formatters for verify-*.js scripts.
//
// Exit codes (read by verify-all-grants.js dispatcher):
//   0 = PASS              — credentials work, resource readable, baseline data captured
//   1 = FAIL              — credentials present but API call failed (auth scope, wrong ID, network, quota)
//   2 = MISSING_ENV       — required env var not set (Corey hasn't finished the access packet step)
//
// Why split 1 vs 2: tells the operator "you skipped a step" (2) vs "you broke a step" (1).
// The dispatcher prints both differently and exits non-zero only when at least one verifier returned 1 or 2.

export const EXIT_PASS = 0;
export const EXIT_FAIL = 1;
export const EXIT_MISSING_ENV = 2;

const COLORS = process.stdout.isTTY
  ? { green: '\x1b[32m', red: '\x1b[31m', yellow: '\x1b[33m', dim: '\x1b[2m', reset: '\x1b[0m' }
  : { green: '', red: '', yellow: '', dim: '', reset: '' };

export function pass(name, summary) {
  console.log(`${COLORS.green}PASS${COLORS.reset}  ${name}  ${COLORS.dim}${summary}${COLORS.reset}`);
}

export function fail(name, reason, hint) {
  console.error(`${COLORS.red}FAIL${COLORS.reset}  ${name}`);
  console.error(`      reason: ${reason}`);
  if (hint) console.error(`      hint:   ${hint}`);
}

export function missing(name, envVars, packetStep) {
  const list = Array.isArray(envVars) ? envVars.join(', ') : envVars;
  console.error(`${COLORS.yellow}SKIP${COLORS.reset}  ${name}`);
  console.error(`      missing env: ${list}`);
  if (packetStep) {
    console.error(`      next step:   eval/measurement-access-requests.md → ${packetStep}`);
  }
}

export function requireEnv(keys, scriptName, packetStep) {
  const missingKeys = keys.filter((k) => !process.env[k] || !process.env[k].trim());
  if (missingKeys.length > 0) {
    missing(scriptName, missingKeys, packetStep);
    process.exit(EXIT_MISSING_ENV);
  }
}
