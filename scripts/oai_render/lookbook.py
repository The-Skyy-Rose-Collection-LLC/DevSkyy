"""On-model lookbook generation — gpt-image-2 edit of a real garment into a scene.

Folded from the engine-comparison prototype (renders/oai/_lookbook/_prototype/):
gpt-image-2 **edit** won decisively over FASHN try-on and FLUX Kontext because it
absorbs a flat product *techflat* + a styled scene in a single pass — producing a
model who genuinely *wears* the garment in the scene, no floating. FASHN needs a
ghost-mannequin/product garment image (wrong input contract for our flat
techflats); Kontext's masked scene-drop produced blank output. Verdict + evidence:
``renders/oai/_lookbook/_prototype/NOTES.md`` (bug-141 for the FASHN dead-end).

This module reuses the canonical OAI imagery infrastructure rather than
re-implementing it:
  • garment refs  -> ``references.build_references`` (canonical SKU→techflat map,
                     hard-fails on a missing garment — no silent fallback)
  • catalog facts -> ``catalog_loader.get_product_with_dossier``
  • the edit call -> ``client.OAIImageClient`` (retry/backoff, gpt-image-2 high)
  • cost + gate   -> ``cost.CostManifest`` / ``format_manifest`` / ``SpendTracker``

CLI:
    python -m scripts.oai_render.lookbook plan     --sku lh-004 --scene <scene.png>
    python -m scripts.oai_render.lookbook generate --sku lh-004 --scene <scene.png> --yes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Ensure OPENAI_API_KEY is present for config.get_api_key() — the project env
# loader (root .env + gemini/.env) may not carry it; .env.hf does. config reads
# the key LAZILY (at OAIImageClient init, in generate_one), so loading .env.hf
# here at import — before any client is built — is sufficient. The interpreter
# reads the value; it is never logged.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env.hf", override=False)
except ImportError:  # pragma: no cover - dotenv optional if key already exported
    pass

from skyyrose.core.catalog_loader import get_product_with_dossier  # noqa: E402
from skyyrose.core.dossier_loader import DossierMissingError  # noqa: E402

from . import config, cost, references  # noqa: E402
from .client import OAIImageClient  # noqa: E402

# Per-collection scene register (the prompt's setting; the actual backdrop image
# is supplied via --scene). love-hurts = the Beauty-and-the-Beast gothic world;
# the others default to the brand's Oakland-concrete-luxury register.
COLLECTION_SCENE: dict[str, str] = {
    "love-hurts": (
        "a candlelit gothic cathedral interior with a Beauty-and-the-Beast mood — "
        "ornate stone arches, stained glass, crimson velvet drapes, an enchanted "
        "rose under a glass cloche, rose petals scattered on the stone floor, "
        "dramatic warm candlelight"
    ),
    "black-rose": (
        "a rain-slick West Oakland concrete underpass at night — brutalist pillars, "
        "silver-rimmed light, wet asphalt reflections, cold monochrome luxury"
    ),
    "signature": (
        "an Oakland rooftop at warm predawn — raw concrete parapet, the Bay Bridge "
        "glowing amber in the haze, gold-graded cinematic editorial light"
    ),
    "kids-capsule": (
        "an Oakland rooftop at magic-hour dusk facing the downtown skyline — warm "
        "rose-gold light, Bay Bridge on the horizon, grounded and unhurried"
    ),
}
DEFAULT_SCENE = "an Oakland concrete-luxury editorial setting with dramatic directional light"


def _garment_paths(sku: str, collection: str) -> list[Path]:
    """Canonical front-only garment references for an on-model render.

    Front-only (``include_back=False``) avoids the back-view / multi-panel collage
    failure mode. Raises ``references.MissingReferenceError`` if no garment source
    exists — never silently substitutes.
    """
    refs = references.build_references(sku, collection, include_back=False)
    # On-model: feed the garment photo/techflat, and a sport patch only when the
    # SKU requires it (jerseys). Exclude collection LOGO refs — as a separate edit
    # input on a worn render the model may treat the branding script as a second
    # garment; the techflat already carries the branding in situ.
    needs_patch = references.requires_patch(sku)
    keep = [
        r
        for r in refs
        if r.path.exists() and (r.kind == "garment" or (r.kind == "patch" and needs_patch))
    ]
    if not keep:
        raise references.MissingReferenceError(f"no usable garment reference for {sku}")
    return [r.path for r in keep]


def _resolve(sku: str, collection: str | None) -> tuple[str, str, str]:
    """Return (name, collection, scene_desc) from the canonical catalog row.

    ``get_product_with_dossier`` hard-fails (KeyError for an unknown SKU,
    DossierMissingError for an un-authored dossier) — convert both to
    MissingReferenceError so ``main`` reports a clean ABORT, never a traceback.
    """
    try:
        row = get_product_with_dossier(sku)
    except (KeyError, DossierMissingError) as exc:
        raise references.MissingReferenceError(f"{sku}: {exc}") from exc
    name = (row.get("name") or sku).strip()
    coll = (collection or row.get("collection") or "").strip()
    scene_desc = COLLECTION_SCENE.get(coll, DEFAULT_SCENE)
    return name, coll, scene_desc


def build_prompt(name: str, scene_desc: str) -> str:
    """Lookbook 'worn, not floating' prompt — garment is the protagonist."""
    return (
        f"Full-body editorial fashion photograph of a model wearing this exact "
        f"{name}, worn naturally with realistic drape, fit, fabric folds and grounded "
        f"contact shadows. Reproduce the garment's exact design, colors, embroidery "
        f"and lettering from the reference image — do not invent, recolor or restyle "
        f"any part of the garment. The model stands in {scene_desc}. The garment is "
        f"the protagonist of the frame. Cinematic, photographic, ultra-detailed, 8k."
    )


def generate_one(sku: str, scene: Path, collection: str | None, dest: Path) -> bytes:
    """Render one on-model lookbook image. Returns PNG bytes, writes to dest."""
    if not scene.exists():
        raise FileNotFoundError(f"scene image not found: {scene}")
    name, coll, scene_desc = _resolve(sku, collection)
    garments = _garment_paths(sku, coll)
    image_paths = [*garments, scene]  # garments lead (authority); scene = context
    prompt = build_prompt(name, scene_desc)
    data = OAIImageClient().edit(prompt=prompt, image_paths=image_paths)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def _manifest(skus: list[str]) -> cost.CostManifest:
    entries = []
    for sku in skus:
        name, coll, _ = _resolve(sku, None)
        # Count the garment refs actually sent to the edit call (not all of
        # build_references, which may include excluded logo refs) so the manifest
        # never overstates the API inputs.
        ref_count = len(_garment_paths(sku, coll))
        entries.append(cost.ManifestEntry(sku=sku, name=name, n_images=1, ref_count=ref_count))
    return cost.CostManifest(entries=entries)


def _run_batch(skus: list[str], scene: Path, collection: str | None, out_dir: Path) -> int:
    """Render each SKU on-model, tracking spend against the hard cap. Returns exit code."""
    import openai

    tracker = cost.SpendTracker()
    failures = 0
    for sku in skus:
        safe_sku = re.sub(r"[^a-z0-9\-]", "", sku.lower())
        dest = out_dir / f"{safe_sku}-onmodel.png"
        if not tracker.can_afford(config.EST_COST_PER_IMAGE_USD):
            print(f"STOP: spend cap ${tracker.cap_usd:.2f} reached before {sku}", file=sys.stderr)
            break
        try:
            print(f"[{sku}] rendering on-model ...", flush=True)
            data = generate_one(sku, scene, collection, dest)
            tracker.add(config.EST_COST_PER_IMAGE_USD)
            print(f"[{sku}] [ok] {dest} ({len(data) // 1024} KB)", flush=True)
        except openai.AuthenticationError:
            # Never print str(exc) — the OpenAI SDK echoes a partial key in it.
            print(
                f"[{sku}] [fail] AuthenticationError: check {config.API_KEY_ENV}", file=sys.stderr
            )
            failures += 1
            break  # every subsequent call fails identically
        except (references.MissingReferenceError, FileNotFoundError) as exc:
            print(f"[{sku}] [fail] {type(exc).__name__}: {exc}", file=sys.stderr)
            failures += 1
        except Exception as exc:  # noqa: BLE001 — surface, continue the batch
            failures += 1
            print(f"[{sku}] [fail] {type(exc).__name__}: {exc}", file=sys.stderr)
    print(f"\nDone. spent ~${tracker.spent_usd:.2f}, {failures} failed -> {out_dir}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="On-model lookbook (gpt-image-2 edit)")
    ap.add_argument("mode", choices=["plan", "generate"])
    ap.add_argument("--sku", action="append", required=True, help="SKU(s) to render")
    ap.add_argument("--scene", type=Path, required=True, help="styled backdrop image")
    ap.add_argument("--collection", default=None, help="override collection (else from catalog)")
    ap.add_argument("--out", type=Path, default=config.OUTPUT_DIR / "_lookbook" / "onmodel")
    ap.add_argument("--yes", action="store_true", help="confirm the paid run (generate)")
    args = ap.parse_args(argv)

    # Anchor --out inside the canonical output dir — a traversal --out must not
    # let a write land outside renders/.
    out_dir = Path(args.out).resolve()
    if not out_dir.is_relative_to(config.OUTPUT_DIR.resolve()):
        print(f"ABORT: --out must be inside {config.OUTPUT_DIR}", file=sys.stderr)
        return 2

    if not args.scene.exists():
        print(f"ABORT: scene not found: {args.scene}", file=sys.stderr)
        return 2

    try:
        manifest = _manifest(args.sku)
    except references.MissingReferenceError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2

    print(cost.format_manifest(manifest))
    if args.mode == "plan":
        return 0

    try:
        cost.enforce_cap(manifest)
    except cost.CostCapExceeded as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2
    if not args.yes:
        print("\nRefusing to spend without --yes (STOP-AND-SHOW gate).", file=sys.stderr)
        return 3
    if not config.api_key_present():
        print(f"ABORT: {config.API_KEY_ENV} not set (add to .env.hf)", file=sys.stderr)
        return 2

    return _run_batch(args.sku, args.scene, args.collection, out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
