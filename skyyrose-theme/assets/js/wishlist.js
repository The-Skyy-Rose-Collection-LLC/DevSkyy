/**
 * Wishlist Functionality
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * Wishlist object.
	 */
	const SkyyRoseWishlistModule = {

		/**
		 * Initialize.
		 */
		init: function() {
			this.bindEvents();
			this.updateCounter();
		},

		/**
		 * Bind events.
		 */
		bindEvents: function() {
			// Toggle wishlist button.
			$(document).on('click', '.wishlist-button', this.toggleWishlist.bind(this));

			// Remove from wishlist.
			$(document).on('click', '.wishlist-remove', this.removeFromWishlist.bind(this));

			// Move to cart.
			$(document).on('click', '.wishlist-move-to-cart', this.moveToCart.bind(this));

			// Move all to cart.
			$(document).on('click', '.wishlist-move-all', this.moveAllToCart.bind(this));

			// Clear wishlist.
			$(document).on('click', '.wishlist-clear-all', this.clearWishlist.bind(this));

			// Share wishlist.
			$(document).on('click', '.wishlist-share', this.shareWishlist.bind(this));
		},

		/**
		 * Toggle wishlist.
		 */
		toggleWishlist: function(e) {
			e.preventDefault();

			const $button = $(e.currentTarget);
			const productId = $button.data('product-id');
			const isInWishlist = $button.hasClass('in-wishlist');

			if (isInWishlist) {
				this.removeFromWishlist(e);
			} else {
				this.addToWishlist(productId, $button);
			}
		},

		/**
		 * Add to wishlist.
		 */
		addToWishlist: function(productId, $button) {
			// Animate heart icon.
			this.animateHeart($button);

			// Make AJAX request.
			$.ajax({
				url: skyyRoseWishlist.ajaxUrl,
				type: 'POST',
				data: {
					action: 'skyyrose_add_to_wishlist',
					nonce: skyyRoseWishlist.nonce,
					product_id: productId
				},
				beforeSend: function() {
					$button.addClass('loading');
				},
				success: function(response) {
					if (response.success) {
						$button.addClass('in-wishlist');
						this.updateCounter(response.data.count);
						this.showToast(skyyRoseWishlist.i18n.addedToWishlist, 'success');
					} else {
						this.showToast(response.data.message, 'error');
					}
				}.bind(this),
				complete: function() {
					$button.removeClass('loading');
				},
				error: function() {
					this.showToast(skyyRoseWishlist.i18n.error, 'error');
				}.bind(this)
			});
		},

		/**
		 * Remove from wishlist.
		 */
		removeFromWishlist: function(e) {
			e.preventDefault();

			const $button = $(e.currentTarget);
			const productId = $button.data('product-id');
			const $productCard = $button.closest('.wishlist-item');

			// Make AJAX request.
			$.ajax({
				url: skyyRoseWishlist.ajaxUrl,
				type: 'POST',
				data: {
					action: 'skyyrose_remove_from_wishlist',
					nonce: skyyRoseWishlist.nonce,
					product_id: productId
				},
				beforeSend: function() {
					$button.addClass('loading');
				},
				success: function(response) {
					if (response.success) {
						// Remove button state if it's a toggle button.
						if ($button.hasClass('wishlist-button')) {
							$button.removeClass('in-wishlist');
						}

						// Fade out and remove product card on wishlist page.
						if ($productCard.length) {
							$productCard.fadeOut(300, function() {
								$(this).remove();

								// Show empty state if no items left.
								if ($('.wishlist-item').length === 0) {
									this.showEmptyState();
								}
							}.bind(this));
						}

						this.updateCounter(response.data.count);
						this.showToast(skyyRoseWishlist.i18n.removedFromWishlist, 'success');
					} else {
						this.showToast(response.data.message, 'error');
					}
				}.bind(this),
				complete: function() {
					$button.removeClass('loading');
				},
				error: function() {
					this.showToast(skyyRoseWishlist.i18n.error, 'error');
				}.bind(this)
			});
		},

		/**
		 * Move to cart.
		 */
		moveToCart: function(e) {
			e.preventDefault();

			const $button = $(e.currentTarget);
			const productId = $button.data('product-id');
			const $productCard = $button.closest('.wishlist-item');

			// Make AJAX request.
			$.ajax({
				url: skyyRoseWishlist.ajaxUrl,
				type: 'POST',
				data: {
					action: 'skyyrose_move_to_cart',
					nonce: skyyRoseWishlist.nonce,
					product_id: productId
				},
				beforeSend: function() {
					$button.addClass('loading');
				},
				success: function(response) {
					if (response.success) {
						// Fade out and remove product card.
						if ($productCard.length) {
							$productCard.fadeOut(300, function() {
								$(this).remove();

								// Show empty state if no items left.
								if ($('.wishlist-item').length === 0) {
									this.showEmptyState();
								}
							}.bind(this));
						}

						this.updateCounter(response.data.count);
						this.updateCartCounter(response.data.cart_count);
						this.showToast(skyyRoseWishlist.i18n.movedToCart, 'success');
					} else {
						this.showToast(response.data.message, 'error');
					}
				}.bind(this),
				complete: function() {
					$button.removeClass('loading');
				},
				error: function() {
					this.showToast(skyyRoseWishlist.i18n.error, 'error');
				}.bind(this)
			});
		},

		/**
		 * Move all to cart.
		 */
		moveAllToCart: function(e) {
			e.preventDefault();

			const $button = $(e.currentTarget);

			// Confirm action.
			if (!confirm('Are you sure you want to move all items to cart?')) {
				return;
			}

			// Make AJAX request.
			$.ajax({
				url: skyyRoseWishlist.ajaxUrl,
				type: 'POST',
				data: {
					action: 'skyyrose_move_all_to_cart',
					nonce: skyyRoseWishlist.nonce
				},
				beforeSend: function() {
					$button.addClass('loading');
				},
				success: function(response) {
					if (response.success) {
						// Fade out all product cards.
						$('.wishlist-item').fadeOut(300, function() {
							$(this).remove();
							this.showEmptyState();
						}.bind(this));

						this.updateCounter(response.data.count);
						this.updateCartCounter(response.data.cart_count);
						this.showToast(response.data.message, 'success');
					} else {
						this.showToast(response.data.message, 'error');
					}
				}.bind(this),
				complete: function() {
					$button.removeClass('loading');
				},
				error: function() {
					this.showToast(skyyRoseWishlist.i18n.error, 'error');
				}.bind(this)
			});
		},

		/**
		 * Clear wishlist.
		 */
		clearWishlist: function(e) {
			e.preventDefault();

			const $button = $(e.currentTarget);

			// Confirm action.
			if (!confirm('Are you sure you want to clear your wishlist?')) {
				return;
			}

			// Make AJAX request.
			$.ajax({
				url: skyyRoseWishlist.ajaxUrl,
				type: 'POST',
				data: {
					action: 'skyyrose_clear_wishlist',
					nonce: skyyRoseWishlist.nonce
				},
				beforeSend: function() {
					$button.addClass('loading');
				},
				success: function(response) {
					if (response.success) {
						// Fade out all product cards.
						$('.wishlist-item').fadeOut(300, function() {
							$(this).remove();
							this.showEmptyState();
						}.bind(this));

						this.updateCounter(response.data.count);
						this.showToast(response.data.message, 'success');
					} else {
						this.showToast(response.data.message, 'error');
					}
				}.bind(this),
				complete: function() {
					$button.removeClass('loading');
				},
				error: function() {
					this.showToast(skyyRoseWishlist.i18n.error, 'error');
				}.bind(this)
			});
		},

		/**
		 * Share wishlist.
		 */
		shareWishlist: function(e) {
			e.preventDefault();

			const url = skyyRoseWishlist.wishlistUrl || window.location.href;
			const title = 'My Wishlist';

			// Use native share API if available.
			if (navigator.share) {
				navigator.share({
					title: title,
					url: url
				}).then(() => {
					this.showToast('Wishlist shared successfully!', 'success');
				}).catch(() => {
					this.copyToClipboard(url);
				});
			} else {
				this.copyToClipboard(url);
			}
		},

		/**
		 * Copy to clipboard.
		 */
		copyToClipboard: function(text) {
			const $temp = $('<input>');
			$('body').append($temp);
			$temp.val(text).select();
			document.execCommand('copy');
			$temp.remove();
			this.showToast('Wishlist link copied to clipboard!', 'success');
		},

		/**
		 * Animate heart icon.
		 */
		animateHeart: function($button) {
			$button.addClass('animating');
			setTimeout(function() {
				$button.removeClass('animating');
			}, 600);
		},

		/**
		 * Update wishlist counter.
		 */
		updateCounter: function(count) {
			if (typeof count === 'undefined') {
				count = skyyRoseWishlist.count;
			}

			const $counter = $('.wishlist-count');

			if ($counter.length) {
				$counter.text(count);

				if (count > 0) {
					$counter.addClass('has-items');
				} else {
					$counter.removeClass('has-items');
				}
			}
		},

		/**
		 * Update cart counter.
		 */
		updateCartCounter: function(count) {
			const $counter = $('.cart-count');

			if ($counter.length) {
				$counter.text(count);

				if (count > 0) {
					$counter.addClass('has-items');
				} else {
					$counter.removeClass('has-items');
				}
			}

			// Trigger WooCommerce cart update event.
			$(document.body).trigger('wc_fragment_refresh');
		},

		/**
		 * Show toast notification.
		 */
		showToast: function(message, type) {
			type = type || 'success';

			const $toast = $('#wishlist-toast');
			const $message = $toast.find('.wishlist-toast-message');
			const $icon = $toast.find('.wishlist-toast-icon');

			// Set message and type.
			$message.text(message);
			$toast.attr('data-type', type);

			// Set icon based on type.
			if (type === 'success') {
				$icon.html('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.667 5L7.5 14.167L3.333 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
			} else {
				$icon.html('<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 18.333c4.602 0 8.333-3.731 8.333-8.333S14.602 1.667 10 1.667 1.667 5.398 1.667 10s3.731 8.333 8.333 8.333zM10 6.667V10M10 13.333h.008" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>');
			}

			// Show toast.
			$toast.addClass('show');

			// Hide after 3 seconds.
			setTimeout(function() {
				$toast.removeClass('show');
			}, 3000);
		},

		/**
		 * Show empty state.
		 */
		showEmptyState: function() {
			const emptyHtml = `
				<div class="wishlist-empty">
					<div class="wishlist-empty-icon">
						<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M40 70C55.464 70 68 57.464 68 42C68 26.536 55.464 14 40 14C24.536 14 12 26.536 12 42C12 57.464 24.536 70 40 70Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
							<path d="M40 26.667V42L48.889 46.444" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
							<path d="M58.333 20L68 10M22 20L12 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
					</div>
					<h2 class="wishlist-empty-title">Your Wishlist is Empty</h2>
					<p class="wishlist-empty-text">Save your favorite items here to purchase later or keep track of items you love.</p>
					<div class="wishlist-empty-actions">
						<a href="${window.location.origin}/shop" class="button alt">Start Shopping</a>
					</div>
				</div>
			`;

			$('.wishlist-grid').fadeOut(300, function() {
				$(this).remove();
				$('.wishlist-actions').fadeOut(300, function() {
					$(this).remove();
					$('.wishlist-page .container').append(emptyHtml);
				});
			});
		}
	};

	/**
	 * Document ready.
	 */
	$(document).ready(function() {
		SkyyRoseWishlistModule.init();
	});

})(jQuery);
