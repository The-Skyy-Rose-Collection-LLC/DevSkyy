"""Dispatch a vision model over techflat references to detect split geometry.

Claude's own vision hit the per-conversation image batch limit, so this
script offloads techflat layout-detection to the project's Gemini vision
client. For each techflat it asks the model to return strict JSON describing:

  - garment_count   : how many distinct garments are in the image
  - layout          : lr | tb | grid_2x2 | single | other
  - regions[]       : per garment-view, a normalized bbox + colorway + view

A follow-on splitter (scripts/split_product_techflats.py) consumes the
analysis JSON and crops each region into {sku}-techflat-{view}.jpeg.

KEY REQUIREMENT
---------------
This calls a PAID vision API. It needs a Gemini key in the environment
(GEMINI_API_KEY / GOOGLE_AI_API_KEY / GOOGLE_API_KEY). This script does NOT
load .env (that path is walled off). Provide the key when you run it:

    GEMINI_API_KEY=... .venv/bin/python scripts/vision_inspect_techflats.py

Usage:
    # default: only techflats flagged for split in techflat-review.json
    .venv/bin/python scripts/vision_inspect_techflats.py
    # explicit files:
    .venv/bin/python scripts/vision_inspect_techflats.py --files lh-003-techflat.jpeg,sg-007-techflat.jpeg
    # everything:
    .venv/bin/python scripts/vision_inspect_techflats.py --all
    # preview the manifest + cost without dispatching:
    .venv/bin/python scripts/vision_inspect_techflats.py --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.core.paths import THEME_ROOT  # noqa: E402

PRODUCT_REFERENCES_DIR = THEME_ROOT / "data" / "product-references"
REVIEW_JSON = PRODUCT_REFERENCES_DIR / "techflat-review.json"
ANALYSIS_JSON = PRODUCT_REFERENCES_DIR / "techflat-vision-analysis.json"

# Per-image cost is negligible on Gemini Flash vision (~$0.0003/image) but we
# surface it anyway per the STOP-AND-SHOW protocol.
_EST_COST_PER_IMAGE = 0.0004

_PROMPT = """You are a fashion-tech-pack layout analyzer. Look at this product
techflat (a flat technical drawing/photo of one or more garments).

Return STRICT JSON only — no prose, no markdown fences. Schema:

{
  "garment_count": <int>,
  "layout": "lr" | "tb" | "grid_2x2" | "single" | "other",
  "regions": [
    {
      "bbox": [x0, y0, x1, y1],   // normalized 0-1 fractions, top-left origin
      "garment": "<short description e.g. 'baseball jersey'>",
      "colorway": "<dominant colors e.g. 'black with white piping'>",
      "view": "front" | "back" | "unknown"
    }
  ]
}

Rules:
- layout "lr" = two views side by side (left/right). "tb" = stacked top/bottom.
  "grid_2x2" = four quadrants. "single" = one garment one view. "other" = anything else.
- One region per distinct garment-VIEW. A front+back of the same garment = 2 regions.
- bbox must tightly bound each garment, excluding empty margins.
- If text/measurement annotations are present, do NOT include them in any bbox.
- Be literal about colors — say what you SEE, not what you expect.
"""


def _list_techflats() -> list[Path]:
    return sorted(PRODUCT_REFERENCES_DIR.glob("*-techflat.*"))


def _split_flagged() -> list[str]:
    """Filenames the founder flagged for split (layout lr/tb/grid) OR left
    unset but with a note containing 'split'. Excludes 'wrong' and 'single'.
    """
    if not REVIEW_JSON.is_file():
        return []
    review = json.loads(REVIEW_JSON.read_text(encoding="utf-8"))
    out = []
    for fn, v in review.items():
        layout = v.get("layout", "unset")
        note = (v.get("note") or "").lower()
        if layout in ("lr", "tb", "grid") or layout == "unset" and ("split" in note or "beanie" in note or "4 " in note):
            out.append(fn)
    return sorted(out)


def _get_vision_keys() -> list[str]:
    from skyyrose.elite_studio.gemini_rest import _get_keys

    return _get_keys()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--files", help="Comma-separated techflat filenames to inspect.")
    parser.add_argument("--all", action="store_true", help="Inspect every techflat.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show manifest + cost, don't dispatch."
    )
    args = parser.parse_args()

    all_files = {p.name: p for p in _list_techflats()}
    if args.all:
        targets = sorted(all_files)
    elif args.files:
        targets = [f.strip() for f in args.files.split(",") if f.strip()]
    else:
        targets = _split_flagged()

    targets = [t for t in targets if t in all_files]
    if not targets:
        print("No techflats to inspect (none flagged for split, or no match).")
        print("Flag layouts in the uploader Techflats tab, or pass --files / --all.")
        return 1

    from skyyrose.elite_studio.config import VISION_GEMINI_MODEL

    # ── STOP-AND-SHOW manifest ──────────────────────────────────────────
    print("=" * 60)
    print("VISION DISPATCH MANIFEST")
    print(f"  Model      : {VISION_GEMINI_MODEL}")
    print(f"  Images     : {len(targets)}")
    print(f"  Est. cost  : ~${len(targets) * _EST_COST_PER_IMAGE:.4f}")
    print(f"  Output     : {ANALYSIS_JSON.relative_to(_REPO_ROOT)}")
    print("  Targets:")
    for t in targets:
        print(f"    - {t}")
    print("=" * 60)

    if args.dry_run:
        print("[dry-run] no API calls made.")
        return 0

    keys = _get_vision_keys()
    if not keys:
        print("\nERROR: no Gemini vision key in the environment.")
        print("Provide one and re-run, e.g.:")
        print("  GEMINI_API_KEY=... .venv/bin/python scripts/vision_inspect_techflats.py")
        return 2

    from skyyrose.elite_studio.gemini_rest import analyze_vision

    results: dict = {}
    if ANALYSIS_JSON.is_file():
        try:
            results = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
        except Exception:
            results = {}

    for fn in targets:
        path = all_files[fn]
        b64 = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        print(f"\n[dispatch] {fn} -> {VISION_GEMINI_MODEL} ...")
        resp = analyze_vision(VISION_GEMINI_MODEL, _PROMPT, b64, mime_type="image/jpeg")
        if not resp.get("success"):
            print(f"  FAILED: {resp.get('error')}")
            results[fn] = {"error": resp.get("error")}
            continue
        text = resp["text"].strip()
        # Strip accidental markdown fences.
        if text.startswith("```"):
            text = text.split("```", 2)[1].lstrip("json").strip() if "```" in text[3:] else text
            text = text.strip("`").lstrip("json").strip()
        try:
            parsed = json.loads(text)
            results[fn] = parsed
            gc = parsed.get("garment_count", "?")
            lay = parsed.get("layout", "?")
            nregions = len(parsed.get("regions", []))
            print(f"  OK: garments={gc} layout={lay} regions={nregions}")
        except json.JSONDecodeError:
            print("  WARN: model did not return clean JSON; storing raw text.")
            results[fn] = {"raw": text}

    ANALYSIS_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(
        f"\nWrote analysis for {len(targets)} techflats -> {ANALYSIS_JSON.relative_to(_REPO_ROOT)}"
    )
    print("Review it, then run the splitter to crop per the detected regions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
