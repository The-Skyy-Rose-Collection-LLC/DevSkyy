"""Tool 5: Generate image via routed engine. PAID API CALL.

Dispatches to verified `nano_banana.generate.*` functions:
    gemini-pro / gemini-flash → generate_gemini    (Google genai SDK)
    gpt-image                 → generate_gpt        (OpenAI Responses+Edit)
    flux-pro                  → generate_flux_fal   (fal.ai FLUX Pro)

Cost (verified 2026-05-05):
    gemini-pro: ~$0.04/image
    gpt-image:  ~$0.08/image
    flux-pro:   ~$0.075/image

State writes: candidate_path (str), bytes_size (int), generation_engine (str)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from agents.render_pipeline.tools._paths import REPO_ROOT, ensure_repo_paths

ensure_repo_paths()

from google.adk.tools.tool_context import ToolContext

log = logging.getLogger(__name__)

# Output dir. Defaults to the canonical Pipeline 1 path documented in
# docs/PIPELINE-ARCHITECTURE.md (`renders/gated/<sku>/`) so downstream
# scorers and WC upload steps can read ADK renders without a copy step.
# Override via RENDER_PIPELINE_OUTPUT_DIR — useful for dev sandboxes and
# CI scratch dirs that need isolation from production output.
_OUTPUT_DIR = Path(os.environ.get("RENDER_PIPELINE_OUTPUT_DIR") or REPO_ROOT / "renders" / "gated")

# Engine routing — single source of truth.
_GEMINI_ENGINES = frozenset({"gemini-pro", "gemini-flash"})
_OPENAI_ENGINES = frozenset({"gpt-image"})
_FAL_ENGINES = frozenset({"flux-pro"})
_SUPPORTED_ENGINES = _GEMINI_ENGINES | _OPENAI_ENGINES | _FAL_ENGINES

# Default Gemini output aspect for product renders.
_GEMINI_ASPECT_RATIO = "3:4"

# Filename substrings that indicate a text-bearing logo (monograms, scripts,
# wordmarks, lettered patches). Sending these as image references causes
# Gemini to hallucinate brand text onto the rendered garment — see
# scripts/nano_banana/pipeline.py:_load_bundle_refs lines 696-697 for the
# original empirical finding. Pure-graphic logos (no letters) are safe.
_TEXT_BEARING_LOGO_HINTS = ("monogram", "script", "wordmark", "lettermark", "patch")

# Logo kind labels used in the reference-image prompt template.
_LOGO_KIND_PRIMARY = "PRIMARY LOGO"
_LOGO_KIND_SECONDARY = "SECONDARY LOGO"

# Reference-image label template — keeps Gemini honest about reproducing the
# canonical art without adding extra text/letters or treating it as a patch.
_LOGO_LABEL_TEMPLATE = (
    "REFERENCE — CANONICAL BRAND LOGO ART ({kind}): "
    "This is the EXACT canonical logo graphic that appears on the garment. "
    "Reproduce its composition, art style, and proportions faithfully — "
    "do not invent missing elements or change the layout. "
    "Apply the technique and colorway specified in the prompt text "
    "(e.g. embossed in black/white/grey). "
    "Do NOT add any text, letters, or wordmarks to the rendered garment."
)


def _is_text_bearing(md_rel: str) -> bool:
    """True when the logo md filename suggests it carries letters/text."""
    md_lower = md_rel.lower()
    return any(hint in md_lower for hint in _TEXT_BEARING_LOGO_HINTS)


def _resolve_logo_image_path(md_rel: str, wp_root: Path, sku: str) -> Path | None:
    """Follow a dossier logo md path → its frontmatter image_path → absolute Path.

    Returns None on any structural failure (md missing, frontmatter missing,
    image file missing, file unreadable). All failures log a warning so the
    caller can debug a misconfigured dossier without losing the render call.
    """
    from skyyrose.core.dossier_loader import _parse_frontmatter

    md_abs = wp_root / md_rel
    if not md_abs.exists():
        log.warning("logo md missing: %s (sku=%s)", md_abs, sku)
        return None

    try:
        md_text = md_abs.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("cannot read logo md %s: %s (sku=%s)", md_abs, exc, sku)
        return None

    fm, _ = _parse_frontmatter(md_text)
    image_rel = fm.get("image_path", "")
    if not image_rel:
        log.warning("no image_path frontmatter in %s (sku=%s)", md_abs, sku)
        return None

    image_abs = wp_root / image_rel
    if not image_abs.exists():
        log.warning("logo image missing: %s (sku=%s)", image_abs, sku)
        return None

    return image_abs


def _resolve_logo_extra_refs(sku: str) -> list[tuple[str, Path]]:
    """Resolve dossier `logo_reference` + `extra_logos` to labeled image refs.

    For each logo markdown referenced by the SKU's dossier, follow its
    frontmatter `image_path` to the canonical brand-logo image and return
    a (label, Path) tuple suitable for `generate_gemini(..., extra_refs=...)`.

    Skips logos whose md filename hints they are text-bearing — sending
    text-bearing references causes Gemini to hallucinate brand letters
    onto the garment. Pure-graphic logos pass through.

    Returns an empty list on any expected failure (no dossier, no
    logo_reference, missing files) — generation continues with the source
    image only. Unexpected exceptions bubble up (caller decides to abort).
    """
    from nano_banana.spec_builder import build_dna_from_sku

    from skyyrose.core.catalog_loader import CATALOG_CSV
    from skyyrose.core.dossier_loader import DossierMissingError

    wp_root = CATALOG_CSV.parent.parent  # wordpress-theme/skyyrose-flagship/

    try:
        dna = build_dna_from_sku(sku)
    except (KeyError, DossierMissingError) as exc:
        log.warning("logo refs: cannot load dna for %s: %s", sku, exc)
        return []

    dossier = getattr(dna, "dossier", None)
    if not dossier:
        return []

    candidates: list[tuple[str, str]] = []
    if dossier.logo_reference:
        candidates.append((_LOGO_KIND_PRIMARY, dossier.logo_reference))
    for extra_md in dossier.extra_logos or []:
        candidates.append((_LOGO_KIND_SECONDARY, extra_md))

    refs: list[tuple[str, Path]] = []
    for kind, md_rel in candidates:
        if _is_text_bearing(md_rel):
            log.info("Skipping text-bearing logo ref %s for %s", md_rel, sku)
            continue

        image_abs = _resolve_logo_image_path(md_rel, wp_root, sku)
        if image_abs is None:
            continue

        refs.append((_LOGO_LABEL_TEMPLATE.format(kind=kind), image_abs))

    log.info(
        "Logo extra_refs for %s: %d (%s)",
        sku,
        len(refs),
        ", ".join(p.name for _, p in refs) if refs else "none",
    )
    return refs


def _missing_state_error(engine: str, prompt: str, source_path: str) -> dict:
    return {
        "error": (
            f"missing required state — engine={engine!r} "
            f"prompt_chars={len(prompt)} source_path={source_path!r}. "
            "Check that route_engine, build_prompt, resolve_source ran first."
        ),
        "output_path": None,
    }


def _dispatch_engine(
    engine: str,
    prompt: str,
    source_path: Path,
    extra_refs: list[tuple[str, Path]] | None,
) -> bytes | None:
    """Call the engine-specific generator. Returns image bytes or None on empty.

    Raises ValueError for engines outside `_SUPPORTED_ENGINES` (caller should
    have already screened, this is defense-in-depth). All other exceptions
    propagate from the underlying SDK so the outer handler can log them.
    """
    from nano_banana.client import get_genai_client, get_openai_client
    from nano_banana.engine_fal import generate_flux_fal
    from nano_banana.generate import (
        GEMINI_FAST,
        GEMINI_PRO,
        generate_gemini,
        generate_gpt,
    )

    if engine in _GEMINI_ENGINES:
        model = GEMINI_PRO if engine == "gemini-pro" else GEMINI_FAST
        return generate_gemini(
            get_genai_client(),
            source_path,
            prompt,
            model=model,
            aspect_ratio=_GEMINI_ASPECT_RATIO,
            extra_refs=extra_refs or None,
        )
    if engine in _OPENAI_ENGINES:
        return generate_gpt(get_openai_client(), prompt, source_path)
    if engine in _FAL_ENGINES:
        return generate_flux_fal(source_path, prompt)

    raise ValueError(f"unsupported engine {engine!r}")


def generate_image_fn(sku: str, view: str, tool_context: ToolContext) -> dict:
    """Dispatch to the routed engine and save bytes to disk.

    Reads state: engine, prompt, source_path
    Writes state: candidate_path, bytes_size, generation_engine

    Returns dict with output_path, engine, bytes_size on success;
    `error` + `output_path=None` on any failure.
    """
    from nano_banana.utils import save_image

    engine = tool_context.state.get("engine", "")
    prompt = tool_context.state.get("prompt", "")
    source_path_str = tool_context.state.get("source_path", "")

    if not engine or not prompt or not source_path_str:
        return _missing_state_error(engine, prompt, source_path_str)

    if engine not in _SUPPORTED_ENGINES:
        return {
            "error": (f"unsupported engine {engine!r} — supported: {sorted(_SUPPORTED_ENGINES)}"),
            "output_path": None,
        }

    source_path = Path(source_path_str)
    if not source_path.exists():
        return {
            "error": f"source image missing: {source_path}",
            "output_path": None,
        }

    extra_refs = _resolve_logo_extra_refs(sku)

    try:
        img_bytes = _dispatch_engine(engine, prompt, source_path, extra_refs)
    except Exception as exc:
        log.exception("generate_image_fn: %s call failed", engine)
        return {
            "error": f"{engine} generation raised {type(exc).__name__}: {exc}",
            "output_path": None,
        }

    if not img_bytes:
        return {"error": f"{engine} returned no bytes", "output_path": None}

    sku_dir = _OUTPUT_DIR / sku
    sku_dir.mkdir(parents=True, exist_ok=True)
    out_path = sku_dir / f"{sku}-{view}-render.webp"
    try:
        save_image(img_bytes, out_path)
    except OSError as exc:
        return {
            "error": f"failed to write render to {out_path}: {exc}",
            "output_path": None,
        }

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
