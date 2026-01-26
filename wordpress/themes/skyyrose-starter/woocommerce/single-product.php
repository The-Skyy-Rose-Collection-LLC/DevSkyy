<?php
/**
 * WooCommerce Single Product Template
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();

global $product;

if (!$product || !$product instanceof WC_Product) {
    get_template_part('template-parts/content', 'none');
    get_footer();
    return;
}

$product_id = $product->get_id();
$collection = skyyrose_get_product_collection($product_id);
$collection_slug = skyyrose_get_product_collection_slug($product_id);
$gallery_ids = $product->get_gallery_image_ids();
$has_gallery = !empty($gallery_ids);
?>

<style>
    :root {
        --product-collection-color: <?php echo esc_attr($collection['color'] ?? 'var(--signature-gold)'); ?>;
    }
</style>

<div class="breadcrumb">
    <div class="container">
        <?php skyyrose_breadcrumbs(); ?>
    </div>
</div>

<section class="product-section">
    <div class="container">
        <div class="product-grid">
            <div class="product-gallery">
                <div class="main-image" id="mainImage">
                    <?php skyyrose_product_badges($product_id); ?>

                    <?php if (has_post_thumbnail()) : ?>
                        <?php the_post_thumbnail('skyyrose-product-large', ['class' => 'gallery-main-img', 'id' => 'galleryMainImg']); ?>
                    <?php else : ?>
                        <div class="product-placeholder large">
                            <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                                <rect x="3" y="3" width="18" height="18" rx="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <path d="M21 15l-5-5L5 21"/>
                            </svg>
                        </div>
                    <?php endif; ?>
                </div>

                <?php if ($has_gallery || has_post_thumbnail()) : ?>
                <div class="thumbnails">
                    <?php if (has_post_thumbnail()) : ?>
                    <button class="thumbnail active" data-image="<?php echo esc_url(get_the_post_thumbnail_url($product_id, 'skyyrose-product-large')); ?>">
                        <?php the_post_thumbnail('thumbnail', ['class' => 'thumb-img']); ?>
                    </button>
                    <?php endif; ?>

                    <?php foreach ($gallery_ids as $image_id) : ?>
                    <button class="thumbnail" data-image="<?php echo esc_url(wp_get_attachment_image_url($image_id, 'skyyrose-product-large')); ?>">
                        <?php echo wp_get_attachment_image($image_id, 'thumbnail', false, ['class' => 'thumb-img']); ?>
                    </button>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
            </div>

            <div class="product-info">
                <?php if ($collection) : ?>
                <a href="<?php echo esc_url(get_term_link($collection_slug, 'product_cat')); ?>" class="collection-link" style="color: var(--product-collection-color);">
                    <?php echo esc_html($collection['name']); ?> Collection
                </a>
                <?php endif; ?>

                <h1 class="product-title"><?php the_title(); ?></h1>

                <p class="product-price"><?php echo $product->get_price_html(); ?></p>

                <div class="product-description">
                    <?php echo wp_kses_post($product->get_short_description() ?: $product->get_description()); ?>
                </div>

                <?php if ($product->is_type('variable')) : ?>
                    <?php woocommerce_variable_add_to_cart(); ?>
                <?php else : ?>
                    <?php if ($product->is_type('simple')) : ?>
                        <?php
                        $attributes = $product->get_attributes();
                        foreach ($attributes as $attribute_name => $attribute) :
                            if (!$attribute->get_visible()) continue;
                            $terms = wc_get_product_terms($product_id, $attribute_name, ['fields' => 'names']);
                            if (empty($terms)) continue;
                        ?>
                        <div class="option-group">
                            <div class="option-label">
                                <span><?php echo esc_html(wc_attribute_label($attribute_name)); ?></span>
                                <?php if (strtolower($attribute_name) === 'pa_size') : ?>
                                <a href="#size-guide" class="size-guide-link"><?php esc_html_e('Size Guide', 'skyyrose'); ?></a>
                                <?php endif; ?>
                            </div>
                            <div class="option-buttons <?php echo esc_attr(sanitize_title($attribute_name)); ?>-options">
                                <?php foreach ($terms as $term) : ?>
                                <button type="button" class="option-btn" data-attribute="<?php echo esc_attr($attribute_name); ?>" data-value="<?php echo esc_attr($term); ?>">
                                    <?php echo esc_html($term); ?>
                                </button>
                                <?php endforeach; ?>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    <?php endif; ?>

                    <div class="quantity-selector">
                        <span class="qty-label"><?php esc_html_e('Quantity', 'skyyrose'); ?></span>
                        <button type="button" class="qty-btn qty-minus" aria-label="<?php esc_attr_e('Decrease quantity', 'skyyrose'); ?>">−</button>
                        <span class="qty-value" id="qtyValue">1</span>
                        <button type="button" class="qty-btn qty-plus" aria-label="<?php esc_attr_e('Increase quantity', 'skyyrose'); ?>">+</button>
                    </div>

                    <div class="product-actions">
                        <button
                            type="button"
                            class="btn btn-primary add-to-cart-btn"
                            data-add-to-cart="<?php echo esc_attr($product_id); ?>"
                            data-quantity="1"
                            <?php echo $product->is_in_stock() ? '' : 'disabled'; ?>
                        >
                            <?php echo $product->is_in_stock() ? esc_html__('Add to Cart', 'skyyrose') : esc_html__('Out of Stock', 'skyyrose'); ?>
                        </button>
                        <button type="button" class="btn btn-wishlist" data-product-id="<?php echo esc_attr($product_id); ?>" aria-label="<?php esc_attr_e('Add to wishlist', 'skyyrose'); ?>">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                            </svg>
                        </button>
                    </div>
                <?php endif; ?>

                <div class="accordion">
                    <div class="accordion-item open">
                        <button class="accordion-header" aria-expanded="true">
                            <h4><?php esc_html_e('Details & Fit', 'skyyrose'); ?></h4>
                            <span class="accordion-icon">+</span>
                        </button>
                        <div class="accordion-content">
                            <div class="accordion-content-inner">
                                <?php
                                $details = get_post_meta($product_id, '_skyyrose_details', true);
                                if ($details) {
                                    echo wp_kses_post($details);
                                } else {
                                    echo wp_kses_post($product->get_description());
                                }
                                ?>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item">
                        <button class="accordion-header" aria-expanded="false">
                            <h4><?php esc_html_e('Materials & Care', 'skyyrose'); ?></h4>
                            <span class="accordion-icon">+</span>
                        </button>
                        <div class="accordion-content">
                            <div class="accordion-content-inner">
                                <?php
                                $care = get_post_meta($product_id, '_skyyrose_care', true);
                                if ($care) {
                                    echo wp_kses_post($care);
                                } else {
                                    ?>
                                    <ul>
                                        <li>Premium quality materials</li>
                                        <li>Machine wash cold, inside out</li>
                                        <li>Tumble dry low</li>
                                        <li>Do not bleach</li>
                                        <li>Iron on low heat if needed</li>
                                    </ul>
                                    <?php
                                }
                                ?>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item">
                        <button class="accordion-header" aria-expanded="false">
                            <h4><?php esc_html_e('Shipping & Returns', 'skyyrose'); ?></h4>
                            <span class="accordion-icon">+</span>
                        </button>
                        <div class="accordion-content">
                            <div class="accordion-content-inner">
                                <ul>
                                    <li>Free shipping on orders over $150</li>
                                    <li>Standard shipping: 5-7 business days</li>
                                    <li>Express shipping: 2-3 business days</li>
                                    <li>30-day return policy on unworn items</li>
                                    <li>Free returns on all domestic orders</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<?php
$related_products = wc_get_related_products($product_id, 4);
if (!empty($related_products)) :
?>
<section class="related-section">
    <div class="container">
        <h2><?php esc_html_e('Complete the Look', 'skyyrose'); ?></h2>
        <div class="related-grid">
            <?php
            foreach ($related_products as $related_id) :
                $related_product = wc_get_product($related_id);
                if (!$related_product) continue;
                $related_collection = skyyrose_get_product_collection($related_id);
            ?>
            <div class="related-card">
                <a href="<?php echo esc_url(get_permalink($related_id)); ?>" class="related-image">
                    <?php echo get_the_post_thumbnail($related_id, 'skyyrose-product', ['class' => 'related-img']); ?>
                </a>
                <div class="related-info">
                    <?php if ($related_collection) : ?>
                    <span class="related-collection" style="color: <?php echo esc_attr($related_collection['color']); ?>">
                        <?php echo esc_html($related_collection['name']); ?>
                    </span>
                    <?php endif; ?>
                    <h3><a href="<?php echo esc_url(get_permalink($related_id)); ?>"><?php echo esc_html($related_product->get_name()); ?></a></h3>
                    <p class="related-price"><?php echo $related_product->get_price_html(); ?></p>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>

<script>
(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        // Gallery thumbnail switching
        var thumbnails = document.querySelectorAll('.thumbnail');
        var mainImg = document.getElementById('galleryMainImg');

        thumbnails.forEach(function(thumb) {
            thumb.addEventListener('click', function() {
                thumbnails.forEach(function(t) { t.classList.remove('active'); });
                thumb.classList.add('active');
                if (mainImg && thumb.dataset.image) {
                    mainImg.src = thumb.dataset.image;
                }
            });
        });

        // Quantity selector
        var qtyValue = document.getElementById('qtyValue');
        var qtyMinus = document.querySelector('.qty-minus');
        var qtyPlus = document.querySelector('.qty-plus');
        var addToCartBtn = document.querySelector('.add-to-cart-btn');
        var qty = 1;

        if (qtyMinus) {
            qtyMinus.addEventListener('click', function() {
                if (qty > 1) {
                    qty--;
                    qtyValue.textContent = qty;
                    if (addToCartBtn) {
                        addToCartBtn.dataset.quantity = qty;
                    }
                }
            });
        }

        if (qtyPlus) {
            qtyPlus.addEventListener('click', function() {
                qty++;
                qtyValue.textContent = qty;
                if (addToCartBtn) {
                    addToCartBtn.dataset.quantity = qty;
                }
            });
        }

        // Option buttons
        document.querySelectorAll('.option-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var siblings = btn.parentElement.querySelectorAll('.option-btn');
                siblings.forEach(function(s) { s.classList.remove('active'); });
                btn.classList.add('active');
            });
        });

        // Accordions
        document.querySelectorAll('.accordion-header').forEach(function(header) {
            header.addEventListener('click', function() {
                var item = header.parentElement;
                var isOpen = item.classList.contains('open');

                // Close all
                document.querySelectorAll('.accordion-item').forEach(function(i) {
                    i.classList.remove('open');
                    i.querySelector('.accordion-header').setAttribute('aria-expanded', 'false');
                });

                // Toggle current
                if (!isOpen) {
                    item.classList.add('open');
                    header.setAttribute('aria-expanded', 'true');
                }
            });
        });
    });
})();
</script>

<?php get_footer(); ?>
