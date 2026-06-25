# v2.html Image Asset Audit — Transparency / Background Removal

**Date:** 2026-05-25  
**Audited file:** `docs/brand/design-mockups/v2.html`  
**Tool:** ImageMagick `identify`

---

## 1. Per-Asset Table

| Asset path (relative to `assets/`) | Size | Dimensions | Has alpha? | Used at (v2.html section) | Needs alpha? | Action |
|---|---|---|---|---|---|---|
| `branding/skyyrose-monogram-nav.webp` | 742B | 50×50 | **NO** (sRGB 3ch) | Navbar brand mark — on translucent gradient bg | **YES** | Replace or re-export with alpha |
| `branding/black-rose-logo-hero-transparent.png` | 165KB | 628×312 | YES (sRGBA 4ch) | Black Rose collection tile (`spread__tile--lg`) | — | No action needed |
| `branding/black-rose-logo-hero.webp` | 50KB | 628×312 | YES (sRGBA 4ch) | Black Rose spread tile (srcset variant) | — | No action needed |
| `branding/black-rose-logo.webp` | 356KB | 2048×2048 | **NO** (sRGB 3ch) | Black Rose product spread tile (br-004 card) | No¹ | Monitor; acceptable for opaque card fill |
| `branding/black-rose-monogram-sr.jpg` | 163KB | 886×886 | **NO** (sRGB 3ch) | Black Rose product spread tile (br-005 card) | No¹ | Monitor; acceptable for opaque card fill |
| `branding/love-hurts-logo-hero.webp` | 206KB | 800×897 | YES (sRGBA 4ch) | Love Hurts collection tile | — | No action needed |
| `branding/signature-logo-hero.webp` | 40KB | 1200×610 | **NO** (sRGB 3ch) | Signature collection tile (spread section) | No¹ | Monitor; acceptable for opaque card fill |
| `branding/hero/beauty-and-beast-{480,768,1280,1680}w.webp` | 22–248KB | 480–1680px wide | NO (sRGB 3ch) | Full-bleed section hero backgrounds | No² | No action needed |
| `branding/hero/forbidden-midnight-{480,768,1280,1680}w.webp` | 28–316KB | 480–1680px wide | NO (sRGB 3ch) | Full-bleed section hero backgrounds | No² | No action needed |
| `branding/hero/luxury-nighttime-{480,768,1280,1680}w.webp` | 17–170KB | 480–1680px wide | NO (sRGB 3ch) | Full-bleed section hero backgrounds | No² | No action needed |
| `images/hero-overlays/br-brand-script.{png,webp,avif}` | 91–710KB | 1600×900 | YES (sRGBA 4ch) | Hero overlay on photo background | Required & met | No action needed |
| `images/hero-overlays/br-patch-hockey.{png,webp}` | 22–138KB | 1600×900 | YES (sRGBA 4ch) | Sport patch overlay on hero | Required & met | No action needed |
| `images/hero-overlays/br-patch-mlb-baseball.{png,webp}` | 47–441KB | 1600×900 | YES (sRGBA 4ch) | Sport patch overlay on hero | Required & met | No action needed |
| `images/hero-overlays/br-patch-nba-basketball.{png,webp}` | 42–307KB | 1600×900 | YES (sRGBA 4ch) | Sport patch overlay on hero | Required & met | No action needed |
| `images/hero-overlays/br-patch-nfl-football.{png,webp}` | 40–213KB | 1600×900 | YES (sRGBA 4ch) | Sport patch overlay on hero | Required & met | No action needed |
| `images/logos/skyy-rose-collection-circular-patch.webp` | 104KB | 1678×1872 | **NO** (sRGB 3ch) | Kids Capsule collection tile | No¹ | Monitor; acceptable for opaque card fill |

**Footnotes:**
1. `spread__tile` background is `var(--sr-charcoal)` — a solid opaque dark. Images are `object-fit: cover` fills of that tile. The overlay is a CSS gradient added on top. No photo bleed from a translucent surface — solid background is fine here.
2. Hero images are full-bleed `<picture>` fills, 100% width × 100% height of the section. They are the background; alpha would be meaningless.

---

## 2. Remediation Plan

### Priority 1 — BLOCKER: `branding/skyyrose-monogram-nav.webp`

**Problem:** 50×50, 742B, 8-bit sRGB, no alpha channel. Placed inside `.navbar__brand` on top of:  
`background: linear-gradient(180deg, rgba(10,10,10,0.85), rgba(10,10,10,0))` + `backdrop-filter: blur(8px)`.  
The image's solid (presumably white or off-white) background rectangle bleeds over the gradient, ruining the translucency effect.

**Check existing inventory first — viable swap candidates:**

| Candidate | Size | Dimensions | Alpha? | Verdict |
|---|---|---|---|---|
| `images/logos/sr-monogram-rose-gold.webp` | 18KB | 720×720 | **NO** (sRGB 3ch) | Not usable without re-export |
| `images/logos/sr-monogram-rose-gold.avif` | 14KB | 720×720 | **NO** (sRGB 3ch) | Not usable without re-export |
| `images/logos/sr-monogram-rose-gold.jpeg` | 62KB | 720×720 | NO (JPEG, no alpha) | Not usable without re-export |
| `images/logos/sr-monogram-gold.webp` | 19KB | 1108×720 | **NO** (sRGB 3ch) | Not usable without re-export |
| `images/logos/sr-monogram-gold.avif` | 13KB | 1108×720 | **NO** (sRGB 3ch) | Not usable without re-export |
| `branding/sr-primary-hero.webp` | 1.5MB | 1024×1024 | NO (sRGB 3ch) | Not relevant (hero photographic asset) |

**Conclusion:** No ready-to-use transparent monogram variant exists in the asset tree. All `sr-monogram-*` and `skyyrose-monogram-*` files are 3-channel sRGB.

**Recommended production approach:**

The `sr-monogram-rose-gold` source at 720×720 is the highest-quality, square-format variant matching the nav's 44×44px display slot. The background appears to be a solid fill (likely white or near-black based on the filename context). Either:

- **Option A — Re-export from source file (fastest, zero loss):** Open the original source (Illustrator / Figma / PSD) and export as WebP with alpha, targeting ≤2KB at 100×100px (2× retina). Name it `skyyrose-monogram-nav-transparent.webp` and swap the `<img src>` in the navbar. This preserves vector crispness and avoids rembg artifacts on a graphic logo.

- **Option B — Automated background removal with `rembg`:** If the source file is unavailable:  
  ```bash
  pip install rembg Pillow
  rembg i wordpress-theme/skyyrose-flagship/assets/images/logos/sr-monogram-rose-gold.webp \
             wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav-transparent.webp
  # Then resize to target output dimensions via cwebp or ImageMagick:
  convert wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav-transparent.webp \
          -resize 100x100 \
          wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav-transparent.webp
  ```
  `rembg` uses U²-Net and works well on graphic logos with clean contrast.  
  **Caveat:** rembg may antialias edges with halos if the monogram has fine details. Inspect output before shipping.

- **Option C — `remove.bg` API (paid):** Pass `sr-monogram-rose-gold.webp` via the API for a cleaner result on complex artwork. Follow the STOP AND SHOW protocol before any paid API call.

- **Option D — ImageMagick `-fuzz` floodfill:** Only reliable if the background is a single solid color with no gradient and the logo has hard edges. Given this is a brand monogram, Option A or B is safer.

**Navbar `<img>` swap line (v2.html:521):**
```html
<!-- current -->
src="../../../wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav.webp"

<!-- after fix (once transparent variant is produced) -->
src="../../../wordpress-theme/skyyrose-flagship/assets/branding/skyyrose-monogram-nav-transparent.webp"
```

---

### Priority 2 — MINOR RISK: `branding/signature-logo-hero.webp`

**Problem:** 1200×610, no alpha. Used as a `spread__tile-img` (object-fit: cover fill) inside a tile with `background: var(--sr-charcoal)`. The tile itself is opaque — the logo image simply fills the card.

**Assessment:** No transparency is needed here unless the design intent is to show the charcoal tile color bleeding through the logo's negative space. If `signature-logo-hero.webp` contains letter-forms or artwork on a matching dark background, it will look correct already. If the background color is a different shade (e.g. off-black vs. charcoal), there will be a visible box artifact at the card boundaries.

**Action:** Visually verify in browser. If there is a mismatch at the image edges, request a transparent export from the design team. Not a blocker.

---

### Priority 3 — MONITOR: `branding/black-rose-logo.webp`, `branding/black-rose-monogram-sr.jpg`, `images/logos/skyy-rose-collection-circular-patch.webp`

All three are 3-channel sRGB used as `object-fit: cover` fills inside opaque `spread__tile` cards with `background: var(--sr-charcoal)`. No translucent surfaces involved.

- `black-rose-logo.webp` (2048×2048) — Over-sized for a card fill. Not a transparency issue; a compression/resize optimization opportunity only.
- `black-rose-monogram-sr.jpg` (886×886) — JPEG means alpha is impossible by format; confirmed this surface doesn't need it.
- `skyy-rose-collection-circular-patch.webp` (1678×1872) — Same reasoning as above.

**Action:** No alpha work required. Flag `black-rose-logo.webp` for resize optimization separately (356KB at 2048px is large for a 600px card slot).

---

## 3. Quick-Check Summary — Monogram Candidates

```
sr-monogram-rose-gold.webp   | 720×720  | alpha=Undefined (NO alpha)
sr-monogram-rose-gold.avif   | 720×720  | alpha=Undefined (NO alpha)
sr-monogram-rose-gold.jpeg   | 720×720  | alpha=Undefined (NO alpha, JPEG)
sr-monogram-gold.webp        | 1108×720 | alpha=Undefined (NO alpha)
sr-monogram-gold.avif        | 1108×720 | alpha=Undefined (NO alpha)
sr-primary-hero.webp         | 1024×1024| alpha=Undefined (NO alpha, photographic)
```

None of the existing `sr-monogram-*` assets carry an alpha channel. The source of truth for a transparent monogram must come from a vector/layered source export or a background-removal pass on `sr-monogram-rose-gold.webp` (best candidate: 720×720 square, correct format for a 2× export).

---

## 4. Recommendation — Navbar Monogram

**Do not swap to any existing asset — all are opaque sRGB.**

The correct path is:

1. **Best:** Re-export from the original brand source file (Figma/Illustrator) as `skyyrose-monogram-nav-transparent.webp`, 100×100px (2× retina for 44×44 display), with alpha. File size should be under 3KB for a simple graphic monogram.

2. **Acceptable fallback:** Run `rembg` on `assets/images/logos/sr-monogram-rose-gold.webp` → inspect output → resize to 100×100 → save as `assets/branding/skyyrose-monogram-nav-transparent.webp` → update v2.html line 521. Verify no halo artifacts around the monogram edges before shipping.

3. **Update `front-page.php` and `inc/enqueue.php` references** in the same commit once the transparent asset is confirmed good — the monogram path is likely referenced in the WordPress theme header template as well.

---

*Audit produced by Frontend Developer agent. Read-only inspection — no images were generated or transformed.*
