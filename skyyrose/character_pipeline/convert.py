"""WS1 — FBX/GLB ingest into a clean working GLB.

FBX input runs through the vendored FBX2glTF binary (pinned v0.9.7, selected by
host platform — darwin has only an x64 release upstream, which runs fine under
Rosetta 2 on Apple Silicon). GLB input passes straight through the same
acceptance checks. Pre-flight scanning happens on the raw FBX bytes BEFORE
conversion: a pre-rigged or textureless FBX is a v1 Non-Goal (spec section 6),
so rejecting it early saves a wasted conversion round trip.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pygltflib import GLTF2

from . import _glb_io

_VENDOR_DIR = Path(__file__).parent / "vendor"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PipelineError(RuntimeError):
    """Raised when an acceptance gate fails; the CLI turns this into a nonzero exit."""


@dataclass
class ConvertResult:
    glb_path: Path
    texture_paths: list[Path] = field(default_factory=list)
    report: dict = field(default_factory=dict)


def _fbx2gltf_binary() -> Path:
    system = platform.system()
    if system == "Linux":
        name = "FBX2glTF-linux-x64"
    elif system == "Darwin":
        name = (
            "FBX2glTF-darwin-x64"  # only x64 release exists upstream; runs under Rosetta 2 on arm64
        )
    else:
        raise PipelineError(f"no vendored FBX2glTF binary for platform {system!r}")
    binary = _VENDOR_DIR / name
    if not binary.exists():
        raise PipelineError(
            f"FBX2glTF binary missing at {binary}. Run "
            "scripts/setup_character_pipeline_vendor.sh to fetch vendored assets."
        )
    return binary


def _scan_fbx_preflight(fbx_bytes: bytes) -> dict:
    """Cheap byte-count scan of the raw FBX BEFORE conversion.

    LimbNode/Deformer/AnimationCurveNode markers indicate an already-rigged
    FBX; PNG signature count of zero means no embedded textures. Both are hard
    rejections — pre-rigged merging and textureless input are v1 Non-Goals.
    """
    limb_nodes = fbx_bytes.count(b"LimbNode")
    deformers = fbx_bytes.count(b"Deformer")
    anim_curves = fbx_bytes.count(b"AnimationCurveNode")
    png_count = fbx_bytes.count(_PNG_SIGNATURE)
    if png_count == 0:
        raise PipelineError("NO_EMBEDDED_TEXTURES: input FBX has zero embedded PNG textures")
    pre_rigged = limb_nodes > 0 or deformers > 0 or anim_curves > 0
    if pre_rigged:
        raise PipelineError(
            "PRE_RIGGED_INPUT: input FBX already contains "
            f"{limb_nodes} LimbNode / {deformers} Deformer / {anim_curves} AnimationCurveNode "
            "markers — merging with an existing rig is a v1 non-goal (see spec section 6)"
        )
    return {
        "limb_node_count": limb_nodes,
        "deformer_count": deformers,
        "anim_curve_count": anim_curves,
        "png_count": png_count,
    }


def _validate_glb(glb_path: Path) -> GLTF2:
    gltf = GLTF2().load(str(glb_path))
    if not gltf.meshes or not gltf.meshes[0].primitives:
        raise PipelineError(f"{glb_path} has no mesh primitives")
    attrs = gltf.meshes[0].primitives[0].attributes
    for required in ("POSITION", "NORMAL", "TEXCOORD_0"):
        if getattr(attrs, required) is None:
            raise PipelineError(f"{glb_path} primitive missing required attribute {required}")
    if not gltf.images:
        raise PipelineError(f"{glb_path} has zero embedded images")
    return gltf


def _extract_textures(gltf: GLTF2, blob: bytes, work_dir: Path) -> list[Path]:
    tex_dir = work_dir / "textures"
    tex_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, image in enumerate(gltf.images):
        if image.bufferView is None:
            continue
        data = _glb_io.image_bytes(gltf, blob, i)
        ext = "jpg" if image.mimeType == "image/jpeg" else "png"
        out = tex_dir / f"{image.name or f'texture_{i}'}.{ext}"
        out.write_bytes(data)
        paths.append(out)
    return paths


def convert_to_glb(input_path: str | Path, work_dir: str | Path) -> ConvertResult:
    """WS1: converts FBX (via vendored FBX2glTF) or passes through GLB, then
    runs the acceptance gate (>=1 mesh primitive with POSITION/NORMAL/TEXCOORD_0,
    >=1 embedded image) and extracts textures to `work_dir/textures/`.
    """
    input_path = Path(input_path)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"input": str(input_path)}

    if input_path.suffix.lower() == ".fbx":
        report["preflight"] = _scan_fbx_preflight(input_path.read_bytes())
        binary = _fbx2gltf_binary()
        out_stem = work_dir / "converted"
        try:
            subprocess.run(
                [
                    str(binary),
                    "-b",
                    "--pbr-metallic-roughness",
                    "-i",
                    str(input_path),
                    "-o",
                    str(out_stem),
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            # capture_output swallows stderr into the exception, and
            # CalledProcessError's own message shows only returncode+argv —
            # surface the converter's actual complaint or the failure is opaque.
            stderr = (exc.stderr or b"").decode(errors="replace").strip()
            raise PipelineError(
                f"FBX2glTF failed with exit code {exc.returncode}: {stderr[-2000:] or '(no stderr)'}"
            ) from exc
        glb_path = out_stem.with_suffix(".glb")
        if not glb_path.exists():
            raise PipelineError(f"FBX2glTF did not produce {glb_path}")
    elif input_path.suffix.lower() == ".glb":
        glb_path = input_path
        report["preflight"] = {"skipped": "glb passthrough"}
    else:
        raise PipelineError(f"unsupported input extension: {input_path.suffix}")

    gltf = _validate_glb(glb_path)
    blob = gltf.binary_blob()
    textures = _extract_textures(gltf, blob, work_dir)
    report["mesh_count"] = len(gltf.meshes)
    report["image_count"] = len(gltf.images)
    report["texture_paths"] = [str(p) for p in textures]

    return ConvertResult(glb_path=glb_path, texture_paths=textures, report=report)
