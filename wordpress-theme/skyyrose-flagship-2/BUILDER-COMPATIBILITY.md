# Builder compatibility

SkyyRose Flagship 2 is a classic WooCommerce theme with a builder-neutral
content contract. The theme owns its brand shell, collection worlds, and safe
WooCommerce fallbacks; an installed builder may explicitly own page content.

## Supported contracts

| Builder | Page content | Canvas/full width | Theme locations | Notes |
|---|---:|---:|---:|---|
| WordPress block editor | Yes | Yes | Theme fallback | Wide alignment and core block styles enabled. |
| Elementor | Yes | Yes | Header, footer, single, archive | Pro locations use Elementor's official registration and display APIs. Google Fonts output is disabled because theme fonts are self-hosted. |
| Divi Builder plugin | Yes | Yes | Divi Theme Builder/plugin-owned | `et-builder` theme support is enabled. Product 3D remains available only through the theme's approved-model resolver. |
| Beaver Builder | Yes | Yes | Plugin-owned | Builder-owned pages receive an unwrapped content area. |

Bricks is not compatible because Bricks is an active WordPress theme, not a
page-builder plugin that can run alongside SkyyRose. Supporting its editor
would require a separate Bricks implementation, not a SkyyRose theme option.

`Builder Full Width` keeps the SkyyRose header and footer. `Builder Canvas`
keeps required WordPress lifecycle hooks but removes the theme shell. Standard
pages also defer automatically when supported builder metadata marks the page
as builder-owned.

## Commerce boundary

WooCommerce remains authoritative for catalog, prices, inventory, tax,
shipping, cart, checkout, orders, and payment state. Elementor Pro or a Divi
Theme Builder template may deliberately replace an assigned product/archive
presentation, but the theme's collection-aware WooCommerce templates remain
the fail-safe default.

Custom SkyyRose Elementor widgets and Divi modules are not included in V2 yet.
Those extensions belong in an optional companion plugin so builder-specific
functionality survives theme switches and the theme remains within marketplace
theme/plugin boundaries. They are not required for native builder widgets.

## Required staging proof

Source compatibility does not prove plugin runtime compatibility. Before a
marketplace claim, install the exact release ZIP on a clean WordPress staging
site and test the currently supported versions of each advertised builder:

1. Create, edit, preview, publish, and revise a standard page.
2. Verify Builder Full Width and Builder Canvas on desktop and mobile.
3. Verify Elementor Pro header/footer/single/archive assignments and fallbacks.
4. Verify Divi Visual Builder save/reload and Theme Builder assignments.
5. Verify shop, product, cart, checkout, account, and collection routes with
   and without assigned builder templates.
6. Deactivate each builder and confirm normal theme fallbacks return without
   fatal errors; document any builder-owned content portability limitations.
