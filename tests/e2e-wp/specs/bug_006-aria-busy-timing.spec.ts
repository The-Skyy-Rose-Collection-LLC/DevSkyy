import { test, expect } from '@playwright/test';

/**
 * bug_006 — aria-busy clears synchronously with status text on the
 * holographic Buy button (.holo__buy).
 *
 * Original bug: aria-busy="true" was set when the click handler ran but
 * removed only inside the 2.0/2.5s setTimeouts that revert visual state.
 * WAI-ARIA defers presenting name changes while aria-busy="true", so by
 * the time aria-busy flipped to false, the meaningful "Added ✓" /
 * "Error" textContent had already reverted to the original button label.
 *
 * Fix in product-card-holo.js: hoist removeAttribute('aria-busy') out of
 * the setTimeouts and into the synchronous resolution branches.
 *
 * STATUS — 2026-05-05: test.fixme'd because production renders the holo
 * Buy element as a navigation link without `data-product-id`:
 *
 *     <a href="..." class="holo__buy">View Technical Details</a>
 *
 * The JS click handler at product-card-holo.js:230 binds via
 * `.holo__buy[data-product-id]` — a selector that matches zero elements
 * on every collection page (verified via grep across 7 production
 * URLs). The AJAX add-to-cart path the fix targets is dormant.
 *
 * The fix on the audit branch IS correct in source. These tests are
 * scaffolding for when the PHP layer adds data-product-id to holo
 * cards (or moves Add-to-Cart out of the holo card entirely). To
 * un-fixme:
 *   1. Confirm production HTML emits .holo__buy[data-product-id]
 *      (`curl https://skyyrose.co/collection-black-rose/ | grep 'holo__buy[^"]*" data-product-id'`)
 *   2. Confirm clicking the button triggers a wc-ajax=add_to_cart fetch
 *   3. Remove the .fixme calls below
 */

const COLLECTION_PATH = '/collection-black-rose/';
const HOLO_BUY = '.holo__buy[data-product-id]';

test.describe('bug_006 — aria-busy clears synchronously with success/error text', () => {
  test.fixme('aria-busy is null at the moment "Added ✓" is rendered', async ({ page }) => {
    await page.route('**?wc-ajax=add_to_cart', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ fragments: {}, cart_hash: 'test-hash-001' }),
      }),
    );

    await page.goto(COLLECTION_PATH);

    const buyBtn = page.locator(HOLO_BUY).first();
    await expect(buyBtn).toBeVisible({ timeout: 15_000 });
    await buyBtn.click();

    await expect(buyBtn).toHaveText('Added ✓', { timeout: 5_000 });
    expect(await buyBtn.getAttribute('aria-busy')).toBeNull();
  });

  test.fixme('aria-busy is null at the moment "Error" is rendered', async ({ page }) => {
    await page.route('**?wc-ajax=add_to_cart', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ error: true }),
      }),
    );

    await page.goto(COLLECTION_PATH);
    const buyBtn = page.locator(HOLO_BUY).first();
    await expect(buyBtn).toBeVisible({ timeout: 15_000 });
    await buyBtn.click();

    await expect(buyBtn).toHaveText('Error', { timeout: 5_000 });
    expect(await buyBtn.getAttribute('aria-busy')).toBeNull();
  });

  test.fixme('disabled stays true through the success window (double-click guard)', async ({ page }) => {
    await page.route('**?wc-ajax=add_to_cart', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ fragments: {}, cart_hash: 'test-hash-002' }),
      }),
    );

    await page.goto(COLLECTION_PATH);
    const buyBtn = page.locator(HOLO_BUY).first();
    await expect(buyBtn).toBeVisible({ timeout: 15_000 });
    await buyBtn.click();
    await expect(buyBtn).toHaveText('Added ✓');
    expect(await buyBtn.isDisabled()).toBe(true);
    await expect(buyBtn).toBeEnabled({ timeout: 4_000 });
  });

  test.fixme('catch branch (network failure) clears aria-busy synchronously', async ({ page }) => {
    await page.route('**?wc-ajax=add_to_cart', (route) => route.abort('failed'));

    await page.goto(COLLECTION_PATH);
    const buyBtn = page.locator(HOLO_BUY).first();
    await expect(buyBtn).toBeVisible({ timeout: 15_000 });
    const originalText = await buyBtn.textContent();
    await buyBtn.click();
    await expect(buyBtn).toHaveText(originalText!, { timeout: 5_000 });
    expect(await buyBtn.getAttribute('aria-busy')).toBeNull();
  });
});

/**
 * Currently-passable smoke test: the collection page renders holo cards
 * with the expected class structure. Doesn't exercise the AJAX click
 * handler (no data-product-id binding, see file header). Asserts the
 * baseline: holo cards still ship and contain a `holo__buy` link.
 */
test.describe('bug_006 — smoke', () => {
  test('collection page renders holo cards with .holo__buy', async ({ page }) => {
    await page.goto(COLLECTION_PATH);

    const cards = page.locator('.holo');
    await expect(cards.first()).toBeVisible({ timeout: 15_000 });

    const buyLinks = page.locator('.holo__buy');
    expect(await buyLinks.count()).toBeGreaterThan(0);
  });
});
