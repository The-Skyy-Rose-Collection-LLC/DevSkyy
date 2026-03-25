/**
 * SkyyRose Elementor Frontend
 *
 * Initializes scroll-reveal animations and resize observers
 * for SkyyRose widgets rendered inside Elementor containers.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */
(function ($) {
	'use strict';

	/* -----------------------------------------------
	   Scroll-Reveal for Elementor Containers
	   ----------------------------------------------- */
	var revealObserver = null;

	function initScrollReveal() {
		if (!('IntersectionObserver' in window)) {
			// Fallback: show everything immediately.
			$('.elementor-widget-container .col-rv').addClass('vis');
			return;
		}

		revealObserver = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('vis');
						revealObserver.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.15 }
		);

		document
			.querySelectorAll('.elementor-widget-container .col-rv')
			.forEach(function (el) {
				revealObserver.observe(el);
			});
	}

	/* -----------------------------------------------
	   Countdown Timer Tick
	   ----------------------------------------------- */
	function initCountdowns() {
		$('.skyyrose-countdown').each(function () {
			var $el = $(this);
			var deadline = new Date($el.data('deadline')).getTime();

			if (isNaN(deadline)) return;

			function tick() {
				var now = Date.now();
				var diff = Math.max(0, deadline - now);

				var d = Math.floor(diff / 86400000);
				var h = Math.floor((diff % 86400000) / 3600000);
				var m = Math.floor((diff % 3600000) / 60000);
				var s = Math.floor((diff % 60000) / 1000);

				$el.find('.cd-days').text(d);
				$el.find('.cd-hours').text(h);
				$el.find('.cd-mins').text(m);
				$el.find('.cd-secs').text(s);

				if (diff > 0) {
					requestAnimationFrame(function () {
						setTimeout(tick, 1000);
					});
				}
			}

			tick();
		});
	}

	/* -----------------------------------------------
	   Elementor Frontend Init
	   ----------------------------------------------- */
	$(window).on('elementor/frontend/init', function () {
		initScrollReveal();
		initCountdowns();
	});
})(jQuery);
