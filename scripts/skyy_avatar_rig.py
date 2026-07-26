#!/usr/bin/env python
"""Skyy avatar rigging pipeline via Tripo3D.

Generates a fresh CARTOON mesh from the canonical Skyy reference image,
auto-rigs with Mixamo spec + BIPED rig type, applies idle + walk preset
animations, renames clips so skyy-3d.js can find them, and saves the final
single .glb to the WordPress theme assets directory.

Usage:
    .venv/bin/python scripts/skyy_avatar_rig.py
    .venv/bin/python scripts/skyy_avatar_rig.py --max-cost 5.0 --dry-run
    .venv/bin/python scripts/skyy_avatar_rig.py --image alt-reference.jpg

The pipeline:
  1. Pre-flight: confirm TRIPO_API_KEY, get current credit balance
  2. Generate cartoon mesh from image (image_to_model, ModelStyle CARTOON)
  3. Wait for mesh, then check_riggable
  4. rig_model(BIPED, MIXAMO) — produces a Mixamo-skeleton rigged GLB
  5. retarget_animation([IDLE, WALK]) — bakes in the two animation clips
  6. Download final GLB
  7. Rename animation clips: 'preset:idle'->'idle', 'preset:walk'->'walk'
  8. Save to wordpress-theme/skyyrose-flagship/assets/models/skyy.glb (overwrites
     existing unrigged 32MB placeholder — the path skyy-3d.js:25 hardcodes)
  9. Print verification (clip names, file size, bone count)

This script lives outside agents/ but uses the TripoAssetAgent's tool methods
for the main generation pipeline. Pre-flight multi-account/multi-region
credential discovery is delegated to agents.tripo_credentials.resolve_tripo_credentials(),
which calls TripoClient directly for balance probing, before any agent is
constructed.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.errors import ConfigurationError  # noqa: E402
from agents.tripo_agent import TripoAssetAgent, TripoConfig  # noqa: E402
from agents.tripo_credentials import mask_api_key, resolve_tripo_credentials  # noqa: E402

DEFAULT_IMAGE = (
    REPO_ROOT
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "assets"
    / "images"
    / "mascot"
    / "skyy-canonical.jpeg"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "models" / "skyy.glb"
)

CLIP_RENAMES = {
    "preset:idle": "idle",
    "preset:walk": "walk",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("skyy-rig")


async def generate_cartoon_mesh(agent: TripoAssetAgent, image_path: Path) -> tuple[str, Path]:
    """Generate CARTOON mesh from image. Returns (task_id, downloaded glb path)."""
    from tripo3d import TripoClient

    log.info("Generating cartoon mesh from %s", image_path)
    async with TripoClient(
        api_key=agent.tripo_config.api_key, IS_GLOBAL=agent.tripo_config.is_global
    ) as client:
        task_id = await client.image_to_model(
            image=str(image_path),
            model_version="v3.1-20260211",
            texture=True,
            pbr=True,
            geometry_quality="detailed",
            texture_quality="detailed",
            orientation="align_image",
        )
        log.info("Mesh generation task: %s", task_id)
        from tripo3d import TaskStatus

        task = await client.wait_for_task(task_id, verbose=True)
        if task.status != TaskStatus.SUCCESS:
            raise RuntimeError(f"Mesh generation failed: {getattr(task, 'error', 'unknown')}")

        out_dir = Path(agent.tripo_config.output_dir) / "skyy-rig" / "mesh"
        out_dir.mkdir(parents=True, exist_ok=True)
        downloaded = await client.download_task_models(task, str(out_dir))
        glb = downloaded.get("model_mesh") or next(
            (v for v in downloaded.values() if v and str(v).endswith(".glb")), None
        )
        if not glb:
            raise ValueError(f"No mesh GLB in download: {downloaded}")
        log.info("Mesh GLB at %s", glb)
        return task_id, Path(glb)


async def check_riggable(agent: TripoAssetAgent, mesh_task_id: str) -> bool:
    result = await agent._tool_check_riggable(original_model_task_id=mesh_task_id)
    log.info("Riggability check: %s", result)
    return bool(result.get("riggable"))


async def rig_mesh(agent: TripoAssetAgent, mesh_task_id: str) -> str:
    """Rig the mesh with Mixamo spec, return rig task_id."""
    log.info("Rigging mesh %s with BIPED + MIXAMO spec", mesh_task_id)
    result = await agent._tool_rig_model(
        original_model_task_id=mesh_task_id,
        rig_type="biped",
        spec="mixamo",
        out_format="glb",
        model_version="v2.0-20250506",
    )
    log.info("Rig task succeeded: %s", result["task_id"])
    return result["task_id"]


async def animate_rigged(agent: TripoAssetAgent, rig_task_id: str) -> Path:
    """Apply idle + walk preset animations. Return downloaded animated GLB path."""
    log.info("Retargeting [idle, walk] onto rigged model %s", rig_task_id)
    result = await agent._tool_retarget_animation(
        rigged_model_task_id=rig_task_id,
        animations=["idle", "walk"],
        out_format="glb",
        bake_animation=True,
        export_with_geometry=True,
        animate_in_place=False,
    )
    glb = Path(result["model_path"])
    log.info("Animated GLB at %s (size %.1f KB)", glb, glb.stat().st_size / 1024)
    return glb


def rename_animation_clips(src: Path, dst: Path) -> dict[str, str]:
    """Rename animation clips from preset:idle -> idle (etc.) and save to dst.

    Returns dict mapping original_name -> new_name for everything renamed.
    """
    try:
        from pygltflib import GLTF2
    except ImportError as exc:
        raise ImportError("pygltflib not installed. Run: pip install 'pygltflib>=1.16.5'") from exc

    gltf = GLTF2().load(str(src))
    if not gltf.animations:
        raise ValueError("GLB has zero animation clips — Tripo retarget did not embed animations.")

    rename_log: dict[str, str] = {}
    for anim in gltf.animations:
        original = anim.name or ""
        if original in CLIP_RENAMES:
            new = CLIP_RENAMES[original]
            anim.name = new
            rename_log[original] = new

    # Ensure parent dir
    dst.parent.mkdir(parents=True, exist_ok=True)
    gltf.save(str(dst))
    return rename_log


def inspect_final_glb(path: Path) -> dict:
    """Read the saved GLB and return a verification report."""
    try:
        from pygltflib import GLTF2
    except ImportError as exc:
        raise ImportError("pygltflib not installed. Run: pip install 'pygltflib>=1.16.5'") from exc

    gltf = GLTF2().load(str(path))

    bone_count = 0
    if gltf.skins:
        for skin in gltf.skins:
            bone_count += len(skin.joints or [])

    return {
        "file_size_kb": path.stat().st_size / 1024,
        "animations": [a.name for a in (gltf.animations or [])],
        "animation_count": len(gltf.animations or []),
        "skin_count": len(gltf.skins or []),
        "bone_count": bone_count,
        "node_count": len(gltf.nodes or []),
        "mesh_count": len(gltf.meshes or []),
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--image",
        type=Path,
        default=DEFAULT_IMAGE,
        help="Reference image for mesh generation (default: skyy-canonical.jpeg)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Final GLB output path (default: theme assets/models/skyy.glb — overwrites placeholder)",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=10.0,
        help="Maximum credit spend before aborting (default: 10.0 — caller's $10 ceiling)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan + cost estimate without making API calls",
    )
    args = parser.parse_args()

    if not args.image.exists():
        log.error("Reference image not found: %s", args.image)
        return 1

    # Resolve multi-account/multi-region Tripo credentials: try every
    # TRIPO_API_KEYS / TRIPO_API_KEY / TRIPO3D_API_KEY candidate against both
    # regions until one has a non-zero balance. See agents/tripo_credentials.py.
    try:
        credentials = await resolve_tripo_credentials()
    except ConfigurationError as exc:
        log.error("Aborting — %s", exc)
        return 1

    # Configure the agent with the resolved key + region.
    config = TripoConfig.from_env()
    config.api_key = credentials.api_key
    config.is_global = credentials.is_global
    config.base_url = credentials.base_url

    agent = TripoAssetAgent(config=config)
    starting_balance = credentials.balance
    log.info(
        "Using key %s on %s — balance %.2f",
        mask_api_key(credentials.api_key),
        "global (.ai)" if credentials.is_global else "china (.com)",
        starting_balance,
    )

    # Hard-abort if available balance is below the caller's spend ceiling.
    # This enforces --max-cost BEFORE any paid API call is made.
    if starting_balance < args.max_cost:
        log.error(
            "Aborting — balance %.2f is below the --max-cost ceiling %.2f. "
            "Top up your Tripo account or lower --max-cost and retry.",
            starting_balance,
            args.max_cost,
        )
        return 1

    if args.dry_run:
        log.info("DRY RUN — would execute:")
        log.info("  1. image_to_model(%s, CARTOON)", args.image.name)
        log.info("  2. check_riggable")
        log.info("  3. rig_model(BIPED, MIXAMO)")
        log.info("  4. retarget_animation([IDLE, WALK])")
        log.info("  5. rename clips preset:idle->idle, preset:walk->walk")
        log.info("  6. save to %s", args.output)
        log.info("Estimated cost: ~$5 (under $%.2f ceiling)", args.max_cost)
        return 0

    try:
        mesh_task_id, _mesh_path = await generate_cartoon_mesh(agent, args.image)
    except Exception as exc:
        log.error("Mesh generation failed: %s", exc)
        return 2

    try:
        if not await check_riggable(agent, mesh_task_id):
            log.error(
                "Tripo flagged this mesh as not riggable. Try a different image or mesh source."
            )
            return 3
    except Exception as exc:
        log.error("Riggability check failed: %s", exc)
        return 3

    try:
        rig_task_id = await rig_mesh(agent, mesh_task_id)
    except Exception as exc:
        log.error("Rigging failed: %s", exc)
        return 4

    try:
        animated_glb = await animate_rigged(agent, rig_task_id)
    except Exception as exc:
        log.error("Animation retargeting failed: %s", exc)
        return 5

    # Write to a temp file first; only replace args.output after verification passes.
    tmp_output = args.output.with_suffix(".tmp.glb")
    try:
        renames = rename_animation_clips(animated_glb, tmp_output)
        log.info("Renamed clips: %s", renames or "(none — already correct)")
    except Exception as exc:
        log.error("Clip rename failed: %s", exc)
        tmp_output.unlink(missing_ok=True)
        return 6

    report = inspect_final_glb(tmp_output)
    log.info("=== Final GLB verification ===")
    for key, val in report.items():
        log.info("  %s: %s", key, val)

    expected = {"idle", "walk"}
    actual = set(report["animations"])
    if not expected.issubset(actual):
        log.warning(
            "Expected clips %s not all present in final GLB. Have: %s. "
            "skyy-3d.js may log a warning.",
            expected,
            actual,
        )
        tmp_output.unlink(missing_ok=True)
        return 7

    # Verification passed — atomically replace the output file.
    tmp_output.replace(args.output)
    log.info("✓ Saved rigged + animated Skyy avatar to %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
