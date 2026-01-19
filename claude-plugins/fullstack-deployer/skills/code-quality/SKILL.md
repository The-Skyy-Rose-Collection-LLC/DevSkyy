# Code Quality

This skill provides comprehensive knowledge for maintaining code quality in Next.js/TypeScript projects. It activates when users mention "eslint", "prettier", "linting", "code quality", "type errors", "typescript errors", "formatting", "code standards", or encounter linting/type errors.

---

## ESLint Configuration

### Setup for Next.js
```bash
# ESLint comes pre-configured with Next.js
# For additional rules:
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-plugin-import
```

### .eslintrc.json
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "plugin:import/recommended",
    "plugin:import/typescript",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "import"],
  "rules": {
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "off",
    "import/order": [
      "error",
      {
        "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
        "newlines-between": "always",
        "alphabetize": { "order": "asc" }
      }
    ],
    "import/no-duplicates": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  },
  "settings": {
    "import/resolver": {
      "typescript": true,
      "node": true
    }
  }
}
```

### .eslintignore
```
node_modules
.next
out
public
*.config.js
*.config.mjs
```

## Prettier Configuration

### Setup
```bash
npm install -D prettier eslint-config-prettier
```

### .prettierrc
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

### .prettierignore
```
node_modules
.next
out
public
package-lock.json
pnpm-lock.yaml
```

## TypeScript Configuration

### tsconfig.json for Next.js
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./*"]
    },
    "forceConsistentCasingInFileNames": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Strict Type Checking Options
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true
  }
}
```

## Package.json Scripts

```json
{
  "scripts": {
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit",
    "quality": "npm run typecheck && npm run lint && npm run format:check",
    "quality:fix": "npm run lint:fix && npm run format"
  }
}
```

## Common ESLint Errors and Fixes

### "React Hook useEffect has missing dependencies"
```typescript
// ❌ Bad
useEffect(() => {
  fetchData(id)
}, []) // Missing 'id' dependency

// ✅ Good
useEffect(() => {
  fetchData(id)
}, [id])

// ✅ Or if intentional, disable rule with comment
useEffect(() => {
  fetchData(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [])
```

### "@typescript-eslint/no-unused-vars"
```typescript
// ❌ Bad
const unused = 'value'

// ✅ Good - prefix with underscore if intentionally unused
const _unused = 'value'

// ✅ Or remove the variable entirely
```

### "import/no-unresolved"
```typescript
// Check tsconfig.json paths are configured
// Check eslint import/resolver settings
// Verify package is installed
```

### "'React' must be in scope"
```typescript
// In Next.js with React 17+, this is not required
// Update .eslintrc.json:
{
  "rules": {
    "react/react-in-jsx-scope": "off"
  }
}
```

## Common TypeScript Errors and Fixes

### "Type 'X' is not assignable to type 'Y'"
```typescript
// ❌ Bad
const data: User = fetchData() // fetchData returns unknown

// ✅ Good - add type assertion or proper typing
const data = fetchData() as User
// Or better:
const data: User = await fetchData<User>()
```

### "Object is possibly 'undefined'"
```typescript
// ❌ Bad
const name = user.profile.name // profile might be undefined

// ✅ Good - optional chaining
const name = user.profile?.name

// ✅ Or null check
if (user.profile) {
  const name = user.profile.name
}

// ✅ Or non-null assertion (if you're certain)
const name = user.profile!.name
```

### "Property 'X' does not exist on type 'Y'"
```typescript
// Define proper types
interface ApiResponse {
  data: Product[]
  meta: { total: number }
}

// ❌ Bad
const response = await fetch('/api/products')
const json = await response.json() // json is 'any'
console.log(json.data) // No type safety

// ✅ Good
const json: ApiResponse = await response.json()
console.log(json.data) // Type-safe
```

### "Argument of type 'X' is not assignable to parameter of type 'Y'"
```typescript
// ❌ Bad
function processId(id: number) { }
processId("123") // Error: string not assignable to number

// ✅ Good
processId(parseInt("123", 10))
// Or fix the function signature
function processId(id: number | string) { }
```

## Husky + lint-staged Setup

### Install
```bash
npm install -D husky lint-staged
npx husky init
```

### .husky/pre-commit
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx lint-staged
```

### package.json lint-staged config
```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml}": [
      "prettier --write"
    ]
  }
}
```

## VS Code Settings

### .vscode/settings.json
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

### .vscode/extensions.json
```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss"
  ]
}
```

## Code Quality Commands

```bash
# Check TypeScript
npx tsc --noEmit

# Run ESLint
npm run lint

# Fix ESLint issues automatically
npm run lint -- --fix

# Check formatting
npx prettier --check .

# Fix formatting
npx prettier --write .

# Run all checks
npm run quality

# Fix all auto-fixable issues
npm run quality:fix
```

## Autonomous Quality Fix Steps

When encountering code quality issues:

1. **Run TypeScript check first**: `npx tsc --noEmit`
2. **If type errors**:
   - Read error message and file location
   - Check if types are properly defined
   - Add missing type definitions or fix type mismatches
3. **Run ESLint**: `npm run lint`
4. **If linting errors**:
   - Try auto-fix first: `npm run lint -- --fix`
   - For remaining errors, fix manually based on rule
   - Use Context7 to understand specific ESLint rules
5. **Run Prettier**: `npx prettier --check .`
6. **If formatting issues**:
   - Auto-fix: `npx prettier --write .`
7. **Re-run all checks** to verify fixes
8. **If stuck on specific error**:
   - Use Context7 to search for the error message
   - Check if it's a known issue with workaround
