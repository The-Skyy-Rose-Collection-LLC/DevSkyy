<?php
/**
 * Template Name: Immersive Experience
 * Description: Immersive collection experience with CSS effects and product hotspots
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();

// Get collection type from page meta or URL
$collection = get_post_meta(get_the_ID(), '_collection_type', true) ?: 'signature';

// Collection configurations
$collections = [
    'black-rose' => [
        'name' => 'Black Rose',
        'tagline' => 'Gothic Elegance',
        'description' => 'Dark, mysterious, and unapologetically bold. The Black Rose collection embodies strength through vulnerability, beauty through darkness.',
        'color' => '#8B0000',
        'gradient' => 'radial-gradient(circle at 30% 40%, rgba(139, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.8) 50%, #000 100%)',
        'shop_url' => '/black-rose',
    ],
    'love-hurts' => [
        'name' => 'Love Hurts',
        'tagline' => 'Romantic Rebellion',
        'description' => 'For those who dare to feel. Soft hearts meet sharp edges in a collection that celebrates emotional depth and vulnerability as strength.',
        'color' => '#B76E79',
        'gradient' => 'radial-gradient(circle at 70% 30%, rgba(183, 110, 121, 0.3) 0%, rgba(50, 20, 30, 0.7) 50%, #000 100%)',
        'shop_url' => '/love-hurts',
    ],
    'signature' => [
        'name' => 'Signature',
        'tagline' => 'Timeless Luxury',
        'description' => 'The foundation of SkyyRose. Premium cuts, gold accents, and architectural tailoring that transcends trends and defines personal style.',
        'color' => '#D4AF37',
        'gradient' => 'radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.2) 0%, rgba(40, 35, 20, 0.6) 50%, #000 100%)',
        'shop_url' => '/signature',
    ],
];

$config = $collections[$collection] ?? $collections['signature'];

// Get featured products for this collection
$products_query = new WP_Query([
    'post_type' => 'product',
    'posts_per_page' => 6,
    'meta_query' => [
        [
            'key' => '_skyyrose_collection',
            'value' => $collection,
            'compare' => '='
        ]
    ],
    'orderby' => 'menu_order',
    'order' => 'ASC'
]);
?>

<style>
:root {
    --collection-color: <?php echo esc_attr($config['color']); ?>;
    --bg-dark: #000000;
}

.immersive-experience {
    min-height: 100vh;
    background: var(--bg-dark);
    color: #fff;
    position: relative;
    overflow: hidden;
}

/* Ambient Background */
.immersive-bg {
    position: fixed;
    inset: 0;
    background: <?php echo esc_attr($config['gradient']); ?>;
    z-index: -2;
}

/* Animated Particles */
.immersive-bg::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(2px 2px at 20% 30%, rgba(255, 255, 255, 0.3), transparent),
        radial-gradient(2px 2px at 60% 70%, rgba(255, 255, 255, 0.2), transparent),
        radial-gradient(1px 1px at 50% 50%, rgba(255, 255, 255, 0.1), transparent),
        radial-gradient(1px 1px at 80% 10%, rgba(255, 255, 255, 0.2), transparent);
    background-size: 200px 200px, 300px 300px, 150px 150px, 250px 250px;
    background-position: 0 0, 40px 60px, 130px 270px, 70px 100px;
    animation: float-particles 20s linear infinite;
}

@keyframes float-particles {
    0% { background-position: 0 0, 40px 60px, 130px 270px, 70px 100px; }
    100% { background-position: 0 -200px, 40px -240px, 130px 70px, 70px -100px; }
}

/* Noise Texture */
.immersive-bg::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.05;
    mix-blend-mode: overlay;
}

/* Hero Section */
.immersive-hero {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 120px 2rem 80px;
    position: relative;
}

.collection-badge {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 50px;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--collection-color);
    margin-bottom: 2rem;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    animation: fadeUp 1s ease-out;
}

.immersive-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(4rem, 12vw, 8rem);
    font-weight: 400;
    margin-bottom: 1rem;
    color: var(--collection-color);
    text-shadow: 0 0 60px rgba(255, 255, 255, 0.1);
    animation: fadeUp 1s ease-out 0.2s backwards;
}

.immersive-tagline {
    font-size: 1.5rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 2rem;
    animation: fadeUp 1s ease-out 0.4s backwards;
}

.immersive-description {
    max-width: 700px;
    font-size: 1.1rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.7);
    margin: 0 auto 3rem;
    animation: fadeUp 1s ease-out 0.6s backwards;
}

.cta-group {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
    animation: fadeUp 1s ease-out 0.8s backwards;
}

.btn {
    padding: 1.2rem 3rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-decoration: none;
    border-radius: 2px;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transform: translateX(-100%);
    transition: transform 0.5s ease;
}

.btn:hover::before {
    transform: translateX(100%);
}

.btn-primary {
    background: var(--collection-color);
    color: #000;
    border: 1px solid var(--collection-color);
}

.btn-primary:hover {
    box-shadow: 0 0 30px var(--collection-color);
    transform: translateY(-3px);
}

.btn-ghost {
    background: transparent;
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-ghost:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #fff;
}

/* Product Hotspots Section */
.hotspots-section {
    padding: 8rem 2rem;
    position: relative;
}

.section-title {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--collection-color);
}

.section-subtitle {
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 5rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.9rem;
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 3rem;
    max-width: 1400px;
    margin: 0 auto;
}

.product-hotspot {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 2rem;
    transition: all 0.4s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}

.product-hotspot::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, var(--collection-color), transparent);
    opacity: 0;
    transition: opacity 0.4s ease;
}

.product-hotspot:hover {
    transform: translateY(-10px);
    border-color: var(--collection-color);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.product-hotspot:hover::before {
    opacity: 0.05;
}

.hotspot-image {
    width: 100%;
    height: 300px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
}

.hotspot-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.product-hotspot:hover .hotspot-image img {
    transform: scale(1.1);
}

.hotspot-placeholder {
    font-size: 4rem;
    opacity: 0.3;
}

.hotspot-info {
    position: relative;
    z-index: 1;
}

.hotspot-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: #fff;
}

.hotspot-price {
    font-size: 1.2rem;
    color: var(--collection-color);
    margin-bottom: 1rem;
    letter-spacing: 1px;
}

.hotspot-description {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.6;
    margin-bottom: 1.5rem;
}

.view-product-btn {
    width: 100%;
    padding: 0.8rem;
    background: transparent;
    border: 1px solid var(--collection-color);
    color: var(--collection-color);
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s ease;
}

.view-product-btn:hover {
    background: var(--collection-color);
    color: #000;
}

/* View Switcher */
.view-switcher {
    position: fixed;
    bottom: 3rem;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50px;
    padding: 1rem 2rem;
    display: flex;
    gap: 1rem;
    z-index: 100;
}

.view-btn {
    padding: 0.6rem 1.5rem;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: rgba(255, 255, 255, 0.7);
    border-radius: 30px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.8rem;
    letter-spacing: 1px;
}

.view-btn.active,
.view-btn:hover {
    background: var(--collection-color);
    border-color: var(--collection-color);
    color: #000;
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive */
@media (max-width: 768px) {
    .immersive-title {
        font-size: 4rem;
    }

    .cta-group {
        flex-direction: column;
        width: 100%;
        max-width: 320px;
        margin: 0 auto;
    }

    .btn {
        width: 100%;
    }

    .products-grid {
        grid-template-columns: 1fr;
    }

    .view-switcher {
        bottom: 1.5rem;
        padding: 0.8rem 1.5rem;
    }

    .view-btn {
        padding: 0.5rem 1rem;
        font-size: 0.7rem;
    }
}
</style>

<div class="immersive-experience">
    <div class="immersive-bg"></div>

    <!-- Hero Section -->
    <section class="immersive-hero">
        <div class="collection-badge"><?php echo esc_html($config['tagline']); ?></div>
        <h1 class="immersive-title"><?php echo esc_html($config['name']); ?></h1>
        <p class="immersive-tagline">Collection Experience</p>
        <p class="immersive-description">
            <?php echo esc_html($config['description']); ?>
        </p>
        <div class="cta-group">
            <a href="<?php echo esc_url($config['shop_url']); ?>" class="btn btn-primary">
                Shop Collection
                <span>→</span>
            </a>
            <a href="#products" class="btn btn-ghost">
                Explore Featured
                <span>↓</span>
            </a>
        </div>
    </section>

    <!-- Product Hotspots -->
    <section id="products" class="hotspots-section">
        <h2 class="section-title">Featured Pieces</h2>
        <p class="section-subtitle">Discover the Collection</p>

        <div class="products-grid">
            <?php
            if ($products_query->have_posts()) :
                while ($products_query->have_posts()) : $products_query->the_post();
                    global $product;
                    $short_desc = get_post_meta(get_the_ID(), '_short_description', true);
                    if (!$short_desc) {
                        $short_desc = wp_trim_words(get_the_excerpt(), 15, '...');
                    }
            ?>
                <div class="product-hotspot" onclick="window.location.href='<?php echo esc_url(get_permalink()); ?>'">
                    <div class="hotspot-image">
                        <?php
                        if (has_post_thumbnail()) {
                            the_post_thumbnail('skyyrose-product');
                        } else {
                            echo '<span class="hotspot-placeholder">✦</span>';
                        }
                        ?>
                    </div>
                    <div class="hotspot-info">
                        <h3 class="hotspot-title"><?php the_title(); ?></h3>
                        <div class="hotspot-price"><?php echo $product->get_price_html(); ?></div>
                        <p class="hotspot-description"><?php echo esc_html($short_desc); ?></p>
                        <button class="view-product-btn" onclick="event.stopPropagation(); window.location.href='<?php echo esc_url(get_permalink()); ?>'">
                            View Details
                        </button>
                    </div>
                </div>
            <?php
                endwhile;
                wp_reset_postdata();
            else :
            ?>
                <div style="grid-column: 1 / -1; text-align: center; padding: 4rem;">
                    <p style="color: rgba(255, 255, 255, 0.5);">Coming Soon</p>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <!-- View Switcher -->
    <div class="view-switcher">
        <button class="view-btn active">Experience</button>
        <a href="<?php echo esc_url($config['shop_url']); ?>" class="view-btn">Shop View</a>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Parallax effect on scroll
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const scrolled = window.pageYOffset;
                const bg = document.querySelector('.immersive-bg');
                if (bg) {
                    bg.style.transform = `translateY(${scrolled * 0.5}px)`;
                }
                ticking = false;
            });
            ticking = true;
        }
    });
});
</script>

<?php get_footer(); ?>
