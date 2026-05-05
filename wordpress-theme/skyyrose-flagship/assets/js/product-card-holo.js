/**
 * Holo Product Card — Interactive Layer
 *
 * Progressive enhancement: magnetic 3D tilt, holographic shimmer tracking,
 * IntersectionObserver entrance animation, quick-add drawer, wishlist toggle.
 *
 * Requires: product-card-holo.css for visual output.
 * No dependencies — vanilla JS, ~6KB unminified.
 *
 * @package SkyyRose
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

	// Restore an aria-label captured before a transient state change.
	// If the element had no aria-label originally, removeAttribute lets the
	// (now-restored) textContent become the a11y name.
	function restoreAriaLabel(el, original) {
		if (original === null || typeof original === 'undefined') {
			el.removeAttribute('aria-label');
		} else {
			el.setAttribute('aria-label', original);
		}
	}

	/* ──────────────────────────────────────────────
	   1. SCROLL ENTRANCE — IntersectionObserver
	   ────────────────────────────────────────────── */

	function initEntrance() {
		/* Delay slightly to ensure layout is calculated after deferred script load */
		setTimeout(function () {
			var cards = document.querySelectorAll('.holo:not(.holo--visible)');
			if (!cards.length) return;

			if (!('IntersectionObserver' in window)) {
				cards.forEach(function (c) { c.classList.add('holo--visible'); });
				return;
			}

			var staggerIdx = 0;
			var observer = new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.style.setProperty('--holo-delay', (staggerIdx * 80) + 'ms');
						entry.target.classList.add('holo--visible');
						staggerIdx++;
						observer.unobserve(entry.target);
					}
				});
			}, { threshold: 0.05, rootMargin: '0px 0px 50px 0px' });

			cards.forEach(function (card) { observer.observe(card); });
		}, 100);
	}

	/* ──────────────────────────────────────────────
	   2. MAGNETIC TILT + HOLOGRAPHIC TRACKING
	   ────────────────────────────────────────────── */

	function initTilt() {
		if (TOUCH || REDUCED) return;

		document.querySelectorAll('.holo').forEach(function (card) {
			var body = card.querySelector('.holo__body');
			if (!body) return;

			// Cache the bounding rect on enter; refresh on resize/scroll only.
			// getBoundingClientRect() forces a layout flush, so calling it on
			// every mousemove (potentially 60+/sec per card) thrashes layout
			// across an entire product grid.
			var rect = null;
			var rafPending = false;
			var lastEvent = null;

			function refreshRect() { rect = card.getBoundingClientRect(); }

			card.addEventListener('mouseenter', refreshRect);
			window.addEventListener('resize', function () { rect = null; }, { passive: true });
			window.addEventListener('scroll', function () { rect = null; }, { passive: true });

			card.addEventListener('mousemove', function (e) {
				lastEvent = e;
				if (rafPending) return;
				rafPending = true;

				requestAnimationFrame(function () {
					rafPending = false;
					if (!lastEvent) return;
					if (!rect) refreshRect();

					var x = (lastEvent.clientX - rect.left) / rect.width;   // 0→1
					var y = (lastEvent.clientY - rect.top) / rect.height;    // 0→1

					var tiltX = ((y - 0.5) * -2 * MAX_TILT).toFixed(2);
					var tiltY = ((x - 0.5) * 2 * MAX_TILT).toFixed(2);
					var angle = (Math.atan2(y - 0.5, x - 0.5) * (180 / Math.PI) + 180).toFixed(1);

					body.style.setProperty('--tilt-x', tiltX + 'deg');
					body.style.setProperty('--tilt-y', tiltY + 'deg');
					body.style.setProperty('--holo-x', (x * 100).toFixed(1) + '%');
					body.style.setProperty('--holo-y', (y * 100).toFixed(1) + '%');
					body.style.setProperty('--holo-angle', angle + 'deg');
				});
			});

			card.addEventListener('mouseleave', function () {
				// Spring back to neutral — CSS transition handles easing
				lastEvent = null;
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

			// Restore state — CSS handles visual via .holo__wishlist--active
			if (list.indexOf(id) !== -1) {
				btn.setAttribute('aria-pressed', 'true');
				btn.classList.add('holo__wishlist--active');
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
					btn.classList.remove('holo__wishlist--active');
				} else {
					current.push(id);
					btn.setAttribute('aria-pressed', 'true');
					btn.classList.add('holo__wishlist--active');
					// Burst animation
					btn.classList.add('holo__wishlist--burst');
					btn.addEventListener('animationend', function () {
						btn.classList.remove('holo__wishlist--burst');
					}, { once: true });
				}

				saveWishlist(current);

				// Toast notification
				if (window.skyyToast) {
					window.skyyToast(active ? 'Removed from wishlist' : 'Added to wishlist', 'info');
				}

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

				// Prevent double-click
				btn.disabled = true;
				btn.setAttribute('aria-busy', 'true');

				var productId = btn.getAttribute('data-product-id');
				var card = btn.closest('.holo');
				var selectedSize = card ? card.querySelector('.holo__size-pill--active') : null;
				var size = selectedSize ? selectedSize.getAttribute('data-size') : '';

				// Loading state. textContent is cleared so the CSS spinner can take
				// over — we set aria-label to keep the button announceable while
				// it has no visible text.
				var originalText = btn.textContent;
				var originalAriaLabel = btn.getAttribute('aria-label');
				btn.classList.add('holo__buy--loading');
				btn.setAttribute('aria-label', 'Adding to cart, please wait');
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
						// textContent is now meaningful — drop the temporary
						// aria-label so the visible text becomes the a11y name.
						restoreAriaLabel(btn, originalAriaLabel);
						setTimeout(function () {
							btn.classList.remove('holo__buy--error');
							btn.textContent = originalText;
							btn.disabled = false;
							btn.removeAttribute('aria-busy');
						}, 2000);
						return;
					}

					// Success
					btn.classList.add('holo__buy--added');
					btn.textContent = 'Added ✓';
					restoreAriaLabel(btn, originalAriaLabel);

					// Update WC fragments (mini-cart count etc.)
					if (data.fragments) {
						jQuery(document.body).trigger('added_to_cart', [data.fragments, data.cart_hash, jQuery(btn)]);
					}

					// Reset after delay
					setTimeout(function () {
						btn.classList.remove('holo__buy--added');
						btn.textContent = originalText;
						btn.disabled = false;
						btn.removeAttribute('aria-busy');
					}, 2500);
				})
				.catch(function () {
					btn.classList.remove('holo__buy--loading');
					btn.textContent = originalText;
					restoreAriaLabel(btn, originalAriaLabel);
					btn.disabled = false;
					btn.removeAttribute('aria-busy');
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
