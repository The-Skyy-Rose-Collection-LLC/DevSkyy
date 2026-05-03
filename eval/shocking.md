# Eval — Shocking

> The user said "I want to be shocked genuinely shocked not impressed." This file defines what counts as shocked. Each criterion must be observable, not vibes-based. If the criterion is too soft to measure, rewrite it until it isn't.

## The bar

A first-time visitor lands on skyyrose.co. They've used Net-a-Porter, ASOS, SSENSE, Highsnobiety, and probably a Vogue feature page. Within 90 seconds, they observe at least 3 things they have NEVER seen on a WordPress storefront before — and at least 1 thing they've never seen on any storefront, period.

Anything less is "impressed", not "shocked".

---

## Observable shock criteria — one PASS per row earns a "shock point"

A shipped theme passes when it earns at least 8 shock points across the 12 criteria below.

### Architectural shock (the "first of its kind" claims)

| ID | Criterion | Test |
|----|-----------|------|
| SHK1 | Visit immersive page → Three.js scene with the actual Bay Bridge / Golden Gate / cathedral renders, not a static photo | Visual check + perf trace shows real WebGL context |
| SHK2 | Click WebXR button on Vision Pro / Quest 3 → step inside the scene, walk around products | Manual on real device |
| SHK3 | On a product page → click "Try on" → upload a photo → 4-model AR result returns in < 8s | Manual + Vercel timing |
| SHK4 | Type a vibes query in search ("dark academia for late October") → semantic results return relevant products, not just keyword matches | Manual + relevance test |
| SHK5 | Visit during a drop → countdown → unlock → live queue position UI updates in real-time as others join | Manual during scheduled drop |
| SHK6 | Open product narrative variant → scroll experience tells a 4-chapter story that ends at "add to cart" CTA — not a tabbed product page | Visual check |

### Craft shock (the polish that makes a buyer say "no way they did that on WordPress")

| ID | Criterion | Test |
|----|-----------|------|
| SHK7 | First page load: zero flash of unstyled content, zero layout shift, fonts arrive instantly because they're self-hosted | DevTools Performance + CLS = 0 |
| SHK8 | Mobile gallery: swipe horizontally to switch products WITHIN the same view (not a back-button-required navigation) — feels native | Manual on iOS Safari |
| SHK9 | Block-based cart and checkout look as designed as the rest of the theme — not generic WooCommerce defaults | Visual check vs. Phase 4 design ref |
| SHK10 | Three.js scenes hit 60fps on M1 MacBook Air with five other tabs open | Chrome FPS meter |

### Brand shock (the things that ONLY this brand could ship)

| ID | Criterion | Test |
|----|-----------|------|
| SHK11 | The Skyy avatar appears as a hidden easter egg in all 3 immersive worlds; finding all 3 unlocks an animated intro that introduces the brand without text | Manual playthrough |
| SHK12 | Voice across the entire site sounds like SkyyRose and nobody else — Oakland, "the Town", "Luxury Grows from Concrete" — not generic luxury copy from a template | Brand voice audit per `eval/brand.md` |

---

## Anti-shock — automatic FAIL if any apply

A buyer is NOT shocked if they observe any of:

| ID | Anti-criterion | Why this fails |
|----|----------------|----------------|
| ANT1 | Generic homepage with rotating hero carousel + "Shop Now" button | Every theme has this. |
| ANT2 | Stock fonts (Inter, Roboto, Helvetica system stack) without intentional pairing | Default = invisible. |
| ANT3 | Cart-fragments AJAX spinner default WC look | Looks like every other WP shop. |
| ANT4 | "Featured Collections" / "Best Sellers" / "Recently Viewed" rails without visual differentiation | Common WC pattern. |
| ANT5 | Blue / purple / "AI Lila" gradient anywhere in the design | Generic AI aesthetic per `eval/brand.md` and `design-taste-frontend` rule. |
| ANT6 | Glassmorphism used as decoration rather than functional layering | Anti-slop rule. |
| ANT7 | More than 2 CTAs above the fold on any page | Decision paralysis. |
| ANT8 | Generic stock photography of models | Brand DNA fails. |
| ANT9 | Footer is a 5-column "Shop / About / Help / Legal / Newsletter" wall | Default theme footer. |
| ANT10 | Mobile menu is a hamburger that opens a vertical text list | Boring / responsive-not-native. |

If any anti-criterion is hit, that section needs rework before shock evaluation can complete.

---

## How to test "shock"

Once theme is built:

1. **Cold-eye test** — find someone who hasn't seen the build. Show them home → collection → product → cart → checkout in 90 seconds. Ask them to write down 3 things they noticed. If "WebGL", "AR try-on", "story product page", "live drop queue", or "vibes search" appear unprompted in their notes → SHK criterion passes for that feature.

2. **Buyer test** — find someone who has bought a fashion theme on ThemeForest. Walk them through the build. Ask: "would you have paid $150 for this?" If yes with no hedging → marketplace shock validated. If "I've seen [feature X] before on [theme Y]" → that feature didn't earn its shock point.

3. **Specific checklist** — manually verify each SHK1-SHK12 criterion above with the prescribed test method.

4. **Anti-shock sweep** — verify zero ANT criteria are present.

5. **Score** — if ≥ 8 shock points AND zero anti-shock criteria, theme passes shock eval.

---

## Notes on what "shock" doesn't mean

- Shock isn't aggressive UI (overdrive without restraint)
- Shock isn't novelty for its own sake (a feature that doesn't help the user can't shock them positively)
- Shock isn't more features — most of the criteria above are about depth, not surface area

The pattern: take something users expect, and either:
1. Replace it with something better and unprecedented (immersive worlds vs. hero carousel)
2. Hold the line where everyone else is sloppy (block cart/checkout polish where every other theme fails)
3. Reveal a layer they didn't know was possible (WebXR session, AR try-on, semantic search)

---

## Final eval

This file is the user's stated bar. Every shipped feature passes through this filter before it counts as done. If a phase hits all functional criteria but earns 0 shock points → that phase didn't actually meet the user's intent; rebuild before declaring complete.
