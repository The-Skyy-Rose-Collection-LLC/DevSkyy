# Graph Report - /Users/theceo/DevSkyy/knowledge-base  (2026-05-03)

## Corpus Check
- Corpus is ~12,941 words - fits in a single context window. You may not need a graph.

## Summary
- 97 nodes · 153 edges · 11 communities detected
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `Anti-Patterns: Confirmed Failure Modes (15 entries)` - 23 edges
2. `ADR 0002: Cost-Cap Hybrid Policy` - 15 edges
3. `Seed Index: Serena Memories` - 11 edges
4. `Trusted Reference Set (16 Canonical Sources)` - 9 edges
5. `ADR 0001: V2 Locked Decisions — Page-Level and Architectural` - 9 edges
6. `Seed Index: GSD Artifacts (.planning/)` - 8 edges
7. `AP-01: Wrong Source Data Driving Everything Downstream` - 8 edges
8. `AP-02: Creating a Second Source of Truth for Product Data` - 8 edges
9. `Skyyrose V2 Knowledge Base README` - 7 edges
10. `Seed Index: claude-mem Observations` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Trusted Ref: WooCommerce (developer.woocommerce.com)` --conceptually_related_to--> `PHP Catalog Reader: skyyrose_get_product_catalog() in inc/product-catalog.php`  [INFERRED]
  knowledge-base/references/trusted-set.md → knowledge-base/lessons/anti-patterns.md
- `Trusted Ref: Three.js (threejs.org/docs)` --semantically_similar_to--> `claude-mem: Three.js / Immersive Experiences Observations`  [INFERRED] [semantically similar]
  knowledge-base/references/trusted-set.md → knowledge-base/seed/from-claude-mem.md
- `AP-04: Calling External APIs Without Checking Cost First` --semantically_similar_to--> `ADR 0002: The $1 Threshold Rule`  [INFERRED] [semantically similar]
  knowledge-base/lessons/anti-patterns.md → knowledge-base/decisions/0002-cost-cap-hybrid-policy.md
- `GSD: .planning/research/PITFALLS.md (HIGH VALUE)` --semantically_similar_to--> `AP-01: Wrong Source Data Driving Everything Downstream`  [INFERRED] [semantically similar]
  knowledge-base/seed/from-gsd.md → knowledge-base/lessons/anti-patterns.md
- `Wolf cerebrum.md: Do-Not-Repeat Section` --semantically_similar_to--> `Anti-Patterns: Confirmed Failure Modes (15 entries)`  [INFERRED] [semantically similar]
  knowledge-base/seed/from-openwolf.md → knowledge-base/lessons/anti-patterns.md

## Hyperedges (group relationships)
- **Four Canonical Catalog Readers — All Point to Same CSV** — catalog_loader_php, catalog_loader_python, catalog_loader_nanobana, catalog_loader_elite_studio [EXTRACTED 1.00]
- **Six Integrated Knowledge Layers for Context Retrieval** — readme_six_layer_system, from_serena_seed, from_gsd_seed, from_openwolf_seed, from_claude_mem_seed, graphify_out_graph_json [EXTRACTED 1.00]
- **Catalog Integrity Anti-Pattern Cluster (AP-01, AP-02, AP-07, AP-12)** — ap_01_wrong_source_data, ap_02_second_sot, ap_07_wc_get_products, ap_12_hardcoded_skus [INFERRED 0.92]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (16): Seed Index: GSD Artifacts (.planning/), Knowledge Graph Output: graphify-out/graph.json, GSD: .planning/codebase/ARCHITECTURE.md, GSD: Phase 14 PATTERNS.md (Highest-Value), GSD: .planning/PROJECT.md (Charter), GSD: .planning/render-pipeline-architecture.md, GSD: .planning/RETROSPECTIVE.md, GSD: .planning/handoffs/trellis2-deployment.md (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (14): ADR 0001: V2 Locked Decisions — Page-Level and Architectural, ADR 0001 §1.2: Architectural Locked Decisions Table, ADR 0001: How to Propose Change to Locked Decision, ADR 0001 §1.1: Page-Level Locked Decisions Table, Rationale: Locked Decisions Prevent Scope Creep and Re-litigation, Trusted Ref: Accessibility WCAG (w3.org/WAI/WCAG22), Trusted Ref: Anthropic Claude API (docs.anthropic.com), Trusted Ref: FASHN (fashn.ai/docs) (+6 more)

### Community 2 - "Community 2"
Cohesion: 0.28
Nodes (13): Anti-Patterns: Confirmed Failure Modes (15 entries), AP-03: Moving Forward with Unfixed Errors, AP-06: Implicit Namespace Packages (Missing __init__.py), AP-08: Reading Library Docs from Memory Instead of Context7, AP-09: Installing ADK into Main .venv/, AP-11: Skipping PHP Lint Before WordPress Theme Commits, AP-14: Formatter Wars (ruff vs black on assert wrapping), AP-15: Writing Stubs, TODOs, or Partial Implementations (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.32
Nodes (12): AP-01: Wrong Source Data Driving Everything Downstream, AP-02: Creating a Second Source of Truth for Product Data, AP-07: Using wc_get_products() in Templates for Catalog Data, AP-12: Hardcoding SKUs in PHP Templates, Elite Studio Catalog Reader: skyyrose.elite_studio.catalog.Catalog, Nano Banana Catalog Reader: nano_banana.catalog.load_catalog, PHP Catalog Reader: skyyrose_get_product_catalog() in inc/product-catalog.php, Python Catalog Reader: skyyrose.core.catalog_loader (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.2
Nodes (10): cmem #572: Compositor retrofit instrument-first over full refactor, cmem #581: Real data required for product replica pipeline, cmem #852: catalog.py silent skips converted to loud errors, claude-mem: Catalog / SKU / Dossier Observations, claude-mem: Decision-Type Observations (Highest-Value), claude-mem: Pipeline / Imagery / Compositor Observations, claude-mem: Three.js / Immersive Experiences Observations, claude-mem: WordPress/WooCommerce/PHP Theme Observations (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (10): ADR 0002: Cost-Cap Hybrid Policy, ADR 0002: Per-API Classification Table, ADR 0002: STOP-AND-SHOW Manifest Format, ADR 0002 Rejected: Option A — Always Autonomous, ADR 0002 Rejected: Option B — Always Confirm, Rationale: Option C (Hybrid) Over Always-Autonomous or Always-Confirm, ADR 0002: The $1 Threshold Rule, AP-04: Calling External APIs Without Checking Cost First (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.29
Nodes (7): AP-05: Deploying to Production Without Dry-Run Verification, Deploy Script: scripts/deploy-theme.sh, Seed Index: OpenWolf System (.wolf/), Wolf buglog.json: Deploy Script Bug Cluster (bug-058 to bug-064), Wolf buglog.json (95 bugs), Wolf cerebrum.md: Key Learnings Section, Wolf cerebrum.md: Source of Truth Section

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (6): AP-10: Modifying innerHTML Instead of DOM Construction, Seed Index: Serena Memories, Serena: api_v1_endpoints_structure.md, Serena: clothing_3d_generation_patterns.md, Serena: mcp_server_audit_2026_01_07.md, Serena: production_audit_findings.md

### Community 8 - "Community 8"
Cohesion: 0.4
Nodes (6): AP-13: Trusting X-Tenant-ID Header Without Verification, cmem #1185: Tenant middleware JWT without verification (pre-fix), cmem #1193: Tenant spoofing vulnerability fixed (HMAC-verified), claude-mem: Security Observations, Serena: SECURITY_CRITICAL_ISSUE_RESOLVED.md, Core Middleware: core/middleware/tenant.py (HMAC-verified X-Tenant-ID)

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (2): Loop Stats KPI Tracker: scripts/measurement/loop-stats.js, Layer 6 Meta-KPI Tracking (loop-stats.js)

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): GSD: .planning/codebase/CONVENTIONS.md

## Knowledge Gaps
- **34 isolated node(s):** `KB Pattern Entry Schema`, `KB Lesson Entry Schema`, `KB Decision Entry Schema (ADR-style)`, `Cross-Reference Conventions Table`, `Layer 6 Meta-KPI Tracking (loop-stats.js)` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 9`** (2 nodes): `Loop Stats KPI Tracker: scripts/measurement/loop-stats.js`, `Layer 6 Meta-KPI Tracking (loop-stats.js)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (1 nodes): `GSD: .planning/codebase/CONVENTIONS.md`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Anti-Patterns: Confirmed Failure Modes (15 entries)` connect `Community 2` to `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `ADR 0002: Cost-Cap Hybrid Policy` connect `Community 5` to `Community 1`, `Community 7`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `KB Pattern Entry Schema`, `KB Lesson Entry Schema`, `KB Decision Entry Schema (ADR-style)` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._