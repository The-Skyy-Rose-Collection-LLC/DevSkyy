# v2.html Fix Manifest — Synthesized from 4 audit reports

**Pipeline:** `luxury-mockup-pipeline` (see `~/.claude/skills/luxury-mockup-pipeline/SKILL.md`)
**Date:** 2026-05-25
**Mockup:** `docs/brand/design-mockups/v2.html`
**Executor:** Senior Developer agent
**Verifier:** inline + final-review agent

## Source audits

1. `docs/brand/design-mockups/v2-polish-mix.md` (UX Architect)
2. `docs/brand/design-mockups/v2-visual-fixes.md` (UI Designer)
3. `docs/brand/design-mockups/v2-canon-audit.md` (Brand Guardian)
4. `docs/brand/design-mockups/v2-asset-audit.md` (Frontend Developer)

## Execution order (priority tiers)

Senior Developer executes tiers in order. Within a tier, fixes are atomic per-fix-group with own commit.

---

## TIER 0 — Critical UX blockers (page is broken right now)

### FIX-T0-01 · Remove duplicate `min-height: 100vh` from `.hero__inner`

**Source:** UI Designer FIX-08
**Symptom:** Both `.hero` and `.hero__inner` declare `min-height: 100vh` — the hero becomes ~200vh tall, pushing below-fold content too far.
**File:** `docs/brand/design-mockups/v2.html`
**Fix:** Find `.hero__inner` rule. Remove the `min-height: 100vh;` line. Keep `padding: var(--space-24) var(--space-8);` and `display: flex; flex-direction: column; justify-content: space-between;`.
**Verify:** Open in browser. Hero should fill exactly one viewport (100vh), not two.
**Commit:** `fix(v2-mockup): hero inner remove duplicate min-height (was 200vh)`

---

## TIER 1 — Brand canon violations (P0/P1)

### FIX-T1-01 · BR cover photo swap (P0-A)

**Source:** Brand Guardian P0-A
**Symptom:** `#br-cover` uses `assets/branding/hero/beauty-and-beast-*.webp` — that's the Love Hurts canonical hero environment per `docs/brand/asset-hierarchy.md`. Love Hurts photo on Black Rose page = canon violation.
**Fix:** In the `#br-cover` `<picture>` block, replace all 4 `beauty-and-beast-{480,768,1280,1680}w.webp` paths with `forbidden-midnight-{480,768,1280,1680}w.webp`. Update the `<img alt="...">` to "Black Rose cover photograph — Oakland nightscape".
**Verify:** `grep -c beauty-and-beast docs/brand/design-mockups/v2.html` → 0.
**Commit:** `fix(v2-mockup): BR cover photo canon — beauty-and-beast (LH) → forbidden-midnight (BR)`

### FIX-T1-02 · BR cover tagline canon (P1-B)

**Source:** Brand Guardian P1-B
**Symptom:** BR cover tagline "Built for those who move through / darkness like it's home." is INVENTED — no source in canon docs.
**Fix:** Replace with verbatim BR canon from `docs/brand/collection-stories.md`:
> Every piece in Black Rose is<br><span class="cover__tagline-accent">the concrete answering back.</span>

Keep the same markup structure (cover__tagline + cover__tagline-accent span); only the text changes.

**Verify:** `grep -c "concrete answering back" docs/brand/design-mockups/v2.html` → 1; `grep -c "darkness like it" docs/brand/design-mockups/v2.html` → 0.
**Commit:** `fix(v2-mockup): BR cover tagline → verbatim canon "concrete answering back"`

### FIX-T1-03 · BR palette accent swap to silver (P1-C)

**Source:** Brand Guardian P1-C
**Symptom:** BR-specific surfaces (`#br-cover`, `#br-hero`, `#br-voice`, `#br-spread`) use `--sr-rose-gold` accent throughout. Black Rose canon accent is Silver `#C0C0C0`.
**Fix:** Add a `.br-page` scoped override block at the END of the `<style>` (before `</style>`) that flips rose-gold → silver for child elements:

```css

  /* === BR collection palette override (per canon — silver, not rose-gold) === */
  .br-page .cover__sr-graffiti { color: var(--sr-silver); }
  .br-page .cover__tagline-accent { color: var(--sr-silver); }
  .br-page .voice__quote .line-2 {
    color: var(--sr-silver);
    text-shadow: 0 0 24px rgba(192, 192, 192, 0.3);
  }
  .br-page .voice__attribution {
    color: rgba(192, 192, 192, 0.75);
    border-top-color: rgba(192, 192, 192, 0.25);
  }
  .br-page .spread__tile-label { color: var(--sr-silver); }
  .br-page .spread__tile:focus-visible,
  .br-page .spread__tile:hover {
    box-shadow: 0 0 0 2px rgba(192, 192, 192, 0.7);
  }
```

(Also add `--sr-silver-rgb: 192, 192, 192;` to `:root` typography block if needed for any future rgba() usage.)

**Verify:** Browser visual — BR page accents render in silver, homepage stays rose-gold.
**Commit:** `fix(v2-mockup): BR collection palette → silver accent per canon`

### FIX-T1-04 · Homepage hero photo alignment (P0-B)

**Source:** Brand Guardian P0-B
**Symptom:** `#home-hero` uses `luxury-nighttime` (Signature canon photo) as background while displaying `br-brand-script` (BR lockup). Two collections' assets on one surface = mixed messaging.
**Fix:** Replace `luxury-nighttime-*.webp` with `forbidden-midnight-*.webp` in the `#home-hero` `<picture>` (same pattern as BR hero already does). Update alt to "Black Rose drop story — Oakland industrial scene".

Note: This means `forbidden-midnight` appears on 3 surfaces (home cover, home hero, BR cover after FIX-T1-01, BR hero). Visual repetition — acceptable per "BR-feature drop story". User can review in Stage 3.

**Verify:** `grep -c luxury-nighttime docs/brand/design-mockups/v2.html` → 0; `grep -c forbidden-midnight docs/brand/design-mockups/v2.html` → 16 (4 srcset × 4 surfaces).
**Commit:** `fix(v2-mockup): home hero photo canon — luxury-nighttime → forbidden-midnight (BR alignment)`

---

## TIER 2 — Visual fidelity (UI Designer fixes)

### FIX-T2-01 · F04 + F08 spread grid restructure with `.spread__tile--brand` variant

**Source:** UI Designer FIX-01
**Symptom:** 3-column grid with `grid-row: 1/3` large tile produces empty cells at certain breakpoints. Logo-hero assets (different aspect ratios) get cropped weirdly inside uniform tiles with `object-fit: cover`.
**Fix:**

1. Modify `.spread__grid` to be 2-column on F04 home spread (already present in `.br-spread`).
2. Add new class `.spread__tile--brand` for tiles that show brand marks (vs product photography):

```css
  .spread__tile--brand {
    background: var(--sr-charcoal);
  }
  .spread__tile--brand .spread__tile-img {
    object-fit: contain;
    padding: var(--space-8);
    opacity: 1;
  }
  .spread__tile--brand:hover .spread__tile-img { opacity: 1; }
```

3. Apply `.spread__tile--brand` to all 4 tiles in `#home-spread` (these are brand marks, not products) and to br-005's monogram tile (`black-rose-monogram-sr.jpg`).
4. Keep `.spread__tile` (cover) for product photography tiles (br-001, br-004, br-008).

**Verify:** Visual — brand marks render contained with padding, products fill tile via cover.
**Commit:** `fix(v2-mockup): spread tile variant for brand marks (object-fit: contain + padding)`

### FIX-T2-02 · Hero lockup drop-shadow reduce

**Source:** UI Designer FIX-03
**Symptom:** Compounded shadows — CSS `drop-shadow(0 6px 24px rgba(0,0,0,0.6))` stacks on the asset's baked-in dimensional treatment. Muddy.
**Fix:** Change `.hero__lockup img` filter to:
`filter: drop-shadow(0 2px 10px rgba(0,0,0,0.35));`
**Verify:** Visual — lockup edges sharper, less halo.
**Commit:** `fix(v2-mockup): hero lockup drop-shadow reduced — less muddy halo`

### FIX-T2-03 · BR hero lockup wider on BR page

**Source:** UI Designer FIX-04
**Symptom:** BR page hero uses same `clamp(280px, 50vw, 720px)` width as homepage. Spec says BR's home turf — lockup should assert more.
**Fix:** Add:

```css
  .br-page .hero__lockup img { width: clamp(320px, 60vw, 880px); }
  .br-page .hero__lockup.is-visible img { transform: scale(1.04); }
```

**Verify:** Visual — BR hero lockup ~20% larger than homepage hero lockup.
**Commit:** `fix(v2-mockup): BR hero lockup wider (60vw vs 50vw) per spec`

### FIX-T2-04 · Hover state strengthen on `.spread__tile`

**Source:** UI Designer FIX-05
**Symptom:** `transform: scale(1.015)` + 50% alpha ring is below the threshold of intentional luxury interaction.
**Fix:** Replace `.spread__tile:hover` rule with:

```css
  .spread__tile:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 36px rgba(0,0,0,0.4), inset 0 0 0 1px rgba(var(--sr-rose-gold-rgb), 0.7);
  }
```

(BR-page variant from FIX-T1-03 overrides the inset ring color to silver via the .br-page scoped block.)

**Verify:** Hover — tile lifts up with shadow + rose-gold (or silver on BR) ring.
**Commit:** `fix(v2-mockup): spread tile hover — translateY lift + ring (luxury interaction grade)`

---

## TIER 3 — Polish layer mix-ins (UX Architect — production homepage polish)

### FIX-T3-01 · Ken Burns hero zoom

**Source:** UX Architect T1-A
**Symptom:** Hero photos are static. Live homepage uses slow zoom+drift to make the hero feel cinematic.
**Fix:** Add keyframe + apply to `.hero__bg` and `.cover__photo`:

```css
  @keyframes heroZoom {
    0% { transform: scale(1.05) translateY(0); }
    100% { transform: scale(1.1) translateY(-2%); }
  }
  .hero__bg, .cover__photo {
    animation: heroZoom 30s var(--ease-in-out) infinite alternate;
    will-change: transform;
  }
  @media (prefers-reduced-motion: reduce) {
    .hero__bg, .cover__photo { animation: none !important; }
  }
```

Note: The parallax JS in Task 11 already applies `translate3d(0, Ypx, 0)` to `.hero__bg.parallax` on scroll. Make sure the keyframe + scroll-translate compose correctly (the scroll-handler will override `transform` during scroll; on idle the keyframe runs). If conflict observed in QA, parallax JS should wrap its transform to include the zoom: `transform: translate3d(0, Ypx, 0) scale(1.05)`.

**Verify:** Browser idle — hero zooms slowly. Reduced-motion — static.
**Commit:** `feat(v2-mockup): ken burns hero zoom (live homepage polish mix-in)`

### FIX-T3-02 · Film grain overlay

**Source:** UX Architect T1-B
**Symptom:** Surfaces read "digital" not "developed". Live homepage uses film grain canvas overlay at 3.5% opacity for editorial-print register.
**Fix:** Add a fixed-position `<canvas id="grain">` element early in body + JS to render noise:

CSS:
```css
  .grain-overlay {
    position: fixed; inset: 0;
    pointer-events: none;
    z-index: 90;
    opacity: 0.035;
    mix-blend-mode: overlay;
  }
```

HTML — add right after opening `<body>`:
```html
<canvas class="grain-overlay" id="grainCanvas" aria-hidden="true"></canvas>
```

JS — add inside the existing IIFE (after the parallax block, before closing `})();`):
```javascript

  // === Film grain overlay ===
  if (!prefersReduced) {
    var grain = document.getElementById('grainCanvas');
    if (grain) {
      var gctx = grain.getContext('2d');
      function sizeGrain() {
        grain.width = window.innerWidth;
        grain.height = window.innerHeight;
      }
      function renderGrain() {
        var w = grain.width, h = grain.height;
        var img = gctx.createImageData(w, h);
        var data = img.data;
        for (var i = 0; i < data.length; i += 4) {
          var v = (Math.random() * 255) | 0;
          data[i] = v; data[i+1] = v; data[i+2] = v; data[i+3] = 255;
        }
        gctx.putImageData(img, 0, 0);
      }
      sizeGrain();
      renderGrain();
      window.addEventListener('resize', function() {
        sizeGrain();
        renderGrain();
      }, { passive: true });
      // Re-render at low rate (2fps) to add live shimmer without burning CPU
      setInterval(renderGrain, 500);
    }
  }
```

**Verify:** Subtle grain visible across all surfaces. Reduced-motion — grain rendered once, no shimmer.
**Commit:** `feat(v2-mockup): film grain overlay (editorial-print register)`

### FIX-T3-03 · Editorial image filter

**Source:** UX Architect T1-C
**Symptom:** Photography reads as e-commerce catalog (oversaturated, too bright) rather than editorial lookbook.
**Fix:** Add ONE global filter rule:

```css
  .cover__photo, .hero__bg, .spread__tile-img {
    filter: contrast(1.04) saturate(0.94) brightness(0.97);
  }
```

**Verify:** Photos slightly cooler/muted — print register.
**Commit:** `feat(v2-mockup): editorial image filter (contrast/saturate/brightness calibration)`

---

## TIER 4 — Asset triage (Frontend Developer)

### FIX-T4-01 · Transparent navbar monogram (BLOCKER per FE audit)

**Source:** Frontend Developer (asset audit)
**Symptom:** `assets/branding/skyyrose-monogram-nav.webp` (50×50, 742B, sRGB 3-channel) has no alpha. Renders against navbar's translucent gradient with a solid background bleed.
**Fix path:** TWO OPTIONS — surface to user:
- **A.** Run `rembg` (Python) on `assets/images/logos/sr-monogram-rose-gold.webp` (720×720, 18KB) to produce a transparent variant. Save to `assets/branding/skyyrose-monogram-nav-transparent.webp` at 100×100. Update v2.html navbar `<img src>` to point at new asset.
- **B.** Manual export from source brand file (Adobe Illustrator / Figma) by design team. Save to same path.

**v2.html change (assuming A or B produces the file):**
```html
<img src="../../../wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav-transparent.webp" ...>
```

**Constraint:** Senior Developer should NOT run `rembg` (potential paid API or compute). Surface to user as a blocker — generation requires user explicit consent (STOP-AND-SHOW protocol).

**For this manifest execution:** Skip — leave the current asset path. Note in final report that this remains the one outstanding asset blocker.

**Commit (if produced):** `fix(v2-mockup): navbar monogram → transparent variant`

### FIX-T4-02 · Downsize `black-rose-logo.webp` (optimization)

**Source:** Frontend Developer (asset audit)
**Symptom:** 356KB at 2048×2048 serving into a 600px-wide spread tile slot — bandwidth waste.
**Fix:** Run `cwebp -q 82 -resize 800 0 black-rose-logo.webp -o black-rose-logo-800.webp`. Update F08 br-004 tile src to point at the new resized variant.

**Constraint:** `cwebp` is local, free, deterministic. Senior Developer CAN run this OR surface to user if cwebp not installed. If running, commit asset under the same wordpress-theme/.../branding/ path.

**Decision:** Surface to user. Asset resize touches the live WP theme assets dir, which is on `main` and could affect production if deployed. Better to gate on user approval.

**For this manifest execution:** Skip — defer to follow-up commit.

---

## Out of scope (per FE audit)

- Brand Guardian P2-A (BR product tiles using brand marks as placeholder instead of real product photography) — this is content/asset work, not implementation. Defer.

## Conflicts resolved during synthesis

- **UI FIX-04 (BR lockup wider) + FIX-T3-01 (Ken Burns zoom):** No conflict. BR lockup uses `transform: scale(1.04)` on `.is-visible`; Ken Burns uses keyframe on `.hero__bg` not the lockup. Different elements.
- **FIX-T1-03 (BR palette silver) + FIX-T2-04 (hover ring):** Handled. BR-page scoped block in FIX-T1-03 overrides FIX-T2-04's rose-gold ring with silver via specificity (`.br-page .spread__tile:hover`).
- **FIX-T3-01 (Ken Burns) + Task 11 parallax JS:** Note in FIX-T3-01 — parallax JS may need to wrap its `transform` to compose with the keyframe. Senior Developer should test and adjust if observed.

## Execution checklist (Senior Developer)

After each commit:
- [ ] `cd /Users/theceo/DevSkyy && python3 -c "import html.parser; p=html.parser.HTMLParser(); p.feed(open('docs/brand/design-mockups/v2.html').read()); print('OK')"` → `OK`
- [ ] `git diff --name-only` shows only `docs/brand/design-mockups/v2.html` (no scope drift)
- [ ] Conventional commit message format
- [ ] No new assets fetched / no API calls

After ALL fixes:
- [ ] Final `git log --oneline -20` summarizing fix-group commits
- [ ] HTML parse final
- [ ] Browser visual check (`open docs/brand/design-mockups/v2.html`)
- [ ] Report any deferred items (FIX-T4-01 transparent monogram + FIX-T4-02 cwebp resize)
