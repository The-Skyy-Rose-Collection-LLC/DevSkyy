# SkyyRose V2 motion + responsive repair contract

**Run:** 2026-08-06  
**Owner:** `fashion-motion-responsive-engineer`  
**Contract:** [`motion-responsive-contract.json`](motion-responsive-contract.json)  
**Disposition:** **BLOCKED for implementation/release; repair contract is ready for a builder.**

This is a remediation handoff, not a claim that V2 has runtime motion. The V2 pages,
interactive inventory, and showcase are still planning/static artifacts. Browser,
touch, WebGL, Core Web Vitals, WooCommerce, and pixel claims remain `UNKNOWN` until a
candidate-bound implementation produces the required evidence bundle. Do not promote
the static showcase as a storefront or motion runtime.

## Audit gaps converted to enforceable fields

| Gap | Contract location | Repair rule | Proof required |
|---|---|---|---|
| No canonical 390/768/1440 behavior | `behavior_matrix[*].responsive` | Every surface declares layout, crop, action order, and motion at each viewport. 390 is one-column and poster-first; 768 is tablet and content-fit; 1440 may use authored sticky/cinematic composition. | Fresh `390x844`, `768x1024`, and `1440x900` captures for default and critical states; section order, CTA visibility, crop, and no-obscured-content assertions. |
| Motion purpose was not machine-bound | `purpose`, `tokens`, `prohibited_patterns` | Motion may guide attention, communicate state, or preserve continuity only. Garment, price, fit, availability, terms, and CTA outrank atmosphere. | Feature census with `data-feature-id`, approved purpose, token usage, and forbidden-pattern scan. |
| No sequencing or cancellation contract | `state_machine` | Use `idle -> entering -> active -> exiting/cancelled/fallback`; one active reveal section. Cancel on route, unmount, hidden tab, resize, Escape/skip, pointer cancel, preference change, timeout, and context loss. Clean observers, timers, RAF, listeners, requests, and frame buffers. | Browser trace that interrupts every state; asserts no stale callback, request, listener, RAF, or decoded buffer remains. |
| Reduced motion was only a CSS reset | `reduced_motion` | Implement CSS and JS preference handling. Remove parallax, stagger, clip/scale travel, loops, auto-rotate, WebGL initialization, and audio autoplay while preserving the same DOM, facts, focus path, order, and CTA states. | Emulated `prefers-reduced-motion: reduce` trace and paired capture; equal DOM/order/CTA reachability and no prohibited runtime work. |
| WebGL/360 fallback was descriptive only | `no_webgl_fallback` | Never initialize WebGL on 390; poster first and capability-gated opt-in at 768; lazy after poster/LCP at 1440. Unsupported, context-loss, GPU timeout, offline, decode, provider, abort, and reduced-motion states render reserved poster/static media plus DOM commerce. | Stubbed canvas/provider failure trace; poster, alt/caption, status, product facts, and Shop/Add to Bag remain visible and keyboard reachable. |
| Focus and touch parity absent | `focus_keyboard_touch_contract` and each matrix row | WCAG 2.2 AA floor; skip link, visible focus, modal trap/Escape/restore, 44px targets, native scroll, pointer cancellation, no page-lock/gesture hijack, no hover-only facts, and keyboard alternatives for drag/swipe. | Keyboard/screen-reader and mobile pointer traces; target-size, overflow, focus visibility, live-region, and focus-restoration assertions. |
| Performance budgets were not candidate-bound | `budgets` | Gate CSS, JS, fonts, images, LCP, CLS, INP, frame health, long tasks, overflow, and touch targets. Intrinsic media dimensions and responsive `srcset`/`sizes` are mandatory. | Lighthouse/browser trace with transfer/decode/memory/frame telemetry at compact, tablet, and expanded profiles; missing telemetry is `UNKNOWN`. |
| Evidence classes were not attached to one candidate | `evidence_artifacts` | Source, responsive captures, interaction, reduced-motion, fallback, performance, commerce truth, and independent reviews share `candidate_id` + stable `data-feature-id`. `UNKNOWN`, stale, missing, or self-approved evidence fails closed. | Candidate directory/manifest with all required artifacts and reviewer records. |

## Required behavior decisions

The JSON contract is the source of truth for the complete matrix. The following
decisions are hard constraints during implementation:

- **390px:** one column; portrait/static art; product, price, fit, availability,
  terms, and primary CTA precede atmosphere. No sticky decision panel, parallax,
  WebGL, hover dependency, or page-locking gesture. Use labeled inner rail/table
  scrollers only when necessary.
- **768px:** tablet composition; use two columns only when content fits and measured
  height does not obscure focus. Keep forms and chapters linear, use visible next/skip
  affordances, and keep 360/WebGL poster-first and opt-in.
- **1440px:** authored 60/40 thesis hero, four-column shop rhythm, and (where measured)
  one controlled sticky scene. PDP decision content stays DOM-readable beside media;
  hotspots always have an adjacent product ledger.
- **Every CTA:** native control, stable geometry, explicit loading/success/error/
  unavailable state, live-region announcement, idempotency, and acknowledgement
  within 100ms. No request, checkout, place-order, stock, or terms state waits for
  motion.
- **Every animated surface:** stable `data-feature-id` and section ID; animate only
  `opacity`/`transform`; use the canonical duration/ease/distance tokens; at most one
  active reveal section and no uniform grid/page cascade.
- **Audio:** off by default; explicit play/pause/volume and transcript; stop on
  navigation or reduced-motion/audio-safe preference. Autoplay is prohibited.

## Implementation and proof sequencing

1. Add the contract and stable feature/section IDs to the implementation. Keep
   current status `planned-not-implemented` until the first candidate is rendered.
2. Implement static DOM order, responsive CSS, intrinsic media boxes, and stateful
   CTAs before adding enhancement motion. Run the 390/768/1440 overflow and focus
   checks on the static path.
3. Add one state machine per feature. Start only on visibility or explicit intent;
   cancel and clean up through the events in `state_machine.cancellation_events`.
4. Add CSS + JS reduced-motion handling and verify preference changes during an active
   entry. The result must be an equivalent usable composition, not an empty state.
5. Add poster-first, capability-gated WebGL/360/provider enhancement. Exercise every
   failure state in `no_webgl_fallback`; never route commerce through canvas.
6. Capture responsive, keyboard/touch, reduced-motion, fallback, and performance
   evidence against one candidate ID. Add SKU/variation/price/availability/event
   records where a feature touches commerce.
7. Hand the bundle to independent visual QA, accessibility, performance, and security
   reviewers. The motion lane cannot approve its own pixels. Any missing, stale,
   skipped, timed-out, or unavailable evidence remains `UNKNOWN` and blocks release.

## Measurable gates

The numeric gates are machine-readable in `budgets`; the minimum release checks are:

- `documentElement.scrollWidth === clientWidth` at 390, 768, and 1440, with only
  explicitly labeled inner table/rail overflow.
- LCP p75 <= 3.0s compact, <= 2.8s tablet, <= 2.5s expanded; CLS p75 <= 0.10
  (target <= 0.05 for shell/PDP); INP p75 <= 200ms; CTA acknowledgement <= 100ms.
- Critical CSS <= 35 KB gzip; route CSS <= 90 KB gzip; route-owned initial JS <= 80
  KB gzip; lazy WebGL/360/provider chunk <= 150 KB gzip; initial WOFF2 <= 150 KB.
- Hero/poster <= 120 KB at 390, <= 160 KB at 768, <= 200 KB at 1440; lazy editorial
  or SKU image <= 250 KB with intrinsic dimensions and responsive sources.
- Approved transitions sustain >= 55 FPS, <= 5% dropped frames, and no motion long
  task over 50ms on the reference mobile profile.
- All actionable touch targets are >= 44x44 CSS px and every gesture has a keyboard
  equivalent.

## Required artifact manifest

At minimum, each candidate directory must contain the artifacts named in
`evidence_artifacts.required`:

```text
candidate.json                 # candidate_id, git SHA, feature/page IDs, source refs
source-provenance.json         # asset/SKU/variation/rights/status mapping
responsive/390x844/*.png       # default + critical states
responsive/768x1024/*.png
responsive/1440x900/*.png
interaction/browser-trace.json # keyboard, focus, touch, CTA, cancellation
accessibility/keyboard.json
accessibility/screen-reader.json
motion/reduced-motion.json
fallback/no-webgl.json
performance/lighthouse.json    # LCP, CLS, INP, bytes, long tasks, frames, overflow
commerce/events.json           # SKU, variation, price, stock, idempotency, CTA states
review/independent-signoff.json
```

File names may vary by runner, but the fields and candidate binding may not. A
planning capture, a static reader, or a successful JSON parse is not implementation
proof.

## Current handoff status

- Contract: **available** at `brain/v2/motion-responsive-contract.json`.
- Static audit: useful as context in `team-run-motion.md`; unchanged by this repair.
- Runtime implementation: **UNKNOWN / not present**.
- Browser, touch, reduced-motion, WebGL fallback, performance, commerce, and
  independent visual approval: **BLOCKED / no candidate evidence**.
- Production theme files, `scripts/verify.sh`, and `v2-page-plan.json`: **not changed**.

The next owner may implement against this contract, then return a candidate-bound
proof bundle for independent review. Until that happens, release remains blocked.
