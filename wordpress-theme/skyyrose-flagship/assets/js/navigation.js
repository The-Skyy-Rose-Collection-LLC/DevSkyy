/**
 * SkyyRose Flagship — Navigation
 *
 * Mobile menu toggle, dropdown behavior, sticky header,
 * and scroll-based header styling.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

( function() {
	'use strict';

	/* ------------------------------------------------
	   DOM References
	   ------------------------------------------------ */
	var header      = document.getElementById( 'masthead' );
	var menuToggle  = document.querySelector( '.menu-toggle' );
	var menuWrap    = document.querySelector( '.primary-menu-container' );
	var dropdowns   = document.querySelectorAll( '.menu-item-has-children' );
	var body        = document.body;

	/* ------------------------------------------------
	   Mobile Menu Toggle
	   ------------------------------------------------ */
	if ( menuToggle && menuWrap ) {
		menuToggle.addEventListener( 'click', function() {
			var expanded = this.getAttribute( 'aria-expanded' ) === 'true';
			this.setAttribute( 'aria-expanded', String( ! expanded ) );
			menuWrap.classList.toggle( 'toggled' );
			body.classList.toggle( 'menu-open' );

			// Animate hamburger → X
			this.classList.toggle( 'is-active' );
		} );

		// Close menu when clicking a link (mobile)
		var menuLinks = menuWrap.querySelectorAll( 'a' );
		menuLinks.forEach( function( link ) {
			link.addEventListener( 'click', function() {
				if ( window.innerWidth <= 768 ) {
					menuWrap.classList.remove( 'toggled' );
					body.classList.remove( 'menu-open' );
					menuToggle.classList.remove( 'is-active' );
					menuToggle.setAttribute( 'aria-expanded', 'false' );
				}
			} );
		} );
	}

	/* ------------------------------------------------
	   Mobile Dropdown Toggles
	   ------------------------------------------------ */
	dropdowns.forEach( function( item ) {
		var parentLink = item.querySelector( ':scope > a' );
		if ( ! parentLink ) return;

		parentLink.addEventListener( 'click', function( e ) {
			if ( window.innerWidth <= 768 ) {
				e.preventDefault();
				item.classList.toggle( 'sub-open' );

				// Close sibling dropdowns
				dropdowns.forEach( function( sibling ) {
					if ( sibling !== item ) {
						sibling.classList.remove( 'sub-open' );
					}
				} );
			}
		} );
	} );

	/* ------------------------------------------------
	   Sticky Header — scroll class
	   ------------------------------------------------ */
	var scrollThreshold = 50;
	var ticking = false;

	function onScroll() {
		if ( ! ticking ) {
			window.requestAnimationFrame( function() {
				if ( window.scrollY > scrollThreshold ) {
					header.classList.add( 'header-scrolled' );
				} else {
					header.classList.remove( 'header-scrolled' );
				}
				ticking = false;
			} );
			ticking = true;
		}
	}

	if ( header ) {
		window.addEventListener( 'scroll', onScroll, { passive: true } );
		// Run once on load in case the page is already scrolled
		onScroll();
	}

	/* ------------------------------------------------
	   Close menus on resize (mobile → desktop)
	   ------------------------------------------------ */
	var resizeTimer;
	window.addEventListener( 'resize', function() {
		clearTimeout( resizeTimer );
		resizeTimer = setTimeout( function() {
			if ( window.innerWidth > 768 ) {
				if ( menuWrap ) menuWrap.classList.remove( 'toggled' );
				body.classList.remove( 'menu-open' );
				if ( menuToggle ) {
					menuToggle.classList.remove( 'is-active' );
					menuToggle.setAttribute( 'aria-expanded', 'false' );
				}
				dropdowns.forEach( function( d ) { d.classList.remove( 'sub-open' ); } );
			}
		}, 150 );
	} );

	/* ------------------------------------------------
	   Keyboard accessibility — Escape closes menus
	   ------------------------------------------------ */
	document.addEventListener( 'keydown', function( e ) {
		if ( e.key === 'Escape' ) {
			if ( menuWrap && menuWrap.classList.contains( 'toggled' ) ) {
				menuWrap.classList.remove( 'toggled' );
				body.classList.remove( 'menu-open' );
				if ( menuToggle ) {
					menuToggle.classList.remove( 'is-active' );
					menuToggle.setAttribute( 'aria-expanded', 'false' );
					menuToggle.focus();
				}
			}
		}
	} );

} )();
