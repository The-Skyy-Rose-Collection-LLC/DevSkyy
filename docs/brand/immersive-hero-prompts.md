# Immersive Hub — Dedicated Hero Master Prompts (Midjourney)

**Purpose:** one dedicated cinematic hero master per collection for the `/experiences/` full-bleed blocks (placement `experience-hero`). Generated 2026-06-17 from the grilled architecture decisions.

## Generation spec (every prompt)
- **Aspect:** `--ar 16:9` · **Model:** `--v 7` (or `--v 6.1`) · `--style raw` for photographic control.
- **Target master:** 2560×1440 (upscale the chosen 4-up; then the `--upbeta`/Creative Upscale or an external upscaler to ≥2560w). Export WebP + AVIF + the srcset ladder (640·1024·1536·2048·2560w) once dropped into `assets/branding/hero/`.
- **Composition rule (critical — these are BACKGROUNDS for a centered name):** keep the **center third as calm negative space** (no busy subject dead-center), push focal subjects to the lower/side thirds, and let the **edges fall to a darker vignette** so an overlaid script wordmark stays legible. No text, no watermark, no logo in the image.
- **Brand register (LOCKED):** Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels DNA — streetwear-meets-luxury, Oakland/Bay concrete. **Never** European luxury-house / ornate-ballroom / fairytale-castle look.
- Negatives to append: `--no text, watermark, logo, people staring at camera, ornate baroque ballroom, castle interior, cartoon`

---

## 01 — SIGNATURE  (gold #D4AF37 + rose-gold #B76E79 · "where it started from")
Bay Area / Oakland golden-hour origin. Its OWN art (stop borrowing the rose/ballroom).

```
Oakland rooftop at golden hour overlooking the Bay, distant Bay Bridge silhouette in warm haze, raw concrete parapet and rebar foreground, a single gilded rose-gold rose resting on the ledge, sun-flare and dust motes, luxury-streetwear editorial, cinematic anamorphic, deep gold #D4AF37 and rose-gold #B76E79 grade against matte black sky, calm empty center sky for a title, dark vignetted edges, Fear of God x Oaklandish mood, photographic, ultra-detailed, 8k --ar 16:9 --style raw --v 7 --no text, watermark, logo, baroque ballroom, castle, cartoon
```

## 02 — BLACK ROSE  (silver #C0C0C0 on black · "beauty through the color black" · armor)
Oakland concrete-gothic night — armor, not a fairytale garden.

```
Rain-slick Oakland concrete underpass at night, monolithic black architecture, a single black rose with silver-chrome edges lit by a hard silver key light, wet asphalt reflections, fog and cold moonlight, brutalist columns, gothic streetwear-luxury, monochrome black with liquid-silver #C0C0C0 highlights, calm dark negative space in the upper center for a title, heavy vignette, Fear of God x Rick-free Oakland concrete mood, cinematic, ultra-detailed, 8k --ar 16:9 --style raw --v 7 --no text, watermark, logo, baroque ballroom, castle interior, color cast, cartoon
```

## 03 — LOVE HURTS  (crimson #DC143C · "Beauty & the Beast, the Beast's POV")
Romantic crimson — re-grounded as crimson-lit urban romance, not a gilded ballroom.

```
Moody crimson-lit concrete loft at dusk, scattered deep-red rose petals across a raw concrete floor, a draped crimson velvet coat over a steel chair, single shaft of red neon and window light, smoke haze, the Beast's solitude — luxury streetwear romance, blood-crimson #DC143C and #9B0F2E against charcoal black, calm darker center for a title, vignetted edges, Palm Angels x Fear of God cinematic editorial, photographic, ultra-detailed, 8k --ar 16:9 --style raw --v 7 --no text, watermark, logo, ornate gold ballroom, fairytale castle, cartoon
```

## 04 — KIDS CAPSULE  (rose-gold #B76E79 + gold · "the heir to the throne")
Regal-but-playful, next-gen — elevated, not a ballroom; concrete with warmth.

```
A child-scale throne of polished concrete and rose-gold trim on an Oakland rooftop at warm golden hour, small luxury sneakers and a tiny crown resting on the seat, soft warm light, balloons-as-architecture restraint, playful-regal heir energy, luxury-streetwear, rose-gold #B76E79 and gold #D4AF37 against soft black, calm bright center for a title, gentle vignette, Kith Kids x Oaklandish editorial, photographic, ultra-detailed, 8k --ar 16:9 --style raw --v 7 --no text, watermark, logo, baroque ballroom, castle, cartoon, creepy
```

---

## After generation — drop-in procedure
1. Save each master to `wordpress-theme/skyyrose-flagship/assets/branding/hero/<slug>-hero-2560w.webp` (+ avif) and the srcset ladder `-640/-1024/-1536/-2048/-2560w`.
2. Set `imagery.hero` in each `data/collections/<slug>/identity.json` to `branding/hero/<slug>-hero` (the placement registry resolves the ladder).
3. Re-run the SOT build + `verify-collection-sot.py` (the new min-dimension gate will pass once 2560w masters exist).
4. Re-render the hub — every block now full-bleed at its placement contract, no stretching.
