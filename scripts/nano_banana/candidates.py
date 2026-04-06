"""Multi-candidate generation — N candidates per view from multiple engines.

Generates candidates using:
- Nano Banana Pro (gemini-3-pro-image-preview) — primary
- Nano Banana Pro with temperature variation — seed diversity
- GPT Image 1.5 — text rendering specialist (when billing available)

All candidates stored in data/candidates/{sku}/{view}/ with metadata.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CANDIDATES_DIR = PROJECT_ROOT / "data" / "candidates"


@dataclass
class Candidate:
    """Metadata for a single generated candidate."""

    sku: str
    view: str
    engine: str
    model: str
    path: str
    size_kb: float
    created_at: str
    attempt: int = 1
    feedback_applied: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _candidate_dir(sku: str, view: str) -> Path:
    path = CANDIDATES_DIR / sku / view
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_candidate(
    image_bytes: bytes,
    sku: str,
    view: str,
    engine: str,
    model: str,
    attempt: int = 1,
    feedback: bool = False,
) -> Candidate:
    """Save candidate image + metadata."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{engine}_{attempt:02d}_{ts}.webp"
    out_path = _candidate_dir(sku, view) / filename
    out_path.write_bytes(image_bytes)
    size_kb = len(image_bytes) / 1024
    log.info("Saved candidate: %s (%.0fKB)", out_path.relative_to(PROJECT_ROOT), size_kb)

    return Candidate(
        sku=sku,
        view=view,
        engine=engine,
        model=model,
        path=str(out_path.relative_to(PROJECT_ROOT)),
        size_kb=size_kb,
        created_at=datetime.now().isoformat(),
        attempt=attempt,
        feedback_applied=feedback,
    )


def generate_candidates(
    clients: dict,
    sku: str,
    view: str,
    source_path: Path,
    prompt: str,
    n: int = 3,
    engines: list[str] = None,
    attempt: int = 1,
    feedback_applied: bool = False,
) -> list[Candidate]:
    """Generate N candidates using multiple engines.

    Args:
        clients: {"gemini": genai.Client, "openai": openai.OpenAI, ...}
        sku: product SKU
        view: 'front' | 'back' | 'branding'
        source_path: reference image path
        prompt: DNA-derived prompt
        n: total candidates to generate
        engines: list of engines to use (default: nano_pro, nano_pro_variant)
        attempt: retry attempt number
        feedback_applied: True if prompt includes targeted corrections
    """
    from nano_banana.generate import GEMINI_PRO, GPT_IMAGE_MODEL, generate_gemini, generate_gpt
    from nano_banana.utils import quality_gate

    if engines is None:
        engines = ["nano_pro", "nano_pro_variant"]
        if clients.get("openai"):
            engines.append("gpt_image")
        engines = engines[:n]

    candidates = []
    engines_to_try = engines * ((n // len(engines)) + 1)  # cycle if n > len(engines)

    for i in range(n):
        engine = engines_to_try[i]
        log.info(
            "[%s/%s] candidate %d/%d via %s (attempt %d)", sku, view, i + 1, n, engine, attempt
        )

        image_bytes = None
        model_used = ""

        if engine == "nano_pro" and clients.get("gemini"):
            image_bytes = generate_gemini(
                clients["gemini"],
                source_path,
                prompt,
                model=GEMINI_PRO,
                enhanced=(attempt > 1),
            )
            model_used = GEMINI_PRO
        elif engine == "nano_pro_variant" and clients.get("gemini"):
            # Slight prompt variation for diversity (add a nudge at end)
            variant_prompt = prompt + f"\n\nRender with subtle lighting variation #{i + 1}."
            image_bytes = generate_gemini(
                clients["gemini"],
                source_path,
                variant_prompt,
                model=GEMINI_PRO,
                enhanced=(attempt > 1),
            )
            model_used = GEMINI_PRO
        elif engine == "gpt_image" and clients.get("openai"):
            image_bytes = generate_gpt(clients["openai"], prompt, source_path)
            model_used = GPT_IMAGE_MODEL
        else:
            log.warning("Engine %s skipped (client unavailable)", engine)
            continue

        if image_bytes and quality_gate(image_bytes, sku, view):
            cand = _save_candidate(
                image_bytes, sku, view, engine, model_used, attempt, feedback_applied
            )
            candidates.append(cand)
        else:
            log.warning("Candidate %d via %s failed quality gate", i + 1, engine)

    return candidates


def save_candidate_manifest(sku: str, view: str, candidates: list[Candidate]) -> Path:
    """Save manifest of all candidates for a SKU/view."""
    manifest_path = _candidate_dir(sku, view) / "_manifest.json"
    existing = []
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
    existing.extend([c.to_dict() for c in candidates])
    manifest_path.write_text(json.dumps(existing, indent=2) + "\n")
    return manifest_path
