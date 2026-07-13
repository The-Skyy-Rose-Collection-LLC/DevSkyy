import { afterEach, describe, expect, it, vi } from 'vitest';

import { RequestThrottle } from '../throttle';

describe('RequestThrottle', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('delays a second wait() call to respect the requests-per-second pacing', async () => {
    vi.useFakeTimers();
    const throttle = new RequestThrottle({ requestsPerSecond: 2 }); // 500ms min gap

    await throttle.wait(); // first call: no prior request, resolves immediately

    const resolved = vi.fn();
    const pending = throttle.wait().then(resolved);

    await vi.advanceTimersByTimeAsync(1);
    expect(resolved).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(500);
    await pending;
    expect(resolved).toHaveBeenCalledTimes(1);
  });

  it('honors Retry-After over the exponential default', () => {
    const throttle = new RequestThrottle();
    expect(throttle.computeBackoffMs(0, '3')).toBe(3000);
    expect(throttle.computeBackoffMs(1, '3')).toBe(3000);
  });

  it('falls back to exponential backoff when Retry-After is absent or invalid', () => {
    const throttle = new RequestThrottle();
    expect(throttle.computeBackoffMs(0, null)).toBe(500);
    expect(throttle.computeBackoffMs(1, null)).toBe(1000);
    expect(throttle.computeBackoffMs(2, null)).toBe(2000);
    expect(throttle.computeBackoffMs(0, 'not-a-number')).toBe(500);
  });
});
