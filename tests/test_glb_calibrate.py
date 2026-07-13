"""Unit tests for the pure helpers in scripts/glb_calibrate.py (no browser, no server)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "glb_calibrate", Path(__file__).resolve().parent.parent / "scripts" / "glb_calibrate.py"
)
glb_calibrate = importlib.util.module_from_spec(_SPEC)
sys.modules["glb_calibrate"] = glb_calibrate
_SPEC.loader.exec_module(glb_calibrate)


class TestBuildGrid:
    def test_full_grid_is_nine_unique_combos(self):
        grid = glb_calibrate.build_grid(small=False)
        assert len(grid) == 9
        assert len(set(grid)) == 9
        assert ("neutral", 1.0) in grid
        assert ("agx", 1.3) in grid

    def test_small_grid_is_two_combos(self):
        grid = glb_calibrate.build_grid(small=True)
        assert grid == [("neutral", 0.7), ("neutral", 1.3)]

    def test_small_grid_is_subset_of_full_grid(self):
        full = set(glb_calibrate.build_grid(small=False))
        small = set(glb_calibrate.build_grid(small=True))
        assert small <= full


class TestComboLabel:
    def test_label_format(self):
        assert glb_calibrate.combo_label(("neutral", 1.0)) == "neutral_1.0"
        assert glb_calibrate.combo_label(("agx", 0.7)) == "agx_0.7"


class TestClassify:
    def test_none_is_unscorable(self):
        assert glb_calibrate.classify(None) == "UNSCORABLE"

    def test_under_threshold_is_correctable(self):
        assert glb_calibrate.classify(19.9, threshold=20.0) == "LIGHTING_CORRECTABLE"

    def test_at_threshold_is_correctable(self):
        assert glb_calibrate.classify(20.0, threshold=20.0) == "LIGHTING_CORRECTABLE"

    def test_over_threshold_is_true_mismatch(self):
        assert glb_calibrate.classify(20.1, threshold=20.0) == "TRUE_MISMATCH"


class TestRecommendedAction:
    def test_below_severe_is_retexture(self):
        assert glb_calibrate.recommended_action(39.9) == "meshy_retexture"

    def test_at_severe_is_regen(self):
        assert glb_calibrate.recommended_action(40.0) == "mesh_regen"

    def test_above_severe_is_regen(self):
        assert glb_calibrate.recommended_action(69.9) == "mesh_regen"


class TestPickCandidateCombo:
    def test_picks_combo_with_most_rescues(self):
        grid_results = {
            "sku-a": {("neutral", 1.0): 15.0, ("agx", 1.3): 25.0},
            "sku-b": {("neutral", 1.0): 25.0, ("agx", 1.3): 10.0},
            "sku-c": {("neutral", 1.0): 5.0, ("agx", 1.3): 8.0},
        }
        best, counts = glb_calibrate.pick_candidate_combo(grid_results, threshold=20.0)
        # neutral/1.0 rescues sku-a, sku-c (2); agx/1.3 rescues sku-b, sku-c (2) -> tie,
        # broken by grid order: neutral/1.0 sorts before agx/1.3.
        assert counts[("neutral", 1.0)] == 2
        assert counts[("agx", 1.3)] == 2
        assert best == ("neutral", 1.0)

    def test_no_rescues_returns_none(self):
        grid_results = {"sku-a": {("neutral", 1.0): 99.0}}
        best, counts = glb_calibrate.pick_candidate_combo(grid_results, threshold=20.0)
        assert best is None
        assert counts == {}

    def test_ignores_none_scores(self):
        grid_results = {"sku-a": {("neutral", 1.0): None, ("agx", 1.0): 5.0}}
        best, counts = glb_calibrate.pick_candidate_combo(grid_results, threshold=20.0)
        assert best == ("agx", 1.0)
        assert ("neutral", 1.0) not in counts


class TestClassifySweep:
    def test_picks_lowest_delta_e_as_best(self):
        combo_scores = {("neutral", 0.7): 25.0, ("agx", 1.3): 12.0, ("aces", 1.0): 30.0}
        result = glb_calibrate.classify_sweep(
            "sg-006", "master.webp", 59.0, combo_scores, threshold=20.0
        )
        assert result.best_combo == ("agx", 1.3)
        assert result.best_delta_e == 12.0
        assert result.classification == "LIGHTING_CORRECTABLE"
        assert result.baseline_delta_e == 59.0
        assert result.grid["agx_1.3"] == 12.0

    def test_all_over_threshold_is_true_mismatch(self):
        combo_scores = {("neutral", 0.7): 45.0, ("agx", 1.3): 41.0}
        result = glb_calibrate.classify_sweep("br-012", None, 69.9, combo_scores, threshold=20.0)
        assert result.classification == "TRUE_MISMATCH"
        assert result.best_delta_e == 41.0
        assert result.best_combo == ("agx", 1.3)

    def test_all_none_scores_is_unscorable(self):
        combo_scores = {("neutral", 0.7): None, ("agx", 1.3): None}
        result = glb_calibrate.classify_sweep("br-009", None, None, combo_scores, threshold=20.0)
        assert result.classification == "UNSCORABLE"
        assert result.best_combo is None
        assert result.best_delta_e is None


class TestBuildRemediationManifest:
    def test_only_includes_true_mismatch(self):
        classifications = [
            glb_calibrate.SkuCalibration(
                sku="br-012",
                master="m.webp",
                baseline_delta_e=69.9,
                grid={"agx_1.3": 41.0},
                best_combo=("agx", 1.3),
                best_delta_e=41.0,
                classification="TRUE_MISMATCH",
            ),
            glb_calibrate.SkuCalibration(
                sku="lh-002",
                master="m2.webp",
                baseline_delta_e=29.6,
                grid={"neutral_1.3": 12.0},
                best_combo=("neutral", 1.3),
                best_delta_e=12.0,
                classification="LIGHTING_CORRECTABLE",
            ),
        ]
        manifest = glb_calibrate.build_remediation_manifest(classifications, threshold=20.0)
        assert manifest["summary"]["count"] == 1
        assert manifest["entries"][0]["sku"] == "br-012"
        assert manifest["entries"][0]["recommended_action"] == "mesh_regen"
        assert manifest["entries"][0]["est_cost_usd"] is None  # mesh_regen is unpriced

    def test_meshy_retexture_priced_correctly(self):
        classifications = [
            glb_calibrate.SkuCalibration(
                sku="sg-011",
                master="m.webp",
                baseline_delta_e=26.9,
                grid={"neutral_1.0": 30.0},
                best_combo=("neutral", 1.0),
                best_delta_e=30.0,
                classification="TRUE_MISMATCH",
            ),
        ]
        manifest = glb_calibrate.build_remediation_manifest(classifications, threshold=20.0)
        assert manifest["entries"][0]["recommended_action"] == "meshy_retexture"
        assert manifest["entries"][0]["est_cost_usd"] == 0.50
        assert manifest["summary"]["est_total_cost_usd"] == 0.50
        assert manifest["summary"]["unpriced_count"] == 0

    def test_empty_when_no_true_mismatch(self):
        classifications = [
            glb_calibrate.SkuCalibration(
                sku="lh-002",
                master="m.webp",
                baseline_delta_e=29.6,
                grid={},
                best_combo=("neutral", 1.3),
                best_delta_e=12.0,
                classification="LIGHTING_CORRECTABLE",
            ),
        ]
        manifest = glb_calibrate.build_remediation_manifest(classifications, threshold=20.0)
        assert manifest["entries"] == []
        assert manifest["summary"]["count"] == 0
        assert manifest["summary"]["est_total_cost_usd"] == 0.0

    def test_mixed_priced_and_unpriced_totals(self):
        classifications = [
            glb_calibrate.SkuCalibration(
                sku="sg-011",
                master=None,
                baseline_delta_e=26.9,
                grid={},
                best_combo=None,
                best_delta_e=39.9,
                classification="TRUE_MISMATCH",
            ),
            glb_calibrate.SkuCalibration(
                sku="br-012",
                master=None,
                baseline_delta_e=69.9,
                grid={},
                best_combo=None,
                best_delta_e=69.9,
                classification="TRUE_MISMATCH",
            ),
        ]
        manifest = glb_calibrate.build_remediation_manifest(classifications, threshold=20.0)
        assert manifest["summary"]["count"] == 2
        assert manifest["summary"]["est_total_cost_usd"] == 0.50  # only the retexture one priced
        assert manifest["summary"]["unpriced_count"] == 1
