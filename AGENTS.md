# Repository Guidelines

## Operating contract

1. Identify the requested outcome and the smallest file scope.
2. Before every task, search the available skills, plugins, agents, and MCPs for a capability that could execute the task effectively.
3. Select only a genuinely domain-specific, production-grade match; do not load or upload unrelated capability context.
4. Inspect current Git state and the authoritative SOT before editing.
5. Use the least expensive local tool that can answer the next question.
6. Edit source with `apply_patch`; regenerate tracked build outputs.
7. Run focused checks, inspect the diff, and report unverified runtime gates.
8. Stop before deployment, external uploads, private-key operations, or paid calls unless explicitly authorized and fully specified.

## Project Structure & Module Organization

DevSkyy is a mixed Python, TypeScript, Next.js, and WordPress monorepo.

- `main_enterprise.py`, `api/`, `agents/`, `orchestration/`: FastAPI and agent platform.
- `src/`: shared TypeScript services, commerce utilities, hooks, and Jest tests.
- `frontend/`: Next.js application; tests live in `frontend/tests/` and colocated files.
- `wordpress-theme/skyyrose-flagship/`: SkyyRose WooCommerce theme, PHP templates, assets, and PHPUnit tests.
- `wordpress-theme/skyyrose-flagship-2/`: release-candidate WordPress/WooCommerce theme. Treat it as separate from v1; do not copy v1 runtime assets or modify v1 while working on v2.
- `tests/`: Python unit, integration, security, and API tests.
- `docs/`: architecture, setup, testing, and operational documentation.
- `pipelines/`, `integrations/`, `security/`: 3D workflows, external systems, and security controls.

Keep generated files out of source directories unless build scripts intentionally track them.
Preserve unrelated worktree changes. Inspect the active worktree and branch before editing; the main checkout and a release-candidate worktree may have different state.

## Common paths

Use these direct paths before broad repository searches:

- `AGENTS.md` — repository instructions and safety gates.
- `tasks/todo.md` — local task ledger when the task is underspecified.
- `SOT.md` — repository source-of-truth index.
- `data/sot-images.json` — approved product-image mapping.
- `main_enterprise.py` — FastAPI application entry point.
- `api/v1/wordpress_integration.py` — WordPress integration boundary.
- `scripts/deploy-theme.sh` — deployment tooling; inspect only unless deployment is explicitly approved.
- `wordpress-theme/package.json` — theme tooling; its scripts target v1 unless a command says otherwise.
- `wordpress-theme/skyyrose-flagship-2/functions.php` — v2 bootstrap, routes, WooCommerce helpers, and enqueues.
- `wordpress-theme/skyyrose-flagship-2/style.css` — v2 theme metadata and version.
- `wordpress-theme/skyyrose-flagship-2/inc/product-3d-viewer.php` — fail-closed GLB resolver and viewer markup.
- `wordpress-theme/skyyrose-flagship-2/assets/sot/3d/approved-models.json` — only approved v2 product-model registry.
- `wordpress-theme/skyyrose-flagship-2/template-collection.php` — v2 collection-world template.
- `wordpress-theme/skyyrose-flagship-2/woocommerce/single-product.php` — v2 PDP wrapper.
- `wordpress-theme/skyyrose-flagship-2/scripts/package-theme.sh` — v2 archive builder; archives committed `HEAD`.
- `tests/` and `frontend/tests/` — Python and frontend test roots.

## Build, Test, and Development Commands

```bash
python -m uvicorn main_enterprise:app --reload --port 8000
pytest tests/ -v
npm run build
npm test
cd frontend && npm run dev
cd frontend && npm run test:e2e
cd wordpress-theme && npm run verify:full
```

Root `npm run lint`, `npm run type-check`, and `npm run format:check` validate TypeScript. Use `pytest tests/ --cov --cov-report=html` for Python coverage. Theme changes require rebuilding committed `.min.css` and `.min.js` outputs.

### WordPress v2 checks and packaging

The parent `wordpress-theme/package.json` build scripts target v1 (`skyyrose-flagship`), not v2. Do not run them expecting v2 output. For v2, edit source first and regenerate matching minified files:

```bash
find wordpress-theme/skyyrose-flagship-2 -name '*.php' -print0 | xargs -0 -n1 php -l
node --check wordpress-theme/skyyrose-flagship-2/assets/js/product-3d-viewer.js
node --check wordpress-theme/skyyrose-flagship-2/assets/js/product-3d-viewer.min.js
git diff --check
```

`wordpress-theme/skyyrose-flagship-2/scripts/package-theme.sh` archives `HEAD`, not an uncommitted worktree. Commit and inspect the scoped diff before creating or handing off a ZIP. Never deploy from an uncommitted tree.

## Coding Style & Naming Conventions

Python uses four spaces, type hints, `snake_case`, Ruff, Black, isort, and mypy. TypeScript uses project ESLint/Prettier rules, `camelCase` functions, and `PascalCase` components/classes. WordPress PHP follows WPCS: prefix functions and hooks with `skyyrose_`, escape output, sanitize input, and use tabs for indentation.

Never add secrets, credentials, production URLs, or generated customer data. Never print, persist, or commit API keys, private keys, trust-root private material, or customer data. If a secret appears in chat or shell history, treat it as exposed and recommend rotation; do not echo it back.

## Source of truth and asset safety

- SOT manifests and current approved production imagery are authoritative. Product cards and WooCommerce product pages must use real approved product imagery; never invent filenames, substitute stock art, or silently replace v1 imagery with unverified renders.
- A product GLB may ship only through the committed v2 `assets/sot/3d/approved-models.json` manifest. The resolver must fail closed on missing or malformed SKU, URL, model hash, five required reference hashes (`front`, `back`, `left`, `right`, `detail-1`), provenance approval, policy-collector approval, founder approval, or gate approval.
- The v2 3D viewer is progressive enhancement: poster/no-JS fallback first, viewport-gated loading, self-hosted dependencies, Save-Data and reduced-motion support, keyboard-accessible controls, and no model viewer library on pages without an approved model.
- Do not trigger paid image, video, 3D, model, CDN, or provider operations while implementing or verifying code. Use existing local/SOT assets and static tests first. A paid call requires explicit user approval, confirmed asset specification, cost/credit check, and fail-closed verification plan.
- Do not produce renders merely to fill an empty manifest. An empty approved-model manifest is a valid safe state until a real product model passes visual identity checks and all approvals.

## Token, agent, and cost discipline

Every tool or agent call must be purpose-built and token-aware:

- State the immediate artifact needed before calling a tool; use the smallest useful file range, output limit, timeout, and search scope.
- Prefer `rg`, targeted reads, `git diff --check`, local syntax checks, and existing scripts over broad scans or repeated full-suite runs. Do not redo delegated work while its result is pending.
- Parallelize independent read-only checks when possible, but never parallelize overlapping edits, deployment, destructive operations, or paid provider calls.
- Reuse agents only when the next task depends on their context; close completed agents before opening another so concurrency is not wasted. Assign disjoint file ownership and require concise evidence-backed handoffs.
- Use independent verification after implementation when risk is material. A verifier must inspect the actual worktree and rerun checks; prose claims are not evidence.
- Do not use `pip install`, `npm install`, `npx`, Context7, remote research, or paid APIs just to explore when local code, lockfiles, cached packages, or static checks answer the question. If a dependency download is genuinely necessary, ask for approval when it may incur cost and record why.
- Never spend money or credits to resolve uncertainty that can be handled by a local fail-closed fallback, manifest miss, static audit, or user decision.
- Keep commentary concise and report only evidence needed for the next decision; avoid dumping entire files, logs, or dependency bundles into context.

## Capability loading policy

Load or upload a skill, agent, plugin, or MCP only when the requested job contains a domain-specific piece that capability can execute to a production-grade standard. A keyword match is not enough.

The capability search is mandatory before every task, even when the result is “no suitable capability.” Searching does not authorize loading, uploading, dispatching, or invoking anything.

- Use the smallest relevant capability set. Do not preload skill catalogs, agent context, plugin bundles, or MCP resources for ordinary file inspection, simple edits, or questions answerable from the repository.
- Read the selected skill instructions completely before acting, then load only the directly required references, scripts, or assets. Do not upload unrelated files or duplicate context already available locally.
- Dispatch an agent only for a bounded, materially useful task with explicit file ownership or verification scope. Do not delegate a one-command check, duplicate an active worker, or leave completed agents open against the concurrency limit.
- Use a plugin only when its underlying capability directly performs the requested domain work; inspect its scope before invocation and do not invoke unrelated bundled tools.
- Use an MCP only when it provides the required domain operation or authoritative external state. Prefer deterministic local checks first; do not use remote MCPs for exploration when local evidence is sufficient.
- Never invoke a paid provider, remote generation, upload, or metered MCP to fill an empty state or resolve uncertainty. Require explicit approval, a known cost, exact inputs, and a verification gate before any potentially billable call.
- For parallel work, make read-only checks independent and keep edit scopes disjoint. Stop and report a blocker when a capability requires new authority, external access, or a paid action outside the user request.

### Tool decision order

Use this order unless the task explicitly requires otherwise:

1. `git status`, `git diff`, `rg`, `rg --files`, and targeted reads.
2. Local syntax, unit, lint, and build checks for the changed surface.
3. Existing local scripts and cached dependencies.
4. A narrowly scoped agent or domain capability with explicit ownership.
5. Browser/staging verification when the environment and authorization exist.
6. Remote, metered, upload, or paid operations only after approval and a cost gate.

Do not escalate merely because a command is convenient. Record the reason when a download, remote call, agent, or full-suite run is necessary.

## Testing Guidelines

Name Python tests `test_*.py`; use `@pytest.mark.unit`, `integration`, `asyncio`, or `slow`. TypeScript tests use `*.test.ts` or `*.test.tsx`. Add regression coverage for every bug. Run focused tests during development, then relevant full suite before review.

For theme work, verify the route matrix when staging is available: homepage, collections index, all four collection routes, shop, pre-order, About, contact, product detail, cart, checkout, account, and fallback content/404. A static pass is not a browser or WooCommerce staging pass; label unavailable runtime checks as unverified.

## Commit & Pull Request Guidelines

History follows Conventional Commit-style subjects: `feat(theme): ...`, `fix(theme): ...`, `docs: ...`, `chore(wolf): ...`. Use imperative, scoped summaries.

Pull requests need problem statement, implementation summary, test evidence, linked issue/bug ID, and screenshots or recordings for UI changes. Note migrations, environment changes, security impact, and deployment steps. Never deploy WordPress or production services without explicit approval. “Finish” or “package” does not authorize deployment or paid asset generation.

## Trust, approval, and deployment gates

- Founder/legal-owner approval covers redistribution rights for supplied films and muted derivatives; retain written authorization as evidence, but never treat it as permission to invent or redistribute unrelated assets.
- Founder, build-attestor, and policy-collector public trust roots are verification inputs. Private keys remain outside the repository; validate key algorithms and resulting files before use.
- The 3D/replica pipeline is downstream of WordPress integration. Finish and verify the WP fallback/resolver contract first; do not send assets to a provider until exact product, approved references, destination, collection assignment, and cost gates are confirmed.
- “Ready” means code checks pass and relevant staging/browser/accessibility/visual/SOT evidence exists. Never claim every page is complete from source inspection alone.
