# SkyyRose Flagship Theme — Project Overview

## Purpose
Production WordPress theme for SkyyRose LLC, a luxury streetwear fashion brand from Oakland, CA. 
Three collections: Black Rose (gothic/silver), Love Hurts (passionate/crimson), Signature (Bay Area/gold).

## Tech Stack
- WordPress custom theme (v4.0.0)
- PHP 7.4+ (no Composer autoloader, manual includes)
- WooCommerce integration (conditional)
- Elementor page builder (conditional, 8 widgets)
- CSS: 31+ stylesheets, design-token system, BEM naming
- JS: 24+ scripts, vanilla JS (no jQuery dependency for custom code)
- Fonts: Google Fonts CDN (8 families) + self-hosted fallbacks

## Brand Colors
- Rose Gold: #B76E79 (primary accent)
- Gold: #D4AF37 (Signature collection)
- Crimson: #DC143C (Love Hurts collection)
- Silver: #C0C0C0 (Black Rose collection)
- Dark: #0A0A0A (background)

## Key Files
- functions.php: Bootstrap loading 15+ inc/ modules
- inc/enqueue.php: Conditional CSS/JS loading per template (1226 lines)
- inc/product-catalog.php: 28 products across 3 collections
- header.php: Fixed glassmorphism navbar (.navbar__ BEM)
- footer.php: 5-column grid footer with newsletter
- design-tokens.css + brand-variables.css: CSS variable system
