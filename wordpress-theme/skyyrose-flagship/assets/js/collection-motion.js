/**
 * Collection Motion Identity — JS-driven pieces
 *
 * Companion to collection-motion.css. Per-collection, all self-gating:
 *   black-rose   — Tilt & Glare on lookbook figures (fine pointer only).
 *   love-hurts   — Interactive Ink Drop on the hero (tap/click).
 *   kids-capsule — bouncing accent field (gravity + damped restitution)
 *                  and confetti burst on WooCommerce added_to_cart.
 *
 * LCP doctrine (page.php Wave 5/7): nothing here hides content or runs
 * ahead of first paint — the script is deferred, listeners are cheap, and
 * the physics loop boots on window load. Reduced motion disables every
 * effect (checked at init AND re-checked live via matchMedia change).
 *
 * @package SkyyRose
 * @since   1.13.0
 */
(function () {
	'use strict';

	var page = document.querySelector('.col-page');
	if (!page) return;

	var collection = page.getAttribute('data-collection') || '';
	var reduceMq = window.matchMedia('(prefers-reduced-motion: reduce)');
	var fineMq = window.matchMedia('(hover: hover) and (pointer: fine)');

	function onReduceChange(handler) {
		reduceMq.addEventListener('change', handler);
	}

	/* ── Black Rose: Tilt & Glare on lookbook figures ─────────────────── */
	function initTiltGlare() {
		if (!fineMq.matches) return;

		var figures = document.querySelectorAll('.col-lookbook__figure');
		if (!figures.length) return;

		Array.prototype.forEach.call(figures, function (fig) {
			var glare = document.createElement('span');
			glare.className = 'col-tilt-glare';
			glare.setAttribute('aria-hidden', 'true');
			fig.appendChild(glare);

			var raf = null;
			var MAX_DEG = 5;

			fig.addEventListener('pointerenter', function () {
				if (reduceMq.matches) return;
				fig.classList.add('is-tilting');
			});

			fig.addEventListener('pointermove', function (e) {
				if (reduceMq.matches || raf) return;
				raf = requestAnimationFrame(function () {
					raf = null;
					var rect = fig.getBoundingClientRect();
					var px = (e.clientX - rect.left) / rect.width;   // 0..1
					var py = (e.clientY - rect.top) / rect.height;  // 0..1
					fig.style.setProperty('--tilt-ry', ((px - 0.5) * 2 * MAX_DEG).toFixed(2) + 'deg');
					fig.style.setProperty('--tilt-rx', ((0.5 - py) * 2 * MAX_DEG).toFixed(2) + 'deg');
					fig.style.setProperty('--glare-x', (px * 100).toFixed(1) + '%');
					fig.style.setProperty('--glare-y', (py * 100).toFixed(1) + '%');
				});
			});

			fig.addEventListener('pointerleave', function () {
				fig.classList.remove('is-tilting');
				fig.style.setProperty('--tilt-rx', '0deg');
				fig.style.setProperty('--tilt-ry', '0deg');
			});
		});
	}

	/* ── Love Hurts: Interactive Ink Drop on the hero ─────────────────── */
	function initInkDrops() {
		var hero = document.querySelector('.col-hero');
		if (!hero) return;

		var layer = document.createElement('div');
		layer.className = 'lh-ink-layer';
		layer.setAttribute('aria-hidden', 'true');
		hero.appendChild(layer);

		var MAX_DROPS = 6;

		hero.addEventListener('pointerdown', function (e) {
			if (reduceMq.matches) return;
			if (layer.childElementCount >= MAX_DROPS) return;

			var rect = hero.getBoundingClientRect();
			var size = 90 + Math.random() * 140;
			var drop = document.createElement('span');
			drop.className = 'lh-ink-drop';
			drop.style.width = size + 'px';
			drop.style.height = size + 'px';
			drop.style.left = (e.clientX - rect.left - size / 2) + 'px';
			drop.style.top = (e.clientY - rect.top - size / 2) + 'px';
			drop.addEventListener('animationend', function () { drop.remove(); });
			layer.appendChild(drop);
		}, { passive: true });
	}

	/* ── Kids Capsule: bouncing accent field (hero) ───────────────────── */
	function initKidsBounce() {
		if (reduceMq.matches) return;

		var hero = document.querySelector('.col-hero');
		if (!hero) return;

		var field = document.createElement('div');
		field.className = 'kc-bounce-field';
		field.setAttribute('aria-hidden', 'true');
		hero.appendChild(field);

		var count = fineMq.matches ? 5 : 3; // touch cap (mobile fallback)
		var GRAVITY = 900;      // px/s²
		var RESTITUTION = 0.68; // energy kept per floor bounce
		var orbs = [];
		var running = false;
		var raf = null;
		var lastTs = 0;

		for (var i = 0; i < count; i++) {
			var el = document.createElement('span');
			el.className = 'kc-bounce' + (i % 3 === 2 ? ' kc-bounce--gold' : '');
			var size = 14 + Math.random() * 22;
			el.style.width = size + 'px';
			el.style.height = size + 'px';
			field.appendChild(el);
			orbs.push({
				el: el,
				size: size,
				x: Math.random() * 80 + 5,        // % seed, converted on first frame
				y: Math.random() * 40,
				vx: (Math.random() - 0.5) * 60,   // px/s
				vy: Math.random() * 40,
				restAt: 0                          // timestamp to relaunch after settling
			});
		}

		// Convert % seeds to px once the field has layout, and place each orb
		// immediately so nothing sits untransformed at the field origin while
		// the loop waits on the IntersectionObserver.
		function seed() {
			var w = field.clientWidth;
			var h = field.clientHeight;
			orbs.forEach(function (o) {
				o.x = (o.x / 100) * w;
				o.y = (o.y / 100) * h;
				o.el.style.transform = 'translate3d(' + o.x.toFixed(1) + 'px,' + o.y.toFixed(1) + 'px,0)';
			});
		}

		function step(ts) {
			raf = null;
			if (!running) return;

			var dt = lastTs ? Math.min((ts - lastTs) / 1000, 0.05) : 0.016;
			lastTs = ts;

			var w = field.clientWidth;
			var h = field.clientHeight;

			orbs.forEach(function (o) {
				var floor = h - o.size;

				if (o.restAt) {
					// Settled — relaunch when its pause expires.
					if (ts >= o.restAt) {
						o.restAt = 0;
						o.vy = -(280 + Math.random() * 240);
						o.vx = (Math.random() - 0.5) * 120;
					}
				} else {
					o.vy += GRAVITY * dt;
					o.x += o.vx * dt;
					o.y += o.vy * dt;

					if (o.y >= floor) {
						o.y = floor;
						o.vy = -o.vy * RESTITUTION;
						if (Math.abs(o.vy) < 60) {
							o.vy = 0;
							o.restAt = ts + 1200 + Math.random() * 2200;
						}
					}
					if (o.x <= 0) { o.x = 0; o.vx = Math.abs(o.vx); }
					if (o.x >= w - o.size) { o.x = w - o.size; o.vx = -Math.abs(o.vx); }
				}

				o.el.style.transform = 'translate3d(' + o.x.toFixed(1) + 'px,' + o.y.toFixed(1) + 'px,0)';
			});

			raf = requestAnimationFrame(step);
		}

		function start() {
			if (running || reduceMq.matches) return;
			running = true;
			lastTs = 0;
			raf = requestAnimationFrame(step);
		}

		function stop() {
			running = false;
			if (raf) { cancelAnimationFrame(raf); raf = null; }
		}

		seed();

		// Run only while the hero is on screen and the tab is visible.
		var heroInView = true;
		if ('IntersectionObserver' in window) {
			heroInView = false;
			new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					heroInView = entry.isIntersecting;
					if (heroInView) { start(); } else { stop(); }
				});
			}).observe(hero);
		} else {
			start();
		}

		document.addEventListener('visibilitychange', function () {
			if (document.hidden) { stop(); } else if (heroInView) { start(); }
		});

		onReduceChange(function () {
			if (reduceMq.matches) { stop(); } // CSS hides the field too.
		});
	}

	/* ── Kids Capsule: confetti on add-to-cart ────────────────────────── */
	function initKidsConfetti() {
		// Quick-add flows (product-card-holo.js, wc-add-to-cart) announce via
		// the jQuery added_to_cart body event; no jQuery = no AJAX add = no-op.
		if (!window.jQuery) return;

		var COLOR_CLASSES = ['', ' kc-confetti--gold', ' kc-confetti--white'];
		var layer = null;

		function burst(originEl) {
			if (!layer) {
				layer = document.createElement('div');
				layer.className = 'kc-confetti-layer';
				layer.setAttribute('aria-hidden', 'true');
				document.body.appendChild(layer);
			}
			if (layer.childElementCount > 80) return; // runaway guard

			var ox = window.innerWidth / 2;
			var oy = window.innerHeight / 3;
			if (originEl && originEl.getBoundingClientRect) {
				var rect = originEl.getBoundingClientRect();
				if (rect.width || rect.height) {
					ox = rect.left + rect.width / 2;
					oy = rect.top + rect.height / 2;
				}
			}

			var n = fineMq.matches ? 20 : 12; // touch cap (mobile fallback)
			for (var i = 0; i < n; i++) {
				var piece = document.createElement('span');
				piece.className = 'kc-confetti' + COLOR_CLASSES[i % COLOR_CLASSES.length];
				piece.style.setProperty('--kc-x0', ox.toFixed(0) + 'px');
				piece.style.setProperty('--kc-y0', oy.toFixed(0) + 'px');
				piece.style.setProperty('--kc-dx', ((Math.random() - 0.5) * 280).toFixed(0) + 'px');
				piece.style.setProperty('--kc-dy', (220 + Math.random() * 220).toFixed(0) + 'px');
				piece.style.setProperty('--kc-rot', (1.5 + Math.random() * 1.5).toFixed(2) + 'turn');
				piece.style.setProperty('--kc-dur', (1.2 + Math.random() * 0.7).toFixed(2) + 's');
				piece.style.setProperty('--kc-delay', (Math.random() * 0.15).toFixed(2) + 's');
				piece.addEventListener('animationend', function (e) { e.target.remove(); });
				layer.appendChild(piece);
			}
		}

		window.jQuery(document.body).on('added_to_cart', function () {
			if (reduceMq.matches) return;
			// added_to_cart signature: (event, fragments, cart_hash, $button) —
			// only the button matters here, so skip naming the unused slots.
			var $button = arguments[3];
			burst($button && $button.length ? $button.get(0) : null);
		});
	}

	/* ── Film spine: scroll scrub (all collections) ───────────────────── */
	/* Progress bar scaleX + media drift + beat cross-fade, all driven off
	 * the track's bounding rect on a passive rAF-throttled scroll listener.
	 * The video element is untouched — currentTime is NEVER seeked (decode
	 * jank); collection-pages.js keeps owning play/pause. Reduced motion:
	 * the listener no-ops and collection-motion.css renders the static
	 * non-sticky fallback. */
	function initFilmSpine() {
		var track = document.querySelector('[data-film-scrub]');
		if (!track) return;

		var media = track.querySelector('.col-film__media');
		var bar = track.querySelector('.col-film__progress');
		var beats = track.querySelectorAll('[data-film-beat]');
		var ticking = false;

		function update() {
			ticking = false;
			var rect = track.getBoundingClientRect();
			var total = rect.height - window.innerHeight;
			if (total <= 0) return;
			var t = Math.min(1, Math.max(0, -rect.top / total));

			if (bar) bar.style.transform = 'scaleX(' + t.toFixed(4) + ')';
			if (media) media.style.transform = 'scale(' + (1 + t * 0.12).toFixed(4) + ') translateY(' + (t * -2.5).toFixed(2) + '%)';
			if (beats.length) {
				var idx = Math.min(beats.length - 1, Math.floor(t * beats.length));
				for (var i = 0; i < beats.length; i++) {
					beats[i].classList.toggle('is-on', i === idx);
				}
			}
		}

		window.addEventListener('scroll', function () {
			if (reduceMq.matches || ticking) return;
			ticking = true;
			requestAnimationFrame(update);
		}, { passive: true });

		if (!reduceMq.matches) update();

		// Live flip to reduced motion: clear the inline drift so the CSS
		// static fallback isn't fighting a stale transform.
		onReduceChange(function () {
			if (reduceMq.matches && media) { media.style.transform = ''; }
		});
	}

	/* ── Boot ─────────────────────────────────────────────────────────── */
	function boot() {
		initFilmSpine();

		if ('black-rose' === collection) {
			initTiltGlare();
		} else if ('love-hurts' === collection) {
			initInkDrops();
		} else if ('kids-capsule' === collection) {
			initKidsConfetti();
			// Physics field waits for full load — decorative, never in the
			// FCP→LCP window.
			if ('complete' === document.readyState) {
				initKidsBounce();
			} else {
				window.addEventListener('load', initKidsBounce, { once: true });
			}
		}
	}

	if ('loading' === document.readyState) {
		document.addEventListener('DOMContentLoaded', boot, { once: true });
	} else {
		boot();
	}
})();
