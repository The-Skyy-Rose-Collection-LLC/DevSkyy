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

		// Fallback removal if animationend never fires (e.g. prefers-reduced-motion).
		setTimeout(function () {
			if (sparkle.parentNode) sparkle.remove();
		}, 5000);
	}

	function initSparkles() {
		if (!sparkleContainer) return;

		var motionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

		// Skip sparkles entirely when user prefers reduced motion.
		if (motionQuery && motionQuery.matches) return;

		// Initial burst.
		for (var i = 0; i < 12; i++) {
			setTimeout(createSparkle, i * 150);
		}

		// Ongoing sparkles — store reference so it can be cleared.
		var sparkleInterval = setInterval(createSparkle, 400);

		// Stop sparkles if user enables reduced motion mid-session.
		if (motionQuery && motionQuery.addEventListener) {
			motionQuery.addEventListener('change', function (e) {
				if (e.matches) clearInterval(sparkleInterval);
			});
		}
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
		var form = document.querySelector('.js-newsletter-form');
		if (!form) return;

		form.addEventListener('submit', function (e) {
			e.preventDefault();
			var emailInput = form.querySelector('input[type="email"]');
			var btn = form.querySelector('button[type="submit"]');

			if (!emailInput || !emailInput.value) return;

			if (btn) {
				btn.textContent = 'Joining...';
				btn.disabled = true;
			}

			var xhr = new XMLHttpRequest();
			xhr.open('POST', form.action || (typeof skyyRoseData !== 'undefined' ? skyyRoseData.ajaxUrl : ''), true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (resp.success) {
							if (btn) {
								btn.textContent = 'Welcome to the Family!';
								btn.classList.add('success');
							}
							if (emailInput) emailInput.value = '';
							setTimeout(function () {
								if (btn) {
									btn.textContent = 'Join the Family';
									btn.disabled = false;
									btn.classList.remove('success');
								}
							}, 3000);
							return;
						}
					} catch (_) { /* fall through */ }
				}
				if (btn) {
					btn.textContent = 'Try Again';
					btn.disabled = false;
				}
			};

			xhr.onerror = function () {
				if (btn) {
					btn.textContent = 'Try Again';
					btn.disabled = false;
				}
			};

			var formData = new FormData(form);
			var params = [];
			formData.forEach(function (value, key) {
				params.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
			});
			xhr.send(params.join('&'));
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
