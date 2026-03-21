/**
 * Experience Analyzer — Behavioral Data Collection
 *
 * Privacy-first tracking: no PII, no cookies, sessionStorage only.
 * Batches events (max 20, 5s flush interval, sendBeacon on unload).
 * Follows the pattern from the theme's analytics-beacon.js.
 *
 * Tracks:
 *   - Scroll depth (%) per page
 *   - Hover targets (CSS selector of hovered products/CTAs)
 *   - Click paths (ordered sequence of clicked elements)
 *   - Time-on-page (seconds)
 *   - Exit intent (mouse leaving viewport top)
 *   - Product interactions (view, hover, quick-view, add-to-cart)
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
	   Config
	   ========================================================================== */

	var CONFIG = {
		batchSize:      20,
		flushInterval:  5000,    // 5s
		maxScrollDepth: 0,
		pageLoadTime:   Date.now(),
	};

	var ctx = SEE.getContext();
	var eventQueue = [];
	var flushTimer = null;

	/* ==========================================================================
	   Event Tracking
	   ========================================================================== */

	function trackEvent(type, target, value) {
		eventQueue.push({
			type:       type,
			target:     target || '',
			value:      value || 0,
			pageType:   ctx.pageType,
			collection: ctx.collection,
			ts:         Date.now(),
		});

		if (eventQueue.length >= CONFIG.batchSize) {
			flush();
		}
	}

	/* ==========================================================================
	   Scroll Depth Tracking
	   ========================================================================== */

	var lastScrollDepth = 0;

	function onScroll() {
		var scrollTop    = window.pageYOffset || document.documentElement.scrollTop;
		var docHeight    = document.documentElement.scrollHeight - window.innerHeight;
		var scrollDepth  = docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;

		if (scrollDepth > CONFIG.maxScrollDepth) {
			CONFIG.maxScrollDepth = scrollDepth;
		}

		// Track at 25% increments.
		var milestone = Math.floor(scrollDepth / 25) * 25;
		if (milestone > lastScrollDepth && milestone > 0) {
			lastScrollDepth = milestone;
			trackEvent('scroll_depth', 'page', milestone);
			SEE.emit('behavior:scroll', { depth: scrollDepth, milestone: milestone });
		}
	}

	/* ==========================================================================
	   Hover Tracking — Product cards and CTAs only
	   ========================================================================== */

	var hoverTimer = null;

	function onMouseOver(e) {
		var target = e.target.closest('[data-see-track], .product, .woocommerce-loop-product__link, [data-product-id]');
		if (!target) {
			return;
		}

		hoverTimer = setTimeout(function () {
			var identifier = target.getAttribute('data-see-track')
				|| target.getAttribute('data-product-id')
				|| target.className.split(' ')[0]
				|| 'unknown';

			trackEvent('hover', identifier, 1);
			SEE.emit('behavior:hover', { target: identifier, element: target });
		}, 500); // Only track if hovered for 500ms+.
	}

	function onMouseOut() {
		if (hoverTimer) {
			clearTimeout(hoverTimer);
			hoverTimer = null;
		}
	}

	/* ==========================================================================
	   Click Path Tracking
	   ========================================================================== */

	function onClick(e) {
		var target = e.target.closest('a, button, [data-see-track], .product, input[type="submit"]');
		if (!target) {
			return;
		}

		var identifier = target.getAttribute('data-see-track')
			|| target.getAttribute('data-product-id')
			|| target.textContent.trim().substring(0, 30)
			|| target.tagName.toLowerCase();

		trackEvent('click', identifier, 1);
		SEE.emit('behavior:click', { target: identifier, element: target });
	}

	/* ==========================================================================
	   Exit Intent Detection
	   ========================================================================== */

	function onMouseLeave(e) {
		if (e.clientY <= 0) {
			trackEvent('exit_intent', 'top', 1);
			SEE.emit('behavior:exit_intent', { direction: 'top' });
		}
	}

	/* ==========================================================================
	   Flush — Send batched events to REST API
	   ========================================================================== */

	function flush() {
		if (eventQueue.length === 0) {
			return;
		}

		var batch = eventQueue.splice(0, CONFIG.batchSize);
		var config = SEE.getConfig();
		var url = (config.restUrl || '/wp-json/see/v1/') + 'analytics/events';

		var payload = JSON.stringify({
			events: batch,
			sessionDuration: Math.round((Date.now() - CONFIG.pageLoadTime) / 1000),
			maxScrollDepth: CONFIG.maxScrollDepth,
		});

		// Prefer sendBeacon for reliability; fall back to fetch.
		if (navigator.sendBeacon) {
			navigator.sendBeacon(url, new Blob([payload], { type: 'application/json' }));
		} else {
			fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-WP-Nonce': config.restNonce || '',
				},
				body: payload,
				keepalive: true,
			}).catch(function () {
				// Network failure — events are lost. Acceptable for analytics.
			});
		}
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('experience-analyzer', {
		init: function () {
			// Start flush interval.
			flushTimer = setInterval(flush, CONFIG.flushInterval);
		},

		ready: function () {
			// Bind event listeners.
			window.addEventListener('scroll', onScroll, { passive: true });
			document.addEventListener('mouseover', onMouseOver, { passive: true });
			document.addEventListener('mouseout', onMouseOut, { passive: true });
			document.addEventListener('click', onClick, { passive: true });
			document.documentElement.addEventListener('mouseleave', onMouseLeave);

			// Track initial page view.
			trackEvent('page_view', ctx.pageType, 1);

			// Track product view if on a product page.
			if (ctx.productSku) {
				trackEvent('product_view', ctx.productSku, 1);
			}

			// Listen for WooCommerce add-to-cart events.
			document.body.addEventListener('added_to_cart', function () {
				trackEvent('add_to_cart', ctx.productSku || 'unknown', 1);
			});
		},

		destroy: function () {
			// Final flush.
			trackEvent('session_end', 'page', Math.round((Date.now() - CONFIG.pageLoadTime) / 1000));
			flush();

			if (flushTimer) {
				clearInterval(flushTimer);
			}
			window.removeEventListener('scroll', onScroll);
			document.removeEventListener('mouseover', onMouseOver);
			document.removeEventListener('mouseout', onMouseOut);
			document.removeEventListener('click', onClick);
			document.documentElement.removeEventListener('mouseleave', onMouseLeave);
		},
	});

	/* ==========================================================================
	   Beacon on unload — ensure final events are sent
	   ========================================================================== */

	window.addEventListener('beforeunload', function () {
		trackEvent('page_exit', 'page', CONFIG.maxScrollDepth);
		flush();
	});

})();
