#!/usr/bin/env python3
"""TRELLIS.2 runner script — invoked as a subprocess by the CLI harness.

This script is the ONLY place that imports trellis2, torch, or o_voxel.
The parent CLI process never imports these packages directly.

Usage (called by trellis_backend.py):
    python trellis_runner.py generate   < job_record.json  > result_record.json
    python trellis_runner.py probe-gpu                     > gpu_info.json

Protocol:
    generate:
        stdin:  JSON-serialised GenerationRecord (as produced by record.to_dict())
        stdout: JSON-serialised GenerationRecord with status=done/failed
        exit 0 always (errors are reported in the JSON result, not exit code)

    probe-gpu:
        stdout: {"available": bool, "device_count": int, "devices": [...]}
        exit 0 on success, exit 1 if torch import fails
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

# ── Helpers ───────────────────────────────────────────────────────────────────


def _emit(payload: dict) -> None:
    """Write payload as JSON to stdout and flush."""
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _fail_record(record: dict, error: str) -> dict:
    """Return record dict with status=failed and error set."""
    return {
        **record,
        "status": "failed",
        "finished_at": time.time(),
        "error": error,
    }


# ── probe-gpu subcommand ──────────────────────────────────────────────────────


def cmd_probe_gpu() -> None:
    """Check CUDA availability and emit GPU info JSON."""
    try:
        import torch
    except ImportError as exc:
        _emit({"available": False, "device_count": 0, "devices": [], "error": str(exc)})
        sys.exit(1)

    available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if available else 0
    devices = []
    for i in range(device_count):
        try:
            props = torch.cuda.get_device_properties(i)
            devices.append(
                {
                    "index": i,
                    "name": props.name,
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                }
            )
        except Exception:
            devices.append({"index": i, "name": "unknown", "total_memory_gb": 0})

    _emit({"available": available, "device_count": device_count, "devices": devices})


# ── generate subcommand ───────────────────────────────────────────────────────


def cmd_generate() -> None:
    """Read GenerationRecord JSON from stdin, run TRELLIS.2, emit result JSON."""
    raw = sys.stdin.read().strip()
    if not raw:
        _emit({"status": "failed", "error": "runner received empty stdin"})
        return

    try:
        record = json.loads(raw)
    except json.JSONDecodeError as exc:
        _emit({"status": "failed", "error": f"invalid JSON on stdin: {exc}"})
        return

    # Mark running
    record["status"] = "running"
    record["started_at"] = time.time()

    image_path = record.get("image_path", "")
    output_dir = record.get("output_dir", "")
    resolution = record.get("resolution", "high")
    seed = record.get("seed", -1)
    decimation_target = record.get("decimation_target", 1_000_000)
    texture_size = record.get("texture_size", 4096)

    # ── Validate inputs ───────────────────────────────────────────────────────

    if not image_path or not Path(image_path).exists():
        _emit(_fail_record(record, f"image not found: {image_path!r}"))
        return

    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _emit(_fail_record(record, f"cannot create output_dir {output_dir!r}: {exc}"))
        return

    # ── Import trellis2 (only happens inside this subprocess) ─────────────────

    try:
        import torch
        from PIL import Image
        from trellis2.pipelines import Trellis2ImageTo3DPipeline
    except ImportError as exc:
        _emit(
            _fail_record(
                record,
                f"import error — ensure trellis2 and torch are installed "
                f"in this Python environment: {exc}",
            )
        )
        return

    # ── CUDA check ────────────────────────────────────────────────────────────

    if not torch.cuda.is_available():
        _emit(
            _fail_record(
                record,
                "CUDA is not available. TRELLIS.2 requires a CUDA-capable GPU.",
            )
        )
        return

    # ── Resolve seed ──────────────────────────────────────────────────────────

    import random

    if seed < 0:
        seed = random.randint(0, 2**31 - 1)
        record["seed"] = seed

    # ── Sampler params from resolution preset ─────────────────────────────────

    RESOLUTION_PRESETS = {
        "low": {
            "sparse_structure_sampler_params": {
                "steps": 12,
                "cfg_strength": 7.5,
                "rescale": 0.7,
            },
            "shape_slat_sampler_params": {
                "steps": 12,
                "cfg_strength": 3.0,
                "rescale_cfg": 0.7,
                "rescale_t": 0.25,
            },
            "tex_slat_sampler_params": {
                "steps": 12,
                "cfg_strength": 3.0,
                "rescale_cfg": 0.7,
                "rescale_t": 0.25,
            },
        },
        "high": {
            "sparse_structure_sampler_params": {
                "steps": 50,
                "cfg_strength": 7.5,
                "rescale": 0.7,
            },
            "shape_slat_sampler_params": {
                "steps": 50,
                "cfg_strength": 3.0,
                "rescale_cfg": 0.7,
                "rescale_t": 0.25,
            },
            "tex_slat_sampler_params": {
                "steps": 50,
                "cfg_strength": 3.0,
                "rescale_cfg": 0.7,
                "rescale_t": 0.25,
            },
        },
    }

    if resolution not in RESOLUTION_PRESETS:
        resolution = "high"
    params = RESOLUTION_PRESETS[resolution]

    # ── Run pipeline ──────────────────────────────────────────────────────────

    try:
        pipeline = Trellis2ImageTo3DPipeline.from_pretrained("microsoft/TRELLIS.2-4B")
        pipeline.cuda()

        image = Image.open(image_path).convert("RGB")

        outputs = pipeline.run(
            image,
            seed=seed,
            preprocess_image=False,
            sparse_structure_sampler_params=params["sparse_structure_sampler_params"],
            shape_slat_sampler_params=params["shape_slat_sampler_params"],
            tex_slat_sampler_params=params["tex_slat_sampler_params"],
            return_latent=True,
        )

        mesh = outputs[0]

    except Exception as exc:
        _emit(_fail_record(record, f"pipeline.run failed: {traceback.format_exc()}"))
        return

    # ── Export GLB ────────────────────────────────────────────────────────────

    try:
        import o_voxel

        job_id = record.get("job_id", "unknown")
        glb_filename = f"{job_id}.glb"
        glb_path = output_path / glb_filename

        glb = o_voxel.postprocess.to_glb(
            vertices=mesh.vertices,
            faces=mesh.faces,
            attr_volume=mesh.attrs,
            coords=mesh.coords,
            attr_layout=pipeline.pbr_attr_layout,
            voxel_size=mesh.voxel_size,
            aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
            decimation_target=decimation_target,
            texture_size=texture_size,
            remesh=True,
            remesh_band=1,
            remesh_project=0,
            verbose=False,
        )

        glb.export(str(glb_path), extension_webp=True)

    except Exception as exc:
        _emit(_fail_record(record, f"GLB export failed: {traceback.format_exc()}"))
        return

    # ── Emit success ──────────────────────────────────────────────────────────

    result = {
        **record,
        "status": "done",
        "finished_at": time.time(),
        "glb_path": str(glb_path.resolve()),
    }
    _emit(result)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "usage: trellis_runner.py <generate|probe-gpu>",
                    "status": "failed",
                }
            ),
            flush=True,
        )
        sys.exit(1)

    subcommand = sys.argv[1]

    if subcommand == "generate":
        cmd_generate()
    elif subcommand == "probe-gpu":
        cmd_probe_gpu()
    else:
        print(
            json.dumps(
                {
                    "error": f"unknown subcommand: {subcommand!r}",
                    "status": "failed",
                }
            ),
            flush=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
