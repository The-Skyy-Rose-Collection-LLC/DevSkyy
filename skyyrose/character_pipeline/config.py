"""Constants registry and character.yaml loader for the character pipeline.

Single source of truth for every numeric literal used across workstreams —
CHARACTER_PIPELINE_SPEC.md section 3. All distances are meters at bind scale
unless noted otherwise.

Only two things scale with a character's detected/target height: landmark
Y-bands (the spec marks these `H`-suffixed, e.g. `[0.62H, 0.70H]`) and
BONE_RADII (spec section 5, "scaled proportionally with target_height").
Every other constant — X/Z point-distance gates, TUBE_R, SEED_ARM_R,
SHOULDER_BLEND_R, slice-scan resolution — is a fixed absolute meter value,
matching how the spec's own section 3 registry lists them (no H suffix, no
scaling instruction). The reference rig_girl.py hardcoded Y-bands as literal
meters (its crotch band was `0.55, 0.70` because that one model was 1.911m
tall); this registry stores the height-FRACTION instead so landmarks.py
auto-detects correctly on any character height. `character.yaml` can still
override any individual field per character.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---- geometry / segmentation tolerances (meters, at bind scale) -----------
CLUSTER_GAP = 0.02  # x-gap splitting slice clusters
TUBE_R = 0.10  # arm-tube validity radius
SEED_ARM_R = 0.055  # forearm/hand seed capsule
SEED_BODY_X = 0.06  # torso-column seed half-width
SHOULDER_BLEND_R = 0.13  # arm/torso weight blend zone
WELD_CUT_MAX_PASSES = 4
WELD_CUT_SHOULDER_FRACTION = 0.85  # cut only mixed tris below 0.85 * shoulder_y
WEIGHT_FALLOFF_POW = 4
MAX_INFLUENCES = 4
# Reference script's validated "y < 0.50" torso-column / pure-leg-territory
# threshold (on a 1.911m model with crotch_y=0.64), re-expressed as a fraction
# of crotch_y (0.50/0.64) so it generalizes to any character height. Shared by
# segment.py's seed_body y-bound and weights.py's leg-territory mask.
TORSO_COLUMN_Y_LO_FRAC = 0.78125
# Hair mask starts at neck_y + HAIR_Y_GAP_FRAC*height (validated 1.30 - 1.28 = 0.02m / 1.911m).
HAIR_Y_GAP_FRAC = 0.01047
# Leg-side x gate (validated 0.02m), as a fraction of height.
LEG_SIDE_GATE_FRAC = 0.01047

# ---- bone radii (meters), measured on Love Hurts Girl (height 1.911m) -----
# Scaled proportionally by target_height / REFERENCE_HEIGHT for other characters
# via CharacterConfig.bone_radius().
REFERENCE_HEIGHT = 1.911
BONE_RADII: dict[str, float] = {
    "Hips": 0.18,
    "Spine": 0.16,
    "Spine1": 0.16,
    "Spine2": 0.15,
    "Neck": 0.08,
    "Head": 0.40,  # the afro
    "Shoulder": 0.08,
    "Arm": 0.055,
    "ForeArm": 0.05,
    "Hand": 0.06,
    "UpLeg": 0.10,
    "Leg": 0.075,
    "Foot": 0.07,
    "Toe": 0.07,
}

# ---- landmark Y-bands, expressed as a FRACTION of total detected height ----
# shoulder/hand use the spec's own literal fractions ([0.62H,0.70H], [0.28H,0.42H]).
# hip_z/chest_z/head_z/foot_z aren't given explicit fractions in the spec text,
# so these are rig_girl.py's validated absolute-meter bands / REFERENCE_HEIGHT.
LANDMARK_BANDS_FRAC: dict[str, tuple[float, float]] = {
    "hip_z": (0.288, 0.366),  # crotch/hip z-depth band
    "chest_z": (0.523, 0.602),  # chest z-depth band
    "head_z": (0.733, 0.837),  # head z-depth band
    "foot_z": (0.010, 0.052),  # foot z-depth band
    "hand": (0.28, 0.42),  # hand centroid band — spec-literal
    "shoulder": (0.62, 0.70),  # shoulder centroid band — spec-literal
}

# ---- landmark X/Z point-distance gates — fixed absolute meters, NOT scaled --
SLICE_BAND_THICKNESS = 0.03  # meters, Y-slice thickness for clustering scans
SLICE_STEP = 0.05  # meters, Y-slice scan step
LANDMARK_X_GATE_FOOT_MIN = 0.05  # foot band |x| lower gate (excludes centerline verts)
LANDMARK_X_GATE_FOOT = 0.40  # foot band |x| upper gate (excludes the opposite foot)
LANDMARK_X_GATE_HAND = 0.16  # hand band |x| lower gate
LANDMARK_X_GATE_SHOULDER = 0.12  # shoulder band |x| lower gate
LANDMARK_X_GATE_CHEST = 0.12  # chest/hip z-sample |x| half-width

# ---- PBR correction ---------------------------------------------------------
PBR = {"metallic": 0.0, "roughness": 0.65, "dead_emissive_max": 16}

# ---- texture targets: (max_dimension, jpeg_quality) -------------------------
TEX = {"hero": (2048, 90), "widget": (1536, 87)}

# ---- WS6 verification gates --------------------------------------------------
GATE = {"static_max_disp": 0.002, "arm_min_mean_disp": 0.20}

# ---- vendored three.js pin ---------------------------------------------------
THREE_VERSION = "r128"


@dataclass
class CharacterConfig:
    """Per-character overrides loaded from character.yaml, layered over the
    height-normalized defaults above. Any field left unset falls back to
    auto-detection (landmarks.py) or the registry default (this module).
    """

    name: str = "character"
    target_height: float | None = None  # meters; None = keep detected mesh height
    bot_name: str = "SkyyRose Concierge"
    endpoint: str = ""
    teasers: list[str] = field(default_factory=list)
    fallbacks: list[str] = field(default_factory=list)
    landmark_overrides: dict[str, Any] = field(default_factory=dict)
    bone_radii_overrides: dict[str, float] = field(default_factory=dict)

    def bone_radius(self, bone_key: str, height: float) -> float:
        """Radius for a bone segment, scaled to this character's detected/target height."""
        base = self.bone_radii_overrides.get(bone_key, BONE_RADII[bone_key])
        return base * (height / REFERENCE_HEIGHT)


def load_character_yaml(path: str | Path) -> CharacterConfig:
    """Loads a character.yaml file into a CharacterConfig."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"character config not found: {path}")
    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    return CharacterConfig(
        name=raw.get("name", "character"),
        target_height=raw.get("target_height"),
        bot_name=raw.get("bot_name", "SkyyRose Concierge"),
        endpoint=raw.get("endpoint", ""),
        teasers=raw.get("teasers", []),
        fallbacks=raw.get("fallbacks", []),
        landmark_overrides=raw.get("landmarks", {}),
        bone_radii_overrides=raw.get("bone_radii", {}),
    )
