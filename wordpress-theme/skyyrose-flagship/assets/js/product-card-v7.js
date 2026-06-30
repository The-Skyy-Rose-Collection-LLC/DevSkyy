/**
 * V7 lookbook card — carousel auto-advance (hover-pauses in place),
 * viewport-gated, + magnetic CTA. Operates on server-rendered markup
 * (no DOM construction, no innerHTML).
 *
 * @package SkyyRose
 */
( function () {
	'use strict';

	var motionQuery = window.matchMedia ? window.matchMedia( '(prefers-reduced-motion: reduce)' ) : null;
	var REDUCE = !! ( motionQuery && motionQuery.matches );
	var ADVANCE_MS = 2800;
	var controllers = [];

	function initCarousel( card ) {
		var shots = Array.prototype.slice.call( card.querySelectorAll( '.v7card__shot' ) );
		var dots  = Array.prototype.slice.call( card.querySelectorAll( '.v7card__dot' ) );
		if ( shots.length <= 1 ) {
			return;
		}
		var idx = 0;
		var timer = null;
		var paused = false;
		var visible = false;

		function show( i ) {
			idx = ( i + shots.length ) % shots.length;
			shots.forEach( function ( s, j ) {
				var active = j === idx;
				if ( active ) {
					s.setAttribute( 'data-active', 'true' );
				} else {
					s.removeAttribute( 'data-active' );
				}
				s.setAttribute( 'aria-hidden', active ? 'false' : 'true' );
			} );
			dots.forEach( function ( d, j ) {
				d.classList.toggle( 'is-on', j === idx );
			} );
		}
		function start() {
			if ( REDUCE || timer || paused || ! visible ) {
				return;
			}
			timer = window.setInterval( function () {
				show( idx + 1 );
			}, ADVANCE_MS );
		}
		function stop() {
			if ( timer ) {
				window.clearInterval( timer );
				timer = null;
			}
		}

		card.addEventListener( 'mouseenter', function () { paused = true; stop(); } );
		card.addEventListener( 'mouseleave', function () { paused = false; start(); } );
		card.addEventListener( 'focusin', function () { paused = true; stop(); } );
		card.addEventListener( 'focusout', function () { paused = false; start(); } );

		if ( 'IntersectionObserver' in window ) {
			var io = new IntersectionObserver( function ( entries ) {
				entries.forEach( function ( e ) {
					visible = e.isIntersecting;
					if ( visible ) {
						start();
					} else {
						stop();
					}
				} );
			}, { threshold: 0 } );
			io.observe( card );
		} else {
			visible = true;
			start();
		}

		controllers.push( { start: start, stop: stop } );
	}

	function initMagnetic( btn ) {
		if ( REDUCE ) {
			return;
		}
		var raf = null;
		var tx = 0;
		var ty = 0;
		var cx = 0;
		var cy = 0;
		function loop() {
			tx += ( cx - tx ) * 0.18;
			ty += ( cy - ty ) * 0.18;
			btn.style.transform = 'translate(' + tx.toFixed( 2 ) + 'px,' + ty.toFixed( 2 ) + 'px)';
			if ( Math.abs( cx - tx ) > 0.1 || Math.abs( cy - ty ) > 0.1 ) {
				raf = window.requestAnimationFrame( loop );
			} else {
				btn.style.transform = 'translate(' + cx + 'px,' + cy + 'px)';
				raf = null;
			}
		}
		btn.addEventListener( 'mousemove', function ( e ) {
			var r = btn.getBoundingClientRect();
			cx = ( e.clientX - ( r.left + r.width / 2 ) ) * 0.35;
			cy = ( e.clientY - ( r.top + r.height / 2 ) ) * 0.45;
			if ( ! raf ) {
				raf = window.requestAnimationFrame( loop );
			}
		} );
		btn.addEventListener( 'mouseleave', function () {
			cx = 0;
			cy = 0;
			if ( ! raf ) {
				raf = window.requestAnimationFrame( loop );
			}
		} );
	}

	function init() {
		Array.prototype.slice.call( document.querySelectorAll( '.v7card' ) ).forEach( initCarousel );
		Array.prototype.slice.call( document.querySelectorAll( '.v7card__add' ) ).forEach( initMagnetic );

		// Pause every carousel in a hidden tab; resume when visible.
		document.addEventListener( 'visibilitychange', function () {
			controllers.forEach( function ( c ) {
				if ( document.hidden ) {
					c.stop();
				} else {
					c.start();
				}
			} );
		} );

		// React to a live change of the reduced-motion preference.
		if ( motionQuery && motionQuery.addEventListener ) {
			motionQuery.addEventListener( 'change', function ( e ) {
				REDUCE = e.matches;
				if ( REDUCE ) {
					controllers.forEach( function ( c ) { c.stop(); } );
				} else {
					controllers.forEach( function ( c ) { c.start(); } );
				}
			} );
		}
	}

	if ( 'loading' === document.readyState ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}
}() );
