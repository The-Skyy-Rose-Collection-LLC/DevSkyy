"""Tests for scripts/oai_render/scene_schema.py.

Six tests covering:
1. Ghost scene has required top-level keys
2. On-model scene includes brand hex #B76E79 in color_palette
3. scene_to_prompt_block output is valid JSON extractable
4. build_prompt(scene=None) is backward-compatible (no SCENE SPEC marker)
5. Unknown on-model collection raises SceneError (no silent fallback)
6. build_scene returns fresh dicts (no shared-state mutation)
7. flatlay → clean-studio scene with top-down camera (not on-model)
8. COLLECTION_SCENES and _ONMODEL_DEFAULTS share the same per-collection landmark
"""

from __future__ import annotations

import json

import pytest

from scripts.oai_render.prompt import COLLECTION_SCENES, SceneError, build_prompt
from scripts.oai_render.scene_schema import build_scene, scene_to_prompt_block

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_GHOST_KWARGS = dict(
    sku="br-001",
    name="The Black Rose Varsity",
    collection="black-rose",
    style="ghost",
)

_ONMODEL_KWARGS = dict(
    sku="sg-001",
    name="The Signature Hoodie",
    collection="signature",
    style="on-model",
)

_BUILD_PROMPT_KWARGS = dict(
    name="The Black Rose Varsity",
    sku="br-001",
    collection="black-rose",
    reference_labels=[],
    dossier_text=None,
    is_patch=False,
    style="ghost",
    view="front",
)


# ---------------------------------------------------------------------------
# Test 1 — ghost scene has required schema keys
# ---------------------------------------------------------------------------


def test_ghost_scene_has_required_keys() -> None:
    scene = build_scene(**_GHOST_KWARGS)
    required = {
        "subject",
        "model",
        "environment",
        "lighting",
        "camera",
        "style",
        "mood",
        "color_palette",
        "constraints",
    }
    assert required.issubset(scene.keys()), f"Missing keys: {required - set(scene.keys())}"
    # ghost-specific: model is None
    assert scene["model"] is None
    assert scene["subject"]["type"] == "ghost-mannequin"


# ---------------------------------------------------------------------------
# Test 2 — on-model scene includes brand rose-gold hex in palette
# ---------------------------------------------------------------------------


def test_onmodel_scene_color_palette_includes_brand_hex() -> None:
    scene = build_scene(**_ONMODEL_KWARGS)
    palette: list[str] = scene["color_palette"]
    assert "#B76E79" in palette, f"Rose Gold #B76E79 missing from palette: {palette}"
    # Also verify the palette is non-empty and all entries are hex strings
    assert all(p.startswith("#") for p in palette), f"Non-hex value in palette: {palette}"


# ---------------------------------------------------------------------------
# Test 3 — scene_to_prompt_block produces a valid-JSON extractable block
# ---------------------------------------------------------------------------


def test_scene_to_prompt_block_valid_json() -> None:
    scene = build_scene(**_GHOST_KWARGS)
    block = scene_to_prompt_block(scene)
    assert block.startswith(
        "SCENE SPEC (JSON)"
    ), f"Block does not start with expected header:\n{block[:80]}"
    # Extract JSON portion — everything after the first newline
    json_part = block[block.index("\n") + 1 :]
    parsed = json.loads(json_part)  # raises if not valid JSON
    assert parsed["subject"]["sku"] == "br-001"


# ---------------------------------------------------------------------------
# Test 4 — build_prompt(scene=None) produces no SCENE SPEC marker
# ---------------------------------------------------------------------------


def test_build_prompt_scene_none_is_backward_compatible() -> None:
    # Call with explicit scene=None
    result_with_none = build_prompt(**_BUILD_PROMPT_KWARGS, scene=None)
    # Call without scene kwarg at all
    result_no_kwarg = build_prompt(**_BUILD_PROMPT_KWARGS)

    assert "SCENE SPEC" not in result_with_none, "scene=None must not inject a SCENE SPEC block"
    assert (
        result_with_none == result_no_kwarg
    ), "scene=None output must equal output with no scene kwarg"


# ---------------------------------------------------------------------------
# Test 5 — unknown on-model collection raises SceneError (no silent fallback)
# ---------------------------------------------------------------------------


def test_unknown_collection_raises_sceneerror() -> None:
    with pytest.raises(SceneError, match="No on-model scene"):
        build_scene(
            sku="xx-001",
            name="Mystery Piece",
            collection="nonexistent-collection",
            style="on-model",
        )


# ---------------------------------------------------------------------------
# Test 6 — build_scene returns fresh dicts (mutation isolation)
# ---------------------------------------------------------------------------


def test_build_scene_returns_fresh_dicts() -> None:
    scene_a = build_scene(**_GHOST_KWARGS)
    scene_b = build_scene(**_GHOST_KWARGS)

    # Mutate scene_a's nested dicts
    scene_a["lighting"]["key"] = "MUTATED"
    scene_a["constraints"]["no_watermarks"] = False
    scene_a["color_palette"].append("#DEADBE")

    # scene_b must be unaffected
    assert (
        scene_b["lighting"]["key"] != "MUTATED"
    ), "Mutation of scene_a.lighting leaked into scene_b — shared reference bug"
    assert (
        scene_b["constraints"]["no_watermarks"] is True
    ), "Mutation of scene_a.constraints leaked into scene_b"
    assert (
        "#DEADBE" not in scene_b["color_palette"]
    ), "Mutation of scene_a.color_palette leaked into scene_b"


# ---------------------------------------------------------------------------
# Test 7 — flatlay → clean-studio scene, top-down camera, no model
# ---------------------------------------------------------------------------


def test_flatlay_uses_clean_studio_topdown_not_onmodel() -> None:
    scene = build_scene(
        sku="br-001",
        name="The Black Rose Varsity",
        collection="black-rose",
        style="flatlay",
    )
    # flatlay must NOT fall through to the on-model branch
    assert scene["model"] is None, "flatlay must have no model"
    assert scene["subject"]["type"] == "flatlay"
    assert scene["environment"] == "seamless studio cyclorama"
    # camera angle must match the top-down flatlay PRESENTATION, not ghost eye-level
    angle = scene["camera"]["angle"].lower()
    assert "top-down" in angle or "overhead" in angle, f"flatlay camera not top-down: {angle}"


# ---------------------------------------------------------------------------
# Test 8 — drift guard: the two collection-environment sources stay aligned
# ---------------------------------------------------------------------------


def test_collection_env_sources_share_landmarks() -> None:
    """
    COLLECTION_SCENES (prompt.py, paired path) and _ONMODEL_DEFAULTS (scene_schema,
    solo path) independently describe each collection's environment. They must
    reference the same landmark so the solo hero and paired look don't diverge.
    """
    from scripts.oai_render.scene_schema import _ONMODEL_DEFAULTS

    landmarks = {
        "black-rose": "bay bridge",
        "love-hurts": "château",
        "signature": "golden gate",
        "kids-capsule": "throne",
    }
    for collection, landmark in landmarks.items():
        paired = COLLECTION_SCENES[collection].lower()
        solo = str(_ONMODEL_DEFAULTS[collection]["environment"]).lower()
        assert landmark in paired, f"{collection}: {landmark!r} missing from COLLECTION_SCENES"
        assert landmark in solo, f"{collection}: {landmark!r} missing from _ONMODEL_DEFAULTS"
