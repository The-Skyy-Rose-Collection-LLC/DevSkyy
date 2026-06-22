/**
 * Collection Pages — Unified JS
 *
 * IntersectionObserver scroll-reveal + floating particle generator.
 * Replaces GSAP ScrollTrigger dependency for collection pages.
 *
 * @package SkyyRose
 * @since   6.1.0
 */
(function () {
	'use strict';

	/* Scroll reveal handled by premium-interactions.js (global) — no duplicate observer here. */

	/* ── Floating Particles ───────────────────────────────────────── */
	/* Guard is particles-only: .col-floating is not emitted on all collection
	 * pages, so particle generation is conditional but newsletter is not. */
	var container = document.querySelector('.col-floating');
	if (container) {
		var page = document.querySelector('.col-page');
		var collection = page ? page.getAttribute('data-collection') : '';
		var chars = { 'love-hurts': '♥', 'black-rose': '•', 'signature': '✦', 'kids-capsule': '✦' };
		var ch = chars[collection] || '✦';
		var count = collection === 'love-hurts' ? 12 : 6;

		for (var i = 0; i < count; i++) {
			var el = document.createElement('div');
			el.className = 'col-float-particle';
			el.textContent = ch;
			el.style.left = Math.random() * 100 + '%';
			el.style.animationDelay = Math.random() * 20 + 's';
			el.style.fontSize = (Math.random() * 0.8 + 0.8) + 'rem';
			container.appendChild(el);
		}
	}

	/* ── Newsletter form handler ──────────────────────────────────── */
	/* Runs on all collection pages regardless of .col-floating presence. */
	var form = document.querySelector('.col-newsletter__form');
	if (form) {
		form.addEventListener('submit', function (e) {
			e.preventDefault();
			var input = form.querySelector('.col-newsletter__input');
			var btn = form.querySelector('.col-newsletter__submit');
			if (!input || !input.value.trim()) return;

			var originalText = btn.textContent;
			btn.textContent = 'Joining...';
			btn.disabled = true;

			/* Klaviyo subscribe via AJAX if available, otherwise show confirmation */
			if (typeof skyyRoseNewsletter !== 'undefined' && skyyRoseNewsletter.ajaxUrl) {
				var xhr = new XMLHttpRequest();
				xhr.open('POST', skyyRoseNewsletter.ajaxUrl);
				xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
				xhr.onload = function () {
					btn.textContent = 'Welcome';
					input.value = '';
					setTimeout(function () { btn.textContent = originalText; btn.disabled = false; }, 3000);
				};
				xhr.onerror = function () {
					btn.textContent = originalText;
					btn.disabled = false;
				};
				xhr.send('action=skyyrose_newsletter_subscribe&email=' + encodeURIComponent(input.value) + '&skyyrose_newsletter_nonce=' + encodeURIComponent(skyyRoseNewsletter.nonce));
			} else {
				btn.textContent = 'Welcome';
				input.value = '';
				setTimeout(function () { btn.textContent = originalText; btn.disabled = false; }, 3000);
			}
		});
	}
})();
