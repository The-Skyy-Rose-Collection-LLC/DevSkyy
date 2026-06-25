"""Unit tests for cli-anything-marvelous core modules.

All tests are pure-Python — no Marvelous Designer installation required.
Synthetic .zpac fixtures are created with stdlib zipfile.

Run:
    pytest cli_anything/marvelous/tests/test_core.py -v
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

import cli_anything.marvelous.core.library as library_mod
import cli_anything.marvelous.core.session as session_mod
import pytest
from cli_anything.marvelous.core.garment import (FabricProperty, Garment,
                                                 PatternPiece)
from cli_anything.marvelous.core.library import (LibraryEntry, delete_entry,
                                                 get_entry, import_project,
                                                 list_library)
from cli_anything.marvelous.core.project import (ProjectFileError, ProjectMeta,
                                                 load_garment_from_project,
                                                 read_project_meta)
from cli_anything.marvelous.core.session import (Session, delete_session,
                                                 list_sessions, load_session,
                                                 new_session, save_session)
from cli_anything.marvelous.utils.marvelous_backend import (
    MarvelousNotFoundError, MarvelousScriptError, find_marvelous_binary,
    load_script_template, render_script_template)

# ── Helpers ───────────────────────────────────────────────────────────────


def _make_zpac(path: Path, manifest: dict | None = None, garment: dict | None = None) -> Path:
    """Create a minimal synthetic .zpac ZIP fixture."""
    with zipfile.ZipFile(path, "w") as zf:
        if manifest is not None:
            zf.writestr("project.json", json.dumps(manifest))
        if garment is not None:
            zf.writestr("garment.json", json.dumps(garment))
    return path


# ── FabricProperty ────────────────────────────────────────────────────────


class TestFabricProperty:
    def test_default_values(self):
        f = FabricProperty(name="Cotton")
        assert f.name == "Cotton"
        assert f.color_hex == "#FFFFFF"
        assert f.density == 0.3

    def test_round_trip_dict(self):
        f = FabricProperty(name="Silk", color_hex="#FF0000", thickness=1.2)
        f2 = FabricProperty.from_dict(f.to_dict())
        assert f2.name == "Silk"
        assert f2.color_hex == "#FF0000"
        assert f2.thickness == 1.2

    def test_from_dict_ignores_unknown_keys(self):
        data = {"name": "Wool", "unknown_field": "ignored", "density": 0.5}
        f = FabricProperty.from_dict(data)
        assert f.name == "Wool"
        assert f.density == 0.5


# ── PatternPiece ──────────────────────────────────────────────────────────


class TestPatternPiece:
    def test_defaults(self):
        p = PatternPiece(name="Front Body")
        assert p.fabric_name == ""
        assert p.vertex_count == 0

    def test_round_trip_dict(self):
        p = PatternPiece(name="Sleeve", fabric_name="Cotton", area_cm2=320.5)
        p2 = PatternPiece.from_dict(p.to_dict())
        assert p2.name == "Sleeve"
        assert p2.fabric_name == "Cotton"
        assert p2.area_cm2 == 320.5

    def test_from_dict_ignores_extra(self):
        p = PatternPiece.from_dict({"name": "Collar", "extra": "ignored"})
        assert p.name == "Collar"


# ── Garment ───────────────────────────────────────────────────────────────


class TestGarment:
    def test_empty_garment(self):
        g = Garment(name="T-Shirt")
        assert g.pattern_count == 0
        assert g.fabric_count == 0

    def test_pattern_count_and_fabric_count(self):
        g = Garment(
            name="Dress",
            patterns=[PatternPiece("Front"), PatternPiece("Back")],
            fabrics=[FabricProperty("Satin")],
        )
        assert g.pattern_count == 2
        assert g.fabric_count == 1

    def test_fabric_by_name_found(self):
        f = FabricProperty("Cotton")
        g = Garment(name="Shirt", fabrics=[f])
        assert g.fabric_by_name("cotton") is f

    def test_fabric_by_name_not_found(self):
        g = Garment(name="Shirt", fabrics=[FabricProperty("Cotton")])
        assert g.fabric_by_name("Polyester") is None

    def test_pattern_by_name(self):
        p = PatternPiece("Front Body")
        g = Garment(name="Jacket", patterns=[p])
        assert g.pattern_by_name("front body") is p
        assert g.pattern_by_name("Back") is None

    def test_to_json_round_trip(self):
        g = Garment(
            name="Blazer",
            patterns=[PatternPiece("Front", fabric_name="Wool")],
            fabrics=[FabricProperty("Wool", color_hex="#222222")],
            simulation_frames=200,
        )
        g2 = Garment.from_json(g.to_json())
        assert g2.name == "Blazer"
        assert g2.simulation_frames == 200
        assert g2.patterns[0].name == "Front"
        assert g2.fabrics[0].color_hex == "#222222"

    def test_from_dict_empty(self):
        g = Garment.from_dict({})
        assert g.name == "Untitled"
        assert g.pattern_count == 0


# ── Project parser ────────────────────────────────────────────────────────


class TestReadProjectMeta:
    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_project_meta(tmp_path / "missing.zpac")

    def test_wrong_extension(self, tmp_path):
        p = tmp_path / "file.obj"
        p.write_bytes(b"")
        with pytest.raises(ProjectFileError, match="Unsupported format"):
            read_project_meta(p)

    def test_not_a_zip(self, tmp_path):
        p = tmp_path / "fake.zpac"
        p.write_bytes(b"not a zip file")
        with pytest.raises(ProjectFileError, match="valid ZIP"):
            read_project_meta(p)

    def test_empty_zip(self, tmp_path):
        p = _make_zpac(tmp_path / "empty.zpac")
        meta = read_project_meta(p)
        assert meta.name == "empty"
        assert meta.file_format == "zpac"
        assert meta.pattern_count == 0
        assert meta.fabric_count == 0

    def test_reads_manifest_name(self, tmp_path):
        p = _make_zpac(
            tmp_path / "shirt.zpac",
            manifest={"name": "Classic Shirt", "md_version": "12.0", "created_at": "2024-01-01"},
        )
        meta = read_project_meta(p)
        assert meta.name == "Classic Shirt"
        assert meta.md_version == "12.0"
        assert meta.created_at == "2024-01-01"

    def test_counts_patterns_and_fabrics_from_garment_json(self, tmp_path):
        garment = {
            "patterns": [{"name": "Front"}, {"name": "Back"}],
            "fabrics": [{"name": "Cotton"}],
        }
        p = _make_zpac(tmp_path / "dress.zpac", garment=garment)
        meta = read_project_meta(p)
        assert meta.pattern_count == 2
        assert meta.fabric_count == 1

    def test_detects_thumbnail(self, tmp_path):
        p = tmp_path / "with_thumb.zpac"
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("thumbnail.png", b"\x89PNG")
        meta = read_project_meta(p)
        assert meta.has_thumbnail is True

    def test_no_thumbnail(self, tmp_path):
        p = _make_zpac(tmp_path / "no_thumb.zpac")
        meta = read_project_meta(p)
        assert meta.has_thumbnail is False

    def test_zprj_format(self, tmp_path):
        p = _make_zpac(tmp_path / "project.zprj")
        meta = read_project_meta(p)
        assert meta.file_format == "zprj"

    def test_to_dict_keys(self, tmp_path):
        p = _make_zpac(tmp_path / "t.zpac", manifest={"name": "T"})
        meta = read_project_meta(p)
        d = meta.to_dict()
        assert "name" in d
        assert "file_format" in d
        assert "pattern_count" in d


class TestLoadGarmentFromProject:
    def test_basic_garment_load(self, tmp_path):
        garment = {
            "patterns": [{"name": "Front", "fabric_name": "Cotton", "area_cm2": 200.0}],
            "fabrics": [{"name": "Cotton", "color_hex": "#FFFFFF"}],
            "simulation_frames": 150,
        }
        p = _make_zpac(tmp_path / "shirt.zpac", manifest={"name": "Shirt"}, garment=garment)
        g = load_garment_from_project(p)
        assert g.name == "Shirt"
        assert g.pattern_count == 1
        assert g.fabric_count == 1
        assert g.patterns[0].name == "Front"
        assert g.fabrics[0].color_hex == "#FFFFFF"
        assert g.simulation_frames == 150

    def test_garment_with_string_patterns(self, tmp_path):
        garment = {"patterns": ["Sleeve", "Collar"], "fabrics": ["Linen"]}
        p = _make_zpac(tmp_path / "g.zpac", garment=garment)
        g = load_garment_from_project(p)
        assert g.pattern_count == 2
        assert g.patterns[0].name == "Sleeve"
        assert g.fabrics[0].name == "Linen"

    def test_source_file_recorded(self, tmp_path):
        p = _make_zpac(tmp_path / "recorded.zpac")
        g = load_garment_from_project(p)
        assert str(p) == g.source_file


# ── Session ───────────────────────────────────────────────────────────────


class TestSession:
    def test_to_dict_round_trip(self):
        s = Session(session_id="test-001", project_path="/tmp/a.zpac", garment_name="Dress")
        s2 = Session.from_dict(s.to_dict())
        assert s2.session_id == "test-001"
        assert s2.project_path == "/tmp/a.zpac"
        assert s2.garment_name == "Dress"

    def test_from_dict_ignores_extra(self):
        s = Session.from_dict({"session_id": "x", "unknown": "y"})
        assert s.session_id == "x"


class TestSessionCrud:
    @pytest.fixture(autouse=True)
    def patch_sessions_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(session_mod, "SESSIONS_DIR", tmp_path / "sessions")

    def test_save_and_load(self):
        s = Session(session_id="s-001", project_path="/tmp/p.zpac")
        save_session(s)
        loaded = load_session("s-001")
        assert loaded.project_path == "/tmp/p.zpac"

    def test_load_missing_raises(self):
        with pytest.raises(FileNotFoundError):
            load_session("nonexistent")

    def test_list_sessions_empty(self):
        assert list_sessions() == []

    def test_list_sessions_sorted(self):
        s1 = Session(session_id="old", updated_at=1000.0)
        s2 = Session(session_id="new", updated_at=2000.0)
        save_session(s1)
        save_session(s2)
        result = list_sessions()
        assert result[0].session_id == "new"
        assert result[1].session_id == "old"

    def test_delete_session_exists(self):
        s = Session(session_id="del-me")
        save_session(s)
        assert delete_session("del-me") is True
        with pytest.raises(FileNotFoundError):
            load_session("del-me")

    def test_delete_session_not_found(self):
        assert delete_session("ghost") is False

    def test_new_session_creates_and_persists(self):
        s = new_session(project_path="/tmp/x.zpac", garment_name="Jacket")
        loaded = load_session(s.session_id)
        assert loaded.project_path == "/tmp/x.zpac"
        assert loaded.garment_name == "Jacket"

    def test_locked_save_json_atomic(self, tmp_path):
        """_locked_save_json writes without leaving temp files behind."""
        from cli_anything.marvelous.core.session import _locked_save_json

        target = tmp_path / "out.json"
        _locked_save_json(target, {"key": "value"})
        assert target.exists()
        with target.open() as f:
            data = json.load(f)
        assert data["key"] == "value"
        # No leftover temp files
        temps = list(tmp_path.glob(".session-*.json"))
        assert len(temps) == 0

    def test_load_malformed_json_raises_value_error(self, tmp_path):
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        bad = session_dir / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        import cli_anything.marvelous.core.session as sm

        sm.SESSIONS_DIR = session_dir
        with pytest.raises(ValueError, match="Malformed"):
            load_session("bad")


# ── Library ───────────────────────────────────────────────────────────────


class TestLibraryEntry:
    def test_round_trip(self):
        e = LibraryEntry(slug="tshirt", name="T-Shirt", tags=["basics", "tops"])
        e2 = LibraryEntry.from_dict(e.to_dict())
        assert e2.slug == "tshirt"
        assert e2.tags == ["basics", "tops"]

    def test_from_dict_bad_tags(self):
        e = LibraryEntry.from_dict({"slug": "x", "name": "X", "tags": None})
        assert e.tags == []


class TestLibraryCrud:
    @pytest.fixture(autouse=True)
    def patch_library_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(library_mod, "LIBRARY_DIR", tmp_path / "library")

    def _make_zpac_file(self, tmp_path: Path, name: str = "test.zpac") -> Path:
        p = tmp_path / name
        _make_zpac(p, manifest={"name": "Test"})
        return p

    def test_list_empty(self):
        assert list_library() == []

    def test_import_and_list(self, tmp_path):
        src = self._make_zpac_file(tmp_path)
        e = import_project(src, "tshirt", "T-Shirt", tags=["basics"])
        entries = list_library()
        assert len(entries) == 1
        assert entries[0].slug == "tshirt"
        assert entries[0].tags == ["basics"]

    def test_import_duplicate_slug_raises(self, tmp_path):
        src = self._make_zpac_file(tmp_path)
        import_project(src, "dup", "Dup")
        src2 = self._make_zpac_file(tmp_path, "test2.zpac")
        with pytest.raises(FileExistsError):
            import_project(src2, "dup", "Dup 2")

    def test_import_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_project(tmp_path / "missing.zpac", "x", "X")

    def test_import_wrong_extension_raises(self, tmp_path):
        obj_file = tmp_path / "model.obj"
        obj_file.write_bytes(b"v 0 0 0")
        with pytest.raises(ValueError, match="Expected .zpac"):
            import_project(obj_file, "x", "X")

    def test_get_entry(self, tmp_path):
        src = self._make_zpac_file(tmp_path)
        import_project(src, "get-test", "Get Test", description="Desc")
        e = get_entry("get-test")
        assert e.description == "Desc"

    def test_get_entry_not_found(self):
        with pytest.raises(KeyError):
            get_entry("nonexistent")

    def test_delete_entry(self, tmp_path):
        src = self._make_zpac_file(tmp_path)
        import_project(src, "to-delete", "To Delete")
        assert delete_entry("to-delete") is True
        assert list_library() == []

    def test_delete_entry_not_found(self):
        assert delete_entry("ghost") is False

    def test_entry_source_path(self, tmp_path):
        src = self._make_zpac_file(tmp_path)
        e = import_project(src, "src-test", "Source Test")
        from cli_anything.marvelous.core.library import entry_source_path

        p = entry_source_path(e)
        assert p is not None
        assert p.exists()


# ── Backend ───────────────────────────────────────────────────────────────


class TestFindMarvelousBinary:
    def test_env_override_not_found_raises(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MARVELOUS_DESIGNER_BIN", str(tmp_path / "missing_binary"))
        with pytest.raises(MarvelousNotFoundError, match="set but file not found"):
            find_marvelous_binary()

    def test_env_override_valid_file(self, monkeypatch, tmp_path):
        fake_bin = tmp_path / "MarvelousDesigner"
        fake_bin.write_bytes(b"#!/bin/sh")
        monkeypatch.setenv("MARVELOUS_DESIGNER_BIN", str(fake_bin))
        result = find_marvelous_binary()
        assert result == str(fake_bin)

    def test_no_md_installed_raises(self, monkeypatch):
        monkeypatch.delenv("MARVELOUS_DESIGNER_BIN", raising=False)
        # Only raises if no real MD installed; mock the glob
        import glob as glob_mod

        monkeypatch.setattr(glob_mod, "glob", lambda *a, **kw: [])
        with pytest.raises(MarvelousNotFoundError):
            find_marvelous_binary()


class TestRenderScriptTemplate:
    def test_basic_substitution(self):
        result = render_script_template(
            "project = r'${project_path}'\nframes = ${frames}",
            {"project_path": "/tmp/shirt.zpac", "frames": "100"},
        )
        assert "project = r'/tmp/shirt.zpac'" in result
        assert "frames = 100" in result

    def test_missing_variable_raises(self):
        with pytest.raises(KeyError):
            render_script_template("x = ${missing}", {})

    def test_multiple_vars(self):
        tmpl = "${a} and ${b} and ${a}"
        result = render_script_template(tmpl, {"a": "foo", "b": "bar"})
        assert result == "foo and bar and foo"


class TestLoadScriptTemplate:
    def test_loads_export_template(self):
        text = load_script_template("export.py.tpl")
        assert "export_api" in text
        assert "${project_path}" in text
        assert "${export_format}" in text

    def test_loads_simulate_template(self):
        text = load_script_template("simulate.py.tpl")
        assert "utility_api.Simulate" in text
        assert "${frames}" in text

    def test_loads_add_fabric_template(self):
        text = load_script_template("add_fabric.py.tpl")
        assert "fabric_api.AssignFabricToPattern" in text
        assert "${pattern_name}" in text

    def test_missing_template_raises(self):
        with pytest.raises(FileNotFoundError):
            load_script_template("nonexistent.py.tpl")
