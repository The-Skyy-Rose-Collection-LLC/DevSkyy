/**
 * SkyyRose Elementor Frontend JavaScript
 *
 * Handles custom Elementor widget interactions and animations on the frontend.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * SkyyRose Elementor Handler
	 */
	const SkyyRoseElementor = {
		/**
		 * Initialize Elementor frontend handlers.
		 */
		init: function() {
			$(window).on('elementor/frontend/init', function() {
				// Add custom frontend handlers here
				SkyyRoseElementor.initCustomWidgets();
			});
		},

		/**
		 * Initialize custom widget handlers.
		 */
		initCustomWidgets: function() {
			// Example: Handle custom widget interactions
			if (typeof elementorFrontend !== 'undefined') {
				// Register custom widget handlers
				elementorFrontend.hooks.addAction('frontend/element_ready/global', function($scope) {
					// Handle lazy loading images
					SkyyRoseElementor.lazyLoadImages($scope);

					// Handle scroll animations
					SkyyRoseElementor.scrollAnimations($scope);
				});
			}
		},

		/**
		 * Lazy load images in Elementor widgets.
		 *
		 * @param {jQuery} $scope - The widget scope.
		 */
		lazyLoadImages: function($scope) {
			const $images = $scope.find('img[data-src]');

			if ($images.length && 'IntersectionObserver' in window) {
				const imageObserver = new IntersectionObserver(function(entries) {
					entries.forEach(function(entry) {
						if (entry.isIntersecting) {
							const $img = $(entry.target);
							$img.attr('src', $img.data('src'));
							$img.removeAttr('data-src');
							imageObserver.unobserve(entry.target);
						}
					});
				});

				$images.each(function() {
					imageObserver.observe(this);
				});
			}
		},

		/**
		 * Handle scroll-triggered animations.
		 *
		 * @param {jQuery} $scope - The widget scope.
		 */
		scrollAnimations: function($scope) {
			const $animatedElements = $scope.find('[data-animation]');

			if ($animatedElements.length && 'IntersectionObserver' in window) {
				const animationObserver = new IntersectionObserver(function(entries) {
					entries.forEach(function(entry) {
						if (entry.isIntersecting) {
							const $element = $(entry.target);
							const animation = $element.data('animation');

							$element.addClass('animated ' + animation);
							animationObserver.unobserve(entry.target);
						}
					});
				}, {
					threshold: 0.1
				});

				$animatedElements.each(function() {
					animationObserver.observe(this);
				});
			}
		}
	};

	/**
	 * Initialize on document ready.
	 */
	$(document).ready(function() {
		SkyyRoseElementor.init();
	});

})(jQuery);
