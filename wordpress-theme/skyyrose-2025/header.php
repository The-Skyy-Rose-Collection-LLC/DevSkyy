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
.site-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1.5rem 0;
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
    letter-spacing: 1px;
}

.site-branding img {
    max-height: 40px;
    width: auto;
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

.primary-menu a {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 0.9rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 500;
    transition: color 0.3s ease;
    position: relative;
}

.primary-menu a:hover,
.primary-menu .current-menu-item > a {
    color: #D4AF37;
}

.primary-menu a::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 0;
    height: 1px;
    background: #D4AF37;
    transition: width 0.3s ease;
}

.primary-menu a:hover::after {
    width: 100%;
}

.cart-icon {
    position: relative;
    color: #fff;
    font-size: 1.2rem;
    cursor: pointer;
}

.cart-count {
    position: absolute;
    top: -8px;
    right: -8px;
    background: #D4AF37;
    color: #000;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}

.mobile-menu-toggle {
    display: none;
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
}

@media (max-width: 1024px) {
    .mobile-menu-toggle {
        display: block;
    }

    .main-navigation {
        position: fixed;
        top: 80px;
        right: -100%;
        width: 300px;
        height: calc(100vh - 80px);
        background: rgba(0, 0, 0, 0.98);
        padding: 2rem;
        transition: right 0.4s ease;
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
        border-left: 1px solid rgba(255, 255, 255, 0.1);
    }

    .main-navigation.active {
        right: 0;
    }

    .primary-menu {
        flex-direction: column;
        align-items: flex-start;
        gap: 1.5rem;
        width: 100%;
    }

    .primary-menu a {
        font-size: 1.1rem;
        width: 100%;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
}
</style>

<header class="site-header">
    <div class="header-container">
        <div class="site-branding">
            <?php if (has_custom_logo()) : ?>
                <?php the_custom_logo(); ?>
            <?php else : ?>
                <a href="<?php echo esc_url(home_url('/')); ?>">
                    <?php bloginfo('name'); ?>
                </a>
            <?php endif; ?>
        </div>

        <nav class="main-navigation" id="mainNav">
            <?php
            if (has_nav_menu('primary')) {
                wp_nav_menu([
                    'theme_location' => 'primary',
                    'menu_class' => 'primary-menu',
                    'container' => false,
                ]);
            } else {
                // Fallback menu if no menu is set
                echo '<ul class="primary-menu">';
                echo '<li><a href="' . esc_url(home_url('/')) . '">Home</a></li>';
                echo '<li><a href="' . esc_url(home_url('/vault')) . '">Pre-Order</a></li>';
                echo '<li><a href="' . esc_url(home_url('/about')) . '">About</a></li>';
                echo '<li><a href="' . esc_url(home_url('/contact')) . '">Contact</a></li>';
                if (class_exists('WooCommerce')) {
                    echo '<li><a href="' . esc_url(wc_get_cart_url()) . '">Cart</a></li>';
                }
                echo '</ul>';
            }
            ?>

            <?php if (class_exists('WooCommerce')) : ?>
            <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="cart-icon">
                <span>🛒</span>
                <?php
                $cart_count = WC()->cart->get_cart_contents_count();
                if ($cart_count > 0) :
                ?>
                <span class="cart-count"><?php echo esc_html($cart_count); ?></span>
                <?php endif; ?>
            </a>
            <?php endif; ?>
        </nav>

        <button class="mobile-menu-toggle" id="mobileMenuToggle" aria-label="Toggle Menu">
            ☰
        </button>
    </div>
</header>

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
