/**
 * Homepage V2 — SkyyRose Elite Web Builder
 *
 * Handles: loader animation, nav scroll state, reveal animations,
 * smooth scroll, mobile menu, newsletter AJAX, cart integration.
 *
 * All event handlers use addEventListener (no inline onclick — CSP compliant).
 * Localized data from WordPress via `skyyrose_homepage` object.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

( function () {
	'use strict';

	/* ======================================================================
	   LOADER — Progress bar with tri-color gradient
	   ====================================================================== */
	( function initLoader() {
		var progress = 0;
		var fill = document.getElementById( 'ldFill' );
		if ( ! fill ) {
			return;
		}
		var iv = setInterval( function () {
			progress += Math.random() * 14 + 5;
			if ( progress >= 100 ) {
				progress = 100;
				clearInterval( iv );
				setTimeout( function () {
					var loader = document.getElementById( 'loader' );
					if ( loader ) {
						loader.classList.add( 'done' );
					}
				}, 400 );
			}
			fill.style.width = progress + '%';
		}, 120 );
	} )();

	/* ======================================================================
	   NAV SCROLL — Toggle .scrolled class on main nav
	   ====================================================================== */
	( function initNavScroll() {
		var navTick = false;
		var nav = document.getElementById( 'mainNav' );
		if ( ! nav ) {
			return;
		}
		window.addEventListener( 'scroll', function () {
			if ( ! navTick ) {
				requestAnimationFrame( function () {
					nav.classList.toggle( 'scrolled', window.scrollY > 80 );
					navTick = false;
				} );
				navTick = true;
			}
		} );
	} )();

	/* ======================================================================
	   REVEAL ANIMATIONS — IntersectionObserver for .rv elements
	   ====================================================================== */
	( function initReveals() {
		var observer = new IntersectionObserver(
			function ( entries ) {
				entries.forEach( function ( entry ) {
					if ( entry.isIntersecting ) {
						entry.target.classList.add( 'vis' );
					}
				} );
			},
			{ threshold: 0.06, rootMargin: '0px 0px -40px 0px' }
		);
		document
			.querySelectorAll( '.rv, .rv-left, .rv-right, .rv-scale' )
			.forEach( function ( el ) {
				observer.observe( el );
			} );
	} )();

	/* ======================================================================
	   SMOOTH SCROLL — Anchor links scroll smoothly
	   ====================================================================== */
	( function initSmoothScroll() {
		document.querySelectorAll( 'a[href^="#"]' ).forEach( function ( a ) {
			a.addEventListener( 'click', function ( e ) {
				var href = a.getAttribute( 'href' );
				if ( href === '#' ) {
					return;
				}
				var target = document.querySelector( href );
				if ( target ) {
					e.preventDefault();
					closeMobileMenu();
					target.scrollIntoView( {
						behavior: 'smooth',
						block: 'start',
					} );
				}
			} );
		} );
	} )();

	/* ======================================================================
	   MOBILE MENU — Open/close full-screen overlay
	   ====================================================================== */
	var mobMenu = document.getElementById( 'mobMenu' );

	function openMobileMenu() {
		if ( mobMenu ) {
			mobMenu.classList.add( 'open' );
			document.body.style.overflow = 'hidden';
		}
	}

	function closeMobileMenu() {
		if ( mobMenu ) {
			mobMenu.classList.remove( 'open' );
			document.body.style.overflow = '';
		}
	}

	// Bind hamburger button.
	var hamBtn = document.querySelector( '.nav-ham' );
	if ( hamBtn ) {
		hamBtn.addEventListener( 'click', openMobileMenu );
	}

	// Bind close button.
	var closeBtn = document.querySelector( '.mob-close' );
	if ( closeBtn ) {
		closeBtn.addEventListener( 'click', closeMobileMenu );
	}

	// Bind mobile menu links to close on click.
	if ( mobMenu ) {
		mobMenu.querySelectorAll( 'a' ).forEach( function ( link ) {
			link.addEventListener( 'click', closeMobileMenu );
		} );
	}

	// Make closeMobileMenu available globally for smooth scroll.
	window.closeMob = closeMobileMenu;

	/* ======================================================================
	   NEWSLETTER — WordPress AJAX submission
	   ====================================================================== */
	( function initNewsletter() {
		var form = document.querySelector( '.nl-form' );
		var emailInput = document.getElementById( 'nlEmail' );
		var submitBtn = document.querySelector( '.nl-submit' );
		if ( ! form || ! emailInput || ! submitBtn ) {
			return;
		}

		submitBtn.addEventListener( 'click', function ( e ) {
			e.preventDefault();
			var email = emailInput.value.trim();

			if ( ! email || email.indexOf( '@' ) === -1 ) {
				showNewsletterMessage( 'Please enter a valid email address.', 'error' );
				return;
			}

			// If WordPress AJAX is available, submit via AJAX.
			if (
				typeof window.skyyrose_homepage !== 'undefined' &&
				window.skyyrose_homepage.ajax_url
			) {
				submitBtn.textContent = '...';
				submitBtn.disabled = true;

				var formData = new FormData();
				formData.append( 'action', 'skyyrose_newsletter_subscribe' );
				formData.append( 'email', email );
				formData.append(
					'skyyrose_newsletter_nonce',
					window.skyyrose_homepage.newsletter_nonce
				);

				fetch( window.skyyrose_homepage.ajax_url, {
					method: 'POST',
					body: formData,
					credentials: 'same-origin',
				} )
					.then( function ( response ) {
						return response.json();
					} )
					.then( function ( data ) {
						if ( data.success ) {
							showNewsletterMessage(
								( data.data && data.data.message ) || 'Welcome to the movement. Oakland love incoming.',
								'success'
							);
							emailInput.value = '';
						} else {
							showNewsletterMessage(
								( data.data && data.data.message ) || 'Something went wrong. Try again.',
								'error'
							);
						}
					} )
					.catch( function () {
						showNewsletterMessage(
							'Network error. Please try again.',
							'error'
						);
					} )
					.finally( function () {
						submitBtn.textContent = 'JOIN';
						submitBtn.disabled = false;
					} );
			} else {
				// Fallback: simple confirmation.
				showNewsletterMessage(
					'Welcome to the movement. Oakland love incoming.',
					'success'
				);
				emailInput.value = '';
			}
		} );

		// Handle Enter key in email input.
		emailInput.addEventListener( 'keydown', function ( e ) {
			if ( e.key === 'Enter' ) {
				e.preventDefault();
				submitBtn.click();
			}
		} );

		function showNewsletterMessage( msg, type ) {
			var existing = form.parentNode.querySelector( '.nl-message' );
			if ( existing ) {
				existing.remove();
			}
			var el = document.createElement( 'p' );
			el.className = 'nl-note nl-message';
			el.textContent = msg;
			el.style.color =
				type === 'error'
					? 'var(--crimson)'
					: 'var(--rose)';
			form.parentNode.insertBefore( el, form.nextSibling );
			setTimeout( function () {
				if ( el.parentNode ) {
					el.remove();
				}
			}, 5000 );
		}
	} )();

	/* ======================================================================
	   CART — WooCommerce integration
	   ====================================================================== */
	( function initCart() {
		var bagBtn = document.querySelector( '.nav-bag' );
		if ( ! bagBtn ) {
			return;
		}
		bagBtn.addEventListener( 'click', function () {
			if (
				typeof window.skyyrose_homepage !== 'undefined' &&
				window.skyyrose_homepage.cart_url
			) {
				window.location.href = window.skyyrose_homepage.cart_url;
			}
		} );
	} )();
} )();
