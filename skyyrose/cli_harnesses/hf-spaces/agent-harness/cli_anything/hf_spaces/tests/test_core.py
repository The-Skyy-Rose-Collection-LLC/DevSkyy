"""
Unit tests for cli-anything-hf-spaces core modules.

No live HF API calls. All HfApi interactions are mocked.
Run with: pytest cli_anything/hf_spaces/tests/test_core.py -v
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cli_anything.hf_spaces.core.hardware import (HARDWARE_SLUGS,
                                                  hardware_table_rows,
                                                  validate_hardware_slug)

# ---------------------------------------------------------------------------
# hardware.py
# ---------------------------------------------------------------------------



class TestHardware:
    def test_all_known_slugs_validate(self):
        for slug in HARDWARE_SLUGS:
            assert validate_hardware_slug(slug) == slug

    def test_invalid_slug_raises(self):
        with pytest.raises(ValueError, match="Unknown hardware tier"):
            validate_hardware_slug("not-a-real-tier")

    def test_hardware_table_rows_count(self):
        rows = hardware_table_rows()
        assert len(rows) == len(HARDWARE_SLUGS)

    def test_hardware_table_rows_fields(self):
        rows = hardware_table_rows()
        for row in rows:
            assert "slug" in row
            assert "cost_usd_hr" in row
            assert "description" in row

    def test_cpu_basic_is_free(self):
        rows = hardware_table_rows()
        cpu_basic = next(r for r in rows if r["slug"] == "cpu-basic")
        assert cpu_basic["cost_usd_hr"] == "free"

    def test_hardware_slugs_tuple_not_empty(self):
        assert len(HARDWARE_SLUGS) >= 18

    def test_t4_small_in_slugs(self):
        assert "t4-small" in HARDWARE_SLUGS

    def test_h100x8_in_slugs(self):
        assert "h100x8" in HARDWARE_SLUGS


# ---------------------------------------------------------------------------
# space.py
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.core.space import (SpaceRef, optional_space_ref,
                                               parse_space_ref)


class TestSpaceRef:
    def test_parse_slug(self):
        ref = SpaceRef.parse("owner/my-space")
        assert ref.owner == "owner"
        assert ref.name == "my-space"

    def test_parse_url(self):
        ref = SpaceRef.parse("https://huggingface.co/spaces/damBruh/test-space")
        assert ref.owner == "damBruh"
        assert ref.name == "test-space"

    def test_parse_url_trailing_slash(self):
        ref = SpaceRef.parse("https://huggingface.co/spaces/owner/name/")
        assert ref.owner == "owner"
        assert ref.name == "name"

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            SpaceRef.parse("not-a-valid-ref")

    def test_repo_id(self):
        ref = SpaceRef.parse("owner/name")
        assert ref.repo_id == "owner/name"

    def test_url_property(self):
        ref = SpaceRef.parse("owner/name")
        assert ref.url == "https://huggingface.co/spaces/owner/name"

    def test_embed_url(self):
        ref = SpaceRef.parse("owner/name")
        assert ref.embed_url == "https://owner-name.hf.space"

    def test_to_dict_roundtrip(self):
        ref = SpaceRef.parse("owner/name")
        d = ref.to_dict()
        ref2 = SpaceRef.from_dict(d)
        assert ref == ref2

    def test_from_dict_repo_id(self):
        ref = SpaceRef.from_dict({"repo_id": "owner/name"})
        assert ref.owner == "owner"
        assert ref.name == "name"

    def test_str(self):
        ref = SpaceRef.parse("owner/name")
        assert str(ref) == "owner/name"

    def test_parse_space_ref_convenience(self):
        ref = parse_space_ref("owner/name")
        assert isinstance(ref, SpaceRef)

    def test_optional_space_ref_none(self):
        assert optional_space_ref(None) is None
        assert optional_space_ref("") is None

    def test_optional_space_ref_value(self):
        ref = optional_space_ref("owner/name")
        assert ref is not None
        assert ref.owner == "owner"

    def test_frozen_immutability(self):
        ref = SpaceRef.parse("owner/name")
        with pytest.raises((AttributeError, TypeError)):
            ref.owner = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# secrets.py
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.core.secrets import (SecretEntry, SecretsBundle,
                                                 VariableEntry)


class TestSecrets:
    def test_secret_entry_str(self):
        s = SecretEntry(key="MY_KEY")
        assert str(s) == "MY_KEY"

    def test_secret_entry_to_dict_no_value(self):
        s = SecretEntry(key="MY_KEY", description="desc")
        d = s.to_dict()
        assert "value" not in d
        assert d["key"] == "MY_KEY"
        assert d["description"] == "desc"

    def test_secret_entry_from_dict_bare_string(self):
        s = SecretEntry.from_dict("MY_KEY")
        assert s.key == "MY_KEY"

    def test_variable_entry_str(self):
        v = VariableEntry(key="K", value="V")
        assert str(v) == "K=V"

    def test_variable_entry_roundtrip(self):
        v = VariableEntry(key="K", value="V", description="d")
        d = v.to_dict()
        v2 = VariableEntry.from_dict(d)
        assert v2.key == v.key
        assert v2.value == v.value
        assert v2.description == v.description

    def test_variables_from_api(self):
        api_resp = {
            "FOO": {"value": "bar", "description": "a var"},
            "BAZ": {"value": "qux"},
        }
        entries = SecretsBundle.variables_from_api(api_resp)
        assert len(entries) == 2
        keys = {e.key for e in entries}
        assert keys == {"FOO", "BAZ"}

    def test_bundle_has_secret(self):
        bundle = SecretsBundle(secrets=[SecretEntry("KEY1")])
        assert bundle.has_secret("KEY1")
        assert not bundle.has_secret("KEY2")

    def test_bundle_get_variable(self):
        bundle = SecretsBundle(variables=[VariableEntry("K", "V")])
        v = bundle.get_variable("K")
        assert v is not None
        assert v.value == "V"
        assert bundle.get_variable("MISSING") is None


# ---------------------------------------------------------------------------
# session.py
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.core.session import (Session, _locked_save_json,
                                                 delete, list_sessions, load,
                                                 save)


class TestSession:
    def test_new_session_fields(self):
        s = Session.new(space_id="owner/name")
        assert s.space_id == "owner/name"
        assert s.session_id
        assert s.created_at > 0

    def test_push_history_appends(self):
        s = Session.new()
        s.push_history({"cmd": "space info"})
        assert len(s.history) == 1

    def test_push_history_caps_at_max(self):
        from cli_anything.hf_spaces.core.session import MAX_HISTORY

        s = Session.new()
        for i in range(MAX_HISTORY + 10):
            s.push_history({"cmd": f"cmd_{i}"})
        assert len(s.history) == MAX_HISTORY

    def test_to_dict_no_token_field(self):
        s = Session.new()
        d = s.to_dict()
        assert "token" not in d
        assert "_token" not in d

    def test_roundtrip(self):
        s = Session.new(space_id="owner/name")
        s.push_history({"cmd": "test"})
        d = s.to_dict()
        s2 = Session.from_dict(d)
        assert s2.session_id == s.session_id
        assert s2.space_id == s.space_id
        assert len(s2.history) == 1

    def test_save_load_delete(self, tmp_path, monkeypatch):
        import cli_anything.hf_spaces.core.session as sess_mod

        monkeypatch.setattr(sess_mod, "_SESSIONS_DIR", tmp_path)

        s = Session.new(space_id="owner/test")
        save(s)
        loaded = load(s.session_id)
        assert loaded.session_id == s.session_id
        assert delete(s.session_id) is True
        assert delete(s.session_id) is False

    def test_load_not_found_raises(self, tmp_path, monkeypatch):
        import cli_anything.hf_spaces.core.session as sess_mod

        monkeypatch.setattr(sess_mod, "_SESSIONS_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            load("nonexistent-id")

    def test_list_sessions_empty(self, tmp_path, monkeypatch):
        import cli_anything.hf_spaces.core.session as sess_mod

        monkeypatch.setattr(sess_mod, "_SESSIONS_DIR", tmp_path)
        assert list_sessions() == []

    def test_list_sessions_multiple(self, tmp_path, monkeypatch):
        import cli_anything.hf_spaces.core.session as sess_mod

        monkeypatch.setattr(sess_mod, "_SESSIONS_DIR", tmp_path)
        s1 = Session.new()
        s2 = Session.new()
        save(s1)
        save(s2)
        sessions = list_sessions()
        assert len(sessions) == 2

    def test_locked_save_json_atomic(self, tmp_path):
        path = tmp_path / "test.json"
        _locked_save_json(path, {"key": "value"})
        assert path.exists()
        with path.open() as f:
            data = json.load(f)
        assert data["key"] == "value"


# ---------------------------------------------------------------------------
# manifest.py
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.core.manifest import (ChangeKind, ManifestSpec,
                                                  build_plan, plan_hardware,
                                                  plan_readme, plan_secrets,
                                                  plan_sleep_time,
                                                  plan_variables)


class TestManifest:
    def test_validate_ok(self):
        spec = ManifestSpec(space_id="owner/name", hardware="cpu-basic")
        spec.validate()  # should not raise

    def test_validate_bad_space_id(self):
        spec = ManifestSpec(space_id="notaslug")
        with pytest.raises(ValueError, match="space_id"):
            spec.validate()

    def test_validate_bad_hardware(self):
        spec = ManifestSpec(space_id="owner/name", hardware="invalid-tier")
        with pytest.raises(ValueError, match="Unknown hardware"):
            spec.validate()

    def test_validate_bad_sleep_time(self):
        spec = ManifestSpec(space_id="owner/name", sleep_time=-5)
        with pytest.raises(ValueError, match="sleep_time"):
            spec.validate()

    def test_to_dict_roundtrip(self):
        spec = ManifestSpec(
            space_id="owner/name",
            hardware="cpu-basic",
            sleep_time=300,
            variables={"K": "V"},
            secrets=["SECRET"],
        )
        d = spec.to_dict()
        spec2 = ManifestSpec.from_dict(d)
        assert spec2.space_id == spec.space_id
        assert spec2.hardware == spec.hardware
        assert spec2.sleep_time == spec.sleep_time
        assert spec2.variables == spec.variables
        assert spec2.secrets == spec.secrets

    def test_save_load(self, tmp_path):
        spec = ManifestSpec(
            space_id="owner/name",
            hardware="t4-small",
            variables={"KEY": "val"},
        )
        path = tmp_path / "manifest.json"
        spec.save(path)
        loaded = ManifestSpec.load(path)
        assert loaded.space_id == spec.space_id
        assert loaded.hardware == spec.hardware

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ManifestSpec.load(tmp_path / "missing.json")

    def test_plan_hardware_change(self):
        change = plan_hardware("t4-small", "cpu-basic")
        assert change is not None
        assert change.kind == ChangeKind.HARDWARE
        assert change.desired == "t4-small"
        assert change.destructive is True

    def test_plan_hardware_no_change(self):
        assert plan_hardware("cpu-basic", "cpu-basic") is None

    def test_plan_hardware_none_desired(self):
        assert plan_hardware(None, "cpu-basic") is None

    def test_plan_sleep_time_change(self):
        change = plan_sleep_time(300, None)
        assert change is not None
        assert change.kind == ChangeKind.SLEEP_TIME
        assert change.desired == "300"

    def test_plan_sleep_time_no_change(self):
        assert plan_sleep_time(300, 300) is None

    def test_plan_variables_set(self):
        changes = plan_variables({"K": "V"}, {})
        assert len(changes) == 1
        assert changes[0].kind == ChangeKind.VARIABLE_SET
        assert changes[0].key == "K"

    def test_plan_variables_delete(self):
        changes = plan_variables({}, {"K": "V"})
        assert len(changes) == 1
        assert changes[0].kind == ChangeKind.VARIABLE_DELETE
        assert changes[0].destructive is True

    def test_plan_variables_no_change(self):
        assert plan_variables({"K": "V"}, {"K": "V"}) == []

    def test_plan_secrets(self):
        changes = plan_secrets(["KEY1", "KEY2"])
        assert len(changes) == 2
        for c in changes:
            assert c.kind == ChangeKind.SECRET_SET
            assert c.current is None  # unreadable by design

    def test_plan_readme_no_change(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("content", encoding="utf-8")
        change = plan_readme(str(f), "content")
        assert change is None

    def test_plan_readme_change(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("new content", encoding="utf-8")
        change = plan_readme(str(f), "old content")
        assert change is not None
        assert change.kind == ChangeKind.README_SYNC

    def test_build_plan_all(self, tmp_path):
        readme_file = tmp_path / "README.md"
        readme_file.write_text("new", encoding="utf-8")
        spec = ManifestSpec(
            space_id="owner/name",
            hardware="t4-small",
            sleep_time=300,
            variables={"K": "V"},
            secrets=["SECRET"],
            readme_path=str(readme_file),
        )
        changes = build_plan(
            spec=spec,
            current_hardware="cpu-basic",
            current_sleep_time=None,
            current_variables={},
            current_readme="old",
        )
        kinds = {c.kind for c in changes}
        assert ChangeKind.HARDWARE in kinds
        assert ChangeKind.SLEEP_TIME in kinds
        assert ChangeKind.VARIABLE_SET in kinds
        assert ChangeKind.SECRET_SET in kinds
        assert ChangeKind.README_SYNC in kinds


# ---------------------------------------------------------------------------
# hf_backend.py — auth resolution (no live calls)
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.utils.hf_backend import (HfAuthError,
                                                     HfBackendError,
                                                     HfRateLimitError,
                                                     HfSpaceNotFoundError,
                                                     _translate_exc,
                                                     require_token,
                                                     resolve_token)


class TestHfBackendAuth:
    def test_resolve_token_explicit(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        token = resolve_token("explicit-token")
        assert token == "explicit-token"

    def test_resolve_token_env(self, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "env-token")
        token = resolve_token()
        assert token == "env-token"

    def test_resolve_token_none(self, monkeypatch, tmp_path):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        # Patch the cache path to a non-existent location
        import cli_anything.hf_spaces.utils.hf_backend as backend_mod

        monkeypatch.setattr(backend_mod, "_HF_TOKEN_CACHE", tmp_path / "no-token")
        token = resolve_token()
        assert token is None

    def test_require_token_raises_when_none(self, monkeypatch, tmp_path):
        import cli_anything.hf_spaces.utils.hf_backend as backend_mod

        monkeypatch.delenv("HF_TOKEN", raising=False)
        monkeypatch.setattr(backend_mod, "_HF_TOKEN_CACHE", tmp_path / "no-token")
        with pytest.raises(HfAuthError):
            require_token()

    def test_require_token_returns_explicit(self, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        assert require_token("explicit") == "explicit"

    def test_translate_exc_401(self):
        with pytest.raises(HfAuthError):
            _translate_exc(Exception("HTTP 401 Unauthorized"), "owner/name")

    def test_translate_exc_404(self):
        with pytest.raises(HfSpaceNotFoundError):
            _translate_exc(Exception("404 not found"), "owner/name")

    def test_translate_exc_429(self):
        with pytest.raises(HfRateLimitError):
            _translate_exc(Exception("429 rate limit exceeded"))

    def test_translate_exc_generic(self):
        with pytest.raises(HfBackendError):
            _translate_exc(Exception("something went wrong"))

    def test_translate_exc_forbidden(self):
        with pytest.raises(HfAuthError):
            _translate_exc(Exception("403 Forbidden"), "owner/name")

    def test_translate_exc_repository_not_found(self):
        with pytest.raises(HfSpaceNotFoundError):
            _translate_exc(Exception("Repository not found"), "owner/name")


# ---------------------------------------------------------------------------
# CLI root — basic smoke tests via Click test runner
# ---------------------------------------------------------------------------

from cli_anything.hf_spaces.hf_spaces_cli import cli
from click.testing import CliRunner


class TestCLISmoke:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "hf-spaces" in result.output.lower() or "huggingface" in result.output.lower()

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_hardware_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["hardware", "--help"])
        assert result.exit_code == 0

    def test_space_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["space", "--help"])
        assert result.exit_code == 0

    def test_secrets_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["secrets", "--help"])
        assert result.exit_code == 0

    def test_vars_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["vars", "--help"])
        assert result.exit_code == 0

    def test_manifest_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["manifest", "--help"])
        assert result.exit_code == 0

    def test_doctor_no_crash(self):
        runner = CliRunner()
        # doctor may exit 1 (no token in test env) but must not crash
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code in (0, 1)

    def test_hardware_list_tiers(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["hardware", "list-tiers"])
        assert result.exit_code == 0
        assert "cpu-basic" in result.output

    def test_hardware_list_tiers_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "hardware", "list-tiers"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["tiers"]) >= 18

    def test_hardware_set_no_confirm_shows_stop(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["hardware", "set", "owner/name", "t4-small"])
        assert result.exit_code == 0
        assert "[STOP]" in result.output

    def test_space_pause_no_confirm_shows_stop(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["space", "pause", "owner/name"])
        assert result.exit_code == 0
        assert "[STOP]" in result.output

    def test_secrets_delete_no_confirm_shows_stop(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["secrets", "delete", "owner/name", "MY_KEY"])
        assert result.exit_code == 0
        assert "[STOP]" in result.output

    def test_secrets_list_no_manifest(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["secrets", "list"])
        assert result.exit_code == 0
        assert "No secrets found" in result.output or "HuggingFace API" in result.output

    def test_manifest_init_creates_file(self, tmp_path):
        runner = CliRunner()
        out_file = str(tmp_path / "manifest.json")
        result = runner.invoke(
            cli,
            ["manifest", "init", "owner/name", "--out", out_file],
        )
        assert result.exit_code == 0
        assert Path(out_file).exists()
        data = json.loads(Path(out_file).read_text())
        assert data["space_id"] == "owner/name"

    def test_manifest_show(self, tmp_path):
        spec = ManifestSpec(space_id="owner/name", hardware="cpu-basic")
        path = tmp_path / "m.json"
        spec.save(path)
        runner = CliRunner()
        result = runner.invoke(cli, ["manifest", "show", str(path)])
        assert result.exit_code == 0
        assert "owner/name" in result.output

    def test_session_list_empty(self, tmp_path, monkeypatch):
        import cli_anything.hf_spaces.core.session as sess_mod

        monkeypatch.setattr(sess_mod, "_SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["session", "list"])
        assert result.exit_code == 0

    def test_json_flag_propagates(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "hardware", "list-tiers"])
        assert result.exit_code == 0
        # Must be valid JSON
        data = json.loads(result.output)
        assert "tiers" in data
