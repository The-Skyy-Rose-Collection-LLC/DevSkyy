# Frontend Codemap

**Last Updated:** 2026-02-19
**Source of Truth:** `src/`, `frontend/`, `package.json`

## Structure

```
src/                               # TypeScript SDK (compiled via tsc)
|-- index.ts                       # Main SDK exports
|-- tsconfig.json                  # TypeScript config (SDK scope)
|
|-- collections/                   # 3D Collection Experiences (Three.js)
|   |-- index.ts                   # Collection exports
|   |-- BaseCollectionExperience.ts  # Abstract base for all collections
|   |-- BlackRoseExperience.ts     # Gothic rose garden (dark ambient, fog)
|   |-- SignatureExperience.ts     # Luxury outdoor (golden hour, butterflies)
|   |-- LoveHurtsExperience.ts    # Gothic castle (candlelight, stained glass)
|   |-- ShowroomExperience.ts     # Virtual showroom (spotlights, orbit)
|   |-- RunwayExperience.ts       # Fashion runway (catwalk, lighting rigs)
|   |-- ARTryOnViewer.ts          # AR try-on viewer
|   |-- WebXRARViewer.ts          # WebXR AR integration
|   |-- HotspotManager.ts         # Interactive 3D hotspots
|   |-- ProductionHandlers.ts     # Production event handlers
|   |-- EnvironmentTransition.ts  # Scene transition effects
|   |-- WooCommerceProductLoader.ts  # WooCommerce product data loader
|   `-- __tests__/                # Collection unit tests
|
|-- components/                    # React Three Fiber Components
|   |-- index.ts                   # Component exports
|   |-- CartModal.tsx              # Shopping cart modal
|   |-- ErrorBoundary.tsx          # React error boundary
|   |-- PriceTag3D.tsx            # 3D price tag overlay
|   |-- ProductConfigurator.tsx   # Product customization UI
|   |-- SuccessCelebration.tsx    # Purchase success animation
|   `-- __tests__/                # Component tests
|
|-- lib/                           # Core Libraries
|   |-- index.ts                   # Library exports
|   |-- cart.ts                    # Cart state management
|   |-- cartManager.ts            # Cart persistence and operations
|   |-- checkout.ts               # Checkout flow logic
|   |-- inventory.ts              # Inventory checking
|   |-- materialSwapper.ts        # Three.js material swap system
|   |-- ModelAssetLoader.ts       # 3D model loading (GLB/GLTF)
|   |-- priceUtils.ts             # Price formatting and calculations
|   |-- productInteraction.ts     # Product interaction handlers
|   |-- stripeIntegration.ts      # Stripe payment integration
|   |-- ThreePerformanceMonitor.ts  # Three.js performance tracking
|   |-- three/                    # Three.js utilities
|   `-- __mocks__/                # Test mocks
|
|-- hooks/                         # React Hooks
|   |-- useCart.ts                 # Cart state hook
|   |-- useCollectionProducts.ts  # Collection product fetching
|   |-- useProductFilters.ts      # Product filtering logic
|   `-- useScrollAnimation.ts     # Scroll-based animations
|
|-- services/                      # Frontend Services
|   |-- AgentService.ts           # AI agent communication
|   |-- OpenAIService.ts          # OpenAI API integration
|   |-- ThreeJSService.ts         # Three.js scene management
|   `-- __tests__/                # Service tests
|
|-- types/                         # TypeScript Type Definitions
|   |-- index.ts                   # Type exports
|   |-- collections.ts            # Collection types
|   `-- product.ts                # Product types
|
|-- config/                        # Frontend Configuration
|-- utils/                         # Utility functions
`-- app/                           # App-level setup

frontend/                          # Next.js Dashboard Application
|-- package.json                   # Frontend-specific dependencies
|-- next.config.ts                 # Next.js configuration
|-- tailwind.config.ts             # Tailwind CSS config
|-- postcss.config.js              # PostCSS config
|-- tsconfig.json                  # TypeScript config (Next.js scope)
|-- eslint.config.mjs              # ESLint config
|-- components.json                # shadcn/ui component config
|
|-- app/                           # Next.js App Router pages
|-- components/                    # React UI components
|-- contexts/                      # React context providers
|-- hooks/                         # Dashboard-specific hooks
|-- lib/                           # Dashboard utility libraries
|-- types/                         # Dashboard type definitions
`-- e2e/                           # End-to-end tests (Playwright)
```

## Key Modules

| Module | Purpose | Location |
|--------|---------|----------|
| `BaseCollectionExperience` | Abstract Three.js scene base class | `src/collections/BaseCollectionExperience.ts` |
| `BlackRoseExperience` | Gothic rose garden 3D scene | `src/collections/BlackRoseExperience.ts` |
| `SignatureExperience` | Luxury outdoor 3D scene | `src/collections/SignatureExperience.ts` |
| `LoveHurtsExperience` | Gothic castle 3D scene | `src/collections/LoveHurtsExperience.ts` |
| `ShowroomExperience` | Virtual showroom 3D scene | `src/collections/ShowroomExperience.ts` |
| `RunwayExperience` | Fashion runway 3D scene | `src/collections/RunwayExperience.ts` |
| `CartModal` | Shopping cart React component | `src/components/CartModal.tsx` |
| `ProductConfigurator` | Product customization component | `src/components/ProductConfigurator.tsx` |
| `ModelAssetLoader` | GLB/GLTF 3D model loader | `src/lib/ModelAssetLoader.ts` |
| `stripeIntegration` | Stripe checkout flow | `src/lib/stripeIntegration.ts` |
| `AgentService` | Backend agent communication | `src/services/AgentService.ts` |
| `ThreeJSService` | Three.js scene lifecycle | `src/services/ThreeJSService.ts` |

## Data Flow

1. **3D Collection Flow**: User visits collection page -> `BaseCollectionExperience` initializes Three.js scene -> Specific experience (e.g., `BlackRoseExperience`) renders environment -> `HotspotManager` adds interactive product hotspots -> `WooCommerceProductLoader` fetches product data -> `ProductConfigurator` allows customization -> `CartModal` manages cart -> `stripeIntegration` handles checkout.

2. **Dashboard Flow**: Next.js app renders pages via App Router -> React components consume data via hooks (`useCart`, `useCollectionProducts`) -> `AgentService` communicates with backend AI agents -> `OpenAIService` provides direct LLM access -> State managed via React contexts.

3. **Build Pipeline**: TypeScript source (`src/`) compiled via `tsc` to `dist/` using config at `config/typescript/tsconfig.json`. Tests run via Jest (`config/testing/jest.config.cjs`). Demos served via Vite (`config/vite/demo.config.ts`).

## NPM Scripts (from package.json)

| Script | Command | Purpose |
|--------|---------|---------|
| `dev` | `nodemon --exec "node --loader ts-node/esm src/index.ts"` | Development server with hot reload |
| `build` | `tsc --project config/typescript/tsconfig.json` | Compile TypeScript to JavaScript |
| `build:watch` | `tsc ... --watch` | Continuous TypeScript compilation |
| `start` | `node dist/index.js` | Run compiled production build |
| `test` | `jest --config config/testing/jest.config.cjs` | Run all tests |
| `test:watch` | `jest ... --watch` | TDD watch mode |
| `test:coverage` | `jest ... --coverage` | Tests with coverage report |
| `test:ci` | `jest ... --ci --coverage --watchAll=false` | CI pipeline test run |
| `test:collections` | `jest ... --testPathPatterns=collections --no-coverage` | Collection-only tests |
| `lint` | `eslint src/**/*.{ts,tsx,js,jsx}` | Check linting errors |
| `lint:fix` | `eslint ... --fix` | Auto-fix linting errors |
| `format` | `prettier --write "src/**/*.{ts,tsx,js,jsx}" "*.{json,md}"` | Format code |
| `format:check` | `prettier --check ...` | Verify formatting |
| `type-check` | `tsc ... --noEmit` | Type checking without emitting |
| `clean` | `rm -rf dist coverage` | Remove build artifacts |
| `precommit` | `lint && type-check && test:ci` | Pre-commit quality gate |
| `demo:collections` | Echo available demos | List demo options |
| `demo:black-rose` | `vite serve ... --collection=black_rose` | Black Rose 3D demo |
| `demo:signature` | `vite serve ... --collection=signature` | Signature 3D demo |
| `demo:love-hurts` | `vite serve ... --collection=love_hurts` | Love Hurts 3D demo |
| `demo:showroom` | `vite serve ... --collection=showroom` | Showroom 3D demo |
| `demo:runway` | `vite serve ... --collection=runway` | Runway 3D demo |
| `security:audit` | `npm audit` | Check for vulnerabilities |
| `security:fix` | `npm audit fix` | Auto-fix vulnerabilities |
| `deps:update` | `npm update` | Update dependencies |
| `deps:check` | `npm outdated` | Check for outdated packages |
| `prepare` | `npm run build` | Auto-build after install |

## Dependencies (Key External)

| Dependency | Version | Purpose |
|-----------|---------|---------|
| `three` | ^0.182.0 | 3D rendering engine |
| `@react-three/fiber` | ^9.5.0 | React Three.js renderer |
| `@react-three/drei` | ^10.7.7 | Three.js helpers for React |
| `react` / `react-dom` | ^19.2.3 | UI framework |
| `next` | 16.1.6 | Dashboard framework |
| `framer-motion` | ^12.30.0 | Animation library |
| `gsap` | ^3.14.2 | Advanced animation |
| `stripe` (via `stripeIntegration`) | -- | Payment processing |
| `tailwindcss` | ^4 | Utility-first CSS |
| `vite` | ^7.2.7 | Development server and bundler |
| `@sentry/nextjs` | ^10.38.0 | Error monitoring |
| `socket.io-client` | ^4.8.1 | WebSocket client |
| `typescript` | ^5.9.3 | Type system |
| `jest` | ^30.2.0 | Test runner |

## Configuration Files

| File | Purpose |
|------|---------|
| `config/typescript/tsconfig.json` | TypeScript compiler options |
| `config/testing/jest.config.cjs` | Jest test configuration |
| `config/vite/demo.config.ts` | Vite demo server configuration |
| `frontend/next.config.ts` | Next.js application config |
| `frontend/tailwind.config.ts` | Tailwind CSS customization |
| `frontend/components.json` | shadcn/ui component registry |
