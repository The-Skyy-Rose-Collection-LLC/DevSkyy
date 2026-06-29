"""Tests for source-level security remediation (SecurityRemediator + /code/fix wire).

Coverage is failure-path-first per the design contract: the whole point of this
component is that a "fix" only ever reports success when a vulnerable line was
actually made safe. The four outcomes must never collapse into one another:

    1. matched vulnerable → fixed           → success
    2. already remediated (idempotent)        → success / no-op
    3. supported CWE but line does not match  → failure / manual
    4. unsupported CWE                         → failure / manual

Plus: dry-run never writes, the AST backstop reverts broken edits, and when mixed
with formatters the security (line-targeted) fix runs FIRST so scan line numbers
stay valid.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.code_security_remediator import SecurityRemediator, SecurityTarget
from api.v1.code import router as code_router
from security.jwt_oauth2_auth import TokenPayload, TokenType, get_current_user

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


# =============================================================================
# Unit: SecurityRemediator (real files, no mocks — it is deterministic & fast)
# =============================================================================


class TestSecurityRemediatorUnit:
    def _write(self, tmp_path: Path, body: str) -> tuple[SecurityRemediator, str]:
        f = tmp_path / "target.py"
        f.write_text(body, encoding="utf-8")
        return SecurityRemediator(tmp_path), "target.py"

    def test_bare_except_fixed(self, tmp_path: Path) -> None:
        rem, rel = self._write(tmp_path, "try:\n    pass\nexcept:\n    pass\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 3)], dry_run=False)
        assert len(results) == 1
        assert results[0].success is True
        assert "except:" in results[0].changes_made[0]
        assert "except Exception:" in results[0].changes_made[0]
        # the file was actually rewritten
        assert "except Exception:" in (tmp_path / "target.py").read_text()

    def test_debug_true_fixed_preserves_spacing(self, tmp_path: Path) -> None:
        rem, rel = self._write(tmp_path, "DEBUG   =   True\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-489", 1)], dry_run=False)
        assert results[0].success is True
        # spacing preserved, only True→False flipped
        assert (tmp_path / "target.py").read_text() == "DEBUG   =   False\n"

    def test_idempotent_already_remediated_is_success_noop(self, tmp_path: Path) -> None:
        """A line already in remediated form is success/no-op, NOT a failure."""
        before = "try:\n    pass\nexcept Exception:\n    pass\n"
        rem, rel = self._write(tmp_path, before)
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 3)], dry_run=False)
        assert results[0].success is True
        assert "already remediated" in results[0].changes_made[0]
        assert (tmp_path / "target.py").read_text() == before  # unchanged

    def test_supported_cwe_but_line_does_not_match_is_failure(self, tmp_path: Path) -> None:
        """Stale line number / false positive → failure-manual, never fake success."""
        rem, rel = self._write(tmp_path, "x = 1\ny = 2\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 1)], dry_run=False)
        assert results[0].success is False
        assert "does not match" in results[0].error
        assert (tmp_path / "target.py").read_text() == "x = 1\ny = 2\n"

    def test_variant_symbol_not_falsely_fixed(self, tmp_path: Path) -> None:
        """``MY_DEBUG = True`` is a different symbol — must not be silently rewritten."""
        rem, rel = self._write(tmp_path, "MY_DEBUG = True\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-489", 1)], dry_run=False)
        assert results[0].success is False
        assert (tmp_path / "target.py").read_text() == "MY_DEBUG = True\n"

    def test_unsupported_cwe_is_manual(self, tmp_path: Path) -> None:
        rem, rel = self._write(tmp_path, "cursor.execute('... %s' % uid)\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-89", 1)], dry_run=False)
        assert results[0].success is False
        assert "manual review required" in results[0].error

    def test_line_out_of_range_is_failure(self, tmp_path: Path) -> None:
        rem, rel = self._write(tmp_path, "x = 1\n")
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 999)], dry_run=False)
        assert results[0].success is False
        assert "out of range" in results[0].error

    def test_dry_run_previews_without_writing(self, tmp_path: Path) -> None:
        before = "try:\n    pass\nexcept:\n    pass\n"
        rem, rel = self._write(tmp_path, before)
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 3)], dry_run=True)
        assert results[0].success is True
        assert "would fix" in results[0].changes_made[0]
        assert (tmp_path / "target.py").read_text() == before  # NOT written

    def test_unparseable_file_is_failure(self, tmp_path: Path) -> None:
        """A file that does not parse cannot have its AST targets confirmed → every
        target fails honestly, file untouched (no blind regex edit)."""
        before = "except:\n"  # standalone except — not valid Python
        rem, rel = self._write(tmp_path, before)
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 1)], dry_run=False)
        assert results[0].success is False
        assert "does not parse" in results[0].error
        assert (tmp_path / "target.py").read_text() == before  # untouched

    def test_match_inside_string_literal_not_fixed(self, tmp_path: Path) -> None:
        """A ``except:`` inside a triple-quoted string is flagged by the line-regex
        scanner but is NOT an AST ExceptHandler — must be failure-manual, not a fake
        success that corrupts the string content."""
        before = 'EXAMPLE = """\ntry:\n    pass\nexcept:\n    pass\n"""\n'
        rem, rel = self._write(tmp_path, before)
        # line 4 is the `except:` inside the string literal
        results = rem.remediate_file(rel, [SecurityTarget("CWE-396", 4)], dry_run=False)
        assert results[0].success is False
        assert "does not match" in results[0].error
        assert (tmp_path / "target.py").read_text() == before  # string untouched

    def test_match_inside_comment_not_fixed(self, tmp_path: Path) -> None:
        """``# DEBUG = True`` in a comment is not an AST Assign → failure-manual."""
        before = "x = 1  # DEBUG = True legacy note\n"
        rem, rel = self._write(tmp_path, before)
        results = rem.remediate_file(rel, [SecurityTarget("CWE-489", 1)], dry_run=False)
        assert results[0].success is False
        assert "does not match" in results[0].error
        assert (tmp_path / "target.py").read_text() == before  # comment untouched

    def test_multi_target_single_file_write_once(self, tmp_path: Path) -> None:
        """One fixable + one unsupported target in the same file: fix applied, other
        reported manual, file written exactly once with the valid edit."""
        before = "try:\n    pass\nexcept:\n    pass\nDEBUG = True\n"
        rem, rel = self._write(tmp_path, before)
        results = rem.remediate_file(
            rel,
            [SecurityTarget("CWE-396", 3), SecurityTarget("CWE-89", 5)],
            dry_run=False,
        )
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) == 1
        assert len(failures) == 1
        assert "manual review required" in failures[0].error
        written = (tmp_path / "target.py").read_text()
        assert "except Exception:" in written
        assert "DEBUG = True" in written  # CWE-89 target did not touch the DEBUG line

    def test_supports_classmethod(self) -> None:
        assert SecurityRemediator.supports("CWE-396") is True
        assert SecurityRemediator.supports("CWE-489") is True
        assert SecurityRemediator.supports("CWE-89") is False
        assert SecurityRemediator.supports(None) is False


# =============================================================================
# Integration: /code/fix with fix_types=["security"]
# =============================================================================


def _admin_user() -> TokenPayload:
    return TokenPayload(sub="admin", jti="j-admin", type=TokenType.ACCESS, roles=["admin"])


def _api_user() -> TokenPayload:
    return TokenPayload(sub="user", jti="j-user", type=TokenType.ACCESS, roles=["api_user"])


@pytest.fixture()
def admin_client() -> TestClient:
    app = FastAPI()
    app.include_router(code_router)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(code_router)
    app.dependency_overrides[get_current_user] = lambda: _api_user()
    return TestClient(app, raise_server_exceptions=False)


@contextmanager
def _repo_temp_py(body: str):
    """Create a real .py file directly under PROJECT_ROOT (so it passes the path
    guard), yield (abs_path, rel_path), and always clean up."""
    fd = tempfile.NamedTemporaryFile(
        dir=str(_PROJECT_ROOT), prefix="sec_remediate_", suffix=".py", delete=False
    )
    try:
        fd.write(body.encode("utf-8"))
        fd.close()
        abs_path = Path(fd.name)
        yield abs_path, abs_path.name
    finally:
        Path(fd.name).unlink(missing_ok=True)


@contextmanager
def _patched_learner():
    """Patch only the SelfLearningEngine so no real learnings file is written; the
    SecurityRemediator itself runs for real."""
    with patch("agents.coding_doctor_agent.SelfLearningEngine") as cls:
        learn = cls.return_value
        learn.initialize = AsyncMock()
        learn.learn = MagicMock()
        learn.save = AsyncMock()
        learn.get_stats = MagicMock(return_value={"total_patterns": 0, "categories": {}})
        yield learn


def _sec_scan(file_path: str, cwe: str, line: int) -> dict:
    return {"issues": [{"file": file_path, "line": line, "type": "security", "rule": cwe}]}


class TestCodeFixSecurityWire:
    def test_dry_run_security_previews_without_writing(self, client: TestClient) -> None:
        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, rel):
            with _patched_learner():
                resp = client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-396", 3),
                        "fix_types": ["security"],
                    },
                )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["dry_run"] is True
            assert data["status"] == "previewed"
            assert data["fixes_applied"] == 1
            assert data["results"][0]["action"] == "fix_security"
            assert data["results"][0]["success"] is True
            assert "would fix" in data["results"][0]["changes_made"][0]
            # not written
            assert "except Exception:" not in abs_path.read_text()

    def test_auto_apply_security_writes_fix(self, admin_client: TestClient) -> None:
        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, rel):
            with _patched_learner() as learn:
                resp = admin_client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-396", 3),
                        "fix_types": ["security"],
                        "auto_apply": True,
                    },
                )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["status"] == "completed"
            assert data["fixes_applied"] == 1
            assert "except Exception:" in abs_path.read_text()  # really fixed
            learn.learn.assert_called()  # security outcome recorded
            learn.save.assert_awaited_once()
            # backup taken before mutation
            assert data["backup_path"] is not None

    def test_auto_apply_security_forbidden_for_non_admin(self, client: TestClient) -> None:
        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, rel):
            with _patched_learner():
                resp = client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-396", 3),
                        "fix_types": ["security"],
                        "auto_apply": True,
                    },
                )
            assert resp.status_code == 403, resp.text
            assert "except Exception:" not in abs_path.read_text()  # not mutated

    def test_unsupported_cwe_reported_manual_not_faked(self, client: TestClient) -> None:
        with _repo_temp_py("cursor.execute('... %s' % uid)\n") as (abs_path, rel):
            with _patched_learner():
                resp = client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-89", 1),
                        "fix_types": ["security"],
                    },
                )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            results = data["results"]
            assert len(results) == 1
            assert results[0]["success"] is False
            assert "manual review required" in results[0]["error"]

    def test_security_not_remediated_unless_requested(self, admin_client: TestClient) -> None:
        """A type=security finding is left untouched when 'security' is not in fix_types."""
        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, rel):
            # patch the tool engines so the 'imports' path is a no-op mock
            with (
                patch("agents.coding_doctor_agent.SelfHealingEngine") as heal_cls,
                _patched_learner(),
            ):
                heal = heal_cls.return_value
                heal.initialize = AsyncMock()
                heal.heal = AsyncMock(side_effect=self._noop_heal)
                resp = admin_client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-396", 3),
                        "fix_types": ["imports"],
                        "auto_apply": True,
                    },
                )
            assert resp.status_code == 200, resp.text
            assert "except Exception:" not in abs_path.read_text()  # security NOT applied

    @staticmethod
    def _noop_heal(issue, dry_run):  # noqa: ARG004 - signature fixed by heal() mock contract
        from agents.coding_doctor_agent import HealingResult

        return HealingResult(
            action=issue.fix_action,
            file_path=issue.file_path,
            success=True,
            changes_made=["noop"],
            error=None,
        )

    def test_security_runs_before_formatters(self, admin_client: TestClient) -> None:
        """Mixed ['security','format']: the line-targeted security fix must be written
        BEFORE the tool healer reads the file, or scan line numbers would be stale."""
        observed: dict = {}

        def _heal(issue, dry_run):
            from agents.coding_doctor_agent import HealingResult

            # record what the file looks like when the tool healer is invoked
            observed["content_at_heal"] = (_PROJECT_ROOT / issue.file_path).read_text()
            return HealingResult(
                action=issue.fix_action,
                file_path=issue.file_path,
                success=True,
                changes_made=["noop"],
                error=None,
            )

        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, rel):
            with (
                patch("agents.coding_doctor_agent.SelfHealingEngine") as heal_cls,
                _patched_learner(),
            ):
                heal = heal_cls.return_value
                heal.initialize = AsyncMock()
                heal.heal = AsyncMock(side_effect=_heal)
                resp = admin_client.post(
                    "/code/fix",
                    json={
                        "scan_results": _sec_scan(str(abs_path), "CWE-396", 3),
                        "fix_types": ["security", "format"],
                        "auto_apply": True,
                    },
                )
            assert resp.status_code == 200, resp.text
            # security fix already on disk when the formatter ran
            assert "except Exception:" in observed["content_at_heal"]

    def test_scan_to_fix_round_trip(self, admin_client: TestClient) -> None:
        """The literal end-to-end proof: a REAL /code/scan output, fed straight into
        /code/fix, actually remediates the file. Guards against field-shape drift
        between what the scanner emits and what the fixer reads (hand-built payloads
        in the other tests cannot)."""
        with _repo_temp_py("try:\n    pass\nexcept:\n    pass\n") as (abs_path, _):
            scan = admin_client.post("/code/scan", json={"path": str(abs_path)})
            assert scan.status_code == 200, scan.text
            scan_issues = scan.json()["issues"]
            # the scanner really found the bare except (CWE-396)
            assert any(i["rule"] == "CWE-396" and i["type"] == "security" for i in scan_issues)

            with _patched_learner():
                fix = admin_client.post(
                    "/code/fix",
                    json={
                        "scan_results": {"issues": scan_issues},
                        "fix_types": ["security"],
                        "auto_apply": True,
                    },
                )
            assert fix.status_code == 200, fix.text
            assert fix.json()["fixes_applied"] >= 1
            assert "except Exception:" in abs_path.read_text()  # really remediated
