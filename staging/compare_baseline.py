#!/usr/bin/env python3
"""
Vulnerability Baseline Comparison
Compares current vulnerability findings against a known baseline,
identifies new vulnerabilities, tracks closed vulnerabilities,
generates delta reports, and flags regressions.
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ChangeType(Enum):
    """Types of changes in vulnerability status"""

    NEW = "new"
    FIXED = "fixed"
    REGRESSION = "regression"
    SEVERITY_INCREASED = "severity_increased"
    SEVERITY_DECREASED = "severity_decreased"
    UNCHANGED = "unchanged"


@dataclass
class VulnerabilityChange:
    """Change in vulnerability status"""

    vulnerability_id: str
    title: str
    change_type: str
    old_severity: Optional[str]
    new_severity: Optional[str]
    old_priority: Optional[str]
    new_priority: Optional[str]
    is_regression: bool
    details: str
    timestamp: str


@dataclass
class BaselineComparison:
    """Comparison between current and baseline findings"""

    new_vulnerabilities: list[dict[str, Any]]
    fixed_vulnerabilities: list[dict[str, Any]]
    regressions: list[dict[str, Any]]
    severity_changes: list[VulnerabilityChange]
    unchanged_vulnerabilities: list[dict[str, Any]]
    statistics: dict[str, Any]
    summary: str


class VulnerabilityBaselineComparator:
    """Compare current findings with baseline"""

    def __init__(self):
        self.current_vulns: dict[str, dict[str, Any]] = {}
        self.baseline_vulns: dict[str, dict[str, Any]] = {}
        self.changes: list[VulnerabilityChange] = []
        self.comparison: Optional[BaselineComparison] = None

    def load_report(self, report_path: Path) -> dict[str, Any]:
        """Load vulnerability report"""
        if not report_path.exists():
            raise FileNotFoundError(f"Report not found: {report_path}")

        with open(report_path) as f:
            return json.load(f)

    def normalize_vulnerability_key(self, vuln: dict[str, Any]) -> str:
        """Generate normalized key for vulnerability matching"""
        import hashlib

        # Use combination of title, type, and affected URLs for matching
        title = vuln.get("title", "").lower().strip()
        vuln_type = vuln.get("vulnerability_type", "")
        urls = sorted(vuln.get("affected_urls", []))

        # Create composite key
        key_parts = [title, vuln_type] + urls[:3]  # Limit URLs to avoid too long keys
        key_string = "|".join(key_parts)

        # Hash for consistent length
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def build_vulnerability_index(
        self, vulnerabilities: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Build index of vulnerabilities by normalized key"""
        index = {}
        for vuln in vulnerabilities:
            # Skip duplicates and false positives
            if vuln.get("is_duplicate") or vuln.get("is_false_positive"):
                continue

            key = self.normalize_vulnerability_key(vuln)
            index[key] = vuln

        return index

    def detect_regression(
        self, baseline_vuln: dict[str, Any], current_vuln: dict[str, Any]
    ) -> bool:
        """Detect if a vulnerability is a regression"""
        # If it was fixed in baseline but appears again
        if baseline_vuln.get("remediation_status") == "fixed":
            return True

        # If severity increased significantly
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        old_severity = baseline_vuln.get("severity", "info")
        new_severity = current_vuln.get("severity", "info")

        if severity_order.get(new_severity, 0) > severity_order.get(old_severity, 0):
            return True

        return False

    def compare_severity(
        self, baseline_vuln: dict[str, Any], current_vuln: dict[str, Any]
    ) -> Optional[ChangeType]:
        """Compare severity levels"""
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

        old_severity = baseline_vuln.get("severity", "info")
        new_severity = current_vuln.get("severity", "info")

        old_level = severity_order.get(old_severity, 0)
        new_level = severity_order.get(new_severity, 0)

        if new_level > old_level:
            return ChangeType.SEVERITY_INCREASED
        elif new_level < old_level:
            return ChangeType.SEVERITY_DECREASED

        return None

    def compare(self, current_path: Path, baseline_path: Path) -> None:
        """Compare current findings with baseline"""
        print(f"Loading current report: {current_path}")
        current_report = self.load_report(current_path)

        print(f"Loading baseline report: {baseline_path}")
        baseline_report = self.load_report(baseline_path)

        # Build indexes
        print("Building vulnerability indexes...")
        self.current_vulns = self.build_vulnerability_index(
            current_report.get("vulnerabilities", [])
        )
        self.baseline_vulns = self.build_vulnerability_index(
            baseline_report.get("vulnerabilities", [])
        )

        print(f"Current vulnerabilities: {len(self.current_vulns)}")
        print(f"Baseline vulnerabilities: {len(self.baseline_vulns)}")

        # Find changes
        self.analyze_changes()

        # Build comparison report
        self.build_comparison_report(current_report, baseline_report)

    def analyze_changes(self) -> None:
        """Analyze changes between current and baseline"""
        current_keys = set(self.current_vulns.keys())
        baseline_keys = set(self.baseline_vulns.keys())

        # New vulnerabilities
        new_keys = current_keys - baseline_keys
        for key in new_keys:
            vuln = self.current_vulns[key]
            change = VulnerabilityChange(
                vulnerability_id=vuln.get("id", key),
                title=vuln.get("title", "Unknown"),
                change_type=ChangeType.NEW.value,
                old_severity=None,
                new_severity=vuln.get("severity"),
                old_priority=None,
                new_priority=vuln.get("priority"),
                is_regression=False,
                details=f"New vulnerability discovered: {vuln.get('vulnerability_type')}",
                timestamp=datetime.now().isoformat(),
            )
            self.changes.append(change)

        # Fixed vulnerabilities
        fixed_keys = baseline_keys - current_keys
        for key in fixed_keys:
            vuln = self.baseline_vulns[key]
            change = VulnerabilityChange(
                vulnerability_id=vuln.get("id", key),
                title=vuln.get("title", "Unknown"),
                change_type=ChangeType.FIXED.value,
                old_severity=vuln.get("severity"),
                new_severity=None,
                old_priority=vuln.get("priority"),
                new_priority=None,
                is_regression=False,
                details="Vulnerability has been fixed",
                timestamp=datetime.now().isoformat(),
            )
            self.changes.append(change)

        # Unchanged or changed vulnerabilities
        common_keys = current_keys & baseline_keys
        for key in common_keys:
            current_vuln = self.current_vulns[key]
            baseline_vuln = self.baseline_vulns[key]

            # Check for severity change
            severity_change = self.compare_severity(baseline_vuln, current_vuln)

            # Check for regression
            is_regression = self.detect_regression(baseline_vuln, current_vuln)

            if severity_change or is_regression:
                change_type = (
                    ChangeType.REGRESSION.value if is_regression else severity_change.value
                )

                details_parts = []
                if severity_change == ChangeType.SEVERITY_INCREASED:
                    details_parts.append(
                        f"Severity increased from {baseline_vuln.get('severity')} to {current_vuln.get('severity')}"
                    )
                elif severity_change == ChangeType.SEVERITY_DECREASED:
                    details_parts.append(
                        f"Severity decreased from {baseline_vuln.get('severity')} to {current_vuln.get('severity')}"
                    )

                if is_regression:
                    details_parts.append(
                        "Regression detected - vulnerability reappeared or worsened"
                    )

                change = VulnerabilityChange(
                    vulnerability_id=current_vuln.get("id", key),
                    title=current_vuln.get("title", "Unknown"),
                    change_type=change_type,
                    old_severity=baseline_vuln.get("severity"),
                    new_severity=current_vuln.get("severity"),
                    old_priority=baseline_vuln.get("priority"),
                    new_priority=current_vuln.get("priority"),
                    is_regression=is_regression,
                    details="; ".join(details_parts),
                    timestamp=datetime.now().isoformat(),
                )
                self.changes.append(change)
            else:
                # Unchanged
                change = VulnerabilityChange(
                    vulnerability_id=current_vuln.get("id", key),
                    title=current_vuln.get("title", "Unknown"),
                    change_type=ChangeType.UNCHANGED.value,
                    old_severity=baseline_vuln.get("severity"),
                    new_severity=current_vuln.get("severity"),
                    old_priority=baseline_vuln.get("priority"),
                    new_priority=current_vuln.get("priority"),
                    is_regression=False,
                    details="No change",
                    timestamp=datetime.now().isoformat(),
                )
                self.changes.append(change)

    def build_comparison_report(
        self, current_report: dict[str, Any], baseline_report: dict[str, Any]
    ) -> None:
        """Build comparison report"""
        # Categorize changes
        new_vulns = []
        fixed_vulns = []
        regressions = []
        severity_changes = []
        unchanged_vulns = []

        for change in self.changes:
            if change.change_type == ChangeType.NEW.value:
                # Find full vulnerability details
                for key, vuln in self.current_vulns.items():
                    if vuln.get("id") == change.vulnerability_id:
                        new_vulns.append(vuln)
                        break

            elif change.change_type == ChangeType.FIXED.value:
                # Find full vulnerability details from baseline
                for key, vuln in self.baseline_vulns.items():
                    if vuln.get("id") == change.vulnerability_id:
                        fixed_vulns.append(vuln)
                        break

            elif change.is_regression:
                # Find full vulnerability details
                for key, vuln in self.current_vulns.items():
                    if vuln.get("id") == change.vulnerability_id:
                        regressions.append(vuln)
                        break

            elif change.change_type in [
                ChangeType.SEVERITY_INCREASED.value,
                ChangeType.SEVERITY_DECREASED.value,
            ]:
                severity_changes.append(change)

            elif change.change_type == ChangeType.UNCHANGED.value:
                for key, vuln in self.current_vulns.items():
                    if vuln.get("id") == change.vulnerability_id:
                        unchanged_vulns.append(vuln)
                        break

        # Calculate statistics
        statistics = {
            "baseline_date": baseline_report.get("metadata", {}).get("generated_at", "Unknown"),
            "current_date": current_report.get("metadata", {}).get("generated_at", "Unknown"),
            "baseline_total": len(self.baseline_vulns),
            "current_total": len(self.current_vulns),
            "new_count": len(new_vulns),
            "fixed_count": len(fixed_vulns),
            "regression_count": len(regressions),
            "severity_increased_count": len(
                [
                    c
                    for c in severity_changes
                    if c.change_type == ChangeType.SEVERITY_INCREASED.value
                ]
            ),
            "severity_decreased_count": len(
                [
                    c
                    for c in severity_changes
                    if c.change_type == ChangeType.SEVERITY_DECREASED.value
                ]
            ),
            "unchanged_count": len(unchanged_vulns),
            "net_change": len(new_vulns) - len(fixed_vulns),
        }

        # Generate summary
        summary_lines = []
        summary_lines.append("Vulnerability Delta Report")
        summary_lines.append(f"Baseline: {statistics['baseline_total']} vulnerabilities")
        summary_lines.append(f"Current:  {statistics['current_total']} vulnerabilities")
        summary_lines.append(f"Net Change: {statistics['net_change']:+d}")
        summary_lines.append("")
        summary_lines.append(f"New Vulnerabilities: {statistics['new_count']}")
        summary_lines.append(f"Fixed Vulnerabilities: {statistics['fixed_count']}")
        summary_lines.append(f"Regressions: {statistics['regression_count']}")
        summary_lines.append(f"Severity Increased: {statistics['severity_increased_count']}")
        summary_lines.append(f"Severity Decreased: {statistics['severity_decreased_count']}")
        summary_lines.append(f"Unchanged: {statistics['unchanged_count']}")

        summary = "\n".join(summary_lines)

        self.comparison = BaselineComparison(
            new_vulnerabilities=new_vulns,
            fixed_vulnerabilities=fixed_vulns,
            regressions=regressions,
            severity_changes=severity_changes,
            unchanged_vulnerabilities=unchanged_vulns,
            statistics=statistics,
            summary=summary,
        )

    def export_json(self, output_path: Path) -> None:
        """Export comparison report to JSON"""
        if not self.comparison:
            raise ValueError("No comparison data available. Run compare() first.")

        output = {
            "metadata": {
                "tool": "VulnerabilityBaselineComparator",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
            },
            "summary": self.comparison.summary,
            "statistics": self.comparison.statistics,
            "new_vulnerabilities": self.comparison.new_vulnerabilities,
            "fixed_vulnerabilities": self.comparison.fixed_vulnerabilities,
            "regressions": self.comparison.regressions,
            "severity_changes": [asdict(c) for c in self.comparison.severity_changes],
            "unchanged_vulnerabilities": self.comparison.unchanged_vulnerabilities,
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\nExported comparison report: {output_path}")

    def print_report(self) -> None:
        """Print human-readable comparison report"""
        if not self.comparison:
            raise ValueError("No comparison data available. Run compare() first.")

        print("\n" + "=" * 80)
        print("VULNERABILITY BASELINE COMPARISON")
        print("=" * 80)
        print(self.comparison.summary)
        print()

        # New vulnerabilities
        if self.comparison.new_vulnerabilities:
            print("=" * 80)
            print(f"NEW VULNERABILITIES ({len(self.comparison.new_vulnerabilities)})")
            print("=" * 80)
            for vuln in self.comparison.new_vulnerabilities:
                print(f"  [{vuln.get('severity', 'unknown').upper()}] {vuln.get('title')}")
                print(f"    Type: {vuln.get('vulnerability_type')}")
                print(f"    Priority: {vuln.get('priority')}")
                if vuln.get("cve_id"):
                    print(f"    CVE: {vuln.get('cve_id')}")
                print()

        # Regressions
        if self.comparison.regressions:
            print("=" * 80)
            print(f"REGRESSIONS ({len(self.comparison.regressions)})")
            print("=" * 80)
            for vuln in self.comparison.regressions:
                print(f"  [REGRESSION] {vuln.get('title')}")
                print(f"    Severity: {vuln.get('severity', 'unknown').upper()}")
                print(f"    Type: {vuln.get('vulnerability_type')}")
                print("    This vulnerability was previously fixed or has worsened")
                print()

        # Fixed vulnerabilities
        if self.comparison.fixed_vulnerabilities:
            print("=" * 80)
            print(f"FIXED VULNERABILITIES ({len(self.comparison.fixed_vulnerabilities)})")
            print("=" * 80)
            for vuln in self.comparison.fixed_vulnerabilities:
                print(f"  [FIXED] {vuln.get('title')}")
                print(f"    Was: {vuln.get('severity', 'unknown').upper()}")
                print()

        # Severity changes
        if self.comparison.severity_changes:
            print("=" * 80)
            print(f"SEVERITY CHANGES ({len(self.comparison.severity_changes)})")
            print("=" * 80)
            for change in self.comparison.severity_changes:
                direction = (
                    "↑" if change.change_type == ChangeType.SEVERITY_INCREASED.value else "↓"
                )
                print(f"  {direction} {change.title}")
                print(f"    {change.old_severity} → {change.new_severity}")
                print()


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print(
            "Usage: python compare_baseline.py <current_report.json> <baseline_report.json> [output.json]"
        )
        sys.exit(1)

    current_path = Path(sys.argv[1])
    baseline_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("vulnerability_delta.json")

    comparator = VulnerabilityBaselineComparator()
    comparator.compare(current_path, baseline_path)
    comparator.export_json(output_path)
    comparator.print_report()

    # Exit with error if regressions found
    if comparator.comparison and comparator.comparison.regressions:
        print("\n" + "=" * 80)
        print("WARNING: Regressions detected!")
        print("=" * 80)
        sys.exit(1)
    else:
        print("\n" + "=" * 80)
        print("No regressions detected")
        print("=" * 80)
        sys.exit(0)


if __name__ == "__main__":
    main()
