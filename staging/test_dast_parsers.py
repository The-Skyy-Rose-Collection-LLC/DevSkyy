#!/usr/bin/env python3
"""
Test script for DAST parsers
Validates that all parsing and triage components work correctly.
"""

import json
import tempfile
from pathlib import Path
import sys

# Sample ZAP report structure
SAMPLE_ZAP_REPORT = {
    "alerts": [
        {
            "pluginid": "40012",
            "alert": "Cross Site Scripting (Reflected)",
            "risk": "High",
            "confidence": "Medium",
            "description": "Cross-site Scripting (XSS) is an attack technique...",
            "solution": "Validate all input and escape output...",
            "reference": "https://owasp.org/www-community/attacks/xss/",
            "cweid": 79,
            "wascid": 8,
            "instances": [
                {
                    "uri": "https://staging.example.com/search?q=test",
                    "method": "GET",
                    "param": "q",
                    "attack": "<script>alert(1)</script>",
                    "evidence": "<script>alert(1)</script>"
                }
            ]
        },
        {
            "pluginid": "10020",
            "alert": "X-Frame-Options Header Not Set",
            "risk": "Medium",
            "confidence": "Medium",
            "description": "X-Frame-Options header is not included...",
            "solution": "Add X-Frame-Options: DENY header",
            "reference": "https://owasp.org/www-community/controls/X-Frame-Options",
            "cweid": 1021,
            "instances": [
                {
                    "uri": "https://staging.example.com/api/products",
                    "method": "GET",
                    "param": "",
                    "attack": "",
                    "evidence": ""
                }
            ]
        }
    ]
}

# Sample Nuclei report (JSONL format)
SAMPLE_NUCLEI_REPORTS = [
    {
        "template-id": "CVE-2021-12345",
        "info": {
            "name": "WordPress Plugin XSS",
            "severity": "high",
            "description": "Cross-site scripting vulnerability in WordPress plugin",
            "tags": ["cve", "wordpress", "xss"],
            "classification": {
                "cve-id": "CVE-2021-12345",
                "cvss-score": 7.2,
                "cvss-metrics": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                "cwe-id": "79"
            },
            "remediation": "Update to version 2.3.4 or later"
        },
        "matched-at": "https://staging.example.com/wp-content/plugins/vulnerable-plugin/",
        "extracted-results": ["Version: 2.2.1"],
        "matcher-name": "version"
    },
    {
        "template-id": "tech-detect",
        "info": {
            "name": "WordPress Detection",
            "severity": "info",
            "description": "WordPress CMS detected",
            "tags": ["tech", "wordpress"]
        },
        "matched-at": "https://staging.example.com/",
        "matcher-name": "wordpress"
    }
]


def create_sample_reports():
    """Create sample report files for testing"""
    temp_dir = Path(tempfile.gettempdir()) / "dast_test"
    temp_dir.mkdir(exist_ok=True)

    # Create ZAP report
    zap_path = temp_dir / "zap_sample.json"
    with open(zap_path, 'w') as f:
        json.dump(SAMPLE_ZAP_REPORT, f, indent=2)

    # Create Nuclei report (JSONL)
    nuclei_path = temp_dir / "nuclei_sample.json"
    with open(nuclei_path, 'w') as f:
        for report in SAMPLE_NUCLEI_REPORTS:
            f.write(json.dumps(report) + '\n')

    return zap_path, nuclei_path, temp_dir


def test_zap_parser(zap_path, output_dir):
    """Test ZAP results parser"""
    print("Testing ZAP parser...")

    sys.path.insert(0, str(Path(__file__).parent))
    from parse_zap_results import ZAPResultsParser

    parser = ZAPResultsParser()
    parser.parse_report(zap_path)

    # Validate parsing
    assert len(parser.findings) == 2, f"Expected 2 findings, got {len(parser.findings)}"
    assert parser.statistics['total_findings'] == 2

    # Check false positive detection
    fp_count = len([f for f in parser.findings if f.is_false_positive])
    print(f"  False positives detected: {fp_count}")

    # Export
    output_path = output_dir / "zap_parsed.json"
    parser.export_json(output_path)

    print("  ZAP parser: PASSED ✓")
    return output_path


def test_nuclei_parser(nuclei_path, output_dir):
    """Test Nuclei results parser"""
    print("Testing Nuclei parser...")

    sys.path.insert(0, str(Path(__file__).parent))
    from parse_nuclei_results import NucleiResultsParser

    parser = NucleiResultsParser()
    parser.parse_report(nuclei_path)

    # Validate parsing
    assert len(parser.findings) == 2, f"Expected 2 findings, got {len(parser.findings)}"

    # Check CVE extraction
    cve_findings = [f for f in parser.findings if f.cve_id]
    assert len(cve_findings) == 1, f"Expected 1 CVE finding, got {len(cve_findings)}"

    # Export
    output_path = output_dir / "nuclei_parsed.json"
    parser.export_json(output_path)

    print("  Nuclei parser: PASSED ✓")
    return output_path


def test_triage(zap_parsed_path, nuclei_parsed_path, output_dir):
    """Test vulnerability triage"""
    print("Testing vulnerability triage...")

    sys.path.insert(0, str(Path(__file__).parent))
    from vulnerability_triage import VulnerabilityTriage

    triage = VulnerabilityTriage()
    triage.triage(zap_parsed_path, nuclei_parsed_path)

    # Validate triage
    assert len(triage.vulnerabilities) > 0, "Expected vulnerabilities after triage"
    assert triage.statistics['total_vulnerabilities'] > 0

    # Check duplicate detection
    print(f"  Total vulnerabilities: {triage.statistics['total_vulnerabilities']}")
    print(f"  Unique vulnerabilities: {triage.statistics['unique_vulnerabilities']}")
    print(f"  Duplicates removed: {triage.statistics['duplicates_removed']}")
    print(f"  Blockers: {triage.statistics['blockers']}")

    # Export
    output_path = output_dir / "triage.json"
    triage.export_json(output_path)

    print("  Vulnerability triage: PASSED ✓")
    return output_path


def test_baseline_comparison(current_path, output_dir):
    """Test baseline comparison"""
    print("Testing baseline comparison...")

    sys.path.insert(0, str(Path(__file__).parent))
    from vulnerability_triage import VulnerabilityTriage
    from compare_baseline import VulnerabilityBaselineComparator

    # Create a modified baseline (simulate fixed vulnerability)
    with open(current_path, 'r') as f:
        current_data = json.load(f)

    baseline_data = current_data.copy()
    # Remove one vulnerability to simulate a fix
    if baseline_data.get('vulnerabilities'):
        baseline_data['vulnerabilities'] = baseline_data['vulnerabilities'][:-1]

    baseline_path = output_dir / "baseline.json"
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f, indent=2)

    # Compare
    comparator = VulnerabilityBaselineComparator()
    comparator.compare(current_path, baseline_path)

    # Validate comparison
    assert comparator.comparison is not None
    print(f"  New vulnerabilities: {comparator.comparison.statistics['new_count']}")
    print(f"  Fixed vulnerabilities: {comparator.comparison.statistics['fixed_count']}")
    print(f"  Net change: {comparator.comparison.statistics['net_change']}")

    # Export
    output_path = output_dir / "delta.json"
    comparator.export_json(output_path)

    print("  Baseline comparison: PASSED ✓")
    return output_path


def main():
    """Run all tests"""
    print("=" * 80)
    print("DAST Parser Test Suite")
    print("=" * 80)
    print()

    try:
        # Create sample reports
        print("Creating sample reports...")
        zap_path, nuclei_path, temp_dir = create_sample_reports()
        print(f"  Sample reports created in: {temp_dir}")
        print()

        # Test ZAP parser
        zap_parsed = test_zap_parser(zap_path, temp_dir)
        print()

        # Test Nuclei parser
        nuclei_parsed = test_nuclei_parser(nuclei_path, temp_dir)
        print()

        # Test triage
        triage_output = test_triage(zap_parsed, nuclei_parsed, temp_dir)
        print()

        # Test baseline comparison
        delta_output = test_baseline_comparison(triage_output, temp_dir)
        print()

        # Summary
        print("=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print()
        print("Test outputs:")
        print(f"  ZAP parsed:     {zap_parsed}")
        print(f"  Nuclei parsed:  {nuclei_parsed}")
        print(f"  Triage:         {triage_output}")
        print(f"  Delta:          {delta_output}")
        print()

        return 0

    except AssertionError as e:
        print()
        print("=" * 80)
        print(f"TEST FAILED: {e}")
        print("=" * 80)
        return 1

    except Exception as e:
        print()
        print("=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
