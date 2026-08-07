# SkyyRose V2 motion + responsive lane report

**Run:** 2026-08-06  
**Owner:** fashion-motion-responsive-engineer lane  
**Scope:** V2 page plan, imagery plan, motion adaptation, interactive scaffold, and showcase implementation.  
**Change policy:** audit only; no existing artifact was modified.

## Verdict

**BLOCKED for implementation/release; static planning review is usable.** V2 is explicitly planned-not-implemented and the interactive inventory is scaffolded-not-implemented. The showcase HTML is a readable renderer/filter, not a storefront or motion runtime. Runtime claims for motion, WebGL, touch, CTA timing, CLS/LCP/INP, or WooCommerce state are therefore UNKNOWN, not passes.

The direction is sound: garment-first composition, mobile-first decision order, native touch, poster/static fallbacks, one signature interaction per experience page, and no motion on critical purchase/service actions. The missing contract is an executable implementation with tokenized timing, cancellation, state transitions, and candidate-bound browser/performance evidence.

## Evidence read

- .wolf/memory.md (current-session design-system and evidence constraints).
- docs/design/fashion-design-system-team.md (motion/responsive ownership, WCAG/performance/evidence gates, and independent QA requirement).
- /Users/theceo/plugins/fashion-theme-team/skills/fashion-theme-team/references/design-system-contract.md (token graph, composition/component states, responsive/motion/performance budgets, fixtures).
- brain/v2/v2-page-plan.json (28 page records, CTA hierarchy, status, and desktop/mobile directions).
- brain/v2/v2-page-and-imagery-plan.md (status, responsive rules, image/crop and review-state requirements).
- brain/references/animated-prompt-pack-adaptation.md (approved motion adaptations and prohibited carries).
- brain/interactive/feature-scaffold.json (22 feature contracts, fallbacks, acceptance and proof lifecycle).
- brain/showcase/{v2-page-plan.html,v2-page-atlas.html,interactive-feature-scaffold.html,index.html,motion-prompt-pack.html} and brain/brand/skyyrose-artifact.css (current static implementation).

## Static implementation findings

| Check | Result | Evidence / implication |
|---|---|---|
| Source status | PASS (planning only) | V2 says planned/not implemented (v2-page-and-imagery-plan.md:6); JSON says planned-not-implemented; scaffold says scaffolded-not-implemented (feature-scaffold.json:7). |
| Brand/motion guardrails | PASS | Garment is protagonist; concrete structure and one rose-gold accent (v2-page-and-imagery-plan.md:8-12). Prompt adaptation rejects generic gradients, cursor trails, fake scarcity, unverified 3D, and blocking motion (animated-prompt-pack-adaptation.md:19-28,49-51). |
| CTA contract | PASS (spec only) | Rose-gold 44px primary, underlined secondary, stable explicit commerce actions with no magnetic/delay (animated-prompt-pack-adaptation.md:30-38; JSON cta_system). Showcase controls use min-height 44px (v2-page-plan.html:10, v2-page-atlas.html:15, motion-prompt-pack.html:11). |
| Responsive intent | PASS (spec only) | Product/price/fit/availability/terms/action move ahead of atmosphere; hotspots become lists; films become posters; forms remain linear and keyboard operable (v2-page-and-imagery-plan.md:47-52). |
| Reduced motion | PARTIAL | Artifact CSS resets smooth scrolling and durations under prefers-reduced-motion (brand/skyyrose-artifact.css:137-140), but no feature verifies semantic equivalence, poster substitution, or cancellation. |
| Runtime motion | UNKNOWN | Showcase scripts only create/filter cards (v2-page-plan.html:82-85, v2-page-atlas.html:110-125, interactive-feature-scaffold.html:72-80); no IntersectionObserver, RAF, gesture, media, or WebGL runtime exists in this scope. |
| Breakpoint contract | PARTIAL | Readers use independent 1000/680, 980/640, 900/620, 820, and 760px cutovers. No canonical 390/768/1440 fixture exists; 768px is split across tablet/mobile rules. |
| Overflow | UNKNOWN / masked | body and html overflow-x:hidden hide overflow in readers (v2-page-plan.html:10, interactive-feature-scaffold.html:11, motion-prompt-pack.html:10). This is not a scroll-width assertion. Tables intentionally scroll in a region and must be labeled. |
| WebGL/3D | UNKNOWN | Scaffold only describes lazy WebGL with poster, GPU budget and fallback (feature-scaffold.json:49); no scene, feature detection, context-loss handling, or poster wiring exists. |
| Evidence | BLOCKED | Scaffold requires source, desktop/mobile captures, keyboard/screen-reader trace, reduced-motion/fallback, performance, commerce truth, and independent sign-off (feature-scaffold.json:15-33). None is attached to an implemented candidate. |

## Purpose and motion token contract

Motion is permitted only when it (1) guides attention to the next chapter, (2) communicates a state transition, or (3) preserves spatial continuity. If none applies, omit it. Garment, price, fit, availability, terms, and the primary CTA always outrank atmosphere.

Use one canonical token graph (semantic names consumed by components; no page-local magic numbers):

| Token | Value | Use / limit |
|---|---:|---|
| --sr-motion-duration-fast | 160ms | Press, underline, filter state; never gate a request. |
| --sr-motion-duration-standard | 360ms | One element/state transition. |
| --sr-motion-duration-slow | 600ms | One hero/chapter entrance only; no uniform page reveal. |
| --sr-motion-ease | cubic-bezier(.16,1,.3,1) | Existing brand token (brand/skyyrose-artifact.css:35). |
| --sr-motion-distance-sm | 8px | Text/CTA continuity. |
| --sr-motion-distance-md | 16px | Chapter/card reveal. |
| --sr-motion-distance-lg | 24px | Hero entrance; do not exceed on 390px. |
| --sr-motion-stagger | 40ms | At most three related items; avoid uniform grid cascades. |
| --sr-motion-max-active | 1 section | New section cancels previous reveal; no global queue. |

Animate opacity and transform only. Layout properties belong to responsive CSS. Do not add scroll-jacking, custom cursors/trails, autoplay audio, fake countdown urgency, garment-competing particles/aurora/gradient meshes, or hover-only product facts. Magnetic CTA is an optional desktop editorial experiment only; disable it for touch, keyboard, reduced motion, checkout, account, and service (animated-prompt-pack-adaptation.md:26-28,34-38).

## Behavior matrix

| Surface / purpose | 390px compact | 768px tablet | 1440px expanded | Trigger, sequencing, cancellation | Focus, keyboard, touch | Reduced-motion / no-WebGL equivalence |
|---|---|---|---|---|---|---|
| Global shell/drawers: orient and expose service state | Compact masthead; labeled menu/search/bag; near-full-screen drawer | Compact/two-row masthead; drawer still owns focus | Wide wordmark/category nav with search/account/bag | Explicit activation; focus enters dialog; Escape/backdrop/close cancel and restore opener | Skip link first; Tab stays in drawer; visible focus; native scroll; targets at least 44px | Instant open/close with same focus path; no animated backdrop required |
| Home/collection chapter reveal: guide attention | Portrait art; linear order; rail shows next-card affordance; no sticky/parallax | Short reveal with static crop; preserve controls | One restrained text/image reveal; optional sticky editorial chapter | IntersectionObserver starts once; one active section; leaving viewport cancels pending sequence; user can skip to CTA | Real links/buttons; touch scroll native; no hover-only facts | Static image/text in final order; products/CTAs immediately present |
| Sticky story/product split: preserve continuity | Normal flow; media then evidence/CTA; never cover add-to-bag/terms | Sticky only if measured height permits; otherwise normal flow | Sticky media beside reading/decision column | Start when both columns measurable; cancel on resize, hidden tab, reduced motion, or skip | Focused content never moves under focused control; native touch scroll | Normal document flow with same captions/product links |
| Shoppable editorial hotspots: connect exact SKU | Ordered labeled product list follows image | List first; optional static coordinate markers | Labeled image hotspots plus adjacent product ledger | Activation opens normal product link; unavailable SKU explicit; no delayed reveal | Tab reaches every hotspot; labels include product/price/status; touch target at least 44px | Captioned image then product cards; all facts remain DOM-readable |
| PDP media/360: prove fit/material/movement | Poster + swipeable static gallery; no auto-rotate; first verified frame is LCP | Lazy 360 only after explicit gesture; static gallery remains | Two-up gallery; optional 36-72-frame verified viewer after activation | Lazy-load on intent/visibility; abort frame fetch/decode on route/unmount; stop on pointerup, blur, Escape | Swipe/drag without page lock; Left/Right/Home/End/Pause/Stop keyboard alternative; captions focusable | Static multi-angle gallery, alt/specs, same Add to Bag path |
| Stateful CTA: communicate request state | Full-width/stacked 44px control; button geometry stable | Same explicit stateful control; no hover-only feedback | Rose-gold primary and restrained hover underline | Activation updates loading state synchronously (at most 100ms); success/error/unavailable explicit; retry follows idempotency | Native button; disabled only while in flight; live region; focus retained/returned | No transition delay; status text/live region is feedback |
| Campaign mystery/chapter: optional discovery | Poster + transcript + Skip to shop near title; no timer pressure | Linear chapter with optional reveal | Optional desktop progress/chapter sequence with skip | User intent only; pause/abort on hidden tab, Escape, skip, reduced motion; preserve progress | Progress announced; keyboard can skip each clue; touch not sole path | Linear lookbook and exact product links; no dark-pattern timer |
| WebGL collection world (future): memorable place | Do not initialize WebGL; poster + chapter scroll | Poster first; opt-in scene only on capable device | Lazy scene after poster/LCP; DOM commerce overlay is primary | Feature-detect WebGL/GPU/memory; abort on context loss, route change, visibility, timeout | DOM heading/CTA independent of canvas; keyboard never enters canvas trap | Static poster + editorial chapter scroll + Shop CTA with same facts |
| Optional audio ritual (future): atmosphere | Off by default; explicit play + transcript | Same, with persistent pause/volume | Explicit play only; no autoplay | Start only on click/tap/keyboard; stop on navigation and reduced-motion/audio-safe preference | Play/pause/volume and transcript focusable; no audio-only information | Visual chapter/text/stills with transcript; no autoplay |

## Sequencing and cancellation requirements

1. Give every animated surface a stable data-feature-id and section ID. Use one state machine per surface: idle -> entering -> active -> exiting/cancelled.
2. Use visibility/intent triggers, never scroll-position hijacking. A reveal starts once per section; disconnect observers after completion.
3. Cancel on route change, unmount, visibilitychange, Escape/Skip, resize breakpoint change, pointer cancel, and preference change. Abort media/provider requests with AbortController; stop RAF/timers/listeners and release decoded frame buffers.
4. A pending effect never delays CTA, form submit, error, stock update, or checkout. Action and text state update immediately; motion is an after-effect.
5. Pause nonessential animation offscreen/background. No infinite loops except approved low-frequency ambient texture, removed under reduced motion.

## Breakpoint and content transformations

These are the missing executable 390/768/1440 fixtures implied by the plan’s desktop/mobile rule (v2-page-and-imagery-plan.md:47-52):

- **390px:** one column; portrait art; product/price/fit/availability/terms/primary action precede atmosphere; rails scroll only inside labeled regions; no sticky decision panel, parallax, WebGL, or hover dependency; dialogs own focus and preserve scroll position.
- **768px:** tablet composition; two-column editorial/product grids only where content fits; forms remain linear with visible next-card/chapter affordances; sticky behavior is opt-in after height/keyboard/touch checks; 360/WebGL remain poster-first and explicit.
- **1440px:** cinematic 60/40 thesis hero; four-column shop rhythm; sticky PDP decision column beside two-up media; lookbook may use one controlled sticky scene and labeled hotspots; commerce actions remain stable and DOM-readable.

Every transformation preserves section IDs, heading order, accessible names, product/SKU mapping, captions, and CTA hierarchy. Never hide essential copy or move a focused element offscreen.

## Reduced motion and fallback contract

The existing CSS preference reset is necessary but insufficient. Implement both CSS and JS preference handling. Under prefers-reduced-motion: reduce, remove parallax, stagger, clip/scale travel, autoplay/ambient loops, auto-rotate, and WebGL initialization; retain the same content, order, captions, focus path, product facts, and CTA state transitions. Static means equivalent usable composition, not an empty placeholder.

For every video/WebGL/360/provider failure, render a reserved-size poster/static image (aspect-ratio plus meaningful alt/caption), inline status where relevant, and the normal DOM commerce path. Exercise WebGL unsupported, context loss, GPU timeout, offline, decode failure, and route-abort states. The scaffold requires poster, GPU budget, keyboard path, and WebGL failure fallback (feature-scaffold.json:49).

## Budgets and measurable gates

These are proposed hard gates for implementation; record compressed transfer and device results against the same candidate ID.

| Budget / metric | Gate |
|---|---:|
| Critical CSS | At most 35 KB gzip per route; all route CSS at most 90 KB gzip |
| Initial JS | At most 80 KB gzip route-owned; WebGL/360/provider code split and lazy, at most 150 KB gzip chunk |
| Initial fonts | At most 150 KB total WOFF2; current three artifact fonts are about 137 KB uncompressed, so subset/verify rather than add another family |
| Hero/poster image | At most 200 KB at 1440; at most 120 KB at 390; intrinsic dimensions/aspect ratio required |
| Lazy editorial/SKU image | At most 250 KB each with responsive srcset/sizes; no eager gallery beyond LCP candidate |
| 360 sequence | Poster first; no frame fetch before intent; cap decoded/in-flight frames per device and abort on exit; measure peak memory |
| LCP | p75 at most 2.5s expanded and 3.0s compact mobile; poster/first verified garment is candidate |
| CLS | p75 at most 0.10 (target at most 0.05 for shell/PDP); zero shifts from media, fonts, CTA, drawer, or canvas |
| INP | p75 at most 200ms; CTA acknowledgement at most 100ms; no animation blocks input |
| Motion frame health | At least 55 FPS during approved transition on reference mobile; at most 5% dropped frames; no motion long task over 50ms |
| Page overflow | scrollWidth equals clientWidth at 390/768/1440, excluding only an explicitly labeled inner table/rail scroller |
| Touch | Every actionable target at least 44x44 CSS px; no page-lock/gesture hijack; swipe/drag has keyboard alternative |

## Exact acceptance checks

Run these against one candidate snapshot; attach command output, trace, screenshots, and PASS/FAIL/UNKNOWN to the proof bundle. Until runtime exists, runtime rows remain UNKNOWN.

1. **Source/schema:** run jq empty on both JSON contracts; assert statuses are not presented as implemented. Verify every feature has stable ID, fallback, CTA, and acceptance list.
2. **Forbidden-pattern scan:** fail production source on scroll-jack, cursor trail/custom cursor, autoplay, fake scarcity, gradient mesh, or unverified 3D; allow these terms only in reject/guardrail documentation.
3. **Viewport overflow:** at 390x844, 768x1024, and 1440x900 assert documentElement.scrollWidth equals clientWidth; separately label and test any table/rail scroller.
4. **Responsive snapshots:** capture every core page plus loading, empty, error, unavailable, long-content, keyboard, and reduced-motion state at all three viewports. Compare section order, visible CTA, product/price/fit/terms priority, crop family, and no obscured content.
5. **Reduced motion:** emulate the preference; assert no parallax/RAF/auto-rotate/WebGL, no transform travel/stagger, no autoplay audio, and equal DOM content/order/CTA reachability. Capture poster/static fallback.
6. **Keyboard/focus:** Tab from skip link through shell; open/close drawer and quick view; verify focus trap, Escape, restore-to-opener, visible focus, hotspot/360 alternatives, live-region state, and no focused element outside viewport. Run name/role/value checks.
7. **Touch:** mobile pointer test for drawer, rail, hotspot-list substitution, gallery/360 drag, and CTA. Assert native vertical scroll, no gesture dead-zone, no page overflow, 44px hit boxes, pointer cancellation, and keyboard parity.
8. **Sequencing/cancellation:** trigger a reveal, immediately scroll away/navigate/hide tab/resize; assert observer, timers, RAF, listeners, media fetches, and decoded frame buffers are cancelled/released. Repeat with reduced motion toggled during entry.
9. **WebGL failure:** stub canvas context unavailable and induce context loss/timeout/offline; assert poster, status, heading, product facts, and Shop CTA remain visible and keyboard reachable. Measure no canvas request on 390/reduced motion before explicit opt-in.
10. **CTA timing/state:** timestamp activation to loading text/disabled state (at most 100ms), success/error/unavailable announcement (at most 1s after response), duplicate prevention/idempotency, and focus retention. Checkout/place-order never waits for motion.
11. **Core Web Vitals:** run Lighthouse/field-style trace on compact and expanded profiles; record LCP/CLS/INP, long tasks, transfer sizes, decode time, memory, and dropped frames. Fail the budget table; missing telemetry is UNKNOWN.
12. **Evidence binding:** data-feature-id, source/SKU/variation, browser trace, desktop/mobile/reduced-motion/fallback screenshots, commerce event log, and independent visual/accessibility/performance/security review share one candidate ID before release-ready (feature-scaffold.json:26-33).

## Handoff blockers

- Build the V2 surfaces and motion state machines; current showcase is documentation, not implementation.
- Consolidate breakpoint tokens and add first-class 390/768/1440 fixtures; current reader CSS has divergent 620/640/680/760/820/900/980/1000px cutovers.
- Add executable reduced-motion, touch, focus, cancellation, WebGL, and poster/static fallback paths.
- Add responsive image dimensions/crop manifests and route budgets; verify the three font files against the at-most-150 KB initial-font gate.
- Produce candidate-bound browser/performance evidence and obtain independent visual QA red-team verdict. The motion lane does not self-certify pixels.

**Final lane status: BLOCKED pending implementation and evidence.**

