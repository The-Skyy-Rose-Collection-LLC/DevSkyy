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

# Filename substrings that indicate a text-bearing logo (monograms, scripts,
# wordmarks, lettered patches). Sending these as image references causes
# Gemini to hallucinate brand text onto the rendered garment — see
# scripts/nano_banana/pipeline.py:_load_bundle_refs lines 696-697 for the
# original empirical finding. Pure-graphic logos (no letters) are safe.
_TEXT_BEARING_LOGO_HINTS = ("monogram", "script", "wordmark", "lettermark", "patch")


def _resolve_logo_extra_refs(sku: str) -> list[tuple[str, Path]]:
    """Resolve dossier `logo_reference` + `extra_logos` to labeled image refs.

    For each logo markdown referenced by the SKU's dossier, follow its
    frontmatter `image_path` to the canonical brand-logo image and return
    a (label, Path) tuple suitable for `generate_gemini(..., extra_refs=...)`.

    Skips any logo whose markdown filename hints it is text-bearing — sending
    text-bearing references causes Gemini to hallucinate brand letters onto
    the garment. Pure-graphic logos (e.g. `black-rose-logo.jpeg`, three-rose
    illustrated cluster, no letters) pass through.

    Returns an empty list on any failure (no dossier, no logo_reference,
    missing files, etc.) — generation continues with the source image only.
    """
    from nano_banana.spec_builder import build_dna_from_sku

    from skyyrose.core.catalog_loader import CATALOG_CSV
    from skyyrose.core.dossier_loader import _parse_frontmatter

    wp_root = CATALOG_CSV.parent.parent  # wordpress-theme/skyyrose-flagship/

    try:
        dna = build_dna_from_sku(sku)
    except Exception as exc:
        log.warning("logo refs: cannot load dna for %s: %s", sku, exc)
        return []

    dossier = getattr(dna, "dossier", None)
    if not dossier:
        return []

    candidates: list[tuple[str, str]] = []
    if dossier.logo_reference:
        candidates.append(("PRIMARY LOGO", dossier.logo_reference))
    for extra in dossier.extra_logos or []:
        candidates.append(("SECONDARY LOGO", extra))

    refs: list[tuple[str, Path]] = []
    for kind, md_rel in candidates:
        md_lower = md_rel.lower()
        if any(hint in md_lower for hint in _TEXT_BEARING_LOGO_HINTS):
            log.info("Skipping text-bearing logo ref %s for %s", md_rel, sku)
            continue

        md_abs = wp_root / md_rel
        if not md_abs.exists():
            log.warning("logo md missing: %s (sku=%s)", md_abs, sku)
            continue

        fm, _ = _parse_frontmatter(md_abs.read_text(encoding="utf-8"))
        image_rel = fm.get("image_path", "")
        if not image_rel:
            log.warning("no image_path frontmatter in %s (sku=%s)", md_abs, sku)
            continue

        image_abs = wp_root / image_rel
        if not image_abs.exists():
            log.warning("logo image missing: %s (sku=%s)", image_abs, sku)
            continue

        label = (
            f"REFERENCE — CANONICAL BRAND LOGO ART ({kind}): "
            "This is the EXACT canonical logo graphic that appears on the garment. "
            "Reproduce its composition, art style, and proportions faithfully — "
            "do not invent missing elements or change the layout. "
            "Apply the technique and colorway specified in the prompt text "
            "(e.g. embossed in black/white/grey). "
            "Do NOT add any text, letters, or wordmarks to the rendered garment."
        )
        refs.append((label, image_abs))

    log.info(
        "Logo extra_refs for %s: %d (%s)",
        sku,
        len(refs),
        ", ".join(p.name for _, p in refs) if refs else "none",
    )
    return refs


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
    extra_refs = _resolve_logo_extra_refs(sku)

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
                extra_refs=extra_refs or None,
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
