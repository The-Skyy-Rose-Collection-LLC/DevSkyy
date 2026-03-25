# Immersive Scene Generation — RALPH Task

## Objective

Generate drakerelated.com-style immersive scene backgrounds where **products are rendered INTO the environment** — not as separate overlays. Each scene should be a single cinematic image with SkyyRose products visibly placed on props within the environment.

## Output Requirements

- Format: `.webp` (primary) + `.png` (fallback)
- Dimensions: 3840x2160 (16:9) minimum, 4K preferred
- Style: Photorealistic, cinematic lighting, dark luxury
- Save to: `wordpress-theme/skyyrose-flagship/assets/scenes/{collection}/`

## Pipeline: `scripts/gemini_scene_gen.py`

Uses the existing Gemini image generation pipeline (same as `gemini_product_gen.py`):

- **Model**: `gemini-2.5-flash-image` ($0.02/image, ~2.5s per generation)
- **Fallback**: Change `MODEL_ID` to `gemini-3-pro-image-preview` for 4K ($0.08/image)
- **Aspect ratio**: 16:9 (ultrawide scene composition)
- **Output**: PNG + WebP auto-conversion
- **Retry**: 3 attempts with 8s delay per scene

### Quick Start

```bash
source .venv-imagery/bin/activate

# Preview prompts without spending API credits
python scripts/gemini_scene_gen.py --all --dry-run

# Generate one scene at a time
python scripts/gemini_scene_gen.py --scene black-rose-moonlit-courtyard

# Generate all scenes for a collection
python scripts/gemini_scene_gen.py --collection black-rose

# Generate everything (6 scenes, ~$0.12 total)
python scripts/gemini_scene_gen.py --all

# Generate with 2 variants per scene for A/B comparison
python scripts/gemini_scene_gen.py --all --variants 2
```

### Related Pipeline Files

| File | Purpose |
|------|---------|
| `scripts/gemini_scene_gen.py` | **THIS SCRIPT** — batch scene generation |
| `scripts/gemini_product_gen.py` | Product image generation (reference pattern) |
| `agents/visual_generation/gemini_native.py` | Async Gemini client with brand DNA injection |
| `agents/visual_generation/visual_generation.py` | Multi-provider router (Imagen, FLUX, LoRA) |
| `services/ml/gemini_client.py` | Full Gemini API with multi-turn editing |

## Brand Visual Language

- Dark luxury: near-black backgrounds (#0A0A0A), dramatic lighting
- Accent colors per collection:
  - Black Rose: Silver (#C0C0C0), moonlit blues
  - Love Hurts: Crimson (#DC143C), pink petals, purple fabrics
  - Signature: Gold (#D4AF37), sunset warmth, Bay Area vibes
- Products are BLACK streetwear (hoodies, joggers, jerseys, jackets) with embroidered rose details

---

## COLLECTION 1: BLACK ROSE — "The Garden"

### Room 1: Moonlit Courtyard
**File:** `black-rose/black-rose-moonlit-courtyard-v2.webp`
**Scene:** Gothic cathedral courtyard at night, moonlight streaming through arched colonnades, marble statues, black rose topiaries, ornate fountain, cobblestone ground, floating petals, blue-silver moonlight atmosphere.

**Products placed IN the scene:**
| Position | Product | Placement Description |
|----------|---------|----------------------|
| Left (15%, 42%) | br-006: BLACK Rose Sherpa Jacket ($95) — black satin with Sherpa lining, embroidered rose | Draped over marble garden statue's arm |
| Center-left (38%, 50%) | br-005: BLACK Rose Hoodie Signature Edition ($65) — premium black hoodie with rose detail | Folded neatly on fountain edge, rose embroidery visible |
| Center-right (62%, 55%) | br-002: BLACK Rose Joggers ($50) — black joggers with embroidered roses | Folded at base of rose topiary |
| Right (82%, 48%) | br-004: BLACK Rose Hoodie ($40) — black hoodie with rose embroidery | Draped over statue pedestal |

**Prompt guidance:** "Photorealistic gothic moonlit courtyard, marble arches, fountain, statues, black rose bushes. BLACK streetwear clothing items naturally placed throughout the scene — a black sherpa jacket draped over a marble statue arm, a black hoodie folded on the fountain edge, black joggers at the base of a topiary, another black hoodie over a pedestal. Moonlit blue-silver lighting, floating rose petals, cinematic depth of field. 16:9 ultrawide, 4K."

### Room 2: Iron Gazebo Garden
**File:** `black-rose/black-rose-iron-gazebo-garden-v2.webp`
**Scene:** Aerial/elevated view of ornate wrought-iron gazebo in center, surrounded by hedge maze, cobblestone paths, rose archways, moonlight.

**Products placed IN the scene:**
| Position | Product | Placement |
|----------|---------|-----------|
| Center (30%, 40%) | br-004: BLACK Rose Hoodie ($40) | Displayed on mannequin inside iron gazebo |
| Right-center (55%, 35%) | br-001: BLACK Rose Crewneck ($35) — black crewneck with rose embroidery | Hanging from rose hedge archway |
| Right (72%, 50%) | br-008: Women's BLACK Rose Hooded Dress ($120) — gothic hooded dress with rose embroidery | Draped over cobblestone garden bench |
| Center-low (48%, 60%) | br-003: BLACK is Beautiful Jersey ($45) — luxury athletic jersey | Displayed on hedge maze wall |

---

## COLLECTION 2: LOVE HURTS — "The Ballroom"

### Room 1: Cathedral Rose Chamber
**File:** `love-hurts/love-hurts-cathedral-rose-chamber-v2.webp`
**Scene:** Gothic cathedral interior, enchanted rose under glass dome (Beauty and the Beast style), stained glass windows with red/pink light, candelabras, crimson rose petals scattered on stone floor, purple/crimson fabric draped from arches.

**Products placed IN the scene:**
| Position | Product | Placement |
|----------|---------|-----------|
| Center-left (35%, 42%) | lh-004: Love Hurts Varsity Jacket ($265) — black satin varsity with fire-red script, rose garden in hood | Draped beside the enchanted rose glass dome |
| Right (68%, 38%) | lh-001: The Fannie Pack ($65) — luxury black fanny pack with rose detail | Hung from gothic candelabra stand |
| Center (52%, 60%) | lh-003: Love Hurts Basketball Shorts ($75) — black mesh with rose design | Displayed on stone ledge in stained glass alcove |

### Room 2: Gothic Ballroom
**File:** `love-hurts/love-hurts-gothic-ballroom-v2.webp`
**Scene:** Vast gothic ballroom, purple velvet drapes, rose under glass dome, pink petals on floor, candlelit chandeliers, dark romantic atmosphere.

**Products placed IN the scene:**
| Position | Product | Placement |
|----------|---------|-----------|
| Center-left (40%, 45%) | lh-002: Love Hurts Joggers BLACK ($95) — black joggers with embroidered rose | Folded on purple velvet drape/chair |
| Right (65%, 48%) | lh-005: Love Hurts Windbreaker ($145) — blush pink windbreaker with rose detailing | Displayed beside glass dome on marble stand |

---

## COLLECTION 3: SIGNATURE — "The Runway"

### Room 1: Waterfront Runway
**File:** `signature/signature-waterfront-runway-v2.webp`
**Scene:** Bay Bridge at night, floating black marble platform over water, gold LED trim lighting, glass orb display case, stepped marble pedestals, reflective marble floor, gold accent lighting.

**Products placed IN the scene:**
| Position | Product | Placement |
|----------|---------|-----------|
| Left (15%, 42%) | sg-009: The SkyyRose Duffle ($85) — luxury duffle bag | Inside glass orb display case |
| Center-left (42%, 35%) | sg-002: Stay Golden Set ($65) — gold colorway set | Hanging in gold-lit LED display frame |
| Center (50%, 38%) | sg-010: Bridge Shorts ($45) — Bay Area inspired shorts | Hanging in gold-lit LED display frame |
| Center-right (62%, 36%) | sg-006: Mint & Lavender Hoodie ($45) — pastel colorblock | Hanging in gold-lit LED display frame |
| Right (75%, 50%) | sg-001: The Bay Set ($195) — blue rose Bay Area ensemble | Featured on stepped marble pedestal |
| Far right (82%, 58%) | sg-008: Signature Beanie Forest Green ($25) | On lower marble pedestal step |

### Room 2: Golden Gate Showroom
**File:** `signature/signature-golden-gate-showroom-v2.webp`
**Scene:** Luxury showroom with floor-to-ceiling panoramic windows showing Golden Gate Bridge at sunset, black marble interior, gold LED strip lighting, clothing racks on walls, marble pedestals, center display table, reflective marble floor.

**Products placed IN the scene:**
| Position | Product | Placement |
|----------|---------|-----------|
| Left (18%, 38%) | sg-003: Signature Tee Orchid ($15) — orchid colorway tee | Hanging on left wall clothing rack |
| Center (50%, 52%) | sg-005: Stay Golden Tee ($40) — gold colorway tee | Featured on center marble display table |
| Left-center (32%, 48%) | sg-007: Signature Beanie Black ($25) | On left marble pedestal |
| Right (78%, 40%) | sg-004: Signature Tee White ($15) | Hanging on right wall clothing rack |

---

## After Generation

1. Convert all PNGs to WebP: `cwebp -q 85 input.png -o output.webp`
2. Update template files to reference `-v2` filenames
3. Verify hotspot positions still align with product locations in new images
4. Test in browser at multiple viewport sizes

## Quality Bar

Reference: drakerelated.com room navigation. Products must look PHYSICALLY PRESENT in the scene, not photoshopped on top. Lighting, shadows, and color grading must match between products and environment.
