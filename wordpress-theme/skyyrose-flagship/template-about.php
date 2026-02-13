<?php
/**
 * Template Name: About Us
 *
 * Complete about page showcasing SkyyRose's story, values,
 * craftsmanship, and team.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main about-page">

	<!-- Hero Section -->
	<section class="about-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<h1 class="hero-title">Where Love Meets Luxury</h1>
			<p class="hero-subtitle">The SkyyRose Story</p>
		</div>
		<div class="hero-background">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/about-hero.jpg' ); ?>" alt="SkyyRose Atelier">
		</div>
	</section>

	<!-- Our Story -->
	<section class="section our-story">
		<div class="container">
			<div class="story-grid">
				<div class="story-content">
					<span class="section-subtitle text-rose-gold">Est. 2024</span>
					<h2 class="section-title">A Journey of Passion</h2>
					<p class="lead-text">SkyyRose was born from a simple belief: that jewelry should tell a story, celebrate moments, and last for generations.</p>
					<p>Founded in Oakland, California, we began with a vision to create luxury jewelry that combines timeless elegance with modern innovation. Every piece we craft honors this vision.</p>
					<p>Our name—SkyyRose—represents the marriage of limitless possibility (Skyy) with timeless beauty (Rose). It's a philosophy that guides everything we create.</p>
				</div>
				<div class="story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/founder-story.jpg' ); ?>" alt="SkyyRose Founder">
				</div>
			</div>
		</div>
	</section>

	<!-- Values -->
	<section class="section values-section bg-rose-gold-light">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">What We Stand For</span>
				<h2 class="section-title">Our Values</h2>
			</div>

			<div class="values-grid">
				<div class="value-card">
					<div class="value-icon">✨</div>
					<h3>Exceptional Quality</h3>
					<p>We use only the finest materials—18k gold, sterling silver, and GIA certified diamonds. Every piece undergoes rigorous quality control.</p>
				</div>

				<div class="value-card">
					<div class="value-icon">🎨</div>
					<h3>Timeless Design</h3>
					<p>Our designs balance classic elegance with contemporary style, creating pieces that remain beautiful for generations.</p>
				</div>

				<div class="value-card">
					<div class="value-icon">🤝</div>
					<h3>Ethical Sourcing</h3>
					<p>We're committed to responsible sourcing. All materials are ethically sourced and conflict-free, supporting fair labor practices.</p>
				</div>

				<div class="value-card">
					<div class="value-icon">💎</div>
					<h3>Master Craftsmanship</h3>
					<p>Each piece is handcrafted by master jewelers with decades of experience. Traditional techniques meet modern precision.</p>
				</div>

				<div class="value-card">
					<div class="value-icon">🌍</div>
					<h3>Sustainability</h3>
					<p>We minimize environmental impact through responsible practices, recycled metals, and sustainable packaging.</p>
				</div>

				<div class="value-card">
					<div class="value-icon">❤️</div>
					<h3>Customer Care</h3>
					<p>Lifetime warranty, complimentary cleaning, and exceptional service. Your satisfaction is our priority.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Craftsmanship Process -->
	<section class="section process-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">The SkyyRose Process</h2>
				<p>From concept to completion, every piece is a labor of love</p>
			</div>

			<div class="process-timeline">
				<div class="process-step">
					<div class="step-number">01</div>
					<h3>Design & Concept</h3>
					<p>Our designers sketch concepts, considering aesthetics, wearability, and emotional resonance. Each design is refined through multiple iterations.</p>
				</div>

				<div class="process-step">
					<div class="step-number">02</div>
					<h3>Material Selection</h3>
					<p>We hand-select every gemstone and metal. Diamonds are GIA certified, gold is tested for purity, and every material meets our exacting standards.</p>
				</div>

				<div class="process-step">
					<div class="step-number">03</div>
					<h3>Master Crafting</h3>
					<p>Expert jewelers bring designs to life using traditional techniques and modern precision tools. Each piece is crafted individually, never mass-produced.</p>
				</div>

				<div class="process-step">
					<div class="step-number">04</div>
					<h3>Quality Inspection</h3>
					<p>Multi-point quality checks ensure perfection. We inspect stone settings, polish, proportions, and structural integrity.</p>
				</div>

				<div class="process-step">
					<div class="step-number">05</div>
					<h3>Packaging & Delivery</h3>
					<p>Pieces are beautifully packaged in our signature boxes with certificates of authenticity and care instructions.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Team Section -->
	<section class="section team-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Meet Our Artisans</h2>
			</div>

			<div class="team-grid">
				<div class="team-card">
					<div class="team-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/team-1.jpg' ); ?>" alt="Master Jeweler">
					</div>
					<h3>Elena Martinez</h3>
					<p class="team-role">Master Jeweler</p>
					<p>25 years of experience in fine jewelry, specializing in rose gold and diamond settings.</p>
				</div>

				<div class="team-card">
					<div class="team-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/team-2.jpg' ); ?>" alt="Lead Designer">
					</div>
					<h3>David Chen</h3>
					<p class="team-role">Lead Designer</p>
					<p>Award-winning designer with a passion for blending traditional and contemporary aesthetics.</p>
				</div>

				<div class="team-card">
					<div class="team-image">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/team-3.jpg' ); ?>" alt="Gemologist">
					</div>
					<h3>Sarah Johnson</h3>
					<p class="team-role">Certified Gemologist</p>
					<p>GIA certified with expertise in diamond grading and gemstone authentication.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Statistics -->
	<section class="section stats-section gradient-rose-gold">
		<div class="container">
			<div class="stats-grid">
				<div class="stat-block">
					<span class="stat-number">10,000+</span>
					<span class="stat-label">Pieces Crafted</span>
				</div>
				<div class="stat-block">
					<span class="stat-number">5,000+</span>
					<span class="stat-label">Happy Customers</span>
				</div>
				<div class="stat-block">
					<span class="stat-number">4.9/5</span>
					<span class="stat-label">Average Rating</span>
				</div>
				<div class="stat-block">
					<span class="stat-number">100%</span>
					<span class="stat-label">Ethical Sourcing</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Call to Action -->
	<section class="section about-cta">
		<div class="container text-center">
			<h2 class="section-title">Experience SkyyRose</h2>
			<p class="section-subtitle">Discover jewelry that celebrates your story</p>
			<div class="cta-actions">
				<a href="/shop" class="btn btn-primary btn-large">Explore Collections</a>
				<a href="/contact" class="btn btn-outline btn-large">Schedule a Consultation</a>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* About Page Specific Styles */
.about-page .about-hero {
	position: relative;
	height: 70vh;
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	color: var(--white);
	overflow: hidden;
}

.about-hero .hero-background {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	z-index: 1;
}

.about-hero .hero-background img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.about-hero .hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, rgba(183, 110, 121, 0.8) 0%, rgba(212, 175, 55, 0.7) 100%);
	z-index: 2;
}

.about-hero .hero-content {
	position: relative;
	z-index: 3;
	max-width: 800px;
	padding: var(--space-xl);
}

.about-hero .hero-title {
	font-size: var(--text-5xl);
	margin-bottom: var(--space-md);
}

.about-hero .hero-subtitle {
	font-size: var(--text-2xl);
	font-family: var(--font-accent);
	opacity: 0.95;
}

.our-story {
	padding: var(--space-5xl) 0;
}

.story-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
	gap: var(--space-4xl);
	align-items: center;
}

.story-content .lead-text {
	font-size: var(--text-xl);
	color: var(--rose-gold);
	font-weight: var(--weight-medium);
	margin-bottom: var(--space-lg);
	line-height: 1.7;
}

.story-content p {
	margin-bottom: var(--space-lg);
	line-height: 1.8;
	color: var(--medium-gray);
}

.story-image {
	border-radius: var(--radius-lg);
	overflow: hidden;
	box-shadow: var(--shadow-xl);
}

.story-image img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.bg-rose-gold-light {
	background: linear-gradient(135deg, rgba(183, 110, 121, 0.05) 0%, rgba(212, 175, 55, 0.03) 100%);
}

.values-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.value-card {
	padding: var(--space-2xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-md);
	text-align: center;
	transition: all var(--transition-luxury);
}

.value-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.value-icon {
	font-size: 3.5rem;
	margin-bottom: var(--space-lg);
}

.value-card h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
}

.value-card p {
	color: var(--medium-gray);
	line-height: 1.7;
}

.process-timeline {
	display: grid;
	gap: var(--space-3xl);
	margin-top: var(--space-4xl);
	max-width: 900px;
	margin-left: auto;
	margin-right: auto;
}

.process-step {
	position: relative;
	padding-left: var(--space-3xl);
	padding-bottom: var(--space-2xl);
	border-left: 3px solid var(--rose-gold);
}

.process-step:last-child {
	border-left-color: transparent;
}

.step-number {
	position: absolute;
	left: -20px;
	top: 0;
	width: 40px;
	height: 40px;
	background: var(--gradient-rose-gold);
	color: var(--white);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: var(--weight-bold);
	box-shadow: var(--shadow-md);
}

.process-step h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
}

.process-step p {
	color: var(--medium-gray);
	line-height: 1.7;
}

.team-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.team-card {
	text-align: center;
	background: var(--white);
	border-radius: var(--radius-lg);
	overflow: hidden;
	box-shadow: var(--shadow-md);
	transition: all var(--transition-luxury);
}

.team-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl);
}

.team-image {
	width: 100%;
	height: 350px;
	overflow: hidden;
	background: var(--off-white);
}

.team-image img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform var(--transition-luxury);
}

.team-card:hover .team-image img {
	transform: scale(1.05);
}

.team-card h3 {
	margin-top: var(--space-lg);
	color: var(--dark-gray);
}

.team-role {
	color: var(--rose-gold);
	font-weight: var(--weight-semibold);
	margin-bottom: var(--space-md);
}

.team-card p:not(.team-role) {
	padding: 0 var(--space-lg) var(--space-xl);
	color: var(--medium-gray);
	line-height: 1.6;
}

.stats-section {
	padding: var(--space-5xl) 0;
	color: var(--white);
}

.stats-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
	gap: var(--space-3xl);
}

.stat-block {
	text-align: center;
}

.stat-number {
	display: block;
	font-size: var(--text-5xl);
	font-weight: var(--weight-bold);
	font-family: var(--font-heading);
	margin-bottom: var(--space-sm);
}

.stat-label {
	display: block;
	font-size: var(--text-lg);
	opacity: 0.9;
}

.about-cta {
	padding: var(--space-5xl) 0;
}

.cta-actions {
	display: flex;
	gap: var(--space-lg);
	justify-content: center;
	flex-wrap: wrap;
	margin-top: var(--space-2xl);
}

@media (max-width: 768px) {
	.about-hero .hero-title {
		font-size: var(--text-3xl);
	}

	.story-grid,
	.values-grid,
	.team-grid,
	.stats-grid {
		grid-template-columns: 1fr;
	}

	.process-timeline {
		margin-left: var(--space-lg);
	}

	.cta-actions {
		flex-direction: column;
	}
}
</style>

<?php
get_footer();
