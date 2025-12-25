# SkyyRose WordPress Site Deployment Guide

**Status**: Ready for Deployment
**Infrastructure**: 80% Complete
**Estimated Completion**: 5 Days
**Last Updated**: 2025-12-25

______________________________________________________________________

## 📋 Executive Summary

This guide walks through the complete SkyyRose WordPress site deployment, from extracted assets to live production. The DevSkyy platform provides production-ready infrastructure for:

- **Elementor Page Builders** (5 templates)
- **WordPress REST API Integration** (CollectionPageManager)
- **3D Model Generation** (Tripo3D API)
- **WooCommerce Configuration** (products, collections, shipping)
- **Performance & SEO Testing**

**Timeline**: 5 days across 5 phases

______________________________________________________________________

## 🏗️ Architecture Overview

```
Phase 1: Asset Extraction (COMPLETE ✓)
  └─ Extract 361MB of product images & specs from updev 4.zip

Phase 1.5: 3D Model Generation (READY)
  └─ Convert product images to GLB/USDZ via Tripo3D API

Phase 2: Template Generation (COMPLETE ✓)
  └─ Generate Elementor JSON for 5 page types

Phase 3: WordPress Deployment (PENDING - requires credentials)
  └─ Deploy pages to WordPress via REST API

Phase 4: WooCommerce Configuration (PENDING - requires Phase 3)
  └─ Create products, categories, shipping rules

Phase 5: Testing & Launch (PENDING - requires Phases 3-4)
  └─ Performance, functionality, SEO validation
```

______________________________________________________________________

## ✅ Phase 1: Asset Extraction (COMPLETE)

**Status**: ✅ DONE
**Output**: 361MB of product images organized by collection

### What Was Done

- Extracted 3 collection ZIP files:
  - **Black Rose**: 83MB (45+ product images)
  - **Love Hurts**: 212MB (75+ product images)
  - **Signature**: 66MB (40+ product images)
- Copied 8 specification documents to `assets/specifications/`

### Output Directory Structure

```
assets/3d-models/
├── black-rose/
│   ├── product_images/
│   │   ├── *.jpg (product photos)
│   │   ├── *.png (design specs)
│   │   └── *.html (reference templates)
│   └── specifications/
│
├── love-hurts/
│   ├── product_images/
│   │   └── *.jpg (product photos)
│   └── videos/
│       └── *.mp4 (product videos)
│
└── signature/
    ├── product_images/
    │   └── *.jpg (product photos)
    └── reference_materials/
```

### Specification Files

All 8 specs copied to `assets/specifications/`:

- `SPINNING_LOGO_SPEC.md` - Logo animation specs
- `HOMEPAGE_SPEC.md` - Homepage layout & sections
- `GLOBAL_CONFIG.md` - Brand colors, typography, spacing
- `BLACK_ROSE_SPEC.md` - Collection-specific design
- `LOVE_HURTS_SPEC.md` - Collection-specific design
- `SIGNATURE_SPEC.md` - Collection-specific design
- `PRODUCT_PAGE_SPEC.md` - Product detail page layout
- `SHOP_ARCHIVE_SPEC.md` - Product grid/archive pages

______________________________________________________________________

## 🤖 Phase 1.5: 3D Model Generation (READY)

**Status**: ⏳ READY TO EXECUTE
**Input**: 164+ product reference images
**Output**: Production-ready GLB + USDZ models
**Time**: ~2-3 hours (depends on API quota)
**Prerequisites**: TRIPO_API_KEY environment variable

### Why This Phase Matters

- Product pages need 3D models for gallery display
- AR Quick Look (iOS) requires USDZ format
- Web viewers use GLB (binary glTF)
- Models must be attached to WooCommerce products

### Setup Instructions

#### 1. Get Tripo3D API Key

```bash
# Visit https://www.tripo3d.ai/dashboard
# Get free API key (100 free generations per month)
# Save key to environment
export TRIPO_API_KEY="your-api-key-here"
```

#### 2. Verify Assets Were Extracted

```bash
# Check that Phase 1 completed successfully
ls -la assets/3d-models/black-rose/ | wc -l
# Should show 40+ files

ls -la assets/3d-models/love-hurts/ | wc -l
# Should show 70+ files

ls -la assets/3d-models/signature/ | wc -l
# Should show 30+ files
```

#### 3. Run 3D Generation Script

```bash
# Execute batch generation
python3 scripts/generate_3d_models_from_assets.py

# Output:
# ✓ Black Rose: 45 models generated
# ✓ Love Hurts: 75 models generated
# ✓ Signature: 38 models generated
# ✓ Inventory saved to: assets/3d-models-generated/GENERATED_INVENTORY.json
```

#### 4. Verify Output

```bash
# Check generated models
find assets/3d-models-generated -name "*.glb" | wc -l
# Should show ~160 GLB files

find assets/3d-models-generated -name "*.usdz" | wc -l
# Should show ~160 USDZ files (for AR Quick Look)
```

### Output Structure

```
assets/3d-models-generated/
├── black-rose/
│   ├── product-name-001.glb
│   ├── product-name-001.usdz
│   ├── product-name-002.glb
│   ├── product-name-002.usdz
│   └── ...
├── love-hurts/
│   ├── product-name-001.glb
│   └── ...
├── signature/
│   ├── product-name-001.glb
│   └── ...
└── GENERATED_INVENTORY.json
```

### Generated Inventory Format

```json
{
  "generated_at": "2025-12-25T08:15:00.000Z",
  "duration_seconds": 7200,
  "collections": [
    {
      "collection": "BLACK_ROSE",
      "total_images": 45,
      "successful": 43,
      "failed": 2,
      "models": [
        {
          "product_name": "Heart Rose Bomber",
          "model_path": "assets/3d-models-generated/black-rose/heart-rose-bomber.glb",
          "model_url": "https://cdn.example.com/models/heart-rose-bomber.glb"
        }
      ]
    }
  ],
  "summary": {
    "total_images_processed": 158,
    "successful": 153,
    "failed": 5,
    "success_rate": "96.8%"
  }
}
```

### Rate Limiting & Costs

- **Free Tier**: 100 generations/month
- **Batch Processing**: 3 concurrent requests (conservative)
- **Expected Cost**: ~$50-100 USD for full collection (at ~$0.50/generation)
- **Time Estimate**: 2-3 hours for 160 generations

______________________________________________________________________

## 🎨 Phase 2: Template Generation (COMPLETE)

**Status**: ✅ DONE
**Output**: 6 Elementor templates as JSON

### What Was Done

Generated production-ready Elementor templates using existing page builders:

1. **Homepage** (`templates/home.json`)

   - Hero section with brand messaging
   - 3D model showcase section
   - Collection navigation
   - Newsletter signup
   - Footer with links

1. **Collection Pages** (3 variants)

   - **Black Rose** (`templates/black_rose.json`)
   - **Love Hurts** (`templates/love_hurts.json`)
   - **Signature** (`templates/signature.json`)
   - Interactive Three.js experiences
   - Product grid with filters
   - Collection-specific branding

1. **About Page** (`templates/about.json`)

   - Brand story
   - Team section
   - Mission/values
   - Contact info

1. **Blog Page** (`templates/blog.json`)

   - Journal/article listing
   - Featured posts
   - Search & filters
   - Related articles

### Output Structure

```
wordpress/elementor_templates/
├── home.json                 # Homepage template
├── black_rose.json           # Black Rose collection
├── love_hurts.json           # Love Hurts collection
├── signature.json            # Signature collection
├── about.json                # About page
└── blog.json                 # Blog/Journal page
```

### Template Schema

Each template is Elementor-compatible JSON with:

```json
{
  "id": "page_id",
  "title": "Page Title",
  "status": "publish",
  "post_type": "page",
  "elementor_version": "3.32.2",
  "sections": [
    {
      "id": "section_1",
      "element_type": "section",
      "settings": { "brand_color": "#B76E79" },
      "elements": [
        {
          "id": "widget_1",
          "element_type": "heading",
          "settings": { "title": "Welcome to SkyyRose" }
        }
      ]
    }
  ]
}
```

### Custom 3D Widgets

Templates include custom Elementor widgets for 3D:

- **ThreeJS Viewer**: Interactive 3D model display
- **AR Quick Look Button**: iOS AR launching
- **Model Carousel**: Rotating product gallery
- **Countdown Timer**: Pre-order countdowns

______________________________________________________________________

## 🚀 Phase 3: WordPress Deployment (PENDING)

**Status**: ⏳ PENDING WordPress Credentials
**Time**: ~2 hours
**Prerequisites**:

- WordPress installation (local, staging, or production)
- Admin credentials with app password
- Elementor Pro 3.32.2+ installed
- WooCommerce plugin installed

### Prerequisites Setup

#### 1. WordPress Installation

```bash
# If using local WordPress (Docker)
docker-compose up -d wordpress

# If using existing WordPress
# Just note the URL for the next step
```

#### 2. Generate App Password

In WordPress admin panel:

1. Go to **Settings** → **Application Passwords**
1. Enter app name: "DevSkyy SkyyRose Deployment"
1. Click "Add New Application Password"
1. Copy the generated password (format: `xxxx-xxxx-xxxx-xxxx`)

#### 3. Set Environment Variables

```bash
# Option A: Command line
export WORDPRESS_URL="https://your-site.local"
export WORDPRESS_USERNAME="admin"
export WORDPRESS_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Option B: .env file
cat > .env.wordpress << 'EOF'
WORDPRESS_URL=https://your-site.local
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EOF
source .env.wordpress
```

### Execution

#### 1. Deploy Pages to WordPress

```bash
python3 scripts/extract_and_deploy_skyyrose.py \
  --wp-url "$WORDPRESS_URL" \
  --wp-username "$WORDPRESS_USERNAME" \
  --wp-app-password "$WORDPRESS_APP_PASSWORD"
```

Expected output:

```
Phase 3: Deploying pages to WordPress...
  ✓ Homepage deployed (page_id: 123)
  ✓ Black Rose collection deployed (page_id: 124)
  ✓ Love Hurts collection deployed (page_id: 125)
  ✓ Signature collection deployed (page_id: 126)
  ✓ About page deployed (page_id: 127)
  ✓ Blog page deployed (page_id: 128)
```

#### 2. Verify Pages in WordPress Admin

```
Admin → Pages
├── SkyyRose - Where Love Meets Luxury (Home)
├── Black Rose Collection
├── Love Hurts Collection
├── Signature Collection
├── About SkyyRose
└── Journal (Blog)
```

#### 3. Configure Page Settings

For each page in WordPress admin:

1. Click "Edit" → "Edit with Elementor"
1. Verify design renders correctly
1. Check that 3D widgets load
1. Set page visibility (Published)
1. Configure SEO (meta title, description)

______________________________________________________________________

## 🛒 Phase 4: WooCommerce Configuration (PENDING)

**Status**: ⏳ PENDING Phase 3
**Time**: ~3 hours
**What You'll Do**:

- Create products for each collection
- Attach 3D models to product galleries
- Create collection categories
- Configure shipping rules

### 4.1 Create Product Categories

In WordPress admin: **Products** → **Categories**

```
Categories to create:
├── Black Rose (description: "Gothic elegance...")
├── Love Hurts (description: "Emotional expression...")
└── Signature (description: "Timeless essentials...")
```

### 4.2 Create Sample Products

For each collection, create at least 3 products:

**Black Rose Collection**

- Product 1: Heart Rose Bomber

  - Price: $299.00
  - Collection: Black Rose
  - Images: Attach 3D GLB + USDZ
  - Description: Use specs from PRODUCT_PAGE_SPEC.md

- Product 2: Rose Gold Hoodie

  - Price: $199.00
  - Collection: Black Rose
  - Images: Attach 3D GLB + USDZ

- Product 3: Black Pearl Tee

  - Price: $89.00
  - Collection: Black Rose
  - Images: Attach 3D GLB + USDZ

**Love Hurts Collection**

- Heart Attack Jacket
- Broken Crown Sweatshirt
- Love Struck Track Pants

**Signature Collection**

- Essential Crew Neck
- Premium Hoodie
- Classic Tee

### 4.3 Attach 3D Models to Products

For each product:

1. Go to **Products** → Edit Product

1. Scroll to **Elementor Custom Content**

1. Add 3D Model Widget:

   ```
   - Model Format: GLB (primary)
   - Model URL: /wp-content/uploads/3d-models/product-name.glb
   - USDZ URL: /wp-content/uploads/3d-models/product-name.usdz (iOS AR)
   - Allow AR: Yes
   - Auto-rotate: Yes
   ```

1. Upload models to WordPress Media:

   ```bash
   # Copy generated models to WordPress media folder
   cp assets/3d-models-generated/*/*.glb /path/to/wordpress/wp-content/uploads/3d-models/
   cp assets/3d-models-generated/*/*.usdz /path/to/wordpress/wp-content/uploads/3d-models/
   ```

### 4.4 Configure Shipping

In WordPress admin: **WooCommerce** → **Settings** → **Shipping**

**Shipping Rules**:

- Free shipping for orders $150+
- Flat rate: $10 for orders under $150
- Estimated delivery: 5-7 business days

```yaml
Flat Rate Shipping:
  Cost: $10.00
  Requires: orders under $150

Free Shipping:
  Min Amount: $150.00
  Requires: orders $150+
```

### 4.5 Configure Checkout

In WordPress admin: **WooCommerce** → **Settings** → **Checkout**

**Payment Methods**:

- Stripe (recommended)
- PayPal
- Apple Pay (via Stripe)

**Checkout Fields**:

- Email, First/Last name
- Address (shipping/billing)
- Phone number
- Newsletter signup

______________________________________________________________________

## ✅ Phase 5: Testing & Verification (PENDING)

**Status**: ⏳ PENDING Phases 3-4
**Time**: ~2 hours
**Success Criteria**: All tests pass + Core Web Vitals > 90

### 5.1 Performance Testing

#### Homepage Performance

```bash
# Test with Google PageSpeed Insights
curl "https://pagespeedonline.googleapis.com/..." \
  --url "https://your-site.com"

# Expected results:
# - LCP (Largest Contentful Paint): < 2.5s
# - FID (First Input Delay): < 100ms
# - CLS (Cumulative Layout Shift): < 0.1
# - PageSpeed Score: 90+
```

#### 3D Model Loading

```
Test: Collection pages with 3D experiences
├─ Load time: < 3 seconds
├─ Model file size: < 5MB
├─ Frame rate: 60 FPS (smooth)
└─ Mobile performance: LCP < 3s
```

#### Mobile Performance

```
Test: Mobile (iPhone 12) performance
├─ Homepage LCP: < 3s
├─ Tap to interactive: < 5s
├─ Mobile PageSpeed: 85+
└─ Touch responsiveness: No delays
```

### 5.2 Functionality Testing

#### Add to Cart Flow

```
1. Navigate to product page
2. Click "Add to Cart" button
3. Verify: Product added to cart
4. Verify: Cart icon updates
5. Verify: Cart count correct
```

#### Checkout Flow

```
1. Go to cart
2. Click "Proceed to Checkout"
3. Enter shipping details
4. Select shipping method
5. Verify: Shipping cost calculated
6. Enter billing info
7. Select payment method
8. Complete payment
9. Verify: Order confirmation email
10. Verify: Order in WordPress admin
```

#### 3D Model Viewer

```
Product pages:
├─ 3D model loads
├─ Auto-rotation works
├─ Zoom/pan works
├─ AR button visible (iOS)
└─ Full-screen view works

AR (iOS only):
├─ "View in AR" button works
├─ Model loads in AR Quick Look
├─ Can rotate/scale in AR
└─ Can share AR view
```

#### Collection Experiences

```
Black Rose Collection:
├─ Three.js scene loads
├─ Gothic rose garden renders
├─ Product grid shows products
├─ Filters work
├─ Product links work

Love Hurts Collection:
├─ Ballroom scene loads
├─ Heart motifs render
├─ Product grid shows products
└─ Checkout integration works

Signature Collection:
├─ Outdoor luxury scene loads
├─ Product display works
└─ Pre-order information shows
```

### 5.3 SEO Validation

#### Meta Tags

```bash
# Check each page
curl -s https://your-site.com | grep -o '<title>.*</title>'
curl -s https://your-site.com | grep -o '<meta name="description"'

# Expected:
# <title>SkyyRose - Where Love Meets Luxury</title>
# <meta name="description" content="Premium luxury streetwear...">
```

#### Schema Markup

```bash
# Check for structured data
curl -s https://your-site.com | grep -o 'schema.org'

# Expected schema types:
# - Organization (brand)
# - Product (each product)
# - BreadcrumbList (navigation)
# - LocalBusiness (Oakland location)
```

#### Sitemap & Robots

```bash
# Verify sitemap
curl https://your-site.com/sitemap.xml

# Should include:
# - All collection pages
# - All product pages
# - All blog posts
```

#### Core Web Vitals

Use Google Search Console or Lighthouse:

```
✓ LCP: < 2.5s
✓ FID: < 100ms
✓ CLS: < 0.1
✓ Overall Score: 90+
```

### 5.4 Post-Launch Checklist

- [ ] All pages accessible and loading
- [ ] Homepage LCP < 2.5s
- [ ] Mobile PageSpeed > 85
- [ ] Add to cart works
- [ ] Checkout completes
- [ ] Order confirmation emails send
- [ ] 3D models display correctly
- [ ] AR Quick Look works (iOS)
- [ ] Collection experiences interactive
- [ ] SEO meta tags correct
- [ ] Schema markup valid
- [ ] Analytics tracking active
- [ ] Email notifications configured
- [ ] Backup created

______________________________________________________________________

## 🔧 Troubleshooting

### Phase 1: Asset Extraction Issues

**Problem**: ZIP files don't extract
**Solution**:

```bash
# Check file integrity
unzip -t /path/to/updev\ 4.zip

# Extract with verbose output
unzip -v /path/to/updev\ 4.zip | head -20
```

**Problem**: Not enough disk space
**Solution**:

```bash
# Check available space
df -h

# Need: ~500MB free
# If insufficient, delete old files or expand drive
```

### Phase 1.5: 3D Generation Issues

**Problem**: "API key not found"
**Solution**:

```bash
# Verify key is set
echo $TRIPO_API_KEY

# If empty, set it
export TRIPO_API_KEY="your-key-from-tripo3d.ai"
```

**Problem**: "Rate limit exceeded"
**Solution**:

```bash
# Tripo limits: 10 requests/minute for free tier
# Script has 3 concurrent limit (conservative)
# Wait 1 hour or upgrade to premium
```

**Problem**: "Generation timed out"
**Solution**:

```bash
# Increase timeout in script
# Look for: TRIPO_TIMEOUT = 300 (seconds)
# Increase to: TRIPO_TIMEOUT = 600 (10 minutes)
```

### Phase 3: WordPress Deployment Issues

**Problem**: "Invalid app password"
**Solution**:

```bash
# Regenerate app password in WordPress
# Settings → Application Passwords
# Delete old password, create new one
# Copy exactly (no spaces)
```

**Problem**: "Connection refused"
**Solution**:

```bash
# Verify WordPress is running
curl -I https://your-site.local

# Check network connectivity
ping your-site.local
```

**Problem**: "Elementor templates invalid"
**Solution**:

```bash
# Verify Elementor is installed
# WordPress Admin → Plugins → Check "Elementor" is active

# Verify Elementor Pro (required for advanced features)
# If missing, install from Elementor marketplace

# Clear Elementor cache
# Settings → Elementor → Cache
```

### Phase 4: WooCommerce Configuration Issues

**Problem**: "Products not showing in collection"
**Solution**:

```bash
# Verify product category assigned
# Edit Product → Product Data → Categories
# Check "Black Rose" (or appropriate collection) is selected

# Verify collection page uses correct shortcode
# Edit Collection Page → Check for [woocommerce_products category="black-rose"]
```

**Problem**: "3D models not displaying"
**Solution**:

```bash
# Verify model files uploaded to media library
# Admin → Media → Check for .glb and .usdz files

# Verify custom widget installed
# Admin → Elementor → Custom Widgets
# Should show: "ThreeJS Viewer" widget

# Check browser console for errors
# DevTools → Console → Any error messages?
```

**Problem**: "Shipping not calculating"
**Solution**:

```bash
# Verify shipping zones configured
# WooCommerce → Settings → Shipping → Zones

# Add zone for your location:
# Zone Name: Domestic
# Zone Regions: United States
# Shipping Methods: Flat Rate + Free Shipping

# Verify shipping class assigned to products
# Products → Categories → Check "Shipping Class"
```

______________________________________________________________________

## 📚 Additional Resources

### Documentation Files

- `CLAUDE.md` - Project configuration and guidelines
- `README.md` - Main project documentation
- `docs/DEVSKYY_MASTER_PLAN.md` - Architecture overview

### SkyyRose Assets

- `assets/3d-models/` - Extracted product images
- `assets/specifications/` - Brand & design specs
- `wordpress/elementor_templates/` - Generated templates
- `wordpress/collection_templates/` - Three.js experiences

### Configuration Files

- `.env.example` - Environment variable template
- `vercel.json` - Deployment configuration
- `docker-compose.yml` - Local WordPress setup

### Support Files

- `scripts/extract_and_deploy_skyyrose.py` - Main orchestrator
- `scripts/generate_3d_models_from_assets.py` - 3D generation
- `tests/test_tripo_api.py` - Tripo3D integration tests

______________________________________________________________________

## 🎯 Success Criteria

### Phase 1: ✅

- [x] 361MB assets extracted
- [x] 8 spec documents copied
- [x] Directory structure verified

### Phase 1.5: ⏳

- [ ] 160+ 3D models generated
- [ ] Models organized by collection
- [ ] GENERATED_INVENTORY.json created
- [ ] Success rate > 90%

### Phase 2: ✅

- [x] 6 Elementor templates created
- [x] Templates exported to JSON
- [x] BrandKit colors applied
- [x] Custom widgets integrated

### Phase 3: ⏳

- [ ] 5 pages deployed to WordPress
- [ ] Pages accessible from frontend
- [ ] Elementor editor works
- [ ] 3D widgets render

### Phase 4: ⏳

- [ ] 9+ products created (3 per collection)
- [ ] 3D models attached to products
- [ ] Categories created and linked
- [ ] Shipping configured ($150 free shipping)

### Phase 5: ⏳

- [ ] Homepage LCP < 2.5s
- [ ] Mobile PageSpeed > 85
- [ ] Add to cart functional
- [ ] Checkout completes
- [ ] 3D models display
- [ ] AR Quick Look works (iOS)
- [ ] Core Web Vitals > 90

______________________________________________________________________

## 📞 Support

### Get Help

1. **Check docs**: Read relevant section in this guide
1. **Check logs**: `scripts/*.log` files for detailed errors
1. **Search issues**: GitHub Issues for similar problems
1. **Contact support**: <support@skyyrose.com>

### Report Issues

Create GitHub issue with:

- Phase where issue occurred
- Error message/logs
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, WordPress version, etc.)

______________________________________________________________________

**Next Steps**:

1. Ensure Phase 1 is complete (check assets extracted)
1. Run Phase 1.5 when you have Tripo API key
1. Provide WordPress credentials to execute Phase 3
1. Follow phases 4-5 for complete deployment

**Questions?** Refer to relevant phase section above or review specification files in `assets/specifications/`.
