<?php
/**
 * Template Name: Signature Collection
 *
 * Showcase template for SkyyRose Signature Collection featuring
 * rose gold and gold luxury jewelry pieces.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-page collection-signature">

	<!-- Collection Hero -->
	<section class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<span class="collection-badge">Signature Collection</span>
			<h1 class="hero-title">Timeless Elegance</h1>
			<p class="hero-subtitle">Where rose gold meets classic sophistication. Our flagship collection combines heritage craftsmanship with modern luxury.</p>
			<div class="hero-actions">
				<a href="#products" class="btn btn-primary">Shop Collection</a>
				<a href="#story" class="btn btn-outline">Collection Story</a>
			</div>
		</div>
		<div class="hero-background">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/signature-hero.jpg' ); ?>" alt="Signature Collection Hero">
		</div>
	</section>

	<!-- Collection Highlights -->
	<section class="section collection-highlights">
		<div class="container">
			<div class="highlights-grid">
				<div class="highlight-card">
					<div class="highlight-icon">✨</div>
					<h3>Rose Gold Excellence</h3>
					<p>Premium 18k rose gold with signature warm luster</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">💎</div>
					<h3>Certified Diamonds</h3>
					<p>GIA certified diamonds with exceptional clarity</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">🎨</div>
					<h3>Artisan Crafted</h3>
					<p>Handcrafted by master jewelers in Oakland</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">♾️</div>
					<h3>Lifetime Warranty</h3>
					<p>Guaranteed quality for generations</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Product Showcase -->
	<section id="products" class="section products-showcase">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">Featured Pieces</span>
				<h2 class="section-title">Signature Collection</h2>
			</div>

			<?php
			// Query WooCommerce products if available
			if ( class_exists( 'WooCommerce' ) ) :
				$args = array(
					'post_type'      => 'product',
					'posts_per_page' => 12,
					'tax_query'      => array(
						array(
							'taxonomy' => 'product_cat',
							'field'    => 'slug',
							'terms'    => 'signature-collection',
						),
					),
				);
				$products = new WP_Query( $args );

				if ( $products->have_posts() ) :
			?>
				<div class="products-grid">
					<?php while ( $products->have_posts() ) : $products->the_post(); ?>
						<?php wc_get_template_part( 'content', 'product' ); ?>
					<?php endwhile; ?>
				</div>
			<?php
				wp_reset_postdata();
				else :
			?>
				<!-- Placeholder Product Grid -->
				<div class="products-grid">
					<?php for ( $i = 1; $i <= 6; $i++ ) : ?>
						<article class="product-card">
							<div class="product-image">
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Signature Product <?php echo $i; ?>">
								<span class="product-badge">New</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Rose Gold Signature Ring <?php echo $i; ?></h3>
								<p class="product-price">$1,299</p>
								<a href="/shop" class="btn btn-secondary">View Details</a>
							</div>
						</article>
					<?php endfor; ?>
				</div>
			<?php
				endif;
			else :
				// No WooCommerce - show static grid
			?>
				<div class="products-grid">
					<?php for ( $i = 1; $i <= 6; $i++ ) : ?>
						<article class="product-card">
							<div class="product-image">
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Signature Product <?php echo $i; ?>">
								<span class="product-badge">New</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Rose Gold Signature Piece <?php echo $i; ?></h3>
								<p class="product-price">$1,299</p>
								<a href="/shop" class="btn btn-secondary">View Details</a>
							</div>
						</article>
					<?php endfor; ?>
				</div>
			<?php endif; ?>

			<div class="text-center" style="margin-top: var(--space-3xl);">
				<a href="/shop?collection=signature" class="btn btn-primary btn-large">View All Signature Pieces</a>
			</div>
		</div>
	</section>

	<!-- Collection Story -->
	<section id="story" class="section collection-story bg-rose-gold-light">
		<div class="container">
			<div class="story-grid">
				<div class="story-content">
					<span class="section-subtitle">The Signature Story</span>
					<h2 class="section-title">Heritage Meets Modernity</h2>
					<p>The Signature Collection represents the pinnacle of SkyyRose craftsmanship. Each piece is meticulously designed to celebrate life's most precious moments.</p>
					<p>Featuring our signature rose gold blend, these pieces capture the warmth of love and the brilliance of commitment. From engagement rings to anniversary gifts, the Signature Collection embodies timeless elegance.</p>
					<div class="story-stats">
						<div class="stat">
							<span class="stat-number">18k</span>
							<span class="stat-label">Rose Gold</span>
						</div>
						<div class="stat">
							<span class="stat-number">GIA</span>
							<span class="stat-label">Certified</span>
						</div>
						<div class="stat">
							<span class="stat-number">∞</span>
							<span class="stat-label">Warranty</span>
						</div>
					</div>
				</div>
				<div class="story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/signature-crafting.jpg' ); ?>" alt="Signature Collection Crafting">
				</div>
			</div>
		</div>
	</section>

	<!-- 3D Experience (if available) -->
	<section class="section three-d-experience">
		<div class="container text-center">
			<div class="section-header">
				<span class="section-subtitle text-rose-gold">Immersive Experience</span>
				<h2 class="section-title">Explore in 3D</h2>
				<p>Rotate, zoom, and examine our jewelry in stunning detail</p>
			</div>
			<div id="signature-3d-viewer" class="three-d-viewer" data-model="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/models/signature-collection.glb' ); ?>">
				<!-- 3D viewer will be initialized by theme JS -->
				<div class="viewer-placeholder">
					<p>Loading 3D experience...</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Materials & Care -->
	<section class="section materials-care">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Materials & Care</h2>
			</div>
			<div class="materials-grid">
				<div class="material-card">
					<h3>18k Rose Gold</h3>
					<p>Our signature metal blend combines 75% pure gold with copper alloys, creating the distinctive warm pink hue that defines the Signature Collection.</p>
				</div>
				<div class="material-card">
					<h3>GIA Certified Diamonds</h3>
					<p>Every diamond is hand-selected and certified by the Gemological Institute of America, ensuring exceptional quality and ethical sourcing.</p>
				</div>
				<div class="material-card">
					<h3>Care Instructions</h3>
					<p>Clean with warm water and mild soap. Store separately in soft pouches. Avoid harsh chemicals and remove during exercise or water activities.</p>
				</div>
				<div class="material-card">
					<h3>Lifetime Service</h3>
					<p>Complimentary cleaning, inspection, and minor repairs for life. Professional restoration services available for all Signature pieces.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="section cta-section gradient-rose-gold">
		<div class="container text-center">
			<h2 class="section-title">Find Your Perfect Signature Piece</h2>
			<p class="section-subtitle">Schedule a private consultation with our jewelry experts</p>
			<div class="cta-actions">
				<a href="/shop?collection=signature" class="btn btn-primary btn-large">Shop Signature</a>
				<a href="/contact" class="btn btn-outline btn-large">Book Consultation</a>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Signature Collection Specific Styles */
.collection-signature .collection-hero {
	position: relative;
	min-height: 80vh;
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	color: var(--white);
	overflow: hidden;
}

.collection-hero .hero-background {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	z-index: 1;
}

.collection-hero .hero-background img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	object-position: center;
}

.collection-hero .hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, rgba(183, 110, 121, 0.85) 0%, rgba(212, 175, 55, 0.75) 100%);
	z-index: 2;
}

.collection-hero .hero-content {
	position: relative;
	z-index: 3;
	max-width: 800px;
	padding: var(--space-xl);
}

.collection-hero .collection-badge {
	display: inline-block;
	padding: var(--space-sm) var(--space-lg);
	font-size: var(--text-sm);
	font-weight: var(--weight-semibold);
	text-transform: uppercase;
	letter-spacing: 0.1em;
	background: rgba(255, 255, 255, 0.2);
	border: 1px solid rgba(255, 255, 255, 0.3);
	border-radius: var(--radius-full);
	margin-bottom: var(--space-lg);
	backdrop-filter: blur(10px);
}

.collection-hero .hero-title {
	font-size: var(--text-5xl);
	margin-bottom: var(--space-md);
	animation: fadeIn var(--transition-luxury) ease-out;
}

.collection-hero .hero-subtitle {
	font-size: var(--text-xl);
	font-family: var(--font-accent);
	margin-bottom: var(--space-2xl);
	opacity: 0.95;
	line-height: 1.6;
}

.hero-actions {
	display: flex;
	gap: var(--space-md);
	justify-content: center;
	flex-wrap: wrap;
}

.collection-highlights {
	padding: var(--space-4xl) 0;
	background: var(--white);
}

.highlights-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
}

.highlight-card {
	text-align: center;
	padding: var(--space-xl);
	background: var(--off-white);
	border-radius: var(--radius-lg);
	transition: all var(--transition-luxury);
}

.highlight-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl);
}

.highlight-icon {
	font-size: 3rem;
	margin-bottom: var(--space-md);
}

.highlight-card h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-sm);
}

.products-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.product-card {
	background: var(--white);
	border-radius: var(--radius-lg);
	overflow: hidden;
	transition: all var(--transition-luxury);
	box-shadow: var(--shadow-md);
}

.product-card:hover {
	transform: translateY(-12px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.product-image {
	position: relative;
	width: 100%;
	height: 350px;
	overflow: hidden;
	background: var(--off-white);
}

.product-image img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform var(--transition-luxury);
}

.product-card:hover .product-image img {
	transform: scale(1.1);
}

.product-badge {
	position: absolute;
	top: var(--space-md);
	right: var(--space-md);
	padding: var(--space-xs) var(--space-md);
	background: var(--gradient-rose-gold);
	color: var(--white);
	font-size: var(--text-xs);
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	letter-spacing: 0.05em;
	border-radius: var(--radius-full);
}

.product-content {
	padding: var(--space-xl);
}

.product-title {
	font-size: var(--text-lg);
	color: var(--dark-gray);
	margin-bottom: var(--space-sm);
}

.product-price {
	font-size: var(--text-2xl);
	color: var(--rose-gold);
	font-weight: var(--weight-bold);
	margin-bottom: var(--space-md);
}

.story-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
	gap: var(--space-4xl);
	align-items: center;
}

.story-stats {
	display: flex;
	gap: var(--space-3xl);
	margin-top: var(--space-2xl);
}

.stat {
	text-align: center;
}

.stat-number {
	display: block;
	font-size: var(--text-4xl);
	font-weight: var(--weight-bold);
	color: var(--rose-gold);
	font-family: var(--font-heading);
}

.stat-label {
	display: block;
	font-size: var(--text-sm);
	text-transform: uppercase;
	letter-spacing: 0.05em;
	color: var(--medium-gray);
	margin-top: var(--space-xs);
}

.three-d-viewer {
	width: 100%;
	height: 600px;
	background: var(--off-white);
	border-radius: var(--radius-lg);
	margin-top: var(--space-2xl);
	box-shadow: var(--shadow-xl);
}

.viewer-placeholder {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100%;
	color: var(--medium-gray);
}

.materials-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.material-card {
	padding: var(--space-2xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-md);
	border-left: 4px solid var(--rose-gold);
}

.material-card h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
}

.bg-rose-gold-light {
	background: linear-gradient(135deg, rgba(183, 110, 121, 0.05) 0%, rgba(212, 175, 55, 0.03) 100%);
}

.cta-actions {
	display: flex;
	gap: var(--space-lg);
	justify-content: center;
	flex-wrap: wrap;
	margin-top: var(--space-xl);
}

@media (max-width: 768px) {
	.collection-hero .hero-title {
		font-size: var(--text-3xl);
	}

	.products-grid {
		grid-template-columns: 1fr;
	}

	.story-grid {
		grid-template-columns: 1fr;
	}

	.story-stats {
		justify-content: space-around;
	}

	.three-d-viewer {
		height: 400px;
	}
}
</style>

<?php
get_footer();
