"""Golden-fixture regression test — spec CHARACTER_PIPELINE_SPEC.md Definition of
Done #2: "WS6 gates wired into CI against golden fixture; a deliberately-broken
weight solve must fail CI naming the wave_R non-arm displacement metric."

Every other test in this suite runs against small hand-built synthetic meshes.
This is the first (and only) test that runs the real pipeline against a real,
complex, clothed character mesh — `love_hurts_girl_static.glb`, derived from
the actual Love Hurts Girl asset via scripts/prepare_character_pipeline_fixture.py.

Regenerate the fixture after any pipeline change:
    python scripts/prepare_character_pipeline_fixture.py

No pytest marker: CI (.github/workflows/ci.yml) runs plain `pytest tests/` with
no `-m` override, which inherits pyproject.toml's default
`-m "not slow and not integration"` — a marked test would silently never run.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from pygltflib import GLTF2

from skyyrose.character_pipeline import _glb_io, segment, skeleton, weights
from skyyrose.character_pipeline.config import load_character_yaml
from skyyrose.character_pipeline.landmarks import detect_landmarks
from skyyrose.character_pipeline.verify import GateFailure, verify_character

FIXTURE = Path(__file__).parent / "fixtures" / "love_hurts_girl_static.glb"
CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "skyyrose"
    / "character_pipeline"
    / "characters"
    / "love_hurts_girl.yaml"
)


def _load_fixture_mesh() -> tuple[np.ndarray, np.ndarray]:
    gltf = GLTF2().load(str(FIXTURE))
    blob = gltf.binary_blob()
    prim = gltf.meshes[0].primitives[0]
    v = _glb_io.read_accessor(gltf, blob, prim.attributes.POSITION).astype(np.float64)
    f = _glb_io.read_accessor(gltf, blob, prim.indices).astype(np.uint32)
    return v, f


def _rig_fixture():
    """Runs landmarks->skeleton->segment->weights on the real fixture, mirroring
    cli.py's _run_build from `landmarks.detect_landmarks` onward — the fixture
    is already post-clean (WS2), so convert/clean are deliberately not re-run."""
    v, f = _load_fixture_mesh()
    config = load_character_yaml(CONFIG_PATH)
    lm = detect_landmarks(v, config)
    skel = skeleton.build_skeleton(lm)
    seg = segment.segment_mesh(v, f, skel)
    w = weights.solve_weights(v, skel, seg, config)
    return v, f, skel, seg, w


def test_golden_fixture_pipeline_passes_all_gates(tmp_path):
    """The real, non-synthetic regression check: does the pipeline still
    correctly rig the real Love Hurts Girl mesh end to end."""
    v, f, skel, seg, w = _rig_fixture()

    assert (
        seg.converged
    ), f"weld-cut did not converge (total_cut={seg.total_cut}, passes={seg.passes_run})"

    rigged_path = tmp_path / "rigged.glb"
    weights.write_rigged_glb(FIXTURE, v, seg.faces, skel, w, rigged_path)

    report = verify_character(rigged_path, tmp_path / "qa")
    failed = [g for g in report.gates if not g["pass"]]
    assert report.all_passed, f"gates failed: {failed} (total_cut={seg.total_cut} for reference)"


def test_corrupted_weights_fails_the_wave_gate_by_name(tmp_path):
    """Proves the WS6 gate has teeth: deliberately corrupt a handful of real,
    legitimately non-arm, below-shoulder vertices to bind 100% to RightArm, and
    confirm verify_character() raises GateFailure naming the EXACT metric spec
    DoD #2 requires (wave_R.non_arm_side_max_disp) — not a substring match,
    since a loosely-targeted corruption (e.g. patching config.TUBE_R) can trip
    a different metric or nothing at all depending on the dead-vertex rescue.
    """
    v, f, skel, seg, w = _rig_fixture()
    idx = {n: i for i, n in enumerate(skel.names)}
    right_arm_idx = idx["mixamorig:RightArm"]
    shoulder_r_y = float(skel.positions[right_arm_idx][1])

    # Real, unambiguous non-arm candidates: back/side torso verts, well below the
    # shoulder, outside BOTH the torso-column band (|x|<SEED_BODY_X=0.06) and the
    # arm itself (RightArm sits at x=-0.18; this zone stays well short of it).
    candidates = np.where(
        (seg.labels != segment.ARM_R)
        & (v[:, 0] < -0.09)
        & (v[:, 0] > -0.15)
        & (v[:, 1] < shoulder_r_y - 0.3)
    )[0]
    assert (
        len(candidates) >= 5
    ), "fixture/skeleton drifted — no unambiguous non-arm corruption candidates found"
    corrupt_idx = candidates[:5]

    # Partial-weight bleed, NOT a full override: keep each vert's real dominant
    # joint at slot 0 (so verify.py's dominant-joint-based seg_labels recompute
    # still classifies these as non-arm — a full RightArm override would make
    # RightArm dominant and self-reclassify the vert as "arm", silently escaping
    # the non_arm_side check it's supposed to trip). A strong secondary weight
    # is enough to move the vert well past 0.002m under RightArm's -1.15rad wave.
    w.joints[corrupt_idx, 1] = right_arm_idx
    w.weights[corrupt_idx] = np.tile([0.6, 0.4, 0.0, 0.0], (len(corrupt_idx), 1))

    rigged_path = tmp_path / "corrupted_rigged.glb"
    weights.write_rigged_glb(FIXTURE, v, seg.faces, skel, w, rigged_path)

    try:
        verify_character(rigged_path, tmp_path / "qa")
        raise AssertionError(
            "expected GateFailure from the deliberately corrupted rig, but verification passed"
        )
    except GateFailure as exc:
        assert (
            exc.metric == "wave_R.non_arm_side_max_disp"
        ), f"wrong gate tripped: {exc.metric} ({exc})"
