# WordPress Deployment Checklist

> **Quick reference for SkyyRose WordPress deployment**
> **Print this and check off as you go!**

---

## ☑️ PRE-DEPLOYMENT

### Theme Preparation
- [x] Theme version: 2.0.0
- [x] 35 PHP files verified
- [x] Security hardening active
- [x] Documentation complete
- [ ] Create production ZIP: `skyyrose-2025-production.zip`

### Backup Verification
- [ ] Database snapshot created
- [ ] Full file backup (wp-content)
- [ ] Backup integrity tested (restore test)
- [ ] Off-site backup copy (AWS S3)

---

## ☑️ CORE UPDATES (Do BEFORE deployment)

### Update Sequence (IN ORDER)
- [ ] **1. WordPress Core** (6.4 → 6.7.1)
  - Time: 10 min | Risk: Low
  - Post-check: Dashboard loads, REST API works

- [ ] **2. WooCommerce** (8.5 → 9.5.2)
  - Time: 15 min | Risk: Medium
  - ⚠️ CRITICAL: Test checkout flow!
  - Post-check: Shop, cart, checkout all work

- [ ] **3. Elementor** (3.18 → 3.25.4)
  - Time: 10 min | Risk: Low
  - ⚠️ Test custom SkyyRose widgets!
  - Post-check: Edit pages, widgets load

- [ ] **4. Other Plugins**
  - Time: 20 min | Risk: Low
  - Update one at a time
  - Test after each update

---

## ☑️ DEPLOYMENT

### Upload Theme
- [ ] Upload ZIP via Appearance → Themes → Upload
- [ ] Activate SkyyRose 2025 theme
- [ ] No fatal errors on activation
- [ ] Dashboard accessible

### WordPress Settings
- [ ] Settings → Reading → Static homepage
- [ ] Settings → Permalinks → Post name
- [ ] Appearance → Menus → Configure primary menu
- [ ] Appearance → Menus → Configure footer menu

---

## ☑️ CREATE PAGES (19 Total)

### Static Pages (6 pages)
- [ ] Home (`/`)
  - Template: Home Page
- [ ] About (`/about/`)
  - Template: About Page
- [ ] Contact (`/contact/`)
  - Template: Contact Page
- [ ] Privacy Policy (`/privacy-policy/`)
  - Template: Default Page
- [ ] Terms (`/terms/`)
  - Template: Default Page
- [ ] Returns (`/returns/`)
  - Template: Default Page

### Interactive Pages - 3D Immersive (3 pages)
- [ ] Black Rose Experience (`/black-rose-experience/`)
  - Template: Collection
  - Meta: `_collection_type = black-rose`
- [ ] Love Hurts Experience (`/love-hurts-experience/`)
  - Template: Collection
  - Meta: `_collection_type = love-hurts`
- [ ] Signature Experience (`/signature-experience/`)
  - Template: Collection
  - Meta: `_collection_type = signature`

### Catalog Pages - Shopping (3 pages)
- [ ] Black Rose Catalog (`/collection-black-rose/`)
  - Template: Collection - Black Rose
  - Slug: `collection-black-rose`
- [ ] Love Hurts Catalog (`/collection-love-hurts/`)
  - Template: Collection - Love Hurts
  - Slug: `collection-love-hurts`
- [ ] Signature Catalog (`/collection-signature/`)
  - Template: Collection - Signature
  - Slug: `collection-signature`

### WooCommerce Pages (Auto-created, verify existence)
- [ ] Shop (`/shop/`)
- [ ] Cart (`/cart/`)
- [ ] Checkout (`/checkout/`)
- [ ] My Account (`/my-account/`)

---

## ☑️ CONFIGURE WOOCOMMERCE

### Product Categories
- [ ] Create: Black Rose Collection
- [ ] Create: Love Hurts Collection
- [ ] Create: Signature Collection

### Add Products
- [ ] Add products to each collection
- [ ] Set `_skyyrose_collection` meta field
  - Values: `black-rose`, `love-hurts`, `signature`
- [ ] Upload product images
- [ ] Set pricing

### Payment Gateway
- [ ] Configure Stripe/PayPal
- [ ] Test mode enabled
- [ ] Test transaction

---

## ☑️ PAGE FUNCTIONALITY TESTS

### Static Pages (6 pages)
- [ ] Home loads (200 status)
- [ ] About loads
- [ ] Contact form submits
- [ ] Privacy Policy accessible
- [ ] Terms accessible
- [ ] Returns accessible

### Interactive Pages (3 pages)
- [ ] Black Rose 3D scene loads
  - [ ] Gothic cathedral renders
  - [ ] Rose petal particles animate
  - [ ] No console errors
- [ ] Love Hurts 3D scene loads
  - [ ] Romantic castle renders
  - [ ] Heart particles animate
  - [ ] No console errors
- [ ] Signature 3D scene loads
  - [ ] Oakland/SF cityscape renders
  - [ ] Golden hour lighting works
  - [ ] No console errors

### Catalog Pages (3 pages)
- [ ] Black Rose Catalog
  - [ ] Product grid displays
  - [ ] Filters work (category)
  - [ ] Add to cart functions
- [ ] Love Hurts Catalog
  - [ ] Product grid displays
  - [ ] Filters work
  - [ ] Add to cart functions
- [ ] Signature Catalog
  - [ ] Product grid displays
  - [ ] Filters work
  - [ ] Add to cart functions

### WooCommerce Pages (4 pages)
- [ ] Shop page displays products
- [ ] Single product page
  - [ ] 3D viewer loads (if available)
  - [ ] Add to cart works
- [ ] Cart page
  - [ ] Products display
  - [ ] Quantity adjust works
  - [ ] Coupon code works
- [ ] Checkout page
  - [ ] Form displays
  - [ ] Payment gateway loads
  - [ ] **TEST TRANSACTION** (test mode)

---

## ☑️ CRITICAL USER FLOWS

### Flow 1: Immersive to Purchase
- [ ] Visit Black Rose Experience
- [ ] Explore 3D scene
- [ ] Click product hotspot
- [ ] Redirected to product page
- [ ] View 3D product viewer
- [ ] Add to cart
- [ ] Complete checkout

### Flow 2: Catalog Shopping
- [ ] Visit Love Hurts Catalog
- [ ] See product grid
- [ ] Filter by "Dresses"
- [ ] Click product card
- [ ] Go to product page
- [ ] Add to cart
- [ ] Complete checkout

### Flow 3: Pre-Order
- [ ] Visit product with pre-order
- [ ] See "Pre-Order" badge
- [ ] Click "Pre-Order Now"
- [ ] Fill form (name, email, size)
- [ ] Submit form
- [ ] Receive confirmation email

---

## ☑️ TECHNICAL CHECKS

### CDN Assets
- [ ] Three.js loads (check console)
- [ ] Babylon.js loads
- [ ] GSAP loads
- [ ] Google Fonts load

### Security Headers
- [ ] Visit securityheaders.com
- [ ] Enter site URL
- [ ] Verify A+ grade
- [ ] Check HTTPS enforced

### Performance
- [ ] Run Lighthouse audit
- [ ] Score: 90+ (target)
- [ ] Core Web Vitals: Green
- [ ] Mobile responsive (320px - 2560px)

### Links
- [ ] No 404 errors
- [ ] All navigation links work
- [ ] Footer links work
- [ ] Product links work
- [ ] CDN assets accessible

---

## ☑️ POST-DEPLOYMENT MONITORING

### Immediate (0-2 hours)
- [ ] No fatal errors in `/wp-content/debug.log`
- [ ] Homepage loads for visitors
- [ ] Shop page accessible
- [ ] Checkout completes

### 24 Hours
- [ ] Monitor error logs
- [ ] Check analytics (traffic)
- [ ] Test checkout on mobile
- [ ] Verify email notifications

### 48 Hours
- [ ] Full page audit (all 19 pages)
- [ ] Performance review
- [ ] Security scan
- [ ] User feedback collection

---

## ☑️ AUTOMATED CHECKS

### Run Health Check Script
```bash
python3 scripts/wordpress_health_check.py --site https://skyyrose.co --output health-report.json
```

### Review Output
- [ ] All pages return 200
- [ ] No critical issues
- [ ] CDN assets accessible
- [ ] Load times < 3 seconds

---

## ☑️ ROLLBACK PLAN (If Issues)

### Minor Issues (site still works)
- [ ] Deactivate last plugin updated
- [ ] Check error log
- [ ] Fix and re-enable

### Major Issues (site broken)
- [ ] Switch to default WordPress theme
- [ ] Restore database from backup
- [ ] Restore files from backup
- [ ] Contact hosting support

---

## ☑️ FINAL SIGN-OFF

### Deployment Complete
- [ ] All 19 pages created and verified
- [ ] Checkout flow tested end-to-end
- [ ] 3D scenes render correctly
- [ ] No console errors
- [ ] Security headers active
- [ ] Performance targets met (90+)
- [ ] Error logs clean

### Monitoring Active
- [ ] Google Analytics tracking
- [ ] Error log monitoring
- [ ] Uptime monitoring (99.9%)
- [ ] Backup schedule confirmed

---

**Deployed By:** _____________________
**Date:** _____________________
**Sign-Off:** _____________________

---

## 📞 EMERGENCY CONTACTS

- **Developer:** dev@skyyrose.co
- **Support:** support.skyyrose.co
- **Hosting:** (hosting provider contact)

---

**✅ DEPLOYMENT COMPLETE**
