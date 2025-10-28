<?php
/**
 * The front page template file
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

get_header(); ?>

<main id="primary" class="site-main">
    <!-- Hero Section -->
    <section class="hero-section">
        <div class="hero-background"></div>
        <div class="hero-content">
            <h1 class="hero-title"><?php bloginfo('name'); ?></h1>
            <p class="hero-subtitle"><?php bloginfo('description'); ?></p>
            <?php if (class_exists('WooCommerce')) : ?>
                <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="hero-cta">
                    <?php esc_html_e('Explore Collection', 'skyy-rose-collection'); ?>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
            <?php endif; ?>
        </div>
    </section>

    <!-- Featured Categories -->
    <?php if (class_exists('WooCommerce')) : ?>
        <section class="featured-categories">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><?php esc_html_e('Shop by Category', 'skyy-rose-collection'); ?></h2>
                    <p class="section-subtitle"><?php esc_html_e('Discover our curated collections of luxury fashion', 'skyy-rose-collection'); ?></p>
                </div>
                
                <div class="categories-grid">
                    <?php
                    $featured_categories = get_terms(array(
                        'taxonomy' => 'product_cat',
                        'hide_empty' => true,
                        'number' => 4,
                        'parent' => 0,
                    ));
                    
                    if ($featured_categories && !is_wp_error($featured_categories)) :
                        foreach ($featured_categories as $category) :
                            $thumbnail_id = get_term_meta($category->term_id, 'thumbnail_id', true);
                            $image_url = $thumbnail_id ? wp_get_attachment_image_url($thumbnail_id, 'medium') : '';
                    ?>
                        <div class="category-card">
                            <a href="<?php echo esc_url(get_term_link($category)); ?>" class="category-link">
                                <?php if ($image_url) : ?>
                                    <div class="category-image">
                                        <img src="<?php echo esc_url($image_url); ?>" alt="<?php echo esc_attr($category->name); ?>">
                                    </div>
                                <?php endif; ?>
                                <div class="category-content">
                                    <h3 class="category-title"><?php echo esc_html($category->name); ?></h3>
                                    <p class="category-count">
                                        <?php printf(_n('%d item', '%d items', $category->count, 'skyy-rose-collection'), $category->count); ?>
                                    </p>
                                </div>
                            </a>
                        </div>
                    <?php
                        endforeach;
                    endif;
                    ?>
                </div>
            </div>
        </section>
    <?php endif; ?>

    <!-- Featured Products -->
    <?php if (class_exists('WooCommerce')) : ?>
        <section class="featured-products">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title"><?php esc_html_e('Featured Products', 'skyy-rose-collection'); ?></h2>
                    <p class="section-subtitle"><?php esc_html_e('Handpicked pieces from our latest collection', 'skyy-rose-collection'); ?></p>
                </div>
                
                <div class="products-grid">
                    <?php
                    $featured_products = wc_get_featured_product_ids();
                    if (!empty($featured_products)) :
                        $args = array(
                            'post_type' => 'product',
                            'posts_per_page' => 8,
                            'post__in' => $featured_products,
                            'meta_query' => WC()->query->get_meta_query(),
                        );
                        
                        $featured_query = new WP_Query($args);
                        
                        if ($featured_query->have_posts()) :
                            while ($featured_query->have_posts()) : $featured_query->the_post();
                                global $product;
                    ?>
                        <div class="product-card">
                            <a href="<?php the_permalink(); ?>" class="product-link">
                                <div class="product-image">
                                    <?php if (has_post_thumbnail()) : ?>
                                        <?php the_post_thumbnail('medium'); ?>
                                    <?php else : ?>
                                        <div class="product-placeholder">
                                            <span><?php esc_html_e('No Image', 'skyy-rose-collection'); ?></span>
                                        </div>
                                    <?php endif; ?>
                                    
                                    <?php if ($product->is_on_sale()) : ?>
                                        <span class="sale-badge"><?php esc_html_e('Sale', 'skyy-rose-collection'); ?></span>
                                    <?php endif; ?>
                                </div>
                                
                                <div class="product-content">
                                    <h3 class="product-title"><?php the_title(); ?></h3>
                                    <div class="product-price">
                                        <?php echo wp_kses_post($product->get_price_html()); ?>
                                    </div>
                                </div>
                            </a>
                        </div>
                    <?php
                            endwhile;
                            wp_reset_postdata();
                        endif;
                    endif;
                    ?>
                </div>
                
                <div class="section-footer">
                    <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn-outline">
                        <?php esc_html_e('View All Products', 'skyy-rose-collection'); ?>
                    </a>
                </div>
            </div>
        </section>
    <?php endif; ?>

    <!-- About Section -->
    <section class="about-section">
        <div class="container">
            <div class="row">
                <div class="col-6">
                    <div class="about-content">
                        <h2 class="section-title"><?php esc_html_e('About Skyy Rose Collection', 'skyy-rose-collection'); ?></h2>
                        <p class="section-text">
                            <?php esc_html_e('We believe that luxury fashion should be accessible, sustainable, and timeless. Our carefully curated collection features pieces that transcend seasons and trends, offering you investment pieces that will remain stylish for years to come.', 'skyy-rose-collection'); ?>
                        </p>
                        <p class="section-text">
                            <?php esc_html_e('Each piece in our collection is selected for its exceptional quality, ethical production, and timeless design. We work directly with artisans and designers who share our commitment to excellence and sustainability.', 'skyy-rose-collection'); ?>
                        </p>
                        <a href="<?php echo esc_url(get_permalink(get_page_by_path('about'))); ?>" class="btn-outline">
                            <?php esc_html_e('Learn More', 'skyy-rose-collection'); ?>
                        </a>
                    </div>
                </div>
                <div class="col-6">
                    <div class="about-image">
                        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/about-image.jpg'); ?>" alt="<?php esc_attr_e('About Skyy Rose Collection', 'skyy-rose-collection'); ?>">
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Newsletter Section -->
    <section class="newsletter-section">
        <div class="container">
            <div class="newsletter-content">
                <h2 class="section-title"><?php esc_html_e('Stay in Style', 'skyy-rose-collection'); ?></h2>
                <p class="section-subtitle">
                    <?php esc_html_e('Subscribe to our newsletter for exclusive access to new collections, styling tips, and special offers.', 'skyy-rose-collection'); ?>
                </p>
                
                <form class="newsletter-form" action="#" method="post">
                    <div class="form-group">
                        <input type="email" name="email" placeholder="<?php esc_attr_e('Enter your email address', 'skyy-rose-collection'); ?>" required>
                        <button type="submit" class="btn-primary">
                            <?php esc_html_e('Subscribe', 'skyy-rose-collection'); ?>
                        </button>
                    </div>
                    <p class="form-note">
                        <?php esc_html_e('By subscribing, you agree to our Privacy Policy and consent to receive updates from our company.', 'skyy-rose-collection'); ?>
                    </p>
                </form>
            </div>
        </div>
    </section>
</main>

<?php get_footer(); ?>
