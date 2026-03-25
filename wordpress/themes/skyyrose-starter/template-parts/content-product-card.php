<?php
/**
 * Product Card Template Part
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

global $product;

if (!$product) {
    return;
}

$product_id = $product->get_id();
$collection = skyyrose_get_product_collection($product_id);
?>

<div class="product-card">
    <?php skyyrose_product_badges($product_id); ?>

    <div class="product-image">
        <a href="<?php the_permalink(); ?>">
            <?php if (has_post_thumbnail()) : ?>
                <?php the_post_thumbnail('skyyrose-product', ['class' => 'product-img']); ?>
            <?php else : ?>
                <div class="product-placeholder">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <path d="M21 15l-5-5L5 21"/>
                    </svg>
                </div>
            <?php endif; ?>
        </a>

        <div class="product-actions">
            <button
                class="product-action-btn"
                data-add-to-cart="<?php echo esc_attr($product_id); ?>"
                aria-label="Add to cart"
                title="Add to Cart"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                    <line x1="3" y1="6" x2="21" y2="6"/>
                    <path d="M16 10a4 4 0 01-8 0"/>
                </svg>
            </button>

            <a
                href="<?php the_permalink(); ?>"
                class="product-action-btn"
                aria-label="View product"
                title="Quick View"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
            </a>

            <button
                class="product-action-btn"
                aria-label="Add to wishlist"
                title="Add to Wishlist"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                </svg>
            </button>
        </div>
    </div>

    <div class="product-info">
        <?php if ($collection) : ?>
            <p class="product-collection" style="color: <?php echo esc_attr($collection['color']); ?>">
                <?php echo esc_html($collection['name']); ?>
            </p>
        <?php endif; ?>

        <h3 class="product-name">
            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        </h3>

        <p class="product-price">
            <?php echo $product->get_price_html(); ?>
        </p>
    </div>
</div>
