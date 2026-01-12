# Elementor Page Templates for SkyyRose Collections

> **Complete guide for building collection pages in Elementor with Three.js integration**
>
> **Created**: 2026-01-11
> **Theme**: Shoptimizer 2.9.0 + Child Theme
> **Elementor Version**: Pro 3.32.2+
> **Target Pages**: SIGNATURE, LOVE HURTS, BLACK ROSE collection pages

---

## 📋 Prerequisites

### Required Plugins
- [x] **Elementor Pro** (version 3.32.2+) - Page builder
- [x] **WooCommerce** (version 8.0+) - Ecommerce functionality
- [x] **Shoptimizer Theme** (version 2.9.0) - Base theme
- [x] **Shoptimizer Child Theme** - Custom Three.js integration

### Optional but Recommended
- [ ] **Rank Math SEO** - Schema.org markup, breadcrumbs
- [ ] **WP Rocket** - Caching for performance
- [ ] **EWWW Image Optimizer** - Auto WebP conversion

---

## 🎨 Collection Page Architecture

### Page Structure (All 3 Collections)

```
┌─────────────────────────────────────────┐
│  SECTION 1: Hero Header                 │
│  - Full-screen (100vh)                  │
│  - Collection name + tagline            │
│  - Scroll indicator                     │
│  - Optional: Video background           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  SECTION 2: Three.js 3D Experience      │
│  - Custom HTML widget                   │
│  - 600px height (desktop)               │
│  - Collection-specific scene            │
│  - Loading state + error handling       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  SECTION 3: Collection Story            │
│  - Text column (60%) + Image (40%)      │
│  - Brand narrative                      │
│  - Design philosophy                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  SECTION 4: Product Grid                │
│  - WooCommerce Products widget          │
│  - Filter by category                   │
│  - 3-column layout (desktop)            │
│  - 2-column (tablet), 1-column (mobile) │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  SECTION 5: Call to Action              │
│  - Newsletter signup or Instagram feed  │
│  - Trust badges                         │
│  - Free shipping message                │
└─────────────────────────────────────────┘
```

---

## 🛠️ Step-by-Step: Creating Collection Pages

### 1. Create New Page

**Path**: WordPress Admin → Pages → Add New

1. **Page Title**: "SIGNATURE Collection" (or "LOVE HURTS", "BLACK ROSE")
2. **Permalink**: `/collections/signature/` (lowercase, hyphens)
3. **Template**: Elementor Full Width (in Page Attributes)
4. **Edit with Elementor**: Click blue "Edit with Elementor" button

---

### 2. SECTION 1: Hero Header

**Add Section**:
- Elementor → Add Section → Single Column
- Section Settings → Layout:
  - Height: Min Height = 100vh
  - Column Position: Middle
  - Content Width: Full Width (100%)

**Background**:
- Style → Background Type: Classic or Gradient
- For **SIGNATURE**: Gradient (#FFE5E5 → #FFF5F0)
- For **LOVE HURTS**: Gradient (#2a1a2e → #4a2545)
- For **BLACK ROSE**: Solid (#0a0a0a)

**Add Column Content**:

1. **Heading Widget** (Collection Name):
   ```
   Content:
     Title: SIGNATURE
     HTML Tag: H1
   Style:
     Typography:
       Font Family: Inter
       Font Size: 80px (desktop), 48px (tablet), 36px (mobile)
       Font Weight: 800
       Letter Spacing: -2px
     Text Color: For SIGNATURE: #B76E79, Others: #ffffff
     Text Align: Center
   Advanced:
     Motion Effects → Entrance Animation: Fade In Up
   ```

2. **Text Editor Widget** (Tagline):
   ```
   Content:
     Text: "Timeless elegance meets modern luxury"
   Style:
     Typography:
       Font Size: 24px (desktop), 18px (mobile)
       Font Weight: 400
     Text Color: #666666 (SIGNATURE), #ffffff opacity 80% (others)
     Text Align: Center
   Advanced:
     Motion Effects → Entrance Animation: Fade In (delay 200ms)
   ```

3. **HTML Widget** (Scroll Indicator):
   ```html
   <div class="scroll-indicator" style="
     position: absolute;
     bottom: 2rem;
     left: 50%;
     transform: translateX(-50%);
     opacity: 0.6;
     animation: bounce 2s infinite;
   ">
     <div style="
       width: 24px;
       height: 24px;
       border-right: 2px solid currentColor;
       border-bottom: 2px solid currentColor;
       transform: rotate(45deg);
     "></div>
   </div>

   <style>
   @keyframes bounce {
     0%, 20%, 50%, 80%, 100% { transform: translateX(-50%) translateY(0); }
     40% { transform: translateX(-50%) translateY(-10px); }
     60% { transform: translateX(-50%) translateY(-5px); }
   }
   </style>
   ```

---

### 3. SECTION 2: Three.js 3D Experience

**Add Section**:
- Elementor → Add Section → Single Column
- Section Settings:
  - Height: Min Height = 600px
  - Padding: 0px (all sides)
  - Background Color: #1a1a1a (dark background for 3D scene)

**Add HTML Widget**:

**For SIGNATURE Collection**:
```html
<!-- Three.js ES Module Import Map -->
<script type="importmap">
{
  "imports": {
    "three": "<?php echo get_stylesheet_directory_uri(); ?>/assets/js/three.module.min.js",
    "three/addons/": "<?php echo get_stylesheet_directory_uri(); ?>/assets/js/addons/"
  }
}
</script>

<!-- 3D Container -->
<div id="signature-3d-container" style="width: 100%; height: 600px; position: relative;"></div>

<!-- Loading State -->
<div id="signature-loading" style="
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #fff;
  z-index: 100;
">
  <div class="spinner" style="
    width: 48px;
    height: 48px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #B76E79;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  "></div>
  <p>Loading 3D Experience...</p>
</div>

<style>
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

<!-- Load Collection Scene -->
<script type="module">
  // Scene will be loaded by functions.php enqueue
  // skyyrose_enqueue_threejs() handles loading signature.js
</script>
```

**For LOVE HURTS Collection**:
- Same structure, replace "signature" with "love-hurts"
- Loading text: "Entering the Enchanted Castle..."
- Border-top-color: #8B4789 (purple)

**For BLACK ROSE Collection**:
- Replace "signature" with "black-rose"
- Loading text: "Unveiling the Gothic Garden..."
- Border-top-color: #C0C0C0 (silver)

**Widget Settings**:
- Advanced → Custom CSS:
  ```css
  /* Responsive: Reduce height on mobile */
  @media (max-width: 768px) {
    #signature-3d-container {
      height: 400px !important;
    }
  }
  ```

---

### 4. SECTION 3: Collection Story

**Add Section**:
- Elementor → Add Section → 2 Columns (60% / 40%)
- Section Settings:
  - Content Width: Boxed (1200px max-width)
  - Padding: 80px top/bottom, 40px left/right

**Column 1 (Text - 60%)**:

1. **Heading Widget**:
   ```
   Title: "The Story Behind SIGNATURE"
   HTML Tag: H2
   Typography: Font Size 36px, Weight 700
   Color: #1a1a1a
   ```

2. **Text Editor Widget**:
   ```
   The SIGNATURE collection embodies timeless elegance through
   carefully curated pieces that blend classic silhouettes with
   modern luxury. Each item is designed to be a wardrobe staple,
   transcending trends and seasons.

   Inspired by the delicate beauty of rose gardens at golden hour,
   this collection features soft, romantic hues and premium fabrics
   that drape beautifully. From everyday essentials to statement
   pieces, SIGNATURE is your foundation for effortless style.
   ```
   - Typography: 18px, Line Height 1.8, Color #666
   - Add margin-bottom: 20px

3. **Button Widget** (Optional):
   ```
   Text: "Explore the Collection ↓"
   Link: #products-section (anchor to product grid)
   Style: Custom, Background #B76E79, Padding 15px 40px
   ```

**Column 2 (Image - 40%)**:
- Image Widget: Upload lifestyle photo or product collage
- Size: Full
- Border Radius: 12px
- Box Shadow: 0 8px 32px rgba(0,0,0,0.15)

---

### 5. SECTION 4: Product Grid

**Add Section**:
- Elementor → Add Section → Single Column
- Section Settings:
  - ID: `products-section` (for anchor link)
  - Background: #f5f5f0 (light background)
  - Padding: 60px top/bottom, 20px left/right

**Add Heading Widget**:
```
Title: "Explore the SIGNATURE Collection"
HTML Tag: H2
Text Align: Center
Typography: Font Size 42px, Weight 700
Margin Bottom: 40px
```

**Add WooCommerce Products Widget**:

**Widget Settings**:
```
Query:
  Source: Products
  Query Type: Main Query
  Filter By: Category
  Category: Select "SIGNATURE" (or respective collection)
  Products Per Page: 12
  Order By: Menu Order

Layout:
  Columns: 3 (desktop), 2 (tablet), 1 (mobile)
  Rows: 4
  Image Ratio: 1:1 (Square)

Pagination:
  Type: Numbers (or Load More button)
  Alignment: Center
```

**Custom CSS** (in Elementor → Site Settings → Custom CSS):
```css
/* Luxury product card styling */
.woocommerce ul.products li.product {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  background: #fff;
}

.woocommerce ul.products li.product:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.woocommerce ul.products li.product img {
  transition: transform 0.6s ease;
}

.woocommerce ul.products li.product:hover img {
  transform: scale(1.05);
}

/* Product card overlay */
.woocommerce ul.products li.product::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.woocommerce ul.products li.product:hover::after {
  opacity: 1;
}

/* Add to cart button - Luxury style */
.woocommerce ul.products li.product .button {
  background: var(--skyyrose-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s ease;
}

.woocommerce ul.products li.product .button:hover {
  background: #a15e69;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(183, 110, 121, 0.4);
}
```

---

### 6. SECTION 5: Call to Action

**Add Section**:
- Elementor → Add Section → Single Column
- Background: Gradient (#B76E79 → #a15e69)
- Padding: 60px top/bottom

**Column Content**:

1. **Heading Widget**:
   ```
   Title: "Stay Connected"
   Color: #ffffff
   Text Align: Center
   Typography: Font Size 36px, Weight 700
   ```

2. **Form Widget** (Elementor Pro):
   ```
   Fields:
     - Email (required, placeholder: "Enter your email")
   Button:
     Text: "Subscribe"
     Width: 250px
   Actions After Submit:
     - Mailchimp (or Email)
   Style:
     Form Fields → Background: rgba(255,255,255,0.2)
     Button → Background: #ffffff, Color: #B76E79
   ```

3. **Icon List Widget** (Trust Badges):
   ```
   Items:
     - ✓ Free Shipping on Orders $75+
     - ✓ Easy Returns & Exchanges
     - ✓ Secure Checkout
   Style:
     Text Color: #ffffff
     Icon Color: #ffffff
     Typography: 16px
   ```

---

## 🎨 Collection-Specific Customizations

### SIGNATURE Collection

**Color Palette**:
- Primary: #B76E79 (Rose Pink)
- Secondary: #d4af37 (Gold)
- Background: #f5f5f0 (Ivory)
- Text: #1a1a1a (Charcoal)

**Fonts**:
- Headings: Inter, Weight 700-800
- Body: Inter, Weight 400

**Mood**: Elegant, timeless, romantic

---

### LOVE HURTS Collection

**Color Palette**:
- Primary: #8B4789 (Deep Purple)
- Secondary: #C71585 (Crimson)
- Background: #2a1a2e (Dark Purple)
- Text: #ffffff (White)

**Fonts**:
- Headings: Playfair Display or Cormorant (serif)
- Body: Inter, Weight 400

**Mood**: Dramatic, gothic romance, Beauty and the Beast

**Additional Elements**:
- Add CSS animation for candle flicker effect
- Use purple/gold gradient overlays
- Include stained glass imagery

---

### BLACK ROSE Collection

**Color Palette**:
- Primary: #C0C0C0 (Silver)
- Secondary: #000000 (Pure Black)
- Background: #0a0a0a (Near Black)
- Text: #ffffff (White)

**Fonts**:
- Headings: Montserrat, Weight 700
- Body: Inter, Weight 300 (Light)

**Mood**: Dark luxury, mysterious, gothic elegance

**Additional Elements**:
- Night sky gradient backgrounds
- Silver metallic accents (CSS shimmer)
- Fog/mist effects (CSS blur)

---

## 📱 Mobile Responsive Settings

### Breakpoints (Elementor)
- **Desktop**: 1025px+
- **Tablet**: 768px - 1024px
- **Mobile**: < 768px

### Mobile-Specific Adjustments

**Hero Section**:
- Height: 70vh (instead of 100vh)
- Font Size: H1 = 36px, Tagline = 18px
- Padding: 20px left/right

**Three.js Container**:
- Height: 400px (instead of 600px)
- Disable post-processing effects for performance
- Simpler particle count (500 instead of 2000)

**Product Grid**:
- Columns: 1 (full-width cards)
- Larger tap targets for buttons (min 48x48px)
- Remove hover effects (use :active instead)

**Navigation**:
- Sticky header on scroll
- Hamburger menu (Elementor Mobile Menu widget)

---

## 🔧 Advanced Features

### 1. Sticky Add to Cart (Shoptimizer Feature)

**Activate**: Shoptimizer → Product Pages → Enable Sticky Add to Cart

**Works automatically** on single product pages when scrolling past main image

---

### 2. Quick View Modal

**Plugin**: [YITH WooCommerce Quick View](https://wordpress.org/plugins/yith-woocommerce-quick-view/)

**Settings**:
- Modal Style: Glassmorphism (match child theme CSS)
- Background Blur: 10px
- Border Radius: 12px

---

### 3. Product Filters (Sidebar or Top Bar)

**Plugin**: [Product Filter by WooBeWoo](https://wordpress.org/plugins/woo-product-filter/)

**Filters to Enable**:
- Size (XS, S, M, L, XL, XXL)
- Color (Visual swatches)
- Price Range (Slider)
- In Stock Only (Toggle)

**Placement**: Above product grid in SECTION 4

---

### 4. Countdown Timer (FOMO)

**Plugin**: [Sales Countdown Timer](https://wordpress.org/plugins/woo-smart-compare/)

**Use Cases**:
- Limited edition products
- Flash sales
- Seasonal collections

**Style**: Match brand colors, integrate with product cards

---

### 5. Wishlist Functionality

**Plugin**: [YITH WooCommerce Wishlist](https://wordpress.org/plugins/yith-woocommerce-wishlist/)

**Icon**: Heart (outline when not saved, filled when saved)
**Position**: Top-right corner of product card

---

## 📊 SEO Optimization

### Page Title & Meta Description

**SIGNATURE Collection**:
```
Title: SIGNATURE Collection | Timeless Luxury Fashion | SkyyRose
Meta Description: Discover the SIGNATURE collection - elegant essentials and wardrobe staples crafted with premium materials. Shop rose-inspired luxury fashion at SkyyRose.
```

**LOVE HURTS Collection**:
```
Title: LOVE HURTS Collection | Gothic Romance Fashion | SkyyRose
Meta Description: Enter the enchanted world of LOVE HURTS - dramatic gothic fashion with Beauty and the Beast aesthetics. Explore limited edition luxury pieces at SkyyRose.
```

**BLACK ROSE Collection**:
```
Title: BLACK ROSE Collection | Dark Luxury Fashion | SkyyRose
Meta Description: Unveil the mystery of BLACK ROSE - dark luxury fashion with silver accents and gothic elegance. Shop exclusive designs at SkyyRose.
```

### Structured Data (Schema.org)

**Already implemented** in Next.js pages, replicate in WordPress using:

**Plugin**: Rank Math SEO → Schema → Collection Page

**Schema Type**: CollectionPage
**Properties**:
- Name: "SIGNATURE Collection"
- Description: (copy from meta)
- URL: https://skyyrose.com/collections/signature
- Brand: SkyyRose
- numberOfItems: (dynamic, from WooCommerce)

---

## ✅ Testing Checklist

Before publishing, verify:

- [ ] Hero section displays correctly (100vh, centered text)
- [ ] Three.js scene loads without errors (check browser console)
- [ ] Scroll indicator animates smoothly
- [ ] Collection story text is readable (contrast ratio ≥ 4.5:1)
- [ ] Product grid displays 3 columns (desktop), responsive on mobile
- [ ] Add to cart buttons work (test with real product)
- [ ] Newsletter form submits successfully
- [ ] Trust badges display in footer section
- [ ] Mobile: All elements stack vertically, no horizontal scroll
- [ ] Mobile: Three.js scene height reduced to 400px
- [ ] Lighthouse Performance score ≥ 90
- [ ] Accessibility score = 100 (alt text, ARIA labels)
- [ ] No console errors or 404s

---

## 🚀 Deployment Steps

### 1. Save as Template

**Elementor → Templates → Saved Templates → Save**

**Template Name**: "Collection Page - SIGNATURE" (or respective collection)
**Type**: Page

**Export**: Download JSON file for backup

---

### 2. Duplicate for Other Collections

**Pages → All Pages → Hover over SIGNATURE → Duplicate**

**Rename**: "LOVE HURTS Collection"
**Permalink**: `/collections/love-hurts/`

**Edit with Elementor**:
- Section 1: Change title to "LOVE HURTS"
- Section 1: Update background gradient (pink → purple)
- Section 2: Replace HTML widget with `love-hurts-3d-container`
- Section 3: Update story text
- Section 4: WooCommerce Products → Filter by "Love Hurts" category

**Repeat** for BLACK ROSE collection

---

### 3. Set as Homepage (Optional)

**Settings → Reading → Homepage displays: A static page**
**Select**: Custom "Homepage" (create separate page with featured collections)

---

### 4. Menu Integration

**Appearance → Menus → Create "Shop Menu"**

```
Collections (Mega Menu)
├── SIGNATURE
├── LOVE HURTS
└── BLACK ROSE
```

**Elementor Pro**: Use Mega Menu widget for dropdown with images

---

## 📚 Resources

### Elementor Documentation
- [Elementor Page Builder](https://elementor.com/help/)
- [Elementor Pro Features](https://elementor.com/pro/)
- [WooCommerce Integration](https://elementor.com/help/woocommerce-widgets/)

### Inspiration
- [Dior Official Site](https://www.dior.com/) - Luxury fashion UX
- [Chanel](https://www.chanel.com/) - Minimalist elegance
- [Gucci](https://www.gucci.com/) - Bold interactive design

### Tools
- [Elementor Template Kits](https://library.elementor.com/) - Pre-made sections
- [WooCommerce Product Blocks](https://woocommerce.com/document/woocommerce-blocks/)
- [Schema Markup Generator](https://technicalseo.com/tools/schema-markup-generator/)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-11
**Next Steps**: Implement first collection page (SIGNATURE), test thoroughly, then duplicate
**Contact**: For questions about Elementor setup, refer to WORDPRESS_ENHANCEMENTS.md
