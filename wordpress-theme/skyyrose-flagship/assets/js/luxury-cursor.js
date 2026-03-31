/**
 * Luxury Cursor — Dot Follower
 *
 * Subtle custom cursor for desktop: small dot + larger ring outline.
 * Disabled on touch devices, mobile (<768px), and prefers-reduced-motion.
 *
 * @package SkyyRose_Flagship
 * @since   5.3.0
 */
(function () {
	'use strict';

	if (window.matchMedia('(hover: none)').matches) return;
	if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
	if (window.innerWidth < 768) return;

	var mx = 0, my = 0, rx = 0, ry = 0;
	var LERP = 0.15;

	var dot = document.createElement('div');
	dot.className = 'cursor-dot';
	dot.setAttribute('aria-hidden', 'true');

	var ring = document.createElement('div');
	ring.className = 'cursor-ring';
	ring.setAttribute('aria-hidden', 'true');

	document.body.appendChild(dot);
	document.body.appendChild(ring);
	document.documentElement.classList.add('cursor-active');

	var HOVER_SEL = 'a, button, [role="button"], input, select, textarea, .holo';

	function onMove(e) {
		mx = e.clientX;
		my = e.clientY;
		dot.style.transform = 'translate(' + mx + 'px,' + my + 'px) translate(-50%,-50%)';
	}

	function tick() {
		rx += (mx - rx) * LERP;
		ry += (my - ry) * LERP;
		ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px) translate(-50%,-50%)';
		requestAnimationFrame(tick);
	}

	function onOver(e) {
		if (e.target && e.target.closest && e.target.closest(HOVER_SEL)) {
			document.documentElement.classList.add('cursor-hover');
		}
	}

	function onOut(e) {
		if (e.target && e.target.closest && e.target.closest(HOVER_SEL)) {
			document.documentElement.classList.remove('cursor-hover');
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
