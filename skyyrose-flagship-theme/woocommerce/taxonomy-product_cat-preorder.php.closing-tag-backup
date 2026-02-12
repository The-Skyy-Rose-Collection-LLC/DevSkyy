<?php
/**
 * Preorder Collection Archive Template
 *
 * WooCommerce taxonomy template for Preorder Collection category.
 * Futuristic portal hub inspired with sci-fi energy theme.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header( 'shop' );

$term = get_queried_object();
$category_id = $term->term_id;
$immersive_page_url = home_url( '/preorder-gateway-3d/' );

// Schema.org CollectionPage markup
$schema_markup = array(
	'@context' => 'https://schema.org',
	'@type' => 'CollectionPage',
	'name' => 'Preorder Collection',
	'description' => 'Futuristic portal hub collection with exclusive preorders',
	'url' => get_term_link( $term ),
);
?>

<script type="application/ld+json">
<?php echo wp_json_encode( $schema_markup ); ?>
</script>

<div class="preorder-collection-archive">
	<!-- Hero Banner -->
	<div class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<div class="hero-inner">
				<span class="hero-badge">⚡ Future Collection</span>
				<h1 class="hero-title">
					<span class="title-icon" aria-hidden="true">🌌</span>
					Preorder Gateway
				</h1>
				<p class="hero-subtitle">Portal Hub Collection</p>
				<p class="hero-description">
					Step into a futuristic portal hub with 262,144 particle systems, custom GLSL energy shaders,
					and Lenis smooth scroll. Explore exclusive preorder collections in our most advanced 3D experience.
				</p>

				<div class="hero-actions">
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-explore-3d">
						<span class="btn-icon" aria-hidden="true">⚡</span>
						<span class="btn-text">
							<span class="btn-main">Enter the Portal</span>
							<span class="btn-sub">3D Immersive Experience</span>
						</span>
						<span class="btn-arrow" aria-hidden="true">→</span>
					</a>

					<button class="btn-scroll-products" onclick="document.getElementById('products-grid').scrollIntoView({behavior: 'smooth'})">
						<span class="btn-icon" aria-hidden="true">📱</span>
						Browse Collection Below
					</button>
				</div>

				<!-- Features -->
				<div class="collection-features">
					<div class="feature-item">
						<span class="feature-icon">🌀</span>
						<span class="feature-label">GLSL Shaders</span>
					</div>
					<div class="feature-item">
						<span class="feature-icon">✨</span>
						<span class="feature-label">262k Particles</span>
					</div>
					<div class="feature-item">
						<span class="feature-icon">🎯</span>
						<span class="feature-label">Smooth Scroll</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Products Section -->
	<div id="products-grid" class="products-section">
		<div class="container">
			<?php if ( $term->description ) : ?>
			<div class="collection-description">
				<?php echo wp_kses_post( wpautop( $term->description ) ); ?>
			</div>
			<?php endif; ?>

			<!-- Filters & Sorting -->
			<div class="products-toolbar">
				<div class="toolbar-left">
					<span class="result-count">
						<?php
						if ( wc_get_loop_prop( 'total' ) ) {
							woocommerce_result_count();
						}
						?>
					</span>
				</div>

				<div class="toolbar-right">
					<?php woocommerce_catalog_ordering(); ?>
				</div>
			</div>

			<?php if ( woocommerce_product_loop() ) : ?>

				<?php do_action( 'woocommerce_before_shop_loop' ); ?>

				<div class="products-grid">
					<?php
					woocommerce_product_loop_start();

					if ( wc_get_loop_prop( 'total' ) ) {
						while ( have_posts() ) {
							the_post();
							do_action( 'woocommerce_shop_loop' );
							wc_get_template_part( 'content', 'product' );
						}
					}

					woocommerce_product_loop_end();
					?>
				</div>

				<?php do_action( 'woocommerce_after_shop_loop' ); ?>

			<?php else : ?>

				<div class="no-products-found">
					<div class="no-products-icon">⚡</div>
					<h2>No products found</h2>
					<p>Portal is initializing. Check back soon for exclusive preorders!</p>
					<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="btn-back-shop">
						Back to Shop
					</a>
				</div>

			<?php endif; ?>

			<!-- Bottom CTA -->
			<div class="bottom-cta">
				<div class="cta-content">
					<h2 class="cta-title">Experience the Future</h2>
					<p class="cta-description">
						Step into our virtual portal hub with custom GLSL shaders, 262,144 particle systems,
						and Lenis smooth scroll. Explore the most advanced 3D collection experience.
					</p>
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-cta-3d">
						<span class="btn-icon" aria-hidden="true">🌌</span>
						Enter 3D Portal
					</a>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
/* Preorder Collection Archive */
.preorder-collection-archive {
	background: #000510;
}

/* Hero Banner */
.collection-hero {
	position: relative;
	min-height: 600px;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, #000510 0%, #0a1a2a 50%, #001a33 100%);
	overflow: hidden;
}

.collection-hero::before {
	content: '';
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background:
		radial-gradient(circle at 20% 50%, rgba(0, 255, 255, 0.2) 0%, transparent 50%),
		radial-gradient(circle at 80% 50%, rgba(255, 0, 255, 0.2) 0%, transparent 50%);
}

.hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: radial-gradient(circle at center, transparent 0%, rgba(0, 5, 16, 0.5) 100%);
}

.hero-content {
	position: relative;
	z-index: 2;
	text-align: center;
	padding: 60px 20px;
	max-width: 900px;
	margin: 0 auto;
}

.hero-badge {
	display: inline-block;
	background: rgba(0, 255, 255, 0.2);
	color: #00ffff;
	padding: 8px 20px;
	border-radius: 30px;
	font-size: 0.85rem;
	font-weight: 700;
	letter-spacing: 1px;
	text-transform: uppercase;
	margin-bottom: 20px;
	border: 2px solid rgba(0, 255, 255, 0.5);
	backdrop-filter: blur(10px);
	font-family: 'Orbitron', monospace;
}

.hero-title {
	font-family: 'Orbitron', monospace;
	font-size: 3.5rem;
	color: #00ffff;
	margin: 0 0 10px 0;
	text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
	line-height: 1.2;
	text-transform: uppercase;
	letter-spacing: 3px;
}

.title-icon {
	font-size: 3rem;
	display: inline-block;
	margin-right: 15px;
	animation: portalPulse 2s ease-in-out infinite;
}

@keyframes portalPulse {
	0%, 100% {
		filter: drop-shadow(0 0 5px rgba(0, 255, 255, 0.8));
		transform: rotate(0deg);
	}
	50% {
		filter: drop-shadow(0 0 20px rgba(255, 0, 255, 1));
		transform: rotate(180deg);
	}
}

.hero-subtitle {
	font-size: 1.4rem;
	color: #ff00ff;
	margin: 0 0 20px 0;
	font-family: 'Orbitron', monospace;
	text-transform: uppercase;
	letter-spacing: 2px;
}

.hero-description {
	font-size: 1.1rem;
	color: #00ddff;
	margin: 0 0 40px 0;
	line-height: 1.8;
	max-width: 700px;
	margin-left: auto;
	margin-right: auto;
}

/* Hero Actions */
.hero-actions {
	display: flex;
	gap: 20px;
	justify-content: center;
	flex-wrap: wrap;
	margin-bottom: 50px;
}

.btn-explore-3d {
	display: inline-flex;
	align-items: center;
	gap: 15px;
	background: linear-gradient(90deg, #00ffff 0%, #ff00ff 100%);
	color: #000;
	padding: 20px 40px;
	border-radius: 50px;
	font-family: 'Orbitron', monospace;
	font-size: 1.1rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(0, 255, 255, 0.5);
	transition: all 0.3s ease;
	border: 3px solid rgba(0, 255, 255, 0.5);
	position: relative;
	overflow: hidden;
	text-transform: uppercase;
}

.btn-explore-3d::before {
	content: '';
	position: absolute;
	top: 0;
	left: -100%;
	width: 100%;
	height: 100%;
	background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
	transition: left 0.5s ease;
}

.btn-explore-3d:hover::before {
	left: 100%;
}

.btn-explore-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(0, 255, 255, 0.7);
}

.btn-text {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}

.btn-main {
	font-size: 1.2rem;
	line-height: 1;
}

.btn-sub {
	font-size: 0.75rem;
	font-weight: 400;
	font-family: system-ui, -apple-system, sans-serif;
	opacity: 0.9;
	margin-top: 3px;
}

.btn-icon {
	font-size: 1.5rem;
}

.btn-arrow {
	font-size: 1.3rem;
	transition: transform 0.3s ease;
}

.btn-explore-3d:hover .btn-arrow {
	transform: translateX(5px);
}

.btn-scroll-products {
	display: inline-flex;
	align-items: center;
	gap: 10px;
	background: rgba(0, 255, 255, 0.1);
	backdrop-filter: blur(10px);
	color: #00ffff;
	padding: 18px 35px;
	border-radius: 50px;
	font-size: 1rem;
	font-weight: 600;
	border: 2px solid rgba(0, 255, 255, 0.5);
	cursor: pointer;
	transition: all 0.3s ease;
	font-family: 'Orbitron', monospace;
	text-transform: uppercase;
}

.btn-scroll-products:hover {
	background: rgba(0, 255, 255, 0.2);
	border-color: #00ffff;
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(0, 255, 255, 0.3);
}

/* Collection Features */
.collection-features {
	display: flex;
	gap: 30px;
	justify-content: center;
	padding-top: 30px;
	border-top: 1px solid rgba(0, 255, 255, 0.3);
}

.feature-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}

.feature-icon {
	font-size: 2rem;
}

.feature-label {
	font-size: 0.85rem;
	color: #00ddff;
	text-transform: uppercase;
	letter-spacing: 1px;
	font-family: 'Orbitron', monospace;
}

/* Products Section */
.products-section {
	padding: 80px 0;
	background: #000510;
}

.container {
	max-width: 1400px;
	margin: 0 auto;
	padding: 0 20px;
}

.collection-description {
	text-align: center;
	max-width: 800px;
	margin: 0 auto 60px;
	font-size: 1.1rem;
	line-height: 1.8;
	color: #00ddff;
}

/* Toolbar */
.products-toolbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40px;
	padding: 20px;
	background: rgba(0, 255, 255, 0.05);
	border-radius: 12px;
	border: 1px solid rgba(0, 255, 255, 0.2);
}

.result-count {
	color: #00ffff;
	font-weight: 600;
	font-family: 'Orbitron', monospace;
}

/* Products Grid */
.products-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 30px;
	margin-bottom: 60px;
}

/* No Products */
.no-products-found {
	text-align: center;
	padding: 80px 20px;
}

.no-products-icon {
	font-size: 4rem;
	margin-bottom: 20px;
	animation: portalPulse 2s ease-in-out infinite;
}

.no-products-found h2 {
	font-family: 'Orbitron', monospace;
	font-size: 2rem;
	color: #00ffff;
	margin-bottom: 15px;
	text-transform: uppercase;
}

.no-products-found p {
	color: #00ddff;
	font-size: 1.1rem;
	margin-bottom: 30px;
}

.btn-back-shop {
	display: inline-block;
	background: linear-gradient(90deg, #00ffff, #ff00ff);
	color: #000;
	padding: 15px 40px;
	border-radius: 30px;
	text-decoration: none;
	font-weight: 600;
	transition: all 0.3s ease;
	border: 2px solid rgba(0, 255, 255, 0.5);
	font-family: 'Orbitron', monospace;
	text-transform: uppercase;
}

.btn-back-shop:hover {
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(0, 255, 255, 0.5);
}

/* Bottom CTA */
.bottom-cta {
	background: linear-gradient(135deg, #000510 0%, #0a1a2a 100%);
	border-radius: 20px;
	padding: 60px 40px;
	text-align: center;
	margin-top: 80px;
	border: 3px solid rgba(0, 255, 255, 0.5);
	box-shadow: 0 10px 40px rgba(0, 255, 255, 0.3);
}

.cta-title {
	font-family: 'Orbitron', monospace;
	font-size: 2.5rem;
	color: #00ffff;
	margin: 0 0 15px 0;
	text-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
	text-transform: uppercase;
}

.cta-description {
	font-size: 1.2rem;
	color: #00ddff;
	margin: 0 0 35px 0;
	max-width: 600px;
	margin-left: auto;
	margin-right: auto;
	line-height: 1.8;
}

.btn-cta-3d {
	display: inline-flex;
	align-items: center;
	gap: 12px;
	background: linear-gradient(90deg, #00ffff 0%, #ff00ff 100%);
	color: #000;
	padding: 20px 50px;
	border-radius: 50px;
	font-family: 'Orbitron', monospace;
	font-size: 1.2rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(0, 255, 255, 0.5);
	transition: all 0.3s ease;
	border: 3px solid rgba(0, 255, 255, 0.5);
	text-transform: uppercase;
}

.btn-cta-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(0, 255, 255, 0.7);
}

/* Responsive */
@media (max-width: 768px) {
	.hero-title {
		font-size: 2.5rem;
	}

	.title-icon {
		font-size: 2rem;
		display: block;
		margin: 0 0 15px 0;
	}

	.hero-actions {
		flex-direction: column;
	}

	.btn-explore-3d,
	.btn-scroll-products {
		width: 100%;
		justify-content: center;
	}

	.collection-features {
		gap: 20px;
		flex-wrap: wrap;
	}

	.products-grid {
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 20px;
	}

	.products-toolbar {
		flex-direction: column;
		gap: 15px;
	}

	.cta-title {
		font-size: 2rem;
	}
}
</style>

<?php
get_footer( 'shop' );
