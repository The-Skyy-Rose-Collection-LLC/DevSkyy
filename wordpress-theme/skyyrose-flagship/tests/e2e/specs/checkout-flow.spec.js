const { test, expect } = require('@playwright/test');

test.describe('WooCommerce Checkout Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Clear cart before each test
        await page.goto('/cart/');
        await page.evaluate(() => {
            document.querySelectorAll('.remove').forEach(btn => btn.click());
        });
    });

    test('should browse products and view product details', async ({ page }) => {
        // Navigate to shop page
        await page.goto('/shop/');

        // Wait for products to load
        await page.waitForSelector('.products');

        // Verify products are displayed
        const products = await page.$$('.product');
        expect(products.length).toBeGreaterThan(0);

        // Click on first product
        await page.click('.product:first-child a');

        // Verify we're on a product page
        await expect(page).toHaveURL(/\/product\//);

        // Verify product details are visible
        await expect(page.locator('.product_title')).toBeVisible();
        await expect(page.locator('.price')).toBeVisible();
        await expect(page.locator('.single_add_to_cart_button')).toBeVisible();
    });

    test('should add product to cart', async ({ page }) => {
        // Go to a product page
        await page.goto('/product/test-product/');

        // Add to cart
        await page.click('.single_add_to_cart_button');

        // Wait for success message
        await page.waitForSelector('.woocommerce-message', { timeout: 5000 });

        // Verify cart count updated
        const cartCount = await page.textContent('.cart-contents-count');
        expect(parseInt(cartCount)).toBeGreaterThan(0);
    });

    test('should update cart quantity', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to cart
        await page.goto('/cart/');

        // Update quantity
        await page.fill('input.qty', '3');
        await page.click('[name="update_cart"]');

        // Wait for cart update
        await page.waitForSelector('.woocommerce-message');

        // Verify quantity updated
        const quantity = await page.inputValue('input.qty');
        expect(quantity).toBe('3');
    });

    test('should remove item from cart', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to cart
        await page.goto('/cart/');

        // Remove item
        await page.click('.remove');

        // Wait for removal
        await page.waitForSelector('.cart-empty', { timeout: 5000 });

        // Verify cart is empty
        await expect(page.locator('.cart-empty')).toBeVisible();
    });

    test('should apply coupon code', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to cart
        await page.goto('/cart/');

        // Apply coupon (assumes a test coupon exists)
        await page.fill('#coupon_code', 'TESTCOUPON');
        await page.click('[name="apply_coupon"]');

        // Wait for coupon application
        await page.waitForSelector('.woocommerce-message, .woocommerce-error', { timeout: 5000 });
    });

    test('should complete checkout as guest', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Proceed to checkout
        await page.goto('/checkout/');

        // Fill billing details
        await page.fill('#billing_first_name', 'John');
        await page.fill('#billing_last_name', 'Doe');
        await page.fill('#billing_email', 'john.doe@example.com');
        await page.fill('#billing_phone', '1234567890');
        await page.fill('#billing_address_1', '123 Test Street');
        await page.fill('#billing_city', 'Test City');
        await page.fill('#billing_postcode', '12345');

        // Select country
        await page.selectOption('#billing_country', 'US');

        // Select state
        await page.selectOption('#billing_state', 'CA');

        // Accept terms
        await page.check('#terms');

        // Place order (with test payment gateway)
        await page.click('#place_order');

        // Wait for order confirmation
        await page.waitForURL(/\/checkout\/order-received\//, { timeout: 30000 });

        // Verify order confirmation
        await expect(page.locator('.woocommerce-thankyou-order-received')).toBeVisible();
    });

    test('should validate required checkout fields', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to checkout
        await page.goto('/checkout/');

        // Try to place order without filling required fields
        await page.click('#place_order');

        // Wait for error messages
        await page.waitForSelector('.woocommerce-error', { timeout: 5000 });

        // Verify error message is shown
        await expect(page.locator('.woocommerce-error')).toBeVisible();
    });

    test('should calculate shipping correctly', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to cart
        await page.goto('/cart/');

        // Click calculate shipping
        if (await page.isVisible('.shipping-calculator-button')) {
            await page.click('.shipping-calculator-button');

            // Fill shipping details
            await page.selectOption('#calc_shipping_country', 'US');
            await page.selectOption('#calc_shipping_state', 'CA');
            await page.fill('#calc_shipping_postcode', '12345');

            // Update shipping
            await page.click('[name="calc_shipping"]');

            // Wait for shipping calculation
            await page.waitForTimeout(2000);

            // Verify shipping cost is displayed
            const shippingCost = await page.textContent('.shipping .woocommerce-Price-amount');
            expect(shippingCost).toBeTruthy();
        }
    });

    test('should display order summary correctly', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        const productPrice = await page.textContent('.price .woocommerce-Price-amount');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to checkout
        await page.goto('/checkout/');

        // Wait for order review
        await page.waitForSelector('#order_review');

        // Verify product is in order summary
        await expect(page.locator('.product-name')).toBeVisible();

        // Verify total is displayed
        await expect(page.locator('.order-total .woocommerce-Price-amount')).toBeVisible();
    });

    test('should handle payment method selection', async ({ page }) => {
        // Add product to cart
        await page.goto('/product/test-product/');
        await page.click('.single_add_to_cart_button');
        await page.waitForSelector('.woocommerce-message');

        // Go to checkout
        await page.goto('/checkout/');

        // Check if multiple payment methods exist
        const paymentMethods = await page.$$('.payment_methods li');

        if (paymentMethods.length > 1) {
            // Select different payment method
            await page.click('.payment_methods li:nth-child(2) input');

            // Verify payment method details are shown
            const paymentBox = await page.isVisible('.payment_box');
            expect(paymentBox).toBeTruthy();
        }
    });
});

test.describe('Product Variations', () => {
    test('should select product variation', async ({ page }) => {
        // Go to a variable product (assumes one exists)
        await page.goto('/product/variable-test-product/');

        // Check if variation selects exist
        if (await page.isVisible('.variations select')) {
            // Select first variation option
            const firstSelect = await page.$('.variations select');
            const options = await firstSelect.$$('option');

            if (options.length > 1) {
                await firstSelect.selectOption({ index: 1 });

                // Wait for variation to load
                await page.waitForTimeout(1000);

                // Verify add to cart button is enabled
                const addToCartButton = await page.$('.single_add_to_cart_button');
                const isDisabled = await addToCartButton.isDisabled();
                expect(isDisabled).toBe(false);
            }
        }
    });
});

test.describe('Responsive Design', () => {
    test('should work on mobile devices', async ({ page }) => {
        // Set mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });

        // Navigate to shop
        await page.goto('/shop/');

        // Verify mobile menu
        if (await page.isVisible('.mobile-menu-toggle')) {
            await page.click('.mobile-menu-toggle');
            await expect(page.locator('.mobile-menu')).toBeVisible();
        }

        // Verify products display correctly
        const products = await page.$$('.product');
        expect(products.length).toBeGreaterThan(0);
    });

    test('should work on tablet devices', async ({ page }) => {
        // Set tablet viewport
        await page.setViewportSize({ width: 768, height: 1024 });

        // Navigate to shop
        await page.goto('/shop/');

        // Verify layout
        const products = await page.$$('.product');
        expect(products.length).toBeGreaterThan(0);
    });
});

test.describe('3D Product Viewer', () => {
    test('should load 3D product viewer', async ({ page }) => {
        // Go to a product with 3D viewer
        await page.goto('/product/3d-test-product/');

        // Wait for Three.js container
        await page.waitForSelector('#three-container', { timeout: 10000 });

        // Verify canvas element exists
        const canvas = await page.$('#three-container canvas');
        expect(canvas).toBeTruthy();
    });

    test('should interact with 3D model', async ({ page }) => {
        await page.goto('/product/3d-test-product/');
        await page.waitForSelector('#three-container canvas');

        const canvas = await page.$('#three-container canvas');
        const boundingBox = await canvas.boundingBox();

        // Simulate mouse drag on canvas (orbit control)
        await page.mouse.move(boundingBox.x + 50, boundingBox.y + 50);
        await page.mouse.down();
        await page.mouse.move(boundingBox.x + 100, boundingBox.y + 100);
        await page.mouse.up();

        // Wait a moment for rendering
        await page.waitForTimeout(500);

        // Verify no errors occurred
        const errors = await page.evaluate(() => {
            return window.threeErrors || [];
        });
        expect(errors.length).toBe(0);
    });
});
