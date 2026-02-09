<?php
/**
 * Template Name: Black Rose Collection - Gothic Cathedral
 *
 * Immersive 3D experience for Black Rose Collection.
 * Gothic cathedral ruins with volumetric fog, firefly particles, and god rays.
 *
 * Features:
 * - Volumetric fog using TSL (Three.js Shading Language)
 * - 50,000 GPU-accelerated firefly particles
 * - God rays with volumetric light scattering
 * - Normal-mapped stone textures
 * - Spatial audio system
 * - WooCommerce product integration
 *
 * Performance: Optimized with LOD, 60fps target
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

// Security: Generate nonce for AJAX
$rest_nonce = wp_create_nonce( 'wp_rest' );
?>

<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta name="description" content="<?php echo esc_attr( get_the_excerpt() ); ?>">

	<!-- Preload critical assets -->
	<link rel="preload" href="<?php echo esc_url( get_template_directory_uri() . '/assets/js/three/scenes/BlackRoseScene.js' ); ?>" as="script">

	<!-- Schema.org -->
	<script type="application/ld+json">
	{
		"@context": "https://schema.org",
		"@type": "WebPage",
		"name": "Black Rose Collection - Gothic Cathedral",
		"description": "Immersive 3D Gothic cathedral experience with volumetric fog and firefly particles",
		"url": "<?php echo esc_url( get_permalink() ); ?>",
		"isPartOf": {
			"@type": "WebSite",
			"name": "<?php bloginfo( 'name' ); ?>",
			"url": "<?php echo esc_url( home_url() ); ?>"
		}
	}
	</script>

	<?php wp_head(); ?>

	<style>
		/* Black Rose Collection Styles */
		:root {
			--cathedral-dark: #0a0a1a;
			--cathedral-purple: #4b0082;
			--cathedral-stone: #2a2a2a;
			--cathedral-glow: #8b008b;
		}

		body {
			margin: 0;
			overflow: hidden;
			font-family: 'Cinzel', serif;
			background: var(--cathedral-dark);
		}

		/* Loading Screen */
		#loading-screen {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2a 100%);
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
			z-index: 10000;
			transition: opacity 1s ease;
		}

		#loading-screen.fade-out {
			opacity: 0;
			pointer-events: none;
		}

		.loading-content {
			text-align: center;
			color: #e0e0e0;
		}

		.loading-icon {
			font-size: 4rem;
			margin-bottom: 30px;
			animation: pulse 2s ease-in-out infinite;
		}

		@keyframes pulse {
			0%, 100% { opacity: 0.6; transform: scale(1); }
			50% { opacity: 1; transform: scale(1.1); }
		}

		.loading-title {
			font-size: 2.5rem;
			margin: 0 0 10px 0;
			color: #9370db;
			text-shadow: 0 0 20px rgba(147, 112, 219, 0.5);
		}

		.loading-subtitle {
			font-size: 1.2rem;
			margin: 0 0 30px 0;
			color: #b19cd9;
			font-style: italic;
		}

		.progress-bar {
			width: 300px;
			height: 4px;
			background: rgba(255, 255, 255, 0.1);
			border-radius: 2px;
			overflow: hidden;
			margin-bottom: 10px;
		}

		.progress-fill {
			height: 100%;
			background: linear-gradient(90deg, #4b0082, #8b008b);
			width: 0%;
			transition: width 0.3s ease;
			box-shadow: 0 0 10px rgba(139, 0, 139, 0.8);
		}

		.progress-text {
			font-size: 0.9rem;
			color: #b19cd9;
		}

		/* 3D Canvas */
		#three-canvas {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
		}

		/* Navigation UI */
		.scene-nav {
			position: fixed;
			top: 20px;
			left: 20px;
			z-index: 100;
			display: flex;
			flex-direction: column;
			gap: 10px;
		}

		.nav-button {
			background: rgba(20, 10, 30, 0.9);
			backdrop-filter: blur(10px);
			color: #9370db;
			border: 2px solid rgba(147, 112, 219, 0.3);
			padding: 12px 20px;
			border-radius: 8px;
			font-family: 'Cinzel', serif;
			font-size: 0.9rem;
			cursor: pointer;
			transition: all 0.3s ease;
			display: flex;
			align-items: center;
			gap: 10px;
		}

		.nav-button:hover {
			background: rgba(75, 0, 130, 0.9);
			border-color: #9370db;
			transform: translateX(5px);
			box-shadow: 0 5px 15px rgba(147, 112, 219, 0.3);
		}

		.nav-icon {
			font-size: 1.2rem;
		}

		/* Controls Panel */
		.controls-panel {
			position: fixed;
			bottom: 20px;
			left: 50%;
			transform: translateX(-50%);
			z-index: 100;
			display: flex;
			gap: 15px;
			background: rgba(20, 10, 30, 0.9);
			backdrop-filter: blur(10px);
			padding: 15px 30px;
			border-radius: 50px;
			border: 2px solid rgba(147, 112, 219, 0.3);
		}

		.control-button {
			background: transparent;
			border: none;
			color: #9370db;
			font-size: 1.8rem;
			cursor: pointer;
			transition: all 0.3s ease;
			padding: 10px;
			border-radius: 50%;
		}

		.control-button:hover {
			background: rgba(147, 112, 219, 0.2);
			transform: scale(1.1);
		}

		.control-button:active {
			transform: scale(0.95);
		}

		/* Info Panel */
		.info-panel {
			position: fixed;
			top: 20px;
			right: 20px;
			z-index: 100;
			background: rgba(20, 10, 30, 0.9);
			backdrop-filter: blur(10px);
			padding: 20px;
			border-radius: 12px;
			border: 2px solid rgba(147, 112, 219, 0.3);
			max-width: 300px;
		}

		.info-title {
			font-size: 1.5rem;
			color: #9370db;
			margin: 0 0 10px 0;
		}

		.info-description {
			font-size: 0.9rem;
			color: #b19cd9;
			line-height: 1.6;
			margin: 0;
		}

		.info-close {
			position: absolute;
			top: 10px;
			right: 10px;
			background: transparent;
			border: none;
			color: #9370db;
			font-size: 1.5rem;
			cursor: pointer;
			transition: color 0.3s ease;
		}

		.info-close:hover {
			color: #b19cd9;
		}

		/* Product Modal */
		.product-modal {
			display: none;
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: rgba(0, 0, 0, 0.8);
			z-index: 1000;
			align-items: center;
			justify-content: center;
		}

		.product-modal.active {
			display: flex;
		}

		.modal-content {
			background: linear-gradient(135deg, #1a0a2a 0%, #2a1a3a 100%);
			padding: 40px;
			border-radius: 20px;
			max-width: 500px;
			width: 90%;
			border: 3px solid rgba(147, 112, 219, 0.5);
			box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
		}

		.modal-close {
			float: right;
			font-size: 2rem;
			color: #9370db;
			cursor: pointer;
			line-height: 1;
			transition: color 0.3s ease;
		}

		.modal-close:hover {
			color: #b19cd9;
		}

		.modal-image {
			width: 100%;
			height: 300px;
			object-fit: cover;
			border-radius: 12px;
			margin-bottom: 20px;
		}

		.modal-title {
			font-size: 1.8rem;
			color: #9370db;
			margin: 0 0 10px 0;
		}

		.modal-price {
			font-size: 1.5rem;
			color: #b19cd9;
			margin: 0 0 20px 0;
			font-weight: 700;
		}

		.modal-description {
			font-size: 1rem;
			color: #d0c0e0;
			line-height: 1.8;
			margin-bottom: 30px;
		}

		.modal-actions {
			display: flex;
			gap: 15px;
		}

		.btn-add-cart,
		.btn-view-product {
			flex: 1;
			padding: 15px;
			border-radius: 10px;
			font-family: 'Cinzel', serif;
			font-size: 1rem;
			font-weight: 600;
			cursor: pointer;
			transition: all 0.3s ease;
			border: none;
			text-decoration: none;
			text-align: center;
			display: block;
		}

		.btn-add-cart {
			background: linear-gradient(135deg, #4b0082, #8b008b);
			color: #fff;
		}

		.btn-add-cart:hover {
			transform: translateY(-2px);
			box-shadow: 0 10px 30px rgba(139, 0, 139, 0.5);
		}

		.btn-view-product {
			background: rgba(147, 112, 219, 0.2);
			color: #9370db;
			border: 2px solid rgba(147, 112, 219, 0.5);
		}

		.btn-view-product:hover {
			background: rgba(147, 112, 219, 0.3);
			border-color: #9370db;
		}

		/* Responsive */
		@media (max-width: 768px) {
			.scene-nav {
				top: 10px;
				left: 10px;
			}

			.nav-button {
				font-size: 0.8rem;
				padding: 10px 15px;
			}

			.controls-panel {
				bottom: 10px;
				padding: 10px 20px;
			}

			.info-panel {
				top: 10px;
				right: 10px;
				max-width: 250px;
				padding: 15px;
			}

			.modal-content {
				padding: 25px;
			}

			.loading-title {
				font-size: 2rem;
			}
		}

		/* Accessibility */
		.sr-only {
			position: absolute;
			width: 1px;
			height: 1px;
			padding: 0;
			margin: -1px;
			overflow: hidden;
			clip: rect(0, 0, 0, 0);
			white-space: nowrap;
			border-width: 0;
		}
	</style>
</head>
<body>
	<!-- Loading Screen -->
	<div id="loading-screen">
		<div class="loading-content">
			<div class="loading-icon">🏰</div>
			<h1 class="loading-title">Black Rose Collection</h1>
			<p class="loading-subtitle">Gothic Cathedral</p>
			<div class="progress-bar">
				<div class="progress-fill" id="progress-fill"></div>
			</div>
			<div class="progress-text" id="progress-text">Loading... 0%</div>
		</div>
	</div>

	<!-- 3D Canvas -->
	<div id="three-canvas"></div>

	<!-- Navigation -->
	<nav class="scene-nav" role="navigation" aria-label="Scene navigation">
		<button class="nav-button" id="nav-home" aria-label="Return to home">
			<span class="nav-icon">🏠</span>
			<span>Home</span>
		</button>
		<button class="nav-button" id="nav-shop" aria-label="View shop">
			<span class="nav-icon">🛍️</span>
			<span>Shop</span>
		</button>
		<button class="nav-button" id="nav-info" aria-label="Show information">
			<span class="nav-icon">ℹ️</span>
			<span>Info</span>
		</button>
	</nav>

	<!-- Controls -->
	<div class="controls-panel" role="toolbar" aria-label="Scene controls">
		<button class="control-button" id="toggle-fog" aria-label="Toggle volumetric fog" title="Toggle Fog">
			<span class="control-icon">🌫️</span>
		</button>
		<button class="control-button" id="toggle-audio" aria-label="Toggle spatial audio" title="Toggle Audio">
			<span class="control-icon">🔇</span>
		</button>
		<button class="control-button" id="fullscreen" aria-label="Toggle fullscreen" title="Fullscreen">
			<span class="control-icon">⛶</span>
		</button>
	</div>

	<!-- Info Panel -->
	<aside class="info-panel" id="info-panel" style="display: none;" role="complementary" aria-label="Scene information">
		<button class="info-close" id="info-close" aria-label="Close information">×</button>
		<h2 class="info-title">Gothic Cathedral</h2>
		<p class="info-description">
			Explore moonlit cathedral ruins with realistic volumetric fog and 50,000 fireflies.
			Click glowing spheres to view products. Features spatial audio and dynamic lighting.
		</p>
	</aside>

	<!-- Product Modal -->
	<div class="product-modal" id="product-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
		<div class="modal-content">
			<span class="modal-close" id="modal-close" aria-label="Close modal">&times;</span>
			<img class="modal-image" id="modal-image" src="" alt="">
			<h3 class="modal-title" id="modal-title"></h3>
			<div class="modal-price" id="modal-price"></div>
			<div class="modal-description" id="modal-description"></div>
			<div class="modal-actions">
				<button class="btn-add-cart" id="btn-add-cart">Add to Cart</button>
				<a class="btn-view-product" id="btn-view-product" href="#">View Details</a>
			</div>
		</div>
	</div>

	<!-- Scripts -->
	<script type="module">
		import BlackRoseScene from '<?php echo esc_url( get_template_directory_uri() . '/assets/js/three/scenes/BlackRoseScene.js' ); ?>';

		let scene;
		let currentProduct = null;

		// Initialize scene
		async function initScene() {
			const container = document.getElementById('three-canvas');
			scene = new BlackRoseScene(container);

			// Setup loading progress
			scene.loadingManager.onProgress = (url, loaded, total) => {
				const progress = Math.round((loaded / total) * 100);
				document.getElementById('progress-fill').style.width = progress + '%';
				document.getElementById('progress-text').textContent = `Loading... ${progress}%`;
			};

			// Setup loading complete
			scene.loadingManager.onLoad = () => {
				setTimeout(() => {
					document.getElementById('loading-screen').classList.add('fade-out');
				}, 500);
			};

			// Initialize
			await scene.init();

			// Setup raycasting for product clicks
			setupProductInteraction();
		}

		// Product interaction
		function setupProductInteraction() {
			const canvas = scene.renderer.domElement;

			canvas.addEventListener('click', (event) => {
				const rect = canvas.getBoundingClientRect();
				const mouse = {
					x: ((event.clientX - rect.left) / rect.width) * 2 - 1,
					y: -((event.clientY - rect.top) / rect.height) * 2 + 1
				};

				scene.raycaster.setFromCamera(mouse, scene.camera);
				const intersects = scene.raycaster.intersectObjects(scene.productHotspots);

				if (intersects.length > 0) {
					const product = intersects[0].object.userData.productData;
					showProductModal(product);
				}
			});
		}

		// Show product modal - SECURE: uses textContent
		function showProductModal(product) {
			currentProduct = product;

			document.getElementById('modal-image').src = product.image;
			document.getElementById('modal-image').alt = product.name;
			document.getElementById('modal-title').textContent = product.name;
			document.getElementById('modal-price').textContent = product.price;
			document.getElementById('modal-description').textContent = product.description || '';
			document.getElementById('btn-view-product').href = product.url;

			document.getElementById('product-modal').classList.add('active');
		}

		// Hide product modal
		function hideProductModal() {
			document.getElementById('product-modal').classList.remove('active');
			currentProduct = null;
		}

		// Navigation handlers
		document.getElementById('nav-home').addEventListener('click', () => {
			window.location.href = '<?php echo esc_url( home_url() ); ?>';
		});

		document.getElementById('nav-shop').addEventListener('click', () => {
			window.location.href = '<?php echo esc_url( home_url( '/shop/' ) ); ?>';
		});

		document.getElementById('nav-info').addEventListener('click', () => {
			const panel = document.getElementById('info-panel');
			panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
		});

		document.getElementById('info-close').addEventListener('click', () => {
			document.getElementById('info-panel').style.display = 'none';
		});

		// Control handlers
		document.getElementById('toggle-fog').addEventListener('click', function() {
			scene.toggleFog();
			const icon = this.querySelector('.control-icon');
			icon.textContent = scene.fogEnabled ? '🌫️' : '☀️';
		});

		document.getElementById('toggle-audio').addEventListener('click', function() {
			scene.toggleAudio();
			const icon = this.querySelector('.control-icon');
			icon.textContent = scene.audioEnabled ? '🔊' : '🔇';
		});

		document.getElementById('fullscreen').addEventListener('click', () => {
			if (!document.fullscreenElement) {
				document.documentElement.requestFullscreen();
			} else {
				document.exitFullscreen();
			}
		});

		// Modal handlers
		document.getElementById('modal-close').addEventListener('click', hideProductModal);

		document.getElementById('product-modal').addEventListener('click', (e) => {
			if (e.target.id === 'product-modal') {
				hideProductModal();
			}
		});

		// Add to cart
		document.getElementById('btn-add-cart').addEventListener('click', async () => {
			if (!currentProduct) return;

			try {
				const response = await fetch('<?php echo esc_url( wc_get_cart_url() ); ?>', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/x-www-form-urlencoded',
						'X-WP-Nonce': '<?php echo esc_js( $rest_nonce ); ?>'
					},
					body: `add-to-cart=${currentProduct.id}&quantity=1`
				});

				if (response.ok) {
					alert('Product added to cart!');
					hideProductModal();
				}
			} catch (error) {
				console.error('Error adding to cart:', error);
				alert('Failed to add product to cart');
			}
		});

		// Keyboard shortcuts
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') {
				if (document.getElementById('product-modal').classList.contains('active')) {
					hideProductModal();
				}
			}
			if (e.key === 'f' || e.key === 'F') {
				document.getElementById('toggle-fog').click();
			}
			if (e.key === 'a' || e.key === 'A') {
				document.getElementById('toggle-audio').click();
			}
		});

		// Cleanup on unload
		window.addEventListener('beforeunload', () => {
			if (scene) {
				scene.dispose();
			}
		});

		// Initialize
		initScene();
	</script>

	<?php wp_footer(); ?>
</body>
</html>

<?php
get_footer();
