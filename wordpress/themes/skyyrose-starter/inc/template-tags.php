<?php
/**
 * SkyyRose Template Tags
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

/**
 * Display the logo
 */
function skyyrose_logo(): void {
    if (has_custom_logo()) {
        the_custom_logo();
    } else {
        ?>
        <a href="<?php echo esc_url(home_url('/')); ?>" class="logo">SKYYROSE</a>
        <?php
    }
}

/**
 * Display cart count
 */
function skyyrose_cart_count(): int {
    if (function_exists('WC') && WC()->cart) {
        return WC()->cart->get_cart_contents_count();
    }
    return 0;
}

/**
 * Display breadcrumbs
 */
function skyyrose_breadcrumbs(): void {
    if (is_front_page()) {
        return;
    }
    ?>
    <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="<?php echo esc_url(home_url('/')); ?>">Home</a>
        <?php
        if (is_singular('product')) {
            global $product;
            $terms = get_the_terms(get_the_ID(), 'product_cat');
            if ($terms && !is_wp_error($terms)) {
                $term = reset($terms);
                ?>
                <span>/</span>
                <a href="<?php echo esc_url(get_term_link($term)); ?>"><?php echo esc_html($term->name); ?></a>
                <?php
            }
            ?>
            <span>/</span>
            <span class="current"><?php the_title(); ?></span>
            <?php
        } elseif (is_product_category()) {
            ?>
            <span>/</span>
            <span class="current"><?php single_term_title(); ?></span>
            <?php
        } elseif (is_shop()) {
            ?>
            <span>/</span>
            <span class="current">Shop</span>
            <?php
        } elseif (is_page()) {
            ?>
            <span>/</span>
            <span class="current"><?php the_title(); ?></span>
            <?php
        }
        ?>
    </nav>
    <?php
}

/**
 * Display product badges
 */
function skyyrose_product_badges($product_id = null): void {
    if (!$product_id) {
        $product_id = get_the_ID();
    }

    $product = wc_get_product($product_id);
    if (!$product) {
        return;
    }

    $badges = [];

    // Collection badge
    $collection = skyyrose_get_product_collection($product_id);
    if ($collection) {
        $badges[] = [
            'text'  => $collection['name'],
            'class' => 'badge-collection',
            'style' => 'background:' . esc_attr($collection['color']),
        ];
    }

    // Sale badge
    if ($product->is_on_sale()) {
        $badges[] = [
            'text'  => 'Sale',
            'class' => 'badge-sale',
        ];
    }

    // New badge (products created in last 30 days)
    $created = get_the_date('U', $product_id);
    if ((time() - $created) < (30 * DAY_IN_SECONDS)) {
        $badges[] = [
            'text'  => 'New',
            'class' => 'badge-new',
        ];
    }

    // Featured/Limited badge
    if ($product->is_featured()) {
        $badges[] = [
            'text'  => 'Limited Edition',
            'class' => 'badge-limited',
        ];
    }

    if (empty($badges)) {
        return;
    }

    echo '<div class="product-badges">';
    foreach ($badges as $badge) {
        $style = isset($badge['style']) ? ' style="' . esc_attr($badge['style']) . '"' : '';
        printf(
            '<span class="badge %s"%s>%s</span>',
            esc_attr($badge['class']),
            $style,
            esc_html($badge['text'])
        );
    }
    echo '</div>';
}

/**
 * Display collection cards for homepage
 */
function skyyrose_collection_cards(): void {
    $collections = skyyrose_get_collections();

    foreach ($collections as $slug => $collection) {
        $link = '';
        if ($collection['category_id']) {
            $link = get_term_link((int) $collection['category_id'], 'product_cat');
        }
        if (is_wp_error($link) || !$link) {
            $link = home_url('/collection-' . $slug);
        }
        ?>
        <div class="collection-card <?php echo esc_attr($slug); ?>">
            <div class="collection-bg" style="--collection-color: <?php echo esc_attr($collection['color']); ?>"></div>
            <div class="collection-content">
                <h3 class="collection-name"><?php echo esc_html($collection['name']); ?></h3>
                <p class="collection-tagline"><?php echo esc_html($collection['tagline']); ?></p>
                <a href="<?php echo esc_url($link); ?>" class="collection-link">
                    Explore Collection
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                </a>
            </div>
        </div>
        <?php
    }
}

/**
 * Display featured products
 */
function skyyrose_featured_products($count = 4): void {
    $args = [
        'post_type'      => 'product',
        'posts_per_page' => $count,
        'post_status'    => 'publish',
        'tax_query'      => [
            [
                'taxonomy' => 'product_visibility',
                'field'    => 'name',
                'terms'    => 'featured',
            ],
        ],
    ];

    $query = new WP_Query($args);

    if (!$query->have_posts()) {
        // Fallback to recent products
        $args = [
            'post_type'      => 'product',
            'posts_per_page' => $count,
            'post_status'    => 'publish',
            'orderby'        => 'date',
            'order'          => 'DESC',
        ];
        $query = new WP_Query($args);
    }

    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            get_template_part('template-parts/content', 'product-card');
        }
        wp_reset_postdata();
    }
}

/**
 * Display social links
 */
function skyyrose_social_links(): void {
    $socials = [
        'instagram' => get_option('skyyrose_instagram', 'https://instagram.com/skyyrose'),
        'tiktok'    => get_option('skyyrose_tiktok', 'https://tiktok.com/@skyyrose'),
        'twitter'   => get_option('skyyrose_twitter', 'https://twitter.com/skyyrose'),
        'pinterest' => get_option('skyyrose_pinterest', 'https://pinterest.com/skyyrose'),
    ];

    $icons = [
        'instagram' => '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
        'tiktok'    => '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12a4 4 0 104 4V4a5 5 0 005 5"/></svg>',
        'twitter'   => '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/></svg>',
        'pinterest' => '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 12a4 4 0 118 0c0 4-3 6-3 6"/><line x1="12" y1="17" x2="12" y2="22"/></svg>',
    ];

    echo '<div class="social-links">';
    foreach ($socials as $network => $url) {
        if ($url) {
            printf(
                '<a href="%s" target="_blank" rel="noopener noreferrer" title="%s">%s</a>',
                esc_url($url),
                esc_attr(ucfirst($network)),
                $icons[$network]
            );
        }
    }
    echo '</div>';
}

/**
 * Display payment icons
 */
function skyyrose_payment_icons(): void {
    $payments = ['visa', 'mastercard', 'amex', 'applepay', 'paypal', 'shoppay'];

    echo '<div class="payment-icons">';
    foreach ($payments as $payment) {
        echo '<span class="payment-icon payment-' . esc_attr($payment) . '" title="' . esc_attr(ucfirst($payment)) . '"></span>';
    }
    echo '</div>';
}
