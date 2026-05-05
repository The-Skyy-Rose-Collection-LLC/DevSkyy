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
	aria-describedby="skyyrose-cookie-consent-message">
	<p id="skyyrose-cookie-consent-message" class="cookie-consent__message">
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
	var banner  = document.getElementById( 'skyyrose-cookie-consent' );
	var accept  = document.getElementById( 'skyyrose-cookie-accept' );
	var decline = document.getElementById( 'skyyrose-cookie-decline' );
	if ( ! banner || ! accept || ! decline ) return;

	// Remember whatever had focus before the banner appeared so we can
	// restore it on dismiss (WCAG 2.4.3).
	var priorFocus = document.activeElement;

	banner.classList.remove( 'cookie-consent--hidden' );

	// Move focus into the dialog. Accept is the recommended action so
	// it gets the initial focus.
	setTimeout( function() { accept.focus(); }, 0 );

	// Focus trap — Tab and Shift+Tab cycle within the dialog only.
	// The dialog has exactly two interactive controls (accept/decline)
	// plus the optional privacy-policy link, so we look up the
	// focusable list at trap time rather than caching.
	function trapFocus( e ) {
		if ( e.key !== 'Tab' ) return;
		var focusable = banner.querySelectorAll(
			'button, a[href], input, [tabindex]:not([tabindex="-1"])'
		);
		if ( ! focusable.length ) return;
		var first = focusable[ 0 ];
		var last  = focusable[ focusable.length - 1 ];
		if ( e.shiftKey && document.activeElement === first ) {
			e.preventDefault();
			last.focus();
		} else if ( ! e.shiftKey && document.activeElement === last ) {
			e.preventDefault();
			first.focus();
		}
	}

	function dismiss( value ) {
		localStorage.setItem( 'skyyrose_cookie_consent', value );
		banner.classList.add( 'cookie-consent--hidden' );
		document.removeEventListener( 'keydown', onKeydown );
		// Return focus to whatever had it before the dialog appeared.
		if ( priorFocus && typeof priorFocus.focus === 'function' ) {
			priorFocus.focus();
		}
	}

	function onKeydown( e ) {
		if ( e.key === 'Escape' ) {
			// Treat Escape as decline — symmetric with the visible button.
			dismiss( 'declined' );
		} else {
			trapFocus( e );
		}
	}

	document.addEventListener( 'keydown', onKeydown );
	accept.addEventListener( 'click', function() { dismiss( 'accepted' ); } );
	decline.addEventListener( 'click', function() { dismiss( 'declined' ); } );
})();
</script>
