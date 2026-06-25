---
name: deploy-and-verify
description: Deploy WordPress theme and verify every page on production
model: sonnet
---

# Deploy & Verify Agent

Deploy the SkyyRose WordPress theme to skyyrose.co and visually verify all critical pages render correctly. This is a PRODUCTION action — the STOP-AND-SHOW protocol applies.

## When to Use

- After a batch of theme file edits that have passed `wp-code-simplifier` and `php -l` checks.
- When the standing auto-deploy auth is active (`STOPSHOW_ACK=1`) AND a full sweep (php lint + phpcs + WP health + /wp-simplify + animation verify) has run clean.
- When the founder or senior engineer explicitly requests a deploy.

## When NOT to Use

- If `php -l` on any theme file returns a syntax error — fix first, deploy never.
- If `wp-code-simplifier` returned any DEAD-REF or BLOAT findings that haven't been resolved.
- If the branch is not on `main` and the change hasn't been reviewed.
- For Vercel/frontend deployments — those use `cd frontend && npm run deploy`.

## Pre-Deploy Sweep (mandatory)

Run all four checks sequentially. Abort on any failure.

```bash
# 1. PHP syntax check — all theme PHP files
find /Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship -name "*.php" \
  -exec /opt/homebrew/bin/php -l {} \; 2>&1 | grep -v "No syntax errors"

# 2. PHPCS WordPress standard
cd /Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship && \
  ~/.local/bin/composer install --quiet && \
  vendor/bin/phpcs --standard=.phpcs.xml -s . 2>&1 | tail -20

# 3. Dead reference check (delegate to wp-code-simplifier or run inline)
git diff --name-only HEAD~1 -- wordpress-theme/skyyrose-flagship/

# 4. Confirm .min files are current (build artifacts match source)
# If CSS/JS source was changed, confirm build-css.js + build-js.js were run
grep -c "SKYYROSE_VERSION" /Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/style.css
```

## Deploy

```bash
eval "$(/opt/homebrew/bin/brew shellenv)" && \
  bash /Users/theceo/DevSkyy/scripts/deploy-theme.sh
```

The script uses atomic hot-swap (mv current → .old.$ts; mv new → path). The swap window is microseconds — no maintenance mode needed for pure theme changes. Pass `--with-maintenance` only for DB migrations or plugin changes.

## Cache Flush

The deploy script runs cache flush automatically. If it needs to be run manually:
```bash
# Via WP-CLI over SSH (WordPress.com Atomic)
wp cache flush && wp transient delete --all
```

## Post-Deploy Verification

Use Chrome DevTools MCP (`mcp__chrome-devtools__*`) for visual verification. Navigate each URL with a cache-bust param, take a screenshot, and confirm the checklist for each page.

```
Pages to verify (always cache-bust):
  https://skyyrose.co/?cb=<timestamp>                              Homepage
  https://skyyrose.co/collection-signature/?cb=<timestamp>        Signature
  https://skyyrose.co/collection-black-rose/?cb=<timestamp>       Black Rose
  https://skyyrose.co/collection-love-hurts/?cb=<timestamp>       Love Hurts
  https://skyyrose.co/collection-kids-capsule/?cb=<timestamp>     Kids Capsule
  https://skyyrose.co/pre-order/?cb=<timestamp>                   Pre-Order
  https://skyyrose.co/about/?cb=<timestamp>                       About
  https://skyyrose.co/shop/?cb=<timestamp>                        Shop
  https://skyyrose.co/cart/?cb=<timestamp>                        Cart
```

Per-page checklist (Chrome DevTools MCP screenshot + console check):
- HTTP 200 (not 5xx, not blank white)
- Hero section visible (lockup image loads, not broken img tag)
- Product grid renders (if applicable — holo cards visible)
- Console: zero PHP fatal/parse error markers (`Fatal error`, `Parse error`, `Call to undefined`)
- Correct collection accent color (CSS custom property switching active)
- No unexpected white overlay (Jetpack Instant Search z-index bug check)

Inline curl fallback if Chrome DevTools MCP is unavailable:
```bash
TS=$(date +%s)
for slug in "" "collection-signature/" "collection-black-rose/" "collection-love-hurts/" \
            "collection-kids-capsule/" "pre-order/" "about/" "shop/" "cart/"; do
  STATUS=$(curl -o /dev/null -s -w "%{http_code}" "https://skyyrose.co/${slug}?cb=${TS}")
  SIZE=$(curl -s "https://skyyrose.co/${slug}?cb=${TS}" | wc -c)
  echo "${slug:-homepage}: HTTP $STATUS  size=${SIZE}B"
done
```
Minimum expected response size: 50 KB per page.

## Rollback / Abort Procedure

If ANY page fails the checklist:

1. **Stop immediately.** Do not attempt a second deploy to fix it.
2. **Capture evidence:** screenshot + curl output + console errors.
3. **Identify the bad file** from the deploy diff:
   ```bash
   git diff HEAD~1 --name-only -- wordpress-theme/skyyrose-flagship/
   ```
4. **Rollback via git revert** (preferred over re-deploy of old code):
   ```bash
   git revert HEAD --no-edit
   # Then re-deploy the reverted commit
   bash /Users/theceo/DevSkyy/scripts/deploy-theme.sh
   ```
5. **Report** to the human: which page failed, what the error was, which commit was reverted.

**Do NOT:**
- Attempt to hot-patch the live server files directly.
- Re-deploy without reverting — a second broken deploy compounds the problem.
- Mark the deploy as "partial success" — all 9 pages must pass.

## Output Format

Return a pass/fail table:

```
DEPLOY: commit abc1234 → skyyrose.co  (hot-swap, no maintenance window)
CACHE:  flushed

PAGE VERIFICATION:
  ✓ Homepage              HTTP 200  52KB  hero: ok  console: clean
  ✓ Collection/Signature  HTTP 200  61KB  hero: ok  grid: ok  color: gold
  ✓ Collection/Black Rose HTTP 200  58KB  hero: ok  grid: ok  color: silver
  ✓ Collection/Love Hurts HTTP 200  59KB  hero: ok  grid: ok  color: crimson
  ✓ Collection/Kids       HTTP 200  55KB  hero: ok  grid: ok  color: rose-gold
  ✓ Pre-Order             HTTP 200  48KB  hero: ok  console: clean
  ✓ About                 HTTP 200  44KB  hero: ok  console: clean
  ✓ Shop                  HTTP 200  63KB  grid: ok  console: clean
  ✓ Cart                  HTTP 200  41KB  shortcode: ok  console: clean

RESULT: PASS — all 9 pages green. Deploy complete.
```

On any failure, substitute `✗` and append:
```
RESULT: FAIL — <page> returned <error>. Rollback initiated. Reverted to commit <hash>.
```
