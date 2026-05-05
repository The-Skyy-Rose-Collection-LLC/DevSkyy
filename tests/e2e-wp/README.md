# skyyrose-wp-e2e

Playwright tests for the SkyyRose WordPress theme at https://skyyrose.co.

Distinct from `frontend/tests/e2e/` which targets the Next.js dashboard at
devskyy.app. This suite is for the customer storefront only.

## Setup

```bash
cd tests/e2e-wp
npm install
npx playwright install chromium
```

## Run

```bash
# All specs (production target)
npm test

# Single bug
npm run test:bug-001
npm run test:bug-006

# Headed (watch the browser)
npm run test:headed

# UI mode (interactive runner)
npm run test:ui

# Override target — for staging or local wp-now
BASE_URL=http://localhost:8881 npm test
```

## What's covered

| Spec | Bug | Status |
|------|-----|--------|
| `bug_001-clock-pause-resume.spec.ts` | bug_001 | **`fixme` — code path inactive on production** (no `#${collection}-experience` element renders). Includes a passing smoke test for "page loads init-3d.js without console errors." |
| `bug_006-aria-busy-timing.spec.ts` | bug_006 | **`fixme` — code path inactive on production** (`.holo__buy` is a navigation link, no `data-product-id`, AJAX click handler never binds). Includes a passing smoke test for "collection page renders holo cards." |

### Why `test.fixme()` instead of just deleting

The bug fixes on PR #486 are real defects in the JS source, but the
activating PHP/HTML state isn't deployed. When PHP changes ship that
emit `data-product-id` on holo cards or render
`<div id="blackrose-experience">` containers in immersive templates,
remove the `.fixme()` calls and the tests become live regression
guards. The scaffolding pays back when those changes land — meanwhile
the smoke tests still run and catch baseline-render regressions.

To re-enable:

```bash
# When data-product-id starts shipping:
curl https://skyyrose.co/collection-black-rose/ | grep -c 'holo__buy[^"]*" data-product-id'
# Should be > 0; then remove .fixme() in bug_006-aria-busy-timing.spec.ts

# When immersive containers start rendering:
curl https://skyyrose.co/experience-black-rose/ | grep -c 'id="blackrose-experience"'
# Should be > 0; then remove .fixme() in bug_001-clock-pause-resume.spec.ts
# (note: also requires init-3d.js:155 to attach _skyyRoseExperience —
# currently a latent bug in the ID-init path)
```

## What's NOT covered (yet)

- **Real screen reader announcements.** The aria-busy contract test is necessary
  but not sufficient. True VoiceOver/NVDA verification requires
  `@guidepup/playwright` integration or manual smoke. Recommended manual smoke:
  enable VoiceOver, click an Add to Cart button, confirm "Added" is announced.
- **Visual regression.** The clock pause/resume snap is invisible to attribute
  checks but visible on screen. Visual diff tooling (Percy / Chromatic) would
  cover that surface.
- **Other product-card-holo paths** beyond click — wishlist, size selection.
- **Cart and checkout flows.** Out of scope for these two bugs.

## Production targeting caveats

These tests run against `https://skyyrose.co` by default. That means:

- **No real WC writes:** all add-to-cart calls are intercepted via Playwright's
  `page.route()` and fulfilled with synthetic JSON responses. The real
  WooCommerce backend never sees the request.
- **Site outages = test failures.** If skyyrose.co is down, these tests fail
  for environmental reasons, not regressions. CI should retry once before
  reporting failure.
- **Cache-bust markers** (`?_test=$ts`) may be needed if Jetpack Boost or
  Cloudflare caches start interfering. Currently relying on Playwright's
  default cache headers.

For offline / deterministic runs, set up a local WordPress via `wp-now`:

```bash
npx @wordpress/wp-now start --path=../../wordpress-theme/skyyrose-flagship
# Then in another terminal:
BASE_URL=http://localhost:8881 npm test
```

## CI integration (deferred)

A `.github/workflows/wp-e2e.yml` would run these on every PR touching
`wordpress-theme/skyyrose-flagship/**`. Deferred until the org-level
GitHub Actions restriction is lifted (see incident note 2026-05-05 —
runner_id=0 on all workflows in this repo).

## Related infrastructure

- `scripts/verify-deploy.sh` — bash-based post-deploy HTTP+content verification
  (runs after every `npm run deploy`). Cheaper than Playwright; covers
  homepage, collections, immersive worlds, pre-order, and product pages.
  Use that for "is the site up" checks; use Playwright for "do specific
  user flows still work."
- `scripts/deploy-theme.sh` — the deploy script that runs verify-deploy.sh
  via the `RUN_FULL_VERIFY=true` env var set by `npm run deploy` in
  `wordpress-theme/package.json`.
