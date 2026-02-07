<?php
/**
 * Template Name: Collection - Love Hurts
 * Description: Romantic rebellion collection - Full product catalog
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

get_header();

$collection_slug = 'love-hurts';
$collection_data = [
    'title' => 'Love Hurts',
    'subtitle' => 'Romantic rebellion. Soft hearts, sharp edges, and the courage to feel deeply.',
    'color' => '#B76E79',
    'glow' => '#F06292',
    'gradient_start' => 'rgba(183, 110, 121, 0.1)',
    'gradient_end' => 'rgba(183, 110, 121, 0.05)',
];
?>

<style>
:root {
    --collection-color: <?php echo esc_attr($collection_data['color']); ?>;
    --collection-glow: <?php echo esc_attr($collection_data['glow']); ?>;
    --gradient-start: <?php echo esc_attr($collection_data['gradient_start']); ?>;
    --gradient-end: <?php echo esc_attr($collection_data['gradient_end']); ?>;
}
</style>

<div class="collection-catalog-page" style="background: #000; color: #fff; min-height: 100vh; padding: 100px 0;">

    <!-- Collection Header -->
    <section class="collection-header" style="text-align: center; padding: 80px 2rem;">
        <h1 style="font-family: 'Playfair Display', serif; font-size: 4rem; margin-bottom: 1rem;">
            Love <span style="color: var(--collection-glow);">Hurts</span>
        </h1>
        <p style="font-size: 1.2rem; color: rgba(255,255,255,0.7); max-width: 700px; margin: 0 auto 3rem;">
            <?php echo esc_html($collection_data['subtitle']); ?>
        </p>
        <div style="height: 1px; width: 100px; background: var(--collection-color); margin: 0 auto;"></div>
    </section>

    <!-- Filters -->
    <div class="collection-filters" style="max-width: 1400px; margin: 0 auto 4rem; padding: 0 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div class="filter-buttons" style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <button class="filter-btn active" data-category="all" style="
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.2);
                    color: #fff;
                    padding: 0.75rem 1.5rem;
                    border-radius: 30px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                ">All Products</button>
                <?php
                $categories = get_terms([
                    'taxonomy' => 'product_cat',
                    'hide_empty' => true,
                ]);
                foreach ($categories as $cat) :
                ?>
                <button class="filter-btn" data-category="<?php echo esc_attr($cat->slug); ?>" style="
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.2);
                    color: #fff;
                    padding: 0.75rem 1.5rem;
                    border-radius: 30px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                "><?php echo esc_html($cat->name); ?></button>
                <?php endforeach; ?>
            </div>
            <div id="productCount" style="color: rgba(255,255,255,0.6); font-size: 0.9rem;"></div>
        </div>
    </div>

    <!-- Products Grid -->
    <div class="products-grid" id="productsGrid" style="
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 2rem;
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 2rem;
    ">
        <?php
        $args = [
            'post_type' => 'product',
            'posts_per_page' => -1,
            'meta_query' => [
                [
                    'key' => '_skyyrose_collection',
                    'value' => $collection_slug,
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
                $categories = wp_get_post_terms(get_the_ID(), 'product_cat', ['fields' => 'slugs']);
                $cat_data = implode(' ', $categories);
        ?>
        <div class="product-card" data-categories="<?php echo esc_attr($cat_data); ?>" style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.3s ease;
            cursor: pointer;
        " onclick="window.location.href='<?php echo esc_url(get_permalink()); ?>'">
            <div style="height: 400px; background: rgba(0,0,0,0.5); overflow: hidden;">
                <?php
                if (has_post_thumbnail()) {
                    the_post_thumbnail('large', ['style' => 'width: 100%; height: 100%; object-fit: cover;']);
                } else {
                    echo '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 4rem;">💕</div>';
                }
                ?>
            </div>
            <div style="padding: 1.5rem;">
                <h3 style="font-family: 'Playfair Display', serif; font-size: 1.3rem; margin-bottom: 0.5rem;">
                    <?php the_title(); ?>
                </h3>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <span style="color: var(--collection-glow); font-size: 1.1rem;">
                        <?php echo $product->get_price_html(); ?>
                    </span>
                    <?php
                    $badge = get_post_meta(get_the_ID(), '_product_badge', true);
                    if ($badge) :
                    ?>
                    <span style="font-size: 0.8rem; color: #999; text-transform: uppercase;">
                        <?php echo esc_html($badge); ?>
                    </span>
                    <?php endif; ?>
                </div>
                <button class="add-to-cart-btn" onclick="event.stopPropagation(); addToCart(<?php echo esc_js($product->get_id()); ?>)" style="
                    width: 100%;
                    padding: 1rem;
                    background: var(--collection-color);
                    border: none;
                    color: #fff;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: 600;
                ">Add to Cart</button>
            </div>
        </div>
        <?php
            endwhile;
            wp_reset_postdata();
        else :
        ?>
        <div style="grid-column: 1 / -1; text-align: center; padding: 4rem;">
            <p style="color: rgba(255,255,255,0.5);">No products found in the Love Hurts collection yet.</p>
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
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            btn.style.borderColor = 'var(--collection-color)';
            btn.style.color = 'var(--collection-color)';

            const category = btn.dataset.category;

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

    // Hover effects
    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px)';
            card.style.borderColor = 'var(--collection-color)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.borderColor = 'rgba(255,255,255,0.1)';
        });
    });

    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            btn.style.boxShadow = '0 0 20px var(--collection-color)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.boxShadow = 'none';
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
            alert('Added to cart! 💕');
            // Trigger cart update event
            jQuery(document.body).trigger('wc_fragment_refresh');
        }
    })
    .catch(error => console.error('Error:', error));
}
</script>

<?php get_footer(); ?>
