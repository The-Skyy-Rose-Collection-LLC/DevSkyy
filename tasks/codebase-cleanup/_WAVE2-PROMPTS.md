# Wave 2 Cleanup Prompts

_Authored 2026-05-06. Source: `tasks/codebase-digest/_CONSOLIDATED-CLEANUP-TARGETS.md` (32 findings, 8 digests). Wave 1 (P0) closed 4 of 6 items in commit `2b6e7ee5c`. Wave 2 takes the remaining 28._

---

## How to dispatch

Wave 2 runs as **4 parallel agents**, one per severity tier. Each agent takes its slice of the consolidated targets file, produces atomic PRs, and reports back. Run them concurrently — independent file scopes, no merge conflicts.

```
Agent A → P0 leftover (2 items)
Agent B → P1 stubs + bugs (12 items)
Agent C → P2 architectural (8 items)
Agent D → P3 stale code (6 items)
```

**Cost note:** Each agent will read ~10–15 source files and produce 2–8 commits. No paid API calls expected (all internal code work). Ballpark: ~200K tokens of tool I/O across all four agents.

---

## Agent A — P0 Leftover (Production Security)

```
You are dispatched to close the remaining P0 findings from
tasks/codebase-digest/_CONSOLIDATED-CLEANUP-TARGETS.md.

Wave 1 already closed:
  ✓ #1  GDPR Article 17 bypass (commit 2b6e7ee5c)
  ✓ #3  audit_log.py read→DATA_CREATED (commit 2b6e7ee5c)
  ✓ #5  CostTracker hard cap (commit 2b6e7ee5c)
  ✓ Frontend dual auth-token keys (commit 2b6e7ee5c)

Your scope (still open):
  □ #2  12 unauthenticated endpoints with cost or data exposure
  □ #4  No SSRF protection at services layer
  □ #6  Round Table auto-publishes to live WordPress as 'publish'

For #2:
  1. Read tasks/codebase-digest/api.md to find the 12 endpoint list.
  2. Verify each endpoint's current auth state via grep on `Depends(get_current_user)` or equivalent.
  3. For each unprotected paid/data-exposing endpoint, add the auth dependency
     from security/auth.py.
  4. The catalog answer endpoint's docstring already acknowledges the risk —
     priority. Then FASHN tryon. Then WebSockets.
  5. Add a regression test asserting 401 on unauthenticated POST.
  6. One commit per endpoint group; PR title pattern:
     `fix(security): require auth on <group> endpoints`

For #4:
  1. Read services-llm-ai3d.md "SSRF" section for the file paths.
  2. Build a shared `services/_lib/url_allowlist.py` with `is_safe_url(url)`
     that blocks 169.254.x.x, file://, gopher://, internal hostnames per
     the project policy already documented in CLAUDE.md "Security" learnings.
  3. Apply at every Replicate/HuggingFace response handler before downstream fetch.
  4. Add unit tests for the allowlist (must include 169.254.169.254 — AWS metadata).

For #6:
  1. Read frontend.md "Round Table auto-publish" section.
  2. Open lib/wordpress/sync-service.ts and trace the status default.
  3. STOP and ASK the user: "Round Table currently publishes as 'publish' on
     production. Was this intended, or should it default to 'draft'?"
     Do NOT change behavior without explicit user confirmation — this could
     reverse customer-visible content.
  4. After user direction, change default + add explicit publish gate if needed.

Constraints:
  - Each fix is its own atomic commit on a new branch fix/p0-wave2-<short-name>.
  - No combined PR — each opens its own PR for review.
  - Update _CONSOLIDATED-CLEANUP-TARGETS.md to mark closed items with ✓ + commit hash.
```

---

## Agent B — P1 Stubs + Real Bugs (12 items)

```
You are dispatched to close P1 findings from
tasks/codebase-digest/_CONSOLIDATED-CLEANUP-TARGETS.md.

P1 splits into two categories:

A. Production stubs returning success (#7–#12, 6 items)
   - TryOnAgent / VariantAgent / ColorCorrectionAgent (skyyrose-python)
   - _enhance_quality() in 3D Round Table (core-orchestration)
   - SelfLearningModule.flush_rag_queue() (agents)
   - MLCapabilitiesModule synthetic random training (agents)
   - _queue_for_processing in image_ingestion.py (services)
   - background_removal.py SOLID_COLOR / CUSTOM_IMAGE paths (services)

B. Real bugs (#13–#18, 6 items)
   - Dual localStorage auth keys [✓ ALREADY CLOSED in Wave 1 — verify and skip]
   - UserRole defined twice (core-orchestration)
   - AlertSeverity enum mismatch (services-llm-ai3d)
   - GeminiModel.GEMINI_PRO bug in image_description_pipeline.py
   - agents.core.base.SuperAgent re-exports deprecated base_legacy
   - Sync I/O inside async methods (3 places)

Workflow per finding:
  1. Read the originating digest section (cited as `[xyz.md]` next to each item).
  2. Confirm the issue still exists (don't trust stale digests — verify in code).
  3. For STUBS: either implement properly OR mark explicitly with
     `raise NotImplementedError("...")` and update the function signature
     so callers can't silently succeed. Whichever the surrounding code
     warrants — when in doubt, raise.
  4. For BUGS: write a regression test FIRST that fails on current code,
     then fix. Pure TDD red→green.
  5. Each fix gets one commit. Group by category in atomic PRs:
     - PR1: silent-stubs-stop-lying (6 commits)
     - PR2: enum-and-import-bugs (3 commits)
     - PR3: async-blocking-io-fix (1 commit covering all 3 places)

Constraints:
  - For stubs that "score success", check whether ANY caller depends on the
    fake success. If yes, stop and surface the dependency before changing.
  - Update CLAUDE.md "Learnings" with the stubs-that-score pattern entry
    so future code reviews catch this.
  - For #13 (auth keys), grep first — Wave 1 already fixed. If still open, finish.
```

---

## Agent C — P2 Architectural Debt (8 items)

```
You are dispatched to triage P2 architectural findings from
tasks/codebase-digest/_CONSOLIDATED-CLEANUP-TARGETS.md.

Scope:
  #19 Duplicate /preorder/ redirect on production
  #20 lib/api.ts (root) vs lib/api/ (directory) parallel implementations
  #21 Five caches across the codebase with no consolidation plan
  #22 15+ in-memory stores process-scoped
  #23 Four parallel agent hierarchies
  #24 Three.js 3D experience system is dormant theme-wide
  #25 Two parallel API versioning systems with mismatched auth
  #26 Hexagonal architecture violation in core/

This tier is RESEARCH-FIRST, not action-first. For each item:
  1. Read the originating digest section.
  2. Verify the finding is still accurate (codebase moves fast).
  3. Produce a one-page decision memo at
     tasks/codebase-cleanup/decisions/<NN>-<slug>.md
     covering:
       - Current state (specific file paths + line numbers)
       - Cost of leaving it (concrete impact)
       - Cost of fixing (LOC, blast radius, testability)
       - Recommended action (fix now / defer to milestone / accept and document)
       - Open questions for the user
  4. DO NOT EXECUTE the fix. These have user-decision dimensions.

Exception — items safe to fix without user input:
  - #19 (duplicate /preorder/ redirect) — this is a clear bug. Fix directly:
    grep for the duplicate, keep the canonical one in inc/redirects.php,
    delete from inc/accessibility-fix.php (which is also #32 P3 cruft).

After decision memos exist, surface a summary to the user with this format:
  | # | Item | Recommendation | User input needed? |

Constraints:
  - This agent produces DOCS + ONE FIX (#19), not architectural rewrites.
  - Architectural rewrites get separate planning sessions per memo.
```

---

## Agent D — P3 Stale Code / Cruft (6 items)

```
You are dispatched to close P3 stale-code findings from
tasks/codebase-digest/_CONSOLIDATED-CLEANUP-TARGETS.md.

Scope:
  #27 agents/devskyy-a2a/.venv/ committed virtualenv
  #28 Scene WebP background images missing from theme deploy
  #29 Version mismatch between code and CLAUDE.md
  #30 front-page.php has its own footer, must mirror footer.php
  #31 smoke-test.sh hardcodes skyyrose.com (typo: should be skyyrose.co)
  #32 inc/accessibility-fix.php legacy redirect block (covered by Agent C #19)

Per-item action:

#27 .venv removal:
  1. `git rm -rf --cached agents/devskyy-a2a/.venv/`
  2. Add `.venv/` to .gitignore at repo root if not already.
  3. STOP and ASK before pushing — repo size impact, history rewrite optional.

#28 Scene WebPs:
  1. Read wp-theme.md "Scene WebP" section to learn the missing files.
  2. Check assets/images/scenes/ — likely on disk but not in deploy script.
  3. Either generate (if missing) or add to scripts/deploy-theme.sh asset list.
  4. Verify by running scripts/deploy-theme.sh --dry-run and grepping output.

#29 Version mismatch:
  1. Read style.css for current SkyyRose version constant.
  2. Read every CLAUDE.md mentioning a version number.
  3. Update all stale references to match style.css.
  4. Add a CI check in .github/workflows/ that fails if they drift.

#30 front-page.php footer:
  1. Read both front-page.php and footer.php.
  2. Diff the wp_footer() preamble.
  3. Add any missing template parts to front-page.php.
  4. Add a test in tests/e2e-wp/ that asserts mobile-nav, cookie-consent,
     toast-container all render on the homepage.

#31 smoke-test.sh:
  1. sed -i '' 's/skyyrose\.com/skyyrose.co/g' smoke-test.sh
  2. Verify the script still passes against production.

#32:
  Skip — handled by Agent C #19.

Constraints:
  - Each fix = atomic commit, one PR for the bundle (P3 is cohesive cleanup).
  - PR title: chore(cleanup): close P3 stale-code findings (5 of 5)
  - Skip #27 if user declines virtualenv removal.
```

---

## Cross-cutting completion criteria

When all 4 agents finish:

- [ ] `_CONSOLIDATED-CLEANUP-TARGETS.md` has ✓ + commit hash next to each closed item
- [ ] Open items have a status note (deferred / blocked / user-input-needed)
- [ ] CLAUDE.md "Learnings" has new entries for any pattern discovered
  (stubs-that-score, version-drift, etc.)
- [ ] All PRs reference back to this prompt file in the description for context

## Dispatch checklist (before launching the 4 agents)

1. [ ] Confirm `fix/p0-critical-cleanup-2026-05-06` is merged to main
       (Wave 1 must land first to avoid conflicts on `_CONSOLIDATED-CLEANUP-TARGETS.md`)
2. [ ] Pull latest main locally
3. [ ] Verify agent quota is reset (was exhausted during Wave 1 digest pass)
4. [ ] Create branch prefix `fix/p0-wave2-*`, `fix/p1-wave2-*`, etc.
5. [ ] Launch all 4 agents in parallel via a single Agent multi-call
