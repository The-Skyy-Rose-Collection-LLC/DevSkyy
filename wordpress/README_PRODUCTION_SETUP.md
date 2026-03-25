# WordPress Production Setup - Master Index

> Complete guide to deleting old pages and deploying SkyyRose production site

**Site**: https://skyyrose.co
**Status**: ✅ Ready for production deployment
**Created**: 2026-01-14

---

## 🚀 Start Here

### For Non-Technical Users (Manual Approach)
👉 **Read**: `QUICK_START_CLEANUP.md`
- Step-by-step manual instructions
- No coding required
- ~10 minutes

### For Developers (Scripted Approach)
👉 **Read**: `PRODUCTION_SETUP_SUMMARY.md` → "Quick Start: Option 2"
- Automated page deletion and creation
- Python scripts with safety checks
- ~3 minutes execution

### For Complete Overview
👉 **Read**: `PRODUCTION_SETUP_SUMMARY.md`
- Full implementation guide
- All 12 access methods
- Troubleshooting
- Next steps

---

## 📚 Documentation Files

### 1. **QUICK_START_CLEANUP.md**
   - **What**: Manual step-by-step guide
   - **Who**: Non-technical users
   - **Time**: ~10 minutes
   - **Contains**:
     - Delete old pages
     - Create 7 production pages
     - Configure homepage
     - Navigate menus

### 2. **PRODUCTION_SETUP_SUMMARY.md**
   - **What**: Complete implementation guide
   - **Who**: Developers & project managers
   - **Time**: Full reference
   - **Contains**:
     - All 12 access methods explained
     - Production page structure
     - Scripts and automation
     - Troubleshooting
     - Timeline & decisions

### 3. **WORDPRESS_ACCESS_METHODS.md**
   - **What**: Comprehensive access guide
   - **Who**: Developers needing flexibility
   - **Time**: Reference
   - **Contains**:
     - Admin dashboard
     - REST API (WordPress.com + WooCommerce)
     - Python/cURL examples
     - XML-RPC
     - WP-CLI
     - Mobile app
     - Third-party tools

### 4. **WORDPRESS_COM_CLEANUP_GUIDE.md**
   - **What**: Detailed cleanup instructions
   - **Who**: Developers using OAuth
   - **Time**: Reference
   - **Contains**:
     - Manual deletion (WordPress Admin)
     - OAuth token setup
     - Script-based deletion
     - Verified page structure

### 5. **PRODUCTION_PAGES_TEMPLATE.md**
   - **What**: Content templates for all pages
   - **Who**: Content creators
   - **Time**: Reference
   - **Contains**:
     - 7 page templates (Home, Shop, Collections, etc.)
     - Shortcode examples
     - Meta information
     - SEO hints

---

## 🔧 Available Scripts

### **wordpress_com_cleanup.py**
Delete all existing WordPress pages

```bash
# List pages (no changes)
python scripts/wordpress_com_cleanup.py --list-only

# Dry-run (see what would be deleted)
python scripts/wordpress_com_cleanup.py --dry-run

# Actually delete (interactive confirmation)
python scripts/wordpress_com_cleanup.py
```

**Requires**: `WORDPRESS_COM_ACCESS_TOKEN` in `.env`

---

### **create_wordpress_production_pages.py**
Create 7 production pages automatically

```bash
# Dry-run (see what would be created)
python scripts/create_wordpress_production_pages.py --dry-run

# Actually create
python scripts/create_wordpress_production_pages.py
```

**Creates**:
- `/` (Home)
- `/experiences` (Parent)
- `/experiences/signature/`
- `/experiences/black-rose/`
- `/experiences/love-hurts/`
- `/shop`
- `/about`
- `/contact`

**Requires**: `WORDPRESS_COM_ACCESS_TOKEN` in `.env`

---

## 🌐 Direct Access Methods

### ✅ Easiest: WordPress Admin Dashboard
- **URL**: https://skyyrose.co/wp-admin/
- **Login**: `skyyroseco` / (password in `.env`)
- **What you can do**: Create, edit, delete pages, products, media

### ✅ Scriptable: REST API (OAuth)
- **Endpoint**: `https://public-api.wordpress.com/rest/v1.1/sites/skyyrose.co/`
- **Auth**: Bearer token (OAuth)
- **Tools**: cURL, Python, Node.js, etc.
- **Use cases**: Automation, CI/CD, bulk operations

### ✅ For Products: WooCommerce API (Basic Auth)
- **Endpoint**: `https://skyyrose.co/wp-json/wc/v3/`
- **Auth**: Consumer Key & Secret (in `.env`)
- **Use cases**: Product management, inventory

### ✅ Legacy: XML-RPC
- **Endpoint**: `https://skyyrose.co/xmlrpc.php`
- **Auth**: Username & password
- **Tools**: Python xmlrpc.client, legacy apps

---

## 🎯 Recommended Approach

### For First Time Setup

**If you're comfortable with WordPress admin dashboard:**
1. Read: `QUICK_START_CLEANUP.md`
2. Go to: https://skyyrose.co/wp-admin/
3. Follow step-by-step instructions
4. Total time: ~10 minutes

**If you prefer automation:**
1. Read: `PRODUCTION_SETUP_SUMMARY.md` (Quick Start section)
2. Ensure `.env` has `WORDPRESS_COM_ACCESS_TOKEN`
3. Run:
   ```bash
   python scripts/wordpress_com_cleanup.py --list-only
   python scripts/create_wordpress_production_pages.py --dry-run
   ```
4. If dry-run looks good, run without `--dry-run`
5. Total time: ~3-5 minutes

---

## 🔐 Environment Variables Needed

### Required
```bash
WORDPRESS_URL=https://skyyrose.co
WORDPRESS_USERNAME=skyyroseco
WORDPRESS_PASSWORD=...  # From WP Admin
```

### Optional (For Scripts)
```bash
WORDPRESS_COM_ACCESS_TOKEN=...  # OAuth token for automation
WOOCOMMERCE_KEY=...              # For product management
WOOCOMMERCE_SECRET=...           # For product management
```

### Get OAuth Token
1. Go to: https://developer.wordpress.com/apps/
2. Create app → get Client ID & Secret
3. Follow OAuth flow in `WORDPRESS_COM_CLEANUP_GUIDE.md`
4. Add token to `.env`

---

## ✅ Verification Checklist

After running cleanup & creation scripts:

- [ ] Visit https://skyyrose.co/ - Home page loads
- [ ] Visit https://skyyrose.co/shop - Shop page loads
- [ ] Visit https://skyyrose.co/experiences/signature/ - Collection loads
- [ ] Visit https://skyyrose.co/experiences/black-rose/ - Collection loads
- [ ] Visit https://skyyrose.co/experiences/love-hurts/ - Collection loads
- [ ] Visit https://skyyrose.co/about/ - About page loads
- [ ] Visit https://skyyrose.co/contact/ - Contact page loads
- [ ] WP Admin → Settings → Reading → Homepage set to "Home"
- [ ] WP Admin → Products → Settings → Shop page set to "Shop"

---

## 🚨 Safety Features

### All Scripts Include
- ✅ Dry-run mode (see what would happen)
- ✅ Confirmation prompts (before deleting)
- ✅ Error handling (safe fallbacks)
- ✅ Logging (see what happened)
- ✅ Rollback info (how to undo)

### Best Practice
1. Always run `--list-only` or `--dry-run` first
2. Review what would happen
3. Then run actual command with confirmation
4. Verify results

---

## 📞 Support

### Questions About...

| Topic | Resource |
|-------|----------|
| Manual cleanup | `QUICK_START_CLEANUP.md` |
| Script setup | `PRODUCTION_SETUP_SUMMARY.md` |
| OAuth token | `WORDPRESS_COM_CLEANUP_GUIDE.md` |
| All access methods | `WORDPRESS_ACCESS_METHODS.md` |
| Page content | `PRODUCTION_PAGES_TEMPLATE.md` |
| Shortcodes | `wordpress/shortcodes.py` |

### External Resources
- WordPress Docs: https://wordpress.org/support/
- WordPress.com Docs: https://wordpress.com/support/
- WooCommerce Docs: https://woocommerce.com/documentation/

---

## 📋 What's Included

### Documentation (5 files)
- ✅ QUICK_START_CLEANUP.md
- ✅ PRODUCTION_SETUP_SUMMARY.md
- ✅ WORDPRESS_ACCESS_METHODS.md
- ✅ WORDPRESS_COM_CLEANUP_GUIDE.md
- ✅ PRODUCTION_PAGES_TEMPLATE.md
- ✅ README_PRODUCTION_SETUP.md (this file)

### Scripts (2 files)
- ✅ `scripts/wordpress_com_cleanup.py`
- ✅ `scripts/create_wordpress_production_pages.py`

### Existing Resources
- ✅ Child theme: `wordpress/shoptimizer-child/`
- ✅ Shortcodes: `wordpress/shortcodes.py`
- ✅ Product utilities: `wordpress/products.py`
- ✅ 3D integration: `wordpress/upload_3d_models_to_wordpress.py`

---

## 🎯 Success Criteria

| Criterion | Status |
|-----------|--------|
| Old pages deleted | ⏳ Pending |
| 7 production pages created | ⏳ Pending |
| Homepage configured | ⏳ Pending |
| Shop page configured | ⏳ Pending |
| Navigation menus added | ⏳ Pending |
| All pages accessible | ⏳ Pending |
| Shortcodes working | ⏳ Pending |
| Analytics enabled | ⏳ Optional |
| Products added | ⏳ Optional |
| 3D models uploaded | ⏳ Optional |

---

## 🚀 Next Steps

### Immediate (Required)
1. Choose approach: Manual (`QUICK_START_CLEANUP.md`) OR Scripted (scripts)
2. Execute cleanup
3. Verify production pages load

### Short Term (Recommended)
1. Add navigation menus
2. Upload products to WooCommerce
3. Configure homepage/shop settings
4. Test shortcodes

### Long Term (Optional)
1. Upload 3D models
2. Enable AR try-on
3. Setup analytics
4. Optimize SEO
5. Add blog posts

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial release |
| | | - 6 documentation files |
| | | - 2 automation scripts |
| | | - 12 access method guides |
| | | - 7 page templates |

---

**Ready to deploy? Pick your approach above and get started!** 🚀
