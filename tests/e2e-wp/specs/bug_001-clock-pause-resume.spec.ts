import { test, expect } from '@playwright/test';

/**
 * bug_001 — Three.js clock survives the visibility change cycle.
 *
 * The pause/resume implementation in experience-base.js was originally
 * calling clock.start(), which zeroes elapsedTime. The subclass scenes
 * read clock.elapsedTime as a monotonic phase variable for sin/cos
 * animations. Resetting it to 0 produced a visible snap on every tab
 * return. The fix uses direct property writes (clock.oldTime,
 * clock.running, clock.autoStart) to bypass start()'s zeroing.
 *
 * STATUS — 2026-05-05: test.fixme'd because the activating DOM containers
 * don't yet render on production:
 *   - init-3d.js queries `.skyyrose-3d-container[data-config]` and
 *     `#${collection}-experience` IDs — neither exists in any current
 *     PHP template. template-immersive-black-rose.php renders only
 *     `<main id="primary">`.
 *   - There's also a latent asymmetry at init-3d.js:155-156: the ID-path
 *     creates the experience but doesn't store it on
 *     container._skyyRoseExperience, while the data-config path at
 *     line 129 does. So even if a container existed, the visibility
 *     handler couldn't find the instance to call pause/resume on.
 *
 * The fix on the audit branch IS correct in source — verified manually
 * via reads of experience-base.js:454-484 + /simplify pass. These tests
 * are scaffolding for when the activating PHP/HTML changes ship. To
 * un-fixme:
 *   1. Confirm the immersive template renders an element matching the
 *      init-3d.js selector
 *   2. Confirm init-3d.js attaches `_skyyRoseExperience` to that element
 *   3. Remove the .fixme call below
 */

const EXP_QUERY = '.skyyrose-3d-container[data-initialized="true"]';

declare global {
  interface HTMLElement { _skyyRoseExperience?: any }
}

const readClock = (q: string) => {
  const c = document.querySelector(q) as HTMLElement | null;
  if (!c?._skyyRoseExperience?.clock) return null;
  const { elapsedTime, running, autoStart } = c._skyyRoseExperience.clock;
  return { elapsedTime, running, autoStart };
};

const setVisibility = (state: 'hidden' | 'visible') => {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true });
  Object.defineProperty(document, 'hidden', { value: state === 'hidden', configurable: true });
  document.dispatchEvent(new Event('visibilitychange'));
};

test.describe('bug_001 — Three.js clock survives visibility change', () => {
  test.fixme('elapsedTime is monotonic across hidden→visible cycle', async ({ page }) => {
    await page.goto('/experience-black-rose/');

    await page.waitForFunction(
      (q) => {
        const c = document.querySelector(q) as HTMLElement | null;
        return !!c?._skyyRoseExperience?.clock?.running;
      },
      EXP_QUERY,
      { timeout: 20_000 },
    );

    await page.waitForTimeout(500);

    const before = await page.evaluate(readClock, EXP_QUERY);
    expect(before).not.toBeNull();
    expect(before!.elapsedTime).toBeGreaterThan(0);
    expect(before!.running).toBe(true);

    await page.evaluate(setVisibility, 'hidden');
    await page.waitForTimeout(700);

    const hidden = await page.evaluate(readClock, EXP_QUERY);
    expect(hidden!.running).toBe(false);

    await page.evaluate(setVisibility, 'visible');
    await page.waitForTimeout(150);

    const after = await page.evaluate(readClock, EXP_QUERY);

    expect(after!.running).toBe(true);
    expect(after!.autoStart).toBe(true);
    expect(after!.elapsedTime).toBeGreaterThan(before!.elapsedTime);
    expect(after!.elapsedTime - before!.elapsedTime).toBeLessThan(0.4);
  });

  test.fixme('pause cancels rAF (no GPU work on hidden tab)', async ({ page }) => {
    await page.goto('/experience-black-rose/');
    await page.waitForFunction(
      (q) => !!(document.querySelector(q) as HTMLElement | null)?._skyyRoseExperience?.clock?.running,
      EXP_QUERY,
      { timeout: 20_000 },
    );

    await page.evaluate(setVisibility, 'hidden');
    await page.waitForTimeout(200);

    const isRunning = await page.evaluate((q) => {
      const c = document.querySelector(q) as HTMLElement | null;
      return c?._skyyRoseExperience?.isRunning;
    }, EXP_QUERY);

    expect(isRunning).toBe(false);
  });
});

/**
 * Currently-passable smoke test: the immersive page loads init-3d.js
 * and Three.js without console errors. Doesn't exercise pause/resume
 * (those need the missing container) but at least proves the JS layer
 * is syntactically intact in the deployed bundle.
 */
test.describe('bug_001 — smoke', () => {
  test('immersive-black-rose page loads init-3d.js without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => {
      if (m.type() === 'error') errors.push(m.text());
    });

    await page.goto('/experience-black-rose/');
    await page.waitForLoadState('networkidle');

    // Three.js + init-3d.js must have loaded
    const threeLoaded = await page.evaluate(() => typeof (window as any).THREE !== 'undefined');
    expect(threeLoaded).toBe(true);

    // No console errors from our scripts (third-party cookie warnings allowed)
    const ourErrors = errors.filter((e) =>
      !/cookie|third-party|preload|font|cors/i.test(e)
      && /skyyrose|experience|init-3d/i.test(e),
    );
    expect(ourErrors).toHaveLength(0);
  });
});
