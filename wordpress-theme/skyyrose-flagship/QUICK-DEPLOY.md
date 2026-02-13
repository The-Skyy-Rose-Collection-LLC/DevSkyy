# SkyyRose Flagship - Quick Deployment Guide

**Status**: Ready for deployment
**Package**: `~/Desktop/skyyrose-flagship-2.0.0-wpcom.zip` (176KB)
**Target**: https://www.skyyrose.co
**Credentials**: Available (Client ID: 123138)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Login to WordPress.com
```
URL: https://wordpress.com/
Site: skyyrose.co
```

### Step 2: Upload Theme (2 minutes)
1. Go to: **Appearance > Themes**
2. Click: **Add New Theme** (top right)
3. Click: **Upload Theme**
4. Drag and drop: `~/Desktop/skyyrose-flagship-2.0.0-wpcom.zip`
5. Click: **Install Now**
6. Wait for "Theme installed successfully" message
7. Click: **Activate**

### Step 3: Set Homepage (1 minute)
1. Go to: **Pages > All Pages**
2. Edit the **Homepage** page (or create one if it doesn't exist)
3. In **Page Attributes** sidebar:
   - Template: Select **"Luxury Homepage"**
4. Click: **Update**

5. Go to: **Settings > Reading**
6. Under "Your homepage displays":
   - Select: **A static page**
   - Homepage: Select **Homepage**
7. Click: **Save Changes**

### Step 4: Clear Cache (30 seconds)
1. Go to: **Jetpack > Settings**
2. Find: **Performance & Speed**
3. Click: **Clear all caches**
4. Wait 2 minutes

### Step 5: Verify (1 minute)
Open new incognito window and visit: https://www.skyyrose.co

**Check for**:
- Rose gold gradient hero section
- "Where Love Meets Luxury" heading
- 3 collection cards (Signature, Love Hurts, Black Rose)
- No errors in browser console (F12)

---

## ✅ Automated Verification

Run this command to verify deployment:

```bash
cd /Users/coreyfoster/Documents/GitHub/DevSkyy/wordpress-theme/skyyrose-flagship
./verify-deployment.sh
```

**Expected Output**:
```
✓ Site is accessible (HTTP 200)
✓ brand-variables.css loads correctly
✓ luxury-theme.css loads correctly
✓ collection-colors.css loads correctly
✓ custom.css loads correctly
✓ Rose Gold color (#B76E79) found in page source
✓ Playfair Display font referenced
✓ SkyyRose Flagship theme detected
```

---

## 🎨 Available Page Templates

After deployment, these templates will be available in **Page Attributes > Template**:

1. **Luxury Homepage** - Main homepage with hero, collections showcase
2. **Signature Collection** - Rose gold luxury showcase
3. **Love Hurts Collection** - Crimson passion theme
4. **Black Rose Collection** - Dark elegance collection
5. **Preorder Gateway** - Pre-launch countdown and email capture
6. **About Us** - Complete about page with team, values, process
7. **Contact** - Contact form, FAQ, consultation booking

### How to Use Templates

1. Create or edit a page
2. Scroll to **Page Attributes** box (right sidebar)
3. Under **Template** dropdown, select desired template
4. Click **Update** or **Publish**

---

## 🔧 Troubleshooting

### Issue: CSS Not Loading (404 Errors)

**Solution**: Clear WordPress.com cache
```
Jetpack > Settings > Performance > Clear all caches
Wait 5 minutes, then hard refresh browser (Ctrl+Shift+R)
```

### Issue: Template Not in Dropdown

**Solution**: Refresh permalinks
```
Settings > Permalinks > Save Changes
Wait 2 minutes, then refresh page editor
```

### Issue: Old Theme Still Showing

**Solution**: Clear browser cache
```
Open incognito/private window
Or hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
```

---

## 📊 What's New in v2.0.0

### 🎨 Templates (9 new files)
- Luxury Homepage (340 lines)
- 3 Collection pages (434-462 lines each)
- Preorder Gateway (417 lines)
- About Us (395 lines)
- Contact (403 lines)
- WooCommerce templates (3 files)

### 🎨 CSS (600+ lines added)
- Homepage enhancements
- Collection-specific styles
- WooCommerce luxury styling
- 7 custom animations
- Responsive breakpoints

### 🛠️ Fixes
- ✅ WordPress.com CSS concatenation disabled
- ✅ MIME type errors resolved
- ✅ CSP headers added (pixel.wp.com, blob: URLs)
- ✅ All brand colors implemented

---

## 📞 Support

**Issues?** Run verification script:
```bash
./verify-deployment.sh
```

**Manual Checklist**: See `DEPLOYMENT-CHECKLIST.md`

**Rollback**: Reactivate previous theme from **Appearance > Themes**

---

**Package**: skyyrose-flagship-2.0.0-wpcom.zip
**Last Updated**: 2026-02-12
**Ralph Loop**: Iteration 1 Complete
