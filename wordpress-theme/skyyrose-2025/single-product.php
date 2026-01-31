<?php
/**
 * Single Product Template
 * WooCommerce product page with collection-specific theming
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();

// Get collection for theming
$collection = get_post_meta(get_the_ID(), '_skyyrose_collection', true) ?: 'signature';

$collection_themes = [
    'black-rose' => [
        'color' => '#8B0000',
        'name' => 'Black Rose',
        'gradient' => 'rgba(139, 0, 0, 0.1)',
    ],
    'love-hurts' => [
        'color' => '#B76E79',
        'name' => 'Love Hurts',
        'gradient' => 'rgba(183, 110, 121, 0.1)',
    ],
    'signature' => [
        'color' => '#D4AF37',
        'name' => 'Signature',
        'gradient' => 'rgba(212, 175, 55, 0.1)',
    ],
];

$theme = $collection_themes[$collection] ?? $collection_themes['signature'];

while (have_posts()) : the_post();
    global $product;

    // Get custom meta
    $care_instructions = get_post_meta(get_the_ID(), '_care_instructions', true);
    $fabric_composition = get_post_meta(get_the_ID(), '_fabric_composition', true);
    $badge = get_post_meta(get_the_ID(), '_product_badge', true);
?>

<style>
:root {
    --product-color: <?php echo esc_attr($theme['color']); ?>;
    --product-gradient: <?php echo esc_attr($theme['gradient']); ?>;
    --bg-dark: #000000;
}

.single-product-page {
    background: var(--bg-dark);
    color: #fff;
    min-height: 100vh;
    padding: 120px 0 80px;
}

.single-product-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background: radial-gradient(circle at 50% 20%, var(--product-gradient) 0%, transparent 60%);
    z-index: -1;
    pointer-events: none;
}

.product-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
}

.product-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6rem;
    margin-bottom: 6rem;
}

/* Gallery */
.product-gallery {
    position: sticky;
    top: 120px;
    height: fit-content;
}

.main-image {
    width: 100%;
    aspect-ratio: 1 / 1;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 1.5rem;
    position: relative;
}

.main-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.placeholder-icon {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 6rem;
    color: rgba(255, 255, 255, 0.1);
}

.thumbnail-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
}

.thumbnail {
    aspect-ratio: 1 / 1;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s ease;
}

.thumbnail:hover,
.thumbnail.active {
    border-color: var(--product-color);
    box-shadow: 0 0 15px var(--product-gradient);
}

.thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Product Info */
.product-info {
    animation: fadeUp 0.8s ease-out;
}

.collection-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 30px;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--product-color);
    margin-bottom: 1.5rem;
}

.product-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    margin-bottom: 1rem;
    line-height: 1.2;
}

.product-price {
    font-size: 2rem;
    color: var(--product-color);
    margin-bottom: 2rem;
    letter-spacing: 1px;
}

.product-description {
    font-size: 1.1rem;
    line-height: 1.8;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 3rem;
    padding-bottom: 3rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Add to Cart */
.add-to-cart-section {
    margin-bottom: 3rem;
}

.quantity-selector {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.quantity-label {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.quantity-input {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    overflow: hidden;
}

.qty-btn {
    width: 40px;
    height: 40px;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 1.2rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.qty-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.qty-number {
    width: 60px;
    text-align: center;
    border: none;
    background: transparent;
    color: #fff;
    font-size: 1rem;
}

.add-to-cart-btn {
    width: 100%;
    padding: 1.5rem;
    background: var(--product-color);
    color: #000;
    border: none;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
}

.add-to-cart-btn::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transform: translateX(-100%);
    transition: transform 0.6s ease;
}

.add-to-cart-btn:hover::before {
    transform: translateX(100%);
}

.add-to-cart-btn:hover {
    box-shadow: 0 0 30px var(--product-color);
    transform: translateY(-2px);
}

.add-to-cart-btn:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

.stock-status {
    margin-top: 1rem;
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
}

/* Product Details */
.product-details {
    margin-bottom: 3rem;
}

.detail-item {
    padding: 1.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-label {
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 0.5rem;
}

.detail-value {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.6;
}

/* Related Products */
.related-products {
    padding: 6rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.related-title {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    margin-bottom: 4rem;
}

.related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
}

.related-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.4s ease;
    cursor: pointer;
}

.related-card:hover {
    transform: translateY(-10px);
    border-color: var(--product-color);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.related-image {
    width: 100%;
    aspect-ratio: 1 / 1;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    margin-bottom: 1rem;
    overflow: hidden;
}

.related-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.related-card:hover .related-image img {
    transform: scale(1.1);
}

.related-name {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
}

.related-price {
    color: var(--product-color);
    font-size: 1rem;
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
@media (max-width: 1024px) {
    .product-grid {
        grid-template-columns: 1fr;
        gap: 3rem;
    }

    .product-gallery {
        position: relative;
        top: 0;
    }

    .product-title {
        font-size: 2.5rem;
    }
}

@media (max-width: 768px) {
    .thumbnail-grid {
        grid-template-columns: repeat(3, 1fr);
    }

    .product-title {
        font-size: 2rem;
    }

    .product-price {
        font-size: 1.5rem;
    }
}
</style>

<div class="single-product-page">
    <div class="product-container">
        <div class="product-grid">
            <!-- Product Gallery -->
            <div class="product-gallery">
                <div class="main-image" id="mainImage">
                    <?php
                    if (has_post_thumbnail()) {
                        the_post_thumbnail('skyyrose-hero');
                    } else {
                        echo '<div class="placeholder-icon">✦</div>';
                    }
                    ?>
                </div>

                <?php
                $attachment_ids = $product->get_gallery_image_ids();
                if (!empty($attachment_ids)) :
                ?>
                <div class="thumbnail-grid">
                    <?php
                    // Add featured image as first thumbnail
                    if (has_post_thumbnail()) :
                    ?>
                    <div class="thumbnail active" data-image="<?php echo esc_url(get_the_post_thumbnail_url(get_the_ID(), 'skyyrose-hero')); ?>">
                        <?php the_post_thumbnail('skyyrose-thumbnail'); ?>
                    </div>
                    <?php
                    endif;

                    // Add gallery images
                    foreach ($attachment_ids as $attachment_id) :
                        $image_url = wp_get_attachment_url($attachment_id);
                    ?>
                    <div class="thumbnail" data-image="<?php echo esc_url($image_url); ?>">
                        <?php echo wp_get_attachment_image($attachment_id, 'skyyrose-thumbnail'); ?>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
            </div>

            <!-- Product Info -->
            <div class="product-info">
                <div class="collection-badge">
                    <?php echo esc_html($theme['name']); ?> Collection
                    <?php if ($badge) : ?>
                        • <?php echo esc_html($badge); ?>
                    <?php endif; ?>
                </div>

                <h1 class="product-title"><?php the_title(); ?></h1>

                <div class="product-price">
                    <?php echo $product->get_price_html(); ?>
                </div>

                <div class="product-description">
                    <?php the_content(); ?>
                </div>

                <!-- Add to Cart -->
                <div class="add-to-cart-section">
                    <?php if ($product->is_in_stock()) : ?>
                        <div class="quantity-selector">
                            <span class="quantity-label">Quantity</span>
                            <div class="quantity-input">
                                <button class="qty-btn" onclick="updateQty(-1)">−</button>
                                <input type="number" class="qty-number" id="qtyInput" value="1" min="1" max="<?php echo esc_attr($product->get_stock_quantity() ?: 999); ?>">
                                <button class="qty-btn" onclick="updateQty(1)">+</button>
                            </div>
                        </div>

                        <button class="add-to-cart-btn" onclick="addToCart()">
                            Add to Cart
                        </button>

                        <div class="stock-status">
                            <?php
                            $stock_qty = $product->get_stock_quantity();
                            if ($stock_qty && $stock_qty <= 10) {
                                echo 'Only ' . esc_html($stock_qty) . ' left in stock';
                            } else {
                                echo 'In Stock';
                            }
                            ?>
                        </div>
                    <?php else : ?>
                        <button class="add-to-cart-btn" disabled>
                            Out of Stock
                        </button>
                    <?php endif; ?>
                </div>

                <!-- Product Details -->
                <div class="product-details">
                    <?php if ($fabric_composition) : ?>
                    <div class="detail-item">
                        <div class="detail-label">Fabric Composition</div>
                        <div class="detail-value"><?php echo esc_html($fabric_composition); ?></div>
                    </div>
                    <?php endif; ?>

                    <?php if ($care_instructions) : ?>
                    <div class="detail-item">
                        <div class="detail-label">Care Instructions</div>
                        <div class="detail-value"><?php echo esc_html($care_instructions); ?></div>
                    </div>
                    <?php endif; ?>

                    <div class="detail-item">
                        <div class="detail-label">SKU</div>
                        <div class="detail-value"><?php echo esc_html($product->get_sku() ?: 'N/A'); ?></div>
                    </div>

                    <?php
                    $categories = get_the_terms(get_the_ID(), 'product_cat');
                    if ($categories && !is_wp_error($categories)) :
                    ?>
                    <div class="detail-item">
                        <div class="detail-label">Category</div>
                        <div class="detail-value">
                            <?php echo esc_html(implode(', ', wp_list_pluck($categories, 'name'))); ?>
                        </div>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>

        <!-- Related Products -->
        <?php
        $related_products = wc_get_related_products($product->get_id(), 3);
        if (!empty($related_products)) :
        ?>
        <div class="related-products">
            <h2 class="related-title">You May Also Like</h2>
            <div class="related-grid">
                <?php
                foreach ($related_products as $related_id) :
                    $related_product = wc_get_product($related_id);
                ?>
                <div class="related-card" onclick="window.location.href='<?php echo esc_url(get_permalink($related_id)); ?>'">
                    <div class="related-image">
                        <?php echo get_the_post_thumbnail($related_id, 'skyyrose-product'); ?>
                    </div>
                    <h3 class="related-name"><?php echo esc_html($related_product->get_name()); ?></h3>
                    <div class="related-price"><?php echo $related_product->get_price_html(); ?></div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>
    </div>
</div>

<script>
// Thumbnail gallery - using safe DOM manipulation
document.querySelectorAll('.thumbnail').forEach(thumb => {
    thumb.addEventListener('click', function() {
        const imageUrl = this.dataset.image;
        const mainImage = document.getElementById('mainImage');

        // Update active state
        document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        // Update main image safely
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = 'Product image';
        mainImage.innerHTML = '';
        mainImage.appendChild(img);
    });
});

// Quantity controls
function updateQty(delta) {
    const input = document.getElementById('qtyInput');
    const current = parseInt(input.value) || 1;
    const min = parseInt(input.min) || 1;
    const max = parseInt(input.max) || 999;
    const newValue = Math.max(min, Math.min(max, current + delta));
    input.value = newValue;
}

// Add to cart
function addToCart() {
    const button = event.target;
    const qty = document.getElementById('qtyInput').value;

    button.disabled = true;
    button.textContent = 'Adding...';

    const formData = new FormData();
    formData.append('action', 'woocommerce_ajax_add_to_cart');
    formData.append('product_id', <?php echo esc_js($product->get_id()); ?>);
    formData.append('quantity', qty);

    fetch('<?php echo esc_url(admin_url('admin-ajax.php')); ?>', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.error) {
            button.textContent = 'Added! ✓';
            setTimeout(() => {
                window.location.href = '<?php echo esc_url(wc_get_cart_url()); ?>';
            }, 800);
        } else {
            button.textContent = 'Error';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Add to Cart';
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.disabled = false;
        button.textContent = 'Add to Cart';
    });
}
</script>

<?php
endwhile;
?>

<?php get_footer(); ?>
