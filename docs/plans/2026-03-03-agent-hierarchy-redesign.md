# DevSkyy Agent Hierarchy Redesign — Phase 2 Design Document

> **For Claude / Ralph:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate 59 agent files into 8 core agents + 1 orchestrator with sub-agent delegation, universal self-healing, and prove-on-DevSkyy-first architecture. This becomes the foundation for a SaaS platform.

**Architecture:** Hierarchical agent system where core agents own domains and delegate to specialized sub-agents. Every component is self-healing. SkyyRose (skyyrose.co) is tenant #1 — the living proof the system works.

**Tech Stack:** Python 3.11+, FastAPI, WebSocket, React Three Fiber (3D portal), Next.js 16, PostgreSQL (Neon)

---

## Vision

1. **DevSkyy genuinely runs skyyrose.co** — agents monitor, heal, and improve the live storefront 24/7
2. **DevSkyy is also a SaaS** — other brands sign up, get agent-operated storefronts
3. **Full auto autonomy** — agents fix, improve, and deploy continuously with budget/critical gates only
4. **Full context awareness** — health + analytics + customer behavior + competitors + seasonal trends
5. **Platform agnostic** — WordPress first (proven via Ralph), Shopify next, then any platform via adapters

---

## Agent Hierarchy

### Before (Current State)
```
59 files → 12 production, 5 implemented (no endpoint), 8 specs, 19 framework, 2 deprecated
Flat structure — every agent reports to nothing
No universal self-healing — only Elite Web Builder has it
```

### After (Target State)
```
ORCHESTRATOR
├── Commerce Agent (4 sub-agents)
├── Content Agent (3 sub-agents)
├── Creative Agent (4 sub-agents)
├── Marketing Agent (3 sub-agents)
├── Operations Agent (4 sub-agents)
├── Analytics Agent (3 sub-agents)
├── Imagery & 3D Agent (5 sub-agents)
└── Web Builder Agent (5 sub-agents)

Total: 9 nodes in 3D portal, 31 sub-agents, universal self-healing
```

---

## Core Agent Definitions

### 1. Commerce Agent
**Existing base:** `agents/commerce_agent.py` (990 lines)
**Endpoint:** `/api/v1/commerce`
**Domain:** All revenue-generating operations

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Product Manager | New (absorb from blueprint) | BUILD | Product data validation, image 404 detection |
| Pricing Engine | Already in Commerce | DONE | Price consistency checks, competitor drift alerts |
| Inventory Tracker | New | BUILD | Stock sync verification, oversell prevention |
| Order Processor | New | BUILD | Failed order retry, payment gateway fallback |
| WordPress Bridge | `wordpress_bridge/agent.py` | ABSORB | WooCommerce sync repair |

### 2. Content Agent
**Existing base:** `agents/skyyrose_content_agent.py` (977 lines)
**Endpoint:** `/api/v1/content`
**Domain:** All written content — pages, products, blogs, SEO

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Collection Content | `collection_content_agent.py` (375 lines) | ABSORB | Missing section detection, stale content refresh |
| SEO Content | Elite Web Builder spec | ABSORB | Ranking drops → auto-optimize, meta tag validation |
| Copywriter | New | BUILD | Brand voice drift detection, tone consistency |

### 3. Creative Agent
**Existing base:** `agents/creative_agent.py` (1,192 lines)
**Endpoint:** `/api/v1/creative`
**Domain:** Visual identity, design system, brand enforcement

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Design System | Elite Web Builder spec | ABSORB | CSS variable consistency, contrast ratio checks |
| Brand Guardian | New | BUILD | Off-brand content detection, color/font violations |
| Asset Generator | New | BUILD | Failed generation retry, quality gate |
| Quality Checker | Elite Web Builder QA spec | ABSORB | Cross-browser regression, visual diff |

### 4. Marketing Agent
**Existing base:** `agents/marketing_agent.py` (936 lines)
**Endpoint:** `/api/v1/marketing`
**Domain:** Campaigns, social, audience growth

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Social Media | `social_media_agent.py` (1,014 lines) | ABSORB | Post failure retry, engagement drop alerts |
| Campaign Manager | Already in Marketing | DONE | Underperforming campaign auto-pause |
| A/B Testing | Already in Marketing | DONE | Statistical significance validation |

### 5. Operations Agent
**Existing base:** `agents/operations_agent.py` (910 lines)
**Endpoint:** `/api/v1/operations`
**Domain:** Deploy, security, health, code quality

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Deployment Manager | Already in Ops | DONE | Failed deploy rollback, health check post-deploy |
| Security Monitor | `security_ops_agent.py` (322 lines) | ABSORB | Vulnerability auto-patch, dependency update |
| Health Checker | New | BUILD | Uptime monitoring, auto-restart services |
| Coding Doctor | `coding_doctor_agent.py` (1,462 lines) | ABSORB | Lint errors auto-fix, type errors auto-resolve |

### 6. Analytics Agent
**Existing base:** `agents/analytics_agent.py` (927 lines)
**Endpoint:** `/api/v1/analytics`
**Domain:** Data, trends, conversion intelligence

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Data Analyst | Already in Analytics | DONE | Anomaly detection, data quality checks |
| Trend Predictor | Already in Analytics | DONE | Model drift detection, retraining triggers |
| Conversion Tracker | New | BUILD | Tracking pixel validation, funnel break alerts |

### 7. Imagery & 3D Agent
**Existing base:** Merge `skyyrose_imagery_agent.py` (635 lines) + `skyyrose_product_agent.py` (193 lines)
**Endpoint:** `/api/v1/imagery`
**Domain:** All visual asset generation — photos, VTON, 3D models

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Gemini Image Gen | `skyyrose_imagery_agent.py` | CORE | Quality gate, retry with different params |
| Fashn VTON | `fashn_agent.py` (691 lines) | ABSORB | Provider failover (WeShopAI → IDM-VTON → FASHN) |
| Tripo 3D | `tripo_agent.py` (1,084 lines) | ABSORB | Mesh quality validation, auto-retry |
| Meshy 3D | `meshy_agent.py` (1,221 lines) | ABSORB | Format validation, fallback to Tripo |
| HF Spaces | `skyyrose_spaces_orchestrator.py` (696 lines) | ABSORB | Space health checks, quota management |

### 8. Web Builder Agent
**Existing base:** `agents/elite_web_builder/` (Director + 8 specs)
**Endpoint:** `/api/v1/web-builder`
**Domain:** Full theme generation, deployment, platform adapters

| Sub-Agent | Source | Status | Self-Healing |
|-----------|--------|--------|-------------|
| Frontend Dev | Elite Web Builder spec (63 lines) | BUILD execute() | Render error detection, component fallback |
| Backend Dev | Elite Web Builder spec (69 lines) | BUILD execute() | PHP lint, function conflict detection |
| Accessibility | Elite Web Builder spec (56 lines) | BUILD execute() | WCAG regression detection, auto-fix ARIA |
| Performance | Elite Web Builder spec (56 lines) | BUILD execute() | Lighthouse score drops → auto-optimize |
| Platform Adapter (WP) | Ralph's proven workflow | BUILD | Deploy failure → rollback → retry |

### + Orchestrator
**Domain:** System-wide routing, escalation, Round Table consensus
**Self-Healing:** Escalation handler, system-wide recovery, budget enforcement

| Component | Source | Status |
|-----------|--------|--------|
| Task Router | `orchestration/domain_router.py` | EXISTS |
| Brand Context | `orchestration/brand_context.py` | EXISTS |
| Round Table | `llm/round_table.py` | EXISTS |
| Self-Healer (system) | `elite_web_builder/core/self_healer.py` | PROMOTE to universal |
| Event Bus Bridge | NEW — WebSocket gateway | BUILD |

---

## Universal Self-Healing Architecture

### SelfHealingMixin (every agent inherits this)

```python
class SelfHealingMixin:
    """Universal self-healing capability for all agents."""

    # Failure categories
    FAILURE_TYPES = [
        "CODE_BUG",        # Logic error in agent output
        "CONFIG",           # Missing env var, wrong setting
        "WRONG_APPROACH",   # Strategy didn't work, try different
        "EXTERNAL",         # API down, rate limited, timeout
        "DATA_QUALITY",     # Bad input data, corrupted state
        "PROVIDER_DOWN",    # LLM/service provider unavailable
    ]

    def diagnose(self, failure) -> Diagnosis
    def heal(self, diagnosis) -> HealResult
    def health_check(self) -> HealthStatus
    def circuit_breaker(self) -> bool
```

### Escalation Chain
```
Sub-agent fails → self-heal (3 attempts, different params)
    ↓ can't fix
Core agent tries (different sub-agent, different approach)
    ↓ can't fix
Orchestrator tries (Round Table consensus, provider swap)
    ↓ can't fix
Dashboard alert (human decides via 3D portal)
```

### Circuit Breaker Pattern (per agent)
- **Closed**: Normal operation
- **Open**: After 5 consecutive failures → stop attempting, alert
- **Half-Open**: After cooldown, try one request → if succeeds, close; if fails, re-open

### Learning Journal (per agent)
- Records every heal attempt: what failed, what fixed it, how long
- Informs future healing: "last time this failed, approach X worked"
- Feeds into Orchestrator's decision-making

---

## Files to Delete (Deprecated/Absorbed)

```
DELETE: agents/base_legacy.py              (719 lines — deprecated, DO NOT USE per CLAUDE.md)
DELETE: agents/operations_legacy.py        (602 lines — deprecated, DO NOT USE per CLAUDE.md)
```

## Files to Restructure

```
MOVE: agents/social_media_agent.py     → agents/core/marketing/sub_agents/social_media.py
MOVE: agents/security_ops_agent.py     → agents/core/operations/sub_agents/security_monitor.py
MOVE: agents/coding_doctor_agent.py    → agents/core/operations/sub_agents/coding_doctor.py
MOVE: agents/collection_content_agent.py → agents/core/content/sub_agents/collection_content.py
MOVE: agents/fashn_agent.py            → agents/core/imagery/sub_agents/fashn_vton.py
MOVE: agents/tripo_agent.py            → agents/core/imagery/sub_agents/tripo_3d.py
MOVE: agents/meshy_agent.py            → agents/core/imagery/sub_agents/meshy_3d.py
MOVE: agents/skyyrose_spaces_orchestrator.py → agents/core/imagery/sub_agents/hf_spaces.py
MOVE: agents/wordpress_bridge/         → agents/core/commerce/sub_agents/wordpress_bridge/
MOVE: agents/wordpress_asset_agent.py  → agents/core/commerce/sub_agents/wordpress_assets.py
```

## New Files to Create

```
NEW: agents/core/__init__.py
NEW: agents/core/base.py               — CoreAgent base class + SelfHealingMixin
NEW: agents/core/sub_agent.py          — SubAgent base class (inherits SelfHealingMixin)
NEW: agents/core/orchestrator.py       — Top-level Orchestrator
NEW: agents/core/commerce/__init__.py
NEW: agents/core/commerce/agent.py     — Commerce CoreAgent (wraps existing commerce_agent.py)
NEW: agents/core/commerce/sub_agents/__init__.py
NEW: agents/core/content/__init__.py
NEW: agents/core/content/agent.py
NEW: agents/core/content/sub_agents/__init__.py
NEW: agents/core/creative/__init__.py
NEW: agents/core/creative/agent.py
NEW: agents/core/creative/sub_agents/__init__.py
NEW: agents/core/marketing/__init__.py
NEW: agents/core/marketing/agent.py
NEW: agents/core/marketing/sub_agents/__init__.py
NEW: agents/core/operations/__init__.py
NEW: agents/core/operations/agent.py
NEW: agents/core/operations/sub_agents/__init__.py
NEW: agents/core/analytics/__init__.py
NEW: agents/core/analytics/agent.py
NEW: agents/core/analytics/sub_agents/__init__.py
NEW: agents/core/imagery/__init__.py
NEW: agents/core/imagery/agent.py
NEW: agents/core/imagery/sub_agents/__init__.py
NEW: agents/core/web_builder/__init__.py
NEW: agents/core/web_builder/agent.py
NEW: agents/core/web_builder/sub_agents/__init__.py
```

## New Directory Structure

```
agents/
├── core/                          # NEW — hierarchical agent system
│   ├── __init__.py
│   ├── base.py                    # CoreAgent + SelfHealingMixin
│   ├── sub_agent.py               # SubAgent base
│   ├── orchestrator.py            # Top-level Orchestrator
│   ├── commerce/
│   │   ├── agent.py               # Commerce CoreAgent
│   │   └── sub_agents/
│   │       ├── product_manager.py
│   │       ├── pricing_engine.py
│   │       ├── inventory_tracker.py
│   │       ├── order_processor.py
│   │       ├── wordpress_bridge/
│   │       └── wordpress_assets.py
│   ├── content/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── collection_content.py
│   │       ├── seo_content.py
│   │       └── copywriter.py
│   ├── creative/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── design_system.py
│   │       ├── brand_guardian.py
│   │       ├── asset_generator.py
│   │       └── quality_checker.py
│   ├── marketing/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── social_media.py
│   │       ├── campaign_manager.py
│   │       └── ab_testing.py
│   ├── operations/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── deployment_manager.py
│   │       ├── security_monitor.py
│   │       ├── health_checker.py
│   │       └── coding_doctor.py
│   ├── analytics/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── data_analyst.py
│   │       ├── trend_predictor.py
│   │       └── conversion_tracker.py
│   ├── imagery/
│   │   ├── agent.py
│   │   └── sub_agents/
│   │       ├── gemini_image.py
│   │       ├── fashn_vton.py
│   │       ├── tripo_3d.py
│   │       ├── meshy_3d.py
│   │       └── hf_spaces.py
│   └── web_builder/
│       ├── agent.py
│       └── sub_agents/
│           ├── frontend_dev.py
│           ├── backend_dev.py
│           ├── accessibility.py
│           ├── performance.py
│           └── platform_adapter.py
│
├── elite_web_builder/             # KEEP — core infrastructure (self_healer, verification, etc.)
│   ├── core/
│   │   ├── self_healer.py         # PROMOTE to universal via SelfHealingMixin
│   │   ├── verification_loop.py
│   │   ├── learning_journal.py
│   │   ├── cost_tracker.py
│   │   └── output_writer.py
│   └── knowledge/                 # KEEP — WordPress knowledge base
│
├── base_super_agent.py            # KEEP — 17 techniques, used by CoreAgent base
├── enhanced_base.py               # KEEP — enhanced techniques
├── models.py                      # KEEP — data models
├── errors.py                      # KEEP — exceptions
├── multimodal_capabilities.py     # KEEP — vision/audio/video
│
├── # DELETED:
│   # base_legacy.py              — DEPRECATED
│   # operations_legacy.py        — DEPRECATED
│
├── # ORIGINAL FILES (keep for backward compat, import from core/):
│   # commerce_agent.py           — imports from core/commerce/agent.py
│   # skyyrose_content_agent.py   — imports from core/content/agent.py
│   # creative_agent.py           — imports from core/creative/agent.py
│   # marketing_agent.py          — imports from core/marketing/agent.py
│   # operations_agent.py         — imports from core/operations/agent.py
│   # analytics_agent.py          — imports from core/analytics/agent.py
│   # skyyrose_imagery_agent.py   — imports from core/imagery/agent.py
│   # support_agent.py            — absorbed into operations
│
└── # SDK & ORCHESTRATION (unchanged):
    # sdk/python/adk/             — framework adapters
    # orchestration/               — routing, RAG, brand context
    # llm/                         — Round Table
```

---

## 3D Agent Portal (Dashboard)

The 3D portal replaces `/admin/agents` and shows the 9-node hierarchy:

- **9 primary nodes** (Orchestrator + 8 core agents) as glowing spheres
- **Click any core agent** → expand to see its sub-agents
- **Real-time data** via WebSocket: agent status, task count, health, healing events
- **Event stream** at bottom: every agent action logged
- **Live metrics** on right: revenue, conversion, health score
- **Self-healing visualization**: when an agent heals, show the repair animation on its node

Built with React Three Fiber (already in `package.json`), converting the blueprint HTML to React components.

---

## SaaS Tiers (Future)

| Tier | Core Agents | Sub-Agents | Platforms | Price Point |
|------|-------------|-----------|-----------|-------------|
| Starter | 3 (Content, Commerce, Ops) | 8 | WordPress | $X/mo |
| Growth | 5 (+ Marketing, Analytics) | 16 | WordPress + Shopify | $XX/mo |
| Enterprise | All 8 + Orchestrator | All 31 | Any platform | $XXX/mo |
| SkyyRose | Full fleet + custom | All + brand-specific | All | Internal |

---

## Execution Strategy

**Track 1 — Dev Team (Dashboard + API wiring):**
- Build 3D portal (React Three Fiber)
- Create WebSocket gateway for real-time agent status
- Wire HTTP endpoints for all core agents
- Build tenant management layer

**Track 2 — You + Ralph (Agent backend):**
- Restructure files into `agents/core/` hierarchy
- Implement SelfHealingMixin as universal base
- Build missing sub-agents
- Prove autonomous loop on skyyrose.co
- Delete deprecated code

---

## Success Criteria

1. All 8 core agents have HTTP endpoints and respond to health checks
2. Self-healing works end-to-end: inject failure → agent detects → heals → reports
3. skyyrose.co is monitored 24/7 by the agent fleet
4. 3D portal shows real-time agent status (not mock data)
5. At least one healing event per day is automatically resolved
6. Package is ready for SaaS tenant #2

---

**Created:** 2026-03-03
**Status:** Approved for implementation
**Tracks:** Parallel (Dashboard + Agent Backend)
