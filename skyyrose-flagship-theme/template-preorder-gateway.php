<?php
/**
 * Template Name: Preorder Gateway - Portal Hub
 *
 * Immersive 3D experience for Preorder Gateway.
 * Futuristic portal hub with custom GLSL shaders, 262k particles, and Lenis smooth scroll.
 *
 * Features:
 * - Custom GLSL portal shader with swirling energy
 * - 262,144 instanced particles (2^18)
 * - Lenis smooth scroll camera sync
 * - Real-time countdown timers
 * - WooCommerce product integration
 *
 * Performance: Optimized with instanced rendering, 60fps target
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
	<link rel="preload" href="<?php echo esc_url( get_template_directory_uri() . '/assets/js/three/scenes/PreorderGatewayScene.js' ); ?>" as="script">

	<!-- Schema.org -->
	<script type="application/ld+json">
	{
		"@context": "https://schema.org",
		"@type": "WebPage",
		"name": "Preorder Gateway - Portal Hub",
		"description": "Immersive 3D portal hub experience with 262k particles and smooth scroll",
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
		/* Preorder Gateway Styles */
		:root {
			--portal-cyan: #00ffff;
			--portal-magenta: #ff00ff;
			--portal-dark: #000510;
			--portal-blue: #0a1a2a;
		}

		body {
			margin: 0;
			font-family: 'Orbitron', monospace;
			background: var(--portal-dark);
			color: var(--portal-cyan);
			overflow-x: hidden;
		}

		/* Loading Screen */
		#loading-screen {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: linear-gradient(135deg, #000510 0%, #0a1a2a 100%);
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
			color: var(--portal-cyan);
		}

		.loading-icon {
			font-size: 4rem;
			margin-bottom: 30px;
			animation: spin 3s linear infinite;
		}

		@keyframes spin {
			from { transform: rotate(0deg); }
			to { transform: rotate(360deg); }
		}

		.loading-title {
			font-size: 2.5rem;
			margin: 0 0 10px 0;
			color: var(--portal-cyan);
			text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
			text-transform: uppercase;
			letter-spacing: 3px;
		}

		.loading-subtitle {
			font-size: 1.2rem;
			margin: 0 0 30px 0;
			color: var(--portal-magenta);
			text-transform: uppercase;
			letter-spacing: 2px;
		}

		.progress-bar {
			width: 300px;
			height: 4px;
			background: rgba(0, 255, 255, 0.2);
			border-radius: 2px;
			overflow: hidden;
			margin-bottom: 10px;
		}

		.progress-fill {
			height: 100%;
			background: linear-gradient(90deg, var(--portal-cyan), var(--portal-magenta));
			width: 0%;
			transition: width 0.3s ease;
			box-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
		}

		.progress-text {
			font-size: 0.9rem;
			color: var(--portal-cyan);
		}

		/* 3D Canvas */
		#three-canvas {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			z-index: 1;
		}

		/* Scroll content */
		.scroll-content {
			position: relative;
			z-index: 2;
			pointer-events: none;
		}

		.scroll-section {
			min-height: 100vh;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 60px 20px;
		}

		/* Countdown Section */
		.countdown-section {
			background: rgba(10, 26, 42, 0.8);
			backdrop-filter: blur(10px);
			border: 2px solid var(--portal-cyan);
			border-radius: 20px;
			padding: 60px;
			text-align: center;
			max-width: 800px;
			margin: 0 auto;
			pointer-events: all;
			box-shadow: 0 0 40px rgba(0, 255, 255, 0.3);
		}

		.countdown-title {
			font-size: 2.5rem;
			margin: 0 0 20px 0;
			color: var(--portal-cyan);
			text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
			text-transform: uppercase;
			letter-spacing: 3px;
		}

		.countdown-subtitle {
			font-size: 1.2rem;
			margin: 0 0 40px 0;
			color: var(--portal-magenta);
		}

		.countdown-grid {
			display: grid;
			grid-template-columns: repeat(4, 1fr);
			gap: 20px;
			margin-bottom: 40px;
		}

		.countdown-item {
			background: rgba(0, 255, 255, 0.1);
			border: 2px solid var(--portal-cyan);
			border-radius: 12px;
			padding: 20px;
		}

		.countdown-value {
			font-size: 3rem;
			font-weight: 700;
			color: var(--portal-cyan);
			text-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
		}

		.countdown-label {
			font-size: 0.9rem;
			color: var(--portal-cyan);
			text-transform: uppercase;
			letter-spacing: 2px;
			margin-top: 10px;
		}

		.btn-preorder {
			display: inline-block;
			background: linear-gradient(90deg, var(--portal-cyan), var(--portal-magenta));
			color: #000;
			padding: 20px 50px;
			border-radius: 50px;
			font-size: 1.2rem;
			font-weight: 700;
			text-decoration: none;
			text-transform: uppercase;
			letter-spacing: 2px;
			transition: all 0.3s ease;
			box-shadow: 0 10px 30px rgba(0, 255, 255, 0.5);
		}

		.btn-preorder:hover {
			transform: translateY(-3px);
			box-shadow: 0 15px 40px rgba(0, 255, 255, 0.7);
		}

		/* Navigation */
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
			background: rgba(10, 26, 42, 0.9);
			backdrop-filter: blur(10px);
			color: var(--portal-cyan);
			border: 2px solid var(--portal-cyan);
			padding: 12px 20px;
			border-radius: 8px;
			font-family: 'Orbitron', monospace;
			font-size: 0.9rem;
			cursor: pointer;
			transition: all 0.3s ease;
			display: flex;
			align-items: center;
			gap: 10px;
			text-transform: uppercase;
		}

		.nav-button:hover {
			background: rgba(0, 255, 255, 0.2);
			transform: translateX(5px);
			box-shadow: 0 5px 15px rgba(0, 255, 255, 0.3);
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
			background: rgba(10, 26, 42, 0.9);
			backdrop-filter: blur(10px);
			padding: 15px 30px;
			border-radius: 50px;
			border: 2px solid var(--portal-cyan);
		}

		.control-button {
			background: transparent;
			border: none;
			color: var(--portal-cyan);
			font-size: 1.8rem;
			cursor: pointer;
			transition: all 0.3s ease;
			padding: 10px;
			border-radius: 50%;
		}

		.control-button:hover {
			background: rgba(0, 255, 255, 0.2);
			transform: scale(1.1);
		}

		/* Product Modal */
		.product-modal {
			display: none;
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: rgba(0, 5, 16, 0.9);
			z-index: 1000;
			align-items: center;
			justify-content: center;
		}

		.product-modal.active {
			display: flex;
		}

		.modal-content {
			background: linear-gradient(135deg, #0a1a2a 0%, #000510 100%);
			padding: 40px;
			border-radius: 20px;
			max-width: 500px;
			width: 90%;
			border: 3px solid var(--portal-cyan);
			box-shadow: 0 20px 60px rgba(0, 255, 255, 0.5);
		}

		.modal-close {
			float: right;
			font-size: 2rem;
			color: var(--portal-cyan);
			cursor: pointer;
			line-height: 1;
			transition: color 0.3s ease;
		}

		.modal-close:hover {
			color: var(--portal-magenta);
		}

		.modal-image {
			width: 100%;
			height: 300px;
			object-fit: cover;
			border-radius: 12px;
			margin-bottom: 20px;
			border: 2px solid var(--portal-cyan);
		}

		.modal-title {
			font-size: 1.8rem;
			color: var(--portal-cyan);
			margin: 0 0 10px 0;
			text-transform: uppercase;
		}

		.modal-price {
			font-size: 1.5rem;
			color: var(--portal-magenta);
			margin: 0 0 20px 0;
			font-weight: 700;
		}

		.modal-actions {
			display: flex;
			gap: 15px;
		}

		.btn-add-cart {
			flex: 1;
			padding: 15px;
			border-radius: 10px;
			font-family: 'Orbitron', monospace;
			font-size: 1rem;
			font-weight: 600;
			cursor: pointer;
			transition: all 0.3s ease;
			border: none;
			background: linear-gradient(90deg, var(--portal-cyan), var(--portal-magenta));
			color: #000;
			text-transform: uppercase;
		}

		.btn-add-cart:hover {
			transform: translateY(-2px);
			box-shadow: 0 10px 30px rgba(0, 255, 255, 0.5);
		}

		/* Responsive */
		@media (max-width: 768px) {
			.countdown-grid {
				grid-template-columns: repeat(2, 1fr);
			}

			.countdown-value {
				font-size: 2rem;
			}

			.countdown-section {
				padding: 40px 30px;
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
			<div class="loading-icon">⚡</div>
			<h1 class="loading-title">Preorder Gateway</h1>
			<p class="loading-subtitle">Portal Hub Initializing</p>
			<div class="progress-bar">
				<div class="progress-fill" id="progress-fill"></div>
			</div>
			<div class="progress-text" id="progress-text">Loading... 0%</div>
		</div>
	</div>

	<!-- 3D Canvas -->
	<div id="three-canvas"></div>

	<!-- Scroll Content -->
	<div class="scroll-content">
		<!-- Hero Section -->
		<div class="scroll-section">
			<div class="countdown-section">
				<h2 class="countdown-title">Portal Opens In</h2>
				<p class="countdown-subtitle">Exclusive Preorder Collection</p>

				<div class="countdown-grid" id="countdown">
					<div class="countdown-item">
						<div class="countdown-value" id="days">00</div>
						<div class="countdown-label">Days</div>
					</div>
					<div class="countdown-item">
						<div class="countdown-value" id="hours">00</div>
						<div class="countdown-label">Hours</div>
					</div>
					<div class="countdown-item">
						<div class="countdown-value" id="minutes">00</div>
						<div class="countdown-label">Minutes</div>
					</div>
					<div class="countdown-item">
						<div class="countdown-value" id="seconds">00</div>
						<div class="countdown-label">Seconds</div>
					</div>
				</div>

				<a href="<?php echo esc_url( home_url( '/product-category/preorder/' ) ); ?>" class="btn-preorder">
					Explore Collection
				</a>
			</div>
		</div>

		<!-- Additional scroll sections can be added here -->
		<div class="scroll-section" style="min-height: 50vh;"></div>
	</div>

	<!-- Navigation -->
	<nav class="scene-nav" role="navigation" aria-label="Scene navigation">
		<button class="nav-button" id="nav-home" aria-label="Return to home">
			<span>🏠</span>
			<span>Home</span>
		</button>
		<button class="nav-button" id="nav-shop" aria-label="View shop">
			<span>🛍️</span>
			<span>Shop</span>
		</button>
	</nav>

	<!-- Controls -->
	<div class="controls-panel" role="toolbar" aria-label="Scene controls">
		<button class="control-button" id="toggle-portal" aria-label="Toggle portal effect" title="Toggle Portal">
			<span class="control-icon">⚡</span>
		</button>
		<button class="control-button" id="fullscreen" aria-label="Toggle fullscreen" title="Fullscreen">
			<span class="control-icon">⛶</span>
		</button>
	</div>

	<!-- Product Modal -->
	<div class="product-modal" id="product-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
		<div class="modal-content">
			<span class="modal-close" id="modal-close" aria-label="Close modal">&times;</span>
			<img class="modal-image" id="modal-image" src="" alt="">
			<h3 class="modal-title" id="modal-title"></h3>
			<div class="modal-price" id="modal-price"></div>
			<div class="modal-actions">
				<button class="btn-add-cart" id="btn-add-cart">Add to Cart</button>
			</div>
		</div>
	</div>

	<!-- Scripts -->
	<script type="module">
		import PreorderGatewayScene from '<?php echo esc_url( get_template_directory_uri() . '/assets/js/three/scenes/PreorderGatewayScene.js' ); ?>';

		let scene;
		let currentProduct = null;

		// Initialize scene
		async function initScene() {
			const container = document.getElementById('three-canvas');
			scene = new PreorderGatewayScene(container);

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

			// Setup product interaction
			setupProductInteraction();

			// Update countdown
			updateCountdown();
			setInterval(updateCountdown, 1000);
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
				const intersects = scene.raycaster.intersectObjects(scene.productPortals);

				if (intersects.length > 0) {
					const product = intersects[0].object.userData.productData;
					showProductModal(product);
				}
			});
		}

		// Countdown timer
		function updateCountdown() {
			const countdown = scene.getCountdownData();

			if (countdown.expired) {
				document.getElementById('days').textContent = '00';
				document.getElementById('hours').textContent = '00';
				document.getElementById('minutes').textContent = '00';
				document.getElementById('seconds').textContent = '00';
				return;
			}

			document.getElementById('days').textContent = String(countdown.days).padStart(2, '0');
			document.getElementById('hours').textContent = String(countdown.hours).padStart(2, '0');
			document.getElementById('minutes').textContent = String(countdown.minutes).padStart(2, '0');
			document.getElementById('seconds').textContent = String(countdown.seconds).padStart(2, '0');
		}

		// Show product modal - SECURE: uses textContent
		function showProductModal(product) {
			currentProduct = product;

			document.getElementById('modal-image').src = product.image;
			document.getElementById('modal-image').alt = product.name;
			document.getElementById('modal-title').textContent = product.name;
			document.getElementById('modal-price').textContent = product.price;

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

		// Control handlers
		document.getElementById('toggle-portal').addEventListener('click', function() {
			scene.togglePortal();
			const icon = this.querySelector('.control-icon');
			icon.textContent = scene.portalActive ? '⚡' : '⭕';
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
