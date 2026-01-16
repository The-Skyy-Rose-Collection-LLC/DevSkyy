<?php
/**
 * SkyyRose Spinning Logo Functions
 *
 * Provides dynamic logo color detection and spinning logo rendering
 *
 * @package SkyyRose_Immersive
 * @version 1.0.0
 */

defined('ABSPATH') || exit;

/**
 * Enqueue spinning logo styles and scripts
 */
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_logo_styles', 11);
function skyyrose_enqueue_logo_styles() {
    // Spinning logo styles
    wp_enqueue_style(
        'skyyrose-spinning-logo',
        SKYYROSE_IMMERSIVE_URI . '/assets/css/spinning-logo.css',
        array('skyyrose-immersive-style'),
        SKYYROSE_IMMERSIVE_VERSION
    );

    // Header JavaScript
    wp_enqueue_script(
        'skyyrose-header-js',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/header.js',
        array(),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );
}

/**
 * Get logo variant based on current page
 *
 * Returns appropriate logo color variant based on page type and collection
 *
 * @return string Logo variant (gold, silver, rose-gold, deep-rose, black)
 */
function skyyrose_get_logo_variant() {
    // Homepage - default gold
    if (is_front_page()) {
        return 'gold';
    }

    // Black Rose collection pages
    if (is_product_category('black-rose') || is_page('black-rose')) {
        return 'silver';
    }

    // Love Hurts collection pages
    if (is_product_category('love-hurts') || is_page('love-hurts')) {
        return 'deep-rose';
    }

    // Signature collection pages
    if (is_product_category('signature') || is_page('signature')) {
        return 'rose-gold';
    }

    // For single products, check their category
    if (is_product()) {
        global $product;

        // Ensure we have a valid product object
        if (!$product instanceof WC_Product) {
            $product = wc_get_product(get_the_ID());
        }

        if ($product && $product instanceof WC_Product) {
            $categories = wp_get_post_terms($product->get_id(), 'product_cat', array('fields' => 'slugs'));

            if (in_array('black-rose', $categories)) {
                return 'silver';
            } elseif (in_array('love-hurts', $categories)) {
                return 'deep-rose';
            } elseif (in_array('signature', $categories)) {
                return 'rose-gold';
            }
        }
    }

    // Check page slug for collection identifiers
    if (is_page()) {
        $page_slug = get_post_field('post_name', get_the_ID());

        if (strpos($page_slug, 'black-rose') !== false || strpos($page_slug, 'blackrose') !== false) {
            return 'silver';
        } elseif (strpos($page_slug, 'love-hurts') !== false || strpos($page_slug, 'lovehurts') !== false) {
            return 'deep-rose';
        } elseif (strpos($page_slug, 'signature') !== false) {
            return 'rose-gold';
        }
    }

    return 'gold'; // Default fallback
}

/**
 * Output spinning logo HTML
 *
 * Renders the spinning logo with appropriate color variant
 *
 * @return void
 */
function skyyrose_spinning_logo() {
    $variant = skyyrose_get_logo_variant();

    // Map variant to collection-specific animated logo
    $logo_map = array(
        'rose-gold' => 'signature',
        'silver' => 'black-rose',
        'deep-rose' => 'love-hurts',
        'gold' => 'skyyrose', // Default/main logo
    );

    $logo_prefix = isset($logo_map[$variant]) ? $logo_map[$variant] : 'skyyrose';

    // Use collection-specific animated GIF logo with responsive srcset
    $logo_url_60 = SKYYROSE_IMMERSIVE_URI . '/assets/images/' . $logo_prefix . '-logo-60px.gif';
    $logo_url_120 = SKYYROSE_IMMERSIVE_URI . '/assets/images/' . $logo_prefix . '-logo-120px.gif';
    ?>
    <a href="<?php echo esc_url(home_url('/')); ?>"
       class="skyyrose-logo skyyrose-logo--<?php echo esc_attr($variant); ?>"
       aria-label="SkyyRose Home">
        <img src="<?php echo esc_url($logo_url_60); ?>"
             srcset="<?php echo esc_url($logo_url_60); ?> 1x, <?php echo esc_url($logo_url_120); ?> 2x"
             alt="SkyyRose"
             class="skyyrose-logo__spinner" />
    </a>
    <?php
}

/**
 * Output complete header with spinning logo
 *
 * Renders full header structure with navigation, logo, and icons
 *
 * @return void
 */
function skyyrose_header_with_spinning_logo() {
    ?>
    <header class="site-header site-header--transparent" id="site-header">
        <!-- Left: Menu & Nav -->
        <div class="site-header__left">
            <button class="site-header__hamburger" aria-label="Menu">
                <span></span>
                <span></span>
                <span></span>
            </button>
            <nav class="site-header__nav">
                <a href="<?php echo esc_url(home_url('/shop/')); ?>"><?php _e('Shop', 'skyyrose-immersive'); ?></a>
                <a href="<?php echo esc_url(home_url('/collections/')); ?>"><?php _e('Collections', 'skyyrose-immersive'); ?></a>
                <a href="<?php echo esc_url(home_url('/about/')); ?>"><?php _e('About', 'skyyrose-immersive'); ?></a>
            </nav>
        </div>

        <!-- Center: Spinning Logo -->
        <div class="site-header__center">
            <?php skyyrose_spinning_logo(); ?>
        </div>

        <!-- Right: Icons -->
        <div class="site-header__right">
            <div class="site-header__icons">
                <button class="site-header__icon site-header__search" aria-label="Search">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM19 19l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>"
                   class="site-header__icon site-header__account"
                   aria-label="Account">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 17v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
                <a href="<?php echo esc_url(wc_get_cart_url()); ?>"
                   class="site-header__icon site-header__cart"
                   aria-label="Cart">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 2L3 6v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6l-3-4H6zM3 6h14M13 10a3 3 0 1 1-6 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <?php
                    $cart_count = WC()->cart->get_cart_contents_count();
                    if ($cart_count > 0) {
                        echo '<span class="site-header__cart-count">' . esc_html($cart_count) . '</span>';
                    }
                    ?>
                </a>
            </div>
        </div>
    </header>
    <?php
}

/**
 * Shortcode: [skyyrose_spinning_logo]
 *
 * Allows inserting the spinning logo via shortcode
 */
add_shortcode('skyyrose_spinning_logo', 'skyyrose_spinning_logo_shortcode');
function skyyrose_spinning_logo_shortcode($atts) {
    $atts = shortcode_atts(array(
        'variant' => '', // Optional: override auto-detection
    ), $atts, 'skyyrose_spinning_logo');

    $variant = !empty($atts['variant']) ? sanitize_key($atts['variant']) : skyyrose_get_logo_variant();

    $allowed_variants = array('gold', 'silver', 'rose-gold', 'deep-rose', 'black');
    if (!in_array($variant, $allowed_variants)) {
        $variant = 'gold';
    }

    // Map variant to collection-specific animated logo
    $logo_map = array(
        'rose-gold' => 'signature',
        'silver' => 'black-rose',
        'deep-rose' => 'love-hurts',
        'gold' => 'skyyrose', // Default/main logo
    );

    $logo_prefix = isset($logo_map[$variant]) ? $logo_map[$variant] : 'skyyrose';

    // Use collection-specific animated GIF logo with responsive srcset
    $logo_url_60 = SKYYROSE_IMMERSIVE_URI . '/assets/images/' . $logo_prefix . '-logo-60px.gif';
    $logo_url_120 = SKYYROSE_IMMERSIVE_URI . '/assets/images/' . $logo_prefix . '-logo-120px.gif';

    ob_start();
    ?>
    <div class="skyyrose-logo skyyrose-logo--<?php echo esc_attr($variant); ?>">
        <img src="<?php echo esc_url($logo_url_60); ?>"
             srcset="<?php echo esc_url($logo_url_60); ?> 1x, <?php echo esc_url($logo_url_120); ?> 2x"
             alt="SkyyRose"
             class="skyyrose-logo__spinner" />
    </div>
    <?php
    return ob_get_clean();
}
