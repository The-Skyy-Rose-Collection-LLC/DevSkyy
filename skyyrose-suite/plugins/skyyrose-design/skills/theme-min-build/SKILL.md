---
name: theme-min-build
description: Use after editing any SkyyRose theme CSS/JS — production serves the .min build, so every source edit must rebuild .min and re-verify BOTH source and .min. Prevents shipping stale minified assets.
origin: SkyyRose
---

# Theme .min Build Discipline

Production does not serve the file you just edited. `$use_min = !SCRIPT_DEBUG` — every
`assets/css/*.css` and `assets/js/*.js` request on skyyrose.co resolves to the `.min`
sibling, not the source. Edit the source and stop there, and the live site keeps serving
the pre-edit bytes: a change that is real in git and invisible in the browser.

> **Boot first:** read `wordpress-theme/skyyrose-flagship/CLAUDE.md` (the `.min` build
> rule, structure, escaping/sanitize/nonce conventions, PHPCS) → `CLAUDE.md` (Deploy table,
> STOP-AND-SHOW protocol, Verification Protocol row for "WP deploy result"). Do not build
> from memory of a prior session — the version pin and build command can drift.

## When to Use

- After ANY edit to a theme `.css` or `.js` file under `wordpress-theme/`.
- Before any theme deploy (`bash scripts/deploy-theme.sh` or `npm run deploy`), as the
  last gate — a deploy ships whatever `.min` currently contains, edited or not.
- Reviewing a PR that touches theme assets and doesn't show a `.min` diff.

## Method

1. **Edit the source** — `assets/css/*.css` / `assets/js/*.js`, never the `.min` file
   directly (hand-edited `.min` drifts from source on the next real build and gets
   silently overwritten).
2. **Rebuild** — `npm run build` from `wordpress-theme/`. This is the only path that
   regenerates `.min` from source; there is no watch-mode substitute for a deploy.
3. **Confirm the change landed in both files** — grep the exact edit in the source AND
   in the `.min` output. A successful build exit code is not proof the bytes changed.
4. **Deploy via STOP-AND-SHOW** — `bash scripts/deploy-theme.sh` (or `npm run deploy`)
   touches production; show the exact files being pushed and wait for confirmation per
   the CLAUDE.md protocol. `npm run deploy:dry` previews without touching the server.
5. **Post-verify** — cache-busted `curl` for HTTP 200 / size / no PHP-error markers, then
   Playwright eyes-on, mobile and desktop.

## Loop until source and .min agree, and live matches

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same diff repeats
twice (that is a broken build step, not a flaky one):

```
1. Edit source.  2. npm run build (from wordpress-theme/).
3. Diff: grep the change in source vs .min — both present?
4. Deploy (STOP-AND-SHOW) → cache-busted curl + Playwright screenshot.
5. Mismatch at step 3 or 4 → fix the build/deploy step, repeat from 2.
```

## Verify from an authoritative source

The build is only real if the bytes are **observed in both files**, never assumed:

- **Grep the source** for the literal edit — confirm it's actually saved where you think.
- **Grep the `.min` file** for the same (minified) substring — if the build ran, it's
  there; if it's absent, `npm run build` did not pick up the change or failed silently.
- **Post-deploy: cache-busted `curl`** — `curl -s "URL?cb=$(date +%s)" | grep` for HTTP
  200, body ≥50KB, no PHP-error markers. WP.com Batcache serves stale bytes on a bare
  fetch; the cache-bust query param is not optional.
- **NEVER WebFetch a live page** — it strips `<script>` tags, so it cannot see whether
  the `.min` asset actually changed, and it silently misses JSON-LD/OG regressions too.
- **Playwright screenshot, mobile AND desktop** — a curl 200 proves the file loaded, not
  that it rendered correctly; eyes-on is the only proof of visual correctness.

## Adversarial pass

- Assume the `.min` is stale until grep proves otherwise, and assume the CDN/Batcache is
  serving a cached response until a cache-busted curl proves otherwise — see
  [[adversarial-verification]]. "The build command ran" and "the live page reflects the
  edit" are two separate claims; neither substitutes for the other.

## Guardrails · Handoff · Log

- Deploy to skyyrose.co is **STOP-AND-SHOW** — never autonomous. Cross-ref
  [[cost-governance-gate]] for the broader act-vs-ask boundary.
- If the edit touches product imagery markup or references, cross-ref
  [[product-image-fidelity-gate]] before deploy.
- Structural/backend theme work outside CSS/JS → hand to `skyyrose-core` (see
  `CROSS-PLUGIN.md`), then **re-verify here** once assets are back in scope.
- Log a build/deploy discrepancy (source and `.min` disagree, or live doesn't match
  either) to `.wolf/buglog.json`, and record the lesson via [[continuous-learning]].
