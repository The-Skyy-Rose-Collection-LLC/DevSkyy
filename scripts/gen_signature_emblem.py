"""One-off: generate Signature collection emblem candidates via gpt-image-2.

Brand asset (NOT a product/SKU render) — a companion piece to the founder-supplied
Black Rose + Love Hurts star-rose emblems. Uses OAIImageClient.generate() with a
transparent background so the output is a native alpha cutout (no rembg needed).

PAID: each candidate ≈ $0.40. Founder-authorized 2026-07-11 ("go paid on both").

    python scripts/gen_signature_emblem.py --n 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.oai_render import config
from scripts.oai_render.client import OAIImageClient

PROMPT = (
    "A 3D glass trophy-style luxury emblem, centered, on a fully transparent "
    "background. A faceted mirror-glass five-pointed star with polished GOLD "
    "(#D4AF37) veined edges and bevels; the star's interior is deep dark with a "
    "subtle warm gold sparkle. Centered inside the star, a single GOLD rose in "
    "full bloom — layered petals rendered in fine engraved-metal linework, the "
    "same painted-illustration / glass-sculpture technique as a matching black "
    "rose and red rose companion set. The rose stem descends with two leaves "
    "into a gold-trimmed pedestal base shaped like a heart, matching the scale "
    "and proportion of the companion emblems. Studio-lit, high luxury display-"
    "piece aesthetic, crisp reflections, no text, no words, no letters. The "
    "emblem is isolated on a completely flat, seamless, PURE WHITE (#FFFFFF) "
    "background with NO cast shadow, NO gradient, and NO scenery, so it can be "
    "cleanly masked to a transparent cut-out."
)

OUT_DIR = Path(__file__).resolve().parents[1] / "renders" / "oai" / "_signature"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2, help="number of candidates")
    args = ap.parse_args()

    if not config.api_key_present():
        print("OPENAI_API_KEY not present — aborting (no spend).", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OAIImageClient()
    est = args.n * config.EST_COST_PER_IMAGE_USD
    print(f"gpt-image-2 · {args.n} candidate(s) · transparent · est ${est:.2f}")

    for i in range(1, args.n + 1):
        img = client.generate(
            prompt=PROMPT,
            size="1024x1536",
            quality="high",
            output_format="png",
            background="opaque",
        )
        out = OUT_DIR / f"signature-emblem-v{i}.png"
        out.write_bytes(img)
        print(f"  wrote {out}  ({len(img)} bytes)")

    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
