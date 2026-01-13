/**
 * API Proxy Utility
 * Handles proxying requests to the backend with proper error handling,
 * caching, and timeout management.
 */

export const BACKEND_URL = process.env.BACKEND_URL || 'https://devskyy-backend.onrender.com';

export interface ProxyOptions {
  /** Cache duration in seconds (default: 0 = no cache) */
  revalidate?: number;
  /** Request timeout in milliseconds (default: 50000) */
  timeout?: number;
  /** Additional headers to include */
  headers?: Record<string, string>;
  /** Whether to include credentials (default: false) */
  credentials?: RequestCredentials;
}

/**
 * Proxy a request to the backend API
 */
export async function proxyToBackend(
  path: string,
  method: string,
  options: ProxyOptions = {},
  body?: BodyInit
) {
  const {
    revalidate = 0,
    timeout = 50000, // 50 seconds to handle Render cold starts
    headers: customHeaders = {},
    credentials = 'omit',
  } = options;

  const url = `${BACKEND_URL}${path}`;

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...customHeaders,
      },
      body,
      credentials,
      signal: controller.signal,
      // Note: Caching handled via Cache-Control response headers, not fetch options
    });

    clearTimeout(timeoutId);

    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${timeout}ms`);
      }
      throw error;
    }

    throw new Error('Unknown error occurred');
  }
}

/**
 * Get cache control header based on revalidate time
 */
export function getCacheControlHeader(revalidate: number): string {
  if (revalidate === 0) {
    return 'no-store, no-cache, must-revalidate';
  }

  // Use stale-while-revalidate for better UX
  const staleTime = revalidate * 2;
  return `public, s-maxage=${revalidate}, stale-while-revalidate=${staleTime}`;
}

/**
 * Create error response
 */
export function createErrorResponse(
  message: string,
  status: number = 500,
  details?: unknown
) {
  return {
    error: message,
    status,
    details: details instanceof Error ? details.message : details,
    timestamp: new Date().toISOString(),
  };
}
