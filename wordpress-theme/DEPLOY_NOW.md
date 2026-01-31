# Deploy SkyyRose Theme - RIGHT NOW (10 Minutes)

## 🎯 FASTEST PATH TO LIVE SITE

Skip OAuth complexity. Use this foolproof manual method:

---

## Step 1: Upload Theme (3 min)

1. **Go to your WordPress admin**:
   - URL: `https://yoursite.wordpress.com/wp-admin`

2. **Navigate to**: Appearance → Themes → Add New

3. **Click**: "Upload Theme"

4. **Choose file**:
   ```
   /Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025-theme.zip
   ```

5. **Click**: "Install Now"

6. **Click**: "Activate"

✅ **Theme installed!**

---

## Step 2: Create Pages (5 min)

Go to: **Pages → Add New**

Create 10 pages (copy-paste these):

### Page 1: Home
- **Title**: `Home`
- **Template**: `Home` (in Page Attributes sidebar)
- **Publish**

### Page 2: The Vault
- **Title**: `The Vault`
- **Template**: `Vault`
- **Publish**

### Page 3: Black Rose
- **Title**: `Black Rose`
- **Template**: `Collection`
- **Custom Fields** (enable in Screen Options if not visible):
  - Name: `_collection_type`
  - Value: `black-rose`
- **Publish**

### Page 4: Black Rose Experience
- **Title**: `Black Rose Experience`
- **Template**: `Immersive Experience`
- **Custom Fields**:
  - Name: `_collection_type`
  - Value: `black-rose`
- **Publish**

### Page 5: Love Hurts
- **Title**: `Love Hurts`
- **Template**: `Collection`
- **Custom Fields**:
  - Name: `_collection_type`
  - Value: `love-hurts`
- **Publish**

### Page 6: Love Hurts Experience
- **Title**: `Love Hurts Experience`
- **Template**: `Immersive Experience`
- **Custom Fields**:
  - Name: `_collection_type`
  - Value: `love-hurts`
- **Publish**

### Page 7: Signature
- **Title**: `Signature`
- **Template**: `Collection`
- **Custom Fields**:
  - Name: `_collection_type`
  - Value: `signature`
- **Publish**

### Page 8: Signature Experience
- **Title**: `Signature Experience`
- **Template**: `Immersive Experience`
- **Custom Fields**:
  - Name: `_collection_type`
  - Value: `signature`
- **Publish**

### Page 9: About
- **Title**: `About`
- **Template**: `About SkyyRose`
- **Publish**

### Page 10: Contact
- **Title**: `Contact`
- **Template**: `Contact`
- **Publish**

✅ **All pages created!**

---

## Step 3: Set Homepage (30 sec)

1. **Go to**: Settings → Reading

2. **Select**: "A static page" (instead of "Your latest posts")

3. **Homepage**: Select "Home"

4. **Click**: "Save Changes"

✅ **Homepage set!**

---

## Step 4: Import Products (2 min)

1. **Go to**: WooCommerce → Products → Import

2. **Click**: "Choose File"

3. **Select**:
   ```
   /Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025/PRODUCT_DATA.csv
   ```

4. **Click**: "Continue"

5. **Click**: "Run the importer"

✅ **30 products imported!**

---

## Step 5: Create Menu (3 min)

1. **Go to**: Appearance → Menus

2. **Click**: "create a new menu"

3. **Name**: `Primary Navigation`

4. **Add pages** in this order (drag to create hierarchy):

```
Home
Collections (create custom link)
  └── Black Rose (create custom link)
      ├── Experience (link to: Black Rose Experience page)
      └── Shop (link to: Black Rose page)
  └── Love Hurts (create custom link)
      ├── Experience (link to: Love Hurts Experience page)
      └── Shop (link to: Love Hurts page)
  └── Signature (create custom link)
      ├── Experience (link to: Signature Experience page)
      └── Shop (link to: Signature page)
Pre-Order (link to: The Vault page)
About
Contact
```

5. **Check**: "Primary Menu" under Menu Settings

6. **Click**: "Save Menu"

✅ **Navigation complete!**

---

## 🎉 YOU'RE LIVE!

Visit your site: `https://yoursite.wordpress.com`

You should see:
- ✅ Beautiful homepage with animated orbs
- ✅ 3 collection pages with products
- ✅ Immersive experience pages
- ✅ The Vault pre-order page
- ✅ About and Contact pages
- ✅ 30 products ready to sell

---

## ⚙️ Optional: WooCommerce Setup

1. **Go to**: WooCommerce → Settings

2. **Payments**: Enable payment methods (Stripe, PayPal, etc.)

3. **Shipping**: Set up shipping zones and rates

4. **Tax**: Configure tax settings

5. **Test order**: Make a test purchase to verify everything works

---

## 🔍 Troubleshooting

**Problem**: Custom Fields not showing
**Fix**: Go to Screen Options (top right) → Check "Custom Fields"

**Problem**: Templates not in dropdown
**Fix**: Make sure theme is activated (Appearance → Themes)

**Problem**: Products not showing on collection pages
**Fix**: Edit product → Set Custom Field `_skyyrose_collection` to `black-rose`, `love-hurts`, or `signature`

**Problem**: Menu dropdowns not working
**Fix**: Drag menu items slightly to the right to create hierarchy

---

## 📞 Need Help?

All documentation is in:
```
/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025/
```

- `DEPLOYMENT_READY.md` - Complete deployment guide
- `SECURITY.md` - Security information
- `WORDPRESS_COM_API.md` - API documentation
- `README.md` - Theme overview

---

**Time to Complete**: ~10 minutes
**Status**: 100% Production Ready ✅

**GO LIVE NOW!** 🚀
