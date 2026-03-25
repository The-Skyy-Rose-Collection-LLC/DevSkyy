<?php
/**
 * The Template for displaying all single products
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/single-product.php.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header('shop');

global $product;

// Get product meta
$collection = get_post_meta($product->get_id(), '_skyyrose_collection', true);
$collection_data = $collection ? skyyrose_get_collection($collection) : null;
$has_3d_model = get_post_meta($product->get_id(), '_skyyrose_3d_model', true);
$gallery_ids = $product->get_gallery_image_ids();
$main_image_id = $product->get_image_id();

// Pre-order status
$preorder_enabled = get_post_meta($product->get_id(), '_preorder_enabled', true) === 'yes';
$preorder_status = get_post_meta($product->get_id(), '_preorder_status', true);

// Dynamic CSS variables for collection theming
$collection_css = '';
if ($collection_data) {
    $collection_css = sprintf(
        '--collection-primary: %s; --collection-secondary: %s; --collection-accent: %s;',
        esc_attr($collection_data['colors']['primary']),
        esc_attr($collection_data['colors']['secondary']),
        esc_attr($collection_data['colors']['accent'])
    );
}
?>

<?php do_action('woocommerce_before_main_content'); ?>

<main id="product-<?php the_ID(); ?>"
      <?php wc_product_class('skyyrose-single-product', $product); ?>
      style="<?php echo esc_attr($collection_css); ?>"
      data-gsap="fade-up">

    <!-- Breadcrumb Navigation -->
    <nav class="product-breadcrumb container" aria-label="<?php esc_attr_e('Breadcrumb', 'skyyrose'); ?>">
        <ol class="breadcrumb-list" itemscope itemtype="https://schema.org/BreadcrumbList">
            <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <a href="<?php echo esc_url(home_url('/')); ?>" itemprop="item">
                    <span itemprop="name"><?php esc_html_e('Home', 'skyyrose'); ?></span>
                </a>
                <meta itemprop="position" content="1">
            </li>
            <li class="breadcrumb-separator" aria-hidden="true">/</li>
            <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" itemprop="item">
                    <span itemprop="name"><?php esc_html_e('Shop', 'skyyrose'); ?></span>
                </a>
                <meta itemprop="position" content="2">
            </li>
            <?php if ($collection_data) : ?>
                <li class="breadcrumb-separator" aria-hidden="true">/</li>
                <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                    <a href="<?php echo esc_url(add_query_arg('collection', $collection, wc_get_page_permalink('shop'))); ?>" itemprop="item">
                        <span itemprop="name"><?php echo esc_html($collection_data['name']); ?></span>
                    </a>
                    <meta itemprop="position" content="3">
                </li>
            <?php endif; ?>
            <li class="breadcrumb-separator" aria-hidden="true">/</li>
            <li class="breadcrumb-item breadcrumb-current" aria-current="page" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <span itemprop="name"><?php the_title(); ?></span>
                <meta itemprop="position" content="<?php echo $collection_data ? '4' : '3'; ?>">
            </li>
        </ol>
    </nav>

    <div class="product-layout container">
        <!-- Left Column: Gallery & 3D Viewer -->
        <div class="product-gallery-column" data-gsap="fade-right">

            <?php if ($has_3d_model) : ?>
            <!-- 3D Model Viewer Section -->
            <div class="product-3d-section glass-card" id="product-3d-viewer">
                <div class="viewer-header">
                    <h3 class="viewer-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                            <path d="M2 17L12 22L22 17"/>
                            <path d="M2 12L12 17L22 12"/>
                        </svg>
                        3D View
                    </h3>
                    <div class="viewer-controls">
                        <button type="button" class="viewer-control-btn" data-action="rotate" title="<?php esc_attr_e('Auto Rotate', 'skyyrose'); ?>">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                <path d="M12 8v4l3 3"/>
                            </svg>
                        </button>
                        <button type="button" class="viewer-control-btn" data-action="fullscreen" title="<?php esc_attr_e('Fullscreen', 'skyyrose'); ?>">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <model-viewer
                    src="<?php echo esc_url($has_3d_model); ?>"
                    alt="<?php echo esc_attr($product->get_name()); ?> 3D Model"
                    ar
                    ar-modes="webxr scene-viewer quick-look"
                    camera-controls
                    touch-action="pan-y"
                    auto-rotate
                    shadow-intensity="1"
                    exposure="0.8"
                    environment-image="neutral"
                    camera-orbit="45deg 55deg 2.5m"
                    min-camera-orbit="auto auto 1m"
                    max-camera-orbit="auto auto 5m"
                    class="skyyrose-model-viewer"
                    loading="lazy"
                    reveal="auto"
                    poster="<?php echo $main_image_id ? esc_url(wp_get_attachment_image_url($main_image_id, 'skyyrose-product')) : ''; ?>"
                >
                    <!-- AR Button -->
                    <button slot="ar-button" class="ar-quick-look-btn magnetic-btn" aria-label="<?php esc_attr_e('View in AR', 'skyyrose'); ?>">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"/>
                            <path d="M12 18V6M6 12H18" stroke-linecap="round"/>
                        </svg>
                        <span><?php esc_html_e('View in Your Space', 'skyyrose'); ?></span>
                    </button>

                    <!-- Loading Progress -->
                    <div slot="progress-bar" class="model-progress">
                        <div class="progress-track">
                            <div class="progress-fill"></div>
                        </div>
                    </div>
                </model-viewer>

                <!-- AR Quick Look Fallback for iOS -->
                <?php if (wp_is_mobile()) : ?>
                <a href="<?php echo esc_url($has_3d_model); ?>"
                   rel="ar"
                   class="ar-fallback-link"
                   download="<?php echo esc_attr(sanitize_file_name($product->get_name())); ?>.usdz">
                    <img src="<?php echo $main_image_id ? esc_url(wp_get_attachment_image_url($main_image_id, 'skyyrose-product-thumb')) : ''; ?>" alt="">
                </a>
                <?php endif; ?>
            </div>
            <?php endif; ?>

            <!-- Image Gallery -->
            <div class="product-gallery glass-card">
                <!-- Main Image Display -->
                <div class="gallery-main-wrapper">
                    <?php if ($collection_data) : ?>
                    <span class="product-collection-badge" style="--badge-color: <?php echo esc_attr($collection_data['colors']['primary']); ?>">
                        <?php echo esc_html($collection_data['name']); ?>
                    </span>
                    <?php endif; ?>

                    <div class="gallery-main-image" id="main-product-image">
                        <?php if ($main_image_id) : ?>
                            <?php echo wp_get_attachment_image($main_image_id, 'skyyrose-product', false, [
                                'class' => 'main-image current',
                                'data-zoom' => wp_get_attachment_image_url($main_image_id, 'full'),
                                'id' => 'primary-image',
                            ]); ?>
                        <?php else : ?>
                            <div class="no-image-placeholder">
                                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                                    <circle cx="8.5" cy="8.5" r="1.5"/>
                                    <path d="M21 15l-5-5L5 21"/>
                                </svg>
                            </div>
                        <?php endif; ?>
                    </div>

                    <!-- Image Zoom Lens -->
                    <div class="image-zoom-lens" id="zoom-lens" aria-hidden="true"></div>
                </div>

                <!-- Thumbnail Navigation -->
                <?php if ($main_image_id || !empty($gallery_ids)) : ?>
                <div class="gallery-thumbnails" role="listbox" aria-label="<?php esc_attr_e('Product images', 'skyyrose'); ?>">
                    <?php if ($main_image_id) : ?>
                    <button type="button"
                            class="gallery-thumb active"
                            data-image-id="<?php echo esc_attr($main_image_id); ?>"
                            data-full-src="<?php echo esc_url(wp_get_attachment_image_url($main_image_id, 'full')); ?>"
                            data-large-src="<?php echo esc_url(wp_get_attachment_image_url($main_image_id, 'skyyrose-product')); ?>"
                            role="option"
                            aria-selected="true"
                            aria-label="<?php esc_attr_e('Main product image', 'skyyrose'); ?>">
                        <?php echo wp_get_attachment_image($main_image_id, 'skyyrose-product-thumb'); ?>
                    </button>
                    <?php endif; ?>

                    <?php foreach ($gallery_ids as $index => $gallery_id) : ?>
                    <button type="button"
                            class="gallery-thumb"
                            data-image-id="<?php echo esc_attr($gallery_id); ?>"
                            data-full-src="<?php echo esc_url(wp_get_attachment_image_url($gallery_id, 'full')); ?>"
                            data-large-src="<?php echo esc_url(wp_get_attachment_image_url($gallery_id, 'skyyrose-product')); ?>"
                            role="option"
                            aria-selected="false"
                            aria-label="<?php printf(esc_attr__('Product image %d', 'skyyrose'), $index + 2); ?>">
                        <?php echo wp_get_attachment_image($gallery_id, 'skyyrose-product-thumb'); ?>
                    </button>
                    <?php endforeach; ?>

                    <?php if ($has_3d_model) : ?>
                    <button type="button"
                            class="gallery-thumb gallery-thumb-3d"
                            data-view="3d"
                            role="option"
                            aria-selected="false"
                            aria-label="<?php esc_attr_e('View 3D model', 'skyyrose'); ?>">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                            <path d="M2 17L12 22L22 17"/>
                            <path d="M2 12L12 17L22 12"/>
                        </svg>
                        <span>3D</span>
                    </button>
                    <?php endif; ?>
                </div>
                <?php endif; ?>
            </div>
        </div>

        <!-- Right Column: Product Info -->
        <div class="product-info-column" data-gsap="fade-left">
            <div class="product-info glass-card">

                <!-- Product Header -->
                <header class="product-header">
                    <?php if ($preorder_enabled) : ?>
                    <div class="preorder-badge <?php echo esc_attr($preorder_status); ?>">
                        <?php
                        $status_labels = [
                            'blooming_soon' => __('Blooming Soon', 'skyyrose'),
                            'now_blooming'  => __('Now Blooming', 'skyyrose'),
                            'available'     => __('Available', 'skyyrose'),
                        ];
                        echo esc_html($status_labels[$preorder_status] ?? $preorder_status);
                        ?>
                    </div>
                    <?php endif; ?>

                    <h1 class="product-title"><?php the_title(); ?></h1>

                    <div class="product-price-wrapper">
                        <?php echo $product->get_price_html(); ?>
                    </div>

                    <?php if ($product->get_short_description()) : ?>
                    <div class="product-short-description">
                        <?php echo wp_kses_post($product->get_short_description()); ?>
                    </div>
                    <?php endif; ?>
                </header>

                <!-- Product Meta Info -->
                <div class="product-meta-info">
                    <?php if ($product->get_sku()) : ?>
                    <div class="meta-item">
                        <span class="meta-label"><?php esc_html_e('SKU:', 'skyyrose'); ?></span>
                        <span class="meta-value"><?php echo esc_html($product->get_sku()); ?></span>
                    </div>
                    <?php endif; ?>

                    <?php if ($product->is_in_stock()) : ?>
                    <div class="meta-item stock-status in-stock">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 6L9 17L4 12"/>
                        </svg>
                        <span><?php esc_html_e('In Stock', 'skyyrose'); ?></span>
                    </div>
                    <?php else : ?>
                    <div class="meta-item stock-status out-of-stock">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                        <span><?php esc_html_e('Out of Stock', 'skyyrose'); ?></span>
                    </div>
                    <?php endif; ?>
                </div>

                <!-- Size Guide Trigger -->
                <button type="button" class="size-guide-trigger magnetic-btn" id="size-guide-btn" aria-haspopup="dialog">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M21 3H3v18h18V3z"/>
                        <path d="M3 9h18M9 21V9"/>
                    </svg>
                    <span><?php esc_html_e('Size Guide', 'skyyrose'); ?></span>
                </button>

                <!-- Add to Cart Form -->
                <div class="product-add-to-cart">
                    <?php
                    /**
                     * Hook: woocommerce_single_product_summary
                     * Includes: add to cart forms, variations, etc.
                     */
                    remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_title', 5);
                    remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_price', 10);
                    remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_excerpt', 20);
                    remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_meta', 40);

                    do_action('woocommerce_single_product_summary');
                    ?>
                </div>

                <!-- Product Actions -->
                <div class="product-actions">
                    <button type="button" class="action-btn wishlist-btn magnetic-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                        </svg>
                        <span><?php esc_html_e('Add to Wishlist', 'skyyrose'); ?></span>
                    </button>

                    <button type="button" class="action-btn share-btn magnetic-btn" data-url="<?php echo esc_url(get_permalink()); ?>" data-title="<?php echo esc_attr($product->get_name()); ?>">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="18" cy="5" r="3"/>
                            <circle cx="6" cy="12" r="3"/>
                            <circle cx="18" cy="19" r="3"/>
                            <path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98"/>
                        </svg>
                        <span><?php esc_html_e('Share', 'skyyrose'); ?></span>
                    </button>
                </div>

                <!-- Product Description Accordion -->
                <div class="product-accordions">
                    <?php if ($product->get_description()) : ?>
                    <details class="product-accordion glass-accordion" open>
                        <summary class="accordion-header">
                            <span><?php esc_html_e('Description', 'skyyrose'); ?></span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M6 9l6 6 6-6"/>
                            </svg>
                        </summary>
                        <div class="accordion-content">
                            <?php echo wp_kses_post($product->get_description()); ?>
                        </div>
                    </details>
                    <?php endif; ?>

                    <?php
                    $attributes = $product->get_attributes();
                    if (!empty($attributes)) :
                    ?>
                    <details class="product-accordion glass-accordion">
                        <summary class="accordion-header">
                            <span><?php esc_html_e('Details & Care', 'skyyrose'); ?></span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M6 9l6 6 6-6"/>
                            </svg>
                        </summary>
                        <div class="accordion-content">
                            <table class="product-attributes">
                                <?php foreach ($attributes as $attribute) :
                                    if (!$attribute->get_visible()) continue;
                                ?>
                                <tr>
                                    <th><?php echo esc_html(wc_attribute_label($attribute->get_name())); ?></th>
                                    <td><?php
                                        $values = $attribute->is_taxonomy()
                                            ? wc_get_product_terms($product->get_id(), $attribute->get_name(), ['fields' => 'names'])
                                            : $attribute->get_options();
                                        echo esc_html(implode(', ', $values));
                                    ?></td>
                                </tr>
                                <?php endforeach; ?>
                            </table>
                        </div>
                    </details>
                    <?php endif; ?>

                    <details class="product-accordion glass-accordion">
                        <summary class="accordion-header">
                            <span><?php esc_html_e('Shipping & Returns', 'skyyrose'); ?></span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M6 9l6 6 6-6"/>
                            </svg>
                        </summary>
                        <div class="accordion-content">
                            <ul class="shipping-info">
                                <li>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M20 6L9 17L4 12"/>
                                    </svg>
                                    <?php esc_html_e('Free shipping on orders over $150', 'skyyrose'); ?>
                                </li>
                                <li>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M20 6L9 17L4 12"/>
                                    </svg>
                                    <?php esc_html_e('Standard shipping: 3-5 business days', 'skyyrose'); ?>
                                </li>
                                <li>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M20 6L9 17L4 12"/>
                                    </svg>
                                    <?php esc_html_e('Express shipping: 1-2 business days', 'skyyrose'); ?>
                                </li>
                                <li>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M20 6L9 17L4 12"/>
                                    </svg>
                                    <?php esc_html_e('30-day returns on unworn items', 'skyyrose'); ?>
                                </li>
                            </ul>
                        </div>
                    </details>
                </div>

                <!-- Trust Badges -->
                <div class="trust-badges">
                    <div class="trust-badge">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                        <span><?php esc_html_e('Secure Checkout', 'skyyrose'); ?></span>
                    </div>
                    <div class="trust-badge">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <rect x="1" y="4" width="22" height="16" rx="2"/>
                            <path d="M1 10h22"/>
                        </svg>
                        <span><?php esc_html_e('All Cards Accepted', 'skyyrose'); ?></span>
                    </div>
                    <div class="trust-badge">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        <span><?php esc_html_e('Oakland, CA', 'skyyrose'); ?></span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Related Products Section -->
    <section class="related-products-section section" data-gsap="fade-up">
        <div class="container">
            <header class="section-header">
                <h2 class="section-title"><?php esc_html_e('You May Also Love', 'skyyrose'); ?></h2>
                <p class="section-subtitle"><?php esc_html_e('Curated pieces to complete your look', 'skyyrose'); ?></p>
            </header>

            <?php
            $related_products = wc_get_related_products($product->get_id(), 4);

            if (!empty($related_products)) :
                $args = [
                    'post_type'      => 'product',
                    'posts_per_page' => 4,
                    'post__in'       => $related_products,
                    'orderby'        => 'post__in',
                ];

                $related_query = new WP_Query($args);

                if ($related_query->have_posts()) :
            ?>
            <div class="products-grid related-products">
                <?php
                while ($related_query->have_posts()) :
                    $related_query->the_post();
                    global $product;
                    wc_get_template_part('content', 'product');
                endwhile;
                ?>
            </div>
            <?php
                endif;
                wp_reset_postdata();
            endif;
            ?>
        </div>
    </section>

</main>

<!-- Size Guide Modal -->
<div class="size-guide-modal glass-modal" id="size-guide-modal" role="dialog" aria-modal="true" aria-labelledby="size-guide-title" hidden>
    <div class="modal-backdrop" data-close-modal></div>
    <div class="modal-content glass-card">
        <header class="modal-header">
            <h3 id="size-guide-title"><?php esc_html_e('Size Guide', 'skyyrose'); ?></h3>
            <button type="button" class="modal-close magnetic-btn" data-close-modal aria-label="<?php esc_attr_e('Close size guide', 'skyyrose'); ?>">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </header>
        <div class="modal-body">
            <div class="size-tabs" role="tablist">
                <button type="button" role="tab" class="size-tab active" data-tab="women" aria-selected="true"><?php esc_html_e('Women', 'skyyrose'); ?></button>
                <button type="button" role="tab" class="size-tab" data-tab="men" aria-selected="false"><?php esc_html_e('Men', 'skyyrose'); ?></button>
            </div>

            <div class="size-chart" role="tabpanel" data-panel="women">
                <table>
                    <thead>
                        <tr>
                            <th><?php esc_html_e('Size', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('US', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('UK', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('EU', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('Bust (in)', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('Waist (in)', 'skyyrose'); ?></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>XS</td><td>0-2</td><td>4-6</td><td>32-34</td><td>31-32</td><td>23-24</td></tr>
                        <tr><td>S</td><td>4-6</td><td>8-10</td><td>36-38</td><td>33-34</td><td>25-26</td></tr>
                        <tr><td>M</td><td>8-10</td><td>12-14</td><td>40-42</td><td>35-36</td><td>27-28</td></tr>
                        <tr><td>L</td><td>12-14</td><td>16-18</td><td>44-46</td><td>37-39</td><td>29-31</td></tr>
                        <tr><td>XL</td><td>16-18</td><td>20-22</td><td>48-50</td><td>40-42</td><td>32-34</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="size-chart" role="tabpanel" data-panel="men" hidden>
                <table>
                    <thead>
                        <tr>
                            <th><?php esc_html_e('Size', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('US', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('UK', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('EU', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('Chest (in)', 'skyyrose'); ?></th>
                            <th><?php esc_html_e('Waist (in)', 'skyyrose'); ?></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>S</td><td>34-36</td><td>34-36</td><td>44-46</td><td>34-36</td><td>28-30</td></tr>
                        <tr><td>M</td><td>38-40</td><td>38-40</td><td>48-50</td><td>38-40</td><td>31-33</td></tr>
                        <tr><td>L</td><td>42-44</td><td>42-44</td><td>52-54</td><td>42-44</td><td>34-36</td></tr>
                        <tr><td>XL</td><td>46-48</td><td>46-48</td><td>56-58</td><td>46-48</td><td>37-39</td></tr>
                        <tr><td>XXL</td><td>50-52</td><td>50-52</td><td>60-62</td><td>50-52</td><td>40-42</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="size-guide-tips">
                <h4><?php esc_html_e('How to Measure', 'skyyrose'); ?></h4>
                <ul>
                    <li><strong><?php esc_html_e('Bust/Chest:', 'skyyrose'); ?></strong> <?php esc_html_e('Measure around the fullest part of your chest', 'skyyrose'); ?></li>
                    <li><strong><?php esc_html_e('Waist:', 'skyyrose'); ?></strong> <?php esc_html_e('Measure around your natural waistline', 'skyyrose'); ?></li>
                    <li><strong><?php esc_html_e('Hips:', 'skyyrose'); ?></strong> <?php esc_html_e('Measure around the fullest part of your hips', 'skyyrose'); ?></li>
                </ul>
            </div>
        </div>
    </div>
</div>

<?php do_action('woocommerce_after_main_content'); ?>

<?php get_footer('shop'); ?>
