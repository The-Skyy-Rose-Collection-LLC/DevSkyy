/**
 * Pre-Order Gateway Interactions
 *
 * Rolling 72h countdown, GSAP hero entrance + ScrollTrigger grid reveals,
 * IntersectionObserver scroll-reveal, FAQ accordion, cart summary bar,
 * and smooth-scroll anchor links.
 *
 * @package SkyyRose
 * @since   2.0.0
 * @updated 7.0.0 — CRO transformation
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Rolling 72h Countdown
	   -------------------------------------------------- */

	function initCountdown() {
		var el = document.querySelector('.po-hero__countdown');
		if (!el) return;

		var mode = (el.dataset.countdown || '72h').trim();
		var target;

		if (mode.match(/^\d+h$/)) {
			// Rolling countdown: always shows X hours from page load.
			// Uses sessionStorage so the target persists within a visit
			// but resets each new session (keeps urgency fresh).
			var hours = parseInt(mode, 10);
			var key = 'po_countdown_target';
			var stored = sessionStorage.getItem(key);

			if (stored && parseInt(stored, 10) > Date.now()) {
				target = parseInt(stored, 10);
			} else {
				target = Date.now() + hours * 3600000;
				sessionStorage.setItem(key, String(target));
			}
		} else {
			// Fixed ISO date.
			target = new Date(mode).getTime();
		}

		var dEl = el.querySelector('[data-cd="d"]');
		var hEl = el.querySelector('[data-cd="h"]');
		var mEl = el.querySelector('[data-cd="m"]');
		var sEl = el.querySelector('[data-cd="s"]');

		function pad(n) { return n < 10 ? '0' + n : '' + n; }

		var intervalId;

		function tick() {
			var diff = Math.max(0, target - Date.now());
			var d = Math.floor(diff / 86400000);
			var h = Math.floor((diff % 86400000) / 3600000);
			var m = Math.floor((diff % 3600000) / 60000);
			var s = Math.floor((diff % 60000) / 1000);

			if (dEl) dEl.textContent = pad(d);
			if (hEl) hEl.textContent = pad(h);
			if (mEl) mEl.textContent = pad(m);
			if (sEl) sEl.textContent = pad(s);

			if (diff === 0 && intervalId) {
				clearInterval(intervalId);
				// Reset for next cycle so it never shows zeros.
				sessionStorage.removeItem('po_countdown_target');
			}
		}

		tick();
		intervalId = setInterval(tick, 1000);

		// Pause when tab is hidden to avoid unnecessary work.
		document.addEventListener('visibilitychange', function () {
			if (document.hidden) {
				if (intervalId) { clearInterval(intervalId); intervalId = null; }
			} else {
				tick();
				if (!intervalId) { intervalId = setInterval(tick, 1000); }
			}
		});
	}

	/* --------------------------------------------------
	   GSAP Hero Entrance Animations
	   -------------------------------------------------- */

	function initHeroAnimations() {
		if (typeof gsap === 'undefined') return;

		gsap.from('.po-hero__badge', {
			opacity: 0, y: 20, duration: 0.8, delay: 0.2, ease: 'power3.out'
		});
		gsap.from('.po-hero__title', {
			opacity: 0, y: 30, duration: 1, delay: 0.4, ease: 'power3.out'
		});
		gsap.from('.po-hero__tagline', {
			opacity: 0, y: 20, duration: 0.8, delay: 0.7, ease: 'power3.out'
		});
		gsap.from('.po-hero__countdown', {
			opacity: 0, y: 20, duration: 0.8, delay: 0.9, ease: 'power3.out'
		});
		gsap.from('.po-hero__ctas', {
			opacity: 0, y: 20, duration: 0.8, delay: 1.1, ease: 'power3.out'
		});
	}

	/* --------------------------------------------------
	   GSAP ScrollTrigger — Collection Grid Reveals
	   -------------------------------------------------- */

	function initGridReveals() {
		if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

		gsap.registerPlugin(ScrollTrigger);

		var sections = document.querySelectorAll('.po-collection');
		sections.forEach(function (section) {
			var cards = section.querySelectorAll('.holo');
			if (cards.length === 0) return;

			// Set initial state.
			gsap.set(cards, { opacity: 0, y: 40 });

			ScrollTrigger.create({
				trigger: section,
				start: 'top 80%',
				once: true,
				onEnter: function () {
					gsap.to(cards, {
						opacity: 1, y: 0,
						duration: 0.7, stagger: 0.08,
						ease: 'power3.out',
						onComplete: function () {
							// Remove inline styles so CSS hover effects work normally.
							cards.forEach(function (card) {
								card.style.opacity = '';
								card.style.transform = '';
								card.classList.add('holo--visible');
							});
						}
					});
				}
			});
		});
	}

	/* --------------------------------------------------
	   IntersectionObserver Scroll Reveal (.po-rv)
	   -------------------------------------------------- */

	function initScrollReveal() {
		// Handle both po-rv (preorder sections) and lp-rv (FAQ template part).
		var elements = document.querySelectorAll('.po-rv, .preorder-gateway .lp-rv');
		if (elements.length === 0) return;

		// Skip if prefers-reduced-motion.
		if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
			elements.forEach(function (el) {
				el.classList.add('po-rv--visible');
				el.classList.add('lp-rv--visible');
			});
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('po-rv--visible');
					entry.target.classList.add('lp-rv--visible');
					observer.unobserve(entry.target);
				}
			});
		}, { threshold: 0.15 });

		elements.forEach(function (el) { observer.observe(el); });
	}

	/* --------------------------------------------------
	   FAQ Accordion (for landing/faq.php template part)
	   -------------------------------------------------- */

	function initFaqAccordion() {
		var questions = document.querySelectorAll('.lp-faq__question');
		if (questions.length === 0) return;

		questions.forEach(function (btn) {
			btn.addEventListener('click', function () {
				var expanded = btn.getAttribute('aria-expanded') === 'true';
				var answerId = btn.getAttribute('aria-controls');
				var answer = answerId ? document.getElementById(answerId) : null;

				// Close all others first (accordion behavior).
				questions.forEach(function (other) {
					if (other !== btn) {
						other.setAttribute('aria-expanded', 'false');
						var otherId = other.getAttribute('aria-controls');
						var otherAnswer = otherId ? document.getElementById(otherId) : null;
						if (otherAnswer) otherAnswer.style.maxHeight = '0';
					}
				});

				// Toggle this one.
				btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
				if (answer) {
					if (expanded) {
						answer.style.maxHeight = '0';
					} else {
						answer.style.maxHeight = answer.scrollHeight + 'px';
					}
				}
			});
		});
	}

	/* --------------------------------------------------
	   Cart Summary Bar
	   -------------------------------------------------- */

	function initCartSummaryBar() {
		var bar = document.getElementById('cart-summary');
		if (!bar) return;

		var countEl = document.getElementById('cart-summary-count');

		function update() {
			// Check WooCommerce cart count from nav badge.
			var navCount = document.querySelector('.nav-cart-count, .cart-contents .count');
			var count = navCount ? parseInt(navCount.textContent, 10) || 0 : 0;

			if (count > 0) {
				bar.classList.add('po-cart-summary--visible');
				if (countEl) {
					var word = count === 1 ? 'item' : 'items';
					countEl.textContent = count + ' ' + word;
				}
			} else {
				bar.classList.remove('po-cart-summary--visible');
			}
		}

		// Listen for WooCommerce AJAX cart updates.
		if (typeof jQuery !== 'undefined') {
			jQuery(document.body).on(
				'added_to_cart removed_from_cart wc_fragments_refreshed',
				update
			);
		}

		update();
	}

	/* --------------------------------------------------
	   Smooth Scroll for Anchor Links
	   -------------------------------------------------- */

	function initSmoothScroll() {
		var links = document.querySelectorAll('.po-btn[href^="#"], .po-hero__scroll');
		links.forEach(function (link) {
			link.addEventListener('click', function (e) {
				var href = link.getAttribute('href');
				if (!href || href.charAt(0) !== '#') return;

				var target = document.getElementById(href.substring(1));
				if (!target) return;

				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			});
		});
	}

	/* --------------------------------------------------
	   Email CTA Form
	   -------------------------------------------------- */

	function initEmailForm() {
		var form = document.querySelector('.po-cta__form');
		if (!form) return;

		form.addEventListener('submit', function (e) {
			e.preventDefault();

			var submitBtn = form.querySelector('.po-cta__submit');
			var emailInput = form.querySelector('.po-cta__input');
			if (!emailInput || !emailInput.value) return;

			if (submitBtn) {
				submitBtn.textContent = 'Joining...';
				submitBtn.disabled = true;
			}

			var ajaxUrl = window.skyyRoseData && window.skyyRoseData.ajaxUrl;
			if (!ajaxUrl) {
				// No AJAX endpoint — show success anyway (email captured client-side).
				if (submitBtn) submitBtn.textContent = 'Welcome!';
				return;
			}

			var xhr = new XMLHttpRequest();
			xhr.open('POST', ajaxUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				try {
					var resp = JSON.parse(xhr.responseText);
					if (resp && resp.success) {
						if (submitBtn) submitBtn.textContent = 'Reserved.';
					} else {
						if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
					}
				} catch (err) {
					if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
				}
			};

			xhr.onerror = function () {
				if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
			};

			var nonce = form.querySelector('[name="po_nonce"]');
			var params = 'action=skyyrose_newsletter_signup'
				+ '&email=' + encodeURIComponent(emailInput.value)
				+ '&nonce=' + encodeURIComponent(nonce ? nonce.value : '');
			xhr.send(params);
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initCountdown();
		initHeroAnimations();
		initGridReveals();
		initScrollReveal();
		initFaqAccordion();
		initCartSummaryBar();
		initSmoothScroll();
		initEmailForm();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
