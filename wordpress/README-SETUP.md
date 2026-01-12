# SkyyRose WordPress Automated Setup Guide

> **Fast-track your luxury ecommerce site deployment with one-command automation**

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites Checklist

Before running the setup script, ensure you have:

- [ ] **WordPress installed** (version 6.0+)
- [ ] **WP-CLI installed** (check: `wp --version`)
- [ ] **Shoptimizer theme purchased** ([Buy here](https://www.commercegurus.com/product/shoptimizer/))
- [ ] **Database backup created** (WP-CLI: `wp db export backup.sql`)
- [ ] **SSH/Terminal access** to your WordPress server
- [ ] **Admin credentials** ready

### One-Command Setup

```bash
# Navigate to WordPress root
cd /path/to/wordpress

# Clone theme files (or upload manually)
# Make setup script executable
chmod +x /path/to/setup-wordpress.sh

# Run automated setup
bash /path/to/setup-wordpress.sh
```

**What happens automatically:**
1. ✅ Installs child theme
2. ✅ Activates required plugins (Elementor, WooCommerce, Rank Math, Wordfence)
3. ✅ Configures WooCommerce (currency, image sizes, gallery)
4. ✅ Creates product categories (SIGNATURE, LOVE HURTS, BLACK ROSE)
5. ✅ Creates collection pages with placeholders
6. ✅ Configures Shoptimizer theme (brand colors, conversion features)
7. ✅ Creates sample products (10 products across 3 collections)
8. ✅ Sets up permalinks
9. ✅ Creates essential pages (Home, Blog, About)

**Duration**: ~3-5 minutes

---

## 📦 What Gets Configured

### Theme & Plugins

| Component | Action | Details |
|-----------|--------|---------|
| **Shoptimizer Child** | Installed & Activated | SkyyRose luxury child theme with Three.js |
| **Elementor** | Installed & Activated | Visual page builder for collection pages |
| **WooCommerce** | Configured | Currency (USD), image sizes (1200×1200), gallery features |
| **Rank Math** | Installed | SEO plugin (manual config required) |
| **Wordfence** | Installed | Security plugin (manual config required) |

### Pages Created

| Page | URL | Status | Notes |
|------|-----|--------|-------|
| **Home** | `/` | Published | Set as front page, Elementor-ready |
| **Collections** | `/collections/` | Published | Parent page for 3 collections |
| **SIGNATURE** | `/collections/signature/` | Published | Three.js placeholder + product grid |
| **LOVE HURTS** | `/collections/love-hurts/` | Published | Three.js placeholder + product grid |
| **BLACK ROSE** | `/collections/black-rose/` | Published | Three.js placeholder + product grid |
| **Blog** | `/blog/` | Published | Set as posts page |
| **About Us** | `/about/` | Published | Brand story page |

### WooCommerce Categories

```
Collections (parent)
├── SIGNATURE Collection
├── LOVE HURTS Collection
└── BLACK ROSE Collection
```

### Sample Products (10 Total)

**SIGNATURE Collection (3)**:
- Signature Rose Hoodie ($89.99)
- Signature Rose Tee ($49.99)
- Signature Rose Joggers ($69.99)

**LOVE HURTS Collection (4)**:
- Love Hurts Windbreaker ($119.99) ⭐ Featured
- Love Hurts Hoodie ($99.99) ⭐ Featured
- Love Hurts Joggers ($74.99)
- Love Hurts Fanny Pack ($39.99)

**BLACK ROSE Collection (3)**:
- Black Rose Sherpa Jacket ($139.99) ⭐ Featured
- Black Rose Hooded Dress ($109.99) ⭐ Featured
- Black Rose Joggers ($79.99)

---

## 🎨 Post-Setup Manual Steps

### Step 1: Configure Collection Pages in Elementor (30-45 min each)

**For each collection page** (SIGNATURE, LOVE HURTS, BLACK ROSE):

1. **WordPress Admin → Pages → [Collection Name] → Edit with Elementor**

2. **Replace Three.js Placeholder**:
   - Delete the placeholder section
   - Add **HTML Widget** (Elementor Pro required)
   - Paste Three.js integration code from `ELEMENTOR_PAGE_TEMPLATES.md`
   - Update container ID (e.g., `love-hurts-3d-container`)

3. **Customize Sections**:
   - Hero: Update headline, tagline, background image
   - Story: Add collection narrative and images
   - CTA: Configure newsletter signup form

4. **Publish & Test**:
   - View page in browser
   - Verify Three.js scene loads (check browser console for errors)
   - Test product interactions (click pedestals)

**Detailed Instructions**: See `ELEMENTOR_PAGE_TEMPLATES.md` (10,000+ words)

---

### Step 2: Upload Product Images (1-2 hours)

**Process images with automation script**:

```bash
# Install Python dependencies
pip install Pillow

# Run image processor
cd /path/to/wordpress
python3 process_product_images.py
```

**What happens**:
- Reads 65+ raw images from `/DevSkyy/assets/3d-models/`
- Crops to 1:1 aspect ratio (center crop)
- Resizes to 4 sizes: 1200×1200, 600×600, 300×300, thumbnails
- Converts to WebP (90% quality, ~40% smaller)
- Organizes by collection and product
- Output: `/wordpress/product-images-processed/`

**Upload to WordPress**:

Option A - WP-CLI (fastest):
```bash
wp media import product-images-processed/**/*.webp --porcelain
```

Option B - WordPress Admin:
1. Media → Add New → Select Files
2. Drag and drop all WebP files (bulk upload)
3. Wait for upload to complete

**Assign to products**:
1. Products → [Product Name] → Edit
2. Product Image → Set product image
3. Product Gallery → Add gallery images
4. Update product

**Detailed Instructions**: See `PRODUCT_IMAGERY_GUIDE.md` (8,000+ words)

---

### Step 3: Import Additional Products (Optional)

If you have more products beyond the 10 samples:

**Via WP-CLI**:
```bash
wp wc product_csv import woocommerce-products-import.csv --user=admin
```

**Via WordPress Admin**:
1. WooCommerce → Products → Import
2. Upload `woocommerce-products-import.csv`
3. Map columns (auto-detected)
4. Run import

**CSV Format**: Pre-configured with:
- SKUs, pricing, inventory
- Product descriptions
- Attributes (Size, Color)
- Category assignments

---

### Step 4: Configure Shoptimizer Conversion Features (15 min)

**WordPress Admin → Shoptimizer → Settings**:

**Conversion Optimization**:
- ✅ Enable Sticky Add to Cart
- ✅ Enable Trust Badges (configure badges in next tab)
- ✅ Enable Distraction-Free Checkout
- ✅ Enable Cart Slider (side cart)

**Trust Badges** (Shoptimizer → Trust Badges):
1. Upload badge icons: Secure Checkout, Free Shipping, 30-Day Returns
2. Position: Below Add to Cart button
3. Display on: Single product pages only

**Colors** (Shoptimizer → Styling):
- Primary Color: `#B76E79` (SkyyRose Pink)
- Secondary Color: `#2a1a2e` (Dark Purple)
- Accent Color: `#d4af37` (Gold)

**Typography**:
- Headings: Playfair Display (serif, elegant)
- Body: Montserrat (sans-serif, modern)

---

### Step 5: Configure Rank Math SEO (20 min)

**WordPress Admin → Rank Math → Setup Wizard**:

1. **Import & Export**: Skip (fresh install)
2. **Your Website**: Select "Online Shop"
3. **Google Services**: Connect Search Console & Analytics
4. **Sitemap**: Enable all (Posts, Pages, Products)
5. **SEO Tweaks**: Enable all recommended settings

**Product Schema** (Rank Math → Schema Templates):
1. Create new template: "Product"
2. Schema Type: "Product"
3. Apply to: All Products
4. Configure fields:
   - Name: `%title%`
   - Description: `%excerpt%`
   - Image: `%product_image%`
   - Price: `%product_price%`
   - Availability: `%product_availability%`
   - Brand: "SkyyRose"

**Collection Page Schema**:
- Schema Type: "CollectionPage"
- Main entity: "OfferCatalog"

---

### Step 6: Configure Wordfence Security (10 min)

**WordPress Admin → Wordfence → Dashboard**:

1. **License**: Activate free or premium key
2. **Scan**: Run initial scan (15-20 min)
3. **Firewall**: Enable Web Application Firewall (WAF)
4. **Brute Force Protection**: Enable login security
5. **Two-Factor Auth**: Enable for admin users

**Recommended Rules**:
- Block country: Enable if you only serve specific regions
- Rate limiting: Max 5 login attempts per minute
- Hide WordPress version: Enable

---

## 🧪 Testing Your Setup

### Quick Smoke Test (5 min)

```bash
# Check WordPress core
wp core version
wp core verify-checksums

# Check theme
wp theme list
wp theme is-active shoptimizer-child-theme

# Check plugins
wp plugin list --status=active

# Check pages
wp post list --post_type=page --format=table

# Check products
wp post list --post_type=product --format=table

# Check categories
wp term list product_cat --format=table
```

### Visual Testing Checklist

- [ ] **Homepage loads** without errors
- [ ] **Collections parent page** displays 3 collection cards
- [ ] **SIGNATURE page** Three.js scene loads (rose garden)
- [ ] **LOVE HURTS page** Three.js scene loads (enchanted rose visible)
- [ ] **BLACK ROSE page** Three.js scene loads (night sky)
- [ ] **Product grids** display correctly on collection pages
- [ ] **Single product pages** show gallery, price, add to cart
- [ ] **Cart/Checkout** functions (test purchase flow)
- [ ] **Mobile responsive** (test on iPhone/Android simulator)
- [ ] **No console errors** (F12 → Console tab)

**Comprehensive Testing**: See `TESTING_PLAN.md` (8,000+ words)

---

## ⚡ Performance Optimization

### After Setup, Optimize for Speed

**Install WP Rocket** (caching plugin):
```bash
# Purchase from https://wp-rocket.me/
# Upload plugin zip via WordPress Admin
wp plugin install /path/to/wp-rocket.zip --activate
```

**WP Rocket Config**:
- ✅ Cache Preloading: Enable
- ✅ Lazy Load Images: Enable
- ✅ Minify CSS/JS: Enable
- ✅ Combine CSS files: Disable (breaks Elementor)
- ✅ Database Optimization: Weekly

**Cloudflare Setup** (free CDN):
1. Create account at [Cloudflare](https://www.cloudflare.com/)
2. Add your domain
3. Update nameservers at your registrar
4. Enable Auto Minify (CSS, JS, HTML)
5. Enable Brotli compression

**Image Optimization**:
- All images already WebP (via `process_product_images.py`)
- WordPress lazy loading enabled by default (6.0+)
- Consider Cloudflare Polish for additional compression

**Target Metrics**:
- Lighthouse Performance: 90+ (desktop), 80+ (mobile)
- LCP (Largest Contentful Paint): < 2.5s
- INP (Interaction to Next Paint): < 200ms
- CLS (Cumulative Layout Shift): < 0.1

---

## 🔧 Troubleshooting

### Setup Script Fails

**Error: "WP-CLI not found"**
```bash
# Install WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp
```

**Error: "WordPress not installed"**
```bash
# Verify you're in WordPress root
ls -la | grep wp-config.php

# If not found, navigate to correct directory
cd /var/www/html  # Common location
```

**Error: "Parent theme not found"**
- Purchase Shoptimizer: https://www.commercegurus.com/product/shoptimizer/
- Upload via WordPress Admin → Appearance → Themes → Add New → Upload Theme

---

### Three.js Scenes Not Loading

**Symptom**: Blank space where 3D scene should be

**Fixes**:
1. **Check file paths** (WordPress Admin → Appearance → Theme File Editor):
   - Verify `assets/js/three.module.min.js` exists
   - Verify `assets/js/collections/love-hurts.js` exists
   - Check file permissions: `chmod 644 *.js`

2. **Clear cache**:
   - Browser: Ctrl+Shift+R (hard reload)
   - WP Rocket: Rocket → Clear Cache
   - Cloudflare: Caching → Purge Everything

3. **Check console errors** (F12 → Console):
   - Look for 404 errors (missing files)
   - CORS errors (check file permissions)
   - JavaScript syntax errors (run `node love-hurts.js` locally to test)

4. **Verify Elementor HTML widget**:
   - Edit page with Elementor
   - Check HTML widget contains import map + scene script
   - Verify container ID matches (e.g., `love-hurts-3d-container`)

---

### Products Not Displaying

**Symptom**: Empty product grids on collection pages

**Fixes**:
1. **Check shortcode**:
   ```
   [products limit="12" columns="4" category="love-hurts" orderby="menu_order"]
   ```
   - Verify `category` slug matches (signature, love-hurts, black-rose)

2. **Check product visibility**:
   ```bash
   wp post list --post_type=product --format=table
   ```
   - Status should be "publish"
   - Categories should be assigned

3. **Rebuild category counts**:
   ```bash
   wp wc tool run recount_terms
   ```

---

## 📞 Support Resources

### Documentation

- **WordPress Setup**: This file (you're reading it!)
- **Elementor Templates**: `ELEMENTOR_PAGE_TEMPLATES.md` (10,000 words)
- **Product Imagery**: `PRODUCT_IMAGERY_GUIDE.md` (8,000 words)
- **Premium Enhancements**: `WORDPRESS_ENHANCEMENTS.md` (15,000 words)
- **Testing Plan**: `TESTING_PLAN.md` (8,000 words)
- **Master Guide**: `README.md` (deployment overview)

### External Resources

- [Shoptimizer Docs](https://www.commercegurus.com/docs/shoptimizer-theme/)
- [Elementor Academy](https://elementor.com/academy/)
- [WooCommerce Docs](https://woocommerce.com/documentation/)
- [WP-CLI Handbook](https://make.wordpress.org/cli/handbook/)
- [Three.js Manual](https://threejs.org/manual/)

---

## 🎉 Success Checklist

Before launching to production, verify:

- [ ] Setup script completed without errors
- [ ] All 3 collection pages display Three.js scenes
- [ ] Enchanted rose visible in LOVE HURTS collection
- [ ] 10+ products created and assigned to collections
- [ ] Product images uploaded and optimized (WebP)
- [ ] Shoptimizer conversion features enabled
- [ ] Rank Math SEO configured (Schema.org markup)
- [ ] Wordfence security scan passed (0 critical issues)
- [ ] SSL certificate installed (HTTPS)
- [ ] Lighthouse Performance score ≥ 90 (desktop)
- [ ] Mobile responsive tested (iPhone, Android, iPad)
- [ ] Checkout flow tested (test purchase completed)
- [ ] Contact form tested (submission successful)
- [ ] Privacy Policy and Terms of Service pages created
- [ ] Google Analytics tracking code added
- [ ] Backup plugin configured (daily backups to cloud)

---

## 📊 Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Lighthouse Performance** | ≥ 90 | - | ⏳ |
| **Lighthouse Accessibility** | 100 | - | ⏳ |
| **Lighthouse Best Practices** | ≥ 95 | - | ⏳ |
| **Lighthouse SEO** | 100 | - | ⏳ |
| **LCP** | < 2.5s | - | ⏳ |
| **INP** | < 200ms | - | ⏳ |
| **CLS** | < 0.1 | - | ⏳ |

**Test with**: [Google PageSpeed Insights](https://pagespeed.web.dev/)

---

**Version**: 1.0.0
**Created**: 2026-01-12
**Status**: Production-Ready
**Author**: Claude (Principal Engineer)

**For your daughter - built with 100x the care ❤️**
