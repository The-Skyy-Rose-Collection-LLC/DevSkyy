<?php
/**
 * SkyyRose Single Product Page
 * 
 * WooCommerce template override. Detects collection category and
 * loads the appropriate collection-skinned product template.
 * Falls back to BLACK ROSE aesthetic for uncategorized products.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 * 
 * @see https://woocommerce.com/document/template-structure/
 */

defined('ABSPATH') || exit;

global $product;

$collection = skyyrose_get_product_collection();
$config     = skyyrose_collection_config($collection);
$meta       = skyyrose_get_product_meta();
$related    = skyyrose_get_collection_products(get_the_ID(), 4);

// Product data
$gallery_ids  = $product->get_gallery_image_ids();
$main_image   = wp_get_attachment_url($product->get_image_id());
$is_variable  = $product->is_type('variable');
$price_html   = $product->get_price_html();
$stock_status = $product->get_stock_status();
$sku          = $product->get_sku();

// Breadcrumb data
$shop_url     = get_permalink(wc_get_page_id('shop'));
$categories   = get_the_terms(get_the_ID(), 'product_cat');
$cat_link     = '';
$cat_name     = $config['label'];
if ($categories && !is_wp_error($categories)) {
    $cat_link = get_term_link($categories[0]);
    $cat_name = $categories[0]->name;
}

get_header('shop');
?>

<style>
:root {
    --sr-accent: <?php echo esc_attr($config['accent']); ?>;
    --sr-accent-rgb: <?php echo esc_attr($config['accent_rgb']); ?>;
    --sr-bg: <?php echo esc_attr($config['bg']); ?>;
    --sr-bg-alt: <?php echo esc_attr($config['bg_alt']); ?>;
    --sr-text: <?php echo esc_attr($config['text']); ?>;
    --sr-dim: <?php echo esc_attr($config['dim']); ?>;
    --sr-gradient: <?php echo esc_attr($config['gradient']); ?>;
    --sr-cta-color: <?php echo esc_attr($config['cta_color']); ?>;
}
</style>

<main id="product-<?php the_ID(); ?>" <?php wc_product_class('sr-product', $product); ?>
      data-collection="<?php echo esc_attr($collection); ?>">

    <!-- ═══ BREADCRUMB ═══ -->
    <nav class="sr-breadcrumb" aria-label="Breadcrumb">
        <div class="sr-container">
            <a href="<?php echo esc_url(home_url('/')); ?>">SkyyRose</a>
            <span class="sr-bc-sep">/</span>
            <a href="<?php echo esc_url($shop_url); ?>">Shop</a>
            <span class="sr-bc-sep">/</span>
            <?php if ($cat_link && !is_wp_error($cat_link)) : ?>
                <a href="<?php echo esc_url($cat_link); ?>"><?php echo esc_html($cat_name); ?></a>
                <span class="sr-bc-sep">/</span>
            <?php endif; ?>
            <span class="sr-bc-current"><?php the_title(); ?></span>
        </div>
    </nav>

    <!-- ═══ PRODUCT HERO — Split Layout ═══ -->
    <section class="sr-hero">
        <div class="sr-container sr-hero-grid">

            <!-- Gallery Column -->
            <div class="sr-gallery" data-gallery>
                <!-- Main Image -->
                <div class="sr-gallery-main">
                    <?php if ($meta['limited']) : ?>
                        <span class="sr-badge-limited">Limited Edition<?php 
                            echo $meta['edition_of'] ? ' — ' . intval($meta['edition_of']) . ' pieces' : ''; 
                        ?></span>
                    <?php endif; ?>

                    <span class="sr-badge-collection"><?php echo esc_html($config['label']); ?></span>

                    <?php if ($main_image) : ?>
                        <img src="<?php echo esc_url($main_image); ?>" 
                             alt="<?php echo esc_attr($product->get_name()); ?>"
                             class="sr-gallery-img sr-gallery-active"
                             id="srMainImg"
                             loading="eager">
                    <?php else : ?>
                        <div class="sr-gallery-placeholder">
                            <span class="sr-gallery-letter"><?php echo esc_html(mb_substr($product->get_name(), 0, 1)); ?></span>
                        </div>
                    <?php endif; ?>

                    <!-- Zoom overlay -->
                    <div class="sr-gallery-zoom" id="srZoom" aria-hidden="true"></div>
                </div>

                <!-- Thumbnails -->
                <?php if (!empty($gallery_ids)) : ?>
                    <div class="sr-gallery-thumbs">
                        <?php if ($main_image) : ?>
                            <button class="sr-thumb sr-thumb-active" data-img="<?php echo esc_url($main_image); ?>">
                                <img src="<?php echo esc_url($main_image); ?>" alt="" loading="lazy">
                            </button>
                        <?php endif; ?>
                        <?php foreach ($gallery_ids as $gid) : 
                            $gurl = wp_get_attachment_url($gid);
                            if (!$gurl) continue;
                        ?>
                            <button class="sr-thumb" data-img="<?php echo esc_url($gurl); ?>">
                                <img src="<?php echo esc_url($gurl); ?>" alt="" loading="lazy">
                            </button>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </div>

            <!-- Info Column -->
            <div class="sr-info">
                <div class="sr-info-inner">
                    <!-- Collection badge -->
                    <p class="sr-info-collection"><?php echo esc_html($config['label']); ?> COLLECTION</p>

                    <!-- Product name -->
                    <h1 class="sr-info-name"><?php the_title(); ?></h1>

                    <!-- Price -->
                    <div class="sr-info-price"><?php echo $price_html; ?></div>

                    <!-- Short description -->
                    <?php if ($product->get_short_description()) : ?>
                        <div class="sr-info-desc">
                            <?php echo wp_kses_post($product->get_short_description()); ?>
                        </div>
                    <?php endif; ?>

                    <!-- Spec table -->
                    <?php if ($meta['material'] || $meta['fit'] || $meta['detail']) : ?>
                        <div class="sr-info-specs">
                            <?php if ($meta['material']) : ?>
                                <div class="sr-spec">
                                    <span class="sr-spec-label">Material</span>
                                    <span class="sr-spec-value"><?php echo esc_html($meta['material']); ?></span>
                                </div>
                            <?php endif; ?>
                            <?php if ($meta['fit']) : ?>
                                <div class="sr-spec">
                                    <span class="sr-spec-label">Fit</span>
                                    <span class="sr-spec-value"><?php echo esc_html($meta['fit']); ?></span>
                                </div>
                            <?php endif; ?>
                            <?php if ($meta['detail']) : ?>
                                <div class="sr-spec">
                                    <span class="sr-spec-label">Detail</span>
                                    <span class="sr-spec-value"><?php echo esc_html($meta['detail']); ?></span>
                                </div>
                            <?php endif; ?>
                            <?php if ($sku) : ?>
                                <div class="sr-spec">
                                    <span class="sr-spec-label">SKU</span>
                                    <span class="sr-spec-value"><?php echo esc_html($sku); ?></span>
                                </div>
                            <?php endif; ?>
                        </div>
                    <?php endif; ?>

                    <!-- Add to Cart Form -->
                    <div class="sr-atc-wrap">
                        <?php
                        // Remove default WC hooks — we control the layout
                        remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_add_to_cart', 30);
                        
                        // Output the appropriate add-to-cart template
                        if ($is_variable) {
                            woocommerce_variable_add_to_cart();
                        } else {
                            woocommerce_simple_add_to_cart();
                        }
                        ?>
                    </div>

                    <!-- Stock status -->
                    <div class="sr-stock sr-stock-<?php echo esc_attr($stock_status); ?>">
                        <?php if ($stock_status === 'instock') : ?>
                            <span class="sr-stock-dot"></span> In Stock — Ready to Ship
                        <?php elseif ($stock_status === 'onbackorder') : ?>
                            <span class="sr-stock-dot"></span> Pre-Order — Ships Spring 2026
                        <?php else : ?>
                            <span class="sr-stock-dot"></span> Sold Out
                        <?php endif; ?>
                    </div>

                    <!-- Trust signals -->
                    <div class="sr-trust">
                        <div class="sr-trust-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                            <span>Secure Checkout</span>
                        </div>
                        <div class="sr-trust-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                            <span>Free Shipping $150+</span>
                        </div>
                        <div class="sr-trust-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12a9 9 0 1018 0 9 9 0 00-18 0z"/><path d="M12 8v4l3 3"/></svg>
                            <span>30-Day Returns</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ═══ PRODUCT DETAILS ACCORDION ═══ -->
    <section class="sr-details">
        <div class="sr-container">
            <div class="sr-details-grid">

                <!-- Full Description -->
                <?php if ($product->get_description()) : ?>
                    <div class="sr-accordion" data-accordion>
                        <button class="sr-accordion-trigger" aria-expanded="true">
                            <span>Description</span>
                            <span class="sr-accordion-icon">−</span>
                        </button>
                        <div class="sr-accordion-content sr-accordion-open">
                            <?php echo wp_kses_post($product->get_description()); ?>
                        </div>
                    </div>
                <?php endif; ?>

                <!-- Materials & Construction -->
                <?php if ($meta['material'] || $meta['care'] || $meta['made_in']) : ?>
                    <div class="sr-accordion" data-accordion>
                        <button class="sr-accordion-trigger" aria-expanded="false">
                            <span>Materials &amp; Care</span>
                            <span class="sr-accordion-icon">+</span>
                        </button>
                        <div class="sr-accordion-content">
                            <?php if ($meta['material']) : ?>
                                <p><strong>Material:</strong> <?php echo esc_html($meta['material']); ?></p>
                            <?php endif; ?>
                            <?php if ($meta['made_in']) : ?>
                                <p><strong>Made in:</strong> <?php echo esc_html($meta['made_in']); ?></p>
                            <?php endif; ?>
                            <?php if ($meta['care']) : ?>
                                <p><strong>Care:</strong> <?php echo esc_html($meta['care']); ?></p>
                            <?php endif; ?>
                        </div>
                    </div>
                <?php endif; ?>

                <!-- Size Guide -->
                <div class="sr-accordion" data-accordion>
                    <button class="sr-accordion-trigger" aria-expanded="false">
                        <span>Size Guide</span>
                        <span class="sr-accordion-icon">+</span>
                    </button>
                    <div class="sr-accordion-content">
                        <p>All SkyyRose pieces are designed gender-neutral. We recommend ordering your usual size for a standard fit, or sizing up for an oversized look.</p>
                        <p>Need help? Email <a href="mailto:corey@skyyrose.co">corey@skyyrose.co</a> with your height and weight for a personal recommendation.</p>
                    </div>
                </div>

                <!-- Shipping & Returns -->
                <div class="sr-accordion" data-accordion>
                    <button class="sr-accordion-trigger" aria-expanded="false">
                        <span>Shipping &amp; Returns</span>
                        <span class="sr-accordion-icon">+</span>
                    </button>
                    <div class="sr-accordion-content">
                        <p>Free shipping on orders over $150. Standard delivery 5-7 business days. Expedited options available at checkout.</p>
                        <p>30-day return policy on unworn items with original tags. Pre-order items ship on the announced date.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ═══ COLLECTION PRODUCTS ═══ -->
    <?php if (!empty($related)) : ?>
        <section class="sr-related">
            <div class="sr-container">
                <div class="sr-related-head">
                    <h2 class="sr-related-title">More from <?php echo esc_html($config['label']); ?></h2>
                    <?php if ($cat_link && !is_wp_error($cat_link)) : ?>
                        <a href="<?php echo esc_url($cat_link); ?>" class="sr-related-link">
                            View Full Collection →
                        </a>
                    <?php endif; ?>
                </div>
                <div class="sr-related-grid">
                    <?php foreach ($related as $rel_product) : 
                        $rel_img = wp_get_attachment_url($rel_product->get_image_id());
                        $rel_link = get_permalink($rel_product->get_id());
                    ?>
                        <a href="<?php echo esc_url($rel_link); ?>" class="sr-related-card">
                            <div class="sr-related-img">
                                <?php if ($rel_img) : ?>
                                    <img src="<?php echo esc_url($rel_img); ?>" 
                                         alt="<?php echo esc_attr($rel_product->get_name()); ?>"
                                         loading="lazy">
                                <?php else : ?>
                                    <span class="sr-related-letter"><?php echo esc_html(mb_substr($rel_product->get_name(), 0, 1)); ?></span>
                                <?php endif; ?>
                                <span class="sr-related-badge"><?php echo esc_html($config['label']); ?></span>
                                <div class="sr-related-hov"><span>View Piece</span></div>
                            </div>
                            <div class="sr-related-body">
                                <h3 class="sr-related-name"><?php echo esc_html($rel_product->get_name()); ?></h3>
                                <span class="sr-related-price"><?php echo $rel_product->get_price_html(); ?></span>
                            </div>
                        </a>
                    <?php endforeach; ?>
                </div>
            </div>
        </section>
    <?php endif; ?>

    <!-- ═══ COLLECTION CTA BANNER ═══ -->
    <section class="sr-cta-banner">
        <div class="sr-container sr-cta-inner">
            <div class="sr-cta-text">
                <p class="sr-cta-eye"><?php echo esc_html($config['badge_text']); ?></p>
                <h2 class="sr-cta-title"><?php echo esc_html($config['label']); ?></h2>
                <p class="sr-cta-tagline"><?php echo esc_html($config['tagline']); ?></p>
            </div>
            <?php if ($cat_link && !is_wp_error($cat_link)) : ?>
                <a href="<?php echo esc_url($cat_link); ?>" class="sr-cta-btn">
                    Shop Full Collection
                </a>
            <?php endif; ?>
        </div>
    </section>

    <!-- ═══ STICKY ADD TO CART (mobile + scroll) ═══ -->
    <div class="sr-sticky-atc" id="srStickyATC" aria-hidden="true">
        <div class="sr-container sr-sticky-inner">
            <div class="sr-sticky-info">
                <span class="sr-sticky-name"><?php the_title(); ?></span>
                <span class="sr-sticky-price"><?php echo $price_html; ?></span>
            </div>
            <a href="#sr-atc-anchor" class="sr-sticky-btn">Add to Bag</a>
        </div>
    </div>

</main>

<?php
get_footer('shop');
