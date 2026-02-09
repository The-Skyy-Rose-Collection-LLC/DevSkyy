<?php
/**
 * Love Hurts Collection Archive Template
 *
 * WooCommerce taxonomy template for Love Hurts Collection category.
 * Beauty and the Beast inspired with magical romance theme.
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
$immersive_page_url = home_url( '/love-hurts-3d/' );

// Schema.org CollectionPage markup
$schema_markup = array(
	'@context' => 'https://schema.org',
	'@type' => 'CollectionPage',
	'name' => 'Love Hurts Collection',
	'description' => 'Enchanted ballroom collection inspired by Beauty and the Beast',
	'url' => get_term_link( $term ),
);
?>

<script type="application/ld+json">
<?php echo wp_json_encode( $schema_markup ); ?>
</script>

<div class="love-hurts-collection-archive">
	<!-- Hero Banner -->
	<div class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<div class="hero-inner">
				<span class="hero-badge">✨ Enchanted Romance</span>
				<h1 class="hero-title">
					<span class="title-icon" aria-hidden="true">🌹</span>
					Love Hurts Collection
				</h1>
				<p class="hero-subtitle">Beauty & the Beast Inspired</p>
				<p class="hero-description">
					Step into an enchanted ballroom with falling rose petals, mystical lighting,
					and hidden Beauty & the Beast easter eggs. Experience romance with a touch of magic.
				</p>

				<div class="hero-actions">
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-explore-3d">
						<span class="btn-icon" aria-hidden="true">✨</span>
						<span class="btn-text">
							<span class="btn-main">Enter the Ballroom</span>
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
						<span class="feature-icon">🎵</span>
						<span class="feature-label">Spatial Audio</span>
					</div>
					<div class="feature-item">
						<span class="feature-icon">💡</span>
						<span class="feature-label">Dynamic Lighting</span>
					</div>
					<div class="feature-item">
						<span class="feature-icon">🌹</span>
						<span class="feature-label">Physics Petals</span>
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
					<div class="no-products-icon">💔</div>
					<h2>No products found</h2>
					<p>Our enchanted collection is being prepared. Check back soon!</p>
					<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="btn-back-shop">
						Back to Shop
					</a>
				</div>

			<?php endif; ?>

			<!-- Bottom CTA -->
			<div class="bottom-cta">
				<div class="cta-content">
					<h2 class="cta-title">Experience the Enchantment</h2>
					<p class="cta-description">
						Step into our virtual ballroom with realistic physics, spatial audio,
						and dynamic lighting. Watch rose petals fall as you explore our most romantic collection.
					</p>
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-cta-3d">
						<span class="btn-icon" aria-hidden="true">🌹</span>
						Enter 3D Ballroom
					</a>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
/* Love Hurts Collection Archive */
.love-hurts-collection-archive {
	background: #fff;
}

/* Hero Banner */
.collection-hero {
	position: relative;
	min-height: 600px;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, #1a0a0a 0%, #4b0082 50%, #8b008b 100%);
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
		radial-gradient(circle at 20% 50%, rgba(255, 20, 147, 0.2) 0%, transparent 50%),
		radial-gradient(circle at 80% 50%, rgba(147, 112, 219, 0.2) 0%, transparent 50%);
}

.hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: radial-gradient(circle at center, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
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
	background: rgba(255, 255, 255, 0.1);
	color: #ffd700;
	padding: 8px 20px;
	border-radius: 30px;
	font-size: 0.85rem;
	font-weight: 700;
	letter-spacing: 1px;
	text-transform: uppercase;
	margin-bottom: 20px;
	border: 2px solid rgba(255, 215, 0, 0.3);
	backdrop-filter: blur(10px);
}

.hero-title {
	font-family: 'Cinzel', serif;
	font-size: 3.5rem;
	color: #ffd700;
	margin: 0 0 10px 0;
	text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
	line-height: 1.2;
}

.title-icon {
	font-size: 3rem;
	display: inline-block;
	margin-right: 15px;
	animation: roseGlow 2s ease-in-out infinite;
}

@keyframes roseGlow {
	0%, 100% {
		filter: drop-shadow(0 0 5px rgba(255, 20, 147, 0.8));
	}
	50% {
		filter: drop-shadow(0 0 20px rgba(255, 20, 147, 1));
	}
}

.hero-subtitle {
	font-size: 1.4rem;
	color: #ff69b4;
	margin: 0 0 20px 0;
	font-style: italic;
	font-weight: 300;
}

.hero-description {
	font-size: 1.1rem;
	color: #e0e0e0;
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
	background: linear-gradient(135deg, #ff1493 0%, #8b008b 100%);
	color: #fff;
	padding: 20px 40px;
	border-radius: 50px;
	font-family: 'Cinzel', serif;
	font-size: 1.1rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(255, 20, 147, 0.4);
	transition: all 0.3s ease;
	border: 3px solid rgba(255, 215, 0, 0.3);
	position: relative;
	overflow: hidden;
}

.btn-explore-3d::before {
	content: '';
	position: absolute;
	top: 0;
	left: -100%;
	width: 100%;
	height: 100%;
	background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
	transition: left 0.5s ease;
}

.btn-explore-3d:hover::before {
	left: 100%;
}

.btn-explore-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(255, 20, 147, 0.6);
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
	background: rgba(255, 255, 255, 0.1);
	backdrop-filter: blur(10px);
	color: #fff;
	padding: 18px 35px;
	border-radius: 50px;
	font-size: 1rem;
	font-weight: 600;
	border: 2px solid rgba(255, 255, 255, 0.3);
	cursor: pointer;
	transition: all 0.3s ease;
}

.btn-scroll-products:hover {
	background: rgba(255, 255, 255, 0.2);
	border-color: #fff;
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

/* Collection Features */
.collection-features {
	display: flex;
	gap: 30px;
	justify-content: center;
	padding-top: 30px;
	border-top: 1px solid rgba(255, 215, 0, 0.2);
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
	color: #e0e0e0;
	text-transform: uppercase;
	letter-spacing: 1px;
}

/* Products Section */
.products-section {
	padding: 80px 0;
	background: #fff;
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
	color: #333;
}

/* Toolbar */
.products-toolbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40px;
	padding: 20px;
	background: rgba(255, 20, 147, 0.05);
	border-radius: 12px;
	border: 1px solid rgba(255, 20, 147, 0.1);
}

.result-count {
	color: #8b008b;
	font-weight: 600;
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
}

.no-products-found h2 {
	font-family: 'Cinzel', serif;
	font-size: 2rem;
	color: #8b008b;
	margin-bottom: 15px;
}

.btn-back-shop {
	display: inline-block;
	background: linear-gradient(135deg, #ff1493, #8b008b);
	color: #fff;
	padding: 15px 40px;
	border-radius: 30px;
	text-decoration: none;
	font-weight: 600;
	transition: all 0.3s ease;
}

.btn-back-shop:hover {
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(255, 20, 147, 0.4);
}

/* Bottom CTA */
.bottom-cta {
	background: linear-gradient(135deg, #1a0a0a 0%, #4b0082 100%);
	border-radius: 20px;
	padding: 60px 40px;
	text-align: center;
	margin-top: 80px;
	border: 3px solid rgba(255, 215, 0, 0.3);
	box-shadow: 0 10px 40px rgba(75, 0, 130, 0.3);
}

.cta-title {
	font-family: 'Cinzel', serif;
	font-size: 2.5rem;
	color: #ffd700;
	margin: 0 0 15px 0;
	text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}

.cta-description {
	font-size: 1.2rem;
	color: #e0e0e0;
	margin: 0 0 35px 0;
	max-width: 600px;
	margin-left: auto;
	margin-right: auto;
}

.btn-cta-3d {
	display: inline-flex;
	align-items: center;
	gap: 12px;
	background: linear-gradient(135deg, #ff1493 0%, #8b008b 100%);
	color: #fff;
	padding: 20px 50px;
	border-radius: 50px;
	font-family: 'Cinzel', serif;
	font-size: 1.2rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(255, 20, 147, 0.4);
	transition: all 0.3s ease;
}

.btn-cta-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(255, 20, 147, 0.6);
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
}
</style>

<?php
get_footer( 'shop' );
