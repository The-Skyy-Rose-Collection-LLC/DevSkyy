<?php
/**
 * Homepage Template
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();
?>

<!-- Hero Section -->
<section class="hero">
    <div class="hero-bg">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>
    <div class="hero-content">
        <span class="hero-badge">Oakland Luxury Streetwear</span>
        <h1 class="hero-title">
            <span>Where Love</span>
            <span>Meets Luxury</span>
        </h1>
        <p class="hero-subtitle">
            Three distinct collections, one unified vision. Born in Oakland, crafted with passion,
            designed for those who wear their heart on their sleeve.
        </p>
        <div class="hero-cta">
            <a href="<?php echo esc_url(home_url('/shop')); ?>" class="btn btn-primary">Shop Now</a>
            <a href="#collections" class="btn btn-outline">Explore Collections</a>
        </div>
    </div>
    <div class="scroll-indicator">
        <span>Scroll</span>
    </div>
</section>

<!-- Collections Section -->
<section class="collections" id="collections">
    <div class="container">
        <div class="section-header">
            <span class="section-label">The Collections</span>
            <h2 class="section-title">Three Stories, One Vision</h2>
            <p class="section-subtitle">
                Each collection represents a chapter in our story—from dark elegance to emotional depth to timeless luxury.
            </p>
        </div>
        <div class="collections-grid">
            <?php skyyrose_collection_cards(); ?>
        </div>
    </div>
</section>

<!-- Featured Products -->
<section class="featured">
    <div class="container">
        <div class="section-header">
            <span class="section-label">Featured</span>
            <h2 class="section-title">New Arrivals</h2>
            <p class="section-subtitle">
                The latest additions to our collections, each piece crafted with intention.
            </p>
        </div>
        <div class="products-grid">
            <?php skyyrose_featured_products(4); ?>
        </div>
        <div class="section-cta">
            <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn-outline">View All Products</a>
        </div>
    </div>
</section>

<!-- Brand Story -->
<section class="brand-story">
    <div class="brand-story-bg"></div>
    <div class="container">
        <div class="brand-story-content">
            <div class="brand-story-text">
                <span class="section-label">Our Story</span>
                <h2>Born in Oakland,<br>Crafted with Love</h2>
                <p>
                    SkyyRose emerged from the vibrant streets of Oakland, where authenticity isn't just valued—it's essential.
                    Founded with a vision to bridge the gap between street culture and luxury fashion, we create pieces that
                    tell stories.
                </p>
                <p>
                    The name "Love Hurts" carries deep meaning—it's our founder's family name, Hurts, woven into the
                    fabric of every piece. This personal connection infuses each collection with genuine emotion and
                    uncompromising quality.
                </p>
                <a href="<?php echo esc_url(home_url('/about')); ?>" class="btn btn-outline">Learn More</a>
            </div>
            <div class="brand-story-visual">
                <div class="brand-story-quote">"Where Love Meets Luxury"</div>
            </div>
        </div>
    </div>
</section>

<?php get_footer(); ?>
