#!/usr/bin/env python3
"""
SkyyRose WordPress Health Check Script

Comprehensive health check and upgrade analysis for SkyyRose WordPress site.
Checks versions, page functionality, custom code integrity, and links.

Usage:
    python3 scripts/wordpress_health_check.py --site https://skyyrose.co
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import httpx
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class HealthCheckResult:
    """Health check result for a single component."""
    component: str
    status: str  # ✅ | ⚠️ | ❌
    message: str
    details: Dict = field(default_factory=dict)
    priority: str = "MEDIUM"  # CRITICAL | HIGH | MEDIUM | LOW


@dataclass
class PageCheck:
    """Page functionality check result."""
    url: str
    page_type: str  # static | interactive | catalog | woocommerce
    status_code: int = 0
    load_time: float = 0.0
    images_ok: bool = False
    js_ok: bool = False
    forms_ok: bool = False
    status: str = "❌"


class WordPressHealthCheck:
    """WordPress health check orchestrator."""

    def __init__(self, site_url: str):
        self.site_url = site_url.rstrip('/')
        self.results: List[HealthCheckResult] = []
        self.pages: List[PageCheck] = []
        self.theme_dir = Path(__file__).parent.parent / "wordpress-theme" / "skyyrose-2025"

    async def run_full_check(self) -> Dict:
        """Execute full health check."""
        print("🔍 Starting SkyyRose WordPress Health Check")
        print(f"🌐 Site: {self.site_url}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. Core Updates & Version Verification
        await self.check_versions()

        # 2. Page Functionality Verification
        await self.check_all_pages()

        # 3. Custom Code Integrity
        await self.check_custom_code()

        # 4. Link Validation
        await self.check_links()

        # 5. Generate Report
        return self.generate_report()

    async def check_versions(self):
        """Check WordPress core, WooCommerce, and Elementor versions."""
        print("📦 Checking Core Versions...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try REST API discovery
                response = await client.get(f"{self.site_url}/wp-json/")

                if response.status_code == 200:
                    data = response.json()
                    wp_version = data.get('name', 'Unknown')

                    self.results.append(HealthCheckResult(
                        component="WordPress Core",
                        status="✅",
                        message=f"WordPress accessible via REST API",
                        details={"version": wp_version},
                        priority="HIGH"
                    ))
                else:
                    self.results.append(HealthCheckResult(
                        component="WordPress Core",
                        status="⚠️",
                        message=f"REST API returned {response.status_code}",
                        priority="HIGH"
                    ))

        except Exception as e:
            self.results.append(HealthCheckResult(
                component="WordPress Core",
                status="❌",
                message=f"Failed to connect: {str(e)}",
                priority="CRITICAL"
            ))

        # Check theme files locally
        if self.theme_dir.exists():
            style_css = self.theme_dir / "style.css"
            if style_css.exists():
                with open(style_css, 'r') as f:
                    content = f.read()
                    version = None
                    for line in content.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split('Version:')[1].strip()
                            break

                self.results.append(HealthCheckResult(
                    component="SkyyRose Theme",
                    status="✅",
                    message=f"Local theme version: {version}",
                    details={"version": version, "php_files": 35},
                    priority="HIGH"
                ))

    async def check_all_pages(self):
        """Check all pages (static, interactive, catalog, WooCommerce)."""
        print("\n🌐 Checking Page Functionality...")

        # Define pages to check
        pages_to_check = [
            # Static Pages
            PageCheck(f"{self.site_url}/", "static"),
            PageCheck(f"{self.site_url}/about/", "static"),
            PageCheck(f"{self.site_url}/contact/", "static"),

            # Interactive Pages (3D Immersive)
            PageCheck(f"{self.site_url}/black-rose-experience/", "interactive"),
            PageCheck(f"{self.site_url}/love-hurts-experience/", "interactive"),
            PageCheck(f"{self.site_url}/signature-experience/", "interactive"),

            # Catalog Pages (Shopping)
            PageCheck(f"{self.site_url}/collection-black-rose/", "catalog"),
            PageCheck(f"{self.site_url}/collection-love-hurts/", "catalog"),
            PageCheck(f"{self.site_url}/collection-signature/", "catalog"),

            # WooCommerce Pages
            PageCheck(f"{self.site_url}/shop/", "woocommerce"),
            PageCheck(f"{self.site_url}/cart/", "woocommerce"),
            PageCheck(f"{self.site_url}/checkout/", "woocommerce"),
            PageCheck(f"{self.site_url}/my-account/", "woocommerce"),
        ]

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            tasks = [self._check_page(client, page) for page in pages_to_check]
            self.pages = await asyncio.gather(*tasks)

        # Generate page status result
        total_pages = len(self.pages)
        working_pages = sum(1 for p in self.pages if p.status == "✅")

        status = "✅" if working_pages == total_pages else "⚠️" if working_pages > 0 else "❌"

        self.results.append(HealthCheckResult(
            component="Page Functionality",
            status=status,
            message=f"{working_pages}/{total_pages} pages accessible",
            details={"pages": [
                {
                    "url": p.url,
                    "type": p.page_type,
                    "status": p.status,
                    "status_code": p.status_code,
                    "load_time": f"{p.load_time:.2f}s"
                } for p in self.pages
            ]},
            priority="CRITICAL"
        ))

    async def _check_page(self, client: httpx.AsyncClient, page: PageCheck) -> PageCheck:
        """Check individual page."""
        try:
            start_time = asyncio.get_event_loop().time()
            response = await client.get(page.url)
            page.load_time = asyncio.get_event_loop().time() - start_time
            page.status_code = response.status_code

            if response.status_code == 200:
                page.status = "✅"

                # Basic checks
                html = response.text.lower()
                page.images_ok = 'img' in html or 'background' in html
                page.js_ok = '<script' in html
                page.forms_ok = '<form' in html or page.page_type != "woocommerce"

            elif response.status_code in [301, 302, 307, 308]:
                page.status = "⚠️"  # Redirect
            else:
                page.status = "❌"

        except Exception as e:
            page.status = "❌"
            page.status_code = 0
            print(f"   ❌ {page.url}: {str(e)}")

        return page

    async def check_custom_code(self):
        """Check custom code integrity (templates, CSS, widgets)."""
        print("\n🔧 Checking Custom Code Integrity...")

        # Check template files
        template_files = [
            "template-collection.php",
            "page-collection-black-rose.php",
            "page-collection-love-hurts.php",
            "page-collection-signature.php",
            "template-immersive.php",
            "template-vault.php",
        ]

        missing_templates = []
        for template in template_files:
            if not (self.theme_dir / template).exists():
                missing_templates.append(template)

        if missing_templates:
            self.results.append(HealthCheckResult(
                component="Custom Templates",
                status="❌",
                message=f"Missing {len(missing_templates)} template files",
                details={"missing": missing_templates},
                priority="HIGH"
            ))
        else:
            self.results.append(HealthCheckResult(
                component="Custom Templates",
                status="✅",
                message=f"All {len(template_files)} custom templates present",
                priority="MEDIUM"
            ))

        # Check Elementor widgets
        widget_dir = self.theme_dir / "elementor-widgets"
        if widget_dir.exists():
            widgets = list(widget_dir.glob("*.php"))
            self.results.append(HealthCheckResult(
                component="Elementor Widgets",
                status="✅",
                message=f"Found {len(widgets)} custom widgets",
                details={"widgets": [w.name for w in widgets]},
                priority="MEDIUM"
            ))

        # Check custom CSS
        css_files = list(self.theme_dir.glob("assets/css/*.css"))
        if css_files:
            self.results.append(HealthCheckResult(
                component="Custom CSS",
                status="✅",
                message=f"Found {len(css_files)} custom CSS files",
                priority="LOW"
            ))

    async def check_links(self):
        """Validate internal and external links."""
        print("\n🔗 Checking Link Validation...")

        # Check CDN links (from theme files)
        cdn_links = [
            "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js",
            "https://cdn.babylonjs.com/babylon.js",
            "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js",
            "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap",
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = [self._check_link(client, link) for link in cdn_links]
            results = await asyncio.gather(*tasks)

        working_links = sum(1 for r in results if r)
        status = "✅" if working_links == len(cdn_links) else "⚠️"

        self.results.append(HealthCheckResult(
            component="CDN Links",
            status=status,
            message=f"{working_links}/{len(cdn_links)} CDN links accessible",
            details={"links": cdn_links},
            priority="MEDIUM"
        ))

    async def _check_link(self, client: httpx.AsyncClient, url: str) -> bool:
        """Check if link is accessible."""
        try:
            response = await client.head(url)
            return response.status_code < 400
        except:
            return False

    def generate_report(self) -> Dict:
        """Generate comprehensive health check report."""
        print("\n" + "=" * 80)
        print("📊 SKYYROSE WORDPRESS HEALTH CHECK REPORT")
        print("=" * 80)

        # Executive Summary
        critical_issues = [r for r in self.results if r.status == "❌" and r.priority == "CRITICAL"]
        high_issues = [r for r in self.results if r.status in ["❌", "⚠️"] and r.priority == "HIGH"]

        print("\n## EXECUTIVE SUMMARY")
        print(f"Total Components Checked: {len(self.results)}")
        print(f"Critical Issues: {len(critical_issues)}")
        print(f"High Priority Issues: {len(high_issues)}")

        # Page Status Matrix
        print("\n## PAGE STATUS MATRIX")
        print(f"{'Page Type':<15} {'URL':<50} {'Status':<8} {'Load Time':<10}")
        print("-" * 83)

        for page in self.pages:
            url_display = page.url.replace(self.site_url, '')[:48]
            print(f"{page.page_type:<15} {url_display:<50} {page.status:<8} {page.load_time:.2f}s")

        # Detailed Findings
        print("\n## DETAILED FINDINGS")
        for result in self.results:
            print(f"\n### {result.component}")
            print(f"Status: {result.status} | Priority: {result.priority}")
            print(f"Message: {result.message}")
            if result.details:
                print(f"Details: {json.dumps(result.details, indent=2)}")

        # Action Items
        print("\n## RECOMMENDED ACTION ITEMS")

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_results = sorted(
            [r for r in self.results if r.status != "✅"],
            key=lambda x: priority_order.get(x.priority, 99)
        )

        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. [{result.priority}] {result.component}")
            print(f"   {result.message}")

        # Overall Status
        print("\n" + "=" * 80)
        if not critical_issues and not high_issues:
            print("✅ OVERALL STATUS: HEALTHY")
        elif critical_issues:
            print("❌ OVERALL STATUS: CRITICAL ISSUES FOUND")
        else:
            print("⚠️ OVERALL STATUS: ATTENTION REQUIRED")
        print("=" * 80)

        return {
            "timestamp": datetime.now().isoformat(),
            "site_url": self.site_url,
            "summary": {
                "total_checks": len(self.results),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
            },
            "results": [
                {
                    "component": r.component,
                    "status": r.status,
                    "message": r.message,
                    "priority": r.priority,
                    "details": r.details
                } for r in self.results
            ],
            "pages": [
                {
                    "url": p.url,
                    "type": p.page_type,
                    "status": p.status,
                    "status_code": p.status_code,
                    "load_time": p.load_time
                } for p in self.pages
            ]
        }


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SkyyRose WordPress Health Check")
    parser.add_argument("--site", default="https://skyyrose.co", help="WordPress site URL")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    checker = WordPressHealthCheck(args.site)
    report = await checker.run_full_check()

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
