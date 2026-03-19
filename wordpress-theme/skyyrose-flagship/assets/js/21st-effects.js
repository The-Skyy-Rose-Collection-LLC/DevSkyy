/**
 * 21st Effects Engine — Auto-applies visual effects to existing DOM elements.
 *
 * Uses Intersection Observer to trigger text reveals and staggered entrances.
 * Uses mousemove to apply 3D tilt on product cards.
 * No React, no build step, no dependencies.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

(function () {
	'use strict';

	/* ──────────────────────────────────────────
	   Configuration: which selectors get which effects
	   ────────────────────────────────────────── */

	var CONFIG = {
		meshGradient: [
			'.lux-hero',
			'.collection-hero',
			'.shop-hero'
		],
		textReveal: [
			'.lux-hero__title',
			'.lux-hero__tagline',
			'.lux-heading',
			'.lux-eyebrow',
			'.collection-hero__title',
			'.collection-hero__subtitle',
			'.collection-hero__desc',
			'.splite__heading',
			'.splite__eyebrow'
		],
		glass: [
			'.lux-craft-grid > *',
			'.lux-col-card'
		],
		pulseBorder: [
			'.lux-btn',
			'.splite__cta'
		],
		tilt: [
			'.product-card',
			'.collections-card',
			'.lux-col-card',
			'.skyy-product-card__inner'
		],
		stagger: [
			'.lux-craft-grid',
			'.product-grid',
			'.lux-cols-grid',
			'.collections-grid',
			'.sr-related-grid',
			'.sr-rv-grid'
		]
	};

	/* ──────────────────────────────────────────
	   Utility: add class to matched elements
	   ────────────────────────────────────────── */

	/* Classes that indicate an existing reveal/animation system is active */
	var EXISTING_REVEAL = ['rv', 'rv-l', 'card-reveal-target'];

	function addFxClass(selectors, className, skipIfRevealed) {
		selectors.forEach(function (sel) {
			document.querySelectorAll(sel).forEach(function (el) {
				if (el.classList.contains(className)) return;

				/* Skip elements already managed by the .rv reveal system */
				if (skipIfRevealed) {
					for (var i = 0; i < EXISTING_REVEAL.length; i++) {
						if (el.classList.contains(EXISTING_REVEAL[i])) return;
					}
				}

				el.classList.add(className);
			});
		});
	}

	/* ──────────────────────────────────────────
	   Intersection Observer: reveal on scroll
	   ────────────────────────────────────────── */

	function initScrollReveal() {
		var targets = document.querySelectorAll('.fx-text-reveal, .fx-text-wipe, .fx-stagger');
		if (!targets.length) return;

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('fx-visible');
						observer.unobserve(entry.target);
					}
				});
			},
			{
				threshold: 0.15,
				rootMargin: '0px 0px -40px 0px'
			}
		);

		targets.forEach(function (el) {
			observer.observe(el);
		});
	}

	/* ──────────────────────────────────────────
	   Card Tilt: 3D perspective on mousemove
	   ────────────────────────────────────────── */

	function initTilt() {
		var cards = document.querySelectorAll('.fx-tilt');
		if (!cards.length) return;

		/* Respect reduced motion preference */
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

		cards.forEach(function (card) {
			card.addEventListener('mousemove', function (e) {
				var rect = card.getBoundingClientRect();
				var x = e.clientX - rect.left;
				var y = e.clientY - rect.top;
				var midX = rect.width / 2;
				var midY = rect.height / 2;

				/* Clamp rotation to ±6 degrees */
				var rotateY = ((x - midX) / midX) * 6;
				var rotateX = ((midY - y) / midY) * 6;

				card.style.transform =
					'perspective(800px) rotateX(' + rotateX.toFixed(2) + 'deg) rotateY(' + rotateY.toFixed(2) + 'deg)';
			});

			card.addEventListener('mouseleave', function () {
				card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
			});
		});
	}

	/* ──────────────────────────────────────────
	   Boot: apply classes then init behaviors
	   ────────────────────────────────────────── */

	function init() {
		/* 1. Mesh gradients on hero sections (no conflict with .rv) */
		addFxClass(CONFIG.meshGradient, 'fx-mesh-gradient', false);

		/* 2. Text reveals — skip elements already using .rv system */
		addFxClass(CONFIG.textReveal, 'fx-text-reveal', true);

		/* 3. Glassmorphism on feature cards */
		addFxClass(CONFIG.glass, 'fx-glass', false);

		/* 4. Pulsing borders on CTAs */
		addFxClass(CONFIG.pulseBorder, 'fx-pulse-border', false);

		/* 5. 3D tilt on product/collection cards — skip .rv cards */
		addFxClass(CONFIG.tilt, 'fx-tilt', true);

		/* 6. Staggered entrance — skip grids whose children use .rv */
		addFxClass(CONFIG.stagger, 'fx-stagger', true);

		/* Activate intersection observers */
		initScrollReveal();

		/* Activate tilt */
		initTilt();
	}

	/* DOM ready */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
