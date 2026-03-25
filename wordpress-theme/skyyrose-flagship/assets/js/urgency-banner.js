/**
 * SkyyRose Flagship — Urgency Countdown Banner
 *
 * Displays a sticky mini-bar with a live countdown to the pre-order deadline.
 * Urgency is the #1 conversion driver in e-commerce — showing a real deadline
 * creates authentic FOMO and drives immediate action.
 *
 * Configuration via wp_localize_script (skyyRoseUrgency):
 *   deadline  — ISO 8601 date string (from get_option('skyyrose_preorder_deadline'))
 *   message   — Custom message (default: "Pre-Order closes in")
 *   ctaUrl    — CTA link URL
 *   ctaText   — CTA button text
 *
 * If no deadline is set, the banner does not render.
 * If the deadline has passed, the banner shows "Pre-Orders Closed" without a timer.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	var config = typeof skyyRoseUrgency !== 'undefined' ? skyyRoseUrgency : {};

	// Require a deadline to render.
	if ( ! config.deadline ) {
		return;
	}

	var deadline = new Date( config.deadline ).getTime();

	// Bail if invalid date.
	if ( isNaN( deadline ) ) {
		return;
	}

	var message = config.message || 'Pre-Order closes in';
	var ctaUrl  = config.ctaUrl  || '/pre-order/';
	var ctaText = config.ctaText || 'Shop Now';

	// Build banner DOM.
	var banner = document.createElement( 'div' );
	banner.id = 'srUrgencyBanner';
	banner.className = 'sr-urgency-banner';
	banner.setAttribute( 'role', 'status' );
	banner.setAttribute( 'aria-live', 'polite' );

	banner.innerHTML =
		'<div class="sr-urgency-inner">' +
			'<span class="sr-urgency-msg">' + escapeHtml( message ) + '</span>' +
			'<span class="sr-urgency-timer" id="srUrgencyTimer"></span>' +
			'<a href="' + escapeHtml( ctaUrl ) + '" class="sr-urgency-cta">' + escapeHtml( ctaText ) + '</a>' +
			'<button class="sr-urgency-dismiss" aria-label="Dismiss">&times;</button>' +
		'</div>';

	// Insert at top of body (before all content).
	document.body.insertBefore( banner, document.body.firstChild );

	// Animate in after next frame.
	requestAnimationFrame( function () {
		banner.classList.add( 'sr-urgency-visible' );
	} );

	var timerEl = document.getElementById( 'srUrgencyTimer' );
	var iv      = null;

	/**
	 * Update the countdown display.
	 */
	function tick() {
		var now  = Date.now();
		var diff = deadline - now;

		if ( diff <= 0 ) {
			timerEl.textContent = 'Closed';
			clearInterval( iv );
			return;
		}

		var days  = Math.floor( diff / 86400000 );
		var hours = Math.floor( ( diff % 86400000 ) / 3600000 );
		var mins  = Math.floor( ( diff % 3600000 ) / 60000 );
		var secs  = Math.floor( ( diff % 60000 ) / 1000 );

		var parts = [];
		if ( days > 0 )  parts.push( days + 'd' );
		if ( hours > 0 ) parts.push( hours + 'h' );
		parts.push( mins + 'm' );
		parts.push( secs + 's' );

		timerEl.textContent = parts.join( ' ' );
	}

	tick();
	iv = setInterval( tick, 1000 );

	// Dismiss handler.
	var dismissBtn = banner.querySelector( '.sr-urgency-dismiss' );
	dismissBtn.addEventListener( 'click', function () {
		banner.classList.remove( 'sr-urgency-visible' );
		clearInterval( iv );
		setTimeout( function () {
			if ( banner.parentNode ) {
				banner.parentNode.removeChild( banner );
			}
			// Remove body padding offset.
			document.body.style.paddingTop = '';
		}, 400 );
		// Remember dismissal for this session.
		sessionStorage.setItem( 'sr_urgency_dismissed', '1' );
	} );

	// Don't show if previously dismissed this session.
	if ( sessionStorage.getItem( 'sr_urgency_dismissed' ) ) {
		banner.parentNode.removeChild( banner );
		clearInterval( iv );
		return;
	}

	// Offset body to account for fixed banner height.
	document.body.style.paddingTop = '44px';

	/**
	 * Simple HTML entity escape.
	 */
	function escapeHtml( str ) {
		var div = document.createElement( 'div' );
		div.appendChild( document.createTextNode( str ) );
		return div.innerHTML;
	}
})();
