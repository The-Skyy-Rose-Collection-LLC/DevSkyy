"""Render empty-set BACKDROP previews of the locked COLLECTION_SCENE strings.

Pure text-to-image (``images.generate`` — no garment, no model) so the founder
can judge the *scene direction* before committing to a paid on-model re-render.
Each preview visualizes one collection's locked ``scene_desc`` as an empty
editorial set plate.

Single source of truth: the scene strings are IMPORTED from ``lookbook`` — never
re-typed here, so a preview can never drift from what the real pipeline renders.

Keys load at runtime from .env.hf via the lookbook import side-effect; the value
is read by the SDK and never logged.

CLI:
    python -m scripts.oai_render.scene_preview plan
    python -m scripts.oai_render.scene_preview generate --yes
    python -m scripts.oai_render.scene_preview generate --collection love-hurts --yes
"""

from __future__ import annotations

import argparse
import base64
import logging
import sys
from pathlib import Path

import openai
from openai import OpenAI

from . import config
from .lookbook import COLLECTION_SCENE  # locked strings — single source of truth

_log = logging.getLogger(__name__)

MODEL = "gpt-image-2"
SIZE = "1536x1024"  # landscape establishing plate
QUALITY = "high"
OUT_DIR = config.OUTPUT_DIR / "_lookbook" / "onmodel"
HARD_CAP_USD = 5.0

# Frame the locked scene_desc as an empty environment plate (no people) so the
# preview shows the SETTING/light, not a model. The garment is absent by design.
_PROMPT = (
    "Cinematic establishing photograph of {scene}. An empty editorial set — no "
    "people, no mannequins, no garments — just the environment, its architecture, "
    "surfaces and light, as a luxury fashion backdrop plate. Photographic, "
    "ultra-detailed, 8k."
)


def _prompt_for(collection: str) -> str:
    # Validate collection is from our allowed set to prevent injection
    if collection not in COLLECTION_SCENE:
        raise KeyError(f"unknown collection: {collection}")
    scene = COLLECTION_SCENE[collection]
    # scene is from a hardcoded dict, but use template string for safety
    return _PROMPT.replace("{scene}", scene)


def _generate_one(collection: str, dest: Path) -> bytes:
    client = OpenAI(api_key=config.get_api_key(), timeout=240.0)
    resp = client.images.generate(
        model=MODEL,
        prompt=_prompt_for(collection),
        size=SIZE,
        quality=QUALITY,
        n=1,
    )
    b64 = resp.data[0].b64_json
    if not b64:
        raise RuntimeError("openai returned no image data")
    data = base64.b64decode(b64)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def _manifest(collections: list[str]) -> str:
    n = len(collections)
    total = n * config.EST_COST_PER_IMAGE_USD
    lines = [
        "STOP — Confirm before proceeding (PAID gpt-image-2 GENERATE — scene backdrop previews):",
        "",
        f"  Model      : {MODEL} (generate, quality={QUALITY}, size={SIZE})",
        "  Mode       : empty-set backdrop plate (no model, no garment)",
        f"  Scenes     : {', '.join(collections)}",
        f"  Images     : {n}",
        f"  Est. cost  : ~${total:.2f}  (FLOOR @ ${config.EST_COST_PER_IMAGE_USD:.2f}/img; OpenAI bills actual)",
        f"  Hard cap   : ${HARD_CAP_USD:.2f}" + ("  EXCEEDED" if total > HARD_CAP_USD else ""),
        f"  Key present: {'yes' if config.api_key_present() else 'NO'}",
        f"  Output     : {OUT_DIR.relative_to(config.PROJECT_ROOT)}/_scene-preview-<collection>.png",
        "",
        "Proceed? [y/N]",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(h)
    _log.setLevel(logging.INFO)
    _log.propagate = False

    ap = argparse.ArgumentParser(description="Scene backdrop previews (gpt-image-2 generate)")
    ap.add_argument("mode", choices=["plan", "generate"])
    ap.add_argument(
        "--collection",
        action="append",
        choices=sorted(COLLECTION_SCENE),
        help="default = all four",
    )
    ap.add_argument("--yes", action="store_true", help="confirm the paid run (generate)")
    args = ap.parse_args(argv)

    collections = args.collection or sorted(COLLECTION_SCENE)
    total = len(collections) * config.EST_COST_PER_IMAGE_USD
    if total > HARD_CAP_USD:
        _log.error("ABORT: estimate $%.2f exceeds hard cap $%.2f", total, HARD_CAP_USD)
        return 2

    print(_manifest(collections))
    if args.mode == "plan":
        return 0
    if not args.yes:
        _log.error("\nRefusing to spend without --yes (STOP-AND-SHOW gate).")
        return 3
    if not config.api_key_present():
        _log.error("ABORT: %s not set (add to .env.hf)", config.API_KEY_ENV)
        return 2

    failures = 0
    for coll in collections:
        # Sanitize collection name to prevent path traversal
        safe_coll = coll.replace("/", "_").replace("\\", "_").replace("..", "_")
        dest = OUT_DIR / f"_scene-preview-{safe_coll}.png"
        # Validate dest is within OUT_DIR to prevent path traversal
        try:
            dest.resolve().relative_to(OUT_DIR.resolve())
        except ValueError:
            _log.error("[%s] ABORT: path traversal attempt", coll)
            return 2
        try:
            _log.info("[%s] rendering backdrop ...", coll)
            data = _generate_one(coll, dest)
            _log.info("[%s] ok %s (%d KB)", coll, dest, len(data) // 1024)
        except openai.AuthenticationError:
            # Never log str(exc) — the SDK echoes a partial key in it.
            _log.error("[%s] FAIL AuthenticationError: check %s", coll, config.API_KEY_ENV)
            return 1
        except Exception as exc:  # noqa: BLE001 — surface type, continue the batch
            failures += 1
            _log.error("[%s] FAIL %s: render failed", coll, type(exc).__name__)
    _log.info("\nDone. %d ok, %d failed -> %s", len(collections) - failures, failures, OUT_DIR)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
