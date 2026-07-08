/**
 * Skyy Mascot — Idle-Time Loader
 *
 * Perf budget (non-negotiable, mascot system scope Pillar 3): the mascot
 * bundle must not cost any LCP/CLS budget. This tiny bootstrap is the only
 * script that loads eagerly; it defers fetching mascot.min.js (and
 * skyy-3d.min.js, when a GLB is configured) until the browser is idle AND
 * the page has had a first interaction — whichever comes first, with a
 * fallback timeout so the character still appears on pages nobody scrolls
 * or touches.
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

	function loadMascot() {
		if ( loaded ) {
			return;
		}
		loaded = true;

		injectScript( config.mascotUrl );
		if ( config.skyy3dUrl ) {
			injectScript( config.skyy3dUrl );
		}
	}

	var FALLBACK_TIMEOUT_MS = 5000;
	var IDLE_TIMEOUT_MS     = 4000;
	var INTERACTION_EVENTS  = [ 'pointerdown', 'keydown', 'touchstart', 'scroll' ];

	function bindInteractionTriggers() {
		INTERACTION_EVENTS.forEach( function ( eventName ) {
			window.addEventListener( eventName, loadMascot, { once: true, passive: true } );
		} );
	}

	bindInteractionTriggers();

	if ( 'requestIdleCallback' in window ) {
		window.requestIdleCallback( loadMascot, { timeout: IDLE_TIMEOUT_MS } );
	} else {
		setTimeout( loadMascot, FALLBACK_TIMEOUT_MS );
	}
} )();
