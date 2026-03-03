# SkyyRose Flagship Theme

> Production WordPress theme (v3.2.0) | 31 CSS, 24 JS, 23 inc/ modules, 28 templates

---

## Critical Rules

- **REST API**: Use `index.php?rest_route=` NOT `/wp-json/` (WordPress.com requirement)
- **Immersive pages** = 3D storytelling (NOT shopping)
- **Catalog pages** = product grids (FOR shopping)
- **Serena MCP** for all file operations (NOT direct file access)
- **Context7** before ANY WordPress/WooCommerce/Elementor code

---

## Structure

```
skyyrose-flagship/
├── functions.php              # Bootstrap: constants + inc/ loader
├── header.php / footer.php    # Site chrome
├── front-page.php             # Homepage
│
├── template-immersive-*.php   # 3D storytelling (3 collections)
├── template-collection-*.php  # Product catalog grids (4 collections)
├── template-preorder-gateway.php  # Pre-order funnel (money page)
├── template-about.php         # Brand story + press
├── template-style-quiz.php    # Interactive quiz
│
├── inc/                       # Backend modules (23 files)
│   ├── product-catalog.php    # Product data + catalog logic
│   ├── ajax-handlers.php      # AJAX endpoints
│   ├── enqueue.php            # Script/style loading
│   ├── security.php           # CSP headers, nonces
│   ├── woocommerce.php        # WC integration
│   └── elementor.php          # Elementor widgets
│
├── template-parts/            # Reusable partials
│   ├── front-page/            # Homepage sections
│   ├── size-guide-modal.php   # Size guide overlay
│   └── brand-ambassador.php   # Brand avatar component
│
├── assets/
│   ├── css/                   # 31 stylesheets
│   ├── js/                    # 24 scripts
│   ├── images/products/       # 80+ product images (renders, sources, patches)
│   ├── images/mascot/         # 7 mascot PNGs
│   ├── images/customers/      # 8 customer photos
│   ├── images/instagram/      # 6 feed images
│   └── scenes/                # 3D scene imagery (love-hurts, black-rose, signature)
│
├── elementor/widgets/         # Custom Elementor widgets
├── woocommerce/               # WC template overrides
└── data/                      # Static product/collection data
```

---

## Key Files

| File | Purpose |
|------|---------|
| `inc/product-catalog.php` | Product array, collection definitions, pricing |
| `inc/ajax-handlers.php` | Cart add, size guide, newsletter AJAX |
| `assets/js/immersive.js` | 3D storytelling engine |
| `assets/js/conversion-engine.js` | Pre-order funnel tracking |
| `assets/js/preorder-gateway.js` | Pre-order page interactions |
| `assets/css/immersive.css` | 3D experience styling |
| `assets/css/front-page.css` | Homepage layout |

---

## Sales Funnel Flow

```
Interactive Pages → Collection Landing → Pre-Order Gateway → Cart
(immersive-*.php)  (collection-*.php)   (preorder-gateway.php)
```

---

## Learnings

- Pre-order page has **6 products only** (not all 28) — check `is_preorder` flag in `product-catalog.php`
- Product images follow naming: `{sku}-{view}-{type}.webp` (e.g., `br-001-front-model.webp`)
- 3 render views per product: `render-front`, `render-back`, `render-branding`
- Mascot appears on: homepage, 404, pre-order, collection pages, and as reference sheet

---

## Verification

```bash
# Check theme version
head -15 wordpress-theme/skyyrose-flagship/style.css

# Count assets
ls wordpress-theme/skyyrose-flagship/assets/css/*.css | wc -l
ls wordpress-theme/skyyrose-flagship/assets/js/*.js | wc -l
ls wordpress-theme/skyyrose-flagship/inc/*.php | wc -l
```
