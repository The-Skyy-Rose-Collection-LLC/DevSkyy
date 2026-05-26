"""Backend wrapper pure-Python tests — no live MD required.

Tests find_marvelous_binary, run_md_script cleanup behaviour,
and render_script_template edge cases.
"""

from __future__ import annotations

import os
import subprocess

import cli_anything.marvelous.utils.marvelous_backend as backend_mod
import pytest
from cli_anything.marvelous.utils.marvelous_backend import (
    MarvelousNotFoundError, MarvelousScriptError, MarvelousTimeoutError,
    find_marvelous_binary, render_script_template, run_md_script)

# ── find_marvelous_binary ─────────────────────────────────────────────────


class TestFindMarvelousBinaryExtra:
    def test_env_var_pointing_to_directory_raises(self, monkeypatch, tmp_path):
        """A path that exists but is a directory (not a file) must raise."""
        monkeypatch.setenv("MARVELOUS_DESIGNER_BIN", str(tmp_path))
        with pytest.raises(MarvelousNotFoundError, match="set but file not found"):
            find_marvelous_binary()

    def test_env_var_empty_string_falls_through(self, monkeypatch):
        """Empty string env var should not trigger the override branch."""
        monkeypatch.setenv("MARVELOUS_DESIGNER_BIN", "")
        import glob as glob_mod

        monkeypatch.setattr(glob_mod, "glob", lambda *a, **kw: [])
        with pytest.raises(MarvelousNotFoundError):
            find_marvelous_binary()

    def test_env_var_whitespace_only_falls_through(self, monkeypatch):
        """Whitespace-only env var is stripped and treated as absent."""
        monkeypatch.setenv("MARVELOUS_DESIGNER_BIN", "   ")
        import glob as glob_mod

        monkeypatch.setattr(glob_mod, "glob", lambda *a, **kw: [])
        with pytest.raises(MarvelousNotFoundError):
            find_marvelous_binary()

    def test_glob_returns_multiple_picks_last(self, monkeypatch, tmp_path):
        """When multiple MD installs are found, the last sorted entry is used."""
        bin_a = tmp_path / "Marvelous Designer 11" / "Marvelous Designer"
        bin_b = tmp_path / "Marvelous Designer 12" / "Marvelous Designer"
        bin_a.parent.mkdir(parents=True)
        bin_b.parent.mkdir(parents=True)
        bin_a.write_bytes(b"v11")
        bin_b.write_bytes(b"v12")

        monkeypatch.delenv("MARVELOUS_DESIGNER_BIN", raising=False)
        import glob as glob_mod

        monkeypatch.setattr(glob_mod, "glob", lambda *a, **kw: sorted([str(bin_a), str(bin_b)]))
        result = find_marvelous_binary()
        assert result == str(bin_b)


# ── run_md_script tempfile cleanup ────────────────────────────────────────


class TestRunMdScriptCleanup:
    def test_tempfile_cleaned_up_on_success(self, monkeypatch, tmp_path):
        """Temp script file must be deleted even when subprocess succeeds."""
        created_paths: list[str] = []
        original_mkstemp = __import__("tempfile").mkstemp

        def capturing_mkstemp(**kwargs):
            fd, name = original_mkstemp(**kwargs)
            created_paths.append(name)
            return fd, name

        import tempfile as tempfile_mod

        monkeypatch.setattr(tempfile_mod, "mkstemp", capturing_mkstemp)

        fake_proc = subprocess.CompletedProcess(args=["fake"], returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)

        fake_bin = tmp_path / "FakeMD"
        fake_bin.write_bytes(b"#!/bin/sh")

        run_md_script("print('hello')", binary=str(fake_bin))

        for path in created_paths:
            assert not os.path.exists(path), f"Temp file not cleaned up: {path}"

    def test_tempfile_cleaned_up_on_script_error(self, monkeypatch, tmp_path):
        """Temp script file must be deleted even when subprocess returns non-zero."""
        created_paths: list[str] = []
        original_mkstemp = __import__("tempfile").mkstemp

        def capturing_mkstemp(**kwargs):
            fd, name = original_mkstemp(**kwargs)
            created_paths.append(name)
            return fd, name

        import tempfile as tempfile_mod

        monkeypatch.setattr(tempfile_mod, "mkstemp", capturing_mkstemp)

        fail_proc = subprocess.CompletedProcess(
            args=["fake"], returncode=1, stdout="", stderr="script error"
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fail_proc)

        fake_bin = tmp_path / "FakeMD"
        fake_bin.write_bytes(b"#!/bin/sh")

        with pytest.raises(MarvelousScriptError):
            run_md_script("raise RuntimeError()", binary=str(fake_bin))

        for path in created_paths:
            assert not os.path.exists(path), f"Temp file not cleaned up: {path}"

    def test_tempfile_cleaned_up_on_timeout(self, monkeypatch, tmp_path):
        """Temp script file must be deleted even when subprocess times out."""
        created_paths: list[str] = []
        original_mkstemp = __import__("tempfile").mkstemp

        def capturing_mkstemp(**kwargs):
            fd, name = original_mkstemp(**kwargs)
            created_paths.append(name)
            return fd, name

        import tempfile as tempfile_mod

        monkeypatch.setattr(tempfile_mod, "mkstemp", capturing_mkstemp)

        def timeout_run(*a, **kw):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=1)

        monkeypatch.setattr(subprocess, "run", timeout_run)

        fake_bin = tmp_path / "FakeMD"
        fake_bin.write_bytes(b"#!/bin/sh")

        with pytest.raises(MarvelousTimeoutError):
            run_md_script("import time; time.sleep(9999)", binary=str(fake_bin), timeout=1)

        for path in created_paths:
            assert not os.path.exists(path), f"Temp file not cleaned up: {path}"

    def test_script_error_captures_returncode_and_stderr(self, monkeypatch, tmp_path):
        fail_proc = subprocess.CompletedProcess(
            args=["fake"], returncode=42, stdout="", stderr="MD internal error"
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fail_proc)

        fake_bin = tmp_path / "FakeMD"
        fake_bin.write_bytes(b"#!/bin/sh")

        with pytest.raises(MarvelousScriptError) as exc_info:
            run_md_script("bad script", binary=str(fake_bin))

        err = exc_info.value
        assert err.returncode == 42
        assert "MD internal error" in err.stderr


# ── render_script_template edge cases ────────────────────────────────────


class TestRenderScriptTemplateEdgeCases:
    def test_empty_template_empty_vars(self):
        assert render_script_template("", {}) == ""

    def test_extra_vars_in_dict_ignored(self):
        """Extra variables not referenced in the template are silently ignored."""
        result = render_script_template("hello = '${name}'", {"name": "world", "extra": "ignored"})
        assert result == "hello = 'world'"

    def test_dollar_sign_bare_invalid_raises(self):
        """Bare $ followed by a digit is an invalid placeholder and raises ValueError."""
        with pytest.raises(ValueError):
            render_script_template("price = $100", {})

    def test_numeric_value_converted_to_string(self):
        """Template.substitute converts int values to str automatically."""
        result = render_script_template("frames = ${n}", {"n": 42})
        assert "42" in result
