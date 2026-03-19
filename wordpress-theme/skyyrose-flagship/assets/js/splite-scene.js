/**
 * Splite Scene — Mouse-tracking spotlight + Spline scene loader.
 *
 * Vanilla JS replacement for Framer Motion's useSpring + lazy React import.
 * Attaches to every .splite__card on the page.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

(function () {
	'use strict';

	/**
	 * Mouse-tracking glow spotlight (ibelick-style).
	 * Follows cursor within .splite__card, fades in on hover.
	 */
	function initSpotlight(card) {
		var glow = card.querySelector('.splite__glow');
		if (!glow) return;

		card.addEventListener('mousemove', function (e) {
			var rect = card.getBoundingClientRect();
			glow.style.left = (e.clientX - rect.left) + 'px';
			glow.style.top = (e.clientY - rect.top) + 'px';
		});
	}

	/**
	 * Hide loader once the Spline viewer finishes loading.
	 * Polls for the <spline-viewer>'s shadow DOM canvas, then fades out the loader.
	 */
	function initSceneLoader(card) {
		var loader = card.querySelector('.splite__loader');
		var viewer = card.querySelector('spline-viewer');
		if (!loader || !viewer) return;

		/* Spline viewer fires a 'load' event when the scene is ready. */
		viewer.addEventListener('load', function () {
			loader.classList.add('hidden');
		});

		/* Fallback: if the load event doesn't fire within 12s, hide the loader anyway. */
		setTimeout(function () {
			loader.classList.add('hidden');
		}, 12000);
	}

	/**
	 * Intersection Observer — only load the Spline runtime when the section
	 * scrolls into view. Prevents a heavy 3D engine from blocking above-the-fold.
	 */
	function initLazySpline() {
		var sections = document.querySelectorAll('.splite');
		if (!sections.length) return;

		/* Check if the Spline viewer script is already loaded. */
		if (customElements.get('spline-viewer')) {
			sections.forEach(function (s) {
				initSpotlight(s.querySelector('.splite__card'));
				initSceneLoader(s.querySelector('.splite__card'));
			});
			return;
		}

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (!entry.isIntersecting) return;

					/* Load the Spline viewer web component from CDN. */
					if (!document.querySelector('script[src*="splinetool/viewer"]')) {
						var script = document.createElement('script');
						script.type = 'module';
						script.src = 'https://unpkg.com/@splinetool/viewer@1.9.82/build/spline-viewer.js';
						document.head.appendChild(script);
					}

					var card = entry.target.querySelector('.splite__card');
					if (card) {
						initSpotlight(card);
						initSceneLoader(card);
					}

					observer.unobserve(entry.target);
				});
			},
			{ rootMargin: '200px' }
		);

		sections.forEach(function (section) {
			observer.observe(section);
		});
	}

	/* Boot on DOM ready. */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', initLazySpline);
	} else {
		initLazySpline();
	}
})();
