# Skyy — Design Rulebook (research-backed, 2026-07-03)

Distilled from 55+ source deep-research (full report in session transcript). Binding for all mascot implementation.

## Entrance & frequency
1. NO pop-in on page load. Primary proactive trigger = 10–30s idle, tuned per page dwell.
2. First visit = ONE contextual nudge, never a tour.
3. Hard cap ~2–4 proactive appearances per session.
4. Dismissed = gone for the session (persisted); never resurface the same prompt.

## Accessibility (WCAG 2.2 — legal conformance, non-negotiable)
5. Any auto-motion >5s needs pause/stop/hide control (SC 2.2.2, Level A).
6. Motion is OPT-IN: base experience ships motion-free; animation layers behind `prefers-reduced-motion: no-preference` (SC 2.3.3).
7. Routine speech → `role="status"`; `role="alert"` reserved for genuine urgency (SC 4.1.3). Accumulated dialogue → `role="log"`.
8. Any panel = native `<dialog>` + showModal(): focus in, trapped, ESC closes, focus restored (SC 2.1.2).

## Voice & brain
9. Deterministic page-aware intents = default brain; LLM tier = escalation only, cached + rate-capped + budget-model (documented 15–16x cost delta vs flagship).
10. Styling advice grounded in structured product/fit data (Levi's STITCH, Stitch Fix pattern) — never open-ended generative "opinions."
11. NEVER guilt, pressure, urgency, or owed-engagement (the Duo failure mode — harder line for luxury).
12. Transparent that Skyy is a designed character (Gen Z trust research: honesty about being virtual wins).

## Luxury fit
13. Precedent that emotional mascot + luxury coexist: Ralph Lauren Polo Bear (2025 animated short, positioning intact).
14. Register = presence and taste, never sales pressure. Voice draws from SkyyRose canon only (from-interview.md) — generic streetwear/luxury tropes read as inauthentic (BoF 2026 warning).
15. Klarna lesson: don't justify her by cost-cutting/automation; she exists for brand distinctiveness and guidance quality.

## Honesty notes
- No mascot-specific conversion A/B data exists industry-wide; vendor chatbot stats are self-interested — never cite as expected lift.
- No known luxury mascot-removal case; risk section built from adjacent evidence.
