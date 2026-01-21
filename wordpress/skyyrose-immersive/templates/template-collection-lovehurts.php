<?php
/**
 * Template Name: Love Hurts Collection (Immersive)
 * Template Post Type: page
 *
 * Immersive 3D throne room experience for the Love Hurts Collection.
 * Features floating hearts, gothic architecture, and emotional expression pieces.
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

// Get WooCommerce products for Love Hurts collection
$lovehurts_products = array();
if (function_exists('wc_get_products')) {
    $lovehurts_products = wc_get_products(array(
        'limit' => 12,
        'status' => 'publish',
        'category' => array('love-hurts', 'love-hurts-collection'),
        'orderby' => 'menu_order',
        'order' => 'ASC',
    ));
}

// Fallback demo products if no WooCommerce products
if (empty($lovehurts_products)) {
    $lovehurts_products = array(
        (object) array(
            'get_id' => function() { return 'demo-1'; },
            'get_name' => function() { return 'Heartbreak Hoodie'; },
            'get_price' => function() { return '165'; },
            'get_short_description' => function() { return 'A tribute piece featuring hand-stitched broken heart motif. Premium French terry with vintage wash.'; },
            'get_permalink' => function() { return '#'; },
            'get_image_id' => function() { return 0; },
        ),
        (object) array(
            'get_id' => function() { return 'demo-2'; },
            'get_name' => function() { return 'Love Letter Jacket'; },
            'get_price' => function() { return '245'; },
            'get_short_description' => function() { return 'Satin bomber with embroidered love letters from the Hurt family archives. Each piece tells a story.'; },
            'get_permalink' => function() { return '#'; },
            'get_image_id' => function() { return 0; },
        ),
        (object) array(
            'get_id' => function() { return 'demo-3'; },
            'get_name' => function() { return 'Bleeding Heart Tee'; },
            'get_price' => function() { return '85'; },
            'get_short_description' => function() { return 'Oversized cotton tee with anatomical heart graphic. Water-based inks for a soft, worn feel.'; },
            'get_permalink' => function() { return '#'; },
            'get_image_id' => function() { return 0; },
        ),
        (object) array(
            'get_id' => function() { return 'demo-4'; },
            'get_name' => function() { return 'Thorns of Love Pants'; },
            'get_price' => function() { return '145'; },
            'get_short_description' => function() { return 'Cargo pants with thorn embroidery down the seams. Heavy cotton twill with adjustable cuffs.'; },
            'get_permalink' => function() { return '#'; },
            'get_image_id' => function() { return 0; },
        ),
    );
}

// Build products data for JavaScript
$products_js_data = array();
$positions = array(
    array(-3, 1.5, 1),
    array(3, 2, 0),
    array(0, 1.5, 3),
    array(-2, 1, -2),
    array(2, 1, -2),
    array(-4, 2, 1),
);

foreach ($lovehurts_products as $index => $product) {
    $pos = $positions[$index % count($positions)];
    $is_demo = is_array($product) || (is_object($product) && isset($product->get_id) && is_callable($product->get_id));

    if ($is_demo) {
        $id = call_user_func($product->get_id);
        $name = call_user_func($product->get_name);
        $price = call_user_func($product->get_price);
        $desc = call_user_func($product->get_short_description);
        $link = call_user_func($product->get_permalink);
        $image = '';
    } else {
        $id = $product->get_id();
        $name = $product->get_name();
        $price = $product->get_price();
        $desc = $product->get_short_description();
        $link = $product->get_permalink();
        $image_id = $product->get_image_id();
        $image = $image_id ? wp_get_attachment_image_url($image_id, 'medium') : '';
    }

    $products_js_data[] = array(
        'id' => $id,
        'name' => $name,
        'price' => $price,
        'description' => $desc,
        'link' => $link,
        'image' => $image,
        'position' => $pos,
    );
}
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOVE HURTS Collection | <?php bloginfo('name'); ?></title>
    <meta name="description" content="Enter the LOVE HURTS virtual castle - an immersive 3D throne room experience featuring SkyyRose's emotional expression collection">
    <?php wp_head(); ?>

    <!-- Import Maps for Three.js ES Modules -->
    <script type="importmap">
    {
        "imports": {
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }
    }
    </script>

    <style>
        /* SkyyRose LOVE HURTS Collection Theme */
        :root {
            --sr-deep-rose: #C41E3A;
            --sr-burgundy: #722F37;
            --sr-blush: #DE5D83;
            --sr-wine: #4A0E1E;
            --sr-gold: #D4AF37;
            --sr-cream: #FFFDD0;
            --sr-charcoal: #1A1A1A;
            --font-display: 'Playfair Display', Georgia, serif;
            --font-body: 'Inter', -apple-system, sans-serif;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

        body {
            font-family: var(--font-body);
            background: var(--sr-wine);
            color: #fff;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }

        /* Loading Screen */
        #loading-screen {
            position: fixed;
            inset: 0;
            background: linear-gradient(135deg, var(--sr-wine) 0%, #2a0a12 100%);
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
            background: linear-gradient(135deg, var(--sr-deep-rose), var(--sr-blush));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: heartbeat 1.5s ease-in-out infinite;
        }

        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            14% { transform: scale(1.05); }
            28% { transform: scale(1); }
            42% { transform: scale(1.05); }
            70% { transform: scale(1); }
        }

        .loading-subtitle {
            font-size: 0.9rem;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: var(--sr-blush);
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
            background: linear-gradient(90deg, var(--sr-burgundy), var(--sr-deep-rose), var(--sr-blush));
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
            background: linear-gradient(180deg, #fff 0%, var(--sr-blush) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(196, 30, 58, 0.6);
        }

        .collection-tagline {
            font-size: 0.85rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: var(--sr-blush);
            margin-top: 0.5rem;
        }

        /* Heart-shaped Hotspots */
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
            background: radial-gradient(circle, var(--sr-deep-rose) 0%, transparent 70%);
            border: 2px solid var(--sr-blush);
            animation: heart-pulse 1.5s ease-in-out infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
            border-radius: 50%;
        }

        .hotspot-inner::before {
            content: '\2661';
            font-size: 1rem;
            color: #fff;
        }

        @keyframes heart-pulse {
            0%, 100% {
                transform: scale(1);
                filter: drop-shadow(0 0 5px rgba(196, 30, 58, 0.5));
            }
            50% {
                transform: scale(1.15);
                filter: drop-shadow(0 0 15px rgba(196, 30, 58, 0.8));
            }
        }

        /* Product Card */
        .product-card {
            position: fixed;
            right: -420px;
            top: 50%;
            transform: translateY(-50%);
            width: 380px;
            max-height: 90vh;
            overflow-y: auto;
            background: linear-gradient(135deg, rgba(74,14,30,0.97) 0%, rgba(42,10,18,0.97) 100%);
            border-left: 1px solid var(--sr-deep-rose);
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
            border: 1px solid var(--sr-blush);
            background: transparent;
            color: var(--sr-blush);
            font-size: 1.4rem;
            cursor: pointer;
            border-radius: 50%;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .product-close:hover {
            border-color: var(--sr-deep-rose);
            color: #fff;
            background: var(--sr-deep-rose);
        }

        .product-badge {
            display: inline-block;
            padding: 0.4rem 1rem;
            background: linear-gradient(135deg, var(--sr-deep-rose), var(--sr-burgundy));
            color: #fff;
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        .product-image {
            width: 100%;
            height: 220px;
            background: linear-gradient(45deg, var(--sr-wine), #2a0a12);
            border: 1px solid rgba(196, 30, 58, 0.3);
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
            font-size: 1.5rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .product-price {
            font-size: 1.25rem;
            color: var(--sr-blush);
            margin-bottom: 1rem;
        }

        .product-description {
            font-size: 0.9rem;
            color: rgba(255,255,255,0.8);
            line-height: 1.6;
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
            background: linear-gradient(135deg, var(--sr-deep-rose), var(--sr-burgundy));
            border: none;
            color: #fff;
            font-family: var(--font-body);
            font-size: 0.85rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .product-cta:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(196, 30, 58, 0.5);
        }

        .product-cta:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .product-link {
            display: block;
            width: 100%;
            padding: 0.75rem;
            background: transparent;
            border: 1px solid var(--sr-blush);
            color: var(--sr-blush);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            text-decoration: none;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .product-link:hover {
            background: var(--sr-blush);
            color: var(--sr-wine);
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
            background: rgba(74, 14, 30, 0.8);
            border: 1px solid var(--sr-blush);
            color: var(--sr-blush);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .nav-btn:hover, .nav-btn.active {
            background: var(--sr-deep-rose);
            border-color: var(--sr-deep-rose);
            color: #fff;
        }

        /* Back Button */
        .back-btn {
            position: fixed;
            top: 2rem;
            left: 2rem;
            padding: 0.8rem 1.2rem;
            background: rgba(74, 14, 30, 0.9);
            border: 1px solid var(--sr-blush);
            color: var(--sr-blush);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 100;
            text-decoration: none;
        }

        .back-btn:hover {
            background: var(--sr-blush);
            color: var(--sr-wine);
        }

        /* Cart Mini Button */
        .cart-mini {
            position: fixed;
            top: 2rem;
            right: 2rem;
            padding: 0.8rem 1.2rem;
            background: rgba(74, 14, 30, 0.9);
            border: 1px solid var(--sr-gold);
            color: var(--sr-gold);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 100;
            text-decoration: none;
        }

        .cart-mini:hover {
            background: var(--sr-gold);
            color: var(--sr-wine);
        }

        .cart-count {
            background: var(--sr-deep-rose);
            color: #fff;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
        }

        /* Family Tribute */
        .family-tribute {
            position: fixed;
            top: 50%;
            left: 2rem;
            transform: translateY(-50%) rotate(-90deg);
            transform-origin: left center;
            font-family: var(--font-display);
            font-size: 0.75rem;
            letter-spacing: 0.3em;
            color: var(--sr-blush);
            opacity: 0.6;
            z-index: 100;
            white-space: nowrap;
        }

        /* Brand Logo */
        .brand-logo {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            font-family: var(--font-display);
            font-size: 1rem;
            letter-spacing: 0.3em;
            color: var(--sr-blush);
            opacity: 0.6;
            z-index: 100;
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 6rem;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: linear-gradient(135deg, var(--sr-deep-rose), var(--sr-burgundy));
            color: #fff;
            padding: 1rem 2rem;
            border-radius: 4px;
            font-size: 0.9rem;
            letter-spacing: 0.1em;
            z-index: 1000;
            opacity: 0;
            transition: all 0.4s ease;
            box-shadow: 0 10px 40px rgba(196, 30, 58, 0.5);
        }

        .toast.visible {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .collection-name { font-size: 1.5rem; }
            .product-card { width: 100%; right: -100%; }
            .product-card.visible { right: 0; }
            .nav-controls { flex-wrap: wrap; justify-content: center; }
            .family-tribute { display: none; }
            .back-btn { top: auto; bottom: 6rem; left: 1rem; }
            .cart-mini { top: 1rem; right: 1rem; }
        }
    </style>
</head>
<body <?php body_class('skyyrose-collection-lovehurts'); ?>>
    <!-- Loading Screen -->
    <div id="loading-screen">
        <div class="loading-logo">SKYYROSE</div>
        <div class="loading-subtitle">Love Hurts Collection</div>
        <div class="loading-progress">
            <div class="loading-bar" id="loading-bar"></div>
        </div>
    </div>

    <!-- 3D Canvas Container -->
    <div id="canvas-container"></div>

    <!-- Back Button -->
    <a href="<?php echo esc_url(home_url('/collections')); ?>" class="back-btn">
        <span>&larr;</span> Back
    </a>

    <!-- Cart Mini Button -->
    <a href="<?php echo esc_url(wc_get_cart_url()); ?>" class="cart-mini">
        <span>&#9825;</span> Cart
        <span class="cart-count" id="cart-count"><?php echo WC()->cart ? WC()->cart->get_cart_contents_count() : 0; ?></span>
    </a>

    <!-- Collection Header -->
    <div class="collection-header">
        <h1 class="collection-name">Love Hurts</h1>
        <p class="collection-tagline">Honoring the Hurt Family Legacy</p>
    </div>

    <!-- Product Hotspots (positioned by JS) -->
    <div id="hotspots-container"></div>

    <!-- Product Card -->
    <div class="product-card" id="product-card">
        <button class="product-close" onclick="closeProductCard()">&times;</button>
        <span class="product-badge" id="product-badge">Love Hurts Collection</span>
        <div class="product-image" id="product-image"></div>
        <h2 class="product-title" id="product-title">Product Name</h2>
        <p class="product-price" id="product-price">$0</p>
        <p class="product-description" id="product-description">Product description.</p>
        <div class="product-actions">
            <button class="product-cta" id="add-to-cart-btn" onclick="addToCartAjax()">Add to Cart</button>
            <a href="#" class="product-link" id="product-link">View Full Details</a>
        </div>
    </div>

    <!-- Navigation -->
    <div class="nav-controls">
        <button class="nav-btn active" data-view="throne">Throne View</button>
        <button class="nav-btn" data-view="altar">Heart Altar</button>
        <button class="nav-btn" data-view="gallery">Gallery</button>
    </div>

    <!-- Family Tribute -->
    <div class="family-tribute">THE HURT FAMILY LEGACY</div>

    <!-- Brand Logo -->
    <div class="brand-logo">SKYYROSE</div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">Added to cart!</div>

    <script type="module">
        import * as THREE from 'three';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
        import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
        import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
        import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
        import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

        // ============================================
        // SKYYROSE LOVE HURTS COLLECTION
        // Virtual Castle Throne Room Experience
        // ============================================

        let scene, camera, renderer, controls, composer;
        let hearts = [], candles = [], throne;
        let clock = new THREE.Clock();
        let hotspots3D = [];
        let currentProductId = null;

        // Product Data from WordPress/WooCommerce
        const products = <?php echo json_encode($products_js_data); ?>;

        // Camera Views
        const cameraViews = {
            throne: { position: new THREE.Vector3(0, 3, 8), target: new THREE.Vector3(0, 2, 0) },
            altar: { position: new THREE.Vector3(5, 2, 0), target: new THREE.Vector3(0, 2, 0) },
            gallery: { position: new THREE.Vector3(-5, 4, 5), target: new THREE.Vector3(0, 1, 0) }
        };

        // Initialize
        init();
        animate();

        function init() {
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a0a10);
            scene.fog = new THREE.FogExp2(0x1a0a10, 0.04);

            // Camera
            camera = new THREE.PerspectiveCamera(
                55,
                window.innerWidth / window.innerHeight,
                0.1,
                100
            );
            camera.position.copy(cameraViews.throne.position);

            // Renderer
            renderer = new THREE.WebGLRenderer({
                antialias: true,
                powerPreference: 'high-performance'
            });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 0.9;
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.copy(cameraViews.throne.target);
            controls.minDistance = 3;
            controls.maxDistance = 15;
            controls.maxPolarAngle = Math.PI / 1.8;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.2;

            // Lighting
            setupLighting();

            // Create Scene Elements
            createFloor();
            createWalls();
            createThrone();
            createHeartAltar();
            createFloatingHearts();
            createCandles();
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
            // Ambient - warm undertone
            const ambient = new THREE.AmbientLight(0x2a1015, 0.4);
            scene.add(ambient);

            // Main spotlight on throne
            const throneLight = new THREE.SpotLight(0xC41E3A, 3, 20, Math.PI / 6, 0.5);
            throneLight.position.set(0, 10, 5);
            throneLight.target.position.set(0, 2, -2);
            throneLight.castShadow = true;
            throneLight.shadow.mapSize.width = 1024;
            throneLight.shadow.mapSize.height = 1024;
            scene.add(throneLight);
            scene.add(throneLight.target);

            // Rose-colored accent lights
            const accent1 = new THREE.PointLight(0xDE5D83, 1.5, 12);
            accent1.position.set(-6, 4, -4);
            scene.add(accent1);

            const accent2 = new THREE.PointLight(0xDE5D83, 1.5, 12);
            accent2.position.set(6, 4, -4);
            scene.add(accent2);

            // Gold rim light
            const rimLight = new THREE.PointLight(0xD4AF37, 1, 15);
            rimLight.position.set(0, 6, -8);
            scene.add(rimLight);

            // Hemisphere for subtle fill
            const hemi = new THREE.HemisphereLight(0x2a1520, 0x0a0508, 0.3);
            scene.add(hemi);
        }

        function createFloor() {
            // Castle stone floor
            const floorGeo = new THREE.PlaneGeometry(30, 30, 20, 20);
            const floorMat = new THREE.MeshStandardMaterial({
                color: 0x2a1a1a,
                roughness: 0.9,
                metalness: 0.1
            });
            const floor = new THREE.Mesh(floorGeo, floorMat);
            floor.rotation.x = -Math.PI / 2;
            floor.receiveShadow = true;
            scene.add(floor);

            // Carpet runner
            const carpetGeo = new THREE.PlaneGeometry(3, 12);
            const carpetMat = new THREE.MeshStandardMaterial({
                color: 0x722F37,
                roughness: 0.8
            });
            const carpet = new THREE.Mesh(carpetGeo, carpetMat);
            carpet.rotation.x = -Math.PI / 2;
            carpet.position.set(0, 0.01, 2);
            scene.add(carpet);
        }

        function createWalls() {
            const wallMat = new THREE.MeshStandardMaterial({
                color: 0x1a0a10,
                roughness: 0.95,
                metalness: 0.05
            });

            // Back wall
            const backWall = new THREE.Mesh(
                new THREE.PlaneGeometry(30, 15),
                wallMat
            );
            backWall.position.set(0, 7.5, -10);
            scene.add(backWall);

            // Side walls
            const leftWall = new THREE.Mesh(
                new THREE.PlaneGeometry(20, 15),
                wallMat
            );
            leftWall.position.set(-10, 7.5, 0);
            leftWall.rotation.y = Math.PI / 2;
            scene.add(leftWall);

            const rightWall = new THREE.Mesh(
                new THREE.PlaneGeometry(20, 15),
                wallMat
            );
            rightWall.position.set(10, 7.5, 0);
            rightWall.rotation.y = -Math.PI / 2;
            scene.add(rightWall);

            // Gothic arches
            createGothicArches();
        }

        function createGothicArches() {
            const archPositions = [-6, -3, 3, 6];

            archPositions.forEach(x => {
                // Arch columns
                const columnGeo = new THREE.CylinderGeometry(0.3, 0.35, 8, 16);
                const columnMat = new THREE.MeshStandardMaterial({
                    color: 0x2a1a1a,
                    roughness: 0.7,
                    metalness: 0.2
                });

                const leftCol = new THREE.Mesh(columnGeo, columnMat);
                leftCol.position.set(x - 1, 4, -9);
                scene.add(leftCol);

                const rightCol = new THREE.Mesh(columnGeo, columnMat);
                rightCol.position.set(x + 1, 4, -9);
                scene.add(rightCol);

                // Arch top
                const archGeo = new THREE.TorusGeometry(1, 0.15, 8, 16, Math.PI);
                const arch = new THREE.Mesh(archGeo, columnMat);
                arch.position.set(x, 8, -9);
                arch.rotation.x = Math.PI / 2;
                scene.add(arch);
            });
        }

        function createThrone() {
            throne = new THREE.Group();

            // Throne seat
            const seatGeo = new THREE.BoxGeometry(2, 0.3, 2);
            const throneMat = new THREE.MeshStandardMaterial({
                color: 0x722F37,
                roughness: 0.4,
                metalness: 0.3
            });
            const seat = new THREE.Mesh(seatGeo, throneMat);
            seat.position.y = 1;
            throne.add(seat);

            // Throne back
            const backGeo = new THREE.BoxGeometry(2.2, 4, 0.3);
            const back = new THREE.Mesh(backGeo, throneMat);
            back.position.set(0, 3, -0.85);
            throne.add(back);

            // Throne top ornament (heart shape made from spheres)
            const heartTop = createHeartShape(0.5, 0xD4AF37);
            heartTop.position.set(0, 5.2, -0.85);
            throne.add(heartTop);

            // Armrests
            const armGeo = new THREE.BoxGeometry(0.3, 0.8, 1.8);
            const leftArm = new THREE.Mesh(armGeo, throneMat);
            leftArm.position.set(-1.1, 1.5, 0);
            throne.add(leftArm);

            const rightArm = new THREE.Mesh(armGeo, throneMat);
            rightArm.position.set(1.1, 1.5, 0);
            throne.add(rightArm);

            // Gold trim
            const trimMat = new THREE.MeshStandardMaterial({
                color: 0xD4AF37,
                roughness: 0.2,
                metalness: 0.8
            });

            const trimGeo = new THREE.TorusGeometry(0.08, 0.02, 8, 32);
            for (let i = 0; i < 6; i++) {
                const trim = new THREE.Mesh(trimGeo, trimMat);
                trim.position.set(0, 1.5 + i * 0.6, -0.7);
                trim.rotation.y = Math.PI / 2;
                throne.add(trim);
            }

            throne.position.set(0, 0, -4);
            throne.castShadow = true;
            scene.add(throne);
        }

        function createHeartShape(size, color) {
            const heartGroup = new THREE.Group();
            const mat = new THREE.MeshStandardMaterial({
                color: color,
                roughness: 0.3,
                metalness: 0.6
            });

            // Heart made from spheres and cone
            const leftLobe = new THREE.Mesh(
                new THREE.SphereGeometry(size * 0.6, 16, 16),
                mat
            );
            leftLobe.position.set(-size * 0.35, size * 0.3, 0);
            heartGroup.add(leftLobe);

            const rightLobe = new THREE.Mesh(
                new THREE.SphereGeometry(size * 0.6, 16, 16),
                mat
            );
            rightLobe.position.set(size * 0.35, size * 0.3, 0);
            heartGroup.add(rightLobe);

            const bottom = new THREE.Mesh(
                new THREE.ConeGeometry(size * 0.7, size, 16),
                mat
            );
            bottom.position.set(0, -size * 0.3, 0);
            bottom.rotation.z = Math.PI;
            heartGroup.add(bottom);

            return heartGroup;
        }

        function createHeartAltar() {
            // Central altar with glowing heart
            const altarBase = new THREE.Mesh(
                new THREE.CylinderGeometry(1, 1.2, 0.5, 32),
                new THREE.MeshStandardMaterial({
                    color: 0x2a1a1a,
                    roughness: 0.6,
                    metalness: 0.3
                })
            );
            altarBase.position.set(0, 0.25, 0);
            scene.add(altarBase);

            // Glowing heart on altar
            const glowingHeart = createHeartShape(0.8, 0xC41E3A);
            glowingHeart.position.set(0, 1.5, 0);
            scene.add(glowingHeart);

            // Heart glow
            const glowGeo = new THREE.SphereGeometry(1.2, 32, 32);
            const glowMat = new THREE.MeshBasicMaterial({
                color: 0xC41E3A,
                transparent: true,
                opacity: 0.15
            });
            const glow = new THREE.Mesh(glowGeo, glowMat);
            glow.position.set(0, 1.5, 0);
            scene.add(glow);

            // Point light from heart
            const heartLight = new THREE.PointLight(0xC41E3A, 2, 8);
            heartLight.position.set(0, 1.5, 0);
            scene.add(heartLight);
        }

        function createFloatingHearts() {
            const heartCount = 50;

            for (let i = 0; i < heartCount; i++) {
                const size = Math.random() * 0.2 + 0.1;
                const colors = [0xC41E3A, 0xDE5D83, 0x722F37, 0xD4AF37];
                const color = colors[Math.floor(Math.random() * colors.length)];

                const heart = createHeartShape(size, color);

                // Random position in room
                heart.position.set(
                    (Math.random() - 0.5) * 16,
                    Math.random() * 8 + 2,
                    (Math.random() - 0.5) * 16
                );

                heart.userData.baseY = heart.position.y;
                heart.userData.phase = Math.random() * Math.PI * 2;
                heart.userData.speed = Math.random() * 0.5 + 0.5;
                heart.userData.rotSpeed = (Math.random() - 0.5) * 0.02;

                hearts.push(heart);
                scene.add(heart);
            }
        }

        function createCandles() {
            const candlePositions = [
                { x: -4, z: -3 },
                { x: 4, z: -3 },
                { x: -2, z: 2 },
                { x: 2, z: 2 },
                { x: -6, z: 0 },
                { x: 6, z: 0 }
            ];

            candlePositions.forEach((pos, i) => {
                const candleGroup = new THREE.Group();

                // Candle stick
                const stickGeo = new THREE.CylinderGeometry(0.15, 0.2, 1.5, 16);
                const stickMat = new THREE.MeshStandardMaterial({
                    color: 0xD4AF37,
                    roughness: 0.3,
                    metalness: 0.7
                });
                const stick = new THREE.Mesh(stickGeo, stickMat);
                stick.position.y = 0.75;
                candleGroup.add(stick);

                // Candle
                const candleGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.8, 16);
                const candleMat = new THREE.MeshStandardMaterial({
                    color: 0xFFF8DC,
                    roughness: 0.9
                });
                const candle = new THREE.Mesh(candleGeo, candleMat);
                candle.position.y = 1.9;
                candleGroup.add(candle);

                // Flame (emissive sphere)
                const flameGeo = new THREE.SphereGeometry(0.06, 16, 16);
                const flameMat = new THREE.MeshBasicMaterial({
                    color: 0xFFAA00
                });
                const flame = new THREE.Mesh(flameGeo, flameMat);
                flame.position.y = 2.4;
                flame.userData.baseY = 2.4;
                flame.userData.phase = i * 0.5;
                candleGroup.add(flame);

                // Candle light
                const candleLight = new THREE.PointLight(0xFFAA00, 0.5, 4);
                candleLight.position.y = 2.4;
                candleGroup.add(candleLight);

                candleGroup.position.set(pos.x, 0, pos.z);
                candles.push({ group: candleGroup, flame, light: candleLight });
                scene.add(candleGroup);
            });
        }

        function createHotspots() {
            products.forEach((product, index) => {
                const pos = new THREE.Vector3(
                    product.position[0],
                    product.position[1],
                    product.position[2]
                );

                // 3D marker (heart-shaped glow)
                const markerGeo = new THREE.SphereGeometry(0.15, 16, 16);
                const markerMat = new THREE.MeshBasicMaterial({
                    color: 0xDE5D83,
                    transparent: true,
                    opacity: 0.9
                });
                const marker = new THREE.Mesh(markerGeo, markerMat);
                marker.position.copy(pos);
                marker.userData.productIndex = index;
                scene.add(marker);
                hotspots3D.push(marker);

                // Pulsing ring
                const ringGeo = new THREE.RingGeometry(0.2, 0.28, 32);
                const ringMat = new THREE.MeshBasicMaterial({
                    color: 0xD4AF37,
                    transparent: true,
                    opacity: 0.5,
                    side: THREE.DoubleSide
                });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.position.copy(pos);
                ring.lookAt(camera.position);
                scene.add(ring);
            });
        }

        function setupPostProcessing() {
            composer = new EffectComposer(renderer);

            const renderPass = new RenderPass(scene, camera);
            composer.addPass(renderPass);

            const bloomPass = new UnrealBloomPass(
                new THREE.Vector2(window.innerWidth, window.innerHeight),
                1.0,   // strength - higher for romantic glow
                0.5,   // radius
                0.3    // threshold
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

            // Animate floating hearts
            hearts.forEach(heart => {
                heart.position.y = heart.userData.baseY +
                    Math.sin(time * heart.userData.speed + heart.userData.phase) * 0.3;
                heart.rotation.y += heart.userData.rotSpeed;
                heart.rotation.z = Math.sin(time + heart.userData.phase) * 0.1;
            });

            // Animate candle flames
            candles.forEach((candle, i) => {
                const flicker = Math.sin(time * 10 + candle.flame.userData.phase) * 0.02;
                candle.flame.position.y = candle.flame.userData.baseY + flicker;
                candle.flame.scale.setScalar(1 + Math.sin(time * 15 + i) * 0.1);
                candle.light.intensity = 0.4 + Math.sin(time * 8 + i) * 0.15;
            });

            // Animate hotspots
            hotspots3D.forEach((marker, i) => {
                marker.scale.setScalar(1 + Math.sin(time * 2 + i) * 0.15);
            });

            // Gentle throne sway
            if (throne) {
                throne.rotation.y = Math.sin(time * 0.5) * 0.02;
            }

            // Render with post-processing
            composer.render();

            // Update 2D hotspot positions
            updateHotspotPositions();
        }

        function updateHotspotPositions() {
            const container = document.getElementById('hotspots-container');
            container.innerHTML = '';

            hotspots3D.forEach(marker => {
                const screenPos = marker.position.clone().project(camera);

                if (screenPos.z < 1) {
                    const x = (screenPos.x * 0.5 + 0.5) * window.innerWidth;
                    const y = (-screenPos.y * 0.5 + 0.5) * window.innerHeight;

                    const hotspot = document.createElement('div');
                    hotspot.className = 'hotspot';
                    hotspot.style.left = `${x}px`;
                    hotspot.style.top = `${y}px`;
                    hotspot.innerHTML = '<div class="hotspot-inner"></div>';
                    hotspot.onclick = () => showProduct(marker.userData.productIndex);
                    container.appendChild(hotspot);
                }
            });
        }

        function showProduct(index) {
            const product = products[index];
            if (!product) return;

            currentProductId = product.id;

            document.getElementById('product-badge').textContent = 'Love Hurts Collection';

            const imageContainer = document.getElementById('product-image');
            if (product.image) {
                imageContainer.innerHTML = `<img src="${product.image}" alt="${product.name}">`;
            } else {
                imageContainer.innerHTML = '&#128148;'; // Broken heart emoji
            }

            document.getElementById('product-title').textContent = product.name;
            document.getElementById('product-price').textContent = '$' + parseFloat(product.price).toFixed(2);
            document.getElementById('product-description').textContent = product.description || 'A stunning piece from the Love Hurts collection.';
            document.getElementById('product-link').href = product.link || '#';

            document.getElementById('product-card').classList.add('visible');

            // Animate camera to product
            const productPos = new THREE.Vector3(
                product.position[0],
                product.position[1],
                product.position[2]
            );
            animateCameraTo(
                productPos.clone().add(new THREE.Vector3(2, 1, 2)),
                productPos
            );
        }

        window.closeProductCard = function() {
            document.getElementById('product-card').classList.remove('visible');
            currentProductId = null;
        };

        // AJAX Add to Cart - WooCommerce Integration
        window.addToCartAjax = function() {
            if (!currentProductId || String(currentProductId).startsWith('demo')) {
                showToast('Demo mode - add real products in WooCommerce');
                return;
            }

            const btn = document.getElementById('add-to-cart-btn');
            btn.disabled = true;
            btn.textContent = 'Adding...';

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
                btn.disabled = false;
                btn.textContent = 'Add to Cart';

                if (data.error) {
                    showToast('Error: ' + (data.error || 'Could not add to cart'));
                } else {
                    showToast('Added to cart!');
                    // Update cart count
                    const countEl = document.getElementById('cart-count');
                    if (countEl && data.cart_hash) {
                        countEl.textContent = parseInt(countEl.textContent) + 1;
                    }
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.textContent = 'Add to Cart';
                showToast('Error adding to cart');
                console.error(err);
            });
        };

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('visible');
            setTimeout(() => {
                toast.classList.remove('visible');
            }, 3000);
        }

        function animateCameraTo(position, target) {
            const startPos = camera.position.clone();
            const startTarget = controls.target.clone();
            const duration = 1200;
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
                progress += Math.random() * 12;
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

    <?php wp_footer(); ?>
</body>
</html>
