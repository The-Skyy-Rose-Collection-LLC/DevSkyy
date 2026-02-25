/**
 * Front Page — Hero animations, sparkle particles, scroll reveals.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Hero Sparkle Particles
	   -------------------------------------------------- */

	var sparkleContainer = document.getElementById('js-hero-sparkles');

	function createSparkle() {
		if (!sparkleContainer) return;

		var sparkle = document.createElement('div');
		sparkle.className = 'hero__sparkle';
		sparkle.style.left = Math.random() * 100 + '%';
		sparkle.style.top = Math.random() * 100 + '%';
		sparkle.style.animationDuration = (1.5 + Math.random() * 2.5) + 's';
		sparkle.style.animationDelay = Math.random() * 0.5 + 's';
		sparkle.style.width = sparkle.style.height = (2 + Math.random() * 3) + 'px';
		sparkleContainer.appendChild(sparkle);

		sparkle.addEventListener('animationend', function () {
			sparkle.remove();
		});
	}

	function initSparkles() {
		if (!sparkleContainer) return;

		// Initial burst.
		for (var i = 0; i < 12; i++) {
			setTimeout(createSparkle, i * 150);
		}

		// Ongoing sparkles.
		setInterval(createSparkle, 400);
	}

	/* --------------------------------------------------
	   Hero Orb Ambient Animation
	   -------------------------------------------------- */

	function initOrbs() {
		var orbs = document.querySelectorAll('.hero__orb');
		if (orbs.length === 0) return;

		// Stagger start with slight randomness.
		orbs.forEach(function (orb, i) {
			orb.style.animationDelay = (i * 0.8 + Math.random() * 0.5) + 's';
		});
	}

	/* --------------------------------------------------
	   Scroll Reveal — Intersection Observer
	   -------------------------------------------------- */

	function initScrollReveal() {
		var revealElements = document.querySelectorAll(
			'.collections__card, .value-prop, .featured-product, ' +
			'.press-item, .testimonial-card, .story-content, ' +
			'.newsletter-section, .section-title, .instagram-item'
		);

		if (revealElements.length === 0 || !('IntersectionObserver' in window)) return;

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('revealed');
					observer.unobserve(entry.target);
				}
			});
		}, {
			threshold: 0.15,
			rootMargin: '0px 0px -50px 0px'
		});

		revealElements.forEach(function (el) {
			el.classList.add('reveal-target');
			observer.observe(el);
		});
	}

	/* --------------------------------------------------
	   Social Proof Counter Animation
	   -------------------------------------------------- */

	function initCounters() {
		var counters = document.querySelectorAll('[data-count-target]');
		if (counters.length === 0) return;

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					animateCounter(entry.target);
					observer.unobserve(entry.target);
				}
			});
		}, { threshold: 0.5 });

		counters.forEach(function (counter) {
			observer.observe(counter);
		});
	}

	function animateCounter(el) {
		var target = parseInt(el.dataset.countTarget, 10);
		if (isNaN(target)) return;

		var duration = 2000;
		var start = 0;
		var startTime = null;

		function step(timestamp) {
			if (!startTime) startTime = timestamp;
			var progress = Math.min((timestamp - startTime) / duration, 1);
			var eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
			var current = Math.floor(eased * target);

			el.textContent = current.toLocaleString();

			if (progress < 1) {
				requestAnimationFrame(step);
			} else {
				el.textContent = target.toLocaleString();
			}
		}

		requestAnimationFrame(step);
	}

	/* --------------------------------------------------
	   Newsletter Form
	   -------------------------------------------------- */

	function initNewsletter() {
		var form = document.querySelector('.newsletter-form');
		if (!form) return;

		form.addEventListener('submit', function (e) {
			e.preventDefault();
			var email = form.querySelector('input[type="email"]');
			var btn = form.querySelector('button[type="submit"]');

			if (!email || !email.value) return;

			if (btn) {
				btn.textContent = 'Joining...';
				btn.disabled = true;
			}

			// Simulate API call (replace with real endpoint).
			setTimeout(function () {
				if (btn) {
					btn.textContent = 'Welcome to the Family!';
					btn.classList.add('success');
				}
				if (email) {
					email.value = '';
				}
				setTimeout(function () {
					if (btn) {
						btn.textContent = 'Join the Family';
						btn.disabled = false;
						btn.classList.remove('success');
					}
				}, 3000);
			}, 1000);
		});
	}

	/* --------------------------------------------------
	   Rotating Text — Cycles through collection names
	   -------------------------------------------------- */

	function initRotatingText() {
		var el = document.querySelector('.js-rotating-text');
		if (!el || !el.dataset.texts) return;

		var texts;
		try {
			texts = JSON.parse(el.dataset.texts);
		} catch (e) {
			return;
		}

		if (!Array.isArray(texts) || texts.length < 2) return;

		var currentIndex = 0;

		setInterval(function () {
			el.style.opacity = '0';
			setTimeout(function () {
				currentIndex = (currentIndex + 1) % texts.length;
				el.textContent = texts[currentIndex];
				el.style.opacity = '1';
			}, 300);
		}, 3000);
	}

	/* --------------------------------------------------
	   Smooth Scroll — Anchor links
	   -------------------------------------------------- */

	function initSmoothScroll() {
		var links = document.querySelectorAll('.js-smooth-scroll');
		links.forEach(function (link) {
			link.addEventListener('click', function (e) {
				var href = link.getAttribute('href');
				if (!href || href.charAt(0) !== '#') return;

				var target = document.querySelector(href);
				if (!target) return;

				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			});
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initSparkles();
		initOrbs();
		initScrollReveal();
		initCounters();
		initNewsletter();
		initRotatingText();
		initSmoothScroll();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
