# verify-theme.sh remediation — 2026-07-24

`npm run verify:theme` went from **5 FAIL / 2 WARN** to **2 FAIL / 2 WARN**.
Three of the original five FAILs were defects in the *harness*, not the theme.

## Fixed

| Aspect | Root cause | Fix |
|---|---|---|
| `min-sync` | mtime comparison (`[ src -nt min ]`). Wrong in **both** directions: false-FAILed `design-tokens.css` (byte-identical), and PASSed `style.min.css` which shipped **Version 1.12.7 against a 1.12.8 source**. | `--check` mode added to `scripts/build-css.js` + `build-js.js`; harness calls them. Compares content by re-deriving output with the real minifier config (no duplicated CleanCSS/terser options). Rebuilt `style.min.css`. |
| `no-placeholders` | One regex conflated dev markers with shipped copy; both hits were legitimate `esc_html__( 'Coming soon' )` strings. | Two tiers: dev markers (`TODO/FIXME/HACK/@stub`) fail anywhere; content placeholders fail only outside a translation call. `XXX` dropped — XXL/XXXL are real size labels here. |
| `phpcs` | 7 errors + 7 warnings. Harness also reported `FAIL … (0 ERROR)` because phpcs exits non-zero on warnings too. | `phpcbf` on the 7 affected files (file-scoped, to avoid churning the concurrent session's WIP). Harness now parses the totals line and grades errors (FAIL) vs warnings (WARN) separately. |
| `phpstan` — *could not run* | `excludePaths: node_modules/` did not exist → abort before analysis. Then a 128M php.ini limit + Xdebug crashed the workers. **PHPStan had never actually run**; the harness reported the crash as "phpstan errors". | `node_modules/ (?)`; harness runs with `XDEBUG_MODE=off --memory-limit=2G` and reports a crash distinctly from a findings list. |
| `phpstan` — 440 → 143 | `stubFiles` was used for WooCommerce stubs. `stubFiles` only *overrides* types of known symbols; it never makes them discoverable — hence 223 `unknown class WC_Product` errors. Plus `SKYYROSE_DIR`/`_URI` are `define()`d from function calls, which PHPStan cannot constant-fold. | Moved WC stubs to `scanFiles`; added `phpstan/constants.php` (scanned, never loaded by WP) + `dynamicConstantNames`. Removed 52 dead `return;` statements after `wp_send_json_*()`. |

### PHPStan false positive worth knowing

`add_action( 'hook', function () { wp_send_json_success(...); } );` makes PHPStan
infer the **registration call itself** as never-returning, so every file-scope
statement after it is reported unreachable. Minimal repro confirmed. It looked
like two AJAX hooks were never registered (`skyyrose_track_referral`,
`skyyrose_clear_wishlist`) — they are registered fine at runtime.

Fixed by naming both closures (`skyyrose_ajax_signin_already`,
`skyyrose_ajax_move_to_cart_guest`), which is better WP practice regardless:
a closure passed to `add_action` can never be `remove_action`'d.

## Still failing (pre-existing theme debt, not introduced here)

### 1. `phpstan` — 143 real findings
Never visible before today because the tool never ran. Hot spots:
`inc/immersive-ajax.php` (26), `woocommerce/checkout/form-checkout.php` (18),
`inc/wishlist-functions.php` (13), `template-preorder-gateway.php` (11).

Largest clusters:
- 16 × `esc_attr()` receiving `int`/`float` instead of `string`
- 16 × `Variable $checkout might not be defined` (WC template global)
- ~30 × always-true/always-false conditions (`is_array()` on an array, negated
  bool always false) — each is either a redundant guard or a real logic slip;
  they need reading, not a codemod.

**Do not baseline these.** A baseline would turn the gate green while the
findings persist, which is the failure mode this whole task existed to fix.

### 2. `file-size` — 5 files over the 800-line limit

| File | Lines | Functions | Plan |
|---|---|---|---|
| `template-preorder-gateway.php` | 885 | 0 | Pure markup — split into `template-parts/preorder/*.php`. Lowest risk; do first. |
| `inc/seo.php` | 1149 | 19 | Split by concern: meta tags / JSON-LD schema / OG+Twitter. Move each function with its own `add_action` to preserve registration order. |
| `inc/template-functions.php` | 970 | 21 | Grab-bag; split by consumer surface. |
| `inc/performance.php` | 939 | 18 | Split: asset hints / image sizes / font handling. |
| `inc/enqueue.php` | 1311 | 8 | **Defer.** ~164 lines/function — a function-length problem, so splitting the file only relocates it. It owns every handle, dependency and version string; a mistake breaks CSS/JS on production surfaces, which is exactly what the `responsive`/`cwv` SKIP aspects cannot verify. Needs browser verification in the loop. |

### 3. Two standing WARNs
- `escaping` — 95 possible unescaped `echo $var` (advisory heuristic; needs review, many are likely already-escaped helpers)
- `a11y-static` — 72 `<img>` without `alt`

## Packaging note

`phpstan.neon`, `phpstan-baseline.neon` and the new `phpstan/` dir were shipping
to production — `.phpcs.xml` was excluded but the PHPStan config never was.
Added to **both** exclude lists in `scripts/deploy-theme.sh` (`RSYNC_EXCLUDES`
and `tar_excludes`, which the file itself says must stay in sync). Not verified
by dry-run: the STOP-AND-SHOW stopgate gates any command naming that script, and
it was not bypassed. Edits are additive array entries, reviewed by reading.

`phpstan/constants.php` is now counted by `php-syntax` (165 → 166 files). It is
never loaded by WordPress; if it ever were, the bare `define( 'COOKIEPATH', … )`
would emit a redefine notice. A `defined()` guard would break PHPStan discovery,
so the docblock carries the warning instead.

## Verification performed

Both rewritten gates were probed to confirm they can still fail:

- `min-sync`: appended a rule to `design-tokens.css` without building → FAIL (exit 1); reverted → PASS. Same probe for JS via `mascot.js`.
- `no-placeholders`: added a bare `// TODO` to `inc/brand-colors.php` → FAIL; reverted → PASS.
- The 52 dead-`return;` removals were verified beyond "it still parses": `git diff -U0`
  confirms the only removed lines are 52 bare `return;` plus the two closure bodies
  intentionally rewritten, and `wordpress-stubs.php` declares `@phpstan-return never`
  on `wp_send_json_error()`/`_success()` — so the removed statements were genuinely
  unreachable, not merely believed to be.
- `min-sync`'s PASS detail no longer reports a scraped asset count. Parsing a number
  out of the child script's log meant a reworded log line would yield "0 assets" and
  still PASS — a fail-open path inside the gate built to remove one. Exit status only.
- `php -l` clean across all 166 delivered PHP files after the 52-line dead-code removal.
- `phpcs`: 0 errors, 0 warnings.

Nothing deployed, nothing committed.
