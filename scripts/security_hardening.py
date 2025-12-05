#!/usr/bin/env python3
"""
Security Hardening Script for DevSkyy Platform

Implements security recommendations from the security assessment.
Run this script to apply security hardening measures.

Author: DevSkyy Security Team
Date: 2025-12-05

Usage:
    python scripts/security_hardening.py --check    # Check security status
    python scripts/security_hardening.py --apply    # Apply hardening measures
    python scripts/security_hardening.py --report   # Generate security report
"""

import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
SECURITY_DIR = PROJECT_ROOT / "security"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

# ============================================================================
# SECURITY CHECKS
# ============================================================================


class SecurityCheck:
    """Base class for security checks."""

    def __init__(self, name: str, severity: str):
        self.name = name
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.status = "PENDING"
        self.message = ""

    def check(self) -> bool:
        """Run security check. Return True if check passes."""
        raise NotImplementedError

    def fix(self) -> bool:
        """Apply security fix. Return True if fix succeeds."""
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """Convert check to dictionary."""
        return {
            "name": self.name,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
        }


class SecretKeyCheck(SecurityCheck):
    """Check if SECRET_KEY is set in environment."""

    def __init__(self):
        super().__init__("SECRET_KEY Environment Variable", "CRITICAL")

    def check(self) -> bool:
        """Check if SECRET_KEY is set."""
        secret_key = os.getenv("SECRET_KEY")
        jwt_secret = os.getenv("JWT_SECRET_KEY")

        if not secret_key and not jwt_secret:
            self.status = "FAIL"
            self.message = "SECRET_KEY and JWT_SECRET_KEY not set in environment"
            return False

        if secret_key and len(secret_key) < 32:
            self.status = "FAIL"
            self.message = f"SECRET_KEY too short ({len(secret_key)} chars, need 32+)"
            return False

        self.status = "PASS"
        self.message = "SECRET_KEY properly configured"
        return True

    def fix(self) -> bool:
        """Generate secure SECRET_KEY."""
        try:
            secret_key = secrets.token_urlsafe(32)
            print(f"\n✅ Generated secure SECRET_KEY:")
            print(f"   SECRET_KEY={secret_key}")
            print("\n⚠️  Add this to your .env file (DO NOT commit to git)")
            return True
        except Exception as e:
            print(f"❌ Failed to generate SECRET_KEY: {e}")
            return False


class EncryptionKeyCheck(SecurityCheck):
    """Check if ENCRYPTION_MASTER_KEY is set."""

    def __init__(self):
        super().__init__("Encryption Master Key", "HIGH")

    def check(self) -> bool:
        """Check if ENCRYPTION_MASTER_KEY is set."""
        encryption_key = os.getenv("ENCRYPTION_MASTER_KEY")

        if not encryption_key:
            self.status = "FAIL"
            self.message = "ENCRYPTION_MASTER_KEY not set"
            return False

        self.status = "PASS"
        self.message = "ENCRYPTION_MASTER_KEY configured"
        return True

    def fix(self) -> bool:
        """Generate encryption master key."""
        try:
            import base64

            key = secrets.token_bytes(32)  # 256 bits
            key_b64 = base64.b64encode(key).decode()

            print(f"\n✅ Generated encryption master key:")
            print(f"   ENCRYPTION_MASTER_KEY={key_b64}")
            print("\n⚠️  Add this to your .env file (DO NOT commit to git)")
            return True
        except Exception as e:
            print(f"❌ Failed to generate encryption key: {e}")
            return False


class HardcodedSecretsCheck(SecurityCheck):
    """Check for hardcoded secrets in code."""

    def __init__(self):
        super().__init__("Hardcoded Secrets Scan", "CRITICAL")

    def check(self) -> bool:
        """Scan for hardcoded secrets."""
        # Patterns to detect
        patterns = [
            (r"password\s*=\s*['\"][^'\"]{5,}['\"]", "Hardcoded password"),
            (r"api_key\s*=\s*['\"][^'\"]{10,}['\"]", "Hardcoded API key"),
            (r"sk-[a-zA-Z0-9]{20,}", "Anthropic/OpenAI API key"),
            (r"SECRET_KEY\s*=\s*['\"][^'\"]{10,}['\"]", "Hardcoded SECRET_KEY"),
        ]

        findings = []

        # Scan Python files
        for py_file in PROJECT_ROOT.rglob("*.py"):
            # Skip test files and virtual environments
            if "test" in str(py_file) or "venv" in str(py_file) or ".venv" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        findings.append(
                            {
                                "file": str(py_file.relative_to(PROJECT_ROOT)),
                                "description": description,
                                "snippet": match.group(0)[:50],
                            }
                        )
            except Exception:
                continue

        if findings:
            self.status = "FAIL"
            self.message = f"Found {len(findings)} potential hardcoded secrets"
            print("\n⚠️  Potential hardcoded secrets found:")
            for finding in findings:
                print(f"   {finding['file']}: {finding['description']}")
            return False

        self.status = "PASS"
        self.message = "No hardcoded secrets detected"
        return True

    def fix(self) -> bool:
        """Cannot automatically fix hardcoded secrets."""
        print("\n⚠️  Manual action required:")
        print("   1. Review flagged files")
        print("   2. Move secrets to environment variables")
        print("   3. Update code to use os.getenv()")
        print("   4. Add secrets to .env (which is in .gitignore)")
        return False


class CSPHeaderCheck(SecurityCheck):
    """Check Content Security Policy configuration."""

    def __init__(self):
        super().__init__("Content Security Policy", "MEDIUM")

    def check(self) -> bool:
        """Check if CSP is properly configured."""
        middleware_file = SECURITY_DIR / "csp_nonce_middleware.py"

        if not middleware_file.exists():
            self.status = "FAIL"
            self.message = "Enhanced CSP middleware not found"
            return False

        # Check if CSP middleware is integrated in main.py
        main_file = PROJECT_ROOT / "main.py"
        if main_file.exists():
            content = main_file.read_text()
            if "CSPNonceMiddleware" not in content:
                self.status = "WARN"
                self.message = "CSP middleware exists but not integrated in main.py"
                return False

        self.status = "PASS"
        self.message = "Enhanced CSP middleware configured"
        return True

    def fix(self) -> bool:
        """Print instructions for CSP integration."""
        print("\n✅ Enhanced CSP middleware available at:")
        print("   security/csp_nonce_middleware.py")
        print("\n📝 Integration instructions:")
        print("   1. Import: from security.csp_nonce_middleware import CSPNonceMiddleware")
        print("   2. Add middleware to main.py:")
        print("      app.add_middleware(CSPNonceMiddleware,")
        print("          allowed_image_domains=['cdn.example.com'],")
        print("          report_uri='/api/v1/csp-report')")
        print("   3. Use nonces in templates:")
        print("      <script nonce=\"{{ request.state.csp_nonce }}\">...</script>")
        return True


class SSRFProtectionCheck(SecurityCheck):
    """Check SSRF protection implementation."""

    def __init__(self):
        super().__init__("SSRF Protection", "HIGH")

    def check(self) -> bool:
        """Check if SSRF protection is implemented."""
        ssrf_file = SECURITY_DIR / "ssrf_protection.py"

        if not ssrf_file.exists():
            self.status = "FAIL"
            self.message = "SSRF protection module not found"
            return False

        self.status = "PASS"
        self.message = "SSRF protection module available"
        return True

    def fix(self) -> bool:
        """Print instructions for SSRF protection."""
        print("\n✅ SSRF protection module available at:")
        print("   security/ssrf_protection.py")
        print("\n📝 Integration instructions:")
        print("   1. Import: from security.ssrf_protection import validate_webhook_url")
        print("   2. Validate URLs before making requests:")
        print("      validate_webhook_url(url)")
        print("   3. Use SSRFSafeHTTPClient for outbound requests:")
        print("      client = SSRFSafeHTTPClient(allowed_domains=['api.example.com'])")
        return True


class DependencyVulnerabilitiesCheck(SecurityCheck):
    """Check for dependency vulnerabilities."""

    def __init__(self):
        super().__init__("Dependency Vulnerabilities", "HIGH")

    def check(self) -> bool:
        """Check dependencies for known vulnerabilities."""
        try:
            import subprocess

            # Try pip-audit
            result = subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                self.status = "WARN"
                self.message = "pip-audit not installed"
                return False

            # Run pip-audit
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                if vulnerabilities.get("vulnerabilities"):
                    count = len(vulnerabilities["vulnerabilities"])
                    self.status = "FAIL"
                    self.message = f"Found {count} vulnerable dependencies"
                    return False

            self.status = "PASS"
            self.message = "No known vulnerabilities in dependencies"
            return True

        except FileNotFoundError:
            self.status = "WARN"
            self.message = "pip-audit not installed (run: pip install pip-audit)"
            return False
        except Exception as e:
            self.status = "ERROR"
            self.message = f"Dependency check failed: {e}"
            return False

    def fix(self) -> bool:
        """Attempt to fix vulnerable dependencies."""
        print("\n📝 Dependency vulnerability remediation:")
        print("   1. Install pip-audit: pip install pip-audit")
        print("   2. Run scan: pip-audit")
        print("   3. Update vulnerable packages: pip install --upgrade <package>")
        print("   4. Re-run pip-audit to verify")
        return True


class DebugModeCheck(SecurityCheck):
    """Check if DEBUG mode is disabled in production."""

    def __init__(self):
        super().__init__("Debug Mode Configuration", "MEDIUM")

    def check(self) -> bool:
        """Check if DEBUG is disabled in production."""
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]

        if environment == "production" and debug:
            self.status = "FAIL"
            self.message = "DEBUG mode enabled in production"
            return False

        self.status = "PASS"
        self.message = f"DEBUG mode properly configured (env: {environment}, debug: {debug})"
        return True

    def fix(self) -> bool:
        """Print fix instructions."""
        print("\n⚠️  Set in .env file:")
        print("   ENVIRONMENT=production")
        print("   DEBUG=False")
        return True


# ============================================================================
# SECURITY HARDENING RUNNER
# ============================================================================


class SecurityHardeningRunner:
    """Runs security checks and applies fixes."""

    def __init__(self):
        self.checks = [
            SecretKeyCheck(),
            EncryptionKeyCheck(),
            HardcodedSecretsCheck(),
            CSPHeaderCheck(),
            SSRFProtectionCheck(),
            DependencyVulnerabilitiesCheck(),
            DebugModeCheck(),
        ]

    def run_checks(self) -> dict[str, Any]:
        """Run all security checks."""
        print("\n" + "=" * 60)
        print("DevSkyy Security Hardening - Running Checks")
        print("=" * 60 + "\n")

        results = {"timestamp": datetime.now().isoformat(), "checks": []}

        for check in self.checks:
            print(f"🔍 Checking: {check.name}...", end=" ")
            passed = check.check()
            print(f"[{check.status}]")

            results["checks"].append(check.to_dict())

        # Summary
        passed_count = sum(1 for c in self.checks if c.status == "PASS")
        failed_count = sum(1 for c in self.checks if c.status == "FAIL")
        warn_count = sum(1 for c in self.checks if c.status == "WARN")

        results["summary"] = {
            "total": len(self.checks),
            "passed": passed_count,
            "failed": failed_count,
            "warnings": warn_count,
        }

        print("\n" + "=" * 60)
        print("Summary:")
        print(f"  ✅ Passed:   {passed_count}/{len(self.checks)}")
        print(f"  ❌ Failed:   {failed_count}/{len(self.checks)}")
        print(f"  ⚠️  Warnings: {warn_count}/{len(self.checks)}")
        print("=" * 60 + "\n")

        return results

    def apply_fixes(self):
        """Apply security fixes."""
        print("\n" + "=" * 60)
        print("DevSkyy Security Hardening - Applying Fixes")
        print("=" * 60 + "\n")

        for check in self.checks:
            if check.status == "FAIL" or check.status == "WARN":
                print(f"\n🔧 Fixing: {check.name}")
                check.fix()

    def generate_report(self, results: dict[str, Any]):
        """Generate security report."""
        ARTIFACTS_DIR.mkdir(exist_ok=True)

        report_file = ARTIFACTS_DIR / f"security-hardening-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        with open(report_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Security report saved to: {report_file}")

        # Generate markdown report
        md_file = report_file.with_suffix(".md")
        with open(md_file, "w") as f:
            f.write(f"# Security Hardening Report\n\n")
            f.write(f"**Date**: {results['timestamp']}\n\n")
            f.write(f"## Summary\n\n")
            f.write(f"- Total Checks: {results['summary']['total']}\n")
            f.write(f"- Passed: {results['summary']['passed']}\n")
            f.write(f"- Failed: {results['summary']['failed']}\n")
            f.write(f"- Warnings: {results['summary']['warnings']}\n\n")
            f.write(f"## Check Results\n\n")

            for check in results["checks"]:
                status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(check["status"], "❓")
                f.write(f"### {status_emoji} {check['name']} ({check['severity']})\n\n")
                f.write(f"**Status**: {check['status']}\n\n")
                f.write(f"**Message**: {check['message']}\n\n")

        print(f"📄 Markdown report saved to: {md_file}")


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DevSkyy Security Hardening")
    parser.add_argument("--check", action="store_true", help="Run security checks")
    parser.add_argument("--apply", action="store_true", help="Apply security fixes")
    parser.add_argument("--report", action="store_true", help="Generate security report")

    args = parser.parse_args()

    runner = SecurityHardeningRunner()

    if not any([args.check, args.apply, args.report]):
        # Default: run checks
        results = runner.run_checks()
        runner.generate_report(results)
    else:
        if args.check or args.report:
            results = runner.run_checks()
            if args.report:
                runner.generate_report(results)

        if args.apply:
            runner.apply_fixes()


if __name__ == "__main__":
    main()
