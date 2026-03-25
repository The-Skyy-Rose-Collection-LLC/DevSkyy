# 🚀 WordPress Cleanup & Production Setup - Quick Start

**Goal**: Delete old pages and prepare SkyyRose WordPress for production

**Time**: ~5 minutes

---

## Step 1: Open WordPress Admin

👉 Go to: **https://skyyrose.co/wp-admin/**

**Login:**
- Username: `skyyroseco`
- Password: Check `.env` → `WORDPRESS_PASSWORD`

---

## Step 2: Delete Old Pages

1. Click **Pages** (left sidebar)
2. You'll see existing pages:
   - ✗ home-2
   - ✗ signature
   - ✗ black-rose
   - ✗ love-hurts
   - ✗ about-2

3. **Select all** (checkbox at top)
4. **Bulk Actions** dropdown → `Move to Trash`
5. **Apply**
6. Go to **Trash** and click **Empty Trash**

✅ **WordPress is now clean!**

---

## Step 3: Create Production Pages (In Order)

### 3.1 Create Parent Page: `/experiences`

1. Click **Pages → Add New**
2. **Title**: `Experiences`
3. **Slug** (URL): `experiences`
4. **Status**: Publish
5. Click **Publish**

✓ This creates `/experiences/` parent page

### 3.2 Create Home Page

1. Click **Pages → Add New**
2. **Title**: `Home`
3. **Slug**: (leave blank - this makes it the homepage)
4. **Content**: Paste from `wordpress/PRODUCTION_PAGES_TEMPLATE.md` → "Home Page"
5. **Status**: Publish
6. Click **Publish**

⚠️ **After publishing HOME**, set it as the homepage:
   - Go to **Settings → Reading**
   - **Static homepage** → Select "Home"
   - Click **Save**

### 3.3 Create Signature Collection Page

1. Click **Pages → Add New**
2. **Title**: `Signature Collection`
3. **Slug**: `signature`
4. **Parent Page**: `Experiences`
5. **Content**: Paste from template → "Signature Collection Experience Page"
6. **Status**: Publish
7. Click **Publish**

✓ Creates `/experiences/signature/`

### 3.4 Create Black Rose Collection Page

1. Click **Pages → Add New**
2. **Title**: `Black Rose Collection`
3. **Slug**: `black-rose`
4. **Parent Page**: `Experiences`
5. **Content**: Paste from template → "Black Rose Collection Experience Page"
6. **Status**: Publish
7. Click **Publish**

✓ Creates `/experiences/black-rose/`

### 3.5 Create Love Hurts Collection Page

1. Click **Pages → Add New**
2. **Title**: `Love Hurts Collection`
3. **Slug**: `love-hurts`
4. **Parent Page**: `Experiences`
5. **Content**: Paste from template → "Love Hurts Collection Experience Page"
6. **Status**: Publish
7. Click **Publish**

✓ Creates `/experiences/love-hurts/`

### 3.6 Create Shop Page

1. Click **Pages → Add New**
2. **Title**: `Shop`
3. **Slug**: `shop`
4. **Content**: Paste from template → "Shop Page"
5. **Status**: Publish
6. Click **Publish**

✓ Creates `/shop/`

⚠️ **After publishing SHOP**, set it as WooCommerce shop page:
   - Go to **Products → Settings** (WooCommerce)
   - Find "Shop page" setting
   - Select "Shop"
   - Click **Save**

### 3.7 Create About Page

1. Click **Pages → Add New**
2. **Title**: `About SkyyRose`
3. **Slug**: `about`
4. **Content**: Paste from template → "About Page"
5. **Status**: Publish
6. Click **Publish**

✓ Creates `/about/`

### 3.8 Create Contact Page

1. Click **Pages → Add New**
2. **Title**: `Contact`
3. **Slug**: `contact`
4. **Content**: Paste from template → "Contact Page"
5. **Status**: Publish
6. Click **Publish**

✓ Creates `/contact/`

---

## Step 4: Verify Production Pages

After creating all pages, verify they exist:

- ✓ https://skyyrose.co/ (Home)
- ✓ https://skyyrose.co/shop (Shop)
- ✓ https://skyyrose.co/experiences/signature (Signature)
- ✓ https://skyyrose.co/experiences/black-rose (Black Rose)
- ✓ https://skyyrose.co/experiences/love-hurts (Love Hurts)
- ✓ https://skyyrose.co/about (About)
- ✓ https://skyyrose.co/contact (Contact)

Click each link to verify they load correctly.

---

## Step 5: Configure Theme Settings (Optional)

Go to **Appearance → Customize**:

1. **Site Identity**
   - Logo: SkyyRose logo
   - Tagline: "Where Love Meets Luxury"

2. **Homepage Settings**
   - Static homepage: `Home`
   - Blog page: (leave blank or create Blog page)

3. **Navigation**
   - Create menu with links to new pages
   - Assign to Primary Menu location

4. **Colors**
   - Primary: `#B76E79` (SkyyRose rose)
   - Secondary: `#C9A962` (rose gold)

---

## Step 6: Add Products to WooCommerce (If Needed)

Go to **Products → All Products**

If no products exist yet:
1. Click **Add New**
2. **Product Name**: (e.g., "Signature Shorts")
3. **Product Type**: Simple Product
4. **Category**: Signature (or Black Rose, Love Hurts)
5. **Price**: Set regular price
6. **Images**: Add product images
7. Click **Publish**

---

## Done! ✅

Your WordPress site is now production-ready with:
- ✓ Clean page structure
- ✓ SEO-friendly URLs
- ✓ Collection experience pages
- ✓ Shop integration
- ✓ Contact page

### Next Steps

1. **Add content** to each page
2. **Upload 3D models** (see `wordpress/upload_3d_models_to_wordpress.py`)
3. **Enable AR** (shortcodes already support it)
4. **Test virtual try-on** (requires WebGL support)
5. **Set up analytics** (Google Analytics 4)

---

## Troubleshooting

### "Slug already exists"
- Edit the conflicting page and change its slug
- Or delete the old page completely

### "Shortcodes not working"
- Theme plugin may need activation
- Check **Plugins → All Plugins** → Activate "SkyyRose Theme" or related

### "Collection logos not showing"
- Upload logos to Media Library
- Or verify theme CSS is loading (`/wp-content/themes/shoptimizer-child/`)

### Pages not visible in navigation
- Go to **Appearance → Menus**
- Create menu and add pages
- Assign to menu location

---

## Files Referenced

- `wordpress/PRODUCTION_PAGES_TEMPLATE.md` - Page content templates
- `wordpress/WORDPRESS_ACCESS_METHODS.md` - All access methods
- `wordpress/WORDPRESS_COM_CLEANUP_GUIDE.md` - Detailed cleanup guide
- `scripts/wordpress_com_cleanup.py` - Automated cleanup (requires OAuth)
- `scripts/create_wordpress_pages.py` - Automated page creation (to be created)

---

## Support

Questions? Check:
- WordPress docs: https://wordpress.org/support/
- WordPress.com docs: https://wordpress.com/support/
- WooCommerce docs: https://woocommerce.com/documentation/
- Elementor docs: https://elementor.com/help/
