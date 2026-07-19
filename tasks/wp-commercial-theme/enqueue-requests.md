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
