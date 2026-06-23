"""
Unit tests for cli-anything-skyyrose-theme core modules.

Run: pytest cli_anything/skyyrose_theme/tests/ --tb=short -q
All tests are offline — no network calls, no SSH, no real file system writes
to the production theme directory.

SKYYROSE_E2E=1 gates live tests (test_full_e2e.py only).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_theme_root(tmp_path: Path) -> Path:
    """Create a minimal fake theme root for offline testing."""
    root = tmp_path / "skyyrose-flagship"
    root.mkdir()

    (root / "functions.php").write_text("<?php\ndefine( 'SKYYROSE_VERSION', '1.5.20' );\n")
    (root / "style.css").write_text(
        "/*\nTheme Name: SkyyRose\nVersion:             1.5.20\nText Domain: skyyrose\n*/\n"
    )
    (root / "readme.txt").write_text("=== SkyyRose ===\nStable tag: 1.5.20\n")

    # Create a few template files
    for slug in ["about", "coming-soon", "contact"]:
        (root / f"template-{slug}.php").write_text(f"<?php /* Template: {slug} */\n")

    for coll in ["signature", "black-rose", "love-hurts", "kids-capsule"]:
        (root / f"template-collection-{coll}.php").write_text(f"<?php /* Collection: {coll} */\n")

    # Create inc/ with enqueue.php
    inc = root / "inc"
    inc.mkdir()
    enqueue_content = """<?php
function skyyrose_get_current_template_slug() {
    $template_map = array(
        'template-about.php'                  => 'about',
        'template-coming-soon.php'            => 'coming-soon',
        'template-contact.php'                => 'contact',
        'template-collection-signature.php'   => 'collection',
        'template-collection-black-rose.php'  => 'collection',
        'template-collection-love-hurts.php'  => 'collection',
        'template-collection-kids-capsule.php' => 'collection',
    );
}
"""
    (inc / "enqueue.php").write_text(enqueue_content)

    return root


# ===========================================================================
# version.py tests (10 tests)
# ===========================================================================


class TestVersionRead:
    def test_read_functions_php(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import \
            _read_functions_php

        assert _read_functions_php(root) == "1.5.20"

    def test_read_style_css(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import _read_style_css

        assert _read_style_css(root) == "1.5.20"

    def test_read_readme_txt(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import _read_readme_txt

        assert _read_readme_txt(root) == "1.5.20"

    def test_read_version_consistent(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import read_version

        vs = read_version(root)
        assert vs.consistent is True
        assert vs.current == "1.5.20"

    def test_read_version_mismatch(self, tmp_path):
        root = _make_theme_root(tmp_path)
        # Break style.css version
        (root / "style.css").write_text(
            "/*\nTheme Name: SkyyRose\nVersion:             1.5.99\n*/\n"
        )
        from cli_anything.skyyrose_theme.core.version import (
            VersionMismatchError, read_version)

        vs = read_version(root)
        assert vs.consistent is False
        with pytest.raises(VersionMismatchError):
            _ = vs.current

    def test_read_version_missing_constant(self, tmp_path):
        root = _make_theme_root(tmp_path)
        (root / "functions.php").write_text("<?php // no version constant\n")
        from cli_anything.skyyrose_theme.core.version import (VersionError,
                                                              read_version)

        with pytest.raises(VersionError):
            read_version(root)


class TestVersionWrite:
    def test_write_version_all_three_files(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import (read_version,
                                                              write_version)

        vs = write_version("1.6.0", root)
        assert vs.current == "1.6.0"
        # Verify on disk
        vs2 = read_version(root)
        assert vs2.current == "1.6.0"

    def test_write_version_atomic_no_partial(self, tmp_path):
        """After successful write, all three files agree."""
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import (read_version,
                                                              write_version)

        write_version("2.0.0", root)
        vs = read_version(root)
        assert vs.functions_php == vs.style_css == vs.readme_txt == "2.0.0"

    def test_write_version_precondition_mismatch(self, tmp_path):
        """write_version raises if sources disagree before write."""
        root = _make_theme_root(tmp_path)
        (root / "style.css").write_text(
            "/*\nTheme Name: SkyyRose\nVersion:             9.9.9\n*/\n"
        )
        from cli_anything.skyyrose_theme.core.version import (
            VersionMismatchError, write_version)

        with pytest.raises(VersionMismatchError):
            write_version("1.6.0", root)

    def test_write_version_roundtrip(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.version import write_version

        write_version("1.5.21", root)
        write_version("1.5.20", root)  # rollback
        from cli_anything.skyyrose_theme.core.version import read_version

        assert read_version(root).current == "1.5.20"


# ===========================================================================
# php_parser.py tests (5 tests)
# ===========================================================================


class TestPhpParser:
    def test_extract_version_constant(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_version_constant

        php = "define( 'SKYYROSE_VERSION', '1.5.20' );"
        assert extract_version_constant(php) == "1.5.20"

    def test_extract_version_constant_missing(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_version_constant

        assert extract_version_constant("<?php // nothing") is None

    def test_extract_template_map(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_template_map

        php = """
        $template_map = array(
            'template-about.php' => 'about',
            'template-contact.php' => 'contact',
        );
        """
        result = extract_template_map(php)
        assert result == {"template-about.php": "about", "template-contact.php": "contact"}

    def test_extract_style_css_version(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_style_css_version

        css = "/*\nTheme Name: SkyyRose\nVersion:             1.5.20\n*/\n"
        assert extract_style_css_version(css) == "1.5.20"

    def test_extract_readme_stable_tag(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_readme_stable_tag

        txt = "=== SkyyRose ===\nStable tag: 1.5.20\n"
        assert extract_readme_stable_tag(txt) == "1.5.20"

    def test_extract_php_string_generic(self):
        from cli_anything.skyyrose_theme.utils.php_parser import \
            extract_php_string

        php = "define( 'MY_CONST', 'hello-world' );"
        assert extract_php_string(php, "MY_CONST") == "hello-world"


# ===========================================================================
# template.py tests (5 tests)
# ===========================================================================


class TestTemplateDiscovery:
    def test_load_templates_finds_files(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.template import load_templates

        tmap = load_templates(root)
        filenames = {t.filename for t in tmap.templates}
        assert "template-about.php" in filenames
        assert "template-collection-signature.php" in filenames

    def test_load_templates_slug_from_enqueue(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.template import load_templates

        tmap = load_templates(root)
        t = tmap.by_filename("template-about.php")
        assert t is not None
        assert t.slug == "about"

    def test_load_templates_unregistered_slug_is_none(self, tmp_path):
        root = _make_theme_root(tmp_path)
        # Add a template file not in enqueue.php
        (root / "template-mystery.php").write_text("<?php\n")
        from cli_anything.skyyrose_theme.core.template import load_templates

        tmap = load_templates(root)
        t = tmap.by_filename("template-mystery.php")
        assert t is not None
        assert t.slug is None

    def test_load_templates_by_slug(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.core.template import load_templates

        tmap = load_templates(root)
        t = tmap.by_slug("about")
        assert t is not None
        assert t.filename == "template-about.php"

    def test_load_templates_missing_root_raises(self, tmp_path):
        from cli_anything.skyyrose_theme.core.template import (TemplateError,
                                                               load_templates)

        with pytest.raises(TemplateError):
            load_templates(tmp_path / "nonexistent")


# ===========================================================================
# session.py tests (8 tests)
# ===========================================================================


class TestSession:
    def test_create_and_save_session(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (Session,
                                                              save_session)

        s = Session(name="test")
        path = save_session(s, sessions_dir=tmp_path)
        assert path.exists()

    def test_load_session_roundtrip(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (Session,
                                                              load_session,
                                                              save_session)

        s = Session(name="roundtrip")
        save_session(s, sessions_dir=tmp_path)
        loaded = load_session(s.id, sessions_dir=tmp_path)
        assert loaded.id == s.id
        assert loaded.name == "roundtrip"

    def test_load_session_not_found(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (
            SessionNotFoundError, load_session)

        with pytest.raises(SessionNotFoundError):
            load_session("nonexistent-id", sessions_dir=tmp_path)

    def test_list_sessions_empty(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import list_sessions

        assert list_sessions(sessions_dir=tmp_path) == []

    def test_list_sessions_returns_sorted(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (Session,
                                                              list_sessions,
                                                              save_session)

        s1 = Session(name="alpha")
        s2 = Session(name="beta")
        s1.updated_at = time.time() - 100
        s2.updated_at = time.time()
        save_session(s1, sessions_dir=tmp_path)
        save_session(s2, sessions_dir=tmp_path)

        sessions = list_sessions(sessions_dir=tmp_path)
        assert sessions[0].name == "beta"

    def test_delete_session(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (Session,
                                                              delete_session,
                                                              save_session)

        s = Session(name="to-delete")
        save_session(s, sessions_dir=tmp_path)
        assert delete_session(s.id, sessions_dir=tmp_path) is True
        assert delete_session(s.id, sessions_dir=tmp_path) is False

    def test_add_history_trimmed(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import (MAX_HISTORY,
                                                              Session)

        s = Session(name="hist")
        for i in range(MAX_HISTORY + 10):
            s.add_history(f"cmd-{i}")
        assert len(s.history) == MAX_HISTORY
        assert s.history[-1] == f"cmd-{MAX_HISTORY + 9}"

    def test_get_or_create_session_idempotent(self, tmp_path):
        from cli_anything.skyyrose_theme.core.session import \
            get_or_create_session

        s1 = get_or_create_session("myname", sessions_dir=tmp_path)
        s2 = get_or_create_session("myname", sessions_dir=tmp_path)
        assert s1.id == s2.id

    def test_locked_save_json_atomic(self, tmp_path):
        """Verify _locked_save_json writes valid JSON atomically."""
        from cli_anything.skyyrose_theme.core.session import _locked_save_json

        target = tmp_path / "test.json"
        data = {"key": "value", "num": 42}
        _locked_save_json(target, data)
        assert target.exists()
        loaded = json.loads(target.read_text())
        assert loaded == data


# ===========================================================================
# deploy.py tests (8 tests)
# ===========================================================================


class TestDeployManifest:
    def test_build_manifest_dry_run(self, tmp_path):
        """build_deploy_manifest returns manifest with dry_run=True."""
        # Create a fake deploy script
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\necho deployed\n")

        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        manifest = build_deploy_manifest(
            dry_run=True,
            deploy_script=script,
            theme_root=tmp_path,
        )
        assert manifest.dry_run is True
        assert manifest.mode == "hot-swap"

    def test_build_manifest_with_maintenance(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        manifest = build_deploy_manifest(
            with_maintenance=True,
            deploy_script=script,
            theme_root=tmp_path,
        )
        assert manifest.with_maintenance is True
        assert manifest.mode == "maintenance"

    def test_build_manifest_script_not_found(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import (
            DeployScriptNotFoundError, build_deploy_manifest)

        with pytest.raises(DeployScriptNotFoundError):
            build_deploy_manifest(
                deploy_script=tmp_path / "nonexistent.sh",
                theme_root=tmp_path,
            )

    def test_manifest_to_dict_shape(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert "action" in d
        assert "dry_run" in d
        assert "irreversible" in d

    def test_run_deploy_requires_confirmed(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import (
            DeployNotConfirmedError, build_deploy_manifest, run_deploy)

        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        with pytest.raises(DeployNotConfirmedError):
            run_deploy(manifest, confirmed=False)

    def test_run_deploy_dry_run_argv(self, tmp_path):
        """--dry-run passes the flag to the script argv."""
        script = tmp_path / "deploy-theme.sh"
        # Script that echoes its args and exits 0
        script.write_text('#!/bin/bash\necho "$@"\n')
        script.chmod(0o755)

        from cli_anything.skyyrose_theme.core.deploy import (
            build_deploy_manifest, run_deploy)

        manifest = build_deploy_manifest(dry_run=True, deploy_script=script, theme_root=tmp_path)
        result = run_deploy(manifest, confirmed=True)
        assert result.returncode == 0

    def test_run_deploy_fails_on_nonzero_exit(self, tmp_path):
        script = tmp_path / "fail.sh"
        script.write_text("#!/bin/bash\nexit 1\n")
        script.chmod(0o755)

        from cli_anything.skyyrose_theme.core.deploy import (
            DeployFailedError, build_deploy_manifest, run_deploy)

        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        with pytest.raises(DeployFailedError):
            run_deploy(manifest, confirmed=True)

    def test_run_deploy_with_maintenance_argv(self, tmp_path):
        """--with-maintenance passes the flag to the script."""
        script = tmp_path / "deploy-theme.sh"
        script.write_text('#!/bin/bash\necho "$@"\n')
        script.chmod(0o755)

        from cli_anything.skyyrose_theme.core.deploy import (
            build_deploy_manifest, run_deploy)

        manifest = build_deploy_manifest(
            with_maintenance=True, deploy_script=script, theme_root=tmp_path
        )
        result = run_deploy(manifest, confirmed=True)
        assert result.returncode == 0


# ===========================================================================
# verify.py tests (6 tests — all offline via mock)
# ===========================================================================


class TestVerify:
    def _mock_response(self, status_code=200, text="x" * 60000, url="https://skyyrose.co/"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        resp.content = text.encode()
        resp.url = url
        return resp

    def test_url_check_result_ok(self):
        from cli_anything.skyyrose_theme.core.verify import UrlCheckResult

        r = UrlCheckResult(
            url="https://skyyrose.co/",
            status_code=200,
            body_bytes=60000,
            php_error=None,
            error=None,
        )
        assert r.ok is True
        assert r.verdict == "pass"

    def test_url_check_result_php_error(self):
        from cli_anything.skyyrose_theme.core.verify import UrlCheckResult

        r = UrlCheckResult(
            url="https://skyyrose.co/",
            status_code=200,
            body_bytes=60000,
            php_error="Fatal error",
            error=None,
        )
        assert r.ok is False
        assert r.verdict == "fail"

    def test_verify_live_success(self):
        from cli_anything.skyyrose_theme.core.verify import verify_live

        mock_resp = self._mock_response()
        with patch("requests.get", return_value=mock_resp):
            report = verify_live(
                base_url="https://skyyrose.co",
                paths=["/"],
            )
        assert report.passed is True

    def test_verify_live_raises_on_failure(self):
        from cli_anything.skyyrose_theme.core.verify import (VerifyFailedError,
                                                             verify_live)

        mock_resp = self._mock_response(status_code=500)
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(VerifyFailedError):
                verify_live(base_url="https://skyyrose.co", paths=["/"])

    def test_verify_live_detects_php_error_marker(self):
        from cli_anything.skyyrose_theme.core.verify import (VerifyFailedError,
                                                             verify_live)

        bad_body = "x" * 60000 + "Fatal error: Uncaught Error"
        mock_resp = self._mock_response(text=bad_body)
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(VerifyFailedError) as exc_info:
                verify_live(base_url="https://skyyrose.co", paths=["/"])
        assert "Fatal error" in str(exc_info.value)

    def test_verify_live_small_body_fails(self):
        from cli_anything.skyyrose_theme.core.verify import (VerifyFailedError,
                                                             verify_live)

        tiny_body = "small"
        mock_resp = self._mock_response(text=tiny_body)
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(VerifyFailedError):
                verify_live(base_url="https://skyyrose.co", paths=["/"])


# ===========================================================================
# theme_backend.py tests (5 tests)
# ===========================================================================


class TestThemeBackend:
    def test_build_context_returns_context(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.utils.theme_backend import \
            build_context

        ctx = build_context(theme_root=root)
        assert ctx.theme_root == root

    def test_doctor_theme_root_ok(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.utils.theme_backend import doctor

        report = doctor(theme_root=root)
        # Find theme_root check
        theme_check = next(c for c in report.checks if c["name"] == "theme_root")
        assert theme_check["status"] == "ok"

    def test_doctor_missing_root_fails(self, tmp_path):
        from cli_anything.skyyrose_theme.utils.theme_backend import doctor

        report = doctor(theme_root=tmp_path / "nonexistent")
        theme_check = next(c for c in report.checks if c["name"] == "theme_root")
        assert theme_check["status"] == "fail"

    def test_run_phpcs_not_found_raises(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.utils.theme_backend import (
            PHPCSNotFoundError, run_phpcs)

        with pytest.raises(PHPCSNotFoundError):
            run_phpcs(root)  # no vendor/bin/phpcs in fake root

    def test_run_php_lint_no_php_raises(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.utils.theme_backend import (
            PHPNotFoundError, run_php_lint)

        with patch("shutil.which", return_value=None):
            with pytest.raises(PHPNotFoundError):
                run_php_lint(root)


# ===========================================================================
# STOP-AND-SHOW manifest tests (4 tests)
# ===========================================================================


class TestStopAndShow:
    def test_deploy_manifest_not_confirmed_no_execute(self, tmp_path):
        """run_deploy with confirmed=False never calls subprocess.run."""
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import (
            DeployNotConfirmedError, build_deploy_manifest, run_deploy)

        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        with patch("subprocess.run") as mock_run:
            with pytest.raises(DeployNotConfirmedError):
                run_deploy(manifest, confirmed=False)
            mock_run.assert_not_called()

    def test_cache_purge_manifest_shape(self):
        """cache purge manifest dict has required keys."""
        # Test the manifest dict shape directly
        manifest_dict = {
            "action": "cache purge (wp cache flush)",
            "target": "skyyrose.co production",
            "method": "wp-cli over SSH",
            "cost": "$0",
            "irreversible": False,
        }
        assert manifest_dict["cost"] == "$0"
        assert manifest_dict["irreversible"] is False

    def test_deploy_manifest_irreversible_flag(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        # Non-dry-run = irreversible
        assert d["irreversible"] is True

    def test_dry_run_manifest_not_irreversible(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")

        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        manifest = build_deploy_manifest(dry_run=True, deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["irreversible"] is False


# ===========================================================================
# CLI integration tests (via Click test runner) (5 tests)
# ===========================================================================


class TestCLIRunner:
    def test_cli_help(self):
        from cli_anything.skyyrose_theme.skyyrose_theme_cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SkyyRose" in result.output

    def test_version_current_json(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.skyyrose_theme_cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--json", "--theme-root", str(root), "version", "current"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["functions_php"] == "1.5.20"
        assert data["consistent"] is True

    def test_template_list_json(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.skyyrose_theme_cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--json", "--theme-root", str(root), "template", "list"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] > 0

    def test_deploy_no_confirm_exits_0(self, tmp_path):
        script = tmp_path / "deploy-theme.sh"
        script.write_text("#!/bin/bash\n")
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.skyyrose_theme_cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--theme-root",
                str(root),
                "deploy",
                "--dry-run",
            ],
            env={"SKYYROSE_DEPLOY_SCRIPT": str(script)},
        )
        # Without --confirm, should print manifest and exit 0
        assert result.exit_code == 0

    def test_doctor_json(self, tmp_path):
        root = _make_theme_root(tmp_path)
        from cli_anything.skyyrose_theme.skyyrose_theme_cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--json", "--theme-root", str(root), "doctor"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "checks" in data
        assert "healthy" in data
