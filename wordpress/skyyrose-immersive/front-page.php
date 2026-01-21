<?php
/**
 * Template Name: Homepage
 *
 * SkyyRose Homepage with immersive 3D hero
 * Morphing geometry + particles + collection previews
 *
 * @package SkyyRose_Immersive
 */

get_header();

// Enqueue hero scene scripts
wp_enqueue_script('threejs');
wp_enqueue_script('threejs-orbit-controls');
wp_enqueue_script('skyyrose-hero-scene');
?>

<main id="main" class="site-main skyyrose-homepage">

    <!-- 3D Hero Section -->
    <section class="hero-3d-section">
        <canvas id="hero-canvas" class="hero-canvas"></canvas>

        <!-- Hero Content Overlay -->
        <div class="hero-content">
            <div class="hero-content-inner">
                <span class="hero-label">Where Love Meets Luxury</span>
                <h1 class="hero-title">SKYYROSE</h1>
                <p class="hero-tagline">Premium streetwear born in Oakland</p>
                <div class="hero-cta-group">
                    <a href="<?php echo home_url('/collections/'); ?>" class="hero-cta primary">Shop Collections</a>
                    <a href="<?php echo home_url('/preorder/'); ?>" class="hero-cta secondary">Pre-Order Experience</a>
                </div>
            </div>
        </div>

        <!-- Scroll Indicator -->
        <div class="hero-scroll-indicator">
            <span class="scroll-text">Scroll to Explore</span>
            <div class="scroll-arrow">↓</div>
        </div>

        <!-- Collection Navigation -->
        <nav class="hero-collection-nav">
            <a href="#collection-blackrose" class="collection-nav-item" data-collection="blackrose">
                <span class="nav-rose">🥀</span>
                <span class="nav-label">Black Rose</span>
            </a>
            <a href="#collection-lovehurts" class="collection-nav-item" data-collection="lovehurts">
                <span class="nav-rose">💔</span>
                <span class="nav-label">Love Hurts</span>
            </a>
            <a href="#collection-signature" class="collection-nav-item" data-collection="signature">
                <span class="nav-rose">🌹</span>
                <span class="nav-label">Signature</span>
            </a>
        </nav>
    </section>

    <!-- Collections Preview -->
    <section class="collections-preview">
        <div class="section-header">
            <span class="section-label">Our Collections</span>
            <h2 class="section-title">Choose Your Journey</h2>
        </div>

        <div class="collections-grid">
            <!-- Black Rose -->
            <article id="collection-blackrose" class="collection-card collection-blackrose">
                <div class="collection-card-bg"></div>
                <div class="collection-card-content">
                    <span class="collection-emoji">🥀</span>
                    <h3 class="collection-name">BLACK ROSE</h3>
                    <p class="collection-tagline">Beauty in Darkness</p>
                    <p class="collection-description">
                        Mysterious elegance meets urban sophistication. Dark florals bloom in the shadows.
                    </p>
                    <a href="<?php echo home_url('/collections/black-rose/'); ?>" class="collection-link">
                        Explore Collection →
                    </a>
                </div>
            </article>

            <!-- Love Hurts -->
            <article id="collection-lovehurts" class="collection-card collection-lovehurts">
                <div class="collection-card-bg"></div>
                <div class="collection-card-content">
                    <span class="collection-emoji">💔</span>
                    <h3 class="collection-name">LOVE HURTS</h3>
                    <p class="collection-tagline">Passion & Pain</p>
                    <p class="collection-description">
                        Bold statements for fearless hearts. When love becomes art, pain transforms into power.
                    </p>
                    <a href="<?php echo home_url('/collections/love-hurts/'); ?>" class="collection-link">
                        Explore Collection →
                    </a>
                </div>
            </article>

            <!-- Signature -->
            <article id="collection-signature" class="collection-card collection-signature">
                <div class="collection-card-bg"></div>
                <div class="collection-card-content">
                    <span class="collection-emoji">🌹</span>
                    <h3 class="collection-name">SIGNATURE</h3>
                    <p class="collection-tagline">The Foundation</p>
                    <p class="collection-description">
                        Timeless essentials built to last. Premium craftsmanship meets everyday luxury.
                    </p>
                    <a href="<?php echo home_url('/collections/signature/'); ?>" class="collection-link">
                        Explore Collection →
                    </a>
                </div>
            </article>
        </div>
    </section>

    <!-- Featured Products -->
    <section class="featured-products">
        <div class="section-header">
            <span class="section-label">New Arrivals</span>
            <h2 class="section-title">Just Dropped</h2>
        </div>

        <div class="products-carousel">
            <?php
            // Query featured/new products
            $args = array(
                'post_type' => 'product',
                'posts_per_page' => 8,
                'meta_query' => array(
                    array(
                        'key' => '_featured',
                        'value' => 'yes',
                    ),
                ),
            );

            $featured = new WP_Query($args);

            // Fallback to recent products if no featured
            if (!$featured->have_posts()) {
                $args = array(
                    'post_type' => 'product',
                    'posts_per_page' => 8,
                    'orderby' => 'date',
                    'order' => 'DESC',
                );
                $featured = new WP_Query($args);
            }

            if ($featured->have_posts()) :
                while ($featured->have_posts()) : $featured->the_post();
                    global $product;
                    ?>
                    <div class="product-card">
                        <a href="<?php the_permalink(); ?>" class="product-card-link">
                            <div class="product-card-image">
                                <?php if (has_post_thumbnail()) : ?>
                                    <?php the_post_thumbnail('woocommerce_thumbnail'); ?>
                                <?php else : ?>
                                    <div class="product-placeholder">
                                        <span>🌹</span>
                                    </div>
                                <?php endif; ?>

                                <?php if ($product && $product->is_on_sale()) : ?>
                                    <span class="product-badge sale">Sale</span>
                                <?php endif; ?>
                            </div>
                            <div class="product-card-info">
                                <h4 class="product-title"><?php the_title(); ?></h4>
                                <p class="product-price"><?php echo $product ? $product->get_price_html() : ''; ?></p>
                            </div>
                        </a>
                    </div>
                    <?php
                endwhile;
                wp_reset_postdata();
            else :
                ?>
                <div class="no-products">
                    <p>New drops coming soon. Stay tuned.</p>
                </div>
                <?php
            endif;
            ?>
        </div>

        <div class="section-cta">
            <a href="<?php echo get_permalink(wc_get_page_id('shop')); ?>" class="btn-shop-all">
                Shop All Products
            </a>
        </div>
    </section>

    <!-- Brand Story Teaser -->
    <section class="brand-story-teaser">
        <div class="story-content">
            <span class="section-label">Oakland Born</span>
            <h2 class="story-title">"Where Love Meets Luxury"</h2>
            <p class="story-text">
                SkyyRose was born from the streets of Oakland—a brand that transforms
                raw emotion into wearable art. Every piece tells a story of passion,
                resilience, and unapologetic self-expression.
            </p>
            <a href="<?php echo home_url('/about/'); ?>" class="story-link">Our Story →</a>
        </div>
        <div class="story-visual">
            <div class="story-rose-grid">
                <span class="story-rose">🥀</span>
                <span class="story-rose">💔</span>
                <span class="story-rose">🌹</span>
            </div>
        </div>
    </section>

    <!-- Pre-Order CTA -->
    <section class="preorder-cta">
        <div class="preorder-content">
            <span class="section-label">Immersive Experience</span>
            <h2 class="preorder-title">Shop in 3D</h2>
            <p class="preorder-text">
                Step into our virtual showroom. Explore all three collections
                in a stunning 3D environment.
            </p>
            <a href="<?php echo home_url('/preorder/'); ?>" class="btn-preorder">
                Enter the Experience →
            </a>
        </div>
    </section>

</main>

<style>
/* Homepage Hero */
.hero-3d-section {
    position: relative;
    height: 100vh;
    min-height: 700px;
    overflow: hidden;
    background: #0a0a0a;
}

.hero-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

.hero-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 10;
    text-align: center;
    color: #fff;
    pointer-events: none;
}

.hero-content-inner {
    pointer-events: auto;
}

.hero-label {
    display: block;
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1rem;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3rem, 10vw, 7rem);
    font-weight: 400;
    letter-spacing: 0.15em;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 60px rgba(183, 110, 121, 0.5);
}

.hero-tagline {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 2.5rem;
    letter-spacing: 0.1em;
}

.hero-cta-group {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

.hero-cta {
    display: inline-block;
    padding: 1rem 2rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    text-decoration: none;
    transition: all 0.3s ease;
}

.hero-cta.primary {
    background: #B76E79;
    color: #fff;
    border: 1px solid #B76E79;
}

.hero-cta.primary:hover {
    background: transparent;
    color: #B76E79;
}

.hero-cta.secondary {
    background: transparent;
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.hero-cta.secondary:hover {
    border-color: #fff;
}

/* Scroll Indicator */
.hero-scroll-indicator {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
}

.scroll-text {
    display: block;
    font-size: 0.625rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.scroll-arrow {
    animation: bounce 2s infinite;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(8px); }
    60% { transform: translateY(4px); }
}

/* Collection Navigation */
.hero-collection-nav {
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.collection-nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
}

.collection-nav-item:hover {
    color: #fff;
    transform: scale(1.1);
}

.nav-rose {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
}

.nav-label {
    font-size: 0.625rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Section Styles */
.section-header {
    text-align: center;
    margin-bottom: 4rem;
}

.section-label {
    display: block;
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #B76E79;
    margin-bottom: 1rem;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 5vw, 3rem);
    color: #fff;
}

/* Collections Preview */
.collections-preview {
    padding: 8rem 2rem;
    background: linear-gradient(180deg, #0a0a0a, #111);
}

.collections-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    max-width: 1400px;
    margin: 0 auto;
}

.collection-card {
    position: relative;
    min-height: 500px;
    overflow: hidden;
    border-radius: 2px;
}

.collection-card-bg {
    position: absolute;
    inset: 0;
    transition: transform 0.6s ease;
}

.collection-blackrose .collection-card-bg {
    background: linear-gradient(135deg, #1a0505 0%, #2a0a0a 100%);
}

.collection-lovehurts .collection-card-bg {
    background: linear-gradient(135deg, #1a0515 0%, #200a1a 100%);
}

.collection-signature .collection-card-bg {
    background: linear-gradient(135deg, #1a1810 0%, #201a10 100%);
}

.collection-card:hover .collection-card-bg {
    transform: scale(1.05);
}

.collection-card-content {
    position: relative;
    z-index: 2;
    padding: 3rem 2rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
}

.collection-emoji {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.collection-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.75rem;
    color: #fff;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

.collection-tagline {
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.collection-description {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.7;
    margin-bottom: 1.5rem;
}

.collection-link {
    color: #B76E79;
    text-decoration: none;
    font-size: 0.875rem;
    letter-spacing: 0.1em;
    transition: color 0.3s ease;
}

.collection-link:hover {
    color: #fff;
}

/* Featured Products */
.featured-products {
    padding: 8rem 2rem;
    background: #0a0a0a;
}

.products-carousel {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
    max-width: 1400px;
    margin: 0 auto 3rem;
}

.product-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;
}

.product-card:hover {
    border-color: rgba(183, 110, 121, 0.3);
    transform: translateY(-4px);
}

.product-card-link {
    text-decoration: none;
    display: block;
}

.product-card-image {
    position: relative;
    aspect-ratio: 1;
    overflow: hidden;
    background: #111;
}

.product-card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.product-card:hover .product-card-image img {
    transform: scale(1.05);
}

.product-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    font-size: 3rem;
    opacity: 0.3;
}

.product-badge {
    position: absolute;
    top: 1rem;
    right: 1rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.625rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.product-badge.sale {
    background: #B76E79;
    color: #fff;
}

.product-card-info {
    padding: 1.5rem;
}

.product-title {
    font-size: 0.875rem;
    color: #fff;
    margin-bottom: 0.5rem;
    font-weight: 400;
}

.product-price {
    color: #B76E79;
    font-size: 0.875rem;
}

.section-cta {
    text-align: center;
}

.btn-shop-all {
    display: inline-block;
    padding: 1rem 2.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    border: 1px solid rgba(183, 110, 121, 0.5);
    color: #B76E79;
    text-decoration: none;
    transition: all 0.3s ease;
}

.btn-shop-all:hover {
    background: #B76E79;
    color: #fff;
}

/* Brand Story Teaser */
.brand-story-teaser {
    padding: 8rem 2rem;
    background: linear-gradient(135deg, #0f0a0b 0%, #0a0a0a 100%);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    max-width: 1200px;
    margin: 0 auto;
    align-items: center;
}

.story-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    color: #fff;
    margin-bottom: 1.5rem;
    font-style: italic;
}

.story-text {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.9;
    margin-bottom: 2rem;
}

.story-link {
    color: #B76E79;
    text-decoration: none;
    font-size: 0.875rem;
    letter-spacing: 0.1em;
}

.story-rose-grid {
    display: flex;
    justify-content: center;
    gap: 2rem;
}

.story-rose {
    font-size: 4rem;
    opacity: 0.8;
    transition: all 0.3s ease;
}

.story-rose:hover {
    transform: scale(1.2);
    opacity: 1;
}

/* Pre-Order CTA */
.preorder-cta {
    padding: 8rem 2rem;
    background: linear-gradient(135deg, #B76E79 0%, #8B4D5C 100%);
    text-align: center;
}

.preorder-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 5vw, 3rem);
    color: #fff;
    margin-bottom: 1rem;
}

.preorder-text {
    color: rgba(255, 255, 255, 0.9);
    max-width: 500px;
    margin: 0 auto 2rem;
    line-height: 1.7;
}

.preorder-cta .section-label {
    color: rgba(255, 255, 255, 0.8);
}

.btn-preorder {
    display: inline-block;
    padding: 1rem 2.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    background: #fff;
    color: #B76E79;
    text-decoration: none;
    transition: all 0.3s ease;
}

.btn-preorder:hover {
    background: #0a0a0a;
    color: #fff;
}

/* Responsive */
@media (max-width: 1024px) {
    .collections-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }

    .collection-card {
        min-height: 350px;
    }

    .products-carousel {
        grid-template-columns: repeat(2, 1fr);
    }

    .brand-story-teaser {
        grid-template-columns: 1fr;
        text-align: center;
    }

    .hero-collection-nav {
        display: none;
    }
}

@media (max-width: 768px) {
    .hero-cta-group {
        flex-direction: column;
        align-items: center;
    }

    .hero-cta {
        width: 100%;
        max-width: 280px;
    }

    .products-carousel {
        grid-template-columns: 1fr;
    }
}
</style>

<script type="module">
import { initHeroScene } from '<?php echo SKYYROSE_IMMERSIVE_URI; ?>/assets/js/hero-scene.js';

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('hero-canvas');
    if (canvas) {
        const heroScene = initHeroScene(canvas, {
            particleCount: window.innerWidth < 768 ? 1500 : 5000,
            enableBloom: true,
            enableChromatic: true
        });

        // Collection nav hover effects
        document.querySelectorAll('.collection-nav-item').forEach(item => {
            item.addEventListener('mouseenter', () => {
                const collection = item.dataset.collection;
                if (heroScene && heroScene.setCollectionTheme) {
                    heroScene.setCollectionTheme(collection);
                }
            });
        });
    }

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
});
</script>

<?php
get_footer();
