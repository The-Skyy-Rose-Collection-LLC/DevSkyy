<?php
/**
 * Template Name: Immersive Full-Screen Experience
 * Description: Full-screen immersive canvas with 3D scenes, minimal UI, and luxury interactions
 *
 * Features:
 * - 100vh full-screen canvas (no header/footer)
 * - Progressive page loader with rose gold spinner
 * - Embed any collection immersive scene or LuxuryProductViewer
 * - Glassmorphism navigation overlay
 * - Call-to-action overlays
 * - Mobile detection and optimization
 * - Accessibility features (keyboard nav, screen reader)
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

// Get immersive mode configuration
$immersive_mode = get_post_meta(get_the_ID(), '_immersive_mode', true) ?: 'collection';
$scene_type = get_post_meta(get_the_ID(), '_scene_type', true) ?: 'black-rose';
$show_cta = get_post_meta(get_the_ID(), '_show_cta', true) !== 'no';
$show_nav = get_post_meta(get_the_ID(), '_show_nav', true) !== 'no';
$product_id = get_post_meta(get_the_ID(), '_featured_product_id', true);

// Scene configurations
$scene_configs = [
    'black-rose' => [
        'title' => 'Black Rose',
        'tagline' => 'Gothic Elegance',
        'color' => '#8B0000',
        'collection' => 'black-rose',
        'class' => 'BlackRoseExperience',
        'script' => 'black-rose-scene.js',
    ],
    'love-hurts' => [
        'title' => 'Love Hurts',
        'tagline' => 'Romantic Rebellion',
        'color' => '#B76E79',
        'collection' => 'love-hurts',
        'class' => 'LoveHurtsCastleExperience',
        'script' => 'love-hurts-scene.js',
    ],
    'signature' => [
        'title' => 'Signature',
        'tagline' => 'Oakland Pride',
        'color' => '#D4AF37',
        'collection' => 'signature',
        'class' => 'SignatureLandmarksTour',
        'script' => 'signature-scene.js',
    ],
];

$config = $scene_configs[$scene_type] ?? $scene_configs['black-rose'];

// Check for mobile
$is_mobile = wp_is_mobile();
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="<?php echo esc_attr($config['color']); ?>">
    <title><?php echo esc_html($config['title']); ?> | <?php bloginfo('name'); ?></title>
    <?php wp_head(); ?>
</head>
<body <?php body_class('immersive-body'); ?>>

<!-- Skip to Content (Accessibility) -->
<a href="#main-content" class="skip-to-content sr-only sr-only-focusable">
    Skip to main content
</a>

<!-- Progressive Page Loader -->
<div id="immersive-loader" class="immersive-loader" role="status" aria-live="polite">
    <div class="loader-container">
        <div class="rose-gold-spinner" aria-hidden="true"></div>
        <div class="loader-text" id="loaderText">Loading Experience...</div>
        <div class="loader-progress">
            <div class="loader-progress-bar" id="loaderProgressBar"></div>
        </div>
    </div>
</div>

<!-- Navigation Overlay (Glassmorphism) -->
<?php if ($show_nav) : ?>
<nav id="immersive-nav" class="immersive-nav" role="navigation" aria-label="Main Navigation">
    <button
        id="navToggle"
        class="nav-hamburger"
        aria-label="Toggle Navigation Menu"
        aria-expanded="false"
        aria-controls="navMenu"
    >
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
    </button>

    <div id="navMenu" class="nav-menu" role="menu" hidden>
        <div class="nav-menu-header">
            <a href="<?php echo esc_url(home_url('/')); ?>" class="nav-logo" aria-label="SkyyRose Home">
                SkyyRose
            </a>
            <button
                id="navClose"
                class="nav-close"
                aria-label="Close Navigation Menu"
            >
                <span aria-hidden="true">&times;</span>
            </button>
        </div>

        <ul class="nav-links" role="none">
            <li role="menuitem">
                <a href="<?php echo esc_url(home_url('/black-rose')); ?>">Black Rose</a>
            </li>
            <li role="menuitem">
                <a href="<?php echo esc_url(home_url('/love-hurts')); ?>">Love Hurts</a>
            </li>
            <li role="menuitem">
                <a href="<?php echo esc_url(home_url('/signature')); ?>">Signature</a>
            </li>
            <li role="menuitem">
                <a href="<?php echo esc_url(home_url('/vault')); ?>">Vault</a>
            </li>
            <li role="menuitem">
                <a href="<?php echo esc_url(wc_get_cart_url()); ?>">Cart</a>
            </li>
        </ul>

        <div class="nav-cta">
            <a href="<?php echo esc_url(home_url('/vault')); ?>" class="btn-nav-primary">
                Pre-Order Vault
            </a>
        </div>
    </div>
</nav>
<?php endif; ?>

<!-- Full-Screen Canvas Container -->
<main id="main-content" class="immersive-canvas-container" role="main">
    <?php if ($is_mobile) : ?>
        <!-- Mobile Fallback or Simplified Version -->
        <div class="mobile-fallback" role="alert">
            <div class="mobile-fallback-content">
                <h1><?php echo esc_html($config['title']); ?></h1>
                <p>For the best immersive experience, please visit us on desktop.</p>
                <a href="<?php echo esc_url(home_url('/' . $config['collection'])); ?>" class="btn-mobile">
                    View Collection
                </a>
            </div>
        </div>
    <?php else : ?>
        <!-- Desktop: Full 3D Canvas -->
        <div id="immersive-scene" class="immersive-scene" data-scene="<?php echo esc_attr($scene_type); ?>"></div>

        <!-- Call-to-Action Overlays -->
        <?php if ($show_cta) : ?>
        <div class="cta-overlay cta-bottom-left">
            <a
                href="<?php echo esc_url(home_url('/' . $config['collection'])); ?>"
                class="btn-cta btn-cta-primary"
                aria-label="Shop <?php echo esc_attr($config['title']); ?> Collection"
            >
                Shop Collection
            </a>
        </div>

        <div class="cta-overlay cta-bottom-right">
            <a
                href="<?php echo esc_url(home_url('/vault')); ?>"
                class="btn-cta btn-cta-vault"
                aria-label="Access Pre-Order Vault"
            >
                Pre-Order Vault
            </a>
        </div>
        <?php endif; ?>

        <!-- Product Quick-View Modal -->
        <div id="quickViewModal" class="quick-view-modal" role="dialog" aria-labelledby="quickViewTitle" aria-modal="true" hidden>
            <div class="quick-view-content">
                <button
                    id="quickViewClose"
                    class="quick-view-close"
                    aria-label="Close Quick View"
                >
                    <span aria-hidden="true">&times;</span>
                </button>

                <div id="quickViewBody" class="quick-view-body">
                    <!-- Dynamically populated by JS -->
                </div>
            </div>
        </div>

        <!-- Controls Hint (Fades after 5s) -->
        <div id="controlsHint" class="controls-hint" role="status" aria-live="polite">
            <p>
                <kbd>Drag</kbd> to explore &nbsp;|&nbsp; <kbd>Scroll</kbd> to zoom &nbsp;|&nbsp;
                <kbd>Click</kbd> products for details
            </p>
        </div>
    <?php endif; ?>
</main>

<!-- Screen Reader Announcements -->
<div class="sr-only" role="status" aria-live="polite" aria-atomic="true" id="srAnnouncements"></div>

<style>
/* Immersive Template Styles */
:root {
    --immersive-color: <?php echo esc_attr($config['color']); ?>;
    --rose-gold: #B76E79;
    --dark-slate: #1a1a1a;
    --gold: #D4AF37;
    --glass-bg: rgba(26, 26, 26, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-blur: blur(20px);
}

/* Reset body/html for full immersion */
.immersive-body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: #000;
    color: #fff;
}

.immersive-body #wpadminbar {
    display: none !important;
}

/* Skip to Content */
.skip-to-content {
    position: fixed;
    top: -100px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--immersive-color);
    color: #000;
    padding: 1rem 2rem;
    border-radius: 4px;
    z-index: 10000;
    transition: top 0.3s ease;
    font-weight: 600;
    text-decoration: none;
}

.skip-to-content:focus {
    top: 20px;
    outline: 3px solid #fff;
    outline-offset: 2px;
}

/* Screen Reader Only */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
    white-space: nowrap;
    border: 0;
}

.sr-only-focusable:focus {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    clip: auto;
    white-space: normal;
}

/* Progressive Loader */
.immersive-loader {
    position: fixed;
    inset: 0;
    background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    transition: opacity 0.8s ease, visibility 0.8s ease;
}

.immersive-loader.fade-out {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
}

.loader-container {
    text-align: center;
}

.rose-gold-spinner {
    width: 80px;
    height: 80px;
    margin: 0 auto 2rem;
    border: 4px solid rgba(183, 110, 121, 0.2);
    border-top-color: var(--rose-gold);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loader-text {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 1rem;
    letter-spacing: 2px;
}

.loader-progress {
    width: 200px;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    margin: 0 auto;
}

.loader-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--rose-gold), var(--gold));
    width: 0%;
    transition: width 0.3s ease;
}

/* Navigation Overlay (Glassmorphism) */
.immersive-nav {
    position: fixed;
    top: 2rem;
    left: 2rem;
    z-index: 1000;
}

.nav-hamburger {
    width: 50px;
    height: 50px;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 5px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.nav-hamburger:hover,
.nav-hamburger:focus {
    background: rgba(183, 110, 121, 0.3);
    border-color: var(--rose-gold);
    outline: none;
    transform: scale(1.05);
}

.hamburger-line {
    width: 24px;
    height: 2px;
    background: #fff;
    transition: all 0.3s ease;
}

.nav-hamburger:hover .hamburger-line {
    background: var(--rose-gold);
}

.nav-menu {
    position: fixed;
    top: 0;
    left: 0;
    width: 350px;
    height: 100vh;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border-right: 1px solid var(--glass-border);
    transform: translateX(-100%);
    transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    padding: 2rem;
    overflow-y: auto;
}

.nav-menu.open {
    transform: translateX(0);
}

.nav-menu-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3rem;
}

.nav-logo {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    color: var(--rose-gold);
    text-decoration: none;
    font-weight: 600;
}

.nav-close {
    background: transparent;
    border: none;
    color: #fff;
    font-size: 3rem;
    cursor: pointer;
    line-height: 1;
    transition: color 0.3s ease;
}

.nav-close:hover,
.nav-close:focus {
    color: var(--rose-gold);
    outline: none;
}

.nav-links {
    list-style: none;
    padding: 0;
    margin: 0 0 3rem 0;
}

.nav-links li {
    margin-bottom: 1.5rem;
}

.nav-links a {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 1.2rem;
    letter-spacing: 1px;
    transition: all 0.3s ease;
    display: block;
    padding: 0.5rem 0;
    border-left: 3px solid transparent;
    padding-left: 1rem;
}

.nav-links a:hover,
.nav-links a:focus {
    color: var(--rose-gold);
    border-left-color: var(--rose-gold);
    transform: translateX(5px);
    outline: none;
}

.nav-cta {
    margin-top: auto;
}

.btn-nav-primary {
    display: block;
    text-align: center;
    background: linear-gradient(135deg, var(--rose-gold), var(--gold));
    color: #000;
    padding: 1rem 2rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    transition: all 0.3s ease;
}

.btn-nav-primary:hover,
.btn-nav-primary:focus {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(183, 110, 121, 0.5);
    outline: none;
}

/* Full-Screen Canvas */
.immersive-canvas-container {
    position: relative;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
}

.immersive-scene {
    width: 100%;
    height: 100%;
    background: #000;
}

/* Call-to-Action Overlays */
.cta-overlay {
    position: fixed;
    z-index: 100;
}

.cta-bottom-left {
    bottom: 3rem;
    left: 3rem;
}

.cta-bottom-right {
    bottom: 3rem;
    right: 3rem;
}

.btn-cta {
    display: inline-block;
    padding: 1rem 2rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    transition: all 0.4s ease;
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    color: #fff;
    font-size: 0.9rem;
}

.btn-cta-primary {
    border-color: var(--immersive-color);
    color: var(--immersive-color);
}

.btn-cta-primary:hover,
.btn-cta-primary:focus {
    background: var(--immersive-color);
    color: #000;
    box-shadow: 0 0 30px var(--immersive-color);
    transform: translateY(-3px);
    outline: 3px solid rgba(255, 255, 255, 0.3);
    outline-offset: 2px;
}

.btn-cta-vault {
    border-color: var(--rose-gold);
    color: var(--rose-gold);
}

.btn-cta-vault:hover,
.btn-cta-vault:focus {
    background: var(--rose-gold);
    color: #000;
    box-shadow: 0 0 30px var(--rose-gold);
    transform: translateY(-3px);
    outline: 3px solid rgba(255, 255, 255, 0.3);
    outline-offset: 2px;
}

/* Quick View Modal */
.quick-view-modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.quick-view-modal.active {
    opacity: 1;
}

.quick-view-content {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 3rem;
    max-width: 800px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    position: relative;
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.quick-view-modal.active .quick-view-content {
    transform: scale(1);
}

.quick-view-close {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: transparent;
    border: none;
    color: #fff;
    font-size: 2.5rem;
    cursor: pointer;
    line-height: 1;
    transition: color 0.3s ease;
}

.quick-view-close:hover,
.quick-view-close:focus {
    color: var(--rose-gold);
    outline: none;
}

.quick-view-body {
    color: #fff;
}

/* Controls Hint */
.controls-hint {
    position: fixed;
    bottom: 8rem;
    left: 50%;
    transform: translateX(-50%);
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 30px;
    padding: 1rem 2rem;
    z-index: 99;
    animation: fadeInOut 5s ease-in-out forwards;
}

.controls-hint p {
    margin: 0;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
}

.controls-hint kbd {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    color: var(--rose-gold);
}

@keyframes fadeInOut {
    0%, 100% { opacity: 0; }
    10%, 90% { opacity: 1; }
}

/* Mobile Fallback */
.mobile-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
    padding: 2rem;
}

.mobile-fallback-content {
    text-align: center;
    max-width: 400px;
}

.mobile-fallback h1 {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    color: var(--immersive-color);
    margin-bottom: 1rem;
}

.mobile-fallback p {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.8;
    margin-bottom: 2rem;
}

.btn-mobile {
    display: inline-block;
    padding: 1rem 2rem;
    background: var(--immersive-color);
    color: #000;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    transition: all 0.3s ease;
}

.btn-mobile:hover,
.btn-mobile:focus {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px var(--immersive-color);
    outline: 3px solid rgba(255, 255, 255, 0.3);
    outline-offset: 2px;
}

/* Responsive */
@media (max-width: 768px) {
    .nav-menu {
        width: 100%;
        border-right: none;
    }

    .cta-overlay {
        bottom: 1.5rem;
        left: 50%;
        transform: translateX(-50%);
    }

    .cta-bottom-left,
    .cta-bottom-right {
        position: static;
        margin-bottom: 1rem;
    }

    .btn-cta {
        font-size: 0.8rem;
        padding: 0.8rem 1.5rem;
    }

    .controls-hint {
        display: none;
    }
}
</style>

<script>
// Immersive Template JavaScript
(function() {
    'use strict';

    // DOM Elements
    const loader = document.getElementById('immersive-loader');
    const loaderText = document.getElementById('loaderText');
    const loaderProgressBar = document.getElementById('loaderProgressBar');
    const navToggle = document.getElementById('navToggle');
    const navClose = document.getElementById('navClose');
    const navMenu = document.getElementById('navMenu');
    const sceneContainer = document.getElementById('immersive-scene');
    const quickViewModal = document.getElementById('quickViewModal');
    const quickViewClose = document.getElementById('quickViewClose');
    const srAnnouncements = document.getElementById('srAnnouncements');

    let experience = null;
    let progress = 0;

    // Screen reader announcement
    function announce(message) {
        if (srAnnouncements) {
            srAnnouncements.textContent = message;
        }
    }

    // Progressive loader
    function updateLoader(percent, message) {
        progress = Math.min(percent, 100);
        if (loaderProgressBar) loaderProgressBar.style.width = progress + '%';
        if (loaderText && message) loaderText.textContent = message;
    }

    function hideLoader() {
        if (loader) {
            loader.classList.add('fade-out');
            setTimeout(() => {
                loader.remove();
                announce('Experience loaded');
            }, 800);
        }
    }

    // Navigation
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.add('open');
            navMenu.hidden = false;
            navToggle.setAttribute('aria-expanded', 'true');
            announce('Navigation menu opened');
        });
    }

    if (navClose && navMenu) {
        navClose.addEventListener('click', () => {
            navMenu.classList.remove('open');
            navMenu.hidden = true;
            if (navToggle) navToggle.setAttribute('aria-expanded', 'false');
            announce('Navigation menu closed');
        });
    }

    // Keyboard navigation
    if (navMenu) {
        navMenu.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                navClose.click();
            }
        });
    }

    // Quick View Modal
    if (quickViewClose && quickViewModal) {
        quickViewClose.addEventListener('click', () => {
            quickViewModal.classList.remove('active');
            quickViewModal.hidden = true;
            announce('Product quick view closed');
        });
    }

    if (quickViewModal) {
        quickViewModal.addEventListener('click', (e) => {
            if (e.target === quickViewModal) {
                quickViewClose.click();
            }
        });

        quickViewModal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                quickViewClose.click();
            }
        });
    }

    // Load and initialize 3D scene
    function initializeScene() {
        if (!sceneContainer) return;

        const sceneType = sceneContainer.dataset.scene;
        updateLoader(10, 'Loading assets...');

        <?php if ($immersive_mode === 'product' && $product_id) : ?>
        // Single product viewer mode
        <?php
        $product = wc_get_product($product_id);
        $model_url = get_post_meta($product_id, '_3d_model_url', true);
        ?>
        updateLoader(30, 'Loading product model...');

        if (typeof LuxuryProductViewer !== 'undefined') {
            experience = new LuxuryProductViewer(sceneContainer, {
                modelUrl: <?php echo json_encode($model_url); ?>,
                productName: <?php echo json_encode($product->get_name()); ?>,
                autoRotate: true,
                showEffects: true,
                enableAR: true,
                onProgress: (percent) => {
                    updateLoader(30 + (percent * 0.6), 'Loading product model...');
                },
                onLoad: () => {
                    updateLoader(100, 'Ready!');
                    setTimeout(hideLoader, 500);
                }
            });
        } else {
            console.error('LuxuryProductViewer not loaded');
            updateLoader(100, 'Error loading viewer');
        }

        <?php else : ?>
        // Collection scene mode
        updateLoader(20, 'Loading scene...');

        const sceneClass = <?php echo json_encode($config['class']); ?>;
        const collection = <?php echo json_encode($config['collection']); ?>;

        if (typeof window[sceneClass] !== 'undefined') {
            const SceneClass = window[sceneClass];
            experience = new SceneClass(sceneContainer, {
                <?php if ($scene_type === 'black-rose') : ?>
                backgroundColor: 0x0d0d0d,
                fogDensity: 0.03,
                petalCount: 50,
                enableBloom: true,
                <?php elseif ($scene_type === 'love-hurts') : ?>
                backgroundColor: 0x1a0a0a,
                fogDensity: 0.02,
                enableBloom: true,
                <?php else : ?>
                backgroundColor: 0xf5f5f0,
                fogNear: 10,
                fogFar: 200,
                timeOfDay: 'golden-hour',
                <?php endif; ?>
                onProgress: (percent) => {
                    updateLoader(20 + (percent * 0.4), 'Loading scene...');
                }
            });

            updateLoader(60, 'Loading products...');

            // Fetch products from WooCommerce
            fetch('<?php echo esc_url(admin_url('admin-ajax.php')); ?>?action=get_collection_products&collection=' + collection)
                .then(response => response.json())
                .then(data => {
                    updateLoader(80, 'Initializing...');

                    if (data.success && data.data) {
                        experience.loadProducts(data.data);
                        experience.start();

                        // Product click handler
                        if (experience.setOnProductClick) {
                            experience.setOnProductClick(function(product) {
                                window.location.href = product.url;
                            });
                        }

                        // Product hover handler
                        if (experience.setOnProductHover) {
                            experience.setOnProductHover(function(product) {
                                if (product) {
                                    announce('Hovering over ' + product.name);
                                }
                            });
                        }

                        updateLoader(100, 'Ready!');
                        setTimeout(hideLoader, 500);
                    } else {
                        console.error('Failed to load products');
                        updateLoader(100, 'Error loading products');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    updateLoader(100, 'Error loading experience');
                });
        } else {
            console.error('Scene class not loaded:', sceneClass);
            updateLoader(100, 'Error: Scene not available');
        }
        <?php endif; ?>
    }

    // Preload critical assets
    function preloadAssets() {
        const assets = [
            <?php echo json_encode(get_template_directory_uri() . '/assets/js/' . $config['script']); ?>,
        ];

        let loaded = 0;
        assets.forEach(src => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = () => {
                loaded++;
                updateLoader((loaded / assets.length) * 10, 'Preloading...');
                if (loaded === assets.length) {
                    initializeScene();
                }
            };
            script.onerror = () => {
                console.error('Failed to load:', src);
                initializeScene(); // Continue anyway
            };
            document.head.appendChild(script);
        });
    }

    // Start loading
    document.addEventListener('DOMContentLoaded', () => {
        updateLoader(5, 'Initializing...');
        setTimeout(preloadAssets, 100);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // ESC to close modal
        if (e.key === 'Escape' && quickViewModal && !quickViewModal.hidden) {
            quickViewClose.click();
        }

        // M to toggle menu
        if (e.key === 'm' && navToggle) {
            navToggle.click();
        }
    });

    // Cleanup on unload
    window.addEventListener('beforeunload', () => {
        if (experience && experience.dispose) {
            experience.dispose();
        }
    });
})();
</script>

<?php wp_footer(); ?>
</body>
</html>
