"""Tests for mcp_tools/tools/wp_deploy.py.

Covers:
    - Pure helpers (_bump_semver, _read_current_versions) — no I/O mocking needed
    - Version surface I/O (_write_version) — temp-file based
    - Dry-run paths on all 4 tools — no subprocess, no network, no theme writes
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_tools.tools import wp_deploy
from mcp_tools.tools.wp_deploy import (
    BackfillNextgenInput,
    BumpVersionInput,
    ReleaseInput,
    VerifyLiveInput,
    _bump_semver,
    _read_current_versions,
    _write_version,
    wp_backfill_nextgen,
    wp_bump_version,
    wp_release,
    wp_verify_live,
)

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestBumpSemver:
    """_bump_semver is a pure function — exhaustive table-driven tests."""

    @pytest.mark.parametrize(
        "current,part,expected",
        [
            ("1.0.0", "patch", "1.0.1"),
            ("1.5.16", "patch", "1.5.17"),
            ("1.5.16", "minor", "1.6.0"),
            ("1.5.16", "major", "2.0.0"),
            ("0.0.0", "patch", "0.0.1"),
            ("9.9.9", "minor", "9.10.0"),
        ],
    )
    def test_valid_bumps(self, current: str, part: str, expected: str) -> None:
        assert _bump_semver(current, part) == expected  # type: ignore[arg-type]

    def test_invalid_semver_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid semver"):
            _bump_semver("1.0", "patch")
        with pytest.raises(ValueError, match="not a valid semver"):
            _bump_semver("v1.0.0", "patch")
        with pytest.raises(ValueError, match="not a valid semver"):
            _bump_semver("1.0.0-rc1", "patch")

    def test_invalid_part_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown bump part"):
            _bump_semver("1.0.0", "nuclear")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Version surface I/O via temp files
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_theme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Build a fake theme directory with the 3 version-bearing files."""
    style = tmp_path / "style.css"
    style.write_text(
        "/*\nTheme Name:         SkyyRose\nVersion:             1.5.16\n*/\n",
        encoding="utf-8",
    )
    readme = tmp_path / "readme.txt"
    readme.write_text(
        "=== SkyyRose ===\nRequires at least: 6.0\nStable tag: 1.5.16\nTested up to: 6.8\n",
        encoding="utf-8",
    )
    functions = tmp_path / "functions.php"
    functions.write_text(
        "<?php\n// Theme bootstrap\ndefine( 'SKYYROSE_VERSION', '1.5.16' );\n",
        encoding="utf-8",
    )

    # Monkey-patch the module-level path constants to point at our temp files.
    monkeypatch.setattr(
        wp_deploy,
        "_VERSION_FILES",
        {"style.css": style, "readme.txt": readme, "functions.php": functions},
    )
    return {"style.css": style, "readme.txt": readme, "functions.php": functions}


class TestReadCurrentVersions:
    def test_reads_all_three(self, temp_theme: dict[str, Path]) -> None:
        versions = _read_current_versions()
        assert versions == {
            "style.css": "1.5.16",
            "readme.txt": "1.5.16",
            "functions.php": "1.5.16",
        }

    def test_missing_file_returns_none(self, temp_theme: dict[str, Path]) -> None:
        temp_theme["readme.txt"].unlink()
        versions = _read_current_versions()
        assert versions["readme.txt"] is None
        assert versions["style.css"] == "1.5.16"

    def test_pattern_mismatch_returns_none(self, temp_theme: dict[str, Path]) -> None:
        temp_theme["style.css"].write_text("/* no version here */", encoding="utf-8")
        versions = _read_current_versions()
        assert versions["style.css"] is None


class TestWriteVersion:
    def test_writes_style_css(self, temp_theme: dict[str, Path]) -> None:
        changed = _write_version("style.css", "1.5.17")
        assert changed is True
        text = temp_theme["style.css"].read_text(encoding="utf-8")
        assert "Version:             1.5.17" in text
        assert "1.5.16" not in text

    def test_writes_functions_php_preserves_quote_style(self, temp_theme: dict[str, Path]) -> None:
        _write_version("functions.php", "2.0.0")
        text = temp_theme["functions.php"].read_text(encoding="utf-8")
        assert "define( 'SKYYROSE_VERSION', '2.0.0' );" in text

    def test_writes_readme(self, temp_theme: dict[str, Path]) -> None:
        _write_version("readme.txt", "1.6.0")
        text = temp_theme["readme.txt"].read_text(encoding="utf-8")
        assert "Stable tag: 1.6.0" in text

    def test_no_op_when_same_version(self, temp_theme: dict[str, Path]) -> None:
        changed = _write_version("style.css", "1.5.16")
        assert changed is False

    def test_missing_pattern_raises(self, temp_theme: dict[str, Path]) -> None:
        temp_theme["style.css"].write_text("/* no version */", encoding="utf-8")
        with pytest.raises(RuntimeError, match="no version pattern matched"):
            _write_version("style.css", "1.5.17")


# ---------------------------------------------------------------------------
# Tool dry-run paths
# ---------------------------------------------------------------------------


class TestBumpVersionTool:
    @pytest.mark.asyncio
    async def test_dry_run_returns_preview(self, temp_theme: dict[str, Path]) -> None:
        result = await wp_bump_version(BumpVersionInput(part="patch", confirm=False))
        assert "1.5.17" in result
        # Files should be unchanged
        assert "1.5.16" in temp_theme["style.css"].read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_confirm_writes_all_three(self, temp_theme: dict[str, Path]) -> None:
        await wp_bump_version(BumpVersionInput(part="patch", confirm=True))
        for path in temp_theme.values():
            assert "1.5.17" in path.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_drift_warning_when_versions_differ(self, temp_theme: dict[str, Path]) -> None:
        # Reproduce the wild-found drift: functions.php=1.5.16, others=1.3.0
        temp_theme["style.css"].write_text("/*\nVersion:             1.3.0\n*/\n", encoding="utf-8")
        temp_theme["readme.txt"].write_text(
            "=== SkyyRose ===\nStable tag: 1.3.0\n", encoding="utf-8"
        )
        result = await wp_bump_version(
            BumpVersionInput(part="patch", confirm=False, response_format="json")
        )
        # The drift warning should appear in the response somewhere — exact
        # envelope shape varies by _format_response. We just need to see that
        # the warning surfaces to the caller.
        assert "drift" in result.lower(), f"expected drift warning in response, got: {result!r}"


class TestVerifyLiveTool:
    @pytest.mark.asyncio
    async def test_ok_on_good_response(self) -> None:
        big_body = "<!doctype html><html>" + ("ok " * 30_000) + "</html>"

        class FakeResponse:
            status_code = 200
            text = big_body
            url = "https://skyyrose.co/"

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def get(self, url):
                return FakeResponse()

        with patch.object(wp_deploy.httpx, "AsyncClient", return_value=FakeClient()):
            result = await wp_verify_live(VerifyLiveInput(public_url="https://skyyrose.co/"))
        assert "Verify OK" in result or "OK" in result

    @pytest.mark.asyncio
    async def test_fail_on_small_body(self) -> None:
        class FakeResponse:
            status_code = 200
            text = "tiny"
            url = "https://skyyrose.co/"

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def get(self, url):
                return FakeResponse()

        with patch.object(wp_deploy.httpx, "AsyncClient", return_value=FakeClient()):
            result = await wp_verify_live(VerifyLiveInput(public_url="https://skyyrose.co/"))
        assert "FAILED" in result

    @pytest.mark.asyncio
    async def test_fail_on_php_fatal(self) -> None:
        class FakeResponse:
            status_code = 200
            text = "<html>" + ("ok " * 30_000) + "Fatal error: oh no</html>"
            url = "https://skyyrose.co/"

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def get(self, url):
                return FakeResponse()

        with patch.object(wp_deploy.httpx, "AsyncClient", return_value=FakeClient()):
            result = await wp_verify_live(VerifyLiveInput(public_url="https://skyyrose.co/"))
        assert "FAILED" in result


class TestReleaseTool:
    @pytest.mark.asyncio
    async def test_blocks_when_working_tree_dirty(self, temp_theme: dict[str, Path]) -> None:
        with (
            patch.object(wp_deploy, "_git_dirty", return_value=True),
            patch.object(
                wp_deploy, "_verify_live_impl", side_effect=AssertionError("should not run")
            ),
        ):
            result = await wp_release(
                ReleaseInput(version_bump="patch", dry_run=False, confirm=True)
            )
        assert "blocked" in result.lower() or "Release blocked" in result

    @pytest.mark.asyncio
    async def test_blocks_when_preverify_fails(self, temp_theme: dict[str, Path]) -> None:
        """CRITICAL gate — refuse to deploy on top of a broken site (CR finding 2026-05-22)."""

        async def fake_verify(url, min_body_kb):
            return {"ok": False, "url": url, "status_code": 500, "gates": {"status_200": False}}

        with (
            patch.object(wp_deploy, "_git_dirty", return_value=False),
            patch.object(wp_deploy, "_verify_live_impl", side_effect=fake_verify),
        ):
            result = await wp_release(
                ReleaseInput(version_bump="patch", dry_run=False, confirm=True)
            )
        # Theme files must NOT be touched when pre-verify fails
        for path in temp_theme.values():
            assert "1.5.16" in path.read_text(encoding="utf-8")
        assert "preverify" in result.lower() or "FAILED" in result

    @pytest.mark.asyncio
    async def test_dry_run_returns_plan(self, temp_theme: dict[str, Path]) -> None:
        async def fake_verify(url, min_body_kb):
            return {"ok": True, "url": url, "status_code": 200, "gates": {}}

        with (
            patch.object(wp_deploy, "_git_dirty", return_value=False),
            patch.object(wp_deploy, "_verify_live_impl", side_effect=fake_verify),
        ):
            result = await wp_release(
                ReleaseInput(version_bump="patch", dry_run=True, confirm=False)
            )
        # Theme files must NOT be touched
        for path in temp_theme.values():
            assert "1.5.16" in path.read_text(encoding="utf-8")
        assert "plan" in result.lower() or "dry-run" in result.lower()


class TestSSRFAllowlist:
    """SSRF defense — VerifyLiveInput.public_url is allowlist-restricted (CR finding 2026-05-22)."""

    def test_skyyrose_co_allowed(self) -> None:
        VerifyLiveInput(public_url="https://skyyrose.co/")  # no raise

    def test_localhost_allowed(self) -> None:
        VerifyLiveInput(public_url="http://localhost:8080/health")  # no raise

    def test_aws_metadata_rejected(self) -> None:
        with pytest.raises(Exception, match="not in allowlist|not allowed"):
            VerifyLiveInput(public_url="http://169.254.169.254/latest/meta-data/")

    def test_file_scheme_rejected(self) -> None:
        with pytest.raises(Exception, match="not allowed|not in allowlist"):
            VerifyLiveInput(public_url="file:///etc/passwd")

    def test_arbitrary_host_rejected(self) -> None:
        with pytest.raises(Exception, match="not in allowlist"):
            VerifyLiveInput(public_url="https://evil.example.com/")


class TestRedaction:
    """Subprocess output must be scrubbed before MCP return (CR finding 2026-05-22)."""

    def test_redacts_sftp_credentials(self) -> None:
        text = "Connecting to bob.smith@sftp.wp.com..."
        redacted = wp_deploy._redact_secrets(text)
        assert "bob.smith" not in redacted
        assert "[REDACTED]" in redacted

    def test_redacts_password_lines(self) -> None:
        text = "password=hunter2-correct-horse"
        redacted = wp_deploy._redact_secrets(text)
        assert "hunter2" not in redacted

    def test_redacts_long_hex_tokens(self) -> None:
        text = "API key: deadbeefcafebabe0123456789abcdef0123456789abcdef"
        redacted = wp_deploy._redact_secrets(text)
        assert "deadbeefcafebabe0123456789abcdef" not in redacted

    def test_redacts_jwt(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.signature_part_here"
        text = f"Authorization: Bearer {jwt}"
        redacted = wp_deploy._redact_secrets(text)
        assert "[REDACTED" in redacted

    def test_empty_string_safe(self) -> None:
        assert wp_deploy._redact_secrets("") == ""

    def test_clean_string_unchanged(self) -> None:
        text = "Deploy succeeded in 12.3s"
        assert wp_deploy._redact_secrets(text) == text


class TestBackfillTool:
    @pytest.mark.asyncio
    async def test_dry_run_returns_plan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Stub the script existence check
        fake_script = tmp_path / "wp-cli-nextgen-backfill.sh"
        fake_script.write_text("#!/bin/bash\necho stub\n")
        monkeypatch.setattr(wp_deploy, "_BACKFILL_SCRIPT", fake_script)

        result = await wp_backfill_nextgen(
            BackfillNextgenInput(limit=25, dry_run=True, confirm=False)
        )
        assert "plan" in result.lower() or "would_execute" in result.lower()

    @pytest.mark.asyncio
    async def test_missing_script_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(wp_deploy, "_BACKFILL_SCRIPT", Path("/nonexistent/script.sh"))
        with pytest.raises(RuntimeError, match="backfill script missing"):
            await wp_backfill_nextgen(BackfillNextgenInput(limit=25, dry_run=False, confirm=True))
