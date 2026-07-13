#!/usr/bin/env python3
"""Prepare tests/character_pipeline/fixtures/love_hurts_girl_static.glb from the
real Love Hurts Girl Blender export, and observe real pipeline numbers on real
geometry for the first time (every existing test uses a small synthetic mesh).

Usage:
    python scripts/prepare_character_pipeline_fixture.py
    python scripts/prepare_character_pipeline_fixture.py --source path/to/other.glb

Rerunnable — safe to re-run after any pipeline change to refresh the fixture
and re-observe real numbers.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pygltflib import GLTF2

from skyyrose.character_pipeline import _glb_io, clean, segment, skeleton, weights
from skyyrose.character_pipeline.config import load_character_yaml
from skyyrose.character_pipeline.landmarks import detect_landmarks
from skyyrose.character_pipeline.verify import verify_character

DEFAULT_SOURCE = "renders/3d/girl-love-hurts/love-hurts-girl-rig.glb"
DEFAULT_OUT = "tests/character_pipeline/fixtures/love_hurts_girl_static.glb"
DEFAULT_CONFIG = "skyyrose/character_pipeline/characters/love_hurts_girl.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = load_character_yaml(args.config) if args.config else None

    source = Path(args.source)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== source: {source} ({source.stat().st_size / 1e6:.2f}MB) ===")
    src_gltf = GLTF2().load(str(source))
    print(f"mesh count: {len(src_gltf.meshes)}")
    for i, mesh in enumerate(src_gltf.meshes):
        print(f"  mesh[{i}] primitive count: {len(mesh.primitives)}")
    if len(src_gltf.meshes) > 1 or len(src_gltf.meshes[0].primitives) > 1:
        print(
            "!!! WARNING: multiple meshes/primitives detected. clean_static() only reads "
            "meshes[0].primitives[0] — geometry beyond that WILL be silently dropped. "
            "Stopping before writing a possibly-incomplete fixture."
        )
        return 1

    print("\n=== WS2: clean_static ===")
    clean_result = clean.clean_static(source, out_path)
    for k, v in clean_result.report.items():
        print(f"  {k}: {v}")

    print(
        "\n=== WS3-6: landmarks -> skeleton -> segment -> weights -> verify (observability pass) ==="
    )
    gltf = GLTF2().load(str(out_path))
    blob = gltf.binary_blob()
    prim = gltf.meshes[0].primitives[0]
    v = _glb_io.read_accessor(gltf, blob, prim.attributes.POSITION).astype(float)
    f = _glb_io.read_accessor(gltf, blob, prim.indices).astype("uint32")
    print(f"  vert_count: {len(v)}  tri_count: {len(f) // 3}")

    lm = detect_landmarks(v, config)
    print(
        f"  landmarks (config={args.config or 'none, pure auto-detect'}): "
        f"height={lm.height:.3f} crotch_y={lm.crotch_y:.3f} neck_y={lm.neck_y:.3f}"
    )

    skel = skeleton.build_skeleton(lm)
    seg_result = segment.segment_mesh(v, f, skel)
    print(
        f"  segment: converged={seg_result.converged} total_cut={seg_result.total_cut} passes_run={seg_result.passes_run}"
    )
    print(
        f"  labels: armL={int((seg_result.labels == segment.ARM_L).sum())} "
        f"armR={int((seg_result.labels == segment.ARM_R).sum())} "
        f"body={int((seg_result.labels == segment.BODY).sum())}"
    )

    weights_result = weights.solve_weights(v, skel, seg_result, config)
    print(
        f"  weights: dead_vert_count={weights_result.dead_vert_count} coverage_joints={len(weights_result.coverage)}"
    )

    rigged_path = out_path.parent / "_prep_rigged_scratch.glb"
    weights.write_rigged_glb(out_path, v, seg_result.faces, skel, weights_result, rigged_path)

    qa_dir = out_path.parent / "_prep_qa_scratch"
    t0 = time.monotonic()
    try:
        report = verify_character(rigged_path, qa_dir)
        elapsed = time.monotonic() - t0
        print(f"  verify_character: ALL {len(report.gates)} gates PASSED in {elapsed:.2f}s")
        for g in report.gates:
            print(
                f"    {g['metric']}: {g['value']:.5f} ({g['op']} {g['threshold']}) pass={g['pass']}"
            )
    except Exception as exc:  # noqa: BLE001 — observability pass, report whatever happens
        elapsed = time.monotonic() - t0
        print(f"  verify_character: FAILED after {elapsed:.2f}s — {exc}")

    rigged_path.unlink(missing_ok=True)
    if qa_dir.exists():
        for p in qa_dir.iterdir():
            p.unlink()
        qa_dir.rmdir()

    print(f"\n=== fixture written: {out_path} ({out_path.stat().st_size / 1e6:.2f}MB) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
