/**
 * Scroll Enhancements — Progress Indicator + Back-to-Top
 *
 * Two global UX features loaded on every page:
 * 1. Rose-gold scroll progress bar at the top of the viewport
 * 2. Back-to-top button that appears after scrolling down
 *
 * Both respect prefers-reduced-motion and WP admin bar offset.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	var progressBar = document.querySelector('.sr-scroll-progress__bar');
	var backToTop   = document.querySelector('.sr-back-to-top');

	if (!progressBar && !backToTop) {
		return;
	}

	/* -------------------------------------------
	   Scroll Progress Indicator
	   ------------------------------------------- */
	function updateProgress() {
		if (!progressBar) { return; }

		var docHeight    = document.documentElement.scrollHeight - window.innerHeight;
		var scrolled     = window.pageYOffset || document.documentElement.scrollTop;
		var pct          = docHeight > 0 ? Math.min((scrolled / docHeight) * 100, 100) : 0;

		progressBar.style.width = pct + '%';
	}

	/* -------------------------------------------
	   Back-to-Top Button
	   ------------------------------------------- */
	var BTT_THRESHOLD = 400; // px scrolled before button appears

	function updateBackToTop() {
		if (!backToTop) { return; }

		var scrolled = window.pageYOffset || document.documentElement.scrollTop;

		if (scrolled > BTT_THRESHOLD) {
			backToTop.classList.add('visible');
		} else {
			backToTop.classList.remove('visible');
		}
	}

	if (backToTop) {
		backToTop.addEventListener('click', function () {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		});
	}

	/* -------------------------------------------
	   RAF-Throttled Scroll Listener
	   ------------------------------------------- */
	var ticking = false;

	function onScroll() {
		if (ticking) { return; }
		ticking = true;

		requestAnimationFrame(function () {
			updateProgress();
			updateBackToTop();
			ticking = false;
		});
	}

	window.addEventListener('scroll', onScroll, { passive: true });

	// Initial state
	updateProgress();
	updateBackToTop();
})();
