"""Render a GLB to a canonical set of angle views via Blender headless.

Coverage is angle-level (Phase 1): an angle is 'verifiable' iff a golden
reference exists for it; otherwise it is 'inferred' and routed to validation +
human. The Blender subprocess writes PNGs; the camera profile comes from
phase0_pose_calibration. Mirrors the temp-runner-script subprocess pattern of
agents.trellis_agent.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

RENDER_ANGLES: tuple[str, ...] = ("front", "back", "left", "right", "detail-1")
_CAMERA_PROFILE = Path(__file__).parent / "camera_profiles" / "skyyrose.json"


def coverage_from_references(
    references: dict[str, Path], angles: tuple[str, ...]
) -> dict[str, bool]:
    """angle -> True if a reference exists (verifiable), else False (inferred)."""
    return {angle: angle in references for angle in angles}


@dataclass(frozen=True)
class RenderViews:
    angle_paths: dict[str, Path]
    coverage: dict[str, bool]

    def verified_angles(self) -> tuple[str, ...]:
        return tuple(a for a, ok in self.coverage.items() if ok)

    def inferred_angles(self) -> tuple[str, ...]:
        return tuple(a for a, ok in self.coverage.items() if not ok)


class BlenderRenderError(RuntimeError):
    """Raised when Blender is unavailable or the render subprocess fails."""


class BlenderRenderer:
    """Headless Blender GLB -> angle PNG renderer."""

    def __init__(
        self, blender_bin: str | None = None, output_dir: Path | str = "renders/fidelity"
    ) -> None:
        self.blender_bin = blender_bin or os.environ.get("BLENDER_BIN") or shutil.which("blender")
        self.output_dir = Path(output_dir)

    def is_available(self) -> bool:
        return bool(self.blender_bin and Path(self.blender_bin).exists())

    def render(self, glb_path: str, references: dict[str, Path]) -> RenderViews:
        if not self.is_available():
            raise BlenderRenderError("blender binary not found (set BLENDER_BIN)")
        run_id = uuid.uuid4().hex[:10]
        out = (self.output_dir / run_id).resolve()
        out.mkdir(parents=True, exist_ok=True)
        script = self._build_script(glb_path=Path(glb_path).resolve(), out_dir=out)
        fd, tmp = tempfile.mkstemp(suffix=".py", prefix="fidelity_render_")
        with os.fdopen(fd, "w") as fh:
            fh.write(script)
        try:
            proc = subprocess.run(
                [self.blender_bin, "-b", "-P", tmp],
                check=False,
                capture_output=True,
                text=True,
                timeout=300,
            )
        finally:
            Path(tmp).unlink(missing_ok=True)
        angle_paths = {a: out / f"{a}.png" for a in RENDER_ANGLES if (out / f"{a}.png").is_file()}
        if proc.returncode != 0 or not angle_paths:
            raise BlenderRenderError(
                f"blender failed (rc={proc.returncode}): {proc.stderr[-1500:]}"
            )
        # Coverage spans the FULL declared angle set, not just angles that
        # rendered: an angle is verified only if it has a reference AND rendered.
        # A render failure therefore surfaces as 'inferred' (-> HUMAN_QUEUE),
        # never silently dropping out of scope.
        has_ref = coverage_from_references(references, RENDER_ANGLES)
        coverage = {a: (has_ref[a] and a in angle_paths) for a in RENDER_ANGLES}
        return RenderViews(angle_paths=angle_paths, coverage=coverage)

    @staticmethod
    def _build_script(glb_path: Path, out_dir: Path) -> str:
        profile = json.loads(_CAMERA_PROFILE.read_text()) if _CAMERA_PROFILE.is_file() else {}
        return f"""import bpy, math, json
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath={str(glb_path)!r})
prof = {json.dumps(profile)}
scene = bpy.context.scene
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True
cam_data = bpy.data.cameras.new("fcam"); cam = bpy.data.objects.new("fcam", cam_data)
scene.collection.objects.link(cam); scene.camera = cam
if prof.get("type") == "ORTHO":
    cam_data.type = "ORTHO"; cam_data.ortho_scale = prof.get("ortho_scale", 1.2)
light_data = bpy.data.lights.new("key", type="SUN"); light = bpy.data.objects.new("key", light_data)
scene.collection.objects.link(light)
RADIUS = 2.5
ANGLES = {{"front": 0, "back": 180, "left": 90, "right": 270, "detail-1": 30}}
for name, deg in ANGLES.items():
    r = math.radians(deg)
    cam.location = (RADIUS*math.sin(r), -RADIUS*math.cos(r), 0.0)
    cam.rotation_euler = (math.radians(90), 0.0, r)
    scene.render.filepath = {str(out_dir)!r} + "/" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("OK")
"""
