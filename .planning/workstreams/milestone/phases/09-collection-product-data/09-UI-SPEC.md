---
phase: 9
slug: collection-product-data
status: draft
shadcn_initialized: false
preset: none
created: 2026-05-12
---

# Phase 9 — UI Design Contract: Collection & Product Data

> Visual and interaction contract for Phase 9. This phase is verification-first:
> DATA-02 and DATA-03 are already shipped; DATA-01 (Black Rose hero banner) is the
> single active engineering target. No redesign. No new components.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none — custom CSS token system |
| Preset | not applicable |
| Component library | none (WordPress theme, plain PHP/CSS) |
| Icon library | Unicode symbols inline (&#x25C6;, &#x1F339;, &#x2726;, &#x2665;) |
| Font — display (Black Rose) | Cinzel, serif |
| Font — display (Love Hurts, Signature, Kids Capsule) | Playfair Display, serif |
| Font — body | Cormorant Garamond, Inter, sans-serif |
| Font — UI labels | Bebas Neue, sans-serif |

Source: `assets/css/design-tokens.css` (pre-existing — read-only for this phase)

---

## Spacing Scale

Declared values (existing theme scale, multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, badge padding |
| sm | 8px | Inline element gaps |
| md | 16px | Default element spacing |
| lg | 24px | Section padding |
| xl | 32px | Layout gaps |
| 2xl | 48px | Major section breaks |
| 3xl | 64px | Hero vertical padding |

Exceptions: Hero image is full-viewport-width, no horizontal padding. Touch targets minimum 44px (RESP-03, already shipped).

Source: pre-existing in `collection-pages.css` — no changes this phase.

---

## Typography

Pre-existing — no changes this phase. Listed for executor reference.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 16px | 400 | 1.5 |
| Label / badge | 12px uppercase | 600 | 1.2 |
| Subheading | 14px | 400 | 1.5 |
| Hero tagline | 20px | 400 | 1.3 |
| Section heading | 28px | 600 | 1.2 |

Source: RESP-01/04 from v1.1 (shipped). No typography changes in Phase 9.

---

## Color — Per-Collection Palette Contract

All values read from `assets/css/design-tokens.css`. No token changes in this phase.

### Default (Kids Capsule / fallback)

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Dominant (60%) | `--skyyrose-bg` | `#0A0A0A` | Page background, hero overlay |
| Secondary (30%) | `--skyyrose-secondary` | `#D4AF37` | Cards, dividers |
| Accent (10%) | `--skyyrose-accent` | `#B76E79` (rose gold) | CTA buttons, badge borders, marquee icons |
| Destructive | n/a | — | No destructive actions in this phase |

### Black Rose (`[data-collection="black-rose"]`)

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Dominant (60%) | `--skyyrose-bg` | `#0A0A0A` | Page background |
| Secondary (30%) | `--skyyrose-secondary` | `#DC143C` | Narrative accents, dividers |
| Accent (10%) | `--skyyrose-accent` | `#C0C0C0` (silver) | CTA buttons, badge borders, hero glow, marquee icons |
| Display font | `--skyyrose-font-display` | Cinzel, serif | Hero logo alt text, section headings |

**Hero visual contract (DATA-01 target):**
- Background image: `assets/branding/sr-collection-black-rose.webp` (1.5MB WebP, dark monochrome)
- Palette impression: silver-on-black, masculine, monochrome — NOT crimson, NOT rose-gold
- If live site shows crimson or rose-gold tones in the Black Rose hero, that is the DATA-01 defect
- Verification pass criterion: hero background is visually dark monochrome with silver accent — no warm or red tones

### Love Hurts (`[data-collection="love-hurts"]`)

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Dominant (60%) | `--skyyrose-bg` | `#0A0A0A` | Page background |
| Secondary (30%) | `--skyyrose-secondary` | `#B76E79` | Narrative accents |
| Accent (10%) | `--skyyrose-accent` | `#DC143C` (crimson) | CTA buttons, badge borders, hero glow |
| Background image | — | `sr-collection-love-hurts.webp` | Enchanted rose under glass |

### Signature (`[data-collection="signature"]`)

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Dominant (60%) | `--skyyrose-bg` | `#0A0A0A` | Page background |
| Secondary (30%) | `--skyyrose-secondary` | `#F7E7CE` | Warm cream narrative accents |
| Accent (10%) | `--skyyrose-accent` | `#D4AF37` (gold) | CTA buttons, badge borders, hero glow |
| Background image | — | `sr-collection-signature.webp` | Oakland skyline |

---

## Hero Banner Visual Contract (DATA-01)

The sole design-facing deliverable of this phase is confirming or fixing the Black Rose hero banner.

| Check | Expected | Pass Condition |
|-------|----------|----------------|
| Hero background image | `sr-collection-black-rose.webp` — dark monochrome model/scene | No crimson or warm tones visible in hero |
| Hero accent glow | Silver (`#C0C0C0`) | Glow around hero content is silver, not red |
| Hero logo | `black-rose-logo-hero-transparent.png` | Logo visible, correct, not swapped with another collection's logo |
| Alt text | "Black Rose Collection — rose from concrete" | Matches `hero_bg_alt` in `inc/collection-content.php:32` |
| Cache-bust suffix | `?v=` + `SKYYROSE_VERSION` | Present on both `hero_bg` and `hero_logo` `<img>` src attributes |
| `data-collection` attribute | `black-rose` | `<div class="col-page" data-collection="black-rose">` in rendered HTML |

**Defect trigger:** If live site renders crimson accent or Love Hurts imagery on the Black Rose page, investigation order per CONTEXT.md:
1. Confirm `hero_bg` value in `inc/collection-content.php:31` — expected `/branding/sr-collection-black-rose.webp`
2. Confirm asset bytes at `assets/branding/sr-collection-black-rose.webp` are not the Love Hurts image
3. Confirm `SKYYROSE_VERSION` constant is current (bump triggers CDN cache invalidation)
4. Run `openwolf designqc` after version bump + redeploy to capture visual diff

---

## Product Grid Contract (DATA-02, DATA-03 — verification only)

Both requirements shipped. This phase verifies state, does not re-implement.

| Check | Expected | Source of truth |
|-------|----------|----------------|
| Pre-order SKUs excluded from live grid | br-004, br-005, br-006, br-d01–d04, lh-001, sg-001, sg-d01 absent from rendered grid | `pre_order` column in `data/skyyrose-catalog.csv` |
| Cross-collection leakage absent | Black Rose page shows only `br-*` SKUs; Love Hurts shows only `lh-*`; Signature shows only `sg-*` | `collection` column in `data/skyyrose-catalog.csv` |
| Empty state (if all products filtered) | "No products available" or equivalent — no blank grid, no broken card slots | `skyyrose_get_collection_display_products()` return value |

**Empty product grid state copy:**
- Heading: "More pieces coming soon."
- Body: "Check back for new drops or browse another collection."
- No destructive actions in this phase.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA — Black Rose | "Shop Black Rose" (source: `collection-content.php:75`) |
| Primary CTA — Love Hurts | "Shop Love Hurts" (source: `collection-content.php:131`) |
| Primary CTA — Signature | "Shop Signature" (source: `collection-content.php:187`) |
| Primary CTA — Kids Capsule | "Shop Kids Capsule" (source: `collection-content.php:235`) |
| Empty product grid heading | "More pieces coming soon." |
| Empty product grid body | "Check back for new drops or browse another collection." |
| Error state (render failure) | Hidden `data-skyyrose-error` beacon only — no visible user-facing error copy (per existing pattern in `page.php:33-38`) |
| Destructive confirmation | None — no destructive actions in this phase |

Source: All CTA copy pre-existing in `inc/collection-content.php`. No copy changes in Phase 9.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable — no shadcn |
| Third-party | none | not applicable |

This phase ships no new JS components or npm packages.

---

## Interaction States

No new interactive components introduced. Existing states (all pre-shipped):

| Component | States |
|-----------|--------|
| CTA button (`.btn-sweep`) | Default, hover (sweep animation), active (press), focus-visible (outline) |
| Secondary CTA (`.btn-border-draw`) | Default, hover (border draw animation), active, focus-visible |
| Hero background | Ken-burns parallax on scroll (`.parallax-ken-burns`) — CSS animation, no JS |
| Scroll-reveal elements (`.col-reveal`, `.rv-*`) | Hidden → `.is-visible` via IntersectionObserver in `premium-interactions.js` |
| Holo product cards | Default, hover (magnetic tilt), focus-visible — pre-existing in `product-card-holo.css/js` |

---

## Verification Sequence

Executor must complete these in order for Phase 9 to be marked done:

1. Load `https://skyyrose.co/collection-black-rose/` — confirm hero is dark monochrome, silver accent, no crimson
2. Inspect rendered HTML — confirm `data-collection="black-rose"` attribute present
3. Inspect hero `<img>` src — confirm `sr-collection-black-rose.webp?v=` prefix (not love-hurts or signature)
4. Load `https://skyyrose.co/collection-love-hurts/` — confirm product grid contains only `lh-*` SKUs, no pre-order SKUs
5. Load `https://skyyrose.co/collection-signature/` — confirm product grid contains only `sg-*` SKUs, no pre-order SKUs
6. If DATA-01 defect confirmed: bump `SKYYROSE_VERSION`, redeploy, rerun `openwolf designqc`

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
