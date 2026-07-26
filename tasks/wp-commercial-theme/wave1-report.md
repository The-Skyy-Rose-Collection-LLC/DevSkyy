# Wave 1 Report — WP Commercial Theme Sweep (2026-07-19)

**Status: BUILT, COMMITTED, PUSHED — DEPLOY BLOCKED BY SESSION PERMISSIONS.**
v1.12.0 is ready on `main` (`15e238068` + `e812c8402`, pushed to origin). The deploy
command was denied by the Claude Code permission classifier in this session.

**To ship:** run `! STOPSHOW_ACK=1 bash scripts/deploy-theme.sh` (the `!` prefix runs it
in-session so the loop sees the output), or just run it in any terminal from the main
checkout. **The loop auto-resumes**: it probes the live version every ~30 min and launches
Sentinel + Pixel + fresh Lighthouse verification the moment live = 1.12.0.

## Baseline (pre-fix, live v1.11.1) — zero pages ≥90 all-categories on mobile
Fires: PDP mobile perf 49 / LCP 27.3s / TBT 671ms · cart CLS 0.49 · black-rose LCP 13.6s ·
pre-order LCP 10.1s · wishlist CLS 0.40 · collections a11y 89 · home mobile 64.
Full data: `baseline/summary.csv` (+ per-audit JSONs).

## Shipped in v1.12.0 (63 files + 2 rider-tracking)
- **Two live P0s**: malformed style.css rule (was also killing the homepage header-hide
  via CSS error recovery); duplicate mobile bottom nav on every page.
- **Perf**: dead render-blocking CSS gone; plugin-stylesheet flood dequeued fail-closed
  (homepage ~40→~29 sheets); 9 handles now serve .min; Inter preload 404-only;
  **header lockup fetch 637KB→5.8KB on every page**; PDP LCP unhidden (reveal-class bug,
  27.3s→expected ~2-4s); cart/wishlist CLS root-caused (late-styled footer) + styled
  empty-cart template (the "bare cart" was WC's un-overridden cart-empty.php).
- **Exposure seal (P0)**: all 36 internal dossiers were world-readable + PDP rendered
  internal spec fields as copy. Now: internal fields never render, runtime reads a
  sanitized compiled index (fail-closed, 35/35 parity), 16 deploy exclusions keep
  dossiers/embeddings/catalog-bak/scripts off the server. Live stays exposed until deploy.
- **Visual**: shop desktop grid collapse fixed (WC float/clearfix phantom card);
  **Hanken Grotesk now the real body font sitewide** (three undefined font vars were
  silently falling back to Inter on 19/20 pages); mobile overlay stack clearance contract
  (consent banner / bottom nav / mascot no longer occlude ~30% of viewport); policy-page
  horizontal scroll fixed; WebGL no-support guard.
- **A11y/SEO**: 16 root-cause fixes — ARIA roles/labels, WCAG-AA contrast (dark ink on
  rose gold; derived text-only tokens), Permissions-Policy self-gating, youtube-nocookie.
- Bugs logged bug-266..274; buglog ID-collision repaired (264/265 backfilled).

## Founder decision queue (nothing auto-applied)
1. **Pre-order hero shows a person smoking** — money page, blocks paid ads. Swap needs
   your call (existing verified asset or new gated render).
2. **PDP/cart best-practices capped at ~79 by Stripe/hCaptcha/Google-Pay third-party
   cookies.** Only path to 90+: scope express-pay + hCaptcha to checkout only —
   conversion trade-off, your call.
3. **Mascot 3D on mobile PDP** drives TBT (three.js + 1.1MB GLB) — proposal: interaction-
   gate or 2D on mobile PDPs only. Brand call.
4. Contrast tweaks flagged for review: dark-ink-on-rose-gold buttons; Love Hurts small-text
   crimson uses derived #FF5C7A (surfaces keep #DC143C); contact gradient light-end #A4626C.
5. **wp-admin ops** (not theme code): uninstall wp.com Fonts-UI Inter; Jetpack Likes off
   pages (FIX-12); catalog CSV still deploys with internal-ish columns (branding_spec,
   render_*) — wave-2 refactor to consumer JSON proposed.
6. PHPUnit: 1 pre-existing failure (test encodes pre-onmodel image order; function
   unchanged) — reconcile test vs intent, separate change.

## Verification plan (auto-runs post-deploy)
Sentinel: fresh 18-URL Lighthouse (mobile+desktop) + faq.desktop re-run + dossier-404
check + Bolt's three dequeue risk spots. Pixel: per-fix Playwright probe harness
(shop grid, Hanken computed font, consent clearance, table containment, zero pageerror).
Loop continues until every page ≥90 (cart/checkout SEO exempt by design) + visual pass.
