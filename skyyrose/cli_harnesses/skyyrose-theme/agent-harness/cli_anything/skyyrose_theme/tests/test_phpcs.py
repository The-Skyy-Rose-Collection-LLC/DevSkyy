"""
PHPCS / PHPCBF argv assembly tests.

Covers:
 - run_phpcs produces correct argv shape (phpcs binary, --standard, -s, .)
 - fix=True switches to phpcbf binary
 - Missing vendor/bin/phpcs raises PHPCSNotFoundError with install hint
 - .phpcs.xml present causes --standard flag; absent means no --standard
 - PHP lint raises PHPNotFoundError when php not on PATH
 - run_phpcs uses theme root as cwd
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_theme_root(
    tmp_path: Path, *, with_phpcs: bool = False, with_phpcsxml: bool = False
) -> Path:
    root = tmp_path / "skyyrose-flagship"
    root.mkdir()
    (root / "functions.php").write_text("<?php\ndefine( 'SKYYROSE_VERSION', '1.5.20' );\n")
    (root / "style.css").write_text("/*\nTheme Name: SkyyRose\nVersion: 1.5.20\n*/\n")
    (root / "readme.txt").write_text("=== SkyyRose ===\nStable tag: 1.5.20\n")

    if with_phpcs or with_phpcsxml:
        vendor_bin = root / "vendor" / "bin"
        vendor_bin.mkdir(parents=True)

    if with_phpcs:
        # Create both phpcs and phpcbf stubs
        for name in ("phpcs", "phpcbf"):
            binary = root / "vendor" / "bin" / name
            binary.write_text("#!/bin/bash\necho ok\nexit 0\n")
            binary.chmod(0o755)

    if with_phpcsxml:
        (root / ".phpcs.xml").write_text(
            '<?xml version="1.0"?><ruleset name="SkyyRose"><rule ref="WordPress"/></ruleset>\n'
        )

    return root


# ---------------------------------------------------------------------------
# B. PHPCS / PHPCBF argv assembly (~8 tests)
# ---------------------------------------------------------------------------


class TestPHPCSArgvAssembly:
    def test_run_phpcs_raises_when_binary_missing(self, tmp_path):
        """No vendor/bin/phpcs → PHPCSNotFoundError with install hint."""
        from cli_anything.skyyrose_theme.utils.theme_backend import (
            PHPCSNotFoundError, run_phpcs)

        root = _make_theme_root(tmp_path)
        with pytest.raises(PHPCSNotFoundError) as exc_info:
            run_phpcs(root)
        assert "composer install" in str(exc_info.value)

    def test_run_phpcs_fix_raises_when_phpcbf_missing(self, tmp_path):
        """fix=True looks for phpcbf; same error if missing."""
        from cli_anything.skyyrose_theme.utils.theme_backend import (
            PHPCSNotFoundError, run_phpcs)

        root = _make_theme_root(tmp_path)
        with pytest.raises(PHPCSNotFoundError):
            run_phpcs(root, fix=True)

    def test_run_phpcs_uses_phpcs_binary(self, tmp_path):
        """fix=False invokes phpcs binary, not phpcbf."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root, fix=False)

        assert any("phpcs" in part and "phpcbf" not in part for part in captured_cmd)

    def test_run_phpcs_fix_uses_phpcbf_binary(self, tmp_path):
        """fix=True invokes phpcbf binary."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root, fix=True)

        assert any("phpcbf" in part for part in captured_cmd)

    def test_run_phpcs_with_phpcsxml_includes_standard_flag(self, tmp_path):
        """.phpcs.xml present → --standard=<path> in argv."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root)

        assert any("--standard=" in part for part in captured_cmd)

    def test_run_phpcs_without_phpcsxml_omits_standard_flag(self, tmp_path):
        """No .phpcs.xml → --standard flag absent from argv."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=False)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root)

        assert not any("--standard=" in part for part in captured_cmd)

    def test_run_phpcs_argv_ends_with_dot(self, tmp_path):
        """argv always ends with '.' (theme root as path arg)."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root)

        assert captured_cmd[-1] == "."

    def test_run_phpcs_argv_includes_minus_s_flag(self, tmp_path):
        """argv includes -s (show sniff codes)."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_cmd = []

        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root)

        assert "-s" in captured_cmd

    def test_run_phpcs_cwd_is_theme_root(self, tmp_path):
        """subprocess.run is called with cwd=str(theme_root)."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        captured_kwargs = {}

        def fake_run(cmd, **kwargs):
            captured_kwargs.update(kwargs)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            run_phpcs(root)

        assert captured_kwargs.get("cwd") == str(root)

    def test_run_phpcs_lint_result_fixed_false_for_check(self, tmp_path):
        """LintResult.fixed is False when fix=False."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            result = run_phpcs(root, fix=False)

        assert result.fixed is False

    def test_run_phpcs_lint_result_fixed_true_for_fix(self, tmp_path):
        """LintResult.fixed is True when fix=True."""
        root = _make_theme_root(tmp_path, with_phpcs=True, with_phpcsxml=True)

        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")):
            from cli_anything.skyyrose_theme.utils.theme_backend import \
                run_phpcs

            result = run_phpcs(root, fix=True)

        assert result.fixed is True

    def test_run_php_lint_raises_when_php_missing(self, tmp_path):
        """PHPNotFoundError raised when php not on PATH."""
        from cli_anything.skyyrose_theme.utils.theme_backend import (
            PHPNotFoundError, run_php_lint)

        root = _make_theme_root(tmp_path)
        with patch("shutil.which", return_value=None):
            with pytest.raises(PHPNotFoundError):
                run_php_lint(root)
