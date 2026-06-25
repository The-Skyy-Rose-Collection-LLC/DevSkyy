# Skyyrose V2 — Plan Index (Cross-Reference)

This is the navigation map between the two source-of-truth planning documents. When the 6-step per-edit workflow's Step 0 needs to find authoritative guidance for a task, it grep's both plans plus this index. **Always check this index first** — it answers "which plan owns this question?" so you don't waste time searching the wrong document.

---

## The two source documents

| Document | Scope | Owns |
|----------|-------|------|
| `docs/SKYYROSE_V2_MASTER_PLAN.md` | Architecture envelope, all phases, all integrations | Operating contract, locked decisions, integration architecture, agent orchestration, phase exit criteria, per-page accountability table, risk matrix |
| `docs/SKYYROSE_WORDPRESS_PLAN.md` | WordPress.com customer surfaces only | Brand story canon, 5-pass thinking protocol, banned-elements rule, compound learning loop, commercial protocols matrix, per-page editorial briefs, critique cycle, KPI dashboard |
| `.claude/plans/merry-shimmying-moonbeam.md` | This build's operationalized plan | Unified Phase 0 deliverable list, grill resolutions, MCP integration decisions, cost-cap policy, source-of-truth pointers |

---

## Decision authority by topic

When a question arises, look here first:

| Topic | Authoritative source | Section |
|-------|---------------------|---------|
| **Operating contract / motto** | V2 master | §0.1 |
| **Gates G1, G2, G3** | V2 master | §0.2 |
| **6-step per-edit workflow** | V2 master | §0.3 |
| **AGENTS.md scope rules** | V2 master | §0.4 |
| **Definition of Done per phase** | V2 master | §0.5 |
| **Page-level locked decisions** (faq, cart, checkout, collections, etc.) | V2 master | §1.1 |
| **Architectural locked decisions** (WP↔Vercel split, FASHN cost cap, Pinecone cadence) | V2 master | §1.2 |
| **Cost-cap thresholds** (Anthropic, AIDesigner, FASHN, Pinecone) | `eval/cost-cap-policy.md` (supersedes V2 §1.3) | hybrid stance per Phase 0 grill Branch 1 |
| **Thesis & differentiators** (WebGL × XR × Drop × AR × Editorial) | V2 master | §2 |
| **Integration architecture** (WP↔Vercel HMAC, route inventory) | V2 master | §3 |
| **Agent & skill orchestration map** (which skill to use when) | V2 master | §4 |
| **Phase 0 → Phase 7 execution phases** | V2 master | §5 |
| **Per-page accountability** (29 → 27 final state per page) | V2 master | §6 |
| **Critical files to read per phase** | V2 master | §7 |
| **Eval framework overview** | V2 master | §8 |
| **Risk matrix** | V2 master | §9 |
| **Quality controller (7 pillars)** | V2 master | §10 |
| **Brand story canon** (Skyyrose voice, NOT-list, Oakland references) | WP plan | §2 |
| **5-pass thinking protocol** (per-page brand/commercial/critique/luxury/technical) | WP plan | §1.1 |
| **Critique loop questions** (the 7 self-critique questions) | WP plan | §1.2 |
| **Banned-by-default elements** (centered hero, 4-col grid, "Shop Now" hero, etc.) | WP plan | §1.3 |
| **Compound learning loop** (KB layers 1–7) | WP plan | §1.5 |
| **Trusted reference set** (16 canonical doc domains) | WP plan | §1.5.4 |
| **Anti-pattern guard** (7 seeded anti-patterns) | WP plan | §1.5 Layer 5 |
| **§3 critique structure** (per-surface audit format) | WP plan | §3.1, §3.2, §3.3 |
| **Commercial protocols matrix** (payments, privacy, a11y, SEO, perf, conversion, trust, inventory, CX, measurement) | WP plan | §4.1–§4.10 |
| **Design system tokens** (colors, type, spacing, radius, shadow, motion) | WP plan | §5.1 |
| **Component primitives** (the 10 components every page composes from) | WP plan | §5.2 |
| **Premium feel checklist** (10 small-moves that compound) | WP plan | §5.3 |
| **Per-page design briefs** (homepage, PDP, cart, collections, etc.) | WP plan | §6.1–§6.10 |
| **Critique-implement-critique cycle** | WP plan | §7.1 |
| **Three personas** ($3K jacket buyer / true believer / cold skeptic) | WP plan | §7.2 |
| **"Would Corey wear this?" filter** | WP plan | §7.3 |
| **WP-0 brand & critique foundation** | WP plan | §8 Phase WP-0 |
| **WP-0.5 measurement provisioning** (access packet, baselines, monitoring) | WP plan | §8 Phase WP-0.5 |
| **KPI dashboard** (10 KPIs with 30/90-day targets) | WP plan | §9 |
| **Governing sentence** ("honor the customer + earn the price tag") | WP plan | §10 |

---

## Cross-document inheritance

The two plans are interlocking, not redundant. Where they overlap:

| Topic | WP plan says | V2 master says | Resolution |
|-------|--------------|----------------|------------|
| Phase numbering | WP-0 → WP-8 | Phase 0 → Phase 7 | **V2 numbering wins.** Operationalized plan uses Phase 0 / 0.5 / 1 / 1.5 / 2 / 3 / 4 / 5 / 6 / 7. WP-N is alias only. |
| Phase 0 deliverables | 8 foundation deliverables (brand, critique, design system, KB, etc.) | 6 eval rubric files (templates, integrations, marketplace, shocking, brand, page-flow) | **Both ship.** Unified Phase 0 delivers union per `.claude/plans/merry-shimmying-moonbeam.md`. |
| Phase 0.5 timing | After G1 | Pre-flight prerequisites (autonomous) | **WP plan wins.** Phase 0.5 happens after G1; pre-flight checks roll into Phase 0.5.a alongside measurement provisioning. |
| Component primitives location | `template-parts/components/*.php` (10 files) | Not specified | WP plan owns component spec; built in Phase 0 (advisor-flagged for foundation timing). |
| Tokens filename | `assets/css/tokens.css` | Not specified | **Existing repo convention wins:** `assets/css/design-tokens.css` (already on disk with min + sourcemap). Phase 0 extends, doesn't create parallel. |
| Cost caps | Not specified | V2 §1.3 thresholds | **`eval/cost-cap-policy.md` supersedes both.** Hybrid stance: >$1 STOP-AND-SHOW, ≤$1 autonomous to V2 thresholds. |
| Trusted reference set | WP §1.5.4 (16 domains) | Not specified | WP plan owns. Persisted to `knowledge-base/references/trusted-set.md` in Phase 0. |
| Anti-patterns | WP §1.5 Layer 5 (7 patterns) | Not specified | WP plan owns. Persisted to `knowledge-base/lessons/anti-patterns.md` in Phase 0, augmented with extracts from `tasks/lessons.md`, `.serena/memories/CRITICAL_WORKFLOW_DIRECTIVE.md`, GSD `RETROSPECTIVE.md`, and curated claude-mem `bugfix` observations. |

---

## How to use this index in the 6-step workflow

When Step 0 of the per-edit workflow runs:

```bash
# Step 0 — Pre-edit knowledge consult
grep -r "<task-keywords>" knowledge-base/ .serena/memories/ .planning/ .wolf/cerebrum.md tasks/lessons.md docs/SKYYROSE_*.md docs/PLAN_INDEX.md
mem-search "<task-keywords>"
graphify query "<task-keywords>"
```

Read this index first to know which document's section to focus on after the grep returns hits. If grep returns multiple files but you only have time to read one, this index tells you which section is authoritative.

---

## Cross-reference conventions (in KB entries, OpenWolf logs, and code comments)

When citing accumulated knowledge across the four memory systems plus these plans:

| Convention | Means |
|------------|-------|
| `[v2: §N.M]` | SKYYROSE_V2_MASTER_PLAN.md section N.M |
| `[wp: §N.M]` | SKYYROSE_WORDPRESS_PLAN.md section N.M |
| `[cmem #NNN]` | claude-mem observation #NNN (look up via `~/.claude-mem/claude-mem.db` or `.wolf/claude-mem-digest.md`) |
| `[serena: <memory-name>]` | `.serena/memories/<memory-name>.md` |
| `[planning: <phase>/<file>]` | `.planning/phases/<phase>/<file>` (GSD artifact) |
| `[wolf: <file>:<line>]` | `.wolf/<file>:<line>` (OpenWolf entry) |
| `[adr: NNNN]` | `docs/adr/NNNN-*.md` |
| `[kb: <category>/<slug>]` | `knowledge-base/<category>/<slug>.md` |

These conventions appear in KB entries, OpenWolf memory.md rows, code comments where load-bearing, and the §1.2 critique-loop self-critique answers (specifically question 6 — "what's the verified canonical reference").
