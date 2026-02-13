# SkyyRose Flagship Theme - WordPress.com Deployment Checklist

**Package**: `skyyrose-flagship-2.0.0-wpcom.zip` (176KB)
**Location**: `/Users/coreyfoster/Desktop/`
**Target Site**: https://www.skyyrose.co
**Deployment Date**: 2026-02-12

---

## ✅ Pre-Deployment Verification (COMPLETE)

- [x] Theme package created (176KB)
- [x] All 10 templates included
- [x] Custom CSS expanded (600+ lines)
- [x] PHP syntax validated (all files pass)
- [x] Git committed and pushed (commit 05b90e1d)
- [x] Documentation complete (DEPLOYMENT-INSTRUCTIONS.md, RALPH-LOOP-STATUS.md)
- [x] SHA256 checksum generated

---

## 🚀 Deployment Steps (ACTION REQUIRED)

### Step 1: Access WordPress.com Admin
1. Open browser to: https://wordpress.com/
2. Log in with WordPress.com credentials
3. Select **SkyyRose** site from dashboard
4. Verify you're on the **Business Plan** (required for custom themes)

### Step 2: Backup Current Theme (Safety)
1. Go to: **Appearance > Themes**
2. Note current active theme name: ________________
3. Download current theme as backup (if possible)
4. Screenshot current theme settings

### Step 3: Upload New Theme Package
1. Navigate to: **Appearance > Themes**
2. Click: **Add New Theme** (top right corner)
3. Click: **Upload Theme** button
4. Click: **Choose File**
5. Select: `/Users/coreyfoster/Desktop/skyyrose-flagship-2.0.0-wpcom.zip`
6. Click: **Install Now**
7. Wait for upload progress bar to complete (176KB should take 5-10 seconds)

**Expected Response**: "Theme installed successfully"

### Step 4: Activate Theme
1. After installation completes, click: **Activate**
2. Confirm activation when prompted
3. Wait for page to refresh

**Expected Response**: You'll see "SkyyRose Flagship" as the active theme

### Step 5: Configure Homepage Template
1. Navigate to: **Pages > All Pages**
2. Find or create page titled: **Homepage** or **Home**
3. Click **Edit** on that page
4. In right sidebar, find **Page Attributes** box
5. Under **Template** dropdown, select: **Luxury Homepage**
6. Click: **Update** to save

### Step 6: Set Static Front Page
1. Navigate to: **Settings > Reading**
2. Under **Your homepage displays**:
   - Select radio button: **A static page**
   - **Homepage** dropdown: Select your **Homepage** page
   - **Posts page** dropdown: Select or create a **Blog** page (optional)
3. Click: **Save Changes**

### Step 7: Clear All Caches
1. Navigate to: **Jetpack > Settings**
2. Find: **Performance & Speed** section
3. Click: **Clear all caches**
4. Wait 2-3 minutes for cache to clear
5. Alternatively, go to: **Tools > Clear Cache** (if available)

### Step 8: Verify Theme Activation
1. Open new incognito/private browser window
2. Navigate to: https://www.skyyrose.co
3. Perform initial visual check (see Step 9)

---

## 🔍 Step 9: Visual Verification Checklist

### Homepage Verification
- [ ] Page loads without errors (check browser console: F12)
- [ ] Hero section displays with gradient background
- [ ] Heading "Where Love Meets Luxury" visible in Playfair Display font
- [ ] Rose Gold brand color (#B76E79) visible in accents
- [ ] Collections showcase displays 3 cards (Signature, Love Hurts, Black Rose)
- [ ] All images load (or placeholders display properly)
- [ ] "Explore Collections" and "Shop Now" buttons visible
- [ ] About section displays
- [ ] Features grid shows 4 cards
- [ ] Footer displays correctly

### CSS Loading Verification
1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Filter by **CSS**
4. Refresh page (Ctrl+Shift+R or Cmd+Shift+R)
5. Verify these files load with **200 status**:
   - [ ] brand-variables.css
   - [ ] luxury-theme.css
   - [ ] collection-colors.css
   - [ ] custom.css
6. **NO 404 errors** should appear
7. **NO MIME type errors** in console

### JavaScript Console Checks
1. Open browser console (F12 > Console tab)
2. Refresh page
3. Verify:
   - [ ] **NO** "Refused to apply style" errors (MIME type)
   - [ ] **NO** 404 errors for CSS files
   - [ ] **NO** CSP violation errors for pixel.wp.com
   - [ ] **NO** blob: URL violations
   - [ ] Only expected WordPress.com analytics scripts load

### Typography Check
- [ ] Headings use **Playfair Display** (serif, elegant)
- [ ] Body text uses **Montserrat** (sans-serif, modern)
- [ ] Font sizes follow hierarchy (h1 larger than h2, etc.)
- [ ] Line heights comfortable for reading

### Mobile Responsive Check
1. Use Chrome DevTools mobile emulation (F12 > Toggle device toolbar)
2. Test these viewports:
   - [ ] Mobile (375px): iPhone SE
   - [ ] Tablet (768px): iPad
   - [ ] Desktop (1440px): Laptop
3. Verify:
   - [ ] Collections stack vertically on mobile
   - [ ] Buttons remain clickable (not too small)
   - [ ] Text remains readable
   - [ ] No horizontal scrolling

---

## 🎨 Step 10: Test New Page Templates

### Collection Pages
1. Create or navigate to: **Signature Collection** page
2. In Page Attributes, select template: **Signature Collection**
3. Click **Update** and preview
4. Verify:
   - [ ] Rose gold + gold theme displays
   - [ ] Product grid shows (WooCommerce products or placeholders)
   - [ ] 3D viewer placeholder displays
   - [ ] Statistics section shows (18k, GIA, ∞)

5. Repeat for **Love Hurts Collection** page
   - [ ] Crimson + rose gold theme
   - [ ] Animated particles background
   - [ ] Passionate quotes display

6. Repeat for **Black Rose Collection** page
   - [ ] Dark theme (black + silver)
   - [ ] Gothic styling
   - [ ] Smoke effects

### About Page
1. Create or navigate to: **About** page
2. Select template: **About Us**
3. Verify:
   - [ ] Brand story displays
   - [ ] Values grid shows 6 cards
   - [ ] Process timeline visible (5 steps)
   - [ ] Team section shows 3 members
   - [ ] Statistics section displays

### Contact Page
1. Create or navigate to: **Contact** page
2. Select template: **Contact**
3. Verify:
   - [ ] Contact options grid (4 methods)
   - [ ] Contact form displays all fields
   - [ ] Form has nonce security (view page source, search for "nonce")
   - [ ] FAQ section shows 6 questions
   - [ ] Submit button functional

### WooCommerce Pages (if WooCommerce active)
1. Navigate to: **Shop** page
2. Verify:
   - [ ] Products display in luxury cards
   - [ ] Hover animations work (image zoom, card lift)
   - [ ] Rose gold badges on sale items
   - [ ] Pagination displays

3. Click on any product
4. Verify single product page:
   - [ ] Two-column layout (image left, details right)
   - [ ] Price in rose gold color
   - [ ] Add to cart button gradient
   - [ ] Product tabs display (Description, Reviews, etc.)

---

## 🐛 Step 11: Troubleshooting Common Issues

### Issue: CSS Files Still Not Loading (404 Errors)

**Diagnosis**:
```bash
# In browser console, you see:
# GET https://skyyrose.co/wp-content/themes/skyyrose-flagship/assets/css/brand-variables.css 404
```

**Solution 1**: Verify theme files uploaded
1. Go to: **Appearance > Theme File Editor**
2. Select: **SkyyRose Flagship**
3. Check if `assets/css/brand-variables.css` exists in file tree
4. If missing, re-upload theme package

**Solution 2**: Clear WordPress.com cache (CRITICAL)
1. Go to: **Jetpack > Settings > Performance**
2. Click: **Clear all caches**
3. Wait 5 minutes (WordPress.com caches aggressively)
4. Hard refresh browser (Ctrl+Shift+R)

**Solution 3**: Check file permissions
1. WordPress.com should auto-set permissions
2. If issues persist, contact WordPress.com support

### Issue: Still Seeing Old Theme Content

**Diagnosis**: Browser or CDN cache

**Solution**:
1. Hard refresh browser: **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)
2. Clear browser cache completely
3. Try incognito/private browsing mode
4. Test from different device/network
5. Check if WordPress.com CDN cache cleared (wait 10-15 minutes)

### Issue: MIME Type Errors Still Appearing

**Diagnosis**:
```bash
# Console shows:
# Refused to apply style from '...' because MIME type ('text/html') is not a supported stylesheet MIME type
```

**Solution**: Verify concatenation is disabled
1. Go to: **Appearance > Theme File Editor**
2. Open: `functions.php`
3. Search for: `CONCATENATE_SCRIPTS`
4. Verify these lines exist:
```php
define( 'CONCATENATE_SCRIPTS', false );
$GLOBALS['concatenate_scripts'] = false;
add_filter( 'js_do_concat', '__return_false', 999 );
add_filter( 'css_do_concat', '__return_false', 999 );
```
5. If missing, theme package was corrupted - re-upload

### Issue: CSP Violations for pixel.wp.com

**Diagnosis**:
```bash
# Console shows:
# Refused to connect to 'https://pixel.wp.com' because it violates CSP
```

**Solution**: Verify CSP headers added
1. Open browser DevTools > Network tab
2. Refresh page
3. Click on main document request
4. Check **Response Headers** for `Content-Security-Policy`
5. Should include: `connect-src 'self' ... https://pixel.wp.com`
6. If missing, verify `functions.php` has `skyyrose_add_csp_headers()` function

### Issue: Placeholder Images Display Instead of Real Products

**This is EXPECTED** - Next Steps:
1. Upload real jewelry photos to Media Library
2. Edit each page to replace placeholder URLs
3. Or add WooCommerce products with real images
4. Placeholders confirm templates are working correctly

### Issue: Template Not Available in Dropdown

**Diagnosis**: Template not recognized by WordPress

**Solution**:
1. Verify template file has correct header:
```php
/**
 * Template Name: Luxury Homepage
 */
```
2. Check file is in theme root (not in subfolder)
3. Refresh WordPress permalinks: **Settings > Permalinks > Save Changes**
4. Wait 2-3 minutes for WordPress.com to detect new template

---

## 📊 Step 12: Performance Verification

### Core Web Vitals Check
1. Go to: https://pagespeed.web.dev/
2. Enter: https://www.skyyrose.co
3. Click: **Analyze**
4. Target scores:
   - [ ] Performance: 85+ (mobile), 90+ (desktop)
   - [ ] Accessibility: 95+
   - [ ] Best Practices: 90+
   - [ ] SEO: 95+

### Lighthouse Audit (Built-in)
1. Open Chrome DevTools (F12)
2. Go to **Lighthouse** tab
3. Select: **Mobile** or **Desktop**
4. Click: **Generate Report**
5. Review:
   - [ ] First Contentful Paint (FCP): < 1.8s
   - [ ] Largest Contentful Paint (LCP): < 2.5s
   - [ ] Cumulative Layout Shift (CLS): < 0.1
   - [ ] Total Blocking Time (TBT): < 200ms

### GTmetrix Test (Optional)
1. Go to: https://gtmetrix.com/
2. Enter: https://www.skyyrose.co
3. Click: **Test your site**
4. Review:
   - [ ] Grade: A or B
   - [ ] Fully loaded time: < 3s
   - [ ] Total page size: < 2MB

---

## ✅ Step 13: Final Acceptance Criteria

### All Must Pass:
- [ ] Homepage loads without errors
- [ ] All 4 CSS files load with 200 status (brand-variables, luxury-theme, collection-colors, custom)
- [ ] No MIME type errors in console
- [ ] No CSP violations for pixel.wp.com or blob: URLs
- [ ] Rose Gold brand color (#B76E79) displays correctly
- [ ] Playfair Display font loads for headings
- [ ] Montserrat font loads for body text
- [ ] Collections showcase displays 3 cards
- [ ] Mobile responsive works (test on phone)
- [ ] All 6 new templates available in Page Attributes dropdown
- [ ] Contact form submits without errors
- [ ] WooCommerce product pages display luxury styling (if WooCommerce active)

### Optional Enhancements (Post-Launch):
- [ ] Replace all placeholder images with real jewelry photos
- [ ] Update collection page URLs in homepage links
- [ ] Add real WooCommerce products
- [ ] Configure Google Analytics
- [ ] Set up email notifications for contact form
- [ ] Add SSL certificate (should auto-provision on WordPress.com)

---

## 📝 Post-Deployment Notes

### Record Results Here:
- **Deployment Date**: ________________
- **Deployed By**: ________________
- **Active Theme**: SkyyRose Flagship v2.0.0
- **All Checks Passed**: Yes / No
- **Issues Found**: ________________
- **Resolution Status**: ________________

### Screenshot Evidence:
1. Take screenshot of: Homepage (full page)
2. Take screenshot of: Browser console (showing no errors)
3. Take screenshot of: Network tab (showing CSS files with 200 status)
4. Take screenshot of: Themes page (showing active theme)
5. Save all screenshots to: `/Users/coreyfoster/Desktop/deployment-verification-YYYY-MM-DD/`

---

## 🔄 Rollback Plan (If Needed)

If critical issues occur and you need to revert:

1. Go to: **Appearance > Themes**
2. Find previous theme (note name from Step 2)
3. Click: **Activate** on old theme
4. Verify site returns to working state
5. Document issue in RALPH-LOOP-STATUS.md
6. Open Issue #__ in GitHub for iteration 2 fixes

---

## 📞 Support Contacts

**WordPress.com Support**:
- Chat: Available in WP Admin dashboard
- Email: support@wordpress.com
- Documentation: https://wordpress.com/support/

**Theme Support**:
- GitHub Issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- Internal: Document issues in RALPH-LOOP-STATUS.md for next iteration

---

**Checklist Version**: 1.0
**Last Updated**: 2026-02-12
**Ralph Loop Iteration**: 1
**Package**: skyyrose-flagship-2.0.0-wpcom.zip (176KB)
