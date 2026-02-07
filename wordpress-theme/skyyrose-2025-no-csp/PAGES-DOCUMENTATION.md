# SkyyRose Theme - Pages Documentation

> Complete reference for all static and interactive pages in the SkyyRose 2025 WordPress theme

## Table of Contents

- [Static Pages](#static-pages)
- [Interactive Pages](#interactive-pages)
- [Template Parts](#template-parts)
- [WooCommerce Templates](#woocommerce-templates)
- [Elementor Widgets](#elementor-widgets)

---

## Static Pages

### 1. Home Page (`template-home.php`)
**Template:** Home Page Template
**Purpose:** Main landing page for SkyyRose luxury fashion brand
**Features:**
- Hero section with brand messaging
- Featured collections showcase
- Product highlights
- Newsletter signup
- Brand story introduction

**Usage:** Assign to homepage in Settings → Reading

---

### 2. About Page (`page-about.php`)
**Template:** About Page Template
**Purpose:** Brand story and heritage showcase
**Features:**
- Brand history timeline
- Designer profile
- Craftsmanship showcase
- Mission & values
- Awards & recognition

**Usage:** Create page → Select "About Page" template

---

### 3. Contact Page (`page-contact.php`)
**Template:** Contact Page Template
**Purpose:** Customer communication hub
**Features:**
- Contact form with validation
- Store locations map
- Business hours
- Social media links
- Customer service information

**Usage:** Create page → Select "Contact Page" template

---

### 4. Default Page (`page.php`)
**Template:** Default Page Template
**Purpose:** Fallback for standard pages
**Features:**
- Standard content layout
- Sidebar support
- Breadcrumb navigation
- Social sharing buttons

**Usage:** Default template for all pages

---

## Interactive Pages

### 1. Immersive Collection Experience (`template-collection.php`)
**Template:** Collection Template
**Purpose:** Interactive 3D storytelling experience for each collection (NOT a product catalog)
**Type:** IMMERSIVE EXPERIENCE (exploration, not shopping)

**Features:**
- **Collection-Specific 3D Scenes:**
  - BLACK ROSE: Gothic cathedral with falling rose petals, dark ambient lighting
  - LOVE HURTS: Romantic castle with heart particles, warm glow, multiple rooms
  - SIGNATURE: Oakland/San Francisco cityscape tour, golden hour lighting

- **Interactive Elements:**
  - Three.js 3D environments
  - GSAP scroll-triggered animations
  - Particle effects (rose petals, hearts, light rays)
  - Camera movement on scroll/navigation
  - Product hotspots in 3D space (clickable to product pages)
  - Spatial audio (optional)
  - Navigation controls (WASD, mouse)

- **Technical Stack:**
  - React Three Fiber
  - Babylon.js (physics)
  - Framer Motion
  - GSAP ScrollTrigger
  - Custom luxury transitions

**Usage:**
1. Create page → Select "Collection" template
2. Set `_collection_type` meta: `black-rose`, `love-hurts`, or `signature`
3. Users explore the scene, click hotspots to view products

**Key Difference from Catalog Pages:**
- ❌ NOT a product grid
- ❌ NOT for browsing all products
- ✅ Immersive brand storytelling
- ✅ Product discovery through exploration
- ✅ Emotional connection to collection theme

**Brand Colors:**
- Black Rose: `#8B0000` (dark red)
- Love Hurts: `#B76E79` (rose gold)
- Signature: `#D4AF37` (golden)

---

### 2. Collection Product Catalogs (NEW - 3 Dedicated Pages)
**Templates:**
- `page-collection-black-rose.php`
- `page-collection-love-hurts.php`
- `page-collection-signature.php`

**Purpose:** Full product catalog display for each collection (SHOPPING EXPERIENCE)
**Type:** PRODUCT CATALOG (browse, filter, add to cart)

**Features:**
- **Full Product Grid:** All products in collection displayed at once
- **Category Filtering:** Filter by product type (dresses, coats, etc.)
- **Product Count:** Live count of visible products
- **Quick Add to Cart:** Direct add-to-cart from grid
- **Product Cards:**
  - Product image (or emoji placeholder)
  - Product title
  - Price (WooCommerce formatted)
  - Badge (New, Pre-Order, Limited, etc.)
  - Add to Cart button

- **Filtering System:**
  - Client-side JavaScript filtering (instant)
  - Category buttons (All, Dresses, Coats, Blazers, etc.)
  - Product count updates dynamically
  - Hover effects with collection colors

**Usage:**
1. Create 3 pages:
   - "Black Rose Collection" → Template: Collection - Black Rose
   - "Love Hurts Collection" → Template: Collection - Love Hurts
   - "Signature Collection" → Template: Collection - Signature
2. Products must have `_skyyrose_collection` meta field set
3. Add to menu: Shop → [Collection Name]

**Key Difference from Immersive Pages:**
- ✅ Product grid layout (not 3D scene)
- ✅ Filter by category
- ✅ Add to cart directly
- ✅ SEO-optimized URLs (`/collection-black-rose`, `/collection-love-hurts`, `/collection-signature`)
- ❌ No 3D navigation
- ❌ No immersive storytelling

**Page URLs:**
- Black Rose Catalog: `/collection-black-rose/`
- Love Hurts Catalog: `/collection-love-hurts/`
- Signature Catalog: `/collection-signature/`

**WooCommerce Integration:**
```php
// Query products by collection meta
$args = [
    'post_type' => 'product',
    'posts_per_page' => -1,
    'meta_query' => [
        [
            'key' => '_skyyrose_collection',
            'value' => 'black-rose', // or 'love-hurts', 'signature'
            'compare' => '='
        ]
    ]
];
```

---

### 3. Immersive Experience (`template-immersive.php`)
**Template:** Immersive Template
**Purpose:** Full-screen immersive brand experiences
**Features:**
- Full viewport 3D scenes
- WebGL shader effects
- Audio integration (optional)
- Gesture controls (swipe, pinch)
- Loading animations with brand logo
- Progress indicators

**Interactive Elements:**
- 360° product views
- Virtual showroom navigation
- Parallax scrolling effects
- Interactive storytelling

**Usage:** Create page → Select "Immersive" template → Configure scene in Elementor

**Performance:**
- Lazy loading for 3D models
- Progressive enhancement
- Mobile-optimized
- Core Web Vitals compliant

---

### 4. Vault (VIP Access) (`template-vault.php`)
**Template:** Vault Template
**Purpose:** Exclusive content for VIP customers
**Features:**
- Authentication required
- Early access to collections
- Limited edition products
- VIP-only offers
- Private sale events

**Access Control:**
- User role: `skyyrose_vip`
- Login redirect to vault
- Session timeout: 30 minutes
- Secure nonce validation

**Usage:** Create page → Select "Vault" template → Restricted to logged-in VIP users

---

## Template Parts

### Content Template (`template-parts/content.php`)
**Purpose:** Reusable content block for posts/pages
**Features:**
- Post thumbnail
- Excerpt with read more
- Post meta (date, author, categories)
- Social sharing
- Comment count

**Used In:** index.php, archive.php, single.php

---

## WooCommerce Templates

### 1. Shop Archive (`woocommerce.php`)
**Purpose:** Main shop page and product archives
**Features:**
- Product grid/list view toggle
- Filter sidebar (price, color, size, collection)
- Sort options (price, popularity, newest)
- Pagination
- Quick view modal
- Add to cart AJAX

**Hooks:**
- `woocommerce_before_main_content`
- `woocommerce_after_main_content`
- Custom breadcrumbs

---

### 2. Single Product (`single-product.php`)
**Purpose:** Individual product detail page
**Features:**
- **3D Product Viewer:**
  - 360° rotation
  - Zoom functionality
  - Material close-ups
  - Color variations

- **Product Information:**
  - Title, price, SKU
  - Size guide modal
  - Material composition
  - Care instructions
  - Shipping information

- **Interactive Elements:**
  - Image gallery with Swiper
  - Pre-order button (if applicable)
  - Wishlist toggle
  - Social sharing

**Custom Fields:**
- `_skyyrose_3d_model_url` (GLB file)
- `_skyyrose_collection` (Black Rose, Love Hurts, Signature)
- `_skyyrose_designer_note` (text)
- `_skyyrose_preorder` (boolean)

---

### 3. Cart (`woocommerce/cart/cart.php`)
**Purpose:** Shopping cart review
**Features:**
- Product thumbnails
- Quantity adjustment
- Remove items
- Coupon code entry
- Shipping calculator
- Subtotal, tax, total
- Continue shopping link
- Proceed to checkout button

**AJAX:**
- Update quantities
- Apply coupon
- Remove item
- Real-time total updates

---

### 4. Checkout (`woocommerce/checkout/form-checkout.php`)
**Purpose:** Order completion
**Features:**
- Billing/shipping forms
- Payment method selection
- Order review
- Terms & conditions
- Guest checkout option
- Saved addresses (logged-in)

**Payment Gateways:**
- Credit/debit cards
- PayPal
- Apple Pay
- Google Pay

**Security:**
- CSRF nonce validation
- SSL required
- PCI compliance
- Rate limiting

---

### 5. My Account (`woocommerce/myaccount/my-account.php`)
**Purpose:** Customer dashboard
**Features:**
- Order history
- Downloads (digital products)
- Addresses (billing/shipping)
- Account details
- Logout

**Endpoints:**
- `/my-account/orders/`
- `/my-account/downloads/`
- `/my-account/edit-address/`
- `/my-account/edit-account/`

---

## Elementor Widgets

### 1. Immersive Scene Widget (`elementor-widgets/immersive-scene.php`)
**Category:** SkyyRose Luxury
**Purpose:** Embed 3D scenes in Elementor pages
**Controls:**
- Scene type (Gothic, Romantic, Urban)
- Camera speed
- Particle density
- Ambient color
- Enable/disable audio

**Preview:** Live preview in Elementor editor

---

### 2. Product Hotspot Widget (`elementor-widgets/product-hotspot.php`)
**Category:** SkyyRose Luxury
**Purpose:** Interactive product markers in 3D space
**Controls:**
- Product ID
- 3D position (X, Y, Z)
- Hotspot icon
- Popup content
- Animation trigger (click, hover)

**Use Case:** Mark products within immersive scenes

---

### 3. Collection Card Widget (`elementor-widgets/collection-card.php`)
**Category:** SkyyRose Luxury
**Purpose:** Animated collection preview cards
**Controls:**
- Collection name
- Featured image
- Hover animation style
- Card layout (horizontal, vertical)
- CTA button text/link

**Animations:**
- Parallax on scroll
- 3D tilt on hover
- Gradient overlay
- Fade-in transitions

---

### 4. Pre-Order Form Widget (`elementor-widgets/pre-order-form.php`)
**Category:** SkyyRose Luxury
**Purpose:** Accept pre-orders for upcoming products
**Controls:**
- Product ID
- Launch date countdown
- Deposit amount
- Form fields (name, email, size)
- Success message

**Features:**
- Email notifications
- Order reservation
- Payment integration
- Waitlist management

**Security:**
- Nonce validation
- Rate limiting (5 attempts per IP)
- Email verification
- GDPR compliant

---

## File Structure

```
skyyrose-2025/
├── functions.php              # Theme initialization, enqueues, custom functions
├── index.php                  # Default template (posts archive)
├── archive.php                # Category/tag archives
├── single.php                 # Single post
├── page.php                   # Default page template
├── header.php                 # Site header
├── footer.php                 # Site footer
├── footer-backup.php          # Backup footer (unused, can delete)
│
├── template-home.php                 # Home page template
├── page-about.php                    # About page template
├── page-contact.php                  # Contact page template
├── template-collection.php           # Immersive 3D collection experience (interactive)
├── page-collection-black-rose.php    # Black Rose product catalog (shopping)
├── page-collection-love-hurts.php    # Love Hurts product catalog (shopping)
├── page-collection-signature.php     # Signature product catalog (shopping)
├── template-immersive.php            # Immersive experience (interactive)
├── template-vault.php                # VIP vault (restricted)
│
├── woocommerce.php            # WooCommerce archive
├── single-product.php         # Product detail page
│
├── woocommerce/
│   ├── cart/
│   │   └── cart.php           # Shopping cart
│   ├── checkout/
│   │   └── form-checkout.php  # Checkout form
│   └── myaccount/
│       └── my-account.php     # Customer account
│
├── template-parts/
│   └── content.php            # Reusable content block
│
├── elementor-widgets/
│   ├── immersive-scene.php    # 3D scene widget
│   ├── product-hotspot.php    # Product marker widget
│   ├── collection-card.php    # Collection card widget
│   └── pre-order-form.php     # Pre-order form widget
│
├── inc/
│   ├── security-hardening.php      # OWASP security, rate limiting, encryption
│   ├── theme-customizer.php        # WordPress Customizer settings
│   ├── woocommerce-config.php      # WooCommerce customizations
│   ├── performance.php             # Caching, lazy loading, optimization
│   ├── performance-optimizations.php # Additional performance tweaks
│   ├── ai-image-enhancement.php    # AI image processing (FLUX, SD3, RemBG)
│   ├── pre-order-functions.php     # Pre-order system logic
│   └── elementor-widgets.php       # Widget registration
│
└── admin/
    └── ai-enhancement-settings.php # Admin panel for AI settings
```

---

## Navigation Structure Recommendation

### Recommended Menu Structure
```
Home
Shop
├── All Products (WooCommerce shop page)
├── Collections (submenu)
│   ├── Black Rose Catalog (/collection-black-rose)
│   ├── Love Hurts Catalog (/collection-love-hurts)
│   └── Signature Catalog (/collection-signature)
Experience (submenu)
├── Black Rose Immersive (/black-rose-experience)
├── Love Hurts Immersive (/love-hurts-experience)
└── Signature Immersive (/signature-experience)
About
Contact
VIP Vault (logged-in only)
```

### User Journey

**Discovery Flow:**
1. User visits "Black Rose Immersive" → Explores 3D gothic cathedral
2. Clicks product hotspot in scene → Redirects to single product page
3. OR clicks "View Full Collection" CTA → Goes to "Black Rose Catalog"
4. Browses grid, filters by category, adds to cart

**Shopping Flow:**
1. User visits "Love Hurts Catalog" → Sees all Love Hurts products
2. Filters by "Dresses" → Grid updates to show only dresses
3. Clicks product card → Goes to single product page
4. Adds to cart, continues shopping

**Key Insight:**
- Immersive pages = **Emotional engagement** (explore brand story)
- Catalog pages = **Transactional** (find product, buy now)
- Both needed for complete luxury e-commerce experience

---

## Page Assignment Guide

### Homepage Setup
1. Go to **Settings → Reading**
2. Select "A static page"
3. Homepage: Select page with "Home Page" template
4. Posts page: Create "Blog" page

### Immersive Collection Pages (3D Experiences)
1. Create page: "Black Rose Experience"
2. Template: Collection
3. Page meta: `_collection_type = black-rose`
4. Featured image: Gothic cathedral scene preview
5. Publish

Repeat for:
- "Love Hurts Experience" (`_collection_type = love-hurts`)
- "Signature Experience" (`_collection_type = signature`)

### Catalog Collection Pages (Product Grids)
1. Create page: "Black Rose Collection"
2. Template: Collection - Black Rose
3. Slug: `collection-black-rose`
4. Featured image: Collection banner
5. Publish

Repeat for:
- "Love Hurts Collection" (Template: Collection - Love Hurts, Slug: `collection-love-hurts`)
- "Signature Collection" (Template: Collection - Signature, Slug: `collection-signature`)

### Immersive Experience
1. Create page: "Experience SkyyRose"
2. Template: Immersive
3. Edit with Elementor
4. Add Immersive Scene Widget
5. Configure scene type and settings

### Vault Setup
1. Create page: "VIP Vault"
2. Template: Vault
3. Set as private
4. Add to menu (conditional: logged-in only)

---

## Interactive Features

### 3D Product Viewer
- **Trigger:** Product page load
- **Library:** React Three Fiber
- **Model Format:** GLB (optimized)
- **Controls:** Orbit, zoom, pan
- **Performance:** Lazy load, LOD (Level of Detail)

### GSAP Animations
- **Scroll Triggers:** Collection reveals, product fade-ins
- **Timelines:** Hero sequences, CTA pulses
- **Performance:** GPU-accelerated, requestAnimationFrame

### Framer Motion
- **Page Transitions:** Fade, slide, scale
- **Component Animations:** Hover states, click feedback
- **Variants:** Defined in `/assets/js/animations/variants.js`

---

## SEO & Performance

### Core Web Vitals
- **LCP (Largest Contentful Paint):** < 2.5s
  - Hero images: WebP with AVIF fallback
  - Lazy loading below fold
  - CDN delivery (jsDelivr)

- **FID (First Input Delay):** < 100ms
  - Defer non-critical JS
  - Code splitting
  - Service worker caching

- **CLS (Cumulative Layout Shift):** < 0.1
  - Reserved space for images
  - Font display: swap
  - No layout-shifting ads

### Security Headers
- Content-Security-Policy
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- Strict-Transport-Security

---

## Brand Guidelines

### Typography
- **Headings:** Playfair Display (serif, elegant)
- **Body:** Inter (sans-serif, readable)
- **Accents:** Cormorant Garamond (luxury feel)

### Color Palette
```css
--black-rose: #8B0000;      /* Dark red, gothic */
--love-hurts: #B76E79;      /* Rose gold, romantic */
--signature: #D4AF37;       /* Gold, luxury */
--black: #000000;           /* Pure black */
--white: #FFFFFF;           /* Pure white */
--gray-light: #F5F5F5;      /* Backgrounds */
--gray-dark: #333333;       /* Text */
```

### Voice & Tone
- **Luxury:** Sophisticated, not pretentious
- **Emotional:** Romantic, passionate
- **Confident:** Bold, unapologetic
- **Inclusive:** Welcoming, not exclusive

---

## Testing Checklist

### Before Launch
- [ ] All pages render correctly
- [ ] Interactive elements functional
- [ ] 3D models load on all devices
- [ ] Forms submit successfully
- [ ] WooCommerce checkout works
- [ ] Mobile responsive (320px - 2560px)
- [ ] Cross-browser (Chrome, Safari, Firefox, Edge)
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Performance (Lighthouse score > 90)
- [ ] Security headers active
- [ ] SSL certificate valid

### Post-Launch Monitoring
- [ ] Google Analytics tracking
- [ ] Error logs (404s, PHP errors)
- [ ] Conversion rate optimization
- [ ] User feedback collection

---

## Support & Maintenance

### Contact
- **Developer:** SkyyRose Development Team
- **Email:** dev@skyyrose.co
- **Documentation:** https://docs.skyyrose.co

### Updates
- **WordPress:** Monthly security updates
- **Theme:** Quarterly feature releases
- **Plugins:** As needed (security patches)

### Backup Schedule
- **Daily:** Database snapshots
- **Weekly:** Full site backup
- **Monthly:** Off-site archive

---

**Last Updated:** 2026-02-04
**Theme Version:** 3.0.0
**WordPress:** 6.4+
**WooCommerce:** 8.5+
**Elementor:** 3.18+
