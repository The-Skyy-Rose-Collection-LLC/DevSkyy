<?php
/**
 * Template Name: Black Rose Collection
 *
 * Mysterious and elegant. Silver and black pieces that make
 * a powerful statement of refined luxury.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-page collection-black-rose">

	<!-- Collection Hero -->
	<section class="collection-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<span class="collection-badge">Black Rose Collection</span>
			<h1 class="hero-title">Dark Elegance</h1>
			<p class="hero-subtitle">Where mystery meets sophistication. Sterling silver and onyx unite in timeless luxury.</p>
			<div class="hero-actions">
				<a href="#products" class="btn btn-primary">Explore Collection</a>
				<a href="#story" class="btn btn-outline">Discover More</a>
			</div>
		</div>
		<div class="hero-background">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/black-rose-hero.jpg' ); ?>" alt="Black Rose Collection Hero">
		</div>
		<div class="hero-smoke"></div>
	</section>

	<!-- Collection Highlights -->
	<section class="section collection-highlights">
		<div class="container">
			<div class="highlights-grid">
				<div class="highlight-card">
					<div class="highlight-icon">🌙</div>
					<h3>Sterling Silver</h3>
					<p>Premium .925 sterling silver with moonlit brilliance</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">⚫</div>
					<h3>Onyx & Obsidian</h3>
					<p>Deep black gemstones with captivating depth</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">🖤</div>
					<h3>Gothic Luxury</h3>
					<p>Dramatic designs with timeless sophistication</p>
				</div>
				<div class="highlight-card">
					<div class="highlight-icon">✨</div>
					<h3>Statement Elegance</h3>
					<p>Pieces that command attention with quiet power</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Product Showcase -->
	<section id="products" class="section products-showcase">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-silver">Featured Pieces</span>
				<h2 class="section-title">Black Rose Collection</h2>
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
							'terms'    => 'black-rose-collection',
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
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Black Rose Product <?php echo $i; ?>">
								<span class="product-badge">Exclusive</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Midnight Silver <?php echo $i; ?></h3>
								<p class="product-price">$1,599</p>
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
								<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Black Rose Product <?php echo $i; ?>">
								<span class="product-badge">Exclusive</span>
							</div>
							<div class="product-content">
								<h3 class="product-title">Midnight Silver Piece <?php echo $i; ?></h3>
								<p class="product-price">$1,599</p>
								<a href="/shop" class="btn btn-secondary">View Details</a>
							</div>
						</article>
					<?php endfor; ?>
				</div>
			<?php endif; ?>

			<div class="text-center" style="margin-top: var(--space-3xl);">
				<a href="/shop?collection=black-rose" class="btn btn-primary btn-large">View All Black Rose Pieces</a>
			</div>
		</div>
	</section>

	<!-- Collection Story -->
	<section id="story" class="section collection-story bg-dark">
		<div class="container">
			<div class="story-grid">
				<div class="story-content">
					<span class="section-subtitle text-silver">The Black Rose Legend</span>
					<h2 class="section-title">Embracing the Shadows</h2>
					<p>Born from the allure of darkness and elegance, the Black Rose Collection celebrates the beauty found in mystery and sophistication.</p>
					<p>Each piece combines sterling silver's moonlit gleam with the deep, captivating darkness of onyx and obsidian. These aren't just accessories—they're expressions of refined power and timeless grace.</p>
					<div class="story-features">
						<div class="feature">
							<h4>.925 Sterling Silver</h4>
							<p>Premium quality with lasting brilliance</p>
						</div>
						<div class="feature">
							<h4>Natural Onyx</h4>
							<p>Hand-selected black gemstones</p>
						</div>
						<div class="feature">
							<h4>Gothic Romance</h4>
							<p>Timeless designs with modern edge</p>
						</div>
					</div>
				</div>
				<div class="story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/black-rose-crafting.jpg' ); ?>" alt="Black Rose Collection Crafting">
				</div>
			</div>
		</div>
	</section>

	<!-- 3D Experience -->
	<section class="section three-d-experience">
		<div class="container text-center">
			<div class="section-header">
				<span class="section-subtitle text-silver">Immersive Experience</span>
				<h2 class="section-title">Explore in 3D</h2>
				<p>Discover the intricate details of Black Rose in stunning 3D</p>
			</div>
			<div id="black-rose-3d-viewer" class="three-d-viewer" data-model="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/models/black-rose-collection.glb' ); ?>">
				<div class="viewer-placeholder">
					<p>Loading 3D experience...</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Craftsmanship -->
	<section class="section craftsmanship">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Artisan Craftsmanship</h2>
			</div>
			<div class="craft-grid">
				<div class="craft-card">
					<h3>Sterling Silver Excellence</h3>
					<p>Each piece begins with premium .925 sterling silver, hand-polished to achieve our signature moonlit finish. The metal is carefully shaped to complement the dark gemstones.</p>
				</div>
				<div class="craft-card">
					<h3>Gemstone Selection</h3>
					<p>We source only the finest natural onyx and obsidian, selecting stones with perfect depth and opacity. Each gem is inspected for quality and consistency.</p>
				</div>
				<div class="craft-card">
					<h3>Gothic Architecture</h3>
					<p>Inspired by gothic cathedrals and Art Deco design, our pieces feature intricate details—filigree work, geometric patterns, and architectural elements.</p>
				</div>
				<div class="craft-card">
					<h3>Oxidized Detailing</h3>
					<p>Strategic oxidation techniques create dramatic contrast, highlighting details and adding depth to the silver while enhancing the mysterious aesthetic.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="section cta-section gradient-black-silver">
		<div class="container text-center">
			<h2 class="section-title">Embrace Dark Elegance</h2>
			<p class="section-subtitle">Discover pieces as mysterious as the night</p>
			<div class="cta-actions">
				<a href="/shop?collection=black-rose" class="btn btn-primary btn-large">Shop Black Rose</a>
				<a href="/contact" class="btn btn-outline btn-large">Private Viewing</a>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Black Rose Collection Specific Styles */
.collection-black-rose .collection-hero {
	position: relative;
	min-height: 90vh;
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
	filter: brightness(0.4);
}

.collection-hero .hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, rgba(20, 20, 20, 0.9) 0%, rgba(192, 192, 192, 0.3) 100%);
	z-index: 2;
}

.collection-hero .hero-smoke {
	position: absolute;
	bottom: 0;
	left: 0;
	width: 100%;
	height: 300px;
	background: linear-gradient(to top, rgba(20, 20, 20, 0.8), transparent);
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
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	letter-spacing: 0.15em;
	background: rgba(20, 20, 20, 0.7);
	border: 2px solid var(--silver);
	border-radius: var(--radius-full);
	margin-bottom: var(--space-lg);
	backdrop-filter: blur(10px);
}

.collection-hero .hero-title {
	font-size: var(--text-6xl);
	margin-bottom: var(--space-md);
	text-shadow: 0 4px 30px rgba(0, 0, 0, 0.7);
	animation: fadeIn var(--transition-luxury) ease-out;
	letter-spacing: 0.05em;
}

.collection-hero .hero-subtitle {
	font-size: var(--text-xl);
	font-family: var(--font-accent);
	margin-bottom: var(--space-2xl);
	opacity: 0.9;
	line-height: 1.6;
	color: var(--silver);
}

.hero-actions {
	display: flex;
	gap: var(--space-md);
	justify-content: center;
	flex-wrap: wrap;
}

.collection-highlights {
	padding: var(--space-4xl) 0;
	background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
	color: var(--white);
}

.highlights-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
}

.highlight-card {
	text-align: center;
	padding: var(--space-xl);
	background: rgba(255, 255, 255, 0.03);
	border-radius: var(--radius-lg);
	border: 1px solid rgba(192, 192, 192, 0.2);
	transition: all var(--transition-luxury);
}

.highlight-card:hover {
	transform: translateY(-8px);
	background: rgba(255, 255, 255, 0.05);
	border-color: var(--silver);
	box-shadow: 0 10px 40px rgba(192, 192, 192, 0.1);
}

.highlight-icon {
	font-size: 3rem;
	margin-bottom: var(--space-md);
}

.highlight-card h3 {
	color: var(--silver);
	margin-bottom: var(--space-sm);
}

.highlight-card p {
	color: rgba(255, 255, 255, 0.7);
}

.products-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.product-card {
	background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
	border-radius: var(--radius-lg);
	overflow: hidden;
	transition: all var(--transition-luxury);
	box-shadow: var(--shadow-md);
	border: 1px solid rgba(192, 192, 192, 0.1);
}

.product-card:hover {
	transform: translateY(-12px);
	box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 40px rgba(192, 192, 192, 0.1);
	border-color: var(--silver);
}

.product-image {
	position: relative;
	width: 100%;
	height: 350px;
	overflow: hidden;
	background: linear-gradient(135deg, #0a0a0a 0%, #2a2a2a 100%);
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
	background: linear-gradient(135deg, #0a0a0a 0%, var(--silver) 100%);
	color: var(--white);
	font-size: var(--text-xs);
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	letter-spacing: 0.1em;
	border-radius: var(--radius-full);
	border: 1px solid var(--silver);
}

.product-content {
	padding: var(--space-xl);
	color: var(--white);
}

.product-title {
	font-size: var(--text-lg);
	color: var(--silver);
	margin-bottom: var(--space-sm);
}

.product-price {
	font-size: var(--text-2xl);
	color: var(--white);
	font-weight: var(--weight-bold);
	margin-bottom: var(--space-md);
}

.text-silver {
	color: var(--silver);
}

.bg-dark {
	background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
	color: var(--white);
}

.story-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
	gap: var(--space-4xl);
	align-items: center;
}

.story-content .section-title {
	color: var(--white);
}

.story-content p {
	color: rgba(255, 255, 255, 0.8);
}

.story-features {
	margin-top: var(--space-2xl);
	display: grid;
	gap: var(--space-lg);
}

.story-features .feature {
	padding: var(--space-lg);
	background: rgba(255, 255, 255, 0.03);
	border-left: 4px solid var(--silver);
	border-radius: var(--radius-md);
}

.story-features h4 {
	color: var(--silver);
	margin-bottom: var(--space-xs);
}

.story-features p {
	color: rgba(255, 255, 255, 0.7);
	font-size: var(--text-sm);
}

.three-d-viewer {
	width: 100%;
	height: 600px;
	background: linear-gradient(135deg, #0a0a0a 0%, #2a2a2a 100%);
	border-radius: var(--radius-lg);
	margin-top: var(--space-2xl);
	box-shadow: var(--shadow-xl);
	border: 2px solid rgba(192, 192, 192, 0.2);
}

.viewer-placeholder {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100%;
	color: var(--silver);
}

.craft-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.craft-card {
	padding: var(--space-2xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-md);
	border-top: 4px solid #0a0a0a;
	transition: all var(--transition-luxury);
}

.craft-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl);
}

.craft-card h3 {
	color: #0a0a0a;
	margin-bottom: var(--space-md);
}

.gradient-black-silver {
	background: linear-gradient(135deg, #0a0a0a 0%, var(--silver) 100%);
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
		font-size: var(--text-4xl);
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
