/**
 * Page upgrade progressive enhancement.
 *
 * Updates a compositor-only reading-progress transform. Content and actions
 * remain fully usable when JavaScript is unavailable.
 */
( function () {
	'use strict';

	const progress = document.querySelector( '[data-sr-progress] span' );
	if ( ! progress ) {
		return;
	}

	let ticking = false;

	const update = () => {
		const root = document.documentElement;
		const distance = Math.max( root.scrollHeight - window.innerHeight, 1 );
		const value = Math.min( Math.max( window.scrollY / distance, 0 ), 1 );
		progress.style.transform = `scaleX(${ value })`;
		ticking = false;
	};

	const requestUpdate = () => {
		if ( ! ticking ) {
			window.requestAnimationFrame( update );
			ticking = true;
		}
	};

	update();
	window.addEventListener( 'scroll', requestUpdate, { passive: true } );
	window.addEventListener( 'resize', requestUpdate, { passive: true } );
}() );
