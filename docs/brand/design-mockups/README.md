# Design Mockups

Static HTML design references. Not production code. Standalone, self-contained, no build step.

## Files

| File | Status | Purpose |
|------|--------|---------|
| [`v2.html`](./v2.html) | **Active 2026-05-25** | Magazine-as-site direction. Locked by founder. See `docs/superpowers/specs/2026-05-25-v2-mockup-design.md` for the spec; `docs/brand/visual-references.md` for The Five canonical references it pulls from. |
| [`collection-designs.html`](./collection-designs.html) | Superseded | First-pass v1 design from earlier session. Kept for historical reference. Visual direction did not survive the brand-canon recalibration. |

## How to view

Open `v2.html` directly in a modern browser (Chrome / Firefox / Safari). All assets resolve via relative paths into `../../../wordpress-theme/skyyrose-flagship/assets/`.

## What v2.html demonstrates

- Magazine-as-site composition: Cover → Hero → Voice → Spread per surface
- Homepage + Black Rose collection page in one scrollable document
- Real brand assets (hero photography from `assets/branding/hero/`, collection lockups from `assets/images/hero-overlays/`, brand-primary monogram)
- Locked typography system (Cinzel masthead, Bebas editorial, Playfair italic voice, Space Mono meta, Inter body)
- IntersectionObserver scroll reveals + parallax photography + `prefers-reduced-motion` fallback
- No Three.js. No WebGL. Vanilla HTML/CSS/JS.

## Production translation

This is a design reference, not the production site. When the visual direction is approved, a separate spec + plan cycle translates v2.html into WordPress theme templates under `wordpress-theme/skyyrose-flagship/template-*.php`.
