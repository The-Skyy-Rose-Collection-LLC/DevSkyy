# Testing & Validation

This skill provides comprehensive knowledge for testing and validating full-stack deployments. It activates when users mention "run tests", "e2e testing", "playwright", "cypress", "api testing", "validation", "health check", "smoke test", or encounter test-related errors.

---

## Testing Strategy for Headless WordPress + Next.js

### Test Pyramid
```
         E2E Tests (Playwright/Cypress)
        /                              \
       /   Integration Tests (API)      \
      /                                  \
     /      Unit Tests (Components)       \
    ------------------------------------------
```

## Unit Testing with Jest

### Setup
```bash
npm install -D jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

### jest.config.js
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
}

module.exports = createJestConfig(customJestConfig)
```

### Component Test Example
```typescript
// __tests__/components/ProductCard.test.tsx
import { render, screen } from '@testing-library/react'
import { ProductCard } from '@/components/ProductCard'

const mockProduct = {
  id: 1,
  name: 'Test Product',
  price: '29.99',
  image: '/test.jpg'
}

describe('ProductCard', () => {
  it('renders product name', () => {
    render(<ProductCard product={mockProduct} />)
    expect(screen.getByText('Test Product')).toBeInTheDocument()
  })

  it('renders price correctly', () => {
    render(<ProductCard product={mockProduct} />)
    expect(screen.getByText('$29.99')).toBeInTheDocument()
  })
})
```

## API Integration Testing

### Testing API Routes
```typescript
// __tests__/api/products.test.ts
import { GET } from '@/app/api/products/route'
import { NextRequest } from 'next/server'

// Mock fetch for WordPress API
global.fetch = jest.fn()

describe('/api/products', () => {
  beforeEach(() => {
    jest.resetAllMocks()
  })

  it('returns products from WordPress', async () => {
    const mockProducts = [{ id: 1, name: 'Product 1' }]

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProducts
    })

    const request = new NextRequest('http://localhost:3000/api/products')
    const response = await GET(request)
    const data = await response.json()

    expect(data).toEqual(mockProducts)
  })

  it('handles WordPress API errors', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500
    })

    const request = new NextRequest('http://localhost:3000/api/products')
    const response = await GET(request)

    expect(response.status).toBe(500)
  })
})
```

## E2E Testing with Playwright

### Setup
```bash
npm init playwright@latest
```

### playwright.config.ts
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2E Test Examples
```typescript
// e2e/homepage.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('loads successfully', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Your Site Name/)
  })

  test('displays products from WooCommerce', async ({ page }) => {
    await page.goto('/')
    const products = page.locator('[data-testid="product-card"]')
    await expect(products.first()).toBeVisible()
  })

  test('navigation works', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Shop')
    await expect(page).toHaveURL(/\/shop/)
  })
})
```

### E-commerce Flow Tests
```typescript
// e2e/checkout.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Checkout Flow', () => {
  test('can add product to cart', async ({ page }) => {
    await page.goto('/products/test-product')
    await page.click('[data-testid="add-to-cart"]')
    await expect(page.locator('[data-testid="cart-count"]')).toHaveText('1')
  })

  test('can complete checkout', async ({ page }) => {
    // Add product to cart
    await page.goto('/products/test-product')
    await page.click('[data-testid="add-to-cart"]')

    // Go to checkout
    await page.goto('/checkout')

    // Fill billing details
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="firstName"]', 'Test')
    await page.fill('[name="lastName"]', 'User')
    await page.fill('[name="address"]', '123 Test St')
    await page.fill('[name="city"]', 'Test City')
    await page.fill('[name="postcode"]', '12345')

    // Submit order
    await page.click('[data-testid="place-order"]')

    // Verify success
    await expect(page).toHaveURL(/\/order-confirmation/)
    await expect(page.locator('h1')).toContainText('Thank you')
  })
})
```

## API Validation Tests

### Health Check Tests
```typescript
// e2e/api-health.spec.ts
import { test, expect } from '@playwright/test'

test.describe('API Health', () => {
  test('main health endpoint returns healthy', async ({ request }) => {
    const response = await request.get('/api/health')
    expect(response.ok()).toBeTruthy()

    const data = await response.json()
    expect(data.status).toBe('healthy')
  })

  test('WordPress connection is healthy', async ({ request }) => {
    const response = await request.get('/api/health')
    const data = await response.json()
    expect(data.services.wordpress.status).toBe('healthy')
  })

  test('WooCommerce connection is healthy', async ({ request }) => {
    const response = await request.get('/api/health')
    const data = await response.json()
    expect(data.services.woocommerce.status).toBe('healthy')
  })
})
```

### Products API Tests
```typescript
// e2e/api-products.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Products API', () => {
  test('returns list of products', async ({ request }) => {
    const response = await request.get('/api/products')
    expect(response.ok()).toBeTruthy()

    const products = await response.json()
    expect(Array.isArray(products)).toBeTruthy()
    expect(products.length).toBeGreaterThan(0)
  })

  test('products have required fields', async ({ request }) => {
    const response = await request.get('/api/products')
    const products = await response.json()

    for (const product of products) {
      expect(product).toHaveProperty('id')
      expect(product).toHaveProperty('name')
      expect(product).toHaveProperty('price')
    }
  })
})
```

## Pre-Deployment Validation Script

```bash
#!/bin/bash
# scripts/validate-deployment.sh

echo "🔍 Running pre-deployment validation..."

# TypeScript check
echo "📝 Checking TypeScript..."
npx tsc --noEmit || { echo "❌ TypeScript errors found"; exit 1; }

# ESLint
echo "🔍 Running ESLint..."
npm run lint || { echo "❌ Linting errors found"; exit 1; }

# Unit tests
echo "🧪 Running unit tests..."
npm test || { echo "❌ Unit tests failed"; exit 1; }

# Build
echo "🏗️ Testing build..."
npm run build || { echo "❌ Build failed"; exit 1; }

# E2E tests (if CI)
if [ "$CI" = "true" ]; then
  echo "🎭 Running E2E tests..."
  npx playwright test || { echo "❌ E2E tests failed"; exit 1; }
fi

echo "✅ All validation checks passed!"
```

## Post-Deployment Validation Script

```bash
#!/bin/bash
# scripts/validate-live.sh

DEPLOYMENT_URL=${1:-"https://your-site.com"}

echo "🔍 Validating deployment at $DEPLOYMENT_URL..."

# Health check
echo "❤️ Checking health endpoint..."
HEALTH=$(curl -s "$DEPLOYMENT_URL/api/health")
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
  echo "❌ Health check failed: $HEALTH"
  exit 1
fi

# WordPress connection
WP_STATUS=$(echo $HEALTH | jq -r '.services.wordpress.status')
if [ "$WP_STATUS" != "healthy" ]; then
  echo "❌ WordPress connection unhealthy"
  exit 1
fi

# WooCommerce connection
WC_STATUS=$(echo $HEALTH | jq -r '.services.woocommerce.status')
if [ "$WC_STATUS" != "healthy" ]; then
  echo "❌ WooCommerce connection unhealthy"
  exit 1
fi

# Homepage loads
echo "🏠 Checking homepage..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOYMENT_URL")
if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Homepage returned $HTTP_CODE"
  exit 1
fi

echo "✅ All post-deployment checks passed!"
```

## Running Tests

```bash
# Unit tests
npm test

# Unit tests in watch mode
npm test -- --watch

# E2E tests
npx playwright test

# E2E tests with UI
npx playwright test --ui

# E2E tests specific file
npx playwright test e2e/checkout.spec.ts

# E2E tests against production
PLAYWRIGHT_BASE_URL=https://your-site.com npx playwright test
```

## Autonomous Testing Steps

When running tests:

1. **Run TypeScript check first** - `npx tsc --noEmit`
2. **Run linting** - `npm run lint`
3. **Run unit tests** - `npm test`
4. **Build the project** - `npm run build`
5. **Run E2E tests** - `npx playwright test`
6. **If tests fail**:
   - Read error message carefully
   - Use Context7 to find solutions for test framework errors
   - Fix issue and re-run tests
7. **Post-deployment** - Run validation script against live URL
