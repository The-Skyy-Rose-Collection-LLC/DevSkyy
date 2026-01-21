<?php
/**
 * SkyyRose Immersive Single Product Template
 *
 * Luxury product detail page with 3D viewer and immersive gallery
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

get_header('shop');

// Get product data
global $product;

if (!$product) {
    $product = wc_get_product(get_the_ID());
}

if (!$product) {
    get_footer('shop');
    return;
}

// Get collection for theming
$collection = '';
$terms = get_the_terms($product->get_id(), 'product_cat');
if ($terms && !is_wp_error($terms)) {
    foreach ($terms as $term) {
        $slug = strtolower($term->slug);
        if (strpos($slug, 'signature') !== false) {
            $collection = 'signature';
        } elseif (strpos($slug, 'black-rose') !== false || strpos($slug, 'blackrose') !== false) {
            $collection = 'blackrose';
        } elseif (strpos($slug, 'love-hurts') !== false || strpos($slug, 'lovehurts') !== false) {
            $collection = 'lovehurts';
        }
    }
}

// Get product images
$gallery_ids = $product->get_gallery_image_ids();
$main_image_id = $product->get_image_id();
$all_images = array_merge([$main_image_id], $gallery_ids);

// Check if 3D model available
$has_3d_model = get_post_meta($product->get_id(), '_skyyrose_3d_model_url', true);
?>

<style>
    :root {
        --sp-rose-gold: #B76E79;
        --sp-obsidian: #1A1A1A;
        --sp-champagne: #F7E7CE;
        --sp-white: #FFFFFF;
        --sp-gold: #D4AF37;
    }

    .skyyrose-single-product {
        background: var(--sp-white);
        min-height: 100vh;
    }

    /* Breadcrumb */
    .sp-breadcrumb {
        padding: 20px 5%;
        font-size: 0.85rem;
        color: #666;
    }
    .sp-breadcrumb a {
        color: var(--sp-rose-gold);
        text-decoration: none;
    }
    .sp-breadcrumb span {
        margin: 0 10px;
        color: #ccc;
    }

    /* Product Layout */
    .sp-product-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 60px;
        padding: 0 5% 80px;
        max-width: 1600px;
        margin: 0 auto;
    }

    /* Gallery Section */
    .sp-gallery {
        position: sticky;
        top: 100px;
        height: fit-content;
    }

    .sp-main-image {
        position: relative;
        aspect-ratio: 1;
        background: #f8f8f8;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .sp-main-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.5s ease;
    }
    .sp-main-image:hover img {
        transform: scale(1.05);
    }
    .sp-main-image .zoom-hint {
        position: absolute;
        bottom: 20px;
        right: 20px;
        background: rgba(0,0,0,0.6);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .sp-main-image:hover .zoom-hint {
        opacity: 1;
    }

    /* 3D Viewer Toggle */
    .sp-3d-toggle {
        position: absolute;
        top: 20px;
        left: 20px;
        background: var(--sp-rose-gold);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s;
        z-index: 10;
    }
    .sp-3d-toggle:hover {
        background: #a05d68;
        transform: scale(1.05);
    }
    .sp-3d-toggle .icon-3d {
        width: 20px;
        height: 20px;
    }

    /* 3D Viewer Canvas */
    .sp-3d-viewer {
        position: absolute;
        inset: 0;
        display: none;
        background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
        border-radius: 8px;
    }
    .sp-3d-viewer.active {
        display: block;
    }
    .sp-3d-viewer canvas {
        width: 100%;
        height: 100%;
    }
    .sp-3d-controls {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 10px;
    }
    .sp-3d-controls button {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .sp-3d-controls button:hover {
        background: rgba(255,255,255,0.3);
    }

    /* Thumbnail Gallery */
    .sp-thumbnails {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding: 10px 0;
    }
    .sp-thumbnail {
        flex: 0 0 80px;
        aspect-ratio: 1;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .sp-thumbnail.active,
    .sp-thumbnail:hover {
        border-color: var(--sp-rose-gold);
    }
    .sp-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* Product Info Section */
    .sp-info {
        padding-top: 20px;
    }

    .sp-collection-badge {
        display: inline-block;
        padding: 6px 16px;
        background: var(--sp-champagne);
        color: var(--sp-obsidian);
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-radius: 3px;
        margin-bottom: 16px;
    }
    .sp-collection-badge.blackrose {
        background: #0A0505;
        color: #DC143C;
    }
    .sp-collection-badge.lovehurts {
        background: #880E4F;
        color: white;
    }

    .sp-title {
        font-size: 2.5rem;
        font-weight: 300;
        margin: 0 0 10px;
        color: var(--sp-obsidian);
        line-height: 1.2;
    }

    .sp-tagline {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 20px;
        font-style: italic;
    }

    .sp-price {
        font-size: 2rem;
        font-weight: 600;
        color: var(--sp-rose-gold);
        margin-bottom: 20px;
    }
    .sp-price del {
        color: #999;
        font-weight: 400;
        font-size: 1.4rem;
        margin-right: 10px;
    }
    .sp-price ins {
        text-decoration: none;
    }
    .sp-price .sale-badge {
        display: inline-block;
        background: #DC143C;
        color: white;
        padding: 4px 10px;
        font-size: 0.8rem;
        border-radius: 3px;
        margin-left: 10px;
        vertical-align: middle;
    }

    /* Ratings */
    .sp-ratings {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 25px;
    }
    .sp-stars {
        color: var(--sp-gold);
        font-size: 1.1rem;
    }
    .sp-review-count {
        color: #666;
        font-size: 0.9rem;
    }
    .sp-review-count a {
        color: var(--sp-rose-gold);
        text-decoration: none;
    }

    /* Short Description */
    .sp-short-description {
        font-size: 1rem;
        line-height: 1.8;
        color: #555;
        margin-bottom: 30px;
        padding-bottom: 30px;
        border-bottom: 1px solid #eee;
    }

    /* Variations */
    .sp-variations {
        margin-bottom: 30px;
    }
    .sp-variation-row {
        margin-bottom: 20px;
    }
    .sp-variation-label {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 10px;
        color: var(--sp-obsidian);
    }
    .sp-size-options,
    .sp-color-options {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .sp-size-btn,
    .sp-color-btn {
        min-width: 50px;
        padding: 12px 20px;
        border: 2px solid #ddd;
        background: white;
        cursor: pointer;
        transition: all 0.3s;
        font-weight: 500;
    }
    .sp-size-btn:hover,
    .sp-size-btn.selected,
    .sp-color-btn:hover,
    .sp-color-btn.selected {
        border-color: var(--sp-rose-gold);
        background: var(--sp-champagne);
    }
    .sp-color-swatch {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 3px solid transparent;
        cursor: pointer;
        transition: all 0.3s;
    }
    .sp-color-swatch:hover,
    .sp-color-swatch.selected {
        border-color: var(--sp-rose-gold);
        transform: scale(1.1);
    }

    /* Quantity & Add to Cart */
    .sp-cart-actions {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
    }
    .sp-quantity {
        display: flex;
        align-items: center;
        border: 2px solid #ddd;
    }
    .sp-qty-btn {
        width: 50px;
        height: 50px;
        border: none;
        background: #f8f8f8;
        cursor: pointer;
        font-size: 1.2rem;
        transition: background 0.3s;
    }
    .sp-qty-btn:hover {
        background: #eee;
    }
    .sp-qty-input {
        width: 60px;
        height: 50px;
        border: none;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 500;
    }

    .sp-add-to-cart {
        flex: 1;
        height: 50px;
        background: var(--sp-rose-gold);
        color: white;
        border: none;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
        transition: all 0.3s;
        position: relative;
        overflow: hidden;
    }
    .sp-add-to-cart:hover {
        background: #a05d68;
    }
    .sp-add-to-cart.adding {
        pointer-events: none;
    }
    .sp-add-to-cart .btn-text {
        transition: opacity 0.3s;
    }
    .sp-add-to-cart.adding .btn-text {
        opacity: 0;
    }
    .sp-add-to-cart .spinner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 24px;
        height: 24px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        opacity: 0;
        animation: none;
    }
    .sp-add-to-cart.adding .spinner {
        opacity: 1;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to { transform: translate(-50%, -50%) rotate(360deg); }
    }

    /* Wishlist Button */
    .sp-wishlist {
        width: 50px;
        height: 50px;
        border: 2px solid #ddd;
        background: white;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .sp-wishlist:hover {
        border-color: var(--sp-rose-gold);
        color: var(--sp-rose-gold);
    }
    .sp-wishlist.active {
        background: var(--sp-rose-gold);
        border-color: var(--sp-rose-gold);
        color: white;
    }

    /* Buy Now Button */
    .sp-buy-now {
        width: 100%;
        height: 55px;
        background: var(--sp-obsidian);
        color: white;
        border: none;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        cursor: pointer;
        transition: all 0.3s;
        margin-bottom: 25px;
    }
    .sp-buy-now:hover {
        background: #333;
    }

    /* Trust Badges */
    .sp-trust-badges {
        display: flex;
        gap: 20px;
        padding: 20px 0;
        border-top: 1px solid #eee;
        border-bottom: 1px solid #eee;
        margin-bottom: 25px;
    }
    .sp-trust-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        color: #666;
    }
    .sp-trust-badge svg {
        width: 20px;
        height: 20px;
        fill: var(--sp-rose-gold);
    }

    /* Accordion */
    .sp-accordion {
        border-top: 1px solid #eee;
    }
    .sp-accordion-item {
        border-bottom: 1px solid #eee;
    }
    .sp-accordion-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        cursor: pointer;
        font-weight: 600;
        color: var(--sp-obsidian);
    }
    .sp-accordion-header svg {
        width: 16px;
        height: 16px;
        transition: transform 0.3s;
    }
    .sp-accordion-item.open .sp-accordion-header svg {
        transform: rotate(180deg);
    }
    .sp-accordion-content {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
    }
    .sp-accordion-item.open .sp-accordion-content {
        max-height: 500px;
    }
    .sp-accordion-inner {
        padding-bottom: 20px;
        color: #555;
        line-height: 1.8;
    }

    /* Social Share */
    .sp-social-share {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-top: 25px;
    }
    .sp-social-share span {
        font-size: 0.9rem;
        color: #666;
    }
    .sp-share-btn {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 1px solid #ddd;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .sp-share-btn:hover {
        border-color: var(--sp-rose-gold);
        color: var(--sp-rose-gold);
    }

    /* Related Products */
    .sp-related {
        padding: 80px 5%;
        background: #f8f8f8;
    }
    .sp-related h2 {
        text-align: center;
        font-size: 2rem;
        font-weight: 300;
        margin-bottom: 50px;
    }
    .sp-related-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 30px;
        max-width: 1400px;
        margin: 0 auto;
    }
    .sp-related-card {
        background: white;
        border-radius: 8px;
        overflow: hidden;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .sp-related-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.1);
    }
    .sp-related-card img {
        width: 100%;
        aspect-ratio: 1;
        object-fit: cover;
    }
    .sp-related-card-info {
        padding: 20px;
    }
    .sp-related-card h3 {
        font-size: 1rem;
        margin: 0 0 8px;
        font-weight: 500;
    }
    .sp-related-card .price {
        color: var(--sp-rose-gold);
        font-weight: 600;
    }

    /* Mobile Responsive */
    @media (max-width: 1024px) {
        .sp-product-container {
            grid-template-columns: 1fr;
            gap: 40px;
        }
        .sp-gallery {
            position: relative;
            top: 0;
        }
        .sp-related-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 600px) {
        .sp-title {
            font-size: 1.8rem;
        }
        .sp-price {
            font-size: 1.6rem;
        }
        .sp-cart-actions {
            flex-wrap: wrap;
        }
        .sp-quantity {
            width: 100%;
            justify-content: center;
        }
        .sp-add-to-cart {
            width: calc(100% - 65px);
        }
        .sp-trust-badges {
            flex-direction: column;
            gap: 15px;
        }
        .sp-related-grid {
            grid-template-columns: 1fr;
        }
    }
</style>

<div class="skyyrose-single-product" data-collection="<?php echo esc_attr($collection); ?>">
    <!-- Breadcrumb -->
    <nav class="sp-breadcrumb">
        <a href="<?php echo home_url(); ?>">Home</a>
        <span>/</span>
        <a href="<?php echo get_permalink(wc_get_page_id('shop')); ?>">Shop</a>
        <span>/</span>
        <?php if ($terms && !is_wp_error($terms)) : ?>
            <a href="<?php echo get_term_link($terms[0]); ?>"><?php echo esc_html($terms[0]->name); ?></a>
            <span>/</span>
        <?php endif; ?>
        <?php echo esc_html($product->get_name()); ?>
    </nav>

    <div class="sp-product-container">
        <!-- Gallery Section -->
        <div class="sp-gallery">
            <div class="sp-main-image" id="main-image-container">
                <?php if ($has_3d_model) : ?>
                    <button class="sp-3d-toggle" id="toggle-3d">
                        <svg class="icon-3d" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                        </svg>
                        View in 3D
                    </button>
                    <div class="sp-3d-viewer" id="product-3d-viewer">
                        <canvas id="product-canvas"></canvas>
                        <div class="sp-3d-controls">
                            <button data-action="rotate">Auto Rotate</button>
                            <button data-action="reset">Reset View</button>
                            <button data-action="close">Close 3D</button>
                        </div>
                    </div>
                <?php endif; ?>

                <?php if ($main_image_id) : ?>
                    <?php echo wp_get_attachment_image($main_image_id, 'large', false, ['id' => 'main-product-image', 'data-zoom' => wp_get_attachment_image_url($main_image_id, 'full')]); ?>
                <?php else : ?>
                    <img src="<?php echo wc_placeholder_img_src(); ?>" alt="<?php echo esc_attr($product->get_name()); ?>" id="main-product-image">
                <?php endif; ?>
                <span class="zoom-hint">Click to zoom</span>
            </div>

            <?php if (count($all_images) > 1) : ?>
                <div class="sp-thumbnails">
                    <?php foreach ($all_images as $index => $image_id) : ?>
                        <div class="sp-thumbnail <?php echo $index === 0 ? 'active' : ''; ?>" data-image-id="<?php echo esc_attr($image_id); ?>">
                            <?php echo wp_get_attachment_image($image_id, 'thumbnail'); ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>

        <!-- Product Info Section -->
        <div class="sp-info">
            <?php if ($collection) : ?>
                <span class="sp-collection-badge <?php echo esc_attr($collection); ?>">
                    <?php echo esc_html(ucwords(str_replace('-', ' ', $collection))); ?> Collection
                </span>
            <?php endif; ?>

            <h1 class="sp-title"><?php echo esc_html($product->get_name()); ?></h1>

            <?php $tagline = get_post_meta($product->get_id(), '_skyyrose_tagline', true); ?>
            <?php if ($tagline) : ?>
                <p class="sp-tagline"><?php echo esc_html($tagline); ?></p>
            <?php endif; ?>

            <div class="sp-price">
                <?php if ($product->is_on_sale()) : ?>
                    <del><?php echo wc_price($product->get_regular_price()); ?></del>
                    <ins><?php echo wc_price($product->get_sale_price()); ?></ins>
                    <?php
                    $discount = round((($product->get_regular_price() - $product->get_sale_price()) / $product->get_regular_price()) * 100);
                    ?>
                    <span class="sale-badge">-<?php echo esc_html($discount); ?>%</span>
                <?php else : ?>
                    <?php echo $product->get_price_html(); ?>
                <?php endif; ?>
            </div>

            <?php if ($product->get_rating_count() > 0) : ?>
                <div class="sp-ratings">
                    <span class="sp-stars">
                        <?php
                        $rating = $product->get_average_rating();
                        for ($i = 1; $i <= 5; $i++) {
                            if ($i <= $rating) {
                                echo '&#9733;';
                            } elseif ($i - 0.5 <= $rating) {
                                echo '&#9734;';
                            } else {
                                echo '&#9734;';
                            }
                        }
                        ?>
                    </span>
                    <span class="sp-review-count">
                        <?php echo esc_html($product->get_rating_count()); ?> reviews
                        <a href="#reviews">Read all</a>
                    </span>
                </div>
            <?php endif; ?>

            <div class="sp-short-description">
                <?php echo wp_kses_post($product->get_short_description()); ?>
            </div>

            <!-- Variations (for variable products) -->
            <?php if ($product->is_type('variable')) : ?>
                <div class="sp-variations">
                    <?php
                    $attributes = $product->get_variation_attributes();
                    foreach ($attributes as $attribute_name => $options) :
                        $label = wc_attribute_label($attribute_name);
                    ?>
                        <div class="sp-variation-row">
                            <div class="sp-variation-label"><?php echo esc_html($label); ?></div>
                            <?php if (strtolower($label) === 'size') : ?>
                                <div class="sp-size-options">
                                    <?php foreach ($options as $option) : ?>
                                        <button class="sp-size-btn" data-attribute="<?php echo esc_attr($attribute_name); ?>" data-value="<?php echo esc_attr($option); ?>">
                                            <?php echo esc_html($option); ?>
                                        </button>
                                    <?php endforeach; ?>
                                </div>
                            <?php elseif (strtolower($label) === 'color') : ?>
                                <div class="sp-color-options">
                                    <?php foreach ($options as $option) : ?>
                                        <div class="sp-color-swatch" data-attribute="<?php echo esc_attr($attribute_name); ?>" data-value="<?php echo esc_attr($option); ?>" style="background-color: <?php echo esc_attr(skyyrose_get_color_hex($option)); ?>;" title="<?php echo esc_attr($option); ?>"></div>
                                    <?php endforeach; ?>
                                </div>
                            <?php else : ?>
                                <div class="sp-size-options">
                                    <?php foreach ($options as $option) : ?>
                                        <button class="sp-size-btn" data-attribute="<?php echo esc_attr($attribute_name); ?>" data-value="<?php echo esc_attr($option); ?>">
                                            <?php echo esc_html($option); ?>
                                        </button>
                                    <?php endforeach; ?>
                                </div>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

            <!-- Quantity & Add to Cart -->
            <div class="sp-cart-actions">
                <div class="sp-quantity">
                    <button class="sp-qty-btn" data-action="decrease">-</button>
                    <input type="number" class="sp-qty-input" value="1" min="1" max="<?php echo esc_attr($product->get_stock_quantity() ?: 99); ?>" id="product-quantity">
                    <button class="sp-qty-btn" data-action="increase">+</button>
                </div>

                <button class="sp-add-to-cart" id="add-to-cart-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                    <span class="btn-text">Add to Cart</span>
                    <span class="spinner"></span>
                </button>

                <button class="sp-wishlist" id="wishlist-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                    </svg>
                </button>
            </div>

            <button class="sp-buy-now" id="buy-now-btn">Buy Now</button>

            <!-- Trust Badges -->
            <div class="sp-trust-badges">
                <div class="sp-trust-badge">
                    <svg viewBox="0 0 24 24"><path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 18l-8-4V8l8 4 8-4v8l-8 4z"/></svg>
                    Free Shipping
                </div>
                <div class="sp-trust-badge">
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    Authentic Guarantee
                </div>
                <div class="sp-trust-badge">
                    <svg viewBox="0 0 24 24"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
                    Easy Returns
                </div>
            </div>

            <!-- Accordion -->
            <div class="sp-accordion">
                <div class="sp-accordion-item">
                    <div class="sp-accordion-header">
                        Description
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                    </div>
                    <div class="sp-accordion-content">
                        <div class="sp-accordion-inner">
                            <?php echo wp_kses_post($product->get_description()); ?>
                        </div>
                    </div>
                </div>

                <div class="sp-accordion-item">
                    <div class="sp-accordion-header">
                        Size Guide
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                    </div>
                    <div class="sp-accordion-content">
                        <div class="sp-accordion-inner">
                            <p><strong>XS:</strong> Chest 32-34", Length 26"</p>
                            <p><strong>S:</strong> Chest 34-36", Length 27"</p>
                            <p><strong>M:</strong> Chest 38-40", Length 28"</p>
                            <p><strong>L:</strong> Chest 42-44", Length 29"</p>
                            <p><strong>XL:</strong> Chest 46-48", Length 30"</p>
                            <p><strong>2XL:</strong> Chest 50-52", Length 31"</p>
                        </div>
                    </div>
                </div>

                <div class="sp-accordion-item">
                    <div class="sp-accordion-header">
                        Shipping & Returns
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"/>
                        </svg>
                    </div>
                    <div class="sp-accordion-content">
                        <div class="sp-accordion-inner">
                            <p><strong>Free Standard Shipping</strong> on orders over $100.</p>
                            <p>Standard delivery: 5-7 business days</p>
                            <p>Express delivery: 2-3 business days (+$15)</p>
                            <p><strong>Returns:</strong> 30-day hassle-free returns. Items must be unworn with tags attached.</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Social Share -->
            <div class="sp-social-share">
                <span>Share:</span>
                <button class="sp-share-btn" data-platform="facebook" aria-label="Share on Facebook">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                    </svg>
                </button>
                <button class="sp-share-btn" data-platform="twitter" aria-label="Share on Twitter">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"/>
                    </svg>
                </button>
                <button class="sp-share-btn" data-platform="pinterest" aria-label="Share on Pinterest">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0a12 12 0 0 0-4.37 23.17c-.1-.9-.2-2.32.04-3.32l1.37-5.8s-.35-.7-.35-1.73c0-1.62.94-2.83 2.1-2.83.99 0 1.47.74 1.47 1.64 0 1-.64 2.5-.96 3.88-.28 1.15.58 2.1 1.72 2.1 2.06 0 3.65-2.17 3.65-5.31 0-2.78-2-4.72-4.85-4.72-3.3 0-5.24 2.48-5.24 5.04 0 1 .38 2.07.87 2.65.1.1.1.2.08.32l-.33 1.35c-.05.2-.17.25-.38.15-1.4-.65-2.28-2.7-2.28-4.35 0-3.53 2.57-6.78 7.4-6.78 3.88 0 6.9 2.77 6.9 6.47 0 3.87-2.44 6.98-5.82 6.98-1.14 0-2.2-.59-2.57-1.3l-.7 2.66c-.25 1-.94 2.25-1.4 3.01A12 12 0 1 0 12 0z"/>
                    </svg>
                </button>
                <button class="sp-share-btn" data-platform="copy" aria-label="Copy link">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Related Products -->
    <?php
    $related_ids = wc_get_related_products($product->get_id(), 4);
    if ($related_ids) :
        $related_products = array_map('wc_get_product', $related_ids);
    ?>
        <section class="sp-related">
            <h2>You May Also Love</h2>
            <div class="sp-related-grid">
                <?php foreach ($related_products as $related) :
                    if (!$related) continue;
                ?>
                    <a href="<?php echo get_permalink($related->get_id()); ?>" class="sp-related-card">
                        <?php echo $related->get_image('woocommerce_thumbnail'); ?>
                        <div class="sp-related-card-info">
                            <h3><?php echo esc_html($related->get_name()); ?></h3>
                            <span class="price"><?php echo $related->get_price_html(); ?></span>
                        </div>
                    </a>
                <?php endforeach; ?>
            </div>
        </section>
    <?php endif; ?>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Thumbnail Gallery
    const thumbnails = document.querySelectorAll('.sp-thumbnail');
    const mainImage = document.getElementById('main-product-image');

    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            thumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            const imageId = this.dataset.imageId;
            const img = this.querySelector('img');
            if (img && mainImage) {
                mainImage.src = img.src.replace('-150x150', '-1024x1024').replace('-100x100', '-1024x1024');
            }
        });
    });

    // Quantity Controls
    const qtyInput = document.getElementById('product-quantity');
    document.querySelectorAll('.sp-qty-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            let value = parseInt(qtyInput.value);
            const max = parseInt(qtyInput.max) || 99;

            if (action === 'increase' && value < max) {
                qtyInput.value = value + 1;
            } else if (action === 'decrease' && value > 1) {
                qtyInput.value = value - 1;
            }
        });
    });

    // Size/Color Selection
    document.querySelectorAll('.sp-size-btn, .sp-color-swatch').forEach(btn => {
        btn.addEventListener('click', function() {
            const attribute = this.dataset.attribute;
            document.querySelectorAll(`[data-attribute="${attribute}"]`).forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // Add to Cart
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const quantity = parseInt(qtyInput.value);

            // Collect variations
            const variations = {};
            document.querySelectorAll('.sp-size-btn.selected, .sp-color-swatch.selected').forEach(selected => {
                variations[selected.dataset.attribute] = selected.dataset.value;
            });

            this.classList.add('adding');

            fetch('<?php echo admin_url('admin-ajax.php'); ?>', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    action: 'skyyrose_add_to_cart',
                    product_id: productId,
                    quantity: quantity,
                    nonce: '<?php echo wp_create_nonce('skyyrose_add_to_cart'); ?>',
                    ...variations
                })
            })
            .then(response => response.json())
            .then(data => {
                this.classList.remove('adding');
                if (data.success) {
                    // Update cart count in header
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount && data.data.cart_count) {
                        cartCount.textContent = data.data.cart_count;
                    }

                    // Show success feedback
                    const btnText = this.querySelector('.btn-text');
                    btnText.textContent = 'Added!';
                    setTimeout(() => {
                        btnText.textContent = 'Add to Cart';
                    }, 2000);
                }
            })
            .catch(error => {
                this.classList.remove('adding');
                console.error('Error:', error);
            });
        });
    }

    // Buy Now
    const buyNowBtn = document.getElementById('buy-now-btn');
    if (buyNowBtn) {
        buyNowBtn.addEventListener('click', function() {
            addToCartBtn.click();
            setTimeout(() => {
                window.location.href = '<?php echo wc_get_checkout_url(); ?>';
            }, 500);
        });
    }

    // Accordion
    document.querySelectorAll('.sp-accordion-header').forEach(header => {
        header.addEventListener('click', function() {
            const item = this.parentElement;
            item.classList.toggle('open');
        });
    });

    // 3D Viewer Toggle
    const toggle3D = document.getElementById('toggle-3d');
    const viewer3D = document.getElementById('product-3d-viewer');
    if (toggle3D && viewer3D) {
        toggle3D.addEventListener('click', function() {
            viewer3D.classList.add('active');
            // Initialize 3D scene if needed
        });

        viewer3D.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.dataset.action;
                if (action === 'close') {
                    viewer3D.classList.remove('active');
                }
            });
        });
    }

    // Social Share
    document.querySelectorAll('.sp-share-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const platform = this.dataset.platform;
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);

            let shareUrl = '';
            switch(platform) {
                case 'facebook':
                    shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                    break;
                case 'twitter':
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                    break;
                case 'pinterest':
                    const image = encodeURIComponent(mainImage?.src || '');
                    shareUrl = `https://pinterest.com/pin/create/button/?url=${url}&media=${image}&description=${title}`;
                    break;
                case 'copy':
                    navigator.clipboard.writeText(window.location.href);
                    alert('Link copied!');
                    return;
            }

            if (shareUrl) {
                window.open(shareUrl, '_blank', 'width=600,height=400');
            }
        });
    });

    // Wishlist
    const wishlistBtn = document.getElementById('wishlist-btn');
    if (wishlistBtn) {
        wishlistBtn.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    }
});
</script>

<?php
get_footer('shop');
