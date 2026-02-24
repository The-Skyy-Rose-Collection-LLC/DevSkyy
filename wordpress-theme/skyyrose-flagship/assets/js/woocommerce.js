/**
 * WooCommerce Scripts — SkyyRose Flagship
 *
 * Enhanced cart interactions, quantity controls, AJAX add-to-cart,
 * product gallery, and checkout UX improvements.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

(function ($) {
	'use strict';

	if (typeof $ === 'undefined') return;

	/* --------------------------------------------------
	 * Quantity +/- Controls
	 *
	 * Wraps quantity inputs with increment/decrement buttons
	 * for a better mobile and desktop UX.
	 * -------------------------------------------------- */
	function initQuantityButtons() {
		$('.woocommerce .quantity')
			.not('.qty-buttons-initialized')
			.each(function () {
				var $qty = $(this).find('input.qty');
				if (!$qty.length) return;

				var min = parseInt($qty.attr('min'), 10) || 1;
				var max = parseInt($qty.attr('max'), 10) || 9999;
				var step = parseInt($qty.attr('step'), 10) || 1;

				var $minus = $(
					'<button type="button" class="qty-btn qty-btn--minus" aria-label="Decrease quantity">&minus;</button>'
				);
				var $plus = $(
					'<button type="button" class="qty-btn qty-btn--plus" aria-label="Increase quantity">&#43;</button>'
				);

				$qty.before($minus).after($plus);
				$(this).addClass('qty-buttons-initialized');

				$minus.on('click', function () {
					var val = parseInt($qty.val(), 10) || min;
					var newVal = Math.max(val - step, min);
					$qty.val(newVal).trigger('change');
				});

				$plus.on('click', function () {
					var val = parseInt($qty.val(), 10) || min;
					var newVal = Math.min(val + step, max);
					$qty.val(newVal).trigger('change');
				});
			});
	}

	/* --------------------------------------------------
	 * AJAX Add to Cart (single product page)
	 * -------------------------------------------------- */
	function initAjaxAddToCart() {
		$(document.body).on(
			'click',
			'.single_add_to_cart_button:not(.disabled)',
			function (e) {
				var $btn = $(this);
				var $form = $btn.closest('form.cart');

				// Only intercept simple products (not variable/grouped).
				if ($form.find('.variations_form').length) return;

				e.preventDefault();

				$btn.addClass('loading').prop('disabled', true);

				var data = $form.serialize();
				data += '&add-to-cart=' + $form.find('[name="add-to-cart"]').val();

				$.ajax({
					url: window.location.href,
					type: 'POST',
					data: data,
					success: function () {
						$btn.removeClass('loading').prop('disabled', false);
						$btn
							.text('Added!')
							.css(
								'background',
								'linear-gradient(135deg, #2ecc71, #27ae60)'
							);

						// Update mini-cart fragments.
						$(document.body).trigger('wc_fragment_refresh');

						setTimeout(function () {
							$btn
								.text('Add to Cart')
								.css('background', '');
						}, 2000);
					},
					error: function () {
						$btn.removeClass('loading').prop('disabled', false);
					},
				});
			}
		);
	}

	/* --------------------------------------------------
	 * Cart Update on Quantity Change
	 * -------------------------------------------------- */
	function initCartAutoUpdate() {
		var updateTimer;

		$('.woocommerce').on('change', '.cart_item .qty', function () {
			clearTimeout(updateTimer);
			updateTimer = setTimeout(function () {
				$('[name="update_cart"]').prop('disabled', false).trigger('click');
			}, 600);
		});
	}

	/* --------------------------------------------------
	 * Product Image Gallery Enhancement
	 *
	 * Adds zoom-on-hover effect for product images.
	 * -------------------------------------------------- */
	function initProductGallery() {
		$('.woocommerce-product-gallery__image').on(
			'mouseenter',
			function () {
				$(this).find('img').css('transform', 'scale(1.05)');
			}
		);

		$('.woocommerce-product-gallery__image').on(
			'mouseleave',
			function () {
				$(this).find('img').css('transform', 'scale(1)');
			}
		);

		$('.woocommerce-product-gallery__image img').css({
			transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
		});
	}

	/* --------------------------------------------------
	 * Checkout Form UX
	 *
	 * Animate labels, smooth scroll to errors.
	 * -------------------------------------------------- */
	function initCheckoutUX() {
		$(document.body).on('checkout_error', function () {
			var $firstError = $('.woocommerce-error li:first');
			if ($firstError.length) {
				$('html, body').animate(
					{ scrollTop: $firstError.offset().top - 100 },
					400
				);
			}
		});
	}

	/* --------------------------------------------------
	 * Initialize
	 * -------------------------------------------------- */
	$(document).ready(function () {
		initQuantityButtons();
		initAjaxAddToCart();
		initCartAutoUpdate();
		initProductGallery();
		initCheckoutUX();
	});

	// Re-init quantity buttons after AJAX cart updates.
	$(document.body).on('updated_cart_totals', initQuantityButtons);
	$(document.body).on('updated_checkout', initQuantityButtons);
})(window.jQuery);
