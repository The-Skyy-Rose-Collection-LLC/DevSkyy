/**
 * Homepage V2 — SkyyRose Elite Web Builder
 *
 * Handles: loader animation, nav scroll state, reveal animations,
 * smooth scroll, mobile menu, newsletter AJAX, cart integration.
 *
 * All event handlers use addEventListener (no inline onclick — CSP compliant).
 * Localized data from WordPress via `skyyrose_homepage` object.
 *
 * @package SkyyRose
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
	   HERO LETTER REVEAL — Split title into staggered <span> letters
	   ====================================================================== */
	( function initLetterReveal() {
		var title = document.querySelector( '.hero-title' );
		if ( ! title ) {
			return;
		}
		var text = title.textContent.trim();
		title.textContent = '';
		title.setAttribute( 'aria-label', text );

		for ( var i = 0; i < text.length; i++ ) {
			var span = document.createElement( 'span' );
			span.className = 'hero-letter';
			span.textContent = text[ i ];
			span.style.animationDelay = ( 0.3 + i * 0.08 ) + 's';
			span.setAttribute( 'aria-hidden', 'true' );
			title.appendChild( span );
		}
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

	/* ======================================================================
	   SCROLL PROGRESS — Rose-gold bar at top of page
	   ====================================================================== */
	( function initScrollProgress() {
		var bar = document.querySelector( '.scroll-progress' );
		if ( ! bar ) {
			return;
		}
		var progressTick = false;
		window.addEventListener( 'scroll', function () {
			if ( ! progressTick ) {
				requestAnimationFrame( function () {
					var docHeight = document.documentElement.scrollHeight - window.innerHeight;
					var pct = docHeight > 0 ? ( window.scrollY / docHeight ) * 100 : 0;
					bar.style.width = pct + '%';
					progressTick = false;
				} );
				progressTick = true;
			}
		} );
	} )();

	/* ======================================================================
	   BACK TO TOP — Appears after scrolling past hero
	   ====================================================================== */
	( function initBackToTop() {
		var btn = document.querySelector( '.back-to-top' );
		if ( ! btn ) {
			return;
		}
		var bttTick = false;
		window.addEventListener( 'scroll', function () {
			if ( ! bttTick ) {
				requestAnimationFrame( function () {
					btn.classList.toggle( 'visible', window.scrollY > window.innerHeight );
					bttTick = false;
				} );
				bttTick = true;
			}
		} );
		btn.addEventListener( 'click', function () {
			window.scrollTo( { top: 0, behavior: 'smooth' } );
		} );
	} )();
} )();

/* ======================================================================
   HOMEPAGE V7 — Concrete theme interactions
   ====================================================================== */

( function () {
	'use strict';

	/* ── Animated canvas grain (12fps — materiality signal) ── */
	( function initGrain() {
		var canvas = document.getElementById( 'grainCanvas' );
		if ( ! canvas ) { return; }
		var ctx = canvas.getContext( '2d' );

		function resize() {
			canvas.width  = window.innerWidth;
			canvas.height = window.innerHeight;
		}
		resize();
		window.addEventListener( 'resize', resize );

		function renderGrain() {
			var w = canvas.width;
			var h = canvas.height;
			var imageData = ctx.createImageData( w, h );
			var data = imageData.data;
			for ( var i = 0; i < data.length; i += 4 ) {
				var v = Math.random() * 255 | 0;
				data[ i ]     = v;
				data[ i + 1 ] = v;
				data[ i + 2 ] = v;
				data[ i + 3 ] = 18; /* ~7% opacity */
			}
			ctx.putImageData( imageData, 0, 0 );
		}

		/* 12fps — intentional flicker matches film grain */
		var grainTimer;
		function scheduleGrain() {
			grainTimer = setTimeout( function () {
				if ( window.requestAnimationFrame ) {
					requestAnimationFrame( function () {
						renderGrain();
						scheduleGrain();
					} );
				}
			}, 1000 / 12 );
		}

		if ( ! window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches ) {
			scheduleGrain();
		}
	} )();

	/* ── Cursor-trigger collection split ── */
	( function initCollectionSplit() {
		var split = document.querySelector( '.collection-split' );
		if ( ! split ) { return; }
		var panelBr = split.querySelector( '.split-br' );
		var panelSg = split.querySelector( '.split-sg' );
		var divider = split.querySelector( '.split-divider' );
		if ( ! panelBr || ! panelSg ) { return; }

		split.addEventListener( 'mousemove', function ( e ) {
			var rect  = split.getBoundingClientRect();
			var ratio = ( e.clientX - rect.left ) / rect.width;

			/* Dim the non-hovered side */
			panelBr.style.filter = ratio < 0.5
				? 'brightness(1.15)'
				: 'brightness(0.55)';
			panelSg.style.filter = ratio >= 0.5
				? 'brightness(1.15)'
				: 'brightness(0.55)';

			/* Subtle divider shift toward cursor */
			if ( divider ) {
				var shift = ( ratio - 0.5 ) * 14;
				divider.style.transform = 'translateX(calc(-50% + ' + shift + 'px))';
			}
		} );

		split.addEventListener( 'mouseleave', function () {
			panelBr.style.filter = '';
			panelSg.style.filter = '';
			if ( divider ) { divider.style.transform = ''; }
		} );
	} )();

	/* ── Specimen ticker — pause on hover ── */
	( function initSpecimenTicker() {
		var track = document.getElementById( 'specimenTrack' );
		if ( ! track ) { return; }
		track.addEventListener( 'mouseenter', function () {
			track.style.animationPlayState = 'paused';
		} );
		track.addEventListener( 'mouseleave', function () {
			track.style.animationPlayState = 'running';
		} );
	} )();

	/* ── Hero concrete word — subtle mouse parallax ── */
	( function initHeroParallax() {
		var word = document.querySelector( '.hero-concrete-word' );
		if ( ! word ) { return; }
		var tick = false;
		window.addEventListener( 'mousemove', function ( e ) {
			if ( tick ) { return; }
			tick = true;
			requestAnimationFrame( function () {
				var cx = window.innerWidth  / 2;
				var cy = window.innerHeight / 2;
				var dx = ( e.clientX - cx ) / cx;
				var dy = ( e.clientY - cy ) / cy;
				word.style.transform =
					'scaleX(0.62) scaleY(1.08) translate(' +
					( dx * 8 ) + 'px, ' + ( dy * 4 ) + 'px)';
				tick = false;
			} );
		} );
	} )();

} )();
