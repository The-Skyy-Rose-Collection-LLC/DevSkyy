<?php
/**
 * Template Name: Contact
 *
 * Contact page with glassmorphism info cards, social media links,
 * showroom & business hours, AJAX form submission, expanded FAQ accordion,
 * map placeholder section, and response promise section.
 *
 * @package SkyyRose
 * @since   3.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

// Customizer values with defaults.
$contact_email   = get_theme_mod( 'contact_email', 'hello@skyyrose.co' );
$contact_phone   = get_theme_mod( 'contact_phone', '' );
$showroom_line_1 = get_theme_mod( 'contact_address_1', 'Oakland, CA' );
$showroom_line_2 = get_theme_mod( 'contact_address_2', 'By Appointment Only' );

// Contact info cards data.
$contact_cards = array(
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
		'title'       => __( 'Email Us', 'skyyrose' ),
		'description' => __( 'Drop us a line anytime. We read every message personally.', 'skyyrose' ),
		'line_1'      => $contact_email,
		'line_2'      => 'press@skyyrose.co',
	),
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'title'       => __( 'Visit Our Showroom', 'skyyrose' ),
		'description' => __( 'Experience the collections in person by appointment.', 'skyyrose' ),
		'line_1'      => $showroom_line_1,
		'line_2'      => $showroom_line_2,
	),
	array(
		'icon'        => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
		'title'       => __( 'Business Hours', 'skyyrose' ),
		'description' => __( 'Our team is available during the following hours (PST).', 'skyyrose' ),
		'line_1'      => __( 'Mon-Fri: 9:00 AM - 6:00 PM', 'skyyrose' ),
		'line_2'      => __( 'Sat: 10:00 AM - 4:00 PM | Sun: Closed', 'skyyrose' ),
	),
);

// Social media links — sourced from centralized function.
$social_icons_map   = array(
	'instagram' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="3.5"/><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>',
	'tiktok'    => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 0 0-.79-.05A6.34 6.34 0 0 0 3.15 15a6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.34-6.34V8.8a8.26 8.26 0 0 0 4.76 1.5V6.88a4.84 4.84 0 0 1-1-.19z"/></svg>',
	'twitter'   => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
	'facebook'  => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
	'youtube'   => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
	'pinterest' => '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12.017 24c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641 0 12.017 0z"/></svg>',
);
$centralized_social = skyyrose_get_social_links();
$social_links       = array();
foreach ( $social_icons_map as $platform => $icon ) {
	if ( isset( $centralized_social[ $platform ] ) ) {
		$social_links[] = array(
			'name' => $centralized_social[ $platform ]['label'],
			'url'  => $centralized_social[ $platform ]['url'],
			'icon' => $icon,
		);
	}
}

// Subject options for the form dropdown.
$subject_options = array(
	''                  => __( 'Select a topic', 'skyyrose' ),
	'general-inquiry'   => __( 'General Inquiry', 'skyyrose' ),
	'order-status'      => __( 'Order Status', 'skyyrose' ),
	'returns-exchanges' => __( 'Returns & Exchanges', 'skyyrose' ),
	'wholesale-inquiry' => __( 'Wholesale Inquiry', 'skyyrose' ),
	'press-media'       => __( 'Press & Media', 'skyyrose' ),
	'collaboration'     => __( 'Collaboration', 'skyyrose' ),
	'custom-orders'     => __( 'Custom Orders', 'skyyrose' ),
	'other'             => __( 'Other', 'skyyrose' ),
);

// "What brought you to SkyyRose?" — brand-voice referral options.
$referral_options = array(
	''             => __( 'Pick one', 'skyyrose' ),
	'the-drop'     => __( 'The drop', 'skyyrose' ),
	'word-of-mouth' => __( 'Word of mouth', 'skyyrose' ),
	'social-media' => __( 'Social media', 'skyyrose' ),
	'just-found-it' => __( 'Just found it', 'skyyrose' ),
);

// FAQ items array for easy editing.
$faq_items = array(
	array(
		'question' => __( 'How long does shipping take?', 'skyyrose' ),
		'answer'   => __( 'Domestic orders ship within 1-2 business days. Standard shipping (5-7 business days) is free on orders over $150. Express (2-3 days) and overnight options are available at checkout. International orders typically take 7-14 business days depending on your location and customs processing times.', 'skyyrose' ),
	),
	array(
		'question' => __( "What's your return policy?", 'skyyrose' ),
		'answer'   => __( 'We offer a 30-day return policy from the date of delivery. Items must be unworn, unwashed, and in their original condition with all tags attached. Simply initiate a return through your order confirmation email or contact us directly. Exchanges are always free. Refunds are processed within 5-7 business days after we receive your return. Pre-order and final sale items may have different policies.', 'skyyrose' ),
	),
	array(
		'question' => __( 'Do you offer custom orders?', 'skyyrose' ),
		'answer'   => __( 'Yes! We love bringing unique visions to life. Our custom order process starts with a consultation where we discuss your ideas, preferred materials, and timeline. Custom pieces typically take 4-6 weeks to produce. Reach out through the contact form with "Custom Orders" selected as the subject, and include details about your vision. Pricing varies based on complexity and materials.', 'skyyrose' ),
	),
	array(
		'question' => __( 'Is wholesale available?', 'skyyrose' ),
		'answer'   => __( 'We selectively partner with boutiques and retailers that align with our brand vision. Our minimum wholesale order is 12 units per style. For wholesale inquiries, select "Wholesale Inquiry" in the contact form and include your business name, location, and the collections you are interested in. Our wholesale team will follow up within 48 hours with pricing and terms.', 'skyyrose' ),
	),
	array(
		'question' => __( 'Do you ship internationally?', 'skyyrose' ),
		'answer'   => __( 'Yes, we ship to over 50 countries worldwide! International shipping rates are calculated at checkout based on your location and order weight. All duties, taxes, and customs fees are the responsibility of the customer. Tracking is provided for all international orders. Please note that delivery times may vary due to customs processing in your country.', 'skyyrose' ),
	),
	array(
		'question' => __( 'How do I track my order?', 'skyyrose' ),
		'answer'   => __( 'Once your order ships, you will receive a confirmation email with your tracking number and a direct link to track your package. You can also check your order status anytime by visiting our Order Tracking page or by contacting us with your order number. We ship with major carriers including USPS, UPS, and FedEx.', 'skyyrose' ),
	),
	array(
		'question' => __( 'What sizes do you carry?', 'skyyrose' ),
		'answer'   => __( 'Most of our pieces are available in sizes XS through XXL. Each product page includes a detailed size guide with measurements for chest, waist, hips, and length. We recommend measuring yourself and comparing to our size charts for the best fit. If you are between sizes, we suggest sizing up for a relaxed fit or down for a more tailored look. Need help? Our styling team is always happy to assist.', 'skyyrose' ),
	),
	array(
		'question' => __( 'Are your products sustainable?', 'skyyrose' ),
		'answer'   => __( 'Sustainability is at the heart of what we do. We use premium, ethically sourced materials including organic cotton, recycled polyester, and responsibly produced hardware. Our limited production runs minimize waste, and we partner with manufacturers who uphold fair labor practices. We are continuously working to reduce our environmental footprint through eco-friendly packaging and carbon-offset shipping options.', 'skyyrose' ),
	),
	array(
		'question' => __( 'Do you do collaborations?', 'skyyrose' ),
		'answer'   => __( "Absolutely! We love partnering with artists, designers, influencers, and brands that share our vision. Whether you're interested in a co-designed capsule, a content collaboration, or a brand partnership, we want to hear from you. Select \"Collaboration\" in the contact form and share your portfolio or social links along with your idea. Our creative team reviews every submission.", 'skyyrose' ),
	),
	array(
		'question' => __( 'How can I join the SkyyRose community?', 'skyyrose' ),
		'answer'   => __( 'There are many ways to be part of the SkyyRose family! Follow us on Instagram, TikTok, and Twitter @skyyrose for the latest drops, behind-the-scenes content, and styling inspiration. Sign up for our newsletter to get early access to new collections and exclusive member discounts. We also host pop-up events in Oakland and other cities throughout the year, so stay tuned for invitations.', 'skyyrose' ),
	),
);
?>

<main id="primary" class="site-main contact-page" role="main" tabindex="-1">

	<!-- Film Grain Overlay -->
	<div class="film-grain" aria-hidden="true"></div>

	<!-- Page Header -->
	<section class="contact-hero" aria-labelledby="contact-hero-title">
		<div class="contact-hero__container">
			<div class="contact-hero__decorative" aria-hidden="true">
				<span class="contact-hero__line contact-hero__line--left"></span>
				<svg class="contact-hero__diamond" width="16" height="16" viewBox="0 0 16 16" fill="none">
					<rect x="8" y="0" width="11.3" height="11.3" rx="1" transform="rotate(45 8 0)" stroke="currentColor" stroke-width="1"/>
				</svg>
				<span class="contact-hero__line contact-hero__line--right"></span>
			</div>
			<h1 id="contact-hero-title" class="contact-hero__title">
				<?php esc_html_e( "We'd Love to Hear From You", 'skyyrose' ); ?>
			</h1>
			<p class="contact-hero__subtitle">
				<?php esc_html_e( 'Whether you have a question about our collections, need styling advice, want to explore a collaboration, or just want to say hello, the SkyyRose community is here for you. Every message matters to us.', 'skyyrose' ); ?>
			</p>
		</div>
	</section>

	<!-- Contact Section: 2-Column Layout -->
	<section class="contact-section" aria-label="<?php esc_attr_e( 'Contact Information and Form', 'skyyrose' ); ?>">
		<div class="contact-section__container">

			<!-- Left Column: Contact Info Cards -->
			<div class="contact-info">
				<h2 class="contact-info__heading">
					<?php esc_html_e( 'Contact Information', 'skyyrose' ); ?>
				</h2>

				<?php foreach ( $contact_cards as $card ) : ?>
					<div class="contact-card">
						<div class="contact-card__icon" aria-hidden="true">
							<?php echo wp_kses( $card['icon'], skyyrose_svg_kses_allowed() ); ?>
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
						<?php esc_html_e( 'Follow Us', 'skyyrose' ); ?>
					</h3>
					<p class="contact-social__description">
						<?php esc_html_e( 'Stay connected with the SkyyRose community for drops, styling tips, and behind-the-scenes content.', 'skyyrose' ); ?>
					</p>
					<div class="contact-social__links">
						<?php foreach ( $social_links as $social ) : ?>
							<a
								href="<?php echo esc_url( $social['url'] ); ?>"
								class="contact-social__link"
								target="_blank"
								rel="noopener noreferrer"
								aria-label="<?php echo esc_attr( sprintf( __( 'Follow SkyyRose on %s', 'skyyrose' ), $social['name'] ) ); ?>"
							>
								<span class="contact-social__link-icon" aria-hidden="true">
									<?php echo wp_kses( $social['icon'], skyyrose_svg_kses_allowed() ); ?>
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
			<?php
			get_template_part(
				'template-parts/contact/form',
				null,
				array(
					'subject_options'  => $subject_options,
					'referral_options' => $referral_options,
				)
			);
			?>

		</div>
	</section>

	<!-- Response Promise Section -->
	<section class="response-promise" aria-label="<?php esc_attr_e( 'Our Response Promise', 'skyyrose' ); ?>">
		<div class="response-promise__container">
			<div class="response-promise__icon" aria-hidden="true">
				<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10"/>
					<polyline points="12 6 12 12 16 14"/>
				</svg>
			</div>
			<h2 class="response-promise__title">
				<?php esc_html_e( 'We Typically Respond Within 24 Hours', 'skyyrose' ); ?>
			</h2>
			<p class="response-promise__text">
				<?php esc_html_e( 'Our team reads every message personally. You will hear back from a real person, not a bot.', 'skyyrose' ); ?>
			</p>
			<div class="response-promise__channels">
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Email', 'skyyrose' ); ?>
					</span>
				</div>
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="3.5"/><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Instagram DM', 'skyyrose' ); ?>
					</span>
				</div>
				<div class="response-promise__channel">
					<div class="response-promise__channel-icon" aria-hidden="true">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
					</div>
					<span class="response-promise__channel-label">
						<?php esc_html_e( 'Live Chat', 'skyyrose' ); ?>
					</span>
				</div>
			</div>
		</div>
	</section>

	<!-- FAQ Accordion Section -->
	<?php
	get_template_part(
		'template-parts/contact/faq-list',
		null,
		array(
			'faq_items' => $faq_items,
		)
	);
	?>

	<!-- Map Section -->
	<section class="contact-map" aria-label="<?php esc_attr_e( 'Our Location', 'skyyrose' ); ?>">
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
						<?php esc_html_e( 'SkyyRose Showroom', 'skyyrose' ); ?>
					</h3>
					<p class="contact-map__address">
						<?php echo esc_html( $showroom_line_1 ); ?><br>
						<?php echo esc_html( $showroom_line_2 ); ?>
					</p>
					<p class="contact-map__hours">
						<?php esc_html_e( 'Mon-Fri 9AM-6PM PST | Sat 10AM-4PM', 'skyyrose' ); ?>
					</p>
					<a
						href="<?php echo esc_url( 'https://www.google.com/maps/search/?api=1&query=Oakland+CA+94612' ); ?>"
						class="contact-map__directions"
						target="_blank"
						rel="noopener noreferrer"
					>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M18 8L22 12L18 16"/>
							<path d="M2 12H22"/>
						</svg>
						<?php esc_html_e( 'Get Directions', 'skyyrose' ); ?>
					</a>
				</div>
			</div>
		</div>
	</section>

</main><!-- #primary -->

<?php
get_footer();
