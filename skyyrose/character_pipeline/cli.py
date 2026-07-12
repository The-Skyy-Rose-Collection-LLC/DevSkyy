"""WS8 — CLI: `devskyy-character build|verify`.

Orchestrates WS1-WS7 in dependency order, writes the top-level report.json,
and exits nonzero on any PipelineError — including WS6's GateFailure, since a
failed pose gate must block shipping the asset, not just get logged.

Registered as its own `devskyy-character` console script rather than folded
into the existing `devskyy` entry point: that name is already claimed by
`main_enterprise:main`, the FastAPI dev-launcher, which is unrelated to this
CLI's purpose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import _glb_io, clean, convert, landmarks, package, segment, skeleton, verify, weights
from .config import CharacterConfig, load_character_yaml
from .convert import PipelineError


def _run_build(input_path: Path, out_dir: Path, config: CharacterConfig, skip_widget: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = out_dir / "_work"
    qa_dir = out_dir / "qa"
    report: dict = {"input": str(input_path)}

    convert_result = convert.convert_to_glb(input_path, work_dir)
    report["convert"] = convert_result.report

    clean_glb_path = work_dir / "clean.glb"
    clean_result = clean.clean_static(convert_result.glb_path, clean_glb_path, config.target_height)
    report.update(clean_result.report)
    if input_path.suffix.lower() == ".fbx":
        ratio = clean_result.report["output_bytes"] / input_path.stat().st_size
        report["hero_to_input_ratio"] = ratio
        if ratio > 0.20:
            raise PipelineError(
                f"hero GLB is {ratio:.1%} of input FBX size, exceeds the 20% acceptance ceiling"
            )

    import pygltflib

    gltf = pygltflib.GLTF2().load(str(clean_result.glb_path))
    blob = gltf.binary_blob()
    prim = gltf.meshes[0].primitives[0]
    v = _glb_io.read_accessor(gltf, blob, prim.attributes.POSITION).astype(float)
    f = _glb_io.read_accessor(gltf, blob, prim.indices).astype("uint32")

    lm = landmarks.detect_landmarks(v, config)
    skel = skeleton.build_skeleton(lm)

    seg_result = segment.segment_mesh(v, f, skel)
    report["welds_cut"] = seg_result.total_cut
    report["weld_cut_passes"] = seg_result.passes_run
    report["labels"] = {
        "armL": int((seg_result.labels == segment.ARM_L).sum()),
        "armR": int((seg_result.labels == segment.ARM_R).sum()),
        "body": int((seg_result.labels == segment.BODY).sum()),
    }

    weights_result = weights.solve_weights(v, skel, seg_result, config)
    report["dead_verts_rescued"] = weights_result.dead_vert_count
    report["weight_coverage"] = weights_result.coverage

    rigged_path = out_dir / f"{input_path.stem}_rigged.glb"
    weights.write_rigged_glb(
        clean_result.glb_path, v, seg_result.faces, skel, weights_result, rigged_path
    )

    verify_report = verify.verify_character(rigged_path, qa_dir)
    report["gates"] = verify_report.gates
    report["round_trip"] = verify_report.round_trip

    static_path = out_dir / f"{input_path.stem}_static.glb"
    static_path.write_bytes(clean_result.glb_path.read_bytes())
    outputs = {"rigged": rigged_path, "static": static_path}

    if not skip_widget:
        widget_glb_path = out_dir / f"{input_path.stem}_widget.glb"
        package.make_widget_glb(rigged_path, widget_glb_path)
        widget_html_path = out_dir / f"{input_path.stem}_widget.html"
        package.make_widget_html(widget_glb_path, widget_html_path)
        widget_external_path = out_dir / f"{input_path.stem}_widget-external.html"
        package.make_widget_html_external(widget_external_path)
        inspector_path = out_dir / f"{input_path.stem}_inspector.html"
        package.make_inspector_html(rigged_path, inspector_path)
        outputs.update(
            {
                "widget_glb": widget_glb_path,
                "widget_html": widget_html_path,
                "widget_html_external": widget_external_path,
                "inspector_html": inspector_path,
            }
        )

    report["outputs"] = {
        name: {"path": str(p), "bytes": p.stat().st_size} for name, p in outputs.items()
    }
    report["tri_count"] = int(len(seg_result.faces) // 3)
    report["vert_count"] = int(len(v))
    return report


def _build(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    out_dir = Path(args.out)
    report: dict = {"input": str(input_path)}
    report_path = out_dir / f"{input_path.stem}_report.json"

    try:
        # Config load sits inside the guarded region: a missing --config path or
        # malformed yaml must exit through the same clean stderr+report contract
        # as every other failure, not a raw FileNotFoundError traceback.
        config = (
            load_character_yaml(args.config)
            if args.config
            else CharacterConfig(name=input_path.stem)
        )
        report = _run_build(input_path, out_dir, config, args.skip_widget)
    except (PipelineError, FileNotFoundError, yaml.YAMLError) as exc:
        report["error"] = str(exc)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"character build FAILED: {exc}", file=sys.stderr)
        return 1

    report_path.write_text(json.dumps(report, indent=2, default=str))
    print(f"character build OK: {report['outputs']['rigged']['path']}")
    return 0


def _verify(args: argparse.Namespace) -> int:
    qa_dir = Path(args.glb).parent / "qa"
    try:
        report = verify.verify_character(args.glb, qa_dir)
    except verify.GateFailure as exc:
        print(f"verification FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"verification OK: {len(report.gates)} gates passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devskyy-character")
    sub = parser.add_subparsers(dest="command", required=True)

    build_p = sub.add_parser("build", help="run the full character pipeline on an FBX or GLB input")
    build_p.add_argument("input")
    build_p.add_argument("--config", default=None, help="path to character.yaml")
    build_p.add_argument("--out", default="dist")
    build_p.add_argument("--skip-widget", action="store_true")
    build_p.set_defaults(func=_build)

    verify_p = sub.add_parser(
        "verify", help="re-run WS6 verification standalone against a rigged GLB"
    )
    verify_p.add_argument("glb")
    verify_p.set_defaults(func=_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
