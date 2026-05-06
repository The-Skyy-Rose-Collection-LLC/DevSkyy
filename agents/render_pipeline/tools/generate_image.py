"""Tool 5: Generate image via routed engine. PAID API CALL.

Dispatches to the verified `nano_banana.generate.*` functions:
    gemini-pro / gemini-flash → `generate_gemini` (Google genai SDK)
    gpt-image                 → `generate_gpt`    (OpenAI Responses+Edit API)
    flux-pro                  → `generate_flux_fal` (fal.ai FLUX Pro)

Cost (verified 2026-05-05):
    gemini-pro: ~$0.04/image
    gpt-image:  ~$0.08/image
    flux-pro:   ~$0.075/image

State writes:
    candidate_path (str), bytes_size, generation_engine
"""

from __future__ import annotations

import logging
from pathlib import Path
from agents.render_pipeline.tools._paths import REPO_ROOT, ensure_repo_paths

ensure_repo_paths()

log = logging.getLogger(__name__)

from google.adk.tools.tool_context import ToolContext

# Output dir mirrors the production pipeline output convention but lives
# under agents/render_pipeline/ so it doesn't collide with nano_banana's
# wordpress-theme/skyyrose-flagship/assets/images/products writes.
_OUTPUT_DIR = REPO_ROOT / "agents" / "render_pipeline" / "output"


def generate_image_fn(sku: str, view: str, tool_context: ToolContext) -> dict:
    """Dispatch to the routed engine and save bytes to disk.

    Reads state: engine, model_id, prompt, source_path
    Writes state: candidate_path, bytes_size

    Returns dict with output_path, engine, bytes_size on success;
    error+output_path=None on failure.
    """
    from nano_banana.client import get_genai_client, get_openai_client
    from nano_banana.engine_fal import generate_flux_fal
    from nano_banana.generate import (
        GEMINI_FAST,
        GEMINI_PRO,
        generate_gemini,
        generate_gpt,
    )
    from nano_banana.utils import save_image

    engine = tool_context.state.get("engine", "")
    prompt = tool_context.state.get("prompt", "")
    source_path_str = tool_context.state.get("source_path", "")

    if not engine or not prompt or not source_path_str:
        return {
            "error": (
                f"missing required state — "
                f"engine={engine!r} prompt_chars={len(prompt)} "
                f"source_path={source_path_str!r}. "
                f"Check that route_engine, build_prompt, resolve_source ran first."
            ),
            "output_path": None,
        }

    source_path = Path(source_path_str)

    img_bytes: bytes | None = None
    try:
        if engine in ("gemini-pro", "gemini-flash"):
            actual_model = GEMINI_PRO if engine == "gemini-pro" else GEMINI_FAST
            client = get_genai_client()
            img_bytes = generate_gemini(
                client,
                source_path,
                prompt,
                model=actual_model,
                aspect_ratio="3:4",
            )
        elif engine == "gpt-image":
            client = get_openai_client()
            img_bytes = generate_gpt(client, prompt, source_path)
        elif engine == "flux-pro":
            img_bytes = generate_flux_fal(source_path, prompt)
        else:
            return {
                "error": f"unsupported engine {engine!r} — supported: gemini-pro/gemini-flash/gpt-image/flux-pro",
                "output_path": None,
            }
    except Exception as exc:
        log.exception("generate_image_fn: %s call failed", engine)
        return {
            "error": f"{engine} generation raised {type(exc).__name__}: {exc}",
            "output_path": None,
        }

    if not img_bytes:
        return {"error": f"{engine} returned no bytes", "output_path": None}

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / f"{sku}-{view}-render.webp"
    save_image(img_bytes, out_path)

    tool_context.state["candidate_path"] = str(out_path)
    tool_context.state["bytes_size"] = len(img_bytes)
    tool_context.state["generation_engine"] = engine

    return {
        "sku": sku,
        "view": view,
        "engine": engine,
        "output_path": str(out_path),
        "bytes_size": len(img_bytes),
    }
