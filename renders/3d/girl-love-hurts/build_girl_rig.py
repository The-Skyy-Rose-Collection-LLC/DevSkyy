"""
Build a 24-bone skeleton for the Love Hurts girl mesh, structurally cloned
from wordpress-theme/skyyrose-flagship/assets/models/skyy.glb (same 24 bone
names / parent-child hierarchy, no finger chain -- Hand is the end effector),
but positioned at the girl mesh's OWN geometry landmarks (not the mascot's
bind-pose numbers -- her proportions differ and must be read off her actual
vertex data).

Run headless:
    blender --background --python build_girl_rig.py

Outputs:
    renders/3d/girl-love-hurts/love-hurts-girl-rig.blend
    renders/3d/girl-love-hurts/love-hurts-girl-rig.glb
    renders/3d/girl-love-hurts/verify_front.png
    renders/3d/girl-love-hurts/verify_side.png

Landmark method (see session notes for full derivation):
  The girl source mesh (Meshy AI, "Love Hurts" Kids Capsule character) is a
  single 52,133-vert / 0-skin / 0-anim mesh in a relaxed standing pose --
  NOT a T-pose. Arms hang at the sides inside long jacket sleeves, so a
  naive per-height X-gap cluster count is noisy (clothing folds, hair
  strands). The landmarks below were derived from real signals in the
  vertex cloud, confirmed against an orthographic front+side render read
  with vision (see PHASE 0 notes):
    - crotch/hip height  : the Z where the center gap (min |x| per Z-band)
                            closes from ~0.07m down to ~0m (measured ~33%
                            of total mesh height from the floor)
    - ankle height        : local MINIMUM leg cross-section width (thinner
                            than both the calf above and the shoe below),
                            measured ~8.5% of total height
    - shoulder height     : the Z band where point density jumps sharply
                            (jacket collar/shoulder seam), ~70% of height
    - wrist height        : the Z band just above the hip where a bump
                            beyond the leg's own baseline width appears on
                            each side (hand emerging from sleeve), ~33%
    - elbow height        : midpoint between shoulder and wrist bands
  For each height band, LEFT/RIGHT side X,Y at limb heights use the
  extreme-X vertex on that side of that band (the arm/leg surface point);
  spine/head/neck use the band centroid (X clamped to the centerline).
  This is deterministic and re-derived from the mesh every run -- no
  hardcoded numbers copied from skyy.glb (whose own head/tail values are
  cm-scale and belong to the mascot's proportions, not hers).

Root scale: the armature is built FRESH with edit bones placed directly in
girl-mesh world-meters -- there is no cm-scale root to "correct". Object
scale is asserted (1,1,1) and scene unit scale is fixed at 1.0 before
export, then re-verified by parsing the exported GLB JSON directly.
"""

import json
import math
import os
import struct

import bpy
from mathutils import Vector

GIRL_SOURCE = "/Users/theceo/Downloads/Meshy_AI_Love_Hurts_Girl_High__0709230707_texture.glb"
OUT_DIR = (
    "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/renders/3d/girl-love-hurts"
)
BLEND_OUT = os.path.join(OUT_DIR, "love-hurts-girl-rig.blend")
GLB_OUT = os.path.join(OUT_DIR, "love-hurts-girl-rig.glb")
FRONT_PNG = os.path.join(OUT_DIR, "verify_front.png")
SIDE_PNG = os.path.join(OUT_DIR, "verify_side.png")

# 24-bone hierarchy cloned from skyy.glb (name -> parent name or None).
# Verified via bpy dump of skyy.glb this session: 24 bones, this exact
# parent map, Mixamo-style, no finger chain (Hand is the leaf end effector).
HIERARCHY = [
    ("Hips", None),
    ("LeftUpLeg", "Hips"),
    ("LeftLeg", "LeftUpLeg"),
    ("LeftFoot", "LeftLeg"),
    ("LeftToeBase", "LeftFoot"),
    ("RightUpLeg", "Hips"),
    ("RightLeg", "RightUpLeg"),
    ("RightFoot", "RightLeg"),
    ("RightToeBase", "RightFoot"),
    ("Spine02", "Hips"),
    ("Spine01", "Spine02"),
    ("Spine", "Spine01"),
    ("LeftShoulder", "Spine"),
    ("LeftArm", "LeftShoulder"),
    ("LeftForeArm", "LeftArm"),
    ("LeftHand", "LeftForeArm"),
    ("RightShoulder", "Spine"),
    ("RightArm", "RightShoulder"),
    ("RightForeArm", "RightArm"),
    ("RightHand", "RightForeArm"),
    ("neck", "Spine"),
    ("Head", "neck"),
    ("head_end", "Head"),
    ("headfront", "Head"),
]
assert len(HIERARCHY) == 24

# Primary tail-continuation per branch bone (the child whose head the
# parent's tail points at); other children are non-connected branches.
PRIMARY_CHILD = {
    "Hips": "Spine02",
    "Spine": "neck",
    "Head": "head_end",
}


def import_girl_mesh(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    mesh_obj = None
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            mesh_obj = obj
            break
    if mesh_obj is None:
        raise RuntimeError("No mesh object found in imported girl GLB")
    return mesh_obj


def world_coords(mesh_obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = mesh_obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    mat = mesh_obj.matrix_world
    coords = [tuple(mat @ v.co) for v in mesh.vertices]
    obj_eval.to_mesh_clear()
    return coords


def band(coords, zmin, height, frac0, frac1):
    z0 = zmin + frac0 * height
    z1 = zmin + frac1 * height
    return [c for c in coords if z0 <= c[2] < z1]


def centroid(pts):
    n = len(pts)
    if n == 0:
        raise RuntimeError("empty band while computing landmark centroid")
    return (
        sum(p[0] for p in pts) / n,
        sum(p[1] for p in pts) / n,
        sum(p[2] for p in pts) / n,
    )


def split_lr(pts):
    left = [p for p in pts if p[0] >= 0]  # +X = Left, matches skyy.glb sign convention
    right = [p for p in pts if p[0] < 0]
    return left, right


def extreme_left(pts):
    return max(pts, key=lambda p: p[0])


def extreme_right(pts):
    return min(pts, key=lambda p: p[0])


def frontmost(pts):
    return min(pts, key=lambda p: p[1])  # front = -Y (confirmed by front-camera render)


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def compute_landmarks(coords):
    zmin = min(c[2] for c in coords)
    zmax = max(c[2] for c in coords)
    height = zmax - zmin
    if height <= 0:
        raise RuntimeError("degenerate mesh height")

    L = {}

    # --- head / neck / spine centerline (band centroid, X forced to 0) ---
    head_end_c = centroid(band(coords, zmin, height, 0.97, 1.001))
    L["head_end"] = (head_end_c[0], head_end_c[1], head_end_c[2])

    head_c = centroid(band(coords, zmin, height, 0.775, 0.825))
    L["Head"] = (0.0, head_c[1], head_c[2])

    headfront_pt = frontmost(band(coords, zmin, height, 0.78, 0.83))
    L["headfront"] = headfront_pt

    neck_c = centroid(band(coords, zmin, height, 0.705, 0.735))
    L["neck"] = (0.0, neck_c[1], neck_c[2])

    spine_c = centroid(band(coords, zmin, height, 0.63, 0.69))
    L["Spine"] = (0.0, spine_c[1], spine_c[2])

    spine01_c = centroid(band(coords, zmin, height, 0.50, 0.60))
    L["Spine01"] = (0.0, spine01_c[1], spine01_c[2])

    spine02_c = centroid(band(coords, zmin, height, 0.40, 0.47))
    L["Spine02"] = (0.0, spine02_c[1], spine02_c[2])

    hips_c = centroid(band(coords, zmin, height, 0.31, 0.35))
    L["Hips"] = (0.0, hips_c[1], hips_c[2])

    # --- legs (per-side, real leg surface points) ---
    leg_upper = band(coords, zmin, height, 0.24, 0.31)
    lu, ru = split_lr(leg_upper)
    L["LeftUpLeg"] = centroid(lu)
    L["RightUpLeg"] = centroid(ru)

    knee_band = band(coords, zmin, height, 0.19, 0.23)
    lk, rk = split_lr(knee_band)
    L["LeftLeg"] = centroid(lk)
    L["RightLeg"] = centroid(rk)

    ankle_band = band(coords, zmin, height, 0.075, 0.095)
    la, ra = split_lr(ankle_band)
    L["LeftFoot"] = centroid(la)
    L["RightFoot"] = centroid(ra)

    toe_band = band(coords, zmin, height, 0.0, 0.04)
    lt, rt = split_lr(toe_band)
    L["LeftToeBase"] = frontmost(lt)
    L["RightToeBase"] = frontmost(rt)

    # --- arms (per-side, extreme-X surface point at each limb height) ---
    shoulder_band = band(coords, zmin, height, 0.685, 0.715)
    shoulder_l = extreme_left(shoulder_band)
    shoulder_r = extreme_right(shoulder_band)
    L["LeftArm"] = shoulder_l
    L["RightArm"] = shoulder_r
    # Clavicle (LeftShoulder/RightShoulder) sits between spine centerline and
    # the shoulder ball -- a distinct, non-zero-length bone (avoids
    # collapsing Shoulder==Arm to a zero-length edge case).
    L["LeftShoulder"] = lerp3(L["Spine"], shoulder_l, 0.45)
    L["RightShoulder"] = lerp3(L["Spine"], shoulder_r, 0.45)

    elbow_band = band(coords, zmin, height, 0.50, 0.53)
    L["LeftForeArm"] = extreme_left(elbow_band)
    L["RightForeArm"] = extreme_right(elbow_band)

    wrist_band = band(coords, zmin, height, 0.32, 0.35)
    L["LeftHand"] = extreme_left(wrist_band)
    L["RightHand"] = extreme_right(wrist_band)

    return L


def synthesize_tail(name, head, landmarks):
    """Tail position for a bone: primary child's head for chain bones,
    or a synthesized extension in a sensible direction for leaves."""
    if name in PRIMARY_CHILD:
        return landmarks[PRIMARY_CHILD[name]]

    if name in ("LeftUpLeg", "LeftLeg", "LeftFoot"):
        child = {"LeftUpLeg": "LeftLeg", "LeftLeg": "LeftFoot", "LeftFoot": "LeftToeBase"}[name]
        return landmarks[child]
    if name in ("RightUpLeg", "RightLeg", "RightFoot"):
        child = {"RightUpLeg": "RightLeg", "RightLeg": "RightFoot", "RightFoot": "RightToeBase"}[
            name
        ]
        return landmarks[child]
    if name in ("LeftShoulder", "LeftArm", "LeftForeArm"):
        child = {"LeftShoulder": "LeftArm", "LeftArm": "LeftForeArm", "LeftForeArm": "LeftHand"}[
            name
        ]
        return landmarks[child]
    if name in ("RightShoulder", "RightArm", "RightForeArm"):
        child = {
            "RightShoulder": "RightArm",
            "RightArm": "RightForeArm",
            "RightForeArm": "RightHand",
        }[name]
        return landmarks[child]
    if name == "Spine02":
        return landmarks["Spine01"]
    if name == "Spine01":
        return landmarks["Spine"]
    if name == "neck":
        return landmarks["Head"]

    # Leaves: extend along the parent->head direction by a fixed fraction.
    parent_name = dict(HIERARCHY)[name]
    parent_head = landmarks[parent_name]
    direction = Vector(head) - Vector(parent_head)
    if direction.length < 1e-6:
        direction = Vector((0, 0, 0.05))
    extended = Vector(head) + direction.normalized() * max(direction.length * 0.4, 0.05)
    return tuple(extended)


def build_armature(landmarks):
    arm_data = bpy.data.armatures.new("GirlArmatureData")
    arm_obj = bpy.data.objects.new("GirlArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.scale = (1.0, 1.0, 1.0)
    arm_obj.location = (0.0, 0.0, 0.0)
    arm_obj.rotation_euler = (0.0, 0.0, 0.0)

    bpy.ops.object.mode_set(mode="EDIT")
    ebones = {}
    for name, parent_name in HIERARCHY:
        eb = arm_data.edit_bones.new(name)
        head = landmarks[name]
        tail = synthesize_tail(name, head, landmarks)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        if (Vector(tail) - Vector(head)).length < 1e-5:
            eb.tail = Vector(head) + Vector((0, 0, 0.03))
        ebones[name] = eb

    for name, parent_name in HIERARCHY:
        if parent_name is not None:
            ebones[name].parent = ebones[parent_name]
            ebones[name].use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def verify_in_blender(arm_obj):
    assert tuple(arm_obj.scale) == (1.0, 1.0, 1.0), f"armature scale not 1.0: {arm_obj.scale}"
    assert (
        bpy.context.scene.unit_settings.scale_length == 1.0
    ), f"scene unit scale_length not 1.0: {bpy.context.scene.unit_settings.scale_length}"
    n_bones = len(arm_obj.data.bones)
    assert n_bones == 24, f"expected 24 bones, got {n_bones}"
    print(
        f"BLENDER-SIDE CHECK OK: scale={tuple(arm_obj.scale)} unit_scale="
        f"{bpy.context.scene.unit_settings.scale_length} bone_count={n_bones}"
    )


def parse_glb_json(path):
    with open(path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", "not a valid GLB file"
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        assert chunk_type == 0x4E4F534A, "first chunk is not JSON"
        json_bytes = f.read(chunk_len)
    return json.loads(json_bytes)


def verify_exported_glb(path):
    gltf = parse_glb_json(path)
    nodes = gltf["nodes"]
    armature_nodes = [n for n in nodes if n.get("name") == "GirlArmature"]
    assert (
        len(armature_nodes) == 1
    ), f"expected exactly 1 'GirlArmature' node, found {len(armature_nodes)}"
    arm_node = armature_nodes[0]
    scale = arm_node.get("scale")
    assert scale is None or list(scale) == [
        1,
        1,
        1,
    ], f"GirlArmature node carries a non-unit scale in exported GLB JSON: {scale}"

    joint_names = set(n for n, _ in HIERARCHY)
    joint_nodes = [n for n in nodes if n.get("name") in joint_names]
    joint_node_names = set(n["name"] for n in joint_nodes)
    assert joint_node_names == joint_names, (
        f"joint name mismatch. missing={joint_names - joint_node_names} "
        f"extra={joint_node_names - joint_names}"
    )
    assert len(joint_nodes) == 24, f"expected 24 joint nodes in GLB, found {len(joint_nodes)}"

    skins = gltf.get("skins", [])
    print(
        f"GLB-JSON CHECK OK: GirlArmature.scale={scale!r} joint_node_count={len(joint_nodes)} "
        f"skins_present={len(skins)} (expected 0 -- no skinning in this phase)"
    )
    return {
        "armature_scale": scale,
        "joint_node_count": len(joint_nodes),
        "skins_present": len(skins),
    }


def add_bone_markers(landmarks):
    """Armature bones are a viewport-only overlay -- bpy.ops.render.render()
    never rasterizes them (same as empties/cameras). To visually verify
    joint placement in a real render, stand in actual renderable mesh
    geometry: a small emissive sphere at every bone head + a thin emissive
    cylinder along every parent->child edge. Debug-only, created AFTER the
    .blend and .glb are already written to disk, so it never reaches either
    output file.
    """
    mat = bpy.data.materials.new("BoneMarkerMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1.0, 0.05, 0.05, 1.0)
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.1, 0.1, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = (1.0, 0.1, 0.1, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0

    r = 0.018
    created = []
    for name, _parent in HIERARCHY:
        head = Vector(landmarks[name])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=head, segments=10, ring_count=6)
        obj = bpy.context.active_object
        obj.data.materials.append(mat)
        created.append(obj)

    up = Vector((0, 0, 1))
    for name, parent_name in HIERARCHY:
        if parent_name is None:
            continue
        h0 = Vector(landmarks[parent_name])
        h1 = Vector(landmarks[name])
        vec = h1 - h0
        length = vec.length
        if length < 1e-6:
            continue
        bpy.ops.mesh.primitive_cylinder_add(
            radius=r * 0.4, depth=length, location=(h0 + h1) / 2, vertices=8
        )
        obj = bpy.context.active_object
        obj.rotation_euler = up.rotation_difference(vec.normalized()).to_euler()
        obj.data.materials.append(mat)
        created.append(obj)

    return created


def render_verification(mesh_obj):
    bbox_corners = [mesh_obj.matrix_world @ Vector(c) for c in mesh_obj.bound_box]
    zs = [c.z for c in bbox_corners]
    xs = [c.x for c in bbox_corners]
    ys = [c.y for c in bbox_corners]
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    height = max(zs) - min(zs)
    ortho_scale = height * 1.15

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1600

    scene.world = bpy.data.worlds.new("VerifyWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.55, 0.55, 0.6, 1)
    bg.inputs[1].default_value = 1.0

    sun_data = bpy.data.lights.new("VerifySun", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("VerifySun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(60), 0, math.radians(30))

    sun2_data = bpy.data.lights.new("VerifySun2", type="SUN")
    sun2_data.energy = 1.5
    sun2 = bpy.data.objects.new("VerifySun2", sun2_data)
    scene.collection.objects.link(sun2)
    sun2.rotation_euler = (math.radians(-60), 0, math.radians(-150))

    def make_cam(name, location, rotation_euler, ortho_scale_val):
        cam_data = bpy.data.cameras.new(name)
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho_scale_val
        cam = bpy.data.objects.new(name, cam_data)
        scene.collection.objects.link(cam)
        cam.location = location
        cam.rotation_euler = rotation_euler
        return cam

    dist = 5.0
    cam_front = make_cam(
        "VerifyCamFront", (cx, cy - dist, cz), (math.radians(90), 0, 0), ortho_scale
    )
    cam_side = make_cam(
        "VerifyCamSide", (cx - dist, cy, cz), (math.radians(90), 0, math.radians(-90)), ortho_scale
    )

    scene.render.filepath = FRONT_PNG
    scene.camera = cam_front
    bpy.ops.render.render(write_still=True)

    scene.render.filepath = SIDE_PNG
    scene.camera = cam_side
    bpy.ops.render.render(write_still=True)

    print(f"RENDERED VERIFICATION: {FRONT_PNG} {SIDE_PNG}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    mesh_obj = import_girl_mesh(GIRL_SOURCE)
    coords = world_coords(mesh_obj)
    print(f"Girl mesh: {mesh_obj.name}, {len(coords)} verts")

    landmarks = compute_landmarks(coords)
    assert set(landmarks.keys()) == set(n for n, _ in HIERARCHY), "landmark set incomplete"
    for name, _ in HIERARCHY:
        x, y, z = landmarks[name]
        print(f"  landmark {name:16s} = ({x:+.4f}, {y:+.4f}, {z:+.4f})")

    bpy.context.scene.unit_settings.scale_length = 1.0
    arm_obj = build_armature(landmarks)
    verify_in_blender(arm_obj)

    # Skeleton + mesh only, no debug markers -- this is the canonical output.
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"SAVED BLEND: {BLEND_OUT}")

    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format="GLB",
        use_selection=False,
        export_apply=False,
    )
    print(f"EXPORTED GLB: {GLB_OUT}")

    result = verify_exported_glb(GLB_OUT)
    print("FINAL VERIFICATION RESULT:", json.dumps(result))

    # Debug-only visual proof, added AFTER both files are already on disk so
    # it never reaches the .blend or .glb -- armature bones themselves are a
    # viewport-only overlay and never appear in a bpy.ops.render.render()
    # output, so stand in real (renderable) marker geometry instead.
    add_bone_markers(landmarks)
    render_verification(mesh_obj)

    print("BUILD_GIRL_RIG_DONE")


if __name__ == "__main__":
    main()
