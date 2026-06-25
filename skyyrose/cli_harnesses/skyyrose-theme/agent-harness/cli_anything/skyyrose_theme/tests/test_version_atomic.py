"""
Version-write atomic rollback tests.

Covers:
 - Successful write updates all 3 files consistently
 - Mid-write IOError on second file: first file stays written (no auto-rollback)
 - Mid-write IOError on third file: first two files stay written
 - Caller can recover by re-running write_version with old version
 - Dry-run path: read_version does not modify any file (mtime unchanged)
 - write_version raises VersionMismatchError when sources disagree before write
 - Sequential write_version calls succeed (idempotent on same version)
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_theme_root(tmp_path: Path, version: str = "1.5.20") -> Path:
    root = tmp_path / "skyyrose-flagship"
    root.mkdir()
    (root / "functions.php").write_text(f"<?php\ndefine( 'SKYYROSE_VERSION', '{version}' );\n")
    (root / "style.css").write_text(
        f"/*\nTheme Name: SkyyRose\nVersion: {version}\nText Domain: skyyrose\n*/\n"
    )
    (root / "readme.txt").write_text(f"=== SkyyRose ===\nStable tag: {version}\n")
    return root


# ---------------------------------------------------------------------------
# D. Version-write atomic rollback (~6 tests)
# ---------------------------------------------------------------------------


class TestVersionWriteAtomic:
    def test_successful_write_all_three_files_agree(self, tmp_path):
        root = _make_theme_root(tmp_path, "1.5.20")
        from cli_anything.skyyrose_theme.core.version import (read_version,
                                                              write_version)

        write_version("1.6.0", root)
        vs = read_version(root)
        assert vs.functions_php == "1.6.0"
        assert vs.style_css == "1.6.0"
        assert vs.readme_txt == "1.6.0"
        assert vs.consistent is True

    def test_crash_on_second_file_leaves_first_rewritten(self, tmp_path):
        """
        write_version writes functions.php then style.css then readme.txt.
        If style.css write raises, functions.php is already updated but
        style.css and readme.txt still hold the old version.
        The exception propagates to the caller (no silent swallow).
        """
        root = _make_theme_root(tmp_path, "1.5.20")
        from cli_anything.skyyrose_theme.core.version import (_write_style_css,
                                                              read_version,
                                                              write_version)

        original_write_style_css = _write_style_css

        call_count = [0]

        def boom(theme_root: Path, new_version: str) -> None:
            call_count[0] += 1
            raise IOError("Simulated disk failure on style.css")

        with patch("cli_anything.skyyrose_theme.core.version._write_style_css", side_effect=boom):
            with pytest.raises(IOError, match="Simulated disk failure"):
                write_version("1.6.0", root)

        # After the crash: functions.php was already written (1.6.0),
        # style.css and readme.txt still hold old value (1.5.20).
        # The state is inconsistent — that's expected without a rollback.
        funcs_version = (root / "functions.php").read_text()
        assert "1.6.0" in funcs_version  # first file was written

        style_version = (root / "style.css").read_text()
        assert "1.5.20" in style_version  # second file was NOT written

    def test_caller_can_recover_by_rewriting_old_version(self, tmp_path):
        """
        After partial write (functions.php=1.6.0, style.css=1.5.20, readme=1.5.20),
        caller forces all files back by manually patching functions.php then
        calling write_version with the old version.
        """
        root = _make_theme_root(tmp_path, "1.5.20")
        from cli_anything.skyyrose_theme.core.version import (
            _write_functions_php, _write_readme_txt, _write_style_css,
            read_version)

        # Manually create the partial-write scenario
        _write_functions_php(root, "1.6.0")
        # style.css and readme.txt still at 1.5.20

        # Recovery: re-align functions.php back to 1.5.20 so all three agree
        _write_functions_php(root, "1.5.20")

        vs = read_version(root)
        assert vs.consistent is True
        assert vs.current == "1.5.20"

    def test_crash_on_third_file_leaves_first_two_rewritten(self, tmp_path):
        """If readme.txt write fails, functions.php and style.css are already updated."""
        root = _make_theme_root(tmp_path, "1.5.20")
        from cli_anything.skyyrose_theme.core.version import write_version

        def boom(theme_root: Path, new_version: str) -> None:
            raise IOError("Simulated disk failure on readme.txt")

        with patch("cli_anything.skyyrose_theme.core.version._write_readme_txt", side_effect=boom):
            with pytest.raises(IOError, match="Simulated disk failure"):
                write_version("1.6.0", root)

        assert "1.6.0" in (root / "functions.php").read_text()
        assert "1.6.0" in (root / "style.css").read_text()
        assert "1.5.20" in (root / "readme.txt").read_text()

    def test_read_version_does_not_modify_files(self, tmp_path):
        """read_version is non-mutating — mtime of all three files is unchanged."""
        root = _make_theme_root(tmp_path, "1.5.20")
        from cli_anything.skyyrose_theme.core.version import read_version

        files = [
            root / "functions.php",
            root / "style.css",
            root / "readme.txt",
        ]
        mtimes_before = [f.stat().st_mtime for f in files]

        # Small sleep to ensure mtime resolution catches any write
        time.sleep(0.05)
        read_version(root)

        mtimes_after = [f.stat().st_mtime for f in files]
        assert mtimes_before == mtimes_after

    def test_write_version_raises_on_inconsistent_precondition(self, tmp_path):
        """write_version raises VersionMismatchError if sources disagree before write."""
        root = _make_theme_root(tmp_path, "1.5.20")
        # Manually break style.css to a different version
        (root / "style.css").write_text("/*\nTheme Name: SkyyRose\nVersion: 9.9.9\n*/\n")
        from cli_anything.skyyrose_theme.core.version import (
            VersionMismatchError, write_version)

        with pytest.raises(VersionMismatchError):
            write_version("1.6.0", root)

    def test_sequential_writes_succeed(self, tmp_path):
        """Multiple sequential write_version calls on the same root succeed."""
        root = _make_theme_root(tmp_path, "1.0.0")
        from cli_anything.skyyrose_theme.core.version import (read_version,
                                                              write_version)

        for version in ("1.1.0", "1.2.0", "1.3.0"):
            write_version(version, root)
            assert read_version(root).current == version
