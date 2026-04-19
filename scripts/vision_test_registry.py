#!/usr/bin/env python3
"""Vision test for registry alignment.

Scans existing product imagery, scores each image against every pending SKU's
color_spec and text_spec via the fidelity module, then surfaces top-N candidates
so the operator can promote pending entries to locked masters via Manifest.lock().

CLIP fidelity is intentionally NOT used here: CLIP needs a reference master,
but this tool's job is to DISCOVER what the master should be. Color (ΔE* CIE76)
plus OCR text match are the two signals available pre-lock.

Usage:
    python scripts/vision_test_registry.py
    python scripts/vision_test_registry.py --strategy weighted --top-n 5
    python scripts/vision_test_registry.py --sku br-001 --sku lh-002
    python scripts/vision_test_registry.py --collection black-rose --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.elite_studio.fidelity import CheckResult, check_color  # noqa: E402
from skyyrose.elite_studio.master_registry import Manifest  # noqa: E402

DEFAULT_IMAGE_DIR = (
    _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
DEFAULT_REPORT = _REPO_ROOT / "vision-test-report.json"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
STRATEGIES = ("veto", "weighted", "color-only")


def gather_images(image_dir: Path) -> list[Path]:
    """Recursively collect image files, skipping hidden dirs and _references/."""
    images: list[Path] = []
    for p in image_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
            continue
        if any(part.startswith(".") or part == "_references" for part in p.parts):
            continue
        images.append(p)
    return sorted(images)


def _extract_ocr_text(image_path: Path) -> str | None:
    """Run pytesseract once and return lowered text, or None if unavailable."""
    try:
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as img:
            return pytesseract.image_to_string(img).lower()
    except Exception:
        return None


def _match_text(extracted: str | None, text_spec: list[str]) -> CheckResult:
    """Substring-match needles against cached OCR text. Mirrors fidelity.check_text shape."""
    if not text_spec:
        return CheckResult(
            name="text", available=True, passed=True, score=1.0, reason="no text_spec"
        )
    if extracted is None:
        return CheckResult(name="text", available=False, reason="pytesseract unavailable")
    found = [n for n in text_spec if n.lower() in extracted]
    missing = [n for n in text_spec if n.lower() not in extracted]
    rate = len(found) / len(text_spec)
    return CheckResult(
        name="text",
        available=True,
        score=round(rate, 3),
        threshold=1.0,
        passed=rate >= 1.0,
        details={"found": found, "missing": missing},
    )


def combined_score(color: dict, text: dict, strategy: str) -> float:
    """Lower = better candidate. inf = disqualified.

    veto:        any failed check disqualifies; else rank by color ΔE*
    weighted:    color ΔE* + (1 - text_rate) * 5 penalty
    color-only:  rank by color ΔE*, ignore text entirely
    """
    c_score = color.get("score")
    if c_score is None:
        return float("inf")
    c_score = float(c_score)

    if strategy == "veto":
        if not color.get("passed"):
            return float("inf")
        if text.get("available") and not text.get("passed"):
            return float("inf")
        return c_score
    if strategy == "weighted":
        penalty = 0.0
        if text.get("available") and text.get("score") is not None:
            penalty = (1.0 - float(text["score"])) * 5.0
        return c_score + penalty
    return c_score  # color-only


def _json_safe(score: float) -> float | str:
    return "inf" if score == float("inf") else score


def _rel_to_repo(p: Path) -> str:
    try:
        return str(p.relative_to(_REPO_ROOT))
    except ValueError:
        return str(p)


def run_vision_test(
    manifest: Manifest,
    images: list[Path],
    *,
    strategy: str = "veto",
    top_n: int = 3,
    sku_filter: list[str] | None = None,
    collection_filter: str | None = None,
) -> dict[str, Any]:
    """Rank all images against every pending SKU. Returns a JSON-safe report dict."""
    color_cache: dict[tuple[Path, str], CheckResult] = {}
    ocr_cache: dict[Path, str | None] = {}

    def get_color(img: Path, spec: dict) -> CheckResult:
        if not spec:
            return CheckResult(name="color", available=True, passed=True, reason="no color_spec")
        key = (img, json.dumps(spec, sort_keys=True))
        cached = color_cache.get(key)
        if cached is None:
            cached = check_color(img, spec)
            color_cache[key] = cached
        return cached

    def get_ocr(img: Path) -> str | None:
        if img not in ocr_cache:
            ocr_cache[img] = _extract_ocr_text(img)
        return ocr_cache[img]

    sku_results: dict[str, dict] = {}

    for sku in manifest.list_skus():
        entry = manifest.require(sku)
        if entry.is_locked:
            continue
        if sku_filter and sku not in sku_filter:
            continue
        if collection_filter and entry.collection != collection_filter:
            continue

        records: list[dict] = []
        for img in images:
            c = get_color(img, entry.color_spec or {}).to_dict()
            t = _match_text(get_ocr(img), entry.text_spec or []).to_dict()
            score = combined_score(c, t, strategy)
            records.append(
                {
                    "image": _rel_to_repo(img),
                    "color": c,
                    "text": t,
                    "combined_score": _json_safe(score),
                    "_sort": score,
                }
            )
        records.sort(key=lambda r: r["_sort"])
        for r in records:
            r.pop("_sort", None)

        qualified = sum(1 for r in records if r["combined_score"] != "inf")
        sku_results[sku] = {
            "collection": entry.collection,
            "status": entry.status,
            "color_spec": entry.color_spec,
            "text_spec": entry.text_spec,
            "candidates": records[:top_n],
            "total_ranked": len(records),
            "qualified_candidates": qualified,
        }

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "strategy": strategy,
        "image_count": len(images),
        "sku_count": len(sku_results),
        "ocr_available": any(v is not None for v in ocr_cache.values()),
        "skus": sku_results,
    }


def print_summary(report: dict) -> None:
    print(
        f"\nStrategy: {report['strategy']} | "
        f"Images: {report['image_count']} | SKUs: {report['sku_count']} | "
        f"OCR: {'yes' if report.get('ocr_available') else 'unavailable'}"
    )
    print(f"{'SKU':<10} {'COLLECTION':<14} {'QUAL':>5}  {'SCORE':>8}  BEST CANDIDATE")
    print("-" * 88)
    for sku, data in report["skus"].items():
        best = data["candidates"][0] if data["candidates"] else None
        if best and best["combined_score"] != "inf":
            score_str = f"{best['combined_score']:.2f}"
            name = Path(best["image"]).name
        else:
            score_str = "—"
            name = "NO MATCH"
        print(
            f"{sku:<10} {data['collection']:<14} "
            f"{data['qualified_candidates']:>5}  {score_str:>8}  {name}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--image-dir", type=Path, default=DEFAULT_IMAGE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--strategy",
        choices=STRATEGIES,
        default="veto",
        help="'veto' (default): any failed check disqualifies. "
        "'weighted': color ΔE + text penalty. 'color-only': ignore text.",
    )
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--sku", action="append", help="Limit to specific SKU(s); repeatable")
    parser.add_argument("--collection", help="Limit to a single collection slug")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print summary only; do not write report"
    )
    args = parser.parse_args(argv)

    if not args.image_dir.is_dir():
        print(f"ERROR: image dir not found: {args.image_dir}", file=sys.stderr)
        return 1

    images = gather_images(args.image_dir)
    rel_dir = _rel_to_repo(args.image_dir)
    print(f"Scanning {len(images)} images from {rel_dir}")

    manifest = Manifest.load()
    total = len(manifest.list_skus())
    pending = sum(1 for s in manifest.list_skus() if not manifest.require(s).is_locked)
    print(f"Manifest: {pending} pending / {total} total SKUs")
    if pending == 0:
        print("No pending SKUs to align. Exiting.")
        return 0

    report = run_vision_test(
        manifest,
        images,
        strategy=args.strategy,
        top_n=args.top_n,
        sku_filter=args.sku,
        collection_filter=args.collection,
    )
    print_summary(report)

    if not args.dry_run:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nReport written: {_rel_to_repo(args.output)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
