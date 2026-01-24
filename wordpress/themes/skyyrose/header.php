<?php
/**
 * The header template for SkyyRose theme
 *
 * Displays the site header with mega menu navigation, cart, and mobile toggle.
 * Features mobile-first responsive design, glassmorphism styling, and GSAP-ready animations.
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#B76E79">
    <link rel="profile" href="https://gmpg.org/xfn/11">

    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- Skip Navigation Link -->
<a class="skip-link sr-only" href="#main-content">
    <?php esc_html_e('Skip to main content', 'skyyrose'); ?>
</a>

<!-- Site Header -->
<header
    id="site-header"
    class="site-header glass-header gsap-header"
    role="banner"
    aria-label="<?php esc_attr_e('Site Header', 'skyyrose'); ?>"
>
    <div class="header-inner">
        <!-- Logo -->
        <div class="header-logo gsap-fade-in">
            <?php if (has_custom_logo()) : ?>
                <?php the_custom_logo(); ?>
            <?php else : ?>
                <a href="<?php echo esc_url(home_url('/')); ?>" class="logo-text" rel="home">
                    <span class="logo-name">SkyyRose</span>
                    <span class="logo-tagline sr-only"><?php esc_html_e('Where Love Meets Luxury', 'skyyrose'); ?></span>
                </a>
            <?php endif; ?>
        </div>

        <!-- Primary Navigation -->
        <nav
            id="primary-nav"
            class="primary-nav gsap-fade-in"
            role="navigation"
            aria-label="<?php esc_attr_e('Primary Navigation', 'skyyrose'); ?>"
        >
            <ul class="nav-menu" role="menubar">
                <!-- Collections Mega Menu -->
                <li class="nav-item has-mega-menu" role="none">
                    <button
                        type="button"
                        class="nav-link mega-menu-trigger"
                        aria-expanded="false"
                        aria-haspopup="true"
                        aria-controls="mega-menu-collections"
                        role="menuitem"
                    >
                        <span><?php esc_html_e('Collections', 'skyyrose'); ?></span>
                        <svg class="nav-arrow" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>

                    <!-- Mega Menu Panel -->
                    <div
                        id="mega-menu-collections"
                        class="mega-menu-panel glass-panel"
                        role="menu"
                        aria-label="<?php esc_attr_e('Collections Menu', 'skyyrose'); ?>"
                    >
                        <div class="mega-menu-inner">
                            <div class="mega-menu-grid">
                                <?php
                                // Collection data
                                $collections = [
                                    'black-rose' => [
                                        'name'        => __('Black Rose', 'skyyrose'),
                                        'tagline'     => __('Dark Romance', 'skyyrose'),
                                        'icon'        => 'rose-dark',
                                        'experience'  => '/collections/black-rose/experience',
                                        'shop'        => '/collections/black-rose',
                                    ],
                                    'signature' => [
                                        'name'        => __('Signature', 'skyyrose'),
                                        'tagline'     => __('Timeless Elegance', 'skyyrose'),
                                        'icon'        => 'rose-gold',
                                        'experience'  => '/collections/signature/experience',
                                        'shop'        => '/collections/signature',
                                    ],
                                    'love-hurts' => [
                                        'name'        => __('Love Hurts', 'skyyrose'),
                                        'tagline'     => __('Bold Statements', 'skyyrose'),
                                        'icon'        => 'rose-crimson',
                                        'experience'  => '/collections/love-hurts/experience',
                                        'shop'        => '/collections/love-hurts',
                                    ],
                                ];

                                foreach ($collections as $slug => $collection) :
                                    $collection_data = skyyrose_get_collection($slug);
                                ?>
                                    <div class="mega-menu-collection" data-collection="<?php echo esc_attr($slug); ?>">
                                        <div class="collection-header">
                                            <div class="collection-icon collection-icon--<?php echo esc_attr($collection['icon']); ?>" aria-hidden="true">
                                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="currentColor"/>
                                                </svg>
                                            </div>
                                            <div class="collection-info">
                                                <h3 class="collection-name"><?php echo esc_html($collection['name']); ?></h3>
                                                <p class="collection-tagline"><?php echo esc_html($collection['tagline']); ?></p>
                                            </div>
                                        </div>
                                        <div class="collection-links">
                                            <a
                                                href="<?php echo esc_url(home_url($collection['experience'])); ?>"
                                                class="collection-link collection-link--experience magnetic-btn"
                                                role="menuitem"
                                            >
                                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                                    <path d="M8 1L10.5 6L16 6.5L12 10.5L13 16L8 13L3 16L4 10.5L0 6.5L5.5 6L8 1Z" fill="currentColor"/>
                                                </svg>
                                                <span><?php esc_html_e('Experience', 'skyyrose'); ?></span>
                                            </a>
                                            <a
                                                href="<?php echo esc_url(home_url($collection['shop'])); ?>"
                                                class="collection-link collection-link--shop magnetic-btn"
                                                role="menuitem"
                                            >
                                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                                    <path d="M4 1L1 4V14C1 14.5523 1.44772 15 2 15H14C14.5523 15 15 14.5523 15 14V4L12 1H4Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                                    <path d="M1 4H15" stroke="currentColor" stroke-width="1.5"/>
                                                    <path d="M11 7C11 8.65685 9.65685 10 8 10C6.34315 10 5 8.65685 5 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                                </svg>
                                                <span><?php esc_html_e('Shop All', 'skyyrose'); ?></span>
                                            </a>
                                        </div>
                                    </div>
                                <?php endforeach; ?>
                            </div>

                            <!-- Featured Collection Preview -->
                            <div class="mega-menu-featured">
                                <div class="featured-preview glass-card">
                                    <div class="featured-image" aria-hidden="true">
                                        <div class="featured-placeholder"></div>
                                    </div>
                                    <div class="featured-content">
                                        <span class="featured-label"><?php esc_html_e('Featured', 'skyyrose'); ?></span>
                                        <h4 class="featured-title"><?php esc_html_e('New Arrivals', 'skyyrose'); ?></h4>
                                        <a href="<?php echo esc_url(home_url('/shop/new-arrivals')); ?>" class="featured-link magnetic-btn">
                                            <?php esc_html_e('Explore Now', 'skyyrose'); ?>
                                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                                                <path d="M2 6H10M10 6L7 3M10 6L7 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </li>

                <!-- Pre-Order -->
                <li class="nav-item" role="none">
                    <a
                        href="<?php echo esc_url(home_url('/pre-order')); ?>"
                        class="nav-link"
                        role="menuitem"
                    >
                        <span><?php esc_html_e('Pre-Order', 'skyyrose'); ?></span>
                        <span class="nav-badge pulse"><?php esc_html_e('New', 'skyyrose'); ?></span>
                    </a>
                </li>

                <!-- About -->
                <li class="nav-item" role="none">
                    <a
                        href="<?php echo esc_url(home_url('/about')); ?>"
                        class="nav-link"
                        role="menuitem"
                    >
                        <?php esc_html_e('About', 'skyyrose'); ?>
                    </a>
                </li>

                <!-- Blog -->
                <li class="nav-item" role="none">
                    <a
                        href="<?php echo esc_url(get_permalink(get_option('page_for_posts'))); ?>"
                        class="nav-link"
                        role="menuitem"
                    >
                        <?php esc_html_e('Blog', 'skyyrose'); ?>
                    </a>
                </li>
            </ul>
        </nav>

        <!-- Header Actions -->
        <div class="header-actions gsap-fade-in">
            <!-- Search Toggle -->
            <button
                type="button"
                class="header-action header-search-toggle"
                aria-label="<?php esc_attr_e('Open Search', 'skyyrose'); ?>"
                aria-expanded="false"
                aria-controls="header-search"
            >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M14 14L18 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </button>

            <!-- Account -->
            <a
                href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>"
                class="header-action header-account"
                aria-label="<?php esc_attr_e('My Account', 'skyyrose'); ?>"
            >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <circle cx="10" cy="6" r="4" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M3 18C3 14.134 6.13401 11 10 11C13.866 11 17 14.134 17 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </a>

            <!-- Cart -->
            <a
                href="<?php echo esc_url(wc_get_cart_url()); ?>"
                class="header-action header-cart"
                aria-label="<?php esc_attr_e('View Cart', 'skyyrose'); ?>"
            >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path d="M5 1L2 5V17C2 17.5523 2.44772 18 3 18H17C17.5523 18 18 17.5523 18 17V5L15 1H5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 5H18" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M14 8C14 10.2091 12.2091 12 10 12C7.79086 12 6 10.2091 6 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <?php if (class_exists('WooCommerce')) : ?>
                    <span
                        class="cart-count<?php echo WC()->cart->get_cart_contents_count() > 0 ? ' has-items' : ''; ?>"
                        aria-label="<?php echo esc_attr(sprintf(__('%d items in cart', 'skyyrose'), WC()->cart->get_cart_contents_count())); ?>"
                    >
                        <?php echo esc_html(WC()->cart->get_cart_contents_count()); ?>
                    </span>
                <?php endif; ?>
            </a>

            <!-- Mobile Menu Toggle -->
            <button
                type="button"
                class="header-action mobile-menu-toggle"
                aria-label="<?php esc_attr_e('Open Menu', 'skyyrose'); ?>"
                aria-expanded="false"
                aria-controls="mobile-nav"
            >
                <span class="hamburger">
                    <span class="hamburger-line"></span>
                    <span class="hamburger-line"></span>
                    <span class="hamburger-line"></span>
                </span>
            </button>
        </div>
    </div>

    <!-- Search Overlay -->
    <div id="header-search" class="header-search glass-panel" aria-hidden="true">
        <div class="header-search-inner">
            <form role="search" method="get" class="search-form" action="<?php echo esc_url(home_url('/')); ?>">
                <label class="sr-only" for="header-search-input"><?php esc_html_e('Search for products', 'skyyrose'); ?></label>
                <input
                    type="search"
                    id="header-search-input"
                    class="search-input"
                    placeholder="<?php esc_attr_e('Search for luxury...', 'skyyrose'); ?>"
                    value="<?php echo get_search_query(); ?>"
                    name="s"
                    autocomplete="off"
                >
                <input type="hidden" name="post_type" value="product">
                <button type="submit" class="search-submit" aria-label="<?php esc_attr_e('Submit search', 'skyyrose'); ?>">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M14 14L18 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            </form>
            <button type="button" class="search-close" aria-label="<?php esc_attr_e('Close search', 'skyyrose'); ?>">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M6 6L18 18M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    </div>
</header>

<!-- Mobile Navigation -->
<nav
    id="mobile-nav"
    class="mobile-nav glass-panel"
    role="navigation"
    aria-label="<?php esc_attr_e('Mobile Navigation', 'skyyrose'); ?>"
    aria-hidden="true"
>
    <div class="mobile-nav-inner">
        <div class="mobile-nav-header">
            <a href="<?php echo esc_url(home_url('/')); ?>" class="mobile-logo">
                <span class="logo-name">SkyyRose</span>
            </a>
            <button
                type="button"
                class="mobile-nav-close"
                aria-label="<?php esc_attr_e('Close Menu', 'skyyrose'); ?>"
            >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M6 6L18 18M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        </div>

        <div class="mobile-nav-content">
            <!-- Mobile Collections Accordion -->
            <div class="mobile-accordion">
                <button
                    type="button"
                    class="mobile-accordion-trigger"
                    aria-expanded="false"
                    aria-controls="mobile-collections"
                >
                    <span><?php esc_html_e('Collections', 'skyyrose'); ?></span>
                    <svg class="accordion-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
                <div id="mobile-collections" class="mobile-accordion-panel" aria-hidden="true">
                    <?php
                    foreach ($collections as $slug => $collection) :
                    ?>
                        <div class="mobile-collection-item">
                            <h4 class="mobile-collection-name"><?php echo esc_html($collection['name']); ?></h4>
                            <div class="mobile-collection-links">
                                <a href="<?php echo esc_url(home_url($collection['experience'])); ?>">
                                    <?php esc_html_e('Experience', 'skyyrose'); ?>
                                </a>
                                <a href="<?php echo esc_url(home_url($collection['shop'])); ?>">
                                    <?php esc_html_e('Shop All', 'skyyrose'); ?>
                                </a>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>

            <!-- Mobile Nav Links -->
            <ul class="mobile-menu-list">
                <li>
                    <a href="<?php echo esc_url(home_url('/pre-order')); ?>" class="mobile-menu-link">
                        <span><?php esc_html_e('Pre-Order', 'skyyrose'); ?></span>
                        <span class="nav-badge pulse"><?php esc_html_e('New', 'skyyrose'); ?></span>
                    </a>
                </li>
                <li>
                    <a href="<?php echo esc_url(home_url('/about')); ?>" class="mobile-menu-link">
                        <?php esc_html_e('About', 'skyyrose'); ?>
                    </a>
                </li>
                <li>
                    <a href="<?php echo esc_url(get_permalink(get_option('page_for_posts'))); ?>" class="mobile-menu-link">
                        <?php esc_html_e('Blog', 'skyyrose'); ?>
                    </a>
                </li>
            </ul>

            <!-- Mobile Account Actions -->
            <div class="mobile-nav-actions">
                <a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="mobile-action-btn">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <circle cx="10" cy="6" r="4" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M3 18C3 14.134 6.13401 11 10 11C13.866 11 17 14.134 17 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <span><?php esc_html_e('Account', 'skyyrose'); ?></span>
                </a>
                <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="mobile-action-btn mobile-cart-btn">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <path d="M5 1L2 5V17C2 17.5523 2.44772 18 3 18H17C17.5523 18 18 17.5523 18 17V5L15 1H5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M2 5H18" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M14 8C14 10.2091 12.2091 12 10 12C7.79086 12 6 10.2091 6 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <span><?php esc_html_e('Cart', 'skyyrose'); ?></span>
                    <?php if (class_exists('WooCommerce') && WC()->cart->get_cart_contents_count() > 0) : ?>
                        <span class="mobile-cart-count"><?php echo esc_html(WC()->cart->get_cart_contents_count()); ?></span>
                    <?php endif; ?>
                </a>
            </div>
        </div>

        <!-- Mobile Footer -->
        <div class="mobile-nav-footer">
            <p class="mobile-tagline"><?php esc_html_e('Where Love Meets Luxury', 'skyyrose'); ?></p>
            <div class="mobile-social">
                <a href="https://instagram.com/skyyrose" target="_blank" rel="noopener noreferrer" aria-label="<?php esc_attr_e('Follow us on Instagram', 'skyyrose'); ?>">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <rect x="2" y="2" width="16" height="16" rx="4" stroke="currentColor" stroke-width="1.5"/>
                        <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="1.5"/>
                        <circle cx="15" cy="5" r="1" fill="currentColor"/>
                    </svg>
                </a>
                <a href="https://tiktok.com/@skyyrose" target="_blank" rel="noopener noreferrer" aria-label="<?php esc_attr_e('Follow us on TikTok', 'skyyrose'); ?>">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <path d="M10 2V13C10 14.6569 8.65685 16 7 16C5.34315 16 4 14.6569 4 13C4 11.3431 5.34315 10 7 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        <path d="M10 2C10 4 12 6 14 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- Mobile Nav Overlay -->
<div class="mobile-nav-overlay" aria-hidden="true"></div>

<?php
/**
 * AJAX Cart Count Update Fragment
 * This fragment is replaced via WooCommerce AJAX when cart is updated
 */
add_filter('woocommerce_add_to_cart_fragments', function($fragments) {
    ob_start();
    ?>
    <span
        class="cart-count<?php echo WC()->cart->get_cart_contents_count() > 0 ? ' has-items' : ''; ?>"
        aria-label="<?php echo esc_attr(sprintf(__('%d items in cart', 'skyyrose'), WC()->cart->get_cart_contents_count())); ?>"
    >
        <?php echo esc_html(WC()->cart->get_cart_contents_count()); ?>
    </span>
    <?php
    $fragments['span.cart-count'] = ob_get_clean();
    return $fragments;
});
?>

<style>
/* ==========================================================================
   Header Styles - Glassmorphism & Mobile-First
   ========================================================================== */

/* Base Header */
.site-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: var(--z-fixed);
    padding: var(--space-4) 0;
    transition:
        background-color var(--transition-base),
        backdrop-filter var(--transition-base),
        box-shadow var(--transition-base);
}

/* Glassmorphism Header */
.glass-header {
    background: rgba(13, 13, 13, 0.8);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--glass-border);
}

.glass-header.scrolled {
    background: rgba(13, 13, 13, 0.95);
    box-shadow: var(--shadow-lg);
}

.header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: var(--container-xl);
    margin: 0 auto;
    padding: 0 var(--space-6);
    gap: var(--space-8);
}

/* Logo */
.header-logo {
    flex-shrink: 0;
}

.logo-text {
    display: block;
    font-family: var(--font-display);
    font-size: var(--text-2xl);
    font-weight: 500;
    color: var(--skyyrose-white);
    letter-spacing: var(--tracking-wider);
    text-decoration: none;
    transition: color var(--transition-fast);
}

.logo-text:hover {
    color: var(--skyyrose-primary);
}

.logo-name {
    display: block;
}

.custom-logo-link img {
    height: 40px;
    width: auto;
}

/* Primary Navigation - Hidden on mobile */
.primary-nav {
    display: none;
}

@media (min-width: 1024px) {
    .primary-nav {
        display: block;
        flex: 1;
    }
}

.nav-menu {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-8);
    margin: 0;
    padding: 0;
    list-style: none;
}

.nav-item {
    position: relative;
}

.nav-link {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) 0;
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-decoration: none;
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider);
    background: none;
    border: none;
    cursor: pointer;
    transition: color var(--transition-fast);
}

.nav-link:hover,
.nav-link:focus {
    color: var(--skyyrose-primary);
}

.nav-arrow {
    transition: transform var(--transition-fast);
}

.mega-menu-trigger[aria-expanded="true"] .nav-arrow {
    transform: rotate(180deg);
}

/* Nav Badge */
.nav-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--skyyrose-white);
    background: var(--skyyrose-primary);
    border-radius: var(--radius-full);
}

.nav-badge.pulse {
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Mega Menu Panel */
.mega-menu-panel {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%) translateY(10px);
    min-width: 700px;
    padding: var(--space-8);
    background: rgba(26, 26, 26, 0.98);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-luxury);
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition:
        opacity var(--transition-base),
        transform var(--transition-base),
        visibility var(--transition-base);
}

.has-mega-menu:hover .mega-menu-panel,
.mega-menu-trigger[aria-expanded="true"] + .mega-menu-panel {
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
    transform: translateX(-50%) translateY(0);
}

.mega-menu-inner {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--space-8);
}

.mega-menu-grid {
    display: grid;
    gap: var(--space-6);
}

/* Collection Items */
.mega-menu-collection {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    transition: background-color var(--transition-fast);
}

.mega-menu-collection:hover {
    background: rgba(255, 255, 255, 0.03);
}

.collection-header {
    display: flex;
    align-items: center;
    gap: var(--space-4);
}

.collection-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-lg);
    transition: transform var(--transition-fast);
}

.collection-icon--rose-dark {
    color: var(--skyyrose-moonlight);
    background: rgba(192, 192, 192, 0.1);
}

.collection-icon--rose-gold {
    color: var(--skyyrose-rose-gold);
    background: rgba(201, 169, 98, 0.1);
}

.collection-icon--rose-crimson {
    color: var(--skyyrose-crimson);
    background: rgba(220, 20, 60, 0.1);
}

.mega-menu-collection:hover .collection-icon {
    transform: scale(1.1);
}

.collection-info {
    flex: 1;
}

.collection-name {
    font-family: var(--font-display);
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--skyyrose-white);
    margin: 0;
}

.collection-tagline {
    font-size: var(--text-sm);
    color: rgba(255, 255, 255, 0.6);
    margin: var(--space-1) 0 0;
}

.collection-links {
    display: flex;
    gap: var(--space-4);
    padding-left: 56px;
}

.collection-link {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition:
        color var(--transition-fast),
        background-color var(--transition-fast);
}

.collection-link:hover {
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.1);
}

.collection-link--experience svg {
    color: var(--skyyrose-rose-gold);
}

/* Featured Preview */
.mega-menu-featured {
    display: flex;
    flex-direction: column;
}

.featured-preview {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--glass-border);
}

.featured-image {
    position: relative;
    height: 150px;
    overflow: hidden;
}

.featured-placeholder {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, var(--skyyrose-primary) 0%, var(--skyyrose-crimson) 100%);
    opacity: 0.3;
}

.featured-content {
    padding: var(--space-4);
}

.featured-label {
    display: inline-block;
    padding: 2px 8px;
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider);
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.15);
    border-radius: var(--radius-sm);
}

.featured-title {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    color: var(--skyyrose-white);
    margin: var(--space-2) 0 var(--space-3);
}

.featured-link {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--skyyrose-primary);
    text-decoration: none;
    transition: gap var(--transition-fast);
}

.featured-link:hover {
    gap: var(--space-3);
}

/* Header Actions */
.header-actions {
    display: flex;
    align-items: center;
    gap: var(--space-4);
}

.header-action {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    color: var(--skyyrose-white);
    background: none;
    border: none;
    border-radius: var(--radius-full);
    cursor: pointer;
    transition:
        color var(--transition-fast),
        background-color var(--transition-fast);
}

.header-action:hover {
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.1);
}

/* Hide search and account on small mobile */
.header-search-toggle,
.header-account {
    display: none;
}

@media (min-width: 640px) {
    .header-search-toggle,
    .header-account {
        display: flex;
    }
}

/* Cart Count */
.header-cart {
    position: relative;
}

.cart-count {
    position: absolute;
    top: -2px;
    right: -2px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    font-size: 10px;
    font-weight: 600;
    color: var(--skyyrose-white);
    background: var(--skyyrose-primary);
    border-radius: var(--radius-full);
    opacity: 0;
    transform: scale(0.5);
    transition:
        opacity var(--transition-fast),
        transform var(--transition-fast);
}

.cart-count.has-items {
    opacity: 1;
    transform: scale(1);
}

/* Mobile Menu Toggle */
.mobile-menu-toggle {
    display: flex;
}

@media (min-width: 1024px) {
    .mobile-menu-toggle {
        display: none;
    }
}

.hamburger {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    width: 22px;
    height: 16px;
}

.hamburger-line {
    display: block;
    width: 100%;
    height: 2px;
    background: currentColor;
    border-radius: 1px;
    transition:
        transform var(--transition-fast),
        opacity var(--transition-fast);
}

.mobile-menu-toggle[aria-expanded="true"] .hamburger-line:nth-child(1) {
    transform: translateY(7px) rotate(45deg);
}

.mobile-menu-toggle[aria-expanded="true"] .hamburger-line:nth-child(2) {
    opacity: 0;
}

.mobile-menu-toggle[aria-expanded="true"] .hamburger-line:nth-child(3) {
    transform: translateY(-7px) rotate(-45deg);
}

/* ==========================================================================
   Search Overlay
   ========================================================================== */

.header-search {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    padding: var(--space-6);
    background: rgba(26, 26, 26, 0.98);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--glass-border);
    opacity: 0;
    visibility: hidden;
    transform: translateY(-10px);
    transition:
        opacity var(--transition-base),
        visibility var(--transition-base),
        transform var(--transition-base);
}

.header-search.is-open {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}

.header-search-inner {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    max-width: var(--container-md);
    margin: 0 auto;
}

.search-form {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--space-3);
}

.search-input {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    font-family: var(--font-body);
    font-size: var(--text-base);
    color: var(--skyyrose-white);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    outline: none;
    transition:
        border-color var(--transition-fast),
        background-color var(--transition-fast);
}

.search-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
    border-color: var(--skyyrose-primary);
    background: rgba(255, 255, 255, 0.08);
}

.search-submit,
.search-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    color: var(--skyyrose-white);
    background: none;
    border: none;
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition:
        color var(--transition-fast),
        background-color var(--transition-fast);
}

.search-submit:hover,
.search-close:hover {
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.1);
}

/* ==========================================================================
   Mobile Navigation
   ========================================================================== */

.mobile-nav {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    max-width: 400px;
    z-index: var(--z-modal);
    background: rgba(26, 26, 26, 0.98);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-left: 1px solid var(--glass-border);
    transform: translateX(100%);
    transition: transform var(--transition-slow);
    overflow-y: auto;
    overscroll-behavior: contain;
}

.mobile-nav.is-open {
    transform: translateX(0);
}

.mobile-nav-inner {
    display: flex;
    flex-direction: column;
    min-height: 100%;
    padding: var(--space-6);
}

.mobile-nav-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: var(--space-6);
    border-bottom: 1px solid var(--glass-border);
}

.mobile-logo {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-decoration: none;
    letter-spacing: var(--tracking-wider);
}

.mobile-nav-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    color: var(--skyyrose-white);
    background: none;
    border: none;
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition:
        color var(--transition-fast),
        background-color var(--transition-fast);
}

.mobile-nav-close:hover {
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.1);
}

.mobile-nav-content {
    flex: 1;
    padding: var(--space-6) 0;
}

/* Mobile Accordion */
.mobile-accordion {
    margin-bottom: var(--space-4);
}

.mobile-accordion-trigger {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: var(--space-4) 0;
    font-family: var(--font-body);
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-align: left;
    background: none;
    border: none;
    border-bottom: 1px solid var(--glass-border);
    cursor: pointer;
    transition: color var(--transition-fast);
}

.mobile-accordion-trigger:hover {
    color: var(--skyyrose-primary);
}

.accordion-arrow {
    transition: transform var(--transition-fast);
}

.mobile-accordion-trigger[aria-expanded="true"] .accordion-arrow {
    transform: rotate(180deg);
}

.mobile-accordion-panel {
    max-height: 0;
    overflow: hidden;
    transition: max-height var(--transition-base);
}

.mobile-accordion-trigger[aria-expanded="true"] + .mobile-accordion-panel {
    max-height: 500px;
}

.mobile-collection-item {
    padding: var(--space-4) 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.mobile-collection-item:last-child {
    border-bottom: none;
}

.mobile-collection-name {
    font-family: var(--font-display);
    font-size: var(--text-base);
    font-weight: 500;
    color: var(--skyyrose-white);
    margin: 0 0 var(--space-2);
}

.mobile-collection-links {
    display: flex;
    gap: var(--space-4);
}

.mobile-collection-links a {
    font-size: var(--text-sm);
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    transition: color var(--transition-fast);
}

.mobile-collection-links a:hover {
    color: var(--skyyrose-primary);
}

/* Mobile Menu List */
.mobile-menu-list {
    list-style: none;
    margin: 0;
    padding: 0;
}

.mobile-menu-link {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4) 0;
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-decoration: none;
    border-bottom: 1px solid var(--glass-border);
    transition: color var(--transition-fast);
}

.mobile-menu-link:hover {
    color: var(--skyyrose-primary);
}

/* Mobile Actions */
.mobile-nav-actions {
    display: flex;
    gap: var(--space-4);
    padding-top: var(--space-6);
    margin-top: var(--space-6);
    border-top: 1px solid var(--glass-border);
}

.mobile-action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-4);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--skyyrose-white);
    text-decoration: none;
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-lg);
    transition:
        color var(--transition-fast),
        background-color var(--transition-fast);
}

.mobile-action-btn:hover {
    color: var(--skyyrose-primary);
    background: rgba(183, 110, 121, 0.1);
}

.mobile-cart-btn {
    position: relative;
}

.mobile-cart-count {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    font-size: 10px;
    font-weight: 600;
    color: var(--skyyrose-white);
    background: var(--skyyrose-primary);
    border-radius: var(--radius-full);
}

/* Mobile Footer */
.mobile-nav-footer {
    padding-top: var(--space-6);
    border-top: 1px solid var(--glass-border);
    text-align: center;
}

.mobile-tagline {
    font-family: var(--font-display);
    font-size: var(--text-sm);
    font-style: italic;
    color: rgba(255, 255, 255, 0.5);
    margin: 0 0 var(--space-4);
}

.mobile-social {
    display: flex;
    justify-content: center;
    gap: var(--space-4);
}

.mobile-social a {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    color: rgba(255, 255, 255, 0.6);
    transition: color var(--transition-fast);
}

.mobile-social a:hover {
    color: var(--skyyrose-primary);
}

/* Mobile Overlay */
.mobile-nav-overlay {
    position: fixed;
    inset: 0;
    z-index: calc(var(--z-modal) - 1);
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    opacity: 0;
    visibility: hidden;
    transition:
        opacity var(--transition-base),
        visibility var(--transition-base);
}

.mobile-nav-overlay.is-open {
    opacity: 1;
    visibility: visible;
}

/* ==========================================================================
   GSAP Animation Classes
   ========================================================================== */

.gsap-header {
    will-change: transform;
}

.gsap-fade-in {
    opacity: 0;
    transform: translateY(-10px);
}

.gsap-fade-in.is-visible {
    opacity: 1;
    transform: translateY(0);
    transition:
        opacity var(--transition-base),
        transform var(--transition-base);
}

/* ==========================================================================
   Skip Link (Accessibility)
   ========================================================================== */

.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    z-index: calc(var(--z-cursor) + 1);
    padding: var(--space-3) var(--space-6);
    font-weight: 600;
    color: var(--skyyrose-white);
    background: var(--skyyrose-primary);
    transition: top var(--transition-fast);
}

.skip-link:focus {
    top: 0;
}

/* ==========================================================================
   Body Padding for Fixed Header
   ========================================================================== */

body {
    padding-top: 72px;
}

@media (min-width: 768px) {
    body {
        padding-top: 80px;
    }
}

/* Prevent scroll when mobile nav is open */
body.mobile-nav-open {
    overflow: hidden;
}
</style>

<script>
/**
 * SkyyRose Header JavaScript
 * Handles mega menu, mobile navigation, search, and scroll behavior
 */
(function() {
    'use strict';

    // Wait for DOM
    document.addEventListener('DOMContentLoaded', function() {
        initHeader();
    });

    function initHeader() {
        const header = document.getElementById('site-header');
        const mobileNav = document.getElementById('mobile-nav');
        const mobileOverlay = document.querySelector('.mobile-nav-overlay');
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        const mobileClose = document.querySelector('.mobile-nav-close');
        const searchToggle = document.querySelector('.header-search-toggle');
        const searchPanel = document.getElementById('header-search');
        const searchClose = document.querySelector('.search-close');
        const searchInput = document.getElementById('header-search-input');
        const megaMenuTriggers = document.querySelectorAll('.mega-menu-trigger');
        const accordionTriggers = document.querySelectorAll('.mobile-accordion-trigger');

        // Scroll behavior
        let lastScroll = 0;
        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;

            if (currentScroll > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        }, { passive: true });

        // Initialize GSAP animations
        if (typeof gsap !== 'undefined') {
            gsap.set('.gsap-fade-in', { opacity: 1, y: 0 });
        } else {
            document.querySelectorAll('.gsap-fade-in').forEach(function(el) {
                el.classList.add('is-visible');
            });
        }

        // Mobile menu toggle
        if (mobileToggle && mobileNav && mobileOverlay) {
            mobileToggle.addEventListener('click', function() {
                const isOpen = mobileNav.classList.contains('is-open');
                toggleMobileNav(!isOpen);
            });

            mobileClose.addEventListener('click', function() {
                toggleMobileNav(false);
            });

            mobileOverlay.addEventListener('click', function() {
                toggleMobileNav(false);
            });
        }

        function toggleMobileNav(open) {
            if (open) {
                mobileNav.classList.add('is-open');
                mobileOverlay.classList.add('is-open');
                mobileToggle.setAttribute('aria-expanded', 'true');
                mobileNav.setAttribute('aria-hidden', 'false');
                document.body.classList.add('mobile-nav-open');

                // Focus trap
                mobileNav.querySelector('a, button').focus();
            } else {
                mobileNav.classList.remove('is-open');
                mobileOverlay.classList.remove('is-open');
                mobileToggle.setAttribute('aria-expanded', 'false');
                mobileNav.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('mobile-nav-open');
                mobileToggle.focus();
            }
        }

        // Search toggle
        if (searchToggle && searchPanel) {
            searchToggle.addEventListener('click', function() {
                const isOpen = searchPanel.classList.contains('is-open');
                toggleSearch(!isOpen);
            });

            searchClose.addEventListener('click', function() {
                toggleSearch(false);
            });
        }

        function toggleSearch(open) {
            if (open) {
                searchPanel.classList.add('is-open');
                searchPanel.setAttribute('aria-hidden', 'false');
                searchToggle.setAttribute('aria-expanded', 'true');
                setTimeout(function() {
                    searchInput.focus();
                }, 100);
            } else {
                searchPanel.classList.remove('is-open');
                searchPanel.setAttribute('aria-hidden', 'true');
                searchToggle.setAttribute('aria-expanded', 'false');
            }
        }

        // Mega menu keyboard navigation
        megaMenuTriggers.forEach(function(trigger) {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

                // Close all other mega menus
                megaMenuTriggers.forEach(function(t) {
                    t.setAttribute('aria-expanded', 'false');
                });

                trigger.setAttribute('aria-expanded', !isExpanded);
            });

            // Keyboard support
            trigger.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    trigger.setAttribute('aria-expanded', 'false');
                    trigger.focus();
                }
            });
        });

        // Close mega menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.has-mega-menu')) {
                megaMenuTriggers.forEach(function(trigger) {
                    trigger.setAttribute('aria-expanded', 'false');
                });
            }
        });

        // Mobile accordion
        accordionTriggers.forEach(function(trigger) {
            trigger.addEventListener('click', function() {
                const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
                trigger.setAttribute('aria-expanded', !isExpanded);

                const panel = trigger.nextElementSibling;
                panel.setAttribute('aria-hidden', isExpanded);
            });
        });

        // Escape key handling
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                toggleMobileNav(false);
                toggleSearch(false);
            }
        });

        // AJAX cart update (WooCommerce)
        if (typeof jQuery !== 'undefined') {
            jQuery(document.body).on('added_to_cart removed_from_cart', function() {
                // Cart count is updated via WooCommerce fragments
                const cartCount = document.querySelector('.cart-count');
                if (cartCount) {
                    cartCount.classList.add('has-items');

                    // Animation pulse
                    cartCount.style.transform = 'scale(1.3)';
                    setTimeout(function() {
                        cartCount.style.transform = 'scale(1)';
                    }, 200);
                }
            });
        }
    }
})();
</script>
