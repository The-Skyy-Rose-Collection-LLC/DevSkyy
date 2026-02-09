/**
 * SkyyRose WooCommerce JavaScript
 *
 * Handles WooCommerce interactions including AJAX add to cart,
 * cart updates, and mini-cart functionality.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * SkyyRose WooCommerce handler.
	 */
	const SkyyRoseWooCommerce = {
		/**
		 * Initialize WooCommerce functionality.
		 */
		init: function() {
			this.ajaxAddToCart();
			this.updateCartFragments();
			this.handleQuantityButtons();
			this.handleCartUpdates();
		},

		/**
		 * AJAX Add to Cart functionality.
		 * Handles adding products to cart without page refresh.
		 */
		ajaxAddToCart: function() {
			$(document).on('click', '.ajax_add_to_cart:not(.loading)', function(e) {
				e.preventDefault();

				const $button = $(this);
				const productId = $button.data('product_id');
				const quantity = $button.data('quantity') || 1;

				// Add loading state
				$button.addClass('loading').attr('disabled', 'disabled');

				// AJAX request to add product to cart
				$.ajax({
					url: wc_add_to_cart_params.ajax_url,
					type: 'POST',
					data: {
						action: 'woocommerce_ajax_add_to_cart',
						product_id: productId,
						quantity: quantity,
						nonce: skyyRoseWoo.nonce
					},
					success: function(response) {
						if (response.error && response.product_url) {
							window.location = response.product_url;
							return;
						}

						// Trigger WooCommerce event for cart fragment refresh
						$(document.body).trigger('added_to_cart', [
							response.fragments,
							response.cart_hash,
							$button
						]);

						// Show success message
						SkyyRoseWooCommerce.showNotification(skyyRoseWoo.addedToCartText, 'success');

						// Remove loading state
						$button.removeClass('loading').removeAttr('disabled');
					},
					error: function() {
						$button.removeClass('loading').removeAttr('disabled');
						SkyyRoseWooCommerce.showNotification('Error adding to cart', 'error');
					}
				});
			});
		},

		/**
		 * Update cart fragments after cart changes.
		 * Refreshes mini-cart and cart totals without page reload.
		 */
		updateCartFragments: function() {
			$(document.body).on('added_to_cart removed_from_cart updated_cart_totals', function() {
				// Update cart fragments
				$.ajax({
					url: wc_add_to_cart_params.wc_ajax_url.toString().replace('%%endpoint%%', 'get_refreshed_fragments'),
					type: 'POST',
					success: function(data) {
						if (data && data.fragments) {
							$.each(data.fragments, function(key, value) {
								$(key).replaceWith(value);
							});

							// Trigger custom event for cart update
							$(document.body).trigger('wc_fragments_refreshed');
						}
					}
				});
			});
		},

		/**
		 * Handle quantity increment/decrement buttons.
		 */
		handleQuantityButtons: function() {
			$(document).on('click', '.qty-btn', function(e) {
				e.preventDefault();

				const $button = $(this);
				const $input = $button.siblings('.qty');
				let currentVal = parseFloat($input.val());
				const max = parseFloat($input.attr('max'));
				const min = parseFloat($input.attr('min'));
				const step = parseFloat($input.attr('step'));

				// Increment or decrement
				if ($button.hasClass('qty-increase')) {
					if (max && currentVal >= max) {
						currentVal = max;
					} else {
						currentVal = currentVal + step;
					}
				} else {
					if (min && currentVal <= min) {
						currentVal = min;
					} else if (currentVal > 0) {
						currentVal = currentVal - step;
					}
				}

				// Update input value
				$input.val(currentVal);
				$input.trigger('change');
			});
		},

		/**
		 * Handle cart updates when quantities change.
		 */
		handleCartUpdates: function() {
			$(document).on('change', 'input.qty', function() {
				const $form = $(this).closest('form');
				if ($form.length) {
					// Trigger update cart button if it exists
					const $updateButton = $form.find('[name="update_cart"]');
					if ($updateButton.length) {
						$updateButton.prop('disabled', false).trigger('click');
					}
				}
			});

			// Update cart on proceed to checkout click
			$(document).on('click', '.checkout-button', function(e) {
				const $updateButton = $('form.woocommerce-cart-form').find('[name="update_cart"]');
				if ($updateButton.length && !$updateButton.prop('disabled')) {
					e.preventDefault();
					$updateButton.trigger('click');

					// Redirect to checkout after cart updates
					$(document.body).on('updated_cart_totals', function() {
						window.location.href = skyyRoseWoo.checkoutUrl;
					});
				}
			});
		},

		/**
		 * Show notification message.
		 *
		 * @param {string} message - The message to display.
		 * @param {string} type - The type of notification (success, error, info).
		 */
		showNotification: function(message, type) {
			// Create notification element
			const $notification = $('<div class="skyyrose-notification ' + type + '">')
				.text(message)
				.appendTo('body');

			// Show notification
			setTimeout(function() {
				$notification.addClass('show');
			}, 100);

			// Hide and remove notification
			setTimeout(function() {
				$notification.removeClass('show');
				setTimeout(function() {
					$notification.remove();
				}, 300);
			}, 3000);
		}
	};

	/**
	 * Initialize on document ready.
	 */
	$(document).ready(function() {
		SkyyRoseWooCommerce.init();
	});

})(jQuery);
