#!/usr/bin/env python3
"""
Nuclei Results Parser
Parses Nuclei JSON findings, categorizes by severity/type, extracts evidence,
maps to CVE database, generates remediation reports, and identifies false positives.
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
    """Severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Vulnerability types"""

    CVE = "cve"
    MISCONFIGURATION = "misconfiguration"
    EXPOSURE = "exposure"
    TAKEOVER = "takeover"
    INJECTION = "injection"
    XSS = "xss"
    SSRF = "ssrf"
    LFI = "lfi"
    RCE = "rce"
    AUTHENTICATION = "authentication"
    DEFAULT_CREDENTIALS = "default-credentials"
    INFO_DISCLOSURE = "info-disclosure"
    OTHER = "other"


@dataclass
class NucleiFinding:
    """Structured Nuclei finding"""

    template_id: str
    name: str
    severity: str
    vulnerability_type: str
    description: str
    tags: list[str]
    reference: list[str]
    cve_id: Optional[str]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    cwe_id: Optional[str]
    matched_at: str
    extracted_results: list[str]
    curl_command: Optional[str]
    matcher_name: Optional[str]
    is_false_positive: bool
    false_positive_reason: Optional[str]
    remediation: Optional[str]
    remediation_status: str


class NucleiResultsParser:
    """Parser for Nuclei JSON reports"""

    # Known false positive patterns
    FALSE_POSITIVE_PATTERNS = [
        {
            "template": "ssl-dns-names",
            "reason": "Certificate domain validation - informational only",
        },
        {"template": "options-method", "reason": "OPTIONS method often required for CORS"},
        {"template": "robots-txt", "reason": "robots.txt presence is expected"},
        {"template": "waf-detect", "reason": "WAF detection is informational"},
    ]

    # CVE patterns for extraction
    CVE_PATTERN = r"CVE-\d{4}-\d{4,7}"

    # CWE patterns for extraction
    CWE_PATTERN = r"CWE-\d+"

    # Remediation guidance
    REMEDIATION_GUIDE = {
        "cve": "Apply the latest security patches and updates for the affected component.",
        "misconfiguration": "Review and correct the security configuration according to best practices.",
        "exposure": "Restrict access to sensitive endpoints and implement proper authentication.",
        "default-credentials": "Change all default credentials immediately and enforce strong password policy.",
        "info-disclosure": "Remove or restrict access to information disclosure endpoints.",
        "injection": "Implement input validation, parameterized queries, and output encoding.",
        "xss": "Implement Content Security Policy, input validation, and output encoding.",
        "ssrf": "Validate and sanitize all user-provided URLs, implement allowlists.",
        "authentication": "Implement multi-factor authentication and secure session management.",
    }

    def __init__(self):
        self.findings: list[NucleiFinding] = []
        self.statistics: dict[str, Any] = {}

    def determine_vulnerability_type(self, info: dict[str, Any], template_id: str) -> str:
        """Determine vulnerability type from template info"""
        tags = info.get("tags", [])

        # Check for CVE
        if any("cve" in tag.lower() for tag in tags):
            return VulnerabilityType.CVE.value

        # Check template ID and tags
        type_mapping = {
            "xss": VulnerabilityType.XSS.value,
            "sqli": VulnerabilityType.INJECTION.value,
            "rce": VulnerabilityType.RCE.value,
            "lfi": VulnerabilityType.LFI.value,
            "ssrf": VulnerabilityType.SSRF.value,
            "takeover": VulnerabilityType.TAKEOVER.value,
            "exposure": VulnerabilityType.EXPOSURE.value,
            "misconfig": VulnerabilityType.MISCONFIGURATION.value,
            "default-login": VulnerabilityType.DEFAULT_CREDENTIALS.value,
            "auth": VulnerabilityType.AUTHENTICATION.value,
        }

        template_lower = template_id.lower()
        for keyword, vuln_type in type_mapping.items():
            if keyword in template_lower or any(keyword in tag.lower() for tag in tags):
                return vuln_type

        return VulnerabilityType.OTHER.value

    def extract_cve_id(self, finding: dict[str, Any]) -> Optional[str]:
        """Extract CVE ID from finding"""
        import re

        info = finding.get("info", {})

        # Check classification
        classification = info.get("classification", {})
        cve_id = classification.get("cve-id")
        if cve_id:
            if isinstance(cve_id, list):
                return cve_id[0] if cve_id else None
            return cve_id

        # Check tags
        tags = info.get("tags", [])
        for tag in tags:
            match = re.search(self.CVE_PATTERN, tag, re.IGNORECASE)
            if match:
                return match.group(0).upper()

        # Check template ID
        template_id = finding.get("template-id", "")
        match = re.search(self.CVE_PATTERN, template_id, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        return None

    def extract_cwe_id(self, info: dict[str, Any]) -> Optional[str]:
        """Extract CWE ID from finding"""
        import re

        classification = info.get("classification", {})
        cwe_id = classification.get("cwe-id")
        if cwe_id:
            if isinstance(cwe_id, list):
                return f"CWE-{cwe_id[0]}" if cwe_id else None
            return f"CWE-{cwe_id}" if not str(cwe_id).startswith("CWE-") else cwe_id

        # Check description
        description = info.get("description", "")
        match = re.search(self.CWE_PATTERN, description, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        return None

    def extract_cvss_info(self, info: dict[str, Any]) -> tuple[Optional[float], Optional[str]]:
        """Extract CVSS score and vector"""
        classification = info.get("classification", {})

        cvss_score = classification.get("cvss-score")
        cvss_vector = classification.get("cvss-metrics")

        if cvss_score:
            try:
                cvss_score = float(cvss_score)
            except (ValueError, TypeError):
                cvss_score = None

        return cvss_score, cvss_vector

    def is_false_positive(self, template_id: str, severity: str) -> tuple[bool, Optional[str]]:
        """Check if finding is a known false positive"""
        for fp_pattern in self.FALSE_POSITIVE_PATTERNS:
            if fp_pattern["template"] in template_id:
                return True, fp_pattern["reason"]

        # Low severity informational findings are often false positives
        if severity == Severity.INFO.value:
            return True, "Informational finding - no security impact"

        return False, None

    def get_remediation(self, vuln_type: str, info: dict[str, Any]) -> Optional[str]:
        """Get remediation guidance for vulnerability"""
        # Use template remediation if available
        remediation = info.get("remediation")
        if remediation:
            return remediation

        # Use standard remediation guide
        return self.REMEDIATION_GUIDE.get(vuln_type)

    def parse_report(self, nuclei_report_path: Path) -> None:
        """Parse Nuclei JSON report (JSONL format)"""
        print(f"Parsing Nuclei report: {nuclei_report_path}")

        if not nuclei_report_path.exists() or nuclei_report_path.stat().st_size == 0:
            print("Warning: Empty or non-existent Nuclei report")
            return

        findings_count = 0
        with open(nuclei_report_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    finding_data = json.loads(line)
                    self.process_finding(finding_data)
                    findings_count += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {e}")
                    continue

        print(f"Parsed {findings_count} findings")
        self.calculate_statistics()

    def process_finding(self, finding_data: dict[str, Any]) -> None:
        """Process a single Nuclei finding"""
        info = finding_data.get("info", {})
        template_id = finding_data.get("template-id", "unknown")
        severity = info.get("severity", "info").lower()

        vuln_type = self.determine_vulnerability_type(info, template_id)
        cve_id = self.extract_cve_id(finding_data)
        cwe_id = self.extract_cwe_id(info)
        cvss_score, cvss_vector = self.extract_cvss_info(info)
        is_fp, fp_reason = self.is_false_positive(template_id, severity)

        finding = NucleiFinding(
            template_id=template_id,
            name=info.get("name", template_id),
            severity=severity,
            vulnerability_type=vuln_type,
            description=info.get("description", ""),
            tags=info.get("tags", []),
            reference=info.get("reference", [])
            if isinstance(info.get("reference"), list)
            else [info.get("reference", "")],
            cve_id=cve_id,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            cwe_id=cwe_id,
            matched_at=finding_data.get("matched-at", finding_data.get("host", "")),
            extracted_results=finding_data.get("extracted-results", []),
            curl_command=finding_data.get("curl-command"),
            matcher_name=finding_data.get("matcher-name"),
            is_false_positive=is_fp,
            false_positive_reason=fp_reason,
            remediation=self.get_remediation(vuln_type, info),
            remediation_status="pending",
        )

        self.findings.append(finding)

    def calculate_statistics(self) -> None:
        """Calculate statistics from findings"""
        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        by_cve = defaultdict(int)

        false_positives = 0
        cve_findings = []

        for finding in self.findings:
            by_severity[finding.severity] += 1
            by_type[finding.vulnerability_type] += 1

            if finding.is_false_positive:
                false_positives += 1

            if finding.cve_id:
                by_cve[finding.cve_id] += 1
                cve_findings.append(
                    {
                        "cve_id": finding.cve_id,
                        "name": finding.name,
                        "severity": finding.severity,
                        "cvss_score": finding.cvss_score,
                    }
                )

        self.statistics = {
            "total_findings": len(self.findings),
            "false_positives": false_positives,
            "true_positives": len(self.findings) - false_positives,
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "cve_count": len(by_cve),
            "cve_findings": cve_findings,
        }

    def generate_human_readable_report(self) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("NUCLEI VULNERABILITY REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Total Findings: {self.statistics['total_findings']}")
        lines.append(f"True Positives: {self.statistics['true_positives']}")
        lines.append(f"False Positives: {self.statistics['false_positives']}")
        lines.append(f"CVE Findings: {self.statistics['cve_count']}")
        lines.append("")

        lines.append("SEVERITY DISTRIBUTION:")
        lines.append("-" * 40)
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = self.statistics["by_severity"].get(severity, 0)
            lines.append(f"  {severity.upper():12} {count:3}")
        lines.append("")

        lines.append("VULNERABILITY TYPE DISTRIBUTION:")
        lines.append("-" * 40)
        for vuln_type, count in sorted(
            self.statistics["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  {vuln_type:25} {count:3}")
        lines.append("")

        # CVE Findings
        if self.statistics["cve_findings"]:
            lines.append("=" * 80)
            lines.append("CVE FINDINGS")
            lines.append("=" * 80)
            for cve_finding in self.statistics["cve_findings"]:
                lines.append(f"  {cve_finding['cve_id']}")
                lines.append(f"    Name: {cve_finding['name']}")
                lines.append(f"    Severity: {cve_finding['severity'].upper()}")
                if cve_finding["cvss_score"]:
                    lines.append(f"    CVSS Score: {cve_finding['cvss_score']}")
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
                lines.append(f"{i}. {finding.name}")
                lines.append(f"   Template: {finding.template_id}")
                lines.append(f"   Type: {finding.vulnerability_type}")
                if finding.cve_id:
                    lines.append(f"   CVE: {finding.cve_id}")
                if finding.cwe_id:
                    lines.append(f"   CWE: {finding.cwe_id}")
                if finding.cvss_score:
                    lines.append(f"   CVSS Score: {finding.cvss_score}")
                lines.append(f"   Matched At: {finding.matched_at}")
                lines.append("")

                if finding.description:
                    lines.append("   Description:")
                    lines.append(f"   {finding.description[:200]}...")
                    lines.append("")

                if finding.remediation:
                    lines.append("   Remediation:")
                    lines.append(f"   {finding.remediation}")
                    lines.append("")

                if finding.extracted_results:
                    lines.append("   Extracted Evidence:")
                    for result in finding.extracted_results[:3]:
                        lines.append(f"     - {result}")
                    lines.append("")

                if finding.reference:
                    lines.append("   References:")
                    for ref in finding.reference[:3]:
                        if ref:
                            lines.append(f"     - {ref}")
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
                lines.append(f"  - {fp.name} ({fp.template_id})")
                lines.append(f"    Reason: {fp.false_positive_reason}")
                lines.append("")

        return "\n".join(lines)

    def export_json(self, output_path: Path) -> None:
        """Export parsed results to JSON"""
        output = {
            "metadata": {
                "parser": "NucleiResultsParser",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "source": "Nuclei",
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
        print("Usage: python parse_nuclei_results.py <nuclei_report.json> [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.with_suffix(".parsed.json")

    parser = NucleiResultsParser()
    parser.parse_report(input_path)

    if not parser.findings:
        print("No findings to process")
        # Create empty report
        parser.export_json(output_path)
        sys.exit(0)

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
    print(f"CVE Findings: {parser.statistics['cve_count']}")
    print("\nSeverity Distribution:")
    for severity in ["critical", "high", "medium", "low", "info"]:
        count = parser.statistics["by_severity"].get(severity, 0)
        print(f"  {severity.upper():12} {count}")


if __name__ == "__main__":
    main()
