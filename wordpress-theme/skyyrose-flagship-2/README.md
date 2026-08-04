# SkyyRose Flagship 2

A classic WordPress theme for standard WordPress and WooCommerce installations.
It is marketplace-ready in packaging and installation boundaries, but it is not
a cross-platform frontend: Shopify, headless, or non-WordPress deployments need
their own adapter rather than a copied PHP theme.

## Requirements

- WordPress 6.8 or newer
- PHP 8.2 or newer
- WooCommerce for shop, product, cart, and checkout surfaces

Activate WooCommerce before activating this theme. Without it, editorial pages
continue to render but commerce components intentionally fall back safely.

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

## Installation

1. Upload the `skyyrose-flagship-2` directory as a complete theme archive; do
   not omit the tracked `.min.css` and `.min.js` production assets.
2. Activate the theme in **Appearance > Themes**.
3. Install and activate WooCommerce, then assign its Shop, Cart, Checkout, and
   My Account pages.
4. Create the documented routes and select the collection template where a
   site uses custom page permalinks.
5. Add menus to the Primary Menu and Footer Menu locations.

The theme uses WooCommerce as product, tax, shipping, stock, and order truth.
Stripe may be enabled through a WooCommerce payment gateway; it must not become
a second catalog or order system.

## Development checks

```bash
find . -name '*.php' -print0 | xargs -0 -n1 php -l
node --check assets/js/theme.js
```

Run the PHP and JavaScript checks before creating an archive. Test the archive
on a staging WordPress install with WooCommerce active, including product,
cart, checkout, and an accessibility keyboard pass. No deployment scripts are
included. Activate only after staging review.

Create an installable archive from tracked files with:

```bash
./scripts/package-theme.sh
```

The resulting `dist/skyyrose-flagship-2.zip` contains one top-level theme
directory and excludes local dependencies, editor files, and uncommitted work.
