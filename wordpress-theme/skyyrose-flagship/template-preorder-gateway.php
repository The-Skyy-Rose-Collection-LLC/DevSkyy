<?php
/**
 * Template Name: Preorder Gateway
 *
 * Pre-launch gateway for upcoming collections with email capture,
 * countdowns, and exclusive early access.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main preorder-gateway">

	<!-- Hero Section with Countdown -->
	<section class="preorder-hero">
		<div class="hero-overlay"></div>
		<div class="hero-content">
			<span class="coming-soon-badge">Coming Soon</span>
			<h1 class="hero-title">Something Extraordinary</h1>
			<p class="hero-subtitle">A new collection unlike anything we've created before</p>

			<!-- Countdown Timer -->
			<div class="countdown-timer" data-launch-date="<?php echo esc_attr( get_post_meta( get_the_ID(), '_launch_date', true ) ?: '2026-03-15T00:00:00' ); ?>">
				<div class="countdown-block">
					<span class="countdown-number" id="days">00</span>
					<span class="countdown-label">Days</span>
				</div>
				<div class="countdown-block">
					<span class="countdown-number" id="hours">00</span>
					<span class="countdown-label">Hours</span>
				</div>
				<div class="countdown-block">
					<span class="countdown-number" id="minutes">00</span>
					<span class="countdown-label">Minutes</span>
				</div>
				<div class="countdown-block">
					<span class="countdown-number" id="seconds">00</span>
					<span class="countdown-label">Seconds</span>
				</div>
			</div>

			<!-- Email Signup -->
			<div class="email-capture">
				<h3>Get Early Access</h3>
				<p>Join the waitlist for exclusive pre-launch pricing and first access</p>
				<form class="signup-form" id="preorder-form" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="preorder_signup">
					<?php wp_nonce_field( 'preorder_signup_nonce', 'preorder_nonce' ); ?>
					<div class="form-group">
						<input
							type="email"
							name="email"
							placeholder="Enter your email"
							required
							class="email-input"
						>
						<button type="submit" class="btn btn-primary">
							Notify Me
						</button>
					</div>
					<p class="form-note">Join <span class="waitlist-count">0</span> others waiting for launch</p>
				</form>
			</div>
		</div>
	</section>

	<!-- Teaser Gallery -->
	<section class="section teaser-section">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">Sneak Peek</span>
				<h2 class="section-title">A Glimpse of What's Coming</h2>
			</div>

			<div class="teaser-grid">
				<div class="teaser-card blur-reveal">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/teaser-1.jpg' ); ?>" alt="Teaser 1">
					<div class="teaser-overlay">
						<span class="teaser-hint">Exclusive Design</span>
					</div>
				</div>
				<div class="teaser-card blur-reveal">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/teaser-2.jpg' ); ?>" alt="Teaser 2">
					<div class="teaser-overlay">
						<span class="teaser-hint">Rare Materials</span>
					</div>
				</div>
				<div class="teaser-card blur-reveal">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/teaser-3.jpg' ); ?>" alt="Teaser 3">
					<div class="teaser-overlay">
						<span class="teaser-hint">Limited Edition</span>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- What to Expect -->
	<section class="section expect-section bg-mauve-light">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">What to Expect</h2>
			</div>

			<div class="expect-grid">
				<div class="expect-card">
					<div class="expect-icon">💎</div>
					<h3>Exceptional Materials</h3>
					<p>We've sourced the finest materials from around the world—gemstones you've never seen before in luxury jewelry.</p>
				</div>
				<div class="expect-card">
					<div class="expect-icon">🎨</div>
					<h3>Revolutionary Design</h3>
					<p>A fresh aesthetic that pushes boundaries while honoring our commitment to timeless elegance.</p>
				</div>
				<div class="expect-card">
					<div class="expect-icon">🌟</div>
					<h3>Limited Quantities</h3>
					<p>Each piece will be produced in strictly limited numbers, ensuring exclusivity and value.</p>
				</div>
				<div class="expect-card">
					<div class="expect-icon">🎁</div>
					<h3>Early Bird Pricing</h3>
					<p>Waitlist members receive exclusive pre-launch pricing—up to 25% off retail.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Social Proof -->
	<section class="section social-proof">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Join Discerning Collectors</h2>
			</div>

			<div class="testimonials-grid">
				<blockquote class="testimonial-card">
					<p>"The previous SkyyRose collections exceeded all expectations. I can't wait to see what's next."</p>
					<cite>— Sarah M., Signature Collection Owner</cite>
				</blockquote>
				<blockquote class="testimonial-card">
					<p>"Worth every moment of the wait. The craftsmanship and attention to detail are unmatched."</p>
					<cite>— James L., Love Hurts Collection Owner</cite>
				</blockquote>
				<blockquote class="testimonial-card">
					<p>"SkyyRose has become my go-to for pieces that make a statement. Always exquisite."</p>
					<cite>— Maria K., Black Rose Collection Owner</cite>
				</blockquote>
			</div>
		</div>
	</section>

	<!-- FAQ -->
	<section class="section faq-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Frequently Asked Questions</h2>
			</div>

			<div class="faq-grid">
				<div class="faq-item">
					<h3>When will this collection launch?</h3>
					<p>The official launch date is displayed in the countdown above. Waitlist members will receive early access 48 hours before the public launch.</p>
				</div>
				<div class="faq-item">
					<h3>What are the benefits of joining the waitlist?</h3>
					<p>Waitlist members receive: exclusive pre-launch pricing (up to 25% off), first access to limited pieces, behind-the-scenes content, and priority customer service.</p>
				</div>
				<div class="faq-item">
					<h3>How limited will the collection be?</h3>
					<p>Most pieces will be produced in quantities of 100 or fewer worldwide. Some signature pieces will be limited to just 25 units.</p>
				</div>
				<div class="faq-item">
					<h3>Can I reserve a piece now?</h3>
					<p>Full reservations open 48 hours before launch for waitlist members. You'll receive an email with a private reservation link.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Final CTA -->
	<section class="section final-cta gradient-rose-gold">
		<div class="container text-center">
			<h2 class="section-title">Don't Miss Out</h2>
			<p class="section-subtitle">Join the waitlist now for exclusive early access and pricing</p>
			<a href="#preorder-form" class="btn btn-primary btn-large smooth-scroll">Join Waitlist</a>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Preorder Gateway Specific Styles */
.preorder-gateway .preorder-hero {
	position: relative;
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	color: var(--white);
	overflow: hidden;
	background: linear-gradient(135deg, var(--rose-gold) 0%, var(--mauve) 100%);
}

.preorder-hero .hero-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.3) 100%);
	z-index: 1;
}

.preorder-hero .hero-content {
	position: relative;
	z-index: 2;
	max-width: 900px;
	padding: var(--space-xl);
}

.coming-soon-badge {
	display: inline-block;
	padding: var(--space-sm) var(--space-xl);
	font-size: var(--text-sm);
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	letter-spacing: 0.2em;
	background: rgba(255, 255, 255, 0.15);
	border: 2px solid rgba(255, 255, 255, 0.3);
	border-radius: var(--radius-full);
	margin-bottom: var(--space-xl);
	backdrop-filter: blur(10px);
	animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
	0%, 100% { opacity: 1; }
	50% { opacity: 0.7; }
}

.preorder-hero .hero-title {
	font-size: var(--text-6xl);
	margin-bottom: var(--space-lg);
	text-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
}

.preorder-hero .hero-subtitle {
	font-size: var(--text-2xl);
	font-family: var(--font-accent);
	margin-bottom: var(--space-3xl);
	opacity: 0.95;
}

.countdown-timer {
	display: flex;
	gap: var(--space-xl);
	justify-content: center;
	margin-bottom: var(--space-3xl);
	flex-wrap: wrap;
}

.countdown-block {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: var(--space-lg) var(--space-xl);
	background: rgba(255, 255, 255, 0.1);
	border-radius: var(--radius-lg);
	backdrop-filter: blur(10px);
	border: 1px solid rgba(255, 255, 255, 0.2);
	min-width: 100px;
}

.countdown-number {
	font-size: var(--text-5xl);
	font-weight: var(--weight-bold);
	font-family: var(--font-heading);
	line-height: 1;
}

.countdown-label {
	font-size: var(--text-sm);
	text-transform: uppercase;
	letter-spacing: 0.1em;
	opacity: 0.8;
	margin-top: var(--space-xs);
}

.email-capture {
	max-width: 600px;
	margin: 0 auto;
	padding: var(--space-2xl);
	background: rgba(255, 255, 255, 0.1);
	border-radius: var(--radius-lg);
	backdrop-filter: blur(15px);
	border: 1px solid rgba(255, 255, 255, 0.2);
}

.email-capture h3 {
	margin-bottom: var(--space-sm);
	font-size: var(--text-2xl);
}

.email-capture > p {
	margin-bottom: var(--space-lg);
	opacity: 0.9;
}

.signup-form .form-group {
	display: flex;
	gap: var(--space-md);
	margin-bottom: var(--space-md);
}

.signup-form .email-input {
	flex: 1;
	padding: var(--space-md) var(--space-lg);
	font-size: var(--text-lg);
	border: 2px solid rgba(255, 255, 255, 0.3);
	border-radius: var(--radius-md);
	background: rgba(255, 255, 255, 0.9);
	color: var(--dark-gray);
	transition: all var(--transition-base);
}

.signup-form .email-input:focus {
	outline: none;
	border-color: var(--white);
	background: var(--white);
}

.signup-form .btn {
	padding: var(--space-md) var(--space-2xl);
	font-size: var(--text-lg);
	white-space: nowrap;
}

.form-note {
	font-size: var(--text-sm);
	opacity: 0.8;
}

.waitlist-count {
	font-weight: var(--weight-bold);
	color: var(--white);
}

.teaser-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
}

.teaser-card {
	position: relative;
	border-radius: var(--radius-lg);
	overflow: hidden;
	aspect-ratio: 1;
	box-shadow: var(--shadow-lg);
}

.teaser-card.blur-reveal img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	filter: blur(20px);
	transition: filter var(--transition-luxury);
}

.teaser-card:hover img {
	filter: blur(5px);
}

.teaser-overlay {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.3);
}

.teaser-hint {
	font-size: var(--text-xl);
	font-weight: var(--weight-bold);
	color: var(--white);
	text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.bg-mauve-light {
	background: linear-gradient(135deg, rgba(216, 167, 177, 0.1) 0%, rgba(183, 110, 121, 0.05) 100%);
}

.expect-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.expect-card {
	text-align: center;
	padding: var(--space-2xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-md);
	transition: all var(--transition-luxury);
}

.expect-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.expect-icon {
	font-size: 3.5rem;
	margin-bottom: var(--space-lg);
}

.expect-card h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
}

.testimonials-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.testimonial-card {
	padding: var(--space-2xl);
	background: var(--off-white);
	border-radius: var(--radius-lg);
	border-left: 4px solid var(--rose-gold);
	box-shadow: var(--shadow-md);
}

.testimonial-card p {
	font-size: var(--text-lg);
	font-style: italic;
	margin-bottom: var(--space-lg);
	color: var(--dark-gray);
}

.testimonial-card cite {
	font-size: var(--text-sm);
	color: var(--medium-gray);
	font-style: normal;
}

.faq-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-2xl);
}

.faq-item {
	padding: var(--space-xl);
	background: var(--white);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-sm);
}

.faq-item h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
	font-size: var(--text-lg);
}

.faq-item p {
	color: var(--medium-gray);
	line-height: 1.7;
}

.final-cta {
	padding: var(--space-4xl) var(--space-xl);
	color: var(--white);
}

.final-cta .section-title,
.final-cta .section-subtitle {
	color: var(--white);
	margin-bottom: var(--space-lg);
}

.smooth-scroll {
	scroll-behavior: smooth;
}

@media (max-width: 768px) {
	.preorder-hero .hero-title {
		font-size: var(--text-4xl);
	}

	.countdown-timer {
		gap: var(--space-md);
	}

	.countdown-block {
		min-width: 70px;
		padding: var(--space-md) var(--space-lg);
	}

	.countdown-number {
		font-size: var(--text-3xl);
	}

	.signup-form .form-group {
		flex-direction: column;
	}

	.teaser-grid,
	.expect-grid,
	.testimonials-grid,
	.faq-grid {
		grid-template-columns: 1fr;
	}
}
</style>

<script>
// Countdown Timer
(function() {
	const timer = document.querySelector('.countdown-timer');
	if (!timer) return;

	const launchDate = new Date(timer.dataset.launchDate).getTime();

	function updateCountdown() {
		const now = new Date().getTime();
		const distance = launchDate - now;

		if (distance < 0) {
			document.getElementById('days').textContent = '00';
			document.getElementById('hours').textContent = '00';
			document.getElementById('minutes').textContent = '00';
			document.getElementById('seconds').textContent = '00';
			return;
		}

		const days = Math.floor(distance / (1000 * 60 * 60 * 24));
		const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
		const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
		const seconds = Math.floor((distance % (1000 * 60)) / 1000);

		document.getElementById('days').textContent = String(days).padStart(2, '0');
		document.getElementById('hours').textContent = String(hours).padStart(2, '0');
		document.getElementById('minutes').textContent = String(minutes).padStart(2, '0');
		document.getElementById('seconds').textContent = String(seconds).padStart(2, '0');
	}

	updateCountdown();
	setInterval(updateCountdown, 1000);
})();

// Smooth Scroll
document.querySelectorAll('a.smooth-scroll').forEach(anchor => {
	anchor.addEventListener('click', function (e) {
		e.preventDefault();
		const target = document.querySelector(this.getAttribute('href'));
		if (target) {
			target.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	});
});
</script>

<?php
get_footer();
