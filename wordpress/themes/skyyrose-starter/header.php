<?php
/**
 * Header Template
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<!-- Navigation -->
<nav class="navbar" id="navbar">
    <?php skyyrose_logo(); ?>

    <ul class="nav-links">
        <?php
        wp_nav_menu([
            'theme_location' => 'primary',
            'container'      => false,
            'items_wrap'     => '%3$s',
            'walker'         => new SkyyRose_Nav_Walker(),
            'fallback_cb'    => function() {
                ?>
                <li><a href="<?php echo esc_url(home_url('/collection-black-rose')); ?>">Black Rose</a></li>
                <li><a href="<?php echo esc_url(home_url('/collection-love-hurts')); ?>">Love Hurts</a></li>
                <li><a href="<?php echo esc_url(home_url('/collection-signature')); ?>">Signature</a></li>
                <li><a href="<?php echo esc_url(home_url('/about')); ?>">About</a></li>
                <li><a href="<?php echo esc_url(home_url('/blog')); ?>">Journal</a></li>
                <?php
            },
        ]);
        ?>
    </ul>

    <div class="nav-actions">
        <button class="nav-icon" id="searchToggle" aria-label="Search">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
            </svg>
        </button>

        <?php if (is_user_logged_in()) : ?>
            <a href="<?php echo esc_url(wc_get_account_endpoint_url('dashboard')); ?>" class="nav-icon" aria-label="Account">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            </a>
        <?php endif; ?>

        <a href="<?php echo esc_url(home_url('/wishlist')); ?>" class="nav-icon" aria-label="Wishlist">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
            </svg>
        </a>

        <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="nav-icon cart-link" aria-label="Cart">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <path d="M16 10a4 4 0 01-8 0"/>
            </svg>
            <span class="cart-count" id="cartCount"><?php echo skyyrose_cart_count(); ?></span>
        </a>

        <button class="nav-icon mobile-menu-toggle" id="mobileMenuToggle" aria-label="Menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="3" y1="6" x2="21" y2="6"/>
                <line x1="3" y1="12" x2="21" y2="12"/>
                <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
        </button>
    </div>
</nav>

<!-- Mobile Menu -->
<div class="mobile-menu" id="mobileMenu">
    <div class="mobile-menu-header">
        <?php skyyrose_logo(); ?>
        <button class="mobile-menu-close" id="mobileMenuClose" aria-label="Close menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
    </div>
    <ul class="mobile-nav-links">
        <li><a href="<?php echo esc_url(home_url('/collection-black-rose')); ?>">Black Rose</a></li>
        <li><a href="<?php echo esc_url(home_url('/collection-love-hurts')); ?>">Love Hurts</a></li>
        <li><a href="<?php echo esc_url(home_url('/collection-signature')); ?>">Signature</a></li>
        <li><a href="<?php echo esc_url(home_url('/about')); ?>">About</a></li>
        <li><a href="<?php echo esc_url(home_url('/blog')); ?>">Journal</a></li>
        <li><a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a></li>
    </ul>
    <?php skyyrose_social_links(); ?>
</div>

<!-- Search Overlay -->
<div class="search-overlay" id="searchOverlay">
    <div class="search-container">
        <form role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>" class="search-form">
            <input type="search" name="s" placeholder="Search products..." autocomplete="off" class="search-input">
            <input type="hidden" name="post_type" value="product">
            <button type="submit" class="search-submit" aria-label="Search">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                </svg>
            </button>
        </form>
        <button class="search-close" id="searchClose" aria-label="Close search">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
    </div>
</div>

<main id="main" class="site-main">
