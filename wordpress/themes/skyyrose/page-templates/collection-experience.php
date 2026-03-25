<?php
/**
 * Template Name: Collection Experience
 * Template Post Type: page
 *
 * Immersive 3D collection experience template with fullscreen viewer,
 * scroll-based camera controls, and product hotspots.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

// Get collection slug from custom field or query param
$collection_slug = get_post_meta(get_the_ID(), '_skyyrose_collection_slug', true);
if (empty($collection_slug) && isset($_GET['collection'])) {
    $collection_slug = sanitize_text_field($_GET['collection']);
}
$collection_slug = $collection_slug ?: 'signature';

// Get collection data
$collection = skyyrose_get_collection($collection_slug);

// Get 3D model URL from custom field
$model_url = get_post_meta(get_the_ID(), '_skyyrose_collection_model', true);

// Get hotspots data
$hotspots_json = get_post_meta(get_the_ID(), '_skyyrose_hotspots', true);
$hotspots = $hotspots_json ? json_decode($hotspots_json, true) : [];

// Get featured products for this collection
$featured_products = new WP_Query([
    'post_type'      => 'product',
    'posts_per_page' => 6,
    'meta_query'     => [
        [
            'key'     => '_skyyrose_collection',
            'value'   => $collection_slug,
            'compare' => '=',
        ],
    ],
    'orderby'        => 'menu_order date',
    'order'          => 'ASC',
]);

// Generate CSS custom properties for collection theming
$collection_styles = sprintf(
    '--collection-primary: %s; --collection-secondary: %s; --collection-accent: %s;',
    esc_attr($collection['colors']['primary']),
    esc_attr($collection['colors']['secondary']),
    esc_attr($collection['colors']['accent'])
);

get_header();
?>

<style>
    .collection-experience-page {
        <?php echo $collection_styles; ?>
    }
</style>

<main id="main-content" class="collection-experience-page" role="main" data-collection="<?php echo esc_attr($collection_slug); ?>">

    <!-- Hero Section -->
    <section class="collection-hero" id="collection-hero">
        <div class="hero-background">
            <div class="hero-gradient"></div>
            <?php if (has_post_thumbnail()) : ?>
                <div class="hero-image">
                    <?php the_post_thumbnail('skyyrose-hero', [
                        'class' => 'hero-bg-image',
                        'loading' => 'eager',
                    ]); ?>
                </div>
            <?php endif; ?>
        </div>

        <div class="hero-content container">
            <div class="hero-text" data-gsap="fade-up">
                <span class="collection-label"><?php esc_html_e('The Collection', 'skyyrose'); ?></span>
                <h1 class="collection-title"><?php echo esc_html($collection['name']); ?></h1>
                <p class="collection-tagline"><?php echo esc_html($collection['tagline']); ?></p>
            </div>

            <div class="hero-scroll-indicator" data-gsap="fade-up" data-gsap-delay="0.5">
                <span><?php esc_html_e('Scroll to Explore', 'skyyrose'); ?></span>
                <div class="scroll-arrow">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M12 5V19M12 19L5 12M12 19L19 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div>
        </div>
    </section>

    <!-- Immersive 3D Experience Section -->
    <section class="collection-3d-experience" id="collection-viewer">
        <div class="experience-container">
            <?php if ($model_url) : ?>
                <div class="model-viewer-wrapper" data-gsap="scale-in">
                    <model-viewer
                        id="collection-model-viewer"
                        src="<?php echo esc_url($model_url); ?>"
                        alt="<?php echo esc_attr($collection['name']); ?> Collection 3D Experience"
                        ar
                        ar-modes="webxr scene-viewer quick-look"
                        camera-controls
                        touch-action="pan-y"
                        auto-rotate
                        auto-rotate-delay="2000"
                        rotation-per-second="15deg"
                        shadow-intensity="1"
                        exposure="0.8"
                        environment-image="neutral"
                        skybox-image=""
                        interpolation-decay="200"
                        min-camera-orbit="auto auto 2m"
                        max-camera-orbit="auto auto 10m"
                        camera-orbit="0deg 75deg 5m"
                        field-of-view="30deg"
                        class="skyyrose-collection-viewer"
                        data-scroll-camera="true"
                    >
                        <!-- Loading State -->
                        <div class="model-loading" slot="poster">
                            <div class="loading-spinner"></div>
                            <p><?php esc_html_e('Loading Experience...', 'skyyrose'); ?></p>
                        </div>

                        <!-- AR Button -->
                        <button slot="ar-button" class="ar-button glass-button">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M12 18V6M6 12H18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            <span><?php esc_html_e('View in AR', 'skyyrose'); ?></span>
                        </button>

                        <!-- Product Hotspots -->
                        <?php if (!empty($hotspots)) : ?>
                            <?php foreach ($hotspots as $index => $hotspot) : ?>
                                <button
                                    class="hotspot"
                                    slot="hotspot-<?php echo esc_attr($index); ?>"
                                    data-position="<?php echo esc_attr($hotspot['position'] ?? '0m 0m 0m'); ?>"
                                    data-normal="<?php echo esc_attr($hotspot['normal'] ?? '0m 0m 1m'); ?>"
                                    data-visibility-attribute="visible"
                                    data-product-id="<?php echo esc_attr($hotspot['product_id'] ?? ''); ?>"
                                    aria-label="<?php echo esc_attr($hotspot['label'] ?? 'View Product'); ?>"
                                >
                                    <div class="hotspot-content glass-card">
                                        <span class="hotspot-label"><?php echo esc_html($hotspot['label'] ?? ''); ?></span>
                                        <?php if (!empty($hotspot['price'])) : ?>
                                            <span class="hotspot-price"><?php echo esc_html($hotspot['price']); ?></span>
                                        <?php endif; ?>
                                    </div>
                                </button>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </model-viewer>

                    <!-- Camera Control Indicators -->
                    <div class="camera-controls-hint glass-panel">
                        <div class="control-hint">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M10 6V14M6 10H14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            <span><?php esc_html_e('Drag to Rotate', 'skyyrose'); ?></span>
                        </div>
                        <div class="control-hint">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                <path d="M10 4V16M10 4L6 8M10 4L14 8M10 16L6 12M10 16L14 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span><?php esc_html_e('Scroll to Zoom', 'skyyrose'); ?></span>
                        </div>
                    </div>
                </div>
            <?php else : ?>
                <!-- Fallback when no 3D model -->
                <div class="experience-fallback">
                    <div class="fallback-gallery" data-gsap="stagger-fade">
                        <?php
                        // Get gallery images from post content or custom field
                        $gallery_ids = get_post_meta(get_the_ID(), '_skyyrose_collection_gallery', true);
                        if ($gallery_ids) :
                            $image_ids = explode(',', $gallery_ids);
                            foreach ($image_ids as $image_id) :
                                ?>
                                <div class="gallery-item">
                                    <?php echo wp_get_attachment_image($image_id, 'skyyrose-collection'); ?>
                                </div>
                            <?php endforeach;
                        endif;
                        ?>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Collection Description -->
            <div class="experience-description glass-panel" data-gsap="fade-up">
                <p><?php echo esc_html($collection['description']); ?></p>
            </div>
        </div>

        <!-- Scroll Progress Indicator -->
        <div class="scroll-progress" aria-hidden="true">
            <div class="progress-bar"></div>
        </div>
    </section>

    <!-- Product Hotspots Reveal Section -->
    <section class="collection-hotspots-section" id="product-hotspots">
        <div class="container">
            <header class="section-header" data-gsap="fade-up">
                <h2 class="section-title"><?php esc_html_e('Discover the Details', 'skyyrose'); ?></h2>
                <p class="section-subtitle"><?php esc_html_e('Tap on the highlighted areas to explore each piece', 'skyyrose'); ?></p>
            </header>

            <div class="hotspot-products-grid" data-gsap="stagger-fade">
                <?php if (!empty($hotspots)) : ?>
                    <?php foreach ($hotspots as $hotspot) : ?>
                        <?php if (!empty($hotspot['product_id'])) :
                            $product = wc_get_product($hotspot['product_id']);
                            if ($product) :
                                ?>
                                <article class="hotspot-product-card glass-card" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                                    <div class="product-image">
                                        <?php echo $product->get_image('skyyrose-product'); ?>
                                    </div>
                                    <div class="product-info">
                                        <h3 class="product-name"><?php echo esc_html($product->get_name()); ?></h3>
                                        <p class="product-price"><?php echo $product->get_price_html(); ?></p>
                                        <a href="<?php echo esc_url($product->get_permalink()); ?>" class="product-link magnetic-btn">
                                            <?php esc_html_e('View Details', 'skyyrose'); ?>
                                        </a>
                                    </div>
                                </article>
                            <?php endif;
                        endif; ?>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </section>

    <!-- Featured Products Grid Section -->
    <section class="collection-products" id="featured-products">
        <div class="container">
            <header class="section-header" data-gsap="fade-up">
                <h2 class="section-title"><?php echo esc_html($collection['name']); ?> <?php esc_html_e('Collection', 'skyyrose'); ?></h2>
                <p class="section-subtitle"><?php esc_html_e('Explore the complete collection', 'skyyrose'); ?></p>
            </header>

            <?php if ($featured_products->have_posts()) : ?>
                <div class="products-grid" data-gsap="stagger-fade">
                    <?php while ($featured_products->have_posts()) : $featured_products->the_post();
                        global $product;
                        if (!$product) continue;
                        ?>
                        <article class="product-card glass-card" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                            <div class="product-card-image">
                                <a href="<?php the_permalink(); ?>" aria-label="<?php echo esc_attr($product->get_name()); ?>">
                                    <?php echo $product->get_image('skyyrose-product'); ?>
                                </a>
                                <?php if ($product->is_on_sale()) : ?>
                                    <span class="sale-badge"><?php esc_html_e('Sale', 'skyyrose'); ?></span>
                                <?php endif; ?>

                                <?php
                                $has_3d = get_post_meta($product->get_id(), '_skyyrose_3d_model', true);
                                if ($has_3d) :
                                    ?>
                                    <span class="badge-3d" title="<?php esc_attr_e('3D View Available', 'skyyrose'); ?>">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5"/>
                                            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5"/>
                                            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5"/>
                                        </svg>
                                    </span>
                                <?php endif; ?>
                            </div>

                            <div class="product-card-content">
                                <h3 class="product-card-title">
                                    <a href="<?php the_permalink(); ?>"><?php echo esc_html($product->get_name()); ?></a>
                                </h3>
                                <p class="product-card-price"><?php echo $product->get_price_html(); ?></p>
                            </div>

                            <div class="product-card-actions">
                                <button class="quick-view-btn magnetic-btn" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                                    <span><?php esc_html_e('Quick View', 'skyyrose'); ?></span>
                                </button>
                            </div>
                        </article>
                    <?php endwhile; ?>
                </div>
                <?php wp_reset_postdata(); ?>
            <?php else : ?>
                <div class="no-products glass-card">
                    <p><?php esc_html_e('Products coming soon to this collection.', 'skyyrose'); ?></p>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <!-- Shop the Collection CTA Section -->
    <section class="collection-cta" id="shop-collection">
        <div class="cta-background">
            <div class="cta-gradient" style="background: linear-gradient(135deg, <?php echo esc_attr($collection['colors']['primary']); ?>20, <?php echo esc_attr($collection['colors']['secondary']); ?>40);"></div>
        </div>

        <div class="container">
            <div class="cta-content glass-panel" data-gsap="scale-in">
                <h2 class="cta-title"><?php esc_html_e('Ready to Elevate Your Style?', 'skyyrose'); ?></h2>
                <p class="cta-description"><?php echo esc_html($collection['tagline']); ?></p>

                <div class="cta-buttons">
                    <a href="<?php echo esc_url(get_permalink(wc_get_page_id('shop')) . '?collection=' . $collection_slug); ?>" class="btn btn-primary magnetic-btn">
                        <span><?php esc_html_e('Shop the Collection', 'skyyrose'); ?></span>
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                            <path d="M4 10H16M16 10L11 5M16 10L11 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </a>

                    <?php if ($model_url) : ?>
                        <button class="btn btn-secondary glass-button" data-action="scroll-to-viewer">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            <span><?php esc_html_e('Explore in 3D', 'skyyrose'); ?></span>
                        </button>
                    <?php endif; ?>
                </div>

                <!-- Collection Stats -->
                <div class="collection-stats">
                    <?php
                    $product_count = $featured_products->found_posts;
                    $min_price = PHP_FLOAT_MAX;
                    $max_price = 0;

                    if ($featured_products->have_posts()) {
                        while ($featured_products->have_posts()) {
                            $featured_products->the_post();
                            global $product;
                            if ($product) {
                                $price = (float) $product->get_price();
                                $min_price = min($min_price, $price);
                                $max_price = max($max_price, $price);
                            }
                        }
                        wp_reset_postdata();
                    }
                    ?>
                    <div class="stat">
                        <span class="stat-value"><?php echo esc_html($product_count); ?></span>
                        <span class="stat-label"><?php esc_html_e('Pieces', 'skyyrose'); ?></span>
                    </div>
                    <?php if ($min_price !== PHP_FLOAT_MAX) : ?>
                        <div class="stat">
                            <span class="stat-value"><?php echo wc_price($min_price); ?></span>
                            <span class="stat-label"><?php esc_html_e('Starting at', 'skyyrose'); ?></span>
                        </div>
                    <?php endif; ?>
                    <div class="stat">
                        <span class="stat-value"><?php esc_html_e('Free', 'skyyrose'); ?></span>
                        <span class="stat-label"><?php esc_html_e('Shipping $150+', 'skyyrose'); ?></span>
                    </div>
                </div>
            </div>
        </div>
    </section>

</main>

<?php
// Enqueue collection experience scripts
wp_enqueue_script('model-viewer', 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js', [], '3.4.0', true);
?>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Scroll-based camera controls for model-viewer
    const modelViewer = document.getElementById('collection-model-viewer');
    const experienceSection = document.getElementById('collection-viewer');

    if (modelViewer && modelViewer.dataset.scrollCamera === 'true') {
        let lastScrollY = 0;

        const handleScroll = () => {
            const rect = experienceSection.getBoundingClientRect();
            const viewportHeight = window.innerHeight;

            // Only apply scroll camera when section is in view
            if (rect.top < viewportHeight && rect.bottom > 0) {
                const scrollProgress = Math.max(0, Math.min(1,
                    (viewportHeight - rect.top) / (viewportHeight + rect.height)
                ));

                // Rotate camera based on scroll
                const theta = scrollProgress * 360;
                const phi = 75 - (scrollProgress * 30); // 75 to 45 degrees
                const distance = 5 + (scrollProgress * 2); // 5m to 7m

                modelViewer.cameraOrbit = `${theta}deg ${phi}deg ${distance}m`;
            }

            lastScrollY = window.scrollY;
        };

        // Throttle scroll handler
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    }

    // Scroll to viewer button
    const scrollToViewerBtn = document.querySelector('[data-action="scroll-to-viewer"]');
    if (scrollToViewerBtn) {
        scrollToViewerBtn.addEventListener('click', () => {
            experienceSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Hotspot click handlers
    const hotspots = document.querySelectorAll('.hotspot');
    hotspots.forEach(hotspot => {
        hotspot.addEventListener('click', () => {
            const productId = hotspot.dataset.productId;
            if (productId) {
                // Trigger quick view or scroll to product
                const productCard = document.querySelector(`.hotspot-product-card[data-product-id="${productId}"]`);
                if (productCard) {
                    productCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    productCard.classList.add('highlighted');
                    setTimeout(() => productCard.classList.remove('highlighted'), 2000);
                }
            }
        });
    });

    // Scroll progress indicator
    const progressBar = document.querySelector('.scroll-progress .progress-bar');
    if (progressBar) {
        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        }, { passive: true });
    }
});
</script>

<?php
get_footer();
