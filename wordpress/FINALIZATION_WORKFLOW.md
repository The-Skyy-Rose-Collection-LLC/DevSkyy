# WordPress Finalization Workflow
**Status**: Ready to Complete | **Time**: ~25-30 minutes | **Complexity**: Medium

---

## ✅ What's Done
- ✅ 8 production pages created with proper hierarchy
- ✅ All pages live and accessible
- ✅ Shortcodes registered (3D viewer, virtual try-on, collections)
- ✅ WooCommerce categories linked (19, 20, 18)

---

## 🎯 What's Remaining (3 Steps)

### Step A: Import Elementor Templates (10 min) ⚡ HIGHEST IMPACT
**Purpose**: Add professional visual design to blank pages

**7 Templates Ready**:
- `home.json` → Home page (spinning logo, collections grid, newsletter)
- `signature.json` → Signature collection experience
- `black_rose.json` → Black Rose collection experience
- `love_hurts.json` → Love Hurts collection experience
- `about.json` → About SkyyRose story
- `collections.json` → Collections overview (fallback)
- `blog.json` → Blog template (optional)

**How to Import** (WordPress Admin):
```
1. Log in: https://skyyrose.co/wp-admin/
2. Elementor → My Library → Import Templates
3. For each page:
   a. Go to page (Edit with Elementor)
   b. Click "Elementor" menu (top left)
   c. Select "Import Template"
   d. Choose matching JSON file
   e. Click "Import"
   f. Review → Publish

4. Expected order:
   - Home (import home.json)
   - Experiences (skip template - keep parent page minimal)
   - Signature (import signature.json)
   - Black Rose (import black_rose.json)
   - Love Hurts (import love_hurts.json)
   - Shop (configure in next section)
   - About (import about.json)
   - Contact (keep form-based template)
```

**Template Features**:
- ✨ Hero sections with collection branding
- 🎨 Color-coded by collection (rose gold, cosmic black, crimson)
- 📱 Mobile-responsive layouts
- 🔗 Shortcodes pre-configured
- 🛍️ Product grids linked to categories
- ⭐ Call-to-action buttons

**Troubleshooting**:
- **Import fails**: Try downloading JSON locally, then upload via Elementor UI
- **Layout breaks**: Check Elementor version (Pro 3.32.2+ required)
- **Shortcodes not rendering**: Verify SkyyRose plugin activated (wordpress/skyyrose_plugin.php)

---

### Step B: Upload 3D Models (3 min) ⚙️ CORE FUNCTIONALITY
**Purpose**: Enable immersive 3D experiences on collection pages

**27 GLB Files Ready**:
- Signature: 16 models
- Black Rose: 11 models
- Love Hurts: 0 (pending Tripo3D credits)

**Option B1: Auto-Upload via Script** (Fastest)
```bash
# Prerequisites: SFTP credentials configured
# Check .env for: SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD

# Upload all models
python3 scripts/upload_3d_to_wordpress.py

# Upload specific collection only
python3 scripts/upload_3d_to_wordpress.py --collection signature
python3 scripts/upload_3d_to_wordpress.py --collection black-rose

# Dry-run first (safe)
python3 scripts/upload_3d_to_wordpress.py --dry-run
```

**Option B2: Manual Upload** (If SFTP not configured)
```
1. Download 3D files from: src/collections/{signature,black-rose,love-hurts}/models/
2. WordPress Admin → Media → Add New
3. Upload GLB files (max 50MB each per .env)
4. Copy file URLs → Use in [skyyrose_3d_viewer] shortcodes
```

**Option B3: Direct URL in Shortcodes** (Fastest, no upload needed)
Models already hosted on GitHub. Shortcodes reference them directly:
```
[skyyrose_collection_experience collection="signature" enable_ar="true"]
↓
Automatically loads 16 GLB files from GitHub + caches locally
```

**Verification**:
After import, visit:
- https://skyyrose.co/experiences/signature/ → Should render 3D viewer
- https://skyyrose.co/experiences/black-rose/ → Should render 3D viewer

---

### Step C: Configure Navigation Menus (5 min) 🧭 USER EXPERIENCE
**Purpose**: Enable site navigation between pages

**Menu Structure**:
```
Main Menu
├── Home
├── Experiences
│   ├── Signature Collection
│   ├── Black Rose Collection
│   └── Love Hurts Collection
├── Shop
├── About
└── Contact

Footer Menu
├── About
├── Contact
└── Privacy Policy (optional)
```

**How to Create** (WordPress Admin):
```
1. Go to: Appearance → Menus
2. Create new menu: "Main Menu"
3. Add pages:
   - Home (select in dropdown)
   - Experiences (select → check "Display as dropdown menu")
   - Shop
   - About
   - Contact
4. Assign menu:
   - Display location → "Primary Menu"
5. Create second menu "Footer Menu" (repeat steps 2-5)
6. Assign to → "Footer Menu" location

7. Test navigation at: https://skyyrose.co/
```

**Mobile Menu** (Shoptimizer theme):
- Automatically collapses to hamburger menu on mobile
- No extra configuration needed
- Test on iPhone/Android

---

## 🚀 Execution Plan

### Quick Path (15-20 min, mostly manual):
```
1. ✅ Import 6 Elementor templates (WordPress admin) — 8 min
2. ✅ Verify 3D models load automatically (no upload needed) — 2 min
3. ✅ Create Main Menu + Footer Menu (WordPress admin) — 5 min
4. ✅ Test all pages & navigation — 5 min
```

### Full Automation Path (5 min, requires SFTP):
```
1. ✅ Run: python3 scripts/upload_3d_to_wordpress.py --dry-run
2. ✅ Run: python3 scripts/upload_3d_to_wordpress.py (if SFTP ready)
3. ✅ Manually import Elementor templates (5 min)
4. ✅ Manually create menus (5 min)
```

---

## 📋 Verification Checklist

After completing all steps:

- [ ] **Pages Load**: All 8 URLs return HTTP 200
- [ ] **Templates Applied**: Home has logo + collections grid
- [ ] **3D Viewer Works**: Visit `/experiences/signature/` → See 3D model
- [ ] **Navigation Menu**: Click Home → Experiences → Signature (follows hierarchy)
- [ ] **Mobile Responsive**: Test on iPhone (menu collapses, layout adapts)
- [ ] **SEO Elements**: Title tags visible in browser tab for each page
- [ ] **Images Load**: Hero images, product thumbnails appear
- [ ] **Forms Work**: Contact form functional

---

## 🎯 Final State

After completing this workflow:

```
✅ WordPress Site Status: PRODUCTION READY

Frontend:
  ✅ 8 pages live with professional Elementor design
  ✅ 3D models embedded in collection experiences
  ✅ Navigation menus fully configured
  ✅ Mobile-responsive layouts
  ✅ Brand colors & imagery consistent

Backend:
  ✅ WooCommerce integrated (27 products ready)
  ✅ Shortcodes functional (3D viewer, virtual try-on)
  ✅ SSL/HTTPS secured
  ✅ Performance optimized (Shoptimizer + caching)

Ready for:
  ✅ Product catalog launch
  ✅ Marketing campaigns
  ✅ Social media links
  ✅ Customer sales
```

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| Elementor templates won't import | Ensure Elementor Pro 3.32.2+ installed. Try manual re-download of JSON |
| 3D models show 404 | GitHub CDN may be slow. Refresh page, clear browser cache |
| Menu items don't appear | Verify menu assigned to "Primary Menu" location in Appearance → Menus |
| Mobile looks broken | Disable page caching in Settings, hard refresh (Cmd+Shift+R) |
| Shortcodes showing as text | Activate SkyyRose plugin in Plugins menu |

---

## 🔗 Quick Links

**WordPress Admin**: https://skyyrose.co/wp-admin/
**Site Frontend**: https://skyyrose.co/

**Key Admin Pages**:
- Elementor Templates: /wp-admin/edit.php?post_type=elementor_library
- Menus: /wp-admin/nav-menus.php
- Settings: /wp-admin/options-general.php
- WooCommerce: /wp-admin/admin.php?page=wc-admin

---

## ⏱️ Time Estimates

| Step | Manual | Automated |
|------|--------|-----------|
| A: Import Templates | 10 min | - (manual required) |
| B: Upload 3D Models | 5 min (script) or 20 min (manual) | 3 min (SFTP) |
| C: Create Menus | 5 min | - (manual required) |
| **TOTAL** | **20 min** | **8 min** (if SFTP ready) |

---

**Next**: Proceed with Option A, B, or C? Or run all simultaneously?
