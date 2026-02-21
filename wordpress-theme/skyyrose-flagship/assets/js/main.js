/**
 * SkyyRose Flagship — Main Theme JS
 *
 * Smooth scroll anchors, scroll-reveal animations,
 * countdown timer support, and lazy-load enhancements.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

( function() {
	'use strict';

	/* ------------------------------------------------
	   Smooth Scroll for Anchor Links
	   ------------------------------------------------ */
	document.querySelectorAll( 'a[href^="#"]' ).forEach( function( anchor ) {
		anchor.addEventListener( 'click', function( e ) {
			var targetId = this.getAttribute( 'href' );
			if ( targetId === '#' || targetId.length < 2 ) return;

			var target = document.querySelector( targetId );
			if ( ! target ) return;

			e.preventDefault();

			var headerHeight = 0;
			var header = document.getElementById( 'masthead' );
			if ( header ) {
				headerHeight = header.offsetHeight;
			}

			var targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;

			window.scrollTo( {
				top: targetPosition,
				behavior: 'smooth'
			} );
		} );
	} );

	/* ------------------------------------------------
	   Scroll-Reveal (IntersectionObserver)
	   ------------------------------------------------ */
	var revealElements = document.querySelectorAll(
		'.fp-collection-row, .fp-story-grid, .fp-trust-item, ' +
		'.cl-lookbook-item, .cl-story-grid, .cl-product-card, ' +
		'.section-header, .cl-experience, .cl-crosssell-card, ' +
		'.po-collection-card, .po-benefit-card, .po-faq-item'
	);

	if ( 'IntersectionObserver' in window && revealElements.length ) {
		var revealObserver = new IntersectionObserver( function( entries ) {
			entries.forEach( function( entry ) {
				if ( entry.isIntersecting ) {
					entry.target.classList.add( 'revealed' );
					revealObserver.unobserve( entry.target );
				}
			} );
		}, {
			threshold: 0.15,
			rootMargin: '0px 0px -40px 0px'
		} );

		revealElements.forEach( function( el ) {
			el.classList.add( 'reveal-on-scroll' );
			revealObserver.observe( el );
		} );
	}

	/* ------------------------------------------------
	   Countdown Timer (Pre-Order Page)
	   ------------------------------------------------ */
	var countdownEl = document.querySelector( '.po-countdown' );
	if ( countdownEl ) {
		var launchDate = countdownEl.getAttribute( 'data-launch-date' );
		if ( ! launchDate ) {
			launchDate = '2026-03-15T00:00:00';
		}

		var target = new Date( launchDate ).getTime();

		function updateCountdown() {
			var now  = Date.now();
			var diff = target - now;

			if ( diff <= 0 ) {
				countdownEl.innerHTML = '<span class="po-countdown-label">We Have Launched!</span>';
				return;
			}

			var days    = Math.floor( diff / ( 1000 * 60 * 60 * 24 ) );
			var hours   = Math.floor( ( diff % ( 1000 * 60 * 60 * 24 ) ) / ( 1000 * 60 * 60 ) );
			var minutes = Math.floor( ( diff % ( 1000 * 60 * 60 ) ) / ( 1000 * 60 ) );
			var seconds = Math.floor( ( diff % ( 1000 * 60 ) ) / 1000 );

			var daysEl    = countdownEl.querySelector( '[data-unit="days"]' );
			var hoursEl   = countdownEl.querySelector( '[data-unit="hours"]' );
			var minutesEl = countdownEl.querySelector( '[data-unit="minutes"]' );
			var secondsEl = countdownEl.querySelector( '[data-unit="seconds"]' );

			if ( daysEl )    daysEl.textContent    = String( days ).padStart( 2, '0' );
			if ( hoursEl )   hoursEl.textContent   = String( hours ).padStart( 2, '0' );
			if ( minutesEl ) minutesEl.textContent = String( minutes ).padStart( 2, '0' );
			if ( secondsEl ) secondsEl.textContent = String( seconds ).padStart( 2, '0' );
		}

		updateCountdown();
		setInterval( updateCountdown, 1000 );
	}

	/* ------------------------------------------------
	   Pre-Order Email Form
	   ------------------------------------------------ */
	var emailForm = document.querySelector( '.po-email-form' );
	if ( emailForm ) {
		emailForm.addEventListener( 'submit', function( e ) {
			e.preventDefault();

			var emailInput = this.querySelector( 'input[type="email"]' );
			var submitBtn  = this.querySelector( 'button[type="submit"]' );

			if ( ! emailInput || ! emailInput.value ) return;

			var originalText = submitBtn.textContent;
			submitBtn.textContent = 'Joining...';
			submitBtn.disabled = true;

			// Simulate success (replace with actual AJAX when backend ready)
			setTimeout( function() {
				submitBtn.textContent = 'You\'re In!';
				emailInput.value = '';
				setTimeout( function() {
					submitBtn.textContent = originalText;
					submitBtn.disabled = false;
				}, 3000 );
			}, 1200 );
		} );
	}

	/* ------------------------------------------------
	   Collection Logo Parallax (subtle)
	   ------------------------------------------------ */
	var heroLogos = document.querySelectorAll( '.cl-logo-svg' );
	if ( heroLogos.length ) {
		window.addEventListener( 'scroll', function() {
			var scrollY = window.pageYOffset;
			heroLogos.forEach( function( logo ) {
				var section = logo.closest( 'section' );
				if ( ! section ) return;
				var rect = section.getBoundingClientRect();
				if ( rect.bottom > 0 && rect.top < window.innerHeight ) {
					var progress = ( window.innerHeight - rect.top ) / ( window.innerHeight + rect.height );
					logo.style.transform = 'translateY(' + ( progress * 15 - 7.5 ) + 'px)';
				}
			} );
		}, { passive: true } );
	}

} )();
