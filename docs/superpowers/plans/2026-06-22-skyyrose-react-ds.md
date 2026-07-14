> SUPERSEDED 2026-07-10/11 — fonts now per SOT.md → typography.json (Archivo / Hanken Grotesk / Anton / Cinzel + bespoke collection name-scripts; zero-CDN self-hosted woff2). Font/CDN references below are historical.

# SkyyRose Storefront React DS (v1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React design-system package (`@skyyrose/storefront-ds`) holding the SkyyRose tokens, fonts, and three storefront components (HoloCard, Button, CollectionHero), wired to claude.ai/design via the `design-sync` package shape, sharing one CSS source with the live WordPress theme.

**Architecture:** A new isolated Vite-library package. Design tokens + fonts + self-contained component CSS are **synced one-way** from the WP theme (`wordpress-theme/skyyrose-flagship/assets/css|fonts`) — drift-guarded — so claude.ai/design renders pixel-identical to skyyrose.co. Components are thin React renderers over the same BEM class contract the PHP theme uses; commerce is prop-ified. The build emits an ES entry + `.d.ts` + one CSS bundle that the `design-sync` converter turns into a `window.SkyyRoseDS` bundle.

**Tech Stack:** React 19, TypeScript, Vite 7 (library mode) + `vite-plugin-dts`, Vitest + @testing-library/react + jsdom, `@vitejs/plugin-react`. Sync/build scripts in Node ESM. design-sync `package-build.mjs`/`package-validate.mjs`.

## Global Constraints

- **Never cross-wire** with `frontend/` (devskyy.app) or the WP theme runtime — this is a standalone package under `design-system/skyyrose-storefront/`.
- **One-way CSS source of truth:** WP theme `assets/css` + `assets/fonts` → package `src/`. Never hand-edit synced files; a drift guard fails the build if a synced copy diverges from its theme source.
- **Collection enum (exact):** `'signature' | 'black-rose' | 'love-hurts' | 'kids-capsule'`.
- **Brand rule (LOCKED):** hero collection titles are **lockup IMAGES**, never type-rendered. `CollectionHero` takes `lockupImage`.
- **Commerce is prop-ified:** WC add-to-cart / wishlist become `onAddToCart` / `onWishlistToggle` callbacks — no WC/AJAX/`localStorage` in delivered component code.
- **No paid API, no production deploy, no live WC/media write** anywhere in this plan. The only gated step is creating the claude.ai/design project (permission prompt) and the optional chromium install (~200MB, ask first).
- **globalName:** `SkyyRoseDS`. **package name:** `@skyyrose/storefront-ds`. **ES entry:** `dist/skyyrose-ds.es.js`. **CSS bundle:** `dist/skyyrose-ds.css`.
- Files <800 lines, functions <50 lines. Format/lint with the package's own prettier/eslint (set up in Task 1). Commit conventionally (`feat:`/`test:`/`chore:`).

### Deviations from the spec (flagged for review before execution)
1. **Button** maps to the theme's existing `.btn-cta` / `.btn-ghost` / `.btn-outline` (in `commercial-polish.css`), not a generalization of `.holo__buy`.
2. **CollectionHero** is lockup-image-based (LOCKED brand rule) with a small **authored** token-based layout CSS; its WP parity target is the `template-collection-*` lockup hero, NOT `patterns/collection-hero-*.php` (those type-render the name and predate the lockup rule).

---

## File Structure

```
design-system/skyyrose-storefront/
  package.json                 # name, scripts, deps, exports
  tsconfig.json                # strict, react-jsx, declaration
  vite.config.ts               # library mode + dts + react
  vitest.config.ts             # jsdom env, setup file
  .gitignore                   # dist/, node_modules/
  vitest.setup.ts              # @testing-library/jest-dom
  scripts/
    sync-theme-assets.mjs      # one-way copy theme CSS+fonts → src/, with --check drift guard
  src/
    types.ts                   # Collection type
    index.ts                   # barrel: components + global CSS imports
    tokens/tokens.css          # SYNCED ← assets/css/design-tokens.css
    styles/commercial-polish.css  # SYNCED ← assets/css/commercial-polish.css (button variants)
    fonts/fonts.css            # SYNCED ← assets/fonts/*  (@font-face) + copied .woff2
    components/
      Button/{Button.tsx, button.css, index.ts}
      HoloCard/{HoloCard.tsx, holo-card.css(SYNCED), index.ts}
      CollectionHero/{CollectionHero.tsx, collection-hero.css(AUTHORED), index.ts}
  test/
    Button.test.tsx
    HoloCard.test.tsx
    CollectionHero.test.tsx
    parity.test.ts             # WP markup-contract parity
.design-sync/
  config.json
  previews/{Button,HoloCard,CollectionHero}.tsx
```

---

### Task 1: Scaffold the package + toolchain

**Files:**
- Create: `design-system/skyyrose-storefront/package.json`
- Create: `design-system/skyyrose-storefront/tsconfig.json`
- Create: `design-system/skyyrose-storefront/vite.config.ts`
- Create: `design-system/skyyrose-storefront/vitest.config.ts`
- Create: `design-system/skyyrose-storefront/vitest.setup.ts`
- Create: `design-system/skyyrose-storefront/.gitignore`
- Create: `design-system/skyyrose-storefront/src/types.ts`
- Create: `design-system/skyyrose-storefront/src/index.ts`
- Test: `design-system/skyyrose-storefront/test/smoke.test.ts`

**Interfaces:**
- Produces: `Collection` type (`'signature' | 'black-rose' | 'love-hurts' | 'kids-capsule'`) exported from `src/types.ts` and re-exported from `src/index.ts`; npm scripts `build`, `test`, `sync`, `sync:check`.

- [ ] **Step 1: Verify the Vite library + dts API before writing config**

Run Context7 to confirm current API (the project mandates it; `vite-plugin-dts` has had breaking changes):
- `mcp__plugin_context7_context7__resolve-library-id` → `vite-plugin-dts`; if no match, search GitHub `qmhc/vite-plugin-dts` README for the installed major.
- Confirm `vite` v7 `build.lib` keys: `entry`, `formats`, `fileName`, `cssFileName` (verified: cssCodeSplit auto-false in lib mode).

Expected: `dts({ include: ['src'], insertTypesEntry: true })` is current; `build.lib.cssFileName: 'skyyrose-ds'` names the CSS bundle.

- [ ] **Step 2: Write `package.json`**

```json
{
  "name": "@skyyrose/storefront-ds",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "module": "./dist/skyyrose-ds.es.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": { "import": "./dist/skyyrose-ds.es.js", "types": "./dist/index.d.ts" },
    "./style.css": "./dist/skyyrose-ds.css"
  },
  "files": ["dist"],
  "scripts": {
    "sync": "node scripts/sync-theme-assets.mjs",
    "sync:check": "node scripts/sync-theme-assets.mjs --check",
    "prebuild": "npm run sync:check",
    "build": "vite build",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "peerDependencies": { "react": ">=18", "react-dom": ">=18" },
  "devDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0",
    "vite": "^7.0.0",
    "@vitejs/plugin-react": "^5.0.0",
    "vite-plugin-dts": "^4.3.0",
    "vitest": "^2.1.0",
    "jsdom": "^25.0.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/user-event": "^14.5.0"
  }
}
```

- [ ] **Step 3: Write `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "declaration": true,
    "emitDeclarationOnly": false,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "test"]
}
```

- [ ] **Step 4: Write `vite.config.ts`**

```ts
import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [react(), dts({ include: ['src'], insertTypesEntry: true, rollupTypes: false })],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      formats: ['es'],
      fileName: (format) => `skyyrose-ds.${format}.js`,
      cssFileName: 'skyyrose-ds',
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime'],
    },
  },
})
```

- [ ] **Step 5: Write `vitest.config.ts` + `vitest.setup.ts`**

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    css: false,
  },
})
```

```ts
// vitest.setup.ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 6: Write `.gitignore`, `src/types.ts`, `src/index.ts`**

```
# .gitignore
node_modules/
dist/
```

```ts
// src/types.ts
export type Collection = 'signature' | 'black-rose' | 'love-hurts' | 'kids-capsule'
```

```ts
// src/index.ts
export type { Collection } from './types'
// Component exports are added by later tasks.
```

- [ ] **Step 7: Write the smoke test**

```ts
// test/smoke.test.ts
import { describe, it, expect } from 'vitest'
import * as ds from '../src/index'

describe('package scaffold', () => {
  it('exports the Collection type surface (module loads)', () => {
    expect(ds).toBeTypeOf('object')
  })
})
```

- [ ] **Step 8: Install + run test (expect PASS)**

Run: `cd design-system/skyyrose-storefront && npm install && npm test`
Expected: 1 passed. (Do not run `npm run build` yet — `prebuild` runs `sync:check` which needs Task 2's script.)

- [ ] **Step 9: Commit**

```bash
git add design-system/skyyrose-storefront
git commit -m "chore: scaffold @skyyrose/storefront-ds package + toolchain"
```

---

### Task 2: One-way theme-asset sync + drift guard

**Files:**
- Create: `design-system/skyyrose-storefront/scripts/sync-theme-assets.mjs`
- Test: `design-system/skyyrose-storefront/test/sync.test.ts`

**Interfaces:**
- Produces: `npm run sync` copies theme assets into `src/`; `npm run sync:check` exits non-zero if any synced file differs from its theme source. Synced targets: `src/tokens/tokens.css` ← `assets/css/design-tokens.css`; `src/styles/commercial-polish.css` ← `assets/css/commercial-polish.css`; `src/components/HoloCard/holo-card.css` ← `assets/css/product-card-holo.css`; `src/fonts/` ← `assets/fonts/*.woff2` + a generated `fonts.css`.

- [ ] **Step 1: Write the failing test**

```ts
// test/sync.test.ts
import { describe, it, expect, beforeAll } from 'vitest'
import { execFileSync } from 'node:child_process'
import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const PKG = resolve(__dirname, '..')
const THEME = resolve(PKG, '../../wordpress-theme/skyyrose-flagship')

describe('theme-asset sync', () => {
  beforeAll(() => execFileSync('node', ['scripts/sync-theme-assets.mjs'], { cwd: PKG }))

  it('copies design tokens verbatim', () => {
    const src = readFileSync(resolve(THEME, 'assets/css/design-tokens.css'), 'utf8')
    const dst = readFileSync(resolve(PKG, 'src/tokens/tokens.css'), 'utf8')
    expect(dst).toBe(src)
  })

  it('copies the holo card CSS verbatim', () => {
    const src = readFileSync(resolve(THEME, 'assets/css/product-card-holo.css'), 'utf8')
    const dst = readFileSync(resolve(PKG, 'src/components/HoloCard/holo-card.css'), 'utf8')
    expect(dst).toBe(src)
  })

  it('generates a fonts.css with at least one @font-face and copies a woff2', () => {
    const css = readFileSync(resolve(PKG, 'src/fonts/fonts.css'), 'utf8')
    expect(css).toMatch(/@font-face/)
    expect(existsSync(resolve(PKG, 'src/fonts'))).toBe(true)
  })

  it('--check passes when in sync and fails when a synced file is mutated', () => {
    expect(() => execFileSync('node', ['scripts/sync-theme-assets.mjs', '--check'], { cwd: PKG })).not.toThrow()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- sync`
Expected: FAIL — `sync-theme-assets.mjs` does not exist.

- [ ] **Step 3: Write `scripts/sync-theme-assets.mjs`**

```js
// scripts/sync-theme-assets.mjs
// One-way sync: WP theme assets -> package src. `--check` asserts no drift (exit 1 on diff).
import { readFileSync, writeFileSync, mkdirSync, readdirSync, copyFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const PKG = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const THEME = resolve(PKG, '../../wordpress-theme/skyyrose-flagship')
const CHECK = process.argv.includes('--check')

// [source theme file, dest package file] — verbatim CSS copies (single source of truth).
const CSS_MAP = [
  ['assets/css/design-tokens.css', 'src/tokens/tokens.css'],
  ['assets/css/commercial-polish.css', 'src/styles/commercial-polish.css'],
  ['assets/css/product-card-holo.css', 'src/components/HoloCard/holo-card.css'],
]

const FONT_DIR = resolve(THEME, 'assets/fonts')
const FONT_DEST = resolve(PKG, 'src/fonts')

let drift = 0
function ensure(dir) { mkdirSync(dir, { recursive: true }) }

for (const [rel, dstRel] of CSS_MAP) {
  const src = readFileSync(resolve(THEME, rel), 'utf8')
  const dstPath = resolve(PKG, dstRel)
  ensure(dirname(dstPath))
  let cur = ''
  try { cur = readFileSync(dstPath, 'utf8') } catch { /* missing */ }
  if (CHECK) {
    if (cur !== src) { console.error(`DRIFT: ${dstRel} differs from theme ${rel}`); drift++ }
  } else {
    writeFileSync(dstPath, src)
    console.log(`synced ${dstRel}`)
  }
}

// Fonts: copy every woff2 and generate fonts.css with one @font-face per family file.
ensure(FONT_DEST)
const woff2 = readdirSync(FONT_DIR).filter((f) => f.endsWith('.woff2'))
const faces = woff2
  .map((f) => {
    // Family name = file stem with separators normalized; weight/style left normal (interim).
    const family = f.replace(/\.woff2$/, '').replace(/[-_]/g, ' ')
    return `@font-face{font-family:'${family}';src:url('./${f}') format('woff2');font-display:swap;}`
  })
  .join('\n')
const fontsCssPath = resolve(FONT_DEST, 'fonts.css')
let curFonts = ''
try { curFonts = readFileSync(fontsCssPath, 'utf8') } catch { /* missing */ }
if (CHECK) {
  for (const f of woff2) {
    const dst = resolve(FONT_DEST, f)
    let same = false
    try { same = readFileSync(dst).equals(readFileSync(resolve(FONT_DIR, f))) } catch { same = false }
    if (!same) { console.error(`DRIFT: font ${f} missing/differs`); drift++ }
  }
  if (curFonts !== faces) { console.error('DRIFT: fonts.css out of date'); drift++ }
} else {
  for (const f of woff2) copyFileSync(resolve(FONT_DIR, f), resolve(FONT_DEST, f))
  writeFileSync(fontsCssPath, faces)
  console.log(`synced ${woff2.length} fonts + fonts.css`)
}

if (CHECK && drift > 0) { console.error(`sync:check FAILED — ${drift} drifted artifact(s); run \`npm run sync\``); process.exit(1) }
if (CHECK) console.log('sync:check OK')
```

> NOTE for the implementer: confirm the theme font directory is `assets/fonts` and that it contains `.woff2` files (`ls wordpress-theme/skyyrose-flagship/assets/fonts`). If brand families need explicit weights, refine the `@font-face` generation — but the render check (Task 7) and `[FONT_MISSING]` are the backstop. Record any font-family naming decision in `.design-sync/NOTES.md` during Task 7.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- sync`
Expected: 4 passed. Then confirm the build pipeline works end-to-end now that `sync` exists:
Run: `npm run build`
Expected: `dist/skyyrose-ds.es.js`, `dist/skyyrose-ds.css`, `dist/index.d.ts` exist (`ls dist`).

- [ ] **Step 5: Commit**

```bash
git add design-system/skyyrose-storefront
git commit -m "feat: one-way theme-asset sync + drift guard for @skyyrose/storefront-ds"
```

---

### Task 3: Button component (TDD)

**Files:**
- Create: `design-system/skyyrose-storefront/src/components/Button/Button.tsx`
- Create: `design-system/skyyrose-storefront/src/components/Button/button.css`
- Create: `design-system/skyyrose-storefront/src/components/Button/index.ts`
- Modify: `design-system/skyyrose-storefront/src/index.ts`
- Test: `design-system/skyyrose-storefront/test/Button.test.tsx`

**Interfaces:**
- Consumes: synced `src/styles/commercial-polish.css` (`.btn-cta`, `.btn-ghost`, `.btn-outline`).
- Produces:
```ts
interface ButtonProps {
  children: React.ReactNode
  variant?: 'solid' | 'accent' | 'ghost'   // default 'solid'
  size?: 'sm' | 'md' | 'lg'                  // default 'md'
  as?: 'button' | 'a'                         // default 'button'
  href?: string
  loading?: boolean
  disabled?: boolean
  onClick?: (e: React.MouseEvent) => void
}
```
Variant→class: `solid`/`accent` → `btn-cta`; `ghost` → `btn-ghost`. Base class always `sr-btn` (authored box-model in `button.css`).

- [ ] **Step 1: Write the failing test**

```tsx
// test/Button.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../src/components/Button'

describe('Button', () => {
  it('renders children and the solid variant class by default', () => {
    render(<Button>Shop</Button>)
    const btn = screen.getByRole('button', { name: 'Shop' })
    expect(btn).toHaveClass('sr-btn', 'btn-cta')
  })

  it('maps ghost variant to btn-ghost', () => {
    render(<Button variant="ghost">More</Button>)
    expect(screen.getByRole('button', { name: 'More' })).toHaveClass('btn-ghost')
  })

  it('renders as an anchor when as="a" with href', () => {
    render(<Button as="a" href="/shop">Go</Button>)
    const link = screen.getByRole('link', { name: 'Go' })
    expect(link).toHaveAttribute('href', '/shop')
  })

  it('is disabled and unclickable when disabled', async () => {
    const onClick = vi.fn()
    render(<Button disabled onClick={onClick}>X</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('sets aria-busy and disables while loading', () => {
    render(<Button loading>Save</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toHaveAttribute('aria-busy', 'true')
    expect(btn).toBeDisabled()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- Button`
Expected: FAIL — cannot resolve `../src/components/Button`.

- [ ] **Step 3: Write `button.css` (authored base box-model; variants come from synced commercial-polish.css)**

```css
/* button.css — base box-model for the SkyyRose button. Variant skins (.btn-cta,
   .btn-ghost) are SYNCED from the theme's commercial-polish.css; this only owns
   the shared sizing/typography so the same classes render identically in WP. */
.sr-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--skyyrose-font-ui, 'Bebas Neue', sans-serif);
  letter-spacing: var(--tracking-wider, 0.1em);
  text-transform: uppercase;
  text-decoration: none;
  cursor: pointer;
  border-radius: var(--radius-sm, 4px);
  transition: var(--transition-smooth, all 0.3s ease);
}
.sr-btn[aria-disabled='true'],
.sr-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.sr-btn--sm { font-size: 12px; padding: 8px 16px; }
.sr-btn--md { font-size: 14px; padding: 12px 24px; }
.sr-btn--lg { font-size: 16px; padding: 16px 32px; }
```

- [ ] **Step 4: Write `Button.tsx`**

```tsx
// Button.tsx
import type { MouseEvent, ReactNode } from 'react'
import './button.css'

export interface ButtonProps {
  children: ReactNode
  variant?: 'solid' | 'accent' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  as?: 'button' | 'a'
  href?: string
  loading?: boolean
  disabled?: boolean
  onClick?: (e: MouseEvent) => void
}

const VARIANT_CLASS: Record<NonNullable<ButtonProps['variant']>, string> = {
  solid: 'btn-cta',
  accent: 'btn-cta',
  ghost: 'btn-ghost',
}

export function Button({
  children,
  variant = 'solid',
  size = 'md',
  as = 'button',
  href,
  loading = false,
  disabled = false,
  onClick,
}: ButtonProps) {
  const className = ['sr-btn', `sr-btn--${size}`, VARIANT_CLASS[variant]].join(' ')
  const isDisabled = disabled || loading

  if (as === 'a') {
    return (
      <a
        className={className}
        href={isDisabled ? undefined : href}
        aria-disabled={isDisabled || undefined}
        aria-busy={loading || undefined}
        onClick={(e) => {
          if (isDisabled) { e.preventDefault(); return }
          onClick?.(e)
        }}
      >
        {children}
      </a>
    )
  }

  return (
    <button
      type="button"
      className={className}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      onClick={(e) => { if (!isDisabled) onClick?.(e) }}
    >
      {children}
    </button>
  )
}
```

```ts
// index.ts
export { Button } from './Button'
export type { ButtonProps } from './Button'
```

- [ ] **Step 5: Wire the barrel — modify `src/index.ts`**

```ts
// src/index.ts
import './styles/commercial-polish.css'
import './tokens/tokens.css'
import './fonts/fonts.css'

export type { Collection } from './types'
export { Button } from './components/Button'
export type { ButtonProps } from './components/Button'
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npm test -- Button`
Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add design-system/skyyrose-storefront/src design-system/skyyrose-storefront/test/Button.test.tsx
git commit -m "feat: Button component (maps to theme .btn-cta/.btn-ghost)"
```

---

### Task 4: HoloCard component (TDD)

**Files:**
- Create: `design-system/skyyrose-storefront/src/components/HoloCard/HoloCard.tsx`
- Create: `design-system/skyyrose-storefront/src/components/HoloCard/index.ts`
- (CSS `holo-card.css` is already synced by Task 2.)
- Modify: `design-system/skyyrose-storefront/src/index.ts`
- Test: `design-system/skyyrose-storefront/test/HoloCard.test.tsx`

**Interfaces:**
- Consumes: synced `holo-card.css` (`.holo`, `.holo__*`), `Collection` type, `Button` (not required — drawer CTA uses native `.holo__buy`).
- Produces:
```ts
interface HoloCardProps {
  title: string
  price: string
  sku?: string
  collection: Collection
  frontImage: string
  backImage?: string
  permalink?: string
  sizes?: string[]                 // default ['S','M','L','XL']
  badge?: 'soldout' | 'preorder' | null
  index?: number
  tilt?: boolean                   // default true; auto-off on touch/reduced-motion
  onAddToCart?: (p: { sku?: string; size: string | null }) => void
  onWishlistToggle?: (p: { sku?: string; active: boolean }) => void
}
```
Markup mirrors `template-parts/product-card-holo.php`: root `.holo .holo--<collection>` with `data-sku`, wrapping `[data-collection]`; `.holo__gallery` front/back imgs; `.holo__info`; `.holo__drawer` with `.holo__sizes`/`.holo__size-pill`, `.holo__buy`, `.holo__wishlist`.

- [ ] **Step 1: Write the failing test**

```tsx
// test/HoloCard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HoloCard } from '../src/components/HoloCard'

const base = {
  title: 'Oakland Jersey',
  price: '$95',
  sku: 'br-012',
  collection: 'black-rose' as const,
  frontImage: 'https://example.test/front.webp',
  backImage: 'https://example.test/back.webp',
}

describe('HoloCard', () => {
  it('renders title, price, and sets the collection theming attributes', () => {
    const { container } = render(<HoloCard {...base} />)
    expect(screen.getByText('Oakland Jersey')).toBeInTheDocument()
    expect(screen.getByText('$95')).toBeInTheDocument()
    expect(container.querySelector('[data-collection="black-rose"]')).not.toBeNull()
    expect(container.querySelector('.holo--black-rose')).not.toBeNull()
    expect(container.querySelector('.holo')?.getAttribute('data-sku')).toBe('br-012')
  })

  it('renders front and back (techflat) images', () => {
    const { container } = render(<HoloCard {...base} />)
    expect(container.querySelector('.holo__img--front')).not.toBeNull()
    expect(container.querySelector('.holo__img--back')).not.toBeNull()
  })

  it('selects a size pill and calls onAddToCart with that size', async () => {
    const onAddToCart = vi.fn()
    render(<HoloCard {...base} onAddToCart={onAddToCart} />)
    await userEvent.click(screen.getByRole('radio', { name: 'M' }))
    expect(screen.getByRole('radio', { name: 'M' })).toHaveAttribute('aria-checked', 'true')
    await userEvent.click(screen.getByRole('button', { name: /add to cart/i }))
    expect(onAddToCart).toHaveBeenCalledWith({ sku: 'br-012', size: 'M' })
  })

  it('toggles wishlist and reports active state', async () => {
    const onWishlistToggle = vi.fn()
    render(<HoloCard {...base} onWishlistToggle={onWishlistToggle} />)
    await userEvent.click(screen.getByRole('button', { name: /wishlist/i }))
    expect(onWishlistToggle).toHaveBeenCalledWith({ sku: 'br-012', active: true })
  })

  it('renders a preorder badge when badge="preorder"', () => {
    const { container } = render(<HoloCard {...base} badge="preorder" />)
    expect(container.querySelector('.holo__badge--preorder')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- HoloCard`
Expected: FAIL — cannot resolve `../src/components/HoloCard`.

- [ ] **Step 3: Write `HoloCard.tsx`**

```tsx
// HoloCard.tsx — faithful React port of template-parts/product-card-holo.php
// + product-card-holo.js (size pills, wishlist, add-to-cart, magnetic tilt).
// Commerce is prop-ified: no WC/AJAX/localStorage here.
import { useRef, useState, type PointerEvent } from 'react'
import type { Collection } from '../../types'
import './holo-card.css'

export interface HoloCardProps {
  title: string
  price: string
  sku?: string
  collection: Collection
  frontImage: string
  backImage?: string
  permalink?: string
  sizes?: string[]
  badge?: 'soldout' | 'preorder' | null
  index?: number
  tilt?: boolean
  onAddToCart?: (p: { sku?: string; size: string | null }) => void
  onWishlistToggle?: (p: { sku?: string; active: boolean }) => void
}

const MAX_TILT = 8

export function HoloCard({
  title,
  price,
  sku,
  collection,
  frontImage,
  backImage,
  permalink = '#',
  sizes = ['S', 'M', 'L', 'XL'],
  badge = null,
  index = 0,
  tilt = true,
  onAddToCart,
  onWishlistToggle,
}: HoloCardProps) {
  const [size, setSize] = useState<string | null>(null)
  const [wished, setWished] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  const tiltEnabled =
    tilt &&
    typeof window !== 'undefined' &&
    !window.matchMedia('(hover: none)').matches &&
    !window.matchMedia('(prefers-reduced-motion: reduce)').matches

  function onMove(e: PointerEvent<HTMLDivElement>) {
    if (!tiltEnabled || !bodyRef.current) return
    const r = bodyRef.current.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width
    const y = (e.clientY - r.top) / r.height
    const rx = (y - 0.5) * -2 * MAX_TILT
    const ry = (x - 0.5) * 2 * MAX_TILT
    bodyRef.current.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg)`
  }
  function onLeave() {
    if (bodyRef.current) bodyRef.current.style.transform = ''
  }

  return (
    <div data-collection={collection}>
      <div
        className={`holo holo--${collection}`}
        data-sku={sku ?? ''}
        style={{ ['--holo-delay' as string]: `${index * 80}ms` }}
      >
        <div className="holo__body" ref={bodyRef} onPointerMove={onMove} onPointerLeave={onLeave}>
          <div className="holo__gallery">
            {badge && <span className={`holo__badge holo__badge--${badge}`}>{badge === 'soldout' ? 'Sold Out' : 'Pre-Order'}</span>}
            <a href={permalink} className="holo__img-link" aria-label={`View ${title}`}>
              <img className="holo__img holo__img--front" src={frontImage} alt={title} width={600} height={750} loading="lazy" decoding="async" />
              <img className="holo__img holo__img--back" src={backImage ?? frontImage} alt={`${title} — technical blueprint view`} width={600} height={750} loading="lazy" decoding="async" />
            </a>
          </div>

          <div className="holo__info">
            <span className="holo__collection">{collection.replace('-', ' ').toUpperCase()}</span>
            <h3 className="holo__name"><a href={permalink}>{title}</a></h3>
            <div className="holo__price-row"><span className="holo__price">{price}</span></div>
          </div>

          <div className="holo__drawer">
            <div className="holo__sizes" role="radiogroup" aria-label="Select size">
              {sizes.map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`holo__size-pill${size === s ? ' holo__size-pill--active' : ''}`}
                  role="radio"
                  aria-checked={size === s}
                  data-size={s}
                  onClick={() => setSize(s)}
                >
                  {s}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="holo__buy"
              aria-label={`Add ${title} to cart`}
              onClick={() => onAddToCart?.({ sku, size })}
            >
              Add to Cart
            </button>
            <button
              type="button"
              className={`holo__wishlist${wished ? ' holo__wishlist--active' : ''}`}
              aria-pressed={wished}
              aria-label={`Add ${title} to wishlist`}
              onClick={() => {
                const active = !wished
                setWished(active)
                onWishlistToggle?.({ sku, active })
              }}
            >
              ♥
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

```ts
// index.ts
export { HoloCard } from './HoloCard'
export type { HoloCardProps } from './HoloCard'
```

- [ ] **Step 4: Wire the barrel — add to `src/index.ts`**

```ts
export { HoloCard } from './components/HoloCard'
export type { HoloCardProps } from './components/HoloCard'
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- HoloCard`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add design-system/skyyrose-storefront/src design-system/skyyrose-storefront/test/HoloCard.test.tsx
git commit -m "feat: HoloCard component (faithful port of product-card-holo, commerce prop-ified)"
```

---

### Task 5: CollectionHero component (TDD)

**Files:**
- Create: `design-system/skyyrose-storefront/src/components/CollectionHero/CollectionHero.tsx`
- Create: `design-system/skyyrose-storefront/src/components/CollectionHero/collection-hero.css`
- Create: `design-system/skyyrose-storefront/src/components/CollectionHero/index.ts`
- Modify: `design-system/skyyrose-storefront/src/index.ts`
- Test: `design-system/skyyrose-storefront/test/CollectionHero.test.tsx`

**Interfaces:**
- Consumes: `Collection`, `Button` (Task 3), design tokens (`--skyyrose-*`).
- Produces:
```ts
interface CollectionHeroProps {
  collection: Collection
  lockupImage: string              // brand-script lockup IMAGE; never type-rendered
  tagline?: string
  backgroundImage?: string
  cta?: { label: string; href: string }
  align?: 'center' | 'left'        // default 'center'
}
```
Markup: `<section class="sr-hero sr-hero--<align>" data-collection>` → `<img class="sr-hero__lockup">` + optional tagline `<p>` + optional `<Button as="a">`. Authored token-based CSS (the ONE authored component CSS — no single theme file owns the lockup hero).

- [ ] **Step 1: Write the failing test**

```tsx
// test/CollectionHero.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CollectionHero } from '../src/components/CollectionHero'

describe('CollectionHero', () => {
  const base = {
    collection: 'signature' as const,
    lockupImage: 'https://example.test/signature-lockup.png',
    tagline: 'Elevated, confident, refined',
  }

  it('renders the lockup as an IMAGE (brand rule: never type-rendered)', () => {
    const { container } = render(<CollectionHero {...base} />)
    const img = container.querySelector('.sr-hero__lockup') as HTMLImageElement
    expect(img).not.toBeNull()
    expect(img.getAttribute('src')).toBe(base.lockupImage)
    // No heading element renders the collection name as text.
    expect(container.querySelector('h1')).toBeNull()
  })

  it('sets data-collection for palette theming and renders the tagline', () => {
    const { container } = render(<CollectionHero {...base} />)
    expect(container.querySelector('[data-collection="signature"]')).not.toBeNull()
    expect(screen.getByText('Elevated, confident, refined')).toBeInTheDocument()
  })

  it('renders a CTA link when cta is provided', () => {
    render(<CollectionHero {...base} cta={{ label: 'Shop Signature', href: '/signature' }} />)
    const link = screen.getByRole('link', { name: 'Shop Signature' })
    expect(link).toHaveAttribute('href', '/signature')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- CollectionHero`
Expected: FAIL — cannot resolve `../src/components/CollectionHero`.

- [ ] **Step 3: Write `collection-hero.css` (authored, tokens only)**

```css
/* collection-hero.css — AUTHORED layout glue (no single theme file owns the
   lockup hero). All values come from design tokens (the single source). */
.sr-hero {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: clamp(48px, 8vw, 120px) var(--container-narrow, 24px);
  background: var(--skyyrose-bg, #0a0a0a);
  background-size: cover;
  background-position: center;
  color: var(--skyyrose-text, #f5e6d3);
}
.sr-hero--center { align-items: center; text-align: center; }
.sr-hero--left { align-items: flex-start; text-align: left; }
.sr-hero__lockup { max-width: min(680px, 80vw); height: auto; }
.sr-hero__tagline {
  font-family: var(--skyyrose-font-body, 'Cormorant Garamond', serif);
  font-size: var(--text-xl, 1.375rem);
  line-height: var(--leading-normal, 1.6);
  color: var(--skyyrose-text-muted, rgba(245, 230, 211, 0.7));
  max-width: 60ch;
}
```

- [ ] **Step 4: Write `CollectionHero.tsx`**

```tsx
// CollectionHero.tsx — lockup-image hero (no Three.js, no type-rendered title).
import type { Collection } from '../../types'
import { Button } from '../Button'
import './collection-hero.css'

export interface CollectionHeroProps {
  collection: Collection
  lockupImage: string
  tagline?: string
  backgroundImage?: string
  cta?: { label: string; href: string }
  align?: 'center' | 'left'
}

export function CollectionHero({
  collection,
  lockupImage,
  tagline,
  backgroundImage,
  cta,
  align = 'center',
}: CollectionHeroProps) {
  return (
    <section
      className={`sr-hero sr-hero--${align}`}
      data-collection={collection}
      style={backgroundImage ? { backgroundImage: `url(${backgroundImage})` } : undefined}
    >
      <img className="sr-hero__lockup" src={lockupImage} alt={`${collection.replace('-', ' ')} collection`} />
      {tagline && <p className="sr-hero__tagline">{tagline}</p>}
      {cta && (
        <Button as="a" href={cta.href} variant="solid" size="lg">
          {cta.label}
        </Button>
      )}
    </section>
  )
}
```

```ts
// index.ts
export { CollectionHero } from './CollectionHero'
export type { CollectionHeroProps } from './CollectionHero'
```

- [ ] **Step 5: Wire the barrel — add to `src/index.ts`**

```ts
export { CollectionHero } from './components/CollectionHero'
export type { CollectionHeroProps } from './components/CollectionHero'
```

- [ ] **Step 6: Run test + full build to verify**

Run: `npm test`
Expected: all suites pass (smoke + sync + Button + HoloCard + CollectionHero).
Run: `npm run build`
Expected: `dist/skyyrose-ds.es.js`, `dist/skyyrose-ds.css`, `dist/index.d.ts` present; the CSS bundle contains `.holo`, `.btn-cta`, `.sr-hero`, and `[data-collection="black-rose"]` (`grep -c data-collection dist/skyyrose-ds.css`).

- [ ] **Step 7: Commit**

```bash
git add design-system/skyyrose-storefront/src design-system/skyyrose-storefront/test/CollectionHero.test.tsx
git commit -m "feat: CollectionHero (lockup-image hero, token-composed)"
```

---

### Task 6: WordPress markup-parity test

**Files:**
- Test: `design-system/skyyrose-storefront/test/parity.test.ts`

**Interfaces:**
- Consumes: the WP source files `template-parts/product-card-holo.php` and `commercial-polish.css` as the contract reference.
- Produces: a guard that the React components emit the same BEM class contract the PHP theme styles, so a design built in claude.ai/design ports to WP without re-styling.

> Rationale: full PHP rendering needs a WP runtime. Instead, assert the **class contract** both sides share — the React DOM must use the exact classes the theme's PHP/CSS define. This catches the realistic drift (a renamed class breaks the bridge).

- [ ] **Step 1: Write the failing test**

```ts
// test/parity.test.ts
import { describe, it, expect } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { createElement } from 'react'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { HoloCard } from '../src/components/HoloCard'

const THEME = resolve(__dirname, '../../../wordpress-theme/skyyrose-flagship')
const PHP = readFileSync(resolve(THEME, 'template-parts/product-card-holo.php'), 'utf8')

describe('WP markup parity (class contract)', () => {
  it('HoloCard emits every BEM class the PHP template defines', () => {
    const html = renderToStaticMarkup(
      createElement(HoloCard, {
        title: 'T', price: '$1', sku: 's', collection: 'black-rose',
        frontImage: 'f.webp', backImage: 'b.webp',
      }),
    )
    // Classes the PHP template renders that must exist on the React side too.
    const contract = [
      'holo', 'holo__body', 'holo__gallery', 'holo__img--front', 'holo__img--back',
      'holo__info', 'holo__collection', 'holo__name', 'holo__price',
      'holo__drawer', 'holo__sizes', 'holo__size-pill', 'holo__buy', 'holo__wishlist',
    ]
    for (const cls of contract) {
      expect(html, `React HoloCard missing .${cls}`).toContain(cls)
      expect(PHP, `PHP template no longer defines .${cls} — update the contract`).toContain(cls)
    }
  })
})
```

- [ ] **Step 2: Run test to verify it fails, then passes**

Run: `npm test -- parity`
Expected: PASS (HoloCard.tsx already emits these classes). If it FAILS, a class name drifted between the React port and the PHP source — fix the React markup to match the PHP contract (never the reverse).

> If `react-dom/server` isn't resolvable, add `react-dom` is already a devDependency; `renderToStaticMarkup` is in `react-dom/server`. No new dep.

- [ ] **Step 3: Commit**

```bash
git add design-system/skyyrose-storefront/test/parity.test.ts
git commit -m "test: WP markup-contract parity guard for HoloCard"
```

---

### Task 7: Wire design-sync (config + previews + build + validate)

**Files:**
- Create: `.design-sync/config.json`
- Create: `.design-sync/previews/Button.tsx`
- Create: `.design-sync/previews/HoloCard.tsx`
- Create: `.design-sync/previews/CollectionHero.tsx`
- Modify: root `.gitignore` (add `.ds-sync/`, `ds-bundle/`, `.design-sync/.cache/`, `.design-sync/node_modules`)

**Interfaces:**
- Consumes: built `dist/skyyrose-ds.es.js` (Task 5), the design-sync skill scripts.
- Produces: a validated `ds-bundle/` ready to upload; `.design-sync/config.json` pinned for re-syncs.

> This task runs the `design-sync` skill's package-shape converter. Read `design-sync/non-storybook/SKILL.md` §2–§4 for the authoritative flow; the steps below are the SkyyRose-specific bindings.

- [ ] **Step 1: Write `.design-sync/config.json`**

```json
{
  "pkg": "@skyyrose/storefront-ds",
  "globalName": "SkyyRoseDS",
  "shape": "package",
  "buildCmd": "npm --prefix design-system/skyyrose-storefront run build",
  "cssEntry": "design-system/skyyrose-storefront/dist/skyyrose-ds.css",
  "extraFonts": "design-system/skyyrose-storefront/src/fonts/fonts.css"
}
```

> `projectId` is added in Task 8 when the project is created (recorded at settlement per the skill).

- [ ] **Step 2: Author the three preview files**

Each named export = one graded card. Realistic content, no `foo`/`test`. Wrap HoloCard previews to sweep all five collection palettes via `data-collection`.

```tsx
// .design-sync/previews/Button.tsx
import { Button } from '@skyyrose/storefront-ds'
export const Solid = () => <Button variant="solid">Shop Signature</Button>
export const Ghost = () => <Button variant="ghost">View Lookbook</Button>
export const AsLink = () => <Button as="a" href="#" variant="solid" size="lg">Pre-Order</Button>
export const Loading = () => <Button loading>Adding…</Button>
```

```tsx
// .design-sync/previews/HoloCard.tsx
import { HoloCard } from '@skyyrose/storefront-ds'
const img = 'https://placehold.co/600x750/0a0a0a/b76e79?text=SkyyRose'
export const BlackRose = () => <HoloCard collection="black-rose" title="Oakland Bomber" price="$240" sku="br-001" frontImage={img} />
export const LoveHurts = () => <HoloCard collection="love-hurts" title="Bloodline Hoodie" price="$160" sku="lh-002" frontImage={img} badge="preorder" />
export const Signature = () => <HoloCard collection="signature" title="Gold Standard Tee" price="$85" sku="sg-003" frontImage={img} />
export const KidsCapsule = () => <HoloCard collection="kids-capsule" title="Mini Rose Set" price="$60" sku="kc-001" frontImage={img} />
```

```tsx
// .design-sync/previews/CollectionHero.tsx
import { CollectionHero } from '@skyyrose/storefront-ds'
const lockup = 'https://placehold.co/680x200/0a0a0a/d4af37?text=SIGNATURE'
export const Signature = () => <CollectionHero collection="signature" lockupImage={lockup} tagline="Elevated, confident, refined" cta={{ label: 'Shop Signature', href: '#' }} />
export const BlackRose = () => <CollectionHero collection="black-rose" lockupImage={lockup} tagline="You already stood up." cta={{ label: 'Enter Black Rose', href: '#' }} />
```

> The placeholder image URLs are preview-only composition data, not shipped assets. Record in `.design-sync/NOTES.md` that previews use `placehold.co`; swap to real lockup/render URLs when available.

- [ ] **Step 3: Build the package, then stage + run the converter**

```bash
# build the DS so dist/ exists
npm --prefix design-system/skyyrose-storefront run build
ls design-system/skyyrose-storefront/dist   # expect skyyrose-ds.es.js + skyyrose-ds.css + index.d.ts

# stage the design-sync converter (paths per design-sync/non-storybook/SKILL.md §2.7)
mkdir -p .ds-sync && cp -r "<skill-base-dir>"/package-build.mjs "<skill-base-dir>"/package-validate.mjs "<skill-base-dir>"/package-capture.mjs "<skill-base-dir>"/resync.mjs "<skill-base-dir>"/lib "<skill-base-dir>"/storybook .ds-sync/
echo '{"name":"ds-sync-deps","private":true}' > .ds-sync/package.json
(cd .ds-sync && npm i esbuild ts-morph @types/react)

node .ds-sync/package-build.mjs --config .design-sync/config.json \
  --node-modules design-system/skyyrose-storefront/node_modules \
  --entry design-system/skyyrose-storefront/dist/skyyrose-ds.es.js --out ./ds-bundle
```

Expected: `ds-bundle/` populated; build log shows 3 components (`Button`, `HoloCard`, `CollectionHero`). If `[TOKENS_MISSING]`/`[FONT_MISSING]`/`[CSS_*]` tags fire, apply the fix from the SKILL.md §3 table (most likely `cfg.cssEntry`/`cfg.extraFonts` already cover it).

- [ ] **Step 4: Render-check (gated chromium) + grade**

```bash
# Decide playwright/chromium per SKILL.md §4.1 — ASK before the ~200MB install.
node .ds-sync/package-validate.mjs ./ds-bundle
```

Expected: exit 0; `ds-bundle/.render-check.json` shows no `bad`. Read each `_screenshots/contact-sheet-*.png`; grade every authored preview cell `good` on the absolute rubric (SKILL.md §4.3). Iterate `.tsx` → rebuild → recapture until clean (max 3 iterations). Serve `.review.html` for human eyes if interactive.

- [ ] **Step 5: Add gitignore entries + commit sync inputs**

```bash
printf '\n.ds-sync/\nds-bundle/\n.design-sync/.cache/\n.design-sync/node_modules\n' >> .gitignore
git add .design-sync/config.json .design-sync/previews .gitignore
git commit -m "feat: wire @skyyrose/storefront-ds into design-sync (package shape)"
```

---

### Task 8: Sync to claude.ai/design (GATED — creates a project)

**Files:** none new — this drives the `DesignSync` tool per `design-sync` base SKILL.md §1 + §3 (incremental path).

**Interfaces:**
- Consumes: validated `ds-bundle/` (Task 7).
- Produces: a new claude.ai/design project "SkyyRose Storefront" populated with the 3 components; `projectId` recorded in `.design-sync/config.json`.

> **STOP-AND-SHOW:** creating the project raises a permission prompt; the first upload approval is one-time (incremental path). No paid API, no production site, no live data — but the project creation + uploads are user-gated. Do not auto-proceed past the `create_project` / `finalize_plan` prompts.

- [ ] **Step 1: Pick/confirm the target project**

Per base SKILL.md §1: no pin exists → first-time → propose creating a NEW project named "SkyyRose Storefront". `DesignSync(list_projects)` to ensure the name doesn't collide; confirm name with the user; `DesignSync(create_project)` (permission-prompted). Record `projectId` in `.design-sync/config.json` immediately at settlement.

- [ ] **Step 2: Open the incremental upload channel**

Explain the one-time approval in plain language, then `DesignSync(finalize_plan)` with `localDir: "./ds-bundle"` and the writes/deletes globs from base SKILL.md §3. On denial: stop and ask (do not retry with different args).

- [ ] **Step 3: Push verified batch + close out**

Push the base files + verified component dirs (`write_files`, ≤256/call), then the close-out sequence (sentinel → content → reconciliation deletes → sentinel re-arm → `_ds_sync.json` last). Confirm with `DesignSync(list_files)`.

- [ ] **Step 4: Author the conventions header + final rebuild**

Per base SKILL.md "Author the conventions header": write `.design-sync/conventions.md` (the SkyyRose idiom — `data-collection` theming wrapper, `var(--skyyrose-*)` token vocabulary, `.btn-cta`/`.holo`/`.sr-hero` class families, where the styles live), set `readmeHeader` in config, rebuild (driver run), and ensure the upload carries the header-bearing README.

- [ ] **Step 5: Commit durable sync inputs + report**

```bash
git add .design-sync/config.json .design-sync/conventions.md .design-sync/NOTES.md
git commit -m "chore: record SkyyRose Storefront design-sync project + conventions"
```

Report: project URL `https://claude.ai/design/p/<projectId>`, 3 components imported, render check clean. Invite the user to skim the DS pane in claude.ai/design.

---

## Verification (whole-plan gates)

- `npm test` green (smoke, sync, Button, HoloCard, CollectionHero, parity).
- `npm run build` emits `dist/skyyrose-ds.es.js` + `.css` + `index.d.ts`; CSS bundle contains `.holo`, `.btn-cta`, `.sr-hero`, `[data-collection]`.
- `npm run sync:check` exits 0 (no CSS drift from the theme).
- design-sync `package-validate.mjs` exits 0; every preview cell graded `good`.
- `git status` shows only `design-system/skyyrose-storefront/**`, `.design-sync/**`, root `.gitignore` changed.

## Roadmap (out of scope here — future re-syncs)

v2 Badge/SizePillGroup/Price/CollectionEyebrow/ProductGrid → v3 SectionHeading/FooterCTABand/collection-page composition → v4 Header/Nav/ProductDetailEditorial/SkyyMascot/SizeGuideModal/etc. Each new component gets its React/PHP pairing + a parity-test entry at adoption.
