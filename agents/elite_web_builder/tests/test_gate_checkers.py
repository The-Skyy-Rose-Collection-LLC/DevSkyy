"""Tests for core.gate_checkers — concrete gate checker implementations."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.gate_checkers import (
    build_gate_checkers,
    check_a11y,
    check_build,
    check_diff,
    check_lint,
    check_perf,
    check_security,
)
from core.verification_loop import Gate, GateStatus

# ---------------------------------------------------------------------------
# BUILD gate
# ---------------------------------------------------------------------------


class TestCheckBuild:
    @pytest.mark.asyncio
    async def test_valid_php(self, tmp_path: Path) -> None:
        (tmp_path / "test.php").write_text("<?php\necho 'hello';\n")
        result = await check_build(["test.php"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_missing_php_tag(self, tmp_path: Path) -> None:
        (tmp_path / "test.php").write_text("echo 'hello';")
        result = await check_build(["test.php"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "<?php" in result.details[0]

    @pytest.mark.asyncio
    async def test_unbalanced_braces_php(self, tmp_path: Path) -> None:
        (tmp_path / "test.php").write_text("<?php\nfunction foo() {\n")
        result = await check_build(["test.php"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_valid_json(self, tmp_path: Path) -> None:
        (tmp_path / "theme.json").write_text('{"version": 3}')
        result = await check_build(["theme.json"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("{invalid json")
        result = await check_build(["bad.json"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_valid_css(self, tmp_path: Path) -> None:
        (tmp_path / "style.css").write_text("body { color: red; }")
        result = await check_build(["style.css"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_unbalanced_css(self, tmp_path: Path) -> None:
        (tmp_path / "bad.css").write_text("body { color: red;")
        result = await check_build(["bad.css"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_valid_js(self, tmp_path: Path) -> None:
        (tmp_path / "main.js").write_text("const x = { a: [1, 2] };")
        result = await check_build(["main.js"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_missing_file(self, tmp_path: Path) -> None:
        result = await check_build(["nonexistent.php"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_empty_file_list(self, tmp_path: Path) -> None:
        result = await check_build([], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_strings_in_braces_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "test.js").write_text('const s = "{ not a brace }";')
        result = await check_build(["test.js"], tmp_path)
        assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# LINT gate
# ---------------------------------------------------------------------------


class TestCheckLint:
    @pytest.mark.asyncio
    async def test_clean_php(self, tmp_path: Path) -> None:
        (tmp_path / "clean.php").write_text("<?php\necho esc_html($name);\n")
        result = await check_lint(["clean.php"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_var_dump_detected(self, tmp_path: Path) -> None:
        (tmp_path / "debug.php").write_text("<?php\nvar_dump($data);\n")
        result = await check_lint(["debug.php"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "var_dump" in result.details[0]

    @pytest.mark.asyncio
    async def test_console_log_detected(self, tmp_path: Path) -> None:
        (tmp_path / "debug.js").write_text("console.log('debug');\n")
        result = await check_lint(["debug.js"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "console.log" in result.details[0]

    @pytest.mark.asyncio
    async def test_eval_detected(self, tmp_path: Path) -> None:
        (tmp_path / "evil.js").write_text("eval('alert(1)');\n")
        result = await check_lint(["evil.js"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_important_css_detected(self, tmp_path: Path) -> None:
        (tmp_path / "hack.css").write_text("body { color: red !important; }")
        result = await check_lint(["hack.css"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_clean_files_pass(self, tmp_path: Path) -> None:
        (tmp_path / "good.js").write_text("const x = 1;\n")
        (tmp_path / "good.css").write_text("body { margin: 0; }")
        result = await check_lint(["good.js", "good.css"], tmp_path)
        assert result.status == GateStatus.PASSED


# ---------------------------------------------------------------------------
# SECURITY gate
# ---------------------------------------------------------------------------


class TestCheckSecurity:
    @pytest.mark.asyncio
    async def test_clean_files(self, tmp_path: Path) -> None:
        (tmp_path / "safe.php").write_text("<?php echo esc_html('hello');\n")
        result = await check_security(["safe.php"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_detects_api_key(self, tmp_path: Path) -> None:
        (tmp_path / "leaked.php").write_text(
            '<?php $key = "sk-abcdefghijklmnopqrstuvwxyz1234567890";\n'
        )
        result = await check_security(["leaked.php"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "API key" in result.details[0]

    @pytest.mark.asyncio
    async def test_detects_private_key(self, tmp_path: Path) -> None:
        (tmp_path / "key.txt").write_text("-----BEGIN RSA PRIVATE KEY-----\ndata\n")
        result = await check_security(["key.txt"], tmp_path)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_detects_innerhtml(self, tmp_path: Path) -> None:
        (tmp_path / "xss.js").write_text("el.innerHTML = userInput;\n")
        result = await check_security(["xss.js"], tmp_path)
        assert result.status == GateStatus.PASSED  # XSS is warning, not critical
        assert len(result.details) > 0  # but reported


# ---------------------------------------------------------------------------
# DIFF gate
# ---------------------------------------------------------------------------


class TestCheckDiff:
    @pytest.mark.asyncio
    async def test_valid_files(self) -> None:
        result = await check_diff(["style.css", "functions.php"])
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_too_many_files(self) -> None:
        files = [f"file_{i}.php" for i in range(100)]
        result = await check_diff(files, max_files=50)
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_unexpected_extension(self) -> None:
        result = await check_diff(["script.exe"])
        assert result.status == GateStatus.FAILED

    @pytest.mark.asyncio
    async def test_suspicious_filename(self) -> None:
        result = await check_diff(["backup.php.bak"])
        assert result.status == GateStatus.FAILED


# ---------------------------------------------------------------------------
# A11Y gate
# ---------------------------------------------------------------------------


class TestCheckA11y:
    @pytest.mark.asyncio
    async def test_valid_html(self, tmp_path: Path) -> None:
        (tmp_path / "page.html").write_text(
            '<html lang="en"><body><img src="x.jpg" alt="photo"></body></html>'
        )
        result = await check_a11y(["page.html"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_img_without_alt(self, tmp_path: Path) -> None:
        (tmp_path / "page.html").write_text('<html lang="en"><body><img src="x.jpg"></body></html>')
        result = await check_a11y(["page.html"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "alt" in result.details[0].lower()

    @pytest.mark.asyncio
    async def test_skips_non_html(self, tmp_path: Path) -> None:
        (tmp_path / "data.json").write_text('{"key": "value"}')
        result = await check_a11y(["data.json"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_php_templates_checked(self, tmp_path: Path) -> None:
        (tmp_path / "page.php").write_text('<?php get_header(); ?><img src="x.jpg">')
        result = await check_a11y(["page.php"], tmp_path)
        assert result.status == GateStatus.FAILED


# ---------------------------------------------------------------------------
# PERF gate
# ---------------------------------------------------------------------------


class TestCheckPerf:
    @pytest.mark.asyncio
    async def test_small_files_pass(self, tmp_path: Path) -> None:
        (tmp_path / "small.css").write_text("body { margin: 0; }")
        result = await check_perf(["small.css"], tmp_path)
        assert result.status == GateStatus.PASSED

    @pytest.mark.asyncio
    async def test_oversized_css_fails(self, tmp_path: Path) -> None:
        (tmp_path / "huge.css").write_text("x" * (200 * 1024))
        result = await check_perf(["huge.css"], tmp_path)
        assert result.status == GateStatus.FAILED
        assert "budget" in result.details[0].lower()


# ---------------------------------------------------------------------------
# build_gate_checkers integration
# ---------------------------------------------------------------------------


class TestBuildGateCheckers:
    def test_returns_all_8_gates(self, tmp_path: Path) -> None:
        (tmp_path / "functions.php").write_text("<?php echo 1;")
        checkers = build_gate_checkers(["functions.php"], tmp_path)
        assert set(checkers.keys()) == set(Gate)

    @pytest.mark.asyncio
    async def test_all_gates_callable(self, tmp_path: Path) -> None:
        (tmp_path / "functions.php").write_text("<?php echo 1;")
        checkers = build_gate_checkers(["functions.php"], tmp_path)
        for gate, checker in checkers.items():
            result = await checker()
            assert result.gate == gate
            assert result.status in (GateStatus.PASSED, GateStatus.SKIPPED)

    @pytest.mark.asyncio
    async def test_types_and_tests_skipped(self, tmp_path: Path) -> None:
        checkers = build_gate_checkers(["functions.php"], tmp_path)
        types_result = await checkers[Gate.TYPES]()
        tests_result = await checkers[Gate.TESTS]()
        assert types_result.status == GateStatus.SKIPPED
        assert tests_result.status == GateStatus.SKIPPED
