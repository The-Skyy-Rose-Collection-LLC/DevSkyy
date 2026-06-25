# SkyyRose Storefront React Design System → claude.ai/design (WordPress-compatible)

**Date:** 2026-06-22
**Status:** Design approved (brainstorming); pending spec review → writing-plans
**Owner:** DevSkyy engineering agent

---

## 1. Goal & context

Make **claude.ai/design** the design/iteration surface for the SkyyRose storefront, and make everything built there land on the **live WordPress storefront (skyyrose.co)** without a rewrite.

claude.ai/design's design agent builds with **React** components synced via the `design-sync` skill (package shape). skyyrose.co is a **classic PHP theme** (`wordpress-theme/skyyrose-flagship/`): PHP template-parts + block patterns + `theme.json`, **no custom JS-built blocks** (verified: zero `block.json`). The two cannot share a runtime, but they can — and already do — share a **CSS class contract**.

**Core principle:** the design system *is* the CSS (tokens + component CSS + BEM classes). React (claude.ai/design) and PHP (skyyrose.co) are thin renderers that emit the **same classes against the same CSS source**. Compatibility is a shared-CSS contract, not a transpiler.

This is increment 1 (foundation-first) of a roadmap to the full ~18-component storefront surface (§8).

---

## 2. Architecture

### 2.1 Single CSS source of truth

The WP theme's `wordpress-theme/skyyrose-flagship/assets/css/` is canonical and already what ships (enqueued via `inc/enqueue.php`, dependency graph rooted at the `skyyrose-design-tokens` handle). The React DS **does not fork** it — the same source bytes feed the React build, **drift-guarded**: a build/CI assertion (hash compare or `diff --exit-code`) fails if the package's copy diverges from the theme source. Direction is one-way: **theme → package**.

Two viable mechanisms (decided in writing-plans):
- **(a) `sync-css` prebuild step** copies the canonical theme CSS files into the package `src/`, plus a drift assertion. Robust across tooling; package stays self-contained.
- **(b) Vite alias / cross-package import** of the theme CSS directly (needs `server.fs.allow` / build config for out-of-root files). Purest single-source, more tooling friction.

Default to (a) for robustness unless (b) proves clean.

### 2.2 New isolated package

Never cross-wired with `frontend/` (devskyy.app dashboard) or the WP theme runtime:

```
design-system/skyyrose-storefront/
  package.json          name "@skyyrose/storefront-ds"; module → dist/skyyrose-ds.es.js
  vite.config.ts        library mode + vite-plugin-dts
  src/
    tokens/tokens.css   ← design-tokens.css (synced; 5 collection palettes)
    fonts/fonts.css     ← @font-face + woff2 (synced from theme assets/fonts/)
    components/
      HoloCard/{HoloCard.tsx, holo-card.css}
      Button/{Button.tsx, button.css}
      CollectionHero/{CollectionHero.tsx, collection-hero.css}
    index.ts            ← barrel export (the .d.ts exports define the design-sync component list)
  dist/                 ← build output: skyyrose-ds.es.js + skyyrose-ds.css + .d.ts tree
.design-sync/
  config.json  previews/  NOTES.md  conventions.md   ← design-sync durable set (committed)
```

### 2.3 Dual renderers, one contract

| Concern | React (design-time, claude.ai/design) | WordPress (ship-time, skyyrose.co) |
|---|---|---|
| Markup | `<Component>.tsx` (JSX) | PHP template-part or block pattern |
| CSS | imported from the single source (§2.1) | enqueued from the single source (already live) |
| Classes | identical BEM (`.holo`, `.holo__body`, `.collection-hero`…) | identical BEM |
| Behavior | React state + hooks | existing vanilla JS (`product-card-holo.js`) / static |

Because both render the same classes against the same CSS, **claude.ai/design output is pixel-identical to skyyrose.co by construction**.

---

## 3. Token + font layer

- **Tokens**: `design-tokens.css` is already pure CSS custom properties — used as-is. The `[data-collection="signature|black-rose|love-hurts|kids-capsule"]` cascade works unchanged in React; collection theming = wrapping in `<div data-collection="…">`. **No React context provider** (avoids `cfg.provider`).
- **Fonts**: brand families (Cinzel, Playfair Display, Cormorant Garamond, Bebas Neue, + per-collection scripts Yellowtail/Pinyon/Kaushan) ship self-hosted as woff2 + `@font-face`, wired to design-sync via `cfg.extraFonts` (else `[FONT_MISSING]` → fallback fonts in every design). Source: theme `assets/fonts/`.

---

## 4. v1 components (faithful PHP→React port, commerce-as-props)

`Collection = 'signature' | 'black-rose' | 'love-hurts' | 'kids-capsule'`

### 4.1 HoloCard — the signature
Ported from `template-parts/product-card-holo.php` + `product-card-holo.css` + `product-card-holo.js`.

```ts
interface HoloCardProps {
  title: string;                 // rendered in Cinzel
  price: string;                 // "$95" or WC price_html
  sku?: string;                  // data-sku + handler payloads
  collection: Collection;        // drives [data-collection] palette
  frontImage: string;            // model/finished render
  backImage?: string;            // techflat; defaults to frontImage
  permalink?: string;            // gallery + title links
  sizes?: string[];              // default ['S','M','L','XL']
  badge?: 'soldout' | 'preorder' | null;
  index?: number;                // stagger entrance delay
  tilt?: boolean;                // magnetic 3D tilt; auto-off on touch/reduced-motion; default true
  onAddToCart?: (p: { sku?: string; size: string | null }) => void;
  onWishlistToggle?: (p: { sku?: string; active: boolean }) => void;
}
```
Behavior: front→techflat hover crossfade (CSS), drawer slide-up (CSS), size-pill + wishlist state (`useState`), optional magnetic tilt (hook; renders neutral at rest in static previews).

### 4.2 Button — generalized `.holo__buy` CTA
```ts
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'solid' | 'accent' | 'ghost';  // solid=white/black, accent=collection accent, ghost=outline; default 'solid'
  size?: 'sm' | 'md' | 'lg';                // default 'md'
  as?: 'button' | 'a';                       // default 'button'
  href?: string;
  loading?: boolean;
  disabled?: boolean;
  onClick?: (e: React.MouseEvent) => void;
}
```
Bebas-Neue uppercase, accent-on-hover. CSS source resolved in plan (generalizes `.holo__buy`).

### 4.3 CollectionHero — image-lockup hero (no Three.js)
Ported from `patterns/collection-hero-{slug}.php` (block patterns, `core/group` markup).
```ts
interface CollectionHeroProps {
  collection: Collection;
  lockupImage: string;        // brand-script lockup IMAGE asset — never type-rendered (brand rule)
  tagline?: string;
  backgroundImage?: string;
  cta?: { label: string; href: string };
  align?: 'center' | 'left';  // default 'center'
}
```

**Commerce is prop-ified:** WC AJAX add-to-cart and localStorage wishlist become `onAddToCart` / `onWishlistToggle`. Components ship fully functional but storefront-agnostic — the design agent composes them; real handlers are wired by consumers.

---

## 5. WordPress compatibility bridge

### 5.1 Component pairing (React ↔ WP artifact)

| React | WP artifact | Status |
|---|---|---|
| `HoloCard.tsx` | `template-parts/product-card-holo.php` | exists — React mirrors it |
| `Button.tsx` | `.holo__buy` / shared CTA class used inline in PHP | primitive; no dedicated partial — shared class only |
| `CollectionHero.tsx` | `patterns/collection-hero-{slug}.php` | exist as block patterns — React mirrors markup |

### 5.2 Two ship-lanes back into WordPress

| Designed in claude.ai/design | Ships to WP as | Effort |
|---|---|---|
| Static sections (hero, landing, marketing) | **Block pattern** (`patterns/*.php`) — already HTML+classes | ~drop-in |
| Dynamic commerce (product card, live WC data) | **PHP template-part** (`template-parts/*.php`) | mechanical JSX→PHP: same classes, `$args` props, `esc_*` |

### 5.3 Round-trip workflow
```
design in claude.ai/design  →  agent emits HTML using the shared classes
   →  static?  paste into a block pattern    |    dynamic?  translate markup to a PHP partial
   →  rebuild .min (build-css.js / build-js.js)  →  deploy  →  visually identical (shared CSS)
```

### 5.4 Drift + parity guards
- **CSS drift guard** (§2.1): build fails if the package CSS copy ≠ theme source.
- **Markup parity test**: render each React component's DOM (jsdom/RTL), normalize, assert the class structure matches the paired PHP/pattern output (captured fixture). Catches when one renderer diverges from the contract.

---

## 6. Build → design-sync pipeline

`.design-sync/config.json` (package shape):
```json
{
  "pkg": "@skyyrose/storefront-ds",
  "globalName": "SkyyRoseDS",
  "shape": "package",
  "buildCmd": "npm run build",
  "cssEntry": "dist/skyyrose-ds.css",
  "extraFonts": "src/fonts/fonts.css",
  "projectId": "<recorded at project creation>"
}
```

Steps (grounded in `design-sync/non-storybook/SKILL.md`):
1. `npm run build` — Vite library mode + `vite-plugin-dts` → `dist/skyyrose-ds.es.js` + `dist/skyyrose-ds.css` (tokens + fonts + component CSS, single closure) + `.d.ts` tree.
2. Stage `.ds-sync/` (copy converter scripts + `lib/`), install `esbuild ts-morph @types/react`.
3. `package-build.mjs --entry ./dist/skyyrose-ds.es.js --out ./ds-bundle` → IIFE on `window.SkyyRoseDS`, `styles.css` `@import` closure, per-component `.d.ts` / `.prompt.md` / preview cards.
4. Author `.design-sync/previews/{HoloCard,Button,CollectionHero}.tsx` — rich previews (HoloCard ×5 collections, Button ×variants, CollectionHero ×collections); each named export = one graded card.
5. `package-validate.mjs ./ds-bundle` — headless chromium render check (playwright+chromium install is **gated**, ~200MB, asks first; `--no-render-check` only with explicit sign-off). Fix `[TAG]` diagnostics → rebuild → grade on the absolute rubric → `.review.html` human review.
6. **design-sync upload** — create a NEW project "SkyyRose Storefront" (creation is **permission-prompted**); incremental path (empty project): one upfront approval, components appear as verified.

---

## 7. Testing & verification

- **Unit (TDD, Vitest + RTL)**: stateful logic only — size-pill selection, wishlist toggle, Button loading/disabled. Hover/tilt are visual-only.
- **Functional gate**: design-sync chromium render check (every preview renders non-empty) + absolute-rubric grading.
- **CSS drift assertion** + **markup parity test** (§5.4).
- **Human sign-off**: `.review.html` locally, then the claude.ai/design DS pane (true render environment).
- Project verification matrix still applies: `pytest`/lint not relevant here; `npm run build` + `tsc --noEmit` + the new package's `vitest` are the green gates.

---

## 8. Incremental roadmap to full site

Each increment is one design-sync re-sync; authored previews + grades carry forward.

- **v1** (this spec): tokens, fonts, **HoloCard, Button, CollectionHero**.
- **v2**: Badge, SizePillGroup, Price, CollectionEyebrow, ProductGrid.
- **v3**: SectionHeading, FooterCTABand, collection-page composition.
- **v4**: Header/Nav, MobileBottomNav, ProductDetailEditorial, SkyyMascot, PinNarrative, SizeGuideModal, CookieConsent.

→ full ~18-component storefront surface. Each new component gets its React/PHP pairing (§5.1) at adoption.

---

## 9. Risks & open items

- **CSS import vs sync-copy** (§2.1) — resolve in plan; Vite `fs.allow` if cross-package import.
- **chromium install gate** — render check needs it; ask before installing.
- **Button / CollectionHero exact CSS source files** — confirm during implementation (HoloCard's is `product-card-holo.css`).
- **Magnetic tilt in static previews** — renders neutral at rest; acceptable.
- **claude.ai/design project creation** — permission-prompted; happens during execution.
- **Re-sync carry-forward** — previews/grades persist via the uploaded `_ds_sync.json` anchor + committed `.design-sync/previews/`.

---

## 10. Out of scope (v1)

- Three.js immersive collection heroes (CollectionHero is the image-lockup variant).
- The other ~15 components (v2–v4 increments).
- Headless WordPress; web-components single-runtime bridge (considered, rejected — SEO/speed + re-architecture cost).
- Any paid-API call, production deploy, or live WC/media write — none required by this pipeline.
