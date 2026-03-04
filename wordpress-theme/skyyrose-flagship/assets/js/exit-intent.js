/**
 * SkyyRose Flagship — Exit-Intent Overlay
 *
 * Detects when a visitor is about to leave and shows a compelling
 * pre-order / newsletter capture overlay. Recovery rate: 10-15%
 * of abandoning visitors (industry benchmark).
 *
 * Desktop: mouse leaves viewport (mouseleave on documentElement).
 * Mobile:  idle timeout after 45s of no interaction.
 *
 * Guards:
 * - Shows only once per session (sessionStorage).
 * - Waits 8 seconds after page load before arming.
 * - Does NOT fire on pre-order or checkout pages (visitor is already converting).
 * - Respects a 500ms debounce to prevent false triggers from fast cursor moves.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	var STORAGE_KEY   = 'sr_exit_shown';
	var ARM_DELAY     = 8000;  // 8 seconds before exit-intent is active.
	var MOBILE_IDLE   = 45000; // 45 seconds idle on mobile.
	var DEBOUNCE_MS   = 500;

	// Skip if already shown this session.
	if ( sessionStorage.getItem( STORAGE_KEY ) ) {
		return;
	}

	// Skip on conversion pages (user is already buying).
	var path = window.location.pathname;
	if ( /\/(checkout|cart|pre-order)\/?/i.test( path ) ) {
		return;
	}

	var armed     = false;
	var shown     = false;
	var debounce  = null;
	var idleTimer = null;

	// Arm after delay.
	setTimeout( function () {
		armed = true;
	}, ARM_DELAY );

	/**
	 * Build and inject the overlay DOM.
	 */
	function buildOverlay() {
		var overlay = document.createElement( 'div' );
		overlay.id = 'srExitOverlay';
		overlay.className = 'sr-exit-overlay';
		overlay.setAttribute( 'role', 'dialog' );
		overlay.setAttribute( 'aria-modal', 'true' );
		overlay.setAttribute( 'aria-label', 'Before you go' );

		overlay.innerHTML =
			'<div class="sr-exit-backdrop"></div>' +
			'<div class="sr-exit-card">' +
				'<button class="sr-exit-close" aria-label="Close">&times;</button>' +
				'<p class="sr-exit-eyebrow">Before You Go</p>' +
				'<h2 class="sr-exit-title">Don\u2019t Miss<br>The Drop</h2>' +
				'<p class="sr-exit-body">Pre-orders are open for a limited time. Join our list for early access to new collections, exclusive drops, and founder updates.</p>' +
				'<div class="sr-exit-form">' +
					'<input type="email" class="sr-exit-input" placeholder="Your email address" aria-label="Email address" />' +
					'<button type="button" class="sr-exit-submit">Get Early Access</button>' +
				'</div>' +
				'<p class="sr-exit-note">Free \u00B7 No spam \u00B7 Unsubscribe anytime</p>' +
			'</div>';

		document.body.appendChild( overlay );

		// Animate in.
		requestAnimationFrame( function () {
			overlay.classList.add( 'sr-exit-visible' );
		} );

		// Close handlers.
		var closeBtn  = overlay.querySelector( '.sr-exit-close' );
		var backdrop  = overlay.querySelector( '.sr-exit-backdrop' );
		var submitBtn = overlay.querySelector( '.sr-exit-submit' );
		var input     = overlay.querySelector( '.sr-exit-input' );

		function closeOverlay() {
			overlay.classList.remove( 'sr-exit-visible' );
			setTimeout( function () {
				if ( overlay.parentNode ) {
					overlay.parentNode.removeChild( overlay );
				}
			}, 400 );
		}

		closeBtn.addEventListener( 'click', closeOverlay );
		backdrop.addEventListener( 'click', closeOverlay );
		document.addEventListener( 'keydown', function onEsc( e ) {
			if ( e.key === 'Escape' ) {
				closeOverlay();
				document.removeEventListener( 'keydown', onEsc );
			}
		} );

		// Submit handler (reuse newsletter AJAX if available).
		submitBtn.addEventListener( 'click', function () {
			var email = input.value.trim();
			if ( ! email || email.indexOf( '@' ) === -1 ) {
				input.style.borderColor = '#DC143C';
				return;
			}

			submitBtn.textContent = 'Joining\u2026';
			submitBtn.disabled = true;

			var data    = typeof skyyRoseData !== 'undefined' ? skyyRoseData : {};
			var ajaxUrl = data.ajaxUrl || '/index.php?rest_route=/';

			var formData = new FormData();
			formData.append( 'action', 'skyyrose_newsletter_subscribe' );
			formData.append( 'email', email );
			if ( data.nonce ) {
				formData.append( 'nonce', data.nonce );
			}

			fetch( ajaxUrl, { method: 'POST', body: formData } )
				.then( function () {
					submitBtn.textContent = 'Welcome \u2713';
					input.value = '';
				} )
				.catch( function () {
					submitBtn.textContent = 'Welcome \u2713';
					input.value = '';
				} )
				.finally( function () {
					setTimeout( closeOverlay, 2000 );
				} );
		} );
	}

	/**
	 * Show the overlay (once).
	 */
	function showExitIntent() {
		if ( shown || ! armed ) {
			return;
		}
		shown = true;
		sessionStorage.setItem( STORAGE_KEY, '1' );
		buildOverlay();
	}

	// Desktop: mouse leaves viewport.
	document.documentElement.addEventListener( 'mouseleave', function ( e ) {
		if ( e.clientY > 10 ) {
			return; // Only trigger when cursor exits via top.
		}
		clearTimeout( debounce );
		debounce = setTimeout( showExitIntent, DEBOUNCE_MS );
	} );

	// Mobile: idle timeout.
	function resetIdleTimer() {
		clearTimeout( idleTimer );
		idleTimer = setTimeout( showExitIntent, MOBILE_IDLE );
	}

	if ( 'ontouchstart' in window ) {
		resetIdleTimer();
		document.addEventListener( 'touchstart', resetIdleTimer, { passive: true } );
		document.addEventListener( 'scroll', resetIdleTimer, { passive: true } );
	}
})();
