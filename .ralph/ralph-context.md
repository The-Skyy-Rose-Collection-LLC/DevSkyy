# Ralph Loop Context

## Context added at 2026-02-24T16:20:00.000Z
## THE EXPERIENCE — TWO LAYERS

### LAYER 1: THE HOTSPOT (what you SEE in the 3D scene)
The product ON the prop IS the hotspot. Use the original product photography or AI-generate a 100% replica of the real product styled naturally on its prop (jacket draped on bench, hoodie hanging on rack, etc.). The product must be visually IDENTICAL to the real garment — same colors, same embroidery, same logo placement, same fabric, same everything. Feed the original product photo as reference input for any AI generation. The hotspot glow/pulse interaction targets THIS product-on-prop image.

### LAYER 2: THE PRODUCT CARD (what pops up on CLICK)
When a user clicks a hotspot, a state-of-the-art product card modal opens featuring:

**Hero Image:** AI-generated fashion model WEARING the product (100% replica on the model)
- The garment on the model must be identical to the real product — same design, same details
- Model vibe matches the collection mood (gothic for BLACK ROSE, passionate for LOVE HURTS, editorial for SIGNATURE)
- Model diversity: mix of genders, body types, ethnicities — Bay Area representation
- Generate using Gemini (`build/generate-fashion-models.js`) or HuggingFace Spaces
- Feed the original product photo as the reference so the AI nails the exact garment

**Product Details:**
- Product name + tagline
- Price + badge (PRE-ORDER / AVAILABLE)
- Short description (from `product-content.json`)
- Size selector (from `config.js` variants)
- Color swatches (from `config.js` variants)
- Add to Cart / Pre-Order CTA button
- Wishlist toggle (uses existing `WishlistManager`)

**Collection Branding — each card is collection-specific:**
- **BLACK ROSE cards**: Dark background, `#B76E79` rose gold accent, gothic typography, subtle rose petal particle effect
- **LOVE HURTS cards**: Deep red/black gradient, `#8B0000` accent, fire/passion energy, bold Oakland street typography
- **SIGNATURE cards**: Cream/gold luxury, `#D4AF37` gold accent, editorial clean layout, runway sophistication

**Collection Link:**
- Every product card has a prominent "EXPLORE [COLLECTION NAME]" button at the bottom
- Links to the collection's product gallery/landing page:
  - BLACK ROSE → `/collections/black-rose` or `template-collection-black-rose.php`
  - LOVE HURTS → `/collections/love-hurts` or `template-collection-love-hurts.php`
  - SIGNATURE → `/collections/signature` or `template-collection-signature.php`
- Secondary "View Full Collection" link in card footer

**Card UX:**
- Opens with smooth scale-up + backdrop blur animation
- Close with ESC, click outside, or X button
- Keyboard accessible (focus trap, arrow keys for gallery)
- Mobile: slides up as bottom sheet
- Swipe between products in same collection

**NEVER ACCEPTABLE:**
- Generic clothing that "looks similar" — must BE our product
- Missing collection branding — every card screams its collection identity
- Dead links — collection links must route to real pages
- Stock photography — AI models only, wearing OUR exact garments

---

## THREE IMAGE SOURCES (in priority order)

### SOURCE 1: Original Product Photography (highest quality)
Path: `assets/3d-models/{collection}/`

### SOURCE 2: 2.5D Processed Assets (transparent PNGs — ideal for Three.js)
Path: `assets/2d-25d-assets/`
- `_parallax.png` = transparent background, BEST for overlaying on 3D props
- `_detail.jpg` = close-up texture detail
- `_depth.jpg` = depth map for parallax effects
- `_shadow.jpg` = pre-baked shadow layer

### SOURCE 3: WordPress CDN (remote, high-res)
Mapping file: `assets/2d-25d-assets/product_image_mappings.json`

---

## EXACT FILE MAPPING: PRODUCT ID → REAL PHOTO

### BLACK ROSE COLLECTION (The Garden scene)

| Product ID | Name | Original Photo (assets/3d-models/black-rose/) | 2.5D Parallax (assets/2d-25d-assets/) |
|-----------|------|-----------------------------------------------|---------------------------------------|
| br-001 | BLACK Rose Crewneck | `PhotoRoom_000_20230616_170635.png` | — |
| br-002 | BLACK Rose Joggers | `PhotoRoom_003_20230616_170635.jpeg` | — |
| br-003 | BLACK is Beautiful Jersey | `5A8946B1-B51F-4144-BCBB-F028462077A0.jpg` | — |
| br-004 | BLACK Rose Hoodie | `Photo Dec 18 2023, 6 09 21 PM (1).png` | — |
| br-005 | BLACK Rose Hoodie Signature | `Photo Dec 18 2023, 6 09 21 PM (2).png` | — |
| br-006 | BLACK Rose Sherpa Jacket | `The BLACK Rose Sherpa.jpg` (front), `The BLACK Rose Sherpa Back.jpg` (back) | `The BLACK Rose Sherpa Back_parallax.png` |
| br-007 | BLACK Rose Basketball Shorts | `PhotoRoom_010_20231221_160237-1.jpeg` | — |
| br-008 | Women's BLACK Rose Hooded Dress | `Womens Black Rose Hooded Dress.jpeg` + `Womens Black Rose Hooded Dress-1.jpeg` | — |

### LOVE HURTS COLLECTION (The Ballroom scene)

| Product ID | Name | Original Photo (assets/3d-models/love-hurts/) | 2.5D Parallax |
|-----------|------|------------------------------------------------|---------------|
| lh-001 | The Fannie | `The FANNIE Pack.jpg` or `_Love Hurts Collection_ _Fannie_ Pack.jpg` | — |
| lh-002 | Love Hurts Joggers | `_Love Hurts Collection_ Sincerely Hearted Joggers (Black).jpg` | — |
| lh-003 | Love Hurts Basketball Shorts | `PhotoRoom_002_20221110_201626.png` | — |
| lh-004 | Love Hurts Varsity Jacket | `Men windbreaker jacket (1).png` | — |
| lh-005 | Love Hurts Windbreaker (Women) | `Womens windbreaker jackets.png` | — |

### SIGNATURE COLLECTION (The Runway scene)

| Product ID | Name | Original Photo (assets/3d-models/signature/) | 2.5D Parallax (assets/2d-25d-assets/) |
|-----------|------|-----------------------------------------------|---------------------------------------|
| sg-001 | The Bay Set (Yay Bridge) | `Photo Sep 20 2022, 7 56 54 PM.jpg` | `The Yay Bridge Set_parallax.png` |
| sg-002 | Stay Golden Tee | `Stay Golden Tee.jpg` | `Stay Golden Tee_parallax.png` |
| sg-003 | Pink Smoke Crewneck | `The Pink Smoke Crewneck.jpg` | `The Pink Smoke Crewneck_parallax.png` |
| sg-004 | Signature Hoodie | `_Signature Collection_ Hoodie.jpg` | `_Signature Collection_ Hoodie_parallax.png` |
| sg-005 | Signature Shorts | `The Signature Shorts.jpg` | `The Signature Shorts_parallax.png` |
| sg-006 | Cotton Candy Tee | `_Signature Collection_ Cotton Candy Tee.jpg` | `_Signature Collection_ Cotton Candy Tee_parallax.png` |
| sg-007 | Cotton Candy Shorts | `_Signature Collection_ Cotton Candy Shorts.jpg` | `_Signature Collection_ Cotton Candy Shorts_parallax.png` |
| sg-008 | Crop Hoodie | `_Signature Collection_ Crop Hoodie front.jpg` | `_Signature Collection_ Crop Hoodie front_parallax.png` |
| sg-009 | Red Rose Beanie | `Signature Collection Red Rose Beanie.jpg` | `Signature Collection Red Rose Beanie_parallax.png` |
| sg-010 | Lavender Rose Beanie | `_Signature Collection_ Lavender Rose Beanie.jpg` | `_Signature Collection_ Lavender Rose Beanie_parallax.png` |
| sg-011 | Original Label Tee (White) | `_Signature Collection_ Original Label Tee (White).jpg` | `_Signature Collection_ Original Label Tee (White)_parallax.png` |
| sg-012 | Original Label Tee (Orchid) | `_Signature Collection_ Original Label Tee (Orchid).jpg` | `_Signature Collection_ Original Label Tee (Orchid)_parallax.png` |
| sg-013 | Sherpa v2 | (in `_Signature Collection_/` subfolder) | `_The Signature Collection_ The Sherpa 2_parallax.png` |
| sg-014 | Sherpa v3 | (in `_Signature Collection_/` subfolder) | `_The Signature Collection_ The Sherpa 3_parallax.png` |

---

## HOW TO LOAD THESE INTO THREE.JS

### For `_parallax.png` files (transparent — BEST for props):
```javascript
const loader = new THREE.TextureLoader();
const texture = loader.load('assets/2d-25d-assets/Stay Golden Tee_parallax.png');
const material = new THREE.MeshBasicMaterial({
  map: texture,
  transparent: true,
  alphaTest: 0.1,
  side: THREE.DoubleSide
});
const plane = new THREE.Mesh(new THREE.PlaneGeometry(aspectW, aspectH), material);
prop.add(plane); // PARENT to the prop mesh, not scene root
```

### For `.jpg` / `.jpeg` / `.png` originals (when no parallax exists):
```javascript
const texture = loader.load('assets/3d-models/black-rose/Womens Black Rose Hooded Dress.jpeg');
const material = new THREE.MeshBasicMaterial({
  map: texture,
  transparent: true, // only if PNG
  side: THREE.DoubleSide
});
// Create plane, parent to prop
```

### Aspect ratio matters:
- Hoodies/Jackets/Dresses: portrait ratio (~0.75:1)
- Shorts/Joggers: landscape-ish (~0.9:1)
- Beanies/Fanny pack: small square-ish (~1:1)
- Sets (Bay Set): wider (~1.2:1)

Scale product planes to be recognizable from the default camera position. Min texture size: the original photo resolution (these are all high-res).

---

## PRODUCT-ON-PROP PLACEMENT RULES

1. Products are PARENTED to prop meshes (bench, rack, pedestal, etc.)
2. Offset product plane 0.01-0.05 units above/in-front of prop surface to prevent z-fighting
3. Angle product plane to face the camera's general direction
4. Clothing items (hoodies, jerseys, dresses): drape angle (~15-20 degree tilt)
5. Flat items (shorts, joggers): lay flat on surface or slight lean
6. Small items (beanies, fannie pack): centered on prop surface

### THE GARDEN (Black Rose) — Prop Assignments:
- Stone bench → br-006 Sherpa Jacket (draped over back)
- Rose arbor arch → br-001 Crewneck (hanging from hook)
- Gothic standing mirror → br-008 Hooded Dress (displayed in front)
- Cathedral stone steps → br-002 Joggers (folded on step)
- Ornate iron gate → br-004 Hoodie (draped over top rail)
- Stone pedestal → br-003 Jersey (laid flat on top)

### THE BALLROOM (Love Hurts) — Prop Assignments:
- Velvet chaise lounge → lh-004 Varsity Jacket (draped across)
- Ornate gold picture frame → lh-002 Joggers (displayed inside frame)
- Marble-top side table → lh-001 The Fannie (sitting on surface)
- Vintage iron dress rack → lh-003 Basketball Shorts (hanging from hook)

### THE RUNWAY (Signature) — Prop Assignments:
- Industrial clothing rack (center) → sg-004 Hoodie + sg-008 Crop Hoodie (hanging)
- Glass display case (left) → sg-009 Red Rose Beanie + sg-010 Lavender Beanie (inside)
- Concrete pedestal (front) → sg-002 Stay Golden Tee (draped)
- Neon-lit wall → sg-001 Bay Set (mounted/displayed)
- Chrome rack (right) → sg-006 Cotton Candy Tee + sg-007 Cotton Candy Shorts
- Car hood (street element) → sg-005 Signature Shorts (laid on hood)
- Mannequin torso → sg-003 Pink Smoke Crewneck (worn on mannequin)
- Backlit panels → sg-011 + sg-012 Original Label Tees (lit from behind)
- Industrial shelf → sg-013 + sg-014 Sherpas (folded on shelf)

---

## INTERACTION ON CLICK:
- Raycaster on product plane meshes
- Hover: scale(1.05) + soft glow + product name tooltip
- Click: open modal with full product data from `CONFIG.rooms[].hotspots[].product`
- Product data (name, price, description, variants) is in `skyyrose/assets/js/config.js`
- Extended descriptions in `skyyrose/assets/data/product-content.json`

## QUALITY STANDARD:
- **Hotspot (scene):** Product on prop must be visually IDENTICAL to the real garment
- **Product card (modal):** AI model wearing a 100% replica of the garment, collection-branded card, link to collection page
- AI generation tools: Gemini (`build/generate-fashion-models.js`), HuggingFace Spaces
- ALWAYS pass the original product photo (paths in table above) as reference input for AI generation
- Every product card MUST link to its collection landing page — no dead ends
- If AI can't nail a 100% replica, use the original product photo as fallback hero — never show a bad likeness
