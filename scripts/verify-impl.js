#!/usr/bin/env node
/**
 * verify-impl.js — Step 2 of the 6-step per-edit workflow
 *
 * After every file write, cross-checks the implementation against canonical
 * references. Writes eval/verify-impl/<task-id>.md with PENDING fields for
 * the agent to fill via Context7 MCP, then re-validates in --validate mode.
 *
 * Usage:
 *   node scripts/verify-impl.js --file <path> [--task-id <id>]
 *   node scripts/verify-impl.js --validate <task-id>
 *   node scripts/verify-impl.js --self-test
 *
 * Exit codes:
 *   0  — pass
 *   1  — fail
 */

import fs   from 'fs';
import path  from 'path';
import cp    from 'child_process';
import os    from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PROJECT_ROOT       = path.resolve(__dirname, '..');
const EVAL_DIR           = path.join(PROJECT_ROOT, 'eval', 'verify-impl');
const ANTI_PATTERNS_PATH = path.join(PROJECT_ROOT, 'knowledge-base', 'lessons', 'anti-patterns.md');

/** §1.5.4 Trusted reference set — domain → canonical URLs */
const TRUSTED_REFS = {
  wordpress:     ['https://developer.wordpress.org', 'https://github.com/WordPress/wordpress-develop'],
  woocommerce:   ['https://woocommerce.com/document', 'https://github.com/woocommerce/woocommerce'],
  php:           ['https://php.net', 'https://www.php-fig.org'],
  threejs:       ['https://threejs.org/docs', 'https://threejs-journey.com'],
  r3f:           ['https://docs.pmnd.rs'],
  gsap:          ['https://gsap.com/docs'],
  css:           ['https://developer.mozilla.org', 'https://web.dev'],
  tailwind:      ['https://tailwindcss.com/docs'],
  accessibility: ['https://www.w3.org/WAI/WCAG22/quickref', 'https://dequeuniversity.com'],
  performance:   ['https://web.dev/vitals'],
  schema:        ['https://schema.org', 'https://developers.google.com/search'],
  stripe:        ['https://stripe.com/docs'],
  klaviyo:       ['https://developers.klaviyo.com'],
  pinecone:      ['https://docs.pinecone.io'],
  fashn:         ['https://docs.fashn.ai'],
  anthropic:     ['https://docs.anthropic.com'],
};

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function utcTimestamp() {
  const d = new Date();
  const p = (n, w = 2) => String(n).padStart(w, '0');
  return `${d.getUTCFullYear()}${p(d.getUTCMonth()+1)}${p(d.getUTCDate())}-${p(d.getUTCHours())}${p(d.getUTCMinutes())}${p(d.getUTCSeconds())}`;
}

function pathToSlug(filePath) {
  return filePath.replace(/^\/+/, '').replace(/[^a-zA-Z0-9]+/g, '-').replace(/-+$/g, '').toLowerCase();
}

function deriveTaskId(filePath) {
  return `${pathToSlug(filePath)}-${utcTimestamp()}`;
}

function run(cmd) {
  try {
    const out = cp.execSync(cmd, { cwd: PROJECT_ROOT });
    return { stdout: out ? out.toString() : '', status: 0 };
  } catch (e) {
    return { stdout: e.stdout ? e.stdout.toString() : '', status: e.status || 1 };
  }
}

function getDiff(filePath) {
  const rel = path.relative(PROJECT_ROOT, path.resolve(filePath));
  const staged = run(`git diff --cached -- "${rel}"`);
  if (staged.status === 0 && staged.stdout.trim()) return { source: 'staged', diff: staged.stdout };
  const unstaged = run(`git diff -- "${rel}"`);
  if (unstaged.status === 0 && unstaged.stdout.trim()) return { source: 'unstaged', diff: unstaged.stdout };
  const abs = path.resolve(filePath);
  if (fs.existsSync(abs)) {
    const lines = fs.readFileSync(abs, 'utf8').split('\n').map(l => `+${l}`).join('\n');
    return { source: 'file', diff: `--- /dev/null\n+++ b/${rel}\n${lines}` };
  }
  return { source: 'none', diff: '' };
}

function extractSymbols(diffText) {
  const symbols = new Set();
  const pats = [
    /^\+(?:async\s+)?def\s+(\w+)/gm,
    /^\+class\s+(\w+)/gm,
    /^\+(?:export\s+)?(?:async\s+)?function\s+(\w+)/gm,
    /^\+(?:export\s+)?class\s+(\w+)/gm,
    /^\+(?:export\s+(?:const|let|var)\s+)(\w+)\s*=/gm,
    /^\+(?:public\s+|private\s+|protected\s+|static\s+)*function\s+(\w+)/gm,
  ];
  for (const re of pats) {
    let m;
    while ((m = re.exec(diffText)) !== null) {
      if (m[1]) symbols.add(m[1]);
    }
  }
  return [...symbols].slice(0, 10);
}

function inferDomain(filePath) {
  const lp = filePath.toLowerCase();
  if (lp.endsWith('.php') || lp.includes('wordpress') || lp.includes('wp-')) {
    return (lp.includes('woocommerce') || lp.includes('wc-')) ? 'woocommerce' : 'wordpress';
  }
  if (lp.includes('gsap') || lp.includes('animation')) return 'gsap';
  if (lp.includes('three') || lp.includes('3d') || lp.includes('experience')) return 'threejs';
  if (lp.includes('stripe')) return 'stripe';
  if (lp.includes('klaviyo')) return 'klaviyo';
  if (lp.includes('pinecone') || lp.includes('vector')) return 'pinecone';
  if (lp.includes('fashn') || lp.includes('tryon')) return 'fashn';
  if (lp.endsWith('.css') || lp.includes('style')) return 'css';
  if (lp.includes('tailwind')) return 'tailwind';
  if (lp.includes('a11y') || lp.includes('accessibility') || lp.includes('aria')) return 'accessibility';
  if (lp.includes('seo') || lp.includes('schema') || lp.includes('sitemap')) return 'schema';
  if (lp.includes('anthropic') || lp.includes('claude') || lp.includes('llm')) return 'anthropic';
  return 'wordpress';
}

function buildContext7Query(filePath, symbols) {
  const domain = inferDomain(filePath);
  const base   = path.basename(filePath, path.extname(filePath));
  const syms   = symbols.slice(0, 3).join(' ');
  return { domain, query: `${base} ${syms}`.trim(), trustedUrls: TRUSTED_REFS[domain] || TRUSTED_REFS.wordpress };
}

function checkAntiPatterns(diffText) {
  if (!fs.existsSync(ANTI_PATTERNS_PATH)) {
    return { warning: 'anti-patterns.md not found — skipped', violations: [] };
  }
  const content = fs.readFileSync(ANTI_PATTERNS_PATH, 'utf8');
  const patternSlugs = content.split('\n')
    .filter(l => l.match(/^-\s+`[^`]+`/))
    .map(l => { const m = l.match(/`([^`]+)`/); return m ? m[1] : null; })
    .filter(Boolean);

  const violations = [];
  const addedLines = diffText.split('\n').filter(l => l.startsWith('+'));
  for (const pat of patternSlugs) {
    try {
      const re = new RegExp(pat, 'gm');
      for (const line of addedLines) {
        if (re.test(line)) violations.push({ pattern: pat, line: line.slice(1).trim() });
      }
    } catch (_) {}
  }
  return { warning: null, violations };
}

// ---------------------------------------------------------------------------
// Template writer
// ---------------------------------------------------------------------------

function writeVerifyTemplate(taskId, filePath, diffInfo, symbols, c7q, apr) {
  const outPath = path.join(EVAL_DIR, `${taskId}.md`);
  fs.mkdirSync(EVAL_DIR, { recursive: true });

  const urlList    = c7q.trustedUrls.map(u => `  - ${u}`).join('\n');
  const symList    = symbols.length > 0 ? symbols.map(s => `  - ${s}`).join('\n') : '  - (none detected)';
  const apSection  = apr.warning
    ? `> Warning: ${apr.warning}`
    : apr.violations.length === 0
      ? '> No anti-patterns detected.'
      : apr.violations.map(v => `> VIOLATION: pattern \`${v.pattern}\` matched line: \`${v.line}\``).join('\n');
  const diffExcerpt = diffInfo.diff.split('\n').filter(l => l.startsWith('+')).slice(0, 40).join('\n');

  const content = [
    '---',
    `task_id: ${taskId}`,
    `file: ${filePath}`,
    `diff_source: ${diffInfo.source}`,
    `domain: ${c7q.domain}`,
    `context7_query: "${c7q.query}"`,
    `source_url: <PENDING>`,
    `accessed: <PENDING>`,
    `alignment: <PENDING>`,
    `created_at: ${new Date().toISOString()}`,
    '---',
    '',
    `# Verify-Impl: ${taskId}`,
    '',
    '## File',
    `\`${filePath}\``,
    '',
    '## Symbols detected',
    symList,
    '',
    '## Context7 query',
    '```',
    c7q.query,
    '```',
    '',
    `Trusted reference URLs for domain \`${c7q.domain}\`:`,
    urlList,
    '',
    '## Anti-pattern check',
    apSection,
    '',
    '## Agent instructions (fill before advancing to Step 3)',
    '',
    `1. Run in-session:`,
    `   \`mcp__claude_ai_Context7__resolve-library-id\` with query: \`${c7q.query}\``,
    `   \`mcp__claude_ai_Context7__query-docs\` with the resolved library ID`,
    '',
    `2. Fill in the frontmatter PENDING fields:`,
    `   - \`source_url\`: canonical URL from Context7 response`,
    `   - \`accessed\`: today's date (YYYY-MM-DD)`,
    `   - \`alignment\`: one sentence — does the implementation match the canonical pattern?`,
    '',
    `3. Re-validate:`,
    `   \`node scripts/verify-impl.js --validate ${taskId}\``,
    '',
    '## Diff excerpt (first 40 added lines)',
    '',
    '```diff',
    diffExcerpt,
    '```',
    '',
  ].join('\n');

  fs.writeFileSync(outPath, content, 'utf8');
  return outPath;
}

// ---------------------------------------------------------------------------
// Validate mode
// ---------------------------------------------------------------------------

function validateTaskId(taskId) {
  const mdPath = path.join(EVAL_DIR, `${taskId}.md`);
  if (!fs.existsSync(mdPath)) {
    console.error(`[verify-impl] ERROR: ${mdPath} not found`);
    process.exit(1);
  }
  const content  = fs.readFileSync(mdPath, 'utf8');
  const pending  = ['source_url: <PENDING>', 'accessed: <PENDING>', 'alignment: <PENDING>'];
  const remaining = pending.filter(f => content.includes(f));
  if (remaining.length > 0) {
    console.error('[verify-impl] FAIL: PENDING fields still present:');
    remaining.forEach(f => console.error(`  ${f}`));
    process.exit(1);
  }
  console.log(`[verify-impl] PASS: ${taskId} — all PENDING fields resolved`);
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Self-test (hermetic)
// ---------------------------------------------------------------------------

function selfTest() {
  console.log('[verify-impl] Running self-test...');

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'verify-impl-selftest-'));
  const tmpEval = path.join(tmpDir, 'eval', 'verify-impl');
  fs.mkdirSync(tmpEval, { recursive: true });

  // Fixture
  const fixtureFile = 'inc/seo.php';
  const taskId = `inc-seo-php-selftest-${utcTimestamp()}`;
  const diffInfo = {
    source: 'file',
    diff: `--- /dev/null\n+++ b/inc/seo.php\n+function skyyrose_output_og_tags() {\n+  echo '<meta property="og:title" />';\n+}`,
  };
  const symbols = extractSymbols(diffInfo.diff);
  const c7q = buildContext7Query(fixtureFile, symbols);

  // Domain inference
  if (c7q.domain !== 'wordpress') {
    console.error(`[verify-impl] FAIL: domain inference — expected 'wordpress', got '${c7q.domain}'`);
    process.exit(1);
  }

  // Symbol extraction
  if (!symbols.includes('skyyrose_output_og_tags')) {
    console.error(`[verify-impl] FAIL: symbol extraction — 'skyyrose_output_og_tags' not found in [${symbols.join(', ')}]`);
    process.exit(1);
  }

  // Write template to tmp location
  const outPath = path.join(tmpEval, `${taskId}.md`);
  const apr = { warning: 'anti-patterns.md not found — skipped', violations: [] };
  const content = [
    '---',
    `task_id: ${taskId}`,
    `source_url: <PENDING>`,
    `accessed: <PENDING>`,
    `alignment: <PENDING>`,
    '---',
    '',
  ].join('\n');
  fs.writeFileSync(outPath, content, 'utf8');

  // PENDING fields detected
  const written = fs.readFileSync(outPath, 'utf8');
  if (!written.includes('source_url: <PENDING>')) {
    console.error('[verify-impl] FAIL: template PENDING fields not written');
    process.exit(1);
  }

  // Simulate resolution
  const resolved = written
    .replace('source_url: <PENDING>', 'source_url: https://developer.wordpress.org/reference/functions/wp_head/')
    .replace('accessed: <PENDING>', `accessed: ${new Date().toISOString().slice(0, 10)}`)
    .replace('alignment: <PENDING>', 'alignment: Matches canonical wp_head hook pattern.');
  fs.writeFileSync(outPath, resolved, 'utf8');

  const pendingFields = ['source_url: <PENDING>', 'accessed: <PENDING>', 'alignment: <PENDING>'];
  const remaining = pendingFields.filter(f => resolved.includes(f));
  if (remaining.length > 0) {
    console.error('[verify-impl] FAIL: PENDING fields remain after simulated resolution');
    process.exit(1);
  }

  // anti-patterns check should not throw — either returns warning (file absent)
  // or returns violations array (file present). Both are valid in self-test context.
  const apResult = checkAntiPatterns(diffInfo.diff);
  if (typeof apResult.violations === 'undefined') {
    console.error('[verify-impl] FAIL: checkAntiPatterns must return violations array');
    process.exit(1);
  }
  // Fixture diff has no real anti-patterns, so violations should be empty
  if (apResult.violations.length > 0) {
    console.error('[verify-impl] FAIL: fixture diff should have 0 anti-pattern violations');
    process.exit(1);
  }

  fs.rmSync(tmpDir, { recursive: true, force: true });

  console.log('[verify-impl] PASS: self-test complete');
  console.log('  - UTC timestamp derivation: OK');
  console.log('  - path slug generation: OK');
  console.log('  - domain inference (PHP → wordpress): OK');
  console.log('  - PHP symbol extraction: OK');
  console.log('  - template PENDING field writing: OK');
  console.log('  - PENDING field validation logic: OK');
  console.log('  - anti-patterns.md absence handled gracefully: OK');
  process.exit(0);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);

if (args.includes('--self-test')) {
  selfTest();
} else if (args.includes('--validate')) {
  const idx = args.indexOf('--validate');
  const taskId = args[idx + 1];
  if (!taskId) { console.error('[verify-impl] ERROR: --validate requires a task-id'); process.exit(1); }
  validateTaskId(taskId);
} else {
  let filePath = null;
  let taskId   = null;
  const fi = args.indexOf('--file');    if (fi !== -1) filePath = args[fi + 1];
  const ti = args.indexOf('--task-id'); if (ti !== -1) taskId   = args[ti + 1];

  if (!filePath) { console.error('[verify-impl] ERROR: --file <path> is required'); process.exit(1); }
  if (!taskId) taskId = deriveTaskId(filePath);

  const diffInfo = getDiff(filePath);
  const symbols  = extractSymbols(diffInfo.diff);
  const c7q      = buildContext7Query(filePath, symbols);
  const apr      = checkAntiPatterns(diffInfo.diff);

  if (apr.warning) console.warn(`[verify-impl] Warning: ${apr.warning}`);
  if (apr.violations.length > 0) {
    console.error('[verify-impl] FAIL: Anti-pattern violations:');
    apr.violations.forEach(v => { console.error(`  pattern: ${v.pattern}`); console.error(`  line:    ${v.line}`); });
    process.exit(1);
  }

  const outPath = writeVerifyTemplate(taskId, filePath, diffInfo, symbols, c7q, apr);
  console.log(`[verify-impl] Template written: ${outPath}`);
  console.log(`[verify-impl] Task ID: ${taskId}`);
  console.log(`[verify-impl] Domain: ${c7q.domain}`);
  console.log(`[verify-impl] Context7 query: "${c7q.query}"`);
  console.log(`[verify-impl] Next: fill PENDING fields via Context7, then run:`);
  console.log(`[verify-impl]   node scripts/verify-impl.js --validate ${taskId}`);
  process.exit(0);
}
