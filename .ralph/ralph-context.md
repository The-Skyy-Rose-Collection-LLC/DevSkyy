# CORRECTION — READ THIS IMMEDIATELY

You made a mistake. The owner said **2 scenes per collection** (6 total). You built **4 scenes for Black Rose and 4 scenes for Love Hurts** (10 total). Fix this NOW.

---

## SCENE ASSIGNMENTS (FINAL — DO NOT ADD MORE)

### BLACK ROSE (pick 2, delete the other 2 rooms from the PHP template)
- **Scene 1**: `black-rose-moonlit-courtyard.png` — Moonlit Courtyard
- **Scene 2**: `black-rose-iron-gazebo-garden.png` — Iron Gazebo Garden
- BACKGROUND ONLY (not immersive rooms): `black-rose-marble-rotunda.png`, `black-rose-white-rose-grotto.png`

### LOVE HURTS (pick 2, delete the other 2 rooms from the PHP template)
- **Scene 1**: `love-hurts-cathedral-rose-chamber.png` — Cathedral Rose Chamber
- **Scene 2**: `love-hurts-gothic-ballroom.png` — Gothic Ballroom
- BACKGROUND ONLY (not immersive rooms): `love-hurts-crimson-throne-room.png`, `love-hurts-enchanted-rose-shrine.png`, `love-hurts-giant-rose-staircase.png`, `love-hurts-reflective-ballroom.png`

### SIGNATURE (already correct — 2 scenes)
- **Scene 1**: `signature-waterfront-runway.png` — Waterfront Runway
- **Scene 2**: `signature-golden-gate-showroom.png` — Golden Gate Showroom

All scene images are at: `assets/scenes/{collection}/`

Use the extra scene images as CSS backgrounds elsewhere in the theme (homepage hero sections, collection landing pages, etc.) — they are NOT wasted, they just shouldn't be immersive rooms.

---

## REAL PRODUCTS — USE THESE (from product-content.json)

### BLACK ROSE COLLECTION (8 products: br-001 through br-008)
| SKU | Name | Owner Price |
|-----|------|-------------|
| br-001 | BLACK Rose Crewneck | DRAFT (no price yet) |
| br-002 | BLACK Rose Joggers | $50 |
| br-003 | BLACK is Beautiful Jersey | DRAFT (no price yet) |
| br-004 | BLACK Rose Hoodie | $40 |
| br-005 | BLACK Rose Hoodie — Signature Edition | $65 |
| br-006 | BLACK Rose Sherpa Jacket | $95 |
| br-007 | BLACK Rose x Love Hurts Basketball Shorts | $65 |
| br-008 | Women's BLACK Rose Hooded Dress | TBD |

### LOVE HURTS COLLECTION (5 products: lh-001 through lh-004 + lh-002b)
| SKU | Name | Owner Price |
|-----|------|-------------|
| lh-001 | The Fannie (fanny pack) | $70 |
| lh-002 | Love Hurts Joggers (BLACK) | $67 |
| lh-002b | Love Hurts Joggers (WHITE) — NEW VARIANT | $67 |
| lh-003 | Love Hurts Basketball Shorts | $55 |
| lh-004 | Love Hurts Varsity Jacket | DRAFT (no price yet) |

### SIGNATURE COLLECTION (14 products: sg-001 through sg-014)
| SKU | Name | Owner Price |
|-----|------|-------------|
| sg-001 | The Bay Set — Tee | $40 |
| sg-001 | The Bay Set — Shorts | $50 |
| sg-002 | Stay Golden Set — Tee | $40 |
| sg-002 | Stay Golden Set — Shorts | $50 |
| sg-003 | The Signature Tee (Orchid) | $15 |
| sg-004 | (not in product-content.json — skip) | — |
| sg-005 | Stay Golden Tee | $40 |
| sg-006 | Mint & Lavender Hoodie | $45 |
| sg-007 | The Signature Beanie | $25 |
| sg-008 | (not in product-content.json — skip) | — |
| sg-009 | The Sherpa Jacket | $80 |
| sg-010 | The Bridge Series Shorts | $25 |
| sg-011-014 | DRAFT (no price yet) |

**NOTE**: sg-001 and sg-002 are sold as SEPARATE pieces (tee + shorts), NOT as sets. Create 2 WooCommerce products for each.

### Items with NO price = save as DRAFT in WooCommerce (not published)

---

## WHAT'S WRONG IN config.js (FIX THESE)

The prices in `skyyrose/assets/js/config.js` are WRONG. They were placeholder prices, not owner-confirmed. Examples:
- br-001 shows $125 → should be DRAFT
- br-002 shows $95 → should be $50
- br-004 shows $145 → should be $40
- lh-001 shows $65 → should be $70
- sg-001 shows $225 → should be $40 tee + $50 shorts (separate)

Update config.js with the correct prices from the table above.

---

## REMAINING TASKS (in order)

1. **FIX SCENES**: Reduce Black Rose and Love Hurts to 2 scenes each in their PHP templates. Use extra images as theme backgrounds.
2. **FIX PRICES**: Update config.js and all PHP templates with owner-confirmed prices above.
3. **ADD lh-002b**: White variant of Love Hurts Joggers — new product entry.
4. **SPLIT sg-001 and sg-002**: These are tee + shorts sold separately, not sets. Create separate product entries.
5. Continue with remaining tasks from original directive (AI imagery, mascot, WooCommerce products, deploy to skyyrose.co).

---

## TOOLS REMINDER
- Elite Web Development Team: `agents/elite_web_builder/`
- WordPress Copilot: `wordpress-copilot/`
- Context7: `resolve-library-id` → `query-docs` BEFORE any library code
- WordPress REST API: Use `index.php?rest_route=` NOT `/wp-json/`
- Product content source: `skyyrose/assets/data/product-content.json`
- Hotspot config source: `skyyrose/assets/js/config.js`
- Scene images: `assets/scenes/{collection}/`
