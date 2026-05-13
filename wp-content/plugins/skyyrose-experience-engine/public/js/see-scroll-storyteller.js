/**
 * Scroll Storyteller — Scroll-Driven Product Reveals
 *
 * Creates Apple-style progressive disclosure on product pages:
 * As the user scrolls, the product story unfolds — image, narrative,
 * materials, details, price, and CTA reveal sequentially.
 *
 * Uses IntersectionObserver with threshold arrays. Falls back to
 * CSS scroll-timeline where supported. Respects prefers-reduced-motion.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var SEE = window.SkyyRoseExperience;
	if (!SEE) {
		return;
	}

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CONFIG = {
		revealThreshold:   [0, 0.1, 0.25, 0.5, 0.75, 1],
		staggerDelay:      120,   // ms between sequential reveals
		parallaxStrength:  0.15,  // Parallax offset multiplier
		enableParallax:    !SEE.prefersReducedMotion,
	};

	var observers = [];
	var parallaxElements = [];
	var rafId = null;

	/* ==========================================================================
	   Story Section Enhancement
	   ========================================================================== */

	function enhanceStorySections() {
		// Find all scroll story containers (injected by WooCommerce integration).
		var containers = document.querySelectorAll('.see-scroll-story');

		containers.forEach(function (container) {
			// Find product page sections to animate.
			var sections = findStorySections(container);
			if (sections.length === 0) {
				return;
			}

			// Apply initial hidden state.
			sections.forEach(function (section, index) {
				section.classList.add('see-story-section');
				section.setAttribute('data-see-story-index', index);
				section.style.setProperty('--see-story-delay', (index * CONFIG.staggerDelay) + 'ms');
			});

			// Create IntersectionObserver for reveals.
			var observer = new IntersectionObserver(
				function (entries) {
					entries.forEach(function (entry) {
						if (entry.isIntersecting && entry.intersectionRatio >= 0.1) {
							revealSection(entry.target);
							observer.unobserve(entry.target);
						}
					});
				},
				{
					threshold: CONFIG.revealThreshold,
					rootMargin: '0px 0px -10% 0px',
				}
			);

			sections.forEach(function (section) {
				observer.observe(section);
			});

			observers.push(observer);
		});

		// Also enhance standalone elements with data-see-reveal attribute.
		var revealElements = document.querySelectorAll('[data-see-reveal]');
		if (revealElements.length > 0) {
			var revealObserver = new IntersectionObserver(
				function (entries) {
					entries.forEach(function (entry) {
						if (entry.isIntersecting) {
							var el = entry.target;
							var revealType = el.getAttribute('data-see-reveal') || 'fade-up';
							el.classList.add('see-revealed', 'see-reveal--' + revealType);
							SEE.emit('scroll:revealed', { element: el, type: revealType });
							revealObserver.unobserve(el);
						}
					});
				},
				{ threshold: 0.15, rootMargin: '0px 0px -5% 0px' }
			);

			revealElements.forEach(function (el) {
				el.classList.add('see-revealable');
				revealObserver.observe(el);
			});

			observers.push(revealObserver);
		}
	}

	/**
	 * Find sections within a product page that should be animated.
	 */
	function findStorySections(container) {
		var selectors = [
			'.woocommerce-product-gallery',
			'.product_title',
			'.woocommerce-product-details__short-description',
			'.product_meta',
			'.price',
			'.single_add_to_cart_button',
			'.woocommerce-tabs',
			'.related.products',
			// Theme-specific sections.
			'.see-curated-section',
			'.skyyrose-product-story',
		];

		var found = [];
		selectors.forEach(function (selector) {
			var el = container.querySelector(selector) || document.querySelector(selector);
			if (el && !el.classList.contains('see-story-section')) {
				found.push(el);
			}
		});

		return found;
	}

	function revealSection(element) {
		element.classList.add('see-story-visible');
		SEE.emit('scroll:section-revealed', {
			index: element.getAttribute('data-see-story-index'),
		});
	}

	/* ==========================================================================
	   Parallax Effect (desktop only, respects reduced motion)
	   ========================================================================== */

	function initParallax() {
		if (!CONFIG.enableParallax) {
			return;
		}

		parallaxElements = Array.from(document.querySelectorAll('[data-see-parallax]'));
		if (parallaxElements.length === 0) {
			return;
		}

		function updateParallax() {
			var scrollY = window.pageYOffset;

			parallaxElements.forEach(function (el) {
				var speed = parseFloat(el.getAttribute('data-see-parallax')) || CONFIG.parallaxStrength;
				var rect = el.getBoundingClientRect();
				var elementCenter = rect.top + rect.height / 2;
				var viewportCenter = window.innerHeight / 2;
				var offset = (elementCenter - viewportCenter) * speed;

				el.style.transform = 'translateY(' + offset.toFixed(1) + 'px)';
			});

			rafId = requestAnimationFrame(updateParallax);
		}

		// Register with Performance Guardian.
		if (SEE.performance) {
			SEE.performance.requestAnimation(
				'scroll-parallax',
				3, // Low priority
				function () { cancelAnimationFrame(rafId); rafId = null; },
				function () { rafId = requestAnimationFrame(updateParallax); }
			);
		}

		rafId = requestAnimationFrame(updateParallax);
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('scroll-storyteller', {
		init: function (moduleConfig) {
			Object.assign(CONFIG, moduleConfig);
		},

		ready: function () {
			if (!SEE.supportsIntersection) {
				// Fallback: reveal everything immediately.
				document.querySelectorAll('.see-story-section').forEach(function (el) {
					el.classList.add('see-story-visible');
				});
				return;
			}

			enhanceStorySections();
			initParallax();
		},

		destroy: function () {
			observers.forEach(function (obs) { obs.disconnect(); });
			observers = [];
			if (rafId) {
				cancelAnimationFrame(rafId);
			}
			if (SEE.performance) {
				SEE.performance.releaseAnimation('scroll-parallax');
			}
		},
	});

})();
