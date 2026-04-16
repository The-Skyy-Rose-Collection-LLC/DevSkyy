# Changelog

## [v3.2.0] — 2026-04-16

## What's New

### Features
- **Experience Engine Phase 2 & 3** — Performance Guardian (global), Brand Atmosphere (collection pages), Experience Analyzer, Smart Showcase with Quick View, and Micro-interactions (cart fly-to + wishlist burst) in WordPress theme
- **Elite Studio** — Complete multi-agent image pipeline (Phases 0–6) with dashboard, command center, design co-pilot, and operator console
- **Character Creation System** — CharacterAgent with consistency engine, sprite generation, and Rosie mascot
- **Creative Operations Hub** — Unified LangGraph router across 14 creative intents
- **Fashion Intelligence Core** — Trends, photography, color, editorial, materials, QA, and design tools
- **Enterprise API v2** — Unified creative ops, character management, expanded webhooks
- **SaaS Infrastructure** — Multi-tenancy, Stripe billing, entitlements, and customer portal
- **Virtual Try-On (Layer 6)** — FASHN API integration, tryon_node, optional graph branch (31 tests)
- **REST API & Webhooks (Layer 5)** — Prometheus metrics, Grafana dashboard, A/B tracking
- **Quality System (Layer 4)** — ML classifier, human review gate, visual regression, dual-QC node
- **Production Queue (Layer 3)** — Job types, producer, consumer, cost tracker, rate limiter, DLQ (83 tests)
- **Skyy 3D Character** — Three.js GLB viewer + mascot widget system

### Fixes
- Verification loop lint, tests, and mascot widget bugs
- Import source-of-truth consolidation — deleted stale `agent_sdk/`, fixed all imports
- Ruff: `StrEnum` migration, `zip(strict=)`, unused variable cleanup
- Black formatting across 8 files

### Performance
- `skyyrose_get_current_template_slug()` — static cache eliminates 4 redundant calls per request

### Refactors
- Redis singleton, mget batch, sorted-set index
- Phase 0 prompt system — dedup, partitioned cache, hoisted constants

