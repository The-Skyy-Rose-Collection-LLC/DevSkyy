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
			<h1 class="hero-title fade-in">Where Love Meets Luxury</h1>
			<p class="hero-subtitle fade-in">Exquisite jewelry crafted with passion, designed to last forever</p>
			<div class="hero-actions fade-in">
				<a href="/shop" class="btn btn-primary">Explore Collections</a>
				<a href="/about" class="btn btn-outline">Our Story</a>
			</div>
		</div>
	</section>

	<!-- Featured Collections -->
	<section class="section collections-showcase">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">Discover Our Collections</span>
				<h2 class="section-title">Luxury Jewelry Collections</h2>
			</div>

			<div class="collections-grid">
				<!-- Signature Collection -->
				<article class="collection-card collection-signature">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Signature Collection">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Signature</span>
						<h3 class="collection-title">Signature Collection</h3>
						<p class="collection-description">Timeless elegance in rose gold, gold, and silver. Our flagship collection combines classic design with modern sophistication.</p>
						<a href="/collection/signature" class="btn btn-secondary">View Collection</a>
					</div>
				</article>

				<!-- Love Hurts Collection -->
				<article class="collection-card collection-love-hurts">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Love Hurts Collection">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Love Hurts</span>
						<h3 class="collection-title">Love Hurts Collection</h3>
						<p class="collection-description">Passionate designs featuring deep crimson and rose gold. Bold pieces for those who wear their heart on their sleeve.</p>
						<a href="/collection/love-hurts" class="btn btn-secondary">View Collection</a>
					</div>
				</article>

				<!-- Black Rose Collection -->
				<article class="collection-card collection-black-rose">
					<div class="collection-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="Black Rose Collection">
					</div>
					<div class="collection-content">
						<span class="collection-badge">Black Rose</span>
						<h3 class="collection-title">Black Rose Collection</h3>
						<p class="collection-description">Mysterious and elegant. Silver and black pieces that make a powerful statement of refined luxury.</p>
						<a href="/collection/black-rose" class="btn btn-secondary">View Collection</a>
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
					<span class="section-subtitle">The SkyyRose Story</span>
					<h2 class="section-title">Crafted with Passion</h2>
					<p>Since our founding, SkyyRose has been dedicated to creating jewelry that tells a story. Each piece is meticulously crafted to celebrate life's most precious moments.</p>
					<p>Our collections blend timeless elegance with contemporary design, using only the finest materials to create pieces that will be treasured for generations.</p>
					<a href="/about" class="btn btn-outline">Learn More</a>
				</div>
				<div class="about-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="SkyyRose Jewelry Crafting">
				</div>
			</div>
		</div>
	</section>

	<!-- Why Choose Us -->
	<section class="section features-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Why Choose SkyyRose</h2>
			</div>

			<div class="features-grid">
				<div class="feature-card card">
					<div class="feature-icon">✨</div>
					<h3 class="card-title">Premium Quality</h3>
					<p class="card-description">Only the finest materials - rose gold, gold, and sterling silver.</p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon">🎨</div>
					<h3 class="card-title">Unique Designs</h3>
					<p class="card-description">Each piece is thoughtfully designed to be one-of-a-kind.</p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon">💎</div>
					<h3 class="card-title">Lifetime Warranty</h3>
					<p class="card-description">We stand behind our craftsmanship with a lifetime guarantee.</p>
				</div>

				<div class="feature-card card">
					<div class="feature-icon">🚚</div>
					<h3 class="card-title">Free Shipping</h3>
					<p class="card-description">Complimentary shipping on all orders over $100.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="section cta-section gradient-rose-gold">
		<div class="container text-center">
			<h2 class="section-title">Ready to Find Your Perfect Piece?</h2>
			<p class="section-subtitle">Explore our full collection of luxury jewelry</p>
			<a href="/shop" class="btn btn-primary btn-large">Shop Now</a>
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
