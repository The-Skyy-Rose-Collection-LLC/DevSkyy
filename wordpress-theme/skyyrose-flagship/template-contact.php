<?php
/**
 * Template Name: Contact
 *
 * Contact page with form, location info, and consultation booking.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main contact-page">

	<!-- Hero Section -->
	<section class="contact-hero">
		<div class="container">
			<div class="hero-content text-center">
				<h1 class="hero-title">Get in Touch</h1>
				<p class="hero-subtitle">We're here to help with any questions about our collections</p>
			</div>
		</div>
	</section>

	<!-- Contact Options -->
	<section class="section contact-options">
		<div class="container">
			<div class="options-grid">
				<div class="option-card">
					<div class="option-icon">📧</div>
					<h3>Email Us</h3>
					<p>hello@skyyrose.com</p>
					<p class="option-note">Response within 24 hours</p>
				</div>

				<div class="option-card">
					<div class="option-icon">📞</div>
					<h3>Call Us</h3>
					<p>(510) 555-ROSE</p>
					<p class="option-note">Mon-Fri, 9am-6pm PST</p>
				</div>

				<div class="option-card">
					<div class="option-icon">📍</div>
					<h3>Visit Us</h3>
					<p>Oakland, California</p>
					<p class="option-note">By appointment only</p>
				</div>

				<div class="option-card">
					<div class="option-icon">💬</div>
					<h3>Live Chat</h3>
					<p>Instant support</p>
					<p class="option-note">Available 9am-9pm PST</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Contact Form & Info -->
	<section class="section contact-main">
		<div class="container">
			<div class="contact-grid">
				<!-- Contact Form -->
				<div class="contact-form-wrapper">
					<h2>Send Us a Message</h2>
					<p class="form-intro">Fill out the form below and we'll get back to you within 24 hours.</p>

					<form class="contact-form" id="contact-form" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
						<input type="hidden" name="action" value="contact_form_submission">
						<?php wp_nonce_field( 'contact_form_nonce', 'contact_nonce' ); ?>

						<div class="form-row">
							<div class="form-group">
								<label for="first-name">First Name *</label>
								<input
									type="text"
									id="first-name"
									name="first_name"
									required
									class="form-control"
								>
							</div>

							<div class="form-group">
								<label for="last-name">Last Name *</label>
								<input
									type="text"
									id="last-name"
									name="last_name"
									required
									class="form-control"
								>
							</div>
						</div>

						<div class="form-group">
							<label for="email">Email Address *</label>
							<input
								type="email"
								id="email"
								name="email"
								required
								class="form-control"
							>
						</div>

						<div class="form-group">
							<label for="phone">Phone Number</label>
							<input
								type="tel"
								id="phone"
								name="phone"
								class="form-control"
							>
						</div>

						<div class="form-group">
							<label for="subject">Subject *</label>
							<select id="subject" name="subject" required class="form-control">
								<option value="">Select a subject...</option>
								<option value="general">General Inquiry</option>
								<option value="consultation">Schedule Consultation</option>
								<option value="custom">Custom Design</option>
								<option value="order">Order Question</option>
								<option value="warranty">Warranty/Repair</option>
								<option value="collaboration">Partnership/Collaboration</option>
							</select>
						</div>

						<div class="form-group">
							<label for="message">Message *</label>
							<textarea
								id="message"
								name="message"
								rows="6"
								required
								class="form-control"
							></textarea>
						</div>

						<div class="form-group">
							<label class="checkbox-label">
								<input type="checkbox" name="newsletter" value="yes">
								<span>Subscribe to our newsletter for exclusive offers and updates</span>
							</label>
						</div>

						<button type="submit" class="btn btn-primary btn-large">Send Message</button>
					</form>
				</div>

				<!-- Additional Info -->
				<div class="contact-info">
					<h3>Schedule a Consultation</h3>
					<p>Visit our Oakland atelier for a private viewing and personalized consultation. Our jewelry experts will guide you through our collections and help you find the perfect piece.</p>

					<div class="info-block">
						<h4>What to Expect</h4>
						<ul>
							<li>Private viewing room</li>
							<li>Expert guidance</li>
							<li>Custom design consultation</li>
							<li>Complimentary refreshments</li>
							<li>No obligation to purchase</li>
						</ul>
					</div>

					<div class="info-block">
						<h4>Hours of Operation</h4>
						<p><strong>Monday - Friday:</strong> 9:00 AM - 6:00 PM<br>
						<strong>Saturday:</strong> 10:00 AM - 5:00 PM<br>
						<strong>Sunday:</strong> By appointment only</p>
					</div>

					<div class="info-block">
						<h4>Location</h4>
						<p>Oakland, California<br>
						Exact address provided upon consultation booking</p>
					</div>

					<a href="#book-consultation" class="btn btn-outline btn-large smooth-scroll">Book Consultation</a>
				</div>
			</div>
		</div>
	</section>

	<!-- FAQ Section -->
	<section class="section faq-section bg-rose-gold-light">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Frequently Asked Questions</h2>
			</div>

			<div class="faq-grid">
				<div class="faq-item">
					<h3>How long does shipping take?</h3>
					<p>Standard shipping takes 3-5 business days within the US. Expedited shipping (1-2 days) is available. International shipping times vary by destination.</p>
				</div>

				<div class="faq-item">
					<h3>Do you offer custom designs?</h3>
					<p>Yes! We specialize in custom jewelry. Schedule a consultation to discuss your vision, and our designers will create a piece uniquely yours.</p>
				</div>

				<div class="faq-item">
					<h3>What is your return policy?</h3>
					<p>30-day returns on all unworn jewelry in original condition. Custom pieces have different terms—please ask for details.</p>
				</div>

				<div class="faq-item">
					<h3>Is financing available?</h3>
					<p>Yes, we offer flexible financing options through Affirm and Klarna. Apply at checkout to see your personalized rates.</p>
				</div>

				<div class="faq-item">
					<h3>Do you offer repairs?</h3>
					<p>All SkyyRose jewelry comes with lifetime warranty covering manufacturing defects and complimentary annual cleanings. Repairs outside warranty are available at competitive rates.</p>
				</div>

				<div class="faq-item">
					<h3>Can I trade in my old jewelry?</h3>
					<p>Yes! We offer trade-in credits on select pieces. Bring your jewelry to a consultation for a free appraisal.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Map Section (Placeholder) -->
	<section class="section map-section">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Find Us</h2>
			</div>
			<div class="map-placeholder">
				<div class="map-content">
					<p>📍 Oakland, California</p>
					<p class="map-note">Exact location provided upon appointment booking</p>
				</div>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<style>
/* Contact Page Specific Styles */
.contact-page .contact-hero {
	padding: var(--space-5xl) 0 var(--space-4xl);
	background: var(--gradient-rose-gold);
	color: var(--white);
}

.contact-hero .hero-title {
	font-size: var(--text-5xl);
	margin-bottom: var(--space-md);
}

.contact-hero .hero-subtitle {
	font-size: var(--text-xl);
	font-family: var(--font-accent);
	opacity: 0.95;
}

.contact-options {
	padding: var(--space-4xl) 0;
	background: var(--white);
}

.options-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: var(--space-2xl);
}

.option-card {
	text-align: center;
	padding: var(--space-2xl);
	background: var(--off-white);
	border-radius: var(--radius-lg);
	transition: all var(--transition-luxury);
}

.option-card:hover {
	transform: translateY(-8px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.option-icon {
	font-size: 3rem;
	margin-bottom: var(--space-md);
}

.option-card h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-sm);
}

.option-card p {
	color: var(--dark-gray);
	font-weight: var(--weight-medium);
	margin-bottom: var(--space-xs);
}

.option-note {
	font-size: var(--text-sm);
	color: var(--medium-gray);
	font-weight: var(--weight-normal);
}

.contact-main {
	padding: var(--space-5xl) 0;
}

.contact-grid {
	display: grid;
	grid-template-columns: 1.5fr 1fr;
	gap: var(--space-4xl);
	align-items: start;
}

.contact-form-wrapper h2 {
	margin-bottom: var(--space-md);
}

.form-intro {
	color: var(--medium-gray);
	margin-bottom: var(--space-2xl);
}

.contact-form {
	background: var(--white);
	padding: var(--space-2xl);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-lg);
}

.form-row {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: var(--space-lg);
}

.form-group {
	margin-bottom: var(--space-lg);
}

.form-group label {
	display: block;
	margin-bottom: var(--space-sm);
	color: var(--dark-gray);
	font-weight: var(--weight-medium);
}

.form-control {
	width: 100%;
	padding: var(--space-md);
	border: 2px solid var(--light-gray);
	border-radius: var(--radius-md);
	font-size: var(--text-base);
	transition: all var(--transition-base);
}

.form-control:focus {
	outline: none;
	border-color: var(--rose-gold);
	box-shadow: 0 0 0 3px rgba(183, 110, 121, 0.1);
}

textarea.form-control {
	resize: vertical;
	min-height: 120px;
}

.checkbox-label {
	display: flex;
	align-items: start;
	gap: var(--space-sm);
	cursor: pointer;
	font-weight: var(--weight-normal);
}

.checkbox-label input[type="checkbox"] {
	margin-top: 4px;
	cursor: pointer;
}

.contact-info {
	background: var(--off-white);
	padding: var(--space-2xl);
	border-radius: var(--radius-lg);
	position: sticky;
	top: var(--space-xl);
}

.contact-info h3 {
	color: var(--rose-gold);
	margin-bottom: var(--space-md);
}

.contact-info > p {
	color: var(--medium-gray);
	line-height: 1.7;
	margin-bottom: var(--space-2xl);
}

.info-block {
	margin-bottom: var(--space-2xl);
	padding-bottom: var(--space-xl);
	border-bottom: 1px solid var(--light-gray);
}

.info-block:last-of-type {
	border-bottom: none;
}

.info-block h4 {
	color: var(--dark-gray);
	margin-bottom: var(--space-md);
}

.info-block ul {
	list-style: none;
	padding: 0;
}

.info-block li {
	padding-left: var(--space-lg);
	position: relative;
	margin-bottom: var(--space-sm);
	color: var(--medium-gray);
}

.info-block li:before {
	content: "✓";
	position: absolute;
	left: 0;
	color: var(--rose-gold);
	font-weight: var(--weight-bold);
}

.info-block p {
	color: var(--medium-gray);
	line-height: 1.7;
}

.bg-rose-gold-light {
	background: linear-gradient(135deg, rgba(183, 110, 121, 0.05) 0%, rgba(212, 175, 55, 0.03) 100%);
}

.faq-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	gap: var(--space-2xl);
	margin-top: var(--space-3xl);
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

.map-section {
	padding: var(--space-5xl) 0;
}

.map-placeholder {
	margin-top: var(--space-2xl);
	height: 400px;
	background: var(--off-white);
	border-radius: var(--radius-lg);
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2px dashed var(--light-gray);
}

.map-content {
	text-align: center;
}

.map-content p {
	font-size: var(--text-xl);
	color: var(--medium-gray);
	margin-bottom: var(--space-sm);
}

.map-note {
	font-size: var(--text-sm);
	color: var(--medium-gray);
	font-style: italic;
}

.smooth-scroll {
	scroll-behavior: smooth;
}

@media (max-width: 768px) {
	.contact-hero .hero-title {
		font-size: var(--text-3xl);
	}

	.options-grid,
	.faq-grid {
		grid-template-columns: 1fr;
	}

	.contact-grid {
		grid-template-columns: 1fr;
	}

	.form-row {
		grid-template-columns: 1fr;
	}

	.contact-info {
		position: static;
	}
}
</style>

<script>
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

// Form Validation Enhancement
document.getElementById('contact-form')?.addEventListener('submit', function(e) {
	// Add any custom validation here
	const email = document.getElementById('email').value;
	if (email && !email.includes('@')) {
		e.preventDefault();
		alert('Please enter a valid email address');
		return false;
	}
});
</script>

<?php
get_footer();
