/**
 * SkyyRose Brand Mascot — Interactive Walking Widget
 *
 * The mascot walks onto the screen from the right side after a delay,
 * stands in the bottom-right corner with idle animations, and opens
 * an interaction panel on click.
 *
 * Features:
 * - Walk-on entrance animation (3s delay)
 * - Idle breathing/bounce animation
 * - Click to open/close interaction panel
 * - Minimize (walk off) and recall (walk back on)
 * - Keyboard accessible (Escape to close/minimize)
 * - Respects prefers-reduced-motion
 * - Collection-aware outfit via data-context attribute
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */
(function () {
	'use strict';

	var WALK_ON_DELAY_MS = 3000;
	var GREETING_HIDE_DELAY_MS = 5000;

	var mascotEl = document.getElementById('skyyrose-mascot');
	if (!mascotEl) return;

	var trigger = document.getElementById('skyyrose-mascot-trigger');
	var panel = document.getElementById('skyyrose-mascot-panel');
	var minimizeBtn = document.getElementById('skyyrose-mascot-minimize');
	var recallBtn = document.getElementById('skyyrose-mascot-recall');
	var closeBtn = mascotEl.querySelector('.skyyrose-mascot__panel-close');
	var greeting = mascotEl.querySelector('.skyyrose-mascot__greeting');

	var isPanelOpen = false;
	var isMinimized = false;
	var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	// Context-aware greetings.
	var contextGreetings = {
		'homepage': 'Welcome to SkyyRose!',
		'black-rose': 'Explore Black Rose...',
		'love-hurts': 'Feel the Love Hurts vibe!',
		'signature': 'The Signature look awaits!',
		'kids-capsule': 'Hey little star!',
		'preorder': 'Pre-order your favorites!',
		'404': 'Oops! Let me help you find your way.',
		'default': 'Hey! Need help?'
	};

	var context = mascotEl.getAttribute('data-context') || 'default';
	if (greeting && contextGreetings[context]) {
		greeting.textContent = contextGreetings[context];
	}

	// -------------------------------------------------------------------------
	// Walk-On Entrance
	// -------------------------------------------------------------------------

	function walkOn() {
		mascotEl.setAttribute('aria-hidden', 'false');
		mascotEl.classList.add('skyyrose-mascot--entering');

		// After walk-on animation completes, switch to idle state.
		var walkDuration = prefersReducedMotion ? 0 : 800;
		setTimeout(function () {
			mascotEl.classList.remove('skyyrose-mascot--entering');
			mascotEl.classList.add('skyyrose-mascot--idle');

			// Show greeting bubble briefly.
			if (greeting) {
				greeting.classList.add('skyyrose-mascot__greeting--visible');
				setTimeout(function () {
					greeting.classList.remove('skyyrose-mascot__greeting--visible');
				}, GREETING_HIDE_DELAY_MS);
			}
		}, walkDuration);
	}

	// -------------------------------------------------------------------------
	// Panel Toggle
	// -------------------------------------------------------------------------

	function openPanel() {
		if (isPanelOpen || isMinimized) return;
		isPanelOpen = true;
		panel.setAttribute('aria-hidden', 'false');
		trigger.setAttribute('aria-expanded', 'true');
		mascotEl.classList.add('skyyrose-mascot--panel-open');
	}

	function closePanel() {
		if (!isPanelOpen) return;
		isPanelOpen = false;
		panel.setAttribute('aria-hidden', 'true');
		trigger.setAttribute('aria-expanded', 'false');
		mascotEl.classList.remove('skyyrose-mascot--panel-open');
	}

	function togglePanel() {
		if (isPanelOpen) {
			closePanel();
		} else {
			openPanel();
		}
	}

	// -------------------------------------------------------------------------
	// Minimize / Recall
	// -------------------------------------------------------------------------

	function minimize() {
		closePanel();
		isMinimized = true;
		mascotEl.classList.remove('skyyrose-mascot--idle');
		mascotEl.classList.add('skyyrose-mascot--exiting');

		var exitDuration = prefersReducedMotion ? 0 : 600;
		setTimeout(function () {
			mascotEl.classList.remove('skyyrose-mascot--exiting');
			mascotEl.classList.add('skyyrose-mascot--hidden');
			mascotEl.setAttribute('aria-hidden', 'true');
			recallBtn.style.display = 'flex';
			recallBtn.setAttribute('aria-hidden', 'false');
		}, exitDuration);
	}

	function recall() {
		isMinimized = false;
		recallBtn.style.display = 'none';
		recallBtn.setAttribute('aria-hidden', 'true');
		mascotEl.classList.remove('skyyrose-mascot--hidden');
		walkOn();
	}

	// -------------------------------------------------------------------------
	// Event Listeners
	// -------------------------------------------------------------------------

	if (trigger) {
		trigger.addEventListener('click', function (e) {
			e.stopPropagation();
			togglePanel();
		});
	}

	if (closeBtn) {
		closeBtn.addEventListener('click', function (e) {
			e.stopPropagation();
			closePanel();
		});
	}

	if (minimizeBtn) {
		minimizeBtn.addEventListener('click', function (e) {
			e.stopPropagation();
			minimize();
		});
	}

	if (recallBtn) {
		recallBtn.addEventListener('click', function (e) {
			e.stopPropagation();
			recall();
		});
	}

	// Close panel when clicking outside.
	document.addEventListener('click', function (e) {
		if (isPanelOpen && !mascotEl.contains(e.target)) {
			closePanel();
		}
	});

	// Keyboard: Escape to close panel or minimize.
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape') {
			if (isPanelOpen) {
				closePanel();
				trigger.focus();
			} else if (!isMinimized) {
				minimize();
			}
		}
	});

	// Hover: show wave reaction via CSS class.
	if (trigger) {
		trigger.addEventListener('mouseenter', function () {
			if (!isPanelOpen && !isMinimized) {
				mascotEl.classList.add('skyyrose-mascot--waving');
			}
		});
		trigger.addEventListener('mouseleave', function () {
			mascotEl.classList.remove('skyyrose-mascot--waving');
		});
	}

	// -------------------------------------------------------------------------
	// Initialize: Walk on after delay
	// -------------------------------------------------------------------------

	setTimeout(walkOn, WALK_ON_DELAY_MS);
})();
