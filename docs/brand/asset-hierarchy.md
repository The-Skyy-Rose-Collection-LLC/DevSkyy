# SkyyRose Brand Asset Hierarchy

Locked 2026-05-24. Canonical source for which logo/mark belongs where.

**Two asset directories — distinct purposes:**
- `assets/branding/` — production-ready, multi-size variants (nav, footer, favicon, hero, thumb). USE THIS for theme chrome + page templates.
- `assets/images/logos/` — full-resolution master logos. SKU-embroidery placement source per `data/logo-registry.json`. Not for page chrome.

---

## Tier 1 — Brand Primary (site-wide)

**Single mark, every page chrome.** Pre-sized variants live in `assets/branding/`.

| Variant | File | Dimensions | Use |
|---------|------|-----------:|-----|
| Nav | `assets/branding/skyyrose-monogram-nav.webp` | 50×50 | Header navbar — **WIRED 2026-05-24** |
| Footer | `assets/branding/skyyrose-monogram-footer.webp` | 60×60 | Footer brand mark |
| Mobile nav | `assets/branding/skyyrose-rose-icon-mobile-nav.webp` | 120×120 | Mobile menu header |
| Favicon | `assets/branding/skyyrose-rose-icon-favicon.webp` | 60×60 | Browser tab favicon |
| Hero | `assets/branding/skyyrose-monogram.webp` | full-res | 404 page, loading state, large brand moments |
| Master | `assets/images/logos/sr-monogram-rose-gold.{avif,webp,jpeg}` | 720×720 master | SKU embroidery render source (br-005) |

**Source of truth:** `data/logo-registry.json` → `brand_primary: "sr-monogram-rose-gold"` + `logos."sr-monogram-rose-gold".site_wide: true`

**Theme integration:** `header.php` navbar — `<img src=".../branding/skyyrose-monogram-nav.webp">` with hover scale + rose-gold drop-shadow.

**Secondary use:** Master version also appears as embroidered right-chest placement on `br-005` (Black Rose Hoodie — Signature Edition).

---

## Tier 2 — Collection Hero Marks

Per-collection brand assets that ANCHOR the collection's visual identity. Distinct from product placements.

### Black Rose
| Asset | File | Use |
|-------|------|-----|
| Black Rose Logo (hero) | `assets/branding/black-rose-logo-hero.webp` | Collection page hero |
| Black Rose Logo (thumb) | `assets/branding/black-rose-logo-thumb.webp` | Category tiles, mini hero |
| Black Rose Logo (nav) | `assets/branding/black-rose-logo-nav.webp` | Collection nav indicator |
| Black Rose Logo (transparent PNGs) | `assets/branding/black-rose-logo-{hero,thumb}-transparent.png` | Overlay on imagery |
| Black Rose Collection Text | `assets/branding/black-rose-collection-text.webp` | Wordmark text |
| Black Rose Cloud Cluster (master) | `assets/images/logos/black-roses-cloud-cluster.*` | SKU embroidery source |
| SR-Monogram BlackRose Hero | `assets/branding/sr-monogram-blackrose-hero.webp` (1024×1024) | Possible glass-star pedestal hero (user-sent image #3 match candidate) |
| Hero environment | `assets/branding/hero/forbidden-midnight-{480,768,1280,1680}w.webp` | Full-bleed Black Rose hero background |

### Love Hurts
| Asset | File | Use |
|-------|------|-----|
| Love Hurts Logo (hero) | `assets/branding/love-hurts-logo-hero.webp` | Collection page hero |
| Love Hurts Logo (thumb) | `assets/branding/love-hurts-logo-thumb.webp` | Category tiles |
| Love Hurts Logo (nav) | `assets/branding/love-hurts-logo-nav.webp` | Collection nav indicator |
| Love Hurts Logo (transparent PNG) | `assets/branding/love-hurts-logo-transparent.png` | Overlay on imagery |
| Love hero | `assets/branding/love-hurts-love-hero.webp` | Split "Love" wordmark hero |
| Hurts hero | `assets/branding/love-hurts-hurts-hero.webp` | Split "Hurts" wordmark hero |
| **Neon Star Pedestal** | `assets/branding/love-hurts-neon-star-ref.jpg` (886×886) | **Matches user-sent image #2 — Beast/rose-under-glass with red neon star + heart + thorns** |
| Love/Hurts wordmark masters | `assets/images/logos/{love,hurts,love-hurts-full}-lettering.{avif,webp,jpeg}` + SVG vectorized | Embroidery + animatable wordmarks |
| Red Roses Cloud Cluster (master) | `assets/images/logos/red-roses-cloud-cluster.*` | SKU embroidery source |
| Heart-Rose Composite (master) | `assets/images/logos/heart-rose-composite.*` | Bomber back, Fannie 'i' dot, accent motif |
| Hero environment | `assets/branding/hero/beauty-and-beast-{480,768,1280,1680}w.webp` | Full-bleed Love Hurts hero background |

### Signature
| Asset | File | Use |
|-------|------|-----|
| Signature Logo (hero) | `assets/branding/signature-logo-hero.webp` | Collection page hero |
| Signature Logo (thumb) | `assets/branding/signature-logo-thumb.webp` | Category tiles |
| Signature Logo (nav) | `assets/branding/signature-logo-nav.webp` | Collection nav indicator |
| Signature Logo (transparent PNGs) | `assets/branding/signature-logo-{hero,thumb}-transparent.png` | Overlay |
| **Geometric Metallic Rose** | `assets/branding/signature-rose-{hero,thumb,nav}.{webp,png}` (hero 374×400) | **Matches user-sent image #1 — Signature's geometric metallic rose-gold rose** |
| Gold SR Monogram (master) | `assets/images/logos/sr-monogram-gold.*` | Signature-only premium colorway hero mark |
| SR Primary Hero | `assets/branding/sr-primary-hero.webp` | Large Signature hero mark |
| Hockey/MLB/NBA/NFL Authentic Cards | `assets/images/logos/{hockey-championship,mlb-authentic-collection,nba-authentic-collection,nfl-authentic-collection}-card.*` | Jersey product PDP overlays |
| Hero environment | `assets/branding/hero/luxury-nighttime-{480,768,1280,1680}w.webp` | Full-bleed Signature hero background |

### Kids Capsule
| Asset | File | Use |
|-------|------|-----|
| Inherits brand primary (rose-gold SR monogram) for hero | `assets/branding/skyyrose-monogram.webp` | Collection palette + brand mark aligned via tonal match |
| SkyyRose Collection Circular Patch (master) | `assets/images/logos/skyy-rose-collection-circular-patch.*` | Right-arm embroidery on kids-001 (and kids-002 pending logo-registry gap resolution) |

---

## Tier 3 — Product-Exclusive Assets

Reserved assets tied to specific SKUs — **do not reuse** without explicit user sign-off.

| Asset | File | Locked to | Reason |
|-------|------|-----------|--------|
| Rose-Gold Rose (standalone) | `rose-gold-rose.{avif,webp,jpeg}` | `sg-015` Windbreaker Set ONLY | User confirmation 2026-04-20 |

---

## What rules govern this hierarchy

1. **One brand primary.** Site-wide chrome (header, footer, favicon) uses `sr-monogram-rose-gold` exclusively. Never substitute a collection mark for the brand primary in chrome.
2. **Collection hero marks scope to collection pages.** Black Rose cluster appears on BR collection page; Love Hurts wordmarks on LH; etc. Don't cross-pollinate.
3. **SKU-exclusive assets stay exclusive.** `rose-gold-rose` is sg-015-only. Bypassing this requires user sign-off in writing.
4. **Recolor allowed where flagged** in `logo-registry.json`. Black-roses-cloud-cluster recolor (rose-gold, blue, purple, lavender) is the most common case — never edit the source file, recolor happens at render time via CSS filters or SVG path fills.
5. **The 3 new pedestal assets** (received 2026-05-24) need to be imported into `assets/images/logos/` before they're available. Currently blocked by Photos Library read permission. Import path: drop files into `/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/assets/images/logos/` manually.

---

## Theme integration map

| Theme surface | Asset | Reference |
|---------------|-------|-----------|
| `header.php` navbar center | `sr-monogram-rose-gold` (brand primary) | Wired 2026-05-24 |
| `footer.php` brand mark | `sr-monogram-rose-gold` (TODO) | Not yet wired |
| `template-collection-black-rose.php` hero | `black-roses-cloud-cluster` + new glass-star (pending) | Needs hero update |
| `template-collection-love-hurts.php` hero | `love-hurts-full-lettering` + new star-rose (pending) | Needs hero update |
| `template-collection-signature.php` hero | `sr-monogram-gold` + new geometric rose (pending) | Needs hero update |
| `template-collection-kids-capsule.php` hero | `sr-monogram-rose-gold` (shares brand primary) | Already aligned |
| Favicon | `sr-monogram-rose-gold` (TODO — generate .ico + variants) | Not yet wired |

---

## Related files

- `data/logo-registry.json` — canonical per-SKU placement map (always read first when adding/changing logo usage)
- `wordpress-theme/skyyrose-flagship/assets/branding/vectorized/` — SVG vectorized wordmarks (love, hurts, love-hurts-full)
- `assets/branding/rose-gold-spin.{mp4,webm}` — actual rose-gold rotating product video (potential brand-primary motion variant)
