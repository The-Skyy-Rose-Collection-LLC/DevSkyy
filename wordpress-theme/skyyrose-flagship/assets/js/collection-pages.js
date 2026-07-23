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

	/* ── Collection film: reduced-motion gate + pause/play toggle ────── */
	/* Markup ships poster-first (no autoplay attribute, preload="none") so
	 * reduced-motion users never trigger a video fetch — calling .play()
	 * below is what actually starts the load. WCAG 2.2.2 requires a stop
	 * mechanism for auto-playing motion lasting over 5s, so the toggle is
	 * revealed only once motion is confirmed allowed. */
	if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
		var filmSections = document.querySelectorAll('.col-film');
		for (var f = 0; f < filmSections.length; f++) {
			(function (section) {
				var video = section.querySelector('.col-film__video');
				var toggle = section.querySelector('.col-film__toggle');
				if (!video || !toggle) return;

				var setToggleState = function (isPlaying) {
					toggle.hidden = false;
					toggle.setAttribute('aria-pressed', isPlaying ? 'false' : 'true');
					toggle.setAttribute('aria-label', isPlaying ? 'Pause background video' : 'Play background video');
					toggle.textContent = isPlaying ? '❚❚' : '▶';
				};

				var playAttempt = video.play();
				if (playAttempt && typeof playAttempt.then === 'function') {
					playAttempt.then(function () { setToggleState(true); }, function () { setToggleState(false); });
				} else {
					setToggleState(true);
				}

				toggle.addEventListener('click', function () {
					if (video.paused) {
						video.play();
						setToggleState(true);
					} else {
						video.pause();
						setToggleState(false);
					}
				});
			})(filmSections[f]);
		}
	}
})();
