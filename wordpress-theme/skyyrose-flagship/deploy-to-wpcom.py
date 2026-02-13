#!/usr/bin/env python3
"""
WordPress.com Theme Deployment Script

Deploys SkyyRose Flagship theme to WordPress.com using OAuth2 credentials.
"""

import base64
import json
import os
import sys
from pathlib import Path

import requests

# WordPress.com OAuth2 Credentials
CLIENT_ID = "123138"
CLIENT_SECRET = "kQRBrHyNdILBsxtasddwwZCvdglbRBFYltwyW1foKDZ8yOrHsEHbHrZqFNXYNf1F"

# Site configuration
SITE_URL = "skyyrose.co"  # WordPress.com site slug (without https://)
THEME_PACKAGE = Path.home() / "Desktop" / "skyyrose-flagship-2.0.0-wpcom.zip"

# WordPress.com REST API endpoints
WP_COM_API_BASE = "https://public-api.wordpress.com/rest/v1.1"


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.BLUE}━━━ {title} ━━━{Colors.RESET}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def get_access_token() -> str:
    """
    Get OAuth2 access token using client credentials flow.

    Note: WordPress.com requires user authorization for theme uploads.
    This function would need to implement the full OAuth2 flow with
    user consent.
    """
    # For now, we'll use Application Passwords instead (more direct)
    # User needs to generate an application password from WordPress.com
    print_warning("OAuth2 requires user authorization flow")
    print_info("Using WordPress.com Application Password instead")
    print_info("Generate one at: https://wordpress.com/me/security/application-passwords")
    print()

    username = input("Enter your WordPress.com username: ").strip()
    app_password = input("Enter your Application Password: ").strip()

    # Encode credentials for Basic Auth
    credentials = f"{username}:{app_password}"
    encoded = base64.b64encode(credentials.encode()).decode()

    return encoded


def upload_theme(auth_token: str) -> dict:
    """
    Upload theme package to WordPress.com.

    Args:
        auth_token: Base64 encoded Basic Auth credentials

    Returns:
        Response data from WordPress.com API
    """
    print_section("Uploading Theme Package")

    if not THEME_PACKAGE.exists():
        print_error(f"Theme package not found: {THEME_PACKAGE}")
        sys.exit(1)

    print_info(f"Package: {THEME_PACKAGE.name}")
    print_info(f"Size: {THEME_PACKAGE.stat().st_size / 1024:.1f} KB")
    print_info(f"Target: {SITE_URL}")
    print()

    # WordPress.com REST API endpoint for theme upload
    # Note: WordPress.com may not support direct theme upload via API
    # Most likely need to use WordPress admin dashboard
    upload_url = f"{WP_COM_API_BASE}/sites/{SITE_URL}/themes/upload"

    headers = {
        "Authorization": f"Basic {auth_token}",
    }

    with open(THEME_PACKAGE, "rb") as f:
        files = {
            "zip": (THEME_PACKAGE.name, f, "application/zip"),
        }

        try:
            print_info("Uploading theme (this may take 30-60 seconds)...")
            response = requests.post(
                upload_url,
                headers=headers,
                files=files,
                timeout=120,
            )

            if response.status_code == 200:
                print_success("Theme uploaded successfully!")
                return response.json()
            else:
                print_error(f"Upload failed: HTTP {response.status_code}")
                print_error(f"Response: {response.text}")
                return {}

        except requests.exceptions.RequestException as e:
            print_error(f"Upload failed: {e}")
            return {}


def activate_theme(auth_token: str, theme_slug: str = "skyyrose-flagship") -> bool:
    """
    Activate the uploaded theme.

    Args:
        auth_token: Base64 encoded Basic Auth credentials
        theme_slug: Theme slug to activate

    Returns:
        True if activation successful, False otherwise
    """
    print_section("Activating Theme")

    activate_url = f"{WP_COM_API_BASE}/sites/{SITE_URL}/themes/{theme_slug}/activate"

    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(activate_url, headers=headers, timeout=30)

        if response.status_code == 200:
            print_success(f"Theme '{theme_slug}' activated successfully!")
            return True
        else:
            print_error(f"Activation failed: HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Activation failed: {e}")
        return False


def main() -> None:
    """Main deployment workflow."""
    print(f"{Colors.BOLD}")
    print("━" * 80)
    print("  SkyyRose Flagship Theme - WordPress.com Deployment")
    print("  Version 2.0.0")
    print("━" * 80)
    print(f"{Colors.RESET}")

    print_warning("IMPORTANT: WordPress.com API has limitations")
    print_info("Theme upload via API may not be supported on all plans")
    print_info("If API upload fails, use manual upload via WordPress admin")
    print()

    # Get authentication
    auth_token = get_access_token()

    # Upload theme
    upload_result = upload_theme(auth_token)

    if not upload_result:
        print()
        print_section("Manual Upload Instructions")
        print_info("Since API upload failed, please upload manually:")
        print_info("1. Go to: https://wordpress.com/themes/skyyrose.co")
        print_info("2. Click: 'Add New Theme' > 'Upload Theme'")
        print_info(f"3. Select: {THEME_PACKAGE}")
        print_info("4. Click: 'Install Now' > 'Activate'")
        print()
        sys.exit(1)

    # Activate theme
    if upload_result:
        theme_slug = upload_result.get("slug", "skyyrose-flagship")
        activate_theme(auth_token, theme_slug)

    print()
    print_section("Deployment Complete")
    print_success("Theme deployment finished!")
    print_info("Next steps:")
    print_info("1. Verify deployment: ./verify-deployment.sh")
    print_info("2. Follow checklist: DEPLOYMENT-CHECKLIST.md")
    print_info("3. Configure pages and templates")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
