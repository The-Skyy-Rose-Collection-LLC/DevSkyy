"""Wire tests for /code/scan endpoint (T3-1).

Verifies:
- Real delegation to CodeSecurityAnalyzer (monkeypatched to avoid FS scanning)
- Field-level SecurityFinding → ScanIssue mapping is exact, not approximated
- Summary counts derived from real findings (not hardcoded)
- Path-containment guard rejects paths outside PROJECT_ROOT with 400
- Non-existent in-project paths return 404
"""

import shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.code import router as code_router
from security.code_analysis import SecurityCategory, SecurityFinding, SecuritySeverity
from security.jwt_oauth2_auth import TokenPayload, TokenType, get_current_user

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _mock_user() -> TokenPayload:
    return TokenPayload(
        sub="test-user",
        jti="jti-test",
        type=TokenType.ACCESS,
        roles=["api_user"],
    )


def _admin_user() -> TokenPayload:
    return TokenPayload(
        sub="admin-user",
        jti="jti-admin",
        type=TokenType.ACCESS,
        roles=["admin"],
    )


@pytest.fixture()
def client() -> TestClient:
    """Isolated FastAPI app, auth bypassed as an api_user (no auto_apply rights)."""
    app = FastAPI()
    app.include_router(code_router)
    app.dependency_overrides[get_current_user] = lambda: _mock_user()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def admin_client() -> TestClient:
    """Isolated FastAPI app, auth bypassed as an ADMIN (may auto_apply)."""
    app = FastAPI()
    app.include_router(code_router)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    return TestClient(app, raise_server_exceptions=False)


def _finding(file_path: str, line_number: int, severity: SecuritySeverity) -> SecurityFinding:
    return SecurityFinding(
        id=f"TEST-SEC001-{line_number}",
        title="SQL Injection Risk",
        description="Potential SQL injection vulnerability detected",
        severity=severity,
        category=SecurityCategory.INJECTION,
        file_path=file_path,
        line_number=line_number,
        code_snippet="cursor.execute('SELECT * FROM t WHERE id = %s' % uid)",
        recommendation="Use parameterized queries",
        cwe_id="CWE-89",
    )


class TestCodeScanMapping:
    """SecurityFinding objects must map faithfully to ScanIssue fields."""

    def test_directory_mapping_and_summary_counts(self, client: TestClient) -> None:
        """Two findings → correct per-field mapping + accurate summary counts."""
        scan_dir = str(_PROJECT_ROOT / "security")
        findings = [
            _finding(scan_dir + "/a.py", 10, SecuritySeverity.HIGH),
            _finding(scan_dir + "/b.py", 42, SecuritySeverity.MEDIUM),
        ]

        with patch("api.v1.code.CodeSecurityAnalyzer.analyze_directory", return_value=findings):
            resp = client.post("/code/scan", json={"path": scan_dir})

        assert resp.status_code == 200, resp.text
        data = resp.json()

        issues = data["issues"]
        assert len(issues) == 2

        # First finding — every mapped field asserted
        first = issues[0]
        assert first["file"] == scan_dir + "/a.py"
        assert first["line"] == 10
        assert first["column"] is None
        assert first["severity"] == "high"  # SecuritySeverity.HIGH.value
        assert first["type"] == "security"
        assert first["message"] == "SQL Injection Risk"
        assert first["rule"] == "CWE-89"  # cwe_id preferred over id
        assert first["suggestion"] == "Use parameterized queries"

        # Second finding — key fields
        second = issues[1]
        assert second["severity"] == "medium"
        assert second["line"] == 42

        # Summary counts must reflect real findings, not hardcoded values
        summary = data["summary"]
        assert summary["critical"] == 0
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 0
        assert summary["info"] == 0
        assert summary["security_issues"] == 2

        # files_scanned must be an honest integer (not the old hardcoded 10)
        assert isinstance(data["files_scanned"], int)

    def test_file_target_uses_analyze_file(self, client: TestClient) -> None:
        """Pointing at a single .py file routes to analyze_file, not analyze_directory."""
        target_file = str(_PROJECT_ROOT / "security" / "code_analysis.py")
        findings = [_finding(target_file, 99, SecuritySeverity.CRITICAL)]

        with patch("api.v1.code.CodeSecurityAnalyzer.analyze_file", return_value=findings):
            resp = client.post("/code/scan", json={"path": target_file})

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["issues"]) == 1
        assert data["issues"][0]["severity"] == "critical"
        assert data["summary"]["critical"] == 1
        assert data["files_scanned"] == 1


class TestCodeScanPathSafety:
    """Path injection and traversal attempts must return HTTP 400."""

    def test_absolute_outside_project_root_returns_400(self, client: TestClient) -> None:
        resp = client.post("/code/scan", json={"path": "/etc"})
        assert resp.status_code == 400

    def test_traversal_outside_project_root_returns_400(self, client: TestClient) -> None:
        # Resolves relative to CWD; when run from DevSkyy this exits the project root
        resp = client.post("/code/scan", json={"path": "../../etc/passwd"})
        assert resp.status_code == 400

    def test_nonexistent_inside_project_returns_404(self, client: TestClient) -> None:
        missing = str(_PROJECT_ROOT / "does_not_exist_xyz_abc_123_sentinel")
        resp = client.post("/code/scan", json={"path": missing})
        assert resp.status_code == 404


def _scan_results(*files: str) -> dict:
    """Build a scan_results payload referencing the given file paths."""
    return {"issues": [{"file": f, "line": 1} for f in files]}


def _default_heal(issue, dry_run):  # noqa: ANN001 - test stub
    """Sync side_effect for the heal AsyncMock — returns a real HealingResult."""
    from agents.coding_doctor_agent import HealingResult

    return HealingResult(
        action=issue.fix_action,
        file_path=issue.file_path,
        success=True,
        changes_made=[f"applied {issue.fix_action.value}"],
        error=None,
    )


@contextmanager
def _patched_engines(heal_side_effect=_default_heal):
    """Patch BOTH SelfHealingEngine and SelfLearningEngine; yield (heal, learn) mocks.

    No real black/isort/ruff/autoflake runs and no real learnings file is written.
    """
    with (
        patch("agents.coding_doctor_agent.SelfHealingEngine") as mock_heal_cls,
        patch("agents.coding_doctor_agent.SelfLearningEngine") as mock_learn_cls,
    ):
        heal = mock_heal_cls.return_value
        heal.initialize = AsyncMock()
        heal.heal = AsyncMock(side_effect=heal_side_effect)

        learn = mock_learn_cls.return_value
        learn.initialize = AsyncMock()
        learn.learn = MagicMock()
        learn.save = AsyncMock()
        learn.get_stats = MagicMock(
            return_value={"total_patterns": 1, "categories": {"maintainability": 1}}
        )
        yield heal, learn


class TestCodeFixWire:
    """POST /code/fix delegates to SelfHealingEngine and records outcomes for learning."""

    _TARGET = str(_PROJECT_ROOT / "security" / "code_analysis.py")

    def test_dry_run_previews_without_learning(self, client: TestClient) -> None:
        """Default (auto_apply=False) previews via the healer; does NOT record learning."""
        with _patched_engines() as (heal, learn):
            resp = client.post(
                "/code/fix",
                json={"scan_results": _scan_results(self._TARGET), "fix_types": ["imports"]},
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["dry_run"] is True
        assert data["status"] == "previewed"
        assert data["files_processed"] == 1
        assert data["fixes_applied"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["action"] == "fix_imports"
        assert data["results"][0]["success"] is True
        heal.heal.assert_awaited_once()  # real delegation occurred
        learn.learn.assert_not_called()  # dry-run previews are not learned from
        learn.save.assert_not_awaited()

    def test_auto_apply_records_learning(self, admin_client: TestClient) -> None:
        """auto_apply=True (ADMIN) applies in place, records each outcome, backs up first."""
        captured: dict = {}

        def _heal(issue, dry_run):
            captured["dry_run"] = dry_run
            return _default_heal(issue, dry_run)

        with _patched_engines(heal_side_effect=_heal) as (heal, learn):
            resp = admin_client.post(
                "/code/fix",
                json={
                    "scan_results": _scan_results(self._TARGET),
                    "fix_types": ["format", "imports"],
                    "auto_apply": True,
                },
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert captured["dry_run"] is False  # real (in-place) run
        assert data["dry_run"] is False
        assert data["status"] == "completed"
        assert heal.heal.await_count == 2  # one per (file × action)
        assert learn.learn.call_count == 2  # every outcome recorded
        learn.save.assert_awaited_once()  # learnings persisted
        assert data["learning_stats"]["total_patterns"] == 1

        # create_backup (default True) made a pre-fix copy before mutating.
        backup = data["backup_path"]
        assert backup is not None
        backup_dir = Path(backup)
        try:
            assert backup_dir.is_dir()
            assert (backup_dir / "security" / "code_analysis.py").exists()
        finally:
            shutil.rmtree(backup_dir, ignore_errors=True)

    def test_auto_apply_forbidden_for_non_admin(self, client: TestClient) -> None:
        """api_user (non-admin) cannot trigger in-place mutation → 403; nothing dispatched."""
        with _patched_engines() as (heal, learn):
            resp = client.post(
                "/code/fix",
                json={
                    "scan_results": _scan_results(self._TARGET),
                    "fix_types": ["imports"],
                    "auto_apply": True,
                },
            )
        assert resp.status_code == 403, resp.text
        heal.heal.assert_not_awaited()
        learn.learn.assert_not_called()

    def test_unsupported_fix_types_reported(self, client: TestClient) -> None:
        """fix_types with no real healer are reported, never faked; nothing dispatched.

        ``security`` is now a real (opt-in) healer, so it is NOT unsupported — but the
        scan_results here carry no ``type=='security'`` findings, so it yields no work
        and the run is still ``no_action``. Only ``docstrings`` is unsupported.
        """
        with _patched_engines() as (heal, learn):
            resp = client.post(
                "/code/fix",
                json={
                    "scan_results": _scan_results(self._TARGET),
                    "fix_types": ["security", "docstrings"],
                },
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "no_action"
        assert set(data["unsupported_fix_types"]) == {"docstrings"}
        assert data["results"] == []
        heal.heal.assert_not_awaited()
        learn.learn.assert_not_called()

    def test_path_outside_project_rejected(self, client: TestClient) -> None:
        """A scan-result file outside the project never reaches the healer."""
        with _patched_engines() as (heal, learn):
            resp = client.post(
                "/code/fix",
                json={"scan_results": _scan_results("/etc/passwd"), "fix_types": ["imports"]},
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["files_processed"] == 0
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is False
        assert "path outside" in data["results"][0]["error"]
        heal.heal.assert_not_awaited()

    def test_requires_scan_results(self, client: TestClient) -> None:
        """scan_id without scan_results → 400 (no scan store to look it up yet)."""
        resp = client.post("/code/fix", json={"scan_id": "abc123", "fix_types": ["imports"]})
        assert resp.status_code == 400

    def test_no_scan_input_returns_400(self, client: TestClient) -> None:
        """Neither scan_id nor scan_results → 400."""
        resp = client.post("/code/fix", json={"fix_types": ["imports"]})
        assert resp.status_code == 400


class TestSelfLearningRoundTrip:
    """Regression for bug-168 — SelfLearningEngine must survive load→save→load→save.

    The /code/fix tests mock the learner wholesale, so the REAL round-trip was never
    exercised: a reloaded entry kept category/last_used as plain strings and the
    SECOND save() crashed (AttributeError: 'str' object has no attribute 'value'),
    which the endpoint's broad except turned into a 500 on every later call. This
    exercises the real engine + real file I/O to prove the persisted-state path.
    """

    def test_learn_save_reload_save_no_crash(self, tmp_path) -> None:
        import asyncio
        import json

        from agents.coding_doctor_agent import IssueCategory, SelfLearningEngine

        store = tmp_path / "learnings.json"

        async def _cycle() -> dict:
            e1 = SelfLearningEngine(store)
            await e1.initialize()
            e1.learn(IssueCategory.MAINTAINABILITY, "fix_imports", "isort", True)
            await e1.save()

            # Reload the persisted file and save AGAIN — the pre-fix crash point.
            e2 = SelfLearningEngine(store)
            await e2.initialize()
            e2.learn(IssueCategory.MAINTAINABILITY, "fix_imports", "isort", False)
            await e2.save()
            return e2.get_stats()

        stats = asyncio.run(_cycle())
        assert stats["total_patterns"] == 1

        entry = json.loads(store.read_text())["patterns"][0]
        assert entry["category"] == "maintainability"
        # second engine reloaded the first's entry, so outcomes accumulate (learning)
        assert entry["success_count"] == 1
        assert entry["failure_count"] == 1
