---
name: luxury-design-taste
description: Luxury streetwear design taste for SkyyRose surfaces — visual hierarchy, restraint, materials, motion, and imagery treatment. Use for any visual design, review, or elevation work on skyyrose.co or the DevSkyy dashboard. Replaces the lost high-end-visual-design / design-taste-frontend / image-taste-frontend skills.
---

# Luxury Design Taste — SkyyRose

Brand truth: "Luxury Grows from Concrete." Oakland-rooted luxury streetwear — NOT European maison minimalism. Canonical references: Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels. Never Chanel/Dior/Celine lineage.

## The garment is the protagonist

Every surface serves the product photography. Copy, chrome, and motion are supporting cast.
- Imagery: on-model shots outrank ghost mannequins outrank flat lays. Full-bleed where possible.
- NEVER: urgency timers, countdown clocks, related-products/"wears with" cross-sell (retired canon), fake scarcity, discount-brand energy.
- Hero titles = brand-script lockup IMAGES (hero-overlays/logos), never type-rendered. Fonts are for interior text only.

## Restraint rules (what separates luxury from template)

- One accent per collection surface: Signature `#D4AF37`, Black Rose `#C0C0C0`, Love Hurts `#DC143C`, Kids Capsule `#B76E79`, on dark `#0A0A0A`. Two accents on one screen = flea market.
- Whitespace is the luxury signal. If a section feels empty, that's usually correct. Density is for dashboards, not storefronts.
- Type scale: big editorial serif moments (Playfair/Cormorant) + tiny wide-tracked utility labels (Bebas Neue, 10-13px, 4-8px letter-spacing). The MIDDLE sizes are where generic creeps in — avoid 16-20px workhorse type on marketing surfaces.
- Materials: glass (rgba white 0.04-0.08 + blur), hairline borders (1px, low-alpha white), metallic gradients ONLY on brand-token hues. No drop shadows heavier than `0 24px 80px rgba(0,0,0,.4)` on dark.

## Motion taste

- Ease: `cubic-bezier(.16,1,.3,1)` (the house curve, `--ease-luxury`). Duration 0.6-1.2s for reveals; nothing snaps.
- Motion must have narrative purpose: reveal on scroll, parallax depth, slow zoom (`heroZoom`-style 20-30s ambient). Decorative twitching = slop.
- Everything animated pauses under `@media (prefers-reduced-motion: reduce)` and stays legible when frozen.
- Auto-scrolling media (marquees, strips) must remain background texture: opacity ≤ 0.25 behind content, masked edges, and never compete with the lockup.

## Imagery treatment

- Product pixels are identity — verify garment matches SKU (eyes-on) before any imagery ships. Wrong-garment is the #1 recurring defect.
- Editorial treatment for background/ambient use: desaturate 30-40%, brightness 0.7-0.8, contrast +5%, vignette-mask edges. Full color is reserved for the product being sold.
- Aspect discipline: portrait 3:4/2:3 for garments, wide only for scenes. Never stretch, never letterbox with visible bars.

## Slop detectors (instant fail)

Centered-everything symmetric layouts; gradient text on headings; emoji in UI; 12-col bootstrap rhythm; uniform border-radius 8px everywhere; stock-photo energy (non-brand models, generic city b-roll); grey-on-white "SaaS clean" palettes; identical card grids without one broken/featured element for rhythm.

## Precedence

When design sources disagree: project `.impeccable.md` > this skill > impeccable > ui-ux-pro-max tables > interactive-web-development examples. ui-ux-pro-max's html-tailwind default and Liquid Glass recommendation are overridden for this project (vanilla CSS; glassmorphism banned outside `product-card-holo`). impeccable's reflex-font rejection does not apply to locked brand fonts (Cinzel, Playfair Display, Cormorant Garamond, Bebas Neue, Inter).
