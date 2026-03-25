<?php
/**
 * Template Name: Black Rose Experience
 * Template Post Type: page
 *
 * Immersive Black Rose collection experience with AR/3D integration,
 * GSAP scroll animations, and pre-order conversion flow.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

// Collection data
$collection = skyyrose_get_collection('black-rose');
$collection_slug = 'black-rose';

// Get products for this collection
$products = wc_get_products([
    'status'   => 'publish',
    'limit'    => 12,
    'category' => [$collection_slug],
    'orderby'  => 'date',
    'order'    => 'DESC',
]);

get_header();
?>

<main id="experience-black-rose" class="experience-page experience-black-rose" data-collection="black-rose">

    <!-- Film Grain Overlay -->
    <div class="film-grain" aria-hidden="true"></div>

    <!-- Animated Orbs Background -->
    <div class="orbs-container" aria-hidden="true">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>

    <!-- ========================================
         SECTION 1: IMMERSIVE HERO
         ======================================== -->
    <section class="experience-hero" data-section="hero">
        <div class="hero-bg">
            <div class="hero-gradient"></div>
            <!-- Floating rose petals animation -->
            <div class="floating-petals" aria-hidden="true">
                <?php for ($i = 1; $i <= 15; $i++) : ?>
                    <div class="petal petal-<?php echo $i; ?>"></div>
                <?php endfor; ?>
            </div>
        </div>

        <div class="hero-content container">
            <div class="hero-text gsap-fade-up">
                <span class="hero-badge">
                    <span class="badge-text">The Collection</span>
                </span>
                <h1 class="hero-title">
                    <span class="title-line">BLACK</span>
                    <span class="title-line accent">ROSE</span>
                </h1>
                <p class="hero-tagline"><?php echo esc_html($collection['tagline']); ?></p>
                <p class="hero-description"><?php echo esc_html($collection['description']); ?></p>
            </div>

            <!-- 3D Model Showcase (placeholder for 2D until 3D ready) -->
            <div class="hero-showcase gsap-scale-in">
                <div class="showcase-frame">
                    <?php
                    // Check if 3D model exists, otherwise show high-quality 2D
                    $hero_3d_model = get_theme_mod('skyyrose_black_rose_hero_3d', '');
                    $hero_image = get_theme_mod('skyyrose_black_rose_hero_image', SKYYROSE_URI . '/assets/images/collections/black-rose-hero.jpg');

                    if ($hero_3d_model) : ?>
                        <model-viewer
                            src="<?php echo esc_url($hero_3d_model); ?>"
                            ios-src="<?php echo esc_url(str_replace('.glb', '.usdz', $hero_3d_model)); ?>"
                            alt="Black Rose Collection 3D Preview"
                            ar
                            ar-modes="webxr scene-viewer quick-look"
                            ar-scale="auto"
                            camera-controls
                            auto-rotate
                            rotation-per-second="15deg"
                            shadow-intensity="1"
                            exposure="0.8"
                            class="hero-model-viewer"
                        >
                            <button slot="ar-button" class="ar-button glass-button">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 22C17.523 22 22 17.523 22 12S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                                    <path d="M12 18v-6m0-6v6m0 0l-3-3m3 3l3-3"/>
                                </svg>
                                <span>View in AR</span>
                            </button>
                            <div class="model-loading" slot="poster">
                                <div class="loading-spinner"></div>
                            </div>
                        </model-viewer>
                    <?php else : ?>
                        <div class="hero-image-container">
                            <img
                                src="<?php echo esc_url($hero_image); ?>"
                                alt="Black Rose Collection"
                                class="hero-image parallax-image"
                                loading="eager"
                            >
                            <div class="image-overlay"></div>
                            <span class="coming-soon-badge">3D Experience Coming Soon</span>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>

        <!-- Scroll Indicator -->
        <div class="scroll-indicator gsap-fade-up" data-gsap-delay="1">
            <span class="scroll-text">Explore</span>
            <div class="scroll-line">
                <div class="scroll-dot"></div>
            </div>
        </div>
    </section>

    <!-- ========================================
         SECTION 2: BRAND STORY SCROLL EXPERIENCE
         ======================================== -->
    <section class="experience-story" data-section="story">
        <div class="story-panels">
            <!-- Panel 1: Origin -->
            <div class="story-panel panel-origin" data-panel="1">
                <div class="panel-content container">
                    <div class="panel-text">
                        <span class="panel-number">01</span>
                        <h2 class="panel-title">Born from Darkness</h2>
                        <p class="panel-description">
                            In the shadows of Oakland's streets, a vision emerged.
                            Black Rose represents the beauty found in darkness—
                            the strength that comes from embracing your true self.
                        </p>
                    </div>
                    <div class="panel-visual">
                        <div class="visual-frame"></div>
                    </div>
                </div>
            </div>

            <!-- Panel 2: Craftsmanship -->
            <div class="story-panel panel-craft" data-panel="2">
                <div class="panel-content container">
                    <div class="panel-text">
                        <span class="panel-number">02</span>
                        <h2 class="panel-title">Crafted with Intention</h2>
                        <p class="panel-description">
                            Every stitch tells a story. Premium materials meet
                            meticulous craftsmanship to create pieces that transcend
                            mere clothing—they become armor for the soul.
                        </p>
                    </div>
                    <div class="panel-visual">
                        <div class="visual-frame"></div>
                    </div>
                </div>
            </div>

            <!-- Panel 3: Identity -->
            <div class="story-panel panel-identity" data-panel="3">
                <div class="panel-content container">
                    <div class="panel-text">
                        <span class="panel-number">03</span>
                        <h2 class="panel-title">Wear Your Truth</h2>
                        <p class="panel-description">
                            Black Rose isn't just a collection—it's a declaration.
                            For those who refuse to fade into the background,
                            who find power in mystery and elegance in rebellion.
                        </p>
                    </div>
                    <div class="panel-visual">
                        <div class="visual-frame"></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ========================================
         SECTION 3: PRODUCT SHOWCASE WITH AR/3D
         ======================================== -->
    <section class="experience-showcase" data-section="showcase">
        <div class="container">
            <header class="section-header gsap-fade-up">
                <span class="section-label">The Pieces</span>
                <h2 class="section-title">Explore the Collection</h2>
                <p class="section-subtitle">
                    Tap any piece to view in AR or explore every detail in 3D
                </p>
            </header>

            <!-- Featured Product Spotlight -->
            <div class="product-spotlight gsap-scale-in">
                <?php
                // Get featured product for this collection
                $featured_product = null;
                foreach ($products as $product) {
                    if ($product->is_featured()) {
                        $featured_product = $product;
                        break;
                    }
                }
                if (!$featured_product && !empty($products)) {
                    $featured_product = $products[0];
                }

                if ($featured_product) :
                    $product_id = $featured_product->get_id();
                    $product_3d = get_post_meta($product_id, '_skyyrose_3d_model', true);
                    $product_image = wp_get_attachment_image_url($featured_product->get_image_id(), 'skyyrose-product');
                ?>
                <div class="spotlight-viewer">
                    <?php if ($product_3d) : ?>
                        <model-viewer
                            src="<?php echo esc_url($product_3d); ?>"
                            ios-src="<?php echo esc_url(str_replace('.glb', '.usdz', $product_3d)); ?>"
                            alt="<?php echo esc_attr($featured_product->get_name()); ?>"
                            ar
                            ar-modes="webxr scene-viewer quick-look"
                            ar-scale="auto"
                            camera-controls
                            touch-action="pan-y"
                            shadow-intensity="1"
                            class="spotlight-model"
                        >
                            <button slot="ar-button" class="ar-button">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                </svg>
                                View in Your Space
                            </button>
                            <!-- Product Hotspots -->
                            <div slot="hotspot-material" class="hotspot" data-position="0.5 0.8 0" data-normal="0 0 1">
                                <div class="hotspot-annotation">Premium Materials</div>
                            </div>
                            <div slot="hotspot-detail" class="hotspot" data-position="-0.3 0.4 0.2" data-normal="0 0 1">
                                <div class="hotspot-annotation">Signature Details</div>
                            </div>
                        </model-viewer>
                    <?php else : ?>
                        <div class="spotlight-image-container">
                            <img
                                src="<?php echo esc_url($product_image); ?>"
                                alt="<?php echo esc_attr($featured_product->get_name()); ?>"
                                class="spotlight-image"
                            >
                            <div class="ar-badge">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                </svg>
                                <span>3D Coming Soon</span>
                            </div>
                        </div>
                    <?php endif; ?>
                </div>

                <div class="spotlight-info">
                    <span class="spotlight-collection">Black Rose Collection</span>
                    <h3 class="spotlight-name"><?php echo esc_html($featured_product->get_name()); ?></h3>
                    <p class="spotlight-description"><?php echo wp_kses_post($featured_product->get_short_description()); ?></p>
                    <div class="spotlight-price"><?php echo $featured_product->get_price_html(); ?></div>
                    <div class="spotlight-actions">
                        <a href="<?php echo esc_url($featured_product->get_permalink()); ?>" class="btn btn-primary">
                            View Details
                        </a>
                        <button type="button" class="btn btn-outline quick-add-btn" data-product-id="<?php echo esc_attr($product_id); ?>">
                            Quick Add
                        </button>
                    </div>
                </div>
                <?php endif; ?>
            </div>
        </div>
    </section>

    <!-- ========================================
         SECTION 4: IMMERSIVE 3D SCENE WITH HOTSPOTS
         ======================================== -->
    <section class="experience-immersive-scene" data-section="immersive">
        <div class="container">
            <header class="section-header gsap-fade-up">
                <span class="section-label">Immersive Experience</span>
                <h2 class="section-title">Enter the Black Rose Garden</h2>
                <p class="section-subtitle">
                    Explore our interactive 3D environment. Discover hidden products and unlock exclusive access.
                </p>
            </header>
        </div>

        <?php
        // Include the scene viewer with hotspots
        $scene_viewer_args = [
            'collection_slug' => $collection_slug,
            'collection'      => $collection,
            'scene_model'     => get_theme_mod('skyyrose_black_rose_scene_3d', ''),
            'hotspots'        => [], // Will be loaded from JSON in template
        ];

        // Load hotspots from central hotspots directory
        $hotspots_file = dirname(SKYYROSE_DIR) . '/../hotspots/black_rose_hotspots.json';
        if (file_exists($hotspots_file)) {
            $hotspots_data = json_decode(file_get_contents($hotspots_file), true);
            $scene_viewer_args['hotspots'] = $hotspots_data['hotspots'] ?? [];
        }

        // Make variables available to template part
        extract($scene_viewer_args);
        get_template_part('template-parts/experience/scene-viewer');
        ?>
    </section>

    <!-- ========================================
         SECTION 5: INLINE PRODUCT CATALOG
         ======================================== -->
    <section class="experience-catalog" data-section="catalog">
        <div class="container">
            <header class="section-header gsap-fade-up">
                <span class="section-label">Shop</span>
                <h2 class="section-title">The Full Collection</h2>
            </header>

            <!-- Filter Bar -->
            <div class="catalog-filters gsap-fade-up">
                <div class="filter-group">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="tops">Tops</button>
                    <button class="filter-btn" data-filter="bottoms">Bottoms</button>
                    <button class="filter-btn" data-filter="outerwear">Outerwear</button>
                    <button class="filter-btn" data-filter="accessories">Accessories</button>
                </div>
                <div class="view-toggle">
                    <button class="view-btn active" data-view="grid" aria-label="Grid view">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                            <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
                        </svg>
                    </button>
                    <button class="view-btn" data-view="list" aria-label="List view">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                            <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
                            <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Product Grid -->
            <div class="catalog-grid gsap-stagger">
                <?php if (!empty($products)) : ?>
                    <?php foreach ($products as $product) :
                        $product_id = $product->get_id();
                        $product_image = wp_get_attachment_image_url($product->get_image_id(), 'skyyrose-product');
                        $product_hover_image = get_post_meta($product_id, '_skyyrose_hover_image', true);
                        $product_3d = get_post_meta($product_id, '_skyyrose_3d_model', true);
                        $product_categories = wp_get_post_terms($product_id, 'product_cat', ['fields' => 'slugs']);
                    ?>
                    <article class="product-card glass-card"
                             data-product-id="<?php echo esc_attr($product_id); ?>"
                             data-categories="<?php echo esc_attr(implode(' ', $product_categories)); ?>">

                        <div class="product-image-wrapper">
                            <a href="<?php echo esc_url($product->get_permalink()); ?>" class="product-link">
                                <img
                                    src="<?php echo esc_url($product_image); ?>"
                                    alt="<?php echo esc_attr($product->get_name()); ?>"
                                    class="product-image product-image-primary"
                                    loading="lazy"
                                >
                                <?php if ($product_hover_image) : ?>
                                <img
                                    src="<?php echo esc_url($product_hover_image); ?>"
                                    alt=""
                                    class="product-image product-image-hover"
                                    loading="lazy"
                                    aria-hidden="true"
                                >
                                <?php endif; ?>
                            </a>

                            <!-- Badges -->
                            <div class="product-badges">
                                <?php if ($product->is_on_sale()) : ?>
                                    <span class="badge badge-sale">Sale</span>
                                <?php endif; ?>
                                <?php if ($product_3d) : ?>
                                    <span class="badge badge-3d" title="3D View Available">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                        </svg>
                                    </span>
                                <?php else : ?>
                                    <span class="badge badge-coming-soon">3D Soon</span>
                                <?php endif; ?>
                            </div>

                            <!-- Quick Actions (slide up on hover) -->
                            <div class="product-actions">
                                <button type="button" class="action-btn quick-view-btn" data-product-id="<?php echo esc_attr($product_id); ?>" title="Quick View">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                        <circle cx="12" cy="12" r="3"/>
                                    </svg>
                                </button>
                                <?php if ($product_3d) : ?>
                                <button type="button" class="action-btn ar-view-btn" data-model="<?php echo esc_url($product_3d); ?>" title="View in AR">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                    </svg>
                                </button>
                                <?php endif; ?>
                                <button type="button" class="action-btn wishlist-btn" data-product-id="<?php echo esc_attr($product_id); ?>" title="Add to Wishlist">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                                    </svg>
                                </button>
                                <button type="button" class="action-btn add-to-cart-btn" data-product-id="<?php echo esc_attr($product_id); ?>" title="Add to Cart">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
                                        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div class="product-info">
                            <span class="product-collection">Black Rose</span>
                            <h3 class="product-name">
                                <a href="<?php echo esc_url($product->get_permalink()); ?>">
                                    <?php echo esc_html($product->get_name()); ?>
                                </a>
                            </h3>
                            <div class="product-price">
                                <?php echo $product->get_price_html(); ?>
                            </div>
                        </div>
                    </article>
                    <?php endforeach; ?>
                <?php else : ?>
                    <div class="no-products">
                        <p>Products coming soon. Join our waitlist to be notified.</p>
                    </div>
                <?php endif; ?>
            </div>

            <!-- View All Link -->
            <div class="catalog-footer gsap-fade-up">
                <a href="<?php echo esc_url(get_term_link('black-rose', 'product_cat')); ?>" class="btn btn-outline">
                    View All Black Rose Products
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                </a>
            </div>
        </div>
    </section>

    <!-- ========================================
         SECTION 6: PRE-ORDER PORTAL
         ======================================== -->
    <section class="experience-portal" data-section="portal">
        <div class="portal-bg">
            <div class="portal-particles" id="portalParticles"></div>
            <div class="portal-glow"></div>
        </div>

        <div class="portal-content container">
            <div class="portal-frame gsap-scale-in">
                <div class="portal-inner">
                    <!-- Animated rose petals scattering effect -->
                    <div class="scatter-petals" aria-hidden="true">
                        <?php for ($i = 1; $i <= 20; $i++) : ?>
                            <div class="scatter-petal scatter-petal-<?php echo $i; ?>"></div>
                        <?php endfor; ?>
                    </div>

                    <div class="portal-text">
                        <span class="portal-label">Exclusive Access</span>
                        <h2 class="portal-title">Enter the<br>Pre-Order Experience</h2>
                        <p class="portal-description">
                            Be among the first to own pieces from the Black Rose collection.
                            Secure your exclusive items before they're released to the public.
                        </p>

                        <div class="portal-benefits">
                            <div class="benefit">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                                <span>Early Access</span>
                            </div>
                            <div class="benefit">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                                <span>Limited Editions</span>
                            </div>
                            <div class="benefit">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                                <span>Priority Shipping</span>
                            </div>
                        </div>

                        <a href="<?php echo esc_url(home_url('/pre-order/')); ?>" class="portal-cta magnetic-btn">
                            <span class="cta-text">Enter Pre-Order</span>
                            <span class="cta-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M5 12h14M12 5l7 7-7 7"/>
                                </svg>
                            </span>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </section>

</main>

<!-- Quick View Modal -->
<div id="quickViewModal" class="modal quick-view-modal" role="dialog" aria-modal="true" aria-hidden="true">
    <div class="modal-backdrop"></div>
    <div class="modal-content glass-panel">
        <button type="button" class="modal-close" aria-label="Close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
        <div class="modal-body">
            <div class="quick-view-loading">
                <div class="loading-spinner"></div>
            </div>
            <div class="quick-view-content"></div>
        </div>
    </div>
</div>

<!-- AR Viewer Modal -->
<div id="arViewerModal" class="modal ar-viewer-modal" role="dialog" aria-modal="true" aria-hidden="true">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <button type="button" class="modal-close" aria-label="Close">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
        <div class="ar-viewer-container">
            <model-viewer
                id="arModalViewer"
                ar
                ar-modes="webxr scene-viewer quick-look"
                camera-controls
                touch-action="pan-y"
                shadow-intensity="1"
                class="ar-modal-viewer"
            >
                <button slot="ar-button" class="ar-button-fullscreen">
                    Launch AR Experience
                </button>
            </model-viewer>
        </div>
    </div>
</div>

<?php get_footer(); ?>
