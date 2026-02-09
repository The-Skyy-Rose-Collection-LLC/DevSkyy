<?php
/**
 * Signature Collection Archive Template
 *
 * WooCommerce taxonomy template for Signature Collection category.
 * Provides traditional grid layout with prominent link to 3D immersive experience.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header( 'shop' );

// Get the current category
$term = get_queried_object();
$category_id = $term->term_id;

// Get the 3D template page URL (assuming you create a page using the template)
$immersive_page_url = home_url( '/signature-collection-3d/' );

// Schema.org CollectionPage markup
$schema_markup = array(
	'@context' => 'https://schema.org',
	'@type' => 'CollectionPage',
	'name' => 'Signature Collection',
	'description' => 'Luxury rose garden collection featuring premium preserved roses',
	'url' => get_term_link( $term ),
);
?>

<script type="application/ld+json">
<?php echo wp_json_encode( $schema_markup ); ?>
</script>

<div class="signature-collection-archive">
	<!-- Hero Banner with 3D CTA -->
	<div class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<div class="hero-inner">
				<span class="hero-badge">Premium Collection</span>
				<h1 class="hero-title">
					<span class="title-icon" aria-hidden="true">🌹</span>
					Signature Collection
				</h1>
				<p class="hero-subtitle">Luxury Rose Garden Pavilion</p>
				<p class="hero-description">
					Experience our finest preserved roses in an immersive 3D environment.
					Step into a virtual glass pavilion bathed in golden hour light.
				</p>

				<div class="hero-actions">
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-explore-3d">
						<span class="btn-icon" aria-hidden="true">✨</span>
						<span class="btn-text">
							<span class="btn-main">Explore in 3D</span>
							<span class="btn-sub">Immersive Experience</span>
						</span>
						<span class="btn-arrow" aria-hidden="true">→</span>
					</a>

					<button class="btn-scroll-products" onclick="document.getElementById('products-grid').scrollIntoView({behavior: 'smooth'})">
						<span class="btn-icon" aria-hidden="true">📱</span>
						Browse Products Below
					</button>
				</div>

				<!-- Quick Stats -->
				<div class="collection-stats">
					<div class="stat-item">
						<span class="stat-value"><?php echo esc_html( $term->count ); ?></span>
						<span class="stat-label">Products</span>
					</div>
					<div class="stat-item">
						<span class="stat-value">Premium</span>
						<span class="stat-label">Quality</span>
					</div>
					<div class="stat-item">
						<span class="stat-value">3D</span>
						<span class="stat-label">Experience</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Products Section -->
	<div id="products-grid" class="products-section">
		<div class="container">
			<!-- Collection Description -->
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

				<?php
				/**
				 * Hook: woocommerce_before_shop_loop.
				 */
				do_action( 'woocommerce_before_shop_loop' );
				?>

				<div class="products-grid">
					<?php
					woocommerce_product_loop_start();

					if ( wc_get_loop_prop( 'total' ) ) {
						while ( have_posts() ) {
							the_post();

							/**
							 * Hook: woocommerce_shop_loop.
							 */
							do_action( 'woocommerce_shop_loop' );

							wc_get_template_part( 'content', 'product' );
						}
					}

					woocommerce_product_loop_end();
					?>
				</div>

				<?php
				/**
				 * Hook: woocommerce_after_shop_loop.
				 */
				do_action( 'woocommerce_after_shop_loop' );
				?>

			<?php else : ?>

				<div class="no-products-found">
					<div class="no-products-icon">🌹</div>
					<h2>No products found</h2>
					<p>We're currently updating our Signature Collection. Please check back soon!</p>
					<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="btn-back-shop">
						Back to Shop
					</a>
				</div>

			<?php endif; ?>

			<!-- Bottom CTA -->
			<div class="bottom-cta">
				<div class="cta-content">
					<h2 class="cta-title">Want the Full Experience?</h2>
					<p class="cta-description">
						Step into our virtual glass pavilion and explore products in stunning 3D with golden hour lighting.
					</p>
					<a href="<?php echo esc_url( $immersive_page_url ); ?>" class="btn-cta-3d">
						<span class="btn-icon" aria-hidden="true">✨</span>
						Launch 3D Experience
					</a>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
/* Signature Collection Archive Styles */
.signature-collection-archive {
	background: #fff;
}

/* Hero Banner */
.collection-hero {
	position: relative;
	min-height: 600px;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, #fff5e6 0%, #ffd9a6 50%, #ffcc99 100%);
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
		radial-gradient(circle at 20% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 50%),
		radial-gradient(circle at 80% 50%, rgba(255, 183, 71, 0.1) 0%, transparent 50%);
	pointer-events: none;
}

.hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: radial-gradient(circle at center, transparent 0%, rgba(139, 69, 19, 0.05) 100%);
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
	background: rgba(255, 255, 255, 0.95);
	color: #8b4513;
	padding: 8px 20px;
	border-radius: 30px;
	font-size: 0.85rem;
	font-weight: 700;
	letter-spacing: 1px;
	text-transform: uppercase;
	margin-bottom: 20px;
	border: 2px solid rgba(255, 215, 0, 0.5);
}

.hero-title {
	font-family: 'Cinzel', serif;
	font-size: 3.5rem;
	color: #8b4513;
	margin: 0 0 10px 0;
	text-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
	line-height: 1.2;
}

.title-icon {
	font-size: 3rem;
	display: inline-block;
	margin-right: 15px;
	animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
	0%, 100% { transform: translateY(0); }
	50% { transform: translateY(-10px); }
}

.hero-subtitle {
	font-size: 1.4rem;
	color: #a0522d;
	margin: 0 0 20px 0;
	font-style: italic;
	font-weight: 300;
}

.hero-description {
	font-size: 1.1rem;
	color: #5d4037;
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
	background: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
	color: #8b4513;
	padding: 20px 40px;
	border-radius: 50px;
	font-family: 'Cinzel', serif;
	font-size: 1.1rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(255, 215, 0, 0.3);
	transition: all 0.3s ease;
	border: 3px solid rgba(139, 69, 19, 0.2);
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
	background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
	transition: left 0.5s ease;
}

.btn-explore-3d:hover::before {
	left: 100%;
}

.btn-explore-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(255, 215, 0, 0.4);
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
	opacity: 0.8;
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
	background: rgba(255, 255, 255, 0.95);
	color: #8b4513;
	padding: 18px 35px;
	border-radius: 50px;
	font-size: 1rem;
	font-weight: 600;
	border: 2px solid rgba(139, 69, 19, 0.3);
	cursor: pointer;
	transition: all 0.3s ease;
}

.btn-scroll-products:hover {
	background: #fff;
	border-color: #8b4513;
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(139, 69, 19, 0.15);
}

/* Collection Stats */
.collection-stats {
	display: flex;
	gap: 40px;
	justify-content: center;
	padding-top: 30px;
	border-top: 2px solid rgba(139, 69, 19, 0.1);
}

.stat-item {
	text-align: center;
}

.stat-value {
	display: block;
	font-family: 'Cinzel', serif;
	font-size: 2rem;
	font-weight: 700;
	color: #8b4513;
	margin-bottom: 5px;
}

.stat-label {
	display: block;
	font-size: 0.85rem;
	color: #a0522d;
	text-transform: uppercase;
	letter-spacing: 1px;
}

/* Products Section */
.products-section {
	padding: 80px 0;
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
	color: #5d4037;
}

/* Toolbar */
.products-toolbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40px;
	padding: 20px;
	background: rgba(255, 245, 230, 0.5);
	border-radius: 12px;
	border: 1px solid rgba(255, 215, 0, 0.2);
}

.toolbar-left,
.toolbar-right {
	display: flex;
	align-items: center;
	gap: 15px;
}

.result-count {
	color: #8b4513;
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
	color: #8b4513;
	margin-bottom: 15px;
}

.no-products-found p {
	font-size: 1.1rem;
	color: #5d4037;
	margin-bottom: 30px;
}

.btn-back-shop {
	display: inline-block;
	background: #8b4513;
	color: #fff;
	padding: 15px 40px;
	border-radius: 30px;
	text-decoration: none;
	font-weight: 600;
	transition: all 0.3s ease;
}

.btn-back-shop:hover {
	background: #a0522d;
	transform: translateY(-2px);
	box-shadow: 0 8px 20px rgba(139, 69, 19, 0.3);
}

/* Bottom CTA */
.bottom-cta {
	background: linear-gradient(135deg, #fff5e6 0%, #ffd9a6 100%);
	border-radius: 20px;
	padding: 60px 40px;
	text-align: center;
	margin-top: 80px;
	border: 3px solid rgba(255, 215, 0, 0.3);
	box-shadow: 0 10px 40px rgba(139, 69, 19, 0.1);
}

.cta-title {
	font-family: 'Cinzel', serif;
	font-size: 2.5rem;
	color: #8b4513;
	margin: 0 0 15px 0;
}

.cta-description {
	font-size: 1.2rem;
	color: #5d4037;
	margin: 0 0 35px 0;
	max-width: 600px;
	margin-left: auto;
	margin-right: auto;
}

.btn-cta-3d {
	display: inline-flex;
	align-items: center;
	gap: 12px;
	background: linear-gradient(135deg, #8b4513 0%, #a0522d 100%);
	color: #fff;
	padding: 20px 50px;
	border-radius: 50px;
	font-family: 'Cinzel', serif;
	font-size: 1.2rem;
	font-weight: 700;
	text-decoration: none;
	box-shadow: 0 10px 30px rgba(139, 69, 19, 0.3);
	transition: all 0.3s ease;
}

.btn-cta-3d:hover {
	transform: translateY(-3px);
	box-shadow: 0 15px 40px rgba(139, 69, 19, 0.4);
	background: linear-gradient(135deg, #a0522d 0%, #8b4513 100%);
}

/* Responsive Design */
@media (max-width: 768px) {
	.hero-title {
		font-size: 2.5rem;
	}

	.title-icon {
		font-size: 2rem;
		display: block;
		margin: 0 0 15px 0;
	}

	.hero-subtitle {
		font-size: 1.1rem;
	}

	.hero-description {
		font-size: 1rem;
	}

	.hero-actions {
		flex-direction: column;
	}

	.btn-explore-3d,
	.btn-scroll-products {
		width: 100%;
		justify-content: center;
	}

	.collection-stats {
		gap: 25px;
	}

	.stat-value {
		font-size: 1.5rem;
	}

	.products-grid {
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 20px;
	}

	.products-toolbar {
		flex-direction: column;
		gap: 15px;
		align-items: stretch;
	}

	.toolbar-left,
	.toolbar-right {
		justify-content: center;
	}

	.bottom-cta {
		padding: 40px 20px;
	}

	.cta-title {
		font-size: 1.8rem;
	}

	.cta-description {
		font-size: 1rem;
	}
}

/* Print Styles */
@media print {
	.collection-hero,
	.bottom-cta,
	.products-toolbar {
		display: none;
	}
}
</style>

<?php
get_footer( 'shop' );
