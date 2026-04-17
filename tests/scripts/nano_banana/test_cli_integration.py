"""CLI integration tests for nano-banana-run.py — subprocess-based.

Tests invoke the CLI entry point via subprocess and assert on exit codes
and stdout content. Follows the pattern from test_deploy_pipeline.py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "nano-banana-run.py"


def run_cli(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run nano-banana-run.py with given arguments via subprocess."""
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "scripts")}
    return subprocess.run(
        ["python", str(RUN_SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


@pytest.mark.integration
class TestDryRun:
    """Verify the dry-run subcommand prints product info without API calls."""

    def test_dry_run_exits_zero(self):
        """dry-run exits 0."""
        result = run_cli("dry-run")
        assert (
            result.returncode == 0
        ), f"dry-run exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_dry_run_lists_products(self):
        """Output contains 'Products:' and a count."""
        result = run_cli("dry-run")
        assert (
            "Products:" in result.stdout
        ), f"Expected 'Products:' in output\nstdout: {result.stdout}"

    def test_dry_run_collection_filter(self):
        """--collection black-rose output only has black-rose SKUs (br-*)."""
        result = run_cli("dry-run", "--collection", "black-rose")
        assert result.returncode == 0

        # Every listed SKU line should contain a br- prefix
        # Lines with product data look like: "  [+] br-001  ..."
        sku_lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().startswith("[") and "]" in line
        ]
        for line in sku_lines:
            # Extract the part after the bracket
            after_bracket = line.split("]", 1)[1].strip()
            sku = after_bracket.split()[0] if after_bracket else ""
            assert sku.startswith(
                "br-"
            ), f"Expected black-rose SKU (br-*), got: '{sku}' in line: '{line}'"

    def test_dry_run_single_sku(self):
        """--sku with a known SKU shows only 1 product."""
        # First get a valid SKU from the catalog via dry-run
        result = run_cli("dry-run")
        assert result.returncode == 0

        # Find the first SKU in the output
        sku = None
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and "]" in stripped:
                after = stripped.split("]", 1)[1].strip()
                parts = after.split()
                if parts:
                    sku = parts[0]
                    break

        if sku is None:
            pytest.skip("No products in catalog to test single-SKU filter")

        result2 = run_cli("dry-run", "--sku", sku)
        assert result2.returncode == 0

        # Count product lines (lines starting with [+] or [x])
        product_lines = [
            line
            for line in result2.stdout.splitlines()
            if line.strip().startswith("[") and "]" in line
        ]
        assert len(product_lines) == 1, (
            f"Expected 1 product line for --sku {sku}, got {len(product_lines)}\n"
            f"stdout: {result2.stdout}"
        )


@pytest.mark.integration
class TestProduceAsyncHelp:
    """Verify produce-async --help prints flag documentation."""

    def test_produce_async_help(self):
        """produce-async --help output contains --collection."""
        result = run_cli("produce-async", "--help")
        assert result.returncode == 0
        assert (
            "--collection" in result.stdout
        ), f"Expected '--collection' in help output\nstdout: {result.stdout}"
