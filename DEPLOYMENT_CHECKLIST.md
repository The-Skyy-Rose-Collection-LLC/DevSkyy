# SkyyRose Deployment Checklist

**Complete checklist for deploying the SkyyRose cinematic WordPress site**

---

## Pre-Deployment (1-2 Hours)

### Environment Setup
- [ ] Python 3.11 or 3.12 installed: `python3 --version`
- [ ] Repository cloned: `/Users/coreyfoster/DevSkyy`
- [ ] `.env` file created from `.env.example`
- [ ] All environment variables configured (see below)

### Dependencies Installation
- [ ] Install Python dependencies: `pip install -e .`
- [ ] Verify installation: `python3 << 'EOF' [see INSTALLATION_REQUIREMENTS.md]`
- [ ] Check Pydantic v2: `pip list | grep pydantic` (should show 2.5+)
- [ ] Check Pillow: `python3 -c "from PIL import Image; print('✓')"`
- [ ] Check OpenCV: `python3 -c "import cv2; print('✓')"`

### API Keys & Credentials
- [ ] **WordPress**
  - [ ] WordPress URL: `http://localhost:8882` (or production URL)
  - [ ] Admin username: `admin` (or your username)
  - [ ] App Password: Generate in WordPress Settings → Security → Application Passwords
    - [ ] Name: "SkyyRose Deployment"
    - [ ] Copy password to `.env` as `WORDPRESS_PASSWORD`

- [ ] **3D Generation APIs**
  - [ ] HuggingFace API Key: https://huggingface.co/settings/tokens
    - [ ] Create token with "read" scope
    - [ ] Copy to `.env` as `HUGGINGFACE_API_KEY`
  - [ ] Tripo3D API Key: https://www.tripo3d.ai/dashboard/key
    - [ ] Copy to `.env` as `TRIPO_API_KEY`
    - [ ] Check account has sufficient credits (~$5-10 recommended for 3 collections)

- [ ] **LLM Providers** (at least one required)
  - [ ] OpenAI: https://platform.openai.com/api-keys
  - [ ] Anthropic: https://console.anthropic.com/
  - [ ] Google: https://aistudio.google.com/app/apikey

### Assets Preparation
- [ ] Verify ZIP file: `/Users/coreyfoster/Desktop/updev 4.zip` exists
- [ ] Confirm ZIP contains 3 collection folders:
  - [ ] `black-rose/` (5 products, 0.62-1.28 MB)
  - [ ] `love-hurts/` (5 products, 0.6-21.87 MB)
  - [ ] `signature/` (5 products, 0.1-3.22 MB)

### WordPress Verification
- [ ] WordPress accessible: `curl http://localhost:8882` returns HTML
- [ ] WordPress API accessible: `curl http://localhost:8882/wp-json/wp/v2/posts`
- [ ] Admin login works: `http://localhost:8882/wp-admin`
- [ ] WooCommerce active (if using): Check Plugins page
- [ ] Elementor Pro active (if using): Check Plugins page
- [ ] Shoptimizer theme active (recommended): Check Appearance → Themes

---

## Deployment (20-35 Minutes)

### Phase 1: Asset Extraction (2-5 min)
```bash
python3 scripts/deploy_skyyrose_site.py \
    --assets-zip "/Users/coreyfoster/Desktop/updev 4.zip" \
    --phase 1 \
    --verbose
```

**Expected Output**:
```
✓ Extracting assets from ZIP...
✓ Found 15 product images (5 × 3 collections)
✓ Generated metadata for: black-rose, love-hurts, signature
✓ Phase 1 complete in 3.2 seconds
```

- [ ] Phase 1 succeeds without errors
- [ ] Check `generated_assets/` directory:
  - [ ] `black-rose_models_metadata.json` exists
  - [ ] `love-hurts_models_metadata.json` exists
  - [ ] `signature_models_metadata.json` exists

### Phase 2-3: WordPress Page Builders (3-5 min)
```bash
python3 scripts/deploy_skyyrose_site.py \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --wordpress-password "YOUR_APP_PASSWORD" \
    --phase 2 \
    --verbose
```

**Expected Output**:
```
✓ Creating home page builder...
✓ Creating product page builder...
✓ Creating collection experience builder...
✓ Creating about page builder...
✓ Creating blog page builder...
✓ Phase 2 complete in 2.4 seconds
```

- [ ] Phase 2-3 succeeds
- [ ] Check WordPress Pages:
  - [ ] Home page created
  - [ ] Sample product page created
  - [ ] Collection pages created

### Phase 4-6: Features (5-10 min)
```bash
python3 scripts/deploy_skyyrose_site.py \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --wordpress-password "YOUR_APP_PASSWORD" \
    --phase 4 \
    --verbose
```

**Expected Output**:
```
✓ Configuring hotspot system...
✓ Setting up pre-order/countdown...
✓ Deploying animations...
✓ Phase 4-6 complete in 6.3 seconds
```

- [ ] All feature phases complete

### Phase 7-9: Press, Deployment, Testing (5-10 min)
```bash
python3 scripts/deploy_skyyrose_site.py \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --wordpress-password "YOUR_APP_PASSWORD" \
    --phase 7 \
    --verbose
```

**Expected Output**:
```
✓ Importing press mentions...
✓ Configuring deployment agents...
✓ Running test validation...
✓ Phase 7-9 complete in 4.8 seconds
```

- [ ] All phases complete

### Full Deployment (All 9 Phases - 20-35 min)
```bash
python3 scripts/deploy_skyyrose_site.py \
    --assets-zip "/Users/coreyfoster/Desktop/updev 4.zip" \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --wordpress-password "YOUR_APP_PASSWORD" \
    --all \
    --verbose
```

- [ ] Deployment starts successfully
- [ ] All 9 phases execute without errors
- [ ] Final summary displays with success metrics

---

## Post-Deployment Verification (15-20 Minutes)

### Core Web Vitals Testing
```bash
python3 scripts/verify_core_web_vitals.py \
    --site-url "http://localhost:8882" \
    --pages "home,product,collection,about" \
    --verbose
```

**Expected Results**:
- [ ] Homepage LCP < 2.5s ✓
- [ ] FID < 100ms ✓
- [ ] CLS < 0.1 ✓
- [ ] TTFB < 600ms ✓
- [ ] Mobile PageSpeed 90+ ✓

### Functionality Testing
```bash
python3 scripts/test_site_functionality.py \
    --site-url "http://localhost:8882" \
    --verbose
```

**Expected Results**:
- [ ] ✓ All 5 collection experiences load
- [ ] ✓ 3D hotspots are interactive
- [ ] ✓ Countdown timers sync with server
- [ ] ✓ Pre-order emails captured
- [ ] ✓ Spinning logo renders
- [ ] ✓ AR Quick Look works (iOS)
- [ ] ✓ Search functionality works
- [ ] ✓ Navigation structure correct

### SEO Validation
```bash
python3 scripts/verify_seo.py \
    --site-url "http://localhost:8882" \
    --verbose
```

**Expected Results**:
- [ ] RankMath Score: 90+ on all pages
- [ ] Meta titles present on all pages
- [ ] Meta descriptions present on all pages
- [ ] Schema markup configured
- [ ] Mobile-friendly design ✓
- [ ] Canonical URLs set ✓
- [ ] Open Graph tags present ✓
- [ ] robots.txt configured ✓

### Manual Verification
- [ ] Visit homepage: http://localhost:8882
  - [ ] Spinning logo visible and rotating
  - [ ] Layout responsive on mobile
  - [ ] Featured collections displayed
- [ ] Visit collection page (e.g., Signature)
  - [ ] 3D viewer loads (Three.js)
  - [ ] Hotspots appear on click
  - [ ] Product cards show details
  - [ ] AR Quick Look button present (if on iOS)
- [ ] Visit product page
  - [ ] 3D model displays
  - [ ] Tabs work (Description, Sizing, Story, Pre-Order)
  - [ ] Countdown timer displays
  - [ ] Add to cart works
- [ ] Visit About page
  - [ ] Press timeline displays
  - [ ] Publication logos visible
  - [ ] Brand story present
- [ ] Check Blog page
  - [ ] Grid layout displays correctly
  - [ ] Search functionality works

---

## Optional Enhancements (Post-Deployment)

- [ ] **Performance Optimization**
  - [ ] Enable caching headers
  - [ ] Optimize images
  - [ ] Minify CSS/JS
  - [ ] Enable CDN

- [ ] **Analytics Setup**
  - [ ] Google Analytics 4
  - [ ] Hotjar for heatmaps
  - [ ] Segment for tracking
  - [ ] RankMath analytics

- [ ] **SEO Optimization**
  - [ ] Generate XML sitemap
  - [ ] Submit to Google Search Console
  - [ ] Configure robots.txt
  - [ ] Set up redirects

- [ ] **Monitoring**
  - [ ] Set up Prometheus metrics
  - [ ] Configure Grafana dashboards
  - [ ] Enable error tracking (Sentry)
  - [ ] Set up log aggregation

---

## Troubleshooting During Deployment

### Issue: Pydantic Validation Error
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated
```
**Solution**: Update Pydantic: `pip install --upgrade pydantic>=2.5`

### Issue: WordPress Connection Failed
```
ConnectionError: Failed to connect to http://localhost:8882
```
**Solution**: 
- Verify WordPress is running: `curl http://localhost:8882`
- Check WORDPRESS_URL in `.env`
- Verify WORDPRESS_PASSWORD is correct

### Issue: HuggingFace API Error
```
AuthenticationError: Invalid authentication token
```
**Solution**: 
- Verify HUGGINGFACE_API_KEY in `.env`
- Check token hasn't expired at huggingface.co/settings/tokens
- Ensure token has "read" scope

### Issue: Tripo3D Generation Timeout
```
TimeoutError: Tripo3D API did not respond within 120 seconds
```
**Solution**: 
- Tripo3D queue may be busy (try again in 5-10 min)
- Increase timeout: `--tripo-timeout 180`
- Check credits at tripo3d.ai dashboard

### Issue: Assets Not Found
```
FileNotFoundError: /Users/coreyfoster/Desktop/updev 4.zip not found
```
**Solution**: 
- Verify ZIP file path
- Ensure file isn't corrupted: `unzip -t "updev 4.zip"`
- Extract manually if needed: `unzip -q "updev 4.zip" -d ./assets/3d-models/`

---

## Post-Deployment Monitoring (24-48 Hours)

- [ ] **Day 1**: Monitor error logs every 2 hours
  - [ ] Check WordPress error logs
  - [ ] Review API response times
  - [ ] Monitor database performance
  - [ ] Check 3D model loading times

- [ ] **Day 2**: Collect baseline metrics
  - [ ] Record Core Web Vitals averages
  - [ ] Note conversion rates
  - [ ] Check crawl status in GSC
  - [ ] Review user behavior analytics

- [ ] **Week 1**: Ongoing monitoring
  - [ ] SEO rankings trending
  - [ ] API response times stable
  - [ ] No critical errors in logs
  - [ ] User engagement metrics healthy

---

## Success Criteria

✅ **Deployment Successful If**:
- All 9 phases execute without errors
- Core Web Vitals pass all thresholds
- Functionality tests pass (20+ test cases)
- SEO score 90+ on all pages
- All 5 collection experiences load
- 3D models visible and interactive
- Press timeline displays correctly
- No errors in WordPress/PHP logs

✅ **Fully Operational When**:
- Homepage loads in < 2.5s (LCP)
- Mobile PageSpeed 90+
- Users can add products to cart
- AR Quick Look works on iOS
- Emails captured for pre-orders
- Analytics tracking working

---

## Rollback Plan (If Needed)

If issues occur:

1. **Stop current deployment**: Press Ctrl+C
2. **Check logs**: `tail -f wp-content/debug.log`
3. **Revert changes**: 
   ```bash
   git status  # See what changed
   git checkout .  # Revert all changes
   ```
4. **Fix issue**: Resolve the problem, see Troubleshooting section
5. **Redeploy**: Run deployment script again

---

## After Deployment - Next Steps

1. **Configure Analytics**
   - Google Analytics 4
   - Hotjar heatmaps
   - RankMath analytics

2. **Setup Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Email alerts

3. **Optimize Performance**
   - Enable caching
   - Optimize images
   - Minify assets
   - Setup CDN

4. **Ongoing Maintenance**
   - Weekly backups
   - Monthly security audits
   - Quarterly content updates
   - Annual performance review

---

## Support Resources

- **Quick Start**: See `docs/SKYYROSE_DEPLOYMENT_QUICKSTART.md`
- **Complete Docs**: See `docs/reports/SKYYROSE_IMPLEMENTATION_COMPLETE.md`
- **3D Pipeline**: See `docs/3D_GENERATION_PIPELINE.md`
- **Installation**: See `INSTALLATION_REQUIREMENTS.md`
- **Work Summary**: See `WORK_COMPLETED_SUMMARY.md`

---

**Deployment Date**: _______________

**Deployed By**: _______________

**Notes**: 

---

**Good luck with your deployment!** 🚀

For any issues, refer to the Troubleshooting section or check the complete documentation files listed above.
