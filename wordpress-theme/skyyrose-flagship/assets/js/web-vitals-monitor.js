/**
 * Web Vitals Performance Monitor
 *
 * Tracks Core Web Vitals (LCP, FID/INP, CLS) using the native
 * PerformanceObserver API. Metrics are logged to the console in
 * development and sent to an analytics endpoint in production.
 *
 * Google uses these three metrics for search ranking (Page Experience
 * update). Monitoring them client-side lets the theme team catch
 * regressions before they affect SEO.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	// Only run in browsers that support PerformanceObserver.
	if (typeof PerformanceObserver === 'undefined') {
		return;
	}

	var vitals = {};
	var isDev = (typeof skyyRoseData !== 'undefined' && skyyRoseData.debug) ||
	            location.hostname === 'localhost' ||
	            location.hostname.indexOf('.local') !== -1;

	/**
	 * Log or send a metric.
	 */
	function reportMetric(name, value, rating) {
		vitals[name] = { value: Math.round(value * 100) / 100, rating: rating };

		if (isDev) {
			var style = rating === 'good' ? 'color:#0cce6b' :
			            rating === 'needs-improvement' ? 'color:#ffa400' : 'color:#ff4e42';
			console.log(
				'%c[WebVitals] ' + name + ': ' + vitals[name].value +
				(name === 'CLS' ? '' : 'ms') + ' (' + rating + ')',
				style + ';font-weight:bold'
			);
		}

		// Production: send to analytics endpoint if available.
		if (!isDev && typeof skyyRoseData !== 'undefined' && skyyRoseData.vitalsEndpoint) {
			var payload = JSON.stringify({
				metric: name,
				value: vitals[name].value,
				rating: rating,
				page: location.pathname,
				timestamp: Date.now()
			});

			if (navigator.sendBeacon) {
				navigator.sendBeacon(skyyRoseData.vitalsEndpoint, payload);
			}
		}
	}

	/**
	 * Rate a metric against Google's thresholds.
	 */
	function rateLCP(ms)  { return ms <= 2500 ? 'good' : ms <= 4000 ? 'needs-improvement' : 'poor'; }
	function rateFID(ms)  { return ms <= 100  ? 'good' : ms <= 300  ? 'needs-improvement' : 'poor'; }
	function rateINP(ms)  { return ms <= 200  ? 'good' : ms <= 500  ? 'needs-improvement' : 'poor'; }
	function rateCLS(val) { return val <= 0.1  ? 'good' : val <= 0.25 ? 'needs-improvement' : 'poor'; }

	// --- Largest Contentful Paint (LCP) ---
	try {
		var lcpObserver = new PerformanceObserver(function (list) {
			var entries = list.getEntries();
			var last = entries[entries.length - 1];
			reportMetric('LCP', last.startTime, rateLCP(last.startTime));
		});
		lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
	} catch (e) { /* unsupported */ }

	// --- First Input Delay (FID) ---
	try {
		var fidObserver = new PerformanceObserver(function (list) {
			var entry = list.getEntries()[0];
			reportMetric('FID', entry.processingStart - entry.startTime,
				rateFID(entry.processingStart - entry.startTime));
		});
		fidObserver.observe({ type: 'first-input', buffered: true });
	} catch (e) { /* unsupported */ }

	// --- Interaction to Next Paint (INP) — replaces FID in 2024+ ---
	try {
		var inpMax = 0;
		var inpObserver = new PerformanceObserver(function (list) {
			var entries = list.getEntries();
			for (var i = 0; i < entries.length; i++) {
				var duration = entries[i].duration;
				if (duration > inpMax) {
					inpMax = duration;
				}
			}
		});
		inpObserver.observe({ type: 'event', buffered: true, durationThreshold: 16 });

		// Report INP on page hide (captures full session).
		document.addEventListener('visibilitychange', function () {
			if (document.visibilityState === 'hidden' && inpMax > 0) {
				reportMetric('INP', inpMax, rateINP(inpMax));
			}
		});
	} catch (e) { /* unsupported */ }

	// --- Cumulative Layout Shift (CLS) ---
	try {
		var clsValue = 0;
		var clsEntries = [];
		var sessionValue = 0;
		var sessionEntries = [];

		var clsObserver = new PerformanceObserver(function (list) {
			var entries = list.getEntries();
			for (var i = 0; i < entries.length; i++) {
				// Only count layout shifts without recent user input.
				if (!entries[i].hadRecentInput) {
					var firstSessionEntry = sessionEntries[0];
					var lastSessionEntry = sessionEntries[sessionEntries.length - 1];

					// Start new session window if gap > 1s or window > 5s.
					if (sessionEntries.length > 0 &&
						(entries[i].startTime - lastSessionEntry.startTime > 1000 ||
						 entries[i].startTime - firstSessionEntry.startTime > 5000)) {
						if (sessionValue > clsValue) {
							clsValue = sessionValue;
						}
						sessionEntries = [];
						sessionValue = 0;
					}

					sessionEntries.push(entries[i]);
					sessionValue += entries[i].value;
				}
			}
		});
		clsObserver.observe({ type: 'layout-shift', buffered: true });

		// Report CLS on page hide.
		document.addEventListener('visibilitychange', function () {
			if (document.visibilityState === 'hidden') {
				if (sessionValue > clsValue) {
					clsValue = sessionValue;
				}
				if (clsValue > 0) {
					reportMetric('CLS', clsValue, rateCLS(clsValue));
				}
			}
		});
	} catch (e) { /* unsupported */ }

})();
