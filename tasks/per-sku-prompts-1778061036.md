# Per-SKU Generator Prompts

Generated 2026-05-06 02:50:36

**Total SKUs:** 2
**Canonical dossier loaded:** 2/2
**Vision cache present:** 1/2

---

## br-001

**Vision cache:** present
**Inferred DNA:** garment=crewneck | fabric=Smooth, lustrous knit fabric with a satin-like sheen for the body and sleeves. T | graphic-type='embroidery' | graphic-colors=['#222222', '#666666', '#AAAAAA', '#FFFFFF', '#708070'] | branding-technique='embroidery'
**Engine route:** `gemini-pro` (gemini-3-pro-image-preview) — Complex fabric (Smooth, lustrous knit fabric with a satin-like sheen for the body and sleeves. The collar, cuffs, and hem are made of a matte, ribbed knit.) — Gemini Pro best at material physics
**Registry template:** `canonical_mode_v1`
**Prompt length:** Layer-0=1135c → +Layer-3=2312c → +Layer-2=1492c → final=4939c

### Final prompt sent to generator

```
CANONICAL DESIGN SPEC (authored truth — overrides any conflicting inferred description below):

GARMENT TYPE (must match exactly):
Crewneck sweatshirt — upper body only, round ribbed neckline, no hood, no buttons, no zipper, no front pocket. NOT a jersey. NOT a hoodie. NOT a jacket. NOT a t-shirt. NOT a tank top. Heavyweight cotton fleece, relaxed fit. **White ribbed neckband, white ribbed sleeve cuffs, white ribbed waist hem** (contrast white trim against the black body — same pattern as the matching joggers in the Black Rose set).

BRANDING — exactly what to render:
> Logo art canonical references:
> - Black Rose three-rose-cluster: `data/brand-logos/black-rose-logo.md`
> - SR monogram (gold lettermark): `data/brand-logos/sr-monogram.md`

### Front
- **front-chest** (~10in tall × proportional width): The Black Rose logo,
  **physically embossed/debossed into the fabric surface** as a tonal raised
  relief. The full art (three roses + stems + thorny vines + cloud) is impressed
  into the fabric — viewer sees the *shapes* in 3D relief but the colors are
  flattened to the base fabric color (no greyscale petals, no green stems, no
  white cloud — all tonal black-on-black). Subtle 3D texture visible only in
  directional/raking light. **Technique:** embossed. **Color:** tonal black-on-black.

### Back
- **back-neck** (small, ~2in wide, top-center just below the white-ribbed
  collar): The SR monogram (gold metallic art — see sr-monogram reference).
  Embroidered directly onto the jersey in gold-tone thread. **Technique:**
  embroidered. **Color:** gold-tone thread (preserves the gold-to-copper
  gradient from the canonical mark).

### Sleeves / Collar / Hem / Other
- **collar-outside / neckband**: White ribbed-knit neckband contrasting against
  the black body. **Technique:** stitched. **Color:** white.
- **left-cuff / right-cuff**: White ribbed-knit sleeve cuffs contrasting
  against the black body. **Technique:** stitched. **Color:** white.
- **hem**: White ribbed-knit waist hem contrasting against the black body.
  **Technique:** stitched. **Color:** white.
- **collar-inside** (~1.75in × 0.75in): Small woven brand label sewn into the
  inside back of the collar. **Technique:** woven-label. **Color:**
  brand-label colors (typically black with brand-color accents).

---

Render task: photorealistic e-commerce product photo of "BLACK Rose Crewneck" — front view only, no model, no mannequin.

Defer to the CANONICAL DESIGN SPEC above for every product detail (garment type, branding, colors, techniques, placements). The canonical spec is authoritative; render exactly what it specifies, nothing more, nothing less.

STUDIO SETUP:
- Deep matte black (#0A0A0A) backdrop with subtle charcoal gradient
- Cool silver key light from upper-left, black fill, thin silver rim light creating metallic edge highlights
- Mood: Dark, authoritative, monochrome luxury — the garment commands the frame
- Garment floats on an invisible form with natural 3D drape and shadow
- Photorealistic fabric texture: visible weave, thread weight, sheen appropriate to the canonical fabric description
- Pure 4K product-photography sharpness, no motion blur, no DOF blur on the garment

VIEW RESTRICTION: front view only. Do NOT show the back. Do NOT add watermarks, price tags, size labels, brand text overlays, or model.

AUTHORED NEGATIVES will follow below — those are the explicit DO-NOT-RENDER rules for this specific product.

DO NOT RENDER (authored canonical negatives):
- NO printed graphics anywhere — not on chest, not on back, not on sleeves, not on hem.
- NO printed text — no "BLACK IS BEAUTIFUL" arched text, no other printed words.
- NO full-color rendering of the rose logo on the front chest — the front-chest
  logo is tonal embossed only. NO kelly-green stems visible. NO white-and-blue
  cloud color visible. NO greyscale rose petals visible. The embossing flattens
  all colors to the base fabric color.
- NO embroidered Black Rose logo on the front chest (the front is embossed,
  NOT embroidered — embroidery would render visible thread color).
- NO embroidered patches on the lower right front (this is NOT a baseball jersey).
- NO SR monogram on the front chest. NO SR monogram on the sleeves. NO SR
  monogram at the back-center. The SR monogram is at the back-neck only.
- NO embroidered roses on mid back (the back-CENTER is empty; the SR monogram
  sits at the back-neck only).
- NO baseball player graphics anywhere.
- NO sleeve patches, sleeve embroidery, sleeve printing — sleeves are clean.
- NO hem or side-seam decoration on the body fabric — the hem is plain ribbed
  knit (white), no logo, no text, no piping.
- NO chest text other than the embossed rose logo.
- NO contrasting-color logos on the body fabric beyond the back-neck SR monogram.
- NO silicone appliqué.
- NO heat-transfer vinyl.
- NO sublimated panels.
- NO black ribbed neckband (the rib trim is WHITE, not tonal black).
```

---

## br-002

**Vision cache:** MISSING
**Inferred DNA:** (no vision cache — generator prompt would lack inferred DNA detail)
**Engine route:** `flux-pro` (fal-ai/flux-pro/v1.1) — Standard garment — FLUX Pro best value (98% quality, 26% cost)
**Registry template:** `canonical_mode_v1`
**Prompt length:** Layer-0=1134c → +Layer-3=2383c → +Layer-2=1362c → final=4879c

### Final prompt sent to generator

```
CANONICAL DESIGN SPEC (authored truth — overrides any conflicting inferred description below):

GARMENT TYPE (must match exactly):
Black jogger sweatpants — lower body only, elasticated waist with drawstring, tapered leg, ribbed ankle cuffs, side hand pockets, back pockets. **White ribbed waistband** at the top, **white ribbed ankle cuffs** at the bottom (contrast white trim against the black body — same pattern as the matching Black Rose Crewneck). NOT shorts. NOT straight-leg sweatpants. NOT cargo pants. NOT track pants with side stripes. NOT leggings. Heavyweight cotton-blend fleece, relaxed fit through the thigh.

BRANDING — exactly what to render:
> Logo art canonical references:
> - Black Rose three-rose-cluster: `data/brand-logos/black-rose-logo.md`
> - SR monogram (gold lettermark): `data/brand-logos/sr-monogram.md`

### Front
- **left-thigh** (~3in × 2in): The Black Rose logo as a **silicone-appliqué
  patch** — raised silicone fused to the fabric, with the **full multi-color
  art preserved**: greyscale rose petals (light grey to dark grey shading),
  bright kelly-green stems, dark-green thorny vines, white-and-light-blue
  cloud at the base. **Technique:** silicone-appliqué. **Color:** full
  multi-color art (NOT tonal, NOT monochrome).

### Back
- **right-thigh** (small, ~1.5in–2in wide, upper-back-right hip area —
  approximately mirroring the position of the front-left silicone patch
  but on the back): The SR monogram, embroidered directly onto the fabric
  in **gold-tone thread** (matching the gold-to-copper gradient of the
  canonical SR mark). **Technique:** embroidered. **Color:** gold-tone thread.

### Sleeves / Collar / Hem / Other
- **inside-waistband** (~1in × 0.5in): Woven size tag (showing the size
  designation, e.g., "M", "L", "XL"). **Technique:** woven-label. **Color:**
  brand-standard (typically black with white/printed size text).
- **waistband-rib**: White ribbed-knit waistband at the top of the joggers,
  contrasting against the black body. **Technique:** stitched. **Color:** white.
- **left-ankle-cuff / right-ankle-cuff**: White ribbed-knit cuffs at the
  ankle openings, contrasting against the black body. **Technique:** stitched.
  **Color:** white.
- **drawstring**: Flat **white** drawstring threaded through the waistband.
  No metal tips, no branded tips. **Technique:** stitched. **Color:** white.

---

Render task: photorealistic e-commerce product photo of "BLACK Rose Joggers" — front view only, no model, no mannequin.

Defer to the CANONICAL DESIGN SPEC above for every product detail (garment type, branding, colors, techniques, placements). The canonical spec is authoritative; render exactly what it specifies, nothing more, nothing less.

STUDIO SETUP:
- Deep matte black (#0A0A0A) backdrop with subtle charcoal gradient
- Cool silver key light from upper-left, black fill, thin silver rim light creating metallic edge highlights
- Mood: Dark, authoritative, monochrome luxury — the garment commands the frame
- Garment floats on an invisible form with natural 3D drape and shadow
- Photorealistic fabric texture: visible weave, thread weight, sheen appropriate to the canonical fabric description
- Pure 4K product-photography sharpness, no motion blur, no DOF blur on the garment

VIEW RESTRICTION: front view only. Do NOT show the back. Do NOT add watermarks, price tags, size labels, brand text overlays, or model.

AUTHORED NEGATIVES will follow below — those are the explicit DO-NOT-RENDER rules for this specific product.

DO NOT RENDER (authored canonical negatives):
- NO logo on the right thigh on the FRONT — the silicone patch is on the
  LEFT thigh of the front view only. (The back-right hip carries a small
  embroidered SR monogram, distinct from the front silicone patch.)
- NO Black Rose silicone patch on the back — the back's only branding is
  the small gold SR monogram on the back-right hip.
- NO embroidered logos on the front of the joggers — the front-left thigh
  is silicone-appliqué, NOT embroidery.
- NO embossed/debossed decoration anywhere.
- NO printed graphics or printed text on the legs, hem, or waistband.
- NO contrast-color side stripes down the legs.
- NO back-pocket flap logos, no pocket trim branding.
- NO logo on the front of the ankle cuffs, no logo on the hem fabric.
- NO "BLACK ROSE" wordmark printed across the leg.
- NO sublimated panels, no heat-transfer vinyl, no puff-print decoration.
- NO black drawstring (the drawstring is WHITE — confirmed in set techflat).
- NO black waistband rib (the waistband rib is WHITE — confirmed).
- NO black ankle cuff rib (the ankle cuff rib is WHITE — confirmed).
- NO chest, sleeve, or upper-body decoration (this is a lower-body-only garment).
- NO tonal/monochrome silicone — the front patch IS in full multi-color
  (preserves the canonical logo's grey roses, kelly-green stems, white-blue cloud).
```

---

