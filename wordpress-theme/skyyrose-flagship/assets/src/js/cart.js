/**
 * SkyyRoseCart — WooCommerce Store API Cart
 *
 * Modern cart class using the WC Store API (REST) instead of legacy
 * admin-ajax.php. Provides add/remove/update with ARIA-live toasts
 * for accessibility.
 *
 * @package SkyyRose_Flagship
 * @since   6.6.0
 */

/* global skyyToast */

( function () {
	'use strict';

	/**
	 * Base URL for WC Store API cart endpoints.
	 *
	 * @type {string}
	 */
	const STORE_API = '/wp-json/wc/store/v1/cart';

	/**
	 * Get a nonce for Store API requests.
	 *
	 * WC Store API uses a custom header instead of query-param nonces.
	 * The nonce is embedded by WooCommerce in a global script variable.
	 *
	 * @returns {string} Nonce value.
	 */
	function getStoreApiNonce() {
		// WC Blocks injects the nonce middleware; fall back to cookie.
		if (
			typeof window.wp !== 'undefined' &&
			window.wp.apiFetch &&
			window.wp.apiFetch.nonceMiddleware
		) {
			return window.wp.apiFetch.nonceMiddleware.nonce || '';
		}
		return '';
	}

	/**
	 * Make a Store API request.
	 *
	 * @param {string} endpoint  Endpoint path (appended to STORE_API).
	 * @param {Object} [options] Fetch options.
	 * @returns {Promise<Object>} Parsed JSON response.
	 */
	async function storeApiFetch( endpoint, options ) {
		const url = STORE_API + ( endpoint ? '/' + endpoint : '' );

		const headers = {
			'Content-Type': 'application/json',
		};

		const nonce = getStoreApiNonce();
		if ( nonce ) {
			headers['Nonce'] = nonce;
		}

		const defaults = {
			method: 'GET',
			headers: headers,
			credentials: 'same-origin',
		};

		const config = Object.assign( {}, defaults, options || {} );

		const response = await fetch( url, config );

		if ( ! response.ok ) {
			const errorData = await response.json().catch( function () {
				return { message: response.statusText };
			} );
			throw new Error( errorData.message || 'Cart request failed' );
		}

		return response.json();
	}

	/**
	 * Show an ARIA-live toast notification.
	 *
	 * Uses the global skyyToast() if available, otherwise falls back
	 * to a minimal ARIA-live region.
	 *
	 * @param {string} message Toast message text.
	 * @param {string} [type]  Toast type: 'success', 'error', 'info'.
	 */
	function announce( message, type ) {
		// Prefer global toast system (loaded from toast.js).
		if ( typeof window.skyyToast === 'function' ) {
			window.skyyToast( message, type || 'success', 3000 );
			return;
		}

		// Fallback: inject a minimal ARIA-live region.
		var region = document.getElementById( 'skyyrose-cart-live' );
		if ( ! region ) {
			region = document.createElement( 'div' );
			region.id = 'skyyrose-cart-live';
			region.setAttribute( 'role', 'status' );
			region.setAttribute( 'aria-live', 'polite' );
			region.setAttribute( 'aria-atomic', 'true' );
			region.className = 'screen-reader-text';
			document.body.appendChild( region );
		}
		region.textContent = message;
	}

	/**
	 * Update all cart count badges in the DOM.
	 *
	 * @param {number} count Current cart item count.
	 */
	function updateCartBadges( count ) {
		var badges = document.querySelectorAll( '.cart-count' );
		badges.forEach( function ( badge ) {
			badge.textContent = count;
			if ( count > 0 ) {
				badge.classList.add( 'has-items' );
			} else {
				badge.classList.remove( 'has-items' );
			}
		} );
	}

	/**
	 * SkyyRoseCart — public cart interface.
	 *
	 * @namespace SkyyRoseCart
	 */
	var SkyyRoseCart = {
		/**
		 * Get full cart data.
		 *
		 * @returns {Promise<Object>} Cart object with items, coupons, totals.
		 */
		get: function () {
			return storeApiFetch( '' );
		},

		/**
		 * Add an item to the cart.
		 *
		 * @param {number}  productId Product ID.
		 * @param {number}  [quantity] Quantity (default 1).
		 * @param {Object}  [variation] Variation attributes.
		 * @returns {Promise<Object>} Updated cart object.
		 */
		addItem: function ( productId, quantity, variation ) {
			var body = {
				id: productId,
				quantity: quantity || 1,
			};
			if ( variation ) {
				body.variation = variation;
			}
			return storeApiFetch( 'add-item', {
				method: 'POST',
				body: JSON.stringify( body ),
			} ).then( function ( cart ) {
				var count = cart.items_count || cart.items.length;
				updateCartBadges( count );
				announce(
					( cart.items.find( function ( i ) {
						return i.id === productId;
					} ) || {} ).name +
						' ' +
						( window.skyyRoseWoo
							? window.skyyRoseWoo.addedToCartText
							: 'added to cart' ),
					'success'
				);
				document.dispatchEvent(
					new CustomEvent( 'skyyrose:cart:updated', { detail: cart } )
				);
				return cart;
			} );
		},

		/**
		 * Remove an item from the cart.
		 *
		 * @param {string} itemKey Cart item key.
		 * @returns {Promise<Object>} Updated cart object.
		 */
		removeItem: function ( itemKey ) {
			return storeApiFetch( 'remove-item', {
				method: 'POST',
				body: JSON.stringify( { key: itemKey } ),
			} ).then( function ( cart ) {
				var count = cart.items_count || cart.items.length;
				updateCartBadges( count );
				announce( 'Item removed from cart', 'info' );
				document.dispatchEvent(
					new CustomEvent( 'skyyrose:cart:updated', { detail: cart } )
				);
				return cart;
			} );
		},

		/**
		 * Update item quantity.
		 *
		 * @param {string} itemKey  Cart item key.
		 * @param {number} quantity New quantity.
		 * @returns {Promise<Object>} Updated cart object.
		 */
		updateItem: function ( itemKey, quantity ) {
			return storeApiFetch( 'update-item', {
				method: 'POST',
				body: JSON.stringify( { key: itemKey, quantity: quantity } ),
			} ).then( function ( cart ) {
				var count = cart.items_count || cart.items.length;
				updateCartBadges( count );
				announce( 'Cart updated', 'success' );
				document.dispatchEvent(
					new CustomEvent( 'skyyrose:cart:updated', { detail: cart } )
				);
				return cart;
			} );
		},

		/**
		 * Apply a coupon code.
		 *
		 * @param {string} code Coupon code.
		 * @returns {Promise<Object>} Updated cart object.
		 */
		applyCoupon: function ( code ) {
			return storeApiFetch( 'apply-coupon', {
				method: 'POST',
				body: JSON.stringify( { code: code } ),
			} ).then( function ( cart ) {
				announce( 'Coupon applied', 'success' );
				document.dispatchEvent(
					new CustomEvent( 'skyyrose:cart:updated', { detail: cart } )
				);
				return cart;
			} );
		},

		/**
		 * Remove a coupon code.
		 *
		 * @param {string} code Coupon code.
		 * @returns {Promise<Object>} Updated cart object.
		 */
		removeCoupon: function ( code ) {
			return storeApiFetch( 'remove-coupon', {
				method: 'POST',
				body: JSON.stringify( { code: code } ),
			} ).then( function ( cart ) {
				announce( 'Coupon removed', 'info' );
				document.dispatchEvent(
					new CustomEvent( 'skyyrose:cart:updated', { detail: cart } )
				);
				return cart;
			} );
		},
	};

	// Expose globally.
	window.SkyyRoseCart = SkyyRoseCart;
} )();
