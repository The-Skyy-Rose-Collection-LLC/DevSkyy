# Enqueue change requests (for Bolt / main — files outside requester's boundary)

## From Atlas — Wave 1 (2026-07-19)

1. **Head-enqueue footer-cro.css globally.** `footer.php:19` includes the part unconditionally,
   so the "only ships where rendered" rationale for the in-part late enqueue is void. Add
   `skyyrose-footer-cro` to `skyyrose_enqueue_global_styles()` (dep: `skyyrose-design-tokens`).
   My interim fix in `template-parts/footer-cro.php` uses `wp_register_style` +
   `wp_print_styles('skyyrose-footer-cro')` — it becomes a harmless no-op once the head
   enqueue exists (already-printed handles are skipped), so no coordination needed.

2. **Mascot cost on mobile PDP.** `product_the-fannie.mobile.json`: three@0.170.0/+esm 855ms
   scripting + DRACOLoader 202ms + skyy.glb 1,117KB — the dominant TBT (671ms) and byte
   driver on the PDP. Request: harden the idle-load gate for `single-product` on mobile
   (require first interaction instead of requestIdleCallback, or skip 3D ≤768px and keep the
   2D sprite). Mascot is founder-loved — visibility rules apply; propose, don't silently cut.

3. **Serve .min for size-guide/luxury-cursor/skeleton CSS** (`inc/enqueue.php:179-206`
   bypasses `$use_min`; .min files exist). `size-guide.css` shows up in the PDP
   render-blocking audit (173ms).

4. **Cross-team (Pixel/main): navbar fallback image.** `header.php:94` puts
   `tsrc-lockup-rotating@2x.webp` (637KB) as `<img>` fallback inside the `<video>` — the HTML
   preload scanner fetches it on every page even when webm plays (offscreen-images flags it;
   745KB est savings on PDP). Swap the fallback `src` to the static poster webp.

5. **fonts.wp.com Inter loads late and reflows text sitewide** (sub-cause in cart/wishlist
   CLS traces; small crumbs elsewhere). Ties into census P1-4 (self-hosted Inter preload
   unused). Consider: drop the `inter-latin.woff2` preload, and audit what registers the
   fonts.wp.com Inter face (Jetpack Global Styles) — it shadows/duplicates our self-hosted one.

## From Pixel — Wave 1 (2026-07-19)

6. **[RESOLVED — Bolt landed this before the request; Inter gated to 404 slug, Hanken sitewide. No action.]** **Font preload flip after the --font-body fix.** `design-tokens.css` §1.12 now defines
   `--font-body: var(--skyyrose-font-body)` — body text on ALL templates switches from the
   Inter fallback to self-hosted Hanken Grotesk (this was the audit D7 root cause: the var
   was consumed by style.css:239 but never defined). Requested end state per team-lead:
   **preload the Hanken Grotesk variable woff2** (it is now the first-paint body face
   sitewide), and demote/drop the Inter preload — Inter remains only a stack fallback and
   the 404 template face. Dovetails with Atlas req #5 (fonts.wp.com Inter shadow/duplicate):
   Bolt's "Inter preload kept on evidence" decision predates this fix — the evidence flips
   once Hanken is the computed body font.

## From Pixel4 — Wave 7 (2026-07-20)

7. **Collection-page critical path is 41 stylesheets+fonts / ~489KB (round-6 BR/SIG mobile
   traces)** — this, not the hero bytes, is what lantern models as the col-hero LCP "load
   delay" (1.4-1.8s): the preloaded hero webp arrives High at ~150ms observed but shares the
   simulated 1.6Mbps link with half a megabyte of CSS/fonts. Home is 35 sheets/400KB, same
   mechanism. Request: prune/defer per-template sheets on collection slugs and home; any
   font-preload work (Pixel3's shop text-LCP handoff) compounds here.

8. **gsap.min.js 0.9-1.2s + ScrollTrigger 0.5s + page inline script 1.2s eval inside the
   FCP→LCP window on collection pages** (round-6 bootup-time, 4x throttle) — the remaining
   col-hero "render delay" driver after my decoding=sync change. If gsap/ScrollTrigger can
   idle-gate on collection slugs the way Wave 6 gated the mascot's three.js, BR/SIG mobile
   LCP should drop ~1s further. Template side is done (no reveal classes above the fold;
   decode now sync).

9. **DELETE the pre-order luxury-nighttime preload — enqueue-performance.php:417** (Pixel5,
   Wave 8). It preloads `branding/hero/luxury-nighttime-1680w.jpg` fetchpriority=high on the
   pre-order template, but v1.12.2 replaced that hero with the founder video: the only
   remaining consumer is the BELOW-FOLD manifesto backdrop (template-preorder-gateway.php
   ~716), whose `<picture>` picks the 1280w WEBP srcset — the preloaded 1680w JPG is fetched
   by NOTHING. Round-7 mobile trace: 229KB High at 133ms, ahead of the real LCP (the 21KB
   video poster), plus lantern link contention. Delete the preload outright — the poster is
   discovered from an inline style attr during HTML parse (~140ms) and needs no preload.
   This is the single biggest slice of the pre-order 85→76 regression.

10. **Inter webfont load — verify gone after theme.json change, else it's DB Global Styles**
   (Pixel5, Wave 8). Round-7 wishlist trace pulls TWO fonts.wp.com Inter v13 files (98+105KB)
   + self-hosted inter-latin.woff2 (48KB) on every page because theme.json assigned the BASE
   body + button fontFamily to Inter — off typography canon (body/UI = Hanken Grotesk; Inter
   is fallback-only). I flipped both theme.json refs to hanken-grotesk. Post-deploy, curl any
   page for `fonts.wp.com/s/inter`: if it persists, wp-admin Global Styles (DB) still pins
   Inter — founder/team-lead action, not theme code. This is the main lever on wishlist's
   text-LCP (FCP 1.5s but LCP 4.2s = webfont swap repaint under ~250KB of simulated font
   contention) and trims every laggard's shared link.
