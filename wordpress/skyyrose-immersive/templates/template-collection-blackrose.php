<?php
/**
 * Template Name: Black Rose Collection (Immersive 3D)
 * Template Post Type: page
 *
 * Immersive 3D rose garden experience for the BLACK ROSE Collection
 * Crimson (#DC143C) + Dark Red (#8B0000) + Silver (#C0C0C0) theme
 *
 * @package SkyyRose_Immersive
 * @since 1.0.0
 */

defined('ABSPATH') || exit;

// Get collection products from WooCommerce
$blackrose_products = wc_get_products(array(
    'limit' => 12,
    'status' => 'publish',
    'category' => array('black-rose', 'black-rose-collection'),
    'orderby' => 'menu_order',
    'order' => 'ASC',
));

// Fallback demo products if no WooCommerce products
$demo_products = array(
    array(
        'id' => 'thorn-hoodie',
        'title' => 'Thorn Hoodie',
        'price' => '$185',
        'description' => 'Premium heavyweight cotton hoodie with embroidered thorn details. Part of our limited BLACK ROSE collection.',
        'badge' => 'Limited Edition',
        'emoji' => '🥀',
        'position' => array('x' => -3, 'y' => 1.5, 'z' => 2)
    ),
    array(
        'id' => 'midnight-jacket',
        'title' => 'Midnight Leather Jacket',
        'price' => '$295',
        'description' => 'Full-grain leather jacket with crimson satin lining. Hand-finished brass hardware.',
        'badge' => 'Exclusive',
        'emoji' => '🌹',
        'position' => array('x' => 3, 'y' => 2, 'z' => -2)
    ),
    array(
        'id' => 'gothic-tee',
        'title' => 'Gothic Rose Tee',
        'price' => '$75',
        'description' => 'Oversized cotton tee with front and back rose graphic. Enzyme-washed for vintage feel.',
        'badge' => 'New Arrival',
        'emoji' => '🖤',
        'position' => array('x' => 0, 'y' => 1, 'z' => 4)
    ),
    array(
        'id' => 'chain-cargo',
        'title' => 'Chain Cargo Pants',
        'price' => '$165',
        'description' => 'Heavy canvas cargo with detachable silver chain details. Multiple utility pockets.',
        'badge' => 'Limited',
        'emoji' => '⛓️',
        'position' => array('x' => -2, 'y' => 1.5, 'z' => -3)
    ),
);

// Build products array for JS
$products_for_js = array();
if (!empty($blackrose_products)) {
    foreach ($blackrose_products as $index => $product) {
        $positions = array(
            array('x' => -3, 'y' => 1.5, 'z' => 2),
            array('x' => 3, 'y' => 2, 'z' => -2),
            array('x' => 0, 'y' => 1, 'z' => 4),
            array('x' => -2, 'y' => 1.5, 'z' => -3),
        );
        $products_for_js[] = array(
            'id' => $product->get_id(),
            'title' => $product->get_name(),
            'price' => wc_price($product->get_price()),
            'price_raw' => $product->get_price(),
            'description' => wp_trim_words($product->get_short_description(), 20),
            'image' => wp_get_attachment_url($product->get_image_id()),
            'badge' => 'Black Rose',
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
    <title>BLACK ROSE Collection | SkyyRose Virtual Garden</title>
    <meta name="description" content="Enter the BLACK ROSE virtual garden - an immersive 3D experience featuring SkyyRose's dark elegance collection">

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
        /* SkyyRose BLACK ROSE Collection Theme */
        :root {
            --sr-black: #0A0505;
            --sr-crimson: #DC143C;
            --sr-dark-red: #8B0000;
            --sr-silver: #C0C0C0;
            --sr-burgundy: #722F37;
            --sr-rose-gold: #B76E79;
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
            background: linear-gradient(135deg, var(--sr-black) 0%, #1a0a0a 100%);
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
            background: linear-gradient(135deg, var(--sr-crimson), var(--sr-rose-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.8; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.02); }
        }

        .loading-subtitle {
            font-size: 0.9rem;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: var(--sr-silver);
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
            background: linear-gradient(90deg, var(--sr-dark-red), var(--sr-crimson));
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
            letter-spacing: 0.2em;
            text-transform: uppercase;
            background: linear-gradient(180deg, #fff 0%, var(--sr-silver) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(220, 20, 60, 0.5);
        }

        .collection-tagline {
            font-size: 0.85rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: var(--sr-crimson);
            margin-top: 0.5rem;
        }

        /* Product Hotspots */
        .hotspot {
            position: absolute;
            width: 40px;
            height: 40px;
            cursor: pointer;
            pointer-events: auto;
            transform: translate(-50%, -50%);
            z-index: 50;
        }

        .hotspot-inner {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: radial-gradient(circle, var(--sr-crimson) 0%, transparent 70%);
            border: 2px solid var(--sr-crimson);
            animation: hotspot-pulse 2s ease-in-out infinite;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }

        .hotspot-inner::before {
            content: '+';
            font-size: 1.5rem;
            color: #fff;
            font-weight: 300;
        }

        @keyframes hotspot-pulse {
            0%, 100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(220, 20, 60, 0.4);
            }
            50% {
                transform: scale(1.1);
                box-shadow: 0 0 20px 10px rgba(220, 20, 60, 0.2);
            }
        }

        /* Product Card */
        .product-card {
            position: fixed;
            right: -420px;
            top: 50%;
            transform: translateY(-50%);
            width: 380px;
            background: linear-gradient(135deg, rgba(10,5,5,0.98) 0%, rgba(26,10,10,0.98) 100%);
            border-left: 1px solid var(--sr-crimson);
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
            border: 1px solid var(--sr-silver);
            background: transparent;
            color: var(--sr-silver);
            font-size: 1.2rem;
            cursor: pointer;
            border-radius: 50%;
            transition: all 0.3s ease;
        }

        .product-close:hover {
            border-color: var(--sr-crimson);
            color: var(--sr-crimson);
        }

        .product-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            background: var(--sr-dark-red);
            color: #fff;
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        .product-image {
            width: 100%;
            height: 220px;
            background: linear-gradient(45deg, var(--sr-black), #1a0a0a);
            border: 1px solid rgba(220, 20, 60, 0.3);
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
        }

        .product-price {
            font-size: 1.4rem;
            color: var(--sr-crimson);
            margin-bottom: 1rem;
        }

        .product-description {
            font-size: 0.9rem;
            color: var(--sr-silver);
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
            background: linear-gradient(135deg, var(--sr-crimson), var(--sr-dark-red));
            border: none;
            color: #fff;
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
            box-shadow: 0 10px 30px rgba(220, 20, 60, 0.4);
        }

        .product-cta.adding {
            background: var(--sr-black);
            border: 1px solid var(--sr-crimson);
        }

        .product-cta.added {
            background: #2ecc71;
        }

        .product-link {
            width: 100%;
            padding: 0.8rem;
            background: transparent;
            border: 1px solid var(--sr-silver);
            color: var(--sr-silver);
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
            background: rgba(192, 192, 192, 0.1);
            color: #fff;
            border-color: #fff;
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
            background: rgba(10, 5, 5, 0.9);
            border: 1px solid var(--sr-silver);
            color: var(--sr-silver);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .nav-btn:hover, .nav-btn.active {
            background: var(--sr-crimson);
            border-color: var(--sr-crimson);
            color: #fff;
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
            background: rgba(10, 5, 5, 0.9);
            border: 1px solid var(--sr-crimson);
            border-radius: 50%;
            color: var(--sr-crimson);
            font-size: 1.2rem;
            cursor: pointer;
            position: relative;
            transition: all 0.3s ease;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cart-mini-btn:hover {
            background: var(--sr-crimson);
            color: #fff;
        }

        .cart-count {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            background: var(--sr-silver);
            border-radius: 50%;
            font-size: 0.7rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--sr-black);
        }

        /* Back Button */
        .back-btn {
            position: fixed;
            top: 2rem;
            left: 2rem;
            padding: 0.8rem 1.2rem;
            background: rgba(10, 5, 5, 0.9);
            border: 1px solid var(--sr-silver);
            color: var(--sr-silver);
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
            background: var(--sr-crimson);
            border-color: var(--sr-crimson);
            color: #fff;
        }

        /* Brand Logo */
        .brand-logo {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            font-family: var(--font-display);
            font-size: 1rem;
            letter-spacing: 0.3em;
            color: var(--sr-silver);
            opacity: 0.6;
            z-index: 100;
        }

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
            color: var(--sr-crimson);
            opacity: 0.4;
            z-index: 100;
        }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(10, 5, 5, 0.95);
            border: 1px solid var(--sr-crimson);
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
        <div class="loading-subtitle">Black Rose Collection</div>
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
        <h1 class="collection-name">Black Rose</h1>
        <p class="collection-tagline">Dark Elegance • Limited Edition</p>
    </div>

    <!-- Product Hotspots (positioned by JS) -->
    <div id="hotspots-container"></div>

    <!-- Product Card -->
    <div class="product-card" id="product-card">
        <button class="product-close" onclick="closeProductCard()">&times;</button>
        <span class="product-badge" id="product-badge">Limited Edition</span>
        <div class="product-image" id="product-image">🥀</div>
        <h2 class="product-title" id="product-title">Thorn Hoodie</h2>
        <p class="product-price" id="product-price">$185</p>
        <p class="product-description" id="product-description">
            Premium heavyweight cotton hoodie with embroidered thorn details.
            Part of our limited BLACK ROSE collection.
        </p>
        <div class="product-actions">
            <button class="product-cta" id="add-to-cart-btn" onclick="addToCartAjax()">Add to Cart</button>
            <a href="#" class="product-link" id="product-link">View Full Details</a>
        </div>
    </div>

    <!-- Navigation -->
    <div class="nav-controls">
        <button class="nav-btn active" data-view="garden">Garden View</button>
        <button class="nav-btn" data-view="throne">Throne View</button>
        <button class="nav-btn" data-view="altar">Altar View</button>
    </div>

    <!-- Brand Watermark -->
    <div class="brand-watermark">BLACK ROSE COLLECTION</div>

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
        // SKYYROSE BLACK ROSE COLLECTION
        // Virtual Garden 3D Experience
        // Crimson (#DC143C) + Dark Red (#8B0000) + Silver (#C0C0C0)
        // ============================================

        let scene, camera, renderer, controls, composer;
        let particles, pillars = [], orbs = [];
        let clock = new THREE.Clock();
        let hotspots3D = [];
        let currentProductId = null;

        // Product Data from WordPress
        const products = <?php echo json_encode($products_for_js); ?>;

        // Camera Views
        const cameraViews = {
            garden: { position: new THREE.Vector3(0, 3, 8), target: new THREE.Vector3(0, 1, 0) },
            throne: { position: new THREE.Vector3(-6, 4, 0), target: new THREE.Vector3(0, 1, 0) },
            altar: { position: new THREE.Vector3(0, 2, -6), target: new THREE.Vector3(0, 1, 2) }
        };

        // Initialize
        init();
        animate();

        function init() {
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0505);
            scene.fog = new THREE.FogExp2(0x0a0505, 0.06);

            // Camera
            camera = new THREE.PerspectiveCamera(
                60,
                window.innerWidth / window.innerHeight,
                0.1,
                100
            );
            camera.position.copy(cameraViews.garden.position);

            // Renderer
            renderer = new THREE.WebGLRenderer({
                antialias: true,
                powerPreference: 'high-performance'
            });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 0.8;
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.copy(cameraViews.garden.target);
            controls.minDistance = 3;
            controls.maxDistance = 15;
            controls.maxPolarAngle = Math.PI / 2;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.3;

            // Lighting
            setupLighting();

            // Create Scene Elements
            createGround();
            createPillars();
            createCentralRose();
            createParticles();
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
            // Ambient light - very subtle
            const ambient = new THREE.AmbientLight(0x1a0a0a, 0.5);
            scene.add(ambient);

            // Main crimson point light
            const mainLight = new THREE.PointLight(0xDC143C, 2, 20);
            mainLight.position.set(0, 5, 0);
            mainLight.castShadow = true;
            scene.add(mainLight);

            // Dark red accent lights
            const accent1 = new THREE.PointLight(0x8B0000, 1.5, 15);
            accent1.position.set(-5, 3, -5);
            scene.add(accent1);

            const accent2 = new THREE.PointLight(0x8B0000, 1.5, 15);
            accent2.position.set(5, 3, 5);
            scene.add(accent2);

            // Silver rim light
            const rimLight = new THREE.PointLight(0xC0C0C0, 1, 12);
            rimLight.position.set(0, 8, -8);
            scene.add(rimLight);

            // Hemisphere light for ground bounce
            const hemi = new THREE.HemisphereLight(0x1a0505, 0x050202, 0.3);
            scene.add(hemi);
        }

        function createGround() {
            // Reflective dark ground
            const groundGeo = new THREE.PlaneGeometry(50, 50);
            const groundMat = new THREE.MeshStandardMaterial({
                color: 0x0a0505,
                roughness: 0.2,
                metalness: 0.8
            });
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.5;
            ground.receiveShadow = true;
            scene.add(ground);
        }

        function createPillars() {
            const pillarPositions = [
                { x: -4, z: -4 },
                { x: 4, z: -4 },
                { x: -4, z: 4 },
                { x: 4, z: 4 },
                { x: -6, z: 0 },
                { x: 6, z: 0 },
                { x: 0, z: -6 },
                { x: 0, z: 6 }
            ];

            pillarPositions.forEach((pos, i) => {
                // Pillar
                const pillarGeo = new THREE.CylinderGeometry(0.3, 0.4, 6, 16);
                const pillarMat = new THREE.MeshStandardMaterial({
                    color: 0x1a1a1a,
                    roughness: 0.4,
                    metalness: 0.6
                });
                const pillar = new THREE.Mesh(pillarGeo, pillarMat);
                pillar.position.set(pos.x, 2.5, pos.z);
                pillar.castShadow = true;
                scene.add(pillar);
                pillars.push(pillar);

                // Glowing orb on top
                const orbGeo = new THREE.SphereGeometry(0.2, 32, 32);
                const orbMat = new THREE.MeshBasicMaterial({
                    color: 0xDC143C,
                    transparent: true,
                    opacity: 0.8
                });
                const orb = new THREE.Mesh(orbGeo, orbMat);
                orb.position.set(pos.x, 5.8, pos.z);
                orb.userData.baseY = 5.8;
                orb.userData.phase = i * 0.5;
                scene.add(orb);
                orbs.push(orb);

                // Point light for each orb
                const orbLight = new THREE.PointLight(0xDC143C, 0.5, 4);
                orbLight.position.copy(orb.position);
                scene.add(orbLight);
            });
        }

        function createCentralRose() {
            // Abstract rose sculpture using layered tori
            const roseGroup = new THREE.Group();

            const petalColors = [0xDC143C, 0x8B0000, 0x722F37, 0xB76E79];

            for (let layer = 0; layer < 5; layer++) {
                const numPetals = 5 + layer;
                const radius = 0.3 + layer * 0.15;
                const height = 0.5 + layer * 0.3;

                for (let p = 0; p < numPetals; p++) {
                    const angle = (p / numPetals) * Math.PI * 2;
                    const petalGeo = new THREE.TorusGeometry(radius, 0.08, 8, 16, Math.PI);
                    const petalMat = new THREE.MeshStandardMaterial({
                        color: petalColors[layer % petalColors.length],
                        roughness: 0.4,
                        metalness: 0.3,
                        side: THREE.DoubleSide
                    });
                    const petal = new THREE.Mesh(petalGeo, petalMat);
                    petal.position.set(
                        Math.cos(angle) * radius * 0.3,
                        height,
                        Math.sin(angle) * radius * 0.3
                    );
                    petal.rotation.x = Math.PI / 2 - layer * 0.2;
                    petal.rotation.y = angle;
                    petal.rotation.z = Math.random() * 0.3;
                    roseGroup.add(petal);
                }
            }

            // Stem
            const stemGeo = new THREE.CylinderGeometry(0.05, 0.08, 2, 8);
            const stemMat = new THREE.MeshStandardMaterial({
                color: 0x1a3a1a,
                roughness: 0.8
            });
            const stem = new THREE.Mesh(stemGeo, stemMat);
            stem.position.y = -0.5;
            roseGroup.add(stem);

            roseGroup.position.set(0, 1.5, 0);
            scene.add(roseGroup);

            // Glow sphere around rose
            const glowGeo = new THREE.SphereGeometry(1.5, 32, 32);
            const glowMat = new THREE.MeshBasicMaterial({
                color: 0xDC143C,
                transparent: true,
                opacity: 0.1
            });
            const glow = new THREE.Mesh(glowGeo, glowMat);
            glow.position.copy(roseGroup.position);
            scene.add(glow);
        }

        function createParticles() {
            // Floating rose petals / particles
            const particleCount = 3000;
            const positions = new Float32Array(particleCount * 3);
            const colors = new Float32Array(particleCount * 3);
            const velocities = [];

            const colorPalette = [
                new THREE.Color(0xDC143C), // Crimson
                new THREE.Color(0x8B0000), // Dark red
                new THREE.Color(0xC0C0C0), // Silver
                new THREE.Color(0xB76E79), // Rose gold
                new THREE.Color(0x722F37)  // Burgundy
            ];

            for (let i = 0; i < particleCount; i++) {
                // Position in cylindrical distribution
                const radius = Math.random() * 15 + 2;
                const angle = Math.random() * Math.PI * 2;
                const height = Math.random() * 10;

                positions[i * 3] = Math.cos(angle) * radius;
                positions[i * 3 + 1] = height;
                positions[i * 3 + 2] = Math.sin(angle) * radius;

                // Random color from palette
                const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
                colors[i * 3] = color.r;
                colors[i * 3 + 1] = color.g;
                colors[i * 3 + 2] = color.b;

                // Velocity for animation
                velocities.push({
                    x: (Math.random() - 0.5) * 0.01,
                    y: -Math.random() * 0.02 - 0.005,
                    z: (Math.random() - 0.5) * 0.01
                });
            }

            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const material = new THREE.PointsMaterial({
                size: 0.1,
                vertexColors: true,
                transparent: true,
                opacity: 0.8,
                blending: THREE.AdditiveBlending,
                sizeAttenuation: true
            });

            particles = new THREE.Points(geometry, material);
            particles.userData.velocities = velocities;
            scene.add(particles);
        }

        function createHotspots() {
            products.forEach((product, index) => {
                const pos = product.position || { x: 0, y: 1.5, z: 0 };

                // 3D marker
                const markerGeo = new THREE.SphereGeometry(0.15, 16, 16);
                const markerMat = new THREE.MeshBasicMaterial({
                    color: 0xDC143C,
                    transparent: true,
                    opacity: 0.8
                });
                const marker = new THREE.Mesh(markerGeo, markerMat);
                marker.position.set(pos.x, pos.y, pos.z);
                marker.userData.productIndex = index;
                scene.add(marker);
                hotspots3D.push(marker);

                // Ring around marker
                const ringGeo = new THREE.RingGeometry(0.2, 0.25, 32);
                const ringMat = new THREE.MeshBasicMaterial({
                    color: 0xC0C0C0,
                    transparent: true,
                    opacity: 0.5,
                    side: THREE.DoubleSide
                });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.position.copy(marker.position);
                ring.rotation.x = -Math.PI / 2;
                scene.add(ring);
            });
        }

        function setupPostProcessing() {
            composer = new EffectComposer(renderer);

            const renderPass = new RenderPass(scene, camera);
            composer.addPass(renderPass);

            const bloomPass = new UnrealBloomPass(
                new THREE.Vector2(window.innerWidth, window.innerHeight),
                0.8,  // strength
                0.4,  // radius
                0.2   // threshold
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

            // Animate orbs
            orbs.forEach((orb, i) => {
                orb.position.y = orb.userData.baseY + Math.sin(time * 2 + orb.userData.phase) * 0.1;
                orb.material.opacity = 0.6 + Math.sin(time * 3 + orb.userData.phase) * 0.2;
            });

            // Animate particles - falling petals
            if (particles) {
                const positions = particles.geometry.attributes.position.array;
                const velocities = particles.userData.velocities;

                for (let i = 0; i < velocities.length; i++) {
                    positions[i * 3] += velocities[i].x;
                    positions[i * 3 + 1] += velocities[i].y;
                    positions[i * 3 + 2] += velocities[i].z;

                    // Reset particles that fall below ground
                    if (positions[i * 3 + 1] < -0.5) {
                        const radius = Math.random() * 15 + 2;
                        const angle = Math.random() * Math.PI * 2;
                        positions[i * 3] = Math.cos(angle) * radius;
                        positions[i * 3 + 1] = 10;
                        positions[i * 3 + 2] = Math.sin(angle) * radius;
                    }
                }

                particles.geometry.attributes.position.needsUpdate = true;
                particles.rotation.y += 0.0002;
            }

            // Animate hotspots
            hotspots3D.forEach((marker, i) => {
                marker.scale.setScalar(1 + Math.sin(time * 3 + i) * 0.1);
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

            document.getElementById('product-badge').textContent = product.badge || 'Black Rose';

            const imageContainer = document.getElementById('product-image');
            if (product.image) {
                imageContainer.innerHTML = `<img src="${product.image}" alt="${product.title}">`;
            } else {
                imageContainer.textContent = product.emoji || '🥀';
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
                new THREE.Vector3(pos.x + 2, pos.y + 1, pos.z + 2),
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
