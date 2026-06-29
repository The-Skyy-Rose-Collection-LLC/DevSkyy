# skyyrose/cli_harnesses/

Experimental tool-integration shims — NOT the production imagery path (that is `skyyrose/elite_studio/`).

- Each subdir is an independent `cli_anything` agent harness wrapping one external tool/target: `comfyui/` (ComfyUI), `trellis/` (TRELLIS), `hf-spaces/` (HuggingFace Spaces), `marvelous/` (Marvelous Designer), `skyyrose-theme/`, `vercel-config/`.
- **ComfyUI: do not modify `comfyui/core/` or `comfyui/utils/`** — that's upstream `cli_anything`. Extend via `commands/`.
- TRELLIS/Tripo here are thin wrappers, separate from `elite_studio/pipeline3d/`. Use the harnesses for experimentation; use `elite_studio/` for production renders (it has the budget/telemetry/money-gate).
- Paid external calls still obey the root STOP-AND-SHOW rule.
