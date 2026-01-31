# SkyyRose WordPress Theme - Complete Build Plan

## Executive Summary

**Objective**: Create a production-ready, luxury fashion WordPress theme for SkyyRose that matches the brand's "Where Love Meets Luxury" positioning with immersive experiences, on-brand imagery, and complete content.

**Status**: Phase 1 - Foundation (Templates need on-brand assets)
**Timeline**: 2-3 weeks for complete production build
**Budget Considerations**: Photography, 3D assets, premium fonts (if needed)

---

## Brand Identity System

### Color Palette

```css
/* Primary Collections */
--black-rose-primary: #8B0000;      /* Deep crimson */
--black-rose-secondary: #DC143C;    /* Crimson highlight */
--black-rose-dark: #3D0000;         /* Shadow tone */

--love-hurts-primary: #B76E79;      /* Rose gold */
--love-hurts-secondary: #E91E63;    /* Pink accent */
--love-hurts-light: #FFB6C1;        /* Soft pink */

--signature-primary: #D4AF37;       /* Gold */
--signature-secondary: #FFD700;     /* Bright gold */
--signature-bronze: #CD7F32;        /* Bronze accent */

/* Neutrals */
--bg-dark: #030303;
--bg-deeper: #000000;
--text-primary: #FFFFFF;
--text-secondary: rgba(255,255,255,0.7);
--text-tertiary: rgba(255,255,255,0.5);
```

### Typography

```css
/* Primary Font Stack */
font-family: 'Playfair Display', Georgia, serif;  /* Headings */
font-family: 'Inter', -apple-system, sans-serif;  /* Body */
font-family: 'Share Tech Mono', 'Courier New', monospace; /* Tech/Vault */

/* Sizes */
--h1: clamp(3.5rem, 9vw, 7.5rem);
--h2: clamp(2.5rem, 6vw, 4rem);
--h3: clamp(1.8rem, 4vw, 2.5rem);
--body: 1rem;
--small: 0.875rem;
--tiny: 0.75rem;
```

### Voice & Tone

| Element | Voice | Example |
|---------|-------|---------|
| Headlines | Bold, Poetic | "Where Love Meets Luxury" |
| Body Copy | Confident, Aspirational | "For those who dare to feel" |
| CTAs | Direct, Urgent | "Secure Your Piece" |
| Product Descriptions | Detailed, Premium | "Hand-crafted Italian wool, tailored to perfection" |
| Error Messages | Friendly, Helpful | "We couldn't find that. Let's get you back on track." |

---

## Asset Requirements

### Photography Style Guide

#### Collection-Specific Aesthetics

**Black Rose Collection:**
- **Mood**: Dark, gothic, mysterious
- **Lighting**: Low-key, dramatic shadows, rim lighting
- **Environment**: Industrial spaces, gothic architecture, urban night
- **Models**: Strong poses, intense expressions
- **Color Grading**: Desaturated with red/crimson highlights
- **Props**: Roses, thorns, wrought iron, leather

**Love Hurts Collection:**
- **Mood**: Romantic, vulnerable, emotional depth
- **Lighting**: Soft, diffused, golden hour
- **Environment**: Castles, gardens, intimate spaces
- **Models**: Emotive, raw expressions
- **Color Grading**: Warm tones, pink/rose gold glow
- **Props**: Flowers, mirrors, candles, vintage frames

**Signature Collection:**
- **Mood**: Luxurious, timeless, sophisticated
- **Lighting**: Clean, editorial, high-key
- **Environment**: Minimalist studios, modern architecture, runways
- **Models**: Confident, poised
- **Color Grading**: Neutral with gold accents
- **Props**: Gold details, geometric shapes, premium fabrics

### Required Image Assets

#### Homepage (template-home.php)
```
assets/images/homepage/
├── hero-bg-black-rose.jpg        (1920x1080, dark/red ambiance)
├── hero-bg-love-hurts.jpg        (1920x1080, pink/romantic)
├── hero-bg-signature.jpg         (1920x1080, gold/minimal)
├── collection-card-black-rose.jpg (800x1200, portrait)
├── collection-card-love-hurts.jpg (800x1200, portrait)
└── collection-card-signature.jpg  (800x1200, portrait)
```

#### Collection Pages
```
assets/images/collections/black-rose/
├── hero-banner.jpg               (1920x600, wide banner)
├── product-01-front.jpg          (1000x1000, square)
├── product-01-back.jpg
├── product-01-detail.jpg
├── product-02-front.jpg
└── ... (repeat for 6-10 products per collection)

assets/images/collections/love-hurts/
└── [same structure]

assets/images/collections/signature/
└── [same structure]
```

#### Vault/Pre-Order Page
```
assets/images/vault/
├── vault-bg-matrix.jpg           (1920x1080, tech aesthetic)
├── product-prototype-3d.jpg      (800x800)
├── product-mystery-box.jpg       (800x800)
└── product-crystal-rose.jpg      (800x800)
```

#### Logos & Brand Assets
```
assets/images/branding/
├── skyyrose-logo-full.svg        (Main logo)
├── skyyrose-logo-icon.svg        (Icon only)
├── black-rose-logo.png           (Collection logo)
├── love-hurts-logo.png
├── signature-logo.png
└── where-love-meets-luxury.svg   (Tagline)
```

### 3D Assets

```
assets/models/
├── black-rose/
│   ├── thorn-hoodie.glb          (< 5MB, optimized)
│   ├── gothic-dress.glb
│   └── sherpa-jacket.glb
├── love-hurts/
│   ├── rose-hoodie.glb
│   └── castle-dress.glb
└── signature/
    ├── foundation-blazer.glb
    ├── icon-trench.glb
    └── signature-shorts.glb
```

### Video Assets (Optional Enhancement)

```
assets/videos/
├── hero-ambient-loop.mp4         (30s loop, 1920x1080, muted)
├── collection-black-rose.mp4     (15s teaser)
├── collection-love-hurts.mp4
└── collection-signature.mp4
```

---

## Content Strategy

### Page Inventory & Content Requirements

#### 1. Homepage
**URL**: `/`
**Template**: `template-home.php`

**Content Blocks**:
1. **Hero Section**
   - Headline: "Where Love Meets Luxury"
   - Subheadline: "Oakland-born streetwear that marries edge with elegance"
   - CTA 1: "Pre-Order Now" → `/vault`
   - CTA 2: "Explore Collections" → scroll to collections

2. **Collections Preview**
   - 3 cards with hover reveals
   - Each links to immersive experience

3. **Featured Products** (NEW - to be added)
   - 6 hero products across collections
   - WooCommerce integration

4. **Brand Story** (NEW - to be added)
   - "Oakland roots, global vision"
   - Founder story or manifesto

5. **Social Proof** (NEW - to be added)
   - Instagram feed or testimonials

#### 2. Collection Pages (x3)
**URLs**: `/black-rose`, `/love-hurts`, `/signature`
**Template**: `template-collection.php`

**Content for Each**:
- Hero banner with collection name + tagline
- Collection philosophy (2-3 paragraphs)
- Product grid (8-12 products)
- Category filters (Tops, Bottoms, Outerwear, Accessories)
- Lookbook gallery (optional)

**Copy Examples**:

**Black Rose**:
```
Headline: "Black Rose"
Tagline: "Dark Elegance. Uncompromised Strength."

Body: "For those who find beauty in shadows. The Black Rose collection
embodies gothic romance meets modern streetwear—sharp silhouettes,
deep crimson accents, and premium black fabrics that command attention.
Each piece is a statement of resilience and power."
```

**Love Hurts**:
```
Headline: "Love Hurts"
Tagline: "Wear Your Heart. Feel Everything."

Body: "Vulnerability is strength. The Love Hurts collection celebrates
raw emotion through soft rose-gold tones, distressed details, and
romantic silhouettes. For those brave enough to love deeply, hurt
openly, and rise stronger."
```

**Signature**:
```
Headline: "Signature"
Tagline: "Timeless Luxury. Absolute Refinement."

Body: "The foundation of your wardrobe. Our Signature collection defines
modern luxury with gold accents, architectural cuts, and premium Italian
fabrics. Classic pieces elevated to art."
```

#### 3. Immersive Collection Experiences (x3)
**URLs**: `/01-black-rose-garden`, `/02-love-hurts-castle`, `/03-signature-runway`
**Template**: `template-immersive-collection.php`

**Content for Each**:
- Full-screen 3D environment
- Interactive product hotspots (6-8 products)
- Ambient music/sound (optional)
- "Enter Standard View" fallback link

#### 4. Vault (Pre-Order)
**URL**: `/vault`
**Template**: `template-vault.php`

**Content**:
- Rotating collection logos
- 3 exclusive pre-order items:
  1. **The Prototype** - First run, limited to 50
  2. **Mystery Box** - Curated surprise
  3. **Crystal Rose** - Ultra-luxury collector's item

#### 5. Single Product Page
**URL**: `/product/[slug]`
**Template**: `single-product.php`

**Content Blocks**:
- Product gallery (4-6 images + optional 3D viewer)
- Title, price, collection badge
- Description (150-300 words)
- Size/color variations
- Care instructions
- Shipping info
- Related products

#### 6. About Page
**URL**: `/about`
**Template**: `page-about.php`

**Content**:
- Founder story
- Brand mission: "Where Love Meets Luxury"
- Oakland roots
- Design philosophy
- Team photos (optional)
- Press mentions

#### 7. Contact Page
**URL**: `/contact`
**Template**: `page-contact.php`

**Content**:
- Contact form
- Email: hello@skyyrose.co
- Social media links
- FAQ section

---

## Placeholder Image Strategy

### Immediate Solution (Days 1-3)

**Option 1: AI-Generated Placeholders**
Use Midjourney/DALL-E with brand-specific prompts:

```
Black Rose Collection:
"luxury gothic streetwear, dark crimson hoodie on model,
dramatic lighting, moody fashion photography, 4k, professional"

Love Hurts Collection:
"romantic luxury streetwear, rose gold dress on model,
soft golden hour lighting, emotional fashion photography, 4k"

Signature Collection:
"minimalist luxury streetwear, gold-accented blazer on model,
clean editorial lighting, modern fashion photography, 4k"
```

**Option 2: Curated Stock Photography**
Sources:
- Unsplash (free, high-quality)
- Pexels (free)
- Adobe Stock (paid, but premium)

Search terms:
- "luxury streetwear dark"
- "gothic fashion model"
- "rose gold fashion editorial"
- "minimalist luxury clothing"

**Option 3: 3D Renders (For Products)**
Use CLO3D, Marvelous Designer, or Blender to create:
- Product renderings that match your aesthetic
- Can be photorealistic
- Full control over colors, textures, lighting
- Reusable across sizes/variations

### Long-term Solution (Weeks 2-4)

**Professional Photoshoot**:
- Hire Oakland-based fashion photographer
- 3 models (one per collection aesthetic)
- 3 locations (urban, romantic, minimal)
- 30-50 edited images
- Estimated budget: $3,000-$8,000

**DIY Professional Quality**:
- Rent photo studio ($50-150/hour)
- Friends/local models
- DSLR or high-end smartphone
- Lightroom for editing
- Estimated budget: $500-$1,500

---

## Technical Architecture

### File Structure

```
skyyrose-2025/
├── style.css                      # Theme header + base styles
├── functions.php                  # Theme setup, enqueues
├── header.php                     # Global header
├── footer.php                     # Global footer
├── index.php                      # Blog archive fallback
├── 404.php                        # Error page
│
├── templates/
│   ├── template-home.php          # Homepage ✅
│   ├── template-vault.php         # Pre-order ✅
│   ├── template-collection.php    # Product grid ✅
│   ├── template-immersive.php     # 3D experience 🔲
│   ├── page-about.php             # About page 🔲
│   └── page-contact.php           # Contact page 🔲
│
├── woocommerce/
│   ├── single-product.php         # Product detail override 🔲
│   ├── archive-product.php        # Shop page override
│   ├── cart/
│   │   └── cart.php               # Cart page override
│   └── checkout/
│       └── form-checkout.php      # Checkout override
│
├── parts/
│   ├── navbar.php                 # Reusable navbar component
│   ├── collection-card.php        # Reusable collection card
│   └── product-card.php           # Reusable product card
│
├── inc/
│   ├── woocommerce-setup.php      # WooCommerce customizations
│   ├── custom-meta-boxes.php      # Product meta fields
│   ├── ajax-handlers.php          # AJAX cart, filters
│   └── shortcodes.php             # Custom shortcodes
│
├── assets/
│   ├── css/
│   │   ├── global.css             # Base styles
│   │   ├── components.css         # Reusable components
│   │   └── utilities.css          # Utility classes
│   ├── js/
│   │   ├── main.js                # Global scripts
│   │   ├── 3d-viewer.js           # Three.js viewer
│   │   ├── animations.js          # GSAP animations
│   │   └── cart.js                # Cart interactions
│   ├── images/                    # [See Asset Requirements]
│   ├── models/                    # GLB 3D models
│   └── fonts/                     # Custom fonts (if any)
│
└── languages/                     # Translation files
    └── skyyrose-2025.pot
```

### WordPress Customizer Options

Add theme customization panel:

```php
// In functions.php
function skyyrose_customize_register($wp_customize) {
    // Brand Colors
    $wp_customize->add_section('skyyrose_colors', [
        'title' => 'SkyyRose Colors',
        'priority' => 30,
    ]);

    $wp_customize->add_setting('black_rose_color', [
        'default' => '#8B0000',
    ]);

    // Collection Toggles
    $wp_customize->add_section('skyyrose_collections', [
        'title' => 'Collection Settings',
    ]);

    $wp_customize->add_setting('show_immersive_experiences', [
        'default' => true,
    ]);

    // Homepage Layout
    $wp_customize->add_section('skyyrose_homepage', [
        'title' => 'Homepage Layout',
    ]);

    $wp_customize->add_setting('hero_headline', [
        'default' => 'Where Love Meets Luxury',
    ]);
}
add_action('customize_register', 'skyyrose_customize_register');
```

---

## WooCommerce Product Structure

### Product Meta Fields (Custom)

```php
// All products
_skyyrose_collection         // 'black-rose', 'love-hurts', 'signature'
_skyyrose_3d_model_url      // URL to GLB file
_product_badge              // 'NEW', 'EXCLUSIVE', 'LIMITED'
_care_instructions          // Washing/care details
_fabric_composition         // Material breakdown

// Vault products only
_vault_preorder             // '1' if in vault
_vault_badge                // 'ENCRYPTED', 'LIMITED', 'ARCHIVE'
_vault_quantity_limit       // Max units (blank = unlimited)
_vault_quantity_sold        // Current sold count
_vault_icon                 // Emoji or icon class

// Immersive products only
_hotspot_position_x         // 3D scene position
_hotspot_position_y
_hotspot_position_z
```

### Sample Product Data

**Product**: Black Rose Sherpa Jacket

```
Name: Black Rose Sherpa Jacket
SKU: BR-SHERPA-001
Price: $185.00
Sale Price: -
Categories: [Black Rose, Outerwear]
Tags: [gothic, winter, sherpa, limited-edition]

Description:
"Embrace the cold in gothic luxury. Our Black Rose Sherpa combines
premium black fleece with deep crimson embroidered roses. Oversized
fit, zip-front closure, and signature thorn-shaped zipper pull.
Oakland-designed, globally crafted."

Short Description:
"Gothic luxury meets cozy comfort. Premium black sherpa with crimson
rose embroidery."

Meta Fields:
_skyyrose_collection: black-rose
_skyyrose_3d_model_url: https://cdn.skyyrose.co/models/black-rose-sherpa.glb
_product_badge: LIMITED
_fabric_composition: 100% Polyester Fleece, Embroidered Details
_care_instructions: Machine wash cold, tumble dry low

Variations:
- Size: S, M, L, XL, XXL
- All same price

Stock: 50 units (10 per size)
```

---

## Development Roadmap

### Phase 1: Foundation (Week 1)
- [x] Basic theme structure
- [x] Homepage template (needs assets)
- [x] Vault template (needs assets)
- [x] Collection grid template (needs assets)
- [ ] Source/create placeholder images
- [ ] Update templates with real imagery
- [ ] Test responsive layouts

### Phase 2: Immersive Experiences (Week 2)
- [ ] Three.js immersive template
- [ ] 3D model integration
- [ ] Interactive hotspots
- [ ] Camera movement system
- [ ] Fallback for non-3D browsers
- [ ] Performance optimization

### Phase 3: WooCommerce Integration (Week 2-3)
- [ ] Single product page with 3D viewer
- [ ] Product quick view modal
- [ ] Cart page customization
- [ ] Checkout page styling
- [ ] Product filtering AJAX
- [ ] Inventory management hooks

### Phase 4: Content & Polish (Week 3-4)
- [ ] About page
- [ ] Contact page with form
- [ ] Blog template (optional)
- [ ] 404 error page
- [ ] Loading states/skeletons
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Cross-browser testing
- [ ] Performance optimization (PageSpeed 90+)

### Phase 5: Launch Prep (Week 4)
- [ ] Professional photography
- [ ] Final content writing
- [ ] SEO optimization
- [ ] Analytics setup (GA4)
- [ ] Social media integration
- [ ] Email marketing integration
- [ ] Pre-launch checklist

---

## Success Metrics

### Performance Targets
- PageSpeed Score: 90+ (mobile & desktop)
- Largest Contentful Paint: < 2.5s
- First Input Delay: < 100ms
- Cumulative Layout Shift: < 0.1
- 3D model load time: < 3s

### User Experience Targets
- Bounce rate: < 40%
- Average session duration: > 3min
- Pages per session: > 3
- Cart abandonment: < 70%
- Mobile conversion: 2%+

### SEO Targets
- Core Web Vitals: Pass
- Accessibility Score: 95+
- Schema markup: Product, Organization, BreadcrumbList
- Meta descriptions: 100% coverage
- Alt text: 100% coverage

---

## Budget Breakdown (Estimated)

| Item | Cost | Priority |
|------|------|----------|
| **Photography** | $3,000-8,000 | HIGH |
| Professional shoot (30-50 images) | | |
| **3D Assets** | $1,500-3,000 | MEDIUM |
| CLO3D subscription + modeling | | |
| **Premium Fonts** (if needed) | $0-500 | LOW |
| Adobe Fonts via Creative Cloud | | |
| **Stock Photography** (temporary) | $0-200 | HIGH |
| Unsplash Pro or Adobe Stock | | |
| **Development** (if outsourced) | $5,000-15,000 | N/A |
| Full theme build | | |
| **Total Estimated** | $9,500-26,700 | |

**DIY Budget**: $1,500-3,500 (using AI images, DIY photography, free tools)

---

## Next Actions

1. **Immediate** (This Week):
   - [ ] Generate AI placeholder images for all collections
   - [ ] Rebuild templates with placeholder imagery
   - [ ] Create component library (navbar, cards, buttons)
   - [ ] Set up WordPress Customizer options

2. **Short-term** (Next 2 Weeks):
   - [ ] Complete immersive template
   - [ ] Finish single product page
   - [ ] WooCommerce product sync script
   - [ ] Content writing for all pages

3. **Long-term** (Month 2):
   - [ ] Professional photoshoot
   - [ ] Replace all placeholders
   - [ ] Launch beta for testing
   - [ ] Collect user feedback
   - [ ] Optimize and refine

---

**Document Version**: 1.0
**Last Updated**: 2026-01-30
**Owner**: SkyyRose LLC
**Status**: Planning → Development
