<?php
/**
 * Custom Shop Page - SkyyRose Luxury Experience
 *
 * Dark luxury aesthetic with glassmorphism, GSAP animations,
 * and collection filtering.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header('shop');

// Get current collection filter
$current_collection = isset($_GET['collection']) ? sanitize_text_field($_GET['collection']) : 'all';

// Collection data
$collections = [
    'all' => [
        'name' => 'All Collections',
        'color' => '#B76E79',
    ],
    'signature' => [
        'name' => 'Signature',
        'color' => '#D4AF37',
        'category_id' => 19,
    ],
    'black-rose' => [
        'name' => 'Black Rose',
        'color' => '#8B0000',
        'category_id' => 20,
    ],
    'love-hurts' => [
        'name' => 'Love Hurts',
        'color' => '#B76E79',
        'category_id' => 18,
    ],
];

// Query products
$args = [
    'post_type' => 'product',
    'posts_per_page' => 12,
    'post_status' => 'publish',
];

if ($current_collection !== 'all' && isset($collections[$current_collection]['category_id'])) {
    $args['tax_query'] = [
        [
            'taxonomy' => 'product_cat',
            'field' => 'term_id',
            'terms' => $collections[$current_collection]['category_id'],
        ],
    ];
}

$products = new WP_Query($args);
?>

<div class="skyyrose-shop" data-collection="<?php echo esc_attr($current_collection); ?>">
    <!-- Ambient Background -->
    <div class="shop-ambient">
        <div class="ambient-orb ambient-orb--1"></div>
        <div class="ambient-orb ambient-orb--2"></div>
        <div class="ambient-orb ambient-orb--3"></div>
    </div>

    <!-- Hero Section -->
    <section class="shop-hero">
        <div class="container">
            <div class="shop-hero__content gsap-fade-up">
                <span class="shop-hero__eyebrow">The Collection</span>
                <h1 class="shop-hero__title">
                    <?php if ($current_collection === 'all') : ?>
                        Where Love Meets Luxury
                    <?php else : ?>
                        <?php echo esc_html($collections[$current_collection]['name']); ?>
                    <?php endif; ?>
                </h1>
                <p class="shop-hero__subtitle">
                    Discover pieces crafted for those who dare to stand out.
                </p>
            </div>
        </div>
    </section>

    <!-- Collection Filter -->
    <section class="shop-filters">
        <div class="container">
            <div class="filter-tabs gsap-fade-up">
                <?php foreach ($collections as $slug => $collection) : ?>
                    <a
                        href="<?php echo esc_url(add_query_arg('collection', $slug, wc_get_page_permalink('shop'))); ?>"
                        class="filter-tab <?php echo $current_collection === $slug ? 'is-active' : ''; ?>"
                        data-collection="<?php echo esc_attr($slug); ?>"
                        style="--tab-color: <?php echo esc_attr($collection['color']); ?>"
                    >
                        <span class="filter-tab__name"><?php echo esc_html($collection['name']); ?></span>
                        <?php if ($slug !== 'all') : ?>
                            <span class="filter-tab__indicator"></span>
                        <?php endif; ?>
                    </a>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

    <!-- Products Grid -->
    <section class="shop-products">
        <div class="container">
            <?php if ($products->have_posts()) : ?>
                <div class="products-grid">
                    <?php
                    $index = 0;
                    while ($products->have_posts()) :
                        $products->the_post();
                        global $product;

                        $image_id = $product->get_image_id();
                        $image_url = wp_get_attachment_image_url($image_id, 'skyyrose-product');
                        $gallery_ids = $product->get_gallery_image_ids();
                        $hover_image = !empty($gallery_ids) ? wp_get_attachment_image_url($gallery_ids[0], 'skyyrose-product') : $image_url;

                        // Get collection
                        $terms = get_the_terms($product->get_id(), 'product_cat');
                        $product_collection = 'signature';
                        if ($terms && !is_wp_error($terms)) {
                            foreach ($terms as $term) {
                                $slug = strtolower($term->slug);
                                if (strpos($slug, 'signature') !== false) $product_collection = 'signature';
                                elseif (strpos($slug, 'black') !== false || strpos($slug, 'rose') !== false) $product_collection = 'black-rose';
                                elseif (strpos($slug, 'love') !== false || strpos($slug, 'hurts') !== false) $product_collection = 'love-hurts';
                            }
                        }
                    ?>
                        <article class="product-card gsap-fade-up" data-index="<?php echo $index; ?>" data-collection="<?php echo esc_attr($product_collection); ?>">
                            <a href="<?php the_permalink(); ?>" class="product-card__link">
                                <!-- Image Container -->
                                <div class="product-card__image-wrapper">
                                    <div class="product-card__image">
                                        <?php if ($image_url) : ?>
                                            <img
                                                src="<?php echo esc_url($image_url); ?>"
                                                alt="<?php echo esc_attr($product->get_name()); ?>"
                                                class="product-card__img product-card__img--primary"
                                                loading="lazy"
                                            >
                                            <?php if ($hover_image !== $image_url) : ?>
                                                <img
                                                    src="<?php echo esc_url($hover_image); ?>"
                                                    alt="<?php echo esc_attr($product->get_name()); ?>"
                                                    class="product-card__img product-card__img--hover"
                                                    loading="lazy"
                                                >
                                            <?php endif; ?>
                                        <?php else : ?>
                                            <div class="product-card__placeholder">
                                                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                                                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                                                    <circle cx="8.5" cy="8.5" r="1.5"/>
                                                    <path d="M21 15l-5-5L5 21"/>
                                                </svg>
                                            </div>
                                        <?php endif; ?>
                                    </div>

                                    <!-- Quick Actions -->
                                    <div class="product-card__actions">
                                        <button type="button" class="product-card__action" data-action="quickview" data-product-id="<?php echo $product->get_id(); ?>" data-product-url="<?php the_permalink(); ?>" aria-label="Quick view">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                                <circle cx="12" cy="12" r="3"/>
                                            </svg>
                                        </button>
                                        <?php if ($product->is_purchasable() && $product->is_in_stock()) : ?>
                                            <button type="button" class="product-card__action" data-action="addtocart" data-product-id="<?php echo $product->get_id(); ?>" aria-label="Add to cart">
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                                                    <line x1="3" y1="6" x2="21" y2="6"/>
                                                    <path d="M16 10a4 4 0 01-8 0"/>
                                                </svg>
                                            </button>
                                        <?php endif; ?>
                                    </div>

                                    <!-- Collection Badge -->
                                    <span class="product-card__badge" style="--badge-color: <?php echo esc_attr($collections[$product_collection]['color']); ?>">
                                        <?php echo esc_html($collections[$product_collection]['name']); ?>
                                    </span>
                                </div>

                                <!-- Product Info -->
                                <div class="product-card__info">
                                    <h3 class="product-card__title"><?php echo esc_html($product->get_name()); ?></h3>
                                    <div class="product-card__price">
                                        <?php echo $product->get_price_html(); ?>
                                    </div>
                                </div>
                            </a>
                        </article>
                    <?php
                        $index++;
                    endwhile;
                    wp_reset_postdata();
                    ?>
                </div>

                <!-- Load More -->
                <?php if ($products->max_num_pages > 1) : ?>
                    <div class="shop-load-more gsap-fade-up">
                        <button type="button" class="btn btn--outline btn--lg" id="loadMoreProducts">
                            <span>Load More</span>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"/>
                            </svg>
                        </button>
                    </div>
                <?php endif; ?>

            <?php else : ?>
                <div class="shop-empty">
                    <p>No products found in this collection.</p>
                    <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn--primary">View All Products</a>
                </div>
            <?php endif; ?>
        </div>
    </section>
</div>

<?php get_template_part('template-parts/shop', 'styles'); ?>
<?php get_template_part('template-parts/shop', 'scripts'); ?>

<?php get_footer('shop'); ?>
