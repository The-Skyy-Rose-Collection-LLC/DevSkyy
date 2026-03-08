# Testing Patterns

**Analysis Date:** 2026-03-07

## Test Framework

**Runner:**
- Jest v29+ with ESM support
- Configuration: `config/testing/jest.config.cjs`
- TypeScript preset: `ts-jest/presets/default-esm`

**Testing Libraries:**
- `@testing-library/react` - React component testing
- `@testing-library/jest-dom` - DOM matchers
- `jest` - Core testing framework

**Run Commands:**
```bash
npm test                    # Run all tests
npm test -- --watch        # Watch mode
npm test -- --coverage     # Generate coverage report
npm test -- --testPathPattern="cart"  # Run specific tests
```

## Test File Organization

**Location:**
- Co-located with source files in `__tests__` directories
- Pattern: `src/{module}/__tests__/{module}.test.ts`

**Naming:**
- Test files: `{Name}.test.ts` or `{Name}.test.tsx`
- Example: `src/lib/__tests__/cart.test.ts`

**Structure:**
```
src/
├── lib/
│   ├── __tests__/
│   │   ├── cart.test.ts
│   │   ├── priceUtils.test.ts
│   │   └── materialSwapper.test.ts
│   ├── cart.ts
│   └── priceUtils.ts
├── hooks/
│   ├── __tests__/
│   │   └── useCart.test.ts
│   └── useCart.ts
└── components/
    ├── __tests__/
    │   ├── ErrorBoundary.test.tsx
    │   └── CartModal.test.tsx
    └── ErrorBoundary.tsx
```

## Test Structure

**Suite Organization:**
```typescript
describe('ModuleName', () => {
  beforeEach(() => {
    // Reset state before each test
    Module.resetInstance?.();
    jest.clearAllMocks();
  });

  describe('feature/functionality', () => {
    it('should do something specific', () => {
      // Test implementation
      expect(result).toBe(expected);
    });

    it('should handle edge case', () => {
      // Edge case test
    });
  });
});
```

**Patterns:**

1. **Factory Functions for Test Data:**
```typescript
function createItem(overrides: Partial<CartItem> = {}): CartItem {
  return {
    productId: 'prod-1',
    sku: 'SKU-001',
    name: 'Test Product',
    price: 99.99,
    quantity: 1,
    ...overrides,
  };
}

// Usage
it('should add item with default values', () => {
  const item = createItem();
  expect(item.quantity).toBe(1);
});

it('should allow overrides', () => {
  const item = createItem({ quantity: 5 });
  expect(item.quantity).toBe(5);
});
```

2. **Setup/Teardown:**
```typescript
beforeEach(() => {
  // Reset singleton instances
  CartManager.resetInstance();
  // Clear localStorage
  localStorage.clear();
  // Clear all mocks
  jest.clearAllMocks();
});
```

3. **Assertions:**
```typescript
// Basic
expect(value).toBe(expected);
expect(value).toEqual(expected);

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();

// Numbers
expect(value).toBe(5);
expect(value).toBeCloseTo(3.14);
expect(value).toBeGreaterThan(0);

// Arrays
expect(items).toHaveLength(2);
expect(items).toContain(item);
expect(items).toContainEqual(expectedItem);

// Objects
expect(obj).toHaveProperty('key');
expect(obj).toMatchObject({ key: 'value' });
expect(obj).toEqual(expect.objectContaining({ key: 'value' }));

// Errors
expect(() => fn()).toThrow('error message');
```

## Mocking

**Framework:** Jest (`jest.fn()`)

**Patterns:**

1. **Mocking Modules:**
```typescript
// Mock a single module
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));
```

2. **Mocking Functions:**
```typescript
const mockFn = jest.fn();
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue('value');
mockFn.mockImplementation((arg) => arg * 2);
```

3. **Mocking Global/APIs:**
```typescript
// Mock fetch
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: jest.fn().mockResolvedValue({ data: 'test' }),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;
```

4. **Mocking React Components:**
```typescript
jest.mock('../SomeComponent', () => ({
  SomeComponent: () => <div>Mocked</div>,
}));
```

5. **Spying on Methods:**
```typescript
const obj = { method: jest.fn() };
jest.spyOn(obj, 'method');
```

**What to Mock:**
- External services (fetch, localStorage)
- Third-party libraries (Logger, analytics)
- Singleton instances (CartManager.getInstance)
- Time-dependent code (setTimeout, setInterval)

**What NOT to Mock:**
- Internal pure functions being tested
- Simple utility functions
- The module under test

## Fixtures and Factories

**Test Data:**
- Factory functions in test files (preferred)
- Shared fixtures in `tests/setup.ts`

**Shared Helpers (from `tests/setup.ts`):**
```typescript
// Custom matchers
expect.extend({
  toBeValidDate(),
  toBeValidUUID(),
  toHaveValidStructure(),
});

// Test helpers
export const createMockAgent = (overrides) => ({ ... });
export const createMockTask = (overrides) => ({ ... });
export const createMockUser = (overrides) => ({ ... });

// Async helpers
export const waitFor = (ms) => Promise;
export const waitForCondition = async (condition, timeout, interval);

// API helpers
export const createMockApiResponse = (data, overrides) => ({ ... });
export const expectToThrowAsync = async (fn, expectedError) => { ... };
```

## Coverage

**Requirements:**
- Global threshold enforced at 77% branches, 80% functions/lines/statements
- Configured in `config/testing/jest.config.cjs`

**View Coverage:**
```bash
npm test -- --coverage
```

**Coverage Reports:**
- Output: `coverage/` directory
- Formats: `text`, `lcov`, `html`, `json`

**Excluded from Coverage:**
- Type definition files (`.d.ts`)
- Configuration files
- Barrel files (`index.ts`)
- WebGL/Three.js rendering files requiring WebGL context

## Test Types

**Unit Tests:**
- Test individual functions/classes in isolation
- Mock all external dependencies
- Fast execution
- Example: `src/lib/__tests__/priceUtils.test.ts`

**Integration Tests:**
- Test multiple modules working together
- Example: CartManager with localStorage

**Component Tests:**
- Test React components with @testing-library/react
- Example: `src/components/__tests__/ErrorBoundary.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

it('should render component', () => {
  render(<MyComponent prop="value" />);
  expect(screen.getByText('Value')).toBeInTheDocument();
});

it('should handle click', () => {
  const onClick = jest.fn();
  render(<Button onClick={onClick}>Click</Button>);
  fireEvent.click(screen.getByRole('button'));
  expect(onClick).toHaveBeenCalled();
});
```

**E2E Tests:**
- Located in `frontend/e2e/` and `frontend/tests/e2e/`
- Framework: Playwright
- Pattern: `*.spec.ts` files

## Common Patterns

**Async Testing:**
```typescript
it('should resolve promise', async () => {
  const result = await asyncFunction();
  expect(result).toBe('expected');
});

it('should reject on error', async () => {
  await expect(asyncFunction()).rejects.toThrow('error');
});
```

**Error Testing:**
```typescript
it('should throw for invalid input', () => {
  expect(() => validateItem({})).toThrow('Invalid cart item');
});

it('should handle async errors', async () => {
  await expectToThrowAsync(async () => {
    await fetchData();
  }, 'Network error');
});
```

**State Testing:**
```typescript
it('should update state on action', () => {
  const cart = CartManager.getInstance();
  const initialState = cart.getState();
  
  cart.addItem(createItem({ quantity: 2 }));
  
  expect(cart.getState().itemCount).toBe(initialState.itemCount + 2);
});
```

**Subscription/Event Testing:**
```typescript
it('should notify subscribers', () => {
  const callback = jest.fn();
  cart.subscribe(callback);
  
  expect(callback).toHaveBeenCalledWith(expect.objectContaining({ items: [] }));
  
  callback.mockClear();
  cart.addItem(item);
  
  expect(callback).toHaveBeenCalledTimes(1);
});
```

---

*Testing analysis: 2026-03-07*
