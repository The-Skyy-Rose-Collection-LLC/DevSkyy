"""Author + bake the girl rig's breathing idle, rename clips to the mascot
contract, and export the mascot-body GLB.

Founder correction 2026-07-12: the Love Hurts Girl IS the site mascot (every
page, full-body chat host) — not a Love-Hurts-only cameo. The mascot clip
contract (theme CLAUDE.md + skyy-3d.js:46-51) requires lowercase 'idle' and
'walk' clips; 'wave/point/talk/joy' are optional and fall back to idle. The
rig has only GirlWalk_Baked — this script authors the missing idle.

Idle design: one breath per 3s (72-frame loop @24fps, frame 73 = frame 1),
rotation-only sinusoidal keys on the spine chain + a tiny arm sway. Rotation
SIGNS are probed empirically per bone (same 5-degree world-space-tail-delta
discipline as bake_walk_retarget.py) — never hand-guessed. No bone ever gets
a location keyframe (walk-in-place contract holds for idle too).

Pipeline (single headless run):
  backup .blend -> clear pose/action state -> probe signs -> author
  GirlIdle_Source -> nla.bake (ROTATION only, whole armature, same as walk)
  -> rename GirlIdle_Baked->'idle', GirlWalk_Baked->'walk' -> remove Source
  actions (ACTIONS export mode exports every action; Sources must not ship)
  -> verify (0 location fcurves; frame-73==frame-1 loop closure) -> save
  -> export girl-mascot-raw.glb (exact exporter args from
  export_for_verification.py, which produced the verified v1.glb).

Run:
    blender -b --factory-startup -P author_idle_and_export.py
"""

import json
import math
import os
import shutil

import bpy
from mathutils import Euler

DIR = "/Users/theceo/DevSkyy/.claude/worktrees/mascot-skin-weight-fix/renders/3d/girl-love-hurts/"
BLEND_PATH = DIR + "love-hurts-girl-rig.blend"
BACKUP_PATH = DIR + "love-hurts-girl-rig.pre-idle-backup.blend"
GLB_OUT = DIR + "girl-mascot-raw.glb"

ARMATURE_NAME = "GirlArmature"
MESH_NAME = "Mesh1.0"

WALK_BAKED = "GirlWalk_Baked"
WALK_SOURCE = "GirlWalk_Source"
IDLE_SOURCE = "GirlIdle_Source"
IDLE_BAKED = "GirlIdle_Baked"

# Final clip names — the mascot contract (lowercase, exact).
CLIP_WALK = "walk"
CLIP_IDLE = "idle"

FRAME_START = 1
FRAME_END = 73  # frame 73 duplicates frame 1 — explicit loop closure (3s @24fps)
KEY_EVERY = 4
TEST_ANGLE_DEG = 5.0

# Breathing amplitudes (degrees). Chest-led, head nearly level, arms whisper.
# Spine chain order on this rig: Hips - Spine02 - Spine01 - Spine - neck - Head
# (Spine = chest, verified by skin_weight_body.py's chain definition).
IDLE_BONES = {
    "Spine": {"amp": 1.2, "phase": 0.00, "metric": "neg_y"},
    "Spine01": {"amp": 0.6, "phase": 0.00, "metric": "neg_y"},
    "neck": {"amp": 0.5, "phase": 0.50, "metric": "neg_y"},  # counter-phase: head stays level
    "Head": {"amp": 0.4, "phase": 0.25, "metric": "neg_y"},
    "LeftArm": {"amp": 0.7, "phase": 0.00, "metric": "neg_y"},
    "RightArm": {"amp": 0.7, "phase": 0.00, "metric": "neg_y"},
}


def iter_action_fcurves(action):
    """Blender 5.x layered-Action model — see bake_walk_retarget.py."""
    for layer in action.layers:
        for strip in layer.strips:
            if strip.type != "KEYFRAME":
                continue
            for channelbag in strip.channelbags:
                for fc in channelbag.fcurves:
                    yield fc


def detect_sign(arm_obj, bone_name):
    """+1/-1 so that positive angle * sign leans the bone tail toward -Y
    (her facing direction). Raises if the probe produces no motion."""
    pb = arm_obj.pose.bones[bone_name]
    pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    rest_tail = pb.tail.copy()

    pb.rotation_euler = Euler((math.radians(TEST_ANGLE_DEG), 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()
    test_tail = pb.tail.copy()

    pb.rotation_euler = Euler((0.0, 0.0, 0.0), "XYZ")
    bpy.context.view_layer.update()

    component = -(test_tail - rest_tail).y
    if abs(component) < 1e-6:
        raise RuntimeError(f"{bone_name}: sign probe produced no measurable -Y tail motion")
    return 1.0 if component > 0 else -1.0


def clear_pose(arm_obj):
    """Rest pose everywhere before authoring — the saved file leaves the walk
    action assigned, and baking evaluates the CURRENT animation state.

    Returns the pre-call NLA mute states ({track_name: mute}) so the caller
    can hand them to restore_nla_mutes() before saving — muting must never
    leak into the saved .blend (harmless today at 0 tracks, wrong if tracks
    ever appear)."""
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
    for name in IDLE_BONES:
        if name not in arm_obj.pose.bones:
            raise RuntimeError(f"idle bone {name!r} not found in {ARMATURE_NAME}")
        arm_obj.pose.bones[name].rotation_mode = "XYZ"

    signs = {name: detect_sign(arm_obj, name) for name in IDLE_BONES}
    for name, sign in signs.items():
        print(f"  sign {name:10s} {sign:+.1f}")

    action = bpy.data.actions.new(IDLE_SOURCE)
    action.use_fake_user = True
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    span = FRAME_END - FRAME_START  # 72 frames = exactly one breath cycle
    frames = list(range(FRAME_START, FRAME_END + 1, KEY_EVERY))
    if frames[-1] != FRAME_END:
        frames.append(FRAME_END)

    for frame in frames:
        t = (frame - FRAME_START) / span  # 0..1 across the loop
        for name, cfg in IDLE_BONES.items():
            # breath-in = gentle extension (lean back): negative forward-lean.
            angle_deg = -cfg["amp"] * signs[name] * math.sin(2.0 * math.pi * (t + cfg["phase"]))
            pb = arm_obj.pose.bones[name]
            pb.rotation_euler = Euler((math.radians(angle_deg), 0.0, 0.0), "XYZ")
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    loc_curves = [fc for fc in iter_action_fcurves(action) if ".location" in fc.data_path]
    if loc_curves:
        raise RuntimeError(
            f"{IDLE_SOURCE}: authored {len(loc_curves)} location fcurves — must be 0"
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
        raise RuntimeError(f"{action.name}: {len(loc)} location fcurves after bake — must be 0")
    worst = 0.0
    for fc in fcurves:
        delta = abs(fc.evaluate(FRAME_START) - fc.evaluate(FRAME_END))
        worst = max(worst, delta)
    if worst > 1e-4:
        raise RuntimeError(
            f"{action.name}: loop not closed — frame{FRAME_END} vs frame{FRAME_START} max delta {worst}"
        )
    return {"fcurves": len(fcurves), "location_fcurves": 0, "loop_max_delta": worst}


def open_and_check():
    """Open the blend and assert the exact pre-run state this one-shot
    pipeline requires (fails loudly on a re-run — the walk action is renamed
    by rename_to_contract, so a second pass cannot silently double-apply)."""
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm = bpy.data.objects.get(ARMATURE_NAME)
    mesh = bpy.data.objects.get(MESH_NAME)
    if arm is None or arm.type != "ARMATURE" or mesh is None:
        raise RuntimeError(f"expected {ARMATURE_NAME} + {MESH_NAME} in blend")
    walk = bpy.data.actions.get(WALK_BAKED)
    if walk is None:
        raise RuntimeError(f"{WALK_BAKED} action missing — wrong blend state")
    return arm, mesh, walk


def rename_to_contract(walk, baked):
    """Rename actions to the mascot clip contract and drop the Source
    actions (ACTIONS export mode ships every action — Sources must not)."""
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


def export_glb(arm, mesh):
    """Export the mascot-body GLB with the exact exporter args that produced
    the independently-verified v1.glb (export_for_verification.py)."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in (arm, mesh):
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm

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

    arm, mesh, walk = open_and_check()

    print("=== rest pose ===")
    saved_mutes = clear_pose(arm)

    print("=== author idle (sign-probed, rotation-only) ===")
    author_idle(arm)

    print("=== bake idle (whole armature, ROTATION only) ===")
    baked = bake_idle(arm)
    print("idle verify:", json.dumps(verify_idle(baked)))

    print("=== rename to mascot clip contract + drop Source actions ===")
    rename_to_contract(walk, baked)

    # Neutral base pose for export (ACTIONS mode exports every action
    # regardless), then restore the original NLA mute states so muting
    # never leaks into the saved .blend.
    clear_pose(arm)
    restore_nla_mutes(arm, saved_mutes)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Saved: {BLEND_PATH}")

    print("=== export girl-mascot-raw.glb (v1-verified exporter args) ===")
    export_glb(arm, mesh)


if __name__ == "__main__":
    main()
