# WordPress Three.js Integration Testing Plan

> **Comprehensive testing checklist for SkyyRose WordPress site**
>
> **Created**: 2026-01-11
> **Target**: Production deployment readiness
> **Testing Environment**: Local WordPress + Staging + Production

---

## 🎯 Testing Objectives

1. **Functionality**: All Three.js scenes load and function correctly
2. **Performance**: Page load < 3s, Lighthouse score ≥ 90
3. **Compatibility**: Works on Chrome, Safari, Firefox, Edge (desktop + mobile)
4. **Accessibility**: WCAG 2.1 AA compliance
5. **SEO**: Schema.org markup, meta tags, Core Web Vitals passing

---

## ✅ Pre-Deployment Checklist

### Theme Installation
- [ ] Shoptimizer parent theme uploaded to `/wp-content/themes/shoptimizer/`
- [ ] Shoptimizer child theme uploaded to `/wp-content/themes/shoptimizer-child-theme/`
- [ ] Child theme activated (Appearance → Themes → Activate "Shoptimizer Child")
- [ ] Child theme `style.css` loaded (check page source for `<link>`)
- [ ] Child theme `functions.php` executing (check for Three.js enqueues)

### Three.js Files
- [ ] `three.module.min.js` (620KB) in `/assets/js/`
- [ ] `signature.js` in `/assets/js/collections/`
- [ ] `love-hurts.js` in `/assets/js/collections/`
- [ ] `black-rose.js` in `/assets/js/collections/`
- [ ] All files are valid UTF-8 encoding (no BOM, no null bytes)

### WordPress Configuration
- [ ] Permalink structure: Post name (Settings → Permalinks)
- [ ] WooCommerce installed and activated
- [ ] Product categories created: "signature", "love-hurts", "black-rose"
- [ ] Elementor Pro installed and activated
- [ ] PHP version ≥ 7.4 (8.0+ recommended)
- [ ] MySQL version ≥ 5.7
- [ ] WordPress version ≥ 6.0

---

## 🧪 JavaScript Syntax Validation

### Manual Testing (Browser Console)

**Test 1: Load Three.js Core**

1. Create test page: `/test-threejs/`
2. Add HTML widget:
   ```html
   <script type="importmap">
   {
     "imports": {
       "three": "<?php echo get_stylesheet_directory_uri(); ?>/assets/js/three.module.min.js"
     }
   }
   </script>

   <script type="module">
   import * as THREE from 'three';
   console.log('Three.js version:', THREE.REVISION);
   console.log('Three.js loaded successfully!');
   </script>
   ```
3. Expected console output: `Three.js version: 152` and `Three.js loaded successfully!`

**Test 2: Load SIGNATURE Scene**

1. Navigate to `/collections/signature/`
2. Open browser console (F12)
3. Check for errors:
   - ✅ No errors: Scene loaded
   - ❌ `404 Not Found`: File path incorrect
   - ❌ `Uncaught SyntaxError`: JavaScript syntax error
   - ❌ `Uncaught ReferenceError`: Missing variable/function

**Expected Console Output**:
```
Three.js loaded
SIGNATURE scene initialized
Camera position: (0, 5, 15)
Renderer initialized: WebGLRenderer
```

**Repeat for**:
- LOVE HURTS collection: `/collections/love-hurts/`
- BLACK ROSE collection: `/collections/black-rose/`

---

### Automated Syntax Check (ESLint)

**Install ESLint** (if not already):
```bash
npm install -g eslint
```

**Validate JavaScript Files**:
```bash
cd /Users/coreyfoster/DevSkyy/wordpress/shoptimizer-child-theme/assets/js/collections

# Check syntax only (no style rules)
eslint signature.js --no-eslintrc --parser-options=ecmaVersion:2022,sourceType:module
eslint love-hurts.js --no-eslintrc --parser-options=ecmaVersion:2022,sourceType:module
eslint black-rose.js --no-eslintrc --parser-options=ecmaVersion:2022,sourceType:module
```

**Expected Output**: `0 errors, 0 warnings` (or specific linting suggestions)

---

## 🎨 Visual Regression Testing

### SIGNATURE Collection

**Scene Elements to Verify**:
- [ ] Rose garden floor (green grass texture)
- [ ] Fountain in center (water particles)
- [ ] Product pedestals (white marble, 5 total)
- [ ] Falling rose petals (pink particles)
- [ ] Brand logo (3D text "SkyyRose")
- [ ] Pathways (beige cobblestones)
- [ ] Ambient lighting (warm golden hour)
- [ ] Camera orbit controls (mouse drag works)

**Interaction Tests**:
1. Click on pedestal → Opens WooCommerce product page
2. Mouse wheel → Zooms in/out smoothly
3. Right-click drag → Pans camera (no context menu)
4. Double-click → Resets camera position

---

### LOVE HURTS Collection

**Scene Elements to Verify**:
- [ ] Enchanted rose under glass dome (CENTER STAGE - most important!)
- [ ] Castle ballroom floor (marble with embossed patterns)
- [ ] Candelabras (flickering flame effect)
- [ ] Stained glass windows (colored light projection)
- [ ] Magic particles (purple/blue/gold mix, 2000+ count)
- [ ] Castle mirrors (ornate gold frames, 4 total)
- [ ] Floor spotlights (product illumination)
- [ ] Ambient candlelight (warm orange glow)

**Enchanted Rose Verification** (CRITICAL):
- [ ] Rose bloom is crimson red with emissive glow
- [ ] Rose has 8 petals arranged in circle
- [ ] Rose gold center sphere is visible
- [ ] Glass dome is transparent (opacity ~15%)
- [ ] Dome has subtle rainbow refraction
- [ ] Pedestal is dark metallic (bronze/iron)
- [ ] Rose rotates slowly (0.1 rad/s)
- [ ] Hero interaction: Click rose → Opens main product

**Interaction Tests**:
1. Click enchanted rose → Opens hero product page
2. Click mirror → Opens product lookbook modal
3. Click floor spotlight → Opens product quick-view

---

### BLACK ROSE Collection

**Scene Elements to Verify**:
- [ ] Night sky (gradient from pure black to dark blue)
- [ ] Twinkling stars (point sprites)
- [ ] Moon (crescent or full, glowing)
- [ ] Cloud sprites (moving slowly)
- [ ] Gothic rose garden (dark obsidian pathways)
- [ ] Silver petals (floating, metallic sheen)
- [ ] Interactive rose bushes (5 total)
- [ ] Fog effect (ground-level mist)
- [ ] Silver moonlight (directional light)

**Interaction Tests**:
1. Click rose bush → Opens product page
2. Hover rose bush → Thorns glow red
3. Find easter egg (hidden black rose) → Exclusive product reveal

---

## 📊 Performance Testing

### Lighthouse Audit

**Run Lighthouse** (Chrome DevTools):
1. Open collection page: `/collections/signature/`
2. DevTools (F12) → Lighthouse tab
3. Mode: Navigation
4. Categories: Performance, Accessibility, Best Practices, SEO
5. Device: Desktop + Mobile (test both)

**Target Scores**:
| Metric | Desktop | Mobile |
|--------|---------|--------|
| Performance | ≥ 90 | ≥ 80 |
| Accessibility | 100 | 100 |
| Best Practices | 95+ | 95+ |
| SEO | 100 | 100 |

**Core Web Vitals**:
- **LCP** (Largest Contentful Paint): < 2.5s
- **INP** (Interaction to Next Paint): < 200ms
- **CLS** (Cumulative Layout Shift): < 0.1

**If Scores are Low**:
- LCP slow → Optimize images (WebP, lazy load), reduce Three.js particle count
- INP high → Reduce JavaScript execution time, defer non-critical scripts
- CLS failing → Add `width`/`height` attributes to images, reserve space for Three.js canvas

---

### WebPageTest (Advanced)

**URL**: [https://www.webpagetest.org/](https://www.webpagetest.org/)

**Test Configuration**:
- URL: `https://skyyrose.com/collections/signature/`
- Location: Dulles, VA (or nearest to your server)
- Browser: Chrome
- Connection: Cable (5 Mbps)
- Runs: 3 (median result)

**Metrics to Check**:
- **Start Render**: < 1.5s (when page becomes visible)
- **Speed Index**: < 3.0s (how quickly content populates)
- **Time to Interactive**: < 4.0s (page fully responsive)
- **Total Page Size**: < 2 MB (including Three.js library)
- **Number of Requests**: < 50 (combine/minify assets)

---

## 🌐 Cross-Browser Compatibility

### Desktop Browsers

| Browser | Version | Test URL | Expected Result |
|---------|---------|----------|-----------------|
| Chrome | Latest (120+) | /collections/signature/ | ✅ Full support |
| Firefox | Latest (121+) | /collections/love-hurts/ | ✅ Full support |
| Safari | Latest (17+) | /collections/black-rose/ | ✅ Full support |
| Edge | Latest (120+) | /collections/signature/ | ✅ Full support |

**Test Cases**:
1. Three.js scene renders correctly
2. WebGL supported (check `renderer.capabilities.isWebGL2`)
3. ES modules imported successfully
4. Orbit controls responsive
5. No console errors

---

### Mobile Devices

| Device | OS | Browser | Resolution | Test |
|--------|-----|---------|-----------|------|
| iPhone 14 Pro | iOS 17 | Safari | 393×852 | All collections |
| iPhone SE | iOS 16 | Safari | 375×667 | All collections |
| Samsung Galaxy S23 | Android 14 | Chrome | 360×800 | All collections |
| iPad Pro | iOS 17 | Safari | 1024×1366 | All collections |

**Mobile-Specific Tests**:
- [ ] Three.js scene height reduced to 400px
- [ ] Touch controls work (pinch to zoom, swipe to rotate)
- [ ] Particle count reduced for performance (500 vs 2000)
- [ ] No horizontal scrolling
- [ ] Buttons are tap-friendly (min 48×48px)
- [ ] Page loads in < 5s on 3G connection

---

## ♿ Accessibility Testing

### WCAG 2.1 AA Compliance

**Automated Tools**:
1. **Lighthouse Accessibility** (Chrome DevTools)
2. **axe DevTools** (Browser extension)
3. **WAVE** (Web Accessibility Evaluation Tool)

**Manual Checks**:

**1. Keyboard Navigation**:
- [ ] Tab through all interactive elements (buttons, links, form fields)
- [ ] Focus indicators visible (`:focus` outline)
- [ ] No keyboard traps (can Tab out of modals)
- [ ] Escape key closes modals
- [ ] Enter/Space activates buttons

**2. Screen Reader Testing** (VoiceOver on Mac, NVDA on Windows):
- [ ] All images have meaningful alt text
- [ ] ARIA labels on Three.js canvas: `aria-label="Interactive 3D collection experience"`
- [ ] Product names announced correctly
- [ ] Form fields labeled properly
- [ ] Live regions for cart updates: `aria-live="polite"`

**3. Color Contrast**:
- [ ] Text on background ≥ 4.5:1 (normal text)
- [ ] Large text (18pt+) ≥ 3:1
- [ ] Interactive elements ≥ 3:1
- [ ] Tool: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

**4. Alternative Content**:
- [ ] Provide static product images for users who can't view Three.js
- [ ] Include text description of 3D scene
- [ ] Ensure site usable with JavaScript disabled (graceful degradation)

---

## 🔍 SEO Verification

### Schema.org Markup

**Tool**: [Google Rich Results Test](https://search.google.com/test/rich-results)

**Test URLs**:
- https://skyyrose.com/collections/signature/
- https://skyyrose.com/collections/love-hurts/
- https://skyyrose.com/collections/black-rose/

**Expected Schema Types**:
- `CollectionPage` (main schema)
- `BreadcrumbList` (navigation breadcrumbs)
- `Product` (for products in grid)
- `Brand` (SkyyRose)

**Validation**:
```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "SIGNATURE Collection",
  "description": "Timeless elegance meets modern luxury...",
  "url": "https://skyyrose.com/collections/signature",
  "brand": {
    "@type": "Brand",
    "name": "SkyyRose"
  },
  "numberOfItems": 12
}
```

---

### Meta Tags

**Verify in Page Source** (`<head>` section):

```html
<!-- Title -->
<title>SIGNATURE Collection | Timeless Luxury Fashion | SkyyRose</title>

<!-- Meta Description -->
<meta name="description" content="Discover the SIGNATURE collection - elegant essentials and wardrobe staples crafted with premium materials...">

<!-- Open Graph (Facebook/Social) -->
<meta property="og:title" content="SIGNATURE Collection | SkyyRose">
<meta property="og:description" content="Timeless elegance meets modern luxury...">
<meta property="og:image" content="https://skyyrose.com/wp-content/uploads/signature-collection-hero.jpg">
<meta property="og:url" content="https://skyyrose.com/collections/signature/">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="SIGNATURE Collection | SkyyRose">
<meta name="twitter:description" content="Timeless elegance meets modern luxury...">
<meta name="twitter:image" content="https://skyyrose.com/wp-content/uploads/signature-collection-hero.jpg">

<!-- Canonical URL -->
<link rel="canonical" href="https://skyyrose.com/collections/signature/">
```

---

### Google Search Console

**After Deployment**:
1. Submit sitemap: `https://skyyrose.com/sitemap_index.xml`
2. Request indexing for collection pages
3. Monitor Core Web Vitals report
4. Check for mobile usability errors
5. Verify structured data (Enhancements → Products)

---

## 🛡️ Security Testing

### WordPress Security

**1. File Permissions**:
```bash
# Directories: 755
find /path/to/wordpress -type d -exec chmod 755 {} \;

# Files: 644
find /path/to/wordpress -type f -exec chmod 644 {} \;

# wp-config.php: 600 (most secure)
chmod 600 /path/to/wordpress/wp-config.php
```

**2. SQL Injection** (WooCommerce forms):
- [ ] Test product search with SQL keywords: `' OR 1=1 --`
- [ ] Expected: Search returns 0 results (input sanitized)

**3. XSS (Cross-Site Scripting)**:
- [ ] Test product review with script tag: `<script>alert('XSS')</script>`
- [ ] Expected: Script stripped, displayed as text

**4. CSRF Protection**:
- [ ] Verify WordPress nonces on forms
- [ ] Check `functions.php` for `wp_create_nonce('skyyrose-collection')`

**5. HTTPS Enforcement**:
- [ ] All assets loaded over HTTPS (no mixed content warnings)
- [ ] Redirect HTTP → HTTPS (test: http://skyyrose.com → https://skyyrose.com)

---

## 📋 WooCommerce Functionality

### Product Pages

**Test Product**: "Love Hurts Windbreaker Jacket - Men's Black"

1. **Product Display**:
   - [ ] Hero image displays (1200×1200px)
   - [ ] Gallery images (4-10 images)
   - [ ] Lightbox zoom works (click image)
   - [ ] Thumbnails clickable (change main image)

2. **Product Information**:
   - [ ] Title, price, SKU displayed
   - [ ] Short description visible
   - [ ] Long description in tabs (Description, Additional Info, Reviews)
   - [ ] Stock status ("In stock" or "Out of stock")

3. **Add to Cart**:
   - [ ] Select size dropdown (if variable product)
   - [ ] Quantity selector (+ / - buttons)
   - [ ] "Add to Cart" button functional
   - [ ] Success message: "Product added to cart"
   - [ ] Cart icon updates (item count)

4. **Sticky Add to Cart** (Shoptimizer):
   - [ ] Scroll down past main image
   - [ ] Sticky bar appears at top
   - [ ] Contains: Product thumbnail, title, price, "Add to Cart" button
   - [ ] Sticky bar functional (adds product to cart)

---

### Checkout Process

**Test Flow**: Add 2 products → Cart → Checkout → Order Complete

1. **Cart Page** (`/cart/`):
   - [ ] Products listed correctly
   - [ ] Quantity updatable (+ / - buttons)
   - [ ] "Remove" button works
   - [ ] Subtotal calculates correctly
   - [ ] "Proceed to Checkout" button visible

2. **Checkout Page** (`/checkout/`):
   - [ ] Billing details form (first name, last name, email, address)
   - [ ] Shipping method selection (if applicable)
   - [ ] Payment method (Stripe, PayPal, etc.)
   - [ ] Order summary sidebar
   - [ ] Trust badges displayed
   - [ ] "Place Order" button functional

3. **Order Confirmation**:
   - [ ] Thank you page displays
   - [ ] Order number shown
   - [ ] Confirmation email sent

---

## 🚨 Error Handling

### Test Scenarios

**1. JavaScript Disabled**:
- [ ] Site still functional (no Three.js, but product grid works)
- [ ] Display message: "For the best experience, enable JavaScript"

**2. WebGL Not Supported**:
- [ ] Fallback message: "Your browser doesn't support 3D graphics. Please upgrade to a modern browser."
- [ ] Product grid still accessible

**3. Slow Connection (3G)**:
- [ ] Loading spinner displays while Three.js loads
- [ ] Skeleton screens for product grid
- [ ] Page doesn't freeze (non-blocking script loading)

**4. 404 Errors**:
- [ ] Three.js file missing: Error message in console, no site crash
- [ ] Product image missing: Placeholder image displayed
- [ ] Page not found: Custom 404 page

---

## 📊 Test Results Template

### Collection: SIGNATURE

**Date Tested**: 2026-01-11
**Tested By**: [Your Name]
**Environment**: Local / Staging / Production

| Test Category | Status | Notes |
|--------------|--------|-------|
| JavaScript Load | ✅ Pass | Scene loaded in 1.2s |
| Visual Rendering | ✅ Pass | All elements visible |
| Interactions | ✅ Pass | Click, drag, zoom working |
| Performance (Lighthouse) | ⚠ Warning | Score: 85 (target: 90) |
| Mobile Responsive | ✅ Pass | iPhone 14 tested |
| Accessibility | ✅ Pass | WCAG AA compliant |
| SEO | ✅ Pass | Schema.org valid |
| Browser Compatibility | ✅ Pass | Chrome, Firefox, Safari |

**Issues Found**:
1. LCP slow on mobile (3.2s) - Reduce particle count from 2000 to 500
2. Minor CLS on product grid - Add height attribute to images

**Action Items**:
- [ ] Optimize particle count for mobile
- [ ] Add explicit image dimensions

---

## 🎯 Sign-Off Criteria

**Ready for Production** when ALL of the following are TRUE:

- [ ] All Three.js scenes load without errors (console clean)
- [ ] Lighthouse Performance ≥ 90 (desktop), ≥ 80 (mobile)
- [ ] Lighthouse Accessibility = 100
- [ ] Core Web Vitals passing (LCP < 2.5s, INP < 200ms, CLS < 0.1)
- [ ] Mobile responsive on 3+ devices (iPhone, Android, iPad)
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] WooCommerce checkout functional (test order placed successfully)
- [ ] Security scan clean (no vulnerabilities)
- [ ] Backup created (database + files)
- [ ] SSL certificate active (HTTPS enforced)
- [ ] Google Analytics tracking installed
- [ ] Sitemap submitted to Google Search Console

---

**Version**: 1.0.0
**Last Updated**: 2026-01-11
**Next Steps**: Execute tests in order, document results, fix issues before production deployment
