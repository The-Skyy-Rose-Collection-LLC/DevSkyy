/**
 * Luxury Cursor — Rose gold ring, gold center dot, sparkle trail.
 * Desktop only (hover: hover). Skipped on touch devices.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

(function () {
	'use strict';

	// Skip on touch-primary devices.
	if (window.matchMedia('(hover: none)').matches) return;

	// Create cursor elements if they don't exist (handles cached HTML).
	function ensureElement(className) {
		var el = document.querySelector('.' + className);
		if (!el) {
			el = document.createElement('div');
			el.className = className;
			el.setAttribute('aria-hidden', 'true');
			document.body.appendChild(el);
		}
		return el;
	}

	var ring  = ensureElement('luxury-cursor-ring');
	var dot   = ensureElement('luxury-cursor-dot');
	var trail = ensureElement('luxury-cursor-trail');

	// Signal to CSS that the custom cursor is active.
	// Without this class, cursor:none won't apply (progressive enhancement).
	document.body.classList.add('luxury-cursor-active');

	var mouseX = 0;
	var mouseY = 0;
	var ringX = 0;
	var ringY = 0;
	var dotX = 0;
	var dotY = 0;
	var isHovering = false;

	/* --------------------------------------------------
	   Mouse Tracking
	   -------------------------------------------------- */

	document.addEventListener('mousemove', function (e) {
		mouseX = e.clientX;
		mouseY = e.clientY;
	}, { passive: true });

	/* --------------------------------------------------
	   Animation Loop — Smooth Follow
	   -------------------------------------------------- */

	function animate() {
		// Ring follows with lag.
		ringX += (mouseX - ringX) * 0.12;
		ringY += (mouseY - ringY) * 0.12;
		ring.style.transform = 'translate(' + ringX + 'px, ' + ringY + 'px) translate(-50%, -50%)' +
			(isHovering ? ' scale(1.5)' : '');

		// Dot follows tightly.
		dotX += (mouseX - dotX) * 0.25;
		dotY += (mouseY - dotY) * 0.25;
		dot.style.transform = 'translate(' + dotX + 'px, ' + dotY + 'px) translate(-50%, -50%)';

		requestAnimationFrame(animate);
	}

	requestAnimationFrame(animate);

	/* --------------------------------------------------
	   Hover State — Expand ring on interactive elements
	   -------------------------------------------------- */

	var interactives = 'a, button, [role="button"], input, select, textarea, .product-card, .hotspot';

	document.addEventListener('mouseover', function (e) {
		if (e.target.closest(interactives)) {
			isHovering = true;
			ring.classList.add('hovering');
			dot.classList.add('hovering');
		}
	});

	document.addEventListener('mouseout', function (e) {
		if (e.target.closest(interactives)) {
			isHovering = false;
			ring.classList.remove('hovering');
			dot.classList.remove('hovering');
		}
	});

	/* --------------------------------------------------
	   Sparkle Trail (throttled)
	   -------------------------------------------------- */

	var lastTrailTime = 0;
	var trailInterval = 60; // ms between sparkles

	if (trail) {
		document.addEventListener('mousemove', function (e) {
			var now = Date.now();
			if (now - lastTrailTime < trailInterval) return;
			lastTrailTime = now;

			var spark = document.createElement('span');
			spark.className = 'cursor-sparkle';
			spark.style.left = e.clientX + 'px';
			spark.style.top = e.clientY + 'px';
			trail.appendChild(spark);

			setTimeout(function () {
				spark.remove();
			}, 600);
		}, { passive: true });
	}

	/* --------------------------------------------------
	   Hide on page leave, show on enter
	   -------------------------------------------------- */

	document.addEventListener('mouseleave', function () {
		ring.style.opacity = '0';
		dot.style.opacity = '0';
	});

	document.addEventListener('mouseenter', function () {
		ring.style.opacity = '1';
		dot.style.opacity = '1';
	});
})();
