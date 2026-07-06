<?php
/**
 * GDPR Cookie Consent Banner
 *
 * Minimal dark luxury consent bar fixed to viewport bottom.
 * Checks localStorage — if consent already recorded, nothing renders.
 *
 * @package SkyyRose
 * @since   6.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$cookie_privacy_url = home_url( '/privacy-policy/' );
?>

<div id="skyyrose-cookie-consent"
	class="cookie-consent cookie-consent--hidden"
	role="dialog"
	aria-modal="true"
	aria-label="<?php esc_attr_e( 'Cookie consent', 'skyyrose' ); ?>"
	aria-describedby="cookie-consent-message">
	<p id="cookie-consent-message" class="cookie-consent__message">
		<?php
		printf(
			/* translators: %1$s and %2$s wrap the privacy policy link */
			esc_html__( 'Cookies keep this site fast and personal. Stay to accept, or %1$sread how we handle your data%2$s.', 'skyyrose' ),
			'<a href="' . esc_url( $cookie_privacy_url ) . '" class="cookie-consent__link">',
			'</a>'
		);
		?>
	</p>
	<div class="cookie-consent__actions">
		<button id="skyyrose-cookie-accept" class="cookie-consent__btn cookie-consent__btn--accept" type="button">
			<?php esc_html_e( 'Accept', 'skyyrose' ); ?>
		</button>
		<button id="skyyrose-cookie-decline" class="cookie-consent__btn cookie-consent__btn--decline" type="button">
			<?php esc_html_e( 'Decline', 'skyyrose' ); ?>
		</button>
	</div>
</div>

<script>
(function() {
	if ( localStorage.getItem( 'skyyrose_cookie_consent' ) ) return;
	var banner      = document.getElementById( 'skyyrose-cookie-consent' );
	var accept      = document.getElementById( 'skyyrose-cookie-accept' );
	var decline     = document.getElementById( 'skyyrose-cookie-decline' );
	var returnFocus = document.activeElement || document.body;
	if ( ! banner || ! accept || ! decline ) return;
	banner.classList.remove( 'cookie-consent--hidden' );
	// Move focus to accept button so keyboard users reach the dialog immediately.
	setTimeout( function() { accept.focus( { preventScroll: true } ); }, 100 );
	function dismiss( value ) {
		localStorage.setItem( 'skyyrose_cookie_consent', value );
		banner.classList.add( 'cookie-consent--hidden' );
		// Return focus to where it was before the dialog appeared.
		if ( returnFocus && typeof returnFocus.focus === 'function' ) {
			returnFocus.focus();
		}
	}
	accept.addEventListener( 'click', function() { dismiss( 'accepted' ); } );
	decline.addEventListener( 'click', function() { dismiss( 'declined' ); } );
	// Escape key: treat as decline (hides banner without storing acceptance).
	document.addEventListener( 'keydown', function( e ) {
		if ( e.key === 'Escape' && ! banner.classList.contains( 'cookie-consent--hidden' ) ) {
			dismiss( 'declined' );
		}
	} );
})();
</script>
