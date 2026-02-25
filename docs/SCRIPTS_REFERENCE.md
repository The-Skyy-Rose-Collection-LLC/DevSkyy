# NPM Scripts Reference

**Total Scripts**: 46 (28 root + 18 frontend)
**Last Updated**: 2026-02-24
**Source**: `package.json` (v3.0.0), `frontend/package.json` (v1.0.0)

This document provides comprehensive reference for all npm scripts available in the DevSkyy platform.

---

## Development Scripts

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run dev` | `nodemon --exec "node --loader ts-node/esm src/index.ts"` | Start development server with hot reload | Local development, testing changes |
| `npm run build` | `tsc --project config/typescript/tsconfig.json` | Compile TypeScript to JavaScript | Before deployment, testing build |
| `npm run build:watch` | `tsc --project config/typescript/tsconfig.json --watch` | Compile TypeScript in watch mode | Active development, continuous compilation |
| `npm run start` | `node dist/index.js` | Start production server from compiled code | Production environment, testing built code |

**Development Workflow:**
1. `npm run dev` - Start development with hot reload
2. Make changes to TypeScript files
3. `npm run build` - Compile before deployment
4. `npm run start` - Test production build

---

## Testing Scripts

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm test` | `jest --config config/testing/jest.config.cjs` | Run all tests | Before commits, during development |
| `npm run test:watch` | `jest --config config/testing/jest.config.js --watch` | Run tests in watch mode | Active TDD, continuous testing |
| `npm run test:coverage` | `jest --config config/testing/jest.config.js --coverage` | Run tests with coverage report | Quality checks, coverage verification |
| `npm run test:ci` | `jest --config config/testing/jest.config.js --ci --coverage --watchAll=false` | Run tests in CI mode | CI/CD pipelines, automated testing |
| `npm run test:collections` | `jest --config config/testing/jest.config.cjs --testPathPatterns=collections --no-coverage` | Test 3D collection components | After collection changes |

**Test-Driven Development (TDD) Workflow:**
1. `npm run test:watch` - Start watch mode
2. Write failing test (RED)
3. Implement minimal code to pass (GREEN)
4. Refactor code (IMPROVE)
5. `npm run test:coverage` - Verify 80%+ coverage

**Coverage Requirements:**
- Minimum: 80% overall coverage
- Required for: All core modules, API endpoints, agents
- Exception: UI components (70% acceptable)

---

## Code Quality Scripts

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run lint` | `eslint src/**/*.{ts,tsx,js,jsx}` | Check code for linting errors | Before commits, code review |
| `npm run lint:fix` | `eslint src/**/*.{ts,tsx,js,jsx} --fix` | Auto-fix linting errors | Before commits, cleanup |
| `npm run format` | `prettier --write "src/**/*.{ts,tsx,js,jsx}" "*.{json,md}"` | Format code with Prettier | Before commits, code cleanup |
| `npm run format:check` | `prettier --check "src/**/*.{ts,tsx,js,jsx}" "*.{json,md}"` | Check code formatting | CI/CD, pre-commit hooks |
| `npm run type-check` | `tsc --project config/typescript/tsconfig.json --noEmit` | Check TypeScript types | Before commits, type safety |

**Pre-Commit Workflow (Mandatory):**
```bash
npm run lint:fix          # Auto-fix linting issues
npm run format            # Format code
npm run type-check        # Verify types
npm test                  # Run all tests
```

**Python Equivalent:**
```bash
isort .                   # Sort imports
ruff check --fix .        # Fix linting
black .                   # Format code
mypy .                    # Type check
pytest -v                 # Run tests
```

---

## Demo Scripts (3D Collections)

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run demo:collections` | `echo '🌹 SkyyRose Collection 3D Experiences Demo'...` | Show available demos | Discover demo options |
| `npm run demo:black-rose` | `npx vite serve --open --config config/vite/demo.config.ts -- --collection=black_rose` | Run Black Rose demo | Test Black Rose 3D experience |
| `npm run demo:signature` | `npx vite serve --open --config config/vite/demo.config.ts -- --collection=signature` | Run Signature demo | Test Signature collection |
| `npm run demo:love-hurts` | `npx vite serve --open --config config/vite/demo.config.ts -- --collection=love_hurts` | Run Love Hurts demo | Test Love Hurts experience |
| `npm run demo:showroom` | `npx vite serve --open --config config/vite/demo.config.ts -- --collection=showroom` | Run Showroom demo | Test virtual showroom |
| `npm run demo:runway` | `npx vite serve --open --config config/vite/demo.config.ts -- --collection=runway` | Run Runway demo | Test runway experience |

**Collection Demos:**
- **Black Rose**: Gothic cathedral immersive experience
- **Signature**: Oakland/San Francisco city tour
- **Love Hurts**: Romantic castle experience
- **Showroom**: Virtual product showroom
- **Runway**: Fashion runway experience

**Demo Workflow:**
1. `npm run demo:collections` - See available demos
2. Choose a collection demo (e.g., `npm run demo:black-rose`)
3. Browser opens automatically with 3D experience
4. Test interactions, performance, 3D models

---

## Maintenance Scripts

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run clean` | `rm -rf dist coverage` | Remove build artifacts | Before fresh build, cleanup |
| `npm run prepare` | `npm run build` | Build before npm install (automatic) | After `npm install`, preparing package |
| `npm run precommit` | `npm run lint && npm run type-check && npm run test:ci` | Run all pre-commit checks | Before git commits |
| `npm run security:audit` | `npm audit` | Check for security vulnerabilities | Regular security checks |
| `npm run security:fix` | `npm audit fix` | Auto-fix security vulnerabilities | After audit findings |
| `npm run deps:update` | `npm update` | Update dependencies to latest compatible | Regular maintenance |
| `npm run deps:check` | `npm outdated` | Check for outdated dependencies | Before updates, maintenance |

**Maintenance Schedule:**
- **Daily**: `npm run precommit` before each commit
- **Weekly**: `npm run security:audit`, review findings
- **Monthly**: `npm run deps:check`, plan updates
- **As Needed**: `npm run clean` if build issues occur

**Security Best Practices:**
1. Run `npm audit` before each release
2. Review vulnerabilities (not all auto-fix is safe)
3. Test after `npm audit fix`
4. Update dependencies regularly (avoid outdated packages)

---

## Script Categories Summary

| Category | Script Count | Purpose |
|----------|--------------|---------|
| **Development** | 4 | Build, watch, serve |
| **Testing** | 5 | Test execution, coverage |
| **Code Quality** | 5 | Linting, formatting, type checking |
| **Demo** | 6 | 3D collection demonstrations |
| **Maintenance** | 8 | Security, dependencies, cleanup |

**Root Total**: 28 scripts

### Frontend Scripts (`frontend/package.json`)

| Category | Count | Purpose |
|----------|-------|---------|
| **Development** | 4 | Next.js dev, build, start, lint |
| **Testing** | 2 | Playwright E2E tests |
| **Deployment** | 4 | Vercel deploy (preview + production) |
| **Vercel CLI** | 8 | Link, env sync, logs, inspect |

**Frontend Total**: 18 scripts
**Combined Total**: 46 scripts

---

## Quick Reference

### Daily Development
```bash
npm run dev              # Start development
npm run test:watch       # TDD workflow
npm run lint:fix         # Fix lint issues
```

### Before Commit
```bash
npm run precommit        # All checks (lint, types, tests)
# Or manually:
npm run lint:fix && npm run type-check && npm test
```

### Before Deployment
```bash
npm run clean            # Clean artifacts
npm run build            # Compile TypeScript
npm run test:ci          # CI tests with coverage
npm run security:audit   # Security check
npm run start            # Test production build
```

### Demo Testing
```bash
npm run demo:collections      # List all demos
npm run demo:black-rose       # Test specific collection
```

### Maintenance
```bash
npm run deps:check       # Check outdated packages
npm run security:audit   # Security vulnerabilities
npm run clean            # Clean build artifacts
```

---

## Frontend Scripts (`frontend/package.json`)

The Next.js frontend dashboard has its own scripts for development, testing, and Vercel deployment.

### Development

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run dev` | `next dev` | Start Next.js dev server | Frontend development |
| `npm run build` | `next build` | Build production bundle | Before deployment |
| `npm run start` | `next start` | Start production server | Testing prod build locally |
| `npm run lint` | `next lint` | Run ESLint | Code quality checks |

### Testing

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run test:e2e` | `playwright test` | Run Playwright E2E tests | Before deployment, CI |
| `npm run test:e2e:ui` | `playwright test --ui` | Run E2E tests with interactive UI | Debugging E2E failures |

### Deployment (Vercel)

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run deploy` | `vercel` | Deploy preview | Testing changes before prod |
| `npm run deploy:prod` | `vercel --prod` | Deploy to production | Production releases |
| `npm run deploy:auto` | `tsx scripts/deploy.ts` | Automated deploy script | CI/CD pipeline |
| `npm run deploy:auto:prod` | `tsx scripts/deploy.ts --prod` | Automated production deploy | CI/CD production pipeline |

### Vercel CLI Utilities

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| `npm run vercel:link` | `vercel link --project=devskyy` | Link to Vercel project | Initial setup |
| `npm run vercel:link:auto` | `./scripts/link-vercel-project.sh` | Auto-link script | CI setup |
| `npm run vercel:env:pull` | `vercel env pull .env.local` | Pull env vars from Vercel | Sync local env |
| `npm run vercel:env:push` | `vercel env push .env.production` | Push env vars to Vercel | Update prod secrets |
| `npm run vercel:logs` | `vercel logs` | View deployment logs | Debugging deployments |
| `npm run vercel:inspect` | `vercel inspect` | Inspect deployment | Checking deploy config |
| `npm run vercel:project` | `vercel project ls` | List Vercel projects | Project management |

**Frontend Workflow:**
```bash
cd frontend
npm run dev          # Start development
npm run lint         # Check quality
npm run test:e2e     # Run E2E tests
npm run build        # Build for production
npm run deploy:prod  # Deploy to Vercel
```

---

## Integration with Python Backend

DevSkyy uses both Node.js (frontend, demos) and Python (backend, ML). Here's how scripts align:

| Task | Node.js Script | Python Equivalent |
|------|---------------|-------------------|
| **Lint** | `npm run lint:fix` | `ruff check --fix .` |
| **Format** | `npm run format` | `black .` && `isort .` |
| **Type Check** | `npm run type-check` | `mypy .` |
| **Test** | `npm test` | `pytest -v` |
| **Coverage** | `npm run test:coverage` | `pytest --cov` |
| **Security** | `npm audit` | `pip-audit` |

**Unified Pre-Commit (Both Stacks):**
```bash
# Frontend (Node.js)
npm run lint:fix && npm run type-check && npm test

# Backend (Python)
isort . && ruff check --fix && black . && pytest -v
```

---

## Troubleshooting

### `npm run dev` fails to start

**Common Causes:**
- Port 3000 already in use
- Missing dependencies
- TypeScript compilation errors

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run type-check
```

### `npm test` fails with module errors

**Solution:**
```bash
# Clear Jest cache
npx jest --clearCache

# Reinstall dependencies
npm install

# Check test configuration
cat config/testing/jest.config.cjs
```

### `npm run build` fails

**Common Causes:**
- TypeScript errors
- Missing type definitions
- Import path issues

**Solution:**
```bash
# Check TypeScript errors
npm run type-check

# Verify tsconfig.json
cat config/typescript/tsconfig.json

# Clean and rebuild
npm run clean
npm run build
```

### Demo scripts fail to open browser

**Solution:**
```bash
# Manually open browser
npm run demo:black-rose
# Then open: http://localhost:5173

# Check Vite config
cat config/vite/demo.config.ts
```

---

## Script Hooks

### Pre-Commit Hook (`.husky/pre-commit`)

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint:fix
npm run type-check
npm test
```

### Post-Install Hook (Automatic)

The `prepare` script runs automatically after `npm install`:
```bash
npm install     # Triggers 'npm run prepare' -> 'npm run build'
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml
- name: Install dependencies
  run: npm ci

- name: Lint
  run: npm run lint

- name: Type check
  run: npm run type-check

- name: Test
  run: npm run test:ci

- name: Build
  run: npm run build
```

### Pre-Deployment Checklist

- [ ] `npm run clean` - Clean artifacts
- [ ] `npm run lint` - No linting errors
- [ ] `npm run type-check` - No type errors
- [ ] `npm run test:ci` - All tests pass, 80%+ coverage
- [ ] `npm run security:audit` - No high/critical vulnerabilities
- [ ] `npm run build` - Build succeeds
- [ ] `npm run start` - Production build works

---

**Document Owner**: DevSkyy Platform Team
**Next Review**: When scripts are added/modified
