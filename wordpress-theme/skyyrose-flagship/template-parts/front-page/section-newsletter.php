<?php
/**
 * Front Page: Newsletter Signup
 *
 * Email signup form with incentive and privacy link.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>

<section class="newsletter" aria-labelledby="newsletter-heading">
	<div class="newsletter__content">
		<span class="section-header__label">
			<?php esc_html_e( 'Stay Connected', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="newsletter__heading" id="newsletter-heading">
			<?php esc_html_e( 'Join the SkyyRose Family', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="newsletter__incentive">
			<?php esc_html_e( 'Get 15% off your first order', 'skyyrose-flagship' ); ?>
		</p>
		<p class="newsletter__text">
			<?php esc_html_e( 'Be the first to know about new drops, exclusive offers, and behind-the-scenes content. No spam, ever. Just luxury in your inbox.', 'skyyrose-flagship' ); ?>
		</p>

		<form class="newsletter__form js-newsletter-form" method="post" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
			<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
			<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">

			<label for="newsletter-email" class="screen-reader-text">
				<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
			</label>
			<input
				type="email"
				id="newsletter-email"
				name="email"
				class="newsletter__input"
				placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
				required
				autocomplete="email"
			>
			<button type="submit" class="btn btn--primary newsletter__submit">
				<?php esc_html_e( 'Subscribe', 'skyyrose-flagship' ); ?>
			</button>
		</form>

		<div class="newsletter__feedback" aria-live="polite" role="status"></div>

		<p class="newsletter__privacy">
			<?php
			echo wp_kses(
				sprintf(
					/* translators: %s: URL to privacy policy page */
					__( 'By subscribing, you agree to our <a href="%s">Privacy Policy</a>. Unsubscribe anytime.', 'skyyrose-flagship' ),
					esc_url( home_url( '/privacy-policy/' ) )
				),
				array(
					'a' => array( 'href' => array() ),
				)
			);
			?>
		</p>
	</div>
</section>
