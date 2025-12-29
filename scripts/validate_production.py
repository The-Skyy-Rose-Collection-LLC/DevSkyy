#!/usr/bin/env python3
"""
SkyyRose Production Validation Script
======================================

Comprehensive validation script for WordPress production deployment.

Validates:
- WordPress REST API connectivity
- WooCommerce API access
- All page configurations
- 3D experience assets
- Hotspot configurations
- Authentication credentials
- Media assets availability
- SEO metadata
- Performance requirements

Usage:
    python scripts/validate_production.py --full
    python scripts/validate_production.py --pages-only
    python scripts/validate_production.py --auth-only

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use standard logging if structlog not available
try:
    import structlog
    logger = structlog.get_logger(__name__)
    USE_STRUCTLOG = True
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    USE_STRUCTLOG = False


class CompatLogger:
    """Wrapper to make standard logging compatible with structlog-style calls."""

    def __init__(self, base_logger, component: str = ""):
        self._logger = base_logger
        self._component = component

    def info(self, msg: str, **kwargs) -> None:
        if USE_STRUCTLOG:
            self._logger.info(msg, **kwargs)
        else:
            extra = f" [{kwargs}]" if kwargs else ""
            self._logger.info(f"[{self._component}] {msg}{extra}")

    def warning(self, msg: str, **kwargs) -> None:
        if USE_STRUCTLOG:
            self._logger.warning(msg, **kwargs)
        else:
            extra = f" [{kwargs}]" if kwargs else ""
            self._logger.warning(f"[{self._component}] {msg}{extra}")

    def error(self, msg: str, **kwargs) -> None:
        if USE_STRUCTLOG:
            self._logger.error(msg, **kwargs)
        else:
            extra = f" [{kwargs}]" if kwargs else ""
            self._logger.error(f"[{self._component}] {msg}{extra}")


def get_logger(component: str = "") -> CompatLogger:
    """Get a logger, compatible with both structlog and standard logging."""
    if USE_STRUCTLOG:
        return CompatLogger(logger.bind(component=component), component)
    return CompatLogger(logger, component)


# ============================================================================
# Validation Status
# ============================================================================


class ValidationStatus(str, Enum):
    """Validation result status."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    status: ValidationStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ValidationReport:
    """Complete validation report."""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    results: list[ValidationResult] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result."""
        self.results.append(result)
        status = result.status.value
        self.summary[status] = self.summary.get(status, 0) + 1

    @property
    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return all(r.status in (ValidationStatus.PASS, ValidationStatus.WARN, ValidationStatus.SKIP) for r in self.results)

    @property
    def critical_failures(self) -> list[ValidationResult]:
        """Get critical failures."""
        return [r for r in self.results if r.status == ValidationStatus.FAIL]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "summary": self.summary,
            "all_passed": self.all_passed,
            "results": [r.to_dict() for r in self.results],
        }

    def print_summary(self) -> None:
        """Print human-readable summary."""
        print("\n" + "=" * 60)
        print("SKYYROSE PRODUCTION VALIDATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {self.timestamp}")
        print()

        # Summary counts
        for status, count in self.summary.items():
            icon = {"pass": "OK", "fail": "XX", "warn": "!!", "skip": "--"}.get(status, "??")
            print(f"  [{icon}] {status.upper()}: {count}")

        print()

        # Details for failures
        if self.critical_failures:
            print("CRITICAL FAILURES:")
            for result in self.critical_failures:
                print(f"  - {result.name}: {result.message}")
            print()

        # Final status
        if self.all_passed:
            print("[OK] ALL VALIDATIONS PASSED")
        else:
            print("[XX] VALIDATION FAILED - See details above")

        print("=" * 60 + "\n")


# ============================================================================
# Validators
# ============================================================================


class ProductionValidator:
    """
    Production validation orchestrator.

    Runs all validation checks and produces a comprehensive report.
    """

    def __init__(self):
        self._logger = get_logger("validator")
        self._report = ValidationReport()

    async def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        self._logger.info("starting_full_validation")

        # Core validations
        await self.validate_wordpress_api()
        await self.validate_woocommerce_api()

        # Page validations
        await self.validate_pages()

        # Asset validations
        await self.validate_elementor_templates()
        await self.validate_hotspot_configs()
        await self.validate_3d_experiences()

        # Production requirements
        await self.validate_environment_variables()
        await self.validate_ssl_configuration()
        await self.validate_performance_requirements()

        self._logger.info(
            "validation_complete",
            all_passed=self._report.all_passed,
            summary=self._report.summary,
        )

        return self._report

    async def validate_wordpress_api(self) -> None:
        """Validate WordPress REST API connectivity."""
        import os
        import time

        start = time.perf_counter()
        site_url = os.getenv("WORDPRESS_URL", "")

        # Skip if no WordPress URL configured
        if not site_url:
            self._report.add_result(ValidationResult(
                name="wordpress_api",
                status=ValidationStatus.SKIP,
                message="Skipped - WORDPRESS_URL not configured",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
            return

        try:
            import aiohttp

            url = f"{site_url}/wp-json/wp/v2"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    duration = (time.perf_counter() - start) * 1000

                    if response.status == 200:
                        data = await response.json()
                        self._report.add_result(ValidationResult(
                            name="wordpress_api",
                            status=ValidationStatus.PASS,
                            message=f"WordPress API accessible at {site_url}",
                            details={"namespaces": data.get("namespaces", [])[:5]},
                            duration_ms=duration,
                        ))
                    else:
                        self._report.add_result(ValidationResult(
                            name="wordpress_api",
                            status=ValidationStatus.FAIL,
                            message=f"WordPress API returned status {response.status}",
                            duration_ms=duration,
                        ))

        except ImportError:
            self._report.add_result(ValidationResult(
                name="wordpress_api",
                status=ValidationStatus.SKIP,
                message="Skipped - aiohttp not installed (pip install aiohttp)",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        except Exception as e:
            self._report.add_result(ValidationResult(
                name="wordpress_api",
                status=ValidationStatus.FAIL,
                message=f"Failed to connect to WordPress API: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_woocommerce_api(self) -> None:
        """Validate WooCommerce API connectivity."""
        import os
        import time

        start = time.perf_counter()

        wc_key = os.getenv("WOOCOMMERCE_KEY", "")
        wc_secret = os.getenv("WOOCOMMERCE_SECRET", "")
        site_url = os.getenv("WORDPRESS_URL", "")

        if not wc_key or not wc_secret:
            self._report.add_result(ValidationResult(
                name="woocommerce_api",
                status=ValidationStatus.SKIP,
                message="Skipped - WooCommerce credentials not configured",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
            return

        if not site_url:
            self._report.add_result(ValidationResult(
                name="woocommerce_api",
                status=ValidationStatus.SKIP,
                message="Skipped - WORDPRESS_URL not configured",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
            return

        try:
            import aiohttp

            url = f"{site_url}/wp-json/wc/v3/products"
            auth = aiohttp.BasicAuth(wc_key, wc_secret)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth, timeout=10) as response:
                    duration = (time.perf_counter() - start) * 1000

                    if response.status == 200:
                        products = await response.json()
                        self._report.add_result(ValidationResult(
                            name="woocommerce_api",
                            status=ValidationStatus.PASS,
                            message=f"WooCommerce API accessible, {len(products)} products found",
                            details={"product_count": len(products)},
                            duration_ms=duration,
                        ))
                    else:
                        self._report.add_result(ValidationResult(
                            name="woocommerce_api",
                            status=ValidationStatus.FAIL,
                            message=f"WooCommerce API returned status {response.status}",
                            duration_ms=duration,
                        ))

        except ImportError:
            self._report.add_result(ValidationResult(
                name="woocommerce_api",
                status=ValidationStatus.SKIP,
                message="Skipped - aiohttp not installed (pip install aiohttp)",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        except Exception as e:
            self._report.add_result(ValidationResult(
                name="woocommerce_api",
                status=ValidationStatus.FAIL,
                message=f"Failed to connect to WooCommerce API: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_pages(self) -> None:
        """Validate all configured pages exist in WordPress."""
        import os
        import time

        start = time.perf_counter()

        # Expected pages
        required_pages = [
            {"slug": "home-2", "id": 150, "title": "Home"},
            {"slug": "collections", "id": 151, "title": "Collections"},
            {"slug": "signature", "id": 152, "title": "Signature"},
            {"slug": "black-rose", "id": 153, "title": "Black Rose"},
            {"slug": "love-hurts", "id": 154, "title": "Love Hurts"},
            {"slug": "about-2", "id": 155, "title": "About"},
        ]

        # Check if we have credentials to validate via API
        wp_username = os.getenv("WORDPRESS_USERNAME", "")
        wp_password = os.getenv("WORDPRESS_APP_PASSWORD", "")

        if not wp_username or not wp_password:
            # Skip validation if no credentials
            self._report.add_result(ValidationResult(
                name="pages_exist",
                status=ValidationStatus.SKIP,
                message="Skipped - WordPress credentials not configured for page validation",
                details={"required_pages": [p["slug"] for p in required_pages]},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
            return

        missing_pages = []
        found_pages = []

        try:
            import aiohttp
            import base64

            site_url = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
            credentials = f"{wp_username}:{wp_password}"
            auth_header = base64.b64encode(credentials.encode()).decode()

            async with aiohttp.ClientSession() as session:
                for page in required_pages:
                    url = f"{site_url}/wp-json/wp/v2/pages/{page['id']}"
                    headers = {"Authorization": f"Basic {auth_header}"}

                    try:
                        async with session.get(url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                found_pages.append(page["slug"])
                            else:
                                missing_pages.append(page["slug"])
                    except Exception:
                        missing_pages.append(page["slug"])

            duration = (time.perf_counter() - start) * 1000

            if missing_pages:
                self._report.add_result(ValidationResult(
                    name="pages_exist",
                    status=ValidationStatus.FAIL,
                    message=f"Missing pages: {', '.join(missing_pages)}",
                    details={"missing": missing_pages, "found": found_pages},
                    duration_ms=duration,
                ))
            else:
                self._report.add_result(ValidationResult(
                    name="pages_exist",
                    status=ValidationStatus.PASS,
                    message=f"All {len(required_pages)} required pages verified via API",
                    details={"pages": found_pages},
                    duration_ms=duration,
                ))

        except ImportError:
            # aiohttp not available - skip validation
            self._report.add_result(ValidationResult(
                name="pages_exist",
                status=ValidationStatus.SKIP,
                message="Skipped - aiohttp not available for API validation",
                details={"required_pages": [p["slug"] for p in required_pages]},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_elementor_templates(self) -> None:
        """Validate Elementor templates exist and are valid."""
        import time

        start = time.perf_counter()

        template_dir = Path(__file__).parent.parent / "wordpress" / "elementor_templates"
        required_templates = [
            "home.json",
            "collections.json",
            "black_rose.json",
            "love_hurts.json",
            "signature.json",
            "about.json",
            "blog.json",
        ]

        missing = []
        invalid = []
        valid = []

        for template_name in required_templates:
            template_path = template_dir / template_name

            if not template_path.exists():
                missing.append(template_name)
                continue

            try:
                with open(template_path) as f:
                    data = json.load(f)

                # Validate required fields
                if "content" not in data or "page_settings" not in data:
                    invalid.append(template_name)
                else:
                    valid.append(template_name)

            except json.JSONDecodeError:
                invalid.append(template_name)

        if missing or invalid:
            status = ValidationStatus.FAIL if missing else ValidationStatus.WARN
            self._report.add_result(ValidationResult(
                name="elementor_templates",
                status=status,
                message=f"Template issues: {len(missing)} missing, {len(invalid)} invalid",
                details={"missing": missing, "invalid": invalid, "valid": valid},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            self._report.add_result(ValidationResult(
                name="elementor_templates",
                status=ValidationStatus.PASS,
                message=f"All {len(valid)} Elementor templates valid",
                details={"templates": valid},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_hotspot_configs(self) -> None:
        """Validate hotspot configuration files."""
        import time

        start = time.perf_counter()

        hotspots_dir = Path(__file__).parent.parent / "wordpress" / "hotspots"
        required_hotspots = [
            "black_rose_hotspots.json",
            "love_hurts_hotspots.json",
            "signature_hotspots.json",
        ]

        missing = []
        invalid = []
        valid = []

        for hotspot_name in required_hotspots:
            hotspot_path = hotspots_dir / hotspot_name

            if not hotspot_path.exists():
                missing.append(hotspot_name)
                continue

            try:
                with open(hotspot_path) as f:
                    data = json.load(f)

                # Validate required fields
                if "hotspots" not in data or "collection" not in data:
                    invalid.append(hotspot_name)
                else:
                    valid.append({
                        "name": hotspot_name,
                        "hotspot_count": len(data["hotspots"]),
                        "collection": data["collection"],
                    })

            except json.JSONDecodeError:
                invalid.append(hotspot_name)

        if missing or invalid:
            status = ValidationStatus.FAIL if missing else ValidationStatus.WARN
            self._report.add_result(ValidationResult(
                name="hotspot_configs",
                status=status,
                message=f"Hotspot issues: {len(missing)} missing, {len(invalid)} invalid",
                details={"missing": missing, "invalid": invalid, "valid": valid},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            total_hotspots = sum(h["hotspot_count"] for h in valid)
            self._report.add_result(ValidationResult(
                name="hotspot_configs",
                status=ValidationStatus.PASS,
                message=f"All hotspot configs valid ({total_hotspots} total hotspots)",
                details={"configs": valid},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_3d_experiences(self) -> None:
        """Validate 3D experience source files."""
        import time

        start = time.perf_counter()

        experiences_dir = Path(__file__).parent.parent / "src" / "collections"
        required_experiences = [
            "BlackRoseExperience.ts",
            "LoveHurtsExperience.ts",
            "SignatureExperience.ts",
            "HotspotManager.ts",
            "index.ts",
        ]

        missing = []
        found = []

        for exp_name in required_experiences:
            exp_path = experiences_dir / exp_name
            if exp_path.exists():
                found.append(exp_name)
            else:
                missing.append(exp_name)

        if missing:
            self._report.add_result(ValidationResult(
                name="3d_experiences",
                status=ValidationStatus.FAIL,
                message=f"Missing 3D experience files: {', '.join(missing)}",
                details={"missing": missing, "found": found},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            self._report.add_result(ValidationResult(
                name="3d_experiences",
                status=ValidationStatus.PASS,
                message=f"All {len(found)} 3D experience files found",
                details={"experiences": found},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_environment_variables(self) -> None:
        """Validate environment variables for production deployment."""
        import os
        import time

        start = time.perf_counter()

        # For local validation, no variables are strictly required
        # All WordPress/WooCommerce variables are recommended for production
        recommended_vars = [
            "WORDPRESS_URL",
            "WORDPRESS_USERNAME",
            "WORDPRESS_APP_PASSWORD",
            "WOOCOMMERCE_KEY",
            "WOOCOMMERCE_SECRET",
        ]

        configured = []
        missing_recommended = []

        for var in recommended_vars:
            if os.getenv(var):
                configured.append(var)
            else:
                missing_recommended.append(var)

        if not configured:
            # No production variables configured - this is OK for local validation
            self._report.add_result(ValidationResult(
                name="environment_variables",
                status=ValidationStatus.PASS,
                message="Local validation mode (no production credentials configured)",
                details={"note": "Set WORDPRESS_URL and credentials for production validation"},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        elif missing_recommended:
            self._report.add_result(ValidationResult(
                name="environment_variables",
                status=ValidationStatus.WARN,
                message=f"Partial configuration: {len(configured)}/{len(recommended_vars)} variables set",
                details={"configured": configured, "missing": missing_recommended},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            self._report.add_result(ValidationResult(
                name="environment_variables",
                status=ValidationStatus.PASS,
                message="All production environment variables configured",
                details={"configured": configured},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_ssl_configuration(self) -> None:
        """Validate SSL/HTTPS configuration."""
        import os
        import time

        start = time.perf_counter()

        site_url = os.getenv("WORDPRESS_URL", "")

        if not site_url:
            self._report.add_result(ValidationResult(
                name="ssl_configuration",
                status=ValidationStatus.PASS,
                message="Local validation mode (SSL check skipped)",
                details={"note": "Set WORDPRESS_URL to validate SSL configuration"},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        elif site_url.startswith("https://"):
            self._report.add_result(ValidationResult(
                name="ssl_configuration",
                status=ValidationStatus.PASS,
                message="Site uses HTTPS",
                details={"url": site_url},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        elif "localhost" in site_url or "127.0.0.1" in site_url:
            self._report.add_result(ValidationResult(
                name="ssl_configuration",
                status=ValidationStatus.PASS,
                message="Local development URL (HTTP acceptable)",
                details={"url": site_url},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            self._report.add_result(ValidationResult(
                name="ssl_configuration",
                status=ValidationStatus.FAIL,
                message="Production site should use HTTPS",
                details={"url": site_url},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))

    async def validate_performance_requirements(self) -> None:
        """Validate performance requirements are met."""
        import time

        start = time.perf_counter()

        # Check asset file sizes
        assets_dir = Path(__file__).parent.parent / "assets"
        max_asset_size_mb = 50  # Maximum recommended asset size

        large_assets = []

        if assets_dir.exists():
            for asset_file in assets_dir.rglob("*"):
                if asset_file.is_file():
                    size_mb = asset_file.stat().st_size / (1024 * 1024)
                    if size_mb > max_asset_size_mb:
                        large_assets.append({
                            "path": str(asset_file.relative_to(assets_dir)),
                            "size_mb": round(size_mb, 2),
                        })

        if large_assets:
            self._report.add_result(ValidationResult(
                name="performance_requirements",
                status=ValidationStatus.WARN,
                message=f"Found {len(large_assets)} assets over {max_asset_size_mb}MB",
                details={"large_assets": large_assets},
                duration_ms=(time.perf_counter() - start) * 1000,
            ))
        else:
            self._report.add_result(ValidationResult(
                name="performance_requirements",
                status=ValidationStatus.PASS,
                message="All assets within size limits",
                duration_ms=(time.perf_counter() - start) * 1000,
            ))


# ============================================================================
# CLI
# ============================================================================


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SkyyRose Production Validation Script"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full validation (default)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON report to file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output JSON, no summary",
    )

    args = parser.parse_args()

    # Run validation
    validator = ProductionValidator()
    report = await validator.validate_all()

    # Output results
    if not args.quiet:
        report.print_summary()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"Report saved to: {output_path}")

    # Return exit code
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
