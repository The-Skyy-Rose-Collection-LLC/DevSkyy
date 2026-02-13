<?php
/**
 * Template Name: Love Hurts Collection
 *
 * Passionate designs featuring deep crimson and rose gold.
 * Bold pieces for those who wear their heart on their sleeve.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-page collection-love-hurts">

	<!-- Collection Hero -->
	<section class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<span class="collection-badge">Love Hurts Collection</span>
			<h1 class="hero-title">Passionate Hearts</h1>
			<p class="hero-subtitle">Where love burns bright. Bold crimson designs that celebrate the intensity of true emotion.</p>
			<div class="hero-actions">
				<a href="#products" class="btn btn-primary">Shop Collection</a>
				<a href="#story" class="btn btn-outline">The Story</a>
			</div>
		</div>
		<div class="hero-background">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/love-hurts-hero.jpg' ); ?>" alt="Love Hurts Collection Hero">
		</div>
		<div class="hero-particles"></div>
	</section>

	<!-- Collection Highlights -->
	<section class="section collection-highlights">
		<div class="container">
			<div class="highlights-grid">
				<div class="highlight-card">
					<div class="highlight-icon">❤️</div>
					<h3>Crimson Fire</h3>
					<p>Deep red gemstones set in rose gold for dramatic impact</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">💘</div>
					<h3>Romantic Edge</h3>
					<p>Bold designs that merge romance with modern attitude</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">🔥</div>
					<h3>Handcrafted Passion</h3>
					<p>Each piece tells a story of intense craftsmanship</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">💍</div>
					<h3>Statement Pieces</h3>
					<p>Designed to be noticed, worn with confidence</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Product Showcase -->
	<section id="products" class="section products-showcase">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-crimson">Featured Pieces</span>
				<h2 class="section-title">Love Hurts Collection</h2>
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
							'terms'    => 'love-hurts-collection',
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
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Love Hurts Product <?php echo $i; ?>">
								<span class="product-badge">Intense</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Crimson Heart <?php echo $i; ?></h3>
								<p class="product-price">$1,499</p>
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
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Love Hurts Product <?php echo $i; ?>">
								<span class="product-badge">Intense</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Crimson Heart Piece <?php echo $i; ?></h3>
								<p class="product-price">$1,499</p>
								<a href="/shop" class="btn btn-secondary">View Details</a>
							</div>
						</article>
					<?php endfor; ?>
				</div>
			<?php endif; ?>

			<div class="text-center" style="margin-top: var(--space-3xl);">
				<a href="/shop?collection=love-hurts" class="btn btn-primary btn-large">View All Love Hurts Pieces</a>
			</div>
		</div>
	</section>

	<!-- Collection Story -->
	<section id="story" class="section collection-story bg-crimson-light">
		<div class="container">
			<div class="story-grid">
				<div class="story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/love-hurts-crafting.jpg' ); ?>" alt="Love Hurts Collection Crafting">
				</div>
				<div class="story-content">
					<span class="section-subtitle">Born from Passion</span>
					<h2 class="section-title">Love That Leaves a Mark</h2>
					<p>The Love Hurts Collection celebrates the raw, unfiltered intensity of true love. Inspired by those who love fiercely and without reservation.</p>
					<p>Each piece features bold crimson gemstones set in our signature rose gold, creating dramatic contrasts that mirror the highs and lows of passionate relationships. These aren't delicate pieces—they're statements of emotional courage.</p>
					<blockquote class="love-hurts-quote">
						"Love is meant to be felt, not hidden. Wear your heart boldly."
					</blockquote>
				</div>
			</div>
		</div>
	</section>

	<!-- 3D Experience -->
	<section class="section three-d-experience">
		<div class="container text-center">
			<div class="section-header">
				<span class="section-subtitle text-crimson">Immersive Experience</span>
				<h2 class="section-title">Explore in 3D</h2>
				<p>Experience the dramatic beauty of Love Hurts in stunning 3D detail</p>
			</div>
			<div id="love-hurts-3d-viewer" class="three-d-viewer" data-model="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/models/love-hurts-collection.glb' ); ?>">
				<div class="viewer-placeholder">
					<p>Loading 3D experience...</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Design Philosophy -->
	<section class="section design-philosophy">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Design Philosophy</h2>
			</div>
			<div class="philosophy-grid">
				<div class="philosophy-card">
					<h3>Emotional Intensity</h3>
					<p>Deep crimson gemstones evoke passion, desire, and the courage to love fully. Each stone is hand-selected for its rich color saturation.</p>
				</div>
				<div class="philosophy-card">
					<h3>Dramatic Contrast</h3>
					<p>The marriage of crimson and rose gold creates visual drama—warm metals against cool reds, softness meeting strength.</p>
				</div>
				<div class="philosophy-card">
					<h3>Bold Silhouettes</h3>
					<p>Larger stone settings, architectural designs, and statement pieces that demand attention and won't be overlooked.</p>
				</div>
				<div class="philosophy-card">
					<h3>Romantic Rebellion</h3>
					<p>Traditional romantic symbolism reimagined with edge—hearts with thorns, roses with attitude, love that bites back.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="section cta-section gradient-crimson">
		<div class="container text-center">
			<h2 class="section-title">Wear Your Heart Boldly</h2>
			<p class="section-subtitle">Discover pieces as passionate as your love story</p>
			<div class="cta-actions">
				<a href="/shop?collection=love-hurts" class="btn btn-primary btn-large">Shop Love Hurts</a>
				<a href="/contact" class="btn btn-outline btn-large">Custom Consultation</a>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Love Hurts Collection Specific Styles */
.collection-love-hurts .collection-hero {
	position: relative;
	min-height: 85vh;
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
	background: linear-gradient(135deg, rgba(220, 20, 60, 0.9) 0%, rgba(183, 110, 121, 0.85) 100%);
	z-index: 2;
}

.collection-hero .hero-particles {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	z-index: 2;
	background-image: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
	background-size: 50px 50px;
	animation: particleFloat 20s linear infinite;
}

@keyframes particleFloat {
	0% { background-position: 0 0; }
	100% { background-position: 50px 50px; }
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
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	letter-spacing: 0.1em;
	background: rgba(220, 20, 60, 0.3);
	border: 2px solid rgba(255, 255, 255, 0.5);
	border-radius: var(--radius-full);
	margin-bottom: var(--space-lg);
	backdrop-filter: blur(10px);
}

.collection-hero .hero-title {
	font-size: var(--text-5xl);
	margin-bottom: var(--space-md);
	text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
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
	background: linear-gradient(135deg, rgba(220, 20, 60, 0.03) 0%, rgba(183, 110, 121, 0.05) 100%);
	border-radius: var(--radius-lg);
	border: 1px solid rgba(220, 20, 60, 0.1);
	transition: all var(--transition-luxury);
}

.highlight-card:hover {
	transform: translateY(-8px);
	box-shadow: 0 10px 30px rgba(220, 20, 60, 0.15);
	border-color: var(--crimson);
}

.highlight-icon {
	font-size: 3rem;
	margin-bottom: var(--space-md);
}

.highlight-card h3 {
	color: var(--crimson);
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
	box-shadow: var(--shadow-xl), 0 0 30px rgba(220, 20, 60, 0.2);
}

.product-image {
	position: relative;
	width: 100%;
	height: 350px;
	overflow: hidden;
	background: linear-gradient(135deg, rgba(220, 20, 60, 0.05) 0%, rgba(183, 110, 121, 0.03) 100%);
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
	background: linear-gradient(135deg, var(--crimson) 0%, var(--rose-gold) 100%);
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
	color: var(--crimson);
	font-weight: var(--weight-bold);
	margin-bottom: var(--space-md);
}

.text-crimson {
	color: var(--crimson);
}

.bg-crimson-light {
	background: linear-gradient(135deg, rgba(220, 20, 60, 0.05) 0%, rgba(183, 110, 121, 0.08) 100%);
}

.story-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
	gap: var(--space-4xl);
	align-items: center;
}

.love-hurts-quote {
	margin-top: var(--space-2xl);
	padding: var(--space-xl);
	border-left: 4px solid var(--crimson);
	background: rgba(220, 20, 60, 0.05);
	font-size: var(--text-xl);
	font-style: italic;
	color: var(--crimson);
	font-family: var(--font-heading);
}

.three-d-viewer {
	width: 100%;
	height: 600px;
	background: linear-gradient(135deg, rgba(220, 20, 60, 0.03) 0%, rgba(183, 110, 121, 0.05) 100%);
	border-radius: var(--radius-lg);
	margin-top: var(--space-2xl);
	box-shadow: var(--shadow-xl);
	border: 2px solid rgba(220, 20, 60, 0.1);
}

.viewer-placeholder {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100%;
	color: var(--medium-gray);
}

.philosophy-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.philosophy-card {
	padding: var(--space-2xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-md);
	border-top: 4px solid var(--crimson);
	transition: all var(--transition-luxury);
}

.philosophy-card:hover {
	transform: translateY(-8px);
	box-shadow: 0 10px 30px rgba(220, 20, 60, 0.15);
}

.philosophy-card h3 {
	color: var(--crimson);
	margin-bottom: var(--space-md);
}

.gradient-crimson {
	background: linear-gradient(135deg, var(--crimson) 0%, var(--rose-gold) 100%);
}

.cta-section {
	padding: var(--space-4xl) var(--space-xl);
	color: var(--white);
}

.cta-section .section-title,
.cta-section .section-subtitle {
	color: var(--white);
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

	.three-d-viewer {
		height: 400px;
	}
}
</style>

<?php
get_footer();
