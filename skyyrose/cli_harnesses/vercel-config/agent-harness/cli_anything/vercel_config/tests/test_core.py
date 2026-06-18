"""Unit tests for cli-anything-vercel-config core modules.

All tests are offline — no network calls, no real Vercel tokens.
Run with:
    pytest cli_anything/vercel_config/tests/test_core.py -v
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from cli_anything.vercel_config.core.project import (
    ProjectRef,
    build_patch_payload,
    parse_project_ref,
    patchable_fields,
)

# ── project.py ────────────────────────────────────────────────────────


class TestProjectRef:
    def test_id_detection_prj_prefix(self):
        ref = ProjectRef("prj_abc123XYZ")
        assert ref.is_id is True
        assert ref.is_slug is False

    def test_slug_detection(self):
        ref = ProjectRef("my-cool-project")
        assert ref.is_id is False
        assert ref.is_slug is True

    def test_strips_whitespace(self):
        ref = ProjectRef("  my-project  ")
        assert ref.id_or_name == "my-project"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ProjectRef("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ProjectRef("   ")

    def test_team_id_optional(self):
        ref = ProjectRef("my-proj", team_id="team_abc")
        assert ref.team_id == "team_abc"

    def test_str_returns_id_or_name(self):
        ref = ProjectRef("my-proj")
        assert str(ref) == "my-proj"

    def test_parse_project_ref_slug(self):
        ref = parse_project_ref("devskyy")
        assert ref.id_or_name == "devskyy"
        assert ref.is_slug

    def test_parse_project_ref_id(self):
        ref = parse_project_ref("prj_8xfdmzkns13XDOq0hKuju3CdEpWn")
        assert ref.is_id

    def test_parse_project_ref_strips_whitespace(self):
        ref = parse_project_ref("  my-project  ")
        assert ref.id_or_name == "my-project"


class TestBuildPatchPayload:
    def test_filters_unknown_keys(self):
        payload = build_patch_payload({"name": "new-name", "unknownField": "x"})
        assert "name" in payload
        assert "unknownField" not in payload

    def test_raises_when_all_unknown(self):
        with pytest.raises(ValueError, match="No patchable fields"):
            build_patch_payload({"unknownField": "x"})

    def test_known_fields_pass_through(self):
        payload = build_patch_payload({"framework": "nextjs", "nodeVersion": "20.x"})
        assert payload == {"framework": "nextjs", "nodeVersion": "20.x"}

    def test_patchable_fields_returns_sorted_list(self):
        fields = patchable_fields()
        assert isinstance(fields, list)
        assert fields == sorted(fields)
        assert "name" in fields
        assert "framework" in fields


# ── env_vars.py ───────────────────────────────────────────────────────


from cli_anything.vercel_config.core.env_vars import EnvVar, EnvVarDiff, diff_env_vars


class TestEnvVar:
    def test_basic_construction(self):
        ev = EnvVar(key="FOO", value="bar", targets=["production"])
        assert ev.key == "FOO"
        assert ev.value == "bar"

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            EnvVar(key="", value="x")

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError, match="Invalid target"):
            EnvVar(key="K", value="v", targets=["staging"])

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid type"):
            EnvVar(key="K", value="v", env_type="unknown")

    def test_identity_tuple_sorted(self):
        ev = EnvVar(key="K", value="v", targets=["preview", "production"])
        assert ev.identity == ("K", ("preview", "production"))

    def test_masked_value(self):
        ev = EnvVar(key="K", value="secret")
        assert ev.masked_value() == "***"

    def test_display_value_reveal_false(self):
        ev = EnvVar(key="K", value="secret")
        assert ev.display_value(reveal=False) == "***"

    def test_display_value_reveal_true(self):
        ev = EnvVar(key="K", value="secret")
        assert ev.display_value(reveal=True) == "secret"

    def test_to_create_payload(self):
        ev = EnvVar(key="DB", value="postgres://x", targets=["production", "preview"])
        p = ev.to_create_payload()
        assert p["key"] == "DB"
        assert p["value"] == "postgres://x"
        assert "production" in p["target"]
        assert "type" in p

    def test_to_create_payload_with_git_branch(self):
        ev = EnvVar(key="K", value="v", targets=["preview"], git_branch="feat/x")
        p = ev.to_create_payload()
        assert p["gitBranch"] == "feat/x"

    def test_from_api_string_target(self):
        record = {"key": "K", "value": "v", "type": "plain", "target": "production", "id": "abc"}
        ev = EnvVar.from_api(record)
        assert ev.targets == ["production"]
        assert ev.id == "abc"

    def test_from_api_list_target(self):
        record = {"key": "K", "value": "v", "type": "plain", "target": ["preview", "development"]}
        ev = EnvVar.from_api(record)
        assert "preview" in ev.targets

    def test_from_api_unknown_type_defaults_to_plain(self):
        record = {"key": "K", "value": "v", "type": "bogus", "target": ["production"]}
        ev = EnvVar.from_api(record)
        assert ev.env_type == "plain"


class TestDiffEnvVars:
    def _ev(self, key, value="v", targets=None, env_id=None):
        return EnvVar(
            key=key,
            value=value,
            targets=targets or ["production"],
            id=env_id,
        )

    def test_add_new_var(self):
        current = []
        desired = [self._ev("NEW_VAR")]
        diffs = diff_env_vars(current, desired)
        assert any(d.action == "add" and d.key == "NEW_VAR" for d in diffs)

    def test_remove_unlisted_var(self):
        current = [self._ev("OLD_VAR", env_id="id1")]
        desired = []
        diffs = diff_env_vars(current, desired)
        assert any(d.action == "remove" and d.key == "OLD_VAR" for d in diffs)

    def test_unchanged_var(self):
        ev = self._ev("SAME", value="same_value")
        diffs = diff_env_vars([ev], [ev])
        assert any(d.action == "unchanged" and d.key == "SAME" for d in diffs)

    def test_update_on_value_change(self):
        cur = self._ev("K", value="old")
        des = self._ev("K", value="new")
        diffs = diff_env_vars([cur], [des])
        assert any(d.action == "update" and d.key == "K" for d in diffs)

    def test_different_targets_are_distinct_identities(self):
        cur = EnvVar(key="K", value="v", targets=["production"])
        des = EnvVar(key="K", value="v", targets=["preview"])
        diffs = diff_env_vars([cur], [des])
        actions = {d.action for d in diffs}
        assert "add" in actions
        assert "remove" in actions

    def test_results_sorted_by_action_then_key(self):
        current = [self._ev("B", env_id="i1"), self._ev("A", env_id="i2")]
        desired = [self._ev("C")]
        diffs = diff_env_vars(current, desired)
        action_keys = [(d.action, d.key) for d in diffs]
        assert action_keys == sorted(action_keys)


# ── domains.py ───────────────────────────────────────────────────────


from cli_anything.vercel_config.core.domains import Domain, DomainDiff, diff_domains


class TestDomain:
    def test_normalizes_hostname(self):
        d = Domain(name="  WWW.EXAMPLE.COM  ")
        assert d.name == "www.example.com"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            Domain(name="")

    def test_redirect_normalized(self):
        d = Domain(name="example.com", redirect="  WWW.EXAMPLE.COM  ")
        assert d.redirect == "www.example.com"

    def test_empty_redirect_becomes_none(self):
        d = Domain(name="example.com", redirect="   ")
        assert d.redirect is None

    def test_identity_is_name(self):
        d = Domain(name="example.com")
        assert d.identity == "example.com"

    def test_to_add_payload_minimal(self):
        d = Domain(name="example.com")
        p = d.to_add_payload()
        assert p == {"name": "example.com"}

    def test_to_add_payload_with_redirect(self):
        d = Domain(name="example.com", redirect="www.example.com")
        p = d.to_add_payload()
        assert p["redirect"] == "www.example.com"

    def test_from_api(self):
        record = {"name": "example.com", "redirect": "www.example.com", "verified": True}
        d = Domain.from_api(record)
        assert d.name == "example.com"
        assert d.redirect == "www.example.com"
        assert d.verified is True


class TestDiffDomains:
    def test_add_new_domain(self):
        diffs = diff_domains([], [Domain(name="new.example.com")])
        assert any(d.action == "add" and d.name == "new.example.com" for d in diffs)

    def test_remove_unlisted(self):
        diffs = diff_domains([Domain(name="old.example.com")], [])
        assert any(d.action == "remove" and d.name == "old.example.com" for d in diffs)

    def test_unchanged(self):
        dom = Domain(name="same.example.com")
        diffs = diff_domains([dom], [dom])
        assert any(d.action == "unchanged" for d in diffs)

    def test_update_on_redirect_change(self):
        cur = Domain(name="x.example.com", redirect=None)
        des = Domain(name="x.example.com", redirect="www.example.com")
        diffs = diff_domains([cur], [des])
        assert any(d.action == "update" and d.name == "x.example.com" for d in diffs)


# ── manifest.py ───────────────────────────────────────────────────────


from cli_anything.vercel_config.core.manifest import (
    Manifest,
    ManifestPlan,
    build_plan,
    load_manifest,
)


class TestManifest:
    def test_empty_project_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            Manifest(project="")

    def test_to_dict_includes_schema(self):
        m = Manifest(project="my-proj")
        d = m.to_dict()
        assert d["schema"] == "cli-anything-vercel-config/manifest/v1"
        assert d["project"] == "my-proj"

    def test_to_dict_omits_empty_sections(self):
        m = Manifest(project="my-proj")
        d = m.to_dict()
        assert "envVars" not in d
        assert "domains" not in d
        assert "projectPatch" not in d

    def test_save_writes_file(self, tmp_path):
        m = Manifest(project="my-proj")
        out = tmp_path / "vc.json"
        m.save(out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["project"] == "my-proj"


class TestLoadManifest:
    def test_load_minimal(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text(json.dumps({"project": "test-proj"}))
        m = load_manifest(p)
        assert m.project == "test-proj"

    def test_load_missing_project_raises(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text(json.dumps({"envVars": []}))
        with pytest.raises(ValueError, match="missing required field 'project'"):
            load_manifest(p)

    def test_load_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nonexistent.json")

    def test_load_malformed_json(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text("not-json{{")
        with pytest.raises(ValueError, match="JSON parse error"):
            load_manifest(p)

    def test_load_env_vars(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text(
            json.dumps(
                {
                    "project": "proj",
                    "envVars": [
                        {
                            "key": "DB_URL",
                            "value": "postgres://x",
                            "type": "plain",
                            "target": ["production"],
                        }
                    ],
                }
            )
        )
        m = load_manifest(p)
        assert len(m.env_vars) == 1
        assert m.env_vars[0].key == "DB_URL"

    def test_load_domains(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text(
            json.dumps(
                {
                    "project": "proj",
                    "domains": [{"name": "example.com"}],
                }
            )
        )
        m = load_manifest(p)
        assert len(m.domains) == 1
        assert m.domains[0].name == "example.com"

    def test_load_remove_unlisted_flags(self, tmp_path):
        p = tmp_path / "vercel-config.json"
        p.write_text(
            json.dumps(
                {
                    "project": "proj",
                    "removeUnlistedEnv": True,
                    "removeUnlistedDomains": True,
                }
            )
        )
        m = load_manifest(p)
        assert m.remove_unlisted_env is True
        assert m.remove_unlisted_domains is True


class TestBuildPlan:
    def _manifest(self, **kwargs):
        return Manifest(project="test-proj", **kwargs)

    def test_no_changes_when_state_matches(self):
        m = self._manifest()
        plan = build_plan(m, {"name": "test-proj"}, [], [])
        assert plan.has_changes is False

    def test_project_patch_detects_diff(self):
        m = self._manifest(project_patch={"framework": "nextjs"})
        actual = {"framework": "remix"}
        plan = build_plan(m, actual, [], [])
        assert "framework" in plan.project_patch

    def test_project_patch_no_change_when_already_set(self):
        m = self._manifest(project_patch={"framework": "nextjs"})
        actual = {"framework": "nextjs"}
        plan = build_plan(m, actual, [], [])
        assert "framework" not in plan.project_patch

    def test_env_add_propagates(self):
        m = self._manifest(env_vars=[EnvVar(key="NEW", value="v")])
        plan = build_plan(m, {}, [], [])
        assert any(d.action == "add" and d.key == "NEW" for d in plan.env_diffs)

    def test_remove_unlisted_false_excludes_removes(self):
        existing_ev = EnvVar(key="ORPHAN", value="v", id="id1")
        m = self._manifest(remove_unlisted_env=False)
        plan = build_plan(m, {}, [existing_ev], [])
        assert not any(d.action == "remove" for d in plan.env_diffs)

    def test_remove_unlisted_true_includes_removes(self):
        existing_ev = EnvVar(key="ORPHAN", value="v", id="id1")
        m = self._manifest(remove_unlisted_env=True)
        plan = build_plan(m, {}, [existing_ev], [])
        assert any(d.action == "remove" and d.key == "ORPHAN" for d in plan.env_diffs)

    def test_plan_to_dict_serializable(self):
        m = self._manifest(env_vars=[EnvVar(key="K", value="v")])
        plan = build_plan(m, {}, [], [])
        d = plan.to_dict()
        assert "hasChanges" in d
        json.dumps(d)  # must be JSON-serializable


# ── session.py ───────────────────────────────────────────────────────


from cli_anything.vercel_config.core.session import (
    Session,
    _locked_save_json,
    delete,
    list_sessions,
    load,
    save,
)


class TestSession:
    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name must not be empty"):
            Session(name="", project="proj")

    def test_empty_project_raises(self):
        with pytest.raises(ValueError, match="project must not be empty"):
            Session(name="s", project="")

    def test_push_history(self):
        s = Session(name="s", project="p")
        s.push_history("env list myproj")
        assert "env list myproj" in s.history

    def test_push_history_caps_at_max(self):
        from cli_anything.vercel_config.core.session import MAX_HISTORY

        s = Session(name="s", project="p")
        for i in range(MAX_HISTORY + 10):
            s.push_history(f"cmd {i}")
        assert len(s.history) == MAX_HISTORY

    def test_to_dict_round_trip(self):
        s = Session(name="test", project="my-proj", team_id="team_x")
        d = s.to_dict()
        s2 = Session.from_dict(d)
        assert s2.name == s.name
        assert s2.project == s.project
        assert s2.team_id == s.team_id

    def test_schema_in_dict(self):
        s = Session(name="s", project="p")
        assert "schema" in s.to_dict()


class TestSessionPersistence:
    def test_save_and_load(self, tmp_path):
        s = Session(name="mysession", project="my-proj")
        save(s, sessions_dir=tmp_path)
        s2 = load("mysession", sessions_dir=tmp_path)
        assert s2.project == "my-proj"

    def test_load_nonexistent_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load("nope", sessions_dir=tmp_path)

    def test_delete_existing(self, tmp_path):
        s = Session(name="todel", project="p")
        save(s, sessions_dir=tmp_path)
        result = delete("todel", sessions_dir=tmp_path)
        assert result is True

    def test_delete_nonexistent_returns_false(self, tmp_path):
        result = delete("nope", sessions_dir=tmp_path)
        assert result is False

    def test_list_sessions_empty(self, tmp_path):
        sessions = list_sessions(sessions_dir=tmp_path)
        assert sessions == []

    def test_list_sessions_multiple(self, tmp_path):
        for name in ("alpha", "beta", "gamma"):
            s = Session(name=name, project="proj")
            save(s, sessions_dir=tmp_path)
        sessions = list_sessions(sessions_dir=tmp_path)
        assert len(sessions) == 3

    def test_list_sessions_skips_corrupt(self, tmp_path):
        (tmp_path / "corrupt.json").write_text("not json{{")
        sessions = list_sessions(sessions_dir=tmp_path)
        assert sessions == []


class TestLockedSaveJson:
    def test_writes_valid_json(self, tmp_path):
        p = tmp_path / "sub" / "data.json"
        _locked_save_json(p, {"key": "value"})
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["key"] == "value"

    def test_creates_parent_dirs(self, tmp_path):
        p = tmp_path / "a" / "b" / "c" / "data.json"
        _locked_save_json(p, {"x": 1})
        assert p.exists()

    def test_atomic_overwrite(self, tmp_path):
        p = tmp_path / "data.json"
        _locked_save_json(p, {"v": 1})
        _locked_save_json(p, {"v": 2})
        data = json.loads(p.read_text())
        assert data["v"] == 2


# ── vercel_backend.py — resolve_token ────────────────────────────────


from cli_anything.vercel_config.utils.vercel_backend import (
    VercelAuthError,
    VercelBackend,
    VercelBackendError,
    VercelNotFoundError,
    VercelRateLimitedError,
    VercelValidationError,
    _confirm,
    resolve_token,
)


class TestResolveToken:
    def test_explicit_token_wins(self):
        assert resolve_token("mytoken") == "mytoken"

    def test_env_var_used_when_no_explicit(self, monkeypatch):
        monkeypatch.setenv("VERCEL_TOKEN", "env_token")
        assert resolve_token() == "env_token"

    def test_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("VERCEL_TOKEN", "env_token")
        assert resolve_token("explicit_token") == "explicit_token"

    def test_raises_when_no_token(self, monkeypatch, tmp_path):
        monkeypatch.delenv("VERCEL_TOKEN", raising=False)
        # Patch auth paths to nonexistent locations
        with patch(
            "cli_anything.vercel_config.utils.vercel_backend._AUTH_JSON_PATHS",
            [tmp_path / "nonexistent.json"],
        ):
            with pytest.raises(VercelAuthError):
                resolve_token()

    def test_reads_token_from_auth_json(self, tmp_path, monkeypatch):
        monkeypatch.delenv("VERCEL_TOKEN", raising=False)
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(json.dumps({"token": "file_token"}))
        with patch(
            "cli_anything.vercel_config.utils.vercel_backend._AUTH_JSON_PATHS",
            [auth_file],
        ):
            assert resolve_token() == "file_token"

    def test_reads_access_token_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("VERCEL_TOKEN", raising=False)
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(json.dumps({"access_token": "at_token"}))
        with patch(
            "cli_anything.vercel_config.utils.vercel_backend._AUTH_JSON_PATHS",
            [auth_file],
        ):
            assert resolve_token() == "at_token"

    def test_skips_corrupt_auth_json(self, tmp_path, monkeypatch):
        monkeypatch.delenv("VERCEL_TOKEN", raising=False)
        auth_file = tmp_path / "auth.json"
        auth_file.write_text("not valid json{{")
        with patch(
            "cli_anything.vercel_config.utils.vercel_backend._AUTH_JSON_PATHS",
            [auth_file],
        ):
            with pytest.raises(VercelAuthError):
                resolve_token()


class TestVercelBackendErrors:
    """Test typed exception raising via _raise_for_status."""

    def _make_backend(self):
        return VercelBackend(token="fake_token")

    def _mock_response(self, status_code: int, body: dict | None = None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.content = b"x"
        if body is not None:
            resp.json.return_value = body
        else:
            resp.json.return_value = {}
        resp.headers = {}
        return resp

    def test_401_raises_auth_error(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = self._mock_response(401, {"error": {"message": "bad token"}})
        with pytest.raises(VercelAuthError):
            _raise_for_status(resp, "/v9/projects/x")

    def test_404_raises_not_found(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = self._mock_response(404, {"error": {"message": "not found"}})
        with pytest.raises(VercelNotFoundError):
            _raise_for_status(resp, "/v9/projects/x")

    def test_400_raises_validation_error(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = self._mock_response(400, {"error": {"message": "bad input"}})
        with pytest.raises(VercelValidationError):
            _raise_for_status(resp, "/v9/projects/x")

    def test_500_raises_backend_error(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = self._mock_response(500, {"error": {"message": "server error"}})
        with pytest.raises(VercelBackendError):
            _raise_for_status(resp, "/v9/projects/x")

    def test_200_returns_dict(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = self._mock_response(200, {"id": "prj_abc"})
        result = _raise_for_status(resp, "/v9/projects/x")
        assert result["id"] == "prj_abc"

    def test_204_returns_empty_dict(self):
        from cli_anything.vercel_config.utils.vercel_backend import _raise_for_status

        resp = MagicMock()
        resp.status_code = 204
        resp.content = b""
        result = _raise_for_status(resp, "/v9/projects/x/env/id")
        assert result == {}


class TestVercelBackend429Retry:
    """Test exponential backoff on 429 responses."""

    def test_retries_on_429_then_succeeds(self):
        import requests

        backend = VercelBackend(token="tok")
        call_count = 0

        def mock_request(**kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.headers = {"Retry-After": "0"}
            if call_count < 3:
                resp.status_code = 429
                resp.content = b"rate limited"
                resp.json.return_value = {}
            else:
                resp.status_code = 200
                resp.content = b'{"id":"prj_x"}'
                resp.json.return_value = {"id": "prj_x"}
            return resp

        backend._session.request = mock_request
        with patch("time.sleep"):
            result = backend._request("GET", "/v9/projects/test")
        assert result["id"] == "prj_x"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        backend = VercelBackend(token="tok")

        def mock_request(**kwargs):
            resp = MagicMock()
            resp.status_code = 429
            resp.headers = {"Retry-After": "0"}
            resp.content = b"rate limited"
            resp.json.return_value = {}
            return resp

        backend._session.request = mock_request
        with patch("time.sleep"):
            with pytest.raises(VercelRateLimitedError):
                backend._request("GET", "/v9/projects/test")
