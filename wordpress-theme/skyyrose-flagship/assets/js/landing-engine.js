/**
 * SkyyRose Landing Page Engine
 *
 * Shared JS for all 3 collection landing pages:
 * - Countdown timer (reads deadline from data attribute or skyyRoseData)
 * - Scroll-reveal animations via IntersectionObserver
 * - FAQ accordion with single-open behavior
 * - Parallax effect on parallax-break images
 * - Nav scroll state (compact on scroll)
 * - Newsletter form AJAX submission
 * - Scarcity pulse animation (auto-managed via CSS)
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

(function () {
	'use strict';

	/* -------------------------------------------------------
	 * 1. Scroll-Reveal (IntersectionObserver)
	 * ------------------------------------------------------- */
	var revealObserver = new IntersectionObserver(
		function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('visible');
					revealObserver.unobserve(entry.target);
				}
			});
		},
		{ threshold: 0.1 }
	);

	document.querySelectorAll('.rv').forEach(function (el) {
		revealObserver.observe(el);
	});

	/* -------------------------------------------------------
	 * 2. Nav Scroll State
	 * ------------------------------------------------------- */
	var nav = document.querySelector('.lp-nav');
	if (nav) {
		window.addEventListener(
			'scroll',
			function () {
				nav.classList.toggle('sc', window.scrollY > 60);
			},
			{ passive: true }
		);
	}

	/* -------------------------------------------------------
	 * 3. FAQ Accordion
	 * ------------------------------------------------------- */
	document.querySelectorAll('.lp-faq__question').forEach(function (question) {
		question.addEventListener('click', function () {
			var item = question.parentElement;
			// Close all other items
			document.querySelectorAll('.lp-faq__item').forEach(function (other) {
				if (other !== item) {
					other.classList.remove('open');
				}
			});
			item.classList.toggle('open');
		});

		// Keyboard accessibility
		question.addEventListener('keydown', function (e) {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				question.click();
			}
		});
	});

	/* -------------------------------------------------------
	 * 4. Countdown Timer
	 *
	 * Reads deadline from [data-countdown-end] attribute on
	 * .lp-countdown element, or falls back to 72 hours from
	 * first page load (persisted in sessionStorage).
	 * ------------------------------------------------------- */
	var countdownEl = document.querySelector('.lp-countdown');

	if (countdownEl) {
		var endAttr = countdownEl.getAttribute('data-countdown-end');
		var endTime;

		if (endAttr) {
			endTime = new Date(endAttr).getTime();
		} else {
			// Fallback: 72 hours from first visit (persisted per session)
			var stored = sessionStorage.getItem('skyyrose_countdown_end');
			if (stored) {
				endTime = parseInt(stored, 10);
			} else {
				endTime = Date.now() + 72 * 3600 * 1000;
				sessionStorage.setItem('skyyrose_countdown_end', endTime.toString());
			}
		}

		function updateCountdown() {
			var remaining = Math.max(0, endTime - Date.now());

			var days = Math.floor(remaining / 86400000);
			var hours = Math.floor((remaining % 86400000) / 3600000);
			var minutes = Math.floor((remaining % 3600000) / 60000);
			var seconds = Math.floor((remaining % 60000) / 1000);

			function pad(n) {
				return String(n).padStart(2, '0');
			}

			var dayEls = countdownEl.querySelectorAll('.cd-d');
			var hourEls = countdownEl.querySelectorAll('.cd-h');
			var minEls = countdownEl.querySelectorAll('.cd-m');
			var secEls = countdownEl.querySelectorAll('.cd-s');

			dayEls.forEach(function (el) { el.textContent = pad(days); });
			hourEls.forEach(function (el) { el.textContent = pad(hours); });
			minEls.forEach(function (el) { el.textContent = pad(minutes); });
			secEls.forEach(function (el) { el.textContent = pad(seconds); });

			if (remaining > 0) {
				requestAnimationFrame(updateCountdown);
			}
		}

		updateCountdown();
	}

	/* -------------------------------------------------------
	 * 5. Parallax Break Images
	 * ------------------------------------------------------- */
	document.querySelectorAll('.lp-parallax img').forEach(function (img) {
		function onScroll() {
			var rect = img.parentElement.getBoundingClientRect();
			var offset = -rect.top * 0.3;
			img.style.transform = 'translateY(' + offset + 'px)';
		}

		window.addEventListener('scroll', onScroll, { passive: true });
	});

	/* -------------------------------------------------------
	 * 6. Newsletter Form (AJAX)
	 *
	 * Posts to admin-ajax.php using the existing
	 * skyyrose_ajax_newsletter_subscribe handler.
	 * ------------------------------------------------------- */
	var newsletterForm = document.querySelector('.lp-email-capture__form');

	if (newsletterForm) {
		newsletterForm.addEventListener('submit', function (e) {
			e.preventDefault();

			var emailInput = newsletterForm.querySelector('.lp-email-capture__input');
			var submitBtn = newsletterForm.querySelector('.lp-email-capture__btn');
			var messageEl = newsletterForm.querySelector('.lp-email-capture__message');
			var email = emailInput ? emailInput.value.trim() : '';

			if (!email) return;

			// Disable button during request
			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.textContent = '...';
			}

			var formData = new FormData();
			formData.append('action', 'skyyrose_newsletter_subscribe');
			formData.append('email', email);

			// Nonce from wp_localize_script
			if (typeof skyyRoseData !== 'undefined' && skyyRoseData.nonce) {
				formData.append('skyyrose_newsletter_nonce', skyyRoseData.nonce);
			}

			var ajaxUrl =
				typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl
					? skyyRoseData.ajaxUrl
					: '/index.php?rest_route=/';

			fetch(ajaxUrl, {
				method: 'POST',
				body: formData,
				credentials: 'same-origin',
			})
				.then(function (response) {
					return response.json();
				})
				.then(function (data) {
					if (messageEl) {
						messageEl.textContent = data.success
							? 'Welcome to the inner circle.'
							: (data.data && data.data.message) || 'Something went wrong.';
						messageEl.classList.add('visible');
					}
					if (data.success && emailInput) {
						emailInput.value = '';
					}
				})
				.catch(function () {
					if (messageEl) {
						messageEl.textContent = 'Network error. Please try again.';
						messageEl.classList.add('visible');
					}
				})
				.finally(function () {
					if (submitBtn) {
						submitBtn.disabled = false;
						submitBtn.textContent = 'Join';
					}
				});
		});
	}
})();
