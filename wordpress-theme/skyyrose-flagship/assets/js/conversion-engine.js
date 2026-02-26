/**
 * Conversion Intelligence Engine — JavaScript
 *
 * Real-time social proof, urgency mechanics, and conversion-driving
 * behaviors. Self-contained, no external dependencies.
 *
 * Modules:
 *   1. SocialProofToasts — Recent purchase/viewer notifications
 *   2. LiveViewerCounter — Simulated real-time viewer counts
 *   3. UrgencyCountdown — Pre-order window countdown timer
 *   4. StockScarcity — "Only X left" visual indicator
 *   5. FloatingCTA — Scroll-triggered sticky pre-order bar
 *   6. ExitIntent — Mouse-leave overlay with special offer
 *   7. ConversionTracker — Event tracking for analytics
 *   8. PreorderProgress — Goal progress bar
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CONFIG = {
		toastInterval: 18000,         // ms between social proof toasts
		toastDuration: 6000,          // ms each toast is visible
		viewerBase: 23,               // base viewer count
		viewerVariance: 18,           // random variance (+/-)
		viewerUpdateInterval: 8000,   // ms between viewer count updates
		countdownTarget: null,        // Set by data attribute or default
		stockLevels: {
			'br-004': 12, 'br-005': 5, 'br-006': 8,
			'lh-001': 10, 'lh-002': 8, 'lh-002b': 6, 'lh-003': 9,
			'sg-001-tee': 7, 'sg-001-shorts': 7, 'sg-009': 5,
		},
		preorderGoal: 500,
		preorderCurrent: 347,
		floatingCTAThreshold: 400,    // px scroll before showing
		exitIntentCooldown: 86400000, // 24h between exit-intent shows
	};

	// Track all intervals for potential cleanup.
	var cleanupIntervals = [];

	/* --------------------------------------------------
	   Utility
	   -------------------------------------------------- */

	function randomInt(min, max) {
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	function createElement(tag, className, attrs) {
		var el = document.createElement(tag);
		if (className) el.className = className;
		if (attrs) {
			Object.keys(attrs).forEach(function (key) {
				if (key === 'textContent') {
					el.textContent = attrs[key];
				} else if (key === 'innerHTML') {
					el.innerHTML = attrs[key];
				} else {
					el.setAttribute(key, attrs[key]);
				}
			});
		}
		return el;
	}

	/* --------------------------------------------------
	   1. Social Proof Toasts
	   -------------------------------------------------- */

	var SOCIAL_PROOF_MESSAGES = [
		{ type: 'purchase', title: 'Someone in Atlanta just pre-ordered', meta: 'BLACK Rose Hoodie — 2 minutes ago' },
		{ type: 'purchase', title: 'Someone in Los Angeles just pre-ordered', meta: 'Love Hurts Varsity Jacket — 5 minutes ago' },
		{ type: 'purchase', title: 'Someone in New York just pre-ordered', meta: 'The Bay Set — 8 minutes ago' },
		{ type: 'purchase', title: 'Someone in Houston just pre-ordered', meta: 'BLACK Rose Sherpa Jacket — 12 minutes ago' },
		{ type: 'purchase', title: 'Someone in Chicago just pre-ordered', meta: 'Mint & Lavender Hoodie — 15 minutes ago' },
		{ type: 'purchase', title: 'Someone in Miami just pre-ordered', meta: 'Love Hurts Windbreaker — 18 minutes ago' },
		{ type: 'trending', title: 'BLACK Rose Hoodie is trending', meta: '47 pre-orders in the last 24 hours' },
		{ type: 'trending', title: 'Love Hurts Varsity Jacket is trending', meta: '32 pre-orders in the last 24 hours' },
		{ type: 'trending', title: 'The Bay Set is trending', meta: '28 pre-orders in the last 24 hours' },
		{ type: 'viewer', title: '38 people are browsing right now', meta: 'Black Rose Collection' },
		{ type: 'viewer', title: '24 people viewing this collection', meta: 'Love Hurts Collection' },
	];

	var toastContainer = null;
	var toastIndex = 0;
	var toastTimer = null;

	function initSocialProofToasts() {
		// Skip social proof toasts on checkout page — WCAG 2.2.2 compliance.
		if (document.body.classList.contains('woocommerce-checkout')) return;

		if (!toastContainer) {
			toastContainer = createElement('div', 'cie-toast-container');
			toastContainer.setAttribute('aria-live', 'polite');
			toastContainer.setAttribute('role', 'status');
			document.body.appendChild(toastContainer);
		}

		// Show first toast after a delay. Clear existing timer if double-init.
		if (toastTimer) clearTimeout(toastTimer);
		toastTimer = setTimeout(showNextToast, 6000);

		// Pause toast cycle when tab is hidden to avoid DOM accumulation.
		document.addEventListener('visibilitychange', function () {
			if (document.hidden) {
				if (toastTimer) { clearTimeout(toastTimer); toastTimer = null; }
			} else if (!toastTimer) {
				toastTimer = setTimeout(showNextToast, CONFIG.toastInterval);
			}
		});
	}

	function showNextToast() {
		var msg = SOCIAL_PROOF_MESSAGES[toastIndex % SOCIAL_PROOF_MESSAGES.length];
		toastIndex++;

		var iconContent = msg.type === 'purchase' ? '\u{1F6CD}' :
		                  msg.type === 'trending' ? '\u{1F525}' : '\u{1F441}';

		var toast = createElement('div', 'cie-toast');

		var icon = createElement('div', 'cie-toast__icon cie-toast__icon--' + msg.type);
		icon.textContent = iconContent;

		var body = createElement('div', 'cie-toast__body');
		var title = createElement('div', 'cie-toast__title');
		title.textContent = msg.title;
		var meta = createElement('div', 'cie-toast__meta');
		meta.textContent = msg.meta;
		body.appendChild(title);
		body.appendChild(meta);

		var close = createElement('button', 'cie-toast__close', {
			'type': 'button',
			'aria-label': 'Dismiss notification',
			'textContent': '\u00D7'
		});
		close.addEventListener('click', function () {
			dismissToast(toast);
		});

		toast.appendChild(icon);
		toast.appendChild(body);
		toast.appendChild(close);
		toastContainer.appendChild(toast);

		// Animate in
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				toast.classList.add('visible');
			});
		});

		// Track the event
		trackEvent('social_proof_shown', { type: msg.type });

		// Auto-dismiss
		setTimeout(function () {
			dismissToast(toast);
		}, CONFIG.toastDuration);

		// Schedule next
		toastTimer = setTimeout(showNextToast, CONFIG.toastInterval);
	}

	function dismissToast(toast) {
		if (!toast || !toast.parentNode) return;
		toast.classList.remove('visible');
		toast.classList.add('exiting');
		setTimeout(function () {
			if (toast.parentNode) toast.parentNode.removeChild(toast);
		}, 500);
	}

	/* --------------------------------------------------
	   2. Live Viewer Counter
	   -------------------------------------------------- */

	function initLiveViewerCounter() {
		var targets = document.querySelectorAll('[data-cie-viewers]');
		if (targets.length === 0) return;

		targets.forEach(function (target) {
			var baseCount = parseInt(target.dataset.cieViewers, 10) || CONFIG.viewerBase;
			var count = baseCount + randomInt(0, CONFIG.viewerVariance);

			var viewer = createElement('div', 'cie-viewers');
			var dot = createElement('span', 'cie-viewers__dot');
			var countEl = createElement('span', 'cie-viewers__count');
			countEl.textContent = count + ' viewing now';
			viewer.appendChild(dot);
			viewer.appendChild(countEl);
			target.appendChild(viewer);

			// Update periodically — store reference for cleanup.
			var viewerInt = setInterval(function () {
				var delta = randomInt(-3, 4);
				count = Math.max(baseCount - 5, Math.min(baseCount + CONFIG.viewerVariance + 5, count + delta));
				countEl.textContent = count + ' viewing now';
				countEl.classList.add('bumped');
				setTimeout(function () {
					countEl.classList.remove('bumped');
				}, 300);
			}, CONFIG.viewerUpdateInterval);
			cleanupIntervals.push(viewerInt);
		});
	}

	/* --------------------------------------------------
	   3. Urgency Countdown Timer
	   -------------------------------------------------- */

	function initUrgencyCountdown() {
		var targets = document.querySelectorAll('[data-cie-countdown]');
		if (targets.length === 0) return;

		targets.forEach(function (target) {
			var endStr = target.dataset.cieCountdown;
			var endDate;

			if (endStr === 'auto') {
				// Auto-generate: midnight tomorrow
				endDate = new Date();
				endDate.setDate(endDate.getDate() + 1);
				endDate.setHours(0, 0, 0, 0);
			} else {
				endDate = new Date(endStr);
			}

			if (isNaN(endDate.getTime())) return;

			var label = createElement('span', 'cie-countdown__label');
			label.textContent = target.dataset.cieCountdownLabel || 'Pre-Order Closes In';

			var segments = ['days', 'hours', 'mins', 'secs'].map(function (unit) {
				var seg = createElement('span', 'cie-countdown__segment');
				var val = createElement('span', 'cie-countdown__value');
				val.dataset.unit = unit;
				val.textContent = '00';
				var unitLabel = createElement('span', 'cie-countdown__unit');
				unitLabel.textContent = unit;
				seg.appendChild(val);
				seg.appendChild(unitLabel);
				return seg;
			});

			var countdown = createElement('div', 'cie-countdown');
			countdown.appendChild(label);

			segments.forEach(function (seg, i) {
				countdown.appendChild(seg);
				if (i < segments.length - 1) {
					var colon = createElement('span', 'cie-countdown__colon');
					colon.textContent = ':';
					countdown.appendChild(colon);
				}
			});

			target.appendChild(countdown);

			function updateCountdown() {
				var now = Date.now();
				var diff = Math.max(0, endDate.getTime() - now);

				var days = Math.floor(diff / 86400000);
				var hours = Math.floor((diff % 86400000) / 3600000);
				var mins = Math.floor((diff % 3600000) / 60000);
				var secs = Math.floor((diff % 60000) / 1000);

				countdown.querySelector('[data-unit="days"]').textContent = String(days).padStart(2, '0');
				countdown.querySelector('[data-unit="hours"]').textContent = String(hours).padStart(2, '0');
				countdown.querySelector('[data-unit="mins"]').textContent = String(mins).padStart(2, '0');
				countdown.querySelector('[data-unit="secs"]').textContent = String(secs).padStart(2, '0');

				// Add urgent class when < 1 hour
				if (diff > 0 && diff < 3600000) {
					countdown.classList.add('urgent');
				} else {
					countdown.classList.remove('urgent');
				}

				if (diff > 0) {
					requestAnimationFrame(function () {
						setTimeout(updateCountdown, 1000);
					});
				}
			}

			updateCountdown();
		});
	}

	/* --------------------------------------------------
	   4. Stock Scarcity Indicator
	   -------------------------------------------------- */

	function initStockScarcity() {
		var targets = document.querySelectorAll('[data-cie-stock]');
		if (targets.length === 0) return;

		targets.forEach(function (target) {
			var sku = target.dataset.cieStock;
			var maxStock = parseInt(target.dataset.cieStockMax, 10) || 50;
			var remaining = CONFIG.stockLevels[sku] || randomInt(3, 20);
			var pct = Math.min(100, (remaining / maxStock) * 100);

			var level = remaining <= 5 ? 'critical' : remaining <= 15 ? 'low' : 'moderate';

			var container = createElement('div', 'cie-scarcity');

			var bar = createElement('div', 'cie-scarcity__bar');
			var fill = createElement('div', 'cie-scarcity__fill cie-scarcity__fill--' + level);
			fill.style.width = '0%';
			bar.appendChild(fill);

			var text = createElement('span', 'cie-scarcity__text cie-scarcity__text--' + level);
			text.textContent = remaining <= 5 ? 'Only ' + remaining + ' left!' :
			                   remaining <= 15 ? remaining + ' remaining' :
			                   'In stock';

			container.appendChild(bar);
			container.appendChild(text);
			target.appendChild(container);

			// Animate fill
			requestAnimationFrame(function () {
				requestAnimationFrame(function () {
					fill.style.width = pct + '%';
				});
			});
		});
	}

	/* --------------------------------------------------
	   5. Floating Pre-Order CTA
	   -------------------------------------------------- */

	function initFloatingCTA() {
		// Only on pages that have a pre-order section
		var hasPreorder = document.querySelector('.collection-preorder-cta') ||
		                  document.querySelector('.preorder-gateway') ||
		                  document.querySelector('.immersive-page');
		if (!hasPreorder) return;

		var bar = createElement('div', 'cie-floating-cta');

		var text = createElement('span', 'cie-floating-cta__text');
		text.innerHTML = '<strong>' + CONFIG.preorderCurrent + '</strong> pre-orders placed — join them';

		var btn = createElement('a', 'cie-floating-cta__btn', {
			'href': '/pre-order/',
			'textContent': 'Pre-Order Now'
		});

		bar.appendChild(text);
		bar.appendChild(btn);
		document.body.appendChild(bar);

		var visible = false;
		var ticking = false;

		function onScroll() {
			if (ticking) return;
			ticking = true;
			requestAnimationFrame(function () {
				var scrollY = window.pageYOffset || document.documentElement.scrollTop;
				if (scrollY > CONFIG.floatingCTAThreshold && !visible) {
					bar.classList.add('visible');
					visible = true;
					trackEvent('floating_cta_shown');
				} else if (scrollY <= CONFIG.floatingCTAThreshold && visible) {
					bar.classList.remove('visible');
					visible = false;
				}
				ticking = false;
			});
		}

		window.addEventListener('scroll', onScroll, { passive: true });

		btn.addEventListener('click', function () {
			trackEvent('floating_cta_clicked');
		});
	}

	/* --------------------------------------------------
	   6. Exit-Intent Detection
	   -------------------------------------------------- */

	function initExitIntent() {
		// Desktop only, and respect cooldown
		var isTouchDevice = window.matchMedia('(hover: none)').matches;
		if (isTouchDevice) return;

		var lastShown = 0;
		try {
			lastShown = parseInt(sessionStorage.getItem('cie_exit_shown') || '0', 10);
		} catch (e) { /* quota */ }

		if (Date.now() - lastShown < CONFIG.exitIntentCooldown) return;

		var triggered = false;

		document.addEventListener('mouseout', function (e) {
			if (triggered) return;
			if (e.clientY > 10) return; // Not leaving from top

			triggered = true;
			showExitOverlay();
		});
	}

	function showExitOverlay() {
		var overlay = createElement('div', 'cie-exit-overlay');

		var modal = createElement('div', 'cie-exit-modal');

		var close = createElement('button', 'cie-exit-modal__close', {
			'type': 'button',
			'aria-label': 'Close',
			'textContent': '\u00D7'
		});

		var monogram = createElement('div', 'cie-exit-modal__monogram');
		monogram.textContent = 'SR';

		var headline = createElement('h2', 'cie-exit-modal__headline');
		headline.textContent = 'Wait — Your Cart Misses You';

		var subtext = createElement('p', 'cie-exit-modal__subtext');
		subtext.textContent = 'Pre-order slots are filling fast. Secure your pieces from the collection before they\'re gone. Luxury Grows from Concrete.';

		var cta = createElement('a', 'cie-exit-modal__cta', {
			'href': '/pre-order/',
			'textContent': 'View Pre-Order'
		});

		var dismiss = createElement('button', 'cie-exit-modal__dismiss', {
			'type': 'button',
			'textContent': 'No thanks, I\'ll keep browsing'
		});

		modal.appendChild(close);
		modal.appendChild(monogram);
		modal.appendChild(headline);
		modal.appendChild(subtext);
		modal.appendChild(cta);
		modal.appendChild(dismiss);
		overlay.appendChild(modal);
		document.body.appendChild(overlay);

		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				overlay.classList.add('visible');
			});
		});

		trackEvent('exit_intent_shown');

		function closeOverlay() {
			overlay.classList.remove('visible');
			setTimeout(function () {
				if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
			}, 400);
			try {
				sessionStorage.setItem('cie_exit_shown', String(Date.now()));
			} catch (e) { /* quota */ }
		}

		close.addEventListener('click', closeOverlay);
		dismiss.addEventListener('click', closeOverlay);
		overlay.addEventListener('click', function (e) {
			if (e.target === overlay) closeOverlay();
		});

		cta.addEventListener('click', function () {
			trackEvent('exit_intent_converted');
		});
	}

	/* --------------------------------------------------
	   7. Preorder Progress Bar
	   -------------------------------------------------- */

	function initPreorderProgress() {
		var targets = document.querySelectorAll('[data-cie-preorder-progress]');
		if (targets.length === 0) return;

		targets.forEach(function (target) {
			var current = CONFIG.preorderCurrent;
			var goal = CONFIG.preorderGoal;
			var pct = Math.min(100, (current / goal) * 100);

			var container = createElement('div', 'cie-preorder-progress');

			var header = createElement('div', 'cie-preorder-progress__header');
			var label = createElement('span', 'cie-preorder-progress__label');
			label.textContent = 'Pre-Order Progress';
			var count = createElement('span', 'cie-preorder-progress__count');
			count.textContent = current + ' / ' + goal + ' goal';
			header.appendChild(label);
			header.appendChild(count);

			var bar = createElement('div', 'cie-preorder-progress__bar');
			var fill = createElement('div', 'cie-preorder-progress__fill');
			fill.style.width = '0%';
			bar.appendChild(fill);

			container.appendChild(header);
			container.appendChild(bar);
			target.appendChild(container);

			// Animate on view
			var observer = new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						fill.style.width = pct.toFixed(1) + '%';
						observer.disconnect();
					}
				});
			}, { threshold: 0.3 });

			observer.observe(container);
		});
	}

	/* --------------------------------------------------
	   8. Room Viewer Counter (Immersive Pages)
	   -------------------------------------------------- */

	function initRoomViewers() {
		var scene = document.querySelector('.immersive-scene');
		if (!scene) return;

		var count = CONFIG.viewerBase + randomInt(5, CONFIG.viewerVariance);
		var roomViewers = createElement('div', 'cie-room-viewers');
		var dot = createElement('span', 'cie-room-viewers__dot');
		var text = document.createTextNode(' ' + count + ' exploring right now');
		roomViewers.appendChild(dot);
		roomViewers.appendChild(text);
		scene.appendChild(roomViewers);

		// Update periodically — store reference for cleanup.
		var roomInt = setInterval(function () {
			var delta = randomInt(-2, 3);
			count = Math.max(CONFIG.viewerBase - 3, count + delta);
			while (roomViewers.childNodes.length > 1) {
				roomViewers.removeChild(roomViewers.lastChild);
			}
			roomViewers.appendChild(document.createTextNode(' ' + count + ' exploring right now'));
		}, CONFIG.viewerUpdateInterval);
		cleanupIntervals.push(roomInt);
	}

	/* --------------------------------------------------
	   9. Confidence Bar
	   -------------------------------------------------- */

	function initConfidenceBar() {
		var targets = document.querySelectorAll('[data-cie-confidence]');
		if (targets.length === 0) return;

		var signals = [
			{ icon: '\u{1F512}', text: 'Secure Checkout' },
			{ icon: '\u{1F4E6}', text: 'Free Shipping' },
			{ icon: '\u{1F504}', text: 'Easy Returns' },
			{ icon: '\u2705', text: 'Authentic Guarantee' },
		];

		targets.forEach(function (target) {
			var bar = createElement('div', 'cie-confidence');
			signals.forEach(function (signal) {
				var item = createElement('span', 'cie-confidence__item');
				var icon = createElement('span', 'cie-confidence__icon');
				icon.textContent = signal.icon;
				item.appendChild(icon);
				item.appendChild(document.createTextNode(signal.text));
				bar.appendChild(item);
			});
			target.appendChild(bar);
		});
	}

	/* --------------------------------------------------
	   10. Conversion Event Tracker
	   -------------------------------------------------- */

	var eventQueue = [];

	function trackEvent(eventName, data) {
		var event = {
			event: eventName,
			timestamp: new Date().toISOString(),
			page: window.location.pathname,
			data: data || {},
		};
		eventQueue.push(event);

		// Dispatch custom event for external listeners
		try {
			window.dispatchEvent(new CustomEvent('cie:event', { detail: event }));
		} catch (e) { /* old browsers */ }
	}

	// Expose for external use
	window.SkyyRoseCIE = {
		trackEvent: trackEvent,
		getEvents: function () { return eventQueue.slice(); },
		config: CONFIG,
	};

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initSocialProofToasts();
		initLiveViewerCounter();
		initUrgencyCountdown();
		initStockScarcity();
		initFloatingCTA();
		initExitIntent();
		initPreorderProgress();
		initRoomViewers();
		initConfidenceBar();

		trackEvent('conversion_engine_loaded');
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
