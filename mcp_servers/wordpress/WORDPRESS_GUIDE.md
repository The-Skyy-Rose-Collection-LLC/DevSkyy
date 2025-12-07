# SkyyRose Theme Development Guide

> **Where Love Meets Luxury** — Oakland's luxury streetwear brand  
> Website: skyyrose.co (NOT .com)

---

## 🏗️ Stack Overview

| Component | Technology |
|-----------|------------|
| CMS | WordPress |
| Page Builder | Elementor Pro |
| E-commerce | WooCommerce |
| Hosting | [Your host] |

---

## 📁 Asset Structure

```
/skyyrose-theme/
├── assets/
│   ├── images/
│   │   ├── products/
│   │   │   ├── love-hurts/        # Heart aRose line, Devoted, emotional pieces
│   │   │   ├── black-rose/        # Heritage line, dark elegance
│   │   │   └── signature/         # Standard, Crest, Piedmont, Marina lines
│   │   ├── logos/                 # Brand marks, wordmarks, icons
│   │   └── lifestyle/             # Campaign shots, lookbook imagery
│   ├── fonts/                     # Custom typography
│   └── icons/                     # UI icons, social icons
├── elementor/
│   ├── templates/                 # Saved Elementor templates (.json)
│   └── widgets/                   # Custom widget configs
├── css/
│   └── skyyrose-custom.css        # Custom styles outside Elementor
├── js/
│   └── skyyrose-custom.js         # Custom scripts
├── CLAUDE.md                      # This file
└── manifest.json                  # Asset registry
```

---

## 🎨 Brand Guidelines

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Obsidian | `#0D0D0D` | Primary black, text |
| Ivory | `#F5F5F0` | Light backgrounds, clean contrast |
| Rose Gold | `#B76E79` | Accent, CTAs, highlights |
| Ember | `#E85D04` | Energy accent (Heritage Ember) |
| Slate | `#4A4A4A` | Secondary text, subtle elements |
| Fog | `#E8E8E8` | Soft backgrounds |

### Typography

| Use | Font | Weight | Fallback |
|-----|------|--------|----------|
| Headlines | Playfair Display | 700 | Georgia, serif |
| Body | Montserrat | 400, 500 | Arial, sans-serif |
| Accent/Logo | Custom Script | — | — |

### Voice & Tone

- **Luxury, not loud** — understated elegance
- **Bay Area pride** — Oakland landmarks, not slang
- **Emotional depth** — "Love Hurts" is personal (Hurts = founder's family name)
- **Gender-neutral** — all pieces are unisex
- **No hyphy slang** — boutique-ready positioning

---

## 🏷️ Product Naming Convention

### Naming Structure

```
[The] + [Bay Area Landmark/Material] + [Product Type] + [- Variant]
```

### Examples

| Pattern | Example |
|---------|---------|
| Landmark + Type | The Piedmont Jacket |
| Material + Type | Obsidian Legging |
| Anchor + Variant | Heritage Jersey - Ember |
| Emotional + Type | Devoted Short |

### Collection Anchors

| Collection | Anchor Names | Variants |
|------------|--------------|----------|
| **BLACK ROSE** | Heritage, The Lake, Grand | Onyx, Ivory, Ember, Oak |
| **LOVE HURTS** | Heart aRose, Devoted, Tender | Onyx, Ivory |
| **SIGNATURE** | The Standard, The Crest, The Piedmont, The Marina | Rosewood, Heather, Slate |

### Banned Terms

- ❌ Hyphy slang (thizz, hella, go dumb, etc.)
- ❌ Street slang (turf, mob, scraper)
- ❌ Generic luxury words without context (premium, exclusive, limited)

### Preferred Terms

- ✅ Oakland neighborhoods (Piedmont, Rockridge, Temescal, Montclair)
- ✅ Bay landmarks (Lake Merritt, Marina, Grand Avenue, Fillmore)
- ✅ Material/gemstone names (Obsidian, Onyx, Slate, Ivory, Ember)
- ✅ Emotional depth (Devoted, Tender, Heritage)

---

## 🛠️ Elementor Development

### Global Settings

```
Site Settings → Colors → Add brand palette
Site Settings → Typography → Set Playfair + Montserrat
Site Settings → Layout → Container max-width: 1200px
```

### Recommended Widgets

| Purpose | Widget | Notes |
|---------|--------|-------|
| Product Grid | Posts/WooCommerce Products | Custom skin for luxury feel |
| Hero | Container + Heading + Button | Full-width, minimal text |
| Collection Banner | Container + Background | Overlay with collection name |
| Newsletter | Form | Minimal fields, elegant styling |

### Template Hierarchy

```
templates/
├── header.json              # Global header
├── footer.json              # Global footer
├── single-product.json      # WooCommerce product page
├── archive-product.json     # Shop/collection pages
├── collection-hero.json     # Reusable collection banner
└── homepage-sections/
    ├── hero.json
    ├── featured-collection.json
    └── about-brand.json
```

### Custom CSS Classes

```css
/* Add to Elementor → Custom CSS or child theme */

.sr-luxury-button {
    background: #0D0D0D;
    color: #F5F5F0;
    padding: 16px 32px;
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    border: none;
    transition: all 0.3s ease;
}

.sr-luxury-button:hover {
    background: #B76E79;
    color: #0D0D0D;
}

.sr-product-card {
    background: #FFFFFF;
    padding: 0;
    border: none;
    box-shadow: none;
}

.sr-product-card:hover {
    transform: translateY(-4px);
    transition: transform 0.3s ease;
}

.sr-collection-title {
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    letter-spacing: 1px;
}

.sr-body-text {
    font-family: 'Montserrat', sans-serif;
    font-weight: 400;
    line-height: 1.8;
    color: #4A4A4A;
}
```

---

## 📸 Image Specifications

### Product Images

| Type | Size | Format | Notes |
|------|------|--------|-------|
| Main | 1200x1200 | JPG | White background, centered |
| Gallery | 1200x1200 | JPG | Alternate angles, details |
| Thumbnail | 600x600 | JPG | Auto-generated by WooCommerce |
| Hover | 1200x1200 | JPG | Optional lifestyle/detail shot |

### Lifestyle/Campaign

| Type | Size | Format | Notes |
|------|------|--------|-------|
| Hero | 1920x1080 | JPG/WebP | Full-width, 16:9 |
| Collection Banner | 1600x600 | JPG/WebP | Wide, text overlay space |
| Instagram | 1080x1080 | JPG | Square format |

### File Naming

```
[product-slug]-[view]-[variant].jpg

Examples:
the-heart-arose-track-pant-front-onyx.jpg
heritage-jersey-detail-ember.jpg
devoted-short-lifestyle-01.jpg
```

---

## 🔌 WooCommerce Integration

### Product Categories

```
Shop
├── Love Hurts
│   ├── Outerwear
│   ├── Bottoms
│   └── Accessories
├── Black Rose
│   ├── Jerseys
│   ├── Tops
│   └── Outerwear
└── Signature
    ├── Essentials
    ├── Outerwear
    └── Accessories
```

### Product Attributes

| Attribute | Values |
|-----------|--------|
| Color | Onyx, Ivory, Ember, Oak, Rosewood, Heather, Slate |
| Size | Small, Medium, Large, X-Large, XX-Large, XXX-Large |
| Collection | Love Hurts, Black Rose, Signature |

### SKU Format

```
[PRODUCT-CODE]-[COLOR-CODE]-[SIZE]

Examples:
HARP-ONX-M      → Heart aRose Track Pant, Onyx, Medium
HRTY-EMB-L      → Heritage Jersey, Ember, Large
CRSTBN-HTH     → Crest Beanie, Heather (no size)
```

---

## 🚀 Deployment Checklist

### Before Launch

- [ ] All product images optimized (TinyPNG/ShortPixel)
- [ ] SEO titles and descriptions set
- [ ] Mobile responsiveness verified
- [ ] WooCommerce checkout tested
- [ ] Payment gateway connected
- [ ] Shipping zones configured
- [ ] Email notifications styled
- [ ] 404 page designed
- [ ] Favicon and site icon set

### Performance

- [ ] Lazy loading enabled
- [ ] CSS/JS minified
- [ ] CDN configured
- [ ] Caching plugin active
- [ ] WebP images enabled

---

## 📞 Quick Reference

| Resource | Location |
|----------|----------|
| Live Site | skyyrose.co |
| WP Admin | skyyrose.co/wp-admin |
| Elementor | Pages → Edit with Elementor |
| WooCommerce | Products → All Products |
| Media Library | Media → Library |

---

## 🤖 AI Instructions for Claude Code

When working on SkyyRose theme:

1. **Always use luxury Bay Area naming** — landmarks over slang
2. **Maintain unisex positioning** — avoid gendered language
3. **Follow color palette strictly** — Obsidian, Ivory, Rose Gold
4. **Product images → 1200x1200** — white background, centered
5. **Test mobile first** — Elementor responsive mode
6. **Commit with clear messages** — `feat: add Heart aRose product template`

### Common Tasks

```bash
# Sync assets to WordPress uploads
wp media import ./assets/images/products/**/*.jpg

# Export Elementor templates
wp elementor library export [template-id]

# Clear cache after changes
wp cache flush
```

---

*Last updated: December 2024*
*Maintained by DevSkyy*
