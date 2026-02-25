/**
 * Immersive WooCommerce Bridge
 *
 * Enhances immersive scene hotspots with live product data from WooCommerce.
 * Falls back gracefully to static data attributes when WooCommerce is unavailable.
 *
 * @package SkyyRose_Flagship
 * @since   3.12.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Guard: only run when localized data is available
	   -------------------------------------------------- */

	if (typeof window.skyyRoseImmersive === 'undefined') {
		return;
	}

	var config = window.skyyRoseImmersive;
	var ajaxUrl = config.ajaxUrl || '';
	var nonce = config.nonce || '';
	var cartUrl = config.cartUrl || '';

	if (!ajaxUrl || !nonce) {
		return;
	}

	/* --------------------------------------------------
	   Product Data Cache
	   -------------------------------------------------- */

	var productCache = new Map();

	/* --------------------------------------------------
	   AJAX Helper
	   -------------------------------------------------- */

	/**
	 * Send a POST request to the WordPress AJAX endpoint.
	 *
	 * @param {string}   action   The AJAX action name.
	 * @param {Object}   params   Key-value pairs for the POST body.
	 * @param {Function} onSuccess Called with the parsed response data on success.
	 * @param {Function} onError   Called with an error message string on failure.
	 */
	function ajaxPost(action, params, onSuccess, onError) {
		var xhr = new XMLHttpRequest();
		xhr.open('POST', ajaxUrl, true);
		xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

		xhr.onload = function () {
			if (xhr.status >= 200 && xhr.status < 300) {
				try {
					var response = JSON.parse(xhr.responseText);
					if (response.success && response.data) {
						onSuccess(response.data);
					} else {
						var msg = (response.data && response.data.message)
							? response.data.message
							: 'Request failed.';
						if (onError) onError(msg);
					}
				} catch (e) {
					if (onError) onError('Invalid response.');
				}
			} else {
				if (onError) onError('Network error.');
			}
		};

		xhr.onerror = function () {
			if (onError) onError('Network error.');
		};

		// Build the POST body.
		var parts = ['action=' + encodeURIComponent(action), 'nonce=' + encodeURIComponent(nonce)];
		for (var key in params) {
			if (params.hasOwnProperty(key)) {
				parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
			}
		}
		xhr.send(parts.join('&'));
	}

	/* --------------------------------------------------
	   Fetch Product by SKU
	   -------------------------------------------------- */

	/**
	 * Fetch live product data from WooCommerce by SKU.
	 *
	 * Returns cached data if available. Caches successful responses.
	 *
	 * @param {string}   sku        The product SKU.
	 * @param {Function} onSuccess  Called with product data object.
	 * @param {Function} onError    Called with error message string.
	 */
	function fetchProductBySku(sku, onSuccess, onError) {
		if (!sku) {
			if (onError) onError('No SKU provided.');
			return;
		}

		// Return cached data if available.
		if (productCache.has(sku)) {
			if (onSuccess) onSuccess(productCache.get(sku));
			return;
		}

		ajaxPost(
			'skyyrose_get_product_by_sku',
			{ sku: sku },
			function (data) {
				productCache.set(sku, data);
				if (onSuccess) onSuccess(data);
			},
			onError
		);
	}

	/* --------------------------------------------------
	   Enhance Hotspots with Live Data
	   -------------------------------------------------- */

	/**
	 * Iterate all hotspot elements and enrich them with live WooCommerce data.
	 *
	 * Looks for .hotspot[data-product-sku] elements and fetches fresh data
	 * for each unique SKU. Updates data attributes and visible price/URL
	 * without replacing the hotspot DOM structure.
	 */
	function enhanceHotspots() {
		var hotspots = document.querySelectorAll('.hotspot[data-product-sku]');

		if (!hotspots.length) {
			// Fall back: try hotspots with data-product-id only.
			hotspots = document.querySelectorAll('.hotspot[data-product-id]');
		}

		if (!hotspots.length) {
			return;
		}

		// Collect unique SKUs to avoid duplicate requests.
		var skuHotspotMap = {};

		for (var i = 0; i < hotspots.length; i++) {
			var hotspot = hotspots[i];
			var sku = hotspot.getAttribute('data-product-sku');

			if (!sku) {
				continue;
			}

			if (!skuHotspotMap[sku]) {
				skuHotspotMap[sku] = [];
			}
			skuHotspotMap[sku].push(hotspot);
		}

		// Fetch data for each unique SKU.
		var skus = Object.keys(skuHotspotMap);

		for (var j = 0; j < skus.length; j++) {
			(function (currentSku) {
				fetchProductBySku(
					currentSku,
					function (data) {
						var targets = skuHotspotMap[currentSku];
						for (var k = 0; k < targets.length; k++) {
							applyLiveData(targets[k], data);
						}
					},
					function () {
						// Silently fall back to static data attributes.
					}
				);
			})(skus[j]);
		}
	}

	/**
	 * Apply live product data to a hotspot element's data attributes.
	 *
	 * If the price has changed, also updates visible price elements
	 * in any open product panel referencing this hotspot.
	 *
	 * @param {Element} hotspot The hotspot DOM element.
	 * @param {Object}  data    Product data from the AJAX response.
	 */
	function applyLiveData(hotspot, data) {
		var oldPrice = hotspot.getAttribute('data-product-price') || '';

		// Update data attributes with live values.
		if (data.name) hotspot.setAttribute('data-product-name', data.name);
		if (data.price) hotspot.setAttribute('data-product-price', '$' + data.price);
		if (data.image_url) hotspot.setAttribute('data-product-image', data.image_url);
		if (data.permalink) hotspot.setAttribute('data-product-url', data.permalink);
		if (data.id) hotspot.setAttribute('data-product-id', data.id);

		// Build sizes string from array.
		if (data.sizes && data.sizes.length) {
			hotspot.setAttribute('data-product-sizes', data.sizes.join(','));
		}

		// Sync price if it changed and the product panel is showing this item.
		var newPrice = '$' + data.price;
		if (oldPrice && oldPrice !== newPrice) {
			syncPriceDisplay(hotspot, newPrice);
		}

		// Mark as live-enhanced for CSS styling hooks.
		hotspot.classList.add('hotspot--live');
	}

	/**
	 * Smoothly update the price display in the product panel if it shows
	 * the product from this hotspot.
	 *
	 * @param {Element} hotspot  The hotspot element.
	 * @param {string}  newPrice The new formatted price string.
	 */
	function syncPriceDisplay(hotspot, newPrice) {
		var panel = document.querySelector('.product-panel.open');
		if (!panel) return;

		var panelPrice = panel.querySelector('.product-panel-price');
		if (!panelPrice) return;

		var panelName = panel.querySelector('.product-panel-name');
		var hotspotName = hotspot.getAttribute('data-product-name');

		// Only update if the panel is showing the same product.
		if (panelName && hotspotName && panelName.textContent === hotspotName) {
			panelPrice.style.transition = 'opacity 0.3s ease';
			panelPrice.style.opacity = '0';

			setTimeout(function () {
				panelPrice.textContent = newPrice;
				panelPrice.style.opacity = '1';
			}, 300);
		}
	}

	/* --------------------------------------------------
	   Live Add to Cart
	   -------------------------------------------------- */

	/**
	 * Add a product to the WooCommerce cart via the dedicated immersive
	 * AJAX endpoint. Shows a toast notification on success.
	 *
	 * @param {number}      productId  WooCommerce product ID.
	 * @param {string|null} size       Optional size attribute value.
	 * @param {Function}    onComplete Called when the request finishes (success or error).
	 */
	function liveAddToCart(productId, size, onComplete) {
		if (!productId) {
			showToast('Unable to add item. Please try from the product page.');
			if (onComplete) onComplete(false);
			return;
		}

		var params = {
			product_id: productId,
			quantity: 1,
		};

		if (size) {
			params.attribute_pa_size = size;
		}

		ajaxPost(
			'skyyrose_immersive_add_to_cart',
			params,
			function (data) {
				showToast(data.message || 'Added to cart!');

				// Update cart count badge via fragments.
				if (data.fragments) {
					for (var selector in data.fragments) {
						if (data.fragments.hasOwnProperty(selector)) {
							var targets = document.querySelectorAll(selector);
							for (var i = 0; i < targets.length; i++) {
								var temp = document.createElement('div');
								temp.innerHTML = data.fragments[selector];
								if (temp.firstChild) {
									targets[i].parentNode.replaceChild(temp.firstChild, targets[i]);
								}
							}
						}
					}
				}

				// Trigger WooCommerce cart fragment refresh if jQuery is available.
				if (typeof jQuery !== 'undefined') {
					jQuery(document.body).trigger('wc_fragment_refresh');
				}

				if (onComplete) onComplete(true);
			},
			function (errorMsg) {
				showToast(errorMsg || 'Could not add item. Please try again.');
				if (onComplete) onComplete(false);
			}
		);
	}

	/* --------------------------------------------------
	   Toast Notification
	   -------------------------------------------------- */

	/**
	 * Show a temporary toast notification at the bottom of the viewport.
	 *
	 * Reuses the existing .immersive-cart-notification element if present,
	 * otherwise creates one.
	 *
	 * @param {string} message The message to display.
	 */
	function showToast(message) {
		var notification = document.querySelector('.immersive-cart-notification');

		if (!notification) {
			notification = document.createElement('div');
			notification.className = 'immersive-cart-notification';
			notification.setAttribute('role', 'status');
			notification.setAttribute('aria-live', 'polite');
			document.body.appendChild(notification);
		}

		notification.textContent = message;
		notification.classList.add('visible');

		setTimeout(function () {
			notification.classList.remove('visible');
		}, 3500);
	}

	/* --------------------------------------------------
	   Intercept Add-to-Cart Button
	   -------------------------------------------------- */

	/**
	 * Override the existing product panel add-to-cart button to use
	 * the dedicated immersive AJAX endpoint instead of the generic
	 * WooCommerce wc-ajax endpoint.
	 *
	 * This does not remove the original listener in immersive.js;
	 * it attaches a capturing listener that prevents propagation
	 * when the bridge is active.
	 */
	function interceptAddToCart() {
		var panel = document.querySelector('.product-panel');
		if (!panel) return;

		var addBtn = panel.querySelector('.btn-add-to-cart');
		if (!addBtn) return;

		addBtn.addEventListener('click', function (e) {
			// Stop the original immersive.js handler from firing.
			e.stopImmediatePropagation();
			e.preventDefault();

			var productId = null;
			var size = '';

			// Get product ID from the currently focused hotspot's data.
			var activeHotspot = document.querySelector('.hotspot:focus, .hotspot[aria-current="true"]');
			if (activeHotspot) {
				productId = activeHotspot.getAttribute('data-product-id');
			}

			// Fall back: check the panel's view-details link for product context.
			if (!productId) {
				var detailsLink = panel.querySelector('.btn-view-details');
				if (detailsLink && detailsLink.href) {
					// Product ID may be stored in a data attribute by applyLiveData.
					var allHotspots = document.querySelectorAll('.hotspot[data-product-url]');
					for (var i = 0; i < allHotspots.length; i++) {
						if (allHotspots[i].getAttribute('data-product-url') === detailsLink.href) {
							productId = allHotspots[i].getAttribute('data-product-id');
							break;
						}
					}
				}
			}

			// Get selected size.
			var sizeContainer = panel.querySelector('.product-panel-sizes');
			if (sizeContainer) {
				var selectedBtn = sizeContainer.querySelector('.size-btn.selected');
				if (selectedBtn) {
					size = selectedBtn.textContent.trim();
				}
			}

			if (!productId) {
				showToast('Please visit the product page to add this item.');
				return;
			}

			// Disable button during request.
			addBtn.disabled = true;
			var originalText = addBtn.textContent;
			addBtn.textContent = 'Adding...';

			liveAddToCart(productId, size, function (success) {
				addBtn.disabled = false;
				if (success) {
					addBtn.textContent = 'Added!';
					setTimeout(function () {
						addBtn.textContent = originalText;
					}, 2000);
				} else {
					addBtn.textContent = originalText;
				}
			});
		}, true); // Capturing phase to fire before immersive.js handler.
	}

	/* --------------------------------------------------
	   Public API (optional, for other scripts to use)
	   -------------------------------------------------- */

	window.skyyRoseWcBridge = {
		fetchProductBySku: fetchProductBySku,
		liveAddToCart: liveAddToCart,
		enhanceHotspots: enhanceHotspots,
		getCache: function () { return productCache; },
	};

	/* --------------------------------------------------
	   Initialize
	   -------------------------------------------------- */

	function init() {
		enhanceHotspots();
		interceptAddToCart();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
