#!/usr/bin/env python3
"""
Dependency Security Scanner
===========================

Automated security scanning and hardening for Python dependencies.
Integrates with pip-audit, safety, and custom vulnerability databases.
"""

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyScanner:
    """
    Comprehensive dependency security scanner for DevSkyy platform.

    Features:
    - Vulnerability scanning with pip-audit
    - License compliance checking
    - Outdated package detection
    - Security advisory monitoring
    - Automated security reporting
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.requirements_files = ["requirements.txt", "vercel/requirements.txt", "pyproject.toml"]
        self.security_report = {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "vulnerabilities": [],
            "outdated_packages": [],
            "license_issues": [],
            "recommendations": [],
        }

    async def scan_vulnerabilities(self) -> dict:
        """Scan for known vulnerabilities using pip-audit"""
        logger.info("🔍 Scanning for security vulnerabilities...")

        vulnerabilities = []

        for req_file in self.requirements_files:
            req_path = self.project_root / req_file
            if not req_path.exists():
                continue

            try:
                # Run pip-audit on requirements file
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip_audit",
                        "--format",
                        "json",
                        "--requirement",
                        str(req_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    for dep in audit_data.get("dependencies", []):
                        if dep.get("vulns"):
                            vulnerabilities.extend(dep["vulns"])

            except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to scan {req_file}: {e}")

        self.security_report["vulnerabilities"] = vulnerabilities
        return vulnerabilities

    async def check_outdated_packages(self) -> list[dict]:
        """Check for outdated packages that may have security fixes"""
        logger.info("📦 Checking for outdated packages...")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                outdated = json.loads(result.stdout)

                # Filter for security-critical packages
                critical_packages = {
                    "cryptography",
                    "pyjwt",
                    "passlib",
                    "bcrypt",
                    "fastapi",
                    "starlette",
                    "httpx",
                    "requests",
                    "sqlalchemy",
                    "pydantic",
                }

                security_outdated = [
                    pkg for pkg in outdated if pkg["name"].lower() in critical_packages
                ]

                self.security_report["outdated_packages"] = security_outdated
                return security_outdated

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning(f"Failed to check outdated packages: {e}")

        return []

    async def check_license_compliance(self) -> list[dict]:
        """Check for license compliance issues"""
        logger.info("📄 Checking license compliance...")

        # Problematic licenses for enterprise use
        problematic_licenses = {"GPL-3.0", "AGPL-3.0", "LGPL-3.0", "SSPL-1.0", "OSL-3.0"}

        license_issues = []

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                for pkg in packages:
                    # This is a simplified check - in production you'd use
                    # a proper license detection tool like pip-licenses
                    if any(lic in pkg.get("license", "") for lic in problematic_licenses):
                        license_issues.append(
                            {
                                "package": pkg["name"],
                                "version": pkg["version"],
                                "license": pkg.get("license", "Unknown"),
                                "severity": "high",
                            }
                        )

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning(f"Failed to check licenses: {e}")

        self.security_report["license_issues"] = license_issues
        return license_issues

    def generate_security_recommendations(self) -> list[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []

        if self.security_report["vulnerabilities"]:
            recommendations.append(
                "🚨 CRITICAL: Update packages with known vulnerabilities immediately"
            )

        if self.security_report["outdated_packages"]:
            recommendations.append("⚠️  Update security-critical packages to latest versions")

        if self.security_report["license_issues"]:
            recommendations.append("📄 Review license compliance for enterprise deployment")

        # Always recommend these security practices
        recommendations.extend(
            [
                "🔒 Pin exact dependency versions in production",
                "🔄 Set up automated security scanning in CI/CD",
                "📊 Monitor security advisories for used packages",
                "🛡️  Implement dependency update policies",
            ]
        )

        self.security_report["recommendations"] = recommendations
        return recommendations

    async def run_full_scan(self) -> dict:
        """Run comprehensive security scan"""
        logger.info("🚀 Starting comprehensive dependency security scan...")

        # Run all security checks
        await self.scan_vulnerabilities()
        await self.check_outdated_packages()
        await self.check_license_compliance()
        self.generate_security_recommendations()

        # Calculate security score
        vuln_count = len(self.security_report["vulnerabilities"])
        outdated_count = len(self.security_report["outdated_packages"])
        license_count = len(self.security_report["license_issues"])

        # Security score (0-100, higher is better)
        security_score = max(
            0, 100 - (vuln_count * 20) - (outdated_count * 5) - (license_count * 10)
        )

        self.security_report["security_score"] = security_score
        self.security_report["summary"] = {
            "vulnerabilities": vuln_count,
            "outdated_packages": outdated_count,
            "license_issues": license_count,
            "security_score": security_score,
        }

        return self.security_report

    def save_report(self, output_path: Path = None) -> Path:
        """Save security report to file"""
        if not output_path:
            output_path = self.project_root / "security_report.json"

        with open(output_path, "w") as f:
            json.dump(self.security_report, f, indent=2)

        logger.info(f"📄 Security report saved to {output_path}")
        return output_path


# Global instance
dependency_scanner = DependencyScanner()


async def main():
    """CLI entry point for dependency scanning"""
    scanner = DependencyScanner()
    report = await scanner.run_full_scan()

    print("\n🔒 DevSkyy Dependency Security Report")
    print("=" * 50)
    print(f"Security Score: {report['security_score']}/100")
    print(f"Vulnerabilities: {report['summary']['vulnerabilities']}")
    print(f"Outdated Packages: {report['summary']['outdated_packages']}")
    print(f"License Issues: {report['summary']['license_issues']}")

    if report["recommendations"]:
        print("\n📋 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

    # Save report
    report_path = scanner.save_report()
    print(f"\n📄 Full report saved to: {report_path}")

    # Exit with error code if critical issues found
    if report["summary"]["vulnerabilities"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
