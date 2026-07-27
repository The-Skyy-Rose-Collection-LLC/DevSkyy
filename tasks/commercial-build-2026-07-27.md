# Commercial-Grade Theme Build — Execution Report, 2026-07-27

Worktree: `.claude/worktrees/glimmering-crafting-shannon` (branch `worktree-glimmering-crafting-shannon`,
base `d855c037f`). The planned `theme-commercial-build` worktree was never created; this session executed
in-place after confirming `origin/main` had NOT diverged on the `wordpress-theme/` path.

**Evidence tags:** `[repo]` read source/working tree · `[live]` probed production this session ·
`[repro]` ran it and observed · `[test]` a check that executed and could have failed · `[inferred]` reasoned, not observed.

---

## 1. Live production baseline — captured BEFORE any change `[live]`

Probed 2026-07-27 via cache-busted `curl` (never WebFetch — it strips `<script>`).

| URL | Status | Bytes | PHP errors |
|---|---|---|---|
| `/` | 200 | 136,802 | none |
| `/collections/signature/` | 200 | 165,326 | none |
| `/collections/black-rose/` | 200 | 179,164 | none |
| `/collections/love-hurts/` | 200 | 137,889 | none |
| `/collections/kids-capsule/` | 200 | 93,057 | none |
| `/shop/` | 200 | 275,548 | none |
| `/cart/` | 200 | 211,546 | none |
| `/checkout/` | 302 → `/cart/` | (target 211,464) | none |
| `/my-account/` | 200 | 162,303 | none |

**Live theme version: 1.12.8.** Verdict: production is HEALTHY. There is no live fire to fight —
this is a depth/quality build, not a rescue.

Two behaviours that are BY DESIGN, not defects — do not "fix" them:
- `/checkout/` 302→`/cart/` on an empty cart is standard WooCommerce.
- Kids Capsule rendering 0 product cards is documented launch mode.

Response bodies saved for post-deploy diffing: `scratchpad/live-baseline/*.html`.

---

## 2. Pre-build gate baseline (so every later claim is attributable)

`npm run verify:theme` at session start, and again after tooling install:

| Aspect | At session start | After `composer install` | Note |
|---|---|---|---|
| php-syntax | PASS (166 files) | PASS | |
| phpcs | **SKIP** (not installed) | **PASS — 0 violations, 160/160 files** | now a real gate |
| phpstan | **SKIP** (not installed) | **FAIL — 144 errors** | pre-existing debt I surfaced, see below |
| min-sync | **FAIL** | **PASS** | `clean-css` was missing from node_modules |
| file-size | FAIL (5 PHP files) | FAIL (same 5) | pre-existing, out of scope |
| escaping | WARN (95) | WARN (95) | mostly noise, see §5 |
| a11y-static | WARN (72 img no alt) | WARN (72) | real, see §5 |
| templates / wc-support / no-placeholders / no-secrets / i18n / pot / json-manifests / style-header / screenshot | PASS | PASS | |

### Two FAILs are NOT the builder's work — recorded so nobody misattributes them

- **min-sync** was failing because `clean-css` was absent from `node_modules`, crashing `build-css.js`
  entirely. Fixed via `npm install` + full `npm run build` (54 CSS + 36 JS, 0 failures). The 36 "stale"
  `.min.js` diffs were single-line minifier-version drift, not content divergence `[repro]`.
- **phpstan 144 errors** appeared only because I ran `composer install`, flipping the aspect from SKIP
  to FAIL. **Proven pre-existing** `[test]`: extracted the pristine committed tree via
  `git archive HEAD | tar -x` into a scratch dir, symlinked `vendor/`, ran PHPStan there →
  **144 at HEAD = 144 in the working tree**. The builder introduced zero new static-analysis errors.
  (Method note: this gives a true pre-change baseline without `git stash`, which is forbidden in a
  shared worktree.)

### The bar for "gate-passing" today

`verify:theme` cannot go fully green today (file-size + phpstan are pre-existing). The real bar:

1. `npm run lint:php` clean
2. `vendor/bin/phpcs --standard=.phpcs.xml .` → **zero violations** (perfect 160/160 clean baseline
   captured pre-build, so any violation is 100% attributable to today's work — sharpest gate available)
3. min-sync PASS
4. file-size FAIL's *file list* unchanged from the 5 below — a new >800-line file would otherwise hide
   as one more line inside an already-red check
5. No new FAIL/WARN category; the two WARN counts must not increase

Pre-existing >800-line PHP files (scoped out): `inc/enqueue.php` 1311 · `inc/seo.php` 1149 ·
`inc/template-functions.php` 970 · `inc/performance.php` 939 · `template-preorder-gateway.php` 885.

---

## 3. Security — Phase 0 pass `[repo]`

Zero CRITICAL, zero HIGH. One MEDIUM found and **fixed this session**:

**bug-289** — `inc/rest-kids-capsule.php`. The public route
`GET /skyyrose/v1/kids-capsule/matching-set/{id}` used `permission_callback => '__return_true'` and
called `wc_get_product()` with no publish-status check, so an ID walk could disclose draft/private
pre-launch product name, price, and preorder edition/claimed counts. Fixed by mirroring the guard the
sibling route already had (`inc/klaviyo-integration.php:356`) — applied to BOTH the kids lookup (404s)
and the matched adult lookup (nulls out rather than leaking). Verified: `php -l` clean, PHPCS clean.

Confirmed solid, do not regress: every state-changing AJAX handler verifies nonces; all 9 `$wpdb`
queries use `prepare()`; admin REST gated on `manage_options`; no file-upload handling; no hardcoded
secrets; XML-RPC disabled; user enumeration blocked.

Accepted/known (not regressions): CSP ships `'unsafe-inline'` in `script-src` plus broad CDNs
(documented as WP/Woo/Elementor-required) — the build must not ADD origins or weaken `form-action 'self'`.

---

## 4. Catalog + imagery integrity `[repo]` `[repro]`

**PASS — 33/33 SKUs resolve imagery through the SOT, zero broken references.**

- Catalog: `data/skyyrose-catalog.csv`, 33 rows / 24 columns, all `published=1`
  (12 black-rose, 5 love-hurts, 14 signature, 2 kids-capsule). SKU numbering has intentional gaps.
- Exact SKU-set match between catalog and `data/sot-images.json` — no orphans in either direction.
- All 108 unique referenced image paths exist on disk AND are git-tracked. None sparse-excluded,
  none untracked, none zero-byte.

Scope caveat, stated honestly: this was **reference integrity only**. No image was opened to verify
garment↔SKU fidelity, so a wrong-garment pixel defect would NOT be caught here. That check is the
`product-fidelity` aspect (needs-vision) and remains unrun.

---

## 5. Accessibility + escaping — attribution census `[repro]`

Both reproduce the gate's numbers exactly, so post-build comparison is apples-to-apples.

- **escaping: 95** — largely noise. **Zero raw superglobals are echoed anywhere in the theme.**
  20 of 57 unique lines carry `phpcs:ignore` annotations as pre-escaped/trusted buffers; most of the
  remainder are boolean-ternary literal echoes, safe by construction. Phase 2 should NOT burn time here.
- **a11y img-no-alt: 72** — this one is real. 14 funnel-critical entries, 40 peripheral.

**Open commercial-grade issue:** `style.css`'s header advertises **"WCAG 2.2 AA"** in its Description
and carries the **`accessibility-ready`** tag — a formally-defined WordPress.org tag with strict
requirements — while 72 `<img>` tags lack `alt`. The claim is currently unsubstantiated. For a theme
being positioned as marketplace-grade this is a rejection risk, and it is the single most important
Phase 2 target. (The header itself is complete and well-formed — License, Text Domain, Tags all present.)

---

## 6. Deploy-source completeness — BLOCKING, read before any deploy

A theme deploy is an **atomic hot-swap**: production loses any file the source tree lacks (bug-252).

**Census: 19 riders documented, 16 present in this worktree, 3 MISSING.**

Missing (all `assets/scenes/**`, untracked, caught by blanket ignore `.gitignore:290`):
- `assets/scenes/black-rose/black-rose-rooftop-garden-v2-avatar.webp`
- `assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber-v2-avatar.webp`
- `assets/scenes/signature/signature-golden-gate-showroom-v2-avatar.webp`

Byte copies exist at `.claude/worktrees/collections-scroll-world/.../assets/scenes/{black-rose,love-hurts,signature}/`
(114,624 / 169,450 / 83,092 B).

**Crucially: per the manifest's own 2026-07-27 entry these 3 ALREADY 404 on production.** So deploying
without them deletes nothing currently serving — it perpetuates an existing gap rather than causing a
regression.

**FOUNDER DECISION (not taken autonomously):** whether to restore these 3 before the deploy. Not done
unilaterally because (a) they are avatar imagery, which is subject to the eyes-on QC gate — they'd need
pixel verification against `assets/branding/mascot/skyy-canonical-reference.jpeg` before shipping, and
(b) omitting them is status-quo, so inaction carries no regression risk.

Also verified: all 1,803 git-tracked theme files exist on disk (0 absent) — tracked-file completeness is
clean. `preflight_completeness()` gate confirmed present at `scripts/deploy-theme.sh:313`, invoked at `:427`.

Register correction: the "17 gitignored riders" memory is **partly stale** — the BR/LH/SIG emblems and
`assets/models/skyy.glb` are now *tracked*, not gitignored. Do not trust that list unverified.

---

## 6a. Phase 1 (a)–(e) scope reconciliation — the founder's central question

**Honest answer: the funnel was ALREADY substantially commercial-grade before today.** Today's work was
gap-closing + latent-defect repair + 4 visual patterns — NOT building a funnel from nothing. Every claim
below was independently spot-checked by the main thread, not accepted on the builder's word.

| # | Deliverable | Verdict | Evidence |
|---|---|---|---|
| (a) | All 6 funnel routes resolve | **COMPLETE pre-existing**, 1 real gap closed today | `front-page.php`; `page-collections.php` + 4 `template-collection-*.php`; PDP `woocommerce/single-product.php` (full custom override); `woocommerce/cart/cart.php`+`cart-empty.php`; `woocommerce/checkout/form-checkout.php`+`thankyou.php`. **Gap closed:** account had NO slug in `skyyrose_get_current_template_slug()` → rendered unstyled WC core markup on dark ground |
| (b) | WC wiring depth | **COMPLETE pre-existing** | add-to-cart simple+variable `single-product.php:161` + `single-product.js:39-107`; AJAX cart `woocommerce.js:199-275`, quick-add `product-card-holo.js:261-268`; mini-cart `header.php:66-71` + fragments `inc/woocommerce.php:188-211`; real catalog via `inc/product-catalog.php` |
| (c) | Real content, no lorem | **COMPLETE** | `no-placeholders` PASS + independent `grep -rinE "lorem ipsum\|dolor sit amet"` = **0 hits** `[repro]`. `template-coming-soon.php` is the `SKYYROSE_COMING_SOON_MODE` kill-switch (default false), not shipped content |
| (d) | Customizer reskinning | **COMPLETE pre-existing** | `inc/customizer.php` — verified **4 sections / 13 settings / 13 controls** (matched pairs) `[repro]`: brand colors, gold accent, dark bg, logo, 7 social networks, contact, KC launch toggle |
| (e) | Demo import + screenshot + header + README | **COMPLETE, one caveat** | `blueprints/skyyrose-demo-setup.json` (4117 B, verified present); screenshot 1200x900 PASS; style.css header PASS; readme.txt 22.5K + 11 docs HTML pages. **Caveat:** import is the WooCommerce **Blueprints admin flow**, not a custom one-click importer, and has NOT been executed (needs a local WP install) |

**Deliberate by-design exclusions — NOT gaps** (do not "fix" these):
- PDP related products + cart collaterals removed per founder canon 2026-05-27 ("the garment is the
  protagonist"), documented in `inc/woocommerce.php:247-254, 526-533` and `woocommerce/cart/cart.php:12-13`.
- Kids Capsule 0 product cards = documented launch mode.
- No Customizer typography toggle — fonts are locked to the `typography.json` SOT; a font picker would
  fork that SOT. Recommend keeping locked.

### New finding: orphaned cross-sell helper (FOUNDER CANON CALL)

`skyyrose_get_cart_wears_with()` — `inc/woocommerce.php:719`, `@since 7.2.0` — has **zero consumers**
`[repro]`: a repo-wide grep across PHP and JS returns only its own definition. It is a cart cross-sell
helper that directly contradicts the canon comment at `woocommerce/cart/cart.php:12-13` stating cart
collaterals are deliberately not fired.

Two valid resolutions, both requiring a canon decision rather than an engineering one:
(i) wire it into `cart.php` — reverses a documented founder canon call, or (ii) delete it as dead code.

**Left untouched deliberately.** This repo's rule is: remove only what YOUR change orphaned; flag
pre-existing dead code, don't delete it unasked. This predates today's work.

---

## 6b. Post-build verification results `[test]` `[repro]`

Every number below is real command output from this session, and every FAIL was attribution-tested
against the pristine committed tree before being accepted as pre-existing.

```
Build:     PASS   56 CSS + 36 JS, 0 failures; .min byte-identical to a fresh build
Types:     FAIL*  PHPStan 144 errors  — 144 at pristine HEAD, so ZERO introduced
Lint:      PASS   PHPCS 0 violations / 160 files, before AND after
           PASS   php -l  166 files, 0 parse errors
           FAIL*  stylelint 452 repo-wide — pre-existing; today's 8 found and FIXED
Tests:     FAIL*  PHPUnit 93 tests / 240 assertions, 1 failure — identical at HEAD
                  Coverage 84.71% lines (266/314)
Security:  PASS   no secrets, no TODO/FIXME/placeholder, no raw superglobal echo
Diff:      55 files (+801/-335); 15 non-.min, 2 new CSS files
```
`*` = attribution-verified pre-existing, NOT introduced by this build.

**file-size list is UNCHANGED** — same 5 files; `inc/enqueue.php` 1311→1325 (+14, the new CSS wiring).
No new >800-line file. This mattered: a new offender would have appeared as one more line inside an
already-red check and read as "unchanged".

**Pre-existing PHPUnit failure** (do not misattribute): `tests/unit/ProductCatalogTest.php:147` expects
`assets/images/br-001.webp`, receives `assets/images/br-001-model.webp`. Identical at pristine HEAD.

### bug-291 — 8 stylelint regressions found and fixed

Repo-wide `lint:css` was ALREADY red (460 errors), so 8 new errors changed neither the pass/fail state
nor meaningfully the count — they would have shipped invisibly. Caught by diffing stylelint output
between the pristine HEAD tree and the working tree.

Fixed: 3 camelCase keyframes (`toastProgress`, `ftNlShake`, `ftNlRise`) renamed to kebab-case, updating
both the `@keyframes` blocks AND every `animation:` caller — verified zero stale references survive in
source or minified output; 3 legacy `:not(a):not(b)` chains modernized to `:not(a, b)`.

The 2 remaining `#customer_login` violations are waived via targeted `stylelint-disable-next-line` with
an explanatory comment: that ID is WooCommerce **core** markup (`templates/myaccount/form-login.php`) and
is not ours to rename. Scoped to those two lines only — the rule stays active everywhere else.

Result: today's CSS is back to its exact HEAD baseline (15 errors, all pre-existing); repo-wide 460→452.

**Generalizable lesson:** an already-failing gate cannot detect new regressions by pass/fail alone, and a
large baseline hides small deltas in the total. Attribution needs the same gate run against the pristine
pre-change tree. Method used throughout today: `git archive HEAD | tar -x` into scratch + symlink
`vendor/` — gives a true baseline without `git stash`, which is forbidden in a shared worktree.

### bug-292 — `translation-ready` was 89% false; regenerated

`style.css` Tags advertise **`translation-ready`**. The shipped `languages/skyyrose.pot` contained
**187 of 1651** translatable msgids — **~11% coverage**. Header still read "SkyyRose 4.0.0" (theme is
1.12.8), POT-Creation-Date 2026-02-08, ~5.5 months stale. Translators could not translate 93% of the theme.

Important distinction: the **code is genuinely internationalized** — strings are correctly wrapped in
`__()`/`esc_html__()` with the `skyyrose` text domain (that's how they were extractable). Only the shipped
*artifact* was stale. So the fix is regeneration, not 1450 code edits.

**Why no gate caught it:** `verify-theme.sh`'s `pot` aspect only asserts the FILE EXISTS — a presence
check masquerading as a coverage check. It passed green the entire time.

Regenerated via `WP_CLI_PHP_ARGS="-d memory_limit=2G" vendor/bin/wp i18n make-pot . --exclude=vendor,node_modules,tests,docs,blueprints,assets/js/lib`.
(The default 128M limit OOMs in the Peast JS parser on this theme's large minified JS — raising the limit
is what makes it work; it is NOT a PHP 8.5 incompatibility, unlike the PHPStan issue.)

Safety checks performed BEFORE overwriting:
- `languages/` held **no `.po`/`.mo` files** → zero existing translations to lose, no `msgmerge` needed
- `.pot` has **no runtime effect** — only translators consume it, so zero regression risk to the site
- `msgfmt --check` valid (only the standard template-header warnings)
- All **50** msgids present in old-but-not-new verified **dead**: retired customizer color names
  ("Dark Gray", "Black to Gold"), old admin labels ("Accessibility Testing"), and "Add to wishlist",
  which now survives only in *docblock comments* and is therefore correctly not extracted
- The newsletter string added earlier the same session survives with its correct source reference

Result: **187 → 1651 msgids.** `i18n-domain` and `pot` aspects still PASS.

---

## 6c. Adversarial verification (Phase 2 + 3) and the fixes it forced

Five independent skeptical probes ran against today's diff — scope reality-check, second-pass security,
accessibility, motion/brand-canon, and line-by-line correctness. Result: **17 attributable findings,
0 blocking (zero CRITICAL/HIGH).** It independently DOWNGRADED two of the builder's self-reported
"COMPLETE" claims to PARTIAL, which is exactly why it ran.

Six real issues were found and **fixed**, then re-verified:

| Fix | Why it mattered |
|---|---|
| **bug-293 — luxury-cursor CSS/JS gate mismatch** | CSS gated on `! $skip_optional_css`, JS only on `'immersive' !== $slug` → on **7 slug types** the script loaded with no stylesheet. Latent for years; today's new `.cursor-label` span (first cursor element with real text) made it render as **stray visible "View" text on search results**. Root-caused via a shared `skyyrose_slug_skips_optional_assets()` helper so the CSS+JS pair cannot drift again |
| **bug-294 — 3 WCAG AA contrast failures** | On a theme advertising WCAG 2.2 AA. Logout link + out-of-stock label were `rgba(255,255,255,0.4)` = **3.77:1**; newsletter error was brand crimson = **3.63:1**. AA needs 4.5:1 |
| **`.toast-container` duplicate definition** | Defined in both `components.css` (today, `z-index:500`) and `footer.css` (pre-existing, `z-index:3000`). footer.css enqueues LATER, so it silently won — which also **defeated the `<480px` mobile full-width rule** the build report claimed as passing. Consolidated to one owner |
| **wishlist.css loaded site-wide** | Every selector targets `page-wishlist.php` markup, but the enqueue had **no conditional** — and before today the file didn't exist, so the `file_exists` guard meant nothing loaded. Creating it made it global. Now page-scoped; the JS stays global (wishlist buttons render on cards site-wide). ⚠️ **Scoping is `[repo]`-reasoned, NOT verified against live:** the condition is `is_page_template('page-wishlist.php') \|\| is_page('wishlist')`. `is_page_template()` requires the template to be ASSIGNED in the DB, and the slug branch relies on the page slug being `wishlist` (implied by `get_page_by_path('wishlist')` at `wishlist-functions.php:761`). If production uses a different slug AND no template assignment, the wishlist ships styleless again — the exact bug this fixes. **Confirm on a live wishlist render.** |
| **`toast.js` unvalidated `href`** | `action.href = opts.actionUrl` accepted any scheme — a latent `javascript:` URI vector. Now resolved + scheme-checked to http(s); relative paths still work |
| **New "View" string missing from `.pot`** | Already resolved by the bug-292 regeneration, which picked it up with source refs |

**Contrast fixes used the existing `--color-text-muted` token (#B3B3B3 = 9.44:1)** rather than inventing
values — fixing legibility AND removing hardcoded rgba. The brand crimson token is **unchanged**; only
the error *text* uses a lightened `#FF5C7A` (6.66:1). Verified `[repro]` that the crimson/danger tokens
remain in live use for borders and backgrounds (`woocommerce.css:247`, `contact.css:377-378,954-955`),
so nothing was orphaned. Every fix carries an inline comment with the measured ratio so the next editor
doesn't silently revert it.

**Reviewed and deliberately NOT changed:** `wishlist.css:166` uses crimson for `.wishlist-remove` on
hover/focus (3.63:1). Left as-is because the control's resting state is `rgba(255,255,255,0.7)` =
**9.72:1** (passes), the crimson appears only transiently, and it doubles as the border — where the
non-text UI threshold is 3:1, which 3.63 clears. The a11y specialist had the full file and did not flag
it. Recoloring a brand accent on a hover state is a design decision, not an engineering one.

**Verified after consolidating `.toast-container`** `[repro]`: `components.css` (the surviving owner) and
`footer.css` (where the duplicate was removed) are BOTH enqueued in `skyyrose_enqueue_global_styles()`,
both guarded only by `file_exists`, both on `wp_enqueue_scripts` priority 10 — so the survivor loads
everywhere the deleted rule did. Worth checking explicitly: stylelint and min-sync structurally cannot
detect "this stylesheet doesn't load on that page", which is precisely the bug-293 failure mode.

**Post-fix re-verification (all real output):** phpcs **0 violations** · phpstan **still exactly 144**
(my new helper function added none) · min-sync **PASS** · file-size list **unchanged** (`enqueue.php`
1325→1347 for the helper; no new offender) · stylelint on today's 6 CSS files **15 = exactly the HEAD
baseline**, repo-wide **452** unchanged → **zero stylelint errors attributable to today**.

### Independently corroborated: the account page needs eyes-on before it can be called done

The adversarial pass flagged account-page resolution as UNVERIFIED. Checking the **saved live
`/my-account/` HTML** `[live]` settles part of it: production renders `wp-block-woocommerce-customer-account`
with **no `<form>` element at all**, and **26 of the 28** `woocommerce-*` classes the new 492-line account
stylesheet targets are **absent** from that page.

Scope stated honestly: that capture is **logged-out**, so orders/addresses/navigation would legitimately
not render — but the *login form* classes should have been present and were not. This is **not** proof the
new CSS is wrong; it IS proof it is **unverified against real markup**, and it is the single most important
thing to check before claiming the account surface is done. Requires a logged-in render.

---

## 6d. Code review of the uncommitted diff — found a CRITICAL

A 4-lane review (security / quality / best-practices / a11y-regression) was run specifically to cover
the gap nothing else had: **the session lead's own six fixes, which no reviewer had seen.** It found a
CRITICAL that every static gate had passed clean.

> ⚠️ **The workflow's `confirmedCount: 0` / `blockingCount: 0` are ARTIFACTS, not results.** All five
> adversarial-verifier and judge agents died on a session limit; only the 4 review lanes completed.
> Reporting "0 blocking" from that output would be the fail-open pattern this repo bans (bug-230).
> The findings below were therefore verified BY HAND in the main thread.

### bug-295 — CRITICAL: the newsletter was 100% non-functional (DOM clobbering)

`footer-cro.js` did `fetch( form.action, … )`. The form contains
`<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">` — required by admin-ajax.
Per the HTML spec a **named form control shadows the form's `action` IDL property**, so `form.action`
returned the *HTMLInputElement*, not the URL.

**Proven in a real browser** (Playwright, against a copy of the actual `footer.php` markup) `[repro]`:
```
form.action instanceof HTMLInputElement : true
String(form.action)                     : "[object HTMLInputElement]"
new Request(form.action).url            : http://…/[object%20HTMLInputElement]
form.getAttribute('action')             : https://skyyrose.co/wp-admin/admin-ajax.php
```
Correcting the review's stated mechanism: it does **not** throw a parse error. It silently resolves to a
bogus same-origin path → 404 → `res.json()` rejects → the `.catch` fires **"Connection problem — please
try again." on every single submission.** Silent garbage is exactly why it shipped unnoticed.

Fixed with `form.getAttribute( 'action' )` (reads the content attribute, immune to shadowing). Rebuilt
and verified the minified bundle contains `getAttribute("action")` and no `form.action`.

**Why no gate caught it:** valid JS, valid PHP, phpcs/php -l/min-sync all green, and the code *reads*
correctly. This class of bug is invisible to static analysis — only a browser finds it.

### bug-296 — MEDIUM: the bug-289 guard was bypassable via variation IDs

`wc_get_product()` returns a `WC_Product_Variation` for a variation ID, and a `product_variation` post
carries its **own** `post_status`. Setting a variable product to draft does **not** cascade to its
children, and `WC_Product_Variation extends WC_Product_Simple` without overriding `get_status()` — so a
variation of a draft pre-launch product reported `publish` and walked straight past the guard added
earlier the same day. An unauthenticated ID walk would return name/price/`price_html`/permalink for
unreleased products.

Fixed by rejecting variations outright (a variation is never valid input here — `_kc_matching_adult_id`
lives on the parent), applied symmetrically to the adult lookup, returning the identical 404 so no
existence signal is introduced.

### Version bumped 1.12.8 → 1.12.9 (deploy-correctness, not a nit)

The review flagged an orphaned `@since 1.12.9`. The real issue is bigger: `SKYYROSE_VERSION` is the
cache-bust parameter on **52** enqueue calls `[repro]`. Shipping modified CSS/JS under an unchanged
version means returning visitors keep serving **stale cached assets** — the deploy would be silently
ineffective. Triple synced: `functions.php:21`, `style.css:12`, `readme.txt:7`. Gate now reports
`Version 1.12.9`.

### Still open from the review (non-blocking, LOW)

- `toast.js` dead `progress` binding — assigned, never read.
- `luxury-cursor.js` touch teardown removes `cursor-active/hover/down` from `<html>` but not the new
  `cursor-labeled` class.
- `toast.js` URL guard permits `//evil.com` and any external `https://` — offsite-link concern, not XSS.
  **Independently proven safe against script execution** `[repro]`: 23 bypass vectors (case variants,
  embedded newline/tab/CR, whitespace and null-byte prefixes, `data:`/`vbscript:`/`blob:`/`file:`) → all
  rejected; **0 script-execution bypasses**. Grep also confirms no caller passes `actionUrl` yet.

---

## 7. Known tooling limitation

PHPStan crashes in its parallel worker under PHP 8.5.6 when invoked bare; this phar build has no `-j`
flag to disable parallelism. It DOES run correctly via the project config
(`XDEBUG_MODE=off vendor/bin/phpstan analyse -c phpstan.neon --memory-limit=2G`). Deliberately did NOT
generate a phpstan baseline — doing so mid-build would mask errors in newly written code.

---

## 8. Scope explicitly deferred past today (sequenced, not dropped)

- **Phase 1b — Immersive Worlds** (all `template-immersive-*.php`, `assets/js/immersive.js`). Owned by
  `wp-immersive`, not the funnel builder — top-of-funnel storytelling, not shopping.
- **12 of the 16 Phase 1a priority patterns.** Only the 4 that extend already-shipping code were in
  today's scope (`luxury-cursor.js`, `product-card-holo.js`, `toast.js`, `footer-cro.js`).
- **file-size refactor** of the 5 oversized PHP files.
- **144 PHPStan errors** — pre-existing backlog.
- **`product-fidelity`** (needs-vision garment↔SKU pixel check) — unrun.
- `archive.php:33` dead `content` template-part reference (blog archive, not funnel).
