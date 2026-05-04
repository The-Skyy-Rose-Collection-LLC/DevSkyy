#!/usr/bin/env python3
"""B2 Compositor real-API smoke test — runs br-001 through all 6 stages.

Cost: ~$0.115 (BRIA $0.005 + Claude Opus $0.015 + IC-Light $0.020 +
FLUX Fill Pro $0.050 + Gemini QA $0.025).

Output:
  renders/output/b2-smoke/br-001-shadow.png       — final composite
  renders/output/b2-smoke/audit-br-001-...json    — per-stage timings + verdict

Usage:
  python scripts/smoke_b2_compositor.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    stream=sys.stderr,
)


def main() -> int:
    from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent

    sku = "br-001"
    collection = "black-rose"
    scene_name = "black-rose-moonlit-courtyard"
    scene_image_path = ROOT / "assets" / "scenes" / collection / f"{scene_name}.png"
    model_image_path = (
        ROOT
        / "skyyrose"
        / "assets"
        / "images"
        / "products"
        / sku
        / f"{sku}-model-front-gemini-upscaled-corrected.jpg"
    )
    output_dir = ROOT / "renders" / "output" / "b2-smoke"

    for label, path in (
        ("scene", scene_image_path),
        ("model", model_image_path),
    ):
        if not path.is_file():
            print(f"✗ {label} image missing: {path}", file=sys.stderr)
            return 1
        print(f"  {label}: {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")

    print(f"  output dir: {output_dir.relative_to(ROOT)}")
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = CompositorAgent()
    started = time.perf_counter()
    print("\n→ running 6-stage compositor pipeline...")
    result = agent.composite(
        sku=sku,
        scene_image_path=str(scene_image_path),
        model_image_path=str(model_image_path),
        collection=collection,
        scene_name=scene_name,
        output_dir=str(output_dir),
    )
    elapsed = time.perf_counter() - started

    print(f"\n--- result ({elapsed:.1f}s) ---")
    print(f"  success:           {result.success}")
    print(f"  stages_completed:  {result.stages_completed}/6")
    print(f"  provider:          {result.provider}")
    print(f"  used_fallback:     {result.used_fallback}")
    if result.fallback_provider:
        print(f"  fallback_provider: {result.fallback_provider}")
    print(f"  qa_status:         {result.qa_status}")
    print(f"  output_path:       {result.output_path}")
    if result.error:
        print(f"  error:             {result.error}")
    if result.audit_log_path:
        print(f"  audit_log:         {result.audit_log_path}")
        try:
            audit = json.loads(Path(result.audit_log_path).read_text())
            print("\n  per-stage timings:")
            for stage_name, stage_data in audit.get("stages", {}).items():
                if isinstance(stage_data, dict):
                    duration = stage_data.get("duration_s", "—")
                    print(f"    {stage_name:12s}: {duration}s")
        except Exception as exc:
            print(f"  (could not parse audit log: {exc})")

    if result.success and Path(result.output_path).is_file():
        size_kb = Path(result.output_path).stat().st_size / 1024
        print(f"\n✓ render written: {result.output_path} ({size_kb:.1f} KB)")
        return 0
    print("\n✗ render did not complete successfully", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
