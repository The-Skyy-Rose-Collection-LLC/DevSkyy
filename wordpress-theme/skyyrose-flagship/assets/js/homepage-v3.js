/**
 * Homepage v3 — behaviour for the eight acts.
 *
 * No loader (deleted: a simulated progress bar is a conversion tax and it
 * covered the LCP). No fake newsletter success. No duplicate scroll-progress
 * bar. Every motion path has a reduced-motion branch, and nothing is left
 * hidden when JS never runs — the reveal gate is opt-IN via [data-anim].
 *
 * This file is inlined by front-page.php (page-optimize strips separately
 * enqueued homepage JS on the host), so it must stay dependency-free.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

( function () {
	'use strict';

	var root = document.querySelector( '.homepage-v3' );
	if ( ! root ) {
		return;
	}

	var reduce = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;

	function qsa( sel, ctx ) {
		return Array.prototype.slice.call( ( ctx || document ).querySelectorAll( sel ) );
	}

	/* ── Editorial reveals ──────────────────────────────────────────────────
	   [data-anim] is what arms the hidden state in CSS. Setting it only here,
	   only when motion is welcome, means no-JS and reduced-motion visitors get
	   the finished layout with nothing stranded behind an observer. */
	function initReveals() {
		if ( reduce || ! ( 'IntersectionObserver' in window ) ) {
			return;
		}
		var targets = qsa( '[data-reveal]', root );
		if ( ! targets.length ) {
			return;
		}
		root.setAttribute( 'data-anim', 'on' );
		var io = new IntersectionObserver( function ( entries ) {
			entries.forEach( function ( entry ) {
				if ( ! entry.isIntersecting ) {
					return;
				}
				entry.target.classList.add( 'is-in' );
				io.unobserve( entry.target );
			} );
		}, { threshold: 0.12, rootMargin: '0px 0px -6%' } );
		targets.forEach( function ( el ) {
			io.observe( el );
		} );
	}

	/* ── Act I — hero film ──────────────────────────────────────────────────
	   Same deferral the pre-order gateway hero proved: the clip fetch is held
	   until load + 2.5s (or the first real gesture) so it never competes with
	   the LCP paint. The poster is an identical frame, so nothing visibly
	   changes when playback starts. */
	function initHeroVideo() {
		var video = root.querySelector( '.hp-hero__video' );
		if ( ! video ) {
			return;
		}
		if ( reduce ) {
			// Poster only. Never auto-run a loop when motion is unwelcome.
			return;
		}
		var boot = function () {
			if ( video.dataset.booted ) {
				return;
			}
			video.dataset.booted = '1';
			video.preload = 'auto';
			video.load();
			var attempt = video.play();
			if ( attempt && attempt.catch ) {
				attempt.catch( function () {
					// Autoplay refused (battery saver etc.) — retry once on a gesture.
					document.addEventListener( 'pointerdown', function () {
						video.play().catch( function () {} );
					}, { once: true } );
				} );
			}
		};
		var bootAfterLoad = function () {
			window.setTimeout( boot, 2500 );
		};
		if ( document.readyState === 'complete' ) {
			bootAfterLoad();
		} else {
			window.addEventListener( 'load', bootAfterLoad, { once: true } );
		}
		[ 'pointerdown', 'touchstart', 'wheel', 'keydown' ].forEach( function ( evt ) {
			window.addEventListener( evt, boot, { once: true, passive: true } );
		} );
	}

	/* ── Act II — ticker ────────────────────────────────────────────────────
	   The tracks animate to translateX(-50%), which only loops seamlessly when
	   the content is exactly duplicated AND wider than the viewport. Four large
	   words are narrower than a desktop viewport on their own, so the top tier
	   needs more copies than the bottom one. Clones are marked [data-dup] and
	   hidden from AT and from the reduced-motion static reflow. */
	function initTicker() {
		if ( reduce ) {
			return;
		}
		[ [ '.hp-ticker__track--left', 5 ], [ '.hp-ticker__track--right', 3 ] ].forEach( function ( pair ) {
			var track = root.querySelector( pair[ 0 ] );
			if ( ! track ) {
				return;
			}
			var group = Array.prototype.slice.call( track.children );
			for ( var i = 0; i < pair[ 1 ]; i++ ) {
				group.forEach( function ( node ) {
					var clone = node.cloneNode( true );
					clone.setAttribute( 'data-dup', '' );
					clone.setAttribute( 'aria-hidden', 'true' );
					track.appendChild( clone );
				} );
			}
		} );
	}

	/* ── Act III — the rooms corridor ───────────────────────────────────────
	   Scroll-snap owns the movement; this only mirrors "which room am I in"
	   into the counter and the dots, and adds keyboard paging.

	   "Current" is the room whose centre is nearest the rail's centre, NOT an
	   IntersectionObserver threshold: with full-viewport rooms two of them
	   clear any threshold mid-swipe and whichever callback fires last wins. */
	function initRooms() {
		var rail = root.querySelector( '[data-rooms-rail]' );
		if ( ! rail ) {
			return;
		}
		var rooms = qsa( '[data-room]', rail );
		var dots = qsa( '[data-room-go]', root );
		var now = root.querySelector( '[data-room-now]' );
		if ( ! rooms.length ) {
			return;
		}

		function mark( index ) {
			if ( now ) {
				now.textContent = ( '0' + ( index + 1 ) ).slice( -2 );
			}
			dots.forEach( function ( dot, di ) {
				dot.setAttribute( 'aria-current', String( di === index ) );
			} );
		}

		var ticking = 0;
		function sync() {
			var box = rail.getBoundingClientRect();
			var mid = box.left + box.width / 2;
			var best = 0;
			var bestDist = Infinity;
			rooms.forEach( function ( room, i ) {
				var rect = room.getBoundingClientRect();
				var dist = Math.abs( rect.left + rect.width / 2 - mid );
				if ( dist < bestDist ) {
					bestDist = dist;
					best = i;
				}
			} );
			// The rail clamps at both ends, so on a wide viewport the first and
			// last room can never physically reach the centre — without this the
			// counter reads 02 while you are sitting at the start of the corridor.
			var max = rail.scrollWidth - rail.clientWidth;
			if ( rail.scrollLeft <= 2 ) {
				best = 0;
			} else if ( rail.scrollLeft >= max - 2 ) {
				best = rooms.length - 1;
			}
			mark( best );
		}

		rail.addEventListener( 'scroll', function () {
			if ( ticking ) {
				return;
			}
			ticking = window.requestAnimationFrame( function () {
				ticking = 0;
				sync();
			} );
		}, { passive: true } );
		sync();

		function goTo( index ) {
			var clamped = Math.max( 0, Math.min( rooms.length - 1, index ) );
			rooms[ clamped ].scrollIntoView( {
				behavior: reduce ? 'auto' : 'smooth',
				inline: 'center',
				block: 'nearest',
			} );
		}

		dots.forEach( function ( dot ) {
			dot.addEventListener( 'click', function () {
				goTo( parseInt( dot.getAttribute( 'data-room-go' ), 10 ) );
			} );
		} );

		rail.addEventListener( 'keydown', function ( event ) {
			var current = 0;
			dots.forEach( function ( dot, i ) {
				if ( dot.getAttribute( 'aria-current' ) === 'true' ) {
					current = i;
				}
			} );
			if ( event.key === 'ArrowRight' ) {
				goTo( current + 1 );
				event.preventDefault();
			} else if ( event.key === 'ArrowLeft' ) {
				goTo( current - 1 );
				event.preventDefault();
			}
		} );
	}

	/* ── Act V — press wall ─────────────────────────────────────────────────
	   Pure-CSS marquee. This only pauses it while the tab is hidden and while
	   a wall link holds keyboard focus, so a focused link never scrolls away. */
	function initPressWall() {
		var track = root.querySelector( '.hp-receipts__track' );
		if ( ! track ) {
			return;
		}
		var pause = function ( on ) {
			track.style.animationPlayState = on ? 'paused' : 'running';
		};
		document.addEventListener( 'visibilitychange', function () {
			pause( document.hidden );
		} );
		track.addEventListener( 'focusin', function () {
			pause( true );
		} );
		track.addEventListener( 'focusout', function () {
			pause( false );
		} );
	}

	/* ── Act VI — founder testimony film ────────────────────────────────────
	   Never autoplays on load: it plays only while its own section is on
	   screen (and pauses when it leaves), so it can never contend with the
	   hero's clip or the LCP. Under reduced motion the poster stands and the
	   transport control still works if the visitor asks for it. */
	function initOrigin() {
		var section = root.querySelector( '.hp-origin' );
		if ( ! section ) {
			return;
		}
		var video = section.querySelector( 'video' );
		var btn = section.querySelector( '[data-origin-play]' );
		if ( ! video || ! btn ) {
			return;
		}
		var iconPlay = section.querySelector( '[data-origin-icon="play"]' );
		var iconPause = section.querySelector( '[data-origin-icon="pause"]' );
		var label = section.querySelector( '[data-origin-label]' );
		var manualPause = false;

		// These are SVGElements: `.hidden` is an HTMLElement IDL property, so
		// assigning it silently sets a plain JS prop and never reaches the
		// content attribute. Set the attribute directly.
		function show( el, on ) {
			if ( ! el ) {
				return;
			}
			if ( on ) {
				el.removeAttribute( 'hidden' );
			} else {
				el.setAttribute( 'hidden', '' );
			}
		}

		function sync() {
			var playing = ! video.paused && ! video.ended;
			show( iconPlay, ! playing );
			show( iconPause, playing );
			if ( label ) {
				label.textContent = playing ? btn.getAttribute( 'data-label-pause' ) : btn.getAttribute( 'data-label-play' );
			}
			btn.setAttribute( 'aria-pressed', String( playing ) );
		}

		btn.addEventListener( 'click', function () {
			if ( video.paused ) {
				manualPause = false;
				video.preload = 'auto';
				video.play().catch( function () {} );
			} else {
				manualPause = true;
				video.pause();
			}
		} );
		video.addEventListener( 'play', sync );
		video.addEventListener( 'pause', sync );
		sync();

		if ( reduce || ! ( 'IntersectionObserver' in window ) ) {
			return;
		}
		var io = new IntersectionObserver( function ( entries ) {
			entries.forEach( function ( entry ) {
				if ( entry.isIntersecting && ! manualPause ) {
					video.preload = 'auto';
					video.play().catch( function () {} );
				} else if ( ! entry.isIntersecting ) {
					video.pause();
				}
			} );
		}, { threshold: 0.45 } );
		io.observe( section );
	}

	/* ── Act VII — keepsake flip ────────────────────────────────────────────
	   A <button> toggle, not a link: there is no hover-then-navigate conflict
	   to solve, so no coarse-pointer two-tap rule applies here. Navigation is
	   the separate CTA below the board. */
	function initFlip() {
		qsa( '[data-flip]', root ).forEach( function ( el ) {
			el.addEventListener( 'click', function () {
				var on = el.classList.toggle( 'is-flipped' );
				el.setAttribute( 'aria-pressed', String( on ) );
			} );
		} );
	}

	/* ── Act VIII — newsletter capture ──────────────────────────────────────
	   Honest by construction: success is painted ONLY after admin-ajax.php
	   answers success. If the endpoint or nonce is missing, or the network
	   fails, the visitor is told so — the previous build showed "Welcome to
	   the movement" without ever sending a request. */
	function initCapture() {
		var form = root.querySelector( '[data-capture]' );
		if ( ! form || form.dataset.wired ) {
			return;
		}
		form.dataset.wired = '1';

		var input = form.querySelector( 'input[type="email"]' );
		var status = form.querySelector( '[data-status]' );
		var submit = form.querySelector( 'button[type="submit"]' );
		var endpoint = form.getAttribute( 'data-ajax-url' ) || '';
		var nonce = form.getAttribute( 'data-nonce' ) || '';
		var copy = {
			empty: form.getAttribute( 'data-msg-empty' ) || '',
			invalid: form.getAttribute( 'data-msg-invalid' ) || '',
			sending: form.getAttribute( 'data-msg-sending' ) || '',
			ok: form.getAttribute( 'data-msg-ok' ) || '',
			fail: form.getAttribute( 'data-msg-fail' ) || '',
			offline: form.getAttribute( 'data-msg-offline' ) || '',
		};

		function say( message, kind ) {
			if ( ! status ) {
				return;
			}
			status.classList.remove( 'is-ok', 'is-err' );
			if ( kind ) {
				status.classList.add( kind === 'ok' ? 'is-ok' : 'is-err' );
			}
			status.textContent = message;
		}

		form.addEventListener( 'submit', function ( event ) {
			event.preventDefault();
			var value = input ? input.value.trim() : '';
			if ( ! value ) {
				say( copy.empty, 'err' );
				if ( input ) {
					input.focus();
				}
				return;
			}
			if ( ! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test( value ) ) {
				say( copy.invalid, 'err' );
				input.focus();
				return;
			}
			if ( ! endpoint || ! nonce || typeof window.fetch !== 'function' ) {
				// No transport — say so. Never a fabricated success.
				say( copy.offline, 'err' );
				return;
			}

			var body = new FormData();
			body.append( 'action', 'skyyrose_newsletter_subscribe' );
			body.append( 'email', value );
			body.append( 'skyyrose_newsletter_nonce', nonce );

			say( copy.sending, null );
			if ( submit ) {
				submit.disabled = true;
			}

			window.fetch( endpoint, {
				method: 'POST',
				body: body,
				credentials: 'same-origin',
			} ).then( function ( response ) {
				return response.json();
			} ).then( function ( data ) {
				if ( data && data.success ) {
					// The page's own confirmation, not the endpoint's: the shared
					// handler answers with a promotional line ("your 15% code is
					// on the way") that this section never offered, and a store
					// must not confirm something it did not promise.
					say( copy.ok, 'ok' );
					input.value = '';
				} else {
					// Errors DO use the server's text — rate-limit and nonce
					// failures are specific and actionable.
					say( ( data && data.data && data.data.message ) || copy.fail, 'err' );
				}
			} ).catch( function () {
				say( copy.offline, 'err' );
			} ).then( function () {
				if ( submit ) {
					submit.disabled = false;
				}
			} );
		} );
	}

	function init() {
		initReveals();
		initHeroVideo();
		initTicker();
		initRooms();
		initPressWall();
		initOrigin();
		initFlip();
		initCapture();
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}
}() );
