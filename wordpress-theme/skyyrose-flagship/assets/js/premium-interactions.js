/**
 * SkyyRose Premium Interactions Engine
 *
 * Motion One-enhanced. inView() replaces IntersectionObserver reveals;
 * scroll(animate()) drives scroll-fade opacity directly.
 * Parallax retains CSS custom property approach (multipliers are CSS-driven).
 * Falls back gracefully if Motion One CDN fails to load.
 *
 * @package SkyyRose
 * @since   6.3.0
 */
(function () {
	'use strict';

	/* ── Feature Detection ─────────────────────────────────────────── */
	var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var hasHover       = window.matchMedia('(hover: hover)').matches;
	var rAF            = window.requestAnimationFrame || function (cb) { setTimeout(cb, 16); };

	/* ── Motion One API (graceful fallback if CDN fails) ───────────── */
	var M          = window.Motion || {};
	var mInView    = typeof M.inView    === 'function' ? M.inView    : null;
	var mAnimate   = typeof M.animate   === 'function' ? M.animate   : null;
	var mScroll    = typeof M.scroll    === 'function' ? M.scroll    : null;

	/* ── Unified reveal selector (single source of truth) ──────────── */
	var revealSelectors =
		'.rv-clip-up,.rv-clip-left,.rv-clip-right,.rv-clip-diagonal,' +
		'.rv-blur,.rv-blur-down,.stagger-grid,' +
		'.rv-split-char,.rv-split-word,.rv-split-line,' +
		'.col-reveal,.lp-rv,.rv';

	if (prefersReduced) {
		document.querySelectorAll(revealSelectors)
			.forEach(function (el) { el.classList.add('is-visible'); });
		return;
	}

	/* ══════════════════════════════════════════════════════════════════
	   1. SPLIT-TEXT ENGINE
	   Wraps text into spans for per-character/word/line animation.
	   Uses only createElement + textContent (no innerHTML).
	   Preserves aria-label on parent, sets aria-hidden on spans.
	   ══════════════════════════════════════════════════════════════════ */

	function clearChildren(el) {
		while (el.firstChild) { el.removeChild(el.firstChild); }
	}

	function splitChars(el) {
		var text = el.textContent.trim();
		if (!text) return;
		el.setAttribute('aria-label', text);
		clearChildren(el);
		var idx = 0;
		for (var i = 0; i < text.length; i++) {
			var ch = text[i];
			if (ch === ' ') { el.appendChild(document.createTextNode(' ')); continue; }
			var span = document.createElement('span');
			span.className = 'sr-char';
			span.textContent = ch;
			span.style.setProperty('--char-index', idx);
			span.setAttribute('aria-hidden', 'true');
			el.appendChild(span);
			idx++;
		}
	}

	function splitWords(el) {
		var text = el.textContent.trim();
		if (!text) return;
		el.setAttribute('aria-label', text);
		var words = text.split(/\s+/);
		clearChildren(el);
		words.forEach(function (word, i) {
			var span = document.createElement('span');
			span.className = 'sr-word';
			span.textContent = word;
			span.style.setProperty('--word-index', i);
			span.setAttribute('aria-hidden', 'true');
			el.appendChild(span);
		});
	}

	function splitLines(el) {
		var text = el.textContent.trim();
		if (!text) return;
		el.setAttribute('aria-label', text);
		var lines = text.split('\n');
		clearChildren(el);
		lines.forEach(function (line, i) {
			var trimmed = line.trim();
			if (!trimmed) return;
			var span = document.createElement('span');
			span.className = 'sr-line';
			span.textContent = trimmed;
			span.style.setProperty('--line-index', i);
			span.setAttribute('aria-hidden', 'true');
			el.appendChild(span);
		});
	}

	document.querySelectorAll('.rv-split-char').forEach(splitChars);
	document.querySelectorAll('.rv-split-word').forEach(splitWords);
	document.querySelectorAll('.rv-split-line').forEach(splitLines);

	/* ══════════════════════════════════════════════════════════════════
	   1.5 ABOVE-FOLD IMMEDIATE REVEAL (S650 fix, 2026-05-24)
	   IO fires after first paint; elements already in viewport stay at
	   opacity:0 briefly. Force-show anything intersecting the viewport
	   at load so above-fold content never flashes empty for reduced-motion
	   users, in-app browsers, or slow JS engines.
	   ══════════════════════════════════════════════════════════════════ */
	rAF(function () {
		var vh = window.innerHeight || document.documentElement.clientHeight;
		document.querySelectorAll(revealSelectors).forEach(function (el) {
			var rect = el.getBoundingClientRect();
			if (rect.top < vh && rect.bottom > 0) {
				el.classList.add('is-visible');
			}
		});
	});

	/* ══════════════════════════════════════════════════════════════════
	   2. SCROLL REVEALS
	   Single observer for the entire theme. Subsumes the per-page observers
	   that previously lived in landing-pages.js and about.js (retired in U-1).
	   Motion One inView() when available; IntersectionObserver fallback.
	   Both paths add 'is-visible' — CSS in animations-premium.css and
	   per-feature stylesheets drive the actual transitions.
	   ══════════════════════════════════════════════════════════════════ */

	if (mInView) {
		mInView(revealSelectors, function (entry) {
			// Motion One v11 passes the IntersectionObserverEntry to the callback,
			// not the element (v10 passed the element). Dereference .target; the
			// `|| entry` keeps it safe if the lib is ever pinned back to v10.
			(entry.target || entry).classList.add('is-visible');
		}, { amount: 0.12, margin: '0px 0px -40px 0px' });
	} else {
		var revealEls = document.querySelectorAll(revealSelectors);
		if (revealEls.length && 'IntersectionObserver' in window) {
			var revealObs = new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						entry.target.classList.add('is-visible');
						revealObs.unobserve(entry.target);
					}
				});
			}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
			revealEls.forEach(function (el) { revealObs.observe(el); });
		} else {
			document.querySelectorAll(revealSelectors)
				.forEach(function (el) { el.classList.add('is-visible'); });
		}
	}

	/* ══════════════════════════════════════════════════════════════════
	   3. STAGGER INDEXER
	   ══════════════════════════════════════════════════════════════════ */

	document.querySelectorAll('.stagger-grid').forEach(function (grid) {
		var children = grid.children;
		for (var i = 0; i < children.length; i++) {
			children[i].style.setProperty('--stagger-index', i);
		}
	});

	/* ══════════════════════════════════════════════════════════════════
	   4. PARALLAX CONTROLLER + SCROLL-FADE
	   Parallax: rAF + CSS custom property (--parallax-offset) so the
	   CSS multipliers (--parallax-slow/medium/fast) stay in control.
	   Scroll-fade: Motion One scroll(animate()) drives opacity directly
	   when available; CSS var fallback otherwise.
	   ══════════════════════════════════════════════════════════════════ */

	var parallaxEls   = document.querySelectorAll('.parallax-slow,.parallax-medium,.parallax-fast,.parallax-ken-burns');
	var scrollFadeEls = document.querySelectorAll('[data-scroll-fade]');
	var scrollTicking = false;

	/* Parallax — always via rAF to preserve CSS multiplier system */
	if (parallaxEls.length) {
		function updateParallax() {
			if (scrollTicking) return;
			scrollTicking = true;
			rAF(function () {
				var viewH = window.innerHeight;
				parallaxEls.forEach(function (el) {
					var rect   = el.getBoundingClientRect();
					var offset = rect.top + rect.height / 2 - viewH / 2;
					el.style.setProperty('--parallax-offset', offset + 'px');
				});
				scrollTicking = false;
			});
		}
		window.addEventListener('scroll', updateParallax, { passive: true });
		updateParallax();
	}

	/* Scroll-fade — Motion One scroll(animate()) or CSS var fallback */
	if (scrollFadeEls.length) {
		if (mScroll && mAnimate) {
			scrollFadeEls.forEach(function (el) {
				mScroll(
					mAnimate(el, { opacity: [1, 0] }, { duration: 1 }),
					{ target: el, offset: ['start start', 'end start'] }
				);
			});
		} else {
			function updateScrollFade() {
				var viewH = window.innerHeight;
				scrollFadeEls.forEach(function (el) {
					var rect     = el.getBoundingClientRect();
					var elH      = rect.height || viewH;
					var progress = Math.max(0, Math.min(1, -rect.top / (elH * 0.6)));
					el.style.setProperty('--scroll-progress', progress);
				});
			}
			window.addEventListener('scroll', updateScrollFade, { passive: true });
			updateScrollFade();
		}
	}

	/* ══════════════════════════════════════════════════════════════════
	   5. MAGNETIC CURSOR (hover devices only)
	   ══════════════════════════════════════════════════════════════════ */

	if (hasHover) {
		document.querySelectorAll('.magnetic').forEach(function (el) {
			el.addEventListener('mousemove', function (e) {
				var rect = el.getBoundingClientRect();
				var mx   = Math.max(-1, Math.min(1, (e.clientX - rect.left - rect.width  / 2) / (rect.width  / 2)));
				var my   = Math.max(-1, Math.min(1, (e.clientY - rect.top  - rect.height / 2) / (rect.height / 2)));
				el.style.setProperty('--mag-x', mx.toFixed(3));
				el.style.setProperty('--mag-y', my.toFixed(3));
			});
			el.addEventListener('mouseleave', function () {
				el.style.setProperty('--mag-x', '0');
				el.style.setProperty('--mag-y', '0');
			});
		});
	}

	/* ══════════════════════════════════════════════════════════════════
	   6. AMBIENT GLOW — Cursor-tracked radial gradient
	   ══════════════════════════════════════════════════════════════════ */

	if (hasHover) {
		document.querySelectorAll('.ambient-glow').forEach(function (el) {
			el.addEventListener('mousemove', function (e) {
				var rect = el.getBoundingClientRect();
				el.style.setProperty('--glow-x', ((e.clientX - rect.left) / rect.width  * 100).toFixed(1) + '%');
				el.style.setProperty('--glow-y', ((e.clientY - rect.top)  / rect.height * 100).toFixed(1) + '%');
			});
		});
	}

	/* ══════════════════════════════════════════════════════════════════
	   7. PAGE TRANSITIONS
	   ══════════════════════════════════════════════════════════════════ */

	document.body.classList.add('page-enter');

	document.addEventListener('click', function (e) {
		var link = e.target.closest('a[href]');
		if (!link) return;

		var href = link.getAttribute('href');
		if (!href || href.charAt(0) === '#' || link.target === '_blank' || link.hasAttribute('download')) return;

		try {
			var url = new URL(href, window.location.origin);
			if (url.origin !== window.location.origin) return;
		} catch (err) { return; }

		if (prefersReduced) { window.location.href = href; return; }

		e.preventDefault();
		document.body.classList.remove('page-enter');
		document.body.classList.add('page-exit');
		setTimeout(function () { window.location.href = href; }, 300);
	});

	/* ══════════════════════════════════════════════════════════════════
	   8. SCROLL-PINNED NARRATIVE
	   Drives template-parts/pin-narrative.php. The tall .pin-narrative
	   section holds a sticky stage; scroll progress through the section
	   maps to the active beat index. Adds .is-pinned to switch the layout
	   from readable flow to the cross-fading sticky stage (CSS owns the
	   transitions). prefersReduced already returned above, so this never
	   runs for reduced-motion users — they keep the flow layout.
	   ══════════════════════════════════════════════════════════════════ */

	function setupPinNarrative(section) {
		var beats = section.querySelectorAll('.pin-beat');
		var dots  = section.querySelectorAll('.pin-narrative__dot');
		if (beats.length < 2) return;

		section.classList.add('is-pinned');

		var current = -1;
		function setActive(idx) {
			if (idx === current) return;
			current = idx;
			for (var b = 0; b < beats.length; b++) {
				beats[b].classList.toggle('is-active', b === idx);
			}
			for (var d = 0; d < dots.length; d++) {
				dots[d].classList.toggle('is-active', d === idx);
			}
		}
		setActive(0);

		var ticking = false;
		function onScroll() {
			if (ticking) return;
			ticking = true;
			rAF(function () {
				var rect  = section.getBoundingClientRect();
				var vh    = window.innerHeight;
				var total = section.offsetHeight - vh;
				if (total <= 0) { setActive(0); ticking = false; return; }
				var scrolled = Math.min(Math.max(-rect.top, 0), total);
				var progress = scrolled / total;
				var idx = Math.min(beats.length - 1, Math.floor(progress * beats.length));
				setActive(idx < 0 ? 0 : idx);
				ticking = false;
			});
		}
		window.addEventListener('scroll', onScroll, { passive: true });
		window.addEventListener('resize', onScroll, { passive: true });
		onScroll();
	}

	document.querySelectorAll('.pin-narrative').forEach(setupPinNarrative);

})();
