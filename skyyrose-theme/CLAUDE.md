# SkyyRose Theme Customizations

## Overview
Custom styling and assets for SkyyRose (skyyrose.co) built on the Shoptimizer theme with Elementor.

## Quick Start

### 1. Add Custom CSS
Copy contents of `css/skyyrose-custom.css` to one of:
- **Elementor**: Hamburger menu > Site Settings > Custom CSS
- **Customizer**: Appearance > Customize > Additional CSS
- **Child Theme**: Add to child theme's `style.css`

### 2. Import Products
1. Go to WooCommerce > Products > Import
2. Select `skyyrose-catalog.csv`
3. Map columns (should auto-detect)
4. Run import

### 3. Upload Product Images
Upload images from `assets/images/products/` to Media Library, then assign to products.

## Brand Rules

### Spelling
- **Correct**: SkyyRose (one word, capital S and R)
- **Wrong**: Skyy Rose, skyy rose, SKYYROSE, SkyRose

### Domain
- **Correct**: skyyrose.co
- **Wrong**: skyyrose.com

### Tone
- Luxury, elevated, boutique-ready
- Never use: discount, clearance, sale (unless actual promotion)

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Rosewood | `#8B4557` | Accent, hover states |
| Onyx | `#1A1A1A` | Primary text, buttons |
| Ivory | `#F5F5F0` | Backgrounds, button text |
| Gold | `#C9A962` | Premium accents |
| Heather | `#9B9B9B` | Muted text |

## Typography

| Element | Font | Weight |
|---------|------|--------|
| Headings | Playfair Display | 500 |
| Body | Inter | 400 |
| Accent | Cormorant Garamond | 500 italic |

## Collections

### Love Hurts (SS25)
Bold statements on heartbreak and resilience.
- The Heart Arose Track Pant
- The Heart Arose Bomber
- Devoted Short

### Signature (Core)
Essential pieces with refined details.
- The Standard Tee
- The Crest Beanie
- The Piedmont Jacket

## File Structure
```
skyyrose-theme/
├── CLAUDE.md              # This file
├── manifest.json          # Brand tokens + asset registry
├── skyyrose-catalog.csv   # WooCommerce product import
├── css/
│   └── skyyrose-custom.css
└── assets/images/products/
    ├── love-hurts/
    └── signature/
```
