#!/usr/bin/env python3
"""
Verify Elementor Page Deployment

Checks that all pages were deployed successfully to WordPress.
Verifies:
- Pages exist
- Elementor data is attached
- Status is correct

Usage:
    python verify_deployment.py
    python verify_deployment.py --verbose
"""

import argparse
import asyncio
import base64
from dataclasses import dataclass
from http import HTTPStatus
import json
import os
from pathlib import Path
import sys
from typing import Any, ClassVar

import httpx


# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class VerificationResult:
    """Result of page verification."""

    page_slug: str
    page_title: str
    exists: bool
    has_elementor_data: bool
    status: str
    page_id: int | None = None
    page_url: str | None = None
    error: str | None = None


class DeploymentVerifier:
    """Verify Elementor page deployments."""

    # Expected pages (same as deployer)
    EXPECTED_PAGES: ClassVar[dict[str, dict[str, Any]]] = {
        "home": {"title": "Homepage", "type": "page"},
        "about": {"title": "About SkyyRose", "type": "page"},
        "love-hurts-collection": {"title": "Love Hurts Collection", "type": "page"},
        "black-rose-collection": {"title": "Black Rose Collection", "type": "page"},
        "signature-collection": {"title": "Signature Collection", "type": "page"},
    }

    EXPECTED_TEMPLATES: ClassVar[dict[str, dict[str, str]]] = {
        "sr-header": {"title": "Global Header", "type": "elementor_library"},
        "sr-footer": {"title": "Global Footer", "type": "elementor_library"},
        "sr-archive-product": {"title": "Shop Archive Template", "type": "elementor_library"},
        "sr-single-product": {"title": "Single Product Template", "type": "elementor_library"},
    }

    def __init__(self, site_url: str, username: str, password: str):
        """Initialize verifier with WordPress credentials."""
        self.site_url = site_url.rstrip("/")
        self.api_base = f"{self.site_url}/wp-json"
        self.username = username
        self.password = password

        # Create basic auth header
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.auth_header = {"Authorization": f"Basic {encoded}"}

        self.results: list[VerificationResult] = []

    async def verify_page(self, slug: str, expected: dict) -> VerificationResult:
        """Verify a single page exists and has Elementor data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.api_base}/wp/v2/pages", params={"slug": slug}, headers=self.auth_header
                )

                if response.status_code != HTTPStatus.OK:
                    return VerificationResult(
                        page_slug=slug,
                        page_title=expected.get("title", slug),
                        exists=False,
                        has_elementor_data=False,
                        status="error",
                        error=f"HTTP {response.status_code}",
                    )

                pages = response.json()
                if not pages:
                    return VerificationResult(
                        page_slug=slug,
                        page_title=expected.get("title", slug),
                        exists=False,
                        has_elementor_data=False,
                        status="not_found",
                    )

                page = pages[0]
                page_id = page.get("id")
                page_url = page.get("link")
                status = page.get("status", "unknown")

                # Check for Elementor data in meta
                meta = page.get("meta", {})
                has_elementor = meta.get("_elementor_edit_mode") == "builder" or "_elementor_data" in meta

                return VerificationResult(
                    page_slug=slug,
                    page_title=page.get("title", {}).get("rendered", slug),
                    exists=True,
                    has_elementor_data=has_elementor,
                    status=status,
                    page_id=page_id,
                    page_url=page_url,
                )

            except Exception as e:
                return VerificationResult(
                    page_slug=slug,
                    page_title=expected.get("title", slug),
                    exists=False,
                    has_elementor_data=False,
                    status="error",
                    error=str(e),
                )

    async def verify_template(self, slug: str, expected: dict) -> VerificationResult:
        """Verify an Elementor library template exists."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Try elementor_library endpoint first
                response = await client.get(
                    f"{self.api_base}/wp/v2/elementor_library", params={"slug": slug}, headers=self.auth_header
                )

                if response.status_code == HTTPStatus.NOT_FOUND:
                    # Endpoint not available, check pages instead
                    return await self.verify_page(slug, expected)

                if response.status_code != HTTPStatus.OK:
                    return VerificationResult(
                        page_slug=slug,
                        page_title=expected.get("title", slug),
                        exists=False,
                        has_elementor_data=False,
                        status="error",
                        error=f"HTTP {response.status_code}",
                    )

                templates = response.json()
                if not templates:
                    return VerificationResult(
                        page_slug=slug,
                        page_title=expected.get("title", slug),
                        exists=False,
                        has_elementor_data=False,
                        status="not_found",
                    )

                template = templates[0]
                return VerificationResult(
                    page_slug=slug,
                    page_title=template.get("title", {}).get("rendered", slug),
                    exists=True,
                    has_elementor_data=True,  # Elementor library items always have data
                    status=template.get("status", "unknown"),
                    page_id=template.get("id"),
                    page_url=template.get("link"),
                )

            except Exception as e:
                return VerificationResult(
                    page_slug=slug,
                    page_title=expected.get("title", slug),
                    exists=False,
                    has_elementor_data=False,
                    status="error",
                    error=str(e),
                )

    async def verify_all(self, verbose: bool = False) -> dict:
        """Verify all expected pages and templates."""
        print("=" * 60)
        print(f"Verifying Deployment on {self.site_url}")
        print("=" * 60)

        # Verify pages
        print("\nPages:")
        for slug, expected in self.EXPECTED_PAGES.items():
            result = await self.verify_page(slug, expected)
            self.results.append(result)

            status_icon = "[OK]" if result.exists and result.has_elementor_data else "[!]" if result.exists else "[X]"
            print(f"  {status_icon} {slug}: {result.status}")
            if verbose and result.page_url:
                print(f"      URL: {result.page_url}")
            if result.error:
                print(f"      Error: {result.error}")

        # Verify templates
        print("\nTheme Templates:")
        for slug, expected in self.EXPECTED_TEMPLATES.items():
            result = await self.verify_template(slug, expected)
            self.results.append(result)

            status_icon = "[OK]" if result.exists and result.has_elementor_data else "[!]" if result.exists else "[X]"
            print(f"  {status_icon} {slug}: {result.status}")
            if verbose and result.page_id:
                print(f"      Edit: {self.site_url}/wp-admin/post.php?post={result.page_id}&action=elementor")
            if result.error:
                print(f"      Error: {result.error}")

        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)

        pages_ok = sum(1 for r in self.results if r.exists and r.has_elementor_data)
        pages_missing = sum(1 for r in self.results if not r.exists)
        pages_no_elementor = sum(1 for r in self.results if r.exists and not r.has_elementor_data)

        print(f"\n  Total Expected: {len(self.results)}")
        print(f"  Fully Deployed: {pages_ok}")
        print(f"  Missing: {pages_missing}")
        print(f"  Missing Elementor Data: {pages_no_elementor}")

        all_ok = pages_ok == len(self.results)

        if all_ok:
            print("\n  [SUCCESS] All pages deployed correctly!")
        else:
            print("\n  [INCOMPLETE] Some pages need attention")

        return {
            "success": all_ok,
            "total": len(self.results),
            "deployed": pages_ok,
            "missing": pages_missing,
            "no_elementor_data": pages_no_elementor,
            "results": [
                {
                    "slug": r.page_slug,
                    "title": r.page_title,
                    "exists": r.exists,
                    "has_elementor_data": r.has_elementor_data,
                    "status": r.status,
                    "page_id": r.page_id,
                    "url": r.page_url,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify Elementor page deployment")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    args = parser.parse_args()

    # Get credentials from environment
    site_url = os.getenv("SKYY_ROSE_SITE_URL")
    username = os.getenv("SKYY_ROSE_USERNAME")
    password = os.getenv("SKYY_ROSE_APP_PASSWORD") or os.getenv("SKYY_ROSE_PASSWORD")

    if not all([site_url, username, password]):
        print("ERROR: Missing WordPress credentials")
        print("Required environment variables:")
        print("  SKYY_ROSE_SITE_URL")
        print("  SKYY_ROSE_USERNAME")
        print("  SKYY_ROSE_APP_PASSWORD (or SKYY_ROSE_PASSWORD)")
        sys.exit(1)

    verifier = DeploymentVerifier(site_url, username, password)
    result = await verifier.verify_all(verbose=args.verbose)

    # Save results
    results_file = Path(__file__).parent / "verification_results.json"
    with open(results_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to: {results_file}")

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
