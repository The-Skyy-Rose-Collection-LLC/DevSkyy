<?php
/**
 * Template Name: Signature Collection (Immersive)
 *
 * Immersive 3D experience for the Signature Collection
 * Rose Garden with Fountain - Crimson, Gold & Ivory
 *
 * @package SkyyRose_Immersive
 */

get_header();

// Enqueue collection scripts
wp_enqueue_script('threejs');
wp_enqueue_script('threejs-orbit-controls');
wp_enqueue_script('skyyrose-experience-base');
wp_enqueue_script('skyyrose-signature-experience');
wp_enqueue_script('skyyrose-3d-init');
?>

<main id="main" class="site-main collection-main collection-signature">

    <!-- Collection Hero -->
    <section class="collection-hero collection-hero-signature">
        <div class="collection-hero-content">
            <img src="<?php echo SKYYROSE_IMMERSIVE_URI; ?>/assets/images/logos/signature-logo.png"
                 alt="Signature Collection"
                 class="collection-hero-logo">
            <h1 class="collection-hero-title">SIGNATURE</h1>
            <p class="collection-hero-tagline">The Foundation. Built to Last.</p>
            <p class="collection-hero-description">
                Premium essentials for everyday luxury. Each piece crafted with intention.
            </p>
            <div class="collection-hero-buttons">
                <a href="#experience" class="collection-hero-cta">Enter 3D Experience</a>
                <a href="#products" class="collection-hero-cta-secondary">Shop Collection →</a>
            </div>
        </div>
        <div class="collection-hero-scroll">↓ Scroll to Explore</div>
    </section>

    <!-- 3D Experience Section -->
    <section id="experience" class="collection-3d-section">
        <div class="skyyrose-3d-container skyyrose-3d-signature" id="signature-experience">

            <!-- Loading Screen -->
            <div class="skyyrose-3d-loading">
                <img src="<?php echo SKYYROSE_IMMERSIVE_URI; ?>/assets/images/logos/signature-logo.png"
                     alt="Loading" class="loading-logo">
                <div class="loading-text">Entering the Rose Garden...</div>
                <div class="loading-bar">
                    <div class="loading-progress"></div>
                </div>
            </div>

            <!-- Navigation Instructions -->
            <div class="skyyrose-3d-instructions">
                <span class="instruction-item">
                    <span class="instruction-icon">🖱️</span>
                    Drag to rotate
                </span>
                <span class="instruction-item">
                    <span class="instruction-icon">🔍</span>
                    Scroll to zoom
                </span>
                <span class="instruction-item">
                    <span class="instruction-icon">👆</span>
                    Click products to view
                </span>
            </div>

            <!-- Fullscreen Button -->
            <button class="skyyrose-fullscreen-btn" title="Toggle Fullscreen">
                <svg viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                </svg>
            </button>
        </div>
    </section>

    <!-- Products Grid -->
    <section id="products" class="collection-products">
        <div class="collection-products-header">
            <h2 class="collection-products-title">Shop the Collection</h2>
            <p class="collection-products-subtitle">Premium essentials for everyday luxury</p>
        </div>

        <div class="collection-products-grid">
            <?php
            // Query Signature Collection products
            $args = array(
                'post_type' => 'product',
                'posts_per_page' => 12,
                'tax_query' => array(
                    array(
                        'taxonomy' => 'product_cat',
                        'field' => 'slug',
                        'terms' => 'signature',
                    ),
                ),
            );

            $products = new WP_Query($args);

            if ($products->have_posts()) :
                while ($products->have_posts()) : $products->the_post();
                    global $product;
                    ?>
                    <div class="skyyrose-product-card">
                        <a href="<?php the_permalink(); ?>" class="product-card-link">
                            <div class="skyyrose-product-card-image">
                                <?php if (has_post_thumbnail()) : ?>
                                    <?php the_post_thumbnail('woocommerce_thumbnail'); ?>
                                <?php endif; ?>

                                <?php if ($product->is_featured()) : ?>
                                    <span class="skyyrose-product-card-badge new">Bestseller</span>
                                <?php endif; ?>
                            </div>
                            <h3 class="skyyrose-product-card-title"><?php the_title(); ?></h3>
                            <p class="skyyrose-product-card-price"><?php echo $product->get_price_html(); ?></p>
                        </a>
                    </div>
                    <?php
                endwhile;
                wp_reset_postdata();
            else :
                ?>
                <div class="collection-no-products">
                    <p>Products coming soon. Check back for our latest drops.</p>
                </div>
                <?php
            endif;
            ?>
        </div>

        <?php if ($products->found_posts > 12) : ?>
        <div class="collection-products-more">
            <a href="<?php echo get_term_link('signature', 'product_cat'); ?>" class="btn-view-all">
                View All Products
            </a>
        </div>
        <?php endif; ?>
    </section>

    <!-- Collection Story -->
    <section class="collection-story">
        <div class="collection-story-content">
            <span class="collection-story-label">The Vision</span>
            <h2 class="collection-story-title">"Foundation of Luxury"</h2>
            <p class="collection-story-text">
                The Signature Collection represents the core of SkyyRose—timeless pieces
                designed to transcend seasons and trends. Crimson, gold, and ivory roses
                symbolize the balance of passion, prosperity, and purity that defines our brand.
            </p>
            <a href="<?php echo home_url('/our-story/'); ?>" class="collection-story-link">
                Our Story →
            </a>
        </div>
    </section>

</main>

<style>
/* Collection-specific overrides */
.collection-hero-signature {
    background: linear-gradient(135deg, #1a1a18 0%, #2a2820 50%, #1a1a18 100%);
    min-height: 60vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 6rem 2rem;
    color: #fff;
    position: relative;
}

.collection-hero-signature .collection-hero-title {
    color: #C9A962;
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    letter-spacing: 0.2em;
    margin-bottom: 0.5rem;
}

.collection-hero-signature .collection-hero-tagline {
    color: rgba(255, 255, 255, 0.8);
    font-size: 1rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

.collection-hero-logo {
    max-width: 200px;
    margin-bottom: 2rem;
}

.collection-3d-section {
    position: relative;
}

.collection-3d-section .skyyrose-3d-container {
    height: 100vh;
}

.collection-products {
    padding: 6rem 2rem;
    background: linear-gradient(180deg, #1a1a18, #0f0f0e);
}

.collection-products-header {
    text-align: center;
    margin-bottom: 4rem;
}

.collection-products-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    color: #C9A962;
    margin-bottom: 0.5rem;
}

.collection-products-subtitle {
    color: rgba(255, 255, 255, 0.6);
}

.collection-products-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
    max-width: 1400px;
    margin: 0 auto;
}

@media (max-width: 1200px) {
    .collection-products-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .collection-products-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }
}

.collection-products .skyyrose-product-card-title {
    color: #fff;
}

.collection-products .skyyrose-product-card-price {
    color: #C9A962;
}

.collection-products-more {
    text-align: center;
    margin-top: 3rem;
}

.btn-view-all {
    display: inline-block;
    padding: 1rem 2.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    border: 1px solid rgba(201, 169, 98, 0.5);
    color: #C9A962;
    text-decoration: none;
    transition: all 0.3s ease;
}

.btn-view-all:hover {
    background: #C9A962;
    color: #0a0a0a;
}

.collection-story {
    padding: 8rem 2rem;
    background: #0a0a0a;
    text-align: center;
}

.collection-story-content {
    max-width: 600px;
    margin: 0 auto;
}

.collection-story-label {
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #C9A962;
    margin-bottom: 1rem;
    display: block;
}

.collection-story-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    color: #fff;
    margin-bottom: 1.5rem;
}

.collection-story-text {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.9;
    margin-bottom: 2rem;
}

.collection-story-link {
    font-size: 0.875rem;
    letter-spacing: 0.1em;
    color: #C9A962;
    text-decoration: none;
    transition: opacity 0.3s ease;
}

.collection-story-link:hover {
    opacity: 0.7;
}
</style>

<script>
// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Fullscreen handler
document.querySelector('.skyyrose-fullscreen-btn')?.addEventListener('click', function() {
    const container = document.getElementById('signature-experience');
    if (!document.fullscreenElement) {
        container.requestFullscreen().catch(err => console.log('Fullscreen error:', err));
    } else {
        document.exitFullscreen();
    }
});
</script>

<?php
get_footer();
