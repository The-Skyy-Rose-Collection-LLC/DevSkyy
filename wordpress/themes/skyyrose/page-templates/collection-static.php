<?php
/**
 * Template Name: Collection Shop
 * Template Post Type: page
 *
 * Static collection shop template with product grid, filters, and pagination.
 * Integrates with WooCommerce for product display and filtering.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

// Get collection slug from custom field or URL
$collection_slug = get_post_meta(get_the_ID(), '_skyyrose_collection_slug', true);
if (empty($collection_slug) && isset($_GET['collection'])) {
    $collection_slug = sanitize_text_field($_GET['collection']);
}
$collection_slug = $collection_slug ?: 'signature';

// Get collection data
$collection = skyyrose_get_collection($collection_slug);

// Get filter parameters from URL
$current_page = max(1, get_query_var('paged') ?: 1);
$products_per_page = 12;

$price_min = isset($_GET['min_price']) ? floatval($_GET['min_price']) : 0;
$price_max = isset($_GET['max_price']) ? floatval($_GET['max_price']) : 0;
$selected_sizes = isset($_GET['sizes']) ? array_map('sanitize_text_field', (array) $_GET['sizes']) : [];
$selected_colors = isset($_GET['colors']) ? array_map('sanitize_text_field', (array) $_GET['colors']) : [];
$orderby = isset($_GET['orderby']) ? sanitize_text_field($_GET['orderby']) : 'menu_order';

// Build WP_Query args
$query_args = [
    'post_type'      => 'product',
    'posts_per_page' => $products_per_page,
    'paged'          => $current_page,
    'post_status'    => 'publish',
    'meta_query'     => [
        'relation' => 'AND',
        [
            'key'     => '_skyyrose_collection',
            'value'   => $collection_slug,
            'compare' => '=',
        ],
    ],
    'tax_query' => [
        [
            'taxonomy' => 'product_visibility',
            'field'    => 'name',
            'terms'    => 'exclude-from-catalog',
            'operator' => 'NOT IN',
        ],
    ],
];

// Add price filter
if ($price_min > 0 || $price_max > 0) {
    if ($price_min > 0) {
        $query_args['meta_query'][] = [
            'key'     => '_price',
            'value'   => $price_min,
            'compare' => '>=',
            'type'    => 'NUMERIC',
        ];
    }
    if ($price_max > 0) {
        $query_args['meta_query'][] = [
            'key'     => '_price',
            'value'   => $price_max,
            'compare' => '<=',
            'type'    => 'NUMERIC',
        ];
    }
}

// Add size filter (product attribute)
if (!empty($selected_sizes)) {
    $query_args['tax_query'][] = [
        'taxonomy' => 'pa_size',
        'field'    => 'slug',
        'terms'    => $selected_sizes,
        'operator' => 'IN',
    ];
}

// Add color filter (product attribute)
if (!empty($selected_colors)) {
    $query_args['tax_query'][] = [
        'taxonomy' => 'pa_color',
        'field'    => 'slug',
        'terms'    => $selected_colors,
        'operator' => 'IN',
    ];
}

// Handle sorting
switch ($orderby) {
    case 'price':
        $query_args['orderby'] = 'meta_value_num';
        $query_args['meta_key'] = '_price';
        $query_args['order'] = 'ASC';
        break;
    case 'price-desc':
        $query_args['orderby'] = 'meta_value_num';
        $query_args['meta_key'] = '_price';
        $query_args['order'] = 'DESC';
        break;
    case 'date':
        $query_args['orderby'] = 'date';
        $query_args['order'] = 'DESC';
        break;
    case 'popularity':
        $query_args['orderby'] = 'meta_value_num';
        $query_args['meta_key'] = 'total_sales';
        $query_args['order'] = 'DESC';
        break;
    case 'rating':
        $query_args['orderby'] = 'meta_value_num';
        $query_args['meta_key'] = '_wc_average_rating';
        $query_args['order'] = 'DESC';
        break;
    default:
        $query_args['orderby'] = 'menu_order date';
        $query_args['order'] = 'ASC';
        break;
}

// Execute query
$products_query = new WP_Query($query_args);

// Get available filter options
$available_sizes = get_terms([
    'taxonomy'   => 'pa_size',
    'hide_empty' => true,
]);

$available_colors = get_terms([
    'taxonomy'   => 'pa_color',
    'hide_empty' => true,
]);

// Get price range for this collection
$price_range_query = new WP_Query([
    'post_type'      => 'product',
    'posts_per_page' => -1,
    'post_status'    => 'publish',
    'fields'         => 'ids',
    'meta_query'     => [
        [
            'key'     => '_skyyrose_collection',
            'value'   => $collection_slug,
            'compare' => '=',
        ],
    ],
]);

$collection_min_price = PHP_FLOAT_MAX;
$collection_max_price = 0;

if ($price_range_query->have_posts()) {
    foreach ($price_range_query->posts as $product_id) {
        $product = wc_get_product($product_id);
        if ($product) {
            $price = (float) $product->get_price();
            $collection_min_price = min($collection_min_price, $price);
            $collection_max_price = max($collection_max_price, $price);
        }
    }
}

if ($collection_min_price === PHP_FLOAT_MAX) {
    $collection_min_price = 0;
}

// Build current URL for filter form
$current_url = get_permalink();

// Generate CSS custom properties for collection theming
$collection_styles = sprintf(
    '--collection-primary: %s; --collection-secondary: %s; --collection-accent: %s;',
    esc_attr($collection['colors']['primary']),
    esc_attr($collection['colors']['secondary']),
    esc_attr($collection['colors']['accent'])
);

get_header();
?>

<style>
    .collection-shop-page {
        <?php echo $collection_styles; ?>
    }
</style>

<main id="main-content" class="collection-shop-page" role="main" data-collection="<?php echo esc_attr($collection_slug); ?>">

    <!-- Collection Header -->
    <header class="collection-header">
        <div class="header-background">
            <?php if (has_post_thumbnail()) : ?>
                <div class="header-image">
                    <?php the_post_thumbnail('skyyrose-hero', [
                        'class' => 'header-bg-image',
                        'loading' => 'eager',
                    ]); ?>
                </div>
            <?php endif; ?>
            <div class="header-gradient"></div>
        </div>

        <div class="container">
            <div class="header-content" data-gsap="fade-up">
                <nav class="breadcrumb" aria-label="<?php esc_attr_e('Breadcrumb', 'skyyrose'); ?>">
                    <a href="<?php echo esc_url(home_url('/')); ?>"><?php esc_html_e('Home', 'skyyrose'); ?></a>
                    <span class="separator" aria-hidden="true">/</span>
                    <a href="<?php echo esc_url(get_permalink(wc_get_page_id('shop'))); ?>"><?php esc_html_e('Shop', 'skyyrose'); ?></a>
                    <span class="separator" aria-hidden="true">/</span>
                    <span class="current" aria-current="page"><?php echo esc_html($collection['name']); ?></span>
                </nav>

                <h1 class="collection-title"><?php echo esc_html($collection['name']); ?></h1>
                <p class="collection-tagline"><?php echo esc_html($collection['tagline']); ?></p>
                <p class="collection-description"><?php echo esc_html($collection['description']); ?></p>

                <div class="collection-meta">
                    <span class="product-count">
                        <?php
                        printf(
                            esc_html(_n('%s Product', '%s Products', $products_query->found_posts, 'skyyrose')),
                            number_format_i18n($products_query->found_posts)
                        );
                        ?>
                    </span>
                </div>
            </div>
        </div>
    </header>

    <!-- Shop Content -->
    <div class="shop-content">
        <div class="container">
            <div class="shop-layout">

                <!-- Filters Sidebar -->
                <aside class="shop-sidebar" id="shop-filters" role="complementary" aria-label="<?php esc_attr_e('Product Filters', 'skyyrose'); ?>">
                    <div class="sidebar-inner glass-panel">
                        <div class="sidebar-header">
                            <h2 class="sidebar-title"><?php esc_html_e('Filters', 'skyyrose'); ?></h2>
                            <?php if ($price_min > 0 || $price_max > 0 || !empty($selected_sizes) || !empty($selected_colors)) : ?>
                                <a href="<?php echo esc_url($current_url . '?collection=' . $collection_slug); ?>" class="clear-filters">
                                    <?php esc_html_e('Clear All', 'skyyrose'); ?>
                                </a>
                            <?php endif; ?>
                        </div>

                        <form method="get" action="<?php echo esc_url($current_url); ?>" class="filters-form" id="product-filters-form">
                            <input type="hidden" name="collection" value="<?php echo esc_attr($collection_slug); ?>">

                            <!-- Price Filter -->
                            <div class="filter-group">
                                <button type="button" class="filter-toggle" aria-expanded="true" aria-controls="filter-price">
                                    <span><?php esc_html_e('Price', 'skyyrose'); ?></span>
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                    </svg>
                                </button>
                                <div class="filter-content" id="filter-price">
                                    <div class="price-range">
                                        <div class="price-inputs">
                                            <label class="price-input">
                                                <span class="sr-only"><?php esc_html_e('Minimum Price', 'skyyrose'); ?></span>
                                                <span class="currency"><?php echo get_woocommerce_currency_symbol(); ?></span>
                                                <input
                                                    type="number"
                                                    name="min_price"
                                                    value="<?php echo esc_attr($price_min ?: ''); ?>"
                                                    placeholder="<?php echo esc_attr(floor($collection_min_price)); ?>"
                                                    min="0"
                                                    step="1"
                                                    class="glass-input"
                                                >
                                            </label>
                                            <span class="price-separator" aria-hidden="true">-</span>
                                            <label class="price-input">
                                                <span class="sr-only"><?php esc_html_e('Maximum Price', 'skyyrose'); ?></span>
                                                <span class="currency"><?php echo get_woocommerce_currency_symbol(); ?></span>
                                                <input
                                                    type="number"
                                                    name="max_price"
                                                    value="<?php echo esc_attr($price_max ?: ''); ?>"
                                                    placeholder="<?php echo esc_attr(ceil($collection_max_price)); ?>"
                                                    min="0"
                                                    step="1"
                                                    class="glass-input"
                                                >
                                            </label>
                                        </div>
                                        <div class="price-range-slider" data-min="<?php echo esc_attr(floor($collection_min_price)); ?>" data-max="<?php echo esc_attr(ceil($collection_max_price)); ?>">
                                            <div class="slider-track"></div>
                                            <div class="slider-range"></div>
                                            <input type="range" class="slider-min" min="<?php echo esc_attr(floor($collection_min_price)); ?>" max="<?php echo esc_attr(ceil($collection_max_price)); ?>" value="<?php echo esc_attr($price_min ?: floor($collection_min_price)); ?>">
                                            <input type="range" class="slider-max" min="<?php echo esc_attr(floor($collection_min_price)); ?>" max="<?php echo esc_attr(ceil($collection_max_price)); ?>" value="<?php echo esc_attr($price_max ?: ceil($collection_max_price)); ?>">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Size Filter -->
                            <?php if (!empty($available_sizes) && !is_wp_error($available_sizes)) : ?>
                                <div class="filter-group">
                                    <button type="button" class="filter-toggle" aria-expanded="true" aria-controls="filter-size">
                                        <span><?php esc_html_e('Size', 'skyyrose'); ?></span>
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                            <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                        </svg>
                                    </button>
                                    <div class="filter-content" id="filter-size">
                                        <div class="filter-options size-options">
                                            <?php foreach ($available_sizes as $size) : ?>
                                                <label class="filter-option size-option">
                                                    <input
                                                        type="checkbox"
                                                        name="sizes[]"
                                                        value="<?php echo esc_attr($size->slug); ?>"
                                                        <?php checked(in_array($size->slug, $selected_sizes, true)); ?>
                                                    >
                                                    <span class="option-label"><?php echo esc_html($size->name); ?></span>
                                                </label>
                                            <?php endforeach; ?>
                                        </div>
                                    </div>
                                </div>
                            <?php endif; ?>

                            <!-- Color Filter -->
                            <?php if (!empty($available_colors) && !is_wp_error($available_colors)) : ?>
                                <div class="filter-group">
                                    <button type="button" class="filter-toggle" aria-expanded="true" aria-controls="filter-color">
                                        <span><?php esc_html_e('Color', 'skyyrose'); ?></span>
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                            <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                        </svg>
                                    </button>
                                    <div class="filter-content" id="filter-color">
                                        <div class="filter-options color-options">
                                            <?php foreach ($available_colors as $color) :
                                                // Get color hex from term meta if available
                                                $color_hex = get_term_meta($color->term_id, 'color_hex', true);
                                                $style = $color_hex ? 'background-color: ' . esc_attr($color_hex) . ';' : '';
                                                ?>
                                                <label class="filter-option color-option">
                                                    <input
                                                        type="checkbox"
                                                        name="colors[]"
                                                        value="<?php echo esc_attr($color->slug); ?>"
                                                        <?php checked(in_array($color->slug, $selected_colors, true)); ?>
                                                    >
                                                    <span class="color-swatch" style="<?php echo $style; ?>" title="<?php echo esc_attr($color->name); ?>"></span>
                                                    <span class="option-label"><?php echo esc_html($color->name); ?></span>
                                                </label>
                                            <?php endforeach; ?>
                                        </div>
                                    </div>
                                </div>
                            <?php endif; ?>

                            <!-- Apply Filters Button -->
                            <button type="submit" class="btn btn-primary apply-filters magnetic-btn">
                                <?php esc_html_e('Apply Filters', 'skyyrose'); ?>
                            </button>
                        </form>
                    </div>

                    <!-- Mobile Filter Toggle -->
                    <button class="mobile-filter-toggle glass-button" aria-controls="shop-filters" aria-expanded="false">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                            <path d="M3 5H17M6 10H14M8 15H12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        <span><?php esc_html_e('Filters', 'skyyrose'); ?></span>
                    </button>
                </aside>

                <!-- Products Grid -->
                <div class="shop-main">
                    <!-- Toolbar -->
                    <div class="shop-toolbar glass-panel">
                        <div class="toolbar-left">
                            <p class="results-count">
                                <?php
                                $first = (($current_page - 1) * $products_per_page) + 1;
                                $last = min($current_page * $products_per_page, $products_query->found_posts);
                                printf(
                                    esc_html__('Showing %1$d-%2$d of %3$d results', 'skyyrose'),
                                    $first,
                                    $last,
                                    $products_query->found_posts
                                );
                                ?>
                            </p>
                        </div>

                        <div class="toolbar-right">
                            <!-- Sort Dropdown -->
                            <div class="sort-dropdown">
                                <label for="orderby" class="sr-only"><?php esc_html_e('Sort by', 'skyyrose'); ?></label>
                                <select name="orderby" id="orderby" class="glass-select" onchange="this.form.submit();">
                                    <option value="menu_order" <?php selected($orderby, 'menu_order'); ?>><?php esc_html_e('Default sorting', 'skyyrose'); ?></option>
                                    <option value="popularity" <?php selected($orderby, 'popularity'); ?>><?php esc_html_e('Sort by popularity', 'skyyrose'); ?></option>
                                    <option value="rating" <?php selected($orderby, 'rating'); ?>><?php esc_html_e('Sort by rating', 'skyyrose'); ?></option>
                                    <option value="date" <?php selected($orderby, 'date'); ?>><?php esc_html_e('Sort by latest', 'skyyrose'); ?></option>
                                    <option value="price" <?php selected($orderby, 'price'); ?>><?php esc_html_e('Sort by price: low to high', 'skyyrose'); ?></option>
                                    <option value="price-desc" <?php selected($orderby, 'price-desc'); ?>><?php esc_html_e('Sort by price: high to low', 'skyyrose'); ?></option>
                                </select>
                            </div>

                            <!-- View Toggle -->
                            <div class="view-toggle" role="group" aria-label="<?php esc_attr_e('View options', 'skyyrose'); ?>">
                                <button type="button" class="view-btn active" data-view="grid" aria-pressed="true" aria-label="<?php esc_attr_e('Grid view', 'skyyrose'); ?>">
                                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                                        <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                                        <rect x="11" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                                        <rect x="1" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                                        <rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                                    </svg>
                                </button>
                                <button type="button" class="view-btn" data-view="list" aria-pressed="false" aria-label="<?php esc_attr_e('List view', 'skyyrose'); ?>">
                                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                                        <path d="M1 4H17M1 9H17M1 14H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Active Filters -->
                    <?php if ($price_min > 0 || $price_max > 0 || !empty($selected_sizes) || !empty($selected_colors)) : ?>
                        <div class="active-filters">
                            <?php if ($price_min > 0 || $price_max > 0) : ?>
                                <span class="active-filter">
                                    <?php
                                    if ($price_min > 0 && $price_max > 0) {
                                        printf(
                                            esc_html__('Price: %1$s - %2$s', 'skyyrose'),
                                            wc_price($price_min),
                                            wc_price($price_max)
                                        );
                                    } elseif ($price_min > 0) {
                                        printf(esc_html__('Price: %s+', 'skyyrose'), wc_price($price_min));
                                    } else {
                                        printf(esc_html__('Price: up to %s', 'skyyrose'), wc_price($price_max));
                                    }
                                    ?>
                                    <button type="button" class="remove-filter" data-filter="price" aria-label="<?php esc_attr_e('Remove price filter', 'skyyrose'); ?>">
                                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                                            <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                        </svg>
                                    </button>
                                </span>
                            <?php endif; ?>

                            <?php foreach ($selected_sizes as $size_slug) :
                                $size_term = get_term_by('slug', $size_slug, 'pa_size');
                                if ($size_term) :
                                    ?>
                                    <span class="active-filter">
                                        <?php printf(esc_html__('Size: %s', 'skyyrose'), esc_html($size_term->name)); ?>
                                        <button type="button" class="remove-filter" data-filter="size" data-value="<?php echo esc_attr($size_slug); ?>" aria-label="<?php printf(esc_attr__('Remove size %s filter', 'skyyrose'), esc_attr($size_term->name)); ?>">
                                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                                                <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                    </span>
                                <?php endif;
                            endforeach; ?>

                            <?php foreach ($selected_colors as $color_slug) :
                                $color_term = get_term_by('slug', $color_slug, 'pa_color');
                                if ($color_term) :
                                    ?>
                                    <span class="active-filter">
                                        <?php printf(esc_html__('Color: %s', 'skyyrose'), esc_html($color_term->name)); ?>
                                        <button type="button" class="remove-filter" data-filter="color" data-value="<?php echo esc_attr($color_slug); ?>" aria-label="<?php printf(esc_attr__('Remove color %s filter', 'skyyrose'), esc_attr($color_term->name)); ?>">
                                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                                                <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                            </svg>
                                        </button>
                                    </span>
                                <?php endif;
                            endforeach; ?>
                        </div>
                    <?php endif; ?>

                    <!-- Products Grid -->
                    <?php if ($products_query->have_posts()) : ?>
                        <div class="products-grid" data-gsap="stagger-fade" id="products-grid">
                            <?php while ($products_query->have_posts()) : $products_query->the_post();
                                global $product;
                                if (!$product) continue;
                                ?>
                                <article class="product-card glass-card" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                                    <div class="product-card-image">
                                        <a href="<?php the_permalink(); ?>" aria-label="<?php echo esc_attr($product->get_name()); ?>">
                                            <?php echo $product->get_image('skyyrose-product'); ?>

                                            <?php
                                            // Show second image on hover if available
                                            $gallery_ids = $product->get_gallery_image_ids();
                                            if (!empty($gallery_ids)) :
                                                ?>
                                                <span class="product-image-hover">
                                                    <?php echo wp_get_attachment_image($gallery_ids[0], 'skyyrose-product'); ?>
                                                </span>
                                            <?php endif; ?>
                                        </a>

                                        <!-- Badges -->
                                        <div class="product-badges">
                                            <?php if ($product->is_on_sale()) : ?>
                                                <span class="badge sale-badge">
                                                    <?php
                                                    $regular = (float) $product->get_regular_price();
                                                    $sale = (float) $product->get_sale_price();
                                                    $percent = $regular > 0 ? round((($regular - $sale) / $regular) * 100) : 0;
                                                    printf(esc_html__('-%d%%', 'skyyrose'), $percent);
                                                    ?>
                                                </span>
                                            <?php endif; ?>

                                            <?php if (!$product->is_in_stock()) : ?>
                                                <span class="badge stock-badge out-of-stock"><?php esc_html_e('Sold Out', 'skyyrose'); ?></span>
                                            <?php endif; ?>

                                            <?php
                                            $has_3d = get_post_meta($product->get_id(), '_skyyrose_3d_model', true);
                                            if ($has_3d) :
                                                ?>
                                                <span class="badge badge-3d" title="<?php esc_attr_e('3D View Available', 'skyyrose'); ?>">
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5"/>
                                                        <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5"/>
                                                        <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5"/>
                                                    </svg>
                                                </span>
                                            <?php endif; ?>
                                        </div>

                                        <!-- Quick Actions -->
                                        <div class="product-quick-actions">
                                            <button class="quick-action wishlist-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>" aria-label="<?php esc_attr_e('Add to wishlist', 'skyyrose'); ?>">
                                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                                    <path d="M10 17.5L2.5 10C1.11929 8.61929 1.11929 6.38071 2.5 5C3.88071 3.61929 6.11929 3.61929 7.5 5L10 7.5L12.5 5C13.8807 3.61929 16.1193 3.61929 17.5 5C18.8807 6.38071 18.8807 8.61929 17.5 10L10 17.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                                </svg>
                                            </button>
                                            <button class="quick-action quick-view-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>" aria-label="<?php esc_attr_e('Quick view', 'skyyrose'); ?>">
                                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                                    <path d="M10 4C4 4 1 10 1 10C1 10 4 16 10 16C16 16 19 10 19 10C19 10 16 4 10 4Z" stroke="currentColor" stroke-width="1.5"/>
                                                    <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="1.5"/>
                                                </svg>
                                            </button>
                                        </div>
                                    </div>

                                    <div class="product-card-content">
                                        <h3 class="product-card-title">
                                            <a href="<?php the_permalink(); ?>"><?php echo esc_html($product->get_name()); ?></a>
                                        </h3>

                                        <?php
                                        // Show product rating
                                        $rating = $product->get_average_rating();
                                        if ($rating > 0) :
                                            ?>
                                            <div class="product-rating" aria-label="<?php printf(esc_attr__('Rated %s out of 5', 'skyyrose'), $rating); ?>">
                                                <?php echo wc_get_star_rating_html($rating, $product->get_review_count()); ?>
                                            </div>
                                        <?php endif; ?>

                                        <p class="product-card-price"><?php echo $product->get_price_html(); ?></p>

                                        <?php
                                        // Show color swatches if available
                                        $colors = $product->get_attribute('pa_color');
                                        if ($colors) :
                                            $color_terms = wc_get_product_terms($product->get_id(), 'pa_color');
                                            if (!empty($color_terms)) :
                                                ?>
                                                <div class="product-swatches">
                                                    <?php foreach (array_slice($color_terms, 0, 4) as $color_term) :
                                                        $color_hex = get_term_meta($color_term->term_id, 'color_hex', true);
                                                        ?>
                                                        <span class="color-swatch-mini" style="<?php echo $color_hex ? 'background-color: ' . esc_attr($color_hex) . ';' : ''; ?>" title="<?php echo esc_attr($color_term->name); ?>"></span>
                                                    <?php endforeach; ?>
                                                    <?php if (count($color_terms) > 4) : ?>
                                                        <span class="more-colors">+<?php echo count($color_terms) - 4; ?></span>
                                                    <?php endif; ?>
                                                </div>
                                            <?php endif;
                                        endif;
                                        ?>
                                    </div>

                                    <div class="product-card-actions">
                                        <?php if ($product->is_in_stock()) : ?>
                                            <?php woocommerce_template_loop_add_to_cart(); ?>
                                        <?php else : ?>
                                            <a href="<?php the_permalink(); ?>" class="btn btn-secondary">
                                                <?php esc_html_e('View Details', 'skyyrose'); ?>
                                            </a>
                                        <?php endif; ?>
                                    </div>
                                </article>
                            <?php endwhile; ?>
                        </div>
                        <?php wp_reset_postdata(); ?>

                        <!-- Pagination -->
                        <?php if ($products_query->max_num_pages > 1) : ?>
                            <nav class="pagination" aria-label="<?php esc_attr_e('Product navigation', 'skyyrose'); ?>">
                                <?php
                                // Build pagination base URL with filters
                                $pagination_base = add_query_arg([
                                    'collection' => $collection_slug,
                                    'min_price'  => $price_min ?: null,
                                    'max_price'  => $price_max ?: null,
                                    'sizes'      => !empty($selected_sizes) ? $selected_sizes : null,
                                    'colors'     => !empty($selected_colors) ? $selected_colors : null,
                                    'orderby'    => $orderby !== 'menu_order' ? $orderby : null,
                                ], $current_url);

                                echo paginate_links([
                                    'base'      => $pagination_base . '%_%',
                                    'format'    => '&paged=%#%',
                                    'current'   => $current_page,
                                    'total'     => $products_query->max_num_pages,
                                    'prev_text' => '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> <span>' . esc_html__('Previous', 'skyyrose') . '</span>',
                                    'next_text' => '<span>' . esc_html__('Next', 'skyyrose') . '</span> <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                                    'mid_size'  => 2,
                                    'type'      => 'list',
                                ]);
                                ?>
                            </nav>
                        <?php endif; ?>

                    <?php else : ?>
                        <!-- No Products Found -->
                        <div class="no-products glass-card">
                            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
                                <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2"/>
                                <path d="M20 44L44 20M20 20L44 44" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                            <h3><?php esc_html_e('No products found', 'skyyrose'); ?></h3>
                            <p><?php esc_html_e('Try adjusting your filters or browse our other collections.', 'skyyrose'); ?></p>
                            <a href="<?php echo esc_url($current_url . '?collection=' . $collection_slug); ?>" class="btn btn-primary">
                                <?php esc_html_e('Clear Filters', 'skyyrose'); ?>
                            </a>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>

</main>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Filter toggle functionality
    const filterToggles = document.querySelectorAll('.filter-toggle');
    filterToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', !expanded);
            const content = document.getElementById(toggle.getAttribute('aria-controls'));
            if (content) {
                content.classList.toggle('collapsed', expanded);
            }
        });
    });

    // Price range slider sync
    const priceSliderMin = document.querySelector('.slider-min');
    const priceSliderMax = document.querySelector('.slider-max');
    const priceInputMin = document.querySelector('input[name="min_price"]');
    const priceInputMax = document.querySelector('input[name="max_price"]');
    const sliderRange = document.querySelector('.slider-range');

    if (priceSliderMin && priceSliderMax) {
        const updateSliderRange = () => {
            const min = parseInt(priceSliderMin.value);
            const max = parseInt(priceSliderMax.value);
            const totalRange = parseInt(priceSliderMax.max) - parseInt(priceSliderMin.min);
            const leftPercent = ((min - parseInt(priceSliderMin.min)) / totalRange) * 100;
            const rightPercent = ((max - parseInt(priceSliderMin.min)) / totalRange) * 100;
            sliderRange.style.left = leftPercent + '%';
            sliderRange.style.right = (100 - rightPercent) + '%';
        };

        priceSliderMin.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            if (value <= parseInt(priceSliderMax.value)) {
                priceInputMin.value = value;
                updateSliderRange();
            }
        });

        priceSliderMax.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            if (value >= parseInt(priceSliderMin.value)) {
                priceInputMax.value = value;
                updateSliderRange();
            }
        });

        updateSliderRange();
    }

    // Mobile filter toggle
    const mobileFilterToggle = document.querySelector('.mobile-filter-toggle');
    const sidebar = document.getElementById('shop-filters');

    if (mobileFilterToggle && sidebar) {
        mobileFilterToggle.addEventListener('click', () => {
            const expanded = mobileFilterToggle.getAttribute('aria-expanded') === 'true';
            mobileFilterToggle.setAttribute('aria-expanded', !expanded);
            sidebar.classList.toggle('is-open', !expanded);
            document.body.classList.toggle('filters-open', !expanded);
        });
    }

    // View toggle
    const viewButtons = document.querySelectorAll('.view-btn');
    const productsGrid = document.getElementById('products-grid');

    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            viewButtons.forEach(b => b.setAttribute('aria-pressed', 'false'));
            btn.setAttribute('aria-pressed', 'true');
            viewButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (productsGrid) {
                productsGrid.classList.remove('grid-view', 'list-view');
                productsGrid.classList.add(view + '-view');
            }
        });
    });

    // Sort dropdown
    const sortSelect = document.getElementById('orderby');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            const url = new URL(window.location.href);
            url.searchParams.set('orderby', sortSelect.value);
            window.location.href = url.toString();
        });
    }

    // Remove filter buttons
    const removeFilterBtns = document.querySelectorAll('.remove-filter');
    removeFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filterType = btn.dataset.filter;
            const filterValue = btn.dataset.value;
            const url = new URL(window.location.href);

            switch (filterType) {
                case 'price':
                    url.searchParams.delete('min_price');
                    url.searchParams.delete('max_price');
                    break;
                case 'size':
                    const sizes = url.searchParams.getAll('sizes[]').filter(s => s !== filterValue);
                    url.searchParams.delete('sizes[]');
                    sizes.forEach(s => url.searchParams.append('sizes[]', s));
                    break;
                case 'color':
                    const colors = url.searchParams.getAll('colors[]').filter(c => c !== filterValue);
                    url.searchParams.delete('colors[]');
                    colors.forEach(c => url.searchParams.append('colors[]', c));
                    break;
            }

            window.location.href = url.toString();
        });
    });
});
</script>

<?php
get_footer();
