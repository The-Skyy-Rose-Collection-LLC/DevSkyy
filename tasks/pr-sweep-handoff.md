# PR sweep handoff — execute post-restart with FABLE subagents

**Created 2026-07-13. Reason:** `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` was pinning all subagents to sonnet
(now removed from `.claude/settings.json`, but the var was already exported into the prior session's
process). A **session restart** clears it → fable subagents run for real. Execute this sweep then.

## Gate
- Fix/rebase/push to PR branches + mark drafts ready = **autonomous** (reversible, no paid/deploy/live-write).
- **MERGING each PR = STOP-AND-SHOW `y`** — merge to `main` re-triggers Vercel Production deploy.
- Run each rebase in the **main checkout** (has assets) — sparse worktrees lack `assets/` (S2439 gotcha), which
  breaks #739's pytest.

## Triage verdicts (already done — do NOT re-triage)

### #720 — homepage hero CTA white-on-white → **CLOSE (superseded)**
- Branch superseded: `main` already carries the identical `.hero-cta.hero-cta-primary` specificity fix
  verbatim at `wordpress-theme/skyyrose-flagship/assets/css/homepage-v2.css:365-370`. Rebase = zero net diff.
- Action: `gh pr close 720 --comment "Superseded — main already carries the identical .hero-cta.hero-cta-primary specificity fix (homepage-v2.css:365-370, verbatim). Rebase = zero net diff."`

### #735 — collection hero centering → **REBASE**
- Branch: `fix/collection-hero-centering`. CI all green. Only blocker: version-string conflict.
- Conflicts (3, version bump only — CSS fix content merges clean): `functions.php` `SKYYROSE_VERSION`,
  `style.css` `Version:`, `readme.txt` `Stable tag:` + changelog. PR at `1.10.4`, main at `1.11.0` (mascot #737).
- Resolve: bump all three to **`1.11.1`**; keep main's 1.11.0 changelog entry above, add 1.11.1 entry for this fix.
- No `.min` rebuild needed (conflict is not CSS). Optional: fold cubic's 2 token nits (`--skyyrose-font-mono`,
  `--skyyrose-text-muted`, token instead of hardcoded rgba text-shadow).
- Push `--force-with-lease`, confirm `mergeStateStatus: CLEAN`.

### #727 — OpenAI product feed audit+generator → **REBASE + READY**
- Branch: `worktree-agent-a68fb39f796b42a61`. Draft. 3 append-only conflicts (trivial — keep both sides):
  `.gitignore`, `.wolf/anatomy.md`, `.wolf/cerebrum.md`.
- After rebase: run its 23 pure-function tests, then `gh pr ready 727`.
- Surface to founder (NOT merge blockers): report flags 2 open decisions — pre-order `availability_date` mapping,
  image-format content-negotiation. Feed must never run `--write` against prod without founder sign-off.

### #739 — brand-assets test pinning → **REBASE + VERIFY + READY**
- Branch: `worktree-brand-assets-pipeline-pinning`. Draft. Conflict with main + **pytest never ran on branch**.
- After rebase: **actually run** `pytest tests/api/test_brand_assets.py -v` in main checkout (needs assets) and
  confirm green BEFORE `gh pr ready 739`. The PR's whole claim is "tests pin to real pipeline outputs" — verify it.

## After all 4
- Report a green table. **Stop.** Do not merge any PR without explicit `y` per PR (Vercel Prod deploy gate).
