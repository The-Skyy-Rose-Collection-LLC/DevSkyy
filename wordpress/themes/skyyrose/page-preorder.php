<?php
/**
 * Template Name: Pre-Order
 * Template Post Type: page
 *
 * Pre-order landing page with countdown timers, early access signup,
 * and products grouped by status (Blooming Soon, Now Blooming).
 *
 * @package SkyyRose
 * @version 2.0.0
 */

defined('ABSPATH') || exit;

get_header();

// Get all pre-order products
$preorder_products = skyyrose_get_preorder_products();

// Group products by status
$grouped_products = [
    'blooming_soon' => [],
    'now_blooming'  => [],
];

foreach ($preorder_products as $product) {
    $status = $product['status'] ?? 'blooming_soon';
    if (isset($grouped_products[$status])) {
        $grouped_products[$status][] = $product;
    }
}

// Group products by collection for the signup form
$collections = [];
foreach ($preorder_products as $product) {
    if (!empty($product['collection']) && !in_array($product['collection'], $collections, true)) {
        $collections[] = $product['collection'];
    }
}

// Get customizer settings
$klaviyo_list_id = get_theme_mod('skyyrose_klaviyo_list_id', '');
$klaviyo_api_key = get_theme_mod('skyyrose_klaviyo_public_key', '');
?>

<main id="main-content" class="preorder-page" role="main">
    <!-- Hero Section -->
    <section class="preorder-hero" data-gsap="fade-up">
        <div class="hero-background">
            <div class="hero-gradient"></div>
            <div class="hero-particles" aria-hidden="true"></div>
        </div>

        <div class="container">
            <div class="hero-content">
                <span class="hero-eyebrow" data-gsap="fade-up" data-gsap-delay="0.1">
                    Exclusive Preview
                </span>
                <h1 class="hero-headline" data-gsap="fade-up" data-gsap-delay="0.2">
                    Coming Soon
                </h1>
                <p class="hero-subheadline" data-gsap="fade-up" data-gsap-delay="0.3">
                    Be the first to bloom
                </p>

                <!-- Decorative Rose Element -->
                <div class="hero-decoration" aria-hidden="true" data-gsap="scale-in" data-gsap-delay="0.5">
                    <svg class="rose-icon" width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M40 10C40 10 50 25 50 35C50 45 45 50 40 55C35 50 30 45 30 35C30 25 40 10 40 10Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M25 25C25 25 35 30 40 40C45 50 40 60 40 70" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M55 25C55 25 45 30 40 40C35 50 40 60 40 70" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M20 45C20 45 30 45 40 50C50 55 55 65 55 75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M60 45C60 45 50 45 40 50C30 55 25 65 25 75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>

                <!-- Scroll Indicator -->
                <a href="#early-access" class="scroll-indicator magnetic-btn" data-gsap="fade-up" data-gsap-delay="0.6" aria-label="Scroll to early access signup">
                    <span class="scroll-text">Explore</span>
                    <svg class="scroll-arrow" width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M12 5V19M12 19L5 12M12 19L19 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
            </div>
        </div>
    </section>

    <!-- Early Access Signup Section -->
    <section id="early-access" class="early-access-section section" data-gsap="fade-up">
        <div class="container">
            <div class="early-access-wrapper">
                <div class="early-access-card glass-card" data-gsap="fade-up" data-gsap-delay="0.1">
                    <div class="card-glow" aria-hidden="true"></div>

                    <div class="early-access-content">
                        <div class="early-access-header">
                            <span class="badge badge-exclusive">VIP Access</span>
                            <h2 class="section-title">Get Early Access</h2>
                            <p class="section-description">
                                Join our exclusive list to receive priority notifications, special pricing, and first access to new collections before they go live.
                            </p>
                        </div>

                        <form
                            id="preorder-signup-form"
                            class="early-access-form"
                            data-klaviyo-list="<?php echo esc_attr($klaviyo_list_id); ?>"
                            novalidate
                        >
                            <?php wp_nonce_field('skyyrose_preorder_signup', 'preorder_signup_nonce'); ?>

                            <div class="form-group">
                                <label for="preorder-email" class="form-label">Email Address</label>
                                <div class="input-wrapper">
                                    <input
                                        type="email"
                                        id="preorder-email"
                                        name="email"
                                        class="glass-input"
                                        placeholder="your@email.com"
                                        required
                                        autocomplete="email"
                                    >
                                    <svg class="input-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                        <path d="M2.5 6.25L9.0755 10.7579C9.62726 11.1451 10.3727 11.1451 10.9245 10.7579L17.5 6.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                        <rect x="2.5" y="4.16669" width="15" height="11.6667" rx="2" stroke="currentColor" stroke-width="1.5"/>
                                    </svg>
                                </div>
                            </div>

                            <?php if (!empty($collections)) : ?>
                                <fieldset class="form-group form-group-collections">
                                    <legend class="form-label">Interested Collections</legend>
                                    <div class="checkbox-group">
                                        <?php foreach ($collections as $collection_slug) :
                                            $collection_data = skyyrose_get_collection($collection_slug);
                                        ?>
                                            <label class="checkbox-label glass-checkbox">
                                                <input
                                                    type="checkbox"
                                                    name="collections[]"
                                                    value="<?php echo esc_attr($collection_slug); ?>"
                                                >
                                                <span class="checkbox-custom" style="--checkbox-accent: <?php echo esc_attr($collection_data['colors']['primary']); ?>"></span>
                                                <span class="checkbox-text"><?php echo esc_html($collection_data['name']); ?></span>
                                            </label>
                                        <?php endforeach; ?>
                                    </div>
                                </fieldset>
                            <?php endif; ?>

                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary btn-glow magnetic-btn">
                                    <span class="btn-text">Join the Waitlist</span>
                                    <span class="btn-loading" aria-hidden="true">
                                        <svg class="spinner" width="20" height="20" viewBox="0 0 20 20" fill="none">
                                            <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="50" stroke-dashoffset="40"/>
                                        </svg>
                                    </span>
                                    <svg class="btn-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                                        <path d="M4.16669 10H15.8334M15.8334 10L10.8334 5M15.8334 10L10.8334 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </button>
                            </div>

                            <p class="form-privacy">
                                By signing up, you agree to our
                                <a href="<?php echo esc_url(get_privacy_policy_url()); ?>">Privacy Policy</a>.
                                Unsubscribe anytime.
                            </p>
                        </form>

                        <!-- Success Message (hidden by default) -->
                        <div id="signup-success" class="signup-success" hidden>
                            <div class="success-icon">
                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                                    <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="2"/>
                                    <path d="M16 24L22 30L34 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </div>
                            <h3>You're on the List!</h3>
                            <p>We'll notify you as soon as new pieces are ready to bloom.</p>
                        </div>
                    </div>

                    <div class="early-access-benefits">
                        <h3 class="benefits-title">VIP Benefits</h3>
                        <ul class="benefits-list">
                            <li class="benefit-item">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                <span>Priority Access</span>
                            </li>
                            <li class="benefit-item">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M20.59 13.41L13.42 20.58C13.2343 20.766 13.0137 20.9135 12.7709 21.0141C12.5281 21.1148 12.2678 21.1666 12.005 21.1666C11.7422 21.1666 11.4819 21.1148 11.2391 21.0141C10.9963 20.9135 10.7757 20.766 10.59 20.58L2 12V2H12L20.59 10.59C20.9625 10.9647 21.1716 11.4716 21.1716 12C21.1716 12.5284 20.9625 13.0353 20.59 13.41Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 7H7.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                <span>Exclusive Pricing</span>
                            </li>
                            <li class="benefit-item">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                <span>48hr Head Start</span>
                            </li>
                            <li class="benefit-item">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                    <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M12 15V3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                <span>Free Shipping</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Pre-Order Products Section -->
    <section class="preorder-products-section section" data-gsap="fade-up">
        <div class="container">
            <?php if (!empty($grouped_products['blooming_soon'])) : ?>
                <!-- Blooming Soon Products -->
                <div class="products-group" data-status="blooming_soon">
                    <header class="group-header" data-gsap="fade-up">
                        <div class="status-badge status-blooming-soon">
                            <span class="status-dot" aria-hidden="true"></span>
                            <span class="status-text">Blooming Soon</span>
                        </div>
                        <h2 class="group-title">Upcoming Releases</h2>
                        <p class="group-description">
                            These exclusive pieces are currently in production. Join the waitlist to be notified the moment they become available.
                        </p>
                    </header>

                    <div class="products-grid">
                        <?php foreach ($grouped_products['blooming_soon'] as $index => $product) :
                            $launch_date_iso = !empty($product['launch_date'])
                                ? date('c', strtotime($product['launch_date']))
                                : '';
                            $collection_data = !empty($product['collection'])
                                ? skyyrose_get_collection($product['collection'])
                                : null;
                        ?>
                            <article
                                class="preorder-product-card glass-card"
                                data-product-id="<?php echo esc_attr($product['id']); ?>"
                                data-launch-date="<?php echo esc_attr($launch_date_iso); ?>"
                                data-status="blooming_soon"
                                data-gsap="fade-up"
                                data-gsap-delay="<?php echo esc_attr(0.1 * ($index % 4)); ?>"
                            >
                                <div class="card-glow" aria-hidden="true"></div>

                                <!-- Product Image -->
                                <div class="product-image-wrapper">
                                    <?php if ($product['ar_enabled']) : ?>
                                        <span class="ar-badge glass-badge" title="AR Quick Look Available">
                                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                                <path d="M8 2L2 5.33333V10.6667L8 14L14 10.6667V5.33333L8 2Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M2 5.33334L8 8.66668L14 5.33334" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M8 14V8.66666" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                            <span class="sr-only">AR Quick Look</span>
                                        </span>
                                    <?php endif; ?>

                                    <?php if ($collection_data) : ?>
                                        <span
                                            class="collection-badge"
                                            style="--badge-color: <?php echo esc_attr($collection_data['colors']['primary']); ?>"
                                        >
                                            <?php echo esc_html($collection_data['name']); ?>
                                        </span>
                                    <?php endif; ?>

                                    <a href="<?php echo esc_url($product['link']); ?>" class="product-image-link">
                                        <?php if (!empty($product['image'])) : ?>
                                            <img
                                                src="<?php echo esc_url($product['image']); ?>"
                                                alt="<?php echo esc_attr($product['name']); ?>"
                                                class="product-image"
                                                loading="lazy"
                                            >
                                        <?php else : ?>
                                            <div class="product-image-placeholder">
                                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                                                    <path d="M42 38V10C42 7.79086 40.2091 6 38 6H10C7.79086 6 6 7.79086 6 10V38C6 40.2091 7.79086 42 10 42H38C40.2091 42 42 40.2091 42 38Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    <path d="M17 20C18.6569 20 20 18.6569 20 17C20 15.3431 18.6569 14 17 14C15.3431 14 14 15.3431 14 17C14 18.6569 15.3431 20 17 20Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    <path d="M42 30L33 21L10 44" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                </svg>
                                            </div>
                                        <?php endif; ?>
                                    </a>
                                </div>

                                <!-- Product Info -->
                                <div class="product-info">
                                    <h3 class="product-name">
                                        <a href="<?php echo esc_url($product['link']); ?>">
                                            <?php echo esc_html($product['name']); ?>
                                        </a>
                                    </h3>

                                    <!-- Countdown Timer -->
                                    <?php if (!empty($product['launch_date'])) : ?>
                                        <div
                                            class="countdown-timer"
                                            data-countdown-target="<?php echo esc_attr($launch_date_iso); ?>"
                                            aria-label="Time until launch"
                                        >
                                            <div class="countdown-unit">
                                                <span class="countdown-value" data-countdown-days>--</span>
                                                <span class="countdown-label">Days</span>
                                            </div>
                                            <span class="countdown-separator" aria-hidden="true">:</span>
                                            <div class="countdown-unit">
                                                <span class="countdown-value" data-countdown-hours>--</span>
                                                <span class="countdown-label">Hours</span>
                                            </div>
                                            <span class="countdown-separator" aria-hidden="true">:</span>
                                            <div class="countdown-unit">
                                                <span class="countdown-value" data-countdown-minutes>--</span>
                                                <span class="countdown-label">Min</span>
                                            </div>
                                            <span class="countdown-separator" aria-hidden="true">:</span>
                                            <div class="countdown-unit">
                                                <span class="countdown-value" data-countdown-seconds>--</span>
                                                <span class="countdown-label">Sec</span>
                                            </div>
                                        </div>
                                    <?php else : ?>
                                        <p class="coming-soon-text">Coming Soon</p>
                                    <?php endif; ?>

                                    <div class="product-price">
                                        <?php echo wp_kses_post($product['price']); ?>
                                    </div>

                                    <button
                                        type="button"
                                        class="btn btn-secondary btn-waitlist magnetic-btn"
                                        data-product-id="<?php echo esc_attr($product['id']); ?>"
                                        data-action="join-waitlist"
                                    >
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                            <path d="M10.6667 14V12.6667C10.6667 11.9594 10.3857 11.2812 9.88562 10.781C9.38552 10.281 8.70724 10 8 10H4C3.29276 10 2.61448 10.281 2.11438 10.781C1.61429 11.2812 1.33334 11.9594 1.33334 12.6667V14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M6 7.33333C7.47276 7.33333 8.66667 6.13943 8.66667 4.66667C8.66667 3.19391 7.47276 2 6 2C4.52724 2 3.33334 3.19391 3.33334 4.66667C3.33334 6.13943 4.52724 7.33333 6 7.33333Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M13.3333 5.33334V9.33334" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M11.3333 7.33334H15.3333" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                        <span>Join Waitlist</span>
                                    </button>
                                </div>
                            </article>
                        <?php endforeach; ?>
                    </div>
                </div>
            <?php endif; ?>

            <?php if (!empty($grouped_products['now_blooming'])) : ?>
                <!-- Now Blooming Products (Available for Pre-Order) -->
                <div class="products-group" data-status="now_blooming">
                    <header class="group-header" data-gsap="fade-up">
                        <div class="status-badge status-now-blooming">
                            <span class="status-dot" aria-hidden="true"></span>
                            <span class="status-text">Now Blooming</span>
                        </div>
                        <h2 class="group-title">Available for Pre-Order</h2>
                        <p class="group-description">
                            These pieces are ready for pre-order. Secure yours now before they sell out.
                        </p>
                    </header>

                    <div class="products-grid">
                        <?php foreach ($grouped_products['now_blooming'] as $index => $product) :
                            $launch_date_iso = !empty($product['launch_date'])
                                ? date('c', strtotime($product['launch_date']))
                                : '';
                            $collection_data = !empty($product['collection'])
                                ? skyyrose_get_collection($product['collection'])
                                : null;
                        ?>
                            <article
                                class="preorder-product-card glass-card preorder-available"
                                data-product-id="<?php echo esc_attr($product['id']); ?>"
                                data-launch-date="<?php echo esc_attr($launch_date_iso); ?>"
                                data-status="now_blooming"
                                data-gsap="fade-up"
                                data-gsap-delay="<?php echo esc_attr(0.1 * ($index % 4)); ?>"
                            >
                                <div class="card-glow card-glow-active" aria-hidden="true"></div>

                                <!-- Product Image -->
                                <div class="product-image-wrapper">
                                    <span class="preorder-badge glass-badge">
                                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                                            <path d="M7 1.16666V12.8333" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M1.16666 7H12.8333" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                        Pre-Order
                                    </span>

                                    <?php if ($product['ar_enabled']) : ?>
                                        <span class="ar-badge glass-badge" title="AR Quick Look Available">
                                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                                <path d="M8 2L2 5.33333V10.6667L8 14L14 10.6667V5.33333L8 2Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M2 5.33334L8 8.66668L14 5.33334" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M8 14V8.66666" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                            <span class="sr-only">AR Quick Look</span>
                                        </span>
                                    <?php endif; ?>

                                    <?php if ($collection_data) : ?>
                                        <span
                                            class="collection-badge"
                                            style="--badge-color: <?php echo esc_attr($collection_data['colors']['primary']); ?>"
                                        >
                                            <?php echo esc_html($collection_data['name']); ?>
                                        </span>
                                    <?php endif; ?>

                                    <a href="<?php echo esc_url($product['link']); ?>" class="product-image-link">
                                        <?php if (!empty($product['image'])) : ?>
                                            <img
                                                src="<?php echo esc_url($product['image']); ?>"
                                                alt="<?php echo esc_attr($product['name']); ?>"
                                                class="product-image"
                                                loading="lazy"
                                            >
                                        <?php else : ?>
                                            <div class="product-image-placeholder">
                                                <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
                                                    <path d="M42 38V10C42 7.79086 40.2091 6 38 6H10C7.79086 6 6 7.79086 6 10V38C6 40.2091 7.79086 42 10 42H38C40.2091 42 42 40.2091 42 38Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    <path d="M17 20C18.6569 20 20 18.6569 20 17C20 15.3431 18.6569 14 17 14C15.3431 14 14 15.3431 14 17C14 18.6569 15.3431 20 17 20Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    <path d="M42 30L33 21L10 44" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                </svg>
                                            </div>
                                        <?php endif; ?>
                                    </a>
                                </div>

                                <!-- Product Info -->
                                <div class="product-info">
                                    <h3 class="product-name">
                                        <a href="<?php echo esc_url($product['link']); ?>">
                                            <?php echo esc_html($product['name']); ?>
                                        </a>
                                    </h3>

                                    <!-- Ships In Timer -->
                                    <?php if (!empty($product['launch_date'])) :
                                        $ship_date = date('F j, Y', strtotime($product['launch_date']));
                                    ?>
                                        <div class="ships-by">
                                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                                <path d="M10.6667 2H1.33334V10.6667H10.6667V2Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M10.6667 5.33334H13.3333L14.6667 7.33334V10.6667H10.6667V5.33334Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M4 14C4.92047 14 5.66667 13.2538 5.66667 12.3333C5.66667 11.4129 4.92047 10.6667 4 10.6667C3.07953 10.6667 2.33334 11.4129 2.33334 12.3333C2.33334 13.2538 3.07953 14 4 14Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                                <path d="M12 14C12.9205 14 13.6667 13.2538 13.6667 12.3333C13.6667 11.4129 12.9205 10.6667 12 10.6667C11.0795 10.6667 10.3333 11.4129 10.3333 12.3333C10.3333 13.2538 11.0795 14 12 14Z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                            <span>Ships by <?php echo esc_html($ship_date); ?></span>
                                        </div>
                                    <?php endif; ?>

                                    <div class="product-price product-price-highlight">
                                        <?php echo wp_kses_post($product['price']); ?>
                                    </div>

                                    <a
                                        href="<?php echo esc_url($product['link']); ?>"
                                        class="btn btn-primary btn-preorder magnetic-btn"
                                    >
                                        <span>Pre-Order Now</span>
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                                            <path d="M3.33334 8H12.6667M12.6667 8L8.66668 4M12.6667 8L8.66668 12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                    </a>
                                </div>
                            </article>
                        <?php endforeach; ?>
                    </div>
                </div>
            <?php endif; ?>

            <?php if (empty($preorder_products)) : ?>
                <!-- No Products Message -->
                <div class="no-products-message glass-card" data-gsap="fade-up">
                    <div class="message-icon">
                        <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                            <path d="M32 16V32L42.6667 37.3333" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M32 56C45.2548 56 56 45.2548 56 32C56 18.7452 45.2548 8 32 8C18.7452 8 8 18.7452 8 32C8 45.2548 18.7452 56 32 56Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <h2>All Current Releases Are Available</h2>
                    <p>There are no upcoming pre-orders at the moment. Sign up for early access to be the first to know when new pieces are announced.</p>
                    <a href="#early-access" class="btn btn-primary magnetic-btn">
                        Get Early Access
                    </a>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <!-- Newsletter CTA Section -->
    <section class="newsletter-cta-section section" data-gsap="fade-up">
        <div class="container">
            <div class="newsletter-cta glass-card" data-gsap="fade-up">
                <div class="cta-content">
                    <h2 class="cta-title">Stay in the Garden</h2>
                    <p class="cta-description">
                        Follow us on social media for behind-the-scenes content, styling tips, and exclusive previews.
                    </p>
                </div>

                <div class="social-links">
                    <a href="<?php echo esc_url(get_theme_mod('skyyrose_instagram', '#')); ?>" class="social-link magnetic-btn" target="_blank" rel="noopener noreferrer" aria-label="Follow us on Instagram">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <rect x="2" y="2" width="20" height="20" rx="5" stroke="currentColor" stroke-width="1.5"/>
                            <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.5"/>
                            <circle cx="18" cy="6" r="1" fill="currentColor"/>
                        </svg>
                    </a>
                    <a href="<?php echo esc_url(get_theme_mod('skyyrose_tiktok', '#')); ?>" class="social-link magnetic-btn" target="_blank" rel="noopener noreferrer" aria-label="Follow us on TikTok">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M9 12C9 14.2091 10.7909 16 13 16C15.2091 16 17 14.2091 17 12V3C17.3333 4.3333 18.6 7 22 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M9 12V21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            <path d="M9 12C5.68629 12 3 14.6863 3 18C3 19.6569 4.34315 21 6 21H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </a>
                    <a href="<?php echo esc_url(get_theme_mod('skyyrose_pinterest', '#')); ?>" class="social-link magnetic-btn" target="_blank" rel="noopener noreferrer" aria-label="Follow us on Pinterest">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M8 14C8 14 9 8 12 8C15 8 15 11 15 12C15 13 14.5 15 12 15C9.5 15 10 12 10 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            <path d="M10 15L8 22" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    </section>
</main>

<style>
/* ==========================================================================
   Pre-Order Page Styles
   ========================================================================== */

/* Hero Section */
.preorder-hero {
    position: relative;
    min-height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.hero-background {
    position: absolute;
    inset: 0;
    z-index: -1;
}

.hero-gradient {
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center, rgba(183, 110, 121, 0.15) 0%, transparent 70%),
                linear-gradient(180deg, var(--skyyrose-black) 0%, rgba(26, 26, 26, 0.9) 100%);
}

.hero-particles {
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(circle at 20% 30%, rgba(183, 110, 121, 0.3) 0%, transparent 2%),
        radial-gradient(circle at 80% 70%, rgba(201, 169, 98, 0.3) 0%, transparent 2%),
        radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 1%);
    animation: particleFloat 20s ease-in-out infinite;
}

@keyframes particleFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(5deg); }
}

.hero-content {
    text-align: center;
    padding: var(--space-8);
}

.hero-eyebrow {
    display: inline-block;
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 500;
    letter-spacing: var(--tracking-luxury);
    text-transform: uppercase;
    color: var(--skyyrose-primary);
    margin-bottom: var(--space-4);
}

.hero-headline {
    font-size: clamp(var(--text-4xl), 10vw, var(--text-7xl));
    font-weight: 400;
    letter-spacing: var(--tracking-tight);
    margin-bottom: var(--space-4);
    background: linear-gradient(135deg, var(--skyyrose-white) 0%, var(--skyyrose-primary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subheadline {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-style: italic;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: var(--space-8);
}

.hero-decoration {
    color: var(--skyyrose-primary);
    opacity: 0.6;
    margin: var(--space-8) auto;
}

.rose-icon {
    animation: rosePulse 4s ease-in-out infinite;
}

@keyframes rosePulse {
    0%, 100% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.1); opacity: 0.8; }
}

.scroll-indicator {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-2);
    color: rgba(255, 255, 255, 0.6);
    font-size: var(--text-sm);
    letter-spacing: var(--tracking-wider);
    text-transform: uppercase;
    transition: color var(--transition-base);
    margin-top: var(--space-8);
}

.scroll-indicator:hover {
    color: var(--skyyrose-primary);
}

.scroll-arrow {
    animation: scrollBounce 2s ease-in-out infinite;
}

@keyframes scrollBounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(8px); }
}

/* Early Access Section */
.early-access-section {
    background: linear-gradient(180deg, transparent 0%, rgba(183, 110, 121, 0.05) 100%);
}

.early-access-wrapper {
    max-width: 900px;
    margin: 0 auto;
}

.early-access-card {
    position: relative;
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: var(--space-12);
    padding: var(--space-12);
    overflow: hidden;
}

@media (max-width: 768px) {
    .early-access-card {
        grid-template-columns: 1fr;
        gap: var(--space-8);
        padding: var(--space-8);
    }
}

.card-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(183, 110, 121, 0.1) 0%, transparent 50%);
    pointer-events: none;
    animation: glowRotate 20s linear infinite;
}

@keyframes glowRotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.early-access-header {
    margin-bottom: var(--space-6);
}

.badge {
    display: inline-block;
    padding: var(--space-1) var(--space-3);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: var(--tracking-wider);
    text-transform: uppercase;
    border-radius: var(--radius-full);
    margin-bottom: var(--space-4);
}

.badge-exclusive {
    background: linear-gradient(135deg, var(--skyyrose-primary) 0%, var(--skyyrose-rose-gold) 100%);
    color: var(--skyyrose-white);
}

.section-title {
    font-size: var(--text-3xl);
    margin-bottom: var(--space-4);
}

.section-description {
    color: rgba(255, 255, 255, 0.7);
    line-height: var(--leading-relaxed);
}

/* Form Styles */
.early-access-form {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}

.form-label {
    font-size: var(--text-sm);
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
}

.input-wrapper {
    position: relative;
}

.glass-input {
    width: 100%;
    padding: var(--space-4) var(--space-4) var(--space-4) var(--space-12);
    font-family: var(--font-body);
    font-size: var(--text-base);
    color: var(--skyyrose-white);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(10px);
    transition: all var(--transition-base);
}

.glass-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

.glass-input:focus {
    outline: none;
    border-color: var(--skyyrose-primary);
    box-shadow: 0 0 0 3px rgba(183, 110, 121, 0.2);
}

.input-icon {
    position: absolute;
    left: var(--space-4);
    top: 50%;
    transform: translateY(-50%);
    color: rgba(255, 255, 255, 0.4);
    pointer-events: none;
}

/* Checkbox Group */
.checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-4);
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    cursor: pointer;
}

.checkbox-label input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
}

.checkbox-custom {
    width: 20px;
    height: 20px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: var(--radius-sm);
    transition: all var(--transition-base);
    position: relative;
}

.checkbox-label input:checked + .checkbox-custom {
    background: var(--checkbox-accent, var(--skyyrose-primary));
    border-color: var(--checkbox-accent, var(--skyyrose-primary));
}

.checkbox-label input:checked + .checkbox-custom::after {
    content: '';
    position: absolute;
    top: 3px;
    left: 6px;
    width: 5px;
    height: 10px;
    border: solid var(--skyyrose-white);
    border-width: 0 2px 2px 0;
    transform: rotate(45deg);
}

.checkbox-text {
    font-size: var(--text-sm);
    color: rgba(255, 255, 255, 0.8);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-4) var(--space-8);
    font-family: var(--font-body);
    font-size: var(--text-sm);
    font-weight: 600;
    letter-spacing: var(--tracking-wider);
    text-transform: uppercase;
    border-radius: var(--radius-lg);
    transition: all var(--transition-base);
    cursor: pointer;
    border: none;
    text-decoration: none;
}

.btn-primary {
    background: linear-gradient(135deg, var(--skyyrose-primary) 0%, var(--skyyrose-rose-gold) 100%);
    color: var(--skyyrose-white);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(183, 110, 121, 0.4);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--skyyrose-white);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--skyyrose-primary);
    color: var(--skyyrose-primary);
}

.btn-glow:hover {
    box-shadow: 0 0 40px rgba(183, 110, 121, 0.5);
}

.btn-loading {
    display: none;
}

.btn.is-loading .btn-text,
.btn.is-loading .btn-icon {
    display: none;
}

.btn.is-loading .btn-loading {
    display: block;
}

.spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.form-privacy {
    font-size: var(--text-xs);
    color: rgba(255, 255, 255, 0.5);
}

.form-privacy a {
    color: var(--skyyrose-primary);
    text-decoration: underline;
}

/* Success Message */
.signup-success {
    text-align: center;
    padding: var(--space-8);
}

.signup-success[hidden] {
    display: none;
}

.success-icon {
    color: var(--skyyrose-primary);
    margin-bottom: var(--space-4);
}

.signup-success h3 {
    font-size: var(--text-2xl);
    margin-bottom: var(--space-2);
}

.signup-success p {
    color: rgba(255, 255, 255, 0.7);
}

/* Benefits List */
.early-access-benefits {
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    padding-left: var(--space-8);
}

@media (max-width: 768px) {
    .early-access-benefits {
        border-left: none;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-left: 0;
        padding-top: var(--space-8);
    }
}

.benefits-title {
    font-size: var(--text-lg);
    font-weight: 500;
    margin-bottom: var(--space-6);
    color: var(--skyyrose-rose-gold);
}

.benefits-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
}

.benefit-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    color: rgba(255, 255, 255, 0.8);
    font-size: var(--text-sm);
}

.benefit-item svg {
    color: var(--skyyrose-primary);
    flex-shrink: 0;
}

/* Products Section */
.preorder-products-section {
    padding-top: var(--space-16);
}

.products-group {
    margin-bottom: var(--space-24);
}

.products-group:last-child {
    margin-bottom: 0;
}

.group-header {
    text-align: center;
    max-width: 600px;
    margin: 0 auto var(--space-12);
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: var(--tracking-wider);
    text-transform: uppercase;
    border-radius: var(--radius-full);
    margin-bottom: var(--space-4);
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: statusPulse 2s ease-in-out infinite;
}

@keyframes statusPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}

.status-blooming-soon {
    background: rgba(201, 169, 98, 0.15);
    border: 1px solid rgba(201, 169, 98, 0.3);
    color: var(--skyyrose-rose-gold);
}

.status-blooming-soon .status-dot {
    background: var(--skyyrose-rose-gold);
}

.status-now-blooming {
    background: rgba(183, 110, 121, 0.15);
    border: 1px solid rgba(183, 110, 121, 0.3);
    color: var(--skyyrose-primary);
}

.status-now-blooming .status-dot {
    background: var(--skyyrose-primary);
}

.group-title {
    font-size: var(--text-3xl);
    margin-bottom: var(--space-4);
}

.group-description {
    color: rgba(255, 255, 255, 0.6);
    line-height: var(--leading-relaxed);
}

/* Products Grid */
.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--space-8);
}

/* Product Card */
.preorder-product-card {
    position: relative;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: all var(--transition-base);
}

.preorder-product-card:hover {
    transform: translateY(-8px);
}

.preorder-product-card:hover .card-glow {
    opacity: 1;
}

.card-glow-active {
    background: radial-gradient(ellipse at center, rgba(183, 110, 121, 0.2) 0%, transparent 50%);
}

/* Product Image */
.product-image-wrapper {
    position: relative;
    aspect-ratio: 3/4;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.02);
}

.product-image-link {
    display: block;
    width: 100%;
    height: 100%;
}

.product-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-slow);
}

.preorder-product-card:hover .product-image {
    transform: scale(1.05);
}

.product-image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.2);
}

/* Badges */
.glass-badge {
    position: absolute;
    z-index: 10;
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-1) var(--space-2);
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--skyyrose-white);
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(10px);
    border-radius: var(--radius-md);
}

.ar-badge {
    top: var(--space-3);
    right: var(--space-3);
}

.preorder-badge {
    top: var(--space-3);
    left: var(--space-3);
    background: linear-gradient(135deg, var(--skyyrose-primary) 0%, var(--skyyrose-rose-gold) 100%);
}

.collection-badge {
    position: absolute;
    bottom: var(--space-3);
    left: var(--space-3);
    padding: var(--space-1) var(--space-3);
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: var(--tracking-wider);
    text-transform: uppercase;
    color: var(--skyyrose-white);
    background: var(--badge-color, var(--skyyrose-primary));
    border-radius: var(--radius-full);
}

/* Product Info */
.product-info {
    padding: var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    flex: 1;
}

.product-name {
    font-size: var(--text-lg);
    font-weight: 500;
    line-height: var(--leading-snug);
}

.product-name a {
    color: var(--skyyrose-white);
    transition: color var(--transition-base);
}

.product-name a:hover {
    color: var(--skyyrose-primary);
}

/* Countdown Timer */
.countdown-timer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-4);
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius-lg);
}

.countdown-unit {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 44px;
}

.countdown-value {
    font-family: var(--font-body);
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--skyyrose-rose-gold);
    font-variant-numeric: tabular-nums;
}

.countdown-label {
    font-size: var(--text-xs);
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: var(--tracking-wider);
}

.countdown-separator {
    font-size: var(--text-xl);
    color: rgba(255, 255, 255, 0.3);
    font-weight: 300;
}

.coming-soon-text {
    text-align: center;
    font-style: italic;
    color: rgba(255, 255, 255, 0.6);
}

/* Ships By */
.ships-by {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: rgba(255, 255, 255, 0.7);
}

.ships-by svg {
    color: var(--skyyrose-primary);
    flex-shrink: 0;
}

/* Product Price */
.product-price {
    font-size: var(--text-lg);
    font-weight: 500;
}

.product-price-highlight {
    color: var(--skyyrose-primary);
}

.product-price del {
    color: rgba(255, 255, 255, 0.4);
    font-size: var(--text-sm);
    margin-right: var(--space-2);
}

.product-price ins {
    text-decoration: none;
}

/* CTA Buttons */
.btn-waitlist,
.btn-preorder {
    margin-top: auto;
}

/* No Products Message */
.no-products-message {
    text-align: center;
    padding: var(--space-16);
    max-width: 500px;
    margin: 0 auto;
}

.message-icon {
    color: var(--skyyrose-primary);
    margin-bottom: var(--space-6);
}

.no-products-message h2 {
    font-size: var(--text-2xl);
    margin-bottom: var(--space-4);
}

.no-products-message p {
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: var(--space-8);
}

/* Newsletter CTA Section */
.newsletter-cta-section {
    padding-bottom: var(--space-32);
}

.newsletter-cta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-8);
    padding: var(--space-12);
    text-align: center;
}

@media (min-width: 768px) {
    .newsletter-cta {
        text-align: left;
    }
}

.cta-content {
    flex: 1;
    min-width: 250px;
}

.cta-title {
    font-size: var(--text-2xl);
    margin-bottom: var(--space-2);
}

.cta-description {
    color: rgba(255, 255, 255, 0.6);
}

.social-links {
    display: flex;
    gap: var(--space-4);
}

.social-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    color: var(--skyyrose-white);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    transition: all var(--transition-base);
}

.social-link:hover {
    background: var(--skyyrose-primary);
    border-color: var(--skyyrose-primary);
    transform: translateY(-2px);
}

/* Glass Card Base */
.glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-2xl);
    backdrop-filter: var(--glass-blur);
}

/* Magnetic Button Hover Effect (handled by JS) */
.magnetic-btn {
    will-change: transform;
}

/* Responsive Adjustments */
@media (max-width: 480px) {
    .countdown-timer {
        flex-wrap: wrap;
    }

    .countdown-separator {
        display: none;
    }

    .countdown-unit {
        width: calc(50% - var(--space-2));
        padding: var(--space-2);
        background: rgba(255, 255, 255, 0.02);
        border-radius: var(--radius-md);
    }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
    .hero-particles,
    .card-glow,
    .rose-icon,
    .scroll-arrow,
    .status-dot,
    .spinner {
        animation: none;
    }

    .preorder-product-card:hover {
        transform: none;
    }
}
</style>

<?php
get_footer();
