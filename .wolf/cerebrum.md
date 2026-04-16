# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-04-07

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **Project:** devskyy
- **Description:** AI-driven multi-agent orchestration platform for enterprise e-commerce automation
- **SDK canonical path:** `sdk/python/agent_sdk/` is the authoritative SDK. Root `agent_sdk/` was a stale copy with wrong brand data and has been deleted.
- **SDK internal imports:** All intra-package imports inside `sdk/python/agent_sdk/` use relative imports (`.module`), NOT absolute `from agent_sdk.module`.
- **base_super_agent:** The `agents/base_super_agent/` package is authoritative. `agents/base_super_agent.py` monolith has been deleted — do not recreate it.
- **Integration tests canonical location:** `tests/integration/` — not `tests/test_*.py` at root for integration-level tests.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-04-15] Never import from root `agent_sdk/` — it no longer exists. Use `from sdk.python.agent_sdk.X import Y`.
- [2026-04-15] Never create `agents/base_super_agent.py` as a flat file — the package at `agents/base_super_agent/` is authoritative and Python will silently ignore the .py if you recreate it anyway.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-04-15] Chose `sdk/python/agent_sdk/` as SDK source of truth over root `agent_sdk/` — root copy had stale brand data ("Where Love Meets Luxury" tagline, missing EliteStudio integration). All internal imports converted to relative to make the package location-independent.
