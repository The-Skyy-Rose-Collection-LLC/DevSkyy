<?php
/**
 * The template for displaying the footer
 *
 * 5-column grid footer with brand column, navigation columns,
 * newsletter signup bar, and copyright.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

?>

	</div><!-- #content -->

	<footer id="colophon" class="site-footer" role="contentinfo">

		<!-- Newsletter Signup Bar -->
		<div class="footer-newsletter">
			<div class="footer-newsletter__container">
				<div class="footer-newsletter__content">
					<h3 class="footer-newsletter__title">
						<?php esc_html_e( 'Join the Inner Circle', 'skyyrose-flagship' ); ?>
					</h3>
					<p class="footer-newsletter__text">
						<?php esc_html_e( 'Exclusive drops, early access, and luxury delivered to your inbox.', 'skyyrose-flagship' ); ?>
					</p>
				</div>
				<form class="footer-newsletter__form" action="<?php echo esc_url( home_url( '/' ) ); ?>" method="post" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
					<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
					<div class="footer-newsletter__input-group">
						<label for="footer-newsletter-email" class="screen-reader-text">
							<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
						</label>
						<input
							type="email"
							id="footer-newsletter-email"
							name="newsletter_email"
							class="footer-newsletter__input"
							placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
							required
							autocomplete="email"
						>
						<button type="submit" class="footer-newsletter__submit" name="skyyrose_newsletter_submit">
							<?php esc_html_e( 'Subscribe', 'skyyrose-flagship' ); ?>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M5 12h14"/>
								<path d="m12 5 7 7-7 7"/>
							</svg>
						</button>
					</div>
				</form>
			</div>
		</div>

		<!-- 5-Column Footer Grid -->
		<div class="footer-grid">
			<div class="footer-grid__container">

				<!-- Column 1: Brand (2fr) -->
				<div class="footer-grid__col footer-grid__col--brand">
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="footer-brand__logo-link" rel="home">
						<img
							src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/sr-monogram.png' ); ?>"
							alt="<?php esc_attr_e( 'SR Monogram', 'skyyrose-flagship' ); ?>"
							class="footer-brand__monogram"
							width="40"
							height="40"
							loading="lazy"
						>
						<span class="footer-brand__text navbar__gradient-text"><?php esc_html_e( 'SKYY ROSE', 'skyyrose-flagship' ); ?></span>
					</a>
					<p class="footer-brand__tagline">
						<?php esc_html_e( 'Where Love Meets Luxury', 'skyyrose-flagship' ); ?>
					</p>
					<p class="footer-brand__description">
						<?php esc_html_e( 'Premium fashion collections crafted with passion, designed for those who dare to express their truth.', 'skyyrose-flagship' ); ?>
					</p>
					<div class="footer-brand__social" aria-label="<?php esc_attr_e( 'Social Media Links', 'skyyrose-flagship' ); ?>">
						<?php
						$social_links = array(
							'instagram' => array(
								'url'   => 'https://instagram.com/theskyyrosecollection',
								'label' => __( 'Instagram', 'skyyrose-flagship' ),
								'icon'  => '<path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2Z"/><circle cx="12" cy="12" r="3.5"/><circle cx="17.5" cy="6.5" r="0.5" fill="currentColor"/>',
							),
							'tiktok'    => array(
								'url'   => 'https://tiktok.com/@skyyrosecollection',
								'label' => __( 'TikTok', 'skyyrose-flagship' ),
								'icon'  => '<path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"/>',
							),
							'twitter'   => array(
								'url'   => 'https://twitter.com/skyyrosellc',
								'label' => __( 'X (Twitter)', 'skyyrose-flagship' ),
								'icon'  => '<path d="M4 4l11.733 16h4.267l-11.733 -16z"/><path d="M4 20l6.768 -6.768m2.46 -2.46l6.772 -6.772"/>',
							),
							'facebook'  => array(
								'url'   => 'https://facebook.com/skyyrosecollection',
								'label' => __( 'Facebook', 'skyyrose-flagship' ),
								'icon'  => '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
							),
						);

						foreach ( $social_links as $platform => $data ) :
							?>
							<a
								href="<?php echo esc_url( $data['url'] ); ?>"
								class="footer-brand__social-link footer-brand__social-link--<?php echo esc_attr( $platform ); ?>"
								aria-label="<?php echo esc_attr( $data['label'] ); ?>"
								target="_blank"
								rel="noopener noreferrer"
							>
								<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
									<?php echo $data['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- SVG markup. ?>
								</svg>
							</a>
						<?php endforeach; ?>
					</div>
				</div>

				<!-- Column 2: Shop (1fr) -->
				<div class="footer-grid__col footer-grid__col--shop">
					<h4 class="footer-grid__heading"><?php esc_html_e( 'Shop', 'skyyrose-flagship' ); ?></h4>
					<ul class="footer-grid__list">
						<li><a href="<?php echo esc_url( home_url( '/collection/black-rose/' ) ); ?>"><?php esc_html_e( 'Black Rose', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/collection/love-hurts/' ) ); ?>"><?php esc_html_e( 'Love Hurts', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/collection/signature/' ) ); ?>"><?php esc_html_e( 'Signature', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/collection/kids-capsule/' ) ); ?>"><?php esc_html_e( 'Kids Capsule', 'skyyrose-flagship' ); ?></a></li>
						<?php if ( class_exists( 'WooCommerce' ) ) : ?>
							<li><a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'All Products', 'skyyrose-flagship' ); ?></a></li>
						<?php endif; ?>
					</ul>
				</div>

				<!-- Column 3: Help (1fr) -->
				<div class="footer-grid__col footer-grid__col--help">
					<h4 class="footer-grid__heading"><?php esc_html_e( 'Help', 'skyyrose-flagship' ); ?></h4>
					<ul class="footer-grid__list">
						<li><a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><?php esc_html_e( 'Contact Us', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>"><?php esc_html_e( 'FAQ', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/shipping/' ) ); ?>"><?php esc_html_e( 'Shipping & Returns', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>"><?php esc_html_e( 'Size Guide', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/care-instructions/' ) ); ?>"><?php esc_html_e( 'Care Instructions', 'skyyrose-flagship' ); ?></a></li>
					</ul>
				</div>

				<!-- Column 4: Legal (1fr) -->
				<div class="footer-grid__col footer-grid__col--legal">
					<h4 class="footer-grid__heading"><?php esc_html_e( 'Legal', 'skyyrose-flagship' ); ?></h4>
					<ul class="footer-grid__list">
						<li><a href="<?php echo esc_url( home_url( '/privacy-policy/' ) ); ?>"><?php esc_html_e( 'Privacy Policy', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/terms-of-service/' ) ); ?>"><?php esc_html_e( 'Terms of Service', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/refund-policy/' ) ); ?>"><?php esc_html_e( 'Refund Policy', 'skyyrose-flagship' ); ?></a></li>
						<li><a href="<?php echo esc_url( home_url( '/accessibility/' ) ); ?>"><?php esc_html_e( 'Accessibility', 'skyyrose-flagship' ); ?></a></li>
					</ul>
				</div>

				<!-- Column 5: Social / Connect (1fr) -->
				<div class="footer-grid__col footer-grid__col--social">
					<h4 class="footer-grid__heading"><?php esc_html_e( 'Connect', 'skyyrose-flagship' ); ?></h4>
					<ul class="footer-grid__list">
						<li>
							<a href="https://instagram.com/theskyyrosecollection" target="_blank" rel="noopener noreferrer">
								<?php esc_html_e( 'Instagram', 'skyyrose-flagship' ); ?>
							</a>
						</li>
						<li>
							<a href="https://tiktok.com/@skyyrosecollection" target="_blank" rel="noopener noreferrer">
								<?php esc_html_e( 'TikTok', 'skyyrose-flagship' ); ?>
							</a>
						</li>
						<li>
							<a href="https://twitter.com/skyyrosellc" target="_blank" rel="noopener noreferrer">
								<?php esc_html_e( 'X (Twitter)', 'skyyrose-flagship' ); ?>
							</a>
						</li>
						<li>
							<a href="https://facebook.com/skyyrosecollection" target="_blank" rel="noopener noreferrer">
								<?php esc_html_e( 'Facebook', 'skyyrose-flagship' ); ?>
							</a>
						</li>
						<li>
							<a href="https://pinterest.com/skyyrosecollection" target="_blank" rel="noopener noreferrer">
								<?php esc_html_e( 'Pinterest', 'skyyrose-flagship' ); ?>
							</a>
						</li>
					</ul>
				</div>

			</div><!-- .footer-grid__container -->
		</div><!-- .footer-grid -->

		<!-- Copyright Bar -->
		<div class="footer-copyright">
			<div class="footer-copyright__container">
				<p class="footer-copyright__text">
					<?php
					printf(
						/* translators: %s: Year */
						esc_html__( '&copy; 2024 The Skyy Rose Collection LLC. All rights reserved.', 'skyyrose-flagship' )
					);
					?>
				</p>
				<?php if ( has_nav_menu( 'footer' ) ) : ?>
					<nav class="footer-copyright__nav" aria-label="<?php esc_attr_e( 'Footer Legal Navigation', 'skyyrose-flagship' ); ?>">
						<?php
						wp_nav_menu(
							array(
								'theme_location'  => 'footer',
								'menu_id'         => 'footer-legal-menu',
								'menu_class'      => 'footer-copyright__menu',
								'container'       => false,
								'depth'           => 1,
								'fallback_cb'     => false,
							)
						);
						?>
					</nav>
				<?php endif; ?>
			</div>
		</div><!-- .footer-copyright -->

	</footer><!-- #colophon -->
</div><!-- #page -->

<!-- Toast Notification Container -->
<div id="toast-container" class="toast-container" aria-live="polite" aria-atomic="true"></div>

<!-- Luxury Cursor (desktop only, hidden from assistive tech) -->
<div class="luxury-cursor" aria-hidden="true">
	<div class="luxury-cursor__dot"></div>
</div>
<div class="luxury-cursor__trail" aria-hidden="true"></div>

<?php wp_footer(); ?>

</body>
</html>
