/**
 * Analytics Beacon — Unified Event Relay
 *
 * Collects conversion events from ALL SkyyRose engines (CIE, Aurora,
 * Pulse, Magnetic Obsidian, Cross-Sell, Journey Gamification, APE)
 * and batches them to the devskyy.app analytics API.
 *
 * Features:
 *   - Batched sends (max 20 events per flush, 10s intervals)
 *   - navigator.sendBeacon for reliable page-unload delivery
 *   - Session ID tracking for unique visitor counting
 *   - Automatic page-view and scroll-depth events
 *   - Listens for cie:event custom events from all engines
 *
 * No dependencies. Vanilla JS.
 *
 * @package SkyyRose_Flagship
 * @since   3.9.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CFG = {
		endpoint:       '/api/conversion',
		flushInterval:  10000,   // 10s between flushes
		maxBatchSize:   20,      // max events per send
		maxQueueSize:   200,     // prevent unbounded growth
		scrollSampleMs: 5000,    // throttle scroll depth reports
		sessionKey:     'sr_analytics_session',
	};

	/* --------------------------------------------------
	   Session Management
	   -------------------------------------------------- */

	var sessionId = '';

	function getSessionId() {
		if (sessionId) return sessionId;
		try {
			sessionId = sessionStorage.getItem(CFG.sessionKey) || '';
			if (!sessionId) {
				sessionId = 'ses_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
				sessionStorage.setItem(CFG.sessionKey, sessionId);
			}
		} catch (e) {
			sessionId = 'ses_' + Date.now().toString(36);
		}
		return sessionId;
	}

	/* --------------------------------------------------
	   Event Queue
	   -------------------------------------------------- */

	var queue = [];

	function enqueue(eventName, data, source) {
		if (queue.length >= CFG.maxQueueSize) {
			queue.shift(); // FIFO eviction
		}

		var enrichedData = data || {};
		enrichedData.session_id = getSessionId();

		// Detect collection from page
		var path = window.location.pathname;
		if (!enrichedData.collection) {
			if (path.indexOf('black-rose') !== -1) enrichedData.collection = 'black-rose';
			else if (path.indexOf('love-hurts') !== -1) enrichedData.collection = 'love-hurts';
			else if (path.indexOf('signature') !== -1) enrichedData.collection = 'signature';
		}

		queue.push({
			event: eventName,
			timestamp: new Date().toISOString(),
			page: path,
			source: source || 'beacon',
			data: enrichedData,
		});
	}

	/* --------------------------------------------------
	   Flush — Send batched events to API
	   -------------------------------------------------- */

	function flush() {
		if (queue.length === 0) return;

		var batch = queue.splice(0, CFG.maxBatchSize);
		var payload = JSON.stringify({ events: batch });

		// Use sendBeacon for reliability (works during page unload)
		if (navigator.sendBeacon) {
			var sent = navigator.sendBeacon(CFG.endpoint, new Blob([payload], { type: 'application/json' }));
			if (!sent) {
				// Beacon failed — re-queue (at front)
				queue.unshift.apply(queue, batch);
			}
		} else {
			// Fallback: XHR fire-and-forget
			var xhr = new XMLHttpRequest();
			xhr.open('POST', CFG.endpoint, true);
			xhr.setRequestHeader('Content-Type', 'application/json');
			xhr.send(payload);
		}
	}

	/* --------------------------------------------------
	   Auto Page View
	   -------------------------------------------------- */

	function trackPageView() {
		enqueue('page_view', {
			referrer: document.referrer || '',
			title: document.title,
			screen_width: window.innerWidth,
		});
	}

	/* --------------------------------------------------
	   Scroll Depth Tracking
	   -------------------------------------------------- */

	function initScrollTracking() {
		var maxDepth = 0;
		var lastReported = 0;
		var docHeight = 0;

		function updateDocHeight() {
			docHeight = Math.max(
				document.body.scrollHeight,
				document.documentElement.scrollHeight,
				1
			);
		}

		updateDocHeight();

		window.addEventListener('scroll', function () {
			var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
			var viewportHeight = window.innerHeight;
			var depth = Math.min(100, Math.round(((scrollTop + viewportHeight) / docHeight) * 100));

			if (depth > maxDepth) {
				maxDepth = depth;
			}

			var now = Date.now();
			if (now - lastReported > CFG.scrollSampleMs && maxDepth > 0) {
				enqueue('scroll_depth', { depth: maxDepth });
				lastReported = now;
			}
		}, { passive: true });
	}

	/* --------------------------------------------------
	   Time on Page Tracking
	   -------------------------------------------------- */

	function initTimeTracking() {
		var startTime = Date.now();

		function reportTime() {
			var seconds = Math.round((Date.now() - startTime) / 1000);
			enqueue('time_on_page', { seconds: seconds });
		}

		// Report every 30 seconds
		setInterval(reportTime, 30000);

		// Report on page unload
		window.addEventListener('beforeunload', reportTime);
	}

	/* --------------------------------------------------
	   Listen to CIE Events (from all conversion engines)
	   -------------------------------------------------- */

	function initCIEListener() {
		window.addEventListener('cie:event', function (e) {
			if (e.detail && e.detail.event) {
				enqueue(e.detail.event, e.detail.data || {}, 'cie');
			}
		});
	}

	/* --------------------------------------------------
	   Listen to Cross-Sell Events
	   -------------------------------------------------- */

	function initCrossSellListener() {
		// Monitor Cross-Sell analytics object changes
		if (window.SkyyRoseCrossSell) {
			var origRefresh = window.SkyyRoseCrossSell.refresh;
			window.SkyyRoseCrossSell.refresh = function () {
				enqueue('cross_sell_shown', {
					panel_views: window.SkyyRoseCrossSell.analytics.panelViews,
				}, 'cross-sell');
				if (origRefresh) origRefresh.call(window.SkyyRoseCrossSell);
			};
		}
	}

	/* --------------------------------------------------
	   Hotspot Click Tracking
	   -------------------------------------------------- */

	function initHotspotTracking() {
		document.addEventListener('click', function (e) {
			var hotspot = e.target.closest ? e.target.closest('.hotspot') : null;
			if (!hotspot) return;

			enqueue('hotspot_click', {
				sku: hotspot.dataset.productId || '',
				product: hotspot.dataset.productName || '',
				price: hotspot.dataset.productPrice || '',
				collection: hotspot.dataset.productCollection || '',
			}, 'immersive');
		});
	}

	/* --------------------------------------------------
	   Room Transition Tracking
	   -------------------------------------------------- */

	function initRoomTracking() {
		var scene = document.querySelector('.immersive-scene');
		if (!scene) return;

		// Watch for room dot clicks
		var dots = scene.querySelectorAll('.room-dot');
		dots.forEach(function (dot) {
			dot.addEventListener('click', function () {
				enqueue('room_transition', {
					room: dot.getAttribute('aria-label') || '',
				}, 'immersive');
			});
		});

		// Watch for nav button clicks
		var navBtns = scene.querySelectorAll('.room-nav-btn');
		navBtns.forEach(function (btn) {
			btn.addEventListener('click', function () {
				enqueue('room_transition', {}, 'immersive');
			});
		});
	}

	/* --------------------------------------------------
	   Product Panel Open Tracking
	   -------------------------------------------------- */

	function initPanelTracking() {
		var panel = document.querySelector('.product-panel');
		if (!panel) return;

		var observer = new MutationObserver(function (mutations) {
			mutations.forEach(function (mutation) {
				if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
					if (panel.classList.contains('open')) {
						var nameEl = panel.querySelector('.product-panel-name');
						var priceEl = panel.querySelector('.product-panel-price');
						enqueue('panel_open', {
							product: nameEl ? nameEl.textContent : '',
							price: priceEl ? priceEl.textContent : '',
							heat_score: 5,
						}, 'immersive');
					}
				}
			});
		});

		observer.observe(panel, { attributes: true, attributeFilter: ['class'] });
	}

	/* --------------------------------------------------
	   Add to Cart Tracking
	   -------------------------------------------------- */

	function initCartTracking() {
		document.addEventListener('click', function (e) {
			var btn = e.target.closest ? e.target.closest('.btn-add-to-cart') : null;
			if (!btn) return;

			var panel = document.querySelector('.product-panel');
			var nameEl = panel ? panel.querySelector('.product-panel-name') : null;
			var priceEl = panel ? panel.querySelector('.product-panel-price') : null;

			enqueue('add_to_cart', {
				product: nameEl ? nameEl.textContent : '',
				price: priceEl ? priceEl.textContent : '',
			}, 'immersive');
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		// Skip on admin pages
		if (document.body.classList.contains('wp-admin')) return;

		trackPageView();
		initScrollTracking();
		initTimeTracking();
		initCIEListener();
		initCrossSellListener();
		initHotspotTracking();
		initRoomTracking();
		initPanelTracking();
		initCartTracking();

		// Periodic flush
		setInterval(flush, CFG.flushInterval);

		// Flush on page unload
		window.addEventListener('beforeunload', flush);

		// Flush on visibility change (tab switch)
		document.addEventListener('visibilitychange', function () {
			if (document.visibilityState === 'hidden') {
				flush();
			}
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
