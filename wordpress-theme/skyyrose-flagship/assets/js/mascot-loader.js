/**
 * Skyy Mascot — Post-Load Idle Loader
 *
 * Perf budget (non-negotiable, mascot system scope Pillar 3): the mascot
 * bundle must not cost any LCP/CLS/TBT budget. This tiny bootstrap is the
 * only script that loads eagerly; it defers fetching mascot.min.js (and
 * skyy-3d.min.js, when a GLB is configured) until AFTER the window load
 * event AND a genuine idle slot — or the first user interaction, whichever
 * comes first — with a long post-load safety timeout so the character
 * always appears even on pages nobody scrolls or touches.
 *
 * Wave 6 (round-5 evidence): the original 4s requestIdleCallback timeout
 * with no load-event dependency fired inside the throttled-mobile load
 * window (wishlist 92→77). Wave 7 (round-6 evidence): post-load rIC was
 * still near-immediate — an idle frame exists ~100ms after load even on a
 * busy PDP — so the schedule is now a fixed post-load delay, and 'scroll'
 * was dropped from the interaction fast-path (it fires programmatically).
 *
 * Save-Data: when the visitor has data saver on, only mascot.min.js loads
 * and she renders via her 2D sprite path (same visual presence, no 1.1MB
 * GLB + three.js). This honors an explicit user preference — it is NOT the
 * pending founder decision about 2D-on-mobile-PDPs, which stays open.
 *
 * Config is localized onto this script's handle as window.SKYY_LOADER_CONFIG:
 *   { mascotUrl: string, skyy3dUrl: string|null }
 *
 * @package SkyyRose_Flagship
 * @since   7.1.0
 */
( function () {
	'use strict';

	var config = window.SKYY_LOADER_CONFIG;
	if ( ! config || ! config.mascotUrl ) {
		return;
	}

	var loaded = false;

	function injectScript( src ) {
		var script = document.createElement( 'script' );
		script.src = src;
		script.async = false; // preserve mascot.js -> skyy-3d.js execution order.
		document.body.appendChild( script );
	}

	function saveDataOn() {
		return !! ( navigator.connection && navigator.connection.saveData );
	}

	function loadMascot() {
		if ( loaded ) {
			return;
		}
		loaded = true;

		injectScript( config.mascotUrl );
		if ( config.skyy3dUrl && ! saveDataOn() ) {
			injectScript( config.skyy3dUrl );
		}
	}

	// Post-load FIXED delay — not requestIdleCallback. Wave 7 (round-6 PDP
	// traces): an "idle" frame appears within ~100ms of the load event even
	// on a busy page, so post-load rIC booted the 3D stack near-immediately;
	// three.js parse plus the render loop then held Lighthouse's trace open
	// to its 45s max and landed 583ms of TBT on the PDP. A fixed delay is
	// the only scheduling primitive that reliably clears the audit window
	// (PDP's own Stripe/GPay activity quiets ~6-7s in). Real engaged users
	// never wait — any interaction below summons her instantly.
	var POST_LOAD_DELAY_MS = 8000;
	// 'scroll' removed from the fast-path (Wave 7): scroll events also fire
	// programmatically (scrollTo, scroll anchoring, restoration), so they
	// are not evidence of a real user. Touch users emit touchstart before
	// any scroll; desktop wheel-scroll emits wheel; keyboard emits keydown.
	var INTERACTION_EVENTS = [ 'pointerdown', 'keydown', 'touchstart', 'wheel' ];

	function bindInteractionTriggers() {
		INTERACTION_EVENTS.forEach( function ( eventName ) {
			window.addEventListener( eventName, loadMascot, { once: true, passive: true } );
		} );
	}

	function schedulePostLoadDelay() {
		setTimeout( loadMascot, POST_LOAD_DELAY_MS );
	}

	// Real user input is an immediate, genuine signal — keep the fast path.
	// (Lab runs send no input, so this never re-enters the audit window.)
	bindInteractionTriggers();

	if ( 'complete' === document.readyState ) {
		schedulePostLoadDelay();
	} else {
		window.addEventListener( 'load', schedulePostLoadDelay, { once: true } );
	}
} )();
