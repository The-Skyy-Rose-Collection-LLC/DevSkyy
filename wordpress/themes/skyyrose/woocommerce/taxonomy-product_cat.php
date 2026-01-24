<?php
/**
 * The Template for displaying product category archives
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/taxonomy-product_cat.php.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header('shop');

// Get current category
$category = get_queried_object();
$category_id = $category->term_id;
$category_slug = $category->slug;

// Try to match category with a collection
$collection_mapping = [
    'signature'    => 'signature',
    'black-rose'   => 'black-rose',
    'love-hurts'   => 'love-hurts',
    // Add more mappings as needed
];

// Check if this category maps to a collection
$matched_collection = null;
foreach ($collection_mapping as $cat_pattern => $collection_slug) {
    if (stripos($category_slug, $cat_pattern) !== false || stripos($category->name, str_replace('-', ' ', $cat_pattern)) !== false) {
        $matched_collection = skyyrose_get_collection($collection_slug);
        break;
    }
}

// Default collection styling if no match
if (!$matched_collection) {
    $matched_collection = [
        'name'        => $category->name,
        'tagline'     => '',
        'description' => $category->description,
        'colors'      => [
            'primary'   => '#B76E79',
            'secondary' => '#1A1A1A',
            'accent'    => '#D4AF37',
        ],
    ];
}

// Category image
$category_image_id = get_term_meta($category_id, 'thumbnail_id', true);
$category_image_url = $category_image_id ? wp_get_attachment_image_url($category_image_id, 'skyyrose-hero') : '';

// Dynamic CSS variables for collection theming
$hero_style = sprintf(
    '--collection-primary: %s; --collection-secondary: %s; --collection-accent: %s;',
    esc_attr($matched_collection['colors']['primary']),
    esc_attr($matched_collection['colors']['secondary']),
    esc_attr($matched_collection['colors']['accent'])
);

// Get sorting
$orderby = isset($_GET['orderby']) ? sanitize_text_field($_GET['orderby']) : 'menu_order';
?>

<?php do_action('woocommerce_before_main_content'); ?>

<main class="skyyrose-category-archive" style="<?php echo esc_attr($hero_style); ?>">

    <!-- Category Hero Section -->
    <section class="category-hero glass-hero" data-gsap="parallax-hero">
        <?php if ($category_image_url) : ?>
        <div class="hero-background">
            <img src="<?php echo esc_url($category_image_url); ?>"
                 alt="<?php echo esc_attr($category->name); ?>"
                 class="hero-bg-image"
                 loading="eager">
            <div class="hero-overlay"></div>
        </div>
        <?php else : ?>
        <div class="hero-background hero-gradient"></div>
        <?php endif; ?>

        <div class="container">
            <div class="hero-content" data-gsap="fade-up">
                <!-- Breadcrumbs -->
                <nav class="category-breadcrumb" aria-label="<?php esc_attr_e('Breadcrumb', 'skyyrose'); ?>">
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
                        <?php
                        // Show parent categories
                        $parent_ids = get_ancestors($category_id, 'product_cat', 'taxonomy');
                        $parent_ids = array_reverse($parent_ids);
                        $position = 3;

                        foreach ($parent_ids as $parent_id) :
                            $parent = get_term($parent_id, 'product_cat');
                            if ($parent && !is_wp_error($parent)) :
                        ?>
                        <li class="breadcrumb-separator" aria-hidden="true">/</li>
                        <li class="breadcrumb-item" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                            <a href="<?php echo esc_url(get_term_link($parent)); ?>" itemprop="item">
                                <span itemprop="name"><?php echo esc_html($parent->name); ?></span>
                            </a>
                            <meta itemprop="position" content="<?php echo esc_attr($position); ?>">
                        </li>
                        <?php
                            $position++;
                            endif;
                        endforeach;
                        ?>
                        <li class="breadcrumb-separator" aria-hidden="true">/</li>
                        <li class="breadcrumb-item breadcrumb-current" aria-current="page" itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                            <span itemprop="name"><?php echo esc_html($category->name); ?></span>
                            <meta itemprop="position" content="<?php echo esc_attr($position); ?>">
                        </li>
                    </ol>
                </nav>

                <!-- Category Title & Description -->
                <header class="category-header">
                    <h1 class="category-title"><?php echo esc_html($matched_collection['name']); ?></h1>
                    <?php if (!empty($matched_collection['tagline'])) : ?>
                    <p class="category-tagline"><?php echo esc_html($matched_collection['tagline']); ?></p>
                    <?php endif; ?>
                </header>

                <?php if ($category->description || !empty($matched_collection['description'])) : ?>
                <div class="category-description glass-card">
                    <?php echo wp_kses_post($category->description ?: $matched_collection['description']); ?>
                </div>
                <?php endif; ?>

                <!-- Category Stats -->
                <div class="category-stats">
                    <div class="stat-item">
                        <span class="stat-value"><?php echo esc_html($category->count); ?></span>
                        <span class="stat-label"><?php echo esc_html(_n('Product', 'Products', $category->count, 'skyyrose')); ?></span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Sub-categories (if any) -->
    <?php
    $subcategories = get_terms([
        'taxonomy'   => 'product_cat',
        'parent'     => $category_id,
        'hide_empty' => true,
    ]);

    if (!empty($subcategories) && !is_wp_error($subcategories)) :
    ?>
    <section class="subcategories-section" data-gsap="fade-up">
        <div class="container">
            <h2 class="section-title sr-only"><?php esc_html_e('Browse Subcategories', 'skyyrose'); ?></h2>

            <div class="subcategories-grid">
                <?php foreach ($subcategories as $index => $subcat) :
                    $subcat_image_id = get_term_meta($subcat->term_id, 'thumbnail_id', true);
                    $subcat_image_url = $subcat_image_id ? wp_get_attachment_image_url($subcat_image_id, 'skyyrose-collection') : '';
                ?>
                <a href="<?php echo esc_url(get_term_link($subcat)); ?>"
                   class="subcategory-card glass-card magnetic-hover"
                   style="--animation-delay: <?php echo esc_attr($index * 0.1); ?>s"
                   data-gsap="fade-up-stagger">
                    <?php if ($subcat_image_url) : ?>
                    <div class="subcategory-image">
                        <img src="<?php echo esc_url($subcat_image_url); ?>"
                             alt="<?php echo esc_attr($subcat->name); ?>"
                             loading="lazy">
                    </div>
                    <?php endif; ?>
                    <div class="subcategory-info">
                        <h3 class="subcategory-name"><?php echo esc_html($subcat->name); ?></h3>
                        <span class="subcategory-count">
                            <?php printf(esc_html(_n('%s item', '%s items', $subcat->count, 'skyyrose')), esc_html($subcat->count)); ?>
                        </span>
                    </div>
                    <span class="subcategory-arrow">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                    </span>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
    </section>
    <?php endif; ?>

    <!-- Shop Controls Bar -->
    <section class="shop-controls" data-gsap="fade-up">
        <div class="container">
            <div class="controls-wrapper glass-card">

                <div class="controls-left">
                    <!-- Results Count -->
                    <div class="results-count">
                        <?php
                        global $wp_query;
                        $total = $wp_query->found_posts;
                        printf(
                            esc_html(_n('Showing %s Product', 'Showing %s Products', $total, 'skyyrose')),
                            '<strong>' . esc_html($total) . '</strong>'
                        );
                        ?>
                    </div>
                </div>

                <div class="controls-right">
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

    <!-- Products Grid -->
    <section class="category-products section">
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
                 * Custom Pagination
                 */
                ?>
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
                 * No Products Found
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
                    <p><?php printf(esc_html__('We couldn\'t find any products in %s. Check back soon for new arrivals.', 'skyyrose'), '<strong>' . esc_html($category->name) . '</strong>'); ?></p>
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

    <!-- Related Categories -->
    <?php
    // Get sibling categories
    $sibling_categories = get_terms([
        'taxonomy'   => 'product_cat',
        'parent'     => $category->parent,
        'hide_empty' => true,
        'exclude'    => [$category_id],
        'number'     => 4,
    ]);

    if (!empty($sibling_categories) && !is_wp_error($sibling_categories)) :
    ?>
    <section class="related-categories-section section" data-gsap="fade-up">
        <div class="container">
            <header class="section-header">
                <h2 class="section-title"><?php esc_html_e('Explore More', 'skyyrose'); ?></h2>
                <p class="section-subtitle"><?php esc_html_e('Discover other collections you might love', 'skyyrose'); ?></p>
            </header>

            <div class="related-categories-grid">
                <?php foreach ($sibling_categories as $index => $related_cat) :
                    $related_image_id = get_term_meta($related_cat->term_id, 'thumbnail_id', true);
                    $related_image_url = $related_image_id ? wp_get_attachment_image_url($related_image_id, 'skyyrose-collection') : '';
                ?>
                <a href="<?php echo esc_url(get_term_link($related_cat)); ?>"
                   class="related-category-card glass-card magnetic-hover"
                   style="--animation-delay: <?php echo esc_attr($index * 0.1); ?>s"
                   data-gsap="fade-up-stagger">
                    <?php if ($related_image_url) : ?>
                    <div class="category-card-image">
                        <img src="<?php echo esc_url($related_image_url); ?>"
                             alt="<?php echo esc_attr($related_cat->name); ?>"
                             loading="lazy">
                    </div>
                    <?php endif; ?>
                    <div class="category-card-content">
                        <h3 class="category-card-title"><?php echo esc_html($related_cat->name); ?></h3>
                        <span class="category-card-count">
                            <?php printf(esc_html(_n('%s product', '%s products', $related_cat->count, 'skyyrose')), esc_html($related_cat->count)); ?>
                        </span>
                        <span class="category-card-link">
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
    <?php endif; ?>

    <!-- Newsletter CTA -->
    <section class="newsletter-cta-section section" style="--cta-color: <?php echo esc_attr($matched_collection['colors']['primary']); ?>;" data-gsap="fade-up">
        <div class="container">
            <div class="newsletter-cta glass-card">
                <div class="cta-content">
                    <h2 class="cta-title"><?php esc_html_e('Stay in the Loop', 'skyyrose'); ?></h2>
                    <p class="cta-text"><?php esc_html_e('Be the first to know about new arrivals, exclusive offers, and styling inspiration.', 'skyyrose'); ?></p>
                </div>
                <form class="cta-form" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" method="post">
                    <input type="hidden" name="action" value="skyyrose_newsletter">
                    <?php wp_nonce_field('skyyrose_newsletter', 'newsletter_nonce'); ?>
                    <div class="form-group">
                        <label for="newsletter-email" class="sr-only"><?php esc_html_e('Email address', 'skyyrose'); ?></label>
                        <input type="email"
                               id="newsletter-email"
                               name="email"
                               class="glass-input"
                               placeholder="<?php esc_attr_e('Enter your email', 'skyyrose'); ?>"
                               required>
                        <button type="submit" class="cta-submit magnetic-btn">
                            <span><?php esc_html_e('Subscribe', 'skyyrose'); ?></span>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M5 12h14M12 5l7 7-7 7"/>
                            </svg>
                        </button>
                    </div>
                </form>
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
