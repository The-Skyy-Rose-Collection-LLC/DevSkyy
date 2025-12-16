/**
 * Vercel Speed Insights Client-Side Integration
 * ==============================================
 *
 * This module provides client-side integration with Vercel Speed Insights
 * for monitoring frontend performance metrics including Core Web Vitals.
 *
 * Documentation: https://vercel.com/docs/speed-insights/package
 */

/**
 * Initialize Vercel Speed Insights on the client
 * This function should be called early in the application lifecycle
 */
export function initializeSpeedInsights(): void {
  if (typeof window === "undefined") {
    console.warn("Speed Insights can only be initialized on the client");
    return;
  }

  // Check if Speed Insights script is already loaded
  if ((window as any).si) {
    console.log("Vercel Speed Insights already initialized");
    return;
  }

  // Initialize the Speed Insights queue function
  (window as any).si =
    (window as any).si ||
    function () {
      (window as any).siq = (window as any).siq || [];
      ((window as any).siq as any[]).push(arguments);
    };

  // Load the Speed Insights script
  const script = document.createElement("script");
  script.defer = true;
  script.src = "/_vercel/speed-insights/script.js";
  script.onload = () => {
    console.log("Vercel Speed Insights script loaded successfully");
  };
  script.onerror = () => {
    console.error("Failed to load Vercel Speed Insights script");
  };

  document.body.appendChild(script);
}

/**
 * Track a custom Web Vital or performance metric
 * @param name - The name of the metric
 * @param value - The value of the metric
 * @param options - Additional options for the metric
 */
export function trackMetric(
  name: string,
  value: number,
  options?: Record<string, any>
): void {
  if (typeof window === "undefined") {
    return;
  }

  if ((window as any).si) {
    ((window as any).si as any)("pageMetrics", {
      name,
      value,
      timestamp: Date.now(),
      ...options,
    });
  }
}

/**
 * Track a page view with optional custom properties
 * @param path - The page path to track
 * @param properties - Optional custom properties
 */
export function trackPageView(path: string, properties?: Record<string, any>): void {
  if (typeof window === "undefined") {
    return;
  }

  if ((window as any).si) {
    ((window as any).si as any)("pageView", {
      path,
      timestamp: Date.now(),
      ...properties,
    });
  }
}

/**
 * Track an event for Speed Insights
 * @param eventName - The name of the event
 * @param properties - Optional event properties
 */
export function trackEvent(eventName: string, properties?: Record<string, any>): void {
  if (typeof window === "undefined") {
    return;
  }

  if ((window as any).si) {
    ((window as any).si as any)("event", {
      name: eventName,
      timestamp: Date.now(),
      ...properties,
    });
  }
}

/**
 * Monitor Core Web Vitals automatically
 * This uses the web-vitals library if available, or the native Web Vitals API
 */
export function monitorCoreWebVitals(): void {
  if (typeof window === "undefined") {
    return;
  }

  // Monitor Largest Contentful Paint (LCP)
  if ("PerformanceObserver" in window) {
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        const timing = lastEntry.renderTime || lastEntry.loadTime || 0;
        trackMetric("LCP", timing, {
          type: "largest-contentful-paint",
        });
      });
      lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });

      // Monitor First Input Delay (FID) / Interaction to Next Paint (INP)
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        for (const entry of entries) {
          const processingTime = (entry as any).processingDuration || 0;
          trackMetric("FID", processingTime, {
            type: "first-input",
            startTime: entry.startTime,
          });
        }
      });
      fidObserver.observe({ entryTypes: ["first-input"] });

      // Monitor Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const entryAny = entry as any;
          if (!entryAny.hadRecentInput) {
            clsValue += entryAny.value || 0;
            trackMetric("CLS", clsValue, {
              type: "layout-shift",
            });
          }
        }
      });
      clsObserver.observe({ entryTypes: ["layout-shift"] });
    } catch (error) {
      console.warn("Failed to monitor Core Web Vitals:", error);
    }
  }
}

/**
 * Configure Speed Insights before send hook
 * Use this to filter or modify data before sending to Vercel
 * @param callback - Function to process data before sending
 */
export function setBeforeSendCallback(
  callback: (data: Record<string, any>) => Record<string, any> | null
): void {
  if (typeof window === "undefined") {
    return;
  }

  (window as any).speedInsightsBeforeSend = callback;
}

/**
 * Initialize Speed Insights with all monitoring features
 * Call this once in your application startup
 */
export function initializeFullSpeedInsights(): void {
  initializeSpeedInsights();
  monitorCoreWebVitals();

  // Optional: Set up a custom before-send hook to filter sensitive data
  setBeforeSendCallback((data) => {
    // You can remove sensitive information from URLs here
    if (data.url && data.url.includes("/api/")) {
      data.url = data.url.replace(/[?&]token=[^&]*/, "");
    }
    return data;
  });

  console.log("Speed Insights fully initialized with Core Web Vitals monitoring");
}

export default {
  initialize: initializeSpeedInsights,
  initializeFull: initializeFullSpeedInsights,
  trackMetric,
  trackPageView,
  trackEvent,
  monitorCoreWebVitals,
  setBeforeSendCallback,
};
