<?php
/**
 * Template Name: About Page
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();

// Check if Elementor is active and page is built with Elementor
$is_elementor = false;
if (did_action('elementor/loaded')) {
    $document = \Elementor\Plugin::$instance->documents->get(get_the_ID());
    $is_elementor = $document && $document->is_built_with_elementor();
}

if ($is_elementor) {
    // Let Elementor render the content
    while (have_posts()) : the_post();
        the_content();
    endwhile;
} else {
    // Use theme template as fallback
?>

<section class="about-hero">
    <div class="about-hero-content">
        <span class="section-label">Our Story</span>
        <h1 class="about-title">Where Love<br>Meets Luxury</h1>
        <p class="about-subtitle">Oakland-born streetwear with a soul, crafted for those who dare to feel deeply and dress boldly.</p>
    </div>
    <div class="about-hero-visual">
        <div class="founder-image">
            <?php
            $founder_image = get_post_meta(get_the_ID(), '_skyyrose_founder_image', true);
            if ($founder_image) {
                echo wp_get_attachment_image($founder_image, 'skyyrose-hero', false, ['class' => 'founder-img']);
            } else {
                echo '<div class="founder-placeholder">◆</div>';
            }
            ?>
        </div>
    </div>
</section>

<section class="about-story">
    <div class="container">
        <div class="story-grid">
            <div class="story-content">
                <h2>Born in Oakland</h2>
                <p>SkyyRose emerged from the vibrant streets of Oakland, where authenticity isn't just valued—it's essential. Founded with a vision to bridge the gap between street culture and luxury fashion, we create pieces that tell stories.</p>
                <p>The name "Love Hurts" carries deep meaning—it's our founder's family name, Hurts, woven into the fabric of every piece. This personal connection infuses each collection with genuine emotion and uncompromising quality.</p>
            </div>
            <div class="story-stats">
                <div class="stat-item">
                    <span class="stat-number">3</span>
                    <span class="stat-label">Collections</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">100+</span>
                    <span class="stat-label">Products</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">Oakland</span>
                    <span class="stat-label">Headquarters</span>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="about-values">
    <div class="container">
        <div class="section-header">
            <span class="section-label">Our Values</span>
            <h2 class="section-title">What We Stand For</h2>
        </div>
        <div class="values-grid">
            <div class="value-card">
                <div class="value-icon">✦</div>
                <h3>Authenticity</h3>
                <p>Every piece reflects genuine expression and real emotions. We don't follow trends—we create meaning.</p>
            </div>
            <div class="value-card">
                <div class="value-icon">◆</div>
                <h3>Quality</h3>
                <p>Premium materials, meticulous craftsmanship, and attention to detail that stands the test of time.</p>
            </div>
            <div class="value-card">
                <div class="value-icon">♡</div>
                <h3>Community</h3>
                <p>Built for those who wear their heart on their sleeve. Fashion as connection, not exclusion.</p>
            </div>
            <div class="value-card">
                <div class="value-icon">★</div>
                <h3>Innovation</h3>
                <p>Pushing boundaries in design and technology, from 3D visualization to sustainable practices.</p>
            </div>
        </div>
    </div>
</section>

<section class="about-collections">
    <div class="container">
        <div class="section-header">
            <span class="section-label">The Collections</span>
            <h2 class="section-title">Three Stories, One Vision</h2>
        </div>
        <div class="collections-showcase">
            <?php
            $collections = skyyrose_get_collections();
            foreach ($collections as $slug => $collection) :
            ?>
            <div class="collection-showcase-item" style="--collection-color: <?php echo esc_attr($collection['color']); ?>">
                <div class="collection-showcase-visual">
                    <span class="collection-icon">◆</span>
                </div>
                <div class="collection-showcase-content">
                    <h3><?php echo esc_html($collection['name']); ?></h3>
                    <p><?php echo esc_html($collection['tagline']); ?></p>
                    <a href="<?php echo esc_url(home_url('/product-category/' . $slug)); ?>" class="btn btn-outline">Explore</a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="about-cta">
    <div class="container">
        <h2>Join the Family</h2>
        <p>Be part of something real. Where every piece has a story, and every customer becomes family.</p>
        <a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn btn-primary">Shop Now</a>
    </div>
</section>

<?php
} // End else (non-Elementor fallback)

get_footer();
?>
