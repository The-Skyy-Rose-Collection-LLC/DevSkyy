# v1.11.0 pre-deploy review — fast-follow items

Source: `/code-review` + `/verification-loop` on release candidate `360fdf506` (theme v1.11.0), 2026-07-13.
Reviews: security = **CLEAR-TO-DEPLOY** (0 findings) · quality = **SHIP** (0 HIGH/CRITICAL).
None of the below block the v1.11.0 deploy — all are latent / cosmetic and do not fire under current verified data. Log and fix in a follow-up commit.

## [MEDIUM] Hero-logo dimensions match SOT asset, not the static fallback
- **Files:** `inc/collection-content.php:119` (love-hurts `hero_logo_h=307`), `:208` (signature `hero_logo_h=189`)
- **Issue:** New CLS-fix dimensions match the SOT-resolved lockup ratio (love-hurts-lockup.webp 1600×1228; signature-lockup.webp 1600×540 — verified). But `page.php:55-58` resolves via `skyyrose_sot_lockup($slug)` first, falling back to `$c['hero_logo']` (love-hurts-logo-hero.webp 800×897 ≈ 0.89:1; signature-logo-hero.webp 1200×610 ≈ 1.97:1) when SOT returns `''`. On that documented fallback path the width/height attrs describe the SOT ratio, not the fallback asset's — so a missing/corrupt/nulled sot.json lockup slot reintroduces the exact logo stretch/CLS this commit fixed, silently, untested.
- **Why not blocking:** both collection `sot.json` are `status: verified` and guarded by the `collection_sot_current` drift check — the fallback can't trigger today.
- **Fix (pick one):** (a) box the SOT path via CSS `aspect-ratio` instead of HTML width/height attrs; (b) select `hero_logo_w/_h` conditionally on which source resolved in `page.php`; (c) simplest — re-encode the two `branding/*-logo-hero.webp` fallbacks to the SOT lockup ratio so both paths agree.

## [LOW] No isset guard on feature image dimensions
- **File:** `template-parts/collection/feature-scroll.php:69-70,85-86`
- **Issue:** Reads `$feature['image_w']`/`['image_h']` unconditionally after the `file_exists()` gate. All 12 current entries are consistent, but a future content edit adding `image` without paired dims throws "Undefined array key" notices on every render.
- **Fix:** `echo esc_attr( $feature['image_w'] ?? '' )` (and `image_h`), or add `isset($feature['image_w'],$feature['image_h'])` to the existing filter loop.

## [LOW] Stale docblock tag
- **File:** `template-parts/collection/founder-pullquote.php:19`
- **Issue:** File now branches on `$args` and serves two slugs; docblock still reads `@since 1.5.4` with no note for the 1.11.0 `$args` contract.
- **Fix:** `@since 1.5.4, per-collection args added 1.11.0`.

## Verification loop snapshot (RC 360fdf506)
- PHP lint: clean · SOT catalog consistency: 25/25 · secrets: 0 · debug calls: 3 `error_log` (all legitimate error handlers, no data leak) · `.min`: fresh (0-diff idempotent rebuild) · fidelity eyes-on: 7/7 · hub/drift/compositor-gate tests: pass.
