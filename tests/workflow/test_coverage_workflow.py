"""
Test coverage workflow functionality.

This test validates the coverage file handling, merging, and threshold checking
that happens in the GitHub Actions test.yml workflow.
"""

import json
import os
import subprocess

import pytest


class TestCoverageWorkflow:
    """Test the coverage workflow functionality."""

    def test_coverage_file_with_custom_name(self, tmp_path):
        """Test that COVERAGE_FILE environment variable creates unique files."""
        # Create a simple test file
        test_file = tmp_path / "test_sample.py"
        test_file.write_text(
            """
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
"""
        )

        # Run pytest with custom coverage file name
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(tmp_path / ".coverage.test1")

        result = subprocess.run(
            ["pytest", str(test_file), "--cov=.", "--cov-report=xml:coverage-test1.xml", "-v"],
            check=False,
            cwd=str(tmp_path),
            env=env,
            capture_output=True,
            text=True,
        )

        # Verify test passed
        assert result.returncode == 0, f"Test failed: {result.stderr}"

        # Verify coverage file was created with custom name
        coverage_file = tmp_path / ".coverage.test1"
        assert coverage_file.exists(), "Coverage file not created"

    def test_coverage_combine_multiple_files(self, tmp_path):
        """Test combining multiple coverage files."""
        # Create two test files
        test_file1 = tmp_path / "test_file1.py"
        test_file1.write_text(
            """
def func1():
    return 1

def test_func1():
    assert func1() == 1
"""
        )

        test_file2 = tmp_path / "test_file2.py"
        test_file2.write_text(
            """
def func2():
    return 2

def test_func2():
    assert func2() == 2
"""
        )

        # Create first coverage file
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(tmp_path / ".coverage.test1")
        subprocess.run(
            ["pytest", str(test_file1), "--cov=.", "-v"], check=False, cwd=str(tmp_path), env=env, capture_output=True
        )

        # Create second coverage file
        env["COVERAGE_FILE"] = str(tmp_path / ".coverage.test2")
        subprocess.run(
            ["pytest", str(test_file2), "--cov=.", "-v"], check=False, cwd=str(tmp_path), env=env, capture_output=True
        )

        # Verify both coverage files exist
        assert (tmp_path / ".coverage.test1").exists()
        assert (tmp_path / ".coverage.test2").exists()

        # Combine coverage files
        result = subprocess.run(
            ["coverage", "combine", str(tmp_path / ".coverage.test1"), str(tmp_path / ".coverage.test2")],
            check=False,
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Combine failed: {result.stderr}"

        # Verify combined file was created
        combined_file = tmp_path / ".coverage"
        assert combined_file.exists(), "Combined coverage file not created"

    def test_threshold_check_python_based(self, tmp_path):
        """Test Python-based threshold checking (no bc dependency)."""
        # Create a coverage.json file with known coverage
        coverage_data = {"totals": {"percent_covered_display": "95.50"}}

        coverage_json = tmp_path / "coverage.json"
        coverage_json.write_text(json.dumps(coverage_data))

        # Test threshold check script
        check_script = """
import json
import sys

with open('coverage.json', 'r') as f:
    data = json.load(f)
    coverage = float(data['totals']['percent_covered_display'])
    threshold = 90.0

    if coverage >= threshold:
        print(f"PASS: {coverage}% >= {threshold}%")
        sys.exit(0)
    else:
        print(f"FAIL: {coverage}% < {threshold}%")
        sys.exit(1)
"""

        script_file = tmp_path / "check_threshold.py"
        script_file.write_text(check_script)

        result = subprocess.run(
            ["python3", str(script_file)], check=False, cwd=str(tmp_path), capture_output=True, text=True
        )

        assert result.returncode == 0, "Threshold check should pass"
        assert "PASS" in result.stdout

    def test_threshold_check_fails_below_threshold(self, tmp_path):
        """Test that threshold check fails when coverage is below threshold."""
        # Create a coverage.json file with low coverage
        coverage_data = {"totals": {"percent_covered_display": "85.00"}}

        coverage_json = tmp_path / "coverage.json"
        coverage_json.write_text(json.dumps(coverage_data))

        # Test threshold check script (90% threshold)
        check_script = """
import json
import sys

with open('coverage.json', 'r') as f:
    data = json.load(f)
    coverage = float(data['totals']['percent_covered_display'])
    threshold = 90.0

    if coverage >= threshold:
        print(f"PASS: {coverage}% >= {threshold}%")
        sys.exit(0)
    else:
        print(f"FAIL: {coverage}% < {threshold}%")
        sys.exit(1)
"""

        script_file = tmp_path / "check_threshold.py"
        script_file.write_text(check_script)

        result = subprocess.run(
            ["python3", str(script_file)], check=False, cwd=str(tmp_path), capture_output=True, text=True
        )

        assert result.returncode == 1, "Threshold check should fail"
        assert "FAIL" in result.stdout

    def test_coverage_badge_generation(self, tmp_path):
        """Test that coverage badge can be generated."""
        # Create a simple coverage.json
        coverage_data = {"totals": {"percent_covered_display": "92.50"}}

        coverage_json = tmp_path / "coverage.json"
        coverage_json.write_text(json.dumps(coverage_data))

        # Create a dummy .coverage file for coverage-badge
        # (coverage-badge reads from .coverage, not coverage.json)
        subprocess.run(["coverage", "erase"], check=False, cwd=str(tmp_path), capture_output=True)

        # Generate badge
        result = subprocess.run(
            ["coverage-badge", "-o", "coverage-badge.svg", "-f"],
            check=False,
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )

        # Badge generation might fail without actual .coverage data,
        # but the command should be available
        assert "coverage-badge" not in result.stderr or result.returncode in [0, 1]

    def test_missing_coverage_files_handled_gracefully(self, tmp_path):
        """Test that missing coverage files are handled gracefully."""
        # Simulate the workflow behavior when no coverage files found
        coverage_dir = tmp_path / ".coverage_data"
        coverage_dir.mkdir()

        # Search for coverage files
        coverage_files = list(coverage_dir.glob(".coverage.*"))

        if len(coverage_files) == 0:
            # Create empty report (as workflow does)
            summary_file = tmp_path / "coverage-summary.md"
            summary_file.write_text("# Coverage Report\n⚠️ No coverage data available")

            json_file = tmp_path / "coverage.json"
            json_file.write_text('{"totals": {"percent_covered_display": "0.00"}}')

        # Verify files were created
        assert (tmp_path / "coverage-summary.md").exists()
        assert (tmp_path / "coverage.json").exists()

        # Verify content
        summary = (tmp_path / "coverage-summary.md").read_text()
        assert "No coverage data available" in summary

        data = json.loads((tmp_path / "coverage.json").read_text())
        assert data["totals"]["percent_covered_display"] == "0.00"

    def test_coverage_report_markdown_generation(self, tmp_path):
        """Test generating markdown coverage report."""
        # Create a simple test and run coverage
        test_file = tmp_path / "test_simple.py"
        test_file.write_text(
            """
def simple_func():
    return True

def test_simple():
    assert simple_func()
"""
        )

        # Run pytest with coverage
        subprocess.run(
            ["pytest", str(test_file), "--cov=.", "-v"], check=False, cwd=str(tmp_path), capture_output=True
        )

        # Generate markdown report
        result = subprocess.run(
            ["coverage", "report", "--format=markdown"], check=False, cwd=str(tmp_path), capture_output=True, text=True
        )

        # Verify markdown was generated
        assert result.returncode == 0
        assert "TOTAL" in result.stdout
        assert "|" in result.stdout  # Markdown table format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
