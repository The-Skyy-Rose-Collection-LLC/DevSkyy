---
name: wp-deploy
description: Deploy the skyyrose-flagship WordPress theme to skyyrose.co through the gated pipeline (scripts/deploy-theme.sh). Use when a theme change is built, verified, and ready to ship to production, or when previewing a deploy with --dry-run. Do NOT use for editing theme code, running verify:theme during development, MU-plugin deploys (scripts/deploy-mu-plugin.sh), WooCommerce data writes, or the Vercel dashboard — those have their own paths.
disable-model-invocation: true
---

# WordPress Theme Deploy

Deploy `wordpress-theme/skyyrose-flagship/` to the live SkyyRose site. The theme deploy is an
**atomic hot-swap**: production ends up with exactly what the source tree contains — anything the
source lacks gets DELETED live (bug-252: v1.10.3 shipped without its tracked signature emblem →
live 404).

## When to use

- A theme change is complete: built, lint-clean, `verify:theme` green, and the founder wants it live.
- You need a deploy preview (`--dry-run`) to see the exact file manifest before asking for approval.
- Post-deploy verification of a deploy that just ran.

**When NOT to use:**

- Mid-development checks — run `npm run verify:theme` / `npm run lint` directly, no deploy involved.
- MU-plugins — `STOPSHOW_ACK=1 bash scripts/deploy-mu-plugin.sh` is a separate, separately-gated path.
- WooCommerce REST writes, WP Media uploads, cache purges — production-touching but not theme deploys.
- Any worktree with a sparse checkout — a sparse tree is NEVER a valid deploy source (see Inputs).

## Inputs

Every item must exist before proceeding. **Absent input = STOP — never proceed with a substitute.**

1. **`.env.wordpress` at the repo root** — SFTP credentials (key `~/.ssh/skyyrose-deploy`, host
   `sftp.wp.com`). Observed 2026-07-28: this file is ABSENT in the `glimmering-crafting-shannon`
   worktree `[repro]` — deploys run from the main checkout `/Users/theceo/DevSkyy`, not from
   worktrees. Absent → stop and switch to the main checkout; do not reconstruct credentials.
2. **A COMPLETE source tree.** `preflight_completeness()` (`scripts/deploy-theme.sh:313`) verifies
   the version triple agrees and every **git-tracked** file exists on disk `[repo]`. Known gap: the
   3 untracked `*-v2-avatar.webp` riders are invisible to it — a tree missing them passes silently.
3. **Fresh `.min` build** — production serves `.min`; a source-only edit ships nothing. `npm run build`
   from `wordpress-theme/` before any deploy that touched CSS/JS.
4. **Version triple bumped** when CSS/JS changed — `SKYYROSE_VERSION` in `functions.php`, `style.css`,
   `readme.txt`. It is the cache-bust param on ~52 enqueue calls; skipping it serves stale assets to
   returning visitors.
5. **Explicit founder approval.** This is STOP-AND-SHOW. The PreToolUse hook
   `.claude/hooks/paid-api-stopgate.sh` blocks the command — observed 2026-07-28, it blocks even
   `--dry-run` `[repro]` — until the manifest is shown, the founder answers `y`, and the call is
   re-issued with `STOPSHOW_ACK=1`.

## Procedure

1. Build minified assets: `cd wordpress-theme && npm run build`.
2. Run the local gate: `npm run verify:theme` — all CLI aspects must be green (see Verification).
3. Diff what will ship: `git diff --name-only HEAD~5 -- wordpress-theme/skyyrose-flagship/` and
   sanity-check the version triple agrees across `functions.php` / `style.css` / `readme.txt`.
4. Preview: `npm run deploy:dry` (a STOP-AND-SHOW surface itself — show manifest, get `y`,
   re-issue with `STOPSHOW_ACK=1`).
5. Print the STOP-AND-SHOW manifest (target, file count, version before→after) and wait for `y`.
6. Deploy: `STOPSHOW_ACK=1 npm run deploy` (wraps `bash ../scripts/deploy-theme.sh`).
7. Post-deploy verification (below), then Playwright eyes-on mobile + desktop.
8. **Fix everything in one batch, test all pages, deploy ONCE** — no drip-deploys.

## Verification

Every check can return "no". A gate that dies mid-run is not a gate that passed — if
`verify:theme` or the deploy script errors out, its silence is an artifact, re-run it (bug-230).
`verify:theme`'s BROWSER/VISION aspects (cwv, responsive, a11y-interactive, product-fidelity) are
**SKIPs from the CLI, not PASSes** — the deploying agent closes them with Playwright/vision after
the deploy.

```bash
cd wordpress-theme && npm run build && npm run verify:theme
```
**PASS:** exit 0, every CLI aspect green — including `min-sync` (every shipped `.min` byte-identical
to a fresh build). `[test]`

```bash
curl -s -o /dev/null -w 'code=%{http_code} size=%{size_download}B\n' "https://skyyrose.co/?cb=$(date +%s)"
```
**PASS:** `code=200` and size ≥ 50000B, no PHP-error markers in body. Observed 2026-07-28:
`code=200 ... size=136605B`. `[live]` Cache-bust is mandatory — Batcache serves stale. NEVER
WebFetch live HTML (strips `<script>`).

```bash
curl -s "https://skyyrose.co/wp-content/themes/skyyrose-flagship/style.css?cb=$(date +%s)" | grep -m1 'Version:'
```
**PASS:** matches the `SKYYROSE_VERSION` you just shipped (live theme was 1.12.8 before this
session's deploys). A mismatch = the swap did not land or the edge cache is stale. `[live]`

Prove the gate can fail (rule 3): once per new environment, delete one tracked theme file in a
scratch copy and run `preflight_completeness()` against it — it must go red — then restore.

## Worked example

Real invocation from this worktree, 2026-07-28:

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/glimmering-crafting-shannon/wordpress-theme
npm run verify:list
```

Observed output (excerpt) `[repro]`:

```
  php-syntax        CLI      php -l on every delivered .php — zero parse errors
  phpstan           CLI      static analysis at the configured level
  min-sync          CLI      every source css/js has a .min sibling, none stale
  cwv               BROWSER  Lighthouse LCP/CLS/TBT — runs only with --url + lighthouse CLI
  product-fidelity  VISION   garment ↔ SKU pixel match — caller/agent reads pixels vs catalog
```

Then attempting the deploy preview from this same worktree:

```bash
bash scripts/deploy-theme.sh --dry-run
```

Observed: **blocked before execution** by `.claude/hooks/paid-api-stopgate.sh` —
`"BLOCKED — STOP-AND-SHOW required per DevSkyy CLAUDE.md … Category: WordPress deploy to
skyyrose.co (production)"` `[repro]`. That is the contract working: no deploy command runs, even
dry, without a shown manifest, a founder `y`, and `STOPSHOW_ACK=1` on the re-issued call. (This
worktree also lacks `.env.wordpress`, so the deploy itself must run from `/Users/theceo/DevSkyy`.)

## Failure modes

- **Missing rider deleted live (bug-252).** The hot-swap deletes anything the source lacks.
  `preflight_completeness()` covers git-tracked files only; untracked riders (currently the 3
  `*-v2-avatar.webp` scene files, `.gitignore:290`) pass silently. `git add -f` a rider to put it
  under the gate.
- **Fail-open override (bug-230 pattern).** `PREFLIGHT_SKIP_COMPLETENESS=1` skips the completeness
  gate with only a loud log line. Never set it to make a red gate green — an emergency override on
  an unverified tree is how riders die.
- **Version-triple drift.** Stale `?ver=` keeps the WP.com edge serving old CSS/JS after a
  successful deploy — the site "deployed fine" but returning visitors see the old design. Bump all
  three files together.
- **Scope-jump reporting (bug-287).** A clean repo tree is `[repo]` evidence only — never report
  "deployed and live" without the post-deploy `curl` + Playwright probes (`[live]`).
- **Large scene assets timing out mid-transfer** — upload separately; a partial transfer plus
  hot-swap is worse than no deploy.
- **Rollback:** `git checkout <last-good-sha> -- wordpress-theme/skyyrose-flagship/`, rebuild, and
  redeploy through the same gated pipeline (the rollback deploy is STOP-AND-SHOW too).
