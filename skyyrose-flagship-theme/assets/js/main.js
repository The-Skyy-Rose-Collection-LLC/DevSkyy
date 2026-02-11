/**
 * Main JavaScript
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * Main Theme Object
	 */
	const SkyyRose = {

		/**
		 * Initialize
		 */
		init: function() {
			this.setupSmooth();
			this.setupAnimations();
		},

		/**
		 * Setup smooth scrolling
		 */
		setupSmooth: function() {
			$('a[href*="#"]:not([href="#"])').on('click', function(e) {
				if (location.pathname.replace(/^\//, '') === this.pathname.replace(/^\//, '') && location.hostname === this.hostname) {
					var target = $(this.hash);
					target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
					if (target.length) {
						e.preventDefault();
						$('html, body').animate({
							scrollTop: target.offset().top - 80
						}, 800);
					}
				}
			});
		},

		/**
		 * Setup scroll animations
		 */
		setupAnimations: function() {
			$(window).on('scroll', function() {
				$('.fade-in-up').each(function() {
					var elementTop = $(this).offset().top;
					var viewportBottom = $(window).scrollTop() + $(window).height();

					if (elementTop < viewportBottom - 100) {
						$(this).addClass('visible');
					}
				});
			});
		}
	};

	/**
	 * Document ready
	 */
	$(document).ready(function() {
		SkyyRose.init();
	});

})(jQuery);
