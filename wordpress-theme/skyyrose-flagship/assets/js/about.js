/**
 * SkyyRose About Page JavaScript (v4.0.0)
 *
 * Features:
 * 1. IntersectionObserver scroll-reveal (.rv → .vis)
 * 2. Press card horizontal drag-to-scroll
 * 3. Hero image parallax (subtle, on scroll)
 *
 * Respects prefers-reduced-motion.
 * No external dependencies.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

(function () {
	'use strict';

	var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ------------------------------------------------------------------
	 * 1. Scroll Reveal — IntersectionObserver
	 * ------------------------------------------------------------------ */
	function initScrollReveal() {
		if (prefersReducedMotion) {
			// Immediately reveal all elements if reduced motion is preferred.
			var els = document.querySelectorAll('.abt-page .rv');
			for (var i = 0; i < els.length; i++) {
				els[i].classList.add('vis');
			}
			return;
		}

		if (!('IntersectionObserver' in window)) {
			// Fallback: reveal everything if IO is unsupported.
			var fallback = document.querySelectorAll('.abt-page .rv');
			for (var j = 0; j < fallback.length; j++) {
				fallback[j].classList.add('vis');
			}
			return;
		}

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('vis');
						observer.unobserve(entry.target);
					}
				});
			},
			{ threshold: 0.06, rootMargin: '0px 0px -40px 0px' }
		);

		document.querySelectorAll('.abt-page .rv').forEach(function (el) {
			observer.observe(el);
		});
	}

	/* ------------------------------------------------------------------
	 * 2. Press Card Horizontal Drag-to-Scroll
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
	 * 3. Hero Parallax (subtle slow-scroll on hero image)
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
		initScrollReveal();
		initPressScroll();
		initHeroParallax();
	}
})();
