# TODOS

Deferred work items with full context. Each entry should be actionable by someone picking it up in 3 months.

---

## 1. Fix all hooks.json paths to use dynamic resolution

**What:** Replace hardcoded `/Users/coreyfoster/DevSkyy/` paths in `.claude/hooks/hooks.json` with portable `git rev-parse --show-toplevel` wrappers.

**Why:** hooks.json is a committed file shared between two machines (`/Users/coreyfoster/` and `/Users/theceo/`). The 4 existing external script references use `/Users/coreyfoster/` which only works on one machine. The new CLAUDE.md tracker hooks already use `git rev-parse` (added March 2026), creating an inconsistency — some hooks are portable, some aren't.

**Context:** The affected entries reference:
- `/Users/coreyfoster/DevSkyy/.claude/hooks/strategic-compact/suggest-compact.sh` (PreToolUse)
- `/Users/coreyfoster/DevSkyy/.claude/hooks/memory-persistence/pre-compact.sh` (PreCompact)
- `/Users/coreyfoster/DevSkyy/.claude/hooks/memory-persistence/session-start.sh` (SessionStart)

The fix is mechanical: wrap each in `bash "$(git rev-parse --show-toplevel)/.claude/hooks/..."`. The new CLAUDE.md tracker hooks demonstrate the pattern. Both machines have `git` available.

**Depends on / blocked by:** Nothing. Can be done independently.

---

## 2. Add Serena MCP change tracking for WordPress files

**What:** Implement a mechanism to detect structural changes made to WordPress theme files via Serena MCP tools, since Serena calls bypass the Claude Code hook system entirely.

**Why:** The CLAUDE.md staleness tracker (added March 2026) only fires on Write/Edit/Bash tool calls. Serena MCP tools (`replace_content`, `create_text_file`, `replace_symbol_body`, etc.) modify WordPress files directly without triggering PostToolUse hooks. This means structural changes to `wordpress-theme/skyyrose-flagship/` go untracked — a blind spot given that the WordPress theme has 14+ page templates, 31 CSS files, and 24 JS files.

**Context:** Possible approaches:
1. **Serena memory hook** — Use Serena's `write_memory` to log structural changes, then read them in session-summary.sh.
2. **Git diff at session end** — Instead of tracking changes live, `session-summary.sh` could run `git diff --name-status` at session end to catch ALL changes (including Serena). This is simpler but loses the mid-session alerting.
3. **Post-Serena poll** — A hook that runs after any Serena tool call and checks `git status` for new/deleted files. Requires Serena to be registered as a tool in the hook matcher.

The git-diff-at-session-end approach (option 2) is likely the best balance of simplicity and coverage. It could be added to `session-summary.sh` as a fallback detection path.

**Depends on / blocked by:** CLAUDE.md staleness tracker must be stable first (the March 2026 implementation).

## 3. Fix ruff/black formatter config disagreement

**What:** Decide on ONE canonical formatter (either ruff-format OR black, not both) and configure the other to not fight it.

**Why:** `ruff format` and `black` disagree on assert-wrap formatting:
- ruff prefers `assert expr, (msg)`
- black prefers `assert (expr), msg`

Pre-commit runs `black --check` as the gate, so ruff-formatted code is rejected. Between sessions, something (IDE format-on-save, a watcher, or a background agent) re-applies ruff-style, causing persistent drift across 7 files: `tests/test_character_system.py`, `tests/test_prompt_intelligence.py`, `tests/test_saas_infrastructure.py`, `tests/integration/test_hybrid_integration.py`, `skyyrose/elite_studio/tests/test_graph_builder_tryon.py`, `scripts/nano_banana/engine_fal.py`, `scripts/verify_pipeline.py`.

**Context:** The Makefile's `make format` does the right thing (`isort → ruff check --fix → black`) because black runs last. The problem is anyone running `ruff format` standalone or having it wired into their editor. Two options:
1. Add `[tool.ruff.format]` section to `pyproject.toml` with settings that match black's output (requires `ruff format` to produce byte-identical output to black, not always possible).
2. Drop black entirely and adopt `ruff format` as the sole formatter — update lint-staged config, Makefile, and CI.

Option 2 is cleaner long-term. Option 1 is faster but fragile.

**Depends on / blocked by:** Agreement on which formatter to keep.

---

## 4. Regenerate WordPress CSS/JS minified files in deploy pipeline

**What:** Move `.min.css` and `.min.js` generation out of the developer workflow and into `scripts/deploy-theme.sh` so min files are always fresh at deploy time.

**Why:** Currently min files are generated ad-hoc by `clean-css-cli`. The nested `wordpress-theme/skyyrose-flagship/.gitignore` ignores `*.min.css`/`*.min.js` by design, so they're never committed. Production serves min files (via enqueue.php `$use_min && file_exists(...)` guard). The deploy pipeline must build them before upload or prod silently falls back to unminified CSS (30-40% slower).

**Context:** Assets to minify:
- `wordpress-theme/skyyrose-flagship/assets/css/*.css` → `*.min.css`
- `wordpress-theme/skyyrose-flagship/assets/js/*.js` → `*.min.js` (terser)

Add to `scripts/deploy-theme.sh` before the rsync step. Promote `clean-css-cli` and `terser` to explicit devDependencies in `wordpress-theme/package.json`. Add `npm run build` script that runs both.

**Depends on / blocked by:** None.

---

## 5. Verify 8 remaining bug fixes from PR #429

**What:** Confirm bugs 5, 6, 7, 8, 9, 10, 12, 13 from the PR #429 review (memory.md `project_pr_review_findings.md`) are still correctly fixed in current code — they were asserted fixed on 2026-04-05 but not re-verified this session.

**Why:** Bugs 1-4 were resolved by deleting `agent_sdk/` wholesale (no code = no bug). Bug 11 was verified present (`wf_*` workflow_id prefixes in `prompts/chain_orchestrator.py`). The rest are in `experience-base.js`, `init-3d.js`, and `enqueue.php` — grep those for the specific patterns (RAF loop removal, constructor throwing, `config.debug` gating, `(containerId, options)` signatures, `wp_localize_script('skyyrose3D', ...)`).

**Context:** Low risk (no high-severity items left) but should be closed before tagging.

**Depends on / blocked by:** Nothing.

---

## 6. Branch & release strategy for v3.3.0

**What:** Define and execute the merge from `wp-theme-work` → `main` with proper version-bumping across three independent artifacts.

**Why:** Current state after the Apr 16 cleanup:
- `wp-theme-work` has 6 commits ahead of origin (the cleanup pass + Phase 1 compositor telemetry).
- Three independent versions: root `3.2.0` (Python+npm), frontend `1.0.0`, WP theme `7.0.1` (now reconciled).
- Only root has git tags. No per-artifact release notes.
- `project_pr_review_findings.md` bugs: 5 resolved, 8 asserted (item #5 above).

**Context:** Proposed flow:
1. Close item #5 (bug re-verification).
2. Close item #4 (min file build step).
3. Push `wp-theme-work` to origin.
4. Open PR `wp-theme-work` → `main`.
5. Let CI (`.github/workflows/ci.yml`) run — must be green.
6. Bump root → `3.3.0` (minor — Experience Engine Phase 4/5, compositor telemetry, test-suite unblock).
7. WP theme already at `7.0.1` (post-drift-fix). Only bump if new features land.
8. Frontend stays `1.0.0` (no changes this cycle).
9. Update `CHANGELOG.md` with real entries per artifact.
10. Merge PR, tag from `main` (not from branch), `gh release create`.
11. Deploy: `scripts/deploy-theme.sh` for WP, Vercel for frontend, Docker/HF for API.

**Depends on / blocked by:** Items #4, #5.

---

## 7. Compositor telemetry baseline analysis (2-week window)

**What:** After 2 weeks of production compositor runs, analyze `skyyrose/elite_studio/logs/compositor-telemetry-*.jsonl` to establish unit-economics baseline: p50/p95/p99 duration per stage, error-rate per stage, cost per composite, retry patterns.

**Why:** The Phase 1 retrofit (`feat(elite-studio): Phase 1 compositor retrofit`) shipped instrument-first over a speculative 40%-token-reduction refactor. Waves 2-4 (schema pinning, `forward_qa_verdict`, idempotent content-hash cache, per-stage circuit breaker) are gated on telemetry evidence — no data, no refactor authorization.

**Context:** Decision logged in `.wolf/cerebrum.md` (2026-04-16): "instrument-first over optimization theatre." Analysis target: week-of 2026-04-30 (two weeks post-deploy). Deliverable: `docs/compositor-baseline-YYYY-MM.md` with findings + Wave 2 go/no-go recommendation.

**Depends on / blocked by:** Telemetry in production for 2 weeks.

---

## 8. Consolidate claude-mem context file policy

**What:** Either fix the claude-mem tool to stop creating empty `<claude-mem-context></claude-mem-context>` placeholder CLAUDE.md files in arbitrary subdirectories, OR add a gitignore rule that distinguishes placeholder vs. content CLAUDE.md files.

**Why:** Every session, claude-mem creates empty 43-byte placeholders in new directories (observed: `.github/`, `frontend/tests/`, `prompts/`, `core/llm/providers/`, `wordpress-theme/`, `tasks/`, `.husky/`). They add noise to `git status`, look suspicious in PRs, and train developers to ignore "new file" warnings — which is how the stray `apple_earnings_analysis_corrected.ipynb` slipped in unnoticed.

**Context:** Can't use a content-based gitignore rule. Options:
1. File a bug/PR upstream (check ~/.claude-mem settings for a placeholder-disable flag).
2. Add a pre-commit hook that rejects CLAUDE.md files containing only `<claude-mem-context></claude-mem-context>`.
3. Gitignore a specific list of directories where placeholders appear, allow root `/CLAUDE.md` + `.wolf/**/CLAUDE.md` as exceptions.

**Depends on / blocked by:** Check claude-mem upstream first.
