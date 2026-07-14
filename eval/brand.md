---
name: Brand Voice & Visual Adherence (skyyrose-brand-dna in eval form)
specified_by: [wp: §2 brand canon, §1.3 banned elements]
phase: 0
test_command: node scripts/measurement/run-brand-eval.js
pass_threshold: 0 banned phrases, palette match on every surface, voice rules honored
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Brand Voice & Visual Adherence

Operationalizes WP §2 (brand canon) and WP §1.3 (banned elements) as a machine-checkable + human-judgment rubric. Every surface is evaluated; failures gate the surface from merging.

## Voice rules (banned phrases — fail any of these = fail this row)

| Banned phrase / pattern | Reason | Replacement |
|------------------------|--------|-------------|
| "the Bay Area" | WP §2.4 — Skyyrose says "The Town" or "Oakland" | "The Town" / "Oakland" |
| "iconic" | WP §2.4 — overused, generic | Specific descriptor of why the thing matters |
| "elevated" | Same | Show, don't say |
| "curated" | Same | "Selected" / "chosen" or just describe the selection |
| "luxe" | Same | The brand IS luxury — saying "luxe" cheapens it |
| "drip" | Same — unless irony is doing work | The garment, by name |
| Exclamation marks in product copy or marketing | WP §2.4 — Skyyrose doesn't shout | Period. Or em-dash. |
| "you deserve this" / "treat yourself" | WP §2.4 — the customer doesn't need permission | Just describe the garment |
| Apologies for price | WP §2.4 — never explain or apologize for the price | Confidence in the price as the price |
| Explaining Oakland to outsiders | WP §2.4 — if they don't get it, the writing is for them anyway | Reference Oakland specifics without footnotes |

## Visual rules (palette + design system)

| Rule | Pass criterion |
|------|----------------|
| Color palette restricted to: `#B76E79` rose-gold, `#0A0A0A` dark, `#D4AF37` gold, `#DC143C` crimson, `#C0C0C0` silver, plus 5 grays + semantic | No off-system colors anywhere on customer-facing surfaces. Brand black (`#0A0A0A`) is the *only* black; brand white the only white. |
| Type system: Archivo (display/hero headings, all collections), Hanken Grotesk (body/UI), Anton (UI caps/accent), Cinzel (engraved-caps accent), Inter (system fallback) — see `SOT.md` → `typography.json` | All font families self-hosted woff2, declared in `theme.json` Font Library + `assets/css/fonts.css`; zero Google Fonts CDN |
| Spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128 token scale | No arbitrary spacing values |
| Radius: 0, 2, 4, 8, 16, full | Most surfaces 0 or 2; 8+ only when intentional |
| Shadow: none / subtle / soft / lifted (4 named tokens) | No drop-shadow stacks |
| Motion: 150 / 250 / 400 / 800ms; 4 named curves | No bespoke transitions |

## Brand-NOT rules (WP §2.3)

| Anti-pattern | Where flagged | Pass criterion |
|--------------|---------------|----------------|
| Athleisure framing | Hero + landing copy | No "performance," "active," "gym-ready" framing |
| Influencer streetwear | Hero + landing copy | No "drop-shipped graphic tees," no celebrity endorsement core |
| Generic luxury (minimalism = sophistication) | Visual + copy | Color, texture, grit present — not pure white-on-white minimalism |
| Sad-aspirational | Copy | Tone is "be more yourself," not "be someone else" |

## Banned elements (WP §1.3 — fail any = fail this row)

For each surface:

- [ ] No centered hero with full-width photo + headline + "Shop Now" button
- [ ] No 4-column equal-spaced product grid with white background
- [ ] No generic stock-photo style imagery
- [ ] No stock badge animations (pulsing dots, generic carousel arrows)
- [ ] No "Lorem ipsum" anywhere
- [ ] No default WooCommerce styling on customer-facing surfaces
- [ ] No trust badge clusters at page bottom (Visa/MC/Amex logos in a row)
- [ ] No "Limited Time Offer!" countdown timers as homepage element
- [ ] No stock testimonial layouts (avatar + name + quote in card)
- [ ] No free shipping bars in colors that fight the design
- [ ] No cookie banners taking >3s to dismiss

## "Would Corey wear this?" filter (WP §7.3)

Every UI element, copy block, or visual passes this filter before ship:

- "Yes, specifically because [reason]" → ship
- "I think so" → not ready; iterate

This is the single most important taste filter on every design decision. It is subjective but binding.

## Test command

```bash
node scripts/measurement/run-brand-eval.js
```

Three checks:

1. **Banned-phrase grep** across all PHP partials, JS strings, theme.json, page meta — exits non-zero on any hit
2. **Palette compliance** check — extracts every color token used in `assets/css/*.css` and compares against the locked palette
3. **Manual judgment review** — flags Phase 4/5/6/7 surfaces for `critique` skill walkthrough; collects human-judgment scores

## Per-surface row format

```yaml
---
surface: <page slug or component>
banned_phrase_violations: <list>
palette_violations: <list>
banned_element_violations: <list>
not_brand_pattern_violations: <list>
would_corey_wear_this: <YES_BECAUSE: <reason> | I_THINK_SO | NO_BECAUSE: <reason>>
last_evaluated: <YYYY-MM-DD>
status: <PASS | FAIL>
---

<prose: any nuance, any judgment-call rationale>
```

## Phase entry checklist

- Phase 0 establishes the rubric (this file) and seeds `eval/banned-elements.md` with the full §1.3 list
- Phase 4 per-template work runs this rubric per page
- Phase 6.8 brand consistency sub-phase runs this sitewide via `Brand Guardian` agent
- Phase 7 ship-check re-runs across all surfaces; gate fails on any `would_corey_wear_this != YES_BECAUSE`
