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
	hidden
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
	// The [hidden] attribute keeps the banner invisible BEFORE the (deferred)
	// stylesheet arrives. cookie-consent.css loads via the print-media swap, so
	// on a cold first visit this script can run BEFORE the sheet applies —
	// revealing then would paint the banner unstyled in-flow (then snap to the
	// fixed bar). Gate the reveal on the sheet being live: .cookie-consent only
	// computes position:fixed once cookie-consent.css has applied. Dismiss
	// paths re-hide via the CSS class so the slide-out transition still plays.
	function reveal() {
		banner.removeAttribute( 'hidden' );
		banner.classList.remove( 'cookie-consent--hidden' );
		// Clearance contract: while the banner is visible, <html> carries this
		// class so fixed bottom widgets (mascot, recall pill) read
		// --skyyrose-consent-clearance and lift above the banner instead of
		// being covered by it (cookie-consent.css defines the var).
		document.documentElement.classList.add( 'skyyrose-consent-open' );
		// Move focus to accept button so keyboard users reach the dialog immediately.
		setTimeout( function() { accept.focus( { preventScroll: true } ); }, 100 );
	}
	function sheetLive() {
		return 'fixed' === window.getComputedStyle( banner ).position;
	}
	if ( sheetLive() ) {
		reveal();
	} else {
		var revealed = false;
		var go = function() { if ( ! revealed ) { revealed = true; reveal(); } };
		var link = document.getElementById( 'skyyrose-cookie-consent-css' );
		if ( link ) { link.addEventListener( 'load', go ); }
		// rAF poll with a 3s cap: worst case (sheet blocked entirely) degrades
		// to the pre-gate behavior instead of never showing the legally
		// required banner.
		var t0 = Date.now();
		( function poll() {
			if ( revealed ) return;
			if ( sheetLive() || Date.now() - t0 > 3000 ) { go(); return; }
			requestAnimationFrame( poll );
		} )();
	}
	function dismiss( value ) {
		localStorage.setItem( 'skyyrose_cookie_consent', value );
		banner.classList.add( 'cookie-consent--hidden' );
		document.documentElement.classList.remove( 'skyyrose-consent-open' );
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
