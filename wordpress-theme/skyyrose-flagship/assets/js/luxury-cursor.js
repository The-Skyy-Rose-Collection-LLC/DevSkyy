/**
 * Luxury Cursor — Dot Follower + Animated Cursor States
 *
 * Subtle custom cursor for desktop: small dot + larger ring outline, plus
 * contextual states — interactive-hover scale (driven by --cursor-*-scale
 * custom properties so the class-based CSS survives the per-frame inline
 * transform), pressed state, and a labeled state: any element carrying
 * data-cursor-label (PHP-translated markup, e.g. the holo card image link)
 * expands the ring into a labeled lens.
 *
 * Disabled on touch devices, mobile (<768px), and prefers-reduced-motion.
 *
 * @package SkyyRose
 * @since   5.3.0
 */
(function () {
	'use strict';

	if (window.matchMedia('(hover: none)').matches) return;
	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
	if (window.innerWidth < 768) return;

	var mx = 0, my = 0, rx = 0, ry = 0;
	var LERP = 0.15;
	var root = document.documentElement;

	var dot = document.createElement('div');
	dot.className = 'cursor-dot';
	dot.setAttribute('aria-hidden', 'true');

	var ring = document.createElement('div');
	ring.className = 'cursor-ring';
	ring.setAttribute('aria-hidden', 'true');

	var label = document.createElement('span');
	label.className = 'cursor-label';
	ring.appendChild(label);

	document.body.appendChild(dot);
	document.body.appendChild(ring);
	root.classList.add('cursor-active');

	var HOVER_SEL = 'a, button, [role="button"], input, select, textarea, .holo';
	var LABEL_SEL = '[data-cursor-label]';

	// scale() references CSS custom properties so stylesheet state classes
	// (.cursor-hover / .cursor-down) keep working: a bare stylesheet
	// transform would lose to these per-frame inline writes.
	function dotTransform() {
		return 'translate(' + mx + 'px,' + my + 'px) translate(-50%,-50%) scale(var(--cursor-dot-scale, 1))';
	}

	function onMove(e) {
		mx = e.clientX;
		my = e.clientY;
		dot.style.transform = dotTransform();
	}

	function tick() {
		rx += (mx - rx) * LERP;
		ry += (my - ry) * LERP;
		ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px) translate(-50%,-50%) scale(var(--cursor-ring-scale, 1))';
		requestAnimationFrame(tick);
	}

	function onOver(e) {
		if (!e.target || !e.target.closest) return;
		if (e.target.closest(HOVER_SEL)) {
			root.classList.add('cursor-hover');
		}
		var labeled = e.target.closest(LABEL_SEL);
		if (labeled) {
			label.textContent = labeled.getAttribute('data-cursor-label') || '';
			root.classList.add('cursor-labeled');
		}
	}

	function onOut(e) {
		if (!e.target || !e.target.closest) return;
		if (e.target.closest(HOVER_SEL)) {
			root.classList.remove('cursor-hover');
		}
		if (e.target.closest(LABEL_SEL)) {
			root.classList.remove('cursor-labeled');
		}
	}

	function onDown() { document.documentElement.classList.add('cursor-down'); }
	function onUp() { document.documentElement.classList.remove('cursor-down'); }

	document.addEventListener('mousemove', onMove, { passive: true });
	document.addEventListener('mouseover', onOver, { passive: true });
	document.addEventListener('mouseout', onOut, { passive: true });
	document.addEventListener('mousedown', onDown);
	document.addEventListener('mouseup', onUp);

	window.addEventListener('touchstart', function () {
		document.documentElement.classList.remove('cursor-active', 'cursor-hover', 'cursor-down');
		if (dot.parentNode) dot.parentNode.removeChild(dot);
		if (ring.parentNode) ring.parentNode.removeChild(ring);
		document.removeEventListener('mousemove', onMove);
		document.removeEventListener('mouseover', onOver);
		document.removeEventListener('mouseout', onOut);
		document.removeEventListener('mousedown', onDown);
		document.removeEventListener('mouseup', onUp);
	}, { once: true });

	requestAnimationFrame(tick);
})();
