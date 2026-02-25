/**
 * SkyyRose Flagship - WooCommerce JavaScript
 *
 * Handles: product gallery, color/size selectors, quantity controls,
 * cart AJAX updates, multi-step checkout navigation.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 */

(function ($) {
	'use strict';

	/* ==================================================
	   PRODUCT GALLERY — Click to swap thumbnails
	   ================================================== */

	var SkyyGallery = {
		init: function () {
			var $gallery = $('[data-skyy-gallery]');
			if (!$gallery.length) {
				return;
			}

			this.$mainImg = $gallery.find('#skyy-gallery-main-img');
			this.$thumbs = $gallery.find('.skyy-single-product__gallery-thumb');

			this.bindEvents();
		},

		bindEvents: function () {
			var self = this;

			this.$thumbs.on('click', function (e) {
				e.preventDefault();
				var $thumb = $(this);
				var newSrc = $thumb.data('src');
				var newFull = $thumb.data('full');

				if (!newSrc) {
					return;
				}

				// Fade transition
				self.$mainImg.css('opacity', '0.5');
				setTimeout(function () {
					self.$mainImg.attr('src', newSrc);
					if (newFull) {
						self.$mainImg.attr('data-full', newFull);
					}
					self.$mainImg.css('opacity', '1');
				}, 200);

				// Update active state (immutable approach: create new state)
				self.$thumbs.removeClass('is-active').attr('aria-checked', 'false');
				$thumb.addClass('is-active').attr('aria-checked', 'true');
			});

			// Lightbox on main image click
			this.$mainImg.on('click', function () {
				var fullSrc = $(this).data('full') || $(this).attr('src');
				SkyyGallery.openLightbox(fullSrc);
			});
		},

		openLightbox: function (src) {
			if (!src) {
				return;
			}

			var $overlay = $('<div>', { 'class': 'skyy-lightbox', role: 'dialog', 'aria-modal': 'true' });
			$('<button>', { 'class': 'skyy-lightbox__close', 'aria-label': 'Close', html: '&times;' }).appendTo($overlay);
			$('<img>', { 'class': 'skyy-lightbox__img', src: src, alt: '' }).appendTo($overlay);

			$('body').append($overlay).css('overflow', 'hidden');

			$overlay.on('click', function (e) {
				if ($(e.target).hasClass('skyy-lightbox') || $(e.target).hasClass('skyy-lightbox__close')) {
					$overlay.remove();
					$('body').css('overflow', '');
				}
			});

			$(document).on('keydown.skyyLightbox', function (e) {
				if (e.key === 'Escape') {
					$overlay.remove();
					$('body').css('overflow', '');
					$(document).off('keydown.skyyLightbox');
				}
			});
		}
	};


	/* ==================================================
	   COLOR SELECTOR — Circle swatches
	   ================================================== */

	var SkyyColorSelector = {
		init: function () {
			this.$swatches = $('.skyy-single-product__color-swatch');
			this.$input = $('[data-skyy-color-input]');
			this.$nameDisplay = $('[data-skyy-color-name]');

			if (!this.$swatches.length) {
				return;
			}

			this.bindEvents();
		},

		bindEvents: function () {
			var self = this;

			this.$swatches.on('click', function () {
				var $swatch = $(this);
				var colorSlug = $swatch.data('color');
				var colorName = $swatch.data('color-name');

				// Update active state
				self.$swatches.removeClass('is-active').attr('aria-checked', 'false');
				$swatch.addClass('is-active').attr('aria-checked', 'true');

				// Update hidden input and display
				self.$input.val(colorSlug);
				self.$nameDisplay.text(colorName);

				// Trigger WC variation update if variable product
				$('form.variations_form').trigger('check_variations');
			});
		}
	};


	/* ==================================================
	   SIZE SELECTOR — S/M/L/XL/XXL buttons
	   ================================================== */

	var SkyySizeSelector = {
		init: function () {
			this.$buttons = $('.skyy-single-product__size-btn');
			this.$input = $('[data-skyy-size-input]');

			if (!this.$buttons.length) {
				return;
			}

			this.bindEvents();
		},

		bindEvents: function () {
			var self = this;

			this.$buttons.on('click', function () {
				var $btn = $(this);
				var sizeSlug = $btn.data('size');

				// Update active state
				self.$buttons.removeClass('is-active').attr('aria-checked', 'false');
				$btn.addClass('is-active').attr('aria-checked', 'true');

				// Update hidden input
				self.$input.val(sizeSlug);

				// Trigger WC variation update
				$('form.variations_form').trigger('check_variations');
			});
		}
	};


	/* ==================================================
	   QUANTITY CONTROLS — +/- buttons
	   ================================================== */

	var SkyyQuantity = {
		init: function () {
			this.bindProductQuantity();
			this.bindCartQuantity();
		},

		bindProductQuantity: function () {
			$(document).on('click', '.skyy-single-product__qty-btn', function () {
				var $btn = $(this);
				var $input = $btn.closest('.skyy-single-product__quantity-wrap').find('.skyy-single-product__qty-input');
				var currentVal = parseInt($input.val(), 10) || 1;
				var min = parseInt($input.attr('min'), 10) || 1;
				var max = parseInt($input.attr('max'), 10) || 99;

				if ($btn.hasClass('skyy-single-product__qty-btn--plus') && currentVal < max) {
					$input.val(currentVal + 1);
				} else if ($btn.hasClass('skyy-single-product__qty-btn--minus') && currentVal > min) {
					$input.val(currentVal - 1);
				}
			});
		},

		bindCartQuantity: function () {
			$(document).on('click', '.skyy-cart__qty-btn', function () {
				var $btn = $(this);
				var $input = $btn.closest('.skyy-cart__qty-controls').find('.skyy-cart__qty-input');
				var currentVal = parseInt($input.val(), 10) || 1;
				var min = parseInt($input.attr('min'), 10) || 0;
				var max = parseInt($input.attr('max'), 10) || 99;

				if ($btn.data('action') === 'increase' && currentVal < max) {
					$input.val(currentVal + 1).trigger('change');
				} else if ($btn.data('action') === 'decrease' && currentVal > min) {
					$input.val(currentVal - 1).trigger('change');
				}
			});
		}
	};


	/* ==================================================
	   ACCORDIONS — Product detail expandable sections
	   ================================================== */

	var SkyyAccordions = {
		init: function () {
			this.$triggers = $('.skyy-single-product__accordion-trigger');

			if (!this.$triggers.length) {
				return;
			}

			this.bindEvents();
		},

		bindEvents: function () {
			this.$triggers.on('click', function () {
				var $trigger = $(this);
				var $panel = $trigger.next('.skyy-single-product__accordion-panel');
				var isExpanded = $trigger.attr('aria-expanded') === 'true';

				// Toggle state (close all others first)
				$('.skyy-single-product__accordion-trigger').not($trigger).attr('aria-expanded', 'false');
				$('.skyy-single-product__accordion-panel').not($panel).attr('hidden', '');

				// Toggle this one
				$trigger.attr('aria-expanded', String(!isExpanded));
				if (isExpanded) {
					$panel.attr('hidden', '');
				} else {
					$panel.removeAttr('hidden');
				}
			});
		}
	};


	/* ==================================================
	   CART UPDATES — AJAX quantity changes
	   ================================================== */

	var SkyyCart = {
		init: function () {
			if (!$('[data-skyy-cart]').length) {
				return;
			}

			this.bindEvents();
		},

		bindEvents: function () {
			var debounceTimer;

			// Auto-update cart on quantity change
			$(document).on('change', '.skyy-cart__qty-input', function () {
				var $form = $(this).closest('form');

				clearTimeout(debounceTimer);
				debounceTimer = setTimeout(function () {
					$form.find('[name="update_cart"]').prop('disabled', false).trigger('click');
				}, 600);
			});

			// Update cart count in header after AJAX
			$(document.body).on('updated_cart_totals', function () {
				SkyyCart.refreshCartCount();
			});

			$(document.body).on('added_to_cart', function () {
				SkyyCart.refreshCartCount();
				SkyyCart.showAddedNotification();
			});
		},

		refreshCartCount: function () {
			$.ajax({
				url: (typeof skyyRoseWoo !== 'undefined') ? skyyRoseWoo.ajaxUrl : '',
				type: 'POST',
				data: {
					action: 'skyyrose_get_cart_count',
					nonce: (typeof skyyRoseWoo !== 'undefined') ? skyyRoseWoo.nonce : ''
				},
				success: function (response) {
					if (response && response.success) {
						$('.cart-count').text(response.data.count);
					}
				}
			});
		},

		showAddedNotification: function () {
			var text = (typeof skyyRoseWoo !== 'undefined') ? skyyRoseWoo.addedToCartText : 'Added to cart';
			var $notice = $('<div class="skyy-cart-notice">' +
				'<svg width="16" height="16" viewBox="0 0 16 16" fill="none">' +
				'<path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
				'</svg>' +
				'<span>' + text + '</span>' +
				'</div>');

			$('body').append($notice);

			setTimeout(function () {
				$notice.addClass('is-visible');
			}, 10);

			setTimeout(function () {
				$notice.removeClass('is-visible');
				setTimeout(function () {
					$notice.remove();
				}, 400);
			}, 3000);
		}
	};


	/* ==================================================
	   CHECKOUT STEPS — Multi-step form navigation
	   ================================================== */

	var SkyyCheckout = {
		currentStep: 1,

		init: function () {
			if (!$('[data-skyy-checkout]').length) {
				return;
			}

			this.$steps = $('[data-skyy-step]');
			this.$progressSteps = $('.skyy-checkout__progress-step');
			this.$progressFill = $('[data-skyy-progress-fill]');

			this.bindEvents();
			this.showStep(1);
		},

		bindEvents: function () {
			var self = this;

			// Next step buttons
			$(document).on('click', '[data-skyy-next-step]', function (e) {
				e.preventDefault();
				var nextStep = parseInt($(this).data('skyy-next-step'), 10);

				if (self.validateCurrentStep()) {
					self.goToStep(nextStep);
				}
			});

			// Previous step buttons
			$(document).on('click', '[data-skyy-prev-step]', function (e) {
				e.preventDefault();
				var prevStep = parseInt($(this).data('skyy-prev-step'), 10);
				self.goToStep(prevStep);
			});

			// Edit buttons in review step
			$(document).on('click', '[data-skyy-goto-step]', function (e) {
				e.preventDefault();
				var targetStep = parseInt($(this).data('skyy-goto-step'), 10);
				self.goToStep(targetStep);
			});
		},

		goToStep: function (step) {
			if (step < 1 || step > 4) {
				return;
			}

			// Populate review data when going to step 4
			if (step === 4) {
				this.populateReview();
			}

			this.currentStep = step;
			this.showStep(step);
			this.updateProgress(step);

			// Scroll to top of form
			$('html, body').animate({
				scrollTop: $('[data-skyy-checkout]').offset().top - 20
			}, 300);
		},

		showStep: function (step) {
			this.$steps
				.removeClass('skyy-checkout__step--active')
				.removeAttr('data-skyy-active');

			$('[data-skyy-step="' + step + '"]')
				.addClass('skyy-checkout__step--active')
				.attr('data-skyy-active', '');
		},

		updateProgress: function (step) {
			var percentage = (step / 4) * 100;
			this.$progressFill.css('width', percentage + '%');

			this.$progressSteps.each(function () {
				var stepNum = parseInt($(this).data('step'), 10);
				$(this)
					.toggleClass('is-active', stepNum <= step)
					.toggleClass('is-complete', stepNum < step);
			});
		},

		validateCurrentStep: function () {
			var isValid = true;
			var $currentPanel = $('[data-skyy-step="' + this.currentStep + '"]');

			// Validate required fields in current step
			$currentPanel.find('input[required], select[required], textarea[required]').each(function () {
				var $field = $(this);
				var $wrapper = $field.closest('.form-row');

				if (!$field.val() || ($field.attr('type') === 'email' && !SkyyCheckout.isValidEmail($field.val()))) {
					isValid = false;
					$wrapper.addClass('woocommerce-invalid');
					$field.css('border-color', 'var(--skyy-woo-danger)');
				} else {
					$wrapper.removeClass('woocommerce-invalid');
					$field.css('border-color', '');
				}
			});

			if (!isValid) {
				// Focus first invalid field
				$currentPanel.find('.woocommerce-invalid input, .woocommerce-invalid select').first().trigger('focus');
			}

			return isValid;
		},

		isValidEmail: function (email) {
			var pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
			return pattern.test(email);
		},

		populateReview: function () {
			// Contact
			var email = $('[name="billing_email"]').val() || '';
			$('[data-skyy-review-email]').text(email);

			// Address
			var addressParts = [
				$('[name="billing_first_name"]').val(),
				$('[name="billing_last_name"]').val(),
				$('[name="billing_address_1"]').val(),
				$('[name="billing_city"]').val(),
				$('[name="billing_state"]').val(),
				$('[name="billing_postcode"]').val()
			].filter(Boolean);
			$('[data-skyy-review-address]').text(addressParts.join(', '));

			// Payment method
			var paymentLabel = $('input[name="payment_method"]:checked').closest('.skyy-checkout__payment-method').find('.skyy-checkout__payment-method-label').text().trim();
			$('[data-skyy-review-payment]').text(paymentLabel || 'Not selected');
		}
	};


	/* ==================================================
	   LIGHTBOX STYLES (injected once)
	   ================================================== */

	function injectLightboxStyles() {
		if ($('#skyy-lightbox-styles').length) {
			return;
		}

		var css =
			'.skyy-lightbox{position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:99999;display:flex;align-items:center;justify-content:center;padding:40px;cursor:pointer;}' +
			'.skyy-lightbox__img{max-width:90vw;max-height:90vh;object-fit:contain;border-radius:8px;cursor:default;}' +
			'.skyy-lightbox__close{position:absolute;top:20px;right:20px;width:44px;height:44px;background:rgba(255,255,255,0.1);border:none;color:#fff;font-size:24px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background 0.2s;}' +
			'.skyy-lightbox__close:hover{background:rgba(255,255,255,0.2);}' +
			'.skyy-cart-notice{position:fixed;bottom:30px;right:30px;display:flex;align-items:center;gap:8px;padding:14px 24px;background:#1a1a1a;border:1px solid rgba(183,110,121,0.4);border-radius:12px;color:#f5f5f5;font-size:0.85rem;font-weight:600;z-index:99998;opacity:0;transform:translateY(10px);transition:all 0.4s cubic-bezier(0.22,1,0.36,1);}' +
			'.skyy-cart-notice.is-visible{opacity:1;transform:translateY(0);}' +
			'.skyy-cart-notice svg{color:#B76E79;}';

		$('<style id="skyy-lightbox-styles">' + css + '</style>').appendTo('head');
	}


	/* ==================================================
	   INIT — DOM Ready
	   ================================================== */

	$(document).ready(function () {
		injectLightboxStyles();
		SkyyGallery.init();
		SkyyColorSelector.init();
		SkyySizeSelector.init();
		SkyyQuantity.init();
		SkyyAccordions.init();
		SkyyCart.init();
		SkyyCheckout.init();
	});

	// Re-init after AJAX (WC fragments)
	$(document.body).on('updated_cart_totals updated_checkout', function () {
		SkyyQuantity.init();
	});

})(jQuery);
