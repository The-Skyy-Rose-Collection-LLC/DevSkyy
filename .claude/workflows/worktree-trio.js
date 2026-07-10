export const meta = {
  name: 'worktree-trio',
  description: 'Advise→Execute→Review harness: Opus plans, Sonnet executes in an isolated git worktree, Fable code-reviews. Hard cap 3 agents per workstream, plus one optional cross-workstream integration checker.',
  whenToUse: 'Multi-workstream implementation sweeps where each item needs plan/build/review with worktree isolation. Invoke with args: {run_tag: "YYYYMMDD" (required — Date.now is unavailable in scripts), repo?: string, integrate?: boolean, on_model_downgrade?: "abort"|"proceed" (default abort — platform may silently downgrade opus/fable to sonnet; preflight detects this and aborts so the human decides), workstreams: [{key, title, brief, branch?}]}. Fix rounds are deliberately NOT in-workflow: needs-fix findings return to the main thread for triage (reviewer ≠ fixer).',
  phases: [
    { title: 'Preflight', detail: 'Probe + audit: verify requested models actually resolve; abort on silent downgrade unless caller opted in', model: 'sonnet' },
    { title: 'Advise', detail: 'Opus spec-grade implementation plan per workstream', model: 'opus' },
    { title: 'Execute', detail: 'Sonnet implements in isolated worktree, commits to ws/* branch', model: 'sonnet' },
    { title: 'Review', detail: 'Fable /code-review of each branch', model: 'fable' },
    { title: 'Integrate', detail: 'Single agent merge-tree conflict check across branches', model: 'sonnet' },
  ],
}

// KNOWN PLATFORM LIMIT (verified 2026-07-07, repro wf_aa733ab7-fb1): agent() model overrides
// 'opus'/'fable' can silently resolve to claude-sonnet-5 — no error, and the REQUESTED model is
// recorded nowhere. Resolved model IS recorded in each agent's transcript (agent-<id>.jsonl).
// The Preflight phase below exploits that: cheap probes + one auditor grep the probes' transcripts
// and the script aborts BEFORE the expensive phases unless args.on_model_downgrade === 'proceed'.

// ---- args validation (gap 8: fully parameterized) ----
// Defensive: some invocation paths deliver args as a JSON-encoded string — parse it.
let ARGS = args
if (typeof ARGS === 'string') {
  try { ARGS = JSON.parse(ARGS) } catch (e) { throw new Error(`worktree-trio: args arrived as an unparseable string (${e.message})`) }
}
if (!ARGS || typeof ARGS !== 'object' || !Array.isArray(ARGS.workstreams) || ARGS.workstreams.length === 0 || !ARGS.run_tag) {
  throw new Error('worktree-trio requires args: {run_tag: "YYYYMMDD[-n]", repo?: "/abs/path", integrate?: true, workstreams: [{key, title, brief, branch?}]} — run_tag must be supplied by the caller (Date.now is unavailable in workflow scripts)')
}
for (const w of ARGS.workstreams) {
  if (!w.key || !w.title || !w.brief) throw new Error(`workstream missing key/title/brief: ${JSON.stringify(w).slice(0, 120)}`)
}
const REPO = ARGS.repo || '/Users/theceo/DevSkyy'
const RUN = String(ARGS.run_tag)
const WORKSTREAMS = ARGS.workstreams.map(w => ({ ...w, branch: w.branch || `ws/${w.key}-${RUN}` }))

const GUARDRAILS = `
HARD CONSTRAINTS (non-negotiable):
- NEVER call paid APIs (OpenAI, FASHN, Gemini, Replicate, Meshy, Tripo, etc). Any test touching a paid/prod boundary MUST mock it.
- NEVER deploy: no real deploy-theme.sh run, no vercel/fly deploy, no SFTP, no WooCommerce/media/live-data writes.
- NEVER read or print secret VALUES. Reference env var NAMES only.
- Work ONLY inside your git worktree. COMMIT all work (nothing uncommitted) with "<type>: <description>" messages.
- Production-grade: zero TODO/FIXME/stub/placeholder in delivered code.
- Python: line length 100, run ruff/black/isort on touched files. WordPress PHP: escape output (esc_html/esc_attr/esc_url), sanitize input, php -l every touched file. Theme CSS/JS edits are INERT live until .min rebuild: run node scripts/build-css.js and node scripts/build-js.js from wordpress-theme/ and commit the .min output too.
- Report honestly: if something is already fixed or genuinely blocked, say so — do not invent work.
`

const EFFICIENT_PRODUCTION = `
EFFICIENT-PRODUCTION DISCIPLINE (binding on every tool call):
- Before any tool call ask: do I already have this? A file read once this session is in context — NEVER re-read it.
- Batch independent reads/greps in ONE parallel block, not sequential calls.
- Check ${REPO}/.wolf/anatomy.md descriptions BEFORE opening a full file; if the description answers the question, skip the read.
- One targeted search that answers in one call beats three vague ones. No exploratory tool spam, no confirmation fetches.
- Verify before claim: Read source → then state. Every factual claim traces to a tool call from THIS run, cited as file:line. Never state a path, symbol, or API shape you have not read. If you don't know, say "unknown" and find out — never invent.

CONTEXT7 MANDATE (all roles, non-negotiable): before writing, planning, or judging ANY code that touches an external library/framework/API — WordPress/WooCommerce/Elementor hooks, MCP SDK/FastMCP, Next.js/React, httpx/Pydantic/pytest plugins, fly/vercel CLIs, anything non-stdlib — load Context7 first via ToolSearch("select:mcp__context7__resolve-library-id,mcp__context7__query-docs"), resolve the library, query the docs with your full question, and verify signatures/behavior against them. Training data is stale; the lookup is cheaper than fixing wrong usage. Exempt: stable web standards (plain HTML/CSS/POSIX shell) and this repo's own code.

VERIFY YOUR WORK (all roles, non-negotiable): nothing is claimed — no plan step, no "done", no finding — without a check RUN IN THIS SESSION whose output could have failed. Run it, read the real output, then claim. Blocked check = report "unverified", never guess.
`

// gap 3: every executor gets the same worktree-environment bootstrap facts
const WORKTREE_BOOTSTRAP = `
WORKTREE ENVIRONMENT (fresh worktrees share tracked files but LACK untracked artifacts — .venv, node_modules, dist, build caches):
- Python tests: the root repo's .venv is an editable install pointing at ${REPO} (the MAIN checkout). Run tests as PYTHONPATH=$(pwd) ${REPO}/.venv/bin/python -m pytest <paths> so YOUR worktree's code takes import precedence. Confirm once with: PYTHONPATH=$(pwd) ${REPO}/.venv/bin/python -c "import skyyrose, sys; print(skyyrose.__file__)" — it must print a path inside your worktree; if it prints the main repo path, STOP and fix invocation before trusting any test result.
- Node builds: if a build script needs node_modules that are absent, run npm ci in the relevant package dir of YOUR worktree first. Never symlink or borrow the main repo's node_modules.
- Branch creation (collision-safe): git checkout -b <branch>. If that fails because the branch already exists from a prior run, use <branch>-b2 (then -b3) and report the ACTUAL branch name you used.
`

const PLAN_SCHEMA = {
  type: 'object',
  required: ['plan', 'deliverables', 'verify'],
  properties: {
    plan: { type: 'string', description: 'Step-by-step implementation plan grounded in actual files read, every step with an inline verify: command' },
    deliverables: { type: 'array', items: { type: 'string' } },
    files_to_touch: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    already_done: { type: 'array', items: { type: 'string' }, description: 'Parts of the brief already resolved on main, with file:line evidence' },
    verify: { type: 'string', description: 'Exact verification commands the executor must run' },
  },
}

const EXEC_SCHEMA = {
  type: 'object',
  required: ['branch', 'worktree_path', 'summary', 'test_output', 'files_changed'],
  properties: {
    branch: { type: 'string', description: 'ACTUAL branch used (may carry -b2 suffix on collision)' },
    worktree_path: { type: 'string', description: 'Absolute pwd of the worktree' },
    summary: { type: 'string' },
    test_output: { type: 'string', description: 'Actual verification command output (truncate to key lines)' },
    files_changed: { type: 'array', items: { type: 'string' } },
    commits: { type: 'array', items: { type: 'string' }, description: 'SHA + subject per commit' },
    deviations: { type: 'array', items: { type: 'string' }, description: 'Where and why you deviated from the advisor plan' },
    blocked: { type: 'string', description: 'Only if genuinely blocked: what and why' },
  },
}

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['verdict', 'findings', 'notes'],
  properties: {
    verdict: { type: 'string', enum: ['approve', 'needs-fix'] },
    findings: {
      type: 'array',
      description: 'Verified findings, most-severe first; empty when verdict=approve',
      items: {
        type: 'object',
        required: ['severity', 'file', 'summary', 'failure_scenario'],
        properties: {
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
          file: { type: 'string', description: 'Repo-relative path' },
          line: { type: 'number' },
          summary: { type: 'string', description: 'One-sentence defect statement' },
          failure_scenario: { type: 'string', description: 'Concrete inputs/state → wrong output/crash' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

const INTEGRATE_SCHEMA = {
  type: 'object',
  required: ['conflicts', 'merge_order', 'notes'],
  properties: {
    conflicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['branches', 'files'],
        properties: {
          branches: { type: 'array', items: { type: 'string' } },
          files: { type: 'array', items: { type: 'string' } },
          detail: { type: 'string' },
        },
      },
    },
    merge_order: { type: 'array', items: { type: 'string' }, description: 'Suggested branch merge order minimizing conflict resolution' },
    notes: { type: 'string' },
  },
}

function planPrompt(ws) {
  return `ROLE SYSTEM PROMPT — OPUS ADVISOR (read-only planner). You produce the spec; you do NOT edit anything.
${EFFICIENT_PRODUCTION}
BORIS DOCTRINE (planning):
- Pour ALL your energy into the plan so the Sonnet executor can 1-shot the implementation. Every ambiguity you leave becomes executor rework.
- Verification is the #1 lever: EVERY step of your plan carries an inline "verify:" command whose output can FAIL. A check that cannot say "no" is a guess, not verification.
- Write the plan as a detailed spec: exact file paths, exact function/hook names, exact insertion points, exact commands to run and expected output — the executor must never re-derive context or make a judgment call you could have made here.
- Hunt for the already-done: parts of the brief may be fixed on main. Prove it with file:line evidence and put it in already_done — planning redundant work is a planning failure.
- Think like a staff engineer reviewing your own plan before handing it off: what will break in a worktree (import precedence, missing node_modules/.venv)? What does the audit/test ACTUALLY check? Name each risk with its mitigation.

Workstream: "${ws.title}" in repo ${REPO}.
${GUARDRAILS}
BRIEF:
${ws.brief}

Investigate the actual current state of the repo (Read/Grep/Glob/Bash read-only), then emit the spec-grade plan.`
}

function execPrompt(ws, plan) {
  return `ROLE SYSTEM PROMPT — SONNET EXECUTOR. You are in a fresh git worktree of ${REPO} — run pwd once to capture your worktree path and work ONLY here. First action: create branch ${ws.branch} (see collision rule below).
${EFFICIENT_PRODUCTION}
${WORKTREE_BOOTSTRAP}
BORIS DOCTRINE (execution):
- The advisor plan is your spec. Execute it step by step; run each step's "verify:" command IMMEDIATELY after the step — never stack unverified steps. The feedback loop is what makes the work good, not the first draft.
- If the code contradicts the plan, STOP that step and re-derive from source — then proceed and record it in deviations. Pushing through a broken assumption is how bad branches happen.
- Prove it works: test_output must be REAL command output from this run, from a check that could have failed. "Looks correct" is not a state.
- Surgical scope: every changed line traces to the brief. No drive-by refactors, no adjacent "improvements", no formatting churn. Match surrounding code style exactly.
- Before reporting done, self-review: "would a staff engineer merge this?" If a step came out hacky, implement the elegant version now — knowing everything you know — rather than shipping the mediocre fix.
- PRODUCTION GATES (all must pass before you may report): zero TODO/FIXME/pass/NotImplementedError/stub/placeholder in delivered code; zero mock data outside tests; verification green with output pasted; git status --short EMPTY (everything committed — the reviewer reads your branch, uncommitted work is invisible); git diff main...HEAD --name-only shows ONLY paths this brief requires.
- Loop write→verify→fix max 5 times; the SAME error twice in a row means you are guessing — stop and report it honestly in blocked. If you block partway, STILL commit the verified steps you completed — partial verified work is reviewable, uncommitted work is lost.

Workstream: "${ws.title}".
${GUARDRAILS}
BRIEF:
${ws.brief}

OPUS ADVISOR PLAN (your spec — deviate only where source contradicts it, and record it in deviations):
${JSON.stringify(plan, null, 2)}

Execute to done. Report the ACTUAL branch, worktree absolute path, real test output, files changed, commit SHAs, deviations. If the advisor marked an item already_done, verify it yourself with one check and note it in summary rather than re-implementing.`
}

// gap 1: reviewer receives the advisor plan; gap 7: mutating-verify caution
function fableReviewPrompt(ws, exec, plan) {
  return `ROLE SYSTEM PROMPT — FABLE REVIEWER (/code-review, read-only). You are the staff-engineer gate: grill these changes and do NOT pass them until they survive your test. You do not edit anything.
${EFFICIENT_PRODUCTION}
BORIS DOCTRINE (review):
- Reviews exist because output volume outpaces scrutiny — you ARE the scrutiny. Hunt like a bug-hunting review agent: one pass each for logic errors, security, and regressions; do not skim.
- Demand proof, don't accept claims: re-run the executor's verify commands yourself and compare output; where behavior matters, diff it against main.
- Don't accept the first plausible reading of a hunk — trace each candidate failure scenario on CONCRETE inputs before reporting it, and DROP any finding you cannot confirm on this branch. A plausible-but-unverified finding is noise.
- Verdict standard: "approve" means you would merge this to main right now, personally. Anything less is "needs-fix".

Workstream: "${ws.title}" in repo ${REPO}.
The executor worked on branch ${exec.branch} in worktree ${exec.worktree_path}.
Executor summary: ${exec.summary}
Executor deviations from plan: ${JSON.stringify(exec.deviations || [])}
Executor test output: ${exec.test_output}
${exec.blocked ? `EXECUTOR BLOCKED: ${exec.blocked} — review the committed partial work; assess whether the block reason is genuine and whether committed steps are sound.` : ''}

THE ADVISOR SPEC the executor was given (check the work AGAINST it — unjustified deviations are findings; items in already_done were verified pre-existing on main, do NOT flag them as missing):
${JSON.stringify(plan, null, 2)}

Review procedure (do not trust the summary — verify everything yourself):
1. git -C ${exec.worktree_path} log --oneline -10 && git -C ${exec.worktree_path} status --short (uncommitted work = a finding)
2. git -C ${exec.worktree_path} diff main...HEAD — read the FULL diff, every hunk.
3. Check completeness against the original brief:
${ws.brief}
4. Hunt across dimensions: correctness (trace failure scenarios on concrete inputs), security (unescaped WP output, injection, secret values in code/docs, SSRF), fail-open error handling, weakened or model-downloading tests, stubs/TODOs/placeholders, scope creep beyond the brief, missing .min rebuild for theme CSS/JS edits, anything that would call a paid API or deploy.
5. VERIFY each candidate finding before reporting it: re-read the surrounding code, confirm the failure scenario is real on this branch — drop anything you cannot confirm. Re-run at least one of the executor's verification commands yourself and compare output. PREFER read-only checks (pytest, php -l, bash -n, grep of built artifacts); if a verify command would MUTATE files (e.g. a .min rebuild), either verify the artifact by inspection instead, or run it and then check git -C ${exec.worktree_path} status --short — any drift you caused is YOURS to report as "reviewer-induced drift", and you must NOT reset or commit anything.
Report findings most-severe first with concrete file:line and a concrete failure scenario each. Verdict "approve" ONLY if you would merge this branch as-is; any critical/high finding forces "needs-fix".`
}

function integratePrompt(branches) {
  return `ROLE SYSTEM PROMPT — INTEGRATION CHECKER (read-only). Repo: ${REPO}. You do NOT edit, merge, or commit anything.
${EFFICIENT_PRODUCTION}
These branches were built in parallel worktrees and will be merged to main by the human-supervised main thread:
${branches.map(b => `- ${b}`).join('\n')}

For every PAIR of branches, detect merge conflicts WITHOUT touching any working tree:
  git -C ${REPO} merge-tree $(git -C ${REPO} merge-base main <A>) <A> <B>   (or the modern: git -C ${REPO} merge-tree --write-tree <A> <B> if supported — check git version first)
Also check each branch against main the same way. Read the output — conflict markers or "CONFLICT" lines identify real overlaps; also compare git diff --name-only lists for shared files (shared file ≠ conflict, but flag it).
Report: concrete conflicts (branch pair + files), shared-file overlaps worth sequencing, and a suggested merge order that minimizes manual resolution. If zero conflicts, say so plainly — that is a valid, verified result.`
}

// ---- Phase 0: MODEL PREFLIGHT (gap 10: verify runtime config, not just deliverables) ----
const PREFLIGHT_SCHEMA = {
  type: 'object',
  required: ['probes', 'notes'],
  properties: {
    probes: {
      type: 'array',
      items: {
        type: 'object',
        required: ['alias', 'resolved_model'],
        properties: {
          alias: { type: 'string', description: 'Requested model alias extracted from the probe prompt (alias=<x>)' },
          resolved_model: { type: 'string', description: 'Model string recorded in that probe transcript, e.g. claude-sonnet-5' },
          file: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

const PROBE_MODELS = ['opus', 'fable', 'sonnet'] // the distinct models this harness requests
const NONCE = `worktree-trio-preflight-${RUN}`

phase('Preflight')
log(`preflight: probing model resolution for ${PROBE_MODELS.join('/')} (platform is known to silently downgrade — verified 2026-07-07)`)
await parallel(PROBE_MODELS.map(m => () =>
  agent(`Model probe ${NONCE} alias=${m}. Reply with exactly the single word: OK`, { label: `probe:${m}`, phase: 'Preflight', model: m, effort: 'low' })))

const auditPrompt = `ROLE — PREFLIGHT MODEL AUDITOR (read-only; Bash + Read only; do NOT edit anything).
A workflow run just executed ${PROBE_MODELS.length} tiny probe agents whose prompts contain the unique marker "${NONCE}". Each probe REQUESTED a different model alias; the platform may have silently resolved them to something else. Your job: report what each probe ACTUALLY ran on.
1. Locate the probe transcripts: grep -rl '${NONCE} alias=' /Users/theceo/.claude/projects/*/subagents/workflows/*/agent-*.jsonl 2>/dev/null (fallback: grep -rl --include='agent-*.jsonl' '${NONCE}' /Users/theceo/.claude/projects/). Expect ${PROBE_MODELS.length} files (your own transcript also contains the marker — exclude the file whose content shows THIS auditor prompt rather than a one-line probe).
2. For each probe file extract: the alias (the text after 'alias=' in the probe prompt, one of: ${PROBE_MODELS.join(', ')}) and the resolved model — the value of the first '"model":"<value>"' occurrence in that file.
3. Report every probe found with its file path. If you find fewer than ${PROBE_MODELS.length}, report exactly what you found and state the shortfall in notes. Never guess or fill in a model you did not read from a transcript.`
let audit = await agent(auditPrompt, { label: 'preflight:audit', phase: 'Preflight', model: 'sonnet', effort: 'low', schema: PREFLIGHT_SCHEMA })
if (audit === null) audit = await agent(auditPrompt, { label: 'preflight:audit-retry', phase: 'Preflight', model: 'sonnet', effort: 'low', schema: PREFLIGHT_SCHEMA })
if (!audit || !Array.isArray(audit.probes) || audit.probes.length === 0) {
  throw new Error('MODEL PREFLIGHT UNVERIFIABLE: auditor could not locate probe transcripts. Refusing to burn the full run on unconfirmed model config. Relaunch, or pass args.on_model_downgrade:"proceed" to skip enforcement knowingly.')
}
const downgraded = audit.probes.filter(p => p.alias && !String(p.resolved_model || '').toLowerCase().includes(String(p.alias).toLowerCase()))
if (downgraded.length) {
  const detail = downgraded.map(p => `${p.alias}→${p.resolved_model}`).join(', ')
  log(`MODEL DOWNGRADE DETECTED: ${detail}`)
  if (ARGS.on_model_downgrade !== 'proceed') {
    throw new Error(`MODEL DOWNGRADE DETECTED: ${detail}. The platform silently resolved these overrides (known limit, verified 2026-07-07). This abort cost ~4 tiny agents instead of a full run. DECISION IS THE CALLER'S: relaunch with args.on_model_downgrade:"proceed" to accept these roles running on the resolved model (role prompts still carry the doctrine), or abandon/reschedule.`)
  }
  log(`caller passed on_model_downgrade:"proceed" — continuing on resolved models with role prompts carrying the doctrine`)
} else {
  log(`preflight clean: ${audit.probes.map(p => `${p.alias}=${p.resolved_model}`).join(', ')}`)
}

phase('Advise')
log(`${WORKSTREAMS.length} workstreams [run ${RUN}]: ${WORKSTREAMS.map(w => w.key).join(', ')} — Opus plans, Sonnet executes in worktrees, Fable code-reviews. 3 agents per workstream, hard cap.`)

const results = await pipeline(
  WORKSTREAMS,
  ws => agent(planPrompt(ws), { label: `advise:${ws.key}`, phase: 'Advise', model: 'opus', effort: 'high', schema: PLAN_SCHEMA }),
  async (plan, ws) => {
    if (!plan) throw new Error('advisor failed')
    // gap 4: one retry on transient executor death (null = died; blocked = honest report, no retry)
    let exec = await agent(execPrompt(ws, plan), { label: `exec:${ws.key}`, phase: 'Execute', model: 'sonnet', isolation: 'worktree', schema: EXEC_SCHEMA })
    if (exec === null) {
      log(`${ws.key}: executor died (terminal API error) — one retry`)
      exec = await agent(execPrompt(ws, plan), { label: `exec-retry:${ws.key}`, phase: 'Execute', model: 'sonnet', isolation: 'worktree', schema: EXEC_SCHEMA })
    }
    return { plan, exec }
  },
  async (prev, ws) => {
    if (!prev || !prev.exec) return { ws: ws.key, status: 'executor-failed', plan: prev ? prev.plan : null }
    const { plan, exec } = prev
    // gap 5: blocked WITH commits still gets reviewed; blocked with nothing committed skips
    if (exec.blocked && !(exec.commits || []).length) return { ws: ws.key, status: 'blocked', blocked: exec.blocked, exec, plan }
    const review = await agent(fableReviewPrompt(ws, exec, plan), { label: `fable-review:${ws.key}`, phase: 'Review', model: 'fable', effort: 'high', schema: REVIEW_SCHEMA })
    if (!review) return { ws: ws.key, status: 'review-failed', exec, plan }
    log(`${ws.key}: Fable verdict = ${review.verdict}${review.findings.length ? ` (${review.findings.length} findings)` : ''}${exec.blocked ? ' [partial: executor blocked]' : ''}`)
    const status = exec.blocked ? 'blocked-partial-reviewed' : (review.verdict === 'approve' ? 'approved' : 'needs-fix')
    return { ws: ws.key, status, exec, review, plan }
  }
)

// gap 6: single cross-workstream integration check (outside the per-workstream cap)
const clean = (results || []).filter(Boolean)
const branches = clean.filter(r => r.exec && (r.exec.commits || []).length).map(r => r.exec.branch)
let integration = null
if (ARGS.integrate !== false && branches.length >= 2) {
  phase('Integrate')
  integration = await agent(integratePrompt(branches), { label: 'integrate:merge-tree', phase: 'Integrate', model: 'sonnet', schema: INTEGRATE_SCHEMA })
}

const summary = clean.map(r => ({
  workstream: r.ws,
  status: r.status,
  branch: r.exec ? r.exec.branch : null,
  worktree: r.exec ? r.exec.worktree_path : null,
  commits: r.exec ? r.exec.commits : null,
  deviations: r.exec ? r.exec.deviations || [] : [],
  findings: r.review ? r.review.findings : [],
  review_notes: r.review ? r.review.notes : null,
  blocked: r.blocked || (r.exec ? r.exec.blocked : null) || null,
}))
log(`done: ${summary.map(s => `${s.workstream}=${s.status}`).join(', ')}`)

// gap 9: explicit main-thread duties — the workflow's word is never final
return {
  run_tag: RUN,
  workstreams: summary,
  integration,
  main_thread_checklist: [
    'Independently re-verify EVERY branch before merging: re-run its tests/lints yourself and read the output — never merge on a subagent\'s word (feedback_independent_reverify).',
    'Check git diff main...<branch> --name-only scope per branch against its brief.',
    'Triage needs-fix findings: dispatch a FRESH fixer per branch (reviewer never fixes), then re-review.',
    'Merge in the integration-suggested order; resolve flagged shared-file overlaps manually.',
    'Anything paid / production / live-data in the deliverables (deploys, env vars, fly secrets) is STOP-AND-SHOW to the founder — the workflow only PREPARED those steps.',
    'After merge: update .wolf/memory.md + buglog + tasks/todo.md; clean up ws/* branches per deletion policy (census first).',
  ],
}
