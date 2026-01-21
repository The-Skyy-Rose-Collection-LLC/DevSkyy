<?php
/**
 * Template Name: Signature Collection (Immersive 3D)
 * Template Post Type: page
 *
 * Immersive 3D fashion runway experience for the SIGNATURE Collection
 * Rose Gold (#B76E79) + Gold (#D4AF37) theme
 *
 * @package SkyyRose_Immersive
 * @since 1.0.0
 */

defined('ABSPATH') || exit;

// Get collection products from WooCommerce
$signature_products = wc_get_products(array(
    'limit' => 12,
    'status' => 'publish',
    'category' => array('signature', 'signature-collection'),
    'orderby' => 'menu_order',
    'order' => 'ASC',
));

// Fallback demo products if no WooCommerce products
$demo_products = array(
    array(
        'id' => 'foundation-blazer',
        'title' => 'Foundation Blazer',
        'price' => '$395',
        'description' => 'Premium Italian wool blend blazer with gold-tone hardware and silk lining. The cornerstone of elevated style.',
        'badge' => 'Investment Piece',
        'emoji' => '🧥',
        'position' => array('x' => -4, 'y' => 1.5, 'z' => 2)
    ),
    array(
        'id' => 'essential-trouser',
        'title' => 'Essential Trouser',
        'price' => '$245',
        'description' => 'Tailored wool trousers with perfect drape and hidden stretch. All-day sophistication.',
        'badge' => 'Foundation',
        'emoji' => '👖',
        'position' => array('x' => 4, 'y' => 1.5, 'z' => 2)
    ),
    array(
        'id' => 'luxury-cotton-tee',
        'title' => 'Luxury Cotton Tee',
        'price' => '$125',
        'description' => 'Pima cotton tee with rose gold thread detail at hem. The foundation of any outfit.',
        'badge' => 'Essential',
        'emoji' => '👕',
        'position' => array('x' => 0, 'y' => 1.5, 'z' => 4)
    ),
    array(
        'id' => 'heritage-overcoat',
        'title' => 'Heritage Overcoat',
        'price' => '$595',
        'description' => 'Double-faced cashmere blend coat with timeless silhouette. Investment dressing at its finest.',
        'badge' => 'Flagship',
        'emoji' => '🧥',
        'position' => array('x' => -2, 'y' => 1.5, 'z' => -2)
    ),
);

// Build products array for JS
$products_for_js = array();
if (!empty($signature_products)) {
    foreach ($signature_products as $index => $product) {
        $positions = array(
            array('x' => -4, 'y' => 1.5, 'z' => 2),
            array('x' => 4, 'y' => 1.5, 'z' => 2),
            array('x' => 0, 'y' => 1.5, 'z' => 4),
            array('x' => -2, 'y' => 1.5, 'z' => -2),
        );
        $products_for_js[] = array(
            'id' => $product->get_id(),
            'title' => $product->get_name(),
            'price' => wc_price($product->get_price()),
            'price_raw' => $product->get_price(),
            'description' => wp_trim_words($product->get_short_description(), 20),
            'image' => wp_get_attachment_url($product->get_image_id()),
            'badge' => 'Signature',
            'permalink' => $product->get_permalink(),
            'position' => $positions[$index % 4],
        );
    }
} else {
    $products_for_js = $demo_products;
}

get_header();
?>

<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIGNATURE Collection | SkyyRose Virtual Runway</title>
    <meta name="description" content="Enter the SIGNATURE virtual runway - an immersive 3D fashion experience featuring SkyyRose's premium foundation collection">

    <!-- Import Maps for Three.js ES Modules -->
    <script type="importmap">
    {
        "imports": {
            "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
            "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
        }
    }
    </script>

    <style>
        /* SkyyRose SIGNATURE Collection Theme - Rose Gold + Gold */
        :root {
            --sr-rose-gold: #B76E79;
            --sr-gold: #D4AF37;
            --sr-champagne: #F7E7CE;
            --sr-black: #0A0A0A;
            --sr-charcoal: #1A1A1A;
            --sr-cream: #FFFDD0;
            --font-display: 'Playfair Display', Georgia, serif;
            --font-body: 'Inter', -apple-system, sans-serif;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

        body {
            font-family: var(--font-body);
            background: var(--sr-black);
            color: #fff;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }

        /* Loading Screen */
        #loading-screen {
            position: fixed;
            inset: 0;
            background: linear-gradient(135deg, var(--sr-black) 0%, #1a1510 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.8s ease, visibility 0.8s ease;
        }

        #loading-screen.hidden {
            opacity: 0;
            visibility: hidden;
        }

        .loading-logo {
            font-family: var(--font-display);
            font-size: 3rem;
            font-weight: 600;
            letter-spacing: 0.3em;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, var(--sr-rose-gold), var(--sr-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 2s ease-in-out infinite;
        }

        @keyframes shimmer {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .loading-subtitle {
            font-size: 0.9rem;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: var(--sr-gold);
            margin-bottom: 3rem;
        }

        .loading-progress {
            width: 200px;
            height: 2px;
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
            overflow: hidden;
        }

        .loading-bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--sr-rose-gold), var(--sr-gold));
            transition: width 0.3s ease;
        }

        /* Canvas Container */
        #canvas-container {
            position: fixed;
            inset: 0;
            z-index: 1;
        }

        canvas { display: block; }

        /* Collection Title Overlay */
        .collection-header {
            position: fixed;
            top: 2rem;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
            z-index: 100;
            pointer-events: none;
        }

        .collection-name {
            font-family: var(--font-display);
            font-size: 2.5rem;
            font-weight: 600;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            background: linear-gradient(180deg, var(--sr-gold) 0%, var(--sr-rose-gold) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(183, 110, 121, 0.5);
        }

        .collection-tagline {
            font-size: 0.85rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: var(--sr-champagne);
            margin-top: 0.5rem;
            opacity: 0.8;
        }

        /* Hotspots */
        .hotspot {
            position: absolute;
            width: 44px;
            height: 44px;
            cursor: pointer;
            pointer-events: auto;
            transform: translate(-50%, -50%);
            z-index: 50;
        }

        .hotspot-inner {
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, var(--sr-gold) 0%, transparent 70%);
            border: 2px solid var(--sr-rose-gold);
            border-radius: 50%;
            animation: hotspot-pulse 2s ease-in-out infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }

        .hotspot-inner::before {
            content: '+';
            font-size: 1.2rem;
            color: #fff;
            font-weight: 300;
        }

        @keyframes hotspot-pulse {
            0%, 100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4);
            }
            50% {
                transform: scale(1.1);
                box-shadow: 0 0 20px 10px rgba(183, 110, 121, 0.3);
            }
        }

        /* Product Card */
        .product-card {
            position: fixed;
            right: -420px;
            top: 50%;
            transform: translateY(-50%);
            width: 380px;
            background: linear-gradient(135deg, rgba(26,26,26,0.98) 0%, rgba(10,10,10,0.98) 100%);
            border-left: 1px solid var(--sr-gold);
            padding: 2rem;
            z-index: 200;
            transition: right 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(20px);
        }

        .product-card.visible {
            right: 0;
        }

        .product-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 36px;
            height: 36px;
            border: 1px solid var(--sr-gold);
            background: transparent;
            color: var(--sr-gold);
            font-size: 1.2rem;
            cursor: pointer;
            border-radius: 50%;
            transition: all 0.3s ease;
        }

        .product-close:hover {
            border-color: var(--sr-rose-gold);
            color: #fff;
            background: var(--sr-rose-gold);
        }

        .product-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border: 1px solid var(--sr-gold);
            color: var(--sr-gold);
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        .product-image {
            width: 100%;
            height: 220px;
            background: linear-gradient(45deg, var(--sr-charcoal), var(--sr-black));
            border: 1px solid rgba(212, 175, 55, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            font-size: 4rem;
            overflow: hidden;
        }

        .product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .product-title {
            font-family: var(--font-display);
            font-size: 1.6rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #fff;
        }

        .product-price {
            font-size: 1.4rem;
            color: var(--sr-gold);
            margin-bottom: 1rem;
            font-weight: 500;
        }

        .product-description {
            font-size: 0.9rem;
            color: rgba(255,255,255,0.7);
            line-height: 1.7;
            margin-bottom: 1.5rem;
        }

        .product-actions {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .product-cta {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, var(--sr-gold), var(--sr-rose-gold));
            border: none;
            color: var(--sr-black);
            font-family: var(--font-body);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .product-cta:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(212, 175, 55, 0.4);
        }

        .product-cta.adding {
            background: var(--sr-charcoal);
            color: var(--sr-gold);
        }

        .product-cta.added {
            background: #2ecc71;
            color: #fff;
        }

        .product-link {
            width: 100%;
            padding: 0.8rem;
            background: transparent;
            border: 1px solid var(--sr-gold);
            color: var(--sr-gold);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            text-decoration: none;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
        }

        .product-link:hover {
            background: rgba(212, 175, 55, 0.1);
            color: #fff;
        }

        /* Navigation Controls */
        .nav-controls {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 1rem;
            z-index: 100;
        }

        .nav-btn {
            padding: 0.8rem 1.5rem;
            background: rgba(26, 26, 26, 0.9);
            border: 1px solid var(--sr-gold);
            color: var(--sr-gold);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .nav-btn:hover, .nav-btn.active {
            background: var(--sr-gold);
            color: var(--sr-black);
        }

        /* Brand Elements */
        .brand-watermark {
            position: fixed;
            top: 50%;
            left: 2rem;
            transform: translateY(-50%);
            writing-mode: vertical-rl;
            text-orientation: mixed;
            font-family: var(--font-display);
            font-size: 0.75rem;
            letter-spacing: 0.4em;
            color: var(--sr-gold);
            opacity: 0.4;
            z-index: 100;
        }

        .brand-logo {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            font-family: var(--font-display);
            font-size: 1rem;
            letter-spacing: 0.3em;
            color: var(--sr-rose-gold);
            opacity: 0.6;
            z-index: 100;
        }

        /* Cart Mini */
        .cart-mini {
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 150;
        }

        .cart-mini-btn {
            width: 50px;
            height: 50px;
            background: rgba(26, 26, 26, 0.9);
            border: 1px solid var(--sr-gold);
            border-radius: 50%;
            color: var(--sr-gold);
            font-size: 1.2rem;
            cursor: pointer;
            position: relative;
            transition: all 0.3s ease;
        }

        .cart-mini-btn:hover {
            background: var(--sr-gold);
            color: var(--sr-black);
        }

        .cart-count {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            background: var(--sr-rose-gold);
            border-radius: 50%;
            font-size: 0.7rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }

        /* Back Button */
        .back-btn {
            position: fixed;
            top: 2rem;
            left: 2rem;
            padding: 0.8rem 1.2rem;
            background: rgba(26, 26, 26, 0.9);
            border: 1px solid var(--sr-gold);
            color: var(--sr-gold);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            text-decoration: none;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .back-btn:hover {
            background: var(--sr-gold);
            color: var(--sr-black);
        }

        /* Toast Notifications */
        .toast {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(26, 26, 26, 0.95);
            border: 1px solid var(--sr-gold);
            padding: 1rem 2rem;
            border-radius: 4px;
            color: #fff;
            font-size: 0.9rem;
            z-index: 1000;
            opacity: 0;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .collection-name { font-size: 1.5rem; }
            .product-card { width: 100%; right: -100%; }
            .product-card.visible { right: 0; }
            .nav-controls { flex-wrap: wrap; justify-content: center; }
            .brand-watermark { display: none; }
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div id="loading-screen">
        <div class="loading-logo">SKYYROSE</div>
        <div class="loading-subtitle">Signature Collection</div>
        <div class="loading-progress">
            <div class="loading-bar" id="loading-bar"></div>
        </div>
    </div>

    <!-- 3D Canvas Container -->
    <div id="canvas-container"></div>

    <!-- Back Button -->
    <a href="<?php echo esc_url(home_url('/collections')); ?>" class="back-btn">
        <span>&larr;</span> Collections
    </a>

    <!-- Cart Mini -->
    <div class="cart-mini">
        <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="cart-mini-btn">
            🛒
            <span class="cart-count"><?php echo WC()->cart ? WC()->cart->get_cart_contents_count() : 0; ?></span>
        </a>
    </div>

    <!-- Collection Header -->
    <div class="collection-header">
        <h1 class="collection-name">Signature</h1>
        <p class="collection-tagline">Premium Foundation Essentials</p>
    </div>

    <!-- Product Hotspots (positioned by JS) -->
    <div id="hotspots-container"></div>

    <!-- Product Card -->
    <div class="product-card" id="product-card">
        <button class="product-close" onclick="closeProductCard()">&times;</button>
        <span class="product-badge" id="product-badge">Investment Piece</span>
        <div class="product-image" id="product-image">🧥</div>
        <h2 class="product-title" id="product-title">Foundation Blazer</h2>
        <p class="product-price" id="product-price">$395</p>
        <p class="product-description" id="product-description">
            Premium Italian wool blend blazer with gold-tone hardware and silk lining. The cornerstone of elevated style.
        </p>
        <div class="product-actions">
            <button class="product-cta" id="add-to-cart-btn" onclick="addToCartAjax()">Add to Cart</button>
            <a href="#" class="product-link" id="product-link">View Full Details</a>
        </div>
    </div>

    <!-- Navigation -->
    <div class="nav-controls">
        <button class="nav-btn active" data-view="runway">Runway View</button>
        <button class="nav-btn" data-view="backstage">Backstage</button>
        <button class="nav-btn" data-view="vip">VIP Lounge</button>
    </div>

    <!-- Brand Watermark -->
    <div class="brand-watermark">SIGNATURE COLLECTION</div>

    <!-- Brand Logo -->
    <div class="brand-logo">SKYYROSE</div>

    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script type="module">
        import * as THREE from 'three';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
        import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
        import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
        import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
        import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

        // ============================================
        // SKYYROSE SIGNATURE COLLECTION
        // Virtual Fashion Runway Experience
        // Rose Gold (#B76E79) + Gold (#D4AF37)
        // ============================================

        let scene, camera, renderer, controls, composer;
        let runway, mannequins = [], particles, spotlights = [];
        let clock = new THREE.Clock();
        let hotspots3D = [];
        let currentProductId = null;

        // Product Data from WordPress
        const products = <?php echo json_encode($products_for_js); ?>;

        // Camera Views
        const cameraViews = {
            runway: { position: new THREE.Vector3(0, 4, 12), target: new THREE.Vector3(0, 2, 0) },
            backstage: { position: new THREE.Vector3(-8, 3, 4), target: new THREE.Vector3(0, 2, 0) },
            vip: { position: new THREE.Vector3(8, 5, 8), target: new THREE.Vector3(0, 1, -2) }
        };

        // Initialize
        init();
        animate();

        function init() {
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a0a);
            scene.fog = new THREE.FogExp2(0x0a0a0a, 0.03);

            // Camera
            camera = new THREE.PerspectiveCamera(
                55,
                window.innerWidth / window.innerHeight,
                0.1,
                100
            );
            camera.position.copy(cameraViews.runway.position);

            // Renderer
            renderer = new THREE.WebGLRenderer({
                antialias: true,
                powerPreference: 'high-performance'
            });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.0;
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.copy(cameraViews.runway.target);
            controls.minDistance = 5;
            controls.maxDistance = 20;
            controls.maxPolarAngle = Math.PI / 1.8;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.15;

            // Lighting
            setupLighting();

            // Create Scene Elements
            createRunway();
            createAudience();
            createMannequins();
            createGoldenParticles();
            createHotspots();

            // Post-processing with Bloom
            setupPostProcessing();

            // Events
            window.addEventListener('resize', onWindowResize);
            setupNavigation();

            // Loading complete
            simulateLoading();
        }

        function setupLighting() {
            // Ambient - warm gold undertone
            const ambient = new THREE.AmbientLight(0x1a1510, 0.4);
            scene.add(ambient);

            // Main runway spotlight
            const mainSpot = new THREE.SpotLight(0xD4AF37, 3, 30, Math.PI / 6, 0.5);
            mainSpot.position.set(0, 15, 0);
            mainSpot.target.position.set(0, 0, 0);
            mainSpot.castShadow = true;
            mainSpot.shadow.mapSize.width = 2048;
            mainSpot.shadow.mapSize.height = 2048;
            scene.add(mainSpot);
            scene.add(mainSpot.target);
            spotlights.push(mainSpot);

            // Rose gold accent lights
            const roseGoldLight1 = new THREE.SpotLight(0xB76E79, 2, 25, Math.PI / 5, 0.6);
            roseGoldLight1.position.set(-8, 10, 5);
            roseGoldLight1.target.position.set(0, 0, 0);
            scene.add(roseGoldLight1);
            scene.add(roseGoldLight1.target);
            spotlights.push(roseGoldLight1);

            const roseGoldLight2 = new THREE.SpotLight(0xB76E79, 2, 25, Math.PI / 5, 0.6);
            roseGoldLight2.position.set(8, 10, 5);
            roseGoldLight2.target.position.set(0, 0, 0);
            scene.add(roseGoldLight2);
            scene.add(roseGoldLight2.target);
            spotlights.push(roseGoldLight2);

            // Gold rim lights
            const goldRim1 = new THREE.PointLight(0xD4AF37, 1.5, 20);
            goldRim1.position.set(-6, 3, -8);
            scene.add(goldRim1);

            const goldRim2 = new THREE.PointLight(0xD4AF37, 1.5, 20);
            goldRim2.position.set(6, 3, -8);
            scene.add(goldRim2);

            // Hemisphere for subtle fill
            const hemi = new THREE.HemisphereLight(0xD4AF37, 0x0a0a0a, 0.2);
            scene.add(hemi);
        }

        function createRunway() {
            // Main runway platform
            const runwayGeo = new THREE.BoxGeometry(6, 0.3, 25);
            const runwayMat = new THREE.MeshStandardMaterial({
                color: 0x1a1a1a,
                roughness: 0.2,
                metalness: 0.8
            });
            runway = new THREE.Mesh(runwayGeo, runwayMat);
            runway.position.set(0, 0.15, 0);
            runway.receiveShadow = true;
            scene.add(runway);

            // Gold edge strips
            const stripMat = new THREE.MeshStandardMaterial({
                color: 0xD4AF37,
                roughness: 0.3,
                metalness: 0.9,
                emissive: 0xD4AF37,
                emissiveIntensity: 0.3
            });

            const leftStrip = new THREE.Mesh(
                new THREE.BoxGeometry(0.1, 0.35, 25),
                stripMat
            );
            leftStrip.position.set(-3, 0.175, 0);
            scene.add(leftStrip);

            const rightStrip = new THREE.Mesh(
                new THREE.BoxGeometry(0.1, 0.35, 25),
                stripMat
            );
            rightStrip.position.set(3, 0.175, 0);
            scene.add(rightStrip);

            // Rose gold accent lines on runway
            const roseGoldMat = new THREE.MeshStandardMaterial({
                color: 0xB76E79,
                roughness: 0.3,
                metalness: 0.9,
                emissive: 0xB76E79,
                emissiveIntensity: 0.2
            });

            for (let i = -10; i <= 10; i += 2) {
                const line = new THREE.Mesh(
                    new THREE.BoxGeometry(5.8, 0.02, 0.05),
                    roseGoldMat
                );
                line.position.set(0, 0.31, i);
                scene.add(line);
            }

            // Backdrop
            const backdropGeo = new THREE.PlaneGeometry(20, 12);
            const backdropMat = new THREE.MeshStandardMaterial({
                color: 0x0a0a0a,
                roughness: 0.95
            });
            const backdrop = new THREE.Mesh(backdropGeo, backdropMat);
            backdrop.position.set(0, 6, -12);
            scene.add(backdrop);

            // SKYYROSE logo on backdrop (simplified)
            const logoGeo = new THREE.TorusGeometry(1.5, 0.08, 16, 100);
            const logoMat = new THREE.MeshStandardMaterial({
                color: 0xD4AF37,
                roughness: 0.2,
                metalness: 0.9,
                emissive: 0xD4AF37,
                emissiveIntensity: 0.5
            });
            const logo = new THREE.Mesh(logoGeo, logoMat);
            logo.position.set(0, 8, -11.5);
            scene.add(logo);
        }

        function createAudience() {
            // Simplified audience silhouettes
            const silhouetteMat = new THREE.MeshBasicMaterial({
                color: 0x0f0f0f,
                transparent: true,
                opacity: 0.8
            });

            for (let side = -1; side <= 1; side += 2) {
                for (let row = 0; row < 3; row++) {
                    for (let i = 0; i < 8; i++) {
                        const height = 1.2 + Math.random() * 0.4;
                        const silhouette = new THREE.Mesh(
                            new THREE.CapsuleGeometry(0.25, height, 4, 8),
                            silhouetteMat
                        );
                        silhouette.position.set(
                            side * (4 + row * 1.2),
                            height / 2 + 0.3,
                            -8 + i * 2.2 + Math.random() * 0.5
                        );
                        scene.add(silhouette);
                    }
                }
            }
        }

        function createMannequins() {
            // Simplified mannequin forms
            const mannequinMat = new THREE.MeshStandardMaterial({
                color: 0x2a2a2a,
                roughness: 0.6,
                metalness: 0.3
            });

            const positions = [
                { x: -2, z: -4 },
                { x: 2, z: -4 },
                { x: 0, z: -8 },
                { x: -1.5, z: 2 },
                { x: 1.5, z: 2 }
            ];

            positions.forEach((pos, i) => {
                const mannequin = new THREE.Group();

                // Body
                const body = new THREE.Mesh(
                    new THREE.CapsuleGeometry(0.35, 1.2, 8, 16),
                    mannequinMat
                );
                body.position.y = 1.2;
                mannequin.add(body);

                // Head
                const head = new THREE.Mesh(
                    new THREE.SphereGeometry(0.2, 16, 16),
                    mannequinMat
                );
                head.position.y = 2.1;
                mannequin.add(head);

                // Shoulders
                const shoulders = new THREE.Mesh(
                    new THREE.BoxGeometry(0.8, 0.15, 0.25),
                    mannequinMat
                );
                shoulders.position.y = 1.8;
                mannequin.add(shoulders);

                mannequin.position.set(pos.x, 0, pos.z);
                mannequin.castShadow = true;
                mannequins.push(mannequin);
                scene.add(mannequin);
            });
        }

        function createGoldenParticles() {
            const particleCount = 1500;
            const positions = new Float32Array(particleCount * 3);
            const colors = new Float32Array(particleCount * 3);

            const goldColor = new THREE.Color(0xD4AF37);
            const roseGoldColor = new THREE.Color(0xB76E79);
            const champagneColor = new THREE.Color(0xF7E7CE);

            for (let i = 0; i < particleCount; i++) {
                // Spread particles around the runway
                positions[i * 3] = (Math.random() - 0.5) * 20;
                positions[i * 3 + 1] = Math.random() * 12;
                positions[i * 3 + 2] = (Math.random() - 0.5) * 30;

                // Mix of gold, rose gold, and champagne colors
                const colorChoice = Math.random();
                let color;
                if (colorChoice < 0.5) {
                    color = goldColor;
                } else if (colorChoice < 0.8) {
                    color = roseGoldColor;
                } else {
                    color = champagneColor;
                }

                colors[i * 3] = color.r;
                colors[i * 3 + 1] = color.g;
                colors[i * 3 + 2] = color.b;
            }

            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const material = new THREE.PointsMaterial({
                size: 0.05,
                vertexColors: true,
                transparent: true,
                opacity: 0.8,
                blending: THREE.AdditiveBlending
            });

            particles = new THREE.Points(geometry, material);
            scene.add(particles);
        }

        function createHotspots() {
            products.forEach((product, index) => {
                const pos = product.position || { x: 0, y: 1.5, z: 0 };

                // 3D marker
                const markerGeo = new THREE.SphereGeometry(0.12, 16, 16);
                const markerMat = new THREE.MeshBasicMaterial({
                    color: 0xD4AF37,
                    transparent: true,
                    opacity: 0.9
                });
                const marker = new THREE.Mesh(markerGeo, markerMat);
                marker.position.set(pos.x, pos.y, pos.z);
                marker.userData.productIndex = index;
                scene.add(marker);
                hotspots3D.push(marker);

                // Pulsing ring
                const ringGeo = new THREE.RingGeometry(0.18, 0.25, 32);
                const ringMat = new THREE.MeshBasicMaterial({
                    color: 0xB76E79,
                    transparent: true,
                    opacity: 0.6,
                    side: THREE.DoubleSide
                });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.position.copy(marker.position);
                scene.add(ring);
            });
        }

        function setupPostProcessing() {
            composer = new EffectComposer(renderer);

            const renderPass = new RenderPass(scene, camera);
            composer.addPass(renderPass);

            const bloomPass = new UnrealBloomPass(
                new THREE.Vector2(window.innerWidth, window.innerHeight),
                0.8,   // strength
                0.4,   // radius
                0.85   // threshold
            );
            composer.addPass(bloomPass);

            const outputPass = new OutputPass();
            composer.addPass(outputPass);
        }

        function animate() {
            requestAnimationFrame(animate);

            const time = clock.getElapsedTime();

            // Update controls
            controls.update();

            // Animate particles - gentle float
            if (particles) {
                particles.rotation.y += 0.0002;
                const positions = particles.geometry.attributes.position.array;
                for (let i = 0; i < positions.length; i += 3) {
                    positions[i + 1] += Math.sin(time + i) * 0.001;
                    if (positions[i + 1] > 12) positions[i + 1] = 0;
                }
                particles.geometry.attributes.position.needsUpdate = true;
            }

            // Animate spotlights
            spotlights.forEach((light, i) => {
                if (i > 0) {
                    light.intensity = 1.5 + Math.sin(time * 2 + i) * 0.5;
                }
            });

            // Animate hotspots
            hotspots3D.forEach((marker, i) => {
                marker.scale.setScalar(1 + Math.sin(time * 2 + i) * 0.15);
            });

            // Render with post-processing
            composer.render();

            // Update 2D hotspot positions
            updateHotspotPositions();
        }

        function updateHotspotPositions() {
            const container = document.getElementById('hotspots-container');
            container.innerHTML = '';

            hotspots3D.forEach((marker, index) => {
                const screenPos = marker.position.clone().project(camera);

                if (screenPos.z < 1) {
                    const x = (screenPos.x * 0.5 + 0.5) * window.innerWidth;
                    const y = (-screenPos.y * 0.5 + 0.5) * window.innerHeight;

                    const hotspot = document.createElement('div');
                    hotspot.className = 'hotspot';
                    hotspot.style.left = `${x}px`;
                    hotspot.style.top = `${y}px`;
                    hotspot.innerHTML = '<div class="hotspot-inner"></div>';
                    hotspot.onclick = () => showProduct(index);
                    container.appendChild(hotspot);
                }
            });
        }

        function showProduct(index) {
            const product = products[index];
            if (!product) return;

            currentProductId = product.id;

            document.getElementById('product-badge').textContent = product.badge || 'Signature';

            const imageContainer = document.getElementById('product-image');
            if (product.image) {
                imageContainer.innerHTML = `<img src="${product.image}" alt="${product.title}">`;
            } else {
                imageContainer.textContent = product.emoji || '🧥';
            }

            document.getElementById('product-title').textContent = product.title;
            document.getElementById('product-price').innerHTML = product.price;
            document.getElementById('product-description').textContent = product.description;

            const linkEl = document.getElementById('product-link');
            if (product.permalink) {
                linkEl.href = product.permalink;
                linkEl.style.display = 'block';
            } else {
                linkEl.style.display = 'none';
            }

            document.getElementById('product-card').classList.add('visible');

            // Animate camera to product
            const pos = product.position || { x: 0, y: 1.5, z: 0 };
            animateCameraTo(
                new THREE.Vector3(pos.x + 3, pos.y + 1, pos.z + 3),
                new THREE.Vector3(pos.x, pos.y, pos.z)
            );
        }

        window.closeProductCard = function() {
            document.getElementById('product-card').classList.remove('visible');
            currentProductId = null;
        };

        window.addToCartAjax = function() {
            if (!currentProductId || typeof currentProductId !== 'number') {
                showToast('Demo mode - Add to cart');
                return;
            }

            const btn = document.getElementById('add-to-cart-btn');
            btn.classList.add('adding');
            btn.textContent = 'Adding...';

            // WooCommerce AJAX add to cart
            const formData = new FormData();
            formData.append('action', 'woocommerce_add_to_cart');
            formData.append('product_id', currentProductId);
            formData.append('quantity', 1);

            fetch('<?php echo admin_url('admin-ajax.php'); ?>', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                btn.classList.remove('adding');
                btn.classList.add('added');
                btn.textContent = 'Added!';

                // Update cart count
                const cartCount = document.querySelector('.cart-count');
                if (cartCount && data.cart_quantity) {
                    cartCount.textContent = data.cart_quantity;
                }

                showToast('Added to cart successfully!');

                setTimeout(() => {
                    btn.classList.remove('added');
                    btn.textContent = 'Add to Cart';
                }, 2000);
            })
            .catch(error => {
                btn.classList.remove('adding');
                btn.textContent = 'Add to Cart';
                showToast('Added to cart!');
            });
        };

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        function animateCameraTo(position, target) {
            const startPos = camera.position.clone();
            const startTarget = controls.target.clone();
            const duration = 1000;
            const startTime = Date.now();

            function updateCamera() {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);

                camera.position.lerpVectors(startPos, position, eased);
                controls.target.lerpVectors(startTarget, target, eased);

                if (progress < 1) {
                    requestAnimationFrame(updateCamera);
                }
            }

            controls.autoRotate = false;
            updateCamera();
        }

        function setupNavigation() {
            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const view = btn.dataset.view;
                    const viewData = cameraViews[view];
                    if (viewData) {
                        animateCameraTo(viewData.position, viewData.target);

                        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                    }
                });
            });
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            composer.setSize(window.innerWidth, window.innerHeight);
        }

        function simulateLoading() {
            const loadingBar = document.getElementById('loading-bar');
            let progress = 0;

            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                    setTimeout(() => {
                        document.getElementById('loading-screen').classList.add('hidden');
                    }, 500);
                }
                loadingBar.style.width = `${progress}%`;
            }, 100);
        }
    </script>
</body>
</html>

<?php get_footer(); ?>
