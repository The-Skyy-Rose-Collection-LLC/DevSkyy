#!/usr/bin/env python
"""Merge two Mixamo-exported GLBs (idle + walk) into the final skyy.glb.

After Tripo's BIPED rigger refused the chibi mascot (bug-096), the Skyy avatar
is rigged via Mixamo (free, handles stylized characters). Mixamo exports each
animation as its own .glb. This script merges them into one file with both
clips ('idle', 'walk') so skyy-3d.js:25 can load a single asset.

Why merge by node-name lookup, not node-index lookup:
  Mixamo's "Download with Skin" produces self-contained GLBs. The skeleton
  bone hierarchy is identical across animations of the same character (the
  rig was built once during upload), so bone NAMES are reliable join keys.
  Node INDICES can drift between exports if Mixamo re-orders during export,
  so we look up `channel.target.node` by name in the source file, then map
  to the matching node by name in the destination file.

Usage:
    .venv/bin/python scripts/skyy_mixamo_merge.py \\
        --idle ~/Downloads/Idle.glb \\
        --walk ~/Downloads/Walking.glb

    # Optional override of output path
    .venv/bin/python scripts/skyy_mixamo_merge.py \\
        --idle Idle.glb --walk Walking.glb \\
        --out wordpress-theme/skyyrose-flagship/assets/models/skyy.glb
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from pygltflib import GLTF2, Animation, AnimationChannel, AnimationSampler  # noqa: E402

DEFAULT_OUTPUT = (
    REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "models" / "skyy.glb"
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("mixamo-merge")


def _node_name_map(gltf: GLTF2) -> dict[str, int]:
    """Build {node_name: node_index} map. Names with no value get a synthetic key."""
    out: dict[str, int] = {}
    for idx, node in enumerate(gltf.nodes or []):
        name = node.name or f"__unnamed_{idx}"
        out[name] = idx
    return out


def _import_animation_clip(
    dst: GLTF2,
    dst_buffer_bytes: bytearray,
    src: GLTF2,
    src_buffer_bytes: bytes,
    src_anim: Animation,
    new_clip_name: str,
) -> Animation:
    """Copy one animation clip from src into dst.

    Re-indexes every reference: bufferView → accessor → sampler → channel.
    Maps channel.target.node from src node-index → dst node-index by NAME.
    Appends src's animation buffer bytes to dst's buffer.
    Returns the newly built Animation object (already appended via caller).
    """
    src_node_names = {idx: (n.name or f"__unnamed_{idx}") for idx, n in enumerate(src.nodes or [])}
    dst_name_to_idx = _node_name_map(dst)

    # Pre-compute which src bufferViews/accessors/samplers we need.
    used_sampler_idxs: set[int] = set()
    for ch in src_anim.channels or []:
        used_sampler_idxs.add(ch.sampler)
    used_accessor_idxs: set[int] = set()
    for s_idx in used_sampler_idxs:
        s = src_anim.samplers[s_idx]
        used_accessor_idxs.add(s.input)
        used_accessor_idxs.add(s.output)
    used_bufferview_idxs: set[int] = set()
    for a_idx in used_accessor_idxs:
        bv_idx = src.accessors[a_idx].bufferView
        if bv_idx is not None:
            used_bufferview_idxs.add(bv_idx)

    # Map src indices → new dst indices.
    bv_remap: dict[int, int] = {}
    for src_bv_idx in sorted(used_bufferview_idxs):
        bv = src.bufferViews[src_bv_idx]
        # Slice the bytes from src buffer, append to dst buffer.
        offset = bv.byteOffset or 0
        length = bv.byteLength
        chunk = bytes(src_buffer_bytes[offset : offset + length])
        new_offset = len(dst_buffer_bytes)
        dst_buffer_bytes.extend(chunk)
        # Pad to 4-byte boundary (glTF spec requirement for buffer views).
        while len(dst_buffer_bytes) % 4 != 0:
            dst_buffer_bytes.append(0)

        # Build new bufferView pointing at dst's only buffer (index 0).
        from pygltflib import BufferView

        new_bv = BufferView(
            buffer=0,
            byteOffset=new_offset,
            byteLength=length,
            byteStride=bv.byteStride,
            target=bv.target,
            name=bv.name,
        )
        if dst.bufferViews is None:
            dst.bufferViews = []
        dst.bufferViews.append(new_bv)
        bv_remap[src_bv_idx] = len(dst.bufferViews) - 1

    accessor_remap: dict[int, int] = {}
    for src_a_idx in sorted(used_accessor_idxs):
        a = src.accessors[src_a_idx]
        from pygltflib import Accessor

        new_a = Accessor(
            bufferView=bv_remap[a.bufferView] if a.bufferView is not None else None,
            byteOffset=a.byteOffset,
            componentType=a.componentType,
            normalized=a.normalized,
            count=a.count,
            type=a.type,
            max=a.max,
            min=a.min,
            name=a.name,
        )
        if dst.accessors is None:
            dst.accessors = []
        dst.accessors.append(new_a)
        accessor_remap[src_a_idx] = len(dst.accessors) - 1

    # Rebuild samplers with new accessor refs.
    new_samplers: list[AnimationSampler] = []
    sampler_remap: dict[int, int] = {}
    for src_s_idx, s in enumerate(src_anim.samplers or []):
        if src_s_idx not in used_sampler_idxs:
            continue
        new_samplers.append(
            AnimationSampler(
                input=accessor_remap[s.input],
                output=accessor_remap[s.output],
                interpolation=s.interpolation,
            )
        )
        sampler_remap[src_s_idx] = len(new_samplers) - 1

    # Rebuild channels with new sampler refs and node-name mapping.
    new_channels: list[AnimationChannel] = []
    for ch in src_anim.channels or []:
        src_target_node_idx = ch.target.node
        if src_target_node_idx is None:
            log.warning("Channel has no target node — skipping (unusual for Mixamo)")
            continue
        src_target_name = src_node_names.get(src_target_node_idx)
        if src_target_name is None or src_target_name not in dst_name_to_idx:
            log.warning(
                "Source bone '%s' not found in destination skeleton — channel dropped",
                src_target_name,
            )
            continue
        from pygltflib import AnimationChannelTarget

        new_channels.append(
            AnimationChannel(
                sampler=sampler_remap[ch.sampler],
                target=AnimationChannelTarget(
                    node=dst_name_to_idx[src_target_name], path=ch.target.path
                ),
            )
        )

    return Animation(name=new_clip_name, samplers=new_samplers, channels=new_channels)


def merge(idle_path: Path, walk_path: Path, out_path: Path) -> dict:
    """Merge idle + walk Mixamo GLBs into out_path. Return a verification report."""
    log.info("Loading idle: %s", idle_path)
    base = GLTF2().load(str(idle_path))
    log.info("Loading walk: %s", walk_path)
    walk = GLTF2().load(str(walk_path))

    # Sanity: both files must have a skin and at least one animation.
    if not base.skins or not base.animations:
        raise ValueError(
            f"Idle GLB at {idle_path} is missing skin or animation. "
            "Re-download from Mixamo with 'Skin: With Skin' and the animation selected."
        )
    if not walk.animations:
        raise ValueError(
            f"Walk GLB at {walk_path} has no animations. Re-download with the walk clip selected."
        )

    # Get base buffer bytes (the only buffer in a Mixamo GLB).
    if not base.buffers:
        raise ValueError(f"Idle GLB at {idle_path} has no buffers — corrupt file?")
    base_buffer_bytes = bytearray(base.binary_blob() or b"")
    if not base_buffer_bytes:
        raise ValueError(f"Idle GLB at {idle_path} has empty buffer — corrupt file?")

    walk_buffer_bytes = walk.binary_blob() or b""
    if not walk_buffer_bytes:
        raise ValueError(f"Walk GLB at {walk_path} has empty buffer — corrupt file?")

    # Rename base's existing animation to 'idle'.
    base.animations[0].name = "idle"
    log.info("Renamed base animation -> 'idle'")

    # Import walk animation as 'walk'.
    walk_clip = _import_animation_clip(
        dst=base,
        dst_buffer_bytes=base_buffer_bytes,
        src=walk,
        src_buffer_bytes=walk_buffer_bytes,
        src_anim=walk.animations[0],
        new_clip_name="walk",
    )
    base.animations.append(walk_clip)
    log.info(
        "Imported walk animation -> 'walk' (%d channels, %d samplers)",
        len(walk_clip.channels),
        len(walk_clip.samplers),
    )

    # Update base buffer to reflect new bytes.
    base.buffers[0].byteLength = len(base_buffer_bytes)
    base.set_binary_blob(bytes(base_buffer_bytes))

    # Save.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(str(out_path))

    # Verify what we wrote.
    final = GLTF2().load(str(out_path))
    bone_count = sum(len(s.joints or []) for s in (final.skins or []))
    return {
        "out_path": str(out_path),
        "file_size_mb": out_path.stat().st_size / 1024 / 1024,
        "animations": [a.name for a in (final.animations or [])],
        "animation_count": len(final.animations or []),
        "skin_count": len(final.skins or []),
        "bone_count": bone_count,
        "node_count": len(final.nodes or []),
        "mesh_count": len(final.meshes or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idle", type=Path, required=True, help="Mixamo idle .glb download")
    parser.add_argument("--walk", type=Path, required=True, help="Mixamo walking .glb download")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()

    for label, p in (("idle", args.idle), ("walk", args.walk)):
        if not p.exists():
            log.error("%s GLB not found: %s", label, p)
            return 1

    report = merge(args.idle, args.walk, args.out)
    log.info("=== Final GLB verification ===")
    for k, v in report.items():
        log.info("  %s: %s", k, v)

    expected = {"idle", "walk"}
    actual = set(report["animations"])
    if not expected.issubset(actual):
        log.error("Missing required clips. Have: %s. Expected: %s", actual, expected)
        return 2

    if report["bone_count"] == 0:
        log.error("Final GLB has 0 bones — Mixamo upload should have produced a skeleton")
        return 3

    log.info("✓ Saved rigged + dual-animation Skyy avatar to %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
