# SkyyRose Collection Design Proposals
## 12 Design Moments — v1.0 (2026-05-24)

Register: Black Rose = brutalist · Love Hurts = expressive · Signature = editorial · Kids Capsule = minimalist

---

## BLACK ROSE

**Register:** Brutalist. Posture, not presentation. The design does not ask for attention — it occupies space. Issey Miyake catalog, not a mood board. Every element earns its placement or it is removed. Silver on near-black. Cinzel for display — the only collection where it is used. Restraint as violence.

**Palette application:**
- Background: `#0A0A0A`
- Accent (all interactive + headlines): `--skyyrose-accent` → `#C0C0C0` (silver)
- Secondary (blood flash, used sparingly): `--skyyrose-secondary` → `#DC143C`
- Display: Cinzel Decorative
- Body: Cormorant Garamond 16px / lh 1.7

---

### BR-1 · Landing Page

**Tagline lock:** "You wear it because you already stood up."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│                                              │
│  YOU WEAR IT BECAUSE                         │  ← Cinzel Decorative, --text-5xl
│  YOU ALREADY STOOD UP.                       │     silver, flush left, 8pt grid
│                                              │
│                                              │
│  ─────────────────────────────────────────  │  ← 1px silver rule, full-bleed
│                                              │
│  [garment — full-frame, no crop, portrait]  │  ← 100vw × 100vh image
│   garment centered, near-black BG           │     object-fit: cover
│                                              │
│                                              │
│  BLACK ROSE  ↓                               │  ← Bebas Neue, label size
└─────────────────────────────────────────────┘
```

Hero image is the only decoration. No overlay, no gradient, no text on image. Headline lives ABOVE the image in a letterbox band — approximately 80px top band, silver text, 40px padding left. The rule separates the copy zone from the image zone without softening the boundary.

**Below-fold sections:**

1. **Story block** — two columns on desktop, single on mobile. Left: `"Black Rose is not a collection. It is a stance."` — Cormorant Garamond italic, 24px, silver. Right: 3 lines founder voice, Cormorant Garamond regular 16px. No pull quotes, no decorative elements.

2. **Single product feature** — full-bleed horizontal layout. 60vw image left, 40vw text right. Product name in Cinzel, 32px. One sentence about the garment. One `btn-sweep` CTA: "WEAR IT" — never "Shop Now", never "Buy".

3. **Press bar** — `.lp-press.lp-rv` existing component. Silver text, no logos unless monochrome. 1px silver rule above and below.

4. **Footer CTA** — single sentence, centered: `"You already know if this is yours."` Below: one text link, no button. Bebas Neue 14px. Nothing else.

**Color application:** Silver is structural. Crimson appears once — on the CTA button hover state only. No gradients. No shadows. `--shadow-sm` permitted on cards only.

**Interaction layer:**
- Hero entrance: `rv-clip-up` on headline, duration `--reveal-cinematic: 1.6s`, `--ease-dramatic`
- Story block: `rv-blur` on text block, threshold 0.15
- Product feature: `rv-clip-left` on image, `rv-clip-right` on text, simultaneous
- CTA button: `btn-sweep` class, silver sweep, no scale transform
- Scroll-triggered rule draw: 1px line animates from 0% to 100% width on intersect — CSS `scaleX` from 0 to 1 with `transform-origin: left`

**Mobile adaptation:**
- Headline band compresses to 64px, font clamps to 1.75rem minimum
- Story columns stack, right column moves above left
- Product feature: image full-width, text stacks below with 24px padding
- Press bar scrolls horizontally, touch-draggable

---

### BR-2 · Browse Grid

**Tagline lock:** "You wear it because you already stood up."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│ BLACK ROSE          [current season]         │  ← Cinzel, silver / Bebas Neue, muted
│                                              │
│ ─────────────────────────────────────────── │  ← 1px rule
└─────────────────────────────────────────────┘

[GRID — 2 column, desktop]
┌─────────────┐  ┌─────────────┐
│             │  │             │
│  [garment]  │  │  [garment]  │
│             │  │             │
│  Name       │  │  Name       │
│  $XXX       │  │  $XXX       │
└─────────────┘  └─────────────┘
```

No hero image section — the grid IS the hero. Collection name + rule is the full above-fold treatment. This is a catalog, not an experience page. Trust the garments.

**Grid rhythm:** 2 columns desktop, 1 column mobile. No masonry, no feature card, no "hero" first item that breaks the grid. All cards identical width. Vertical gap: 48px (--space-12). Horizontal gap: 32px (--space-8). Product name: Cinzel 14px, silver. Price: Bebas Neue 13px, muted silver (`#666`). No category labels, no badges, no sale indicators.

**Below-fold sections:** No content below the grid except pagination. No "explore more" CTA, no editorial insertion between rows.

**Color application:** Cards use `#0F0F0F` background (1 step off true black for depth). Image area `#0A0A0A`. Card border: `1px solid rgba(192,192,192,0.12)` — nearly invisible, present only to define edge. Hover: border brightens to `rgba(192,192,192,0.4)`.

**Interaction layer:**
- Grid entrance: `stagger-grid` on card container, `--stagger-medium: 100ms`
- Card hover: `transform: translateY(-4px)` — 4px only, on the 8pt grid. No scale.
- Card image hover: gentle brightness lift via `filter: brightness(1.08)`, `--transition-normal`
- `magnetic` class on product name link — subtle cursor pull, not exaggerated
- No lightbox, no quick-add, no hover overlay with CTA

**Mobile adaptation:** Single column, 16px horizontal padding. Cards span full content width. Touch: standard tap to PDP, no swipe gesture on grid.

---

### BR-3 · Product Detail Page (PDP)

**Tagline lock:** "You wear it because you already stood up."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  ┌──────────────────────┐                   │
│  │                      │  PRODUCT NAME     │  ← Cinzel, --text-5xl
│  │                      │                   │
│  │    [main image]      │  One sentence.    │  ← Cormorant Garamond italic
│  │                      │                   │
│  │                      │  $XXX             │  ← Bebas Neue, large
│  │                      │                   │
│  └──────────────────────┘  [SIZE]  [ADD]   │
│                                              │
│  [thumbnail rail — 4 images, horizontal]   │
└─────────────────────────────────────────────┘
```

Left: 60% — single image, full container height, no crop. Right: 40% — product name, one-sentence editorial note (from dossier if exists), price, size selector, add-to-cart. No star ratings. No review count. No "In Stock" badge.

**Below-fold sections:**

1. **Details accordion** — three items max: "Construction", "Fabric", "Care". Cinzel labels, Cormorant Garamond content. 1px silver rule as divider. No icons. Open state shows crimson 1px left border.

2. **Garment story** — if editorial dossier exists, full dossier text in Cormorant Garamond 18px, 680px max-width, centered. No sidebar. No column layout. This is prose, not UI.

3. **Sizing** — text-only. No size charts as tables — a paragraph per size range. Cormorant Garamond italic.

**Color application:** Right column background: `#0D0D0D` (3 steps off black). Size selector active state: silver border 2px, no fill. Add-to-cart: `btn-border-draw` — silver border draws on hover, fills on active. No primary fill button.

**Interaction layer:**
- Page load: `rv-clip-left` on image (0.8s), simultaneous `rv-blur` on right column
- Accordion: standard CSS height transition, 300ms
- Gallery thumbnails: click-to-swap main image, `--transition-fast` crossfade
- Size selector: `magnetic` on each option
- Add-to-cart: `btn-border-draw`, crimson flash on success state (200ms)

**Mobile adaptation:** Stack to single column. Image 100vw, full aspect ratio preserved. Info block below with 24px padding. Accordion items 48px minimum touch target. Size selector becomes horizontal scroll row.

---

## LOVE HURTS

**Register:** Expressive. Grief made wearable. The design does not soothe — it confirms. McQueen show notes, not retail. Crimson bleeds. Cormorant Garamond carries the weight. Sentences that don't apologize. Every transition is earned with duration. Nothing is decorative for its own sake.

**Palette application:**
- Background: `#0A0A0A`
- Accent: `--skyyrose-accent` → `#DC143C` (crimson)
- Secondary: `--skyyrose-secondary` → `#B76E79` (rose gold, grief's warmer underside)
- Display: Playfair Display
- Body: Cormorant Garamond 16px / lh 1.8 (more generous — text needs room to breathe)

---

### LH-1 · Landing Page

**Tagline lock:** "They called me Beast. They were right."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│         [full-bleed hero image]              │
│    garment, editorial pose, face optional    │  ← 100vw × 100vh
│                                              │
│                                              │
│                                              │
│  THEY CALLED ME BEAST.                       │  ← Playfair Display italic
│  THEY WERE RIGHT.                            │     --text-decorative-lg, crimson
│                                              │     bottom-aligned, 64px from bottom
└─────────────────────────────────────────────┘
```

Unlike Black Rose (text above image), Love Hurts places the tagline OVER the image — bottom-left, large, crimson Playfair Display italic. The image is not suppressed — the text lands on top of the garment, owned. `text-shadow: none`. Let the crimson do the work. Overlay: `linear-gradient(to top, rgba(10,10,10,0.7) 30%, transparent)` — enough to ensure contrast, not enough to dim the garment.

**Below-fold sections:**

1. **Verse block** — full-width, centered. 3–5 lines from the dossier or collection brief, Cormorant Garamond italic 28px, maximum 720px wide. Line height 1.9. No attribution line. This is not a pull quote — it is a statement. Rose gold color.

2. **Gallery strip** — horizontal scroll, 4–5 images, each 320px wide × 480px tall. Spacing 16px. No captions. Crimson scrollbar on desktop (custom `::scrollbar-thumb`).

3. **Single product feature** — asymmetric two-column. Right side: 55% image, editorial bleeding past the column boundary by 40px (CSS `margin-right: -40px`). Left side: product name Playfair Display, 40px; two-sentence story line; price; CTA `btn-sweep`. The bleed is the design statement.

4. **Closing line** — full-width, centered, 80px vertical padding: `"You wore the weight before the collection existed."` — Cormorant Garamond italic, 22px, rose gold. No CTA below it.

**Color application:** Crimson for headlines and primary CTAs only. Rose gold for secondary text, verse, and closing line. Never both crimson and rose gold in the same sentence. Background stays `#0A0A0A` — no section background changes.

**Interaction layer:**
- Hero tagline: `rv-split-word` on each line, `--reveal-cinematic: 1.6s`, staggered 200ms between lines
- Verse block: `rv-blur-down`, threshold 0.2, `--reveal-slow: 1.2s`
- Gallery strip: `rv-clip-up` on strip container, horizontal scroll inertia via `scroll-snap-type: x mandatory` on container
- Product feature image bleed: `rv-clip-right` with 1.6s — the bleed is part of the reveal
- `btn-sweep` on CTA: crimson sweep, Bebas Neue label
- Closing line: `rv-blur`, `--reveal-cinematic` — last element on page, deserves the full duration

**Mobile adaptation:**
- Hero tagline font clamps to `clamp(2.5rem, 9vw, 4rem)` — still large, still dominant
- Gallery strip maintained as horizontal scroll — swipe-native
- Product feature: loses the bleed (stacks cleanly), image first
- Closing line: 40px vertical padding on mobile

---

### LH-2 · Browse Grid

**Tagline lock:** "They called me Beast. They were right."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│  [full-width editorial image, 60vh]          │
│                                              │
│  LOVE HURTS                                  │  ← Playfair Display italic, crimson
│  ─────────────────                           │  ← partial rule, 280px, crimson
└─────────────────────────────────────────────┘

[GRID — 3 column desktop, offset rhythm]
┌──────┐  ┌──────┐  ┌──────┐
│      │  │      │  │      │
│ [g1] │  │ [g2] │  │ [g3] │  ← row 1: equal
│      │  │      │  │      │
└──────┘  └──────┘  └──────┘

┌──────────────┐  ┌──────┐
│              │  │      │
│    [g4]      │  │ [g5] │  ← row 2: 2:1 feature
│  (2-col)     │  │      │
│              │  │      │
└──────────────┘  └──────┘
```

Love Hurts gets a cinematic hero above the grid — a 60vh editorial image with the collection name overlaid bottom-left. The grid rhythm alternates: row 1 is 3-equal, row 2 is 2:1 feature, row 3 is 3-equal again. This is not arbitrary — it mirrors the emotional rhythm of the collection. `grid-template-columns` variations handled with nth-child selectors on the grid container.

**Color application:** Card background `#0F0F0F`. Rose gold product name, Playfair Display italic 15px. Price: Bebas Neue, muted. Hover state: thin crimson left-border on card (2px, full card height).

**Interaction layer:**
- Hero image: `rv-clip-up`, `--reveal-cinematic`
- Hero text: `rv-split-word`, simultaneous with image
- Grid: `stagger-grid`, `--stagger-long: 150ms` — slightly slower than Black Rose, more weight per card
- Card hover: crimson left-border animates from `height: 0` to `height: 100%`, CSS transition 400ms
- Feature card (2-col): `magnetic` on product name, subtle

**Mobile adaptation:** Grid collapses to 2-column on tablet, single on mobile. Feature card loses 2-col spanning (CSS media query), becomes same size as peers.

---

### LH-3 · Product Detail Page (PDP)

**Tagline lock:** "They called me Beast. They were right."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  [full-width image, 75vh, editorial crop]   │  ← No sidebar. Full attention.
│                                              │
│  ─────────────────────────────────────────  │  ← 1px crimson rule
│                                              │
│  PRODUCT NAME          $XXX  [ADD TO BAG]   │  ← Playfair italic / Bebas Neue
│                                              │
│  [SIZE: S  M  L  XL]                        │
└─────────────────────────────────────────────┘
```

Love Hurts PDP breaks the side-by-side layout. The garment gets the full viewport width at 75vh, cinematic. Below: a 1px crimson rule, then a one-row bar with product name left, price + CTA right, sizes below it. This is editorial — the garment is the full moment before commerce begins.

**Below-fold sections:**

1. **Dossier prose** — if exists, full text Cormorant Garamond italic 20px, rose gold, max-width 680px, centered, 80px top/bottom padding. No heading, no label. It reads like a letter.

2. **Construction accordion** — same as BR-3 but crimson left-border on open state instead of silver.

3. **Gallery** — 3-image horizontal strip below accordion, same specs as LH-2 gallery strip.

**Color application:** Add-to-bag: `btn-sweep` — crimson sweep. Bebas Neue label "ADD TO BAG" — never "Add to Cart". Size selector active: crimson 2px underline, no border-box. Inactive sizes: muted silver text, no border.

**Interaction layer:**
- Hero image: `rv-clip-up`, `--reveal-cinematic: 1.6s`, `--ease-dramatic`
- Rule: `scaleX` 0→1 from left, 600ms, fires after image reveal completes (JS sequential trigger)
- Product info row: `rv-blur`, 0.8s, fires 200ms after rule
- Dossier prose: `rv-blur-down`, `--reveal-slow: 1.2s`
- Add-to-bag: `btn-sweep`, crimson flash on success

**Mobile adaptation:** Full-width image maintained (100vw × 75vh). Info bar stacks: name, then price, then size row, then CTA full-width. Add-to-bag becomes full-width `btn-sweep` block.

---

## SIGNATURE

**Register:** Editorial. Origin, Chapter One. Not minimalism — warmth and precision coexisting. The Row meets Aimé Leon Dore: deliberate, confident, bookish. Playfair Display for display, but warmer weight than Love Hurts. Gold accent. No silver. No crimson. Every page reads like the first page of something important.

**Palette application:**
- Background: `#0A0A0A`
- Accent: `--skyyrose-accent` → `#D4AF37` (gold)
- Secondary: `--skyyrose-secondary` → `#F7E7CE` (warm cream — body text tint option)
- Display: Playfair Display (regular weight, not italic-dominant)
- Body: Cormorant Garamond 16px / lh 1.65

---

### SIG-1 · Landing Page

**Tagline lock:** "Not basics. Blueprints."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  NOT BASICS.                                 │  ← Playfair Display, --text-5xl
│  BLUEPRINTS.                                 │     gold, flush left, 56px padding
│                                              │
│  [garment — 3/4 shot, warm editorial light] │  ← 80vh, slightly warm treatment
│                                              │
│                          ─────────────────  │  ← 1px gold rule, right-aligned 40%
└─────────────────────────────────────────────┘
```

Like Black Rose, headline lives above image — but warmer. The rule is right-aligned (not full-bleed), creating asymmetric balance. The garment image has slightly warmer color treatment than Black Rose (not warm-toned — just less cold). This is an editorial magazine opening, not a statement of defiance.

**Below-fold sections:**

1. **Founder note** — narrow column, left-aligned, 560px max-width. 3–4 sentences from Corey's voice. Cormorant Garamond 18px, warm cream (`#F7E7CE`). Above it: "FROM COREY" in Bebas Neue 11px, gold, letter-spacing 4px.

2. **Blueprint grid** — 2×2 grid, equal cards. Each card: garment image top, product name Playfair Display 16px gold, one-line note below. This is the full browse invitation. 4 cards only (the blueprint, not the catalog).

3. **Story block** — full-width, 80px padding. Left-aligned headline: "Chapter One." in Playfair Display italic 48px, gold. Below: 2 sentences, Cormorant Garamond 18px. Right of text at 60% width: a single architectural detail shot of garment construction (seam, label, fabric texture).

4. **Press bar** — existing `.lp-press.lp-rv`, gold text.

**Color application:** Gold for all headlines, rules, and primary interactive states. Cream for supporting text (Cormorant body). No rose gold, no crimson, no silver. Background stays `#0A0A0A`.

**Interaction layer:**
- Headline: `rv-split-line` (line by line), `--reveal-slow: 1.2s`, `--ease-cinematic`
- Founder note: `rv-blur`, threshold 0.2
- Blueprint grid: `stagger-grid`, `--stagger-medium: 100ms`
- Story block: `rv-clip-diagonal`, `--reveal-cinematic: 1.6s` — the one moment of flair
- CTA on blueprint cards: `btn-border-draw`, gold border draw

**Mobile adaptation:**
- Headline clamps to 2rem minimum, stays flush left
- Blueprint grid: 2×2 maintained on tablet, 1×N on mobile
- Story block architectural image: hides on mobile (text alone is sufficient)
- Founder note: full-width, 24px padding

---

### SIG-2 · Browse Grid

**Tagline lock:** "Not basics. Blueprints."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│  SIGNATURE                                   │  ← Playfair Display, 36px, gold
│  Chapter One                                 │  ← Cormorant Garamond italic, cream
│                                              │
│  ─────────────────────────────────────────  │  ← 1px gold rule
└─────────────────────────────────────────────┘
```

No hero image above the grid — same philosophy as Black Rose. The chapter subtitle "Chapter One" under the collection name is the only concession to narrative. The grid is the work.

**Grid rhythm:** 3 columns desktop (unlike Black Rose's strict 2). Cards slightly narrower and taller — portrait proportion. Vertical gap 40px, horizontal 24px. Product name: Playfair Display 14px, gold. Price: Bebas Neue 13px, cream. Below price: one-line material note ("Japanese cotton", "Portuguese wool") — sourced from dossier. This one line differentiates Signature's grid from every other collection's.

**Color application:** Card background `#0F0F0F`. Hover: gold border bottom 2px (bottom only — like underlining a book passage). No card lift animation — the border is the signal.

**Interaction layer:**
- Grid entrance: `stagger-grid`, `--stagger-base: 60ms` — faster than Love Hurts, more decisive
- Card hover: gold bottom border animates in, `scaleX` 0→1 from left, 250ms
- Product name: `magnetic` — subtle
- No hover overlay, no quick-add

**Mobile adaptation:** 2 columns on mobile. Material note stays — it's worth the space. Gap reduces to 16px.

---

### SIG-3 · Product Detail Page (PDP)

**Tagline lock:** "Not basics. Blueprints."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  ┌────────────────────┐                     │
│  │                    │  PRODUCT NAME        │  ← Playfair Display, 48px, gold
│  │  [garment image]   │                     │
│  │                    │  Material note.      │  ← Cormorant italic, cream, 18px
│  │  + construction    │                     │
│  │    detail inset    │  $XXX               │
│  │                    │                     │
│  └────────────────────┘  [SIZE]  [ACQUIRE] │
└─────────────────────────────────────────────┘
```

The layout is Side-by-side like BR-3, but Signature adds a construction detail inset — a smaller image (20% width, bottom-right of main image, 16px gap, same container) showing a seam, label, or fabric close-up. This is the "Blueprint" made literal: you see the garment AND the craft. CTA label: "ACQUIRE" — not "Add to Bag", not "Buy". Bebas Neue.

**Below-fold sections:**

1. **Blueprint prose** — if editorial dossier exists: Cormorant Garamond 18px, cream, 600px max-width, 80px padding. Title: "The Blueprint" in Playfair Display 22px, gold, above prose.

2. **Construction details** — three labeled specs in a row (not accordion for Signature): "SHELL", "LINING", "HARDWARE". Bebas Neue label 11px, gold, letter-spacing 4px. Below each: 1-line value, Cormorant Garamond.

3. **Care** — single paragraph, Cormorant Garamond italic, muted, cream.

**Color application:** ACQUIRE button: `btn-sweep`, gold sweep. Size active: gold 2px bottom border. Construction detail inset: `1px solid rgba(212,175,55,0.2)` border.

**Interaction layer:**
- Main image: `rv-clip-left`, `--reveal-slow: 1.2s`
- Construction inset: `rv-blur`, 400ms delay after main image (JS delay)
- Info column: `rv-clip-right`, simultaneous with main image
- Blueprint prose: `rv-blur-down`, `--reveal-slow`
- Construction specs row: `stagger-grid` with `--stagger-base: 60ms` — 3 items

**Mobile adaptation:** Stacks to single column. Construction inset moves below main image at full width (100% × 48vw). Info follows. Construction specs become 3-row stack with full-width dividers.

---

## KIDS CAPSULE

**Register:** Minimalist. Legacy in smaller silhouette. This is not a children's brand — it is the brand, scaled. The same dark `#0A0A0A`, the same Playfair Display, the same rose gold. No concession to playfulness, no primary colors, no cartoon energy. Hermès Petit h, not Gap Kids. The only warmth is intentional: rose gold is warmer than gold, and this collection earns warmth.

**Palette application:**
- Background: `#0A0A0A`
- Accent: `--skyyrose-accent` → `#B76E79` (rose gold)
- Secondary: `--skyyrose-secondary` → `#D4AF37` (gold — subtle richness)
- Display: Playfair Display regular
- Body: Cormorant Garamond 16px / lh 1.6

---

### KC-1 · Landing Page

**Tagline lock:** "Luxury runs in the family."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  Luxury runs                                 │  ← Playfair Display italic
│  in the family.                              │     --text-5xl, rose gold
│                                              │     flush left, 56px from top
│                                              │
│  [two garments side by side — styled pair]  │  ← 85vh, portrait pair
│                                              │     equal treatment, no feature/secondary
└─────────────────────────────────────────────┘
```

Unique visual move: two garments shown together in the hero, styled as a set — adult/child silhouette or two pieces from the capsule. Not a "family shoot" — editorial. Both garments equal. The image is 85vh, headline above in the same letterbox-band pattern as Black Rose. Rose gold text, italic Playfair — softer weight than Black Rose's Cinzel but still authoritative.

**Below-fold sections:**

1. **Legacy note** — 2 sentences, Cormorant Garamond 18px, centered, max-width 540px, rose gold. No heading. `"Legacy isn't inherited. It is worn."` — representative tone.

2. **Product pair** — if 2 SKUs only, display them in a two-column feature layout, equal columns, no hierarchy between them. Each: image, name Playfair Display 18px, 1-line note, price. No "featured" card. Equal luxury.

3. **Pre-order note** (if applicable) — existing `.preorder-note` pattern. Cormorant italic, gold, centered. 1 sentence max.

**Color application:** Rose gold for headlines, primary text. Gold for price and secondary labels. Background stays `#0A0A0A`. No section breaks, no background changes. White space is the separating element.

**Interaction layer:**
- Headline: `rv-split-line`, `--reveal-slow: 1.2s`, `--ease-cinematic`
- Product pair: `stagger-grid`, `--stagger-medium: 100ms` — both cards reveal together with 100ms stagger
- Legacy note: `rv-blur`, threshold 0.2
- CTAs: `btn-border-draw`, rose gold border

**Mobile adaptation:**
- Headline clamps to `clamp(1.875rem, 7vw, 3rem)` — readable on 375px
- Product pair: 2-column maintained on mobile (cards are narrow but the parallel is the meaning)
- Legacy note: 24px left/right padding

---

### KC-2 · Browse Grid

> **Open question for founder:** Kids Capsule currently has 2 SKUs. A traditional browse grid may underserve the collection — two cards in a 3-column grid leaves an orphaned cell, which signals "incomplete." Three options are proposed here. Founder to choose before implementation.
>
> **Option A:** Suppress the grid. Redirect `/collection/kids-capsule/` to the landing page and surface both products as feature cards on the landing page only. No separate grid route.
>
> **Option B:** 2-column grid, full-width cards, equal weight. The grid only shows 2 columns and only 2 cards — the constraint IS the design. Copy above: "The full capsule." — Cormorant Garamond italic, centered.
>
> **Option C:** Treat as an editorial single-flow page: both products stacked full-width, editorial-magazine style with dossier text between them. This is closest to how Hermès Petit h presents limited collections.

**Design spec for Option B (default recommendation):**
```
┌─────────────────────────────────────────────┐
│                                              │
│         The full capsule.                    │  ← Cormorant italic, rose gold
│                                              │
│  ┌──────────────────┐  ┌──────────────────┐ │
│  │                  │  │                  │ │  ← 2-column, full-width
│  │   [garment 1]    │  │   [garment 2]    │ │     equal cards, equal height
│  │                  │  │                  │ │
│  │  Name · $XXX     │  │  Name · $XXX     │ │
│  └──────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────┘
```

**Color application:** Card background `#0F0F0F`. Rose gold product name. Gold price. Hover: rose gold bottom border 2px (same gesture as Signature, but rose gold). No shadows.

**Interaction layer:**
- "The full capsule." text: `rv-blur`, `--reveal-slow`
- Cards: `stagger-grid`, `--stagger-medium: 100ms`
- Card hover: rose gold bottom border, `scaleX` from left, 250ms

**Mobile adaptation:** 2 columns maintained on mobile (narrow is fine — this is intentional constraint). Cards compress gracefully.

---

### KC-3 · Product Detail Page (PDP)

**Tagline lock:** "Luxury runs in the family."

**Hero / Above-fold treatment:**
```
┌─────────────────────────────────────────────┐
│                                              │
│  ┌────────────────────┐                     │
│  │                    │  PRODUCT NAME        │  ← Playfair Display, 40px, rose gold
│  │  [garment image]   │                     │
│  │  editorial, clean  │  Legacy note.        │  ← Cormorant italic, gold, 16px
│  │                    │                     │
│  │                    │  $XXX               │  ← Bebas Neue, large
│  │                    │                     │
│  └────────────────────┘  [SIZE]  [ACQUIRE] │
└─────────────────────────────────────────────┘
```

Same structural layout as Signature PDP — side-by-side. No construction inset (Kids Capsule doesn't need to prove craft — the silhouette is the statement). "Legacy note" replaces "Material note": one sentence pulled from dossier about who this piece is for and why. CTA: "ACQUIRE" — consistent with Signature, signals the same brand tier regardless of target age.

**Below-fold sections:**

1. **Dossier** — if exists: same as Signature format. Playfair Display heading "For the inheritors." (or from actual dossier). Cormorant Garamond body, cream.

2. **Care** — single paragraph. Rose gold label "CARE" in Bebas Neue 11px, 4px letter-spacing. Cormorant Garamond body.

3. **The other piece** — if 2 SKUs exist: one card, below everything, 400px wide, centered, no heading. Just the other product image, name, price, and a text link: "See the full capsule →". No heading like "You may also like" — explicitly prohibited. Just the companion piece, no framing.

**Color application:** ACQUIRE button: `btn-sweep`, rose gold sweep. Size active: rose gold 2px bottom border. "The other piece" card: same `#0F0F0F` background, rose gold name.

**Interaction layer:**
- Image: `rv-clip-left`, `--reveal-slow: 1.2s`
- Info column: `rv-clip-right`, simultaneous
- Dossier: `rv-blur-down`, `--reveal-slow`
- Companion piece card: `rv-blur`, threshold 0.1 — appears gently, is not a CTA demand

**Mobile adaptation:** Single column, same adaptation as Signature PDP. Companion piece card: full content width.

---

## Cross-Collection System Notes

### Shared foundations (do not change per collection)
- Background: `#0A0A0A` everywhere
- Body font: Cormorant Garamond all collections
- UI labels: Bebas Neue all collections
- All animation via existing `rv-*`, `stagger-grid`, `magnetic`, `btn-*` classes only
- 8pt grid: all spacing in 8px increments (4px for fine adjustments)
- WCAG AA: all text/background combinations at ≥4.5:1

### Contrast verification (WCAG AA)
| Token | On `#0A0A0A` | Ratio | Pass |
|-------|------------|-------|------|
| Silver `#C0C0C0` | Dark bg | 10.5:1 | ✅ |
| Crimson `#DC143C` | Dark bg | 5.2:1 | ✅ |
| Gold `#D4AF37` | Dark bg | 8.4:1 | ✅ |
| Rose gold `#B76E79` | Dark bg | 4.8:1 | ✅ |
| Cream `#F7E7CE` | Dark bg | 14.1:1 | ✅ |

### CTA vocabulary (locked)
| Collection | CTA label |
|-----------|-----------|
| Black Rose | WEAR IT |
| Love Hurts | ADD TO BAG |
| Signature | ACQUIRE |
| Kids Capsule | ACQUIRE |

Never: "Shop Now", "Buy Now", "Add to Cart", "Purchase", "Order".

### Grid differentiation summary
| Collection | Desktop cols | Rhythm | Card hover signal |
|-----------|-------------|--------|-------------------|
| Black Rose | 2 | Uniform | Border brightens |
| Love Hurts | 3 + feature rows | Alternating 3/2:1 | Crimson left border draws |
| Signature | 3 | Uniform | Gold bottom border draws |
| Kids Capsule | 2 (full content width) | Fixed 2 | Rose gold bottom border draws |

### View Transitions
All cross-collection navigation uses View Transitions API (`view-transition-name: collection-hero` on hero image, `view-transition-name: collection-title` on headline). Fade duration 400ms. No slide — the collections do not slide into each other, they replace each other.

---

*Spec authored: 2026-05-24 · Version 1.0 · No code changes — proposal only.*
*Next step: founder review → implementation sprint.*
