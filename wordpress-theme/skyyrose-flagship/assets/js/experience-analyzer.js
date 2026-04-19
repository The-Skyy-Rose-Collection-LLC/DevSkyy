/**
 * Experience Analyzer — Behavioral Tracking & Event Relay
 *
 * Part of the SkyyRose Experience Engine, Phase 3.
 *
 * Tracks user interactions with product cards and relays them in batches
 * to the Experience Engine REST API (Phase 1) for analytics and
 * personalization scoring.
 *
 * Events tracked:
 *   product_view      — card enters the viewport (IntersectionObserver)
 *   product_dwell     — user hovers a card ≥ 800ms
 *   product_click     — any card CTA click (buy, wishlist, quickview)
 *   product_quickview — quick-view dialog opened
 *
 * Batching strategy:
 *   - Events queue in memory
 *   - Flush every 30 seconds
 *   - Flush on page unload via navigator.sendBeacon (no XHR blocking)
 *
 * @module experience-analyzer
 * @since  6.4.0
 */
(function () {
  'use strict';

  var FLUSH_INTERVAL = 30000; // 30 seconds
  var DWELL_THRESHOLD = 800; // ms before hover counts as dwell

  var queue = [];
  var dwellTimers = {};

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function getCardData(el) {
    var article = el.closest('[data-product-id]');
    if (!article) return null;
    return {
      product_id: article.dataset.productId || '',
      sku: article.dataset.sku || '',
      collection: article.dataset.collection || '',
    };
  }

  function push(type, data) {
    // Field names MUST match the REST handler contract in
    // inc/experience-analyzer.php: skyyrose_see_store_events() reads
    // type, ts, target, pageType, collection, value. Anything else is
    // silently dropped server-side.
    queue.push({
      type: type,
      target: data.sku || data.product_id || '',
      pageType: window.location.pathname,
      collection: data.collection || '',
      value: 0,
      ts: Date.now(),
    });
  }

  // -------------------------------------------------------------------------
  // Flush
  // -------------------------------------------------------------------------

  function getVisitorHash() {
    // Prefer cookie set server-side by personalization.php.
    var match = document.cookie.match(/(?:^|;\s*)skyy_visitor=([a-f0-9]{16,64})/);
    if (match) return match[1];
    // Fallback: generate and persist in localStorage.
    var stored = localStorage.getItem('skyy_vh');
    if (stored && /^[a-f0-9]{16}$/.test(stored)) return stored;
    var bytes = new Uint8Array(8);
    crypto.getRandomValues(bytes);
    var hash = Array.from(bytes)
      .map(function (b) {
        return b.toString(16).padStart(2, '0');
      })
      .join('');
    localStorage.setItem('skyy_vh', hash);
    return hash;
  }

  function getEndpoint() {
    return '/?rest_route=/skyyrose/v1/analytics/events';
  }

  function buildPayload() {
    return JSON.stringify({
      visitorHash: getVisitorHash(),
      events: queue.splice(0, queue.length), // drain the queue
    });
  }

  function flush(sync) {
    if (queue.length === 0) return;

    var endpoint = getEndpoint();
    var payload = buildPayload();

    // On unload, sendBeacon is non-blocking and reliable.
    if (sync && navigator.sendBeacon) {
      var blob = new Blob([payload], { type: 'application/json' });
      navigator.sendBeacon(endpoint, blob);
      return;
    }

    // Standard flush: fire-and-forget fetch.
    if (typeof fetch !== 'undefined') {
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        credentials: 'same-origin',
        keepalive: true,
      }).catch(function () {
        // Silently drop failed flushes — analytics are non-critical.
      });
    }
  }

  // -------------------------------------------------------------------------
  // Observers & listeners
  // -------------------------------------------------------------------------

  function initViewTracking() {
    if (!('IntersectionObserver' in window)) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var data = getCardData(entry.target);
          if (data) push('product_view', data);
          observer.unobserve(entry.target); // fire once per card per load
        });
      },
      { threshold: 0.5 }
    );

    document.querySelectorAll('[data-product-id]').forEach(function (el) {
      observer.observe(el);
    });
  }

  function initDwellTracking() {
    document.addEventListener(
      'mouseenter',
      function (e) {
        var article = e.target.closest('[data-product-id]');
        if (!article) return;
        var id = article.dataset.productId;
        if (dwellTimers[id]) return;
        dwellTimers[id] = setTimeout(function () {
          var data = getCardData(article);
          if (data) push('product_dwell', data);
          delete dwellTimers[id];
        }, DWELL_THRESHOLD);
      },
      true
    );

    document.addEventListener(
      'mouseleave',
      function (e) {
        var article = e.target.closest('[data-product-id]');
        if (!article) return;
        var id = article.dataset.productId;
        clearTimeout(dwellTimers[id]);
        delete dwellTimers[id];
      },
      true
    );
  }

  function initClickTracking() {
    document.addEventListener('click', function (e) {
      var target = e.target;

      // Add-to-cart
      if (target.closest('.holo__buy')) {
        var data = getCardData(target);
        if (data) push('product_click', Object.assign({}, data, { action: 'add_to_cart' }));
        return;
      }

      // Wishlist
      if (target.closest('.holo__wishlist')) {
        var data = getCardData(target);
        if (data) push('product_click', Object.assign({}, data, { action: 'wishlist' }));
        return;
      }

      // Quick view
      if (target.closest('.holo__quickview')) {
        var data = getCardData(target);
        if (data) push('product_quickview', data);
        return;
      }
    });
  }

  // -------------------------------------------------------------------------
  // Lifecycle
  // -------------------------------------------------------------------------

  function init() {
    initViewTracking();
    initDwellTracking();
    initClickTracking();

    setInterval(flush, FLUSH_INTERVAL);

    // Flush remaining events before unload.
    window.addEventListener('pagehide', function () {
      flush(true);
    });
    window.addEventListener('beforeunload', function () {
      flush(true);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
