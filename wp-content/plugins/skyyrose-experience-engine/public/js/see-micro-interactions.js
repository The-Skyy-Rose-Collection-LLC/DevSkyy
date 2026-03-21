/**
 * Micro-Interactions — Cart Fly, Wishlist Burst, Toasts, Hover Feedback
 *
 * Delightful micro-interactions that build subconscious brand trust:
 *   1. Add-to-cart fly animation (product thumbnail flies to cart icon)
 *   2. Wishlist heart burst (particle explosion on heart click)
 *   3. Toast notifications with brand styling
 *   4. Hover magnetism on CTAs
 *   5. Loading shimmer skeletons
 *   6. Success/error state feedback
 *
 * All animations < 300ms for micro, 500-800ms for celebrations.
 * Respects prefers-reduced-motion.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var SEE = window.SkyyRoseExperience;
	if (!SEE) {
		return;
	}

	var reduced = SEE.prefersReducedMotion;

	/* ==========================================================================
	   Toast Notification System
	   ========================================================================== */

	var toastContainer = null;
	var toastQueue = [];
	var maxToasts = 3;

	function showToast(message, type, duration) {
		if (!toastContainer) {
			toastContainer = document.getElementById('see-toast-container');
		}
		if (!toastContainer) {
			return;
		}

		type = type || 'info'; // info | success | error | warning
		duration = duration || 4000;

		var toast = document.createElement('div');
		toast.className = 'see-toast see-toast--' + type;
		toast.setAttribute('role', 'status');
		toast.innerHTML = '<span class="see-toast-text">' + message + '</span>' +
			'<button class="see-toast-close" aria-label="Dismiss">&times;</button>';

		// Close button.
		toast.querySelector('.see-toast-close').addEventListener('click', function () {
			dismissToast(toast);
		});

		// Limit visible toasts.
		var existing = toastContainer.querySelectorAll('.see-toast');
		if (existing.length >= maxToasts) {
			dismissToast(existing[0]);
		}

		toastContainer.appendChild(toast);

		// Trigger enter animation.
		requestAnimationFrame(function () {
			toast.classList.add('see-toast--visible');
		});

		// Auto-dismiss.
		setTimeout(function () {
			dismissToast(toast);
		}, duration);
	}

	function dismissToast(toast) {
		if (!toast || !toast.parentNode) {
			return;
		}
		toast.classList.remove('see-toast--visible');
		toast.classList.add('see-toast--exit');
		setTimeout(function () {
			if (toast.parentNode) {
				toast.parentNode.removeChild(toast);
			}
		}, 300);
	}

	/* ==========================================================================
	   Add-to-Cart Fly Animation
	   ========================================================================== */

	function initCartFly() {
		if (reduced) {
			return;
		}

		// Listen for WooCommerce AJAX add-to-cart.
		document.body.addEventListener('added_to_cart', function (e, fragments, hash, button) {
			// Find the product image near the clicked button.
			var btn = document.querySelector('.added_to_cart') || document.querySelector('.ajax_add_to_cart.added');
			if (!btn) {
				return;
			}

			var card = btn.closest('.see-product-wrapper, .product');
			var img = card ? card.querySelector('img') : null;
			var cartIcon = document.querySelector('.cart-contents, .site-header-cart, [data-cart-count]');

			if (img && cartIcon) {
				flyToCart(img, cartIcon);
			}

			showToast('Added to cart', 'success', 3000);
			SEE.emit('micro:add-to-cart');
		});

		// Also listen for single product page add-to-cart.
		var singleBtn = document.querySelector('.single_add_to_cart_button');
		if (singleBtn) {
			singleBtn.addEventListener('click', function () {
				singleBtn.classList.add('see-btn-pulse');
				setTimeout(function () {
					singleBtn.classList.remove('see-btn-pulse');
				}, 600);
			});
		}
	}

	function flyToCart(sourceEl, targetEl) {
		var sourceRect = sourceEl.getBoundingClientRect();
		var targetRect = targetEl.getBoundingClientRect();

		var clone = sourceEl.cloneNode(true);
		clone.className = 'see-fly-clone';
		clone.style.position = 'fixed';
		clone.style.left = sourceRect.left + 'px';
		clone.style.top = sourceRect.top + 'px';
		clone.style.width = sourceRect.width + 'px';
		clone.style.height = sourceRect.height + 'px';
		clone.style.zIndex = '10000';
		clone.style.pointerEvents = 'none';
		clone.style.borderRadius = '8px';
		clone.style.transition = 'all 600ms cubic-bezier(0.16, 1, 0.3, 1)';

		document.body.appendChild(clone);

		requestAnimationFrame(function () {
			clone.style.left = targetRect.left + 'px';
			clone.style.top = targetRect.top + 'px';
			clone.style.width = '30px';
			clone.style.height = '30px';
			clone.style.opacity = '0.3';
			clone.style.borderRadius = '50%';
		});

		setTimeout(function () {
			if (clone.parentNode) {
				clone.parentNode.removeChild(clone);
			}
			// Bounce the cart icon.
			targetEl.classList.add('see-cart-bounce');
			setTimeout(function () {
				targetEl.classList.remove('see-cart-bounce');
			}, 400);
		}, 650);
	}

	/* ==========================================================================
	   Wishlist Heart Burst
	   ========================================================================== */

	function initWishlistBurst() {
		if (reduced) {
			return;
		}

		document.addEventListener('click', function (e) {
			var wishlistBtn = e.target.closest('.see-wishlist-btn, .yith-wcwl-add-to-wishlist a, .skyyrose-wishlist-btn');
			if (!wishlistBtn) {
				return;
			}

			createHeartBurst(wishlistBtn);
			SEE.emit('micro:wishlist');
		});
	}

	function createHeartBurst(element) {
		var rect = element.getBoundingClientRect();
		var centerX = rect.left + rect.width / 2;
		var centerY = rect.top + rect.height / 2;

		for (var i = 0; i < 6; i++) {
			var particle = document.createElement('span');
			particle.className = 'see-heart-particle';
			particle.textContent = '\u2764'; // ❤
			particle.style.position = 'fixed';
			particle.style.left = centerX + 'px';
			particle.style.top = centerY + 'px';
			particle.style.zIndex = '10000';
			particle.style.pointerEvents = 'none';
			particle.style.fontSize = (8 + Math.random() * 8) + 'px';
			particle.style.color = '#DC143C';
			particle.style.transition = 'all 600ms cubic-bezier(0.16, 1, 0.3, 1)';

			document.body.appendChild(particle);

			var angle = (Math.PI * 2 * i) / 6 + (Math.random() - 0.5);
			var distance = 20 + Math.random() * 30;
			var dx = Math.cos(angle) * distance;
			var dy = Math.sin(angle) * distance;

			(function (p, dx, dy) {
				requestAnimationFrame(function () {
					p.style.transform = 'translate(' + dx + 'px, ' + dy + 'px)';
					p.style.opacity = '0';
				});
				setTimeout(function () {
					if (p.parentNode) {
						p.parentNode.removeChild(p);
					}
				}, 650);
			})(particle, dx, dy);
		}
	}

	/* ==========================================================================
	   CTA Hover Magnetism
	   ========================================================================== */

	function initHoverMagnetism() {
		if (reduced) {
			return;
		}

		var ctas = document.querySelectorAll('.see-qv-link, .single_add_to_cart_button, .button.add_to_cart_button, [data-see-magnetic]');
		ctas.forEach(function (cta) {
			cta.addEventListener('mousemove', function (e) {
				var rect = cta.getBoundingClientRect();
				var x = e.clientX - rect.left - rect.width / 2;
				var y = e.clientY - rect.top - rect.height / 2;
				cta.style.transform = 'translate(' + (x * 0.15) + 'px, ' + (y * 0.15) + 'px)';
			});

			cta.addEventListener('mouseleave', function () {
				cta.style.transform = '';
			});
		});
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('micro-interactions', {
		init: function () {},

		ready: function () {
			initCartFly();
			initWishlistBurst();
			initHoverMagnetism();
		},

		destroy: function () {
			// Remove any lingering clones/particles.
			document.querySelectorAll('.see-fly-clone, .see-heart-particle').forEach(function (el) {
				el.remove();
			});
		},
	});

	// Expose toast for other modules.
	SEE.toast = showToast;

})();
