#!/usr/bin/env python3
"""
Validate WordPress Setup for SkyyRose Deployment

Checks:
1. WordPress site is accessible
2. REST API is enabled
3. Elementor plugin installed
4. WooCommerce plugin installed
5. Credentials are valid
"""

import asyncio
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))


async def validate_wordpress_setup(
    wordpress_url: str,
    wordpress_username: str,
    wordpress_app_password: str,
) -> dict[str, Any]:
    """Validate WordPress setup.

    Args:
        wordpress_url: WordPress site URL
        wordpress_username: Admin username
        wordpress_app_password: App password

    Returns:
        Validation results dict
    """
    results: dict[str, Any] = {
        "wordpress_url": wordpress_url,
        "username": wordpress_username,
        "checks": {},
        "status": "unknown",
        "errors": [],
        "warnings": [],
    }

    # Ensure URL format
    if not wordpress_url.startswith("http"):
        wordpress_url = f"https://{wordpress_url}"
    if not wordpress_url.endswith("/"):
        wordpress_url += "/"

    results["wordpress_url"] = wordpress_url

    # Create session with auth
    auth = aiohttp.BasicAuth(wordpress_username, wordpress_app_password)

    async with aiohttp.ClientSession(auth=auth) as session:
        # Check 1: Site accessibility
        print("Checking WordPress accessibility...", end=" ")
        try:
            async with session.get(wordpress_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    results["checks"]["site_accessible"] = True
                    print("✓")
                else:
                    results["checks"]["site_accessible"] = False
                    results["errors"].append(f"Site returned status {resp.status}")
                    print(f"✗ (status: {resp.status})")
        except Exception as e:
            results["checks"]["site_accessible"] = False
            results["errors"].append(f"Could not connect: {e}")
            print(f"✗ ({e})")
            return results

        # Check 2: REST API enabled
        print("Checking REST API...", end=" ")
        rest_url = urljoin(wordpress_url, "wp-json/")
        try:
            async with session.get(rest_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    results["checks"]["rest_api_enabled"] = True
                    print("✓")
                else:
                    results["checks"]["rest_api_enabled"] = False
                    results["errors"].append(f"REST API returned {resp.status}")
                    print(f"✗ (status: {resp.status})")
        except Exception as e:
            results["checks"]["rest_api_enabled"] = False
            results["errors"].append(f"REST API error: {e}")
            print(f"✗ ({e})")

        # Check 3: Credentials valid
        print("Checking credentials...", end=" ")
        try:
            async with session.get(urljoin(wordpress_url, "wp-json/wp/v2/users/me")) as resp:
                if resp.status == 200:
                    results["checks"]["credentials_valid"] = True
                    user_data = await resp.json()
                    results["authenticated_user"] = user_data.get("name", "unknown")
                    print(f"✓ ({user_data.get('name')})")
                else:
                    results["checks"]["credentials_valid"] = False
                    results["errors"].append(f"Authentication failed (status: {resp.status})")
                    print("✗ (invalid credentials)")
        except Exception as e:
            results["checks"]["credentials_valid"] = False
            results["errors"].append(f"Authentication error: {e}")
            print(f"✗ ({e})")

        # Check 4: Elementor installed
        print("Checking Elementor plugin...", end=" ")
        try:
            async with session.get(urljoin(wordpress_url, "wp-json/wp/v2/plugins")) as resp:
                if resp.status == 200:
                    plugins = await resp.json()
                    elementor_installed = any("elementor" in p.get("slug", "").lower() for p in plugins)
                    if elementor_installed:
                        results["checks"]["elementor_installed"] = True
                        print("✓")
                    else:
                        results["checks"]["elementor_installed"] = False
                        results["warnings"].append("Elementor plugin not found - install from WordPress.org")
                        print("✗ (not installed)")
                else:
                    results["checks"]["elementor_installed"] = None
                    results["warnings"].append("Could not check plugins (API returned " + str(resp.status) + ")")
                    print("? (could not verify)")
        except Exception as e:
            results["checks"]["elementor_installed"] = None
            results["warnings"].append(f"Could not check Elementor: {e}")
            print(f"? ({e})")

        # Check 5: WooCommerce installed
        print("Checking WooCommerce plugin...", end=" ")
        try:
            async with session.get(urljoin(wordpress_url, "wp-json/wp/v2/plugins")) as resp:
                if resp.status == 200:
                    plugins = await resp.json()
                    woocommerce_installed = any("woocommerce" in p.get("slug", "").lower() for p in plugins)
                    if woocommerce_installed:
                        results["checks"]["woocommerce_installed"] = True
                        print("✓")
                    else:
                        results["checks"]["woocommerce_installed"] = False
                        results["warnings"].append("WooCommerce plugin not found - install from WordPress.org")
                        print("✗ (not installed)")
                else:
                    results["checks"]["woocommerce_installed"] = None
                    print("? (could not verify)")
        except Exception as e:
            results["checks"]["woocommerce_installed"] = None
            results["warnings"].append(f"Could not check WooCommerce: {e}")
            print(f"? ({e})")

    # Determine overall status
    all_checks = results["checks"]
    critical_passed = all(all_checks.get(key) for key in ["site_accessible", "rest_api_enabled", "credentials_valid"])

    if critical_passed:
        results["status"] = "ready"
        if results["warnings"]:
            results["status"] = "ready_with_warnings"
    else:
        results["status"] = "not_ready"

    return results


async def main() -> int:
    """Main entry point."""
    import os

    # Get credentials from environment
    wordpress_url = os.getenv("WORDPRESS_URL", "")
    wordpress_username = os.getenv("WORDPRESS_USERNAME", "admin")
    wordpress_app_password = os.getenv("WORDPRESS_APP_PASSWORD", "")

    # If not from environment, prompt user
    if not wordpress_url:
        print("\n🔧 WordPress Setup Validator")
        print("=" * 50)
        wordpress_url = input("Enter WordPress URL (e.g., https://mysite.local): ").strip()

    if not wordpress_app_password:
        wordpress_app_password = input("Enter app password: ").strip()

    print(f"\nValidating connection to: {wordpress_url}")
    print("=" * 50 + "\n")

    # Validate
    results = await validate_wordpress_setup(
        wordpress_url=wordpress_url,
        wordpress_username=wordpress_username,
        wordpress_app_password=wordpress_app_password,
    )

    # Print results
    print("\n" + "=" * 50)
    print("VALIDATION RESULTS")
    print("=" * 50)
    print(f"Status: {results['status'].upper()}")
    print(f"URL: {results['wordpress_url']}")
    print(f"User: {results.get('authenticated_user', 'unknown')}")

    if results["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    if results["errors"]:
        print("\n❌ Errors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\n" + "=" * 50)

    # Exit code based on status
    if results["status"] == "ready":
        print("✓ Ready to deploy!")
        return 0
    elif results["status"] == "ready_with_warnings":
        print("⚠️  Mostly ready (fix warnings to proceed)")
        return 0
    else:
        print("✗ Not ready - fix errors before deploying")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
