<?php
/**
 * The Template for displaying product archives, including the main shop page
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/archive-product.php.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header('shop');

// Get current collection filter from URL
$current_collection = isset($_GET['collection']) ? sanitize_text_field($_GET['collection']) : '';

// Available collections
$collections = [
    'signature'  => skyyrose_get_collection('signature'),
    'black-rose' => skyyrose_get_collection('black-rose'),
    'love-hurts' => skyyrose_get_collection('love-hurts'),
];

// Get sorting
$orderby = isset($_GET['orderby']) ? sanitize_text_field($_GET['orderby']) : 'menu_order';

// Shop page hero styles
$hero_style = '';
if ($current_collection && isset($collections[$current_collection])) {
    $collection_data = $collections[$current_collection];
    $hero_style = sprintf(
        '--hero-primary: %s; --hero-secondary: %s; --hero-accent: %s;',
        esc_attr($collection_data['colors']['primary']),
        esc_attr($collection_data['colors']['secondary']),
        esc_attr($collection_data['colors']['accent'])
    );
}
?>

<?php do_action('woocommerce_before_main_content'); ?>

<main class="skyyrose-shop-archive" style="<?php echo esc_attr($hero_style); ?>">

    <!-- Shop Hero Section -->
    <section class="shop-hero glass-hero" data-gsap="fade-down">
        <div class="container">
            <header class="shop-header">
                <?php if (is_shop()) : ?>
                    <h1 class="shop-title"><?php woocommerce_page_title(); ?></h1>
                    <p class="shop-subtitle"><?php esc_html_e('Discover pieces that tell your story', 'skyyrose'); ?></p>
                <?php elseif (is_product_category()) : ?>
                    <h1 class="shop-title"><?php single_cat_title(); ?></h1>
                    <?php if (category_description()) : ?>
                        <div class="shop-description"><?php echo wp_kses_post(category_description()); ?></div>
                    <?php endif; ?>
                <?php elseif (is_product_tag()) : ?>
                    <h1 class="shop-title"><?php single_tag_title(); ?></h1>
                <?php endif; ?>
            </header>

            <!-- Breadcrumbs -->
            <nav class="shop-breadcrumb" aria-label="<?php esc_attr_e('Breadcrumb', 'skyyrose'); ?>">
                <ol class="breadcrumb-list" itemscope itemtype="https://schema.org/BreadcrumbList">
                    <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                        <a href="<?php echo esc_url(home_url('/')); ?>" itemprop="item">
                            <span itemprop="name"><?php esc_html_e('Home', 'skyyrose'); ?></span>
                        </a>
                        <meta itemprop="position" content="1">
                    </li>
                    <li class="breadcrumb-separator" aria-hidden="true">/</li>
                    <li class="breadcrumb-item <?php echo !is_product_category() && !is_product_tag() ? 'breadcrumb-current' : ''; ?>"
                        <?php echo !is_product_category() && !is_product_tag() ? 'aria-current="page"' : ''; ?>
                        itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                        <?php if (is_product_category() || is_product_tag()) : ?>
                            <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" itemprop="item">
                                <span itemprop="name"><?php esc_html_e('Shop', 'skyyrose'); ?></span>
                            </a>
                        <?php else : ?>
                            <span itemprop="name"><?php esc_html_e('Shop', 'skyyrose'); ?></span>
                        <?php endif; ?>
                        <meta itemprop="position" content="2">
                    </li>
                    <?php if (is_product_category()) : ?>
                        <li class="breadcrumb-separator" aria-hidden="true">/</li>
                        <li class="breadcrumb-item breadcrumb-current" aria-current="page" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                            <span itemprop="name"><?php single_cat_title(); ?></span>
                            <meta itemprop="position" content="3">
                        </li>
                    <?php elseif (is_product_tag()) : ?>
                        <li class="breadcrumb-separator" aria-hidden="true">/</li>
                        <li class="breadcrumb-item breadcrumb-current" aria-current="page" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                            <span itemprop="name"><?php single_tag_title(); ?></span>
                            <meta itemprop="position" content="3">
                        </li>
                    <?php endif; ?>
                </ol>
            </nav>
        </div>
    </section>

    <!-- Shop Controls Bar -->
    <section class="shop-controls" data-gsap="fade-up">
        <div class="container">
            <div class="controls-wrapper glass-card">

                <!-- Collection Filter Buttons -->
                <div class="collection-filters" role="group" aria-label="<?php esc_attr_e('Filter by collection', 'skyyrose'); ?>">
                    <a href="<?php echo esc_url(remove_query_arg('collection')); ?>"
                       class="collection-filter-btn magnetic-btn <?php echo empty($current_collection) ? 'active' : ''; ?>"
                       <?php echo empty($current_collection) ? 'aria-current="true"' : ''; ?>>
                        <span><?php esc_html_e('All', 'skyyrose'); ?></span>
                    </a>

                    <?php foreach ($collections as $slug => $data) : ?>
                    <a href="<?php echo esc_url(add_query_arg('collection', $slug)); ?>"
                       class="collection-filter-btn magnetic-btn <?php echo $current_collection === $slug ? 'active' : ''; ?>"
                       style="--filter-color: <?php echo esc_attr($data['colors']['primary']); ?>"
                       <?php echo $current_collection === $slug ? 'aria-current="true"' : ''; ?>>
                        <span><?php echo esc_html($data['name']); ?></span>
                    </a>
                    <?php endforeach; ?>
                </div>

                <div class="controls-right">
                    <!-- Results Count -->
                    <div class="results-count">
                        <?php
                        global $wp_query;
                        $total = $wp_query->found_posts;
                        printf(
                            esc_html(_n('%s Product', '%s Products', $total, 'skyyrose')),
                            '<strong>' . esc_html($total) . '</strong>'
                        );
                        ?>
                    </div>

                    <!-- Sort Dropdown -->
                    <div class="sort-dropdown glass-dropdown">
                        <label for="sort-select" class="sr-only"><?php esc_html_e('Sort by', 'skyyrose'); ?></label>
                        <select id="sort-select" class="sort-select glass-input" onchange="window.location.href=this.value;">
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'menu_order')); ?>" <?php selected($orderby, 'menu_order'); ?>>
                                <?php esc_html_e('Default Sorting', 'skyyrose'); ?>
                            </option>
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'popularity')); ?>" <?php selected($orderby, 'popularity'); ?>>
                                <?php esc_html_e('Popularity', 'skyyrose'); ?>
                            </option>
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'rating')); ?>" <?php selected($orderby, 'rating'); ?>>
                                <?php esc_html_e('Average Rating', 'skyyrose'); ?>
                            </option>
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'date')); ?>" <?php selected($orderby, 'date'); ?>>
                                <?php esc_html_e('Latest', 'skyyrose'); ?>
                            </option>
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'price')); ?>" <?php selected($orderby, 'price'); ?>>
                                <?php esc_html_e('Price: Low to High', 'skyyrose'); ?>
                            </option>
                            <option value="<?php echo esc_url(add_query_arg('orderby', 'price-desc')); ?>" <?php selected($orderby, 'price-desc'); ?>>
                                <?php esc_html_e('Price: High to Low', 'skyyrose'); ?>
                            </option>
                        </select>
                        <svg class="dropdown-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 9l6 6 6-6"/>
                        </svg>
                    </div>

                    <!-- View Toggle -->
                    <div class="view-toggle" role="group" aria-label="<?php esc_attr_e('View options', 'skyyrose'); ?>">
                        <button type="button" class="view-btn active" data-view="grid" aria-label="<?php esc_attr_e('Grid view', 'skyyrose'); ?>" aria-pressed="true">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <rect x="3" y="3" width="7" height="7"/>
                                <rect x="14" y="3" width="7" height="7"/>
                                <rect x="3" y="14" width="7" height="7"/>
                                <rect x="14" y="14" width="7" height="7"/>
                            </svg>
                        </button>
                        <button type="button" class="view-btn" data-view="list" aria-label="<?php esc_attr_e('List view', 'skyyrose'); ?>" aria-pressed="false">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Active Collection Banner -->
    <?php if ($current_collection && isset($collections[$current_collection])) :
        $active_collection = $collections[$current_collection];
    ?>
    <section class="collection-banner" style="--collection-primary: <?php echo esc_attr($active_collection['colors']['primary']); ?>; --collection-secondary: <?php echo esc_attr($active_collection['colors']['secondary']); ?>;" data-gsap="fade-in">
        <div class="container">
            <div class="banner-content glass-card">
                <div class="banner-text">
                    <h2 class="banner-title"><?php echo esc_html($active_collection['name']); ?></h2>
                    <p class="banner-tagline"><?php echo esc_html($active_collection['tagline']); ?></p>
                </div>
                <a href="<?php echo esc_url(home_url('/collections/' . $current_collection)); ?>" class="banner-cta magnetic-btn primary-btn">
                    <?php esc_html_e('Explore Collection', 'skyyrose'); ?>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                </a>
            </div>
        </div>
    </section>
    <?php endif; ?>

    <!-- Products Grid -->
    <section class="shop-products section">
        <div class="container">
            <?php
            if (woocommerce_product_loop()) {
                /**
                 * Hook: woocommerce_before_shop_loop.
                 *
                 * @hooked woocommerce_output_all_notices - 10
                 * @hooked woocommerce_result_count - 20
                 * @hooked woocommerce_catalog_ordering - 30
                 */
                do_action('woocommerce_before_shop_loop');

                // Apply collection filter if set
                if ($current_collection) {
                    add_action('pre_get_posts', function($query) use ($current_collection) {
                        if (!is_admin() && $query->is_main_query() && (is_shop() || is_product_category())) {
                            $meta_query = $query->get('meta_query') ?: [];
                            $meta_query[] = [
                                'key'   => '_skyyrose_collection',
                                'value' => $current_collection,
                            ];
                            $query->set('meta_query', $meta_query);
                        }
                    });
                }

                woocommerce_product_loop_start();

                if (wc_get_loop_prop('total')) {
                    $index = 0;
                    while (have_posts()) {
                        the_post();

                        /**
                         * Hook: woocommerce_shop_loop.
                         */
                        do_action('woocommerce_shop_loop');

                        // Add stagger animation delay
                        echo '<div class="product-card-wrapper" style="--animation-delay: ' . esc_attr($index * 0.1) . 's" data-gsap="fade-up-stagger">';
                        wc_get_template_part('content', 'product');
                        echo '</div>';

                        $index++;
                    }
                }

                woocommerce_product_loop_end();

                /**
                 * Hook: woocommerce_after_shop_loop.
                 *
                 * @hooked woocommerce_pagination - 10
                 */
                ?>

                <!-- Custom Pagination -->
                <nav class="shop-pagination" aria-label="<?php esc_attr_e('Products navigation', 'skyyrose'); ?>">
                    <?php
                    global $wp_query;
                    $total_pages = $wp_query->max_num_pages;
                    $current_page = max(1, get_query_var('paged'));

                    if ($total_pages > 1) :
                    ?>
                    <div class="pagination-wrapper glass-card">
                        <?php if ($current_page > 1) : ?>
                        <a href="<?php echo esc_url(get_pagenum_link($current_page - 1)); ?>" class="pagination-btn prev-btn magnetic-btn" aria-label="<?php esc_attr_e('Previous page', 'skyyrose'); ?>">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M15 18l-6-6 6-6"/>
                            </svg>
                            <span><?php esc_html_e('Previous', 'skyyrose'); ?></span>
                        </a>
                        <?php endif; ?>

                        <div class="pagination-numbers">
                            <?php
                            // Always show first page
                            if ($current_page > 3) {
                                echo '<a href="' . esc_url(get_pagenum_link(1)) . '" class="pagination-num magnetic-btn">1</a>';
                                if ($current_page > 4) {
                                    echo '<span class="pagination-ellipsis">...</span>';
                                }
                            }

                            // Show pages around current
                            for ($i = max(1, $current_page - 2); $i <= min($total_pages, $current_page + 2); $i++) {
                                if ($i === $current_page) {
                                    echo '<span class="pagination-num current" aria-current="page">' . $i . '</span>';
                                } else {
                                    echo '<a href="' . esc_url(get_pagenum_link($i)) . '" class="pagination-num magnetic-btn">' . $i . '</a>';
                                }
                            }

                            // Always show last page
                            if ($current_page < $total_pages - 2) {
                                if ($current_page < $total_pages - 3) {
                                    echo '<span class="pagination-ellipsis">...</span>';
                                }
                                echo '<a href="' . esc_url(get_pagenum_link($total_pages)) . '" class="pagination-num magnetic-btn">' . $total_pages . '</a>';
                            }
                            ?>
                        </div>

                        <?php if ($current_page < $total_pages) : ?>
                        <a href="<?php echo esc_url(get_pagenum_link($current_page + 1)); ?>" class="pagination-btn next-btn magnetic-btn" aria-label="<?php esc_attr_e('Next page', 'skyyrose'); ?>">
                            <span><?php esc_html_e('Next', 'skyyrose'); ?></span>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </a>
                        <?php endif; ?>
                    </div>
                    <?php endif; ?>
                </nav>
                <?php

            } else {
                /**
                 * Hook: woocommerce_no_products_found.
                 *
                 * @hooked wc_no_products_found - 10
                 */
                ?>
                <div class="no-products-found glass-card" data-gsap="fade-in">
                    <div class="no-products-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="M21 21l-4.35-4.35"/>
                        </svg>
                    </div>
                    <h2><?php esc_html_e('No products found', 'skyyrose'); ?></h2>
                    <p><?php esc_html_e('We couldn\'t find any products matching your criteria. Try adjusting your filters or browse our collections.', 'skyyrose'); ?></p>
                    <div class="no-products-actions">
                        <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="magnetic-btn primary-btn">
                            <?php esc_html_e('View All Products', 'skyyrose'); ?>
                        </a>
                    </div>
                </div>
                <?php
            }
            ?>
        </div>
    </section>

    <!-- Featured Collections CTA -->
    <section class="collections-cta section" data-gsap="fade-up">
        <div class="container">
            <header class="section-header">
                <h2 class="section-title"><?php esc_html_e('Explore Our Collections', 'skyyrose'); ?></h2>
                <p class="section-subtitle"><?php esc_html_e('Each collection tells a unique story of luxury and style', 'skyyrose'); ?></p>
            </header>

            <div class="collections-grid">
                <?php foreach ($collections as $slug => $data) : ?>
                <a href="<?php echo esc_url(add_query_arg('collection', $slug, wc_get_page_permalink('shop'))); ?>"
                   class="collection-card glass-card magnetic-hover"
                   style="--card-primary: <?php echo esc_attr($data['colors']['primary']); ?>; --card-secondary: <?php echo esc_attr($data['colors']['secondary']); ?>;"
                   data-gsap="fade-up-stagger">
                    <div class="collection-card-bg"></div>
                    <div class="collection-card-content">
                        <h3 class="collection-card-title"><?php echo esc_html($data['name']); ?></h3>
                        <p class="collection-card-tagline"><?php echo esc_html($data['tagline']); ?></p>
                        <span class="collection-card-link">
                            <?php esc_html_e('Shop Now', 'skyyrose'); ?>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M5 12h14M12 5l7 7-7 7"/>
                            </svg>
                        </span>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

</main>

<?php
/**
 * Hook: woocommerce_after_main_content.
 *
 * @hooked woocommerce_output_content_wrapper_end - 10 (outputs closing divs for the content)
 */
do_action('woocommerce_after_main_content');

get_footer('shop');
?>
