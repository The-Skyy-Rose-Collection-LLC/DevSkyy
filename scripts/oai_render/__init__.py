"""SkyyRose product render pipeline — OpenAI gpt-image-2 (high fidelity).

Replaces the Gemini/nano-banana build. Renders every product with one
deterministic, identical procedure via the OpenAI image *edit* endpoint,
feeding real garment photos + logo + sport-patch references so the output
is a 100%-replicated mockup (no element invented or dropped).

Modules:
  config      — model params, paths, cost guardrails, API-key loader
  references  — SKU → garment / logo / patch reference images (ported map)
  prompt      — fixed render procedure + per-SKU dossier injection
  client      — gpt-image-2 images.edit call with retry/backoff
  cost        — per-image estimate + STOP-AND-SHOW manifest + hard cap
  pipeline    — per-SKU + batch orchestration (dry-run by default)
  cli         — executable entrypoint (dry-run / generate)

Spec: tasks/oai-render-pipeline-spec.html
"""

from __future__ import annotations

__version__ = "1.0.0"
