<?php
/**
 * Template Name: Signature Experience
 * Description: Immersive AR experience page for Signature collection
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header();

// Collection data
$collection = skyyrose_get_collection('signature');
$collection_slug = 'signature';

// Hero settings (customizable via ACF or Customizer)
$hero_title = get_post_meta(get_the_ID(), '_experience_hero_title', true) ?: $collection['name'];
$hero_tagline = get_post_meta(get_the_ID(), '_experience_hero_tagline', true) ?: $collection['tagline'];
$hero_3d_model = get_post_meta(get_the_ID(), '_experience_hero_model', true);
$hero_image = get_post_meta(get_the_ID(), '_experience_hero_image', true) ?: get_the_post_thumbnail_url(get_the_ID(), 'full');
$hero_video = get_post_meta(get_the_ID(), '_experience_hero_video', true);

// Story panels
$story_panels = [
    [
        'title' => 'Timeless Craftsmanship',
        'content' => 'Every Signature piece is a testament to meticulous attention to detail. From initial sketch to final stitch, perfection is our only standard.',
        'image' => SKYYROSE_URI . '/assets/images/signature/story-1.jpg',
    ],
    [
        'title' => 'Luxurious Materials',
        'content' => 'We source the finest fabrics from around the world. Italian silks, French lace, Japanese denim - only the exceptional makes the cut.',
        'image' => SKYYROSE_URI . '/assets/images/signature/story-2.jpg',
    ],
    [
        'title' => 'Oakland Heritage',
        'content' => 'Rooted in the vibrant culture of Oakland, our Signature collection bridges old-world elegance with modern street sophistication.',
        'image' => SKYYROSE_URI . '/assets/images/signature/story-3.jpg',
    ],
];

// Get products from this collection
$products_args = [
    'post_type'      => 'product',
    'posts_per_page' => 12,
    'tax_query'      => [
        [
            'taxonomy' => 'product_cat',
            'field'    => 'slug',
            'terms'    => $collection_slug,
        ],
    ],
];
$products_query = new WP_Query($products_args);

// Featured/spotlight products
$spotlight_products = [];
if ($products_query->have_posts()) {
    $count = 0;
    while ($products_query->have_posts() && $count < 3) {
        $products_query->the_post();
        $product = wc_get_product(get_the_ID());
        if ($product) {
            $spotlight_products[] = [
                'id'          => get_the_ID(),
                'name'        => $product->get_name(),
                'price'       => $product->get_price_html(),
                'image'       => wp_get_attachment_image_url($product->get_image_id(), 'skyyrose-collection'),
                'link'        => $product->get_permalink(),
                'model_src'   => get_post_meta(get_the_ID(), '_3d_model_glb', true),
                'ios_src'     => get_post_meta(get_the_ID(), '_3d_model_usdz', true),
                'description' => wp_trim_words($product->get_short_description(), 20),
            ];
        }
        $count++;
    }
    wp_reset_postdata();
}
?>

<main id="primary" class="experience-page experience-page--signature">

    <!-- Film Grain Overlay -->
    <div class="film-grain" aria-hidden="true"></div>

    <!-- Animated Orbs - Gold themed for Signature -->
    <div class="orbs-container" aria-hidden="true">
        <div class="orb orb--1"></div>
        <div class="orb orb--2"></div>
        <div class="orb orb--3"></div>
    </div>

    <!-- Hero Section -->
    <section class="experience-hero">
        <?php if ($hero_video) : ?>
            <div class="experience-hero__bg experience-hero__bg--video">
                <video autoplay muted loop playsinline>
                    <source src="<?php echo esc_url($hero_video); ?>" type="video/mp4">
                </video>
            </div>
        <?php elseif ($hero_image) : ?>
            <div class="experience-hero__bg" style="background-image: url('<?php echo esc_url($hero_image); ?>');"></div>
        <?php endif; ?>

        <div class="experience-hero__content">
            <div class="experience-hero__badge">
                <span>Flagship Collection</span>
            </div>

            <h1 class="experience-hero__title"><?php echo esc_html($hero_title); ?></h1>
            <p class="experience-hero__tagline"><?php echo esc_html($hero_tagline); ?></p>

            <div class="experience-hero__3d-container">
                <?php if ($hero_3d_model) : ?>
                    <model-viewer
                        src="<?php echo esc_url($hero_3d_model); ?>"
                        ios-src="<?php echo esc_url(str_replace('.glb', '.usdz', $hero_3d_model)); ?>"
                        ar
                        ar-modes="webxr scene-viewer quick-look"
                        ar-scale="auto"
                        camera-controls
                        auto-rotate
                        rotation-per-second="15deg"
                        shadow-intensity="1.2"
                        exposure="1.1"
                        class="experience-hero__model-viewer">
                        <button slot="ar-button" class="ar-button">
                            <span class="ar-button__icon" aria-hidden="true">&#x1F4F1;</span>
                            Experience in AR
                        </button>
                        <div class="model-viewer__loading">
                            <div class="loading-spinner loading-spinner--gold"></div>
                        </div>
                    </model-viewer>
                <?php else : ?>
                    <!-- 2D Placeholder until 3D models are ready -->
                    <div class="experience-hero__2d-showcase experience-hero__2d-showcase--runway">
                        <?php if (!empty($spotlight_products)) : ?>
                            <div class="runway-showcase">
                                <?php foreach (array_slice($spotlight_products, 0, 3) as $index => $product) : ?>
                                    <img
                                        src="<?php echo esc_url($product['image']); ?>"
                                        alt="<?php echo esc_attr($product['name']); ?>"
                                        class="runway-image runway-image--<?php echo $index + 1; ?>"
                                        loading="<?php echo $index === 0 ? 'eager' : 'lazy'; ?>"
                                    >
                                <?php endforeach; ?>
                            </div>
                        <?php endif; ?>
                        <div class="badge-3d-coming badge-3d-coming--gold">
                            <span>3D Runway</span>
                            <span>Coming Soon</span>
                        </div>
                    </div>
                <?php endif; ?>
            </div>

            <div class="experience-hero__cta">
                <a href="#catalog" class="btn btn--gold btn--lg">
                    Shop the Collection
                </a>
                <a href="#story" class="btn btn--ghost btn--lg">
                    The Signature Story
                </a>
            </div>
        </div>

        <div class="experience-hero__scroll-indicator">
            <span>Discover Excellence</span>
            <div class="scroll-arrow scroll-arrow--gold"></div>
        </div>
    </section>

    <!-- Story Section -->
    <section id="story" class="experience-story">
        <div class="container">
            <header class="section-header">
                <span class="section-eyebrow">Our Heritage</span>
                <h2 class="section-title">The Signature Story</h2>
                <p class="section-subtitle"><?php echo esc_html($collection['description']); ?></p>
            </header>

            <div class="story-panels story-panels--elegant">
                <?php foreach ($story_panels as $index => $panel) : ?>
                    <article class="story-panel story-panel--<?php echo ($index % 2 === 0) ? 'left' : 'right'; ?>" data-panel="<?php echo esc_attr($index); ?>">
                        <div class="story-panel__content">
                            <span class="story-panel__number"><?php echo str_pad($index + 1, 2, '0', STR_PAD_LEFT); ?></span>
                            <h3 class="story-panel__title"><?php echo esc_html($panel['title']); ?></h3>
                            <p class="story-panel__text"><?php echo esc_html($panel['content']); ?></p>
                        </div>
                        <div class="story-panel__media">
                            <div class="story-panel__frame">
                                <img
                                    src="<?php echo esc_url($panel['image']); ?>"
                                    alt="<?php echo esc_attr($panel['title']); ?>"
                                    loading="lazy"
                                >
                            </div>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

    <!-- Product Showcase Section -->
    <section class="experience-showcase">
        <div class="container">
            <header class="section-header">
                <span class="section-eyebrow">Editor's Picks</span>
                <h2 class="section-title">Featured Signatures</h2>
                <p class="section-subtitle">Curated pieces that define the collection</p>
            </header>

            <div class="spotlight-grid spotlight-grid--luxury">
                <?php foreach ($spotlight_products as $product) : ?>
                    <article
                        class="spotlight-item spotlight-item--signature glass-card"
                        data-product-id="<?php echo esc_attr($product['id']); ?>"
                        data-model-src="<?php echo esc_attr($product['model_src']); ?>"
                        data-ios-src="<?php echo esc_attr($product['ios_src']); ?>"
                        data-description="<?php echo esc_attr($product['description']); ?>">

                        <div class="spotlight-item__media">
                            <?php if ($product['model_src']) : ?>
                                <model-viewer
                                    src="<?php echo esc_url($product['model_src']); ?>"
                                    ios-src="<?php echo esc_url($product['ios_src']); ?>"
                                    ar
                                    ar-modes="webxr scene-viewer quick-look"
                                    camera-controls
                                    auto-rotate
                                    rotation-per-second="20deg"
                                    shadow-intensity="0.8"
                                    exposure="1.05">
                                    <button slot="ar-button" class="ar-button ar-button--gold">AR</button>
                                </model-viewer>
                            <?php else : ?>
                                <img
                                    src="<?php echo esc_url($product['image']); ?>"
                                    alt="<?php echo esc_attr($product['name']); ?>"
                                    loading="lazy"
                                >
                                <span class="badge-3d-soon badge-3d-soon--gold">3D Soon</span>
                            <?php endif; ?>
                        </div>

                        <div class="spotlight-item__info">
                            <h3 class="spotlight-item__title"><?php echo esc_html($product['name']); ?></h3>
                            <p class="spotlight-item__price"><?php echo $product['price']; ?></p>
                            <a href="<?php echo esc_url($product['link']); ?>" class="btn btn--gold btn--sm">
                                Explore Piece
                            </a>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

    <!-- Immersive 3D Scene with Hotspots -->
    <section class="experience-immersive-scene" data-section="immersive">
        <div class="container">
            <header class="section-header gsap-fade-up">
                <span class="section-eyebrow">Immersive Experience</span>
                <h2 class="section-title">Walk the Runway</h2>
                <p class="section-subtitle">
                    Step into our virtual runway. Explore each piece in stunning detail and discover exclusive designs.
                </p>
            </header>
        </div>

        <?php
        // Include the scene viewer with hotspots
        $scene_viewer_args = [
            'collection_slug' => $collection_slug,
            'collection'      => $collection,
            'scene_model'     => get_theme_mod('skyyrose_signature_scene_3d', ''),
            'hotspots'        => [],
        ];

        // Load hotspots from central hotspots directory
        $hotspots_file = dirname(SKYYROSE_DIR) . '/../hotspots/signature_hotspots.json';
        if (file_exists($hotspots_file)) {
            $hotspots_data = json_decode(file_get_contents($hotspots_file), true);
            $scene_viewer_args['hotspots'] = $hotspots_data['hotspots'] ?? [];
        }

        // Make variables available to template part
        extract($scene_viewer_args);
        get_template_part('template-parts/experience/scene-viewer');
        ?>
    </section>

    <!-- Product Catalog Section -->
    <section id="catalog" class="experience-catalog">
        <div class="container">
            <header class="section-header">
                <span class="section-eyebrow">Shop</span>
                <h2 class="section-title">Complete Collection</h2>
                <p class="section-subtitle">Every piece in the <?php echo esc_html($collection['name']); ?> line</p>
            </header>

            <?php if ($products_query->have_posts()) : ?>
                <div class="products-grid products-grid--luxury">
                    <?php
                    $products_query->rewind_posts();
                    while ($products_query->have_posts()) :
                        $products_query->the_post();
                        $product = wc_get_product(get_the_ID());
                        if (!$product) continue;

                        $product_id = get_the_ID();
                        $model_src = get_post_meta($product_id, '_3d_model_glb', true);
                        $ios_src = get_post_meta($product_id, '_3d_model_usdz', true);
                        ?>
                        <article
                            class="product-card product-card--signature glass-card"
                            data-product-id="<?php echo esc_attr($product_id); ?>"
                            data-model-src="<?php echo esc_attr($model_src); ?>"
                            data-ios-src="<?php echo esc_attr($ios_src); ?>"
                            data-description="<?php echo esc_attr(wp_trim_words($product->get_short_description(), 15)); ?>">

                            <div class="product-card__image">
                                <a href="<?php echo esc_url($product->get_permalink()); ?>" class="product-card__link">
                                    <?php echo $product->get_image('skyyrose-product'); ?>
                                </a>

                                <?php if ($model_src) : ?>
                                    <span class="badge-ar badge-ar--gold">AR Ready</span>
                                <?php endif; ?>

                                <div class="product-card__actions">
                                    <button class="product-card__quick-view" aria-label="Quick view">
                                        <span aria-hidden="true">&#x1F441;</span>
                                    </button>
                                    <button class="product-card__wishlist" aria-label="Add to wishlist">
                                        <span aria-hidden="true">&#x2665;</span>
                                    </button>
                                    <?php if ($model_src) : ?>
                                        <button class="product-card__ar" aria-label="View in AR">
                                            <span aria-hidden="true">&#x1F4F1;</span>
                                        </button>
                                    <?php endif; ?>
                                </div>
                            </div>

                            <div class="product-card__info">
                                <h3 class="product-card__title">
                                    <a href="<?php echo esc_url($product->get_permalink()); ?>">
                                        <?php echo esc_html($product->get_name()); ?>
                                    </a>
                                </h3>
                                <p class="product-card__price"><?php echo $product->get_price_html(); ?></p>
                                <button class="product-card__cart btn btn--gold btn--sm">
                                    Add to Collection
                                </button>
                            </div>
                        </article>
                    <?php endwhile; ?>
                </div>

                <?php
                // Pagination
                $total_pages = $products_query->max_num_pages;
                if ($total_pages > 1) :
                    ?>
                    <nav class="pagination pagination--gold">
                        <?php
                        echo paginate_links([
                            'total'     => $total_pages,
                            'prev_text' => '&larr; Previous',
                            'next_text' => 'Next &rarr;',
                        ]);
                        ?>
                    </nav>
                <?php endif; ?>

                <?php wp_reset_postdata(); ?>

            <?php else : ?>
                <div class="no-products">
                    <p>The Signature collection is being curated. Pre-order to secure your piece.</p>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <!-- Pre-Order Portal Section -->
    <section class="experience-portal experience-portal--signature">
        <div class="portal-bg">
            <!-- Animated gold particles for Signature collection -->
            <div class="portal-particles" aria-hidden="true">
                <?php for ($i = 1; $i <= 20; $i++) : ?>
                    <div class="particle particle--<?php echo $i; ?>"></div>
                <?php endfor; ?>
            </div>
        </div>

        <div class="container">
            <div class="portal-content portal-content--signature glass-card">
                <div class="portal-badge">
                    <span>Exclusive Access</span>
                </div>

                <h2 class="portal-title">Join the Inner Circle</h2>
                <p class="portal-subtitle">
                    Pre-order the <?php echo esc_html($collection['name']); ?> collection for priority access,
                    exclusive colorways, and personalized styling consultations.
                </p>

                <div class="portal-features portal-features--horizontal">
                    <div class="portal-feature">
                        <span class="portal-feature__icon portal-feature__icon--gold" aria-hidden="true">&#x1F451;</span>
                        <span class="portal-feature__text">VIP Priority Shipping</span>
                    </div>
                    <div class="portal-feature">
                        <span class="portal-feature__icon portal-feature__icon--gold" aria-hidden="true">&#x2728;</span>
                        <span class="portal-feature__text">Exclusive Colorways</span>
                    </div>
                    <div class="portal-feature">
                        <span class="portal-feature__icon portal-feature__icon--gold" aria-hidden="true">&#x1F4AC;</span>
                        <span class="portal-feature__text">Personal Styling</span>
                    </div>
                </div>

                <a
                    href="<?php echo esc_url(home_url('/pre-order/')); ?>"
                    class="portal-cta btn btn--gold btn--xl"
                    data-href="<?php echo esc_url(home_url('/pre-order/')); ?>">
                    Reserve Your Signature
                </a>

                <p class="portal-note">
                    Limited quantities available. Secure yours today.
                </p>
            </div>
        </div>
    </section>

</main>

<?php get_footer(); ?>
