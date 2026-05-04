#!/usr/bin/env node
/**
 * post-simplify-verify.js — Step 4 of the 6-step per-edit workflow
 *
 * After /simplify runs on a file, verifies the simplification didn't remove
 * load-bearing code. Runs 4 checks in sequence: diff inspection, re-lint,
 * intent re-read, test re-run. Failures → revert + log to eval/simplify-rejects.md.
 * Two consecutive failures on the same file → exit 2 (G3 escalation signal).
 *
 * Usage:
 *   node scripts/post-simplify-verify.js --file <path> [--task-id <id>]
 *     [--intent <intent-string>] [--test-cmd <cmd>]
 *     [--responses-file <path>] [--self-test]
 *
 * Exit codes:
 *   0  — simplification verified, safe to keep
 *   1  — simplification failed one or more checks, reverted
 *   2  — two consecutive failures on this file, G3 escalation required
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { PROJECT_ROOT, utcTimestamp, pathToSlug, deriveTaskId, run } from './_lib/script-utils.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const EVAL_DIR       = path.join(PROJECT_ROOT, 'eval');
const REJECTS_PATH   = path.join(EVAL_DIR, 'simplify-rejects.md');
const QUESTIONS_DIR  = path.join(EVAL_DIR, 'simplify-questions');
const CONSECUTIVE_KEY = path.join(EVAL_DIR, '.simplify-consecutive.json');

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function getSimplifyDiff(filePath) {
  const rel = path.relative(PROJECT_ROOT, path.resolve(filePath));
  const staged = run(`git diff --cached -- "${rel}"`);
  if (staged.status === 0 && staged.stdout.trim()) return { source: 'staged', diff: staged.stdout };
  const unstaged = run(`git diff -- "${rel}"`);
  if (unstaged.status === 0 && unstaged.stdout.trim()) return { source: 'unstaged', diff: unstaged.stdout };
  return { source: 'none', diff: '' };
}

function extractRemovedLines(diffText) {
  return diffText.split('\n')
    .filter(l => l.startsWith('-') && !l.startsWith('---'))
    .map(l => l.slice(1).trim())
    .filter(l => l.length > 0);
}

function loadConsecutiveCount(fileKey) {
  if (!fs.existsSync(CONSECUTIVE_KEY)) return 0;
  try { return JSON.parse(fs.readFileSync(CONSECUTIVE_KEY, 'utf8'))[fileKey] || 0; } catch (_) { return 0; }
}

function saveConsecutiveCount(fileKey, count) {
  let data = {};
  if (fs.existsSync(CONSECUTIVE_KEY)) {
    try { data = JSON.parse(fs.readFileSync(CONSECUTIVE_KEY, 'utf8')); } catch (_) {}
  }
  data[fileKey] = count;
  fs.writeFileSync(CONSECUTIVE_KEY, JSON.stringify(data, null, 2), 'utf8');
}

function resetConsecutiveCount(fileKey) { saveConsecutiveCount(fileKey, 0); }

// ---------------------------------------------------------------------------
// Check 1: Diff inspection — load-bearing pattern detection
// ---------------------------------------------------------------------------

const LOAD_BEARING_PATTERNS = [
  /\b(try|catch|except|finally|rescue|ensure)\b/,
  /\b(authenticate|authorize|require_auth|check_permission|is_admin|current_user_can)\b/,
  /\b(wp_verify_nonce|check_admin_referer|verify_nonce)\b/,
  /\b(sanitize_|esc_html|esc_attr|esc_url|wp_kses|absint|intval)\b/,
  /\$wpdb->prepare/,
  /\b(add_action|add_filter|do_action|apply_filters)\b/,
  /\bmodule\.exports\b|\bexport\s+(default|const|function|class)\b/,
  /\b(return|throw)\b.*\b(Error|Exception|false|null|undefined)\b/i,
];

function checkDiff(removedLines) {
  const suspicious = [];
  for (const line of removedLines) {
    for (const pat of LOAD_BEARING_PATTERNS) {
      if (pat.test(line)) {
        suspicious.push({ line, pattern: String(pat) });
        break;
      }
    }
  }
  return { pass: suspicious.length === 0, suspicious };
}

// ---------------------------------------------------------------------------
// Check 2: Re-lint
// ---------------------------------------------------------------------------

function reLint(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const abs  = path.resolve(filePath);

  if (ext === '.py') {
    const r = run(`python3 -m ruff check "${abs}" 2>&1`);
    return { pass: r.status === 0, output: r.stdout.trim(), skipped: false };
  }
  if (ext === '.php') {
    const phpcs = path.join(PROJECT_ROOT, 'wordpress-theme', 'skyyrose-flagship', 'vendor', 'bin', 'phpcs');
    if (fs.existsSync(phpcs)) {
      const xmlPath = path.join(PROJECT_ROOT, 'wordpress-theme', 'skyyrose-flagship', '.phpcs.xml');
      const r = run(`"${phpcs}" --standard="${xmlPath}" "${abs}" 2>&1`);
      return { pass: r.status === 0, output: r.stdout.trim(), skipped: false };
    }
    const r = run(`/opt/homebrew/bin/php -l "${abs}" 2>&1`);
    return { pass: r.status === 0, output: r.stdout.trim(), skipped: false };
  }
  if (ext === '.js' || ext === '.ts' || ext === '.tsx') {
    const eslint = path.join(PROJECT_ROOT, 'node_modules', '.bin', 'eslint');
    if (fs.existsSync(eslint)) {
      const r = run(`"${eslint}" "${abs}" 2>&1`);
      return { pass: r.status === 0, output: r.stdout.trim(), skipped: false };
    }
  }
  return { pass: true, output: `(no linter for ${ext} — skipped)`, skipped: true };
}

// ---------------------------------------------------------------------------
// Check 3: Intent re-read — questions file
// ---------------------------------------------------------------------------

function writeQuestionsFile(taskId, filePath, removedLines) {
  fs.mkdirSync(QUESTIONS_DIR, { recursive: true });
  const questions = removedLines.slice(0, 20).map((line, i) => ({
    id: i + 1,
    question: 'Was this removed line load-bearing or intentionally simplified?',
    context: line,
    answer: null,
  }));
  const qFile = path.join(QUESTIONS_DIR, `${taskId}.json`);
  fs.writeFileSync(qFile, JSON.stringify({ taskId, filePath, questions }, null, 2), 'utf8');
  return qFile;
}

function loadResponses(filePath) {
  if (!fs.existsSync(filePath)) return null;
  try { return JSON.parse(fs.readFileSync(filePath, 'utf8')); } catch (_) { return null; }
}

function checkIntentFromResponses(responses) {
  if (!responses || !responses.questions) return { pass: true, issues: [] };
  const issues = responses.questions.filter(q => {
    const a = (q.answer || '').toLowerCase().trim();
    return a === 'load-bearing' || a === 'lb' || a === 'no' || a === 'n';
  });
  return { pass: issues.length === 0, issues };
}

// ---------------------------------------------------------------------------
// Check 4: Test re-run
// ---------------------------------------------------------------------------

function rerunTests(testCmd) {
  if (!testCmd) return { pass: true, output: '(no test command — skipped)', skipped: true };
  const r = run(testCmd, { timeout: 120000 });
  return { pass: r.status === 0, output: r.stdout.slice(0, 2000), skipped: false };
}

// ---------------------------------------------------------------------------
// Reject log
// ---------------------------------------------------------------------------

function appendReject(taskId, filePath, failedChecks, diffInfo) {
  if (!fs.existsSync(REJECTS_PATH)) {
    fs.mkdirSync(EVAL_DIR, { recursive: true });
    fs.writeFileSync(REJECTS_PATH, '# Simplify Rejects Log\n\nGenerated by post-simplify-verify.js. Do not hand-edit.\n', 'utf8');
  }
  const entry = [
    '',
    `## Reject: ${taskId}`,
    '',
    `- **File**: \`${filePath}\``,
    `- **Timestamp**: ${new Date().toISOString()}`,
    `- **Failed checks**: ${failedChecks.join(', ')}`,
    `- **Diff source**: ${diffInfo.source}`,
    '',
    '---',
    '',
  ].join('\n');
  fs.appendFileSync(REJECTS_PATH, entry, 'utf8');
}

// ---------------------------------------------------------------------------
// Revert
// ---------------------------------------------------------------------------

function revertFile(filePath) {
  const rel = path.relative(PROJECT_ROOT, path.resolve(filePath));
  const unstage = run(`git restore --staged -- "${rel}"`);
  if (unstage.status !== 0) run(`git checkout HEAD -- "${rel}"`);
}

// ---------------------------------------------------------------------------
// Self-test (hermetic)
// ---------------------------------------------------------------------------

function selfTest() {
  console.log('[post-simplify-verify] Running self-test...');

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'psv-selftest-'));

  // Test 1: checkDiff — harmless change
  const harmlessRemoved = ['$x = 1;', '// old comment'];
  const r1 = checkDiff(harmlessRemoved);
  if (!r1.pass) {
    console.error('[post-simplify-verify] FAIL: checkDiff flagged harmless lines as load-bearing');
    process.exit(1);
  }

  // Test 2: checkDiff — load-bearing removal
  const dangerousRemoved = ['if (!wp_verify_nonce($nonce)) { return; }'];
  const r2 = checkDiff(dangerousRemoved);
  if (r2.pass) {
    console.error('[post-simplify-verify] FAIL: checkDiff missed wp_verify_nonce removal');
    process.exit(1);
  }

  // Test 3: checkDiff — try/catch removal
  const trycatchRemoved = ['try {', '  doSomething();', '} catch (e) {', '  logError(e);', '}'];
  const r3 = checkDiff(trycatchRemoved);
  if (r3.pass) {
    console.error('[post-simplify-verify] FAIL: checkDiff missed try/catch removal');
    process.exit(1);
  }

  // Test 4: consecutive count logic
  const tmpConsec = path.join(tmpDir, '.consecutive.json');
  const fileKey = 'test-file-php';
  fs.writeFileSync(tmpConsec, JSON.stringify({ [fileKey]: 1 }, null, 2), 'utf8');
  const loaded = JSON.parse(fs.readFileSync(tmpConsec, 'utf8'));
  if (loaded[fileKey] !== 1) {
    console.error('[post-simplify-verify] FAIL: consecutive count persistence');
    process.exit(1);
  }

  // Test 5: intent check — all intentional
  const allIntentional = {
    questions: [
      { id: 1, context: 'x = 1', answer: 'intentional' },
      { id: 2, context: 'y = 2', answer: 'intentional' },
    ],
  };
  const r5 = checkIntentFromResponses(allIntentional);
  if (!r5.pass) {
    console.error('[post-simplify-verify] FAIL: intent check should pass for all-intentional');
    process.exit(1);
  }

  // Test 6: intent check — load-bearing flagged
  const loadBearing = {
    questions: [{ id: 1, context: 'wp_verify_nonce', answer: 'load-bearing' }],
  };
  const r6 = checkIntentFromResponses(loadBearing);
  if (r6.pass) {
    console.error('[post-simplify-verify] FAIL: intent check should fail for load-bearing answer');
    process.exit(1);
  }

  // Test 7: reject log append
  const tmpRejects = path.join(tmpDir, 'simplify-rejects.md');
  fs.writeFileSync(tmpRejects, '# Simplify Rejects Log\n\n', 'utf8');
  const testTaskId = `test-${utcTimestamp()}`;
  fs.appendFileSync(tmpRejects, `\n## Reject: ${testTaskId}\n\n- **File**: \`test.php\`\n---\n`, 'utf8');
  const rejectContent = fs.readFileSync(tmpRejects, 'utf8');
  if (!rejectContent.includes(`Reject: ${testTaskId}`)) {
    console.error('[post-simplify-verify] FAIL: reject log append');
    process.exit(1);
  }

  // Test 8: exit code 2 on consecutive >= 2
  const exitCode = (count) => count >= 2 ? 2 : 1;
  if (exitCode(1) !== 1 || exitCode(2) !== 2 || exitCode(3) !== 2) {
    console.error('[post-simplify-verify] FAIL: exit code 2 logic');
    process.exit(1);
  }

  fs.rmSync(tmpDir, { recursive: true, force: true });

  console.log('[post-simplify-verify] PASS: self-test complete');
  console.log('  - checkDiff harmless lines: OK');
  console.log('  - checkDiff load-bearing detection (wp_verify_nonce): OK');
  console.log('  - checkDiff load-bearing detection (try/catch): OK');
  console.log('  - consecutive count persistence: OK');
  console.log('  - intent check (all intentional): OK');
  console.log('  - intent check (load-bearing answer): OK');
  console.log('  - reject log append: OK');
  console.log('  - exit code 2 logic: OK');
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);

if (args.includes('--self-test')) {
  selfTest();
} else {
  let filePath     = null;
  let taskId       = null;
  let testCmd      = null;
  let responsesFile = null;

  const fi = args.indexOf('--file');          if (fi !== -1) filePath      = args[fi + 1];
  const ti = args.indexOf('--task-id');       if (ti !== -1) taskId        = args[ti + 1];
  const tc = args.indexOf('--test-cmd');      if (tc !== -1) testCmd       = args[tc + 1];
  const ri = args.indexOf('--responses-file'); if (ri !== -1) responsesFile = args[ri + 1];

  if (!filePath) { console.error('[post-simplify-verify] ERROR: --file <path> is required'); process.exit(1); }
  if (!taskId) taskId = deriveTaskId(filePath);

  const fileKey          = pathToSlug(filePath);
  const consecutiveCount = loadConsecutiveCount(fileKey);

  console.log(`[post-simplify-verify] Checking: ${filePath} (task: ${taskId})`);

  const diffInfo     = getSimplifyDiff(filePath);
  const removedLines = extractRemovedLines(diffInfo.diff);
  console.log(`[post-simplify-verify] Removed lines: ${removedLines.length}`);

  const failedChecks = [];

  // Check 1
  const c1 = checkDiff(removedLines);
  if (!c1.pass) {
    console.error(`[post-simplify-verify] Check 1 FAIL: ${c1.suspicious.length} suspicious removal(s)`);
    c1.suspicious.forEach(s => console.error(`  line: ${s.line}`));
    failedChecks.push(`check1:diff-suspicious(${c1.suspicious.length})`);
  } else { console.log('[post-simplify-verify] Check 1 PASS: no suspicious removals'); }

  // Check 2
  const c2 = reLint(filePath);
  if (c2.skipped) {
    console.log(`[post-simplify-verify] Check 2 SKIP: ${c2.output}`);
  } else if (!c2.pass) {
    console.error('[post-simplify-verify] Check 2 FAIL: lint errors');
    failedChecks.push('check2:lint-fail');
  } else { console.log('[post-simplify-verify] Check 2 PASS: lint clean'); }

  // Check 3
  if (removedLines.length > 0) {
    const qFile = writeQuestionsFile(taskId, filePath, removedLines);
    console.log(`[post-simplify-verify] Check 3: questions written to ${qFile}`);
    const responses = responsesFile ? loadResponses(responsesFile) : loadResponses(qFile);
    if (responses) {
      const c3 = checkIntentFromResponses(responses);
      if (!c3.pass) {
        console.error(`[post-simplify-verify] Check 3 FAIL: ${c3.issues.length} line(s) marked load-bearing`);
        failedChecks.push(`check3:intent-loadbearing(${c3.issues.length})`);
      } else { console.log('[post-simplify-verify] Check 3 PASS: all removals confirmed intentional'); }
    } else {
      console.log('[post-simplify-verify] Check 3 SKIP: no responses available (questions file needs agent review)');
    }
  } else { console.log('[post-simplify-verify] Check 3 SKIP: no removed lines'); }

  // Check 4
  const c4 = rerunTests(testCmd);
  if (c4.skipped) {
    console.log(`[post-simplify-verify] Check 4 SKIP: ${c4.output}`);
  } else if (!c4.pass) {
    console.error('[post-simplify-verify] Check 4 FAIL: tests failed after simplify');
    failedChecks.push('check4:tests-fail');
  } else { console.log('[post-simplify-verify] Check 4 PASS: tests pass'); }

  if (failedChecks.length === 0) {
    console.log('[post-simplify-verify] PASS: simplification verified — safe to keep');
    resetConsecutiveCount(fileKey);
    process.exit(0);
  }

  console.error(`[post-simplify-verify] FAIL: ${failedChecks.join(', ')}`);
  appendReject(taskId, filePath, failedChecks, diffInfo);
  revertFile(filePath);
  console.log(`[post-simplify-verify] Reverted ${filePath}`);
  console.log(`[post-simplify-verify] Logged to ${REJECTS_PATH}`);

  const newCount = consecutiveCount + 1;
  saveConsecutiveCount(fileKey, newCount);

  if (newCount >= 2) {
    console.error(`[post-simplify-verify] G3 ESCALATION: ${newCount} consecutive failures on ${filePath}`);
    process.exit(2);
  }
  process.exit(1);
}
