"""CLI-Anything harness tools: agent-native Blender and GIMP control.

Wraps cli-anything-blender and cli-anything-gimp (installed from ~/Code/CLI-Anything)
via subprocess. Both CLIs use --json for machine-readable output.

Slots into the 3D pipeline post-Tripo/Meshy (cleanup, retopo, bake) and
the imagery pipeline between Stage 3 (composite) and Stage 5 (QA).
"""

import json
import shlex
import subprocess

from pydantic import Field

from mcp_tools.security import secure_tool
from mcp_tools.server import PTC_CALLER, logger, mcp
from mcp_tools.types import BaseAgentInput

_CLI_TIMEOUT = 120  # seconds — long enough for render ops


def _run_cli(binary: str, command: str, project: str | None, dry_run: bool) -> str:
    """Invoke a cli-anything binary and return its JSON output as a string."""
    argv = [binary, "--json"]
    if project:
        argv += ["--project", project]
    if dry_run:
        argv.append("--dry-run")
    argv += shlex.split(command)

    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=_CLI_TIMEOUT,
        )
    except FileNotFoundError:
        return json.dumps(
            {
                "error": f"{binary} not found — run: pip install -e ~/Code/CLI-Anything/{binary.split('-')[-1]}/agent-harness/"
            }
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {_CLI_TIMEOUT}s", "command": command})

    if result.returncode != 0:
        return json.dumps(
            {
                "error": f"Exit {result.returncode}",
                "stderr": result.stderr.strip(),
                "stdout": result.stdout.strip(),
                "command": command,
            }
        )

    raw = result.stdout.strip()
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return raw


# ── Blender ──────────────────────────────────────────────────────────────────


class BlenderEditInput(BaseAgentInput):
    """Input for agent-native Blender scene editing."""

    command: str = Field(
        ...,
        description=(
            "Blender subcommand + args. Groups: object, material, modifier, "
            "render, scene, camera, light, animation, session, preview. "
            "Examples: 'object add --type MESH_CUBE --name Body', "
            "'render now --output /tmp/out.png', 'modifier add --name Decimate --type DECIMATE'"
        ),
        min_length=1,
        max_length=500,
    )
    project: str | None = Field(
        default=None,
        description="Path to .blend-cli.json project file. Omit for ephemeral session.",
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate command without writing to disk.",
    )


@mcp.tool(
    name="devskyy_blender_edit",
    annotations={
        "title": "DevSkyy Blender Editor (CLI-Anything)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {"command": "object add --type MESH_CUBE --name Body", "dry_run": False},
            {"command": "modifier add --name Decimate --ratio 0.3", "dry_run": False},
            {"command": "render now --output /tmp/jersey_render.png --samples 128"},
            {"command": "material create --name RoseGold --color 0.718,0.431,0.475,1"},
            {"command": "scene new --name JerseyCleanup"},
        ],
    },
)
@secure_tool("blender_edit")
async def blender_edit(params: BlenderEditInput) -> str:
    """Control Blender headlessly via the CLI-Anything agent harness.

    Drives Blender's Python API (bpy) through a stable CLI surface — no GUI,
    no manual bpy scripting. Use for post-Tripo/Meshy cleanup: retopology,
    UV bake, decimation, material assignment, and rendering.

    **Command groups:**
    - `object` — add, remove, transform, list mesh objects
    - `modifier` — Decimate, Subdivision, Solidify, Mirror, etc.
    - `material` — create, assign, set PBR properties
    - `render` — configure and trigger renders (output path, samples, engine)
    - `scene` — new/load/save scenes
    - `camera` — add, position, set active
    - `light` — POINT, SUN, SPOT, AREA
    - `animation` — keyframes, timeline
    - `session` — save/load session state
    - `preview` — capture preview bundle

    **Pipeline position:** `services/three_d/` round-table, post-Tripo stage.

    Args:
        params: BlenderEditInput with command string, optional project path, dry_run flag.

    Returns:
        str: JSON output from the CLI harness.
    """
    logger.info("blender_edit: command=%s dry_run=%s", params.command, params.dry_run)
    return _run_cli("cli-anything-blender", params.command, params.project, params.dry_run)


# ── GIMP ─────────────────────────────────────────────────────────────────────


class GimpEditInput(BaseAgentInput):
    """Input for agent-native GIMP image editing."""

    command: str = Field(
        ...,
        description=(
            "GIMP subcommand + args. Groups: layer, filter, canvas, draw, "
            "export, media, project, session. "
            "Examples: 'layer add --name Overlay --mode multiply', "
            "'filter apply --name gaussian-blur --radius 3', "
            "'export save --output /tmp/clean.png --format PNG'"
        ),
        min_length=1,
        max_length=500,
    )
    project: str | None = Field(
        default=None,
        description="Path to .gimp-cli.json project file. Omit for ephemeral session.",
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate command without writing to disk.",
    )


@mcp.tool(
    name="devskyy_gimp_edit",
    annotations={
        "title": "DevSkyy GIMP Editor (CLI-Anything)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "defer_loading": True,
        "allowed_callers": [PTC_CALLER],
        "input_examples": [
            {"command": "media open --path /tmp/render.png"},
            {"command": "filter apply --name gaussian-blur --radius 2"},
            {"command": "layer add --name Mask --mode normal --opacity 80"},
            {"command": "export save --output /tmp/clean.png --format PNG"},
            {"command": "canvas resize --width 2048 --height 2048 --anchor center"},
        ],
    },
)
@secure_tool("gimp_edit")
async def gimp_edit(params: GimpEditInput) -> str:
    """Control GIMP headlessly via the CLI-Anything agent harness.

    Drives GIMP's Script-Fu/Python-Fu through a stable CLI surface. Use for
    deterministic pixel operations that diffusion models handle poorly: background
    artifact removal, exact-color fills, mask refinement, precise cropping.

    **Command groups:**
    - `layer` — add, remove, flatten, set blend mode/opacity
    - `filter` — gaussian-blur, unsharp-mask, curves, levels, color-balance
    - `canvas` — resize, crop, rotate, flatten
    - `draw` — paint, fill, erase (applied at render time)
    - `export` — save as PNG/JPEG/WebP/TIFF with quality options
    - `media` — open image files into the session
    - `project` — save/load GIMP project state
    - `session` — session management

    **Pipeline position:** `services/imagery/` between Stage 3 (composite) and Stage 5 (QA).

    Args:
        params: GimpEditInput with command string, optional project path, dry_run flag.

    Returns:
        str: JSON output from the CLI harness.
    """
    logger.info("gimp_edit: command=%s dry_run=%s", params.command, params.dry_run)
    return _run_cli("cli-anything-gimp", params.command, params.project, params.dry_run)
