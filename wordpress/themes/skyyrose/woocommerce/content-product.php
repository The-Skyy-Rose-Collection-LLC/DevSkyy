<?php
/**
 * The template for displaying product content within loops
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/content-product.php.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

global $product;

// Ensure visibility.
if (empty($product) || !$product->is_visible()) {
    return;
}

// Get product meta
$collection = get_post_meta($product->get_id(), '_skyyrose_collection', true);
$collection_data = $collection ? skyyrose_get_collection($collection) : null;
$has_3d_model = get_post_meta($product->get_id(), '_skyyrose_3d_model', true);
$preorder_enabled = get_post_meta($product->get_id(), '_preorder_enabled', true) === 'yes';
$preorder_status = get_post_meta($product->get_id(), '_preorder_status', true);

// Gallery images for hover effect
$gallery_ids = $product->get_gallery_image_ids();
$hover_image_id = !empty($gallery_ids) ? $gallery_ids[0] : null;

// Dynamic styles for collection theming
$card_styles = '';
if ($collection_data) {
    $card_styles = sprintf(
        '--card-accent: %s; --card-secondary: %s;',
        esc_attr($collection_data['colors']['primary']),
        esc_attr($collection_data['colors']['secondary'])
    );
}
?>

<article <?php wc_product_class('skyyrose-product-card glass-card', $product); ?> style="<?php echo esc_attr($card_styles); ?>">

    <!-- Product Image Section -->
    <div class="product-card-image">
        <a href="<?php the_permalink(); ?>" class="product-image-link" aria-label="<?php echo esc_attr(sprintf(__('View %s', 'skyyrose'), $product->get_name())); ?>">

            <!-- Primary Image -->
            <div class="product-image primary-image">
                <?php if ($product->get_image_id()) : ?>
                    <?php echo $product->get_image('skyyrose-product', [
                        'class' => 'product-thumb',
                        'loading' => 'lazy',
                    ]); ?>
                <?php else : ?>
                    <div class="product-image-placeholder">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                            <rect x="3" y="3" width="18" height="18" rx="2"/>
                            <circle cx="8.5" cy="8.5" r="1.5"/>
                            <path d="M21 15l-5-5L5 21"/>
                        </svg>
                    </div>
                <?php endif; ?>
            </div>

            <!-- Hover Image (if gallery exists) -->
            <?php if ($hover_image_id) : ?>
            <div class="product-image hover-image">
                <?php echo wp_get_attachment_image($hover_image_id, 'skyyrose-product', false, [
                    'class' => 'product-thumb-hover',
                    'loading' => 'lazy',
                ]); ?>
            </div>
            <?php endif; ?>
        </a>

        <!-- Badges Layer -->
        <div class="product-badges">
            <?php if ($collection_data) : ?>
            <span class="product-badge collection-badge" style="--badge-color: <?php echo esc_attr($collection_data['colors']['primary']); ?>">
                <?php echo esc_html($collection_data['name']); ?>
            </span>
            <?php endif; ?>

            <?php if ($product->is_on_sale()) : ?>
            <span class="product-badge sale-badge">
                <?php
                if ($product->is_type('variable')) {
                    $percentages = [];
                    $prices = $product->get_variation_prices();
                    foreach ($prices['price'] as $key => $price) {
                        if ($prices['regular_price'][$key] > 0) {
                            $percentages[] = round(100 - ($prices['sale_price'][$key] / $prices['regular_price'][$key] * 100));
                        }
                    }
                    $percentage = max($percentages);
                } else {
                    $percentage = round(100 - ($product->get_sale_price() / $product->get_regular_price() * 100));
                }
                printf(esc_html__('-%d%%', 'skyyrose'), $percentage);
                ?>
            </span>
            <?php endif; ?>

            <?php if ($preorder_enabled) : ?>
            <span class="product-badge preorder-badge <?php echo esc_attr($preorder_status); ?>">
                <?php
                $status_labels = [
                    'blooming_soon' => __('Coming Soon', 'skyyrose'),
                    'now_blooming'  => __('Pre-Order', 'skyyrose'),
                    'available'     => __('New', 'skyyrose'),
                ];
                echo esc_html($status_labels[$preorder_status] ?? __('Pre-Order', 'skyyrose'));
                ?>
            </span>
            <?php endif; ?>

            <?php if ($has_3d_model) : ?>
            <span class="product-badge ar-badge" title="<?php esc_attr_e('3D & AR Available', 'skyyrose'); ?>">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                    <path d="M2 17L12 22L22 17"/>
                    <path d="M2 12L12 17L22 12"/>
                </svg>
                <span class="sr-only"><?php esc_html_e('3D View Available', 'skyyrose'); ?></span>
            </span>
            <?php endif; ?>

            <?php if (!$product->is_in_stock()) : ?>
            <span class="product-badge out-of-stock-badge">
                <?php esc_html_e('Sold Out', 'skyyrose'); ?>
            </span>
            <?php endif; ?>
        </div>

        <!-- Quick Actions Overlay -->
        <div class="product-quick-actions">
            <!-- Quick View Button -->
            <button type="button"
                    class="quick-action-btn quick-view-btn magnetic-btn"
                    data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                    aria-label="<?php esc_attr_e('Quick view', 'skyyrose'); ?>"
                    title="<?php esc_attr_e('Quick View', 'skyyrose'); ?>">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
            </button>

            <!-- Wishlist Button -->
            <button type="button"
                    class="quick-action-btn wishlist-btn magnetic-btn"
                    data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                    aria-label="<?php esc_attr_e('Add to wishlist', 'skyyrose'); ?>"
                    title="<?php esc_attr_e('Add to Wishlist', 'skyyrose'); ?>">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                </svg>
            </button>

            <?php if ($has_3d_model) : ?>
            <!-- 3D View Button -->
            <button type="button"
                    class="quick-action-btn view-3d-btn magnetic-btn"
                    data-model-url="<?php echo esc_url($has_3d_model); ?>"
                    data-product-name="<?php echo esc_attr($product->get_name()); ?>"
                    aria-label="<?php esc_attr_e('View in 3D', 'skyyrose'); ?>"
                    title="<?php esc_attr_e('View in 3D', 'skyyrose'); ?>">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                    <path d="M2 17L12 22L22 17"/>
                    <path d="M2 12L12 17L22 12"/>
                </svg>
            </button>
            <?php endif; ?>
        </div>
    </div>

    <!-- Product Info Section -->
    <div class="product-card-info">
        <!-- Product Name -->
        <h3 class="product-card-title">
            <a href="<?php the_permalink(); ?>">
                <?php the_title(); ?>
            </a>
        </h3>

        <!-- Product Price -->
        <div class="product-card-price">
            <?php echo $product->get_price_html(); ?>
        </div>

        <!-- Product Rating (if enabled and has reviews) -->
        <?php if (wc_review_ratings_enabled() && $product->get_average_rating()) : ?>
        <div class="product-card-rating">
            <?php
            $rating = $product->get_average_rating();
            $review_count = $product->get_review_count();
            ?>
            <div class="star-rating" role="img" aria-label="<?php printf(esc_attr__('Rated %s out of 5', 'skyyrose'), $rating); ?>">
                <?php for ($i = 1; $i <= 5; $i++) :
                    $fill_class = $i <= floor($rating) ? 'filled' : ($i - 0.5 <= $rating ? 'half-filled' : 'empty');
                ?>
                <svg class="star <?php echo esc_attr($fill_class); ?>" width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <?php endfor; ?>
            </div>
            <span class="review-count">(<?php echo esc_html($review_count); ?>)</span>
        </div>
        <?php endif; ?>

        <!-- Swatches (for variable products) -->
        <?php if ($product->is_type('variable')) :
            $attributes = $product->get_variation_attributes();
            $color_attribute = null;

            // Look for color attribute
            foreach ($attributes as $attr_name => $options) {
                if (stripos($attr_name, 'color') !== false || stripos($attr_name, 'colour') !== false) {
                    $color_attribute = ['name' => $attr_name, 'options' => $options];
                    break;
                }
            }

            if ($color_attribute && !empty($color_attribute['options'])) :
        ?>
        <div class="product-color-swatches" role="group" aria-label="<?php esc_attr_e('Available colors', 'skyyrose'); ?>">
            <?php
            $shown = 0;
            foreach ($color_attribute['options'] as $option) :
                if ($shown >= 4) {
                    $remaining = count($color_attribute['options']) - 4;
                    echo '<span class="swatch-more">+' . $remaining . '</span>';
                    break;
                }

                // Try to get color from term meta
                $color_hex = '';
                $term = get_term_by('slug', $option, $color_attribute['name']);
                if ($term) {
                    $color_hex = get_term_meta($term->term_id, 'color_hex', true);
                }

                // Fallback color mapping
                if (!$color_hex) {
                    $color_map = [
                        'black' => '#0A0A0A',
                        'white' => '#FFFFFF',
                        'red' => '#DC143C',
                        'pink' => '#B76E79',
                        'gold' => '#C9A962',
                        'silver' => '#C0C0C0',
                        'navy' => '#1A1A2E',
                        'rose' => '#B76E79',
                    ];
                    $color_key = strtolower($option);
                    $color_hex = $color_map[$color_key] ?? '#888888';
                }
            ?>
            <span class="color-swatch"
                  style="--swatch-color: <?php echo esc_attr($color_hex); ?>"
                  title="<?php echo esc_attr(ucfirst($option)); ?>"
                  role="img"
                  aria-label="<?php echo esc_attr(ucfirst($option)); ?>">
            </span>
            <?php
                $shown++;
            endforeach;
            ?>
        </div>
        <?php
            endif;
        endif;
        ?>

        <!-- Add to Cart Button -->
        <div class="product-card-actions">
            <?php if ($product->is_in_stock() && $product->is_purchasable()) : ?>
                <?php if ($product->is_type('simple')) : ?>
                    <!-- AJAX Add to Cart for Simple Products -->
                    <button type="button"
                            class="add-to-cart-btn ajax-add-to-cart magnetic-btn"
                            data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                            data-product-sku="<?php echo esc_attr($product->get_sku()); ?>"
                            data-quantity="1"
                            aria-label="<?php echo esc_attr(sprintf(__('Add %s to cart', 'skyyrose'), $product->get_name())); ?>">
                        <span class="btn-text">
                            <?php
                            if ($preorder_enabled && $preorder_status === 'blooming_soon') {
                                esc_html_e('Join Waitlist', 'skyyrose');
                            } elseif ($preorder_enabled) {
                                esc_html_e('Pre-Order', 'skyyrose');
                            } else {
                                esc_html_e('Add to Bag', 'skyyrose');
                            }
                            ?>
                        </span>
                        <span class="btn-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                                <path d="M3 6h18"/>
                                <path d="M16 10a4 4 0 01-8 0"/>
                            </svg>
                        </span>
                        <span class="btn-loading" hidden>
                            <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
                                <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </span>
                        <span class="btn-success" hidden>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 6L9 17l-5-5"/>
                            </svg>
                        </span>
                    </button>
                <?php else : ?>
                    <!-- Select Options for Variable/Other Products -->
                    <a href="<?php the_permalink(); ?>"
                       class="add-to-cart-btn select-options-btn magnetic-btn"
                       aria-label="<?php echo esc_attr(sprintf(__('Select options for %s', 'skyyrose'), $product->get_name())); ?>">
                        <span class="btn-text">
                            <?php esc_html_e('Select Options', 'skyyrose'); ?>
                        </span>
                        <span class="btn-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M5 12h14M12 5l7 7-7 7"/>
                            </svg>
                        </span>
                    </a>
                <?php endif; ?>
            <?php else : ?>
                <!-- Out of Stock -->
                <button type="button" class="add-to-cart-btn out-of-stock-btn" disabled>
                    <span class="btn-text"><?php esc_html_e('Sold Out', 'skyyrose'); ?></span>
                </button>
            <?php endif; ?>
        </div>
    </div>
</article>
