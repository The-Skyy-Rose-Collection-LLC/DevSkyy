/**
 * Request pacing + 429 backoff for the WordPress↔dashboard wiring client
 * (WS7). Framework-free (setTimeout only) so it can be unit-tested with
 * vitest fake timers.
 */

export interface ThrottleOptions {
  requestsPerSecond?: number;
  maxRetries?: number;
}

export class RequestThrottle {
  private lastRequestAt = 0;
  private readonly rps: number;
  readonly maxRetries: number;

  constructor(opts: ThrottleOptions = {}) {
    this.rps = opts.requestsPerSecond ?? 2;
    this.maxRetries = opts.maxRetries ?? 2;
  }

  /** Resolve once it is safe to fire the next request under the rps budget. */
  async wait(): Promise<void> {
    const minGapMs = 1000 / this.rps;
    const elapsed = Date.now() - this.lastRequestAt;
    if (elapsed < minGapMs) {
      await new Promise((resolve) => setTimeout(resolve, minGapMs - elapsed));
    }
    this.lastRequestAt = Date.now();
  }

  /** Retry-After (seconds) wins when present and valid; otherwise exponential backoff. */
  computeBackoffMs(attempt: number, retryAfterHeader: string | null): number {
    if (retryAfterHeader) {
      const seconds = Number.parseInt(retryAfterHeader, 10);
      if (Number.isFinite(seconds) && seconds >= 0) return seconds * 1000;
    }
    return 2 ** attempt * 500;
  }
}
