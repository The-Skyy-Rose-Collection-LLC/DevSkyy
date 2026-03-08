/**
 * Progressive Image Loading (Blur-Up / LQIP)
 *
 * Adds a perceived-instant loading experience for product images.
 * Images with `data-src` show a CSS blur transition as they load.
 * Falls back gracefully when IntersectionObserver isn't available.
 *
 * Usage: Add class "sr-progressive" and data-src="full.jpg" to any <img>.
 *        The src should be a tiny placeholder (or omitted for loading="lazy").
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	if ( ! ( 'IntersectionObserver' in window ) ) {
		// Fallback: load all images immediately.
		document.querySelectorAll( 'img.sr-progressive[data-src]' ).forEach( function ( img ) {
			img.src = img.dataset.src;
			img.classList.add( 'sr-progressive--loaded' );
		} );
		return;
	}

	var observer = new IntersectionObserver(
		function ( entries ) {
			entries.forEach( function ( entry ) {
				if ( ! entry.isIntersecting ) {
					return;
				}

				var img = entry.target;
				var fullSrc = img.dataset.src;

				if ( ! fullSrc ) {
					return;
				}

				// Preload in memory, then swap.
				var preloader = new Image();
				preloader.onload = function () {
					img.src = fullSrc;
					img.removeAttribute( 'data-src' );
					img.classList.add( 'sr-progressive--loaded' );
				};
				preloader.src = fullSrc;

				observer.unobserve( img );
			} );
		},
		{
			rootMargin: '200px 0px', // Start loading 200px before viewport.
			threshold: 0.01,
		}
	);

	// Observe all progressive images.
	document.querySelectorAll( 'img.sr-progressive[data-src]' ).forEach( function ( img ) {
		observer.observe( img );
	} );

	// Also handle images added dynamically (AJAX product grids, etc.).
	if ( 'MutationObserver' in window ) {
		var domObserver = new MutationObserver( function ( mutations ) {
			mutations.forEach( function ( mutation ) {
				mutation.addedNodes.forEach( function ( node ) {
					if ( node.nodeType !== 1 ) {
						return;
					}
					if ( node.matches && node.matches( 'img.sr-progressive[data-src]' ) ) {
						observer.observe( node );
					}
					if ( node.querySelectorAll ) {
						node.querySelectorAll( 'img.sr-progressive[data-src]' ).forEach( function ( img ) {
							observer.observe( img );
						} );
					}
				} );
			} );
		} );

		domObserver.observe( document.body, { childList: true, subtree: true } );
	}
})();
