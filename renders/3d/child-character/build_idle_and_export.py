"""Phase 5 (cont.): author the child rig's breathing idle clip, rename
clips to the mascot runtime contract ('idle'/'walk', lowercase, exact --
skyy-3d.js:46-47 requires both at minimum, confirmed this session by
grepping the actual runtime script), and export the final GLB.

Idle design mirrors author_idle_and_export.py (girl rig): one breath per
3s (72-frame loop @24fps, frame 73 = frame 1), rotation-only sinusoidal
keys on the spine chain + arm sway. Arm sway reuses this session's
empirically-confirmed axis: LeftArm/RightArm swing on local-Z (not local-X
-- see build_walk_cycle.py's module docstring for why this T-pose rig's
arm axes differ from the girl rig's hanging-arm convention), applied ON
TOP of the permanent Shoulder-down static offset (also established this
session) so the idle sway reads as a natural arms-at-the-side breathing
motion, not a T-pose sway.

Run: blender --background --factory-startup --python build_idle_and_export.py
"""

import json
import math
import os
import shutil

import bpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(HERE, "child-character-skinned.blend")
BACKUP_PATH = os.path.join(HERE, "child-character-skinned.pre-idle-backup.blend")
GLB_OUT = os.path.join(HERE, "child-character-final.glb")

WALK_BAKED = "ChildWalk_Baked"
WALK_SOURCE = "ChildWalk_Source"
IDLE_SOURCE = "ChildIdle_Source"
IDLE_BAKED = "ChildIdle_Baked"

CLIP_WALK = "walk"
CLIP_IDLE = "idle"

FRAME_START = 1
FRAME_END = 73
KEY_EVERY = 4
TEST_ANGLE_DEG = 5.0

SHOULDER_DOWN_OFFSET_DEG = -90.0  # same static correction as build_walk_cycle.py

# Spine chain bones use local-X (matches this rig's near-vertical spine,
# same convention as the girl rig -- confirmed valid, spine bones point
# nearly straight up on both rigs). Arms use local-Z (T-pose-specific,
# confirmed this session).
IDLE_BONES_X = {
    "Spine": {"amp": 1.2, "phase": 0.00},
    "Spine01": {"amp": 0.6, "phase": 0.00},
    "neck": {"amp": 0.5, "phase": 0.50},
    "Head": {"amp": 0.4, "phase": 0.25},
}
IDLE_BONES_Z = {
    "LeftArm": {"amp": 0.7, "phase": 0.00},
    "RightArm": {"amp": 0.7, "phase": 0.00},
}
ALL_IDLE_BONES = list(IDLE_BONES_X) + list(IDLE_BONES_Z)


def iter_action_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


def zero_euler(axis_idx, angle_rad=0.0):
    v = [0.0, 0.0, 0.0]
    v[axis_idx] = angle_rad
    return Euler(tuple(v), "XYZ")


def detect_sign(arm_obj, bone_name, axis_idx):
    """neg_y metric -- same convention as build_walk_cycle.py: positive
    result means +angle on this axis leans the bone tail toward -Y (the
    facing direction)."""
    pb = arm_obj.pose.bones[bone_name]
    base = pb.rotation_euler.copy()
    rest_tail = pb.tail.copy()

    pb.rotation_euler = base.copy()
    pb.rotation_euler[axis_idx] += math.radians(TEST_ANGLE_DEG)
    bpy.context.view_layer.update()
    test_tail = pb.tail.copy()

    pb.rotation_euler = base
    bpy.context.view_layer.update()

    component = -(test_tail - rest_tail).y
    if abs(component) < 1e-6:
        raise RuntimeError(f"{bone_name}: sign probe produced no measurable -Y tail motion")
    return 1.0 if component > 0 else -1.0


def apply_shoulder_down_offset(arm_obj):
    for side in ("Left", "Right"):
        pb = arm_obj.pose.bones[f"{side}Shoulder"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = zero_euler(0, math.radians(SHOULDER_DOWN_OFFSET_DEG))
    bpy.context.view_layer.update()


def clear_pose(arm_obj):
    saved_mutes = {}
    if arm_obj.animation_data:
        arm_obj.animation_data.action = None
        for track in arm_obj.animation_data.nla_tracks:
            saved_mutes[track.name] = track.mute
            track.mute = True
    for pb in arm_obj.pose.bones:
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
        pb.location = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    return saved_mutes


def restore_nla_mutes(arm_obj, saved_mutes):
    if not arm_obj.animation_data:
        return
    for track in arm_obj.animation_data.nla_tracks:
        if track.name in saved_mutes:
            track.mute = saved_mutes[track.name]


def author_idle(arm_obj):
    for name in ALL_IDLE_BONES:
        arm_obj.pose.bones[name].rotation_mode = "XYZ"
    arm_obj.pose.bones["LeftShoulder"].rotation_mode = "XYZ"
    arm_obj.pose.bones["RightShoulder"].rotation_mode = "XYZ"

    apply_shoulder_down_offset(arm_obj)

    signs_x = {name: detect_sign(arm_obj, name, 0) for name in IDLE_BONES_X}
    signs_z = {name: detect_sign(arm_obj, name, 2) for name in IDLE_BONES_Z}
    for name, sign in {**signs_x, **signs_z}.items():
        print(f"  sign {name:10s} {sign:+.1f}")

    action = bpy.data.actions.new(IDLE_SOURCE)
    action.use_fake_user = True
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    for side in ("Left", "Right"):
        arm_obj.pose.bones[f"{side}Shoulder"].keyframe_insert(
            data_path="rotation_euler", frame=FRAME_START
        )
        arm_obj.pose.bones[f"{side}Shoulder"].keyframe_insert(
            data_path="rotation_euler", frame=FRAME_END
        )

    span = FRAME_END - FRAME_START
    frames = list(range(FRAME_START, FRAME_END + 1, KEY_EVERY))
    if frames[-1] != FRAME_END:
        frames.append(FRAME_END)

    for frame in frames:
        t = (frame - FRAME_START) / span
        for name, cfg in IDLE_BONES_X.items():
            angle_deg = -cfg["amp"] * signs_x[name] * math.sin(2.0 * math.pi * (t + cfg["phase"]))
            pb = arm_obj.pose.bones[name]
            pb.rotation_euler = zero_euler(0, math.radians(angle_deg))
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        for name, cfg in IDLE_BONES_Z.items():
            angle_deg = -cfg["amp"] * signs_z[name] * math.sin(2.0 * math.pi * (t + cfg["phase"]))
            pb = arm_obj.pose.bones[name]
            pb.rotation_euler = zero_euler(2, math.radians(angle_deg))
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    loc_curves = [fc for fc in iter_action_fcurves(action) if ".location" in fc.data_path]
    if loc_curves:
        raise RuntimeError(
            f"{IDLE_SOURCE}: authored {len(loc_curves)} location fcurves -- must be 0"
        )
    print(
        f"Authored {IDLE_SOURCE}: {len(list(iter_action_fcurves(action)))} fcurves, {len(frames)} keyed frames"
    )
    return action


def bake_idle(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")

    bpy.context.scene.frame_start = FRAME_START
    bpy.context.scene.frame_end = FRAME_END

    bpy.ops.nla.bake(
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,
        clean_curves=False,
        bake_types={"POSE"},
        channel_types={"ROTATION"},
    )
    baked = arm_obj.animation_data.action
    if baked is None:
        raise RuntimeError("nla.bake left no action assigned")
    baked.name = IDLE_BAKED
    baked.use_fake_user = True
    bpy.ops.object.mode_set(mode="OBJECT")
    return baked


def verify_idle(action):
    fcurves = list(iter_action_fcurves(action))
    loc = [fc for fc in fcurves if ".location" in fc.data_path]
    if loc:
        raise RuntimeError(f"{action.name}: {len(loc)} location fcurves after bake -- must be 0")
    worst = 0.0
    for fc in fcurves:
        delta = abs(fc.evaluate(FRAME_START) - fc.evaluate(FRAME_END))
        worst = max(worst, delta)
    if worst > 1e-4:
        raise RuntimeError(f"{action.name}: loop not closed -- max delta {worst}")
    return {"fcurves": len(fcurves), "location_fcurves": 0, "loop_max_delta": worst}


def open_and_check():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm_obj = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh_obj = next(o for o in bpy.data.objects if o.type == "MESH")
    walk = bpy.data.actions.get(WALK_BAKED)
    if walk is None:
        raise RuntimeError(f"{WALK_BAKED} action missing -- wrong blend state")
    return arm_obj, mesh_obj, walk


def rename_to_contract(walk, baked):
    walk.name = CLIP_WALK
    baked.name = CLIP_IDLE
    for src_name in (WALK_SOURCE, IDLE_SOURCE):
        src = bpy.data.actions.get(src_name)
        if src is not None:
            bpy.data.actions.remove(src)
    exported_actions = sorted(a.name for a in bpy.data.actions)
    print("actions remaining:", exported_actions)
    if exported_actions != [CLIP_IDLE, CLIP_WALK]:
        raise RuntimeError(f"expected exactly ['idle','walk'], got {exported_actions}")


def export_glb(arm_obj, mesh_obj):
    bpy.ops.object.select_all(action="DESELECT")
    for o in (arm_obj, mesh_obj):
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format="GLB",
        use_selection=True,
        use_visible=False,
        export_yup=True,
        export_apply=False,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_bake_animation=False,
        export_skins=True,
        export_morph_animation=True,
        export_frame_range=False,
        export_optimize_animation_size=True,
        export_optimize_animation_keep_anim_armature=True,
        export_extras=True,
        export_image_format="AUTO",
    )
    size = os.path.getsize(GLB_OUT)
    with open(GLB_OUT, "rb") as f:
        if f.read(4) != b"glTF":
            raise RuntimeError("exported file lacks glTF magic")
    print(f"EXPORT_OK {GLB_OUT} ({size} bytes)")


def main():
    shutil.copy2(BLEND_PATH, BACKUP_PATH)
    print(f"Backup: {BACKUP_PATH}")

    arm_obj, mesh_obj, walk = open_and_check()

    print("=== rest pose ===")
    saved_mutes = clear_pose(arm_obj)

    print("=== author idle (sign-probed, rotation-only) ===")
    author_idle(arm_obj)

    print("=== bake idle ===")
    baked = bake_idle(arm_obj)
    print("idle verify:", json.dumps(verify_idle(baked)))

    print("=== rename to mascot clip contract + drop Source actions ===")
    rename_to_contract(walk, baked)

    clear_pose(arm_obj)
    restore_nla_mutes(arm_obj, saved_mutes)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Saved: {BLEND_PATH}")

    print("=== export child-character-final.glb ===")
    export_glb(arm_obj, mesh_obj)


if __name__ == "__main__":
    main()
