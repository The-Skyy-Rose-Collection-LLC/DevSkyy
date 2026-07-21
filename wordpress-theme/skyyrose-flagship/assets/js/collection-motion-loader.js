/**
 * Collection Motion — Post-Load Loader
 *
 * Wave 7b (round-6 evidence): gsap (0.9-1.2s) + ScrollTrigger (0.5s) +
 * engine evaluation landed inside the FCP→LCP window on collection pages —
 * the dominant col-hero "render delay" (BR 3,254ms). Everything this chain
 * powers sits BELOW the 100vh hero (the embedded scene layer renders at
 * collection/page.php:184, feature-scroll and the grid further down), so
 * none of it may compete with the hero paint.
 *
 * Same timing doctrine as mascot-loader.js: first real interaction summons
 * the chain instantly (a scrolling user emits wheel/touchstart the moment
 * they move — i.e. scroll intent), otherwise a fixed 8s-after-load delay
 * boots it outside the audit window. requestIdleCallback is deliberately
 * NOT used — it fires ~100ms after load even on busy pages (Wave 7 lesson).
 *
 * Injection preserves execution order (async=false): gsap → ScrollTrigger →
 * immersive-core → feature-scroll → immersive → wc-bridge. Every script in
 * the chain self-inits when document.readyState is already complete.
 *
 * Config localized as window.SKYY_MOTION_CONFIG = { scripts: string[] }.
 *
 * @package SkyyRose_Flagship
 * @since   1.12.5
 */
( function () {
	'use strict';

	var config = window.SKYY_MOTION_CONFIG;
	if ( ! config || ! config.scripts || ! config.scripts.length ) {
		return;
	}

	var loaded = false;

	function loadChain() {
		if ( loaded ) {
			return;
		}
		loaded = true;
		config.scripts.forEach( function ( src ) {
			var script = document.createElement( 'script' );
			script.src = src;
			script.async = false; // preserve gsap → ScrollTrigger → engines order.
			document.body.appendChild( script );
		} );
	}

	var POST_LOAD_DELAY_MS = 8000;
	var INTERACTION_EVENTS = [ 'pointerdown', 'keydown', 'touchstart', 'wheel' ];

	INTERACTION_EVENTS.forEach( function ( eventName ) {
		window.addEventListener( eventName, loadChain, { once: true, passive: true } );
	} );

	function schedule() {
		setTimeout( loadChain, POST_LOAD_DELAY_MS );
	}

	if ( 'complete' === document.readyState ) {
		schedule();
	} else {
		window.addEventListener( 'load', schedule, { once: true } );
	}
} )();
