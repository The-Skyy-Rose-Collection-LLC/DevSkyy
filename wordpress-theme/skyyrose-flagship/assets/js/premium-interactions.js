/**
 * SkyyRose Premium Interactions Engine
 *
 * Vanilla JS — zero dependencies. Drives the animations-premium.css system.
 * Features: split-text, parallax, stagger grids, magnetic cursor, scroll-fade,
 * ambient glow, page transitions. All gated behind feature detection.
 *
 * @package SkyyRose_Flagship
 * @since   6.2.0
 */
(function () {
	'use strict';

	/* ── Feature Detection ─────────────────────────────────────────── */
	var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var hasHover = window.matchMedia('(hover: hover)').matches;
	var rAF = window.requestAnimationFrame || function (cb) { setTimeout(cb, 16); };

	if (prefersReduced) {
		document.querySelectorAll('.rv-clip-up,.rv-clip-left,.rv-clip-right,.rv-clip-diagonal,.rv-blur,.rv-blur-down,.stagger-grid,.rv-split-char,.rv-split-word,.rv-split-line,.col-reveal').forEach(function (el) {
			el.classList.add('is-visible');
		});
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
			if (ch === ' ') {
				el.appendChild(document.createTextNode(' '));
				continue;
			}
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
	   2. INTERSECTION OBSERVER — Unified reveal trigger
	   ══════════════════════════════════════════════════════════════════ */

	var revealSelectors = [
		'.rv-clip-up', '.rv-clip-left', '.rv-clip-right', '.rv-clip-diagonal',
		'.rv-blur', '.rv-blur-down',
		'.stagger-grid',
		'.rv-split-char', '.rv-split-word', '.rv-split-line',
		'.col-reveal'
	].join(',');

	var revealEls = document.querySelectorAll(revealSelectors);

	if (revealEls.length && 'IntersectionObserver' in window) {
		var revealObs = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('is-visible');
					revealObs.unobserve(entry.target);
				}
			});
		}, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });

		revealEls.forEach(function (el) { revealObs.observe(el); });
	} else {
		revealEls.forEach(function (el) { el.classList.add('is-visible'); });
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
	   ══════════════════════════════════════════════════════════════════ */

	var parallaxEls = document.querySelectorAll('.parallax-slow,.parallax-medium,.parallax-fast,.parallax-ken-burns');
	var scrollFadeEls = document.querySelectorAll('[data-scroll-fade]');
	var scrollTicking = false;

	function onScroll() {
		if (scrollTicking) return;
		scrollTicking = true;
		rAF(function () {
			var viewH = window.innerHeight;

			parallaxEls.forEach(function (el) {
				var rect = el.getBoundingClientRect();
				var offset = (rect.top + rect.height / 2 - viewH / 2);
				el.style.setProperty('--parallax-offset', offset + 'px');
			});

			scrollFadeEls.forEach(function (el) {
				var rect = el.getBoundingClientRect();
				var elH = rect.height || viewH;
				var progress = Math.max(0, Math.min(1, -rect.top / (elH * 0.6)));
				el.style.setProperty('--scroll-progress', progress);
			});

			scrollTicking = false;
		});
	}

	if ((parallaxEls.length || scrollFadeEls.length) && !prefersReduced) {
		window.addEventListener('scroll', onScroll, { passive: true });
		onScroll();
	}

	/* ══════════════════════════════════════════════════════════════════
	   5. MAGNETIC CURSOR (hover devices only)
	   ══════════════════════════════════════════════════════════════════ */

	if (hasHover) {
		document.querySelectorAll('.magnetic').forEach(function (el) {
			el.addEventListener('mousemove', function (e) {
				var rect = el.getBoundingClientRect();
				var mx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
				var my = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
				mx = Math.max(-1, Math.min(1, mx));
				my = Math.max(-1, Math.min(1, my));
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
				var x = ((e.clientX - rect.left) / rect.width * 100).toFixed(1);
				var y = ((e.clientY - rect.top) / rect.height * 100).toFixed(1);
				el.style.setProperty('--glow-x', x + '%');
				el.style.setProperty('--glow-y', y + '%');
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

		/* Reduced-motion: skip exit animation, navigate immediately */
		if (prefersReduced) {
			window.location.href = href;
			return;
		}

		e.preventDefault();
		document.body.classList.remove('page-enter');
		document.body.classList.add('page-exit');

		setTimeout(function () {
			window.location.href = href;
		}, 300);
	});

})();
