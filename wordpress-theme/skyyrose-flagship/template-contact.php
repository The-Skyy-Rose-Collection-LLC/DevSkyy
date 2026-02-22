<?php
/**
 * Template Name: Contact
 *
 * Contact page with glassmorphism info cards, social media links,
 * showroom & business hours, AJAX form submission, expanded FAQ accordion,
 * map placeholder section, and response promise section.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

// Customizer values with defaults.
$contact_email = get_theme_mod( 'contact_email', 'hello@skyyrose.co' );
$contact_phone = get_theme_mod( 'contact_phone', '' );

// Contact info cards data.
$contact_cards = array(
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
		'title'       => __( 'Email Us', 'skyyrose-flagship' ),
		'description' => __( 'Drop us a line anytime. We read every message personally.', 'skyyrose-flagship' ),
		'line_1'      => esc_html( $contact_email ),
		'line_2'      => 'press@skyyrose.co',
	),
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'title'       => __( 'Visit Our Showroom', 'skyyrose-flagship' ),
		'description' => __( 'Experience the collections in person by appointment.', 'skyyrose-flagship' ),
		'line_1'      => __( '1234 Broadway, Suite 200', 'skyyrose-flagship' ),
		'line_2'      => __( 'Oakland, CA 94612', 'skyyrose-flagship' ),
	),
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
		'title'       => __( 'Business Hours', 'skyyrose-flagship' ),
		'description' => __( 'Our team is available during the following hours (PST).', 'skyyrose-flagship' ),
		'line_1'      => __( 'Mon-Fri: 9:00 AM - 6:00 PM', 'skyyrose-flagship' ),
		'line_2'      => __( 'Sat: 10:00 AM - 4:00 PM | Sun: Closed', 'skyyrose-flagship' ),
	),
);

// Social media links.
$social_links = array(
	array(
		'name' => 'Instagram',
		'url'  => 'https://instagram.com/skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="3.5"/><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>',
	),
	array(
		'name' => 'TikTok',
		'url'  => 'https://tiktok.com/@skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 0 0-.79-.05A6.34 6.34 0 0 0 3.15 15a6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.34-6.34V8.8a8.26 8.26 0 0 0 4.76 1.5V6.88a4.84 4.84 0 0 1-1-.19z"/></svg>',
	),
	array(
		'name' => 'Twitter',
		'url'  => 'https://twitter.com/skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
	),
	array(
		'name' => 'Facebook',
		'url'  => 'https://facebook.com/skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
	),
	array(
		'name' => 'YouTube',
		'url'  => 'https://youtube.com/@skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
	),
	array(
		'name' => 'Pinterest',
		'url'  => 'https://pinterest.com/skyyrose',
		'icon' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12.017 24c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641 0 12.017 0z"/></svg>',
	),
);

// Subject options for the form dropdown.
$subject_options = array(
	''                  => __( 'Select a topic', 'skyyrose-flagship' ),
	'general-inquiry'   => __( 'General Inquiry', 'skyyrose-flagship' ),
	'order-status'      => __( 'Order Status', 'skyyrose-flagship' ),
	'returns-exchanges' => __( 'Returns & Exchanges', 'skyyrose-flagship' ),
	'wholesale-inquiry' => __( 'Wholesale Inquiry', 'skyyrose-flagship' ),
	'press-media'       => __( 'Press & Media', 'skyyrose-flagship' ),
	'collaboration'     => __( 'Collaboration', 'skyyrose-flagship' ),
	'custom-orders'     => __( 'Custom Orders', 'skyyrose-flagship' ),
	'other'             => __( 'Other', 'skyyrose-flagship' ),
);

// "How did you hear about us?" options.
$referral_options = array(
	''                => __( 'Please select', 'skyyrose-flagship' ),
	'instagram'       => __( 'Instagram', 'skyyrose-flagship' ),
	'tiktok'          => __( 'TikTok', 'skyyrose-flagship' ),
	'twitter'         => __( 'Twitter / X', 'skyyrose-flagship' ),
	'facebook'        => __( 'Facebook', 'skyyrose-flagship' ),
	'youtube'         => __( 'YouTube', 'skyyrose-flagship' ),
	'google-search'   => __( 'Google Search', 'skyyrose-flagship' ),
	'friend-referral' => __( 'Friend or Family', 'skyyrose-flagship' ),
	'press-article'   => __( 'Press / Article', 'skyyrose-flagship' ),
	'event'           => __( 'Event or Pop-Up', 'skyyrose-flagship' ),
	'other'           => __( 'Other', 'skyyrose-flagship' ),
);

// FAQ items array for easy editing.
$faq_items = array(
	array(
		'question' => __( 'How long does shipping take?', 'skyyrose-flagship' ),
		'answer'   => __( 'Domestic orders ship within 1-2 business days. Standard shipping (5-7 business days) is free on orders over $150. Express (2-3 days) and overnight options are available at checkout. International orders typically take 7-14 business days depending on your location and customs processing times.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( "What's your return policy?", 'skyyrose-flagship' ),
		'answer'   => __( 'We offer a 30-day return policy from the date of delivery. Items must be unworn, unwashed, and in their original condition with all tags attached. Simply initiate a return through your order confirmation email or contact us directly. Exchanges are always free. Refunds are processed within 5-7 business days after we receive your return. Pre-order and final sale items may have different policies.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'Do you offer custom orders?', 'skyyrose-flagship' ),
		'answer'   => __( 'Yes! We love bringing unique visions to life. Our custom order process starts with a consultation where we discuss your ideas, preferred materials, and timeline. Custom pieces typically take 4-6 weeks to produce. Reach out through the contact form with "Custom Orders" selected as the subject, and include details about your vision. Pricing varies based on complexity and materials.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'Is wholesale available?', 'skyyrose-flagship' ),
		'answer'   => __( 'We selectively partner with boutiques and retailers that align with our brand vision. Our minimum wholesale order is 12 units per style. For wholesale inquiries, select "Wholesale Inquiry" in the contact form and include your business name, location, and the collections you are interested in. Our wholesale team will follow up within 48 hours with pricing and terms.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'Do you ship internationally?', 'skyyrose-flagship' ),
		'answer'   => __( 'Yes, we ship to over 50 countries worldwide! International shipping rates are calculated at checkout based on your location and order weight. All duties, taxes, and customs fees are the responsibility of the customer. Tracking is provided for all international orders. Please note that delivery times may vary due to customs processing in your country.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'How do I track my order?', 'skyyrose-flagship' ),
		'answer'   => __( 'Once your order ships, you will receive a confirmation email with your tracking number and a direct link to track your package. You can also check your order status anytime by visiting our Order Tracking page or by contacting us with your order number. We ship with major carriers including USPS, UPS, and FedEx.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'What sizes do you carry?', 'skyyrose-flagship' ),
		'answer'   => __( 'Most of our pieces are available in sizes XS through XXL. Each product page includes a detailed size guide with measurements for chest, waist, hips, and length. We recommend measuring yourself and comparing to our size charts for the best fit. If you are between sizes, we suggest sizing up for a relaxed fit or down for a more tailored look. Need help? Our styling team is always happy to assist.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'Are your products sustainable?', 'skyyrose-flagship' ),
		'answer'   => __( 'Sustainability is at the heart of what we do. We use premium, ethically sourced materials including organic cotton, recycled polyester, and responsibly produced hardware. Our limited production runs minimize waste, and we partner with manufacturers who uphold fair labor practices. We are continuously working to reduce our environmental footprint through eco-friendly packaging and carbon-offset shipping options.', 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'Do you do collaborations?', 'skyyrose-flagship' ),
		'answer'   => __( "Absolutely! We love partnering with artists, designers, influencers, and brands that share our vision. Whether you're interested in a co-designed capsule, a content collaboration, or a brand partnership, we want to hear from you. Select \"Collaboration\" in the contact form and share your portfolio or social links along with your idea. Our creative team reviews every submission.", 'skyyrose-flagship' ),
	),
	array(
		'question' => __( 'How can I join the SkyyRose community?', 'skyyrose-flagship' ),
		'answer'   => __( 'There are many ways to be part of the SkyyRose family! Follow us on Instagram, TikTok, and Twitter @skyyrose for the latest drops, behind-the-scenes content, and styling inspiration. Sign up for our newsletter to get early access to new collections and exclusive member discounts. We also host pop-up events in Oakland and other cities throughout the year, so stay tuned for invitations.', 'skyyrose-flagship' ),
	),
);
?>

<main id="primary" class="site-main contact-page">

	<!-- Film Grain Overlay -->
	<div class="film-grain" aria-hidden="true"></div>

	<!-- Page Header -->
	<section class="contact-hero">
		<div class="contact-hero__container">
			<div class="contact-hero__decorative" aria-hidden="true">
				<span class="contact-hero__line contact-hero__line--left"></span>
				<svg class="contact-hero__diamond" width="16" height="16" viewBox="0 0 16 16" fill="none">
					<rect x="8" y="0" width="11.3" height="11.3" rx="1" transform="rotate(45 8 0)" stroke="currentColor" stroke-width="1"/>
				</svg>
				<span class="contact-hero__line contact-hero__line--right"></span>
			</div>
			<h1 class="contact-hero__title">
				<?php esc_html_e( "We'd Love to Hear From You", 'skyyrose-flagship' ); ?>
			</h1>
			<p class="contact-hero__subtitle">
				<?php esc_html_e( 'Whether you have a question about our collections, need styling advice, want to explore a collaboration, or just want to say hello, the SkyyRose community is here for you. Every message matters to us.', 'skyyrose-flagship' ); ?>
			</p>
		</div>
	</section>

	<!-- Contact Section: 2-Column Layout -->
	<section class="contact-section" aria-label="<?php esc_attr_e( 'Contact Information and Form', 'skyyrose-flagship' ); ?>">
		<div class="contact-section__container">

			<!-- Left Column: Contact Info Cards -->
			<div class="contact-info">
				<h2 class="contact-info__heading">
					<?php esc_html_e( 'Contact Information', 'skyyrose-flagship' ); ?>
				</h2>

				<?php foreach ( $contact_cards as $card ) : ?>
					<div class="contact-card">
						<div class="contact-card__icon" aria-hidden="true">
							<?php echo $card['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- SVG markup. ?>
						</div>
						<div class="contact-card__content">
							<h3 class="contact-card__title">
								<?php echo esc_html( $card['title'] ); ?>
							</h3>
							<p class="contact-card__description">
								<?php echo esc_html( $card['description'] ); ?>
							</p>
							<p class="contact-card__text">
								<?php echo esc_html( $card['line_1'] ); ?>
								<br>
								<?php echo esc_html( $card['line_2'] ); ?>
							</p>
						</div>
					</div>
				<?php endforeach; ?>

				<!-- Social Media Links -->
				<div class="contact-social">
					<h3 class="contact-social__heading">
						<?php esc_html_e( 'Follow Us', 'skyyrose-flagship' ); ?>
					</h3>
					<p class="contact-social__description">
						<?php esc_html_e( 'Stay connected with the SkyyRose community for drops, styling tips, and behind-the-scenes content.', 'skyyrose-flagship' ); ?>
					</p>
					<div class="contact-social__links">
						<?php foreach ( $social_links as $social ) : ?>
							<a
								href="<?php echo esc_url( $social['url'] ); ?>"
								class="contact-social__link"
								target="_blank"
								rel="noopener noreferrer"
								aria-label="<?php echo esc_attr( sprintf( __( 'Follow SkyyRose on %s', 'skyyrose-flagship' ), $social['name'] ) ); ?>"
							>
								<span class="contact-social__link-icon" aria-hidden="true">
									<?php echo $social['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- SVG markup. ?>
								</span>
								<span class="contact-social__link-name">
									<?php echo esc_html( $social['name'] ); ?>
								</span>
							</a>
						<?php endforeach; ?>
					</div>
				</div>
			</div>

			<!-- Right Column: Contact Form -->
			<div class="contact-form-wrapper">
				<h2 class="contact-form__heading">
					<?php esc_html_e( 'Send Us a Message', 'skyyrose-flagship' ); ?>
				</h2>

				<form
					id="skyyrose-contact-form"
					class="contact-form"
					method="post"
					action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>"
					novalidate
				>
					<?php wp_nonce_field( 'skyyrose_contact_form', 'skyyrose_contact_nonce' ); ?>
					<input type="hidden" name="action" value="skyyrose_contact_submit">

					<!-- Honeypot field for bot detection -->
					<div class="contact-form__hp" aria-hidden="true">
						<label for="contact-website">
							<?php esc_html_e( 'Website', 'skyyrose-flagship' ); ?>
						</label>
						<input
							type="text"
							id="contact-website"
							name="website"
							tabindex="-1"
							autocomplete="off"
						>
					</div>

					<div class="contact-form__row">
						<div class="contact-form__group">
							<label for="contact-first-name" class="contact-form__label">
								<?php esc_html_e( 'First Name', 'skyyrose-flagship' ); ?>
							</label>
							<input
								type="text"
								id="contact-first-name"
								name="first_name"
								class="contact-form__input"
								required
								autocomplete="given-name"
								aria-required="true"
								placeholder="<?php esc_attr_e( 'Your first name', 'skyyrose-flagship' ); ?>"
							>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
						<div class="contact-form__group">
							<label for="contact-last-name" class="contact-form__label">
								<?php esc_html_e( 'Last Name', 'skyyrose-flagship' ); ?>
							</label>
							<input
								type="text"
								id="contact-last-name"
								name="last_name"
								class="contact-form__input"
								required
								autocomplete="family-name"
								aria-required="true"
								placeholder="<?php esc_attr_e( 'Your last name', 'skyyrose-flagship' ); ?>"
							>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
					</div>

					<div class="contact-form__row">
						<div class="contact-form__group">
							<label for="contact-email" class="contact-form__label">
								<?php esc_html_e( 'Email Address', 'skyyrose-flagship' ); ?>
							</label>
							<input
								type="email"
								id="contact-email"
								name="email"
								class="contact-form__input"
								required
								autocomplete="email"
								aria-required="true"
								placeholder="<?php esc_attr_e( 'you@example.com', 'skyyrose-flagship' ); ?>"
							>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
						<div class="contact-form__group">
							<label for="contact-phone" class="contact-form__label">
								<?php esc_html_e( 'Phone (Optional)', 'skyyrose-flagship' ); ?>
							</label>
							<input
								type="tel"
								id="contact-phone"
								name="phone"
								class="contact-form__input"
								autocomplete="tel"
								placeholder="<?php esc_attr_e( '(555) 123-4567', 'skyyrose-flagship' ); ?>"
							>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
					</div>

					<div class="contact-form__row">
						<div class="contact-form__group">
							<label for="contact-subject" class="contact-form__label">
								<?php esc_html_e( 'Subject', 'skyyrose-flagship' ); ?>
							</label>
							<select
								id="contact-subject"
								name="subject"
								class="contact-form__select"
								required
								aria-required="true"
							>
								<?php foreach ( $subject_options as $value => $label ) : ?>
									<option value="<?php echo esc_attr( $value ); ?>">
										<?php echo esc_html( $label ); ?>
									</option>
								<?php endforeach; ?>
							</select>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
						<div class="contact-form__group contact-form__group--order-number" id="order-number-group">
							<label for="contact-order-number" class="contact-form__label">
								<?php esc_html_e( 'Order Number (Optional)', 'skyyrose-flagship' ); ?>
							</label>
							<input
								type="text"
								id="contact-order-number"
								name="order_number"
								class="contact-form__input"
								placeholder="<?php esc_attr_e( 'e.g. SR-2025-123456', 'skyyrose-flagship' ); ?>"
							>
							<span class="contact-form__error" role="alert" aria-live="polite"></span>
						</div>
					</div>

					<!-- Preferred Contact Method -->
					<div class="contact-form__group">
						<fieldset class="contact-form__fieldset">
							<legend class="contact-form__label">
								<?php esc_html_e( 'Preferred Contact Method', 'skyyrose-flagship' ); ?>
							</legend>
							<div class="contact-form__radio-group">
								<label class="contact-form__radio-label">
									<input
										type="radio"
										name="preferred_contact"
										value="email"
										class="contact-form__radio"
										checked
									>
									<span class="contact-form__radio-indicator" aria-hidden="true"></span>
									<span class="contact-form__radio-text">
										<?php esc_html_e( 'Email', 'skyyrose-flagship' ); ?>
									</span>
								</label>
								<label class="contact-form__radio-label">
									<input
										type="radio"
										name="preferred_contact"
										value="phone"
										class="contact-form__radio"
									>
									<span class="contact-form__radio-indicator" aria-hidden="true"></span>
									<span class="contact-form__radio-text">
										<?php esc_html_e( 'Phone', 'skyyrose-flagship' ); ?>
									</span>
								</label>
								<label class="contact-form__radio-label">
									<input
										type="radio"
										name="preferred_contact"
										value="either"
										class="contact-form__radio"
									>
									<span class="contact-form__radio-indicator" aria-hidden="true"></span>
									<span class="contact-form__radio-text">
										<?php esc_html_e( 'Either', 'skyyrose-flagship' ); ?>
									</span>
								</label>
							</div>
						</fieldset>
					</div>

					<div class="contact-form__group">
						<label for="contact-message" class="contact-form__label">
							<?php esc_html_e( 'Your Message', 'skyyrose-flagship' ); ?>
						</label>
						<textarea
							id="contact-message"
							name="message"
							class="contact-form__textarea"
							required
							aria-required="true"
							placeholder="<?php esc_attr_e( "Tell us what's on your mind. We're all ears...", 'skyyrose-flagship' ); ?>"
						></textarea>
						<span class="contact-form__error" role="alert" aria-live="polite"></span>
					</div>

					<div class="contact-form__group">
						<label for="contact-referral" class="contact-form__label">
							<?php esc_html_e( 'How Did You Hear About Us? (Optional)', 'skyyrose-flagship' ); ?>
						</label>
						<select
							id="contact-referral"
							name="referral_source"
							class="contact-form__select"
						>
							<?php foreach ( $referral_options as $value => $label ) : ?>
								<option value="<?php echo esc_attr( $value ); ?>">
									<?php echo esc_html( $label ); ?>
								</option>
							<?php endforeach; ?>
						</select>
					</div>

					<button type="submit" class="contact-form__submit" id="contact-submit-btn">
						<span class="contact-form__submit-text">
							<?php esc_html_e( 'Send Message', 'skyyrose-flagship' ); ?>
						</span>
						<span class="contact-form__submit-loading" aria-hidden="true">
							<svg class="contact-form__spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
								<path d="M21 12a9 9 0 1 1-6.219-8.56"/>
							</svg>
							<?php esc_html_e( 'Sending...', 'skyyrose-flagship' ); ?>
						</span>
					</button>
				</form>
			</div>

		</div>
	</section>

	<!-- Response Promise Section -->
	<section class="response-promise" aria-label="<?php esc_attr_e( 'Our Response Promise', 'skyyrose-flagship' ); ?>">
		<div class="response-promise__container">
			<div class="response-promise__icon" aria-hidden="true">
				<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10"/>
					<polyline points="12 6 12 12 16 14"/>
				</svg>
			</div>
			<h2 class="response-promise__title">
				<?php esc_html_e( 'We Typically Respond Within 24 Hours', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="response-promise__text">
				<?php esc_html_e( 'Our team reads every message personally. You will hear back from a real person, not a bot.', 'skyyrose-flagship' ); ?>
			</p>
			<div class="response-promise__channels">
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Email', 'skyyrose-flagship' ); ?>
					</span>
				</div>
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="3.5"/><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Instagram DM', 'skyyrose-flagship' ); ?>
					</span>
				</div>
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Live Chat', 'skyyrose-flagship' ); ?>
					</span>
				</div>
			</div>
		</div>
	</section>

	<!-- FAQ Accordion Section -->
	<section class="faq-section" aria-label="<?php esc_attr_e( 'Frequently Asked Questions', 'skyyrose-flagship' ); ?>">
		<div class="faq-section__container">
			<h2 class="faq-section__heading">
				<?php esc_html_e( 'Frequently Asked Questions', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="faq-section__subheading">
				<?php esc_html_e( "Can't find what you're looking for? Send us a message above and we'll get back to you.", 'skyyrose-flagship' ); ?>
			</p>

			<div class="faq-accordion" role="list">
				<?php foreach ( $faq_items as $index => $faq ) : ?>
					<?php $faq_id = 'faq-answer-' . $index; ?>
					<div class="faq-item" role="listitem">
						<button
							class="faq-item__trigger"
							type="button"
							aria-expanded="false"
							aria-controls="<?php echo esc_attr( $faq_id ); ?>"
							id="faq-trigger-<?php echo esc_attr( $index ); ?>"
						>
							<span class="faq-item__question">
								<?php echo esc_html( $faq['question'] ); ?>
							</span>
							<span class="faq-item__icon" aria-hidden="true">
								<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<line x1="12" y1="5" x2="12" y2="19"/>
									<line x1="5" y1="12" x2="19" y2="12"/>
								</svg>
							</span>
						</button>
						<div
							class="faq-item__panel"
							id="<?php echo esc_attr( $faq_id ); ?>"
							role="region"
							aria-labelledby="faq-trigger-<?php echo esc_attr( $index ); ?>"
							hidden
						>
							<p class="faq-item__answer">
								<?php echo esc_html( $faq['answer'] ); ?>
							</p>
						</div>
					</div>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

	<!-- Map Section -->
	<section class="contact-map" aria-label="<?php esc_attr_e( 'Our Location', 'skyyrose-flagship' ); ?>">
		<div class="contact-map__container">
			<div class="contact-map__content">
				<div class="contact-map__placeholder" aria-hidden="true">
					<div class="contact-map__grid">
						<div class="contact-map__grid-line contact-map__grid-line--h"></div>
						<div class="contact-map__grid-line contact-map__grid-line--h"></div>
						<div class="contact-map__grid-line contact-map__grid-line--h"></div>
						<div class="contact-map__grid-line contact-map__grid-line--v"></div>
						<div class="contact-map__grid-line contact-map__grid-line--v"></div>
						<div class="contact-map__grid-line contact-map__grid-line--v"></div>
					</div>
					<div class="contact-map__pin">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
							<circle cx="12" cy="10" r="3"/>
						</svg>
						<span class="contact-map__pin-pulse"></span>
					</div>
				</div>
				<div class="contact-map__info">
					<h3 class="contact-map__title">
						<?php esc_html_e( 'SkyyRose Showroom', 'skyyrose-flagship' ); ?>
					</h3>
					<p class="contact-map__address">
						<?php esc_html_e( '1234 Broadway, Suite 200', 'skyyrose-flagship' ); ?><br>
						<?php esc_html_e( 'Oakland, CA 94612', 'skyyrose-flagship' ); ?>
					</p>
					<p class="contact-map__hours">
						<?php esc_html_e( 'Mon-Fri 9AM-6PM PST | Sat 10AM-4PM', 'skyyrose-flagship' ); ?>
					</p>
					<a
						href="https://www.google.com/maps/search/?api=1&query=Oakland+CA+94612"
						class="contact-map__directions"
						target="_blank"
						rel="noopener noreferrer"
					>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M18 8L22 12L18 16"/>
							<path d="M2 12H22"/>
						</svg>
						<?php esc_html_e( 'Get Directions', 'skyyrose-flagship' ); ?>
					</a>
				</div>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<?php
get_footer();
