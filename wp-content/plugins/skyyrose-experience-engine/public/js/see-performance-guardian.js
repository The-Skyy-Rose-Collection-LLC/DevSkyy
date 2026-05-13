/**
 * Performance Guardian — Animation Budget Manager & Lazy Load Orchestrator
 *
 * Ensures all SEE modules and theme engines respect Core Web Vitals:
 *   1. Animation budget — hard cap on concurrent animations (5 desktop, 3 mobile)
 *   2. Lazy module loading — below-fold modules init via IntersectionObserver
 *   3. CLS monitoring — logs PerformanceObserver entries to Experience Analyzer
 *   4. FPS watchdog — auto-pauses lowest-priority animations if FPS drops
 *   5. Tab visibility — pauses ALL animations when tab is hidden
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var SEE = window.SkyyRoseExperience;
	if (!SEE) {
		return;
	}

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var isMobile = window.innerWidth < 768;

	var CONFIG = {
		maxConcurrentAnimations: isMobile ? 3 : 5,
		fpsThreshold:            30,      // Below this, start pausing animations.
		fpsCheckInterval:        2000,    // ms between FPS checks.
		lazyRootMargin:          '200px', // Pre-load modules 200px before viewport.
		mobileBudgetRatio:       0.6,     // Mobile gets 60% of desktop budget.
	};

	/* ==========================================================================
	   Animation Budget Manager
	   ========================================================================== */

	var activeAnimations = [];
	var paused = false;

	function requestAnimation(id, priority, pauseFn, resumeFn) {
		// Remove any existing entry with same id.
		activeAnimations = activeAnimations.filter(function (a) { return a.id !== id; });

		if (activeAnimations.length >= CONFIG.maxConcurrentAnimations) {
			// Pause lowest-priority animation to make room.
			activeAnimations.sort(function (a, b) { return a.priority - b.priority; });
			var victim = activeAnimations.shift();
			if (victim && typeof victim.pause === 'function') {
				victim.pause();
				victim.state = 'paused';
			}
		}

		activeAnimations.push({
			id: id,
			priority: priority || 5,
			pause: pauseFn,
			resume: resumeFn,
			state: 'active',
		});

		return true;
	}

	function releaseAnimation(id) {
		activeAnimations = activeAnimations.filter(function (a) { return a.id !== id; });

		// Resume highest-priority paused animation if under budget.
		var pausedAnims = activeAnimations.filter(function (a) { return a.state === 'paused'; });
		if (pausedAnims.length > 0 && activeAnimations.filter(function (a) { return a.state === 'active'; }).length < CONFIG.maxConcurrentAnimations) {
			pausedAnims.sort(function (a, b) { return b.priority - a.priority; });
			var resumed = pausedAnims[0];
			if (typeof resumed.resume === 'function') {
				resumed.resume();
				resumed.state = 'active';
			}
		}
	}

	/* ==========================================================================
	   FPS Watchdog
	   ========================================================================== */

	var frameCount = 0;
	var lastFpsCheck = performance.now();
	var rafId = null;

	function fpsLoop(now) {
		frameCount++;
		if (now - lastFpsCheck >= CONFIG.fpsCheckInterval) {
			var fps = Math.round((frameCount * 1000) / (now - lastFpsCheck));
			frameCount = 0;
			lastFpsCheck = now;

			SEE.emit('performance:fps', { fps: fps });

			if (fps < CONFIG.fpsThreshold && activeAnimations.length > 1) {
				// Pause lowest-priority active animation.
				var actives = activeAnimations
					.filter(function (a) { return a.state === 'active'; })
					.sort(function (a, b) { return a.priority - b.priority; });

				if (actives.length > 1) {
					var victim = actives[0];
					if (typeof victim.pause === 'function') {
						victim.pause();
						victim.state = 'paused';
						SEE.emit('performance:throttled', { id: victim.id, fps: fps });
					}
				}
			}
		}
		rafId = requestAnimationFrame(fpsLoop);
	}

	/* ==========================================================================
	   Tab Visibility — Pause/resume all on hidden/visible
	   ========================================================================== */

	document.addEventListener('visibilitychange', function () {
		if (document.hidden) {
			paused = true;
			activeAnimations.forEach(function (a) {
				if (a.state === 'active' && typeof a.pause === 'function') {
					a.pause();
					a.state = 'tab-paused';
				}
			});
			if (rafId) {
				cancelAnimationFrame(rafId);
				rafId = null;
			}
			SEE.emit('performance:tab-hidden');
		} else {
			paused = false;
			activeAnimations.forEach(function (a) {
				if (a.state === 'tab-paused' && typeof a.resume === 'function') {
					a.resume();
					a.state = 'active';
				}
			});
			frameCount = 0;
			lastFpsCheck = performance.now();
			rafId = requestAnimationFrame(fpsLoop);
			SEE.emit('performance:tab-visible');
		}
	});

	/* ==========================================================================
	   CLS & LCP Monitoring via PerformanceObserver
	   ========================================================================== */

	var vitals = { cls: 0, lcp: 0, inp: 0 };

	if (typeof PerformanceObserver !== 'undefined') {
		try {
			// CLS
			var clsObserver = new PerformanceObserver(function (list) {
				list.getEntries().forEach(function (entry) {
					if (!entry.hadRecentInput) {
						vitals.cls += entry.value;
					}
				});
				SEE.emit('performance:cls', { value: vitals.cls });
			});
			clsObserver.observe({ type: 'layout-shift', buffered: true });

			// LCP
			var lcpObserver = new PerformanceObserver(function (list) {
				var entries = list.getEntries();
				var last = entries[entries.length - 1];
				if (last) {
					vitals.lcp = last.startTime;
					SEE.emit('performance:lcp', { value: vitals.lcp });
				}
			});
			lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
		} catch (e) {
			// PerformanceObserver types not supported — fail silently.
		}
	}

	/* ==========================================================================
	   Lazy Module Loader — IntersectionObserver for below-fold sections
	   ========================================================================== */

	function observeLazyElements() {
		if (!SEE.supportsIntersection) {
			return;
		}

		var observer = new IntersectionObserver(
			function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						var el = entry.target;
						var moduleId = el.getAttribute('data-see-lazy-module');
						if (moduleId) {
							SEE.emit('lazy:load', { module: moduleId, element: el });
							el.classList.add('see-lazy-loaded');
							observer.unobserve(el);
						}
					}
				});
			},
			{ rootMargin: CONFIG.lazyRootMargin }
		);

		document.querySelectorAll('[data-see-lazy-module]').forEach(function (el) {
			observer.observe(el);
		});
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('performance-guardian', {
		init: function () {
			// Start FPS watchdog.
			rafId = requestAnimationFrame(fpsLoop);
		},

		ready: function () {
			observeLazyElements();
		},

		destroy: function () {
			if (rafId) {
				cancelAnimationFrame(rafId);
			}
			activeAnimations = [];
		},
	});

	/* ==========================================================================
	   Public API extensions
	   ========================================================================== */

	SEE.performance = {
		requestAnimation: requestAnimation,
		releaseAnimation: releaseAnimation,
		getVitals:        function () { return Object.assign({}, vitals); },
		getActiveCount:   function () {
			return activeAnimations.filter(function (a) { return a.state === 'active'; }).length;
		},
		getBudget: function () {
			return CONFIG.maxConcurrentAnimations;
		},
		isPaused: function () {
			return paused;
		},
	};

})();
