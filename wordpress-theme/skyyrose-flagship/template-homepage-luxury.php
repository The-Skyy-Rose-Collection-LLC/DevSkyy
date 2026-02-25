<?php
/**
 * Template Name: Luxury Homepage
 *
 * Full-featured luxury homepage with brand styling and collection showcases.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main luxury-homepage">

	<!-- Hero Section -->
	<section class="hero luxury-hero">
		<div class="hero-content">
			<h1 class="hero-title fade-in"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></h1>
			<p class="hero-subtitle fade-in">Oakland luxury streetwear crafted with passion, designed to make a statement</p>
			<div class="hero-actions fade-in">
				<a href="/collections" class="btn btn-primary">Explore Collections</a>
				<a href="/about" class="btn btn-outline">Our Story</a>
			</div>
		</div>
	</section>

	<!-- Featured Collections -->
	<section class="section collections-showcase">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">Discover Our Collections</span>
				<h2 class="section-title">Luxury Streetwear Collections</h2>
			</div>

			<div class="collections-grid">
				<!-- Signature Collection -->
				<article class="collection-card collection-signature">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="<?php esc_attr_e( 'Signature Collection', 'skyyrose-flagship' ); ?>" width="600" height="400" loading="lazy">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Signature</span>
						<h3 class="collection-title"><?php esc_html_e( 'Signature Collection', 'skyyrose-flagship' ); ?></h3>
						<p class="collection-description"><?php esc_html_e( 'West Coast prestige meets rose gold warmth. Premium hoodies, joggers, and statement pieces for the Bay Area lifestyle.', 'skyyrose-flagship' ); ?></p>
						<a href="/collection/signature" class="btn btn-secondary"><?php esc_html_e( 'View Collection', 'skyyrose-flagship' ); ?></a>
					</div>
				</article>

				<!-- Love Hurts Collection -->
				<article class="collection-card collection-love-hurts">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="<?php esc_attr_e( 'Love Hurts Collection', 'skyyrose-flagship' ); ?>" width="600" height="400" loading="lazy">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Love Hurts</span>
						<h3 class="collection-title"><?php esc_html_e( 'Love Hurts Collection', 'skyyrose-flagship' ); ?></h3>
						<p class="collection-description"><?php esc_html_e( 'Raw passion in deep crimson. Varsity jackets, bombers, and streetwear for those who wear their heart on their sleeve.', 'skyyrose-flagship' ); ?></p>
						<a href="/collection/love-hurts" class="btn btn-secondary"><?php esc_html_e( 'View Collection', 'skyyrose-flagship' ); ?></a>
					</div>
				</article>

				<!-- Black Rose Collection -->
				<article class="collection-card collection-black-rose">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="<?php esc_attr_e( 'Black Rose Collection', 'skyyrose-flagship' ); ?>" width="600" height="400" loading="lazy">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Black Rose</span>
						<h3 class="collection-title"><?php esc_html_e( 'Black Rose Collection', 'skyyrose-flagship' ); ?></h3>
						<p class="collection-description"><?php esc_html_e( 'Gothic luxury blooms in midnight. Embroidered hoodies, sherpa jackets, and fleece with defiant elegance.', 'skyyrose-flagship' ); ?></p>
						<a href="/collection/black-rose" class="btn btn-secondary"><?php esc_html_e( 'View Collection', 'skyyrose-flagship' ); ?></a>
					</div>
				</article>
			</div>
		</div>
	</section>

	<!-- About Section -->
	<section class="section about-section bg-rose-gold">
		<div class="container">
			<div class="about-grid">
				<div class="about-content">
					<span class="section-subtitle"><?php esc_html_e( 'The SkyyRose Story', 'skyyrose-flagship' ); ?></span>
					<h2 class="section-title"><?php esc_html_e( 'Crafted with Passion', 'skyyrose-flagship' ); ?></h2>
					<p><?php esc_html_e( 'Born in Oakland, SkyyRose is luxury streetwear that tells a story. Every stitch is a statement, every drop a declaration of self-expression and defiant elegance.', 'skyyrose-flagship' ); ?></p>
					<p><?php esc_html_e( 'Our collections blend gothic romance, raw emotion, and West Coast prestige into premium garments designed for those who refuse to blend in.', 'skyyrose-flagship' ); ?></p>
					<a href="/about" class="btn btn-outline"><?php esc_html_e( 'Learn More', 'skyyrose-flagship' ); ?></a>
				</div>
				<div class="about-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="<?php esc_attr_e( 'SkyyRose Luxury Streetwear', 'skyyrose-flagship' ); ?>" width="600" height="400" loading="lazy">
				</div>
			</div>
		</div>
	</section>

	<!-- Why Choose Us -->
	<section class="section features-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title"><?php esc_html_e( 'Why Choose SkyyRose', 'skyyrose-flagship' ); ?></h2>
			</div>

			<div class="features-grid">
				<div class="feature-card card">
					<div class="feature-icon" aria-hidden="true">&#10024;</div>
					<h3 class="card-title"><?php esc_html_e( 'Premium Quality', 'skyyrose-flagship' ); ?></h3>
					<p class="card-description"><?php esc_html_e( 'Heavyweight fabrics, custom embroidery, and meticulous construction.', 'skyyrose-flagship' ); ?></p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon" aria-hidden="true">&#127912;</div>
					<h3 class="card-title"><?php esc_html_e( 'Limited Editions', 'skyyrose-flagship' ); ?></h3>
					<p class="card-description"><?php esc_html_e( 'Each drop is numbered and limited. Once they are gone, they are gone.', 'skyyrose-flagship' ); ?></p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon" aria-hidden="true">&#128142;</div>
					<h3 class="card-title"><?php esc_html_e( 'Immersive Experiences', 'skyyrose-flagship' ); ?></h3>
					<p class="card-description"><?php esc_html_e( 'Explore collections through 3D immersive rooms before you buy.', 'skyyrose-flagship' ); ?></p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon" aria-hidden="true">&#128666;</div>
					<h3 class="card-title"><?php esc_html_e( 'Free Shipping', 'skyyrose-flagship' ); ?></h3>
					<p class="card-description"><?php esc_html_e( 'Complimentary shipping on all orders over $100.', 'skyyrose-flagship' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="section cta-section gradient-rose-gold">
		<div class="container text-center">
			<h2 class="section-title"><?php esc_html_e( 'Ready to Make Your Statement?', 'skyyrose-flagship' ); ?></h2>
			<p class="section-subtitle"><?php esc_html_e( 'Pre-order the latest drops before they sell out', 'skyyrose-flagship' ); ?></p>
			<a href="/pre-order" class="btn btn-primary btn-large"><?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?></a>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Additional homepage-specific styles */
.luxury-homepage .hero {
	min-height: 70vh;
	background: var(--gradient-rose-gold);
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	color: var(--white);
}

.hero-title {
	font-size: var(--text-4xl);
	margin-bottom: var(--space-lg);
	animation: fadeIn var(--transition-luxury) ease-out;
}

.hero-subtitle {
	font-size: var(--text-xl);
	font-family: var(--font-accent);
	margin-bottom: var(--space-2xl);
	opacity: 0.95;
}

.hero-actions {
	display: flex;
	gap: var(--space-md);
	justify-content: center;
	flex-wrap: wrap;
}

.collections-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.collection-card {
	background: var(--white);
	border-radius: var(--radius-lg);
	overflow: hidden;
	transition: all var(--transition-luxury);
	box-shadow: var(--shadow-md);
}

.collection-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.collection-image {
	width: 100%;
	height: 300px;
	overflow: hidden;
}

.collection-image img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform var(--transition-luxury);
}

.collection-card:hover .collection-image img {
	transform: scale(1.05);
}

.collection-content {
	padding: var(--space-xl);
}

.collection-badge {
	display: inline-block;
	padding: var(--space-xs) var(--space-md);
	font-size: var(--text-sm);
	font-weight: var(--weight-semibold);
	text-transform: uppercase;
	letter-spacing: 0.05em;
	border-radius: var(--radius-full);
	margin-bottom: var(--space-md);
}

.about-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-3xl);
	align-items: center;
}

.features-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-xl);
	margin-top: var(--space-2xl);
}

.feature-icon {
	font-size: 3rem;
	margin-bottom: var(--space-md);
}

.cta-section {
	padding: var(--space-4xl) var(--space-xl);
	color: var(--white);
}

.cta-section .section-title,
.cta-section .section-subtitle {
	color: var(--white);
}

.btn-large {
	padding: var(--space-lg) var(--space-3xl);
	font-size: var(--text-lg);
}

@media (max-width: 768px) {
	.hero-title {
		font-size: var(--text-3xl);
	}

	.collections-grid,
	.features-grid {
		grid-template-columns: 1fr;
	}

	.hero-actions {
		flex-direction: column;
	}
}
</style>

<?php
get_footer();
