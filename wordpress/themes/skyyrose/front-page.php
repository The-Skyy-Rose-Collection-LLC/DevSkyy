<?php
/**
 * Front Page Template
 *
 * The template for displaying the homepage with video hero,
 * collections grid, parallax sections, and featured products.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header();

// Get collections data
$collections = [
    'black-rose' => skyyrose_get_collection('black-rose'),
    'signature'  => skyyrose_get_collection('signature'),
    'love-hurts' => skyyrose_get_collection('love-hurts'),
];

// Get customizer options with defaults
$hero_video_url = get_theme_mod('skyyrose_hero_video', SKYYROSE_URI . '/assets/video/hero-bg.mp4');
$hero_poster    = get_theme_mod('skyyrose_hero_poster', SKYYROSE_URI . '/assets/images/hero-poster.jpg');
$parallax_image = get_theme_mod('skyyrose_parallax_image', SKYYROSE_URI . '/assets/images/parallax-bg.jpg');
$instagram_handle = get_theme_mod('skyyrose_instagram_handle', 'SkyyRose');
?>

<main id="main-content" class="site-main front-page" role="main" style="view-transition-name: main-content;">

    <?php
    /**
     * =========================================================================
     * SECTION 1: HERO (100vh Video Background)
     * =========================================================================
     */
    ?>
    <section
        id="hero"
        class="hero-section"
        aria-label="<?php esc_attr_e('Welcome to SkyyRose', 'skyyrose'); ?>"
        style="view-transition-name: hero-section;"
    >
        <!-- Video Background -->
        <div class="hero-video-wrapper">
            <video
                class="hero-video parallax-layer"
                autoplay
                muted
                loop
                playsinline
                poster="<?php echo esc_url($hero_poster); ?>"
                aria-hidden="true"
            >
                <source src="<?php echo esc_url($hero_video_url); ?>" type="video/mp4">
            </video>
            <div class="hero-video-overlay" aria-hidden="true"></div>
        </div>

        <!-- Hero Content -->
        <div class="hero-content container">
            <div class="hero-text gsap-fade-up">
                <p class="hero-subtitle" data-gsap-delay="0.2">
                    <?php echo esc_html(get_theme_mod('skyyrose_hero_subtitle', 'SkyyRose')); ?>
                </p>
                <h1 class="hero-title" data-gsap-delay="0.4">
                    <?php echo esc_html(get_theme_mod('skyyrose_hero_title', 'Where Love Meets Luxury')); ?>
                </h1>
                <div class="hero-cta gsap-fade-up" data-gsap-delay="0.6">
                    <a
                        href="<?php echo esc_url(get_theme_mod('skyyrose_hero_cta_link', '/collections/')); ?>"
                        class="btn btn-primary magnetic-btn"
                    >
                        <span class="btn-text">
                            <?php echo esc_html(get_theme_mod('skyyrose_hero_cta_text', 'Explore Collections')); ?>
                        </span>
                        <span class="btn-icon" aria-hidden="true">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M4.167 10h11.666M10 4.167L15.833 10 10 15.833" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </span>
                    </a>
                </div>
            </div>
        </div>

        <!-- Scroll Indicator -->
        <div class="scroll-indicator gsap-fade-up" data-gsap-delay="1" aria-hidden="true">
            <div class="scroll-indicator-inner">
                <span class="scroll-text"><?php esc_html_e('Scroll', 'skyyrose'); ?></span>
                <div class="scroll-line">
                    <div class="scroll-dot"></div>
                </div>
            </div>
        </div>
    </section>

    <?php
    /**
     * =========================================================================
     * SECTION 2: COLLECTIONS GRID
     * =========================================================================
     */
    ?>
    <section
        id="collections"
        class="collections-section section"
        aria-labelledby="collections-title"
        style="view-transition-name: collections-section;"
    >
        <div class="container">
            <!-- Section Header -->
            <header class="section-header gsap-fade-up">
                <h2 id="collections-title" class="section-title">
                    <?php esc_html_e('The Collections', 'skyyrose'); ?>
                </h2>
                <div class="section-divider" aria-hidden="true">
                    <span class="divider-line"></span>
                    <span class="divider-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 21C12 21 4 14.5 4 9.5C4 6.46 6.46 4 9.5 4C11.06 4 12 5 12 5C12 5 12.94 4 14.5 4C17.54 4 20 6.46 20 9.5C20 14.5 12 21 12 21Z" fill="currentColor"/>
                        </svg>
                    </span>
                    <span class="divider-line"></span>
                </div>
            </header>

            <!-- Collections Grid -->
            <div class="collections-grid gsap-stagger" role="list">
                <?php
                $delay = 0;
                foreach ($collections as $slug => $collection) :
                    $collection_url = get_term_link($slug, 'product_cat');
                    if (is_wp_error($collection_url)) {
                        $collection_url = home_url('/collection/' . $slug . '/');
                    }
                    $collection_image = get_theme_mod(
                        'skyyrose_collection_' . str_replace('-', '_', $slug) . '_image',
                        SKYYROSE_URI . '/assets/images/collection-' . $slug . '.jpg'
                    );
                ?>
                    <article
                        class="collection-card glass-card gsap-scale-in"
                        role="listitem"
                        data-gsap-delay="<?php echo esc_attr($delay); ?>"
                        data-collection="<?php echo esc_attr($slug); ?>"
                        style="--collection-primary: <?php echo esc_attr($collection['colors']['primary']); ?>; --collection-secondary: <?php echo esc_attr($collection['colors']['secondary']); ?>;"
                    >
                        <div class="collection-image-wrapper">
                            <img
                                src="<?php echo esc_url($collection_image); ?>"
                                alt="<?php echo esc_attr($collection['name']); ?> Collection"
                                class="collection-image"
                                loading="lazy"
                                decoding="async"
                            >
                            <div class="collection-overlay" aria-hidden="true"></div>
                        </div>

                        <div class="collection-content">
                            <h3 class="collection-name">
                                <?php echo esc_html($collection['name']); ?>
                            </h3>
                            <p class="collection-tagline">
                                <?php echo esc_html($collection['tagline']); ?>
                            </p>
                            <a
                                href="<?php echo esc_url($collection_url); ?>"
                                class="collection-link magnetic-btn"
                                aria-label="<?php printf(esc_attr__('Explore %s Collection', 'skyyrose'), $collection['name']); ?>"
                            >
                                <span class="link-text"><?php esc_html_e('Explore', 'skyyrose'); ?></span>
                                <span class="link-arrow" aria-hidden="true">
                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                        <path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </span>
                            </a>
                        </div>

                        <!-- Hover Effect Layer -->
                        <div class="collection-hover-layer" aria-hidden="true"></div>
                    </article>
                <?php
                    $delay += 0.15;
                endforeach;
                ?>
            </div>
        </div>
    </section>

    <?php
    /**
     * =========================================================================
     * SECTION 3: PARALLAX BRAND SECTION
     * =========================================================================
     */
    ?>
    <section
        id="brand-statement"
        class="parallax-section"
        aria-labelledby="brand-tagline"
        style="view-transition-name: parallax-section;"
    >
        <!-- Parallax Background -->
        <div class="parallax-bg parallax-layer" aria-hidden="true">
            <img
                src="<?php echo esc_url($parallax_image); ?>"
                alt=""
                class="parallax-image"
                loading="lazy"
                decoding="async"
            >
            <div class="parallax-overlay"></div>
        </div>

        <!-- Parallax Content -->
        <div class="parallax-content container">
            <blockquote class="brand-statement gsap-fade-up">
                <p id="brand-tagline" class="brand-tagline">
                    <?php echo esc_html(get_theme_mod('skyyrose_brand_tagline', 'Luxury is not about the price tag. It\'s about the feeling of being extraordinary.')); ?>
                </p>
                <footer class="brand-attribution">
                    <cite class="brand-name">
                        <?php echo esc_html(get_theme_mod('skyyrose_brand_attribution', '- SkyyRose')); ?>
                    </cite>
                </footer>
            </blockquote>
        </div>

        <!-- Decorative Elements -->
        <div class="parallax-decoration" aria-hidden="true">
            <div class="decoration-line left"></div>
            <div class="decoration-line right"></div>
        </div>
    </section>

    <?php
    /**
     * =========================================================================
     * SECTION 4: FEATURED PRODUCTS / NEW ARRIVALS
     * =========================================================================
     */
    if (class_exists('WooCommerce')) :
        $featured_products = wc_get_products([
            'status'   => 'publish',
            'limit'    => 4,
            'orderby'  => 'date',
            'order'    => 'DESC',
            'featured' => true,
        ]);

        // Fallback to latest products if no featured products
        if (empty($featured_products)) {
            $featured_products = wc_get_products([
                'status'  => 'publish',
                'limit'   => 4,
                'orderby' => 'date',
                'order'   => 'DESC',
            ]);
        }

        if (!empty($featured_products)) :
    ?>
    <section
        id="featured-products"
        class="featured-products-section section"
        aria-labelledby="featured-title"
        style="view-transition-name: featured-section;"
    >
        <div class="container">
            <!-- Section Header -->
            <header class="section-header gsap-fade-up">
                <h2 id="featured-title" class="section-title">
                    <?php esc_html_e('New Arrivals', 'skyyrose'); ?>
                </h2>
                <p class="section-subtitle">
                    <?php esc_html_e('Discover our latest pieces crafted for the extraordinary', 'skyyrose'); ?>
                </p>
            </header>

            <!-- Products Grid -->
            <div class="products-grid gsap-stagger" role="list">
                <?php
                $delay = 0;
                foreach ($featured_products as $product) :
                    $product_id = $product->get_id();
                    $product_image = wp_get_attachment_image_url($product->get_image_id(), 'skyyrose-product');
                    $product_image_hover = get_post_meta($product_id, '_skyyrose_hover_image', true);
                    $has_3d = get_post_meta($product_id, '_skyyrose_3d_enabled', true) === 'yes';
                ?>
                    <article
                        class="product-card glass-card gsap-scale-in"
                        role="listitem"
                        data-gsap-delay="<?php echo esc_attr($delay); ?>"
                        data-product-id="<?php echo esc_attr($product_id); ?>"
                    >
                        <!-- Product Image -->
                        <div class="product-image-wrapper">
                            <a href="<?php echo esc_url($product->get_permalink()); ?>" class="product-image-link">
                                <img
                                    src="<?php echo esc_url($product_image); ?>"
                                    alt="<?php echo esc_attr($product->get_name()); ?>"
                                    class="product-image product-image-primary"
                                    loading="lazy"
                                    decoding="async"
                                >
                                <?php if ($product_image_hover) : ?>
                                    <img
                                        src="<?php echo esc_url($product_image_hover); ?>"
                                        alt=""
                                        class="product-image product-image-hover"
                                        loading="lazy"
                                        decoding="async"
                                        aria-hidden="true"
                                    >
                                <?php endif; ?>
                            </a>

                            <!-- Product Badges -->
                            <div class="product-badges">
                                <?php if ($product->is_on_sale()) : ?>
                                    <span class="badge badge-sale">
                                        <?php esc_html_e('Sale', 'skyyrose'); ?>
                                    </span>
                                <?php endif; ?>

                                <?php if ($has_3d) : ?>
                                    <span class="badge badge-3d" title="<?php esc_attr_e('3D View Available', 'skyyrose'); ?>">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                            <path d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                                            <path d="M8 8V15M8 8L2 4.5M8 8L14 4.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                                        </svg>
                                        <span class="sr-only"><?php esc_html_e('3D View Available', 'skyyrose'); ?></span>
                                    </span>
                                <?php endif; ?>

                                <?php if (!$product->is_in_stock()) : ?>
                                    <span class="badge badge-sold-out">
                                        <?php esc_html_e('Sold Out', 'skyyrose'); ?>
                                    </span>
                                <?php endif; ?>
                            </div>

                            <!-- Quick Actions -->
                            <div class="product-actions">
                                <button
                                    type="button"
                                    class="action-btn quick-view-btn magnetic-btn"
                                    data-product-id="<?php echo esc_attr($product_id); ?>"
                                    aria-label="<?php printf(esc_attr__('Quick view %s', 'skyyrose'), $product->get_name()); ?>"
                                >
                                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                        <path d="M10 4C4 4 1 10 1 10C1 10 4 16 10 16C16 16 19 10 19 10C19 10 16 4 10 4Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                        <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="1.5"/>
                                    </svg>
                                    <span class="action-text"><?php esc_html_e('Quick View', 'skyyrose'); ?></span>
                                </button>

                                <button
                                    type="button"
                                    class="action-btn wishlist-btn magnetic-btn"
                                    data-product-id="<?php echo esc_attr($product_id); ?>"
                                    aria-label="<?php printf(esc_attr__('Add %s to wishlist', 'skyyrose'), $product->get_name()); ?>"
                                >
                                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                        <path d="M10 17.5C10 17.5 2.5 12.5 2.5 7.5C2.5 4.73858 4.73858 2.5 7.5 2.5C8.79593 2.5 10 3.33333 10 3.33333C10 3.33333 11.2041 2.5 12.5 2.5C15.2614 2.5 17.5 4.73858 17.5 7.5C17.5 12.5 10 17.5 10 17.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <!-- Product Info -->
                        <div class="product-info">
                            <h3 class="product-name">
                                <a href="<?php echo esc_url($product->get_permalink()); ?>">
                                    <?php echo esc_html($product->get_name()); ?>
                                </a>
                            </h3>

                            <?php
                            $categories = wc_get_product_category_list($product_id, ', ');
                            if ($categories) :
                            ?>
                                <p class="product-category">
                                    <?php echo wp_kses_post($categories); ?>
                                </p>
                            <?php endif; ?>

                            <div class="product-price">
                                <?php echo wp_kses_post($product->get_price_html()); ?>
                            </div>
                        </div>
                    </article>
                <?php
                    $delay += 0.1;
                endforeach;
                ?>
            </div>

            <!-- View All Link -->
            <div class="section-footer gsap-fade-up">
                <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn-outline magnetic-btn">
                    <span class="btn-text"><?php esc_html_e('View All Products', 'skyyrose'); ?></span>
                    <span class="btn-icon" aria-hidden="true">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M4.167 10h11.666M10 4.167L15.833 10 10 15.833" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </span>
                </a>
            </div>
        </div>
    </section>
    <?php
        endif;
    endif;
    ?>

    <?php
    /**
     * =========================================================================
     * SECTION 5: INSTAGRAM FEED
     * =========================================================================
     */
    ?>
    <section
        id="instagram"
        class="instagram-section section"
        aria-labelledby="instagram-title"
        style="view-transition-name: instagram-section;"
    >
        <div class="container">
            <!-- Section Header -->
            <header class="section-header gsap-fade-up">
                <h2 id="instagram-title" class="section-title">
                    <?php printf(esc_html__('Follow @%s', 'skyyrose'), esc_html($instagram_handle)); ?>
                </h2>
                <p class="section-subtitle">
                    <?php esc_html_e('Join our community and share your SkyyRose moments', 'skyyrose'); ?>
                </p>
            </header>

            <!-- Instagram Feed Container -->
            <div class="instagram-feed gsap-stagger">
                <?php
                /**
                 * Instagram Feed Shortcode
                 *
                 * Compatible with popular Instagram plugins:
                 * - Smash Balloon Instagram Feed (instagram-feed)
                 * - Instagram Feed by developer (instagram-feed-gallery)
                 * - Starter Templates (starter-templates-instagram)
                 */
                $instagram_shortcode = get_theme_mod('skyyrose_instagram_shortcode', '[instagram-feed feed=1]');

                if (!empty($instagram_shortcode)) {
                    echo do_shortcode($instagram_shortcode);
                } else {
                    // Fallback placeholder grid
                    ?>
                    <div class="instagram-placeholder-grid" role="list" aria-label="<?php esc_attr_e('Instagram Feed Placeholder', 'skyyrose'); ?>">
                        <?php for ($i = 1; $i <= 6; $i++) : ?>
                            <div class="instagram-placeholder-item gsap-scale-in" role="listitem" data-gsap-delay="<?php echo esc_attr(($i - 1) * 0.1); ?>">
                                <div class="placeholder-image"></div>
                                <div class="placeholder-overlay">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                        <rect x="2" y="2" width="20" height="20" rx="5" stroke="currentColor" stroke-width="1.5"/>
                                        <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.5"/>
                                        <circle cx="17.5" cy="6.5" r="1.5" fill="currentColor"/>
                                    </svg>
                                </div>
                            </div>
                        <?php endfor; ?>
                    </div>
                    <?php
                }
                ?>
            </div>

            <!-- Instagram CTA -->
            <div class="section-footer gsap-fade-up">
                <a
                    href="https://instagram.com/<?php echo esc_attr($instagram_handle); ?>"
                    class="btn btn-outline magnetic-btn"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    <span class="btn-icon" aria-hidden="true">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <rect x="2" y="2" width="16" height="16" rx="4" stroke="currentColor" stroke-width="1.5"/>
                            <circle cx="10" cy="10" r="3.5" stroke="currentColor" stroke-width="1.5"/>
                            <circle cx="14.5" cy="5.5" r="1" fill="currentColor"/>
                        </svg>
                    </span>
                    <span class="btn-text">
                        <?php printf(esc_html__('Follow @%s', 'skyyrose'), esc_html($instagram_handle)); ?>
                    </span>
                </a>
            </div>
        </div>
    </section>

</main>

<?php
/**
 * =========================================================================
 * FRONT PAGE STYLES (Inline Critical CSS)
 * =========================================================================
 */
?>
<style id="skyyrose-front-page-critical">
/* Hero Section */
.hero-section {
    position: relative;
    height: 100vh;
    min-height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.hero-video-wrapper {
    position: absolute;
    inset: 0;
    z-index: var(--z-below);
}

.hero-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.hero-video-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0.4) 0%,
        rgba(0, 0, 0, 0.2) 50%,
        rgba(0, 0, 0, 0.6) 100%
    );
}

.hero-content {
    position: relative;
    z-index: var(--z-above);
    text-align: center;
    max-width: var(--container-md);
}

.hero-text {
    padding: var(--space-8);
}

.hero-subtitle {
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 500;
    letter-spacing: var(--tracking-luxury);
    text-transform: uppercase;
    color: var(--skyyrose-rose-gold);
    margin-bottom: var(--space-4);
}

.hero-title {
    font-size: var(--text-6xl);
    font-weight: 400;
    line-height: var(--leading-tight);
    letter-spacing: var(--tracking-tight);
    margin-bottom: var(--space-8);
    text-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

@media (max-width: 768px) {
    .hero-title {
        font-size: var(--text-4xl);
    }
}

.hero-cta {
    display: inline-block;
}

/* Scroll Indicator */
.scroll-indicator {
    position: absolute;
    bottom: var(--space-10);
    left: 50%;
    transform: translateX(-50%);
    z-index: var(--z-above);
}

.scroll-indicator-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
}

.scroll-text {
    font-size: var(--text-xs);
    letter-spacing: var(--tracking-widest);
    text-transform: uppercase;
    color: var(--skyyrose-white);
    opacity: 0.7;
}

.scroll-line {
    width: 1px;
    height: 60px;
    background: rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
}

.scroll-dot {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 3px;
    height: 10px;
    background: var(--skyyrose-rose-gold);
    border-radius: var(--radius-full);
    animation: scrollDot 2s ease-in-out infinite;
}

@keyframes scrollDot {
    0%, 100% { top: 0; opacity: 1; }
    50% { top: 50px; opacity: 0.3; }
}

/* Section Headers */
.section-header {
    text-align: center;
    margin-bottom: var(--space-16);
}

.section-title {
    font-size: var(--text-4xl);
    margin-bottom: var(--space-4);
}

.section-subtitle {
    font-size: var(--text-lg);
    color: rgba(255, 255, 255, 0.7);
    max-width: 600px;
    margin: 0 auto;
}

.section-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-4);
    margin-top: var(--space-6);
}

.divider-line {
    width: 60px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--skyyrose-rose-gold), transparent);
}

.divider-icon {
    color: var(--skyyrose-primary);
}

.section-footer {
    text-align: center;
    margin-top: var(--space-12);
}

/* Collections Grid */
.collections-section {
    background: var(--skyyrose-black);
}

.collections-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-8);
}

@media (max-width: 1024px) {
    .collections-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 640px) {
    .collections-grid {
        grid-template-columns: 1fr;
    }
}

.collection-card {
    position: relative;
    border-radius: var(--radius-2xl);
    overflow: hidden;
    aspect-ratio: 3 / 4;
    cursor: pointer;
    transition: transform var(--transition-luxury), box-shadow var(--transition-luxury);
}

.collection-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-luxury);
}

.collection-image-wrapper {
    position: absolute;
    inset: 0;
}

.collection-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-luxury);
}

.collection-card:hover .collection-image {
    transform: scale(1.05);
}

.collection-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        to top,
        rgba(0, 0, 0, 0.8) 0%,
        rgba(0, 0, 0, 0.2) 50%,
        transparent 100%
    );
}

.collection-content {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: var(--space-8);
    z-index: var(--z-above);
}

.collection-name {
    font-size: var(--text-2xl);
    margin-bottom: var(--space-2);
    color: var(--skyyrose-white);
}

.collection-tagline {
    font-size: var(--text-sm);
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: var(--space-4);
}

.collection-link {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    font-weight: 500;
    letter-spacing: var(--tracking-wide);
    text-transform: uppercase;
    color: var(--skyyrose-rose-gold);
    transition: gap var(--transition-fast);
}

.collection-link:hover {
    gap: var(--space-3);
    color: var(--skyyrose-white);
}

.collection-hover-layer {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        135deg,
        var(--collection-primary, var(--skyyrose-primary)) 0%,
        var(--collection-secondary, var(--skyyrose-secondary)) 100%
    );
    opacity: 0;
    transition: opacity var(--transition-luxury);
    pointer-events: none;
}

.collection-card:hover .collection-hover-layer {
    opacity: 0.15;
}

/* Parallax Section */
.parallax-section {
    position: relative;
    min-height: 60vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.parallax-bg {
    position: absolute;
    inset: -20%;
    z-index: var(--z-below);
}

.parallax-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.parallax-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
}

.parallax-content {
    position: relative;
    z-index: var(--z-above);
    text-align: center;
    padding: var(--space-16) var(--space-6);
}

.brand-statement {
    max-width: var(--container-md);
    margin: 0 auto;
}

.brand-tagline {
    font-family: var(--font-display);
    font-size: var(--text-3xl);
    font-style: italic;
    line-height: var(--leading-relaxed);
    color: var(--skyyrose-white);
    margin-bottom: var(--space-6);
}

@media (max-width: 768px) {
    .brand-tagline {
        font-size: var(--text-2xl);
    }
}

.brand-attribution {
    margin-top: var(--space-4);
}

.brand-name {
    font-size: var(--text-sm);
    font-style: normal;
    letter-spacing: var(--tracking-luxury);
    text-transform: uppercase;
    color: var(--skyyrose-rose-gold);
}

.parallax-decoration {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.decoration-line {
    position: absolute;
    width: 1px;
    height: 100px;
    background: linear-gradient(to bottom, transparent, var(--skyyrose-rose-gold), transparent);
}

.decoration-line.left {
    left: 10%;
    top: 20%;
}

.decoration-line.right {
    right: 10%;
    bottom: 20%;
}

/* Featured Products */
.featured-products-section {
    background: var(--skyyrose-charcoal);
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-6);
}

@media (max-width: 1024px) {
    .products-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 640px) {
    .products-grid {
        grid-template-columns: 1fr;
    }
}

.product-card {
    position: relative;
    border-radius: var(--radius-xl);
    overflow: hidden;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.product-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
}

.product-image-wrapper {
    position: relative;
    aspect-ratio: 4 / 5;
    overflow: hidden;
}

.product-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: opacity var(--transition-base);
}

.product-image-hover {
    position: absolute;
    inset: 0;
    opacity: 0;
}

.product-card:hover .product-image-primary {
    opacity: 0;
}

.product-card:hover .product-image-hover {
    opacity: 1;
}

.product-badges {
    position: absolute;
    top: var(--space-3);
    left: var(--space-3);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-1) var(--space-2);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: var(--tracking-wide);
    border-radius: var(--radius-sm);
}

.badge-sale {
    background: var(--skyyrose-crimson);
    color: var(--skyyrose-white);
}

.badge-3d {
    background: var(--skyyrose-rose-gold);
    color: var(--skyyrose-black);
}

.badge-sold-out {
    background: rgba(255, 255, 255, 0.1);
    color: var(--skyyrose-white);
}

.product-actions {
    position: absolute;
    bottom: var(--space-4);
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    display: flex;
    gap: var(--space-2);
    opacity: 0;
    transition: opacity var(--transition-base), transform var(--transition-base);
}

.product-card:hover .product-actions {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.action-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    background: var(--skyyrose-white);
    color: var(--skyyrose-black);
    font-size: var(--text-xs);
    font-weight: 500;
    border-radius: var(--radius-full);
    transition: background var(--transition-fast), color var(--transition-fast);
}

.action-btn:hover {
    background: var(--skyyrose-primary);
    color: var(--skyyrose-white);
}

.wishlist-btn {
    padding: var(--space-2);
}

.product-info {
    padding: var(--space-4);
}

.product-name {
    font-size: var(--text-base);
    font-weight: 500;
    margin-bottom: var(--space-1);
}

.product-name a {
    color: var(--skyyrose-white);
    transition: color var(--transition-fast);
}

.product-name a:hover {
    color: var(--skyyrose-rose-gold);
}

.product-category {
    font-size: var(--text-xs);
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: var(--space-2);
}

.product-category a {
    color: inherit;
}

.product-price {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--skyyrose-rose-gold);
}

.product-price del {
    color: rgba(255, 255, 255, 0.4);
    font-weight: 400;
    margin-right: var(--space-2);
}

/* Instagram Section */
.instagram-section {
    background: var(--skyyrose-black);
}

.instagram-feed {
    margin-bottom: var(--space-8);
}

.instagram-placeholder-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: var(--space-4);
}

@media (max-width: 1024px) {
    .instagram-placeholder-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 640px) {
    .instagram-placeholder-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.instagram-placeholder-item {
    position: relative;
    aspect-ratio: 1;
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
}

.placeholder-image {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        135deg,
        rgba(183, 110, 121, 0.1) 0%,
        rgba(201, 169, 98, 0.1) 100%
    );
}

.placeholder-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.3);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-4) var(--space-8);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 500;
    letter-spacing: var(--tracking-wide);
    text-transform: uppercase;
    border-radius: var(--radius-full);
    transition: all var(--transition-base);
    cursor: pointer;
}

.btn-primary {
    background: var(--skyyrose-primary);
    color: var(--skyyrose-white);
    border: 2px solid var(--skyyrose-primary);
}

.btn-primary:hover {
    background: transparent;
    color: var(--skyyrose-white);
}

.btn-outline {
    background: transparent;
    color: var(--skyyrose-white);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-outline:hover {
    background: var(--skyyrose-white);
    color: var(--skyyrose-black);
    border-color: var(--skyyrose-white);
}

.btn-icon {
    transition: transform var(--transition-fast);
}

.btn:hover .btn-icon {
    transform: translateX(4px);
}

/* GSAP Animation Classes */
.gsap-fade-up {
    opacity: 0;
    transform: translateY(40px);
}

.gsap-scale-in {
    opacity: 0;
    transform: scale(0.95);
}

.gsap-stagger > * {
    opacity: 0;
    transform: translateY(30px);
}

/* Parallax Layer Marker */
.parallax-layer {
    will-change: transform;
}

/* View Transitions */
@supports (view-transition-name: none) {
    ::view-transition-old(main-content),
    ::view-transition-new(main-content) {
        animation-duration: 0.5s;
    }

    ::view-transition-old(hero-section),
    ::view-transition-new(hero-section) {
        animation-duration: 0.6s;
    }
}

/* Magnetic Button Effect Indicator */
.magnetic-btn {
    position: relative;
    will-change: transform;
}

/* Glass Card Styles */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
}
</style>

<?php
get_footer();
