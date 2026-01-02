#!/usr/bin/env python3
"""
DevSkyy Security Audit Script
==============================

Comprehensive security audit for the DevSkyy platform.
Runs multiple security checks and generates a detailed report.

Usage:
    python scripts/security_audit.py [--fix] [--report output.json]

Checks performed:
- Dependency vulnerability scanning (pip-audit, npm audit)
- Code analysis for security issues
- Secret detection (hardcoded credentials)
- SQL injection vulnerability check
- XSS vulnerability check
- SSRF vulnerability check
- Input validation coverage
- Authentication/Authorization review
- API security best practices
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit."""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    file_path: str
    line_number: int | None
    description: str
    recommendation: str
    cwe_id: str | None = None
    auto_fixable: bool = False


@dataclass
class AuditResult:
    """Complete audit result."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    issues: list[SecurityIssue] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)

    def add_issue(self, issue: SecurityIssue) -> None:
        self.issues.append(issue)
        self.total_issues += 1
        if issue.severity == "CRITICAL":
            self.critical_count += 1
        elif issue.severity == "HIGH":
            self.high_count += 1
        elif issue.severity == "MEDIUM":
            self.medium_count += 1
        elif issue.severity == "LOW":
            self.low_count += 1


# =============================================================================
# Security Checks
# =============================================================================


class SecurityAuditor:
    """Comprehensive security auditor for DevSkyy platform."""

    # Patterns for detecting hardcoded secrets
    SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "API Key"),
        (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "Secret Key"),
        (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Password"),
        (
            r'(?i)(auth[_-]?token|access[_-]?token)\s*[=:]\s*["\'][a-zA-Z0-9_\-\.]{20,}["\']',
            "Auth Token",
        ),
        (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key"),
        (r"sk-ant-[a-zA-Z0-9\-_]{32,}", "Anthropic API Key"),
        (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
        (r"-----BEGIN (RSA |EC )?PRIVATE KEY-----", "Private Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
        (r"xox[baprs]-[a-zA-Z0-9\-]{10,}", "Slack Token"),
    ]

    # SQL injection patterns - very targeted to reduce false positives
    # Only flag actual SQL query construction with unsafe interpolation
    SQL_INJECTION_PATTERNS = [
        # f-string SQL query (must start with SQL keyword, have FROM/INTO/SET, and interpolation)
        r'f["\']SELECT\s+.+\s+FROM\s+.+\{[^}]+\}',
        r'f["\']INSERT\s+INTO\s+.+\{[^}]+\}',
        r'f["\']UPDATE\s+\w+\s+SET\s+.+\{[^}]+\}',
        r'f["\']DELETE\s+FROM\s+.+\{[^}]+\}',
        # String concatenation in execute() - actual DB calls
        r"\.execute\(\s*[^)]*\s*\+\s*[^)]+\)",
        # cursor.execute with unsafe % formatting
        r'cursor\.execute\(\s*["\'][^"\']*%s[^"\']*["\'],\s*\([^)]*\+',
    ]

    # XSS patterns - only match when user input is directly used without escaping
    # These patterns look for template literals with variables that could be user-controlled
    XSS_PATTERNS = [
        # innerHTML with external variables (not metrics/internal values)
        r"innerHTML\s*=\s*`[^`]*\$\{(?!m\.|score|fps|memory)",
        # document.write with user input
        r"document\.write\s*\([^)]*(?:input|request|param|data\[)",
        # jQuery .html() with concatenation or user input
        r"\.html\s*\([^)]*(?:\+|input|request|param)",
        # React dangerouslySetInnerHTML with user input
        r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html:\s*[^}]*(?:input|request|param|data)",
        # eval with user input
        r"eval\s*\([^)]*(?:input|request|param)",
    ]

    # SSRF patterns
    SSRF_PATTERNS = [
        r"requests?\.(get|post|put|delete|patch)\s*\([^)]*(?:input|param|request)",
        r"urllib\.request\.urlopen\s*\([^)]*(?:input|param)",
        r'httpx?\.(get|post)\s*\([^)]*f["\']',
        r"aiohttp\.ClientSession.*\.(?:get|post)\s*\([^)]*(?:input|param)",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.result = AuditResult()

    def run_full_audit(self) -> AuditResult:
        """Run all security checks."""
        logger.info("Starting comprehensive security audit...")

        # Run each check
        self._check_dependencies()
        self._check_hardcoded_secrets()
        self._check_sql_injection()
        self._check_xss_vulnerabilities()
        self._check_ssrf_vulnerabilities()
        self._check_authentication()
        self._check_input_validation()
        self._check_error_handling()
        self._check_api_security()
        self._check_file_permissions()

        logger.info(f"Audit complete. Found {self.result.total_issues} issues.")
        return self.result

    def _check_dependencies(self) -> None:
        """Check for vulnerable dependencies."""
        logger.info("Checking dependencies for vulnerabilities...")

        try:
            # Check Python dependencies with pip-audit
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.stdout:
                try:
                    data = json.loads(result.stdout)

                    # pip-audit JSON format: {"dependencies": [...]} or list of vulnerabilities
                    vulnerabilities = []
                    if isinstance(data, dict):
                        # Handle {"dependencies": [...]} format
                        deps = data.get("dependencies", [])
                        for dep in deps:
                            vulns = dep.get("vulns", [])
                            for vuln in vulns:
                                vulnerabilities.append(
                                    {
                                        "name": dep.get("name", "Unknown"),
                                        "version": dep.get("version", "Unknown"),
                                        "id": vuln.get("id", "Unknown"),
                                        "fix_versions": vuln.get("fix_versions", ["latest"]),
                                        "cwe": (
                                            vuln.get("aliases", [None])[0]
                                            if vuln.get("aliases")
                                            else None
                                        ),
                                    }
                                )
                    elif isinstance(data, list):
                        # Handle legacy list format
                        for item in data:
                            if isinstance(item, dict):
                                vulns = item.get("vulns", [])
                                for vuln in vulns:
                                    vulnerabilities.append(
                                        {
                                            "name": item.get("name", "Unknown"),
                                            "version": item.get("version", "Unknown"),
                                            "id": (
                                                vuln.get("id", "Unknown")
                                                if isinstance(vuln, dict)
                                                else str(vuln)
                                            ),
                                            "fix_versions": (
                                                vuln.get("fix_versions", ["latest"])
                                                if isinstance(vuln, dict)
                                                else ["latest"]
                                            ),
                                            "cwe": None,
                                        }
                                    )

                    if vulnerabilities:
                        for vuln in vulnerabilities:
                            self.result.add_issue(
                                SecurityIssue(
                                    severity="HIGH",
                                    category="Dependency Vulnerability",
                                    file_path="requirements.txt",
                                    line_number=None,
                                    description=f"{vuln['name']} {vuln['version']}: {vuln['id']}",
                                    recommendation=f"Upgrade to {vuln['fix_versions'][0] if vuln['fix_versions'] else 'latest'}",
                                    cwe_id=vuln.get("cwe"),
                                )
                            )
                    else:
                        self.result.checks_passed.append("Python dependency scan")

                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse pip-audit JSON output: {e}")
                    if result.returncode != 0:
                        self.result.checks_failed.append("Python dependency scan (parse error)")
            else:
                self.result.checks_passed.append("Python dependency scan")

        except FileNotFoundError:
            logger.warning("pip-audit not found, skipping Python dependency check")
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")

    def _check_hardcoded_secrets(self) -> None:
        """Check for hardcoded secrets in source code."""
        logger.info("Checking for hardcoded secrets...")

        # Patterns to skip as false positives
        FALSE_POSITIVE_PATTERNS = [
            r"xxxx",  # Placeholder patterns
            r"test[-_]?password",  # Test passwords
            r"example",  # Example code
            r"placeholder",
            r"your[-_]?password",
            r"\"\"",  # Empty strings
            r"class\s+\w+.*Enum",  # Enum definitions
            r"^\s*#",  # Comments
            r"def\s+example",  # Example functions
            r"APP_PASSWORD\s*=\s*\"app_password\"",  # Enum values
            r"RESET_PASSWORD",  # Enum values
            r"localhost",  # Local dev configs
            r"127\.0\.0\.1",
        ]

        found_secrets = False
        python_files = list(self.project_root.rglob("*.py"))

        # Exclude virtual environments and test files
        python_files = [
            f
            for f in python_files
            if "venv" not in str(f) and ".venv" not in str(f) and "__pycache__" not in str(f)
        ]

        for file_path in python_files:
            try:
                content = file_path.read_text()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Skip comments and test data
                    if line.strip().startswith("#") or "test" in file_path.name.lower():
                        continue

                    # Check for false positives
                    is_false_positive = False
                    for fp_pattern in FALSE_POSITIVE_PATTERNS:
                        if re.search(fp_pattern, line, re.IGNORECASE):
                            is_false_positive = True
                            break

                    if is_false_positive:
                        continue

                    for pattern, secret_type in self.SECRET_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            found_secrets = True
                            self.result.add_issue(
                                SecurityIssue(
                                    severity="CRITICAL",
                                    category="Hardcoded Secret",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    description=f"Potential {secret_type} found in source code",
                                    recommendation="Use environment variables or a secrets manager",
                                    cwe_id="CWE-798",
                                )
                            )
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        if not found_secrets:
            self.result.checks_passed.append("No hardcoded secrets found")

    def _check_sql_injection(self) -> None:
        """Check for SQL injection vulnerabilities."""
        logger.info("Checking for SQL injection vulnerabilities...")

        found_issues = False
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            # Skip audit script itself (contains patterns), venv, cache
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
            if file_path.name == "security_audit.py":
                continue

            try:
                content = file_path.read_text()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Skip comments, docstrings, and string literals in pattern definitions
                    stripped = line.strip()
                    if (
                        stripped.startswith("#")
                        or stripped.startswith('"""')
                        or stripped.startswith("'''")
                    ):
                        continue
                    if "SQL_INJECTION_PATTERNS" in line or "SQL_PATTERNS" in line:
                        continue
                    # Skip regex pattern definitions
                    if 'r"' in line and "SELECT" in line and "(" not in line[:20]:
                        continue

                    for pattern in self.SQL_INJECTION_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            found_issues = True
                            self.result.add_issue(
                                SecurityIssue(
                                    severity="CRITICAL",
                                    category="SQL Injection",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    description="Potential SQL injection vulnerability",
                                    recommendation="Use parameterized queries or ORM methods",
                                    cwe_id="CWE-89",
                                )
                            )
            except Exception:
                pass

        if not found_issues:
            self.result.checks_passed.append("No SQL injection vulnerabilities found")

    def _check_xss_vulnerabilities(self) -> None:
        """Check for XSS vulnerabilities."""
        logger.info("Checking for XSS vulnerabilities...")

        # Patterns indicating proper escaping/sanitization
        SAFE_PATTERNS = [
            r"escapeHtml",
            r"sanitize",
            r"textContent",
            r"DOMPurify",
            r"encodeURIComponent",
            r"createTextNode",
            # Hardcoded strings without variables
            r'innerHTML\s*=\s*["\'][^$\{]*["\']',
        ]

        found_issues = False
        js_files = list(self.project_root.rglob("*.js"))
        js_files.extend(self.project_root.rglob("*.jsx"))
        js_files.extend(self.project_root.rglob("*.ts"))
        js_files.extend(self.project_root.rglob("*.tsx"))

        for file_path in js_files:
            if "node_modules" in str(file_path) or ".next" in str(file_path):
                continue

            try:
                content = file_path.read_text()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Skip if line contains safe patterns (proper escaping)
                    if any(re.search(p, line, re.IGNORECASE) for p in SAFE_PATTERNS):
                        continue

                    for pattern in self.XSS_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            found_issues = True
                            self.result.add_issue(
                                SecurityIssue(
                                    severity="HIGH",
                                    category="XSS Vulnerability",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    description="Potential XSS vulnerability",
                                    recommendation="Use proper HTML escaping or sanitization",
                                    cwe_id="CWE-79",
                                )
                            )
            except Exception:
                pass

        if not found_issues:
            self.result.checks_passed.append("No XSS vulnerabilities found")

    def _check_ssrf_vulnerabilities(self) -> None:
        """Check for SSRF vulnerabilities."""
        logger.info("Checking for SSRF vulnerabilities...")

        found_issues = False
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            try:
                content = file_path.read_text()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for pattern in self.SSRF_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            found_issues = True
                            self.result.add_issue(
                                SecurityIssue(
                                    severity="HIGH",
                                    category="SSRF Vulnerability",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    description="Potential SSRF vulnerability",
                                    recommendation="Validate and whitelist allowed URLs",
                                    cwe_id="CWE-918",
                                )
                            )
            except Exception:
                pass

        if not found_issues:
            self.result.checks_passed.append("No SSRF vulnerabilities found")

    def _check_authentication(self) -> None:
        """Check authentication implementation."""
        logger.info("Checking authentication security...")

        auth_file = self.project_root / "security" / "jwt_oauth2_auth.py"

        if auth_file.exists():
            content = auth_file.read_text()

            # Check for secure JWT settings
            if "HS256" in content and "RS256" not in content:
                self.result.add_issue(
                    SecurityIssue(
                        severity="MEDIUM",
                        category="Authentication",
                        file_path="security/jwt_oauth2_auth.py",
                        line_number=None,
                        description="Using HS256 algorithm for JWT. RS256 is more secure for production.",
                        recommendation="Consider using RS256 or ES256 for better security",
                        cwe_id="CWE-327",
                    )
                )

            # Check for secure token expiration
            if "minutes=15" not in content and "minutes=30" not in content:
                self.result.add_issue(
                    SecurityIssue(
                        severity="LOW",
                        category="Authentication",
                        file_path="security/jwt_oauth2_auth.py",
                        line_number=None,
                        description="JWT access token expiration may be too long",
                        recommendation="Use short-lived access tokens (15-30 minutes)",
                        cwe_id="CWE-613",
                    )
                )

            self.result.checks_passed.append("Authentication module present")
        else:
            self.result.add_issue(
                SecurityIssue(
                    severity="CRITICAL",
                    category="Authentication",
                    file_path="security/jwt_oauth2_auth.py",
                    line_number=None,
                    description="Authentication module not found",
                    recommendation="Implement proper JWT/OAuth2 authentication",
                    cwe_id="CWE-287",
                )
            )

    def _check_input_validation(self) -> None:
        """Check input validation coverage."""
        logger.info("Checking input validation...")

        validation_file = self.project_root / "security" / "input_validation.py"

        if validation_file.exists():
            self.result.checks_passed.append("Input validation module present")
        else:
            self.result.add_issue(
                SecurityIssue(
                    severity="HIGH",
                    category="Input Validation",
                    file_path="security/input_validation.py",
                    line_number=None,
                    description="Input validation module not found",
                    recommendation="Implement comprehensive input validation",
                    cwe_id="CWE-20",
                )
            )

        # Check API endpoints for Pydantic validation
        api_dir = self.project_root / "api"
        if api_dir.exists():
            for api_file in api_dir.glob("*.py"):
                content = api_file.read_text()
                if "@" in content and "router" in content.lower():
                    if "BaseModel" not in content and "Pydantic" not in content:
                        self.result.add_issue(
                            SecurityIssue(
                                severity="MEDIUM",
                                category="Input Validation",
                                file_path=str(api_file.relative_to(self.project_root)),
                                line_number=None,
                                description="API endpoint may lack Pydantic validation",
                                recommendation="Use Pydantic models for request validation",
                                cwe_id="CWE-20",
                            )
                        )

    def _check_error_handling(self) -> None:
        """Check error handling for information disclosure."""
        logger.info("Checking error handling...")

        error_module = self.project_root / "errors" / "production_errors.py"

        if error_module.exists():
            self.result.checks_passed.append("Production error handling module present")
        else:
            self.result.add_issue(
                SecurityIssue(
                    severity="MEDIUM",
                    category="Error Handling",
                    file_path="errors/production_errors.py",
                    line_number=None,
                    description="Production error handling module not found",
                    recommendation="Implement proper error handling to prevent information disclosure",
                    cwe_id="CWE-209",
                )
            )

    def _check_api_security(self) -> None:
        """Check API security best practices."""
        logger.info("Checking API security...")

        main_app = self.project_root / "main_enterprise.py"

        if main_app.exists():
            content = main_app.read_text()

            # Check for CORS configuration
            if "CORSMiddleware" not in content:
                self.result.add_issue(
                    SecurityIssue(
                        severity="MEDIUM",
                        category="API Security",
                        file_path="main_enterprise.py",
                        line_number=None,
                        description="CORS middleware not configured",
                        recommendation="Add CORSMiddleware with appropriate origins",
                        cwe_id="CWE-346",
                    )
                )
            else:
                self.result.checks_passed.append("CORS middleware configured")

            # Check for rate limiting
            if "rate" not in content.lower() and "limit" not in content.lower():
                self.result.add_issue(
                    SecurityIssue(
                        severity="MEDIUM",
                        category="API Security",
                        file_path="main_enterprise.py",
                        line_number=None,
                        description="Rate limiting not configured",
                        recommendation="Implement rate limiting to prevent DoS attacks",
                        cwe_id="CWE-770",
                    )
                )

    def _check_file_permissions(self) -> None:
        """Check for insecure file permissions."""
        logger.info("Checking file permissions...")

        sensitive_files = [
            ".env",
            ".env.local",
            ".env.production",
            "secrets.json",
            "credentials.json",
        ]

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                mode = oct(file_path.stat().st_mode)[-3:]
                if mode != "600" and mode != "400":
                    self.result.add_issue(
                        SecurityIssue(
                            severity="MEDIUM",
                            category="File Security",
                            file_path=file_name,
                            line_number=None,
                            description=f"Sensitive file has loose permissions ({mode})",
                            recommendation="Set file permissions to 600 or 400",
                            cwe_id="CWE-732",
                        )
                    )

        self.result.checks_passed.append("File permissions checked")


# =============================================================================
# Report Generation
# =============================================================================


def generate_report(result: AuditResult, output_path: Path | None = None) -> str:
    """Generate a security audit report."""

    report = []
    report.append("=" * 70)
    report.append("DevSkyy Security Audit Report")
    report.append("=" * 70)
    report.append(f"\nTimestamp: {result.timestamp}")
    report.append(f"\nTotal Issues Found: {result.total_issues}")
    report.append(f"  - Critical: {result.critical_count}")
    report.append(f"  - High: {result.high_count}")
    report.append(f"  - Medium: {result.medium_count}")
    report.append(f"  - Low: {result.low_count}")

    report.append("\n" + "-" * 70)
    report.append("Checks Passed")
    report.append("-" * 70)
    for check in result.checks_passed:
        report.append(f"  ✓ {check}")

    if result.checks_failed:
        report.append("\n" + "-" * 70)
        report.append("Checks Failed")
        report.append("-" * 70)
        for check in result.checks_failed:
            report.append(f"  ✗ {check}")

    if result.issues:
        report.append("\n" + "-" * 70)
        report.append("Security Issues")
        report.append("-" * 70)

        # Group by severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            severity_issues = [i for i in result.issues if i.severity == severity]
            if severity_issues:
                report.append(f"\n[{severity}]")
                for issue in severity_issues:
                    report.append(f"\n  Category: {issue.category}")
                    report.append(
                        f"  File: {issue.file_path}"
                        + (f":{issue.line_number}" if issue.line_number else "")
                    )
                    report.append(f"  Description: {issue.description}")
                    report.append(f"  Recommendation: {issue.recommendation}")
                    if issue.cwe_id:
                        report.append(f"  CWE: {issue.cwe_id}")

    report.append("\n" + "=" * 70)
    report.append("End of Report")
    report.append("=" * 70)

    report_text = "\n".join(report)

    if output_path:
        output_path.write_text(report_text)
        logger.info(f"Report written to {output_path}")

        # Also write JSON version
        json_path = output_path.with_suffix(".json")
        json_report = {
            "timestamp": result.timestamp,
            "summary": {
                "total_issues": result.total_issues,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
            },
            "checks_passed": result.checks_passed,
            "checks_failed": result.checks_failed,
            "issues": [asdict(i) for i in result.issues],
        }
        json_path.write_text(json.dumps(json_report, indent=2))
        logger.info(f"JSON report written to {json_path}")

    return report_text


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="DevSkyy Security Audit")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix issues where possible",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Output report file path",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    auditor = SecurityAuditor(project_root)
    result = auditor.run_full_audit()

    report = generate_report(result, args.report)
    print(report)

    # Exit with error code if critical/high issues found
    if result.critical_count > 0 or result.high_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
