<?php
/**
 * Template Name: Signature Collection - Luxury Rose Garden Pavilion
 * Description: 3D immersive shopping experience for Signature Collection
 *
 * Context7 Implementation:
 * - Three.js glass materials with transmission
 * - GSAP camera animations
 * - WooCommerce REST API integration
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

get_header();
?>

<div id="signature-collection-experience" class="three-scene-wrapper signature-collection">
	<!-- Loading Screen -->
	<div id="loading-screen" class="loading-overlay">
		<div class="loading-content">
			<div class="signature-loader">
				<div class="rose-icon">🌹</div>
				<p class="loading-text">Entering the luxury pavilion...</p>
				<div class="loading-progress">
					<div class="progress-bar" id="progress-bar"></div>
					<span class="progress-text" id="progress-text">0%</span>
				</div>
			</div>
		</div>
	</div>

	<!-- 3D Scene Container -->
	<div id="signature-scene-container" class="scene-container"></div>

	<!-- UI Overlay -->
	<div class="scene-ui-overlay">
		<!-- Navigation Menu -->
		<nav class="signature-navigation" aria-label="Collection Navigation">
			<h1 class="collection-title">Signature Collection</h1>
			<p class="collection-subtitle">Luxury Rose Garden Pavilion</p>
			<ul class="scene-nav-menu">
				<li><button class="nav-btn" data-section="entrance" aria-label="View Entrance">Entrance</button></li>
				<li><button class="nav-btn" data-section="center" aria-label="View Center">Center Gallery</button></li>
				<li><button class="nav-btn" data-section="products" aria-label="View Products">Products</button></li>
			</ul>

			<!-- Link to Static Archive -->
			<a href="<?php echo esc_url( get_term_link( 'signature-collection', 'product_cat' ) ); ?>" class="btn-static-view">
				<span class="icon">📱</span>
				View Grid Layout
			</a>
		</nav>

		<!-- Instructions -->
		<div class="scene-instructions" role="status" aria-live="polite">
			<p><span class="instruction-icon" aria-hidden="true">🖱️</span> <span class="sr-only">Mouse:</span> Click and drag to explore</p>
			<p><span class="instruction-icon" aria-hidden="true">📱</span> <span class="sr-only">Touch:</span> One finger to rotate, two to zoom</p>
			<p><span class="instruction-icon" aria-hidden="true">✨</span> Click glowing markers to view products</p>
		</div>

		<!-- Performance Stats (Dev Only) -->
		<?php if ( defined( 'WP_DEBUG' ) && WP_DEBUG ) : ?>
		<div id="stats-container" class="stats-debug"></div>
		<?php endif; ?>
	</div>

	<!-- Product Modal -->
	<div id="product-modal" class="signature-modal" style="display: none;" role="dialog" aria-modal="true" aria-labelledby="modal-title">
		<div class="modal-overlay" role="presentation"></div>
		<div class="modal-content">
			<button class="modal-close" aria-label="Close product details">&times;</button>

			<div class="modal-inner">
				<div class="product-display">
					<div id="product-image" class="product-image-container">
						<!-- Product image loaded dynamically -->
					</div>

					<div class="product-info">
						<h2 id="modal-title" class="product-title"></h2>
						<div id="product-price" class="product-price"></div>
						<div id="product-description" class="product-description"></div>

						<div class="product-meta">
							<div class="product-sku"></div>
							<div class="product-availability"></div>
						</div>

						<div class="product-actions">
							<button id="add-to-cart-btn" class="btn-signature btn-add-cart">
								<span class="btn-icon" aria-hidden="true">🛒</span>
								Add to Cart
							</button>
							<a href="#" id="view-details-link" class="btn-signature btn-view-details">
								View Full Details
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
/* Signature Collection Styles */
.three-scene-wrapper.signature-collection {
	position: relative;
	width: 100vw;
	height: 100vh;
	overflow: hidden;
	background: linear-gradient(135deg, #fff5e6 0%, #ffd9a6 100%);
}

/* Loading Screen */
.loading-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, #fff5e6 0%, #ffd9a6 50%, #ffcc99 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
	transition: opacity 0.5s ease-out;
}

.loading-overlay.fade-out {
	opacity: 0;
	pointer-events: none;
}

.signature-loader {
	text-align: center;
	color: #8b4513;
}

.rose-icon {
	font-size: 4rem;
	animation: roseFloat 3s ease-in-out infinite;
}

@keyframes roseFloat {
	0%, 100% { transform: translateY(0) rotate(0deg); }
	50% { transform: translateY(-20px) rotate(10deg); }
}

.loading-text {
	font-family: 'Cinzel', serif;
	font-size: 1.3rem;
	margin: 20px 0;
	text-shadow: 0 2px 4px rgba(139, 69, 19, 0.2);
}

.loading-progress {
	width: 350px;
	height: 6px;
	background: rgba(139, 69, 19, 0.2);
	border-radius: 3px;
	overflow: hidden;
	margin: 20px auto;
	position: relative;
}

.progress-bar {
	width: 0%;
	height: 100%;
	background: linear-gradient(90deg, #ffd700, #ffb347);
	transition: width 0.3s ease-out;
}

.progress-text {
	font-size: 0.9rem;
	font-weight: bold;
	color: #8b4513;
	margin-top: 10px;
	display: block;
}

/* Scene Container */
.scene-container {
	width: 100%;
	height: 100%;
}

/* UI Overlay */
.scene-ui-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	pointer-events: none;
	z-index: 10;
}

.scene-ui-overlay > * {
	pointer-events: auto;
}

/* Navigation */
.signature-navigation {
	position: absolute;
	top: 20px;
	left: 20px;
	background: rgba(255, 255, 255, 0.95);
	backdrop-filter: blur(10px);
	padding: 25px;
	border-radius: 12px;
	border: 2px solid rgba(255, 215, 0, 0.5);
	box-shadow: 0 8px 32px rgba(139, 69, 19, 0.15);
	max-width: 280px;
}

.collection-title {
	font-family: 'Cinzel', serif;
	font-size: 1.6rem;
	color: #8b4513;
	margin: 0 0 5px 0;
	text-shadow: 0 2px 4px rgba(255, 215, 0, 0.3);
}

.collection-subtitle {
	font-size: 0.9rem;
	color: #a0522d;
	margin: 0 0 20px 0;
	font-style: italic;
}

.scene-nav-menu {
	list-style: none;
	padding: 0;
	margin: 0 0 20px 0;
}

.scene-nav-menu li {
	margin-bottom: 10px;
}

.nav-btn {
	background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 183, 71, 0.1));
	border: 2px solid rgba(255, 215, 0, 0.6);
	color: #8b4513;
	padding: 12px 20px;
	border-radius: 8px;
	cursor: pointer;
	font-family: 'Cinzel', serif;
	font-size: 0.95rem;
	font-weight: 600;
	width: 100%;
	text-align: left;
	transition: all 0.3s ease;
}

.nav-btn:hover,
.nav-btn:focus {
	background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 183, 71, 0.2));
	box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
	transform: translateX(5px);
}

.btn-static-view {
	display: block;
	background: #8b4513;
	color: #fff;
	padding: 12px;
	border-radius: 8px;
	text-align: center;
	text-decoration: none;
	font-size: 0.9rem;
	font-weight: 600;
	transition: all 0.3s ease;
}

.btn-static-view:hover {
	background: #a0522d;
	box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
}

.btn-static-view .icon {
	margin-right: 8px;
}

/* Instructions */
.scene-instructions {
	position: absolute;
	bottom: 20px;
	left: 20px;
	background: rgba(255, 255, 255, 0.95);
	backdrop-filter: blur(10px);
	padding: 15px 20px;
	border-radius: 10px;
	border: 2px solid rgba(255, 215, 0, 0.5);
	color: #8b4513;
	font-size: 0.9rem;
	box-shadow: 0 4px 16px rgba(139, 69, 19, 0.1);
}

.scene-instructions p {
	margin: 8px 0;
	display: flex;
	align-items: center;
}

.instruction-icon {
	margin-right: 10px;
	font-size: 1.2rem;
}

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

/* Product Modal */
.signature-modal {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	z-index: 10000;
}

.modal-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: rgba(0, 0, 0, 0.85);
	backdrop-filter: blur(8px);
}

.modal-content {
	position: relative;
	width: 90%;
	max-width: 1000px;
	height: 85%;
	margin: 5% auto;
	background: linear-gradient(135deg, #fff 0%, #fff5e6 100%);
	border-radius: 20px;
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	border: 3px solid #ffd700;
	z-index: 10001;
	overflow: hidden;
}

.modal-close {
	position: absolute;
	top: 15px;
	right: 15px;
	background: rgba(255, 255, 255, 0.9);
	border: 2px solid #ffd700;
	color: #8b4513;
	width: 45px;
	height: 45px;
	border-radius: 50%;
	font-size: 1.8rem;
	cursor: pointer;
	z-index: 10002;
	transition: all 0.3s ease;
	display: flex;
	align-items: center;
	justify-content: center;
}

.modal-close:hover {
	transform: scale(1.1) rotate(90deg);
	background: #ffd700;
	color: #fff;
}

.modal-inner {
	padding: 30px;
	height: 100%;
	overflow-y: auto;
}

.product-display {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 40px;
	height: 100%;
}

.product-image-container {
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 245, 230, 0.5);
	border-radius: 15px;
	overflow: hidden;
	border: 2px solid rgba(255, 215, 0, 0.3);
}

.product-image-container img {
	max-width: 100%;
	max-height: 100%;
	object-fit: contain;
}

.product-info {
	color: #8b4513;
}

.product-title {
	font-family: 'Cinzel', serif;
	font-size: 2.2rem;
	margin-bottom: 15px;
	color: #8b4513;
	text-shadow: 0 2px 4px rgba(255, 215, 0, 0.2);
}

.product-price {
	font-size: 1.8rem;
	font-weight: bold;
	margin-bottom: 20px;
	color: #a0522d;
}

.product-description {
	font-size: 1.05rem;
	line-height: 1.7;
	margin-bottom: 25px;
	color: #5d4037;
}

.product-actions {
	display: flex;
	gap: 15px;
	margin-top: 30px;
}

.btn-signature {
	padding: 15px 30px;
	border-radius: 10px;
	font-family: 'Cinzel', serif;
	font-size: 1.05rem;
	font-weight: 600;
	cursor: pointer;
	transition: all 0.3s ease;
	border: 2px solid;
	text-decoration: none;
	display: inline-flex;
	align-items: center;
	justify-content: center;
}

.btn-add-cart {
	background: linear-gradient(135deg, #ffd700, #ffb347);
	border-color: #8b4513;
	color: #8b4513;
	flex: 1;
}

.btn-add-cart:hover {
	background: linear-gradient(135deg, #ffe55c, #ffc266);
	box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
	transform: translateY(-2px);
}

.btn-view-details {
	background: transparent;
	border-color: #8b4513;
	color: #8b4513;
}

.btn-view-details:hover {
	background: rgba(139, 69, 19, 0.1);
	box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
}

.btn-icon {
	margin-right: 8px;
}

/* Responsive Design */
@media (max-width: 768px) {
	.product-display {
		grid-template-columns: 1fr;
	}

	.signature-navigation,
	.scene-instructions {
		font-size: 0.85rem;
		padding: 12px 15px;
	}

	.collection-title {
		font-size: 1.3rem;
	}

	.modal-content {
		width: 95%;
		height: 90%;
	}

	.product-actions {
		flex-direction: column;
	}
}

/* Stats Debug */
.stats-debug {
	position: absolute;
	top: 20px;
	right: 20px;
	background: rgba(0, 0, 0, 0.8);
	color: #0f0;
	padding: 10px;
	border-radius: 5px;
	font-family: monospace;
	font-size: 0.8rem;
}
</style>

<script type="module">
import SignatureScene from '<?php echo get_template_directory_uri(); ?>/assets/js/three/scenes/SignatureScene.js';

document.addEventListener('DOMContentLoaded', () => {
	const container = document.getElementById('signature-scene-container');
	const loadingScreen = document.getElementById('loading-screen');
	const progressBar = document.getElementById('progress-bar');
	const progressText = document.getElementById('progress-text');

	// Initialize scene
	const scene = new SignatureScene(container);

	// Update loading progress
	scene.onLoadProgress = (url, itemsLoaded, itemsTotal, progress) => {
		progressBar.style.width = `${progress}%`;
		progressText.textContent = `${Math.round(progress)}%`;
	};

	// Hide loading screen after initialization
	scene.onLoadComplete = () => {
		setTimeout(() => {
			loadingScreen.classList.add('fade-out');
			setTimeout(() => {
				loadingScreen.style.display = 'none';
			}, 500);
		}, 1000);
	};

	// Navigation buttons
	document.querySelectorAll('.nav-btn').forEach(btn => {
		btn.addEventListener('click', (e) => {
			const section = e.target.dataset.section;
			scene.navigateToSection(section);
		});
	});

	// Product hotspot click handler
	window.addEventListener('productHotspotClick', (e) => {
		const { productId, productName, productPrice, productImage, productUrl } = e.detail;
		openProductModal(productId, productName, productPrice, productImage, productUrl);
	});

	// Modal controls
	const modal = document.getElementById('product-modal');
	const modalClose = modal.querySelector('.modal-close');
	const modalOverlay = modal.querySelector('.modal-overlay');

	modalClose.addEventListener('click', closeProductModal);
	modalOverlay.addEventListener('click', closeProductModal);

	// Keyboard accessibility for modal
	document.addEventListener('keydown', (e) => {
		if (e.key === 'Escape' && modal.style.display === 'block') {
			closeProductModal();
		}
	});

	function openProductModal(productId, productName, productPrice, productImage, productUrl) {
		// Set modal content using textContent for security
		document.getElementById('modal-title').textContent = productName;

		// For price HTML (with currency symbols), use textContent if possible or sanitize
		const priceElement = document.getElementById('product-price');
		priceElement.textContent = productPrice;

		// Set product image
		const productImageContainer = document.getElementById('product-image');
		productImageContainer.textContent = ''; // Clear previous content
		if (productImage) {
			const img = document.createElement('img');
			img.src = productImage;
			img.alt = productName;
			productImageContainer.appendChild(img);
		}

		// Set view details link
		document.getElementById('view-details-link').href = productUrl;

		// Set add to cart button
		const addToCartBtn = document.getElementById('add-to-cart-btn');
		addToCartBtn.dataset.productId = productId;

		// Show modal
		modal.style.display = 'block';

		// Focus on close button for accessibility
		setTimeout(() => modalClose.focus(), 100);
	}

	function closeProductModal() {
		modal.style.display = 'none';
	}

	// Add to cart functionality (WooCommerce integration)
	document.getElementById('add-to-cart-btn').addEventListener('click', function() {
		const productId = this.dataset.productId;

		// Add to cart via AJAX
		const formData = new FormData();
		formData.append('action', 'woocommerce_add_to_cart');
		formData.append('product_id', productId);
		formData.append('quantity', 1);

		fetch('<?php echo admin_url('admin-ajax.php'); ?>', {
			method: 'POST',
			body: formData
		})
		.then(res => res.json())
		.then(data => {
			if (data.success) {
				alert('Product added to cart!');
				closeProductModal();
				// Update cart count if applicable
				document.dispatchEvent(new Event('wc-fragments-refresh'));
			} else {
				alert('Error adding to cart. Please try again.');
			}
		})
		.catch(error => {
			console.error('Add to cart error:', error);
			alert('Error adding to cart. Please try again.');
		});
	});

	// Cleanup on page unload
	window.addEventListener('beforeunload', () => {
		scene.dispose();
	});
});
</script>

<?php get_footer(); ?>
