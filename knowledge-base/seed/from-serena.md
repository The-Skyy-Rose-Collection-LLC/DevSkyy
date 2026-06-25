# Seed Index: Serena Memories (`.serena/memories/`)

**Phase 0 seeding date:** 2026-05-03
**Total memories:** 29 files
**How to use:** When a task matches a category below, load the corresponding Serena memory into context via `Read .serena/memories/<filename>` before beginning work. These are pointer entries — full content lives in the memory file, not here.

---

## Coding Standards & Workflow

### `coding_standards.md`
- **Covers:** Production-only code mandate (no placeholders, no stubs), Three.js CDN version lock (`three@0.160.0`), WordPress PHP validation checklist, quality gates.
- **Relevant for:** Any Three.js integration, any WordPress PHP file, any API endpoint implementation.
- `[serena: coding_standards]`

### `CRITICAL_WORKFLOW_DIRECTIVE.md`
- **Covers:** "DO NOT MOVE ON UNTIL ALL ERRORS ARE FIXED" — stop-on-error mandate established 2025-12-25. TypeScript, linting, ruff violations all block forward progress. Sequential fix-verify-proceed protocol.
- **Relevant for:** Any task where a pre-commit hook or CI check fails; debugging sessions where the temptation is to push through.
- `[serena: CRITICAL_WORKFLOW_DIRECTIVE]`

### `error_handling_protocol.md`
- **Covers:** 4-step error protocol: Acknowledge → Fix → Harden → Verify. Anti-patterns list (`continue-on-error: true`, skipping failing tests, moving on with "will fix later").
- **Relevant for:** CI failures, test failures, runtime exceptions, build errors — any error class.
- `[serena: error_handling_protocol]`

### `user_expectations.md`
- **Covers:** Context7 on EVERY task (mandatory), no over-analysis, working solutions first time, production quality immediately. 3D viewer requirements (real clothing shapes, OrbitControls, SkyyRose brand colors).
- **Relevant for:** Any session kickoff; serves as the "what the user will judge you against" reminder.
- `[serena: user_expectations]`

---

## Project Facts (Catalog / SKU / URLs)

### `canonical_catalog_source_of_truth.md`
- **Covers:** THE canonical catalog file (`data/skyyrose-catalog.csv`), all four reader paths (Python `catalog_loader`, Nano Banana, Elite Studio, PHP helpers), 21-column schema, retired SKU codes, retired source files (deleted 2026-04-19), open hardcoded-SKU issues in 3 frontend admin pages.
- **Relevant for:** Any catalog/SKU/pricing work, any pipeline that reads product data, any PHP template rendering products.
- `[serena: canonical_catalog_source_of_truth]`

### `skyyrose_url.md`
- **Covers:** Primary URL: `skyyrose.co`. Disambiguation of the two sites.
- **Relevant for:** Deploy targets, API endpoint construction, CORS config.
- `[serena: skyyrose_url]`

### `woocommerce_api_credentials.md`
- **Covers:** WooCommerce Client ID (123138) and credential setup for REST API access.
- **Relevant for:** WooCommerce REST API calls, product/order write operations.
- `[serena: woocommerce_api_credentials]`

---

## Architecture & Deployment

### `production_audit_findings.md`
- **Covers:** Grade B+ (7.8/10) architecture audit. 6 SuperAgents, 21 MCP tools. 5 known open issues: CSP `unsafe-inline`, missing input validation before tool execution, no timeout on Round Table parallel LLM calls, in-memory rate limiting (not distributed), ~30 console.log in frontend. Component score table (Backend Core 8.5, Security 9.0, Frontend 7.5).
- **Relevant for:** Security reviews, production readiness checks, any work touching gateway/middleware/auth.
- `[serena: production_audit_findings]`

### `api_v1_endpoints_structure.md`
- **Covers:** All `/api/v1/` routers (dashboard, tasks, round_table, brand, tools), Pydantic models for all request/response, AgentRegistry pattern, frontend API client map (`frontend/lib/api.ts`).
- **Relevant for:** API endpoint work, adding new routes, frontend ↔ backend integration, agent execution.
- `[serena: api_v1_endpoints_structure]`

### `skyyrose_deployment_status.md`
- **Covers:** Final deployment status snapshot (2025-12-25). Base state for understanding what was live at that point.
- **Relevant for:** Understanding deployment history; checking what was deployed and when.
- `[serena: skyyrose_deployment_status]`

### `wordpress_deployment_status.md`
- **Covers:** WordPress deployment completion record — what was deployed and confirmed working.
- **Relevant for:** WordPress deploy planning; confirming what's already live.
- `[serena: wordpress_deployment_status]`

### `wordpress_theme_current.md`
- **Covers:** Current state of `skyyrose-flagship` theme (version 3.2.0 as of this memory's write date — NOTE: version has since advanced; verify in `style.css` before citing).
- **Relevant for:** Theme version references, understanding baseline state before current V2 build.
- `[serena: wordpress_theme_current]`

### `skyyrose_wordpress_child_theme_deployment.md`
- **Covers:** Deployment guide for the WordPress child theme (package location, SFTP deploy steps).
- **Relevant for:** Any deploy that involves the WordPress theme.
- `[serena: skyyrose_wordpress_child_theme_deployment]`

### `skyyrose-child-theme-architecture.md`
- **Covers:** Research summary for immersive child theme architecture — how Three.js scenes integrate with the WP theme.
- **Relevant for:** Immersive template work, Three.js ↔ WordPress integration patterns.
- `[serena: skyyrose-child-theme-architecture]`

---

## Audit Findings

### `SECURITY_CRITICAL_ISSUE_RESOLVED.md`
- **Covers:** Critical resolved issue: `.env.secrets` and `.env.secrets.backup` were accidentally tracked by git (exposed API keys). Resolution: `git rm --cached`, deleted files, enhanced `.gitignore`. Follow-up actions still open as of this memory's date: key rotation review, git history audit.
- **Relevant for:** Any security review, any `.env` file handling, any git history concerns.
- `[serena: SECURITY_CRITICAL_ISSUE_RESOLVED]`

### `mcp_server_audit_2026_01_07.md`
- **Covers:** MCP server audit findings from January 2026. 21 tools in `devskyy_mcp.py`.
- **Relevant for:** MCP tool additions, DevSkyy MCP architecture understanding.
- `[serena: mcp_server_audit_2026_01_07]`

### `enterprise_cleanup_phase2_2026_01_07.md`
- **Covers:** Dead code cleanup phase 2 — what was removed and why.
- **Relevant for:** Understanding what's been cleaned up; avoiding resurrection of deleted code.
- `[serena: enterprise_cleanup_phase2_2026_01_07]`

---

## MCP Setup

### `devskyy_mcp_critical_fuchsia_ape_setup.md`
- **Covers:** DevSkyy MCP server (Critical Fuchsia Ape) — configuration status and setup details.
- **Relevant for:** MCP server troubleshooting, MCP tool availability.
- `[serena: devskyy_mcp_critical_fuchsia_ape_setup]`

### `devskyy_mcp_skyyrose_complete_setup.md`
- **Covers:** Complete MCP setup for SkyyRose integration — all tools and their configurations.
- **Relevant for:** Full MCP tool inventory, integration with SkyyRose pipelines.
- `[serena: devskyy_mcp_skyyrose_complete_setup]`

### `phase3_wordpress_mcp_integration_2026_01_07.md`
- **Covers:** Phase 3 WordPress MCP integration — completion record.
- **Relevant for:** WordPress ↔ MCP bridge understanding; what was integrated in Phase 3.
- `[serena: phase3_wordpress_mcp_integration_2026_01_07]`

---

## Implementation Notes (Pipeline / Feature-Specific)

### `advanced_2d_25d_visualization_techniques_2026_01_08.md`
- **Covers:** 2D/2.5D product visualization techniques — research and implementation patterns for product display.
- **Relevant for:** Product visualization work, image display patterns, alternative to full 3D.
- `[serena: advanced_2d_25d_visualization_techniques_2026_01_08]`

### `clothing_3d_generation_patterns.md`
- **Covers:** Filter logic to identify actual clothing items (vs accessories) for 3D model generation eligibility. Garment type classification patterns.
- **Relevant for:** 3D generation pipeline, batch processing SKUs for 3D, filtering what qualifies for 3D generation.
- `[serena: clothing_3d_generation_patterns]`

### `collection_experiences_requirements.md`
- **Covers:** Requirements for collection interactive experiences — what each collection page must provide.
- **Relevant for:** Collection page builds (Phase 1–2), experience template implementation.
- `[serena: collection_experiences_requirements]`

### `interactive_collection_pages_requirements.md`
- **Covers:** Requirements for interactive collection pages (created 2026-01-11) — scroll behaviors, product cards, filter interactions.
- **Relevant for:** Collection page design and build work.
- `[serena: interactive_collection_pages_requirements]`

### `ralph_wiggums_implementation_2026_01_07.md`
- **Covers:** Ralph-Wiggums error loop implementation — retry/fallback logic in MCP server and LLM Round Table.
- **Relevant for:** Error recovery patterns, LLM retry logic, MCP error handling.
- `[serena: ralph_wiggums_implementation_2026_01_07]`

### `spinning_logo_implementation.md`
- **Covers:** SkyyRose spinning logo implementation — Three.js/CSS animation for brand mark.
- **Relevant for:** Logo animation, brand identity elements in Three.js scenes.
- `[serena: spinning_logo_implementation]`

### `agent_count_fix_2026_01_07.md`
- **Covers:** Dynamic agent count fix (problem and solution) — moved from hardcoded to `orchestration/agent_counter.py`.
- **Relevant for:** Agent registry work, agent count display, dynamic agent loading.
- `[serena: agent_count_fix_2026_01_07]`

### `branch_consolidation_phase1_2026_01_07.md`
- **Covers:** Branch consolidation Phase 1 completion record (2026-01-07).
- **Relevant for:** Git history reference; understanding what was consolidated.
- `[serena: branch_consolidation_phase1_2026_01_07]`

### `dashboard_configuration_2026_01_07.md`
- **Covers:** DevSkyy dashboard configuration overview (2026-01-07).
- **Relevant for:** Dashboard setup, frontend configuration.
- `[serena: dashboard_configuration_2026_01_07]`

---

## Highest-Leverage Memories (read these first in any new session)

| Priority | Memory | Why |
|----------|--------|-----|
| 1 | `canonical_catalog_source_of_truth.md` | Every product task starts here |
| 2 | `CRITICAL_WORKFLOW_DIRECTIVE.md` | Governs error handling posture |
| 3 | `user_expectations.md` | Quality bar and Context7 mandate |
| 4 | `error_handling_protocol.md` | How to respond to any failure |
| 5 | `production_audit_findings.md` | What's already known to be broken |
| 6 | `SECURITY_CRITICAL_ISSUE_RESOLVED.md` | Security posture baseline |
| 7 | `coding_standards.md` | Code quality rules |
| 8 | `api_v1_endpoints_structure.md` | API architecture reference |
