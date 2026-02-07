<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="view-transition" content="same-origin">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<style>
:root {
    --skyyrose-gold: #B76E79;
    --skyyrose-dark: #1a1a1a;
    --skyyrose-light: #ffffff;
}

.site-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1rem 0;
    transition: all 0.4s cubic-bezier(0.43, 0.13, 0.23, 0.96);
}

.site-header.scrolled {
    padding: 0.5rem 0;
    background: rgba(0, 0, 0, 0.98);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.site-header.transparent {
    background: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.site-branding a {
    color: #fff;
    text-decoration: none;
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 2px;
    transition: color 0.3s ease;
}

.site-branding a:hover {
    color: var(--skyyrose-gold);
}

.site-branding img {
    max-height: 45px;
    width: auto;
    transition: transform 0.3s ease;
}

.site-branding:hover img {
    transform: scale(1.05);
}

.main-navigation {
    display: flex;
    align-items: center;
    gap: 3rem;
}

.primary-menu {
    display: flex;
    align-items: center;
    gap: 2.5rem;
    list-style: none;
    margin: 0;
    padding: 0;
}

.primary-menu > li {
    position: relative;
}

.primary-menu > li > a {
    color: rgba(255, 255, 255, 0.85);
    text-decoration: none;
    font-size: 0.85rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 500;
    transition: color 0.3s ease;
    position: relative;
    padding: 0.5rem 0;
    display: block;
}

.primary-menu > li > a:hover,
.primary-menu .current-menu-item > a {
    color: var(--skyyrose-gold);
}

.primary-menu > li > a::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 0;
    height: 2px;
    background: var(--skyyrose-gold);
    transition: width 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
}

.primary-menu > li > a:hover::after,
.primary-menu .current-menu-item > a::after {
    width: 100%;
}

/* Mega Menu */
.primary-menu .menu-item-has-children {
    position: relative;
}

.primary-menu .sub-menu {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: rgba(0, 0, 0, 0.98);
    backdrop-filter: blur(30px);
    border: 1px solid rgba(183, 110, 121, 0.2);
    border-radius: 8px;
    padding: 2rem;
    min-width: 600px;
    opacity: 0;
    visibility: hidden;
    transition: all 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    list-style: none;
    margin: 0;
}

.primary-menu .menu-item-has-children:hover .sub-menu {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(10px);
}

.sub-menu li {
    margin: 0;
}

.sub-menu a {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.9rem;
    letter-spacing: 1px;
    padding: 0.75rem 1rem;
    display: block;
    border-radius: 6px;
    transition: all 0.3s ease;
    text-transform: none;
}

.sub-menu a:hover {
    background: rgba(183, 110, 121, 0.15);
    color: var(--skyyrose-gold);
    transform: translateX(5px);
}

/* Header Icons */
.header-icons {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.header-icon {
    position: relative;
    color: rgba(255, 255, 255, 0.85);
    font-size: 1.2rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
}

.header-icon:hover {
    color: var(--skyyrose-gold);
    transform: scale(1.1);
}

.icon-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: var(--skyyrose-gold);
    color: var(--skyyrose-dark);
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}

/* Search Modal */
.search-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(20px);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    visibility: hidden;
    transition: all 0.4s ease;
}

.search-modal.active {
    opacity: 1;
    visibility: visible;
}

.search-modal-content {
    max-width: 800px;
    width: 90%;
    transform: translateY(30px);
    transition: transform 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
}

.search-modal.active .search-modal-content {
    transform: translateY(0);
}

.search-form-modal {
    position: relative;
}

.search-form-modal input {
    width: 100%;
    padding: 1.5rem 3rem 1.5rem 1.5rem;
    font-size: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(183, 110, 121, 0.3);
    border-radius: 12px;
    color: #fff;
    font-family: 'Playfair Display', serif;
}

.search-form-modal input:focus {
    outline: none;
    border-color: var(--skyyrose-gold);
}

.search-close {
    position: absolute;
    top: -60px;
    right: 0;
    background: none;
    border: none;
    color: #fff;
    font-size: 2rem;
    cursor: pointer;
    transition: transform 0.3s ease;
}

.search-close:hover {
    transform: rotate(90deg);
    color: var(--skyyrose-gold);
}

/* Mobile Menu */
.mobile-menu-toggle {
    display: none;
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
    transition: color 0.3s ease;
}

.mobile-menu-toggle:hover {
    color: var(--skyyrose-gold);
}

@media (max-width: 1024px) {
    .mobile-menu-toggle {
        display: block;
    }

    .main-navigation {
        position: fixed;
        top: 0;
        right: -100%;
        width: 320px;
        height: 100vh;
        background: rgba(0, 0, 0, 0.98);
        backdrop-filter: blur(30px);
        padding: 6rem 2rem 2rem;
        transition: right 0.4s cubic-bezier(0.6, -0.05, 0.01, 0.99);
        flex-direction: column;
        align-items: flex-start;
        gap: 2rem;
        border-left: 1px solid rgba(183, 110, 121, 0.2);
        overflow-y: auto;
    }

    .main-navigation.active {
        right: 0;
    }

    .primary-menu {
        flex-direction: column;
        align-items: flex-start;
        gap: 0;
        width: 100%;
    }

    .primary-menu > li {
        width: 100%;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .primary-menu > li > a {
        font-size: 1rem;
        width: 100%;
        padding: 1rem 0;
    }

    .primary-menu .sub-menu {
        position: static;
        transform: none;
        opacity: 1;
        visibility: visible;
        min-width: 100%;
        padding: 0 0 0 1rem;
        background: transparent;
        border: none;
        box-shadow: none;
        display: none;
        grid-template-columns: 1fr;
    }

    .primary-menu .menu-item-has-children.open .sub-menu {
        display: block;
    }

    .header-icons {
        flex-direction: row;
        justify-content: flex-start;
        width: 100%;
        padding-top: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
}

/* Animation on load */
@keyframes headerSlideDown {
    from {
        transform: translateY(-100%);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.site-header {
    animation: headerSlideDown 0.6s cubic-bezier(0.43, 0.13, 0.23, 0.96);
}
</style>

<header class="site-header" id="masthead">
    <div class="header-container">
        <div class="site-branding">
            <?php if (has_custom_logo()) : ?>
                <?php the_custom_logo(); ?>
            <?php else : ?>
                <a href="<?php echo esc_url(home_url('/')); ?>" rel="home">
                    <?php bloginfo('name'); ?>
                </a>
            <?php endif; ?>
        </div>

        <nav class="main-navigation" id="mainNav" role="navigation" aria-label="Primary Navigation">
            <?php
            if (has_nav_menu('primary')) {
                wp_nav_menu([
                    'theme_location' => 'primary',
                    'menu_class' => 'primary-menu',
                    'container' => false,
                    'fallback_cb' => false,
                ]);
            } else {
                // Fallback menu
                echo '<ul class="primary-menu">';
                echo '<li><a href="' . esc_url(home_url('/')) . '">Home</a></li>';
                echo '<li class="menu-item-has-children">';
                echo '<a href="#">Collections</a>';
                echo '<ul class="sub-menu">';
                echo '<li><a href="' . esc_url(home_url('/collection/black-rose')) . '">BLACK ROSE</a></li>';
                echo '<li><a href="' . esc_url(home_url('/collection/love-hurts')) . '">LOVE HURTS</a></li>';
                echo '<li><a href="' . esc_url(home_url('/collection/signature')) . '">SIGNATURE</a></li>';
                echo '</ul>';
                echo '</li>';
                echo '<li><a href="' . esc_url(home_url('/vault')) . '">Vault</a></li>';
                echo '<li><a href="' . esc_url(home_url('/about')) . '">About</a></li>';
                echo '<li><a href="' . esc_url(home_url('/contact')) . '">Contact</a></li>';
                if (class_exists('WooCommerce')) {
                    echo '<li><a href="' . esc_url(wc_get_page_permalink('shop')) . '">Shop</a></li>';
                }
                echo '</ul>';
            }
            ?>

            <div class="header-icons">
                <!-- Search Icon -->
                <button class="header-icon search-toggle" id="searchToggle" aria-label="Search">
                    <span>🔍</span>
                </button>

                <?php if (is_user_logged_in()) : ?>
                <!-- Account Icon -->
                <a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="header-icon" aria-label="My Account">
                    <span>👤</span>
                </a>
                <?php else : ?>
                <a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="header-icon" aria-label="Login">
                    <span>👤</span>
                </a>
                <?php endif; ?>

                <?php if (class_exists('WooCommerce')) : ?>
                <!-- Wishlist Icon (placeholder - requires plugin) -->
                <a href="#" class="header-icon" aria-label="Wishlist">
                    <span>♡</span>
                    <span class="icon-badge">0</span>
                </a>

                <!-- Cart Icon -->
                <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="header-icon cart-icon" aria-label="Shopping Cart">
                    <span>🛒</span>
                    <?php
                    $cart_count = WC()->cart->get_cart_contents_count();
                    if ($cart_count > 0) :
                    ?>
                    <span class="icon-badge"><?php echo esc_html($cart_count); ?></span>
                    <?php endif; ?>
                </a>
                <?php endif; ?>
            </div>
        </nav>

        <button class="mobile-menu-toggle" id="mobileMenuToggle" aria-label="Toggle Menu" aria-expanded="false">
            <span>☰</span>
        </button>
    </div>
</header>

<!-- Search Modal -->
<div class="search-modal" id="searchModal">
    <div class="search-modal-content">
        <button class="search-close" id="searchClose" aria-label="Close Search">&times;</button>
        <form role="search" method="get" class="search-form-modal" action="<?php echo esc_url(home_url('/')); ?>">
            <input type="search" 
                   name="s" 
                   placeholder="Search SkyyRose..." 
                   aria-label="Search"
                   autocomplete="off">
        </form>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const header = document.getElementById('masthead');
    const toggle = document.getElementById('mobileMenuToggle');
    const nav = document.getElementById('mainNav');
    const searchToggle = document.getElementById('searchToggle');
    const searchModal = document.getElementById('searchModal');
    const searchClose = document.getElementById('searchClose');
    const body = document.body;

    // Sticky header on scroll
    let lastScroll = 0;
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            header.classList.add('scrolled');
            header.classList.remove('transparent');
        } else {
            header.classList.remove('scrolled');
            // Add transparent class on homepage hero
            if (body.classList.contains('home') && currentScroll < 50) {
                header.classList.add('transparent');
            }
        }
        
        lastScroll = currentScroll;
    });

    // Mobile menu toggle
    if (toggle && nav) {
        toggle.addEventListener('click', function() {
            const isActive = nav.classList.toggle('active');
            toggle.setAttribute('aria-expanded', isActive);
            body.style.overflow = isActive ? 'hidden' : '';
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!nav.contains(e.target) && !toggle.contains(e.target) && nav.classList.contains('active')) {
                nav.classList.remove('active');
                toggle.setAttribute('aria-expanded', 'false');
                body.style.overflow = '';
            }
        });

        // Mobile submenu toggle
        const menuItemsWithChildren = document.querySelectorAll('.menu-item-has-children > a');
        menuItemsWithChildren.forEach(function(item) {
            item.addEventListener('click', function(e) {
                if (window.innerWidth <= 1024) {
                    e.preventDefault();
                    this.parentElement.classList.toggle('open');
                }
            });
        });
    }

    // Search modal
    if (searchToggle && searchModal && searchClose) {
        searchToggle.addEventListener('click', function() {
            searchModal.classList.add('active');
            body.style.overflow = 'hidden';
            setTimeout(function() {
                searchModal.querySelector('input').focus();
            }, 100);
        });

        searchClose.addEventListener('click', function() {
            searchModal.classList.remove('active');
            body.style.overflow = '';
        });

        searchModal.addEventListener('click', function(e) {
            if (e.target === searchModal) {
                searchModal.classList.remove('active');
                body.style.overflow = '';
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && searchModal.classList.contains('active')) {
                searchModal.classList.remove('active');
                body.style.overflow = '';
            }
        });
    }

    // Update cart count dynamically (AJAX)
    <?php if (class_exists('WooCommerce')) : ?>
    jQuery(document.body).on('added_to_cart removed_from_cart', function() {
        jQuery.get('<?php echo esc_url(wc_get_cart_url()); ?>', function(data) {
            const count = jQuery(data).find('.icon-badge').text();
            jQuery('.cart-icon .icon-badge').text(count);
        });
    });
    <?php endif; ?>
});
</script>

<script>
// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('mobileMenuToggle');
    const nav = document.getElementById('mainNav');

    if (toggle && nav) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!nav.contains(e.target) && !toggle.contains(e.target)) {
                nav.classList.remove('active');
            }
        });
    }
});
</script>
