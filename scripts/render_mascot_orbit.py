"""Render a rigged mascot GLB from N orbit angles for identity-reference use.

Purpose: produce a consistent-lighting, multi-angle still set of the SkyyRose
mascot. The set serves as (1) a locked Higgsfield ``@mascot`` Element reference
set fed via Seedance's ``image_references`` role, (2) ArcFace/QC identity frames,
and (3) Soul-ID training data IF the mascot ever moves to ``soul_cinema_studio``
(Seedance 2.0 has no Soul slot — verified against the live API 2026-07-23).

Reuses the lighting + bounding-box camera-fit approach from
``scripts/render_professional.py`` and adds an azimuth/elevation orbit loop.

Headless usage:
    blender -b -P scripts/render_mascot_orbit.py -- <input.glb> <out_dir> [count]

Emits one ``VERIFIED_RENDER_SUCCESS: <path>`` line per frame written.
"""

from __future__ import annotations

import math
import os
import sys

import bpy
import mathutils

# 20 angles: 12 mid-elevation azimuths (30 deg apart) + 4 high + 4 low.
# Face-forward is unknown a priori, so a full 360 sweep guarantees coverage;
# a contact-sheet vision pass afterward picks the front-facing frames.
_MID_ELEV = math.radians(8)
_HIGH_ELEV = math.radians(28)
_LOW_ELEV = math.radians(-12)
_RES = 1024  # >= 960px Soul/Element floor


def setup_render_settings(res: int = _RES) -> None:
    scene = bpy.context.scene
    # Blender 5.x: "BLENDER_EEVEE" IS EEVEE-Next (the legacy string was dropped).
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    # Solid, consistent neutral background — reference sets want a stable,
    # non-transparent backdrop (transparent frames confuse Element/Soul
    # ingestion and ArcFace alike).
    scene.render.film_transparent = False
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.14, 0.14, 0.15, 1.0)  # near-neutral charcoal
    bg.inputs[1].default_value = 1.0


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_glb(filepath: str) -> list:
    bpy.ops.import_scene.gltf(filepath=filepath)
    return [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]


def setup_3point_lighting(center: mathutils.Vector, radius: float) -> None:
    r = max(radius, 0.5)
    specs = [
        ("KEY", (5, -5, 10), 1000),
        ("FILL", (-5, -5, 5), 400),
        ("RIM", (0, 5, 5), 600),
    ]
    for _, dir_vec, energy in specs:
        loc = center + mathutils.Vector(dir_vec).normalized() * r * 4
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.active_object
        light.data.energy = energy * (r * r)  # scale energy to model size
        light.data.size = r * 2


def scene_bounds(targets: list) -> tuple[mathutils.Vector, float]:
    coords = []
    for obj in targets:
        for v in obj.bound_box:
            coords.append(obj.matrix_world @ mathutils.Vector(v))
    if not coords:
        raise SystemExit("ERROR: no mesh geometry found in GLB")
    center = sum(coords, mathutils.Vector((0, 0, 0))) / len(coords)
    radius = max((v - center).length for v in coords)
    return center, radius


def place_camera(
    cam, center: mathutils.Vector, radius: float, azimuth: float, elevation: float
) -> None:
    dist = radius * 3.2
    horiz = math.cos(elevation) * dist
    x = center.x + math.sin(azimuth) * horiz
    y = center.y - math.cos(azimuth) * horiz
    z = center.z + math.sin(elevation) * dist
    cam.location = mathutils.Vector((x, y, z))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def build_angle_list(count: int) -> list[tuple[str, float, float]]:
    angles: list[tuple[str, float, float]] = []
    mid_n = max(count - 8, 4)
    for i in range(mid_n):
        az = 2 * math.pi * i / mid_n
        angles.append((f"mid{i:02d}", az, _MID_ELEV))
    for i in range(4):
        az = 2 * math.pi * i / 4 + math.radians(45)
        angles.append((f"high{i:02d}", az, _HIGH_ELEV))
    for i in range(4):
        az = 2 * math.pi * i / 4
        angles.append((f"low{i:02d}", az, _LOW_ELEV))
    return angles[:count]


def main() -> None:
    argv = sys.argv
    if "--" not in argv:
        raise SystemExit(
            "usage: blender -b -P render_mascot_orbit.py -- <in.glb> <out_dir> [count]"
        )
    args = argv[argv.index("--") + 1 :]
    input_path = args[0]
    out_dir = args[1]
    count = int(args[2]) if len(args) > 2 else 20
    os.makedirs(out_dir, exist_ok=True)

    clear_scene()
    setup_render_settings()
    meshes = import_glb(input_path)
    center, radius = scene_bounds(meshes)
    setup_3point_lighting(center, radius)

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam

    for idx, (label, az, elev) in enumerate(build_angle_list(count)):
        place_camera(cam, center, radius, az, elev)
        out_path = os.path.join(out_dir, f"mascot-{idx:02d}-{label}.png")
        bpy.context.scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"VERIFIED_RENDER_SUCCESS: {out_path}")


if __name__ == "__main__":
    main()
