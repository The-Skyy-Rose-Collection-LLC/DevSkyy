# Fix Log — WP Commercial Theme Sweep

## Wave 1 — 2026-07-19

### P0-1: style.css malformed rule (missing `{`)
- `style.css:515-522` selector list ended with `,` then `padding-top: 0; }` — rule dead.
- CSS error recovery consumed through line 530's `{`, ALSO killing `.homepage-v2 .site-header/.site-footer { display:none }` → double-nav risk on homepage, header-offset dead on immersive templates.
- Fix: last selector now ends ` {`. style.css served unminified (get_stylesheet_uri) — no build step needed.
- Found: Atlas census. Verified: direct read + Atlas's production curl byte-match.

### P0-2: duplicate mobile-bottom-nav include
- `footer.php:253` (intentional, in-footer per WS4 acceptance) + `footer.php:260` (stale) both rendered `<nav class="mobile-nav">` — duplicate fixed chrome + duplicate a11y landmark on every page.
- Fix: deleted line-260 include. `php -l` clean.
- Found: Atlas census (live-verified 2× nav on /about/ + /collections/black-rose/).

### Baseline (pre-fix) — tasks/wp-commercial-theme/baseline/summary.csv
Zero pages ≥90 all-categories on mobile. Fires: PDP mobile perf 49 / LCP 27.3s / TBT 671ms / BP 79 · cart CLS 0.49 + SEO 69 · black-rose mobile LCP 13.6s · landing-BR LCP 13.7s · pre-order mobile LCP 10.1s · wishlist desktop CLS 0.40 · collections a11y 89 · homepage mobile perf 64.
Data gaps to re-run at verify: faq desktop (truncated row), 404 probe (both rows errored).
