# HTML to WordPress Conversion Guide

## Overview

You have 18 HTML pages in `/wordpress website pages/` that need to be converted to WordPress templates.

## Page Inventory

### Immersive Collection Pages (3D/Interactive)
- `01-black-rose-garden_immersive.html` → Black Rose immersive experience
- `02-love-hurts-castle_immersive.html` → Love Hurts immersive experience
- `03-signature-runway_immersive.html` → Signature immersive experience

### Static Collection Pages
- `collection-black-rose.html` → Black Rose product grid
- `collection-love-hurts.html` → Love Hurts product grid
- `collection-signature.html` → Signature product grid ✅ **CONVERTED**

### Pre-Order/Vault Pages
- `pre-order.html` → The Vault pre-order page ✅ **CONVERTED**
- `pre-order_immersive.html` → Alternative vault design

### Homepage
- `homepage_enhanced.html` → Enhanced homepage with animations
- `homepage.html` → Original homepage

### E-Commerce Pages
- `cart.html` → Shopping cart (WooCommerce handles this)
- `checkout.html` → Checkout page (WooCommerce handles this)
- `single-product.html` → Product detail page

### Info Pages
- `about.html` → About page
- `contact.html` → Contact page

## Conversion Strategy

### Templates Already Created

1. ✅ **template-vault.php** - Pre-order/Vault page
   - Converts: `pre-order.html`
   - Features: Rotating logos, glassmorphism, neon green theme

2. ✅ **template-collection.php** - Collection product grid
   - Converts: `collection-signature.html`, `collection-black-rose.html`, `collection-love-hurts.html`
   - Features: Dynamic filtering, collection-specific colors

### Templates Needed

#### High Priority

3. **template-home.php** - Homepage
   - Convert: `homepage_enhanced.html`
   - Features: Hero section, collection previews, animations

4. **template-immersive-collection.php** - 3D Collection Experience
   - Convert: `01-black-rose-garden_immersive.html`, `02-love-hurts-castle_immersive.html`, `03-signature-runway_immersive.html`
   - Features: Three.js 3D scenes, interactive elements

5. **single-product.php** - Product Detail Page (override WooCommerce)
   - Convert: `single-product.html`
   - Features: 3D model viewer, product gallery, add to cart

#### Medium Priority

6. **page-about.php** - About page
   - Convert: `about.html`
   - Features: Brand story, team info

7. **page-contact.php** - Contact page
   - Convert: `contact.html`
   - Features: Contact form, map

#### Low Priority (WooCommerce Handles)

8. **cart.php** - Cart page (WooCommerce override)
9. **checkout.php** - Checkout page (WooCommerce override)

## Conversion Workflow

### Step 1: Extract Assets

```bash
# Copy images and logos from HTML pages
cd "/Users/coreyfoster/DevSkyy/wordpress website pages"

# Upload to WordPress theme
cp -r assets/* /path/to/wp-content/themes/skyyrose-2025/assets/
```

### Step 2: Convert HTML to PHP Template

**Pattern:**

```php
<?php
/**
 * Template Name: [Page Name]
 * Description: [Description]
 */

get_header();
?>

<!-- Your HTML content here -->
<!-- Replace hardcoded links with WordPress functions -->

<?php get_footer(); ?>
```

### Step 3: Replace Static Links

| HTML | WordPress |
|------|-----------|
| `<a href="homepage.html">` | `<a href="<?php echo home_url(); ?>">` |
| `<a href="cart.html">` | `<a href="<?php echo wc_get_cart_url(); ?>">` |
| `<img src="assets/logo.png">` | `<img src="<?php echo get_template_directory_uri(); ?>/assets/logo.png">` |
| `<a href="single-product.html?id=123">` | `<a href="<?php echo get_permalink(123); ?>">` |

### Step 4: Integrate WooCommerce

**Product Loops:**

```php
<?php
$args = ['post_type' => 'product', 'posts_per_page' => 10];
$products = new WP_Query($args);

if ($products->have_posts()) :
    while ($products->have_posts()) : $products->the_post();
        global $product;
        ?>
        <div class="product-card">
            <h3><?php the_title(); ?></h3>
            <span><?php echo $product->get_price_html(); ?></span>
            <button onclick="addToCart(<?php echo $product->get_id(); ?>)">Add to Cart</button>
        </div>
        <?php
    endwhile;
endif;
wp_reset_postdata();
?>
```

### Step 5: Add Dynamic Navigation

**Replace hardcoded navbar:**

```php
<nav class="navbar">
    <a href="<?php echo home_url(); ?>" class="logo">SKYYROSE</a>
    <ul class="nav-links">
        <li><a href="<?php echo get_permalink(get_page_by_path('black-rose')); ?>">Black Rose</a></li>
        <li><a href="<?php echo get_permalink(get_page_by_path('love-hurts')); ?>">Love Hurts</a></li>
        <li><a href="<?php echo get_permalink(get_page_by_path('signature')); ?>">Signature</a></li>
        <li><a href="<?php echo get_permalink(get_page_by_path('vault')); ?>">Vault</a></li>
    </ul>
    <div>
        <a href="<?php echo wc_get_cart_url(); ?>">
            CART (<?php echo WC()->cart->get_cart_contents_count(); ?>)
        </a>
    </div>
</nav>
```

## File Structure

```
wordpress-theme/skyyrose-2025/
├── template-vault.php              ✅ Created
├── template-collection.php         ✅ Created
├── template-home.php               🔲 Need to create
├── template-immersive-collection.php 🔲 Need to create
├── single-product.php              🔲 Need to create
├── page-about.php                  🔲 Need to create
├── page-contact.php                🔲 Need to create
├── header.php                      ✅ Exists
├── footer.php                      ✅ Exists
├── functions.php                   ✅ Exists
├── style.css                       ✅ Exists
└── assets/
    ├── images/
    │   ├── BLACK-Rose-LOGO.PNG
    │   ├── Love-Hurts-LOGO.PNG
    │   └── Signature-LOGO.PNG
    └── js/
        ├── animations.js
        ├── 3d-viewer.js
        └── main.js
```

## WordPress Setup

### 1. Create Pages

For each template, create a page in WordPress admin:

```
Pages → Add New
Title: "The Vault"
Template: Select "The Vault - Pre-Order"
Publish
```

### 2. Set Up WooCommerce Products

Products need these custom fields for templates to work:

| Meta Key | Description | Example |
|----------|-------------|---------|
| `_skyyrose_collection` | Collection slug | `signature` |
| `_product_badge` | Badge text | `EXCLUSIVE` |
| `_vault_preorder` | Enable in Vault | `1` |
| `_vault_badge` | Vault badge | `ENCRYPTED` |
| `_vault_quantity_limit` | Max units | `50` |
| `_skyyrose_3d_model_url` | 3D model URL | `https://...` |

### 3. Create Menu

```
Appearance → Menus
Create: "Primary Navigation"
Add pages: Home, Black Rose, Love Hurts, Signature, Vault
Assign to location: Primary Menu
```

## Next Steps

### Immediate (Use `/wordpress-ops` Skill)

1. Convert `homepage_enhanced.html` → `template-home.php`
2. Convert immersive pages → `template-immersive-collection.php`
3. Upload collection logos to theme assets
4. Create pages in WordPress admin
5. Test product filtering and cart functionality

### Future Enhancements

1. Add AJAX filtering without page reload
2. Implement product quick view
3. Add wishlist functionality
4. Set up pre-order inventory tracking
5. Configure email notifications for Vault purchases

## Testing Checklist

- [ ] Navigation links work
- [ ] Products display correctly
- [ ] Add to cart functions
- [ ] Filters work on collection pages
- [ ] 3D models load (if enabled)
- [ ] Mobile responsive
- [ ] Cart icon updates
- [ ] Pre-order limits enforced

## Common Issues

### Issue: Products not showing
**Fix:** Check `_skyyrose_collection` meta matches collection slug

### Issue: 3D models not loading
**Fix:** Verify `_skyyrose_3d_model_url` and Three.js scripts enqueued

### Issue: Styling conflicts
**Fix:** Wrap template styles in `.template-name-page { }` selector

### Issue: Cart not updating
**Fix:** Enable WooCommerce AJAX in settings

## Resources

- **Deployment Guide**: `VAULT_DEPLOYMENT.md`
- **WordPress-Ops Skill**: `/wordpress-ops`
- **WooCommerce Docs**: https://woocommerce.com/documentation/
- **Theme Functions**: `functions.php`

---

**Created**: 2026-01-30
**Status**: 2/18 pages converted
**Next**: Homepage and immersive templates
