# Coding Conventions

**Analysis Date:** 2026-03-07

## Naming Patterns

**Files:**
- PascalCase: Components, classes, interfaces (`CartManager.ts`, `ErrorBoundary.tsx`)
- camelCase: Hooks, utilities, functions (`useCart.ts`, `priceUtils.ts`)
- kebab-case: Configuration files only
- Test files: `{name}.test.ts` or `{name}.test.tsx`

**Functions:**
- camelCase for all functions
- Verb prefix for action functions: `getXxx()`, `setXxx()`, `addXxx()`, `removeXxx()`, `updateXxx()`
- Noun prefix for query functions: `hasXxx()`, `isXxx()`, `findXxx()`
- Use descriptive names: `syncWithWooCommerce()` not `sync()`

**Variables:**
- camelCase for all variables and constants
- Boolean variables: `isXxx`, `hasXxx`, `canXxx`, `shouldXxx`
- Arrays: plural nouns (`items`, `products`, `users`)
- Private class members: prefix with underscore NOT used; use `private` keyword

**Types:**
- PascalCase for interfaces, types, enums
- Interface prefixes: `{Name}Config`, `{Name}State`, `{Name}Props`, `{Name}Return`
- Avoid `any` type - use `unknown` or proper generics

## Code Style

**Formatting:**
- Tool: Prettier
- Key settings:
  - `semi: true`
  - `singleQuote: true`
  - `printWidth: 120`
  - `tabWidth: 2`
  - `trailingComma: es5`
  - `arrowParens: avoid`
  - `bracketSpacing: true`

**Linting:**
- Tool: ESLint with TypeScript parser
- Configuration: `.eslintrc.cjs`

**Key Rules Enforced:**
```javascript
// TypeScript
'@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
'@typescript-eslint/prefer-const': 'error'
'@typescript-eslint/consistent-type-definitions': ['error', 'interface']
'@typescript-eslint/consistent-type-imports': 'error'
'@typescript-eslint/no-floating-promises': 'error'
'@typescript-eslint/no-misused-promises': 'error'
'@typescript-eslint/prefer-nullish-coalescing': 'error'
'@typescript-eslint/prefer-optional-chain': 'error'

// General
'no-console': 'warn'
'no-debugger': 'error'
'prefer-arrow-callback': 'error'
'comma-dangle': ['error', 'always-multiline']
'semi': ['error', 'always']
'quotes': ['error', 'single']
'indent': ['error', 2]
'max-len': ['warn', { code: 120 }]
```

**Indentation:** 2 spaces (no tabs)

## Import Organization

**Order:**
1. External libraries (React, three.js, etc.)
2. Internal modules (`@/config`, `@/utils`, `@/services`)
3. Relative imports (`../lib`, `./components`)
4. Type imports

**Path Aliases:**
```typescript
'@/components' → 'src/components'
'@/utils'       → 'src/utils'
'@/types'       → 'src/types'
'@/services'    → 'src/services'
'@/hooks'       → 'src/hooks'
'@/config'      → 'src/config'
```

**Import Style:**
```typescript
// Named imports (preferred)
import { useState, useEffect } from 'react';
import { CartManager, CartItem } from '../lib/cart';
import { Logger } from '../utils/Logger';

// Type imports
import type { CartState, CartConfig } from '../lib/cart';
```

## Error Handling

**Patterns:**

1. **Try-catch with re-throw** (for critical operations):
```typescript
public addItem(item: CartItem): void {
  try {
    // Validate
    if (!item.productId || item.price < 0) {
      throw new Error('Invalid cart item');
    }
    // Operation
    this.items.push(item);
  } catch (error) {
    this.logger.error('Failed to add item', error);
    throw error;
  }
}
```

2. **Try-catch with graceful handling** (for non-critical):
```typescript
public saveToLocalStorage(): void {
  try {
    localStorage.setItem(this.key, JSON.stringify(data));
  } catch (error) {
    this.logger.error('Failed to save', error);
  }
}
```

3. **Error type checking:**
```typescript
catch (err) {
  const message = err instanceof Error ? err.message : 'Unknown error';
}
```

**Error Boundaries:** Use `ErrorBoundary` component (`src/components/ErrorBoundary.tsx`) to catch React render errors.

**Validation:** Throw early with descriptive messages:
```typescript
if (!item.productId) {
  throw new Error('Invalid cart item: missing required field productId');
}
```

## Logging

**Framework:** Custom `Logger` class (`src/utils/Logger.ts`)

**Patterns:**
```typescript
const logger = new Logger('ServiceName');

// Log levels
logger.debug('Detailed info', { metadata });
logger.info('Operation completed', { item });
logger.warn('Unexpected but handled', { reason });
logger.error('Operation failed', error, { context });
logger.fatal('Critical failure', error, { impact });
```

**When to Log:**
- `debug`: Detailed flow information
- `info`: Key operations (add item, remove item, sync)
- `warn`: Recoverable issues (missing optional config)
- `error`: Failures that don't crash the app
- `fatal`: Critical failures requiring attention

**Log include:** Timestamps, service name, message, metadata, error details

## Comments

**When to Comment:**
- JSDoc for all exported functions/classes
- Complex business logic
- Non-obvious workarounds
- TODO comments for future work

**JSDoc Example:**
```typescript
/**
 * Calculate discount percentage
 * @param original - Original price
 * @param sale - Sale price
 * @returns Discount percentage (0-100)
 */
export function calculateDiscount(original: number, sale: number): number {
  // ...
}
```

**Avoid:**
- Obvious comments (`// Increment counter`)
- Commented-out code (delete, don't commit)
- Incomplete comments

## Function Design

**Size:** Keep functions focused - single responsibility

**Parameters:**
- Max 3-4 parameters; use objects for more
- Use optional parameters with defaults
- Validate early

```typescript
// Good
function createItem(overrides: Partial<CartItem> = {}): CartItem {
  return { productId: 'default', quantity: 1, ...overrides };
}
```

**Return Values:**
- Always return same type (or use union)
- Return copies of arrays/objects, not references
```typescript
public getItems(): CartItem[] {
  return [...this.items]; // Return copy
}
```

## Module Design

**Exports:**
- Named exports preferred
- Barrel files (`index.ts`) for public APIs
```typescript
// lib/index.ts
export { CartManager, getCartManager } from './cart';
export { formatPrice, calculateDiscount } from './priceUtils';
```

**Singleton Pattern:**
```typescript
export class CartManager {
  private static instance: CartManager | null = null;

  public static getInstance(): CartManager {
    if (!CartManager.instance) {
      CartManager.instance = new CartManager();
    }
    return CartManager.instance;
  }

  public static resetInstance(): void {  // For testing
    CartManager.instance = null;
  }
}
```

**React Hooks:**
- Always return object with named properties
- Include loading and error states
- Use `useMemo` for expensive operations
- Use `useCallback` for functions passed to children

---

*Convention analysis: 2026-03-07*
