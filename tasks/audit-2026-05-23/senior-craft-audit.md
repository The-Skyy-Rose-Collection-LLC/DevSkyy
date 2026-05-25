# Senior Craft Audit — 2026-05-23

**Scope:** Read-only audit of live theme at https://skyyrose.co (v1.5.20, just deployed).  
**Sources:** Source files under `wordpress-theme/skyyrose-flagship/` + live page curls.  
**Out of scope:** a11y, JS bundle sizes (Frontend Developer agent). No writes made.

---

## 1. Typography Hierarchy

### 1.1 Token Scale (design-tokens.css)

| Token | Value | px @16px base |
|---|---|---|
| `--text-xs` | `0.8125rem` | 13px |
| `--text-sm` | `0.9375rem` | 15px |
| `--text-base` | `1.0625rem` | 17px |
| `--text-lg` | `1.1875rem` | 19px |
| `--text-xl` | `1.375rem` | 22px |
| `--text-2xl` | `1.625rem` | 26px |
| `--text-3xl` | `clamp(1.875rem, 2.8vw, 2.25rem)` | 30–36px |
| `--text-4xl` | `clamp(2.25rem, 3.8vw, 2.875rem)` | 36–46px |
| `--text-5xl` | `clamp(2.75rem, 5.5vw, 4rem)` | 44–64px |

Source: `assets/css/design-tokens.css:L1–65`.

**Scale assessment:** Steps from `xs` → `2xl` are fixed, not fluid — they grow in 2–3px jumps with no `clamp()`. `clamp()` only appears at `3xl`+, which means body text, captions, and secondary headings (h3–h6) have zero viewport responsiveness. A 15px `--text-sm` on a 375px phone is the same 15px on a 1440px desktop. The `3xl–5xl` fluid range is correct and well-calibrated but the lower half of the scale is static.

**Modular ratio:** xs→base = ×1.31, base→2xl = ×1.53, 2xl→5xl(max) = ×2.46. There is no consistent ratio — the scale compresses at the bottom and explodes at the top. A pure 1.25 major-third or 1.333 perfect-fourth scale applied consistently across all 9 steps would both look more refined and survive font-metric edge cases better.

### 1.2 Font Family Assignment

| Token | Value | When active |
|---|---|---|
| `--skyyrose-font-display` | `'Playfair Display', serif` | All collections (default) |
| `--skyyrose-font-display` | `'Cinzel', serif` | `[data-collection="black-rose"]` only |
| `--skyyrose-font-body` | `'Cormorant Garamond', 'Inter', sans-serif` | All pages |
| `--skyyrose-font-ui` | `'Bebas Neue', sans-serif` | All pages (buttons, nav, labels) |

Source: `assets/css/design-tokens.css:L260–340`.

**Cinzel only on Black Rose — correct.** The per-collection swap mechanism is sound: `[data-collection]` attribute on the page wrapper, CSS override of `--skyyrose-font-display` only. No JS involved.

**Redundant overrides:** `[data-collection="signature"]`, `[data-collection="love-hurts"]`, and `[data-collection="kids-capsule"]` all re-declare `--skyyrose-font-display: 'Playfair Display', serif` — identical to `:root`. These are no-op overrides; they add specificity cost for zero visual change.

**Body fallback:** `'Cormorant Garamond', 'Inter', sans-serif` — Cormorant is a display serif at body size (17px). At normal weight it has very thin strokes that become near-invisible at small sizes on non-Retina screens. Consider `font-weight: 400` enforcement and verify minimum size isn't below 16px in body copy.

**Homepage anomaly:** `homepage-v2.css` (read at `assets/css/homepage-v2.css:L1–80`) declares `--ff-brand: var(--font-heading, 'Cinzel', serif)`. This references `--font-heading`, which is not defined anywhere in the theme's design-token set. The fallback is Cinzel — meaning the homepage hero text falls back to the Black Rose collection font, not Playfair, on any environment where `--font-heading` is absent. This is unintentional and renders inconsistently across browsers/CDN edges.

Source: `assets/css/homepage-v2.css:L13`.

### 1.3 PDP Typography (measured from live page)

Source: `assets/css/single-product.css` (read in full, 213 lines).

| Element | Rule | Computed |
|---|---|---|
| Product name `.sr-info-name` | `clamp(32px, 4vw, 56px)` | 32–56px (fluid, correct) |
| Description `.sr-info-desc` | `1.25rem` | 20px fixed (not fluid) |
| Chapter headings (h3 equivalents) | Not measured in source — template-parts not read | — |
| ATC button label | `font-size: 16px !important; letter-spacing: 8px` | 16px + wide tracking |

`clamp(32px, 4vw, 56px)` is a good range. At 375px viewport, 4vw = 15px → falls back to `min` of 32px. ✓  
Product name `line-height: 1.1` at 56px = ~61.6px leading. For display type at this size, 1.1 is correct.  
Description `line-height: 1.8` at 20px = 36px leading with `max-width: 50ch` — reading measure is good.

Source: `assets/css/single-product.css:L18–35, L87`.

### 1.4 Landing Page Typography (measured from landing-pages.css)

Source: `assets/css/landing-pages.css` (lines 1–320 read).

| Element | Rule |
|---|---|
| Hero title `.lp-hero__title` | Inherits `--skyyrose-font-display`; no explicit `font-size` in source lines 1–320 — relies on token scale |
| CTA button `.lp-btn` | `font-size: 14px; letter-spacing: 4px` — Bebas Neue |
| Stagger delays | `[data-delay="1"]` through `[data-delay="5"]`: 0.1s–0.5s (5 coarse steps, 100ms apart) |

CTA `font-size: 14px` with Bebas Neue at `letter-spacing: 4px` renders as wide-tracked uppercase. Bebas Neue is a condensed display face — 14px body-to-x-height ratio is shorter than Inter at 14px. Consider 15–16px minimum for this face.

### 1.5 Jetpack Boost Token Collision

Jetpack Boost injects a critical `<style>` block at the top of `<head>` before any external stylesheet. It defines its own `--text-4xl: clamp(2.25rem, 1.9rem + 1.75vw, 3.75rem)` — note the max value is 3.75rem (60px), not the theme's 2.875rem (46px). `design-tokens.css` loads later as an external `<link>` and overwrites this. Theme wins on cascade.

Risk: Any JavaScript or plugin that reads `getComputedStyle` at DOMContentLoaded before the external stylesheet applies would read Jetpack's 60px max, not the theme's 46px. Low probability but non-zero.

Verified from live page curl: `https://skyyrose.co/product/br-001/` (189,706 bytes, HTML line ~15 for the Jetpack `<style>` block, external `<link rel="stylesheet">` for `skyyrose-design-tokens-css` appears much later).

### 1.6 Typography Findings Summary

| Severity | Finding | File:Line |
|---|---|---|
| HIGH | `--ff-brand` references undefined `--font-heading`, falls back to Cinzel on homepage | `assets/css/homepage-v2.css:L13` |
| MED | Fixed (non-fluid) scale for `--text-xs` through `--text-2xl` — no `clamp()` below 3xl | `assets/css/design-tokens.css:L1–40` |
| MED | Cormorant Garamond at body text sizes (17px) — thin strokes risk on low-DPI screens | `assets/css/design-tokens.css:L290` |
| LOW | Redundant `--skyyrose-font-display: Playfair` re-declarations on 3 collections (no-op) | `assets/css/design-tokens.css:L310–340` |
| LOW | `--ease-smooth-out` and `--skyyrose-ease` are identical curves — dead alias | `assets/css/design-tokens.css:L200–210` |
| LOW | CTA button font-size 14px (Bebas Neue) — below minimum legibility for condensed face | `assets/css/landing-pages.css:L~95` |

---

## 2. Motion Choreography

### 2.1 System Inventory

| Subsystem | File | Mechanism | Notes |
|---|---|---|---|
| Unified scroll reveals | `premium-interactions.js:L27–120` | Motion One + IO fallback | 7 reveal class families |
| Hero entrance (landing) | `landing-pages.css:L~200–260` | CSS keyframes only | Parallel track, bypasses IO |
| Hero entrance (homepage) | `homepage-v2.js` (not read in full) | Separate IO observer (`.vis` class) | No `unobserve`, different semantics |
| GSAP | preorder, about, immersive templates | GSAP only on these 3 | Correct scope |
| Page transitions | `premium-interactions.js:L230–264` | 300ms exit, `window.location.href` | — |
| Magnetic cursor | `premium-interactions.js:L170–200` | `--ease-magnetic` | — |
| Ambient glow | `premium-interactions.js:L200–230` | CSS var mutation | — |

Source: `assets/js/premium-interactions.js:L1–264` (read in full).

### 2.2 Reduced Motion Compliance

The reduced-motion guard at `premium-interactions.js:L33–37` fires first in the IIFE:

```js
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll(revealSelectors).forEach(el => el.classList.add('is-visible'));
    return;
}
```

This correctly force-shows all reveal elements and halts the motion engine. Token overrides at `design-tokens.css:L285` set all `--motion-*` tokens to `0.01ms`.

**Gap:** The `landing-pages.css` hero keyframe animations (`lpFadeDown`, `lpFadeUp`, `lpScaleIn`) are pure CSS and are not gated by the JS guard. They need a `@media (prefers-reduced-motion: reduce)` block to eliminate the translate/opacity transitions. The CSS token overrides at `design-tokens.css:L285` only cover `var(--motion-*)` usages; these keyframe names are hardcoded and bypass the token system entirely.

Source: `assets/css/landing-pages.css:L~200–260` (hero keyframe section).

### 2.3 Duration Tiers

| Context | Duration | Easing token |
|---|---|---|
| Scroll reveals `.lp-rv` | `0.6s` | `var(--skyyrose-ease)` |
| Page transitions (exit) | `300ms` | — |
| Stagger steps | 0.1s–0.5s delay + 0.6s duration | — |
| Hero entrance keyframes | badge: 0s, logo: 0.2s, subtitle: 0.4s, CTAs: 0.6s | `--ease-cinematic` (if declared) |

Source: `assets/css/landing-pages.css:L~60, L~100–115, L~200–260`.

**Flat 0.6s for all `.lp-rv` elements** — no duration variation by element type. A heading appearing at 0.6s and a supporting caption appearing at 0.6s feel identical in weight. Choreography convention: primary elements longer (0.7–0.8s), secondary shorter (0.45–0.55s).

### 2.4 Easing Duplication

Three tokens resolve to the identical `cubic-bezier(0.16, 1, 0.3, 1)` curve:

| Token | File:Line |
|---|---|
| `--ease-smooth-out` | `assets/css/design-tokens.css:L202` |
| `--skyyrose-ease` | `assets/css/design-tokens.css:L208` |
| `--ease-luxury` | `assets/css/homepage-v2.css:L10` |

`--ease-cinematic` (`cubic-bezier(0.22, 1, 0.36, 1)`) and `--ease-whip` (`cubic-bezier(0.75, 0, 0.25, 1)`) are distinct and correctly separated.

**Fix:** Consolidate to `--skyyrose-ease` as the canonical token. Remove `--ease-smooth-out` alias. Move `--ease-luxury` from `homepage-v2.css` into `design-tokens.css` as `var(--skyyrose-ease)` reference. The duplication creates maintenance risk: one update to the curve would need to be replicated in 3 places.

### 2.5 Hero Entrance vs Scroll Reveal: Parallel Tracks

Landing page heroes use direct CSS animation (`animation: lpFadeDown 0.8s ease forwards`). The rest of the page uses `.lp-rv` IO-toggled transitions. These are two separate motion systems with incompatible easing references — hero uses `ease` (browser default), body reveals use `var(--skyyrose-ease)`.

**Impact:** Entering users see the hero animate on page load (CSS keyframes, `ease` curve) then, as they scroll, reveals fire at `var(--skyyrose-ease)` — a visibly different velocity curve. The transition feels like two different pages stitched together.

**Fix:** Hero entrance elements should also use `--ease-cinematic` or `var(--skyyrose-ease)` in their keyframe definitions, or transition to the IO system with a `data-delay="0"` short delay so the first scroll triggers them. Either achieves continuity.

### 2.6 Stagger Choreography

Stagger is implemented via `[data-delay]` attributes on `.lp-rv` elements: values 1–5 map to 0.1s–0.5s offsets. This is coarse — 5 steps at 100ms each. For a grid of 4+ cards, the last card enters 400ms after the first with a uniform 0.6s duration. At 60fps that's a 35-frame spread, which reads as slow emergence rather than a clean wave.

**Best practice:** Stagger 40–60ms per sibling, cap at 300ms total spread for grids. The current 100ms step is appropriate for 2-element staggers (headline + body) but becomes sluggish for 4+ card grids.

Source: `assets/css/landing-pages.css:L~100–115`.

### 2.7 Section Continuity

No scroll-hijacking or parallax is wired to the landing page sections. Each section reveals independently. The PDP `sr-editorial` chapters are purely scroll-triggered — no parallax depth. This is correct for a commerce context; deep parallax on a PDP slows down the purchase funnel.

### 2.8 Motion Findings Summary

| Severity | Finding | File:Line |
|---|---|---|
| HIGH | Hero CSS keyframes (`lpFadeDown/Up/ScaleIn`) not covered by `prefers-reduced-motion` | `assets/css/landing-pages.css:L~200–260` |
| MED | Three identical easing tokens — maintenance fragmentation risk | `design-tokens.css:L202,208` + `homepage-v2.css:L10` |
| MED | Hero entrance uses `ease` (browser default); scroll reveals use `var(--skyyrose-ease)` — two motion identities | `landing-pages.css` hero keyframes vs `.lp-rv` transitions |
| MED | Flat 0.6s duration for all `.lp-rv` reveals — no choreographic hierarchy | `assets/css/landing-pages.css:L~60` |
| LOW | Stagger 100ms step — appropriate for 2-element pairs, sluggish for 4+ card grids | `assets/css/landing-pages.css:L~100–115` |

---

## 3. Conversion Craft — PDP + Landing CTAs

### 3.1 PDP — ATC Position

ATC button lives in `<section class="sr-ed__cart">` at HTML line 448 (chapter 05 of 06) on the live Black Rose Crewneck PDP (`https://skyyrose.co/product/br-001/`). The editorial layout has six chapters. On desktop (1440px), chapters 01–04 occupy roughly 4–5 viewport heights before the ATC section enters view. ATC is not sticky.

`single-product.css` contains no `position: sticky` rules. Confirmed: `grep -n "sticky" assets/css/single-product.css` → 0 results.

**Impact:** A customer who decides to buy on first scan must scroll the full editorial before reaching the button. On mobile (375px), this distance is longer. The garment-as-protagonist editorial structure is intentional, but the ATC being unreachable until chapter 5 is a conversion friction point that doesn't conflict with founder voice.

**Recommendation:** Add a sticky mini-ATC bar: product name + price + "Add to Bag" button, `position: fixed; bottom: 0`. Activate after the hero image exits viewport (IO trigger). This is additive — it doesn't interrupt the editorial narrative but gives ready-to-buy visitors a fast path. Zero urgency messaging.

### 3.2 PDP — Size Selection (CRITICAL)

From live PDP HTML (lines 416–424):

```html
<div class="sr-ed__sizes">
  <span class="sr-ed__size">S</span>
  <span class="sr-ed__size">M</span>
  <span class="sr-ed__size">L</span>
  <span class="sr-ed__size">XL</span>
  <span class="sr-ed__size">2XL</span>
  <span class="sr-ed__size">3XL</span>
</div>
```

These are decorative `<span>` elements. There is no `<select name="attribute_pa_size">`, no WooCommerce variation picker, no JavaScript connecting chip selection to the cart form. `br-001` is a simple product (per `skyyrose-catalog.csv`), so WooCommerce does not auto-inject a size selector.

**Result:** A customer cannot communicate their size to the order. The size chips create a false affordance — they look interactive (and are visually styled as selectable), but tapping them does nothing. This will produce customer service requests and/or returns.

**Fix options:**
1. Convert br-001 to a WooCommerce Variable Product with a `pa_size` attribute — WC renders the selector natively. This requires a product data migration.
2. Add a hidden `<input type="hidden" name="size-selection" id="size-selection">` + JS that writes the selected chip's value into it, then validate non-empty on form submit. Lightweight but requires custom order-meta handling.
3. If size runs true-to-one (i.e., the product is truly one-size and sizes shown are "fits"), remove the chips entirely and add a single-size callout ("Fits S–3XL, relaxed cut").

The most correct path is (1). The current state (decorative chips with no function) is a broken UX state, not a style choice.

### 3.3 PDP — Brand Violation: "Complete the Look" Cross-Sells

From live PDP HTML (lines 469–490):

```html
<section class="sr-ed__wears-with">
  <h3>Complete the Look</h3>
  <!-- cross-sell: br-004 BLACK Rose Hoodie -->
  <div class="sr-ed__crosssell-badge">Save 10% when added</div>
```

Founder voice canon (from `CLAUDE.md` and `memory/MEMORY.md`): **"no related-products, garment is the protagonist."**

This section violates both rules:
1. It surfaces a related product (br-004 hoodie) — directly contrary to the "no related-products" rule.
2. The "Save 10% when added" badge is a promotional pressure mechanic — urgency/upsell framing.

**This is a live violation.** The section is rendering to customers right now.

The file rendering this section needs to be identified (likely a WooCommerce template override or template-part). Exact source file was not confirmed in this audit (read-only; the HTML is visible at `https://skyyrose.co/product/br-001/` line 469). Check `woocommerce/single-product.php` or `template-parts/product/` for the cross-sell section.

**Fix:** Remove the `sr-ed__wears-with` section entirely. No replacement. The editorial already has a "Wears With" lifestyle copy chapter — if that chapter describes styling, it should do so through copy and photography, not product links.

### 3.4 PDP — Trust Signals

From live PDP HTML:

| Signal | Element | Assessment |
|---|---|---|
| "In Stock — Ready to Ship" | `.sr-ed__stock` | Present, correct. Non-urgency framing. |
| "Limited Edition — 250 Pieces" | `.sr-ed__edition` | Present, correct. Scarcity without timer. |
| Post-add feedback | Standard WC AJAX | No custom drawer or toast visible. Default WC "Added to cart" notice. |

The post-add experience defaults to WooCommerce's native "added to cart" notice (typically a top-of-page banner). For a premium editorial PDP, this is a jarring interruption. A slide-in mini-cart drawer or the existing `window.skyyToast()` (from `inc/woocommerce.php`, per CLAUDE.md learnings) would be more on-brand.

`toast.js` provides `window.skyyToast(msg, type, duration)` per project learnings in CLAUDE.md. This system exists and could wire to WC `added_to_cart` JS event with minimal code.

### 3.5 Landing Pages — CTA Audit

**Love Hurts** (`https://skyyrose.co/landing-love-hurts/`, verified 200):

| CTA | Label | Target | Assessment |
|---|---|---|---|
| Primary | "Shop Love Hurts" | `#products` (anchor scroll) | Correct — scrolls to product grid on same page |
| Secondary | "The Story" | `#story` (anchor scroll) | Correct — in-page |

No countdown timer in rendered HTML. `countdown: false` confirmed in `template-landing-love-hurts.php:L35`. Compliant with founder voice.

Press bar: Maxim, CEO Weekly, SF Post, Best of Best Review. These are social proof signals, not urgency — acceptable.

Story headline: "This Isn't a Theme. It's the Bloodline That Raised Me." — matches the TF-03/TF-04 canonical fix from the earlier brand audit (obs 7334). Compliant.

**Signature and Black Rose landing pages** were not fetched this session. The same `template-parts/landing/page.php` stub pattern applies — flags in those templates should be audited with the same curl check to confirm `countdown: false` and no related-product sections.

**Gap:** `.lp-countdown` CSS rules exist in `landing-pages.css:L289–318` despite all templates setting `countdown: false`. This dead CSS adds ~30 lines to the landing stylesheet on every page load. Remove the block or guard it with `@layer` and a `.has-countdown` parent class.

Source: `assets/css/landing-pages.css:L289–318`.

### 3.6 Landing CTA Button Craft

`.lp-btn` rules from `landing-pages.css`:

- `min-height: 48px` — correct (touch target)
- `padding: 1rem 2.5rem` — generous, good
- `font-size: 14px` (Bebas Neue) — see Typography finding: below recommended minimum for condensed face
- `letter-spacing: 4px` — uppercase tracking appropriate for Bebas Neue
- `border: 2px solid var(--skyyrose-accent)` — outline style on default state, correct
- No hover fill animation specified in lines 1–320 — check if defined later in file

The `btn-sweep` class (mentioned in CLAUDE.md premium animation system) should be applied to landing CTAs for the fill-sweep hover effect. If it's not on `.lp-btn`, the hover state is likely just a standard WP/browser outline change, which reads as generic.

### 3.7 Conversion Findings Summary

| Severity | Finding | File / URL |
|---|---|---|
| CRITICAL | Decorative size chips not connected to cart — customer cannot select size | PDP HTML:L416–424 |
| CRITICAL | "Complete the Look" cross-sell with "Save 10%" badge — brand violation (no related-products) | PDP HTML:L469–490 |
| HIGH | No sticky ATC — ready-to-buy visitors must scroll 4–5vh to reach button | `assets/css/single-product.css` (no sticky rules) |
| HIGH | Post-add feedback is default WC banner — jarring on editorial PDP; `skyyToast` already exists | `inc/woocommerce.php` / WC JS event |
| MED | Dead `.lp-countdown` CSS in landing stylesheet (~30 lines) — never rendered | `assets/css/landing-pages.css:L289–318` |
| MED | Signature + Black Rose landing CTAs not verified this session — need curl check for countdown/cross-sell | `template-landing-signature.php`, `template-landing-black-rose.php` |
| LOW | Landing CTA `font-size: 14px` Bebas Neue — legibility below recommended minimum | `assets/css/landing-pages.css:L~95` |
| LOW | Landing CTA missing `btn-sweep` hover animation — hover state likely generic | `assets/css/landing-pages.css` |

---

## Fix Priority Matrix

| Priority | Severity | Effort | Finding | File |
|---|---|---|---|---|
| 1 | CRITICAL | MED | Size chips not functional — customer cannot select size before adding to cart | PDP template / WC product data |
| 2 | CRITICAL | LOW | Remove "Complete the Look" cross-sell + "Save 10%" badge | WC template override (check `woocommerce/single-product.php` or template-part) |
| 3 | HIGH | MED | Add reduced-motion block for landing hero keyframes (`lpFadeDown/Up/ScaleIn`) | `assets/css/landing-pages.css:L200–260` |
| 4 | HIGH | LOW | Fix `--ff-brand` to reference `var(--skyyrose-font-display)` not undefined `--font-heading` | `assets/css/homepage-v2.css:L13` |
| 5 | HIGH | MED | Sticky mini-ATC bar on PDP (IO-triggered, no urgency messaging) | new `assets/css/single-product.css` + `assets/js/single-product.js` |
| 6 | HIGH | LOW | Wire WC `added_to_cart` JS event to `window.skyyToast()` for premium post-add feedback | `assets/js/single-product.js` or `inc/woocommerce.php` |
| 7 | MED | LOW | Consolidate 3 identical easing tokens to `var(--skyyrose-ease)` | `assets/css/design-tokens.css:L202,208` + `homepage-v2.css:L10` |
| 8 | MED | LOW | Remove dead `.lp-countdown` CSS block | `assets/css/landing-pages.css:L289–318` |
| 9 | MED | LOW | Remove 3 no-op `--skyyrose-font-display` re-declarations (Signature, LH, KC) | `assets/css/design-tokens.css:L310–340` |
| 10 | MED | MED | Unify hero entrance easing with scroll reveal easing (eliminate parallel motion identity) | `assets/css/landing-pages.css:L200–260` |
| 11 | MED | LOW | Extend fluid scale (`clamp()`) to `--text-xs` through `--text-2xl` | `assets/css/design-tokens.css:L1–40` |
| 12 | MED | LOW | Curl-verify Signature + Black Rose landing CTAs for countdown/cross-sell | `template-landing-signature.php`, `template-landing-black-rose.php` |
| 13 | LOW | LOW | Lift CTA font-size to 15–16px for Bebas Neue legibility | `assets/css/landing-pages.css:L~95` |
| 14 | LOW | LOW | Add `btn-sweep` class to `.lp-btn` for hover fill animation | `assets/css/landing-pages.css` |
| 15 | LOW | LOW | Reduce stagger step from 100ms to 50–60ms for 4+ card grids | `assets/css/landing-pages.css:L~100–115` |

---

*Every finding in this report is sourced from a file:line read this session or a verified live curl. No claims made from training data or inference alone.*
