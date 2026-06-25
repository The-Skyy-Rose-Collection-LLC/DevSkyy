# Phase 2: Husky Foundation - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Install Husky v9 at the monorepo root so git hooks infrastructure is functional. A pre-commit hook must exist, be executable, and fire on `git commit`. Remove the broken Husky v4 config from the WordPress theme package.json. This phase is pure plumbing — Phase 3 adds the real lint/type-check scripts to hooks.

</domain>

<decisions>
## Implementation Decisions

### Hook scope
- Pre-commit hook contains a bare proof-of-life echo ("pre-commit hook active") — no lint/test logic
- Phase 3 owns the actual hook content (lint-staged, ESLint, ruff, etc.)
- Pre-commit only — no pre-push hook in this phase
- Root `package.json` prepare script chains both: `"prepare": "husky && npm run build"`

### WordPress theme cleanup
- Full removal of Husky from WordPress theme package.json:
  - Delete the `husky.hooks` block (lines 136-141) — broken v4 syntax
  - Remove `husky` from devDependencies (v8.0.3)
  - Remove `"prepare": "husky install"` script entirely (not replace with no-op)
- Run `npm install` in theme directory to regenerate package-lock.json without husky
- Theme's ESLint (v8) left alone — out of scope for this phase

### Verification approach
- Permanent verification script at `scripts/verify-hooks.sh`
- Script checks 3 things: `.husky/pre-commit` exists, is executable, and `git commit` triggers the hook (captures output)
- Useful for onboarding, debugging, and regression testing

### Claude's Discretion
- Exact echo message in pre-commit hook
- Whether to initialize Husky with `npx husky init` or manual setup
- Verification script implementation details (temp file strategy, cleanup)
- Whether existing .git/hooks/ files (post-checkout, post-commit, post-merge) need attention

</decisions>

<specifics>
## Specific Ideas

- User wants recommended/standard approaches throughout — no custom cleverness
- Phase 2 is "pure plumbing" — prove the hook system works, Phase 3 fills it with real checks
- Monorepo root manages all hooks — theme does not have its own Husky installation

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- Root `package.json` already has `husky: ^9.1.7` in devDependencies — just needs initialization
- Existing `"precommit"` script in root package.json (`npm run lint && npm run type-check && npm run test:ci`) — reference for Phase 3, not used now

### Established Patterns
- Root `"prepare"` script currently runs `"npm run build"` — will be chained with `husky`
- WordPress theme uses `scripts/` directory for utility scripts (matches verification script location)

### Integration Points
- `.husky/pre-commit` is the primary deliverable — must be created and executable
- Root `package.json` prepare script is the auto-install mechanism for collaborators
- WordPress theme `package.json` is the cleanup target (remove broken config)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-husky-foundation*
*Context gathered: 2026-03-08*
