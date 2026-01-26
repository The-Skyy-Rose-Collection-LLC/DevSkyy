<?php
/**
 * WooCommerce Shop Archive Template
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();

$current_collection = '';
$term = get_queried_object();
if ($term instanceof WP_Term && $term->taxonomy === 'product_cat') {
    $current_collection = $term->slug;
}
$collections = skyyrose_get_collections();
$collection_data = $collections[$current_collection] ?? null;
?>

<section class="shop-hero<?php echo $collection_data ? ' collection-hero' : ''; ?>"<?php echo $collection_data ? ' style="--collection-color: ' . esc_attr($collection_data['color']) . ';"' : ''; ?>>
    <?php if ($collection_data) : ?>
        <div class="collection-badge"><?php echo esc_html($collection_data['tagline'] ?? 'Collection'); ?></div>
    <?php endif; ?>

    <h1 class="shop-title">
        <?php
        if ($collection_data) {
            echo esc_html($collection_data['name']);
        } elseif (is_search()) {
            printf(esc_html__('Search results for: %s', 'skyyrose'), get_search_query());
        } else {
            woocommerce_page_title();
        }
        ?>
    </h1>

    <?php if ($collection_data && isset($collection_data['description'])) : ?>
        <p class="shop-subtitle"><?php echo esc_html($collection_data['description']); ?></p>
    <?php endif; ?>

    <div class="scroll-indicator">
        <span>Discover</span>
    </div>
</section>

<?php if ($collection_data) : ?>
<section class="collection-story">
    <div class="container">
        <div class="collection-story-grid">
            <div class="collection-story-content">
                <h2><?php echo esc_html($collection_data['story_title'] ?? 'The Story'); ?></h2>
                <p><?php echo esc_html($collection_data['story'] ?? ''); ?></p>
                <?php if (isset($collection_data['features'])) : ?>
                <div class="collection-features">
                    <?php foreach ($collection_data['features'] as $feature) : ?>
                    <div class="feature-item">
                        <span class="feature-icon">✦</span>
                        <div>
                            <h4><?php echo esc_html($feature['title']); ?></h4>
                            <p><?php echo esc_html($feature['description']); ?></p>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
            </div>
            <div class="collection-story-visual">
                <?php echo esc_html($collection_data['icon'] ?? '◆'); ?>
            </div>
        </div>
    </div>
</section>
<?php endif; ?>

<section class="shop-section">
    <div class="container">
        <div class="shop-toolbar">
            <div class="shop-filters">
                <button class="filter-btn active" data-filter="all">All</button>
                <?php if (!$current_collection) : ?>
                    <?php foreach ($collections as $slug => $data) : ?>
                    <button class="filter-btn" data-filter="<?php echo esc_attr($slug); ?>"><?php echo esc_html($data['name']); ?></button>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>

            <div class="shop-sort">
                <label for="shop-orderby" class="visually-hidden"><?php esc_html_e('Sort by', 'skyyrose'); ?></label>
                <select id="shop-orderby" class="shop-orderby">
                    <option value="default"><?php esc_html_e('Default sorting', 'skyyrose'); ?></option>
                    <option value="popularity"><?php esc_html_e('Sort by popularity', 'skyyrose'); ?></option>
                    <option value="date"><?php esc_html_e('Sort by latest', 'skyyrose'); ?></option>
                    <option value="price"><?php esc_html_e('Sort by price: low to high', 'skyyrose'); ?></option>
                    <option value="price-desc"><?php esc_html_e('Sort by price: high to low', 'skyyrose'); ?></option>
                </select>
            </div>
        </div>

        <?php if (woocommerce_product_loop()) : ?>
            <div class="products-grid">
                <?php
                while (have_posts()) :
                    the_post();
                    global $product;
                    ?>
                    <div class="product-card" data-collection="<?php echo esc_attr(skyyrose_get_product_collection_slug($product->get_id())); ?>">
                        <?php skyyrose_product_badges($product->get_id()); ?>

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
                                    class="product-action-btn quick-add"
                                    data-add-to-cart="<?php echo esc_attr($product->get_id()); ?>"
                                    aria-label="<?php esc_attr_e('Add to cart', 'skyyrose'); ?>"
                                    title="<?php esc_attr_e('Quick Add', 'skyyrose'); ?>"
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
                                    aria-label="<?php esc_attr_e('View product', 'skyyrose'); ?>"
                                    title="<?php esc_attr_e('Quick View', 'skyyrose'); ?>"
                                >
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                        <circle cx="12" cy="12" r="3"/>
                                    </svg>
                                </a>

                                <button
                                    class="product-action-btn wishlist-btn"
                                    data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                                    aria-label="<?php esc_attr_e('Add to wishlist', 'skyyrose'); ?>"
                                    title="<?php esc_attr_e('Add to Wishlist', 'skyyrose'); ?>"
                                >
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div class="product-info">
                            <?php
                            $collection = skyyrose_get_product_collection($product->get_id());
                            if ($collection) : ?>
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
                <?php endwhile; ?>
            </div>

            <?php
            $total_pages = wc_get_loop_prop('total_pages');
            if ($total_pages > 1) :
            ?>
            <nav class="shop-pagination">
                <?php
                echo paginate_links([
                    'total'     => $total_pages,
                    'current'   => max(1, get_query_var('paged')),
                    'prev_text' => '←',
                    'next_text' => '→',
                ]);
                ?>
            </nav>
            <?php endif; ?>

        <?php else : ?>
            <div class="no-products">
                <h2><?php esc_html_e('No products found', 'skyyrose'); ?></h2>
                <p><?php esc_html_e('Check back soon for new arrivals.', 'skyyrose'); ?></p>
                <a href="<?php echo esc_url(home_url('/shop')); ?>" class="btn btn-primary"><?php esc_html_e('Browse All Products', 'skyyrose'); ?></a>
            </div>
        <?php endif; ?>
    </div>
</section>

<?php if ($collection_data) : ?>
<section class="collection-cta">
    <div class="container">
        <h2>Experience <?php echo esc_html($collection_data['name']); ?></h2>
        <p>Discover the full collection and find your perfect piece.</p>
        <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn-outline">View All Collections</a>
    </div>
</section>
<?php endif; ?>

<?php get_footer(); ?>
