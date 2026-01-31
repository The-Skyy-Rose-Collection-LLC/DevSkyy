<?php
/**
 * Template Name: The Vault - Pre-Order
 * Description: Futuristic pre-order page with rotating collection logos
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

get_header();
?>

<div class="vault-page">
    <!-- Rotating Logo Header -->
    <div class="vault-header">
        <div class="rotating-logo-container" id="logoContainer">
            <!-- Populated by JavaScript -->
        </div>
        <h1 class="vault-title">THE VAULT</h1>
        <p class="vault-subtitle text-mono">SECURE PRE-ORDER ACCESS GRANTED</p>
    </div>

    <!-- Products Grid -->
    <div class="vault-frame">
        <?php
        // Query WooCommerce products with 'pre-order' tag or custom meta
        $args = [
            'post_type' => 'product',
            'posts_per_page' => -1,
            'meta_query' => [
                [
                    'key' => '_vault_preorder',
                    'value' => '1',
                    'compare' => '='
                ]
            ],
            'orderby' => 'menu_order',
            'order' => 'ASC'
        ];

        $vault_products = new WP_Query($args);

        if ($vault_products->have_posts()) :
            while ($vault_products->have_posts()) : $vault_products->the_post();
                global $product;

                // Get custom meta
                $security_badge = get_post_meta(get_the_ID(), '_vault_badge', true) ?: 'ENCRYPTED';
                $quantity_limit = get_post_meta(get_the_ID(), '_vault_quantity_limit', true);
                $quantity_sold = get_post_meta(get_the_ID(), '_vault_quantity_sold', true) ?: 0;
                $icon = get_post_meta(get_the_ID(), '_vault_icon', true) ?: '🔐';
                $model_url = get_post_meta(get_the_ID(), '_skyyrose_3d_model_url', true);

                // Calculate quantity display
                if ($quantity_limit) {
                    $qty_display = "QTY: {$quantity_sold}/{$quantity_limit}";
                } else {
                    $qty_display = "QTY: UNLIMITED";
                }
        ?>
                <div class="vault-card glass" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                    <span class="secure-badge text-mono"><?php echo esc_html($security_badge); ?></span>

                    <?php if ($model_url) : ?>
                        <!-- 3D Model Viewer -->
                        <div class="item-visual item-visual-3d" data-model="<?php echo esc_url($model_url); ?>">
                            <div class="loading-skeleton"></div>
                        </div>
                    <?php else : ?>
                        <!-- Fallback Icon/Image -->
                        <div class="item-visual">
                            <?php
                            if (has_post_thumbnail()) {
                                the_post_thumbnail('skyyrose-product', ['class' => 'vault-product-img']);
                            } else {
                                echo '<span class="vault-icon">' . esc_html($icon) . '</span>';
                            }
                            ?>
                        </div>
                    <?php endif; ?>

                    <h3 class="item-name"><?php the_title(); ?></h3>

                    <div class="item-meta text-mono">
                        <span><?php echo esc_html($qty_display); ?></span>
                        <span><?php echo $product->get_price_html(); ?></span>
                    </div>

                    <?php if ($product->is_in_stock()) : ?>
                        <button class="preorder-btn text-mono"
                                data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                                onclick="addToCart(<?php echo esc_js($product->get_id()); ?>)">
                            SECURE ASSET
                        </button>
                    <?php else : ?>
                        <button class="preorder-btn preorder-btn-disabled text-mono" disabled>
                            SOLD OUT
                        </button>
                    <?php endif; ?>
                </div>
        <?php
            endwhile;
            wp_reset_postdata();
        else :
        ?>
            <div class="vault-empty glass">
                <p class="text-mono">NO ASSETS AVAILABLE AT THIS TIME</p>
            </div>
        <?php endif; ?>
    </div>

    <footer class="vault-footer">
        <p class="text-mono">SECURE CONNECTION ESTABLISHED. SKYYROSE VAULT SYSTEM V2.0</p>
    </footer>
</div>

<style>
:root {
    --neon-green: #00ff41;
    --neon-glow: #80ff9a;
    --bg-dark: #050505;
    --glass-border-vault: rgba(0, 255, 65, 0.2);
    --glass-bg-vault: rgba(0, 20, 5, 0.6);
    --glass-blur-vault: blur(20px);
}

/* Override body background for vault page */
.vault-page {
    min-height: 100vh;
    background: var(--bg-dark);
    color: #fff;
    padding-bottom: 4rem;
}

/* Tech Grid Background */
.vault-page::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        linear-gradient(rgba(0, 255, 65, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 65, 0.05) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: -1;
    pointer-events: none;
}

.vault-page::after {
    content: '';
    position: fixed;
    inset: 0;
    background: radial-gradient(circle at 50% 50%, transparent 0%, #000 90%);
    z-index: -1;
    pointer-events: none;
}

.text-mono {
    font-family: 'Share Tech Mono', 'Courier New', monospace;
}

/* Header */
.vault-header {
    padding: 150px 2rem 60px;
    text-align: center;
}

.rotating-logo-container {
    height: 120px;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 30px;
    perspective: 1000px;
    position: relative;
}

.collection-logo {
    position: absolute;
    opacity: 0;
    transform: translateY(20px) rotateX(-20deg);
    transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    filter: blur(10px);
}

.collection-logo.active {
    opacity: 1;
    transform: translateY(0) rotateX(0deg);
    filter: blur(0);
}

.collection-logo.exit {
    opacity: 0;
    transform: translateY(-20px) rotateX(20deg);
    filter: blur(10px);
}

.collection-logo img {
    max-height: 100px;
    width: auto;
}

.vault-title {
    font-family: 'Playfair Display', serif;
    font-size: 4rem;
    margin-bottom: 1rem;
    color: #fff;
}

.vault-subtitle {
    color: var(--neon-green);
    letter-spacing: 2px;
    font-size: 1.2rem;
}

/* Products Grid */
.vault-frame {
    max-width: 1200px;
    margin: 0 auto 6rem;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    padding: 0 2rem;
}

.vault-card {
    position: relative;
    padding: 2rem;
    background: var(--glass-bg-vault);
    backdrop-filter: var(--glass-blur-vault);
    border: 1px solid var(--glass-border-vault);
    border-radius: 8px;
    transition: all 0.3s ease;
}

.vault-card:hover {
    border-color: var(--neon-green);
    box-shadow: 0 0 30px rgba(0, 255, 65, 0.1);
}

.secure-badge {
    position: absolute;
    top: 1rem;
    right: 1rem;
    border: 1px solid var(--neon-green);
    color: var(--neon-green);
    padding: 0.2rem 0.5rem;
    font-size: 0.7rem;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 2px;
}

.item-visual {
    height: 250px;
    background: rgba(0, 255, 65, 0.02);
    border: 1px dashed rgba(0, 255, 65, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    margin-bottom: 1.5rem;
    border-radius: 4px;
    overflow: hidden;
}

.item-visual-3d {
    border: none;
    background: #000;
}

.vault-product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.vault-icon {
    font-size: 4rem;
}

.item-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: #fff;
}

.item-meta {
    display: flex;
    justify-content: space-between;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
}

.preorder-btn {
    width: 100%;
    padding: 1rem;
    background: var(--neon-green);
    color: #000;
    border: none;
    font-weight: bold;
    letter-spacing: 1px;
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 4px;
    font-size: 0.9rem;
}

.preorder-btn:hover {
    box-shadow: 0 0 20px var(--neon-green);
    transform: scale(1.02);
}

.preorder-btn-disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

.preorder-btn-disabled:hover {
    transform: none;
    box-shadow: none;
}

.vault-empty {
    grid-column: 1 / -1;
    text-align: center;
    padding: 4rem;
    background: var(--glass-bg-vault);
    border: 1px solid var(--glass-border-vault);
}

/* Footer */
.vault-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    padding: 4rem 2rem;
    color: #444;
}

/* Responsive */
@media (max-width: 768px) {
    .vault-title {
        font-size: 2.5rem;
    }

    .vault-subtitle {
        font-size: 1rem;
    }

    .vault-frame {
        grid-template-columns: 1fr;
        padding: 0 1rem;
    }

    .rotating-logo-container {
        height: 80px;
    }

    .collection-logo img {
        max-height: 60px;
    }
}
</style>

<script>
// Rotating Collection Logos
(function() {
    const logos = <?php
        // Get collection logos from WordPress uploads or assets
        echo json_encode([
            [
                'name' => 'BLACK ROSE',
                'img' => get_template_directory_uri() . '/assets/images/BLACK-Rose-LOGO.PNG',
                'theme' => 'theme-black-rose'
            ],
            [
                'name' => 'LOVE HURTS',
                'img' => get_template_directory_uri() . '/assets/images/Love-Hurts-LOGO.PNG',
                'theme' => 'theme-love-hurts'
            ],
            [
                'name' => 'SIGNATURE',
                'img' => get_template_directory_uri() . '/assets/images/Signature-LOGO.PNG',
                'theme' => 'theme-signature'
            ]
        ]);
    ?>;

    const container = document.getElementById('logoContainer');
    let currentIndex = 0;

    function renderLogos() {
        container.innerHTML = '';
        logos.forEach((logo, index) => {
            const el = document.createElement('div');
            el.className = 'collection-logo ' + logo.theme;
            if (index === 0) el.classList.add('active');
            
            const img = document.createElement('img');
            img.src = logo.img;
            img.alt = logo.name;
            img.onerror = function() { this.style.display = 'none'; };
            
            el.appendChild(img);
            container.appendChild(el);
        });
    }

    function rotateLogo() {
        const children = container.children;
        if (children.length === 0) return;

        const current = children[currentIndex];
        const nextIndex = (currentIndex + 1) % logos.length;
        const next = children[nextIndex];

        current.classList.remove('active');
        current.classList.add('exit');

        setTimeout(() => {
            current.classList.remove('exit');
        }, 800);

        next.classList.add('active');
        currentIndex = nextIndex;
    }

    renderLogos();
    setInterval(rotateLogo, 3000);
})();

// Add to Cart Handler
function addToCart(productId) {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'PROCESSING...';

    // Use WordPress AJAX
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
        if (data.error) {
            button.textContent = 'ERROR';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'SECURE ASSET';
            }, 2000);
        } else {
            button.textContent = 'SECURED ✓';
            setTimeout(() => {
                window.location.href = '<?php echo esc_url(wc_get_cart_url()); ?>';
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Add to cart error:', error);
        button.disabled = false;
        button.textContent = 'SECURE ASSET';
    });
}

// Initialize 3D viewers for products with models
document.addEventListener('DOMContentLoaded', () => {
    const viewers = document.querySelectorAll('.item-visual-3d[data-model]');
    viewers.forEach(viewer => {
        const modelUrl = viewer.dataset.model;
        if (modelUrl && window.initSkyyRose3DViewer) {
            window.initSkyyRose3DViewer(viewer, modelUrl);
        }
    });
});
</script>

<?php get_footer(); ?>
