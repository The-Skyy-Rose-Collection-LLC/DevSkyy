<?php
/**
 * Template Name: Collection - Signature
 * Description: Gold-themed luxury collection page with product grid
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();

// Get collection from query param or page meta
$collection = isset($_GET['collection']) ? sanitize_text_field($_GET['collection']) : 'signature';
$collection_meta = get_post_meta(get_the_ID(), '_collection_type', true) ?: $collection;

// Collection themes
$themes = [
    'signature' => [
        'title' => 'Signature',
        'subtitle' => 'Timeless luxury defined by sharp cuts, gold details, and premium fabrications. The foundation of SkyyRose.',
        'color' => '#D4AF37',
        'glow' => '#FDD835',
        'gradient_start' => 'rgba(212, 175, 55, 0.1)',
        'gradient_end' => 'rgba(212, 175, 55, 0.05)',
    ],
    'black-rose' => [
        'title' => 'Black Rose',
        'subtitle' => 'Gothic elegance meets modern streetwear. Dark, mysterious, and unapologetically bold.',
        'color' => '#8B0000',
        'glow' => '#DC143C',
        'gradient_start' => 'rgba(139, 0, 0, 0.1)',
        'gradient_end' => 'rgba(139, 0, 0, 0.05)',
    ],
    'love-hurts' => [
        'title' => 'Love Hurts',
        'subtitle' => 'Romantic rebellion. Soft hearts, sharp edges, and the courage to feel deeply.',
        'color' => '#E91E63',
        'glow' => '#F06292',
        'gradient_start' => 'rgba(233, 30, 99, 0.1)',
        'gradient_end' => 'rgba(233, 30, 99, 0.05)',
    ],
];

$theme = $themes[$collection_meta] ?? $themes['signature'];
?>

<style>
:root {
    --collection-color: <?php echo esc_attr($theme['color']); ?>;
    --collection-glow: <?php echo esc_attr($theme['glow']); ?>;
    --gradient-start: <?php echo esc_attr($theme['gradient_start']); ?>;
    --gradient-end: <?php echo esc_attr($theme['gradient_end']); ?>;
    --bg-dark: #000000;
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-blur: blur(20px);
}

.collection-page {
    background: var(--bg-dark);
    color: #fff;
    min-height: 100vh;
}

/* Ambient Background */
.collection-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(circle at 50% 10%, var(--gradient-start) 0%, transparent 50%),
        radial-gradient(circle at 50% 90%, var(--gradient-end) 0%, transparent 50%);
    z-index: -1;
    pointer-events: none;
}

/* Noise Texture */
.collection-page::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%' height='100%' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.04;
    pointer-events: none;
    z-index: 9999;
    mix-blend-mode: overlay;
}

.text-gradient {
    background: linear-gradient(135deg, #fff 0%, var(--collection-color) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Hero */
.collection-hero {
    padding: 180px 2rem 80px;
    text-align: center;
    position: relative;
}

.collection-hero::before {
    content: '';
    position: absolute;
    top: -50px;
    left: 50%;
    transform: translateX(-50%);
    width: 1px;
    height: 150px;
    background: linear-gradient(to bottom, transparent, var(--collection-color));
}

.collection-hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 5rem;
    margin-bottom: 1rem;
    animation: fadeUp 1s ease-out;
}

.collection-hero p {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.6);
    max-width: 600px;
    margin: 0 auto 3rem;
    animation: fadeUp 1s ease-out 0.2s backwards;
}

/* Filter Bar */
.filter-container {
    max-width: 1400px;
    margin: 0 auto 4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2rem;
    animation: fadeUp 1s ease-out 0.4s backwards;
}

.filter-group {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.filter-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.7);
    padding: 0.5rem 1.5rem;
    border-radius: 30px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.9rem;
}

.filter-btn:hover,
.filter-btn.active {
    border-color: var(--collection-color);
    color: var(--collection-color);
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
}

/* Product Grid */
.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 3rem;
    max-width: 1400px;
    margin: 0 auto 8rem;
    padding: 0 2rem;
}

.product-card {
    border-radius: 4px;
    overflow: hidden;
    transition: transform 0.4s ease;
    position: relative;
    cursor: pointer;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.product-card:hover {
    transform: translateY(-10px);
}

.card-image-wrapper {
    height: 400px;
    background: rgba(255, 255, 255, 0.02);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.card-image-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.card-image-wrapper .placeholder {
    font-size: 4rem;
}

.card-image-wrapper::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle, var(--gradient-start) 0%, transparent 70%);
    opacity: 0;
    transition: opacity 0.4s ease;
}

.product-card:hover .card-image-wrapper::after {
    opacity: 1;
}

.product-info {
    padding: 1.5rem;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
}

.product-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
}

.product-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.product-price {
    color: var(--collection-glow);
    font-size: 1.1rem;
    letter-spacing: 1px;
}

.product-badge {
    font-size: 0.8rem;
    color: #666;
    text-transform: uppercase;
}

.add-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(90deg, transparent, var(--gradient-start), transparent);
    border: 1px solid var(--collection-color);
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 2px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 600;
}

.add-btn:hover {
    background: var(--collection-color);
    color: #000;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive */
@media (max-width: 768px) {
    .collection-hero h1 {
        font-size: 3rem;
    }

    .filter-container {
        flex-direction: column;
        gap: 1rem;
        align-items: flex-start;
    }

    .products-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<div class="collection-page">
    <?php if ($collection_meta === 'black-rose') : ?>
    <!-- BLACK ROSE Immersive 3D Experience -->
    <div id="black-rose-immersive" class="immersive-3d-container" style="height: 100vh; width: 100%; position: relative;">
        <div class="immersive-loading" style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #c0c0c0;
            font-size: 1.2rem;
            z-index: 100;
        ">
            Loading BLACK ROSE experience...
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.getElementById('black-rose-immersive');
        const loading = container.querySelector('.immersive-loading');
        
        if (typeof BlackRoseExperience !== 'undefined') {
            // Initialize BLACK ROSE experience
            const experience = new BlackRoseExperience(container, {
                backgroundColor: 0x0d0d0d,
                fogDensity: 0.03,
                petalCount: 50,
                enableBloom: true
            });

            // Fetch products from WooCommerce
            fetch('<?php echo esc_url(admin_url('admin-ajax.php')); ?>?action=get_collection_products&collection=black-rose')
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data) {
                        // Load products into scene
                        experience.loadProducts(data.data);
                        loading.style.display = 'none';
                        experience.start();

                        // Handle product clicks
                        experience.setOnProductClick(function(product) {
                            // Redirect to product page or show modal
                            window.location.href = product.url;
                        });

                        // Handle product hover
                        experience.setOnProductHover(function(product) {
                            if (product) {
                                console.log('Hovering:', product.name);
                            }
                        });
                    } else {
                        loading.textContent = 'Failed to load products';
                    }
                })
                .catch(error => {
                    console.error('Error loading products:', error);
                    loading.textContent = 'Error loading experience';
                });
        } else {
            loading.textContent = 'THREE.js not loaded';
        }
    });
    </script>
    <?php endif; ?>

    <section class="collection-hero">
        <h1>
            <?php
            $title_parts = explode(' ', $theme['title']);
            if (count($title_parts) > 1) {
                echo esc_html($title_parts[0]) . '<span class="text-gradient">' . esc_html($title_parts[1]) . '</span>';
            } else {
                echo '<span class="text-gradient">' . esc_html($theme['title']) . '</span>';
            }
            ?>
        </h1>
        <p><?php echo esc_html($theme['subtitle']); ?></p>
    </section>

    <div class="filter-container">
        <div class="filter-group">
            <button class="filter-btn active" data-category="all">All</button>
            <?php
            // Get unique product categories for this collection
            $categories = get_terms([
                'taxonomy' => 'product_cat',
                'hide_empty' => true,
            ]);

            foreach ($categories as $category) {
                echo '<button class="filter-btn" data-category="' . esc_attr($category->slug) . '">';
                echo esc_html($category->name);
                echo '</button>';
            }
            ?>
        </div>
        <div style="font-size: 0.9rem; color: rgba(255,255,255,0.6);" id="productCount">
            <!-- Updated by JS -->
        </div>
    </div>

    <div class="products-grid" id="productsGrid">
        <?php
        // Query products for this collection
        $args = [
            'post_type' => 'product',
            'posts_per_page' => -1,
            'meta_query' => [
                [
                    'key' => '_skyyrose_collection',
                    'value' => $collection_meta,
                    'compare' => '='
                ]
            ],
            'orderby' => 'menu_order',
            'order' => 'ASC'
        ];

        $products = new WP_Query($args);

        if ($products->have_posts()) :
            while ($products->have_posts()) : $products->the_post();
                global $product;

                $badge = get_post_meta(get_the_ID(), '_product_badge', true);
                $categories = wp_get_post_terms(get_the_ID(), 'product_cat', ['fields' => 'slugs']);
                $cat_data = implode(' ', $categories);
        ?>
                <div class="product-card" data-categories="<?php echo esc_attr($cat_data); ?>" onclick="window.location.href='<?php echo esc_url(get_permalink()); ?>'">
                    <div class="card-image-wrapper">
                        <?php
                        if (has_post_thumbnail()) {
                            the_post_thumbnail('skyyrose-product');
                        } else {
                            // Fallback emoji based on product type
                            $type = wp_get_post_terms(get_the_ID(), 'product_cat', ['fields' => 'names']);
                            $emoji = '👔'; // Default
                            if (!empty($type)) {
                                $type_name = strtolower($type[0]);
                                if (strpos($type_name, 'dress') !== false) $emoji = '👗';
                                elseif (strpos($type_name, 'coat') !== false) $emoji = '🧥';
                                elseif (strpos($type_name, 'blazer') !== false) $emoji = '🕴️';
                            }
                            echo '<span class="placeholder">' . $emoji . '</span>';
                        }
                        ?>
                    </div>
                    <div class="product-info">
                        <h3 class="product-title"><?php the_title(); ?></h3>
                        <div class="product-meta">
                            <span class="product-price"><?php echo $product->get_price_html(); ?></span>
                            <?php if ($badge) : ?>
                                <span class="product-badge"><?php echo esc_html($badge); ?></span>
                            <?php endif; ?>
                        </div>
                        <button class="add-btn" onclick="event.stopPropagation(); addToCart(<?php echo esc_js($product->get_id()); ?>)">
                            Add to Cart
                        </button>
                    </div>
                </div>
        <?php
            endwhile;
            wp_reset_postdata();
        else :
        ?>
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem;">
                <p style="color: rgba(255,255,255,0.5);">No products found in this collection.</p>
            </div>
        <?php endif; ?>
    </div>
</div>

<script>
// Filter functionality
document.addEventListener('DOMContentLoaded', () => {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const products = document.querySelectorAll('.product-card');
    const productCount = document.getElementById('productCount');

    function updateCount() {
        const visible = Array.from(products).filter(p => p.style.display !== 'none').length;
        productCount.textContent = `${visible} PRODUCT${visible !== 1 ? 'S' : ''}`;
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const category = btn.dataset.category;

            // Filter products
            products.forEach(product => {
                if (category === 'all' || product.dataset.categories.includes(category)) {
                    product.style.display = '';
                } else {
                    product.style.display = 'none';
                }
            });

            updateCount();
        });
    });

    updateCount();
});

// Add to cart
function addToCart(productId) {
    const formData = new FormData();
    formData.append('action', 'woocommerce_ajax_add_to_cart');
    formData.append('product_id', productId);
    formData.append('quantity', 1);

    fetch('<?php echo esc_url(admin_url('admin-ajax.php')); ?>', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            // Update cart count or show notification
            alert('Added to cart!');
        }
    })
    .catch(error => console.error('Add to cart error:', error));
}
</script>

<?php get_footer(); ?>
