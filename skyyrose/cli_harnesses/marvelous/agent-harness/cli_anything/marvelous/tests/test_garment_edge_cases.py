"""Garment dataclass edge-case tests — pure-Python, no MD required.

Covers default/override field combinations, serialisation round-trips,
and boundary conditions not exercised in test_core.py.
"""

from __future__ import annotations

import json

import pytest
from cli_anything.marvelous.core.garment import (FabricProperty, Garment,
                                                 PatternPiece)

# ── FabricProperty edge cases ─────────────────────────────────────────────


class TestFabricPropertyEdgeCases:
    def test_all_fields_round_trip(self):
        f = FabricProperty(
            name="Heavy Denim",
            texture_path="/textures/denim.png",
            color_hex="#1A2B3C",
            density=0.8,
            thickness=2.1,
            stretch_weft=120.0,
            stretch_warp=110.0,
            shear_stiffness=25.0,
            bending_weft=1.2,
            bending_warp=1.1,
        )
        f2 = FabricProperty.from_dict(f.to_dict())
        assert f2.texture_path == "/textures/denim.png"
        assert f2.density == pytest.approx(0.8)
        assert f2.stretch_weft == pytest.approx(120.0)
        assert f2.shear_stiffness == pytest.approx(25.0)

    def test_default_density_is_float(self):
        f = FabricProperty(name="Linen")
        assert isinstance(f.density, float)

    def test_default_color_hex_is_white(self):
        f = FabricProperty(name="Canvas")
        assert f.color_hex == "#FFFFFF"

    def test_from_dict_with_only_name(self):
        f = FabricProperty.from_dict({"name": "MinimalFabric"})
        assert f.name == "MinimalFabric"
        assert f.thickness == 0.5  # default

    def test_to_dict_contains_all_fields(self):
        f = FabricProperty(name="Test")
        d = f.to_dict()
        expected_keys = {
            "name",
            "texture_path",
            "color_hex",
            "density",
            "thickness",
            "stretch_weft",
            "stretch_warp",
            "shear_stiffness",
            "bending_weft",
            "bending_warp",
        }
        assert expected_keys == set(d.keys())


# ── PatternPiece edge cases ───────────────────────────────────────────────


class TestPatternPieceEdgeCases:
    def test_all_fields_round_trip(self):
        p = PatternPiece(
            name="Back Bodice",
            fabric_name="Silk",
            vertex_count=512,
            area_cm2=480.75,
            notes="Bias cut",
        )
        p2 = PatternPiece.from_dict(p.to_dict())
        assert p2.vertex_count == 512
        assert p2.area_cm2 == pytest.approx(480.75)
        assert p2.notes == "Bias cut"

    def test_default_vertex_count_is_zero(self):
        p = PatternPiece(name="Collar")
        assert p.vertex_count == 0

    def test_from_dict_only_name(self):
        p = PatternPiece.from_dict({"name": "Cuff"})
        assert p.name == "Cuff"
        assert p.area_cm2 == 0.0


# ── Garment edge cases ────────────────────────────────────────────────────


class TestGarmentEdgeCases:
    def test_simulation_frames_default(self):
        g = Garment(name="Default Frames")
        assert g.simulation_frames == 100

    def test_simulation_frames_override(self):
        g = Garment(name="Long Sim", simulation_frames=500)
        assert g.simulation_frames == 500

    def test_notes_preserved_through_round_trip(self):
        g = Garment(name="Noted", notes="Sample garment for testing")
        g2 = Garment.from_dict(g.to_dict())
        assert g2.notes == "Sample garment for testing"

    def test_source_file_preserved_through_round_trip(self):
        g = Garment(name="Sourced", source_file="/projects/shirt.zpac")
        g2 = Garment.from_dict(g.to_dict())
        assert g2.source_file == "/projects/shirt.zpac"

    def test_multiple_fabrics_all_preserved(self):
        fabrics = [
            FabricProperty("Cotton"),
            FabricProperty("Polyester"),
            FabricProperty("Lycra"),
        ]
        g = Garment(name="Blend", fabrics=fabrics)
        g2 = Garment.from_dict(g.to_dict())
        assert g2.fabric_count == 3
        names = {f.name for f in g2.fabrics}
        assert names == {"Cotton", "Polyester", "Lycra"}

    def test_fabric_by_name_case_insensitive_variants(self):
        f = FabricProperty("Cashmere")
        g = Garment(name="Luxury", fabrics=[f])
        assert g.fabric_by_name("CASHMERE") is f
        assert g.fabric_by_name("cashmere") is f
        assert g.fabric_by_name("Cashmere") is f

    def test_pattern_by_name_case_insensitive_variants(self):
        p = PatternPiece("LEFT SLEEVE")
        g = Garment(name="Coat", patterns=[p])
        assert g.pattern_by_name("left sleeve") is p
        assert g.pattern_by_name("LEFT SLEEVE") is p
        assert g.pattern_by_name("Left Sleeve") is p

    def test_to_json_produces_valid_json(self):
        g = Garment(
            name="JSON Test",
            patterns=[PatternPiece("Front")],
            fabrics=[FabricProperty("Silk")],
        )
        raw = g.to_json()
        parsed = json.loads(raw)
        assert parsed["name"] == "JSON Test"
        assert len(parsed["patterns"]) == 1

    def test_from_json_round_trip_with_unicode(self):
        g = Garment(name="ткань", notes="Unicode fabric")
        g2 = Garment.from_json(g.to_json())
        assert g2.name == "ткань"

    def test_from_dict_simulation_frames_coercion(self):
        """simulation_frames provided as string should be coerced to int."""
        g = Garment.from_dict({"name": "Coerce", "simulation_frames": "200"})
        assert g.simulation_frames == 200
        assert isinstance(g.simulation_frames, int)
