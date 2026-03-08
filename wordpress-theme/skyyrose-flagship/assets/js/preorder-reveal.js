/**
 * Pre-Order Reveal Cards
 *
 * Countdown timer + dramatic reveal animation for pre-order products.
 * Cards start blurred/locked, count down to a deadline, then reveal
 * with particle burst and pulsing CTA.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

(function () {
	'use strict';

	var PARTICLE_CLEANUP_MS = 2500;

	/**
	 * Check if user prefers reduced motion.
	 */
	function prefersReducedMotion() {
		return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	}

	/* -----------------------------------------------
	   Scroll Reveal (IntersectionObserver)
	   ----------------------------------------------- */

	function initScrollReveal() {
		var cards = document.querySelectorAll('.prc');

		if (!cards.length) return;

		if (prefersReducedMotion()) {
			cards.forEach(function (card) {
				card.classList.add('prc--visible');
			});
			return;
		}

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('prc--visible');
						observer.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.15 }
		);

		cards.forEach(function (card) {
			observer.observe(card);
		});
	}

	/* -----------------------------------------------
	   Countdown + Reveal
	   ----------------------------------------------- */

	function initCountdowns() {
		var cards = document.querySelectorAll('.prc[data-reveal-time]');

		cards.forEach(function (card) {
			var revealTime = card.getAttribute('data-reveal-time');
			if (!revealTime) return;

			var deadline = new Date(revealTime).getTime();

			// If already past deadline, reveal immediately.
			if (Date.now() >= deadline) {
				revealCard(card);
				return;
			}

			// Start countdown interval.
			var interval = setInterval(function () {
				var remaining = deadline - Date.now();

				if (remaining <= 0) {
					clearInterval(interval);
					revealCard(card);
					return;
				}

				updateCountdown(card, remaining);
			}, 1000);

			// Initial update.
			updateCountdown(card, deadline - Date.now());
		});
	}

	/**
	 * Update countdown display values.
	 */
	function updateCountdown(card, remainingMs) {
		var totalSeconds = Math.floor(remainingMs / 1000);
		var days = Math.floor(totalSeconds / 86400);
		var hours = Math.floor((totalSeconds % 86400) / 3600);
		var minutes = Math.floor((totalSeconds % 3600) / 60);
		var seconds = totalSeconds % 60;

		var daysEl = card.querySelector('[data-unit="days"]');
		var hoursEl = card.querySelector('[data-unit="hours"]');
		var minutesEl = card.querySelector('[data-unit="minutes"]');
		var secondsEl = card.querySelector('[data-unit="seconds"]');

		if (daysEl) daysEl.textContent = padZero(days);
		if (hoursEl) hoursEl.textContent = padZero(hours);
		if (minutesEl) minutesEl.textContent = padZero(minutes);
		if (secondsEl) secondsEl.textContent = padZero(seconds);
	}

	/**
	 * Pad single-digit numbers with leading zero.
	 */
	function padZero(n) {
		return n < 10 ? '0' + n : String(n);
	}

	/**
	 * Reveal a pre-order card with particle burst animation.
	 */
	function revealCard(card) {
		// Remove locked state, add revealed.
		card.classList.remove('prc--locked');
		card.classList.add('prc--revealed');

		// Trigger particle burst.
		if (!prefersReducedMotion()) {
			var particles = card.querySelector('.prc__particles');
			if (particles) {
				particles.classList.add('prc__particles--active');

				// Clean up particles after animation completes.
				setTimeout(function () {
					particles.classList.remove('prc__particles--active');
				}, PARTICLE_CLEANUP_MS);
			}
		}
	}

	/* -----------------------------------------------
	   Size Pill Selection (pre-order variant)
	   ----------------------------------------------- */

	function initSizePills() {
		document.addEventListener('click', function (e) {
			var pill = e.target.closest('.prc__size-pill');
			if (!pill) return;

			var card = pill.closest('.prc');
			if (!card) return;

			// Deselect siblings.
			var siblings = card.querySelectorAll('.prc__size-pill');
			siblings.forEach(function (s) {
				s.classList.remove('prc__size-pill--selected');
				s.setAttribute('aria-checked', 'false');
			});

			// Select clicked pill.
			pill.classList.add('prc__size-pill--selected');
			pill.setAttribute('aria-checked', 'true');
			card.setAttribute('data-selected-size', pill.getAttribute('data-size'));
		});

		// Keyboard navigation.
		document.addEventListener('keydown', function (e) {
			var pill = e.target.closest('.prc__size-pill');
			if (!pill) return;

			var pills = Array.from(pill.parentNode.querySelectorAll('.prc__size-pill'));
			var idx = pills.indexOf(pill);
			var next = -1;

			if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
				next = (idx + 1) % pills.length;
			} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
				next = (idx - 1 + pills.length) % pills.length;
			}

			if (next >= 0) {
				e.preventDefault();
				pills[next].focus();
				pills[next].click();
			}
		});
	}

	/* -----------------------------------------------
	   AJAX Quick-Buy (pre-order variant)
	   ----------------------------------------------- */

	function initQuickBuy() {
		document.addEventListener('click', function (e) {
			var btn = e.target.closest('.prc__buy-btn');
			if (!btn) return;

			var card = btn.closest('.prc');
			if (!card) return;

			// Block if card is still locked.
			if (card.classList.contains('prc--locked')) return;

			var sku = btn.getAttribute('data-sku') || card.getAttribute('data-product-sku');
			var size = card.getAttribute('data-selected-size') || '';

			// Require size selection for multi-size products.
			var sizePills = card.querySelectorAll('.prc__size-pill');
			if (sizePills.length > 0 && !size) {
				var sizesContainer = card.querySelector('.prc__sizes');
				if (sizesContainer) {
					sizesContainer.style.outline = '2px solid var(--color-rose-gold, #B76E79)';
					sizesContainer.style.outlineOffset = '2px';
					setTimeout(function () {
						sizesContainer.style.outline = '';
						sizesContainer.style.outlineOffset = '';
					}, 1500);
				}
				return;
			}

			// Check WooCommerce availability.
			if (typeof skyyRoseCards === 'undefined' || !skyyRoseCards.wcActive) {
				btn.textContent = 'Store Unavailable';
				btn.classList.add('prc__buy-btn--loading');
				return;
			}

			var originalText = btn.textContent;
			btn.textContent = 'Adding...';
			btn.classList.add('prc__buy-btn--loading');

			var formData = new FormData();
			formData.append('action', 'skyyrose_immersive_add_to_cart');
			formData.append('sku', sku);
			formData.append('quantity', '1');
			formData.append('nonce', skyyRoseCards.nonce);

			if (size) {
				formData.append('attribute_pa_size', size);
			}

			fetch(skyyRoseCards.ajaxUrl, {
				method: 'POST',
				credentials: 'same-origin',
				body: formData,
			})
				.then(function (response) { return response.json(); })
				.then(function (data) {
					if (data.success) {
						btn.textContent = 'Added!';
						btn.classList.remove('prc__buy-btn--loading');
						btn.classList.add('prc__buy-btn--success');

						if (data.data && data.data.fragments) {
							Object.keys(data.data.fragments).forEach(function (selector) {
								var el = document.querySelector(selector);
								if (el) el.outerHTML = data.data.fragments[selector];
							});
						}
					} else {
						btn.textContent = (data.data && data.data.message) || 'Error';
					}
				})
				.catch(function () {
					btn.textContent = 'Network Error';
				})
				.finally(function () {
					setTimeout(function () {
						btn.classList.remove('prc__buy-btn--loading', 'prc__buy-btn--success');
						btn.textContent = originalText;
					}, 2000);
				});
		});
	}

	/* -----------------------------------------------
	   Initialize
	   ----------------------------------------------- */

	function init() {
		initScrollReveal();
		initCountdowns();
		initSizePills();
		initQuickBuy();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
