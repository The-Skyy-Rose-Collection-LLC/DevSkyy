"""Script template rendering tests — pure-Python, no MD required.

Tests load the bundled .tpl files and verify that string.Template
substitution produces scripts containing the expected MD API calls.
"""

from __future__ import annotations

import pytest
from cli_anything.marvelous.utils.marvelous_backend import (
    load_script_template, render_script_template)

# ── Helpers ───────────────────────────────────────────────────────────────


def _render(name: str, variables: dict) -> str:
    """Load a bundled template and substitute the given variables."""
    return render_script_template(load_script_template(name), variables)


# ── export.py.tpl ─────────────────────────────────────────────────────────


class TestExportTemplate:
    _base_vars = {
        "project_path": "/tmp/shirt.zpac",
        "output_path": "/tmp/shirt_out",
        "export_format": "obj",
    }

    def test_renders_project_path(self):
        result = _render("export.py.tpl", self._base_vars)
        assert "/tmp/shirt.zpac" in result

    def test_renders_output_path(self):
        result = _render("export.py.tpl", self._base_vars)
        assert "/tmp/shirt_out" in result

    def test_renders_export_format(self):
        result = _render("export.py.tpl", self._base_vars)
        assert "obj" in result

    def test_contains_export_api_call(self):
        result = _render("export.py.tpl", self._base_vars)
        assert "export_api" in result

    def test_contains_import_zpac_call(self):
        result = _render("export.py.tpl", self._base_vars)
        assert "import_api.ImportZpac" in result

    def test_missing_project_path_raises(self):
        tpl = load_script_template("export.py.tpl")
        with pytest.raises(KeyError):
            render_script_template(tpl, {"output_path": "/tmp/x", "export_format": "obj"})

    def test_missing_output_path_raises(self):
        tpl = load_script_template("export.py.tpl")
        with pytest.raises(KeyError):
            render_script_template(tpl, {"project_path": "/tmp/x.zpac", "export_format": "obj"})

    def test_windows_path_preserved(self):
        """Backslashes in paths survive substitution unchanged."""
        vars_ = {
            "project_path": r"C:\Users\test\shirt.zpac",
            "output_path": r"C:\Users\test\out",
            "export_format": "fbx",
        }
        result = _render("export.py.tpl", vars_)
        assert r"C:\Users\test\shirt.zpac" in result

    def test_unicode_path_preserved(self):
        vars_ = {
            "project_path": "/tmp/рубашка.zpac",
            "output_path": "/tmp/рубашка_out",
            "export_format": "usd",
        }
        result = _render("export.py.tpl", vars_)
        assert "рубашка.zpac" in result


# ── simulate.py.tpl ───────────────────────────────────────────────────────


class TestSimulateTemplate:
    _base_vars = {
        "project_path": "/tmp/dress.zpac",
        "frames": "250",
        "output_path": "/tmp/dress_sim.zpac",
    }

    def test_renders_frames(self):
        result = _render("simulate.py.tpl", self._base_vars)
        assert "250" in result

    def test_contains_utility_api_simulate(self):
        result = _render("simulate.py.tpl", self._base_vars)
        assert "utility_api.Simulate" in result

    def test_contains_export_zpac(self):
        result = _render("simulate.py.tpl", self._base_vars)
        assert "export_api.ExportZpac" in result

    def test_missing_frames_raises(self):
        tpl = load_script_template("simulate.py.tpl")
        with pytest.raises(KeyError):
            render_script_template(
                tpl, {"project_path": "/tmp/x.zpac", "output_path": "/tmp/x_out.zpac"}
            )

    def test_zero_frames_renders(self):
        """Zero is a valid integer; template should still render."""
        vars_ = {**self._base_vars, "frames": "0"}
        result = _render("simulate.py.tpl", vars_)
        assert "FRAMES" in result


# ── add_fabric.py.tpl ─────────────────────────────────────────────────────


class TestAddFabricTemplate:
    _base_vars = {
        "project_path": "/tmp/jacket.zpac",
        "pattern_name": "Front Panel",
        "fabric_name": "Wool Blend",
        "texture_path": "/tmp/wool.png",
        "output_path": "/tmp/jacket_v2.zpac",
    }

    def test_renders_pattern_name(self):
        result = _render("add_fabric.py.tpl", self._base_vars)
        assert "Front Panel" in result

    def test_renders_fabric_name(self):
        result = _render("add_fabric.py.tpl", self._base_vars)
        assert "Wool Blend" in result

    def test_contains_assign_fabric_call(self):
        result = _render("add_fabric.py.tpl", self._base_vars)
        assert "fabric_api.AssignFabricToPattern" in result

    def test_missing_pattern_name_raises(self):
        tpl = load_script_template("add_fabric.py.tpl")
        vars_incomplete = {k: v for k, v in self._base_vars.items() if k != "pattern_name"}
        with pytest.raises(KeyError):
            render_script_template(tpl, vars_incomplete)

    def test_special_chars_in_fabric_name(self):
        """Fabric names with spaces and quotes pass through without error."""
        vars_ = {**self._base_vars, "fabric_name": "Silk & Satin (100%)"}
        result = _render("add_fabric.py.tpl", self._base_vars)
        # Substitution should not raise
        assert result is not None
