# Shared Memory — Luxury Mockup Pipeline

Cross-agent memory pool. Anything that benefits all 5 agents lives here. Per-agent memory dirs (`../<agent-slug>/`) hold discipline-specific notes.

## Protocol

**Format:** one fact per `.md` file, slugged filename, YAML frontmatter (name, description, tags, applies_to, last_verified). Body is the fact + WHY + HOW TO APPLY.

**Index discipline:** this file is a one-line index. Each entry: `- [Title](slug.md) — one-line hook`. Under 150 chars per line. Truncated past line 200.

**Read before dispatch:** every agent reads its own `INDEX.md` + this `_shared/INDEX.md` before starting work. If a fact is in memory, do NOT re-discover it.

**Write after correction:** any time the orchestrator corrects an agent, or the founder corrects pipeline output, append a memory entry naming the correction + WHY + HOW TO APPLY.

**Decay:** memories about repo state carry `last_verified` dates. Re-verify if > 30 days old.

## Cross-reference

- Project memory: `/Users/theceo/.claude/projects/-Users-theceo-DevSkyy/memory/MEMORY.md`
- Claude-mem DB: `~/.claude-mem/claude-mem.db`
- Canon docs: `/Users/theceo/DevSkyy/docs/brand/`

## Entries

- [The Five canonical brands](the-five.md) — Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels. Never cite locked-out European luxury lineage.
- [primary_focus_surfaces discipline](scope-policy.md) — Full-site scope + focus marker. Agents see whole site, deliver against target.
- [SaaS Gate non-negotiable](saas-gate.md) — Every deliverable mobile-verified + image-optimized + sales-presentation-grade before surfacing.
- [Founder STOP-AND-SHOW protocol](stop-and-show.md) — Paid API calls / compute / production writes need explicit founder y/yes before execution.
- [Multi-agent audit false-positive rate ~25%](audit-verification.md) — Always curl + grep live state before drafting any audit fix.
- [WebFetch strips script tags](no-webfetch-for-scripts.md) — Use curl + grep for JSON-LD / OG / inline JS audits.
