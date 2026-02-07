# The Vault - Deployment Guide

## Overview

The Vault is a futuristic pre-order page template for WordPress/WooCommerce with:
- Matrix-style tech grid background
- Rotating collection logos
- Glassmorphism product cards
- Optional 3D model viewers
- WooCommerce cart integration

## Files Created

```
wordpress-theme/skyyrose-2025/
├── template-vault.php          # Main page template
├── assets/
│   └── images/                 # Collection logos (upload these)
│       ├── BLACK-Rose-LOGO.PNG
│       ├── Love-Hurts-LOGO.PNG
│       └── Signature-LOGO.PNG

scripts/
└── sync_vault_products.py      # Python script to create products
```

## Deployment Steps

### 1. Upload Theme Files

Via FTP/SSH:
```bash
# Upload template to your WordPress theme directory
scp template-vault.php user@server:/path/to/wp-content/themes/skyyrose-2025/
```

Via WordPress Admin:
1. Appearance → Theme File Editor
2. Add New File → `template-vault.php`
3. Paste the template code

### 2. Upload Collection Logos

Upload these images to your theme's assets folder:
```
wp-content/themes/skyyrose-2025/assets/images/
├── BLACK-Rose-LOGO.PNG
├── Love-Hurts-LOGO.PNG
└── Signature-LOGO.PNG
```

**Location in DevSkyy**:
- Check `assets/` directory for existing logos
- Or use the logos from your website pages

### 3. Create Vault Products

**Option A: Use Python Script** (Recommended)

```bash
# From DevSkyy root
cd /Users/coreyfoster/DevSkyy

# Set environment variables in .env
WOO_CONSUMER_KEY=ck_xxxxxxxxxxxxx
WOO_CONSUMER_SECRET=cs_xxxxxxxxxxxxx
WORDPRESS_URL=https://skyyrose.co

# Run sync
python scripts/sync_vault_products.py
```

**Option B: Manual Creation**

1. Go to **Products → Add New**
2. Add product details:
   - Name: "The Prototype"
   - Price: $500.00
   - SKU: VAULT-PROTO-001
   - Description: "Limited edition prototype design..."

3. In **Custom Fields** (scroll down):
   - `_vault_preorder`: 1
   - `_vault_badge`: ENCRYPTED
   - `_vault_quantity_limit`: 50
   - `_vault_icon`: 🔐

4. Click **Publish**

Repeat for each product (see `scripts/sync_vault_products.py` for data).

### 4. Create Vault Page

1. **Pages → Add New**
2. Title: "The Vault"
3. In **Page Attributes** (right sidebar):
   - Template: Select **"The Vault - Pre-Order"**
4. Permalink: `/vault` or `/the-vault`
5. Click **Publish**

### 5. Add Share Tech Mono Font (Optional)

If the monospace font isn't loading, add to `functions.php`:

```php
function skyyrose_vault_fonts() {
    wp_enqueue_style(
        'share-tech-mono',
        'https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap',
        [],
        null
    );
}
add_action('wp_enqueue_scripts', 'skyyrose_vault_fonts');
```

### 6. Test Add to Cart

The template includes AJAX add-to-cart functionality:

1. Visit `/vault` page
2. Click **"SECURE ASSET"** button
3. Product should be added to cart
4. User redirected to cart page

If not working, enable WooCommerce AJAX in **WooCommerce → Settings → Advanced**:
- Enable AJAX add to cart buttons on archives: ✓

## Product Meta Fields

Custom meta fields used by the Vault template:

| Meta Key | Type | Description | Example |
|----------|------|-------------|---------|
| `_vault_preorder` | string | Enable Vault display | `"1"` |
| `_vault_badge` | string | Security badge text | `"ENCRYPTED"` |
| `_vault_quantity_limit` | string | Max quantity (empty = unlimited) | `"50"` |
| `_vault_quantity_sold` | string | Items sold (auto-updated) | `"0"` |
| `_vault_icon` | string | Emoji/icon fallback | `"🔐"` |
| `_skyyrose_3d_model_url` | string | GLB model URL (optional) | `"https://..."` |

## 3D Model Integration

If products have 3D models, add the GLB URL:

1. Edit product
2. Scroll to **3D Model** meta box (right sidebar)
3. Enter GLB URL: `https://github.com/.../model.glb`
4. Update product

The template will automatically display the 3D viewer instead of the icon.

**Existing 3D Models**:
See memory: `skyyrose_deployment_status` for GitHub release URLs.

## Customization

### Change Colors

In `template-vault.php`, modify CSS variables:

```css
:root {
    --neon-green: #00ff41;  /* Change to your brand color */
    --bg-dark: #050505;
    --glass-bg-vault: rgba(0, 20, 5, 0.6);
}
```

### Add More Products

1. Add product data to `VAULT_PRODUCTS` in `scripts/sync_vault_products.py`
2. Run sync script again
3. Products auto-appear on Vault page

### Modify Grid Layout

Change grid columns:
```css
.vault-frame {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); /* Adjust 300px */
}
```

## Troubleshooting

### Products Not Showing

1. Check product has `_vault_preorder` meta set to `"1"`
2. Verify product status is `"publish"`
3. Check WooCommerce → Products for inventory

### Logos Not Rotating

1. Verify image paths in JavaScript (line ~250)
2. Check browser console for 404 errors
3. Upload missing logo files to correct directory

### Add to Cart Not Working

1. Check WooCommerce is active
2. Verify product is in stock
3. Check browser console for JavaScript errors
4. Enable WooCommerce logs: WooCommerce → Status → Logs

### 3D Models Not Loading

1. Verify `window.initSkyyRose3DViewer` function exists
2. Check Three.js is loaded (view page source)
3. Ensure GLB URL is valid and accessible

## WordPress.com vs Self-Hosted

**WordPress.com** (Business Plan+):
- Upload theme via Appearance → Themes → Upload Theme
- Custom code allowed on Business plan and above
- REST API URL: `https://site.wordpress.com/index.php?rest_route=/wc/v3/`

**Self-Hosted**:
- FTP/SSH access for theme files
- Full control over plugins and code
- REST API URL: `https://site.com/wp-json/wc/v3/`

## Security Notes

- All user inputs are escaped (`esc_html`, `esc_url`, `esc_attr`)
- XSS prevention via DOM manipulation (no `innerHTML`)
- WooCommerce nonce verification for AJAX
- Product IDs validated before cart operations

## Next Steps

1. ✅ Deploy template file
2. ✅ Upload collection logos
3. ✅ Create Vault products
4. ✅ Create Vault page
5. 🔲 Test purchasing flow
6. 🔲 Configure payment gateway
7. 🔲 Set up inventory notifications
8. 🔲 Add to main navigation menu

## Support

For issues or questions:
- Check CLAUDE.md for DevSkyy protocols
- Review `wordpress-ops` skill for WooCommerce patterns
- Test locally before deploying to production
