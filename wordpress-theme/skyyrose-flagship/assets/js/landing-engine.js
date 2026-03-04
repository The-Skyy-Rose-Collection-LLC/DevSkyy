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
	 * 7. Social Proof Notification Toasts (FOMO Engine)
	 *
	 * Injects a toast element and cycles through simulated
	 * recent-order notifications every 20-35 seconds.
	 * Uses real product names from the collection.
	 * ------------------------------------------------------- */
	var lpPage = document.querySelector('.lp-page');
	var collection = lpPage ? lpPage.getAttribute('data-collection') : '';

	if (lpPage && collection) {
		// Collection-specific notifications
		var toastData = {
			'black-rose': [
				{ name: 'Sarah', city: 'Oakland', product: 'Hockey Jersey (Teal)' },
				{ name: 'Marcus', city: 'Atlanta', product: 'Football Jersey (Red #80)' },
				{ name: 'Deja', city: 'Chicago', product: 'Basketball Jersey' },
				{ name: 'Tyler', city: 'Houston', product: 'Football Jersey (White #32)' },
				{ name: 'Keisha', city: 'Brooklyn', product: 'Hoodie' },
			],
			'love-hurts': [
				{ name: 'Aaliyah', city: 'Chicago', product: 'The Fannie Pack' },
				{ name: 'Kevin', city: 'Houston', product: 'Varsity Jacket' },
				{ name: 'Priya', city: 'San Jose', product: 'Bomber Jacket' },
				{ name: 'Andre', city: 'Oakland', product: 'The Fannie Pack' },
				{ name: 'Monica', city: 'Dallas', product: 'Hoodie' },
			],
			'signature': [
				{ name: 'Chris', city: 'San Francisco', product: 'Windbreaker Set' },
				{ name: 'Jordan', city: 'LA', product: 'Collection Shorts' },
				{ name: 'Priya', city: 'Brooklyn', product: 'Beanie (Black)' },
				{ name: 'Andre', city: 'Oakland', product: 'Beanie (Forest Green)' },
				{ name: 'Lisa', city: 'Portland', product: 'Collection Shorts' },
			],
		};

		var notifications = toastData[collection] || [];

		if (notifications.length > 0) {
			// Create toast element
			var toast = document.createElement('div');
			toast.className = 'lp-toast';
			toast.setAttribute('role', 'status');
			toast.setAttribute('aria-live', 'polite');
			toast.innerHTML =
				'<span class="lp-toast__icon">\u2714</span>' +
				'<div class="lp-toast__body">' +
				'<div class="lp-toast__text"></div>' +
				'<div class="lp-toast__time"></div>' +
				'</div>' +
				'<button class="lp-toast__close" aria-label="Dismiss notification">\u00D7</button>';
			document.body.appendChild(toast);

			var toastText = toast.querySelector('.lp-toast__text');
			var toastTime = toast.querySelector('.lp-toast__time');
			var closeBtn = toast.querySelector('.lp-toast__close');
			var toastIndex = 0;
			var toastTimer = null;
			var hideTimer = null;

			function showToast() {
				var item = notifications[toastIndex % notifications.length];
				var minutes = Math.floor(Math.random() * 18) + 2; // 2-20 minutes ago
				toastText.innerHTML =
					'<strong>' + item.name + '</strong> from ' + item.city +
					' just ordered the <strong>' + item.product + '</strong>';
				toastTime.textContent = minutes + ' min ago';
				toast.classList.add('visible');

				hideTimer = setTimeout(function () {
					toast.classList.remove('visible');
				}, 5000);

				toastIndex++;
				toastTimer = setTimeout(showToast, (Math.random() * 15000) + 20000); // 20-35s
			}

			closeBtn.addEventListener('click', function () {
				toast.classList.remove('visible');
				if (hideTimer) clearTimeout(hideTimer);
			});

			// Start after 8 seconds on page
			setTimeout(showToast, 8000);
		}
	}

	/* -------------------------------------------------------
	 * 8. Sticky Mobile CTA Bar
	 *
	 * Appears on mobile when user scrolls past the hero section.
	 * Hides when near the bottom (email capture) to avoid clutter.
	 * ------------------------------------------------------- */
	if (lpPage && collection) {
		var collectionNames = {
			'black-rose': 'BLACK ROSE',
			'love-hurts': 'LOVE HURTS',
			'signature': 'SIGNATURE',
		};

		var stickyBar = document.createElement('div');
		stickyBar.className = 'lp-sticky-cta';
		stickyBar.setAttribute('role', 'complementary');
		stickyBar.setAttribute('aria-label', 'Quick shop');
		stickyBar.innerHTML =
			'<span class="lp-sticky-cta__label">' +
			(collectionNames[collection] || 'SKYYROSE') +
			'</span>' +
			'<a href="#products" class="lp-sticky-cta__btn">Shop Now</a>';
		document.body.appendChild(stickyBar);

		var hero = document.querySelector('.lp-hero');
		var emailCapture = document.querySelector('.lp-email-capture');

		if (hero) {
			window.addEventListener('scroll', function () {
				var heroBottom = hero.getBoundingClientRect().bottom;
				var nearBottom = emailCapture
					? emailCapture.getBoundingClientRect().top < window.innerHeight
					: false;
				stickyBar.classList.toggle('visible', heroBottom < 0 && !nearBottom);
			}, { passive: true });
		}

		// Smooth scroll to products section
		stickyBar.querySelector('.lp-sticky-cta__btn').addEventListener('click', function (e) {
			var target = document.querySelector('#products');
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	}

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
