# SkyyRose V2 Visual Dialogue Plan

Planning-only pass for Flagship 2. This document compares the V1 production theme with the V2 release candidate and defines the visual/story conversation V2 should stage. It does not authorize PHP, CSS, JS, asset generation, theme activation, or deployment.

## 1. Reading of the two systems

V1’s strength is cumulative storytelling: the homepage and collection pages move from atmosphere to founder voice to product, then back into world, lookbook, manifesto, cross-navigation, and newsletter. Its collection page has a clear “film spine → product grid → immersive experience → lookbook → philosophy → founder/story → CTA” rhythm.

V2’s strength is a more ownable house grammar: numbered chapters, `sr2-*` editorial framing, collection lockups, native horizontal rails, sticky narrative chapters, image-curtain reveals, WooCommerce-bound cards, and explicit poster/text fallbacks. Its main risk is compression: some V1-specific founder and collection language has been replaced with broad campaign copy, and some V2 visual assignments are repeated or do not yet carry enough collection-specific product truth.

The V2 direction is therefore: keep V1’s emotional order and proof points, but express them through one coherent “house / chapter / world / piece” system. Every visual beat must answer one of three questions:

1. Where did this world come from?
2. What makes this world materially distinct?
3. Where can the visitor enter it without leaving the story?

## 2. Canonical guardrails

### Authority order

- Collection story, identity, palette, lockup: V1 `data/collections/<slug>/identity.json` and `copy.md`; generated SOT views are `sot.json`.
- Non-product imagery: V1 `data/visual-manifest.json`, carried into V2’s verified `assets/sot/` bundle and `ASSET-PROVENANCE.md`.
- Product names, availability, price, imagery, stock, pre-order state, and product URLs: WooCommerce in V2; never hand-authored in a visual plan or scene.
- Founder film and portrait: V2 `ASSET-PROVENANCE.md`; film is opt-in, controls-only, muted derivative only.
- Collection names are image lockups where the SOT says the lockup is canonical. Do not type-render a lockup as a substitute.

### Story truth to preserve

- Signature: the beginning; “Not basics. Blueprints.”; the first rose and the Oakland foundation.
- Black Rose: “Defining beauty through the color black.”; Oakland-specific gravity; black as posture/conviction/armor, not generic darkness.
- Love Hurts: Beauty and the Beast from the Beast’s perspective; the Hurts bloodline; “They called me Beast. They were right.”
- Kids Capsule: “The Heir to the throne.”; the daughter/name/legacy story; same craftsmanship in smaller silhouettes, without sentimentality.
- Global house: Oakland-born independent luxury, four collections, limited/finite product truth only where the catalog/WooCommerce state supports it.

### Do not promote as canon without a separate approval

- V2’s broad replacement lines when they displace the exact collection copy above.
- Any scene hotspot whose label, SKU, image, or URL is not resolved from WooCommerce/catalog truth.
- Unverified physical-campaign concepts in the Kids Capsule copy file (soil cards, packaging threads, or “torch pass” campaign mechanics). They are not runtime asset/product truth for this plan.
- Press, awards, dates, founder biography expansions, or product claims unless retained from the canonical source and assigned to an approved page.

## 3. House-wide sequence

The recommended V2 journey is:

`Arrive at the house → meet the origin → choose a world → enter a collection → encounter a piece → verify the order path → reserve/buy → continue the house`

The visual dialogue should alternate between three registers:

- **Atmosphere:** verified scene or founder image creates desire and place.
- **Voice:** short canonical line supplies meaning; longer copy is available in the accessible reading order.
- **Proof:** a real WooCommerce product, collection state, fulfillment statement, or service path gives the emotion a truthful next action.

Motion should reveal hierarchy, not decorate it: slow depth/parallax on large imagery, image-curtain reveals on chapter entry, horizontal rail progress for worlds, and restrained product-image transitions. Reduced motion must keep the same sequence as a static vertical reading order.

## 4. Page-by-page visual dialogue plans

### 4.1 Homepage — the house invitation

| Beat | Plan |
|---|---|
| Sequence | 1) Oakland arrival / campaign hero → 2) house mark and statement → 3) four-world rail → 4) live featured pieces → 5) founder/origin bridge → 6) reserve portal. |
| Emotional beat | Recognition, then curiosity: “This is a house with a point of view; which chapter is mine?” |
| Approved visual identity | Primary: `assets/sot/branding/hero/flagship-house-runway-gpt2.webp` and responsive derivatives; `assets/sot/video/tsrc-spin-alpha.*` only as the registered brand-motion mark. Multi-collection lockup should use the verified Skyy Rose / Signature-capable lockup from the SOT, not a newly typed logo. |
| Copy purpose | Keep V2’s short arrival statement as a door, but let the house story use only approved Oakland/founder language. The collection rail copy must be the four canonical collection seeds/taglines, not generic adjectives. |
| Motion/reveal | Hero depth is optional enhancement; first-paint copy and mark remain visible without JS. Rail advances by native scroll/touch and explicit previous/next controls. Featured products use image curtain reveal only after content is available. |
| Product/collection truth | The collection rail is four worlds. The product strip is a live WooCommerce query; never imply “new,” “limited,” or “pre-order” unless the queried product state supports it. |
| Fallback | Static campaign hero/poster, static four-card vertical stack, normal product grid, and text statement. `prefers-reduced-motion` removes depth, rail pinning, and reveal transforms while preserving anchors. |
| CTA | “Enter collections” is the story CTA; “Shop the house” is the commerce CTA; reserve portal CTA goes to `/pre-order/`. |

**V1 strength to retain:** the home-to-collection emotional handoff and a visible reason to enter pre-order. **V2 ownership move:** use the Flagship House campaign image and TSRC mark as a repeatable house signature, then make each world card visibly distinct by its own lockup, palette, scene, and canonical line.

### 4.2 About — origin before expansion

| Beat | Plan |
|---|---|
| Sequence | 1) Founder portrait / promise → 2) founder quote → 3) optional controlled film → 4) origin chapter → 5) five-stop world rail (origin plus four collections) → 6) mission/collection CTA. |
| Emotional beat | Intimacy, credibility, then inheritance: the house is a person’s promise before it is a retail system. |
| Approved visual identity | `assets/sot/branding/about/skyy-rose-founder-portrait.jpg`; approved muted film derivative through the WordPress Media Library per `ASSET-PROVENANCE.md`; V2 `assets/scroll-world/scene-1-signature.webp` through `scene-4-kids-capsule.webp`. |
| Copy purpose | Preserve V1’s founder-first strength and exact canonical quotes, but remove unsupported additions. The film explains/embodies; the text transcript/quote makes the story available without playback. |
| Motion/reveal | Portrait may use subtle depth; film never autoplays and always exposes controls. World rail may pin on desktop but must become a normal horizontal/vertical scroller on touch and reduced motion. |
| Product/collection truth | The four world chapters link to the four V2 collection routes. No products appear until the visitor chooses a world. |
| Fallback | Portrait + full text chapters + vertical collection links if video, JS, or horizontal pinning is unavailable. |
| CTA | “Enter the collections.” Each world card has a direct “Enter [collection]” link. |

**Gap:** V1 provides timeline, Oakland/community, and press-room beats that V2 currently compresses into origin/film/world/mission. Preserve the verified parts of those beats as optional editorial subsections only if their source copy and links remain canonical; do not reintroduce unsupported press claims by visual implication.

### 4.3 Collections index — four doors, not a product dump

| Beat | Plan |
|---|---|
| Sequence | House hero → four collection doors → optional live cross-house product strip → reserve invitation. |
| Emotional beat | Orientation and choice. Each collection should feel like a different room in one building. |
| Approved visual identity | V2 `branding/hero/signature-golden-gate-yacht-1280w.webp` as house-scale opener; V2 scroll-world scene for each collection; each collection’s SOT lockup. |
| Copy purpose | Use canonical collection seeds/taglines as the one-line distinction. Avoid V2’s “Signature begins / Black Rose protects…” phrasing unless approved as a derivative line. |
| Motion/reveal | Numbered cards reveal in sequence; native rail with visible count and buttons. No card should depend on hover. |
| Product/collection truth | Four collections, four routes. Product count can be displayed only when calculated from current catalog/WooCommerce state. |
| Fallback | Four full-width stacked cards with lockup, line, description, and link. |
| CTA | “Enter world” per card; “Find your chapter” for the optional live strip; “Enter pre-order” for reserve. |

### 4.4 Collection pages — one system, four distinct voices

The shared V2 order should be: hero lockup → canonical intro → real product grid → immersive world rail → manifesto/lookbook → cross-collection continuation. This changes V1’s order only where needed to prevent an emotional scene from implying a product that is not available. If the “story before product” effect is more important for a specific launch, place a short canonical intro/world chapter before the first product row, but keep the product truth immediately reachable.

| Collection | Approved visual identity | Emotional dialogue and copy purpose | Product truth / CTA |
|---|---|---|---|
| Signature | `branding/hero/signature-golden-gate-yacht-1280w.webp`; `images/immersive/scene-signature-golden-gate.webp`; `images/immersive/scene-signature-oakland-atelier-gpt2.webp`; `images/lockups/signature-lockup.webp`; `images/logos/rose-gold-rose.webp`; `images/lookbook/lb-rose-hoodie-beanie-480w.webp`. | Establish bedrock, not nostalgia. Lead with “Not basics. Blueprints.” and the canonical first-rose/Oakland origin. Use Bay Bridge as Oakland-connected place only where the approved story permits. | Query Signature WooCommerce products; no hand-authored SKU promise. Hero CTA: “Shop pieces.” Story CTA: “Enter the world.” Closing CTA: collection shop or real pre-order route according to product state. |
| Black Rose | `images/immersive/scene-black-rose-moon-court-gpt2.webp`; verified Black Rose lockup; `images/logos/black-roses-cloud-cluster.webp`; `images/lookbook/lb-black-rose-football-480w.webp` and hockey lookbook; approved Black Rose patches only as product-story accents. | Make black specific: Oakland gravity, posture, conviction, armor. The visual progression is pressure → depth → silver glint → standing presence. Use the canonical “The beauty of the color black…”/“You wear it because you already stood up” register rather than generic gothic copy. | Render only WooCommerce/catalog-bound Black Rose pieces and real back/front imagery. Patch accents must correspond to the relevant product story. CTA: “Shop the Collection” / “Enter the world.” |
| Love Hurts | `branding/hero/beauty-and-beast-1280w.webp`; `images/immersive/scene-love-hurts-cathedral.webp`; `images/immersive/scene-love-hurts-cracked-rose-gpt2.webp`; `images/lockups/love-hurts-lockup.webp`; `images/logos/heart-rose-composite.webp`; `images/lookbook/lb-love-hurts-varsity-480w.webp`. | Move from Beast’s exterior to protected tenderness. Preserve “They called me Beast. They were right.” and the Hurts bloodline framing; do not reduce it to “love leaves a mark.” | Render only live Love Hurts products and their approved images. CTA: “Shop pieces,” then “Carry the bloodline” only if that exact CTA is approved in the collection content; otherwise use the neutral collection CTA. |
| Kids Capsule | `images/immersive/scene-kids-capsule-playroom.webp`, runway, and heir-runway GPT-2 scene; `images/scroll-world/scene-4-kids-capsule.webp`; `images/logos/sr-monogram-rose-gold.webp`; `images/lookbook/lb-kid-black-rose-480w.webp`. | Treat legacy as inheritance, not cute nostalgia. Use “The Heir to the throne” / “Luxury runs in the family” only as canonical copy. Keep the two-SKU/tight-capsule truth visible when product data confirms it. | WooCommerce is the only source for current Kids Capsule products, price, sizes, and stock. No invented childwear scene hotspot. CTA goes to the real Kids Capsule collection/product route. |

**Shared collection motion:** V1’s film spine and feature-scroll idea should survive as a V2 “world rail + manifesto” dialogue: one image establishes place, one short line names the beat, one real product link lets the visitor enter. Use image curtain reveals, restrained parallax, and progress indicators. A static chapter list must remain equivalent in meaning.

### 4.5 Pre-order — desire, then reservation clarity

| Beat | Plan |
|---|---|
| Sequence | Silent editorial film/poster → collection choice → approved Black Rose salon scene/hotspots where each hotspot resolves to a real product → three-step reservation explanation → live pre-order products → fulfillment/FAQ → email or return-to-collection. |
| Emotional beat | Anticipation becomes confidence. The visitor should understand what they are reserving before the CTA becomes urgent. |
| Approved visual identity | `assets/sot/video/preorder-portrait-noaudio.mp4` and poster; `assets/sot/images/preorder/black-rose-salon.webp`; V1 global `luxury-nighttime` and verified SR seal/monogram only if present in the V2 SOT bundle. |
| Copy purpose | Keep V1’s “built from the concrete up” process clarity and limited/finite language only where product/order data supports it. The film is mood; the three steps are operational truth. |
| Motion/reveal | Film is muted and controls-enabled; autoplay behavior must remain subject to the page’s accessibility/performance contract. Hotspot focus state mirrors the selected card. Reduced motion shows poster and static hotspot/card list. |
| Product/collection truth | Product cards are WooCommerce `pre-order` state; no empty placeholder presented as an available piece. A hotspot may link only to the corresponding real product. |
| Fallback | Poster plus accessible list of scene items; normal product grid; plain text steps and FAQ. |
| CTA | “Explore pieces,” “Reserve,” and final “View pre-order pieces” only when the query returns eligible products. |

**V1 strength to retain:** the journey/process, lookbook, manifesto, FAQ, and email capture after the gateway. **V2 ownership move:** make the Black Rose salon the one distinctive interactive editorial scene, while ensuring it is a sanctioned hotspot→real-product bridge rather than an invented catalog.

### 4.6 Shop/archive — editorial frame around live commerce

V1’s product grids have stronger lookbook rhythm and collection-aware card treatment. V2 should retain the editorial header, collection-world tabs, and product-card parity, but keep all names, images, prices, stock, and badges WooCommerce-bound. The visual plan is: shop masthead → collection filters → live grid → empty/error state → service links.

Motion is limited to card image transition/reveal and filter state; no parallax should obscure price, availability, or add-to-cart controls. Fallback is a plain, keyboard-operable grid. CTA is the product card action or collection filter, never a visual-only hotspot.

### 4.7 Single product — piece as evidence of the world

V2 already gives the PDP a collection breadcrumb, collection-world aside, and optional fail-closed 3D viewer. Preserve V1’s editorial product detail feel, but order it as: product media and truth → purchase controls → collection context → details/fit/service → related real products.

Approved imagery is the WooCommerce product media resolved by the product record. A 3D viewer appears only when the approved-model manifest and integrity gates pass; otherwise the static product gallery is the complete experience. No placeholder model, speculative material claim, or scene image should stand in for a product view. CTA is the real add-to-cart/pre-order action.

### 4.8 Cart and checkout — remove spectacle, keep confidence

These are not story pages. Preserve V2’s house chrome, but let the order summary, product image, quantity, price, shipping/tax, notices, and payment path dominate. The visual dialogue is “you chose a piece; here is exactly what happens next.” Reduced motion and no-JS fallback must remain fully usable. CTA is checkout progression or payment submission supplied by WooCommerce.

### 4.9 Contact — the house answers

V1 has a richer community/service surface; V2 has a more direct “Talk to the house” page. Keep V2’s Signature Oakland atelier image as a quiet contextual backdrop, with an immediate text/form layer. The image is decorative if it does not carry verified location meaning. Preserve the response promise and service routes only if their actual values are current. Fallback is the form and direct email/phone text. CTA: “Send to the house.”

### 4.10 FAQ, shipping/returns, size guide, policy, and generic editorial pages

V1 supplies dedicated, scannable information templates with reveal classes and clear CTAs. V2 currently routes these through the generic page/content path while linking to them from contact. This is a parity gap, not an invitation to add decorative imagery first.

Plan: give each service page a restrained house-standard header, then keep the canonical content as the primary visual object—accordion/details, tables, steps, and notices. Use no unverified product or founder image. Reduced motion is the default-equivalent reading order. CTAs: FAQ → contact; shipping/returns → support; size guide → return to product/shop; policy → relevant service route.

### 4.11 Blog/journal, builder-owned pages, 404, and maintenance states

V1 has broader editorial and fallback surfaces; V2 has a journal index, builder templates, and safe commerce fallbacks. Keep these surfaces deliberately quieter than the homepage and collection worlds. Builder content owns its page body; the theme should supply consistent skip link, heading, contrast, focus, and footer chrome. Empty journal, missing collection, WooCommerce-disabled, and 404 states need real text and a route back to collections/shop—not blank canvases or broken scene mounts.

## 5. Page-by-page gap matrix

| Surface | V1 storytelling strength | V2 candidate state | Gap / risk | Priority |
|---|---|---|---|---|
| Homepage | Strong collection/world introduction and commerce bridge. | Stronger house hero, TSRC mark, four-world rail, live products, origin, reserve portal. | V2 homepage copy is more generic; verify every hero/house claim and preserve canonical collection distinctions. | P0 |
| About | Founder portrait, quote, video/interview, origin, mission, collections, timeline, Oakland, press. | Founder portrait, controlled film, origin, five-chapter world rail, mission. | Timeline/community/press proof is compressed; film delivery depends on Media Library handoff. | P1 |
| Collections index | Four cards, lockups, descriptions, piece counts, reserve CTA. | House hero, world rail, live product strip. | V2 needs canonical one-line collection distinctions and a clear non-JS four-card fallback. | P0 |
| Signature | Gold/Oakland origin, first-rose story, lookbook, experience, founder quote. | Shared template, Golden Gate/yacht + atelier scenes, manifesto, one lookbook. | V2 config copy is shorter and needs canonical Signature voice; preserve Oakland/Bay Bridge precision. | P0 |
| Black Rose | Strong film spine, patches/lookbook, founder quote, concrete/armor story, immersive rooms. | Moon-court hero, three world scenes, atmosphere mark, lookbook. | Product/story accents and exact “color black” canon are diluted; repeated moon-court art can flatten chapters. | P0 |
| Love Hurts | Bloodline story, grandmother/family voice, Beast/rose narrative, immersive rooms. | Cathedral/chamber/cracked-rose rail, manifesto, one lookbook. | V2 “love leaves a mark” is less ownable than locked Beast/Hurts language; verify scene-to-copy pairings. | P0 |
| Kids Capsule | Daughter/legacy story, smaller-silhouette truth, tight product set, playful-but-premium world. | Four scene references, shared template, one lookbook. | Avoid unapproved campaign mechanics and generic “heir” imagery; expose product truth only from WooCommerce. | P0 |
| Pre-order | V1 has film hero, gateway, products, process, lookbook, manifesto, FAQ, email. | Portrait film, Black Rose salon hotspots, three steps, live reserve grid, service links. | V2 must retain V1’s operational clarity and bind every hotspot to a real product; no autoplay/accessibility ambiguity. | P0 |
| Shop/archive | Mature editorial product cards and collection context. | Cleaner house header, world filters, live cards. | Validate card parity, collection filters, empty states, and no story copy implying unavailable inventory. | P1 |
| PDP | Editorial media, product detail, collection context, related commerce. | Collection-aware breadcrumb/aside, WooCommerce media, fail-closed 3D. | Ensure static gallery remains complete when 3D is unavailable; verify all collection metadata is product-bound. | P0 |
| Cart/checkout | Commerce-first, branded chrome. | WooCommerce templates and safe fallback. | Keep visual restraint and ensure no immersive dependency blocks purchase. | P1 |
| Contact | Community, appointment, FAQ-like answers, response promise, location surface. | Direct “Talk to the house” image/form/service links. | V2 needs parity review for current contact channels and service promise; image must remain decorative/contextual. | P1 |
| FAQ / shipping / returns / size guide | Dedicated scan-friendly information layouts. | Generic editorial page path plus links. | Major visual and information-architecture parity gap; content truth is more important than added imagery. | P0 |
| Journal / builder / 404 / disabled WooCommerce | Mature fallback surface exists in V1. | Journal and builder templates; safe WooCommerce fallbacks. | Verify every state has real copy, focus order, and route back to the house. | P1 |

## 6. Accessibility and graceful degradation contract

Every planned visual dialogue must have an equivalent text/action dialogue:

- Lockup image has a real accessible name and a visible or screen-reader heading.
- Decorative scene art is empty-alt; meaningful founder/product images describe the subject without marketing invention.
- Horizontal worlds expose native scroll, focusable cards, previous/next controls, count/progress, and a vertical/reduced-motion reading order.
- Videos are controls-enabled, muted where applicable, never required to understand the story, and always have an approved poster/static fallback.
- Hotspots are links or buttons with visible selected state and a product name sourced from the real product record.
- `prefers-reduced-motion: reduce` removes camera/depth/scrub/reveal transforms but preserves the same chapter sequence, content, and CTA.
- Low-end/WebGL-unavailable behavior is an image/text scene, not an empty canvas. V2’s product 3D remains fail-closed and optional.
- No visual plan introduces autoplay audio.

## 7. Prioritized implementation backlog

### P0 — canon and funnel integrity

1. **Create a V2 visual truth map.** Bind each page beat to the V1 identity/copy/SOT record, V2 asset path, and WooCommerce/catalog resolver. Dependency: none. Output: reviewable mapping before copy or motion changes.
2. **Reconcile V2 collection copy.** Replace or explicitly approve generic V2 lines where they displace Signature, Black Rose, Love Hurts, or Kids Capsule canon. Dependency: item 1 and brand-owner copy approval.
3. **Complete collection-specific scene assignments.** Ensure every world chapter has a distinct approved image or is intentionally labeled as a repeated atmospheric beat; do not imply unique rooms where the asset is repeated. Dependency: item 1; no new asset generation in this pass.
4. **Make collection index and collection pages equivalent without motion.** Confirm lockup, heading, description, world links, product links, and CTA survive JS off/reduced motion/mobile. Dependency: existing V2 template/CSS implementation.
5. **Audit preorder hotspots against WooCommerce.** Prove each hotspot resolves to the product represented in the salon and that empty/preorder states cannot render false availability. Dependency: live/staging WooCommerce data and approved scene-product map.
6. **Restore service-page visual parity.** Define V2 templates/content presentation for FAQ, shipping/returns, size guide, policy, and related support routes. Dependency: canonical service copy and route inventory.
7. **PDP truth/fallback review.** Test static gallery, optional 3D gate, collection context, price/stock/preorder labels, and CTA under WooCommerce active/inactive and missing-media states. Dependency: WooCommerce staging and approved-model manifest.

### P1 — story and polish

8. **Tune homepage dialogue.** Make the hero, world rail, live products, origin, and reserve portal read as one sequence; keep first paint independent of reveal JS. Dependency: P0 items 1–4.
9. **Rebuild About as origin → film → worlds.** Preserve V1’s strongest canonical founder material while using V2’s portrait/film provenance and accessible handoff. Dependency: film Media Library delivery decision and copy approval.
10. **Carry V1’s collection film-spine rhythm into V2 rails.** Use one meaningful scene beat, one canonical line, and one real product/collection route per chapter. Dependency: P0 items 2–5.
11. **Verify mobile and low-end fallbacks.** Test reduced motion, no WebGL, slow connection, touch rails, keyboard controls, posters, empty product queries, and WooCommerce-disabled rendering. Dependency: implemented P0/P1 surfaces; browser/device test environment.
12. **Align visual tokens and lockup handling.** Confirm every collection surface uses its own SOT palette/lockup and that no unsupported font/hex/asset appears in overlays. Dependency: canonical asset map.

### P2 — optional enhancement after truth is stable

13. **Add restrained depth and reveal choreography** to hero/world/manifesto sections after motion QA proves the static sequence. Dependency: P1 item 11.
14. **Add editorial product-view enhancements** only where the product record and media contract support them. Dependency: PDP truth review.
15. **Consider additional approved editorial proof** (timeline, press, community) on About only after source, rights, and currentness are revalidated. Dependency: content-owner approval; do not infer from V1 presence.

## 8. Definition of done for the visual pass

V2 is ready for visual implementation when each major surface has one approved image/lockup identity, one canonical copy purpose, one truthful next action, and one tested static fallback. No scene is considered successful because it animates; it succeeds when the same emotional beat remains legible with motion removed and the next click still lands on the real collection, product, service, or pre-order path.

## Evidence inspected

- V1: `CLAUDE.md`, `data/collections/README.md`, `data/collections/*/{identity.json,copy.md,sot.json}`, `data/visual-manifest.json`, `front-page.php`, `template-about.php`, `template-parts/about/*`, `page-collections.php`, `template-parts/collection/page.php`, `template-parts/collection/{film-spine,feature-scroll,founder-pullquote}.php`, `template-preorder-gateway.php`, `template-contact.php`, `template-faq.php`, `template-shipping-returns.php`.
- V2: `README.md`, `ASSET-PROVENANCE.md`, `front-page.php`, `functions.php`, `template-collection.php`, `template-collections-index.php`, `template-parts/about-scroll-world.php`, `template-parts/collections-index.php`, `page.php`, WooCommerce archive/single-product templates, `assets/sot/`, and `assets/scroll-world/`.
