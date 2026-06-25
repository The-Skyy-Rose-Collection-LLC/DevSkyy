/**
 * Performance Guardian — FPS Watchdog & Animation Budget Manager
 *
 * Part of the SkyyRose Experience Engine, Phase 2.
 *
 * Monitors frame rate in real-time via requestAnimationFrame. When FPS drops
 * below the configured threshold (default 30), adds `.skyy-motion-reduced` to
 * <body> to throttle non-critical CSS animations. Automatically recovers once
 * the frame rate stabilizes.
 *
 * Respects `prefers-reduced-motion`: if the OS flag is set, the class is added
 * immediately and the RAF loop never starts.
 *
 * Exposes `window.SkyyPerformance` so other modules (e.g. brand-atmosphere)
 * can check the throttle state before starting their own RAF loops.
 *
 * @module performance-guardian
 * @since  6.4.0
 */
(function () {
  'use strict';

  /** @type {{ fpsThreshold: number, checkInterval: number, throttleDuration: number, debug: boolean }} */
  var budget = window.SkyyPerformanceBudget || {
    fpsThreshold: 30,
    checkInterval: 2000,
    throttleDuration: 5000,
    debug: false,
  };

  // Respect OS-level reduced-motion preference immediately.
  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (motionQuery.matches) {
    document.body.classList.add('skyy-motion-reduced');
    window.SkyyPerformance = {
      isThrottled: function () {
        return true;
      },
      forceThrottle: function () {},
      forceRecover: function () {},
    };
    return;
  }

  var frameCount = 0;
  var lastTime = performance.now();
  var throttleTimeout = null;
  var isThrottled = false;
  var rafHandle = null;

  function countFrame(now) {
    frameCount++;
    rafHandle = requestAnimationFrame(countFrame);
  }

  function measureFPS() {
    var now = performance.now();
    var elapsed = now - lastTime;
    if (elapsed === 0) return;

    var fps = Math.round((frameCount / elapsed) * 1000);
    frameCount = 0;
    lastTime = now;

    if (budget.debug || window.SKYYROSE_DEBUG) {
      // eslint-disable-next-line no-console
      console.log('[SkyyPerformance] FPS:', fps);
    }

    if (fps < budget.fpsThreshold && !isThrottled) {
      throttle();
    }
  }

  function throttle() {
    isThrottled = true;
    document.body.classList.add('skyy-motion-reduced');

    if (budget.debug || window.SKYYROSE_DEBUG) {
      // eslint-disable-next-line no-console
      console.warn('[SkyyPerformance] Low FPS — throttling animations.');
    }

    clearTimeout(throttleTimeout);
    throttleTimeout = setTimeout(recover, budget.throttleDuration);
  }

  function recover() {
    isThrottled = false;
    document.body.classList.remove('skyy-motion-reduced');

    if (budget.debug || window.SKYYROSE_DEBUG) {
      // eslint-disable-next-line no-console
      console.log('[SkyyPerformance] Recovered — restoring animations.');
    }
  }

  // Start the FPS counting loop.
  rafHandle = requestAnimationFrame(countFrame);

  // Sample FPS on the configured interval.
  setInterval(measureFPS, budget.checkInterval);

  // Pause counting when the tab is hidden to avoid stale readings on re-focus.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      cancelAnimationFrame(rafHandle);
      frameCount = 0;
    } else {
      lastTime = performance.now();
      rafHandle = requestAnimationFrame(countFrame);
    }
  });

  // Expose API for other modules.
  window.SkyyPerformance = {
    isThrottled: function () {
      return isThrottled;
    },
    forceThrottle: throttle,
    forceRecover: recover,
  };
})();
