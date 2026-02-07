<?php
/**
 * Template Name: The Vault - Pre-Order
 * Description: Enhanced multi-collection pre-order page with countdown, live stats, and 3D viewers
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

get_header();

// Get launch date from customizer or default
$launch_date = get_theme_mod('skyyrose_vault_launch_date', date('Y-m-d H:i:s', strtotime('+30 days')));

// Get stock data
$vault_stock = skyyrose_get_total_vault_stock();

// Collection themes
$collection_themes = [
    'black-rose' => [
        'label' => 'BLACK ROSE',
        'color' => '#8B0000',
        'glow' => '#DC143C',
        'description' => 'Gothic elegance'
    ],
    'love-hurts' => [
        'label' => 'LOVE HURTS',
        'color' => '#E91E63',
        'glow' => '#F06292',
        'description' => 'Romantic castle'
    ],
    'signature' => [
        'label' => 'SIGNATURE',
        'color' => '#D4AF37',
        'glow' => '#FDD835',
        'description' => 'Oakland pride'
    ]
];
?>

<div class="vault-page">
    <!-- Hero Section with Countdown -->
    <section class="vault-hero">
        <div class="rotating-logo-container" id="logoContainer">
            <!-- Populated by JavaScript -->
        </div>

        <h1 class="vault-title">THE VAULT</h1>
        <p class="vault-tagline">Exclusive Access to ALL Collections</p>

        <!-- Countdown Timer -->
        <div class="countdown-timer" id="launchCountdown" data-launch="<?php echo esc_attr($launch_date); ?>">
            <div class="countdown-unit">
                <span class="count-value" id="days">00</span>
                <span class="count-label">DAYS</span>
            </div>
            <div class="countdown-unit">
                <span class="count-value" id="hours">00</span>
                <span class="count-label">HOURS</span>
            </div>
            <div class="countdown-unit">
                <span class="count-value" id="minutes">00</span>
                <span class="count-label">MINUTES</span>
            </div>
            <div class="countdown-unit">
                <span class="count-value" id="seconds">00</span>
                <span class="count-label">SECONDS</span>
            </div>
        </div>

        <p class="vault-subtitle text-mono">SECURE PRE-ORDER ACCESS GRANTED</p>

        <!-- Live Indicators -->
        <div class="vault-indicators">
            <div class="live-indicator">
                <span class="pulse-dot"></span>
                <span class="viewer-count" id="viewerCount">0</span>
                <span class="viewer-label">viewing</span>
            </div>

            <div class="stock-indicator">
                <div class="stock-bar">
                    <div class="stock-progress" style="width: <?php echo esc_attr($vault_stock['percent_sold']); ?>%"></div>
                </div>
                <p class="stock-text text-mono">
                    <?php echo esc_html($vault_stock['remaining']); ?> OF <?php echo esc_html($vault_stock['total']); ?> ITEMS REMAINING
                </p>
            </div>
        </div>
    </section>

    <!-- Collection Tabs -->
    <nav class="collection-tabs" role="tablist">
        <button class="tab-btn active" data-collection="all" role="tab" aria-selected="true">
            ALL COLLECTIONS
        </button>
        <?php foreach ($collection_themes as $slug => $theme): ?>
            <button class="tab-btn" data-collection="<?php echo esc_attr($slug); ?>" role="tab" aria-selected="false">
                <?php echo esc_html($theme['label']); ?>
            </button>
        <?php endforeach; ?>
    </nav>

    <!-- Products Grid -->
    <div class="vault-frame" id="vaultProducts">
        <?php
        // Query ALL vault products from all collections
        $vault_products = skyyrose_get_vault_products(['black-rose', 'love-hurts', 'signature']);

        if ($vault_products->have_posts()) :
            while ($vault_products->have_posts()) : $vault_products->the_post();
                global $product;

                // Get product meta
                $collection_slug = get_post_meta(get_the_ID(), '_skyyrose_collection', true) ?: 'signature';
                $collection_theme = $collection_themes[$collection_slug] ?? $collection_themes['signature'];
                $security_badge = get_post_meta(get_the_ID(), '_vault_badge', true) ?: 'ENCRYPTED';
                $model_url = get_post_meta(get_the_ID(), '_skyyrose_3d_model_url', true);
                $icon = get_post_meta(get_the_ID(), '_vault_icon', true) ?: '🔐';

                // Get variations if variable product
                $variations = [];
                if ($product->is_type('variable')) {
                    $available_variations = $product->get_available_variations();
                    foreach ($available_variations as $variation) {
                        $variations[] = [
                            'id' => $variation['variation_id'],
                            'attributes' => $variation['attributes'],
                            'display' => implode(' / ', array_map('wc_attribute_label', $variation['attributes']))
                        ];
                    }
                }
        ?>
                <div class="vault-card glass"
                     data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                     data-collection="<?php echo esc_attr($collection_slug); ?>">

                    <!-- Collection Badge -->
                    <span class="collection-badge" style="background: <?php echo esc_attr($collection_theme['color']); ?>">
                        <?php echo esc_html($collection_theme['label']); ?>
                    </span>

                    <span class="secure-badge text-mono"><?php echo esc_html($security_badge); ?></span>

                    <?php if ($model_url): ?>
                        <!-- 3D Product Viewer -->
                        <div class="vault-3d-viewer"
                             data-model="<?php echo esc_url($model_url); ?>"
                             data-name="<?php echo esc_attr(get_the_title()); ?>"
                             data-collection="<?php echo esc_attr($collection_slug); ?>">
                            <div class="loading-skeleton"></div>
                        </div>
                    <?php else: ?>
                        <!-- Fallback Image -->
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
                    <p class="item-description"><?php echo esc_html($collection_theme['description']); ?></p>

                    <div class="item-meta text-mono">
                        <span class="item-stock">
                            <?php
                            $stock = $product->get_stock_quantity();
                            echo $stock ? esc_html($stock) . ' IN STOCK' : 'IN STOCK';
                            ?>
                        </span>
                        <span class="item-price"><?php echo wp_kses_post($product->get_price_html()); ?></span>
                    </div>

                    <?php if (!empty($variations)): ?>
                        <!-- Variable Product Selection -->
                        <div class="product-variations">
                            <select class="variation-select" data-product-id="<?php echo esc_attr($product->get_id()); ?>">
                                <option value="">Select Options</option>
                                <?php foreach ($variations as $variation): ?>
                                    <option value="<?php echo esc_attr($variation['id']); ?>">
                                        <?php echo esc_html($variation['display']); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                    <?php endif; ?>

                    <?php if ($product->is_in_stock()): ?>
                        <button class="preorder-btn text-mono"
                                data-product-id="<?php echo esc_attr($product->get_id()); ?>"
                                data-collection="<?php echo esc_attr($collection_slug); ?>"
                                style="border-color: <?php echo esc_attr($collection_theme['glow']); ?>"
                                onclick="addToVaultCart(<?php echo esc_js($product->get_id()); ?>, '<?php echo esc_js($collection_slug); ?>')">
                            SECURE PRE-ORDER
                        </button>
                    <?php else: ?>
                        <button class="preorder-btn preorder-btn-disabled text-mono" disabled>
                            SOLD OUT
                        </button>
                    <?php endif; ?>
                </div>
        <?php
            endwhile;
            wp_reset_postdata();
        else:
        ?>
            <div class="vault-empty glass">
                <p class="text-mono">NO ASSETS AVAILABLE AT THIS TIME</p>
                <p>Check back soon for exclusive pre-order opportunities</p>
            </div>
        <?php endif; ?>
    </div>

    <!-- Testimonials Section -->
    <section class="vault-testimonials">
        <h2 class="section-title">VAULT MEMBER TESTIMONIALS</h2>
        <div class="testimonials-grid">
            <?php
            $testimonials = [
                [
                    'quote' => 'The Vault gives me early access to all collections. The 3D product viewers are incredible!',
                    'author' => 'Sarah M.',
                    'collection' => 'BLACK ROSE Member'
                ],
                [
                    'quote' => 'Pre-ordering from The Vault was seamless. Love the exclusive early access code.',
                    'author' => 'Marcus T.',
                    'collection' => 'SIGNATURE Member'
                ],
                [
                    'quote' => 'The quality and exclusivity make it worth it. SkyyRose delivers luxury.',
                    'author' => 'Elena R.',
                    'collection' => 'LOVE HURTS Member'
                ]
            ];

            foreach ($testimonials as $testimonial):
            ?>
                <div class="testimonial-card glass">
                    <p class="testimonial-quote">"<?php echo esc_html($testimonial['quote']); ?>"</p>
                    <div class="testimonial-author">
                        <strong><?php echo esc_html($testimonial['author']); ?></strong>
                        <span class="testimonial-collection"><?php echo esc_html($testimonial['collection']); ?></span>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </section>

    <footer class="vault-footer">
        <p class="text-mono">SECURE CONNECTION ESTABLISHED. SKYYROSE VAULT SYSTEM V3.0</p>
        <p class="footer-tagline">Where Love Meets Luxury</p>
    </footer>
</div>

<style>
<?php include get_template_directory() . '/assets/css/vault-enhanced.css'; ?>
</style>

<script>
// Vault data from WordPress
const vaultData = {
    ajaxUrl: '<?php echo esc_js(admin_url('admin-ajax.php')); ?>',
    cartUrl: '<?php echo esc_js(wc_get_cart_url()); ?>',
    nonce: '<?php echo esc_js(wp_create_nonce('skyyrose_vault')); ?>',
    launchDate: '<?php echo esc_js($launch_date); ?>',
    sessionId: Math.random().toString(36).substring(7),
    collections: <?php echo json_encode(array_keys($collection_themes)); ?>,
    themes: <?php echo json_encode($collection_themes); ?>
};

<?php include get_template_directory() . '/assets/js/vault-enhanced.js'; ?>
</script>

<?php get_footer(); ?>
