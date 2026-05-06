"""Single-SKU 3-way source-strategy comparison — diagnostic, paid.

Tests Hypothesis: "the source image dominates the generator signal,
not the text prompt." Runs the same SKU through the production
pipeline three times, varying ONLY the source image:

  Strategy 1 — `render`     : existing on-disk render (current default,
                              defective for br-001 — scored 42 → 30 with
                              Layer 3+3.5)
  Strategy 2 — `techflat`   : data/product-bundles/{name}/techflat-front.*
                              (clean canonical 2D layout)
  Strategy 3 — `source-photo`: data/product-bundles/{name}/source-photo.*
                              (real product photo if available)

Holds everything else constant: same dossier, same Layer 3 + Layer 3.5,
same engine routing (input to router), same QA tournament. The ONLY
variable is the source image passed to the pipeline.

If techflat or source-photo scores SIGNIFICANTLY higher than render-as-source,
the ADK design's `ResolveSourceTool` should default to non-render sources.

Cost: ~$0.30 (3 × $0.10/SKU). Wall: ~24 min sequential.

Usage:
    python scripts/nano_banana/_compare_source_strategies.py --sku br-001
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


def _load(p: Path) -> None:
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _load_env_files() -> list[str]:
    for envf in (
        ".env.judge-gpt-vision",
        ".env.judge-gemini-vision",
        ".env.judge-opus-thinking",
        ".env.hf",
        ".env.secrets",
    ):
        _load(REPO / envf)
    needed = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "FAL_KEY"]
    return [k for k in needed if not os.environ.get(k)]


def _resolve_strategy_source(sku: str, name: str, strategy: str) -> Path | None:
    """Return the source image path for a given strategy, or None if unavailable."""
    img_dir = REPO / "wordpress-theme/skyyrose-flagship/assets/images/products"
    bundle_dir = REPO / "data/product-bundles" / name

    if strategy == "render":
        # The existing on-disk render (whatever the catalog source_override resolves to)
        from nano_banana.catalog import load_catalog

        row = load_catalog().get(sku, {})
        override = row.get("source_override", "")
        if override:
            p = img_dir / override
            return p if p.exists() else None
        return None

    if strategy == "techflat":
        for ext in ("jpeg", "jpg", "png", "webp"):
            p = bundle_dir / f"techflat-front.{ext}"
            if p.exists():
                return p
        return None

    if strategy == "source-photo":
        for ext in ("jpg", "jpeg", "png", "webp"):
            p = bundle_dir / f"source-photo.{ext}"
            if p.exists():
                return p
        # photo-front is the conventional alternate
        for ext in ("jpg", "jpeg", "png", "webp"):
            p = bundle_dir / f"photo-front.{ext}"
            if p.exists():
                return p
        return None

    raise ValueError(f"unknown strategy: {strategy}")


log = logging.getLogger("compare_source_strategies")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sku", type=str, default="br-001")
    parser.add_argument(
        "--strategies",
        type=str,
        default="render,techflat,source-photo",
        help="Comma-separated source strategies to test",
    )
    args = parser.parse_args()

    missing = _load_env_files()
    if missing:
        print(f"ERROR: missing env keys: {missing}", file=sys.stderr)
        return 1

    from nano_banana.catalog import load_catalog
    from nano_banana.pipeline import ProductionPipeline

    catalog = load_catalog()
    row = catalog.get(args.sku)
    if not row:
        print(f"ERROR: {args.sku} not in catalog", file=sys.stderr)
        return 2
    name = row.get("name", args.sku)
    collection = row.get("collection", "")

    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    # Resolve source paths upfront — any missing strategy aborts before paid calls
    resolutions: dict[str, Path | None] = {}
    for s in strategies:
        path = _resolve_strategy_source(args.sku, name, s)
        resolutions[s] = path
        if path is None:
            print(f"WARN: strategy '{s}' has no source for {args.sku} — will skip", file=sys.stderr)

    runnable = [s for s in strategies if resolutions[s] is not None]
    if not runnable:
        print("ERROR: no runnable strategies", file=sys.stderr)
        return 3

    print(f"\nSKU      : {args.sku} — {name} ({collection})")
    print(f"Strategies to test ({len(runnable)}):")
    for s in runnable:
        size_kb = resolutions[s].stat().st_size / 1024
        print(f"  {s:<14} → {resolutions[s].name} ({size_kb:.0f} KB)")
    print()

    pipe = ProductionPipeline.from_env()
    results: list[dict] = []

    for s in runnable:
        src = resolutions[s]
        log.info("=" * 70)
        log.info("STRATEGY: %s — source=%s", s, src.name)
        log.info("=" * 70)
        product = {"sku": args.sku, "name": name, "collection": collection}
        t0 = time.monotonic()
        try:
            result = pipe.run_single(product, src, view="front")
            results.append(
                {
                    "strategy": s,
                    "source_image": str(src),
                    "qa_score": result.qa_score,
                    "qa_passed": result.qa_passed,
                    "engine_used": result.engine_used,
                    "attempts": result.attempts,
                    "cost_usd": result.cost_usd,
                    "refinement_applied": result.refinement_applied,
                    "issues": result.issues,
                    "elapsed_seconds": time.monotonic() - t0,
                    "output_path": str(result.output_path) if result.output_path else None,
                }
            )
        except Exception as exc:
            log.error("strategy %s raised %s: %s", s, type(exc).__name__, exc)
            results.append(
                {
                    "strategy": s,
                    "source_image": str(src),
                    "qa_score": None,
                    "error": f"{type(exc).__name__}: {exc}",
                    "elapsed_seconds": time.monotonic() - t0,
                }
            )

    # Save + display
    out = REPO / "tasks" / f"source-strategy-comparison-{args.sku}-{int(time.time())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"sku": args.sku, "name": name, "results": results}, indent=2))

    print()
    print("=" * 70)
    print(f"RESULTS for {args.sku}")
    print("=" * 70)
    print(f"{'STRATEGY':<14} {'QA':>6}  {'PASS':<5} {'REF':<5} {'ENG':<14} {'COST':>8} {'WALL':>6}")
    print("-" * 70)
    for r in results:
        score = "ERROR" if r.get("qa_score") is None else f"{r['qa_score']:.1f}"
        passed = str(r.get("qa_passed", False))
        ref = str(r.get("refinement_applied", False))
        eng = r.get("engine_used", "(none)") or "(none)"
        cost = r.get("cost_usd", 0.0)
        wall = r.get("elapsed_seconds", 0.0)
        print(
            f"{r['strategy']:<14} {score:>6}  {passed:<5} {ref:<5} "
            f"{eng:<14} ${cost:>7.3f} {wall:>5.0f}s"
        )

    valid = [r for r in results if r.get("qa_score") is not None]
    if len(valid) >= 2:
        best = max(valid, key=lambda r: r["qa_score"])
        worst = min(valid, key=lambda r: r["qa_score"])
        print()
        print(f"Best : {best['strategy']:<14} = {best['qa_score']:.1f}")
        print(f"Worst: {worst['strategy']:<14} = {worst['qa_score']:.1f}")
        print(f"Range: {best['qa_score'] - worst['qa_score']:.1f} pts")
        if best["qa_score"] - worst["qa_score"] >= 15:
            print(
                "\n  → SOURCE IMAGE IS A DOMINANT SIGNAL. ADK design must elevate "
                "ResolveSourceTool to first-class."
            )
        elif best["qa_score"] - worst["qa_score"] >= 5:
            print(
                "\n  → Source image moves the needle moderately. ADK should support "
                "configurable source strategies but text prompt is the bigger lever."
            )
        else:
            print(
                "\n  → Source image variation is noise-level. Bottleneck is elsewhere "
                "(generator quality, dossier authoring, or judge calibration)."
            )

    print(f"\nFull results: {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
