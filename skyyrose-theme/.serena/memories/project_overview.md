# SkyyRose Flagship Theme - Project Overview

## Purpose
Premium flagship WordPress theme for SkyyRose e-commerce platform featuring:
- Three.js 3D product visualization integration
- Full WooCommerce support
- Elementor Pro compatibility
- Modern web standards with performance optimization

## Tech Stack
- **CMS**: WordPress 6.0+ (PHP 7.4+)
- **E-commerce**: WooCommerce
- **Page Builder**: Elementor Pro
- **3D Graphics**: Three.js v0.159.0
- **Build Tools**: Webpack 5, clean-css-cli
- **Testing**: Jest, Playwright, Lighthouse, Pa11y, Axe
- **Code Quality**: ESLint, Prettier, Husky

## Codebase Structure
```
/
├── functions.php           # Main theme functions
├── inc/                    # Theme functionality modules
│   ├── woocommerce.php     # WooCommerce integration
│   ├── elementor.php       # Elementor integration
│   ├── wishlist-functions.php # Wishlist REST API
│   └── template-functions.php
├── assets/
│   ├── js/                 # JavaScript (Three.js, wishlist, etc.)
│   └── css/                # Additional stylesheets
├── template-parts/         # Reusable template components
├── woocommerce/            # WooCommerce template overrides
├── elementor/              # Elementor widgets
├── tests/                  # Jest + Playwright tests
└── scripts/                # Build and validation scripts
```

## WordPress Coding Standards
- Follows WordPress PHP Coding Standards
- Function names: `skyyrose_` prefix, lowercase with underscores
- Hook priority: 10 (default) unless timing-critical
- Output escaping: Always use `esc_html()`, `esc_attr()`, `wp_kses_post()`
- Localization: All strings wrapped in `esc_html__()` with `skyyrose-flagship` text domain
