/**
 * Complete the Look — PDP cross-sell quick-add behavior.
 *
 * Wires the .sr-complete-look section emitted by
 * template-parts/complete-the-look.php to WooCommerce's add-to-cart AJAX
 * endpoint. Per-button state, optimistic UI, and a wc_fragment_refresh
 * trigger so the mini-cart count updates without a full reload.
 *
 * Extracted from an inline <script> in the template part in v1.5.7
 * — the template no longer ships JS inline, which lets us version,
 * minify, and CSP-nonce this behavior like every other script.
 *
 * Reads data-product-id + data-nonce from each .sr-cl-card__add button
 * (emitted by the template). Falls back to skyyRoseWoo.ajaxUrl /
 * skyyRoseData.ajaxUrl / wp-admin/admin-ajax.php when wc_add_to_cart_params
 * isn't on the page.
 *
 * @package SkyyRose
 * @since   1.5.7
 */
( function () {
	'use strict';

	var section = document.querySelector( '.sr-complete-look' );
	if ( ! section ) {
		return;
	}

	var ajaxUrl = ( typeof skyyRoseWoo !== 'undefined' && skyyRoseWoo.ajaxUrl )
		? skyyRoseWoo.ajaxUrl
		: ( typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl )
		? skyyRoseData.ajaxUrl
		: '/wp-admin/admin-ajax.php';

	section.querySelectorAll( '.sr-cl-card__add' ).forEach( function ( btn ) {
		btn.addEventListener( 'click', function () {
			var pid  = btn.dataset.productId;
			var orig = btn.textContent;
			if ( ! pid ) {
				return;
			}

			btn.disabled    = true;
			btn.textContent = '…';

			// Use WooCommerce standard add-to-cart AJAX endpoint when available.
			var wcUrl = ( typeof wc_add_to_cart_params !== 'undefined' )
				? wc_add_to_cart_params.ajax_url
				: ajaxUrl;

			fetch( wcUrl + '?wc-ajax=add_to_cart', {
				method: 'POST',
				headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
				body: 'product_id=' + encodeURIComponent( pid ) + '&quantity=1',
			} )
				.then( function ( r ) { return r.json(); } )
				.then( function ( resp ) {
					btn.textContent = resp.error ? orig : 'Added ✓';
					btn.disabled    = false;
					if ( ! resp.error && typeof jQuery !== 'undefined' ) {
						jQuery( document.body ).trigger( 'wc_fragment_refresh' );
					}
					setTimeout( function () { btn.textContent = orig; }, 2500 );
				} )
				.catch( function () {
					btn.textContent = orig;
					btn.disabled    = false;
				} );
		} );
	} );
}() );
