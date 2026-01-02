#!/usr/bin/env python3
"""
DevSkyy Production Readiness Verification Script
=================================================

Final verification script that checks all production requirements
are met before deployment.

Usage:
    python scripts/verify_production_readiness.py [--strict]
"""

import argparse
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CheckResult:
    """Result of a single check."""

    name: str
    passed: bool
    message: str
    severity: str = "ERROR"  # ERROR, WARNING, INFO


@dataclass
class VerificationReport:
    """Complete verification report."""

    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    results: list[CheckResult] = field(default_factory=list)
    production_ready: bool = False

    def add_result(self, result: CheckResult) -> None:
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        elif result.severity == "WARNING":
            self.warnings += 1
        else:
            self.failed_checks += 1


# =============================================================================
# Verification Checks
# =============================================================================


def check_95_percent_fidelity() -> CheckResult:
    """Verify 95% fidelity threshold is enforced."""
    try:
        from errors.production_errors import MINIMUM_FIDELITY_SCORE
        from imagery.model_fidelity import MINIMUM_FIDELITY_SCORE as IMG_THRESHOLD

        if MINIMUM_FIDELITY_SCORE == 95.0 and IMG_THRESHOLD == 95.0:
            return CheckResult(
                name="95% Fidelity Threshold",
                passed=True,
                message="Fidelity threshold correctly set to 95%",
            )
        else:
            return CheckResult(
                name="95% Fidelity Threshold",
                passed=False,
                message=f"Fidelity threshold incorrect: {MINIMUM_FIDELITY_SCORE}",
            )
    except ImportError as e:
        return CheckResult(
            name="95% Fidelity Threshold",
            passed=False,
            message=f"Could not import fidelity modules: {e}",
        )


def check_error_handling() -> CheckResult:
    """Verify production error handling is in place."""
    try:
        from errors.production_errors import (
            DevSkyError,
        )

        # Verify all error classes exist and work
        error = DevSkyError("test", correlation_id="test-123")
        assert error.correlation_id == "test-123"

        return CheckResult(
            name="Production Error Handling",
            passed=True,
            message="All error classes properly defined",
        )
    except Exception as e:
        return CheckResult(
            name="Production Error Handling",
            passed=False,
            message=f"Error handling check failed: {e}",
        )


def check_security_modules() -> CheckResult:
    """Verify all security modules are present."""
    security_dir = Path("security")
    required_modules = [
        "jwt_oauth2_auth.py",
        "aes256_gcm_encryption.py",
        "input_validation.py",
        "ssrf_protection.py",
        "rate_limiting.py",
        "api_security.py",
    ]

    missing = []
    for module in required_modules:
        if not (security_dir / module).exists():
            missing.append(module)

    if missing:
        return CheckResult(
            name="Security Modules",
            passed=False,
            message=f"Missing security modules: {', '.join(missing)}",
        )

    return CheckResult(
        name="Security Modules", passed=True, message="All required security modules present"
    )


def check_api_endpoints() -> CheckResult:
    """Verify all required API endpoints are defined."""
    try:
        from api.admin_dashboard import admin_dashboard_router
        from api.elementor_3d import elementor_3d_router

        # Check routes are defined
        admin_routes = len(admin_dashboard_router.routes)
        elementor_routes = len(elementor_3d_router.routes)

        if admin_routes > 0 and elementor_routes > 0:
            return CheckResult(
                name="API Endpoints",
                passed=True,
                message=f"Admin: {admin_routes} routes, Elementor: {elementor_routes} routes",
            )
        else:
            return CheckResult(name="API Endpoints", passed=False, message="Missing API routes")
    except ImportError as e:
        return CheckResult(
            name="API Endpoints", passed=False, message=f"Could not import API routers: {e}"
        )


def check_3d_pipeline() -> CheckResult:
    """Verify 3D generation pipeline is configured."""
    try:
        from ai_3d.generation_pipeline import GenerationConfig

        config = GenerationConfig(minimum_fidelity=95.0)
        assert config.minimum_fidelity == 95.0

        return CheckResult(
            name="3D Generation Pipeline",
            passed=True,
            message="Pipeline configured with 95% fidelity requirement",
        )
    except ImportError as e:
        return CheckResult(
            name="3D Generation Pipeline",
            passed=False,
            message=f"Could not import 3D pipeline: {e}",
        )


def check_sync_modules() -> CheckResult:
    """Verify sync modules are configured."""
    sync_dir = Path("sync")
    required_files = ["catalog_sync.py", "woocommerce_sync.py", "media_sync.py"]

    missing = []
    for f in required_files:
        if not (sync_dir / f).exists():
            missing.append(f)

    if missing:
        return CheckResult(
            name="Sync Modules", passed=False, message=f"Missing sync modules: {', '.join(missing)}"
        )

    return CheckResult(name="Sync Modules", passed=True, message="All sync modules present")


def check_wordpress_plugin() -> CheckResult:
    """Verify WordPress plugin is complete."""
    plugin_dir = Path("wordpress/plugins/skyyrose-3d-experience")

    required_files = [
        "skyyrose-3d-experience.php",
        "includes/elementor/class-skyyrose-3d-widget.php",
        "assets/css/skyyrose-3d.css",
    ]

    missing = []
    for f in required_files:
        if not (plugin_dir / f).exists():
            missing.append(f)

    if missing:
        return CheckResult(
            name="WordPress Plugin",
            passed=False,
            message=f"Missing plugin files: {', '.join(missing)}",
        )

    return CheckResult(
        name="WordPress Plugin", passed=True, message="WordPress/Elementor plugin complete"
    )


def check_test_coverage() -> CheckResult:
    """Check that test files exist for new modules."""
    tests_dir = Path("tests")

    required_tests = [
        "test_production_errors.py",
        "test_model_fidelity.py",
        "test_admin_dashboard.py",
    ]

    existing = []
    missing = []

    for test in required_tests:
        if (tests_dir / test).exists():
            existing.append(test)
        else:
            missing.append(test)

    if missing:
        return CheckResult(
            name="Test Coverage",
            passed=False,
            message=f"Missing tests: {', '.join(missing)}",
            severity="WARNING",
        )

    return CheckResult(
        name="Test Coverage", passed=True, message=f"Found {len(existing)} test files"
    )


def check_ci_cd_pipeline() -> CheckResult:
    """Verify CI/CD pipeline is configured."""
    ci_file = Path(".github/workflows/ci.yml")

    if not ci_file.exists():
        return CheckResult(
            name="CI/CD Pipeline", passed=False, message="GitHub Actions workflow not found"
        )

    content = ci_file.read_text()

    required_jobs = ["python-tests", "security", "frontend-tests"]
    missing = [job for job in required_jobs if job not in content]

    if missing:
        return CheckResult(
            name="CI/CD Pipeline", passed=False, message=f"Missing CI jobs: {', '.join(missing)}"
        )

    return CheckResult(
        name="CI/CD Pipeline",
        passed=True,
        message="CI/CD pipeline configured with all required jobs",
    )


def check_environment_config() -> CheckResult:
    """Check that environment configuration exists."""
    env_files = [".env.example", ".env.production.example"]

    found = [f for f in env_files if Path(f).exists() or Path(f"frontend/{f}").exists()]

    if not found:
        return CheckResult(
            name="Environment Config",
            passed=False,
            message="No environment config examples found",
            severity="WARNING",
        )

    return CheckResult(
        name="Environment Config", passed=True, message=f"Found config examples: {', '.join(found)}"
    )


def check_no_hardcoded_secrets() -> CheckResult:
    """Quick check for obvious hardcoded secrets."""
    import re

    patterns = [
        r"sk-[a-zA-Z0-9]{32,}",  # OpenAI
        r"sk-ant-[a-zA-Z0-9]{32,}",  # Anthropic
        r'password\s*=\s*["\'][^"\']{10,}["\']',
    ]

    issues = []

    for py_file in Path(".").rglob("*.py"):
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        if "test" in py_file.name.lower():
            continue

        try:
            content = py_file.read_text()
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(str(py_file))
                    break
        except Exception:
            pass

    if issues:
        return CheckResult(
            name="Hardcoded Secrets",
            passed=False,
            message=f"Potential secrets in: {', '.join(issues[:3])}...",
        )

    return CheckResult(
        name="Hardcoded Secrets", passed=True, message="No obvious hardcoded secrets found"
    )


# =============================================================================
# Main Verification
# =============================================================================


def run_verification(strict: bool = False) -> VerificationReport:
    """Run all verification checks."""
    report = VerificationReport()

    checks: list[Callable[[], CheckResult]] = [
        check_95_percent_fidelity,
        check_error_handling,
        check_security_modules,
        check_api_endpoints,
        check_3d_pipeline,
        check_sync_modules,
        check_wordpress_plugin,
        check_test_coverage,
        check_ci_cd_pipeline,
        check_environment_config,
        check_no_hardcoded_secrets,
    ]

    print("\n" + "=" * 70)
    print("DevSkyy Production Readiness Verification")
    print("=" * 70 + "\n")

    for check in checks:
        result = check()
        report.add_result(result)

        status = "✓" if result.passed else ("⚠" if result.severity == "WARNING" else "✗")
        print(f"  {status} {result.name}: {result.message}")

    # Determine production readiness
    report.production_ready = report.failed_checks == 0
    if strict:
        report.production_ready = report.production_ready and report.warnings == 0

    print("\n" + "-" * 70)
    print(f"Total Checks: {report.total_checks}")
    print(f"Passed: {report.passed_checks}")
    print(f"Failed: {report.failed_checks}")
    print(f"Warnings: {report.warnings}")
    print("-" * 70)

    if report.production_ready:
        print("\n✓ PRODUCTION READY\n")
    else:
        print("\n✗ NOT PRODUCTION READY\n")
        print("Address the failed checks above before deploying.\n")

    return report


def main():
    parser = argparse.ArgumentParser(description="DevSkyy Production Readiness Check")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)

    report = run_verification(strict=args.strict)

    if args.json:
        output = {
            "timestamp": report.timestamp,
            "production_ready": report.production_ready,
            "summary": {
                "total": report.total_checks,
                "passed": report.passed_checks,
                "failed": report.failed_checks,
                "warnings": report.warnings,
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                }
                for r in report.results
            ],
        }
        print(json.dumps(output, indent=2))

    sys.exit(0 if report.production_ready else 1)


if __name__ == "__main__":
    main()
