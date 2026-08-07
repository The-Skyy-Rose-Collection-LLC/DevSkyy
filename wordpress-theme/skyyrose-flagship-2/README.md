# SkyyRose Flagship 2

Isolated marketplace-ready WooCommerce theme. Existing production templates remain untouched; approved campaign visuals were promoted into production SOT registry.

## Included surfaces

- Homepage with GPT-Image-2 campaign hero, founder-provided TSRC transparent rotating mark, SOT SkyyRose script title, collection runway, live featured products, origin story, and pre-order portal.
- Collections index plus automatic routes for Signature, Black Rose, Love Hurts, and Kids Capsule.
- Collection-specific lockups, fonts, palettes, stories, product grids, immersive horizontal chapters, lookbooks, and cross-navigation.
- WooCommerce shop archive, collection-aware single product, cart, notices, tabs, and checkout-ready controls.
- Pre-Order, About, Contact, and generic content pages.
- Keyboard-operable navigation, pinned vertical-to-horizontal Scroll World on desktop, native snap scrolling on touch/reduced-motion, visible focus, image curtain reveals, sticky narrative chapters, and pointer-depth enhancement.

## Asset contract

- `assets/sot/` contains theme-local copies of verified non-product visuals and self-hosted fonts from current SkyyRose SOT.
- Product truth and product imagery remain WooCommerce-managed.
- `assets/sot/` contains runtime campaign art registered in production `data/visual-manifest.json` version 1.3.1. `IMAGE-PROMPTS.md` preserves GPT-Image-2 generation provenance without duplicate staging assets.
- No legacy asset bundle exists in this theme.
- Theme has no dependency on current production theme after upload.

## Routes

Create pages using these slugs:

- `/collections/`
- `/collections/signature/`
- `/collections/black-rose/`
- `/collections/love-hurts/`
- `/collections/kids-capsule/`
- `/pre-order/`
- `/about/`
- `/contact/`

Collection routes map automatically to `template-collection.php`; manual template selection is optional.

## Development checks

```bash
find . -name '*.php' -print0 | xargs -0 -n1 php -l
node --check assets/js/theme.js
```

No deployment scripts included. Activate only after staging review.
