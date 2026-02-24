/**
 * Collection Pages — 3D logo rotation, product grid animation,
 * sort/filter controls, and kids capsule floating elements.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   3D Logo Rotation (CSS-driven, JS triggers)
	   -------------------------------------------------- */

	function initLogoRotation() {
		var logos = document.querySelectorAll('.collection-logo-3d');
		if (logos.length === 0) return;

		logos.forEach(function (logo) {
			// Pause on hover for inspection.
			logo.addEventListener('mouseenter', function () {
				logo.style.animationPlayState = 'paused';
			});
			logo.addEventListener('mouseleave', function () {
				logo.style.animationPlayState = 'running';
			});
		});
	}

	/* --------------------------------------------------
	   Product Card Stagger Animation
	   -------------------------------------------------- */

	function initProductCardReveal() {
		var cards = document.querySelectorAll('.product-card');
		if (cards.length === 0 || !('IntersectionObserver' in window)) return;

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('revealed');
					observer.unobserve(entry.target);
				}
			});
		}, {
			threshold: 0.1,
			rootMargin: '0px 0px -30px 0px'
		});

		cards.forEach(function (card, i) {
			card.style.transitionDelay = (i * 0.08) + 's';
			card.classList.add('card-reveal-target');
			observer.observe(card);
		});
	}

	/* --------------------------------------------------
	   Collection Filter / Sort (if present)
	   -------------------------------------------------- */

	function initCollectionFilter() {
		var filterBtns = document.querySelectorAll('.collection-filter-btn');
		var productCards = document.querySelectorAll('.product-card[data-category]');
		if (filterBtns.length === 0) return;

		filterBtns.forEach(function (btn) {
			btn.addEventListener('click', function () {
				var filter = btn.dataset.filter;

				// Toggle active state.
				filterBtns.forEach(function (b) { b.classList.remove('active'); });
				btn.classList.add('active');

				productCards.forEach(function (card) {
					if (filter === 'all' || card.dataset.category === filter) {
						card.style.display = '';
						card.classList.add('revealed');
					} else {
						card.style.display = 'none';
					}
				});
			});
		});
	}

	/* --------------------------------------------------
	   Quick-View Overlay
	   -------------------------------------------------- */

	function initQuickView() {
		var quickViewBtns = document.querySelectorAll('.product-card-overlay, .quick-view-btn');
		if (quickViewBtns.length === 0) return;

		quickViewBtns.forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.preventDefault();
				var card = btn.closest('.product-card');
				if (!card) return;

				var productUrl = card.querySelector('a') ? card.querySelector('a').href : '#';
				// Navigate to product page.
				if (productUrl !== '#') {
					window.location.href = productUrl;
				}
			});
		});
	}

	/* --------------------------------------------------
	   Kids Capsule — Floating Stars & Bubbles
	   -------------------------------------------------- */

	function initKidsFloatingElements() {
		var container = document.querySelector('.kids-capsule-floating');
		if (!container) return;

		var symbols = ['★', '✦', '◦', '✧', '○'];

		function createFloater() {
			var el = document.createElement('span');
			el.className = 'kids-floater';
			el.textContent = symbols[Math.floor(Math.random() * symbols.length)];
			el.style.left = Math.random() * 100 + '%';
			el.style.fontSize = (10 + Math.random() * 16) + 'px';
			el.style.animationDuration = (4 + Math.random() * 6) + 's';
			el.style.opacity = (0.15 + Math.random() * 0.25).toString();
			container.appendChild(el);

			el.addEventListener('animationend', function () {
				el.remove();
			});
		}

		for (var i = 0; i < 8; i++) {
			setTimeout(createFloater, i * 300);
		}
		setInterval(createFloater, 800);
	}

	/* --------------------------------------------------
	   Cross-Collection Navigation Highlights
	   -------------------------------------------------- */

	function initCrossNavHighlight() {
		var navCards = document.querySelectorAll('.cross-collection-card');
		if (navCards.length === 0) return;

		navCards.forEach(function (card) {
			card.addEventListener('mouseenter', function () {
				card.classList.add('hovered');
			});
			card.addEventListener('mouseleave', function () {
				card.classList.remove('hovered');
			});
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initLogoRotation();
		initProductCardReveal();
		initCollectionFilter();
		initQuickView();
		initKidsFloatingElements();
		initCrossNavHighlight();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
