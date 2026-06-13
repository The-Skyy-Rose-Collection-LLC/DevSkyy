# SkyyRose Suite — Cross-Plugin Doctrine

Five plugins, one marketplace. The orchestrator (`skyyrose`) is the front door; the four themed plugins do the work and hand off to each other along a fixed graph.

## Plugins & namespaces

| Plugin | Namespace | Owns |
|--------|-----------|------|
| `skyyrose` | `skyyrose:*` | Task classification + routing; `/skyyrose <task>`; the dev-team workflow. |
| `skyyrose-market` | `skyyrose-market:*` | Brand voice, product copy, SEO, email flows, paid media, influencer, social, launch. |
| `skyyrose-design` | `skyyrose-design:*` | Imagery (gpt-image-2), frontend, Three.js/immersive, WP/WooCommerce theming, a11y, layout. |
| `skyyrose-core` | `skyyrose-core:*` | Backend (FastAPI/Python), data, infra, behavior discipline, planning, memory & self-healing. |
| `skyyrose-qa` | `skyyrose-qa:*` | TDD, drive-to-green, verification, audits, evals, code review. |

## Handoff graph

```
            /skyyrose <task>
                  │
          skyyrose-orchestrator  (classify → route)
                  │
   ┌──────────────┼───────────────┬───────────────┐
   ▼              ▼               ▼               ▼
market ───────► design ───────► qa ◄──────────── core
 (copy,          (build:         (verify:         (engineer:
  campaign,       imagery, FE,    TDD, audit,      API, data,
  social)         WP, 3D)         review)          memory, plan)
                  │               ▲                  │
                  └── render/build ┘                 │
   self-heal: any plugin ───────► skyyrose-qa:drive-to-green ──► skyyrose-core (memory log)
```

- **market → design:** a campaign/launch needs imagery, a landing page, or PDP work → hand to `skyyrose-design`.
- **design → qa:** any built artifact (theme code, component, render prompt) → `skyyrose-qa` verifies before it ships.
- **core → qa:** backend changes → `skyyrose-qa` for TDD + review.
- **qa → core:** failures/lessons logged to memory via `skyyrose-core` (claude-mem / `.wolf/cerebrum.md` / `.wolf/buglog.json`).
- **self-heal:** any plugin detecting a regression calls `skyyrose-qa:drive-to-green`; the resolution is recorded by `skyyrose-core` memory skills.

## When to call which

| Intent | Route to |
|--------|----------|
| "write copy / email / social / launch plan / SEO" | `skyyrose-market` |
| "generate a product image / build a page / theme / 3D" | `skyyrose-design` |
| "build an API / fix backend / migration / plan a feature" | `skyyrose-core` |
| "test it / review it / audit / make it pass / verify" | `skyyrose-qa` |
| multi-step (e.g. "launch the drop") | `skyyrose` orchestrator → dev-team workflow spanning all four |

## Operating discipline

Every agent in every plugin carries the always-on block referencing `skyyrose-core:token-aware-behavior` + `skyyrose-core:efficient-production`. Paid renders (gpt-image-2) and any production write go through STOP-AND-SHOW (owned by `skyyrose-design`'s imagery skills). The canonical imagery engine is OpenAI Image 2 (`gpt-image-2`); product facts resolve through the catalog CSV + per-SKU dossiers only.
