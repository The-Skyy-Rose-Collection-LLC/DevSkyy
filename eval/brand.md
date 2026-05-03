# Eval — Brand Voice & Visual Constraints

> The `skyyrose-brand-dna` skill is the source of truth. This file translates its rules into observable criteria. Every shipped surface is graded against these. The brand is what makes the difference between "luxury fashion theme" and "SkyyRose theme."

## Voice — universal rules

| ID | Criterion | Method |
|----|-----------|--------|
| V1 | Tagline is "Luxury Grows from Concrete." — exactly this string, nowhere modified | grep |
| V2 | "Where Love Meets Luxury" — RETIRED. Must appear ZERO times | grep — must return 0 results |
| V3 | "the Bay Area" — replaced with "the Town" everywhere except formal address contexts | grep + manual |
| V4 | Banned generic-luxury phrases (zero occurrences in shipped copy): "premium" (standalone), "exclusive" (standalone), "high-quality" (standalone), "elevated", "curated experience" | grep |
| V5 | "Oakland" or "East Oakland" appears at least once on home page or about page | grep |
| V6 | Founder's name (Corey Foster) appears on about page or origin sections | grep |
| V7 | Founder's daughter (Skyy Rose) appears in brand story | grep |
| V8 | Voice is direct, declarative — no "we hope you'll find", "perhaps you might consider", or other hedging | manual review |

## Voice — per collection

### Black Rose (gothic / Oakland defiance)
| ID | Criterion | Method |
|----|-----------|--------|
| BR1 | Black Rose copy uses Cinzel display font (or close fallback) | CSS audit |
| BR2 | Tone: defiant, refined, quietly menacing — not aggressive | Editorial review |
| BR3 | References to the Bay Bridge, Oakland night, concrete, silver, deep black | grep + content review |
| BR4 | No pink, no rose-gold accents on Black Rose surfaces (unless cross-collection nav) | CSS audit + visual |
| BR5 | Color palette: silver `#C0C0C0`, deep black `#0A0A0A`, charcoal | Hex check |

### Love Hurts (B&B / passionate / vulnerable)
| ID | Criterion | Method |
|----|-----------|--------|
| LH1 | Love Hurts copy uses Playfair Display | CSS audit |
| LH2 | Tone: emotional, vulnerable, raw — but never melodramatic | Editorial review |
| LH3 | Beauty and the Beast references (rose dome, cathedral, "every petal tells a story") | grep |
| LH4 | "Hurts" is acknowledged as the founder's family name when context permits | Editorial check |
| LH5 | Color palette: crimson `#DC143C`, rose, deep red | Hex check |

### Signature (Bay Area / golden / everyday luxury)
| ID | Criterion | Method |
|----|-----------|--------|
| SIG1 | Signature copy uses Playfair Display + Bebas Neue accents | CSS audit |
| SIG2 | Tone: confident, golden, foundational — wardrobe staples reframed | Editorial review |
| SIG3 | Golden Gate / SF references on Signature surfaces | grep |
| SIG4 | Color palette: gold `#D4AF37`, warm whites, charcoal | Hex check |

### Kids Capsule (playful / tender / mini-me)
| ID | Criterion | Method |
|----|-----------|--------|
| K1 | Kids Capsule uses Cormorant Garamond body, playful display | CSS audit |
| K2 | Tone: warm, playful, NEVER condescending to children OR parents | Editorial review |
| K3 | "Mini-me" / "Luxury runs in the family" / "next generation" framing | grep |
| K4 | Color palette: rose-gold `#B76E79`, soft pinks, warm tones | Hex check |

## Visual — typography

| ID | Criterion | Method |
|----|-----------|--------|
| TYP1 | Cinzel, Playfair Display, Cormorant Garamond, Bebas Neue, Inter all loaded as woff2 from `/assets/fonts/` | Network panel — zero `fonts.googleapis.com` |
| TYP2 | Inter is the system fallback font ONLY — never a primary display choice | CSS audit |
| TYP3 | No "Satoshi" font (was reverted per learnings) | grep + CSS audit |
| TYP4 | Font sizes follow a typographic scale (1.250 / 1.333 / 1.414) — not arbitrary px values | CSS audit |
| TYP5 | Line height ≥ 1.5 on body copy | CSS audit |
| TYP6 | Headings have explicit `font-weight` (no relying on browser bold) | CSS audit |
| TYP7 | Per-collection font pairing matches BR / LH / SIG / K rules above | Visual + CSS |

## Visual — color

| ID | Criterion | Method |
|----|-----------|--------|
| COL1 | Brand tokens defined in `assets/css/design-tokens.css` (rose-gold, dark, gold, crimson, silver) | File check |
| COL2 | No hex values hardcoded outside design-tokens.css — all colors via CSS variables | grep |
| COL3 | No "AI Lila" — no purple gradient (`#a78bfa` → `#818cf8`) on any surface | CSS audit |
| COL4 | No Bootstrap default blue (`#0d6efd`) | CSS audit |
| COL5 | Per-collection palette swap via `data-collection` attribute, NOT class names | DOM + CSS audit |
| COL6 | Color combinations meet WCAG 2.2 AA contrast (see `eval/marketplace.md` ACC10) | axe |

## Visual — layout & motion

| ID | Criterion | Method |
|----|-----------|--------|
| LAY1 | Generous macro-whitespace (`py-24` to `py-40` per `high-end-visual-design`) on chrome surfaces | Visual + CSS |
| LAY2 | Dense working areas (forms, product detail) use Tailwind / utility scale | CSS audit |
| LAY3 | Bento grids are gapless where appropriate (`gap-0`) | CSS audit |
| LAY4 | No glassmorphism as decoration — only as functional layering | Visual review |
| LAY5 | No gradient text on display headings (anti-slop rule) | CSS audit |
| LAY6 | No "side-stripe" decorative borders on cards | Visual review |
| LAY7 | Motion respects `prefers-reduced-motion: reduce` everywhere | Manual |
| LAY8 | GSAP only on permitted templates (immersive / preorder / about / experiences) | Code audit |
| LAY9 | Other pages use IntersectionObserver scroll-reveal (`.col-reveal`, `.lp-rv`) — NOT GSAP | Code audit |

## Visual — imagery

| ID | Criterion | Method |
|----|-----------|--------|
| IMG1 | Product photography is real product imagery (renders or photos), not stock | Manual |
| IMG2 | Editorial / lifestyle shots feature culturally accurate, non-stereotypical representation | `Cultural Intelligence Strategist` + `Inclusive Visuals Specialist` review |
| IMG3 | Hero images and overlays match per-collection palette and atmosphere | Visual review |
| IMG4 | Brand logos load correctly across all collections (`brand-logos/`) | Visual + 404 check |
| IMG5 | Skyy avatar canonical reference is `assets/images/mascot/skyy-canonical.jpeg` (no other) | grep |

## Visual — micro-interactions (`delight` skill domain)

| ID | Criterion | Method |
|----|-----------|--------|
| MIC1 | Hover states on cards feel intentional (lift, tint, reveal) — not default browser hover | CSS audit + visual |
| MIC2 | Button press states give haptic-feeling visual feedback | Visual |
| MIC3 | Empty states (cart, wishlist, search) include personality copy + CTA — not generic "No items" | Manual |
| MIC4 | Loading states avoid generic spinners — use brand-aware skeletons or shimmer | Visual |
| MIC5 | Form errors are warm and helpful, not aggressive ("Looks like that's not quite a valid email") | Editorial |
| MIC6 | Skyy avatar easter egg present in immersive worlds (CLAUDE.md note) | Manual playthrough |

---

## Brand voice audit protocol

For every shipped page / surface:

1. Run `grep` against banned phrases (V2, V4) on the rendered HTML
2. Run `grep` for required brand markers (V1, V3, V5, V6, V7) where appropriate
3. Per-collection check: surface within Black Rose context uses Cinzel + dark palette + Oakland references
4. Read final copy aloud — does it sound like SkyyRose, or like a generic luxury template? If unclear → run `skyyrose-content-engine` rewrite
5. Cross-check with `skyyrose-brand-dna` skill's banned-phrase list

Block phase exit on any V1-V8 violation. Per-collection violations (BR, LH, SIG, K) require revision but can ship if cross-collection neutrality is preserved.

---

## What a brand-DNA failure looks like

- A button that says "Shop Premium Collection" → V4 fail (banned word "premium" standalone)
- "Discover the Bay Area's hottest streetwear" → V3 fail (use "the Town")
- A hero with "Where love meets luxury" → V2 fail (retired tagline)
- A Black Rose product card with rose-gold accent borders → BR4 fail (no rose-gold on BR surfaces)
- An empty cart that says "Your cart is empty" → MIC3 fail (no personality)
- A purple gradient anywhere → COL3 + ANT5 fail
