/**
 * Page Transitions — SkyyRose
 *
 * Smooth cross-fade transitions between pages using the View Transitions API
 * (Chrome 111+) with graceful degradation for unsupported browsers.
 *
 * Also handles:
 *  - Skeleton screen injection/removal on image loads
 *  - Scarcity indicator animation on scroll
 *
 * @package SkyyRose
 * @since   6.4.0
 */

(function () {
	'use strict';

	/* ── Respect reduced motion ────────────────────────────────── */
	var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ══════════════════════════════════════════════════════════════
	   1. VIEW TRANSITIONS (progressive enhancement)
	   ══════════════════════════════════════════════════════════════ */

	if (!prefersReduced && document.startViewTransition) {
		document.addEventListener('click', function (e) {
			var link = e.target.closest('a[href]');
			if (!link) return;

			var url = link.href;
			if (
				link.origin !== location.origin ||
				link.hasAttribute('download') ||
				link.target === '_blank' ||
				(link.hash && link.pathname === location.pathname) ||
				e.ctrlKey || e.metaKey || e.shiftKey
			) {
				return;
			}

			e.preventDefault();

			document.startViewTransition(function () {
				return fetch(url)
					.then(function (res) { return res.text(); })
					.then(function (html) {
						var parser = new DOMParser();
						var doc = parser.parseFromString(html, 'text/html');

						// Replace main content using safe DOM methods (no innerHTML)
						var newContent = doc.getElementById('content') || doc.querySelector('main');
						var currentContent = document.getElementById('content') || document.querySelector('main');

						if (currentContent && newContent) {
							// Move parsed child nodes into the live DOM
							while (currentContent.firstChild) {
								currentContent.removeChild(currentContent.firstChild);
							}
							while (newContent.firstChild) {
								currentContent.appendChild(document.adoptNode(newContent.firstChild));
							}
						}

						document.title = doc.title;
						history.pushState(null, '', url);
						window.scrollTo(0, 0);

						initSkeletons();
						initScarcityBars();
					});
			});
		});

		var ptLastPath = location.pathname + location.search;
		window.addEventListener('popstate', function () {
			var ptNow = location.pathname + location.search;
			// Hash-only or synthetic popstate (scroll restoration, injected
			// history entries) must not hard-reload the page mid-scroll.
			if (ptNow === ptLastPath) {
				return;
			}
			ptLastPath = ptNow;
			if (document.startViewTransition) {
				document.startViewTransition(function () {
					location.reload();
				});
			}
		});
	}

	/* ══════════════════════════════════════════════════════════════
	   2. SKELETON SCREENS — auto-inject on lazy images
	   ══════════════════════════════════════════════════════════════ */

	function initSkeletons() {
		var lazyImages = document.querySelectorAll('.holo__img[loading="lazy"]');

		lazyImages.forEach(function (img) {
			if (img.complete && img.naturalHeight > 0) return;
			if (img.parentElement.querySelector('.skeleton--img')) return;

			var skel = document.createElement('div');
			skel.className = 'skeleton skeleton--img';
			skel.setAttribute('aria-hidden', 'true');
			img.parentElement.insertBefore(skel, img);

			img.addEventListener('load', function () {
				skel.classList.add('loaded');
				setTimeout(function () {
					if (skel.parentNode) skel.parentNode.removeChild(skel);
				}, 500);
			}, { once: true });

			img.addEventListener('error', function () {
				if (skel.parentNode) skel.parentNode.removeChild(skel);
			}, { once: true });
		});
	}

	/* ══════════════════════════════════════════════════════════════
	   3. SCARCITY BARS — animate fill width on scroll into view
	   ══════════════════════════════════════════════════════════════ */

	function initScarcityBars() {
		var bars = document.querySelectorAll('.holo__scarcity-fill');
		if (!bars.length) return;

		if (prefersReduced) {
			bars.forEach(function (bar) {
				bar.style.width = bar.getAttribute('data-percent') + '%';
			});
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					var fill = entry.target;
					fill.style.width = fill.getAttribute('data-percent') + '%';
					observer.unobserve(fill);
				}
			});
		}, { threshold: 0.5 });

		bars.forEach(function (bar) {
			bar.style.width = '0%';
			observer.observe(bar);
		});
	}

	/* ══════════════════════════════════════════════════════════════
	   4. INIT ON LOAD
	   ══════════════════════════════════════════════════════════════ */

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', function () {
			initSkeletons();
			initScarcityBars();
		});
	} else {
		initSkeletons();
		initScarcityBars();
	}

})();
