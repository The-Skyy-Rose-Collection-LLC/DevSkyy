# Codebase Concerns

**Analysis Date:** 2026-03-07

## Tech Debt

**Incomplete Sorting Implementation:**
- Issue: `sortProducts` function in `src/hooks/useProductFilters.ts` has TODO comment for implementing sales/view-based sorting
- Files: `src/hooks/useProductFilters.ts` (line 126)
- Impact: Products cannot be sorted by popularity, limiting merchandising capabilities
- Fix approach: Implement sorting based on sales data or view count from analytics

**Missing Credential Refresh:**
- Issue: Self-healing service lacks credential refresh logic
- Files: `frontend/lib/autonomous/self-healing-service.ts` (line 160)
- Impact: API credentials may expire without refresh, causing autonomous operations to fail
- Fix approach: Implement credential refresh logic for external service APIs

**Incomplete Backend Persistence:**
- Issue: Settings page saves only to local storage, not backend API
- Files: `/page.tsx`frontend/app/admin/settings (line 116)
- Impact: Settings lost on browser clear/incognito, not synced across devices
- Fix approach: Add backend API integration for settings persistence

## Known Bugs

**Stripe Environment Issue:**
- Symptoms: Stripe initialization warnings in SSR/server environments
- Files: `src/lib/stripeIntegration.ts` (lines 142, 147, 148, 156)
- Trigger: Running code in non-browser environment without proper guards
- Workaround: Environment checks in place but logging noise persists

**WooCommerce Product Loader Null Returns:**
- Symptoms: Null returns for missing products or network errors
- Files: `src/collections/WooCommerceProductLoader.ts` (lines 147, 160, 179, 186, 197, 223, 246, 259, 276, 282, 296, 302, 322, 335, 408, 413)
- Trigger: Network failures, invalid product IDs, missing metadata
- Workaround: Proper null checking in calling code required

## Security Considerations

**Console Error Logging in Production:**
- Risk: Sensitive error details exposed via console statements in production
- Files: 232 console statements across the codebase (including `src/lib/checkout.ts`, `src/collections/WooCommerceProductLoader.ts`)
- Current mitigation: None - errors logged directly to console
- Recommendations: Use structured logging (Logger.ts already exists) with appropriate log levels for production

**Type Safety Gaps:**
- Risk: 33 usages of `any` type create potential runtime errors
- Files: Multiple files including `frontend/lib/wordpress/operations-manager.ts`, `frontend/lib/vercel/deployment-manager.ts`, `src/hooks/useCollectionProducts.ts`
- Current mitigation: Partial TypeScript coverage
- Recommendations: Replace `any` types with proper interfaces, especially in `frontend/lib/vercel/deployment-manager.ts` which has 5+ `any` usages

**Stripe Key Handling:**
- Risk: Test key exposed in test files
- Files: `src/lib/__tests__/stripeIntegration.test.ts` (line 92)
- Current mitigation: Uses test key (`pk_test_123`)
- Recommendations: Use environment variables for all API keys even in tests

## Performance Bottlenecks

**Large Collection Experience Classes:**
- Problem: Collection experience files exceed 1000 lines each
- Files: 
  - `src/collections/BlackRoseExperience.ts` (1148 lines)
  - `src/collections/LoveHurtsExperience.ts` (1134 lines)
  - `src/collections/SignatureExperience.ts` (1034 lines)
- Cause: Single Responsibility Principle violated, monolithic classes
- Improvement path: Extract common behavior into mixins/traits, separate product loading, scene setup, animation logic

**ModelAssetLoader Complexity:**
- Problem: 645-line file handling multiple responsibilities
- Files: `src/lib/ModelAssetLoader.ts`
- Cause: Loading, caching, progress tracking all in one class
- Improvement path: Split into ModelLoader, ModelCache, ProgressTracker

**BaseCollectionExperience Size:**
- Problem: 746-line base class with too many responsibilities
- Files: `src/collections/BaseCollectionExperience.ts`
- Cause: All collection types inherit from single base with full feature set
- Improvement path: Use composition over inheritance, create trait interfaces

## Fragile Areas

**WooCommerceProductLoader Error Handling:**
- Files: `src/collections/WooCommerceProductLoader.ts`
- Why fragile: 20+ null return paths with inconsistent error propagation
- Safe modification: Add Result types instead of nulls, use Either pattern
- Test coverage: Has tests but edge cases around network timeouts not covered

**Three.js Scene Initialization:**
- Files: `src/collections/BaseCollectionExperience.ts`, all collection experience files
- Why fragile: WebGL context loss/restore handling complex, many async load paths
- Safe modification: Add integration tests for context lifecycle
- Test coverage: Unit tests exist but no WebGL context simulation

**Checkout Flow:**
- Files: `src/lib/checkout.ts`, `frontend/app/api/checkout/route.ts`
- Why fragile: Multiple external dependencies (Stripe, WooCommerce), 9 catch blocks
- Safe modification: Add saga pattern for distributed transactions
- Test coverage: Missing E2E tests for failed payment scenarios

## Scaling Limits

**Agent Service Task Management:**
- Current capacity: In-memory Map storage for tasks
- Files: `src/services/AgentService.ts`
- Limit: No persistence, lost on restart; no task queue scaling
- Scaling path: Integrate with BullMQ (already in dependencies) for persistent task queue

**In-Memory Cart:**
- Current capacity: Browser memory only
- Files: `src/lib/cart.ts`, `src/hooks/useCart.ts`
- Limit: Lost on page refresh, no cross-device sync
- Scaling path: Persist to localStorage with sync to backend

## Dependencies at Risk

**Multiple AI SDK Versions:**
- Risk: `@ai-sdk/anthropic`, `@ai-sdk/openai`, `@ai-sdk/google` with different major versions
- Impact: API compatibility issues, potential runtime errors
- Migration plan: Standardize on unified AI SDK or pin specific versions

**Stripe Version Mismatch:**
- Risk: `stripe` (20.3.1) vs `@stripe/stripe-js` (8.8.0) - major version gap
- Impact: API incompatibility between server and client SDKs
- Migration plan: Align to compatible versions

**Three.js Version Fragmentation:**
- Risk: Root `package.json` uses ^0.182.0, frontend uses ^0.172.0
- Impact: Type incompatibilities, runtime issues with different versions
- Migration plan: Single version across all packages

**Deprecated Packages:**
- Risk: `mongoose` (9.0.1) - MongoDB driver moving to `@mongodb-js/sdk`
- Impact: Security updates may stop for older version
- Migration plan: Migrate to MongoDB Node.js driver v7+

## Missing Critical Features

**Error Recovery:**
- Problem: No retry logic for transient failures in API routes
- Blocks: Automatic retry on network timeout, rate limiting

**Circuit Breaker:**
- Problem: No circuit breaker pattern for external services
- Blocks: Cascading failure prevention when third-party APIs are down

**Distributed Tracing:**
- Problem: OpenTelemetry configured but not fully integrated
- Blocks: End-to-end request tracing across services

## Test Coverage Gaps

**Collection Experiences:**
- What's not tested: Context loss/restore, WebXR sessions, AR try-on
- Files: `src/collections/WebXRARViewer.ts`, `src/collections/ARTryOnViewer.ts`
- Risk: AR features could break without detection
- Priority: High (customer-facing feature)

**Admin Dashboard API:**
- What's not tested: Error responses, authentication failures
- Files: `frontend/app/api/*` routes
- Risk: API errors could return unexpected responses
- Priority: Medium

**Agent Service:**
- What's not tested: Task execution failures, agent recovery
- Files: `src/services/AgentService.ts`
- Risk: Agent failures not gracefully handled
- Priority: Medium

**Checkout Flow:**
- What's not tested: Payment failure scenarios, order creation failures
- Files: `src/lib/checkout.ts`, `frontend/app/api/checkout/route.ts`
- Risk: Failed payments could leave inconsistent state
- Priority: High

---

*Concerns audit: 2026-03-07*
