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
		var useSku = true;

		if (!hotspots.length) {
			// Fall back: try hotspots with data-product-id only.
			hotspots = document.querySelectorAll('.hotspot[data-product-id]');
			useSku = false;
		}

		if (!hotspots.length) {
			return;
		}

		// Collect unique SKUs to avoid duplicate requests.
		var skuHotspotMap = {};

		for (var i = 0; i < hotspots.length; i++) {
			var hotspot = hotspots[i];
			var sku = useSku
				? hotspot.getAttribute('data-product-sku')
				: hotspot.getAttribute('data-product-id');

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
		if (data.price) {
			var rawPrice = String(data.price).replace(/^\$/, '');
			hotspot.setAttribute('data-product-price', '$' + rawPrice);
		}
		if (data.image_url) hotspot.setAttribute('data-product-image', data.image_url);
		if (data.permalink) hotspot.setAttribute('data-product-url', data.permalink);
		if (data.id) hotspot.setAttribute('data-product-id', data.id);

		// Build sizes string from array.
		if (data.sizes && data.sizes.length) {
			hotspot.setAttribute('data-product-sizes', data.sizes.join(','));
		}

		// Sync price if it changed and the product panel is showing this item.
		var newPrice = '$' + String(data.price || '').replace(/^\$/, '');
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
	 * @param {string}      sku        Product SKU (e.g., 'br-006').
	 * @param {string|null} size       Optional size attribute value.
	 * @param {Function}    onComplete Called when the request finishes (success or error).
	 */
	function liveAddToCart(sku, size, onComplete) {
		if (!sku) {
			showToast('Unable to add item. Please try from the product page.');
			if (onComplete) onComplete(false);
			return;
		}

		var params = {
			sku: sku,
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

				// Update cart count badge via WC fragments (selector allowlist).
				if (data.fragments) {
					var numericSelectors = [
						'.cart-count-badge', '.navbar__cart-badge',
						'.cart-count', '.cart-subtotal'
					];
					for (var selector in data.fragments) {
						if (!data.fragments.hasOwnProperty(selector)) continue;
						var isNumeric = false;
						for (var a = 0; a < numericSelectors.length; a++) {
							if (selector === numericSelectors[a]) { isNumeric = true; break; }
						}
						if (!isNumeric) continue; // HTML widget selectors handled by WC jQuery fragment refresh below.
						try {
							var targets = document.querySelectorAll(selector);
							// Extract text only — strip HTML tags without innerHTML parsing (CSP safe).
							var rawHtml = String(data.fragments[selector] || '');
							var text = rawHtml.replace(/<[^>]*>/g, '').trim();
							for (var i = 0; i < targets.length; i++) {
								targets[i].textContent = text;
							}
						} catch (e) { /* invalid selector — skip */ }
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
	var toastTimer = 0;

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

		// Clear any pending hide so rapid calls don't cut the new toast short.
		clearTimeout(toastTimer);
		toastTimer = setTimeout(function () {
			notification.classList.remove('visible');
		}, 3500);
	}

	/* --------------------------------------------------
	   Intercept Add-to-Cart Button
	   -------------------------------------------------- */

	/**
	 * Override the product panel add-to-cart button to use the
	 * dedicated immersive AJAX endpoint (SKU-based) instead of
	 * the generic WooCommerce wc-ajax endpoint.
	 */
	function interceptAddToCart() {
		var panel = document.querySelector('.product-panel');
		if (!panel) return;

		var addBtn = panel.querySelector('.btn-add-to-cart');
		if (!addBtn) return;

		addBtn.addEventListener('click', function (e) {
			e.preventDefault();

			var productSku = '';
			var size = '';

			// Read product SKU from panel data attribute (set by immersive.js openPanel).
			// Prefer currentProductSku (actual SKU string) over currentProductId (numeric WC ID).
			if (panel.dataset.currentProductSku) {
				productSku = panel.dataset.currentProductSku;
			} else if (panel.dataset.currentProductId) {
				// Fallback: resolve numeric ID to SKU via hotspot data-product-sku attribute.
				var matchingHotspot = document.querySelector('.hotspot[data-product-id="' + panel.dataset.currentProductId + '"]');
				productSku = matchingHotspot ? (matchingHotspot.getAttribute('data-product-sku') || '') : '';
			}

			// Fall back: focused or active hotspot.
			if (!productSku) {
				var activeHotspot = document.querySelector('.hotspot:focus, .hotspot[aria-current="true"]');
				if (activeHotspot) {
					productSku = activeHotspot.getAttribute('data-product-sku')
						|| activeHotspot.getAttribute('data-product-id')
						|| '';
				}
			}

			// Fall back: check the panel's view-details link for product context.
			if (!productSku) {
				var detailsLink = panel.querySelector('.btn-view-details');
				if (detailsLink && detailsLink.href) {
					var allHotspots = document.querySelectorAll('.hotspot[data-product-sku], .hotspot[data-product-id]');
					for (var i = 0; i < allHotspots.length; i++) {
						if (allHotspots[i].getAttribute('data-product-url') === detailsLink.href) {
							productSku = allHotspots[i].getAttribute('data-product-sku')
								|| allHotspots[i].getAttribute('data-product-id')
								|| '';
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

			if (!productSku) {
				showToast('Please visit the product page to add this item.');
				return;
			}

			// Disable button during request.
			addBtn.disabled = true;
			var originalText = addBtn.textContent;
			addBtn.textContent = 'Adding...';

			liveAddToCart(productSku, size, function (success) {
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
		}); // Bubble phase — sole add-to-cart handler (immersive.js initAddToCart removed in v3.2.4).
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
