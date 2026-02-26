/**
 * Immersive Collection Experience
 *
 * Handles hotspot interactions, product panel slide-up,
 * multi-room scene transitions, loading screen, keyboard
 * navigation, and touch/swipe support.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 */

(function () {
	'use strict';

	/* Image fallback handled by navigation.js (site-wide). */

	/* --------------------------------------------------
	   DOM References
	   -------------------------------------------------- */

	var scene         = document.querySelector('.immersive-scene');
	var loading       = document.querySelector('.scene-loading');
	var viewport      = document.querySelector('.scene-viewport');
	var layers        = viewport ? Array.from(viewport.querySelectorAll('.scene-layer')) : [];
	var hotspotGroups = scene ? Array.from(scene.querySelectorAll('.hotspot-container')) : [];
	var allHotspots   = scene ? Array.from(scene.querySelectorAll('.hotspot')) : [];
	var titleOverlay  = document.querySelector('.scene-title-overlay');

	// Product panel
	var panelOverlay  = document.querySelector('.product-panel-overlay');
	var panel         = document.querySelector('.product-panel');
	var panelClose    = document.querySelector('.product-panel-close');
	var panelThumb    = panel ? panel.querySelector('.product-panel-thumb img') : null;
	var panelName     = panel ? panel.querySelector('.product-panel-name') : null;
	var panelPrice    = panel ? panel.querySelector('.product-panel-price') : null;
	var panelCol      = panel ? panel.querySelector('.product-panel-collection') : null;
	var panelProp     = panel ? panel.querySelector('.product-panel-prop') : null;
	var panelSizes    = panel ? panel.querySelector('.product-panel-sizes') : null;
	var panelDetails  = panel ? panel.querySelector('.btn-view-details') : null;

	// Room navigation
	var prevBtn       = scene ? scene.querySelector('.room-nav-prev .room-nav-btn') : null;
	var nextBtn       = scene ? scene.querySelector('.room-nav-next .room-nav-btn') : null;
	var dots          = scene ? Array.from(scene.querySelectorAll('.room-dot')) : [];
	var roomNameEl    = scene ? scene.querySelector('.room-name') : null;

	var currentRoom     = 0;
	var totalRooms      = layers.length;
	var isTransitioning = false;
	var lastFocused     = null;

	/* --------------------------------------------------
	   Loading Screen
	   -------------------------------------------------- */

	function dismissLoading() {
		if (!loading) return;
		loading.classList.add('hidden');
	}

	function initLoading() {
		if (!loading || !viewport) return;

		var firstImg = viewport.querySelector('.scene-layer.active img');
		if (!firstImg) {
			dismissLoading();
			return;
		}

		if (firstImg.complete && firstImg.naturalWidth > 0) {
			// Image already cached — short delay for polish.
			setTimeout(dismissLoading, 400);
		} else {
			firstImg.addEventListener('load', function () {
				setTimeout(dismissLoading, 300);
			});
			// Fallback timeout in case image stalls.
			setTimeout(dismissLoading, 5000);
		}
	}

	/* --------------------------------------------------
	   Title Auto-Hide
	   -------------------------------------------------- */

	function initTitleAutoHide() {
		if (!titleOverlay) return;
		setTimeout(function () {
			titleOverlay.classList.add('hidden');
		}, 4000);
	}

	/* --------------------------------------------------
	   Product Panel
	   -------------------------------------------------- */

	function openPanel(data) {
		if (!panel || !panelOverlay) return;

		if (panelThumb)   panelThumb.src = data.image || '';
		if (panelThumb)   panelThumb.alt = data.name || '';
		if (panelName)    panelName.textContent = data.name || '';
		if (panelPrice)   panelPrice.textContent = data.price || '';
		if (panelCol)     panelCol.textContent = data.collection || '';
		if (panelProp)    panelProp.textContent = data.propLabel || '';
		if (panelProp)    panelProp.style.display = data.propLabel ? '' : 'none';
		if (panelDetails) {
			if (data.url && data.url !== '#') {
				panelDetails.href = data.url;
				panelDetails.style.display = '';
			} else {
				panelDetails.style.display = 'none';
			}
		}

		// Populate sizes
		if (panelSizes) {
			panelSizes.innerHTML = '';
			var sizes = (data.sizes || '').split(',').filter(Boolean);
			sizes.forEach(function (size) {
				var btn = document.createElement('button');
				btn.type = 'button';
				btn.className = 'size-btn';
				btn.textContent = size.trim();
				btn.addEventListener('click', function () {
					panelSizes.querySelectorAll('.size-btn').forEach(function (b) {
						b.classList.remove('selected');
					});
					btn.classList.add('selected');
				});
				panelSizes.appendChild(btn);
			});
		}

		panel.classList.add('open');
		panelOverlay.classList.add('open');
		panelOverlay.setAttribute('aria-hidden', 'false');
		panel.setAttribute('aria-hidden', 'false');

		// Store product ID on panel for cross-script access (immersive-wc-bridge.js).
		if (data.productId) {
			panel.dataset.currentProductId = data.productId;
		}

		// Focus trap: move focus into panel.
		if (panelClose) panelClose.focus();
	}

	function closePanel() {
		if (!panel || !panelOverlay) return;

		panel.classList.remove('open');
		panelOverlay.classList.remove('open');
		panelOverlay.setAttribute('aria-hidden', 'true');
		panel.setAttribute('aria-hidden', 'true');

		// Restore focus to the hotspot that opened the panel.
		if (lastFocused) {
			lastFocused.focus();
			lastFocused = null;
		}
	}

	/**
	 * Trap Tab focus within the product panel while it is open.
	 */
	function handlePanelKeydown(e) {
		if (e.key !== 'Tab' || !panel) return;

		var focusable = panel.querySelectorAll(
			'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
		);
		if (focusable.length === 0) return;

		var first = focusable[0];
		var last  = focusable[focusable.length - 1];

		if (e.shiftKey) {
			if (document.activeElement === first) {
				e.preventDefault();
				last.focus();
			}
		} else {
			if (document.activeElement === last) {
				e.preventDefault();
				first.focus();
			}
		}
	}

	function initPanel() {
		if (panelClose) {
			panelClose.addEventListener('click', closePanel);
		}

		if (panelOverlay) {
			panelOverlay.addEventListener('click', closePanel);
		}

		// Focus trap within the product panel.
		if (panel) {
			panel.addEventListener('keydown', handlePanelKeydown);
		}
	}

	/* --------------------------------------------------
	   Hotspot Interactions
	   -------------------------------------------------- */

	function initHotspots() {
		allHotspots.forEach(function (hotspot) {
			hotspot.addEventListener('click', function (e) {
				e.preventDefault();

				lastFocused = hotspot;

				// Track product ID for add-to-cart.
				currentProductId = hotspot.dataset.productId || null;

				var productData = {
					name:       hotspot.dataset.productName,
					price:      hotspot.dataset.productPrice,
					image:      hotspot.dataset.productImage,
					collection: hotspot.dataset.productCollection,
					sizes:      hotspot.dataset.productSizes,
					url:        hotspot.dataset.productUrl,
					propLabel:  hotspot.dataset.propLabel || ''
				};

				openPanel(productData);

				// Analytics: dispatch hotspot click event for analytics-beacon.js.
				trackHotspotEvent('hotspot_click', {
					product_id:   hotspot.dataset.productId,
					product_name: hotspot.dataset.productName,
					product_price: hotspot.dataset.productPrice,
					collection:   hotspot.dataset.productCollection,
					room:         getCurrentRoomName()
				});
			});
		});
	}

	/**
	 * Dispatch a conversion event for the analytics beacon.
	 */
	function trackHotspotEvent(eventName, data) {
		try {
			document.dispatchEvent(new CustomEvent('cie:event', {
				detail: {
					type:      eventName,
					category:  'immersive',
					timestamp: Date.now(),
					data:      data
				}
			}));
		} catch (e) {
			// Silently fail if CustomEvent is not supported.
		}
	}

	/**
	 * Get the current room name for analytics context.
	 */
	function getCurrentRoomName() {
		if (roomNameEl) return roomNameEl.textContent || '';
		if (layers[currentRoom]) return layers[currentRoom].dataset.roomName || '';
		return '';
	}

	/* --------------------------------------------------
	   Room Navigation
	   -------------------------------------------------- */

	function goToRoom(index) {
		if (isTransitioning || index === currentRoom || index < 0 || index >= totalRooms) return;

		isTransitioning = true;

		// Reset parallax transform on outgoing layer.
		var outgoingImg = layers[currentRoom].querySelector('img');
		if (outgoingImg) {
			outgoingImg.style.transform = '';
		}

		// Fade layers
		layers[currentRoom].classList.remove('active');
		layers[index].classList.add('active');

		// Swap hotspot containers
		if (hotspotGroups.length > 1) {
			hotspotGroups[currentRoom].style.display = 'none';
			hotspotGroups[index].style.display = '';
		}

		// Update dots
		if (dots.length > 0) {
			dots[currentRoom].classList.remove('active');
			dots[index].classList.add('active');
		}

		// Update room name
		var newRoomName = layers[index].dataset.roomName || '';
		if (roomNameEl) {
			roomNameEl.textContent = newRoomName;
		}

		currentRoom = index;

		// Unlock after crossfade completes.
		setTimeout(function () {
			isTransitioning = false;
		}, 650);
	}

	function initRoomNav() {
		if (totalRooms <= 1) {
			// Single-room page — hide room nav elements.
			var navPrev = scene ? scene.querySelector('.room-nav-prev') : null;
			var navNext = scene ? scene.querySelector('.room-nav-next') : null;
			var indicators = scene ? scene.querySelector('.room-indicators') : null;
			if (navPrev) navPrev.style.display = 'none';
			if (navNext) navNext.style.display = 'none';
			if (indicators) indicators.style.display = 'none';
			if (roomNameEl) roomNameEl.style.display = 'none';
			return;
		}

		if (prevBtn) {
			prevBtn.addEventListener('click', function () {
				var target = currentRoom === 0 ? totalRooms - 1 : currentRoom - 1;
				goToRoom(target);
			});
		}

		if (nextBtn) {
			nextBtn.addEventListener('click', function () {
				var target = currentRoom === totalRooms - 1 ? 0 : currentRoom + 1;
				goToRoom(target);
			});
		}

		dots.forEach(function (dot, i) {
			dot.addEventListener('click', function () {
				goToRoom(i);
			});
		});
	}

	/* --------------------------------------------------
	   Keyboard Navigation
	   -------------------------------------------------- */

	function initKeyboard() {
		document.addEventListener('keydown', function (e) {
			// Close panel on Escape.
			if (e.key === 'Escape') {
				closePanel();
				return;
			}

			// Room navigation with arrow keys (only when panel is closed).
			if (panel && panel.classList.contains('open')) return;

			if (totalRooms > 1) {
				if (e.key === 'ArrowLeft') {
					var prev = currentRoom === 0 ? totalRooms - 1 : currentRoom - 1;
					goToRoom(prev);
				} else if (e.key === 'ArrowRight') {
					var next = currentRoom === totalRooms - 1 ? 0 : currentRoom + 1;
					goToRoom(next);
				}
			}
		});
	}

	/* --------------------------------------------------
	   Touch / Swipe Support
	   -------------------------------------------------- */

	function initSwipe() {
		if (!scene || totalRooms <= 1) return;

		var startX = 0;
		var startY = 0;
		var threshold = 50;

		scene.addEventListener('touchstart', function (e) {
			startX = e.changedTouches[0].clientX;
			startY = e.changedTouches[0].clientY;
		}, { passive: true });

		scene.addEventListener('touchend', function (e) {
			var dx = e.changedTouches[0].clientX - startX;
			var dy = e.changedTouches[0].clientY - startY;

			// Only trigger horizontal swipe, ignore vertical scrolls.
			if (Math.abs(dx) < threshold || Math.abs(dy) > Math.abs(dx)) return;

			if (dx < 0) {
				// Swipe left → next room
				var next = currentRoom === totalRooms - 1 ? 0 : currentRoom + 1;
				goToRoom(next);
			} else {
				// Swipe right → prev room
				var prev = currentRoom === 0 ? totalRooms - 1 : currentRoom - 1;
				goToRoom(prev);
			}
		}, { passive: true });
	}

	/* --------------------------------------------------
	   Enhanced Room Transitions (Crossfade)
	   -------------------------------------------------- */

	function initEnhancedTransitions() {
		if (totalRooms <= 1) return;

		// Ensure all layers have GPU-accelerated transitions.
		layers.forEach(function (layer) {
			layer.style.willChange = 'opacity';
		});
	}

	/* --------------------------------------------------
	   Parallax Depth Effect (Desktop Only)
	   -------------------------------------------------- */

	function initParallax() {
		if (!viewport) return;

		// Detect touch-primary devices and skip parallax.
		var isTouchDevice = window.matchMedia('(hover: none)').matches;
		if (isTouchDevice) return;

		var parallaxStrength = 0.025; // 2.5% max shift
		var ticking = false;
		var targetX = 0;
		var targetY = 0;
		var currentX = 0;
		var currentY = 0;

		scene.addEventListener('mousemove', function (e) {
			// Normalize mouse position to -1..1 from center.
			var rect = scene.getBoundingClientRect();
			targetX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
			targetY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;

			if (!ticking) {
				ticking = true;
				requestAnimationFrame(applyParallax);
			}
		});

		scene.addEventListener('mouseleave', function () {
			targetX = 0;
			targetY = 0;
			if (!ticking) {
				ticking = true;
				requestAnimationFrame(applyParallax);
			}
		});

		function applyParallax() {
			// Smooth lerp toward target for fluid feel.
			currentX += (targetX - currentX) * 0.08;
			currentY += (targetY - currentY) * 0.08;

			var shiftX = -(currentX * parallaxStrength * 100);
			var shiftY = -(currentY * parallaxStrength * 100);

			// Apply subtle translate to the active scene layer image.
			var activeLayer = viewport.querySelector('.scene-layer.active');
			if (activeLayer) {
				var img = activeLayer.querySelector('img');
				if (img) {
					img.style.transform = 'scale(1.04) translate(' + shiftX.toFixed(2) + '%, ' + shiftY.toFixed(2) + '%)';
				}
			}

			// Continue animation if not at rest.
			var distX = Math.abs(targetX - currentX);
			var distY = Math.abs(targetY - currentY);
			if (distX > 0.001 || distY > 0.001) {
				requestAnimationFrame(applyParallax);
			} else {
				ticking = false;
			}
		}
	}

	/* --------------------------------------------------
	   Cinematic Mode Integration
	   -------------------------------------------------- */

	function initCinematicIntegration() {
		if (!scene) return;

		var cinematicToggle = document.querySelector('.cinematic-toggle');
		if (!cinematicToggle) return;

		// Sync initial state: if body already has cinematic-mode
		// (restored from sessionStorage by cinematic-mode.js), apply to scene.
		if (document.body.classList.contains('cinematic-mode')) {
			scene.classList.add('cinematic-active');
		}

		// Listen for clicks on the toggle to mirror the class.
		cinematicToggle.addEventListener('click', function () {
			// cinematic-mode.js toggles body class first; read after microtask.
			setTimeout(function () {
				if (document.body.classList.contains('cinematic-mode')) {
					scene.classList.add('cinematic-active');
				} else {
					scene.classList.remove('cinematic-active');
				}
			}, 0);
		});

		// Also listen for Escape to exit cinematic mode.
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape' && scene.classList.contains('cinematic-active')) {
				scene.classList.remove('cinematic-active');
				// Sync body state too.
				document.body.classList.remove('cinematic-mode');
				cinematicToggle.setAttribute('aria-pressed', 'false');
				try { sessionStorage.removeItem('skyyrose_cinematic_mode'); } catch (err) { /* quota */ }
			}
		});
	}

	/* --------------------------------------------------
	   Add-to-Cart (Pre-Order) via WooCommerce AJAX
	   -------------------------------------------------- */

	var panelAddToCart = panel ? panel.querySelector('.btn-add-to-cart') : null;
	var currentProductId = null;

	function initAddToCart() {
		if (!panelAddToCart) return;

		panelAddToCart.addEventListener('click', function () {
			if (!currentProductId) return;

			// Check if WooCommerce AJAX endpoint is available.
			var wcAjaxUrl = getWcAjaxUrl();
			if (!wcAjaxUrl) {
				showCartNotification('Pre-order unavailable. Please visit the product page.');
				return;
			}

			panelAddToCart.disabled = true;
			var originalText = panelAddToCart.textContent;
			panelAddToCart.textContent = 'Adding...';

			var xhr = new XMLHttpRequest();
			xhr.open('POST', wcAjaxUrl + '?wc-ajax=add_to_cart', true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			// Get selected size before sending request (must be before onload to avoid hoisting issue).
			var selectedSize = '';
			if (panelSizes) {
				var selectedBtn = panelSizes.querySelector('.size-btn.selected');
				if (selectedBtn) {
					selectedSize = selectedBtn.textContent;
				}
			}

			xhr.onload = function () {
				panelAddToCart.disabled = false;
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var response = JSON.parse(xhr.responseText);
						if (response.error) {
							showCartNotification('Could not add item. Please try from the product page.');
						} else {
							panelAddToCart.textContent = 'Added!';
							showCartNotification('Added to pre-order cart!');
							// Analytics: track successful add-to-cart.
							trackHotspotEvent('add_to_cart', {
								product_id:    currentProductId,
								product_name:  panelName ? panelName.textContent : '',
								product_price: panelPrice ? panelPrice.textContent : '',
								size:          selectedSize,
								room:          getCurrentRoomName()
							});
							// Trigger WooCommerce cart fragment refresh.
							if (typeof jQuery !== 'undefined') {
								jQuery(document.body).trigger('wc_fragment_refresh');
							}
							setTimeout(function () {
								panelAddToCart.textContent = originalText;
							}, 2000);
							return;
						}
					} catch (e) {
						showCartNotification('Could not add item. Please try from the product page.');
					}
				} else {
					showCartNotification('Could not add item. Please try from the product page.');
				}
				panelAddToCart.textContent = originalText;
			};

			xhr.onerror = function () {
				panelAddToCart.disabled = false;
				panelAddToCart.textContent = originalText;
				showCartNotification('Network error. Please try again.');
			};

			var postData = 'product_id=' + encodeURIComponent(currentProductId) +
				'&quantity=1';
			if (selectedSize) {
				postData += '&attribute_pa_size=' + encodeURIComponent(selectedSize);
			}
			xhr.send(postData);
		});
	}

	/**
	 * Determine the WooCommerce AJAX URL. WordPress.com uses
	 * index.php?rest_route= but the wc-ajax endpoint is on the
	 * standard site URL as a query parameter.
	 */
	function getWcAjaxUrl() {
		// wc_add_to_cart_params is localized by WooCommerce when active.
		if (typeof wc_add_to_cart_params !== 'undefined' && wc_add_to_cart_params.wc_ajax_url) {
			return wc_add_to_cart_params.wc_ajax_url.toString().replace('%%endpoint%%', 'add_to_cart');
		}
		// No fallback — WP.com routing requires the localized URL.
		return null;
	}

	function showCartNotification(message) {
		// Reuse existing notification or create one.
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
		}, 3000);
	}

	/* --------------------------------------------------
	   Hotspot Hover Preview Tooltip
	   -------------------------------------------------- */

	function initHotspotPreview() {
		allHotspots.forEach(function (hotspot) {
			// Skip if this hotspot already has a label element.
			if (hotspot.querySelector('.hotspot-label')) return;

			var productName = hotspot.dataset.productName;
			if (!productName) return;

			var tooltip = document.createElement('span');
			tooltip.className = 'hotspot-label hotspot-label--generated';
			tooltip.setAttribute('aria-hidden', 'true');

			// Show product name + price (as per directive: "Hover: name + price tooltip").
			var productPrice = hotspot.dataset.productPrice || '';
			var nameSpan = document.createElement('span');
			nameSpan.className = 'hotspot-label-name';
			nameSpan.textContent = productName;
			tooltip.appendChild(nameSpan);

			if (productPrice) {
				var priceSpan = document.createElement('span');
				priceSpan.className = 'hotspot-label-price';
				priceSpan.textContent = productPrice;
				tooltip.appendChild(priceSpan);
			}

			hotspot.appendChild(tooltip);
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		if (!scene) return;

		initLoading();
		initTitleAutoHide();
		initPanel();
		initHotspots();
		initRoomNav();
		initKeyboard();
		initSwipe();
		initEnhancedTransitions();
		initParallax();
		initCinematicIntegration();
		initAddToCart();
		initHotspotPreview();
	}

	// Run when DOM is ready.
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
