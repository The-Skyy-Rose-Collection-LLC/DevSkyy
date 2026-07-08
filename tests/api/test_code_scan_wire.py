"""Wire tests for /code/scan endpoint (T3-1).

Verifies:
- Real delegation to CodeSecurityAnalyzer (monkeypatched to avoid FS scanning)
- Field-level SecurityFinding → ScanIssue mapping is exact, not approximated
- Summary counts derived from real findings (not hardcoded)
- Path-containment guard rejects paths outside PROJECT_ROOT with 400
- Non-existent in-project paths return 404
"""

from pathlib import Path
from unittest.mock import patch

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


@pytest.fixture()
def client() -> TestClient:
    """Isolated FastAPI app with auth dependency bypassed."""
    app = FastAPI()
    app.include_router(code_router)
    app.dependency_overrides[get_current_user] = lambda: _mock_user()
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
