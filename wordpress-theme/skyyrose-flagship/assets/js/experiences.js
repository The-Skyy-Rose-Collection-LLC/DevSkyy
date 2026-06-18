/**
 * experiences.js — Immersive Worlds hub (/experiences/) behaviour.
 *
 * Entrance reveal per block (IntersectionObserver), progress-rail active state,
 * and smooth rail navigation. Reduced-motion safe. No innerHTML, no inline JS
 * (CSP-compliant — enqueued, slug-gated in inc/enqueue.php).
 *
 * @package SkyyRose
 */
(function () {
	'use strict';

	var hub = document.querySelector('.experiences-hub');
	if (!hub) {
		return;
	}

	var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var blocks = Array.prototype.slice.call(document.querySelectorAll('.exp-block'));
	var contents = Array.prototype.slice.call(document.querySelectorAll('.exp-block__content'));
	var ticks = Array.prototype.slice.call(document.querySelectorAll('.exp-rail__tick'));

	// ── Entrance reveal ──────────────────────────────────────────────────────
	if (prefersReduced || !('IntersectionObserver' in window)) {
		contents.forEach(function (c) {
			c.classList.add('is-visible');
		});
	} else {
		var revealObserver = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('is-visible');
					}
				});
			},
			{ threshold: 0.45, rootMargin: '0px 0px -80px 0px' }
		);
		contents.forEach(function (c) {
			revealObserver.observe(c);
		});
	}

	// ── Progress-rail active state ───────────────────────────────────────────
	if ('IntersectionObserver' in window && ticks.length) {
		var activeIndex = 0;
		var setActive = function (idx) {
			if (idx === activeIndex || !ticks[idx]) {
				return;
			}
			if (ticks[activeIndex]) {
				ticks[activeIndex].classList.remove('is-active');
			}
			activeIndex = idx;
			ticks[activeIndex].classList.add('is-active');
		};

		var railObserver = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						var idx = parseInt(entry.target.getAttribute('data-block'), 10);
						if (!isNaN(idx)) {
							setActive(idx);
						}
					}
				});
			},
			{ threshold: 0.5 }
		);
		blocks.forEach(function (b) {
			railObserver.observe(b);
		});
	}

	// ── Rail click → smooth scroll ───────────────────────────────────────────
	ticks.forEach(function (tick) {
		tick.addEventListener('click', function (e) {
			var idx = parseInt(tick.getAttribute('data-index'), 10);
			var target = blocks[idx];
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth' });
			}
		});
	});
})();
