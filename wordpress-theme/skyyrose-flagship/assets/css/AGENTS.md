# assets/css/ — SkyyRose Theme Design System

## Isolated Workspace

**Your scope — read/write freely:**
```
wordpress-theme/skyyrose-flagship/assets/css/
```

**Adjacent reads allowed (do not write):**
```
wordpress-theme/skyyrose-flagship/inc/enqueue.php        # understand load order
wordpress-theme/skyyrose-flagship/template-parts/        # read class names in use
wordpress-theme/skyyrose-flagship/*.php                  # read template markup
```

**Out of bounds — do not touch:**
```
wordpress-theme/skyyrose-flagship/assets/js/             # separate agent scope
wordpress-theme/skyyrose-flagship/inc/                   # separate agent scope
frontend/                                                # completely separate system
```

If a fix requires a PHP template change (e.g., adding a class to markup), describe the required change and request the template-parts agent applies it.

---

## Infrastructure

**Host**: WordPress.com Business plan — NOT self-hosted
- **Deploy**: `bash scripts/deploy-theme.sh` (atomic hot-swap script) OR `sftp sftp.wp.com` (SSH) — both require explicit user confirmation
- No build pipeline — CSS is plain CSS, loaded via `wp_enqueue_style()` in `inc/enqueue.php`
- Version-busted via `SKYYROSE_VERSION` constant — bump the constant to force cache invalidation

---

## Permissions

You MAY:
- Add, modify, or delete CSS rules in any file in your workspace
- Add new tokens to `design-tokens.css`
- Add new utility classes to `components.css`
- Add new collection overrides to `collection-pages.css` or `landing-pages.css`
- Wrap animations in `@media (prefers-reduced-motion: reduce)` overrides in `accessibility.css`
- Remove dead CSS rules for PHP sections that have been deleted

You MUST NOT (without explicit user confirmation):
- Add raw hex colors — use design tokens (`var(--color-*)`)
- Set `display: grid` on anything except the 3 approved product grid selectors
- Add GSAP classes or keyframes to collection/landing page files
- Modify `design-tokens.css` token names (breaking change — all files reference them)
- Execute the deploy script

---

## Safeguards — Hard Rules

**Token mandate — no raw values:**
```css
/* WRONG */
color: #B76E79;
font-family: 'Cinzel', serif;
margin: 16px;

/* CORRECT */
color: var(--color-rose-gold);
font-family: var(--font-heading-black-rose);
margin: var(--space-4);
```

**Focus rings — never remove without replacement:**
```css
/* WRONG */
:focus { outline: none; }

/* CORRECT */
:focus-visible { outline: 2px solid var(--color-rose-gold); outline-offset: 2px; }
```

**Holo grid — only these 3 selectors may be `display: grid`:**
```css
.product-grid           { display: grid; }
.product-grid__items    { display: grid; }
.br-product-grid__items { display: grid; }
```
Setting `display: grid` on `.holo-card` or any holo wrapper breaks the magnetic tilt system.

**Showcase card content visible by default** (mobile has no hover):
```css
/* WRONG — breaks mobile */
.showcase-card__content { opacity: 0; }
.showcase-card:hover .showcase-card__content { opacity: 1; }

/* CORRECT — visible by default */
.showcase-card__content { opacity: 1; }
```

**Immediate fix mandate**: If you find a raw hex color or missing reduced-motion override while working, fix it in the same edit.

---

43 CSS files. Every color, space, and animation in the theme flows from here.

## File Roles (key files)

| File | Purpose |
|------|---------|
| `design-tokens.css` | **Root of truth** — all CSS custom properties (`--color-*`, `--space-*`, `--font-*`, `--radius-*`). Nothing gets a raw value that isn't declared here first. |
| `components.css` | Shared UI components (buttons, badges, cards, modals, toasts). |
| `collection-pages.css` | Unified stylesheet for all 4 collection pages (`col-*` classes). Replaced 4 per-collection files. |
| `landing-pages.css` | Landing page styles (`lp-*` classes) — mirrors collection-pages patterns but with `--lp-*` vars. |
| `animations-premium.css` | Global premium animation classes — loaded on every page. |
| `accessibility.css` | Focus rings, reduced-motion overrides, screen-reader utilities. |
| `cookie-consent.css` | Cookie banner — self-contained, no design token deps except brand colors. |
| `contact.css` | Contact page only. |
| `holo-card.css` / `product-card-holo.css` | Holographic card tilt/shimmer system. |
| `design-tokens.css` | All CSS custom properties. Fix colors HERE, not in individual files. |

## Token System

**ALL values must reference a token. Never hardcode a hex color, font stack, or numeric space.**

```css
/* WRONG */
color: #B76E79;

/* CORRECT */
color: var(--color-rose-gold);
```

Brand tokens defined in `design-tokens.css`:

| Token | Value | Usage |
|-------|-------|-------|
| `--color-rose-gold` | `#B76E79` | Global accent, Kids Capsule |
| `--color-dark` | `#0A0A0A` | Background |
| `--color-silver` | `#C0C0C0` | Black Rose accent |
| `--color-crimson` | `#DC143C` | Love Hurts accent |
| `--color-gold` | `#D4AF37` | Signature accent |

## Collection Palette Switching

Collection pages and landing pages use CSS custom property overrides — no JS class toggling needed.

```css
/* PHP sets data-collection on <body> */
/* CSS overrides collection-specific vars */
[data-collection="black-rose"]  { --col-accent: var(--color-silver);   --col-glow: ... }
[data-collection="love-hurts"]  { --col-accent: var(--color-crimson);  --col-glow: ... }
[data-collection="signature"]   { --col-accent: var(--color-gold);     --col-glow: ... }
[data-collection="kids-capsule"]{ --col-accent: var(--color-rose-gold); --col-glow: ... }
```

Landing pages use the same `[data-collection]` attribute with `--lp-*` variable overrides.

## Class Naming Conventions

| Page type | Prefix | Scroll-reveal class | Animation engine |
|-----------|--------|--------------------|--------------------|
| Collection pages | `col-*` | `.col-reveal` | IntersectionObserver |
| Landing pages | `lp-*` | `.lp-rv` | IntersectionObserver |
| Preorder page | — | — | GSAP |
| About page | — | — | GSAP |
| Immersive templates | — | — | GSAP |
| Front page | — | — | Three.js + particles |

**GSAP is ONLY for preorder, about, and immersive templates.** Collection and landing pages use
IntersectionObserver. Do not add GSAP to collection or landing page CSS/JS.

## Premium Animation Classes (global — `animations-premium.css`)

These classes are available on every page. Use them in PHP templates; do not re-implement the animations:

| Class | Effect |
|-------|--------|
| `rv-clip-up` | Clip-path reveal, upward |
| `rv-clip-left` | Clip-path reveal, leftward |
| `rv-blur-in` | Blur-to-sharp entrance |
| `rv-split-text` | Text line split reveal |
| `stagger-grid` | Children stagger in sequence |
| `magnetic` | Cursor magnetic pull on hover |
| `btn-sweep` | Background sweep on hover |
| `btn-border-draw` | SVG border draw on hover |

These are wired in `premium-interactions.js`. Never replicate them inline.

## Holo Card Grid — The One Grid Rule

Only these three selectors may be `display: grid`:

```css
.product-grid            { display: grid; }
.product-grid__items     { display: grid; }
.br-product-grid__items  { display: grid; }
```

No other selector in this codebase should set `display: grid` on product containers.
Using `display: grid` on `.holo-card` or its wrappers breaks the magnetic tilt system.

## Content Visibility Default

**Showcase card content must be `opacity: 1` by default.** Mobile has no hover state.
Hiding content until hover leaves mobile users with blank cards.

```css
/* WRONG — breaks mobile */
.showcase-card__content { opacity: 0; transition: opacity 0.3s; }
.showcase-card:hover .showcase-card__content { opacity: 1; }

/* CORRECT — visible by default, enhanced on hover */
.showcase-card__content { opacity: 1; }
.showcase-card:hover .showcase-card__content { /* enhancement only */ }
```

## Accessibility Requirements

- All interactive elements: WCAG AA contrast (`4.5:1` text, `3:1` UI components)
- Focus rings: defined in `accessibility.css` — never set `outline: none` without a replacement
- `@media (prefers-reduced-motion: reduce)`: wrap all `transition` and `animation` in this override (defined globally in `accessibility.css`)
- Icon-only buttons: must have `aria-label` — no exceptions

## When Removing a PHP Section

When a PHP template section is removed:

1. Remove the section's CSS rules from the corresponding CSS file
2. Remove the responsive breakpoint overrides for that section
3. Check `design-tokens.css` for tokens only used by the removed section — remove those too
4. Run `npm run lint:php && npm run verify` before commit

## Mandatory Quality Workflow

After every change to any CSS file in your workspace, run ALL three steps in order.

### 1. CSS Lint
```bash
cd wordpress-theme/skyyrose-flagship
# Check for raw hex colors that snuck in:
grep -rn '#[0-9A-Fa-f]\{3,6\}' assets/css/ --include="*.css" | grep -v 'design-tokens.css'
# Must return no results (only design-tokens.css may contain raw hex values)

# PHP lint to catch any associated template changes:
npm run lint:php
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified CSS file(s). Focus on:
- Duplicate property declarations (same property set twice in same rule)
- Selectors that can be simplified with `:is()` or `:where()`
- Dead rules for removed PHP sections

### 3. /verification-loop
```bash
# Verify live site loads
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/
# Must return 200.

# If collection CSS was modified:
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/collections/black-rose/
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/collections/love-hurts/

# Verify no token violations snuck in:
grep -c 'var(--color-' assets/css/collection-pages.css
# Should be > 0 (all colors via tokens)
```

---

## Do NOT

- Set raw hex colors — use design tokens
- Add GSAP to collection or landing pages
- Set `display: grid` on anything except the three approved product grid selectors
- Hide content with `opacity: 0` by default if the reveal requires hover
- Add `outline: none` without a visible focus replacement in `accessibility.css`
- Add per-collection CSS files — `collection-pages.css` handles all 4 collections
- Reference retired files: `collection-black-rose.css`, `collection-love-hurts.css`, `collection-signature.css`, `collection-kids-capsule.css` (replaced by unified file)
- Touch files outside your workspace without flagging to the user
