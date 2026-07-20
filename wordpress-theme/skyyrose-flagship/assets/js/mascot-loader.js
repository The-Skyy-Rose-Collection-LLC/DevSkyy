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
 * Wave 6 (round-5 evidence): the previous idle gate used a 4s
 * requestIdleCallback timeout with no load-event dependency, which fired
 * INSIDE the throttled-mobile load window — skyy-3d's three.js import then
 * cost ~950ms of main-thread (wishlist 92→77, TBT ~375ms). The idle
 * countdown now starts only after `load`, and the rIC timeout is long: a
 * timeout-forced fire is the she-must-appear guarantee, not the normal
 * path — genuine idle (≈ post-TTI) is.
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

	// Post-load timings: rIC's timeout is deliberately long — it exists only
	// to guarantee appearance, so the normal fire is a REAL idle period
	// (after TTI), keeping three.js evaluation out of the Lighthouse TBT
	// window. Old-browser fallback waits a beat after load instead.
	var POST_LOAD_IDLE_TIMEOUT_MS = 8000;
	var FALLBACK_TIMEOUT_MS       = 3000;
	var INTERACTION_EVENTS        = [ 'pointerdown', 'keydown', 'touchstart', 'scroll' ];

	function bindInteractionTriggers() {
		INTERACTION_EVENTS.forEach( function ( eventName ) {
			window.addEventListener( eventName, loadMascot, { once: true, passive: true } );
		} );
	}

	function scheduleIdleLoad() {
		if ( 'requestIdleCallback' in window ) {
			window.requestIdleCallback( loadMascot, { timeout: POST_LOAD_IDLE_TIMEOUT_MS } );
		} else {
			setTimeout( loadMascot, FALLBACK_TIMEOUT_MS );
		}
	}

	// Real user input is an immediate, genuine signal — keep the fast path.
	// (Lab runs have no input, so this never re-enters the audit window.)
	bindInteractionTriggers();

	if ( 'complete' === document.readyState ) {
		scheduleIdleLoad();
	} else {
		window.addEventListener( 'load', scheduleIdleLoad, { once: true } );
	}
} )();
