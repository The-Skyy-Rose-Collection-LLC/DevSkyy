# SkyyRose Deployment - Quick Start

**Estimated Time**: 5 days
**Current Status**: Phases 1-2 Complete, Phase 1.5 Ready

______________________________________________________________________

## 📊 Status at a Glance

| Phase | Name | Status | Time | Blocker |
|-------|------|--------|------|---------|
| 1 | Asset Extraction | ✅ Complete | 1h | None |
| 1.5 | 3D Model Generation | ⏳ Ready | 2-3h | Tripo API Key |
| 2 | Template Generation | ✅ Complete | 1h | None |
| 3 | WordPress Deploy | ⏳ Pending | 2h | WordPress Credentials |
| 4 | WooCommerce Config | ⏳ Pending | 3h | Phase 3 Complete |
| 5 | Testing & Launch | ⏳ Pending | 2h | Phases 3-4 Complete |

______________________________________________________________________

## 🚀 Quick Commands

### Phase 1.5: Generate 3D Models

```bash
# 1. Set API key
export TRIPO_API_KEY="your-key-from-tripo3d.ai"

# 2. Run generation
python3 scripts/generate_3d_models_from_assets.py

# 3. Check output
find assets/3d-models-generated -name "*.glb" | wc -l
```

### Phase 2: View Generated Templates

```bash
# Templates already generated in
ls wordpress/elementor_templates/

# Contents:
# - home.json (homepage)
# - black_rose.json (collection)
# - love_hurts.json (collection)
# - signature.json (collection)
# - about.json (about page)
# - blog.json (blog page)
```

### Phase 3: Deploy to WordPress

```bash
# 1. Get WordPress app password from admin panel
#    Settings → Application Passwords

# 2. Deploy
python3 scripts/extract_and_deploy_skyyrose.py \
  --wp-url "https://your-site.local" \
  --wp-username "admin" \
  --wp-app-password "xxxx-xxxx-xxxx-xxxx"

# 3. Verify in admin
#    Admin → Pages → Should see 5 new pages
```

### Phase 4: Create Products

```bash
# In WordPress Admin:
# 1. Products → Categories → Create 3 categories
#    - Black Rose
#    - Love Hurts
#    - Signature

# 2. Products → Add Product
#    - Name: "Heart Rose Bomber"
#    - Price: $299
#    - Category: Black Rose
#    - Upload 3D model (GLB + USDZ)
#    - Repeat for 8 more products

# 3. WooCommerce → Settings → Shipping
#    - Flat rate: $10 (under $150)
#    - Free shipping: $150+
```

### Phase 5: Test Everything

```bash
# Performance
curl "https://pagespeedonline.googleapis.com/..." \
  --url "https://your-site.com"

# Functionality
# 1. Add product to cart
# 2. Complete checkout
# 3. View 3D model on product page
# 4. Test AR (iOS)

# SEO
# 1. Check meta tags
# 2. Check schema.org markup
# 3. Check sitemap.xml
```

______________________________________________________________________

## 📁 Important Files

### Orchestration Scripts

```
scripts/
├── extract_and_deploy_skyyrose.py      # Main orchestrator
└── generate_3d_models_from_assets.py   # 3D generation
```

### Generated Assets

```
wordpress/elementor_templates/
├── home.json
├── black_rose.json
├── love_hurts.json
├── signature.json
├── about.json
└── blog.json

assets/3d-models-generated/          # Output (Phase 1.5)
├── black-rose/
├── love-hurts/
├── signature/
└── GENERATED_INVENTORY.json
```

### Documentation

```
docs/
├── SKYYROSE_DEPLOYMENT_GUIDE.md     # Full guide (you are here)
├── SKYYROSE_QUICK_START.md          # Quick reference
└── ...
```

______________________________________________________________________

## ⚡ Common Tasks

### Check Phase 1 Output

```bash
du -sh assets/3d-models/
# Should show ~361 MB

find assets/3d-models -type f | wc -l
# Should show 200+ files
```

### Check Phase 2 Output

```bash
ls -lh wordpress/elementor_templates/
# Should show 6 JSON files
# Each 50-100 KB
```

### Monitor Phase 1.5 Progress

```bash
# While running
python3 scripts/generate_3d_models_from_assets.py 2>&1 | tee generation.log

# Watch generation
tail -f generation.log | grep "Generating"
```

### Verify WordPress Connection

```bash
# Test connectivity
curl -I https://your-site.local/wp-json/

# Check response
# Should show: HTTP/1.1 200 OK
```

### Check WooCommerce Products

```bash
# Via WordPress admin
# Products → All Products

# Via REST API
curl -u admin:app_password https://your-site.local/wp-json/wc/v3/products
```

______________________________________________________________________

## 🔧 Troubleshooting Quick Fixes

### "API key not found" (Phase 1.5)

```bash
echo $TRIPO_API_KEY
# If empty: export TRIPO_API_KEY="your-key"
```

### "Connection refused" (Phase 3)

```bash
# Make sure WordPress is running
docker-compose up -d wordpress

# Wait for startup
sleep 10

# Test connection
curl -I https://localhost:8080
```

### "Invalid credentials" (Phase 3)

```bash
# Re-generate app password in WordPress admin
# Settings → Application Passwords → Delete old → Create new

# Copy exactly (no extra spaces)
export WORDPRESS_APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
```

### "3D models not displaying" (Phase 4)

```bash
# 1. Verify models uploaded to Media
# 2. Check WordPress has plugin: "Elementor Pro"
# 3. Check custom widget installed
# 4. Check browser console for errors
```

______________________________________________________________________

## 📋 Pre-Launch Checklist

### Before Phase 1.5

- [ ] Assets extracted to `assets/3d-models/` (Phase 1 complete)
- [ ] Tripo API key obtained from <https://tripo3d.ai/dashboard>
- [ ] API key set: `export TRIPO_API_KEY="..."`

### Before Phase 3

- [ ] WordPress site available at WORDPRESS_URL
- [ ] Admin user exists
- [ ] App password generated
- [ ] Elementor plugin installed
- [ ] WooCommerce plugin installed

### Before Phase 4

- [ ] Phase 3 deployment successful
- [ ] All 5 pages visible in WordPress admin
- [ ] Elementor templates loaded correctly

### Before Phase 5

- [ ] All 9+ products created
- [ ] 3D models attached to products
- [ ] Categories created and assigned
- [ ] Shipping rules configured

______________________________________________________________________

## 🎯 Next Immediate Steps

### Right Now (2 minutes)

1. Read full `docs/SKYYROSE_DEPLOYMENT_GUIDE.md`
1. Verify Phase 1 completed: `du -sh assets/3d-models/`

### Within 24 Hours (30 minutes)

1. Get Tripo API key from <https://tripo3d.ai/dashboard> (free tier OK)
1. Set environment variable: `export TRIPO_API_KEY="..."`
1. Run: `python3 scripts/generate_3d_models_from_assets.py`
1. Monitor progress and verify GENERATED_INVENTORY.json created

### Within 48 Hours (2 hours)

1. Get WordPress site running (local, staging, or production)
1. Generate app password in WordPress admin
1. Run: `python3 scripts/extract_and_deploy_skyyrose.py --wp-url ... --wp-username ... --wp-app-password ...`
1. Verify pages appear in WordPress admin

### Within 72 Hours (5 hours)

1. Create 9+ products in WooCommerce
1. Attach 3D models to product galleries
1. Configure shipping rules
1. Test add-to-cart flow

### Within 5 Days (2 hours)

1. Run performance tests (PageSpeed Insights)
1. Test functionality (checkout, 3D viewer, AR)
1. Validate SEO (meta tags, schema, sitemap)
1. Launch to production

______________________________________________________________________

## 📚 Reference

### Full Documentation

- **Main Guide**: `docs/SKYYROSE_DEPLOYMENT_GUIDE.md` (complete with troubleshooting)
- **Architecture**: `docs/DEVSKYY_MASTER_PLAN.md` (system design)
- **Project Config**: `CLAUDE.md` (development guidelines)

### Key Files

- **Elementor Templates**: `wordpress/elementor_templates/`
- **Extracted Assets**: `assets/3d-models/`
- **Specifications**: `assets/specifications/`
- **Generated Models**: `assets/3d-models-generated/` (after Phase 1.5)

### External Resources

- **Tripo3D Docs**: <https://docs.tripo3d.ai/>
- **Elementor Docs**: <https://elementor.com/docs/>
- **WooCommerce Docs**: <https://woocommerce.com/documentation/>
- **WordPress REST API**: <https://developer.wordpress.org/rest-api/>

______________________________________________________________________

## ✨ What's Already Done

✅ **Phase 1**: 361MB of product images extracted
✅ **Phase 2**: 6 Elementor templates generated

## ⏳ What's Next

⏳ **Phase 1.5**: Generate 160+ 3D models (requires Tripo API key)
⏳ **Phase 3**: Deploy to WordPress (requires WordPress credentials)
⏳ **Phase 4**: Create products and collections
⏳ **Phase 5**: Test and launch

______________________________________________________________________

**You are here**: Quick start guide ready
**What to do next**: Follow immediate steps above OR read full guide in `docs/SKYYROSE_DEPLOYMENT_GUIDE.md`
