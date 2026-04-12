/**
 * Kids Capsule — Launch Mode JS
 *
 * Countdown timer, GSAP ScrollTrigger animations, and waitlist form.
 * Loaded only when KC is in launch mode (slug: kc-launch).
 *
 * @package SkyyRose
 * @since   6.5.0
 */

(function () {
	'use strict';

	var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ---------------------------------------------------------------
	 * 1. Countdown Timer
	 * --------------------------------------------------------------- */

	function initCountdown() {
		var container = document.querySelector('.kc-countdown[data-countdown]');
		if (!container) {
			return;
		}

		var targetDate = new Date(container.getAttribute('data-countdown')).getTime();
		if (isNaN(targetDate)) {
			return;
		}

		var els = {
			d: container.querySelector('[data-cd="d"]'),
			h: container.querySelector('[data-cd="h"]'),
			m: container.querySelector('[data-cd="m"]'),
			s: container.querySelector('[data-cd="s"]'),
		};

		function pad(n) {
			return n < 10 ? '0' + n : String(n);
		}

		function tick() {
			var now  = Date.now();
			var diff = Math.max(0, targetDate - now);

			var d = Math.floor(diff / 86400000);
			var h = Math.floor((diff % 86400000) / 3600000);
			var m = Math.floor((diff % 3600000) / 60000);
			var s = Math.floor((diff % 60000) / 1000);

			if (els.d) { els.d.textContent = pad(d); }
			if (els.h) { els.h.textContent = pad(h); }
			if (els.m) { els.m.textContent = pad(m); }
			if (els.s) { els.s.textContent = pad(s); }

			if (diff > 0) {
				requestAnimationFrame(tick);
			}
		}

		tick();
	}

	/* ---------------------------------------------------------------
	 * 2. GSAP Scroll Animations
	 * --------------------------------------------------------------- */

	function initAnimations() {
		if (reducedMotion) {
			return;
		}

		if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
			return;
		}

		gsap.registerPlugin(ScrollTrigger);

		// Hero entrance.
		var heroContent = document.querySelector('.kc-teaser__hero-content');
		if (heroContent) {
			gsap.from(heroContent.children, {
				y: 40,
				opacity: 0,
				duration: 1,
				stagger: 0.15,
				ease: 'power2.out',
			});
		}

		// Reveal sections on scroll.
		var sections = document.querySelectorAll('.kc-teaser__reveal, .kc-teaser__countdown, .kc-teaser__preview, .kc-teaser__waitlist, .kc-teaser__anchor');

		sections.forEach(function (section) {
			gsap.from(section, {
				scrollTrigger: {
					trigger: section,
					start: 'top 85%',
					once: true,
				},
				y: 30,
				opacity: 0,
				duration: 0.8,
				ease: 'power2.out',
			});
		});

		// Silhouette scale-in.
		var silhouettes = document.querySelectorAll('.kc-teaser__silhouette');
		if (silhouettes.length) {
			gsap.from(silhouettes, {
				scrollTrigger: {
					trigger: '.kc-teaser__silhouettes',
					start: 'top 80%',
					once: true,
				},
				scale: 0.9,
				opacity: 0,
				duration: 0.8,
				stagger: 0.2,
				ease: 'power2.out',
			});
		}
	}

	/* ---------------------------------------------------------------
	 * 3. Waitlist Form
	 * --------------------------------------------------------------- */

	function initWaitlistForm() {
		var form = document.getElementById('kc-waitlist-form');
		if (!form) {
			return;
		}

		form.addEventListener('submit', function (e) {
			e.preventDefault();

			var emailInput = form.querySelector('#kc-email');
			var statusEl   = form.querySelector('.kc-waitlist-form__status');
			var nonceInput = form.querySelector('[name="kc_waitlist_nonce"]');
			var btn        = form.querySelector('.kc-waitlist-form__btn');
			var email      = emailInput ? emailInput.value.trim() : '';
			var nonce      = nonceInput ? nonceInput.value : '';

			if (!email) {
				return;
			}

			if (btn) {
				btn.disabled = true;
				btn.textContent = 'Sending...';
			}

			var body = new FormData();
			body.append('action', 'skyyrose_newsletter_signup');
			body.append('email', email);
			body.append('list', 'kids_capsule');
			body.append('kc_waitlist_nonce', nonce);

			var ajaxUrl = (typeof skyyRoseWoo !== 'undefined' && skyyRoseWoo.ajax_url)
				? skyyRoseWoo.ajax_url
				: '/wp-admin/admin-ajax.php';

			fetch(ajaxUrl, {
				method: 'POST',
				body: body,
				credentials: 'same-origin',
			})
				.then(function (res) { return res.json(); })
				.then(function (data) {
					if (statusEl) {
						statusEl.textContent = data.success
							? 'You\'re on the list! We\'ll be in touch.'
							: (data.data && data.data.message ? data.data.message : 'Something went wrong. Please try again.');
					}
					if (data.success && emailInput) {
						emailInput.value = '';
					}
				})
				.catch(function () {
					if (statusEl) {
						statusEl.textContent = 'Something went wrong. Please try again.';
					}
				})
				.finally(function () {
					if (btn) {
						btn.disabled = false;
						btn.textContent = 'Join the Waitlist';
					}
				});
		});
	}

	/* ---------------------------------------------------------------
	 * 4. Init
	 * --------------------------------------------------------------- */

	function init() {
		initCountdown();
		initAnimations();
		initWaitlistForm();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
