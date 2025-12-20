#!/usr/bin/env python3
"""
OWASP ZAP Results Parser
Parses ZAP JSON reports, categorizes findings, extracts evidence,
generates human-readable reports, and identifies false positives.
"""

import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class Severity(Enum):
    """Severity levels mapping ZAP risk to standard severity"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OWASPCategory(Enum):
    """OWASP Top 10 Categories"""

    A01_BROKEN_ACCESS_CONTROL = "A01:2021 - Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_DATA_INTEGRITY = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"
    OTHER = "Other Security Issues"


@dataclass
class ZAPFinding:
    """Structured ZAP finding"""

    id: str
    title: str
    severity: str
    confidence: str
    description: str
    solution: str
    reference: str
    owasp_category: str
    cwe_id: Optional[str]
    wasc_id: Optional[str]
    instances: list[dict[str, Any]]
    is_false_positive: bool
    false_positive_reason: Optional[str]
    remediation_status: str
    remediation_notes: Optional[str]


class ZAPResultsParser:
    """Parser for OWASP ZAP JSON reports"""

    # Known false positive patterns
    FALSE_POSITIVE_PATTERNS = [
        {
            "alert": "X-Frame-Options Header Not Set",
            "pattern": "api/",
            "reason": "API endpoints don't need X-Frame-Options",
        },
        {
            "alert": "Content Security Policy (CSP) Header Not Set",
            "pattern": "/static/",
            "reason": "Static assets served separately with appropriate headers",
        },
        {
            "alert": "Cookie Without SameSite Attribute",
            "pattern": "__vercel_",
            "reason": "Vercel infrastructure cookies",
        },
    ]

    # OWASP mapping based on alert names
    OWASP_MAPPING = {
        "SQL Injection": OWASPCategory.A03_INJECTION,
        "Cross Site Scripting": OWASPCategory.A03_INJECTION,
        "Path Traversal": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        "Remote Code Execution": OWASPCategory.A03_INJECTION,
        "Authentication": OWASPCategory.A07_AUTH_FAILURES,
        "Session": OWASPCategory.A07_AUTH_FAILURES,
        "CSRF": OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        "Insecure Cryptographic": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "TLS": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "SSL": OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
        "Content Security Policy": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "X-Frame-Options": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "X-Content-Type": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "Server Leaks": OWASPCategory.A05_SECURITY_MISCONFIGURATION,
        "SSRF": OWASPCategory.A10_SSRF,
        "XXE": OWASPCategory.A03_INJECTION,
        "Deserialization": OWASPCategory.A08_DATA_INTEGRITY,
    }

    def __init__(self):
        self.findings: list[ZAPFinding] = []
        self.statistics: dict[str, Any] = {}

    def map_severity(self, zap_risk: str) -> str:
        """Map ZAP risk level to standard severity"""
        mapping = {
            "High": Severity.CRITICAL.value,
            "Medium": Severity.HIGH.value,
            "Low": Severity.MEDIUM.value,
            "Informational": Severity.INFO.value,
        }
        return mapping.get(zap_risk, Severity.INFO.value)

    def determine_owasp_category(self, alert_name: str) -> str:
        """Determine OWASP Top 10 category from alert name"""
        for keyword, category in self.OWASP_MAPPING.items():
            if keyword.lower() in alert_name.lower():
                return category.value
        return OWASPCategory.OTHER.value

    def is_false_positive(self, alert: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check if finding is a known false positive"""
        alert_name = alert.get("alert", "")

        for instance in alert.get("instances", []):
            url = instance.get("uri", "")

            for fp_pattern in self.FALSE_POSITIVE_PATTERNS:
                if (
                    fp_pattern["alert"].lower() in alert_name.lower()
                    and fp_pattern["pattern"] in url
                ):
                    return True, fp_pattern["reason"]

        return False, None

    def extract_cwe_id(self, alert: dict[str, Any]) -> Optional[str]:
        """Extract CWE ID from alert reference"""
        cweid = alert.get("cweid")
        if cweid:
            return f"CWE-{cweid}"

        # Try to extract from reference
        reference = alert.get("reference", "")
        if "CWE-" in reference:
            # Extract CWE-XXX pattern
            import re

            match = re.search(r"CWE-(\d+)", reference)
            if match:
                return f"CWE-{match.group(1)}"

        return None

    def parse_report(self, zap_report_path: Path) -> None:
        """Parse ZAP JSON report"""
        print(f"Parsing ZAP report: {zap_report_path}")

        with open(zap_report_path) as f:
            data = json.load(f)

        alerts = data.get("alerts", [])
        print(f"Found {len(alerts)} unique alert types")

        for alert in alerts:
            is_fp, fp_reason = self.is_false_positive(alert)

            finding = ZAPFinding(
                id=str(alert.get("pluginid", "")),
                title=alert.get("alert", "Unknown Alert"),
                severity=self.map_severity(alert.get("risk", "Informational")),
                confidence=alert.get("confidence", "Unknown"),
                description=alert.get("description", ""),
                solution=alert.get("solution", ""),
                reference=alert.get("reference", ""),
                owasp_category=self.determine_owasp_category(alert.get("alert", "")),
                cwe_id=self.extract_cwe_id(alert),
                wasc_id=str(alert.get("wascid", "")) if alert.get("wascid") else None,
                instances=[
                    {
                        "url": instance.get("uri", ""),
                        "method": instance.get("method", ""),
                        "param": instance.get("param", ""),
                        "attack": instance.get("attack", ""),
                        "evidence": instance.get("evidence", ""),
                    }
                    for instance in alert.get("instances", [])
                ],
                is_false_positive=is_fp,
                false_positive_reason=fp_reason,
                remediation_status="pending",
                remediation_notes=None,
            )

            self.findings.append(finding)

        self.calculate_statistics()
        print(f"Parsed {len(self.findings)} findings")

    def calculate_statistics(self) -> None:
        """Calculate statistics from findings"""
        by_severity = defaultdict(int)
        by_owasp = defaultdict(int)
        by_confidence = defaultdict(int)

        false_positives = 0
        total_instances = 0

        for finding in self.findings:
            by_severity[finding.severity] += 1
            by_owasp[finding.owasp_category] += 1
            by_confidence[finding.confidence] += 1
            total_instances += len(finding.instances)

            if finding.is_false_positive:
                false_positives += 1

        self.statistics = {
            "total_findings": len(self.findings),
            "total_instances": total_instances,
            "false_positives": false_positives,
            "true_positives": len(self.findings) - false_positives,
            "by_severity": dict(by_severity),
            "by_owasp_category": dict(by_owasp),
            "by_confidence": dict(by_confidence),
        }

    def generate_human_readable_report(self) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("OWASP ZAP VULNERABILITY REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Total Findings: {self.statistics['total_findings']}")
        lines.append(f"True Positives: {self.statistics['true_positives']}")
        lines.append(f"False Positives: {self.statistics['false_positives']}")
        lines.append("")

        lines.append("SEVERITY DISTRIBUTION:")
        lines.append("-" * 40)
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = self.statistics["by_severity"].get(severity, 0)
            lines.append(f"  {severity.upper():12} {count:3}")
        lines.append("")

        lines.append("OWASP TOP 10 DISTRIBUTION:")
        lines.append("-" * 40)
        for category, count in sorted(
            self.statistics["by_owasp_category"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {category}: {count}")
        lines.append("")

        # Group findings by severity
        findings_by_severity = defaultdict(list)
        for finding in self.findings:
            if not finding.is_false_positive:
                findings_by_severity[finding.severity].append(finding)

        # Report findings by severity
        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = findings_by_severity.get(severity, [])
            if not findings:
                continue

            lines.append("")
            lines.append("=" * 80)
            lines.append(f"{severity.upper()} SEVERITY FINDINGS ({len(findings)})")
            lines.append("=" * 80)

            for i, finding in enumerate(findings, 1):
                lines.append("")
                lines.append(f"{i}. {finding.title}")
                lines.append(f"   Plugin ID: {finding.id}")
                lines.append(f"   Confidence: {finding.confidence}")
                lines.append(f"   OWASP Category: {finding.owasp_category}")
                if finding.cwe_id:
                    lines.append(f"   CWE: {finding.cwe_id}")
                lines.append(f"   Instances: {len(finding.instances)}")
                lines.append("")
                lines.append("   Description:")
                lines.append(f"   {finding.description[:200]}...")
                lines.append("")
                lines.append("   Solution:")
                lines.append(f"   {finding.solution[:200]}...")
                lines.append("")

                # Show first 3 instances
                if finding.instances:
                    lines.append("   Evidence (sample):")
                    for inst in finding.instances[:3]:
                        lines.append(f"     URL: {inst['url']}")
                        if inst["param"]:
                            lines.append(f"     Parameter: {inst['param']}")
                        if inst["evidence"]:
                            lines.append(f"     Evidence: {inst['evidence'][:100]}...")
                        lines.append("")

                lines.append("-" * 80)

        # False positives section
        false_positives = [f for f in self.findings if f.is_false_positive]
        if false_positives:
            lines.append("")
            lines.append("=" * 80)
            lines.append(f"FALSE POSITIVES ({len(false_positives)})")
            lines.append("=" * 80)
            for fp in false_positives:
                lines.append(f"  - {fp.title}")
                lines.append(f"    Reason: {fp.false_positive_reason}")
                lines.append("")

        return "\n".join(lines)

    def export_json(self, output_path: Path) -> None:
        """Export parsed results to JSON"""
        output = {
            "metadata": {
                "parser": "ZAPResultsParser",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "source": "OWASP ZAP",
            },
            "statistics": self.statistics,
            "findings": [asdict(f) for f in self.findings],
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Exported JSON report: {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python parse_zap_results.py <zap_report.json> [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".parsed.json")

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    parser = ZAPResultsParser()
    parser.parse_report(input_path)

    # Generate human-readable report
    text_report = parser.generate_human_readable_report()
    text_output_path = output_path.with_suffix(".txt")
    with open(text_output_path, "w") as f:
        f.write(text_report)
    print(f"Generated text report: {text_output_path}")

    # Export JSON
    parser.export_json(output_path)

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Findings: {parser.statistics['total_findings']}")
    print(f"True Positives: {parser.statistics['true_positives']}")
    print(f"False Positives: {parser.statistics['false_positives']}")
    print("\nSeverity Distribution:")
    for severity in ["critical", "high", "medium", "low", "info"]:
        count = parser.statistics["by_severity"].get(severity, 0)
        print(f"  {severity.upper():12} {count}")


if __name__ == "__main__":
    main()
