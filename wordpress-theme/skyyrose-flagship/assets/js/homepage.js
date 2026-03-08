/**
 * SkyyRose Flagship — Homepage JavaScript
 *
 * Handles: cinematic loader, scroll-reveal, nav scroll state,
 * smooth scroll, featured product size selection, and newsletter AJAX.
 *
 * Product data is passed from PHP via wp_localize_script (skyyRoseHomepage).
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	/* ═══════════════════════════════════════════
	   1. CINEMATIC LOADER
	   ═══════════════════════════════════════════ */
	(function initLoader() {
		var fill = document.getElementById( 'loaderFill' );
		if ( ! fill ) {
			return;
		}

		var progress = 0;
		var iv = setInterval( function () {
			progress += Math.random() * 12 + 4;
			if ( progress >= 100 ) {
				progress = 100;
				clearInterval( iv );
				setTimeout( function () {
					var loader = document.getElementById( 'loader' );
					if ( loader ) {
						loader.classList.add( 'done' );
					}
				}, 500 );
			}
			fill.style.width = progress + '%';
		}, 140 );
	})();

	/* ═══════════════════════════════════════════
	   2. SCROLL-REVEAL (IntersectionObserver)
	   ═══════════════════════════════════════════ */
	function initReveals() {
		if ( ! ( 'IntersectionObserver' in window ) ) {
			document.querySelectorAll( '.rv, .rv-left, .rv-right' ).forEach( function ( el ) {
				el.classList.add( 'vis' );
			} );
			return;
		}

		var observer = new IntersectionObserver(
			function ( entries ) {
				entries.forEach( function ( entry ) {
					if ( entry.isIntersecting ) {
						entry.target.classList.add( 'vis' );
					}
				} );
			},
			{ threshold: 0.08, rootMargin: '0px 0px -30px 0px' }
		);

		document.querySelectorAll( '.rv, .rv-left, .rv-right' ).forEach( function ( el ) {
			observer.observe( el );
		} );
	}

	/* ═══════════════════════════════════════════
	   3. NAV SCROLL STATE
	   ═══════════════════════════════════════════ */
	function initNavScroll() {
		var nav = document.getElementById( 'mainNav' );
		if ( ! nav ) {
			return;
		}

		var ticking = false;
		window.addEventListener( 'scroll', function () {
			if ( ! ticking ) {
				requestAnimationFrame( function () {
					nav.classList.toggle( 'scrolled', window.scrollY > 80 );
					ticking = false;
				} );
				ticking = true;
			}
		}, { passive: true } );
	}

	/* ═══════════════════════════════════════════
	   4. SMOOTH SCROLL FOR ANCHOR LINKS
	   ═══════════════════════════════════════════ */
	function initSmoothScroll() {
		document.querySelectorAll( 'a[href^="#"]' ).forEach( function ( anchor ) {
			anchor.addEventListener( 'click', function ( e ) {
				var target = document.querySelector( anchor.getAttribute( 'href' ) );
				if ( target ) {
					e.preventDefault();
					target.scrollIntoView( { behavior: 'smooth', block: 'start' } );
				}
			} );
		} );
	}

	/* ═══════════════════════════════════════════
	   5. FEATURED PRODUCT SIZE SELECTOR
	   ═══════════════════════════════════════════ */
	function initSizeSelectors() {
		document.querySelectorAll( '.cl-feat-sizes' ).forEach( function ( container ) {
			container.addEventListener( 'click', function ( e ) {
				var btn = e.target.closest( 'button' );
				if ( ! btn ) {
					return;
				}

				container.querySelectorAll( 'button' ).forEach( function ( b ) {
					b.classList.remove( 'sel' );
				} );
				btn.classList.add( 'sel' );

				// Store selected size on the parent featured section.
				var section = container.closest( '.cl-featured' );
				if ( section ) {
					section.dataset.selectedSize = btn.textContent.trim();
				}
			} );
		} );
	}

	/* ═══════════════════════════════════════════
	   6. NEWSLETTER FORM (AJAX)
	   ═══════════════════════════════════════════ */
	function initNewsletter() {
		var form = document.querySelector( '.nl-form' );
		if ( ! form ) {
			return;
		}

		var submitBtn = form.querySelector( '.nl-submit' );
		var input = form.querySelector( '.nl-input' );

		if ( ! submitBtn || ! input ) {
			return;
		}

		submitBtn.addEventListener( 'click', function ( e ) {
			e.preventDefault();

			var email = input.value.trim();
			if ( ! email || email.indexOf( '@' ) === -1 ) {
				input.style.borderColor = '#DC143C';
				return;
			}

			// Use WordPress AJAX if available.
			var data = typeof skyyRoseData !== 'undefined' ? skyyRoseData : {};
			var ajaxUrl = data.ajaxUrl || '/index.php?rest_route=/';

			submitBtn.textContent = 'JOINING...';
			submitBtn.disabled = true;

			var formData = new FormData();
			formData.append( 'action', 'skyyrose_newsletter_subscribe' );
			formData.append( 'email', email );
			if ( data.nonce ) {
				formData.append( 'nonce', data.nonce );
			}

			fetch( ajaxUrl, {
				method: 'POST',
				body: formData,
			} )
			.then( function () {
				submitBtn.textContent = 'WELCOME';
				input.value = '';
				input.style.borderColor = '';
			} )
			.catch( function () {
				submitBtn.textContent = 'WELCOME';
				input.value = '';
			} )
			.finally( function () {
				setTimeout( function () {
					submitBtn.textContent = 'JOIN';
					submitBtn.disabled = false;
				}, 3000 );
			} );
		} );
	}

	/* ═══════════════════════════════════════════
	   7. KEYBOARD ESCAPE TO CLOSE MODALS
	   ═══════════════════════════════════════════ */
	document.addEventListener( 'keydown', function ( e ) {
		if ( e.key === 'Escape' ) {
			var cartPnl = document.getElementById( 'cartPnl' );
			if ( cartPnl ) {
				cartPnl.classList.remove( 'open' );
			}
		}
	} );

	/* ═══════════════════════════════════════════
	   INIT ON DOM READY
	   ═══════════════════════════════════════════ */
	document.addEventListener( 'DOMContentLoaded', function () {
		initReveals();
		initNavScroll();
		initSmoothScroll();
		initSizeSelectors();
		initNewsletter();
	} );
})();
