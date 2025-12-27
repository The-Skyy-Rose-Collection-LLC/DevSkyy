# SkyyRose Deployment Quick Start Guide

**Quick deployment reference for the complete SkyyRose cinematic WordPress site**

---

## One-Command Deployment

```bash
python3 scripts/deploy_skyyrose_site.py \
    --assets-zip "/Users/coreyfoster/Desktop/updev 4.zip" \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --wordpress-password "your-admin-password" \
    --all \
    --verbose
```

---

## Prerequisites Checklist

- [ ] Extract `/Users/coreyfoster/Desktop/updev 4.zip` to `assets/3d-models/`
- [ ] WordPress instance running at target URL
- [ ] WordPress admin credentials available
- [ ] Python 3.11+ installed
- [ ] Install dependencies: `pip install -e .`
- [ ] Verify installation: See INSTALLATION_REQUIREMENTS.md
- [ ] All environment variables configured (see `.env.example`)
- [ ] API keys obtained:
  - [ ] HUGGINGFACE_API_KEY (free tier available)
  - [ ] TRIPO_API_KEY (paid, ~$0.50-1.00 per model)
  - [ ] WORDPRESS_APP_PASSWORD (generated in WordPress settings)

---

## 3D Generation Pipeline (Multi-Stage)

The deployment automatically executes a 4-stage 3D generation pipeline:

1. **Stage 1 (Image Optimization)**: PIL/OpenCV prepare images (1024×1024, transparent background)
2. **Stage 2 (HuggingFace Shap-E)**: Quick preview + optimization hints (2-5s per product, free)
3. **Stage 3 (Tripo3D)**: Production GLB/USDZ models (30-120s per product, ~$0.50-1.00 each)
4. **Stage 4 (WordPress Upload)**: Upload to media library and link to products

**Why Two 3D Services?**

- HuggingFace: Fast validation before expensive Tripo3D generation
- Tripo3D: Production-quality models with material enhancements

For details, see: `docs/3D_GENERATION_PIPELINE.md`

---

## Phase Execution

### Quick Summary (9 Phases)

1. **Phase 1**: Extract assets and generate 3D model metadata
2. **Phase 2**: Create 5 WordPress page builders
3. **Phase 3**: Register 14+ Elementor widgets
4. **Phase 4**: Configure 3D hotspot system
5. **Phase 5**: Setup pre-order/countdown system
6. **Phase 6**: Deploy spinning logo and animations
7. **Phase 7**: Import 16 press mentions
8. **Phase 8**: Configure deployment coordination
9. **Phase 9**: Run testing validation suite

### Individual Phase Deployment

```bash
# Deploy only Phase 1 (asset extraction)
python3 scripts/deploy_skyyrose_site.py \
    --assets-zip "/path/to/updev 4.zip" \
    --phase 1 \
    --verbose

# Deploy Phase 2 (page builders)
python3 scripts/deploy_skyyrose_site.py \
    --phase 2 \
    --wordpress-url "http://localhost:8882" \
    --wordpress-user "admin" \
    --verbose

# Skip to Phase 7 (press timeline)
python3 scripts/deploy_skyyrose_site.py \
    --phase 7 \
    --wordpress-url "http://localhost:8882" \
    --verbose
```

---

## Post-Deployment Verification

### Validate Performance

```bash
python3 scripts/verify_core_web_vitals.py \
    --site-url "http://localhost:8882" \
    --pages "home,product,collection,about" \
    --verbose
```

**Expected Results**:

- LCP < 2.5s ✓
- FID < 100ms ✓
- CLS < 0.1 ✓
- TTFB < 600ms ✓
- Mobile PageSpeed 90+ ✓

### Validate Functionality

```bash
python3 scripts/test_site_functionality.py \
    --site-url "http://localhost:8882" \
    --verbose
```

**Expected Results**:

- ✓ All 5 collection experiences load
- ✓ 3D hotspots are interactive
- ✓ Countdown timers sync
- ✓ Pre-order emails captured
- ✓ Spinning logo renders
- ✓ AR Quick Look works (iOS)

### Validate SEO

```bash
python3 scripts/verify_seo.py \
    --site-url "http://localhost:8882" \
    --verbose
```

**Expected Results**:

- RankMath Score: 90+ ✓
- Meta tags present ✓
- Schema markup configured ✓
- Mobile-friendly ✓
- Canonical URLs set ✓

---

## Collection-Specific Details

### Black Rose (Modern Luxury)

- **Colors**: Primary #000000, Accent #C0C0C0 (Silver)
- **Theme**: Dark elegance meets modern luxury
- **Products**: 5 models with 50-200K polygons
- **AR Support**: USDZ format for iOS
- **Hotspots**: 5 interactive 3D positions

### Love Hurts (Emotional)

- **Colors**: Primary #2D1B1F, Accent #B76E79 (Rose Gold)
- **Theme**: Raw emotion transformed into high fashion
- **Products**: 5 models (note: 1 large 21.87MB image)
- **AR Support**: USDZ format for iOS
- **Hotspots**: 5 interactive 3D positions

### Signature (Premium Essentials)

- **Colors**: Primary #0D0D0D, Accent #D4AF37 (Gold)
- **Theme**: Premium essentials built to last
- **Products**: 5 models with varied file sizes
- **AR Support**: USDZ format for iOS
- **Hotspots**: 5 interactive 3D positions

---

## Troubleshooting

### Issue: Pydantic Validation Error

**Solution**: Update Pydantic to v2.x

```bash
pip install --upgrade pydantic
```

### Issue: WordPress Connection Failed

**Solution**: Verify WordPress URL and credentials

```bash
# Test connection
curl -X GET "http://localhost:8882/wp-json/wp/v2/posts" \
  -H "Authorization: Bearer YOUR_APP_PASSWORD"
```

### Issue: Assets Not Found

**Solution**: Verify ZIP extraction

```bash
ls -la assets/3d-models/
# Should show: black-rose/ love-hurts/ signature/
```

### Issue: 3D Model Generation Timeout

**Solution**: Increase timeout and use limit

```bash
python3 scripts/deploy_skyyrose_site.py \
    --phase 3 \
    --limit 2 \
    --verbose
```

---

## Environment Variables

### Required

```bash
WORDPRESS_URL=http://localhost:8882
WORDPRESS_USER=admin
WORDPRESS_PASSWORD=your-password
```

### Optional (for features)

```bash
TRIPO_API_KEY=your-tripo-key       # For 3D generation
HUGGINGFACE_API_KEY=your-hf-key    # For preview generation
KLAVIYO_API_KEY=your-klaviyo-key   # For email capture
```

---

## Performance Expectations

### Deployment Duration

- Phase 1 (Assets): 2-5 minutes
- Phase 2-3 (WordPress): 3-5 minutes
- Phase 4-5 (Features): 5-10 minutes
- Phase 6-7 (Content): 2-3 minutes
- Phase 8-9 (Testing): 5-10 minutes

**Total**: 20-35 minutes for full deployment

### Resource Requirements

- **Disk Space**: 500MB (ZIP extraction + 3D models)
- **RAM**: 2GB minimum, 4GB+ recommended
- **Network**: Stable connection (API calls to WordPress, Tripo3D, HuggingFace)
- **CPU**: Multi-core recommended (async task execution)

---

## Success Checklist

Post-deployment verification:

- [ ] All 5 collection experiences load without errors
- [ ] 3D models display with correct colors and textures
- [ ] Hotspot cards appear on click
- [ ] Countdown timers sync with server time
- [ ] Pre-order form accepts email submissions
- [ ] Spinning logo rotates smoothly
- [ ] Press timeline displays all 16 mentions
- [ ] Core Web Vitals all pass targets
- [ ] SEO scores 90+ on all pages
- [ ] Mobile layout responsive and functional

---

## Next Steps

1. **Immediate**: Deploy using one-command above
2. **Post-Deploy**: Run verification scripts
3. **Testing**: Execute functionality and SEO tests
4. **Monitoring**: Watch error logs for 24 hours
5. **Optimization**: Fine-tune based on analytics

---

## Support Resources

- **Documentation**: See `docs/reports/SKYYROSE_IMPLEMENTATION_COMPLETE.md`
- **Architecture**: See `docs/architecture/DEVSKYY_MASTER_PLAN.md`
- **API Reference**: See `docs/api/ECOMMERCE_API.md`
- **Troubleshooting**: See `docs/runbooks/` directory

---

**Ready to Deploy?** Run the one-command above and follow the console output.

**Questions?** Check the full documentation in `docs/reports/SKYYROSE_IMPLEMENTATION_COMPLETE.md`

---

**Version**: 1.0.0
**Last Updated**: December 25, 2025
