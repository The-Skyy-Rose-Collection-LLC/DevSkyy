/**
 * Holo Product Card — Interactive Layer
 *
 * Progressive enhancement: magnetic 3D tilt, holographic shimmer tracking,
 * IntersectionObserver entrance animation, quick-add drawer, wishlist toggle.
 *
 * Requires: product-card-holo.css for visual output.
 * No dependencies — vanilla JS, ~6KB unminified.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

(function () {
	'use strict';

	/* ──────────────────────────────────────────────
	   CONSTANTS
	   ────────────────────────────────────────────── */

	var MAX_TILT = 8;                  // degrees
	var TOUCH = matchMedia('(hover: none)').matches;
	var REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ──────────────────────────────────────────────
	   1. SCROLL ENTRANCE — IntersectionObserver
	   ────────────────────────────────────────────── */

	function initEntrance() {
		var cards = document.querySelectorAll('.holo:not(.holo--visible)');
		if (!cards.length) return;

		if (!('IntersectionObserver' in window)) {
			cards.forEach(function (c) { c.classList.add('holo--visible'); });
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('holo--visible');
					observer.unobserve(entry.target);
				}
			});
		}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

		cards.forEach(function (card) { observer.observe(card); });
	}

	/* ──────────────────────────────────────────────
	   2. MAGNETIC TILT + HOLOGRAPHIC TRACKING
	   ────────────────────────────────────────────── */

	function initTilt() {
		if (TOUCH || REDUCED) return;

		document.querySelectorAll('.holo').forEach(function (card) {
			var body = card.querySelector('.holo__body');
			if (!body) return;

			card.addEventListener('mousemove', function (e) {
				var rect = card.getBoundingClientRect();
				var x = (e.clientX - rect.left) / rect.width;   // 0→1
				var y = (e.clientY - rect.top) / rect.height;    // 0→1

				// Tilt: map [0,1] to [-MAX, +MAX] degrees
				var tiltX = ((y - 0.5) * -2 * MAX_TILT).toFixed(2);
				var tiltY = ((x - 0.5) * 2 * MAX_TILT).toFixed(2);

				// Holographic angle: angle from center
				var angle = (Math.atan2(y - 0.5, x - 0.5) * (180 / Math.PI) + 180).toFixed(1);

				body.style.setProperty('--tilt-x', tiltX + 'deg');
				body.style.setProperty('--tilt-y', tiltY + 'deg');
				body.style.setProperty('--holo-x', (x * 100).toFixed(1) + '%');
				body.style.setProperty('--holo-y', (y * 100).toFixed(1) + '%');
				body.style.setProperty('--holo-angle', angle + 'deg');
			});

			card.addEventListener('mouseleave', function () {
				// Spring back to neutral — CSS transition handles easing
				body.style.setProperty('--tilt-x', '0deg');
				body.style.setProperty('--tilt-y', '0deg');
			});
		});
	}

	/* ──────────────────────────────────────────────
	   3. WISHLIST TOGGLE (localStorage)
	   ────────────────────────────────────────────── */

	var WISHLIST_KEY = 'skyyrose_wishlist';

	function getWishlist() {
		try {
			return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || [];
		} catch (e) {
			return [];
		}
	}

	function saveWishlist(list) {
		try {
			localStorage.setItem(WISHLIST_KEY, JSON.stringify(list));
		} catch (e) { /* quota exceeded — fail silently */ }
	}

	function initWishlist() {
		var list = getWishlist();

		document.querySelectorAll('.holo__wishlist').forEach(function (btn) {
			var id = btn.getAttribute('data-wishlist-id');
			if (!id) return;

			// Restore state
			if (list.indexOf(id) !== -1) {
				btn.setAttribute('aria-pressed', 'true');
			}

			btn.addEventListener('click', function (e) {
				e.preventDefault();
				e.stopPropagation();

				var current = getWishlist();
				var idx = current.indexOf(id);
				var active = idx !== -1;

				if (active) {
					current.splice(idx, 1);
					btn.setAttribute('aria-pressed', 'false');
				} else {
					current.push(id);
					btn.setAttribute('aria-pressed', 'true');
					// Burst animation
					btn.classList.add('holo__wishlist--burst');
					btn.addEventListener('animationend', function () {
						btn.classList.remove('holo__wishlist--burst');
					}, { once: true });
				}

				saveWishlist(current);

				// Dispatch event for other systems (analytics, badge count)
				document.dispatchEvent(new CustomEvent('skyyrose:wishlist', {
					detail: { id: id, action: active ? 'remove' : 'add' }
				}));
			});
		});
	}

	/* ──────────────────────────────────────────────
	   4. QUICK-ADD DRAWER — Size selection + AJAX cart
	   ────────────────────────────────────────────── */

	function initDrawer() {
		// Size pill selection
		document.querySelectorAll('.holo__sizes').forEach(function (group) {
			var pills = group.querySelectorAll('.holo__size-pill');
			var card = group.closest('.holo');
			var buyBtn = card ? card.querySelector('.holo__buy') : null;

			pills.forEach(function (pill) {
				pill.addEventListener('click', function () {
					// Deselect siblings
					pills.forEach(function (p) {
						p.classList.remove('holo__size-pill--active');
						p.setAttribute('aria-checked', 'false');
					});

					// Select this
					pill.classList.add('holo__size-pill--active');
					pill.setAttribute('aria-checked', 'true');

					// Enable buy button
					if (buyBtn) {
						buyBtn.disabled = false;
					}
				});
			});
		});

		// Buy button AJAX
		document.querySelectorAll('.holo__buy[data-product-id]').forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.preventDefault();
				if (btn.disabled) return;

				var productId = btn.getAttribute('data-product-id');
				var card = btn.closest('.holo');
				var selectedSize = card ? card.querySelector('.holo__size-pill--active') : null;
				var size = selectedSize ? selectedSize.getAttribute('data-size') : '';

				// Loading state
				var originalText = btn.textContent;
				btn.classList.add('holo__buy--loading');
				btn.textContent = '';

				// Build request
				var formData = new FormData();
				formData.append('product_id', productId);
				formData.append('quantity', '1');
				if (size) {
					formData.append('attribute_pa_size', size);
				}

				// Use WC AJAX add-to-cart endpoint
				var ajaxUrl = (typeof wc_add_to_cart_params !== 'undefined')
					? wc_add_to_cart_params.wc_ajax_url.replace('%%endpoint%%', 'add_to_cart')
					: '/?wc-ajax=add_to_cart';

				fetch(ajaxUrl, {
					method: 'POST',
					body: formData,
					credentials: 'same-origin'
				})
				.then(function (res) { return res.json(); })
				.then(function (data) {
					btn.classList.remove('holo__buy--loading');

					if (data.error) {
						btn.classList.add('holo__buy--error');
						btn.textContent = 'Error';
						setTimeout(function () {
							btn.classList.remove('holo__buy--error');
							btn.textContent = originalText;
						}, 2000);
						return;
					}

					// Success
					btn.classList.add('holo__buy--added');
					btn.textContent = 'Added ✓';

					// Update WC fragments (mini-cart count etc.)
					if (data.fragments) {
						jQuery(document.body).trigger('added_to_cart', [data.fragments, data.cart_hash, jQuery(btn)]);
					}

					// Reset after delay
					setTimeout(function () {
						btn.classList.remove('holo__buy--added');
						btn.textContent = originalText;
					}, 2500);
				})
				.catch(function () {
					btn.classList.remove('holo__buy--loading');
					btn.textContent = originalText;
				});
			});
		});
	}

	/* ──────────────────────────────────────────────
	   5. INIT — Wait for DOM
	   ────────────────────────────────────────────── */

	function init() {
		initEntrance();
		initTilt();
		initWishlist();
		initDrawer();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
