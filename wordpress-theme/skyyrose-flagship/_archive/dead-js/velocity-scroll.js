/**
 * Velocity — Scroll-Driven Product Storytelling Engine
 *
 * Powers the Velocity CSS classes and drives scroll-linked behaviors:
 *
 *   1. Progressive Product Reveal (IntersectionObserver-driven)
 *   2. Story Beat Triggering
 *   3. Cinematic Room Depth Parallax (mouse/scroll-driven)
 *   4. Scroll Progress Spine (auto-injects progress indicator)
 *   5. Momentum Section Transitions (velocity-aware reveals)
 *   6. Product Spotlight Zone (center-viewport detection)
 *   7. Engagement Velocity Tracking (scroll speed → dashboard relay)
 *
 * Emits cie:event custom events consumed by analytics-beacon.js.
 * No dependencies — vanilla JS. Production-quality.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CFG = {
		/* IntersectionObserver thresholds */
		revealThreshold:     0.18,
		storyBeatThreshold:  0.30,
		spotlightThreshold:  [0, 0.3, 0.5, 0.7, 1],

		/* Parallax multipliers */
		parallaxBg:          0.3,
		parallaxFg:          1.4,

		/* Scroll velocity sampling */
		velocityWindowMs:    300,
		fastScrollPxPerSec:  1200,

		/* Spotlight zone: center 40% of viewport */
		spotlightTop:        0.30,
		spotlightBottom:     0.70,

		/* Velocity indicator auto-hide delay (ms) */
		velocityHideDelay:   1500,

		/* Spine section markers: CSS selector for trackable sections */
		sectionSelector:     '.vel-section, .collection-section, .immersive-scene, .preorder-section',

		/* Analytics event names */
		eventReveal:         'velocity_product_reveal',
		eventStoryBeat:      'velocity_story_beat',
		eventSpotlight:      'velocity_spotlight',
		eventScrollDepth:    'velocity_scroll_depth',
	};


	/* ==========================================================================
	   Shared state
	   ========================================================================== */

	var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var scrollY      = 0;
	var prevScrollY  = 0;
	var scrollSpeed  = 0;
	var docHeight    = 1;
	var vpHeight     = window.innerHeight;
	var cleanupFns   = [];
	var observers    = [];
	var intervals    = [];


	/* ==========================================================================
	   Utility
	   ========================================================================== */

	function clamp(val, min, max) {
		return Math.max(min, Math.min(max, val));
	}

	function emitCIE(eventName, data) {
		try {
			window.dispatchEvent(new CustomEvent('cie:event', {
				detail: { event: eventName, data: data || {} }
			}));
		} catch (e) { /* silent in older browsers */ }
	}

	function throttle(fn, ms) {
		var lastCall = 0;
		return function () {
			var now = Date.now();
			if (now - lastCall >= ms) {
				lastCall = now;
				fn.apply(null, arguments);
			}
		};
	}


	/* ==========================================================================
	   1. Progressive Product Reveal
	   ========================================================================== */

	function initProductReveals() {
		var targets = document.querySelectorAll('.vel-product-reveal');
		if (!targets.length) return;

		if (!('IntersectionObserver' in window)) {
			for (var i = 0; i < targets.length; i++) {
				targets[i].classList.add('vel-revealed');
			}
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			for (var j = 0; j < entries.length; j++) {
				if (!entries[j].isIntersecting) continue;

				var el = entries[j].target;
				el.classList.add('vel-revealed');

				/* Emit analytics */
				var sku = el.getAttribute('data-sku') || '';
				var name = el.getAttribute('data-product-name') || '';
				emitCIE(CFG.eventReveal, { sku: sku, product: name });

				observer.unobserve(el);
			}
		}, { threshold: CFG.revealThreshold });

		for (var k = 0; k < targets.length; k++) {
			observer.observe(targets[k]);
		}
		observers.push(observer);
	}


	/* ==========================================================================
	   2. Story Beat Triggering
	   ========================================================================== */

	function initStoryBeats() {
		var beats = document.querySelectorAll('.vel-story-beat');
		if (!beats.length) return;

		if (!('IntersectionObserver' in window)) {
			for (var i = 0; i < beats.length; i++) {
				beats[i].classList.add('vel-in-view');
			}
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			for (var j = 0; j < entries.length; j++) {
				if (!entries[j].isIntersecting) continue;

				var el = entries[j].target;
				el.classList.add('vel-in-view');

				var beatId = el.getAttribute('data-beat-id') || '';
				emitCIE(CFG.eventStoryBeat, { beat_id: beatId });

				observer.unobserve(el);
			}
		}, { threshold: CFG.storyBeatThreshold });

		for (var k = 0; k < beats.length; k++) {
			observer.observe(beats[k]);
		}
		observers.push(observer);
	}


	/* ==========================================================================
	   3. Cinematic Room Depth Parallax
	   ========================================================================== */

	function initParallax() {
		var scenes = document.querySelectorAll('.vel-scene-depth');
		if (!scenes.length || REDUCED) return;

		function updateParallax() {
			for (var i = 0; i < scenes.length; i++) {
				var scene = scenes[i];
				var rect = scene.getBoundingClientRect();

				/* Only process visible scenes */
				if (rect.bottom < 0 || rect.top > vpHeight) continue;

				/* How far into viewport (0 = top entering, 1 = bottom leaving) */
				var progress = clamp((vpHeight - rect.top) / (vpHeight + rect.height), 0, 1);
				var offset = (progress - 0.5) * 60; /* -30px to +30px range */

				var bgLayers = scene.querySelectorAll('.vel-layer-bg');
				var fgLayers = scene.querySelectorAll('.vel-layer-fg');

				for (var b = 0; b < bgLayers.length; b++) {
					bgLayers[b].style.transform = 'translateY(' + (offset * CFG.parallaxBg) + 'px)';
				}
				for (var f = 0; f < fgLayers.length; f++) {
					fgLayers[f].style.transform = 'translateY(' + (offset * CFG.parallaxFg * -1) + 'px)';
				}
			}
		}

		var onScroll = throttle(function () {
			requestAnimationFrame(updateParallax);
		}, 16);

		window.addEventListener('scroll', onScroll, { passive: true });
		cleanupFns.push(function () {
			window.removeEventListener('scroll', onScroll);
		});

		/* Initial calc */
		updateParallax();
	}


	/* ==========================================================================
	   4. Scroll Progress Spine
	   ========================================================================== */

	function initScrollSpine() {
		/* Don't inject on very short pages */
		if (document.body.scrollHeight <= vpHeight * 1.5) return;

		/* Create spine container */
		var spine = document.createElement('div');
		spine.className = 'vel-scroll-spine';
		spine.setAttribute('aria-hidden', 'true');

		var fill = document.createElement('div');
		fill.className = 'vel-scroll-spine__fill';
		spine.appendChild(fill);

		/* Add section markers */
		var sections = document.querySelectorAll(CFG.sectionSelector);
		var markerEls = [];

		for (var i = 0; i < sections.length; i++) {
			var marker = document.createElement('div');
			marker.className = 'vel-scroll-spine__marker';
			spine.appendChild(marker);
			markerEls.push({ el: marker, section: sections[i] });
		}

		document.body.appendChild(spine);

		/* Update positions on scroll */
		function updateSpine() {
			var scrollFrac = clamp(scrollY / Math.max(1, docHeight - vpHeight), 0, 1);
			document.documentElement.style.setProperty('--vel-scroll', scrollFrac.toFixed(4));

			/* Position markers based on section location in document */
			for (var j = 0; j < markerEls.length; j++) {
				var sectionTop = markerEls[j].section.offsetTop;
				var markerFrac = clamp(sectionTop / Math.max(1, docHeight), 0, 1);
				markerEls[j].el.style.top = (markerFrac * 100) + '%';

				/* Mark as passed if we've scrolled past */
				if (scrollFrac >= markerFrac - 0.01) {
					markerEls[j].el.classList.add('vel-passed');
				} else {
					markerEls[j].el.classList.remove('vel-passed');
				}
			}
		}

		var onScroll = throttle(function () {
			requestAnimationFrame(updateSpine);
		}, 16);

		window.addEventListener('scroll', onScroll, { passive: true });
		cleanupFns.push(function () {
			window.removeEventListener('scroll', onScroll);
			if (spine.parentNode) spine.parentNode.removeChild(spine);
		});

		updateSpine();
	}


	/* ==========================================================================
	   5. Momentum Section Transitions
	   ========================================================================== */

	function initMomentum() {
		var targets = document.querySelectorAll('.vel-momentum');
		if (!targets.length) return;

		if (!('IntersectionObserver' in window)) {
			for (var i = 0; i < targets.length; i++) {
				targets[i].classList.add('vel-in-view');
			}
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			for (var j = 0; j < entries.length; j++) {
				if (!entries[j].isIntersecting) continue;

				var el = entries[j].target;
				el.classList.add('vel-in-view');

				/* Check scroll velocity for fast-scroll class */
				if (scrollSpeed > CFG.fastScrollPxPerSec && !REDUCED) {
					el.classList.add('vel-fast-scroll');
				}

				observer.unobserve(el);
			}
		}, { threshold: CFG.revealThreshold });

		for (var k = 0; k < targets.length; k++) {
			observer.observe(targets[k]);
		}
		observers.push(observer);
	}


	/* ==========================================================================
	   6. Product Spotlight Zone
	   ========================================================================== */

	function initSpotlight() {
		var spotlights = document.querySelectorAll('.vel-spotlight');
		if (!spotlights.length) return;

		var spotlightTop = vpHeight * CFG.spotlightTop;
		var spotlightBottom = vpHeight * CFG.spotlightBottom;

		function updateSpotlights() {
			for (var i = 0; i < spotlights.length; i++) {
				var rect = spotlights[i].getBoundingClientRect();
				var center = rect.top + rect.height / 2;
				var inZone = center >= spotlightTop && center <= spotlightBottom;

				if (inZone && !spotlights[i].classList.contains('vel-in-spotlight')) {
					spotlights[i].classList.add('vel-in-spotlight');
					var sku = spotlights[i].getAttribute('data-sku') || '';
					emitCIE(CFG.eventSpotlight, { sku: sku });
				} else if (!inZone) {
					spotlights[i].classList.remove('vel-in-spotlight');
				}
			}
		}

		var onScroll = throttle(function () {
			requestAnimationFrame(updateSpotlights);
		}, 50);

		window.addEventListener('scroll', onScroll, { passive: true });
		cleanupFns.push(function () {
			window.removeEventListener('scroll', onScroll);
		});

		updateSpotlights();
	}


	/* ==========================================================================
	   7. Engagement Velocity Tracking
	   ========================================================================== */

	function initVelocityTracking() {
		var indicator = null;
		var hideTimer = null;
		var lastScrollTime = Date.now();
		var depthMilestones = { 25: false, 50: false, 75: false, 100: false };

		/* Auto-inject velocity indicator (desktop only) */
		if (!window.matchMedia('(pointer: fine)').matches) return;

		indicator = document.createElement('div');
		indicator.className = 'vel-velocity-indicator';
		indicator.innerHTML =
			'<span class="vel-velocity-indicator__flame"></span>' +
			'<span class="vel-velocity-indicator__label">Exploring</span>';
		document.body.appendChild(indicator);

		function updateVelocity() {
			scrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
			var now = Date.now();
			var dt = now - lastScrollTime;

			if (dt > 0) {
				scrollSpeed = Math.abs(scrollY - prevScrollY) / (dt / 1000);
			}
			prevScrollY = scrollY;
			lastScrollTime = now;

			/* Update document height */
			docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);

			/* Scroll depth milestones */
			var depth = Math.round((scrollY / Math.max(1, docHeight - vpHeight)) * 100);
			for (var milestone in depthMilestones) {
				if (Object.prototype.hasOwnProperty.call(depthMilestones, milestone)) {
					var ms = parseInt(milestone, 10);
					if (depth >= ms && !depthMilestones[milestone]) {
						depthMilestones[milestone] = true;
						emitCIE(CFG.eventScrollDepth, { depth: ms, velocity: Math.round(scrollSpeed) });
					}
				}
			}

			/* Update velocity indicator */
			if (indicator) {
				/* Show on active scrolling */
				if (scrollSpeed > 100) {
					indicator.classList.add('vel-active');

					/* Set intensity level */
					indicator.classList.remove('vel-intensity-1', 'vel-intensity-2', 'vel-intensity-3');
					if (scrollSpeed > CFG.fastScrollPxPerSec) {
						indicator.classList.add('vel-intensity-3');
					} else if (scrollSpeed > 600) {
						indicator.classList.add('vel-intensity-2');
					} else {
						indicator.classList.add('vel-intensity-1');
					}

					/* Reset hide timer */
					clearTimeout(hideTimer);
					hideTimer = setTimeout(function () {
						indicator.classList.remove('vel-active');
					}, CFG.velocityHideDelay);
				}
			}
		}

		var onScroll = throttle(updateVelocity, 50);
		window.addEventListener('scroll', onScroll, { passive: true });

		cleanupFns.push(function () {
			window.removeEventListener('scroll', onScroll);
			clearTimeout(hideTimer);
			if (indicator && indicator.parentNode) {
				indicator.parentNode.removeChild(indicator);
			}
		});

		/* Initial update */
		updateVelocity();
	}


	/* ==========================================================================
	   8. Viewport Resize Handler
	   ========================================================================== */

	function initResizeHandler() {
		var onResize = throttle(function () {
			vpHeight = window.innerHeight;
			docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
		}, 200);

		window.addEventListener('resize', onResize, { passive: true });
		cleanupFns.push(function () {
			window.removeEventListener('resize', onResize);
		});
	}


	/* ==========================================================================
	   Cleanup
	   ========================================================================== */

	function destroy() {
		var i;
		for (i = 0; i < observers.length; i++) {
			observers[i].disconnect();
		}
		for (i = 0; i < intervals.length; i++) {
			clearInterval(intervals[i]);
		}
		for (i = 0; i < cleanupFns.length; i++) {
			cleanupFns[i]();
		}
	}


	/* ==========================================================================
	   Init
	   ========================================================================== */

	function init() {
		/* Skip on admin pages */
		if (document.body.classList.contains('wp-admin')) return;

		/* Initialize scroll state */
		scrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
		prevScrollY = scrollY;
		docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
		vpHeight = window.innerHeight;

		initProductReveals();
		initStoryBeats();
		initParallax();
		initScrollSpine();
		initMomentum();
		initSpotlight();
		initVelocityTracking();
		initResizeHandler();

		/* Cleanup on unload */
		window.addEventListener('beforeunload', destroy);
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
