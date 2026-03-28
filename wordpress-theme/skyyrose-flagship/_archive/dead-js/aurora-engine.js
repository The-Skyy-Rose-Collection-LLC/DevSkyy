/**
 * Aurora — Ambient Engagement Engine
 *
 * Powers the Aurora CSS classes and manages interactive conversion
 * behaviors: CTA shimmer, engagement depth tracking, scroll reveals,
 * product card 3D tilt, VIP countdown, and scarcity level management.
 *
 * No dependencies — vanilla JS. Production-quality.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CONFIG = {
		/* Shimmer stagger (ms between each CTA receiving its shimmer class) */
		shimmerStaggerMs:       200,

		/* Engagement depth weights (must sum to 1.0) */
		engagementWeightScroll: 0.35,
		engagementWeightTime:   0.35,
		engagementWeightClicks: 0.30,

		/* Time ceiling: seconds on page that count as 100% time engagement */
		engagementTimeCeiling:  60,

		/* Clicks that count as 100% interaction engagement */
		engagementClickCeiling: 10,

		/* VIP unlock threshold (0-100) */
		vipUnlockThreshold:     80,

		/* Discount code revealed at VIP unlock */
		vipDiscountCode:        'SKYYROSE15',

		/* Scroll reveal IntersectionObserver threshold */
		revealThreshold:        0.15,

		/* Countdown target date (ISO 8601) */
		countdownTarget:        '2026-04-01T00:00:00',

		/* Countdown update interval (ms) */
		countdownInterval:      1000,

		/* Engagement score update interval (ms) */
		engagementTickMs:       500
	};


	/* ==========================================================================
	   Accessibility — Respect prefers-reduced-motion
	   ========================================================================== */

	var prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;


	/* ==========================================================================
	   Utility
	   ========================================================================== */

	/**
	 * Sanitize text content to prevent XSS in any dynamic strings.
	 */
	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	/**
	 * Zero-pad a number to 2 digits.
	 */
	function pad2(n) {
		return n < 10 ? '0' + n : '' + n;
	}


	/* ==========================================================================
	   AuroraEngine Class
	   ========================================================================== */

	function AuroraEngine() {
		/* Cleanup tracking */
		this.intervals = [];
		this.rafs = [];
		this.observers = [];
		this.cleanupFns = [];

		/* Engagement state */
		this.scrollPercent = 0;
		this.timeOnPage = 0;
		this.interactionCount = 0;
		this.engagementScore = 0;
		this.vipUnlocked = false;

		/* Timestamps */
		this.pageLoadTime = Date.now();
	}


	/* --------------------------------------------------------------------------
	   init() — Entry point
	   -------------------------------------------------------------------------- */

	AuroraEngine.prototype.init = function () {
		/* Skip on admin pages */
		if (document.body.classList.contains('wp-admin')) return;

		/* Check for prior VIP unlock in this session */
		if (sessionStorage.getItem('sr_aurora_vip_unlocked') === '1') {
			this.vipUnlocked = true;
			this._applyVipState();
		}

		this.initShimmerController();
		this.initEngagementTracker();
		this.initScrollReveals();
		this.initProductTilt();
		this.initCountdown();
		this.initScarcityLevels();

		/* Cleanup on page unload */
		var self = this;
		window.addEventListener('beforeunload', function () {
			self.destroy();
		});
	};


	/* --------------------------------------------------------------------------
	   destroy() — Cleanup all intervals, observers, and RAF handles
	   -------------------------------------------------------------------------- */

	AuroraEngine.prototype.destroy = function () {
		var i;
		for (i = 0; i < this.intervals.length; i++) {
			clearInterval(this.intervals[i]);
		}
		for (i = 0; i < this.rafs.length; i++) {
			cancelAnimationFrame(this.rafs[i]);
		}
		for (i = 0; i < this.observers.length; i++) {
			this.observers[i].disconnect();
		}
		for (i = 0; i < this.cleanupFns.length; i++) {
			this.cleanupFns[i]();
		}
	};


	/* ==========================================================================
	   1. CTA Shimmer Controller
	   ========================================================================== */

	AuroraEngine.prototype.initShimmerController = function () {
		/* Collect all shimmer targets */
		var targets = document.querySelectorAll(
			'.btn-primary, .btn-preorder, [data-aurora-shimmer]'
		);
		if (!targets.length) return;

		/* If user prefers reduced motion, add class without animation delay */
		if (prefersReducedMotion) {
			for (var i = 0; i < targets.length; i++) {
				targets[i].classList.add('aurora-shimmer');
			}
			return;
		}

		/* Stagger shimmer class application so buttons don't all shimmer at once */
		for (var j = 0; j < targets.length; j++) {
			(function (el, index) {
				var delay = index * CONFIG.shimmerStaggerMs;
				/* Set a CSS custom property for animation-delay so the CSS
				   keyframes can stagger even after the class is applied */
				el.style.setProperty('--aurora-shimmer-delay', delay + 'ms');
				setTimeout(function () {
					el.classList.add('aurora-shimmer');
				}, delay);
			})(targets[j], j);
		}
	};


	/* ==========================================================================
	   2. Engagement Depth Tracker
	   ========================================================================== */

	AuroraEngine.prototype.initEngagementTracker = function () {
		var self = this;

		/* --- Scroll tracking --- */
		var scrollHandler = function () {
			var docHeight = Math.max(
				document.body.scrollHeight,
				document.documentElement.scrollHeight
			);
			var viewportHeight = window.innerHeight;
			var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
			var scrollable = docHeight - viewportHeight;

			if (scrollable > 0) {
				self.scrollPercent = Math.min(100, Math.round((scrollTop / scrollable) * 100));
			} else {
				self.scrollPercent = 100;
			}
		};

		window.addEventListener('scroll', scrollHandler, { passive: true });
		this.cleanupFns.push(function () {
			window.removeEventListener('scroll', scrollHandler);
		});

		/* Capture initial scroll position */
		scrollHandler();

		/* --- Interaction tracking (clicks on hotspots, product cards, CTAs) --- */
		var clickHandler = function (e) {
			var target = e.target;
			/* Walk up to check if click was on a product-interactive element */
			var el = target;
			var maxDepth = 6;
			while (el && maxDepth > 0) {
				if (
					el.classList &&
					(
						el.classList.contains('product-grid-card') ||
						el.classList.contains('hotspot') ||
						el.classList.contains('btn-primary') ||
						el.classList.contains('btn-preorder') ||
						el.classList.contains('aurora-tilt') ||
						el.hasAttribute && el.hasAttribute('data-aurora-shimmer')
					)
				) {
					self.interactionCount++;
					break;
				}
				el = el.parentElement;
				maxDepth--;
			}
		};

		document.addEventListener('click', clickHandler);
		this.cleanupFns.push(function () {
			document.removeEventListener('click', clickHandler);
		});

		/* --- Periodic engagement score calculation --- */
		var engagementTick = function () {
			/* Time component: seconds on page, capped at ceiling */
			var elapsed = (Date.now() - self.pageLoadTime) / 1000;
			self.timeOnPage = Math.min(elapsed, CONFIG.engagementTimeCeiling);
			var timePercent = (self.timeOnPage / CONFIG.engagementTimeCeiling) * 100;

			/* Click component: capped at ceiling */
			var clickPercent = Math.min(100, (self.interactionCount / CONFIG.engagementClickCeiling) * 100);

			/* Combined weighted score */
			self.engagementScore = Math.round(
				(self.scrollPercent * CONFIG.engagementWeightScroll) +
				(timePercent * CONFIG.engagementWeightTime) +
				(clickPercent * CONFIG.engagementWeightClicks)
			);

			/* Clamp to 0-100 */
			self.engagementScore = Math.max(0, Math.min(100, self.engagementScore));

			/* Update CSS custom property on the document */
			document.documentElement.style.setProperty(
				'--aurora-engagement',
				self.engagementScore
			);

			/* VIP unlock check */
			if (!self.vipUnlocked && self.engagementScore >= CONFIG.vipUnlockThreshold) {
				self.vipUnlocked = true;
				sessionStorage.setItem('sr_aurora_vip_unlocked', '1');
				self._triggerVipUnlock();
			}
		};

		this.intervals.push(setInterval(engagementTick, CONFIG.engagementTickMs));

		/* Run once immediately */
		engagementTick();
	};


	/**
	 * Trigger VIP unlock: add class to progress widget and reveal discount code.
	 */
	AuroraEngine.prototype._triggerVipUnlock = function () {
		this._applyVipState();

		/* Animate the reveal if the widget exists */
		var widget = document.querySelector('.aurora-progress-widget');
		if (widget) {
			var codeEl = widget.querySelector('.aurora-vip-code');
			if (codeEl) {
				codeEl.style.opacity = '0';
				codeEl.style.transform = 'translateY(8px)';

				/* Use rAF for smooth transition start */
				var raf = requestAnimationFrame(function () {
					codeEl.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
					codeEl.style.opacity = '1';
					codeEl.style.transform = 'translateY(0)';
				});
				this.rafs.push(raf);
			}
		}
	};


	/**
	 * Apply VIP state to the DOM (used on both fresh unlock and session restore).
	 */
	AuroraEngine.prototype._applyVipState = function () {
		var widget = document.querySelector('.aurora-progress-widget');
		if (widget) {
			widget.classList.add('aurora-vip-unlocked');

			/* If there is no code element yet, inject one */
			if (!widget.querySelector('.aurora-vip-code')) {
				var codeEl = document.createElement('div');
				codeEl.className = 'aurora-vip-code';
				codeEl.innerHTML =
					'<span class="aurora-vip-code__label">Your VIP Code:</span> ' +
					'<strong class="aurora-vip-code__value">' +
					escapeHtml(CONFIG.vipDiscountCode) +
					'</strong>';
				widget.appendChild(codeEl);
			}
		}
	};


	/* ==========================================================================
	   3. Smart Scroll Reveals
	   ========================================================================== */

	AuroraEngine.prototype.initScrollReveals = function () {
		var targets = document.querySelectorAll('.aurora-reveal');
		if (!targets.length) return;

		/* If IntersectionObserver is not supported, reveal everything immediately */
		if (!('IntersectionObserver' in window)) {
			for (var i = 0; i < targets.length; i++) {
				targets[i].classList.add('aurora-revealed');
			}
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			for (var j = 0; j < entries.length; j++) {
				var entry = entries[j];
				if (!entry.isIntersecting) continue;

				var el = entry.target;
				var delay = parseInt(el.getAttribute('data-aurora-delay'), 10) || 0;

				/* Apply reveal with optional stagger delay */
				if (delay > 0 && !prefersReducedMotion) {
					(function (element, ms) {
						setTimeout(function () {
							element.classList.add('aurora-revealed');
						}, ms);
					})(el, delay);
				} else {
					el.classList.add('aurora-revealed');
				}

				/* Stop observing once revealed */
				observer.unobserve(el);
			}
		}, {
			threshold: CONFIG.revealThreshold
		});

		for (var k = 0; k < targets.length; k++) {
			observer.observe(targets[k]);
		}

		this.observers.push(observer);
	};


	/* ==========================================================================
	   4. Product Card 3D Tilt
	   ========================================================================== */

	AuroraEngine.prototype.initProductTilt = function () {
		/* Only enable on devices with a fine pointer (desktop) */
		if (!window.matchMedia || !window.matchMedia('(pointer: fine)').matches) return;

		/* Skip if user prefers reduced motion */
		if (prefersReducedMotion) return;

		var tiltElements = document.querySelectorAll('.aurora-tilt');
		if (!tiltElements.length) return;

		var self = this;

		for (var i = 0; i < tiltElements.length; i++) {
			(function (el) {
				var onMouseMove = function (e) {
					var rect = el.getBoundingClientRect();
					var x = ((e.clientX - rect.left) / rect.width) * 100;
					var y = ((e.clientY - rect.top) / rect.height) * 100;

					/* Clamp to 0-100 */
					x = Math.max(0, Math.min(100, x));
					y = Math.max(0, Math.min(100, y));

					/* Use rAF for smooth updates */
					requestAnimationFrame(function () {
						el.style.setProperty('--mouse-x', x);
						el.style.setProperty('--mouse-y', y);
					});
				};

				var onMouseLeave = function () {
					/* Reset to center on leave */
					requestAnimationFrame(function () {
						el.style.setProperty('--mouse-x', 50);
						el.style.setProperty('--mouse-y', 50);
					});
				};

				el.addEventListener('mousemove', onMouseMove);
				el.addEventListener('mouseleave', onMouseLeave);

				/* Set initial centered values */
				el.style.setProperty('--mouse-x', 50);
				el.style.setProperty('--mouse-y', 50);

				self.cleanupFns.push(function () {
					el.removeEventListener('mousemove', onMouseMove);
					el.removeEventListener('mouseleave', onMouseLeave);
				});
			})(tiltElements[i]);
		}
	};


	/* ==========================================================================
	   5. VIP Countdown Timer
	   ========================================================================== */

	AuroraEngine.prototype.initCountdown = function () {
		var targetDate = new Date(CONFIG.countdownTarget).getTime();
		if (isNaN(targetDate)) return;

		/* Look for an existing container or auto-create one */
		var container = document.querySelector('.aurora-countdown');
		var autoCreated = false;

		if (!container) {
			container = this._createCountdownBar();
			autoCreated = true;
		}

		/* Inject the countdown digits structure */
		var countdownInner = document.createElement('div');
		countdownInner.className = 'aurora-countdown__inner';
		countdownInner.innerHTML =
			'<span class="aurora-countdown__label">Pre-order closes in</span>' +
			'<div class="aurora-countdown__digits">' +
				'<span class="aurora-countdown__unit">' +
					'<span class="aurora-countdown__number" data-aurora-days>--</span>' +
					'<span class="aurora-countdown__unit-label">Days</span>' +
				'</span>' +
				'<span class="aurora-countdown__sep">:</span>' +
				'<span class="aurora-countdown__unit">' +
					'<span class="aurora-countdown__number" data-aurora-hours>--</span>' +
					'<span class="aurora-countdown__unit-label">Hrs</span>' +
				'</span>' +
				'<span class="aurora-countdown__sep">:</span>' +
				'<span class="aurora-countdown__unit">' +
					'<span class="aurora-countdown__number" data-aurora-mins>--</span>' +
					'<span class="aurora-countdown__unit-label">Min</span>' +
				'</span>' +
				'<span class="aurora-countdown__sep">:</span>' +
				'<span class="aurora-countdown__unit">' +
					'<span class="aurora-countdown__number" data-aurora-secs>--</span>' +
					'<span class="aurora-countdown__unit-label">Sec</span>' +
				'</span>' +
			'</div>';

		container.appendChild(countdownInner);

		/* Cache DOM refs for the tick function */
		var daysEl = container.querySelector('[data-aurora-days]');
		var hoursEl = container.querySelector('[data-aurora-hours]');
		var minsEl = container.querySelector('[data-aurora-mins]');
		var secsEl = container.querySelector('[data-aurora-secs]');

		function tick() {
			var now = Date.now();
			var diff = Math.max(0, targetDate - now);

			var days = Math.floor(diff / 86400000);
			var hours = Math.floor((diff % 86400000) / 3600000);
			var mins = Math.floor((diff % 3600000) / 60000);
			var secs = Math.floor((diff % 60000) / 1000);

			if (daysEl) daysEl.textContent = pad2(days);
			if (hoursEl) hoursEl.textContent = pad2(hours);
			if (minsEl) minsEl.textContent = pad2(mins);
			if (secsEl) secsEl.textContent = pad2(secs);

			/* If countdown expired, show launch message */
			if (diff === 0) {
				var label = container.querySelector('.aurora-countdown__label');
				if (label) label.textContent = 'Now Available';

				var digits = container.querySelector('.aurora-countdown__digits');
				if (digits) digits.style.display = 'none';
			}
		}

		/* Run immediately, then on interval */
		tick();
		this.intervals.push(setInterval(tick, CONFIG.countdownInterval));
	};


	/**
	 * Auto-create a slim countdown bar and inject it at the top of the page.
	 */
	AuroraEngine.prototype._createCountdownBar = function () {
		var bar = document.createElement('div');
		bar.className = 'aurora-countdown aurora-countdown--bar';
		bar.setAttribute('role', 'timer');
		bar.setAttribute('aria-label', 'Pre-order countdown');

		/* Insert as first child of body so it sits at the very top */
		if (document.body.firstChild) {
			document.body.insertBefore(bar, document.body.firstChild);
		} else {
			document.body.appendChild(bar);
		}

		return bar;
	};


	/* ==========================================================================
	   6. Scarcity Level Manager
	   ========================================================================== */

	AuroraEngine.prototype.initScarcityLevels = function () {
		var elements = document.querySelectorAll('[data-aurora-scarcity]');
		if (!elements.length) return;

		for (var i = 0; i < elements.length; i++) {
			var el = elements[i];
			var value = parseInt(el.getAttribute('data-aurora-scarcity'), 10);

			/* Skip invalid values */
			if (isNaN(value) || value < 1 || value > 10) continue;

			/* Remove any existing scarcity class to prevent duplicates */
			el.classList.remove('scarcity-normal', 'scarcity-limited', 'scarcity-critical');

			if (value >= 7) {
				el.classList.add('scarcity-normal');
			} else if (value >= 4) {
				el.classList.add('scarcity-limited');
			} else {
				el.classList.add('scarcity-critical');
			}
		}
	};


	/* ==========================================================================
	   Initialization — DOMContentLoaded
	   ========================================================================== */

	var engine = new AuroraEngine();

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', function () {
			engine.init();
		});
	} else {
		engine.init();
	}

})();
