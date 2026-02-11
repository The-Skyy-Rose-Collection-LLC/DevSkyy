/**
 * Navigation JavaScript
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * Navigation Module
	 */
	const Navigation = {

		/**
		 * Initialize
		 */
		init: function() {
			this.setupMobileMenu();
			this.setupStickyHeader();
		},

		/**
		 * Setup mobile menu toggle
		 */
		setupMobileMenu: function() {
			$('.menu-toggle').on('click', function(e) {
				e.preventDefault();
				$(this).toggleClass('active');
				$('.main-navigation').toggleClass('active');
				$('body').toggleClass('menu-open');

				// Update aria-expanded
				var expanded = $(this).attr('aria-expanded') === 'true';
				$(this).attr('aria-expanded', !expanded);
			});

			// Close menu when clicking outside
			$(document).on('click', function(e) {
				if (!$(e.target).closest('.main-navigation, .menu-toggle').length) {
					$('.menu-toggle').removeClass('active');
					$('.main-navigation').removeClass('active');
					$('body').removeClass('menu-open');
					$('.menu-toggle').attr('aria-expanded', 'false');
				}
			});

			// Close menu on escape key
			$(document).on('keydown', function(e) {
				if (e.key === 'Escape' && $('.main-navigation').hasClass('active')) {
					$('.menu-toggle').removeClass('active');
					$('.main-navigation').removeClass('active');
					$('body').removeClass('menu-open');
					$('.menu-toggle').attr('aria-expanded', 'false');
				}
			});
		},

		/**
		 * Setup sticky header
		 */
		setupStickyHeader: function() {
			let lastScroll = 0;
			const header = $('.site-header');

			$(window).on('scroll', function() {
				const currentScroll = $(this).scrollTop();

				if (currentScroll > 100) {
					header.addClass('scrolled');
				} else {
					header.removeClass('scrolled');
				}

				// Hide/show header on scroll
				if (currentScroll > lastScroll && currentScroll > 200) {
					header.addClass('hidden');
				} else {
					header.removeClass('hidden');
				}

				lastScroll = currentScroll;
			});
		}
	};

	/**
	 * Document ready
	 */
	$(document).ready(function() {
		Navigation.init();
	});

})(jQuery);
