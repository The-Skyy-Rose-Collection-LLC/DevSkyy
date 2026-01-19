# WooCommerce Theme Development

This skill provides comprehensive knowledge for building immersive WooCommerce themes. It activates when users mention "WooCommerce", "product pages", "cart", "checkout", "e-commerce theme", or need to customize WooCommerce templates.

---

## WooCommerce Theme Support

```php
// functions.php
function theme_woocommerce_support() {
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');
}
add_action('after_setup_theme', 'theme_woocommerce_support');
```

## Template Hierarchy

```
theme/
└── woocommerce/
    ├── archive-product.php          # Shop page
    ├── single-product.php           # Product page
    ├── content-product.php          # Product in loop
    ├── content-single-product.php   # Single product content
    ├── cart/
    │   ├── cart.php
    │   └── cart-totals.php
    ├── checkout/
    │   ├── form-checkout.php
    │   └── thankyou.php
    ├── single-product/
    │   ├── title.php
    │   ├── price.php
    │   ├── add-to-cart/
    │   └── tabs/
    └── loop/
        ├── loop-start.php
        └── loop-end.php
```

## Product Loop Customization

### Custom Product Card
```php
// woocommerce/content-product.php
<li <?php wc_product_class('product-card', $product); ?>>
    <div class="product-card__image">
        <?php woocommerce_template_loop_product_thumbnail(); ?>
        <div class="product-card__overlay">
            <button class="quick-view" data-product-id="<?php echo $product->get_id(); ?>">
                Quick View
            </button>
        </div>
    </div>

    <div class="product-card__content">
        <h3 class="product-card__title">
            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        </h3>

        <div class="product-card__price">
            <?php woocommerce_template_loop_price(); ?>
        </div>

        <div class="product-card__rating">
            <?php woocommerce_template_loop_rating(); ?>
        </div>
    </div>

    <div class="product-card__actions">
        <?php woocommerce_template_loop_add_to_cart(); ?>
    </div>
</li>
```

### Custom Add to Cart Button
```php
// Remove default button
remove_action('woocommerce_after_shop_loop_item', 'woocommerce_template_loop_add_to_cart', 10);

// Add custom button
add_action('woocommerce_after_shop_loop_item', 'custom_add_to_cart_button', 10);
function custom_add_to_cart_button() {
    global $product;

    if ($product->is_type('simple') && $product->is_in_stock()) {
        echo sprintf(
            '<button class="custom-add-to-cart" data-product-id="%s" data-quantity="1">
                <span class="button-text">Add to Cart</span>
                <span class="button-icon">
                    <svg>...</svg>
                </span>
            </button>',
            $product->get_id()
        );
    } else {
        echo sprintf(
            '<a href="%s" class="custom-view-product">View Options</a>',
            get_permalink($product->get_id())
        );
    }
}
```

## Single Product Page

### Custom Layout
```php
// Remove default hooks
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_title', 5);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_price', 10);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_excerpt', 20);

// Add custom structure
add_action('woocommerce_single_product_summary', 'custom_product_header', 5);
function custom_product_header() {
    global $product;
    ?>
    <div class="product-header">
        <nav class="breadcrumb">
            <?php woocommerce_breadcrumb(); ?>
        </nav>

        <h1 class="product-title"><?php the_title(); ?></h1>

        <div class="product-meta">
            <?php if ($product->get_sku()) : ?>
                <span class="sku">SKU: <?php echo $product->get_sku(); ?></span>
            <?php endif; ?>

            <div class="rating">
                <?php woocommerce_template_single_rating(); ?>
            </div>
        </div>

        <div class="product-price">
            <?php woocommerce_template_single_price(); ?>
        </div>
    </div>
    <?php
}
```

### Product Gallery Enhancement
```php
// Custom gallery with 3D viewer option
add_action('woocommerce_before_single_product_summary', 'custom_product_gallery', 20);
function custom_product_gallery() {
    global $product;

    $gallery_ids = $product->get_gallery_image_ids();
    $main_image = $product->get_image_id();
    $model_url = get_post_meta($product->get_id(), '_3d_model_url', true);
    ?>
    <div class="product-gallery">
        <?php if ($model_url) : ?>
            <div class="gallery-3d-viewer" data-model="<?php echo esc_url($model_url); ?>">
                <!-- 3D Viewer renders here -->
            </div>
            <button class="toggle-view" data-view="3d">View in 3D</button>
        <?php endif; ?>

        <div class="gallery-main">
            <?php echo wp_get_attachment_image($main_image, 'large'); ?>
        </div>

        <div class="gallery-thumbnails">
            <?php foreach ($gallery_ids as $id) : ?>
                <button class="thumbnail" data-image-id="<?php echo $id; ?>">
                    <?php echo wp_get_attachment_image($id, 'thumbnail'); ?>
                </button>
            <?php endforeach; ?>
        </div>
    </div>
    <?php
}
```

## AJAX Add to Cart

```javascript
// Custom AJAX add to cart
document.querySelectorAll('.custom-add-to-cart').forEach(button => {
    button.addEventListener('click', async function(e) {
        e.preventDefault();

        const productId = this.dataset.productId;
        const quantity = this.dataset.quantity || 1;

        this.classList.add('loading');

        try {
            const response = await fetch(wc_add_to_cart_params.ajax_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    action: 'woocommerce_ajax_add_to_cart',
                    product_id: productId,
                    quantity: quantity,
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update cart count
            document.querySelector('.cart-count').textContent = data.cart_count;

            // Success animation
            this.classList.remove('loading');
            this.classList.add('success');

            // Animate product to cart
            animateToCart(this);

        } catch (error) {
            console.error('Add to cart failed:', error);
            this.classList.remove('loading');
            this.classList.add('error');
        }
    });
});
```

## Cart Customization

```php
// woocommerce/cart/cart.php
<div class="custom-cart">
    <h1 class="cart-title">Your Cart</h1>

    <?php if (WC()->cart->is_empty()) : ?>
        <div class="cart-empty">
            <p>Your cart is empty</p>
            <a href="<?php echo wc_get_page_permalink('shop'); ?>" class="continue-shopping">
                Continue Shopping
            </a>
        </div>
    <?php else : ?>
        <div class="cart-items">
            <?php foreach (WC()->cart->get_cart() as $cart_item_key => $cart_item) :
                $product = $cart_item['data'];
            ?>
                <div class="cart-item" data-key="<?php echo $cart_item_key; ?>">
                    <div class="cart-item__image">
                        <?php echo $product->get_image('thumbnail'); ?>
                    </div>

                    <div class="cart-item__details">
                        <h3><?php echo $product->get_name(); ?></h3>
                        <p class="price"><?php echo WC()->cart->get_product_price($product); ?></p>
                    </div>

                    <div class="cart-item__quantity">
                        <button class="qty-btn minus">-</button>
                        <input type="number" value="<?php echo $cart_item['quantity']; ?>" min="1">
                        <button class="qty-btn plus">+</button>
                    </div>

                    <div class="cart-item__subtotal">
                        <?php echo WC()->cart->get_product_subtotal($product, $cart_item['quantity']); ?>
                    </div>

                    <button class="cart-item__remove" data-key="<?php echo $cart_item_key; ?>">
                        Remove
                    </button>
                </div>
            <?php endforeach; ?>
        </div>

        <div class="cart-summary">
            <?php woocommerce_cart_totals(); ?>
        </div>
    <?php endif; ?>
</div>
```

## Checkout Customization

```php
// Customize checkout fields
add_filter('woocommerce_checkout_fields', 'custom_checkout_fields');
function custom_checkout_fields($fields) {
    // Reorder fields
    $fields['billing']['billing_email']['priority'] = 5;

    // Add custom field
    $fields['billing']['billing_company_type'] = [
        'type' => 'select',
        'label' => 'Company Type',
        'options' => [
            '' => 'Select...',
            'individual' => 'Individual',
            'business' => 'Business',
        ],
        'priority' => 25,
    ];

    // Customize placeholders
    $fields['billing']['billing_first_name']['placeholder'] = 'First Name';

    return $fields;
}
```

## Mini Cart

```php
// AJAX mini cart
add_filter('woocommerce_add_to_cart_fragments', 'custom_mini_cart_fragment');
function custom_mini_cart_fragment($fragments) {
    ob_start();
    ?>
    <div class="mini-cart">
        <span class="cart-count"><?php echo WC()->cart->get_cart_contents_count(); ?></span>
        <div class="mini-cart__dropdown">
            <?php woocommerce_mini_cart(); ?>
        </div>
    </div>
    <?php
    $fragments['.mini-cart'] = ob_get_clean();
    return $fragments;
}
```

## Performance Tips

- Use `wc_get_product()` instead of `new WC_Product()`
- Cache expensive queries
- Lazy load product images
- Use AJAX for cart updates
- Minimize checkout fields
