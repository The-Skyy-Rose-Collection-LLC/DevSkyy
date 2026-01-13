<?php
/**
 * Template Name: 3D Product Viewer
 * Description: Interactive 3D product viewer for SkyyRose collections
 */

get_header();
?>

<style>
    .viewer-page {
        min-height: 100vh;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
        padding: 20px;
        font-family: 'Segoe UI', sans-serif;
    }
    .viewer-header {
        text-align: center;
        padding: 40px 20px;
    }
    .viewer-header h1 {
        color: #B76E79;
        font-size: 2.5rem;
        margin-bottom: 10px;
    }
    .viewer-header p {
        color: #888;
        font-size: 1.1rem;
    }
    .viewer-container {
        max-width: 1400px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: 1fr 350px;
        gap: 30px;
    }
    @media (max-width: 900px) {
        .viewer-container {
            grid-template-columns: 1fr;
        }
    }
    #canvas-container {
        background: #0d0d1a;
        border-radius: 16px;
        overflow: hidden;
        aspect-ratio: 16/10;
        position: relative;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    #viewer-canvas {
        width: 100%;
        height: 100%;
        display: block;
    }
    .controls-hint {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.7);
        color: #fff;
        padding: 10px 20px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    .product-panel {
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 25px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .panel-title {
        color: #fff;
        font-size: 1.3rem;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .product-grid {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    .product-card {
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s;
        border: 2px solid transparent;
    }
    .product-card:hover {
        background: rgba(183,110,121,0.2);
        transform: translateX(5px);
    }
    .product-card.active {
        border-color: #B76E79;
        background: rgba(183,110,121,0.15);
    }
    .product-name {
        color: #fff;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .product-price {
        color: #B76E79;
        font-size: 1.1rem;
    }
    .product-desc {
        color: #888;
        font-size: 0.85rem;
        margin-top: 8px;
    }
    .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: #0d0d1a;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
    }
    .spinner {
        width: 50px;
        height: 50px;
        border: 3px solid rgba(183,110,121,0.3);
        border-top-color: #B76E79;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .hidden { display: none; }
</style>

<div class="viewer-page">
    <div class="viewer-header">
        <h1>SkyyRose 3D Collection</h1>
        <p>Explore our luxury pieces in stunning 3D - drag to rotate, scroll to zoom</p>
    </div>

    <div class="viewer-container">
        <div id="canvas-container">
            <canvas id="viewer-canvas"></canvas>
            <div id="loading-overlay" class="loading-overlay">
                <div class="spinner"></div>
            </div>
            <div class="controls-hint">Drag to rotate | Scroll to zoom</div>
        </div>

        <div class="product-panel">
            <h2 class="panel-title">Select Product</h2>
            <div id="product-grid" class="product-grid"></div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>

<script>
(function() {
    'use strict';

    // Product data
    const products = [
        { id: 'rose-tee', name: 'Rose Signature Tee', price: '$89', desc: 'Premium cotton with rose gold accents', color: 0xB76E79 },
        { id: 'noir-jacket', name: 'Noir Leather Jacket', price: '$450', desc: 'Italian leather, hand-stitched details', color: 0x1a1a1a },
        { id: 'skyy-hoodie', name: 'Skyy Luxury Hoodie', price: '$165', desc: 'French terry with metallic finish', color: 0x4a4a6a },
        { id: 'gold-beanie', name: 'Gold Thread Beanie', price: '$75', desc: 'Merino wool with gold embroidery', color: 0xd4af37 }
    ];

    let scene, camera, renderer, controls, currentModel;
    const canvas = document.getElementById('viewer-canvas');
    const container = document.getElementById('canvas-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const productGrid = document.getElementById('product-grid');

    function init() {
        // Scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0d0d1a);

        // Camera
        camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.5, 4);

        // Renderer
        renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;

        // Controls
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.minDistance = 2;
        controls.maxDistance = 8;
        controls.maxPolarAngle = Math.PI / 1.8;
        controls.target.set(0, 0.8, 0);

        // Lighting
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambient);

        const keyLight = new THREE.DirectionalLight(0xffffff, 1);
        keyLight.position.set(5, 8, 5);
        keyLight.castShadow = true;
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        scene.add(keyLight);

        const fillLight = new THREE.DirectionalLight(0xB76E79, 0.3);
        fillLight.position.set(-5, 3, -5);
        scene.add(fillLight);

        const rimLight = new THREE.PointLight(0xffffff, 0.5);
        rimLight.position.set(0, 5, -3);
        scene.add(rimLight);

        // Ground
        const groundGeo = new THREE.CircleGeometry(3, 64);
        const groundMat = new THREE.MeshStandardMaterial({
            color: 0x111122,
            roughness: 0.8,
            metalness: 0.2
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);

        // Build product cards
        buildProductCards();

        // Load first product
        loadProduct(products[0]);

        // Resize handler
        window.addEventListener('resize', onResize);

        // Animation loop
        animate();
    }

    function buildProductCards() {
        products.forEach(function(product, index) {
            var card = document.createElement('div');
            card.className = 'product-card' + (index === 0 ? ' active' : '');
            card.setAttribute('data-id', product.id);

            var nameDiv = document.createElement('div');
            nameDiv.className = 'product-name';
            nameDiv.textContent = product.name;

            var priceDiv = document.createElement('div');
            priceDiv.className = 'product-price';
            priceDiv.textContent = product.price;

            var descDiv = document.createElement('div');
            descDiv.className = 'product-desc';
            descDiv.textContent = product.desc;

            card.appendChild(nameDiv);
            card.appendChild(priceDiv);
            card.appendChild(descDiv);

            card.addEventListener('click', function() {
                document.querySelectorAll('.product-card').forEach(function(c) {
                    c.classList.remove('active');
                });
                card.classList.add('active');
                loadProduct(product);
            });

            productGrid.appendChild(card);
        });
    }

    function loadProduct(product) {
        loadingOverlay.classList.remove('hidden');

        // Remove old model
        if (currentModel) {
            scene.remove(currentModel);
            currentModel.traverse(function(child) {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(function(m) { m.dispose(); });
                    } else {
                        child.material.dispose();
                    }
                }
            });
        }

        // Create procedural model based on product type
        var group = new THREE.Group();
        var material = new THREE.MeshStandardMaterial({
            color: product.color,
            roughness: 0.4,
            metalness: 0.1
        });

        if (product.id === 'rose-tee') {
            // T-shirt shape
            var bodyGeo = new THREE.CylinderGeometry(0.4, 0.5, 0.8, 32);
            var body = new THREE.Mesh(bodyGeo, material);
            body.position.y = 0.8;
            body.castShadow = true;
            group.add(body);

            // Sleeves
            var sleeveGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.3, 16);
            var leftSleeve = new THREE.Mesh(sleeveGeo, material);
            leftSleeve.position.set(-0.5, 1.05, 0);
            leftSleeve.rotation.z = Math.PI / 3;
            leftSleeve.castShadow = true;
            group.add(leftSleeve);

            var rightSleeve = new THREE.Mesh(sleeveGeo, material);
            rightSleeve.position.set(0.5, 1.05, 0);
            rightSleeve.rotation.z = -Math.PI / 3;
            rightSleeve.castShadow = true;
            group.add(rightSleeve);

            // Collar
            var collarGeo = new THREE.TorusGeometry(0.15, 0.03, 8, 32);
            var collar = new THREE.Mesh(collarGeo, material);
            collar.position.y = 1.2;
            collar.rotation.x = Math.PI / 2;
            group.add(collar);

        } else if (product.id === 'noir-jacket') {
            // Jacket body
            var jacketMat = new THREE.MeshStandardMaterial({
                color: product.color,
                roughness: 0.3,
                metalness: 0.4
            });

            var bodyGeo = new THREE.BoxGeometry(0.9, 0.9, 0.4);
            var body = new THREE.Mesh(bodyGeo, jacketMat);
            body.position.y = 0.85;
            body.castShadow = true;
            group.add(body);

            // Sleeves
            var sleeveGeo = new THREE.CylinderGeometry(0.1, 0.12, 0.7, 16);
            var leftSleeve = new THREE.Mesh(sleeveGeo, jacketMat);
            leftSleeve.position.set(-0.55, 0.9, 0);
            leftSleeve.rotation.z = Math.PI / 6;
            leftSleeve.castShadow = true;
            group.add(leftSleeve);

            var rightSleeve = new THREE.Mesh(sleeveGeo, jacketMat);
            rightSleeve.position.set(0.55, 0.9, 0);
            rightSleeve.rotation.z = -Math.PI / 6;
            rightSleeve.castShadow = true;
            group.add(rightSleeve);

            // Collar
            var collarGeo = new THREE.BoxGeometry(0.4, 0.15, 0.15);
            var collar = new THREE.Mesh(collarGeo, jacketMat);
            collar.position.set(0, 1.35, 0.15);
            collar.rotation.x = -0.3;
            group.add(collar);

        } else if (product.id === 'skyy-hoodie') {
            // Hoodie body
            var bodyGeo = new THREE.CylinderGeometry(0.45, 0.55, 0.85, 32);
            var body = new THREE.Mesh(bodyGeo, material);
            body.position.y = 0.8;
            body.castShadow = true;
            group.add(body);

            // Hood
            var hoodGeo = new THREE.SphereGeometry(0.3, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
            var hood = new THREE.Mesh(hoodGeo, material);
            hood.position.set(0, 1.15, -0.1);
            hood.rotation.x = 0.3;
            hood.castShadow = true;
            group.add(hood);

            // Sleeves
            var sleeveGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.6, 16);
            var leftSleeve = new THREE.Mesh(sleeveGeo, material);
            leftSleeve.position.set(-0.55, 0.95, 0);
            leftSleeve.rotation.z = Math.PI / 4;
            leftSleeve.castShadow = true;
            group.add(leftSleeve);

            var rightSleeve = new THREE.Mesh(sleeveGeo, material);
            rightSleeve.position.set(0.55, 0.95, 0);
            rightSleeve.rotation.z = -Math.PI / 4;
            rightSleeve.castShadow = true;
            group.add(rightSleeve);

        } else if (product.id === 'gold-beanie') {
            // Beanie
            var beanieMat = new THREE.MeshStandardMaterial({
                color: product.color,
                roughness: 0.6,
                metalness: 0.3
            });

            var beanieGeo = new THREE.SphereGeometry(0.35, 32, 24, 0, Math.PI * 2, 0, Math.PI / 1.5);
            var beanie = new THREE.Mesh(beanieGeo, beanieMat);
            beanie.position.y = 1.1;
            beanie.castShadow = true;
            group.add(beanie);

            // Fold
            var foldGeo = new THREE.TorusGeometry(0.33, 0.06, 8, 32);
            var fold = new THREE.Mesh(foldGeo, beanieMat);
            fold.position.y = 0.85;
            fold.rotation.x = Math.PI / 2;
            group.add(fold);

            // Pom-pom
            var pomGeo = new THREE.SphereGeometry(0.1, 16, 16);
            var pom = new THREE.Mesh(pomGeo, beanieMat);
            pom.position.y = 1.4;
            pom.castShadow = true;
            group.add(pom);
        }

        currentModel = group;
        scene.add(currentModel);

        // Hide loading after brief delay
        setTimeout(function() {
            loadingOverlay.classList.add('hidden');
        }, 300);
    }

    function onResize() {
        var width = container.clientWidth;
        var height = container.clientHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }

    function animate() {
        requestAnimationFrame(animate);

        // Slow rotation
        if (currentModel) {
            currentModel.rotation.y += 0.003;
        }

        controls.update();
        renderer.render(scene, camera);
    }

    // Start
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>

<?php get_footer(); ?>
