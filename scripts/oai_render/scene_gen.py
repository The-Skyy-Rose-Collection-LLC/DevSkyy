"""Scene-only backdrop generation (no product references) for immersive rooms.

Text-to-image via :meth:`OAIImageClient.generate` — used where no founder scene
master exists (Kids Capsule). Same money discipline as the rest of the pipeline:
dry-run by default, cost manifest printed, hard cap enforced, ``--yes`` required
to spend.

Usage:
    python -m scripts.oai_render.scene_gen plan
    python -m scripts.oai_render.scene_gen generate --yes
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from . import config
from .cost import CostManifest, ManifestEntry, enforce_cap, format_manifest

# Landscape backdrop, both dimensions divisible by 16 (gpt-image-2 requirement);
# matches the cathedral reference master's 3:2 aspect.
_SCENE_SIZE = "1344x896"

# Brand-canon scene intents for the two Kids Capsule immersive rooms.
# SOURCE OF TRUTH: docs/brand/collection-stories.md "Kids Capsule — The Heir" +
# data/collections/kids-capsule/sot.json palette (bg #0A0A0A, rose_gold #B76E79,
# gold #D4AF37). Founder mandate, VERBATIM: "No pastels. No cartoons. Skyy Rose
# doesn't wear that. She wears what her father built — premium, dark, elegant.
# Scaled down but never dumbed down." Products are dark-first (red/black,
# purple/black hoodie sets). NEVER paraphrase this into pastel/princess/plush.
_KC_STYLE = (
    "Painterly cinematic interior photograph. DARK-FIRST luxury: near-black "
    "(#0A0A0A) architecture and floors, warm rose-gold (#B76E79) and antique "
    "gold (#D4AF37) accent lighting, black marble with rose-gold veining. "
    "Premium, dark, elegant — an heir's inheritance, not a nursery. "
    "STRICTLY NO pastels, NO cartoons, NO plush toys, NO tulle or princess "
    "styling, no people, no readable text, no logos."
)

_SCENES: tuple[tuple[str, str], ...] = (
    (
        "scene-kids-capsule-playroom",
        "The Playroom, reimagined as a child-scaled dark atelier: the same "
        "black-marble and rose-gold showroom language as a luxury flagship, "
        "scaled down — low black-marble plinths, small garment alcoves lit in "
        "warm rose-gold holding dark red/black and purple/black kidswear "
        "silhouettes, a low reading nook in black velvet with gold piping, "
        f"tall windows with night city glow. Legacy, not nostalgia. {_KC_STYLE}",
    ),
    (
        "scene-kids-capsule-runway",
        "The Runway: a scaled-down catwalk in the family house style — matte "
        "black runway deck edged in glowing rose-gold light, black-marble "
        "floor, dramatic pools of warm gold spotlight, dark architectural "
        "arches behind the stage kissed with rose-gold uplighting, low black "
        f"velvet seating. Powerful, elevated, born into legacy. {_KC_STYLE}",
    ),
)

_OUT_DIR = config.OUTPUT_DIR / "_scenes" / "kids-capsule"


@dataclass
class _Args:
    mode: str
    yes: bool


def _parse(argv: list[str] | None) -> _Args:
    ap = argparse.ArgumentParser(description="Scene-only backdrop generation (gpt-image-2)")
    ap.add_argument("mode", choices=["plan", "generate"])
    ap.add_argument("--yes", action="store_true", help="confirm the paid run (generate)")
    ns = ap.parse_args(argv)
    return _Args(mode=ns.mode, yes=ns.yes)


def _manifest() -> CostManifest:
    entries = [
        ManifestEntry(sku=name, name=name, n_images=1, ref_count=0, note="scene-only backdrop")
        for name, _prompt in _SCENES
    ]
    return CostManifest(entries=entries)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    manifest = _manifest()
    print(format_manifest(manifest))

    if args.mode == "plan":
        print("\nPlan only — zero API calls. Re-run with `generate --yes` to spend.")
        return 0
    if not args.yes:
        print("\nRefusing to spend without --yes.", file=sys.stderr)
        return 1

    enforce_cap(manifest)

    from .client import OAIImageClient

    client = OAIImageClient()
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, prompt in _SCENES:
        out = _OUT_DIR / f"{name}.png"
        print(f"\n[{name}] generating ({_SCENE_SIZE}) ...", flush=True)
        data = client.generate(prompt=prompt, size=_SCENE_SIZE, background="opaque")
        out.write_bytes(data)
        print(f"  -> {out} ({out.stat().st_size // 1024}KB)", flush=True)

    print("\nDone. Review the scenes eyes-on before converting/deploying.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
