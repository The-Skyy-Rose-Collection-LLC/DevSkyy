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
	 * reduced-motion users never trigger a video fetch — calling .play() is
	 * what starts the load. An IntersectionObserver defers that load until the
	 * film scrolls near view and pauses it off-screen (battery/bandwidth); a
	 * matchMedia change-listener stops playback if the user enables reduced
	 * motion after load. WCAG 2.2.2: the pause/play toggle (APG play/pause
	 * pattern — a swapping label, no aria-pressed) is revealed only once
	 * motion is confirmed allowed. */
	(function () {
		var reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
		var sections = document.querySelectorAll('.col-film');
		if (!sections.length) return;

		var films = [];
		for (var f = 0; f < sections.length; f++) {
			(function (section) {
				var video = section.querySelector('.col-film__video');
				var toggle = section.querySelector('.col-film__toggle');
				if (!video || !toggle) return;

				var userPaused = false; // true only after an explicit toggle-pause

				var setToggleState = function (isPlaying) {
					toggle.hidden = false;
					toggle.setAttribute('aria-label', isPlaying ? 'Pause background video' : 'Play background video');
					toggle.textContent = isPlaying ? '❚❚' : '▶';
				};

				var play = function () {
					if (reduceMq.matches || userPaused) return;
					var p = video.play();
					if (p && typeof p.then === 'function') {
						p.then(function () { setToggleState(true); }, function () { setToggleState(false); });
					} else {
						setToggleState(true);
					}
				};

				toggle.addEventListener('click', function () {
					if (video.paused) {
						userPaused = false;
						play();
					} else {
						userPaused = true;
						video.pause();
						setToggleState(false);
					}
				});

				films.push({ section: section, video: video, play: play });
			})(sections[f]);
		}

		if (!films.length) return;

		var findFilm = function (el) {
			for (var i = 0; i < films.length; i++) {
				if (films[i].section === el) return films[i];
			}
			return null;
		};

		// Play near-view, pause off-screen. No IO support → play immediately.
		if ('IntersectionObserver' in window) {
			var io = new IntersectionObserver(function (entries) {
				for (var i = 0; i < entries.length; i++) {
					var film = findFilm(entries[i].target);
					if (!film) continue;
					if (entries[i].isIntersecting) {
						film.play();
					} else if (!film.video.paused) {
						film.video.pause();
					}
				}
			}, { rootMargin: '200px 0px' });
			for (var k = 0; k < films.length; k++) io.observe(films[k].section);
		} else {
			for (var m = 0; m < films.length; m++) films[m].play();
		}

		// Stop playback if the user turns on reduced motion after load.
		var onReduceChange = function () {
			if (!reduceMq.matches) return;
			for (var n = 0; n < films.length; n++) {
				films[n].video.pause();
				var t = films[n].section.querySelector('.col-film__toggle');
				if (t) { t.hidden = true; }
			}
		};
		if (reduceMq.addEventListener) {
			reduceMq.addEventListener('change', onReduceChange);
		} else if (reduceMq.addListener) {
			reduceMq.addListener(onReduceChange);
		}
	})();
})();
