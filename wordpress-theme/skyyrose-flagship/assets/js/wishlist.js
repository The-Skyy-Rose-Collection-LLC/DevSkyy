/**
 * SkyyRose Wishlist
 *
 * Handles add/remove/toggle wishlist via AJAX.
 * Depends on localized `skyyRoseWishlist` object from PHP.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */
(function () {
  'use strict';

  if (typeof jQuery === 'undefined') return;
  var $ = jQuery;
  var config = window.skyyRoseWishlist || {};

  /**
   * Send wishlist AJAX request.
   *
   * @param {string} action    AJAX action name.
   * @param {number} productId Product ID.
   * @param {Function} callback  Success callback.
   */
  function wishlistRequest(action, productId, callback) {
    $.ajax({
      url: config.ajaxUrl,
      type: 'POST',
      data: {
        action: action,
        product_id: productId,
        nonce: config.nonce,
      },
      success: function (response) {
        if (callback) {
          callback(response);
        }
      },
      error: function () {
        showNotice(config.i18n && config.i18n.error || 'An error occurred', 'error');
      },
    });
  }

  /**
   * Update all wishlist count badges on the page.
   *
   * @param {number} count New wishlist count.
   */
  function updateCounts(count) {
    $('.js-wishlist-count, .wishlist-count').text(count);
  }

  /**
   * Show a brief notification toast.
   *
   * @param {string} message Notice text.
   * @param {string} type    'success' or 'error'.
   */
  function showNotice(message, type) {
    var $notice = $('<div>').addClass('skyyrose-notice skyyrose-notice--' + (type || 'success'));
    $notice.text(message); // Use textContent to prevent XSS from server-supplied messages.
    $('body').append($notice);
    setTimeout(function () {
      $notice.addClass('visible');
    }, 10);
    setTimeout(function () {
      $notice.removeClass('visible');
      setTimeout(function () {
        $notice.remove();
      }, 300);
    }, 2500);
  }

  /**
   * Toggle wishlist state for a button.
   *
   * @param {jQuery} $btn      The wishlist button element.
   * @param {number} productId Product ID.
   */
  function toggleWishlist($btn, productId) {
    var inWishlist = $btn.hasClass('in-wishlist');
    var action = inWishlist ? 'skyyrose_remove_from_wishlist' : 'skyyrose_add_to_wishlist';

    $btn.addClass('loading');

    wishlistRequest(action, productId, function (response) {
      $btn.removeClass('loading');

      if (response.success) {
        $btn.toggleClass('in-wishlist');
        updateCounts(response.data.count);

        var msg = inWishlist
          ? (config.i18n && config.i18n.removedFromWishlist || 'Removed from wishlist')
          : (config.i18n && config.i18n.addedToWishlist || 'Added to wishlist');
        showNotice(msg, 'success');
      } else {
        showNotice(response.data && response.data.message || config.i18n && config.i18n.error || 'An error occurred', 'error');
      }
    });
  }

  // Bind click handlers on wishlist buttons (delegated for dynamic content).
  $(document).on('click', '.wishlist-button, .js-wishlist-btn, .product-grid-wishlist, .modal-wishlist-btn', function (e) {
    e.preventDefault();
    e.stopPropagation();

    var $btn = $(this);
    var productId = $btn.data('product-id') || $btn.closest('[data-product-id]').data('product-id');

    if (!productId) {
      return;
    }

    toggleWishlist($btn, productId);
  });

  // Move to cart button.
  $(document).on('click', '.js-wishlist-move-to-cart', function (e) {
    e.preventDefault();

    var $btn = $(this);
    var productId = $btn.data('product-id');

    if (!productId) {
      return;
    }

    $btn.addClass('loading');

    wishlistRequest('skyyrose_move_to_cart', productId, function (response) {
      $btn.removeClass('loading');

      if (response.success) {
        $btn.closest('.wishlist-item').fadeOut(300, function () {
          $(this).remove();
        });
        updateCounts(response.data.count);
        $('.js-cart-count, .cart-count').text(response.data.cart_count);
        showNotice(config.i18n && config.i18n.movedToCart || 'Moved to cart', 'success');
      }
    });
  });

  // Clear all wishlist items.
  $(document).on('click', '.js-wishlist-clear', function (e) {
    e.preventDefault();

    wishlistRequest('skyyrose_clear_wishlist', 0, function (response) {
      if (response.success) {
        $('.wishlist-item').fadeOut(300, function () {
          $(this).remove();
        });
        updateCounts(0);
        $('.wishlist-button, .js-wishlist-btn').removeClass('in-wishlist');
      }
    });
  });

  // Move all to cart.
  $(document).on('click', '.js-wishlist-move-all', function (e) {
    e.preventDefault();

    wishlistRequest('skyyrose_move_all_to_cart', 0, function (response) {
      if (response.success) {
        $('.wishlist-item').fadeOut(300, function () {
          $(this).remove();
        });
        updateCounts(response.data.count);
        $('.js-cart-count, .cart-count').text(response.data.cart_count);
        showNotice(response.data.message, 'success');
      }
    });
  });
})();
