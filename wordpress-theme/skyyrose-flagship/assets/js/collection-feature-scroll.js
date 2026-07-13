/**
 * Collection Feature Scroll — active-item + sticky-image choreography.
 *
 * GSAP ScrollTrigger drives the active state on desktop (discrete swap per
 * item — no scrub); IntersectionObserver is the fallback when GSAP is
 * unavailable, motion is reduced, or the viewport is mobile (where CSS
 * stacks the layout and the classes only steer the accent state).
 *
 * No innerHTML — class toggles only.
 *
 * @package SkyyRose
 * @since   1.10.3
 */

(function () {
	'use strict';

	function init() {
		var section = document.querySelector('[data-featscroll]');
		if (!section) {
			return;
		}

		var items = Array.prototype.slice.call(section.querySelectorAll('[data-feat-item]'));
		var imgs = Array.prototype.slice.call(section.querySelectorAll('[data-feat-img]'));
		if (items.length < 2) {
			return;
		}

		var current = -1;

		function activate(index) {
			if (index === current || index < 0) {
				return;
			}
			current = index;
			items.forEach(function (item, i) {
				item.classList.toggle('is-active', i === index);
			});
			imgs.forEach(function (img, i) {
				img.classList.toggle('is-active', i === index);
			});
		}

		activate(0);

		var desktop = window.matchMedia('(min-width: 901px)').matches;
		var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

		if (window.gsap && window.ScrollTrigger && desktop && !reduced) {
			window.gsap.registerPlugin(window.ScrollTrigger);
			items.forEach(function (item, i) {
				window.ScrollTrigger.create({
					trigger: item,
					start: 'top 55%',
					end: 'bottom 55%',
					onEnter: function () {
						activate(i);
					},
					onEnterBack: function () {
						activate(i);
					}
				});
			});
			return;
		}

		if (!('IntersectionObserver' in window)) {
			return;
		}
		var io = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						activate(items.indexOf(entry.target));
					}
				});
			},
			{ rootMargin: '-45% 0px -45% 0px' }
		);
		items.forEach(function (item) {
			io.observe(item);
		});
	}

	if ('loading' === document.readyState) {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
}());
