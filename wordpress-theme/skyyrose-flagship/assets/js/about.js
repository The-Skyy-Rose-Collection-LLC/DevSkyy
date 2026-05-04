/**
 * SkyyRose About Page JavaScript
 *
 * Features:
 * 1. Press card horizontal drag-to-scroll
 * 2. Hero image parallax (subtle, on scroll)
 *
 * Scroll-reveal for .abt-page .rv is handled by the unified observer in
 * premium-interactions.js (retired local copy in U-1, 2026-05-04).
 *
 * Respects prefers-reduced-motion.
 * No external dependencies.
 *
 * @package SkyyRose
 * @since   4.0.0
 */

(function () {
	'use strict';

	var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ------------------------------------------------------------------
	 * 1. Press Card Horizontal Drag-to-Scroll
	 * ------------------------------------------------------------------ */
	function initPressScroll() {
		var ps = document.getElementById('pressScroll');
		if (!ps) return;

		var isDown = false;
		var startX = 0;
		var scrollLeft = 0;

		ps.addEventListener('mousedown', function (e) {
			isDown = true;
			ps.classList.add('is-dragging');
			startX = e.pageX - ps.offsetLeft;
			scrollLeft = ps.scrollLeft;
		});

		ps.addEventListener('mouseleave', function () {
			isDown = false;
			ps.classList.remove('is-dragging');
		});

		ps.addEventListener('mouseup', function () {
			isDown = false;
			ps.classList.remove('is-dragging');
		});

		ps.addEventListener('mousemove', function (e) {
			if (!isDown) return;
			e.preventDefault();
			var x = e.pageX - ps.offsetLeft;
			ps.scrollLeft = scrollLeft - (x - startX) * 1.5;
		});

		// Hint: start with a slight offset so user knows it scrolls.
		setTimeout(function () {
			if (ps.scrollWidth > ps.clientWidth) {
				ps.scrollLeft = 20;
			}
		}, 1200);
	}

	/* ------------------------------------------------------------------
	 * 2. Hero Parallax (subtle slow-scroll on hero image)
	 * ------------------------------------------------------------------ */
	function initHeroParallax() {
		if (prefersReducedMotion) return;

		var heroImg = document.querySelector('.abt-hero__img img');
		if (!heroImg) return;

		var ticking = false;

		window.addEventListener('scroll', function () {
			if (!ticking) {
				window.requestAnimationFrame(function () {
					var scrollY = window.scrollY;
					// Only apply parallax in the hero viewport range.
					if (scrollY < window.innerHeight * 1.2) {
						heroImg.style.transform = 'scale(1) translateY(' + (scrollY * 0.15) + 'px)';
					}
					ticking = false;
				});
				ticking = true;
			}
		}, { passive: true });
	}

	/* ------------------------------------------------------------------
	 * Init
	 * ------------------------------------------------------------------ */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

	function init() {
		initPressScroll();
		initHeroParallax();
	}
})();
