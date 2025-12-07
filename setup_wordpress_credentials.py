#!/usr/bin/env python3
"""
WordPress Credentials Setup Script for DevSkyy Platform
Interactive script to configure WordPress credentials securely
"""

from getpass import getpass
import os
from pathlib import Path
import sys
from typing import Any

import requests


def print_header():
    """Print setup header."""


def get_user_input(prompt: str, required: bool = True, sensitive: bool = False) -> str:
    """Get user input with validation."""
    while True:
        value = getpass(f"{prompt}: ") if sensitive else input(f"{prompt}: ").strip()

        if value or not required:
            return value


def test_wordpress_connection(
    site_url: str, username: str, password: str, app_password: str | None = None
) -> dict[str, Any]:
    """Test WordPress connection."""
    try:
        # Ensure proper URL format
        if not site_url.startswith(("http://", "https://")):
            site_url = f"https://{site_url}"
        site_url = site_url.rstrip("/")

        # Test basic site connectivity
        response = requests.get(f"{site_url}/wp-json/wp/v2", timeout=10)
        api_accessible = response.status_code == 200

        if not api_accessible:
            return {
                "success": False,
                "error": f"WordPress REST API not accessible (Status: {response.status_code})",
                "site_url": site_url,
            }

        # Test authentication if app password provided
        auth_test = False
        if app_password:
            import base64

            auth_header = base64.b64encode(f"{username}:{app_password}".encode()).decode()

            auth_response = requests.get(
                f"{site_url}/wp-json/wp/v2/users/me", headers={"Authorization": f"Basic {auth_header}"}, timeout=10
            )
            auth_test = auth_response.status_code == 200

        return {
            "success": True,
            "site_url": site_url,
            "api_accessible": api_accessible,
            "auth_test": auth_test,
            "has_app_password": bool(app_password),
        }

    except requests.RequestException as e:
        return {"success": False, "error": f"Connection failed: {e!s}", "site_url": site_url}


def collect_wordpress_credentials() -> dict[str, str]:
    """Collect WordPress credentials from user."""

    credentials = {}

    # Basic WordPress credentials
    credentials["SKYY_ROSE_SITE_URL"] = get_user_input("WordPress Site URL (e.g., https://your-site.com)")
    credentials["SKYY_ROSE_USERNAME"] = get_user_input("WordPress Admin Username")
    credentials["SKYY_ROSE_PASSWORD"] = get_user_input("WordPress Admin Password", sensitive=True)

    # Application password (recommended)

    app_password = get_user_input("Application Password (optional, but recommended)", required=False, sensitive=True)
    if app_password:
        credentials["SKYY_ROSE_APP_PASSWORD"] = app_password

    return credentials


def collect_ftp_credentials() -> dict[str, str]:
    """Collect FTP credentials from user."""

    use_ftp = input("Configure FTP credentials? (y/N): ").lower().startswith("y")

    if not use_ftp:
        return {}

    ftp_credentials = {}
    ftp_credentials["SKYY_ROSE_FTP_HOST"] = get_user_input("FTP Host")
    ftp_credentials["SKYY_ROSE_FTP_USERNAME"] = get_user_input("FTP Username")
    ftp_credentials["SKYY_ROSE_FTP_PASSWORD"] = get_user_input("FTP Password", sensitive=True)

    ftp_port = get_user_input("FTP Port (default: 21)", required=False)
    if ftp_port:
        ftp_credentials["SKYY_ROSE_FTP_PORT"] = ftp_port

    return ftp_credentials


def collect_sftp_credentials() -> dict[str, str]:
    """Collect SFTP credentials from user."""

    use_sftp = input("Configure SFTP credentials? (y/N): ").lower().startswith("y")

    if not use_sftp:
        return {}

    sftp_credentials = {}
    sftp_credentials["SKYY_ROSE_SFTP_HOST"] = get_user_input("SFTP Host")
    sftp_credentials["SKYY_ROSE_SFTP_USERNAME"] = get_user_input("SFTP Username")

    # Choose between password or private key
    auth_method = input("Authentication method - (p)assword or (k)ey file? (p/k): ").lower()

    if auth_method.startswith("k"):
        key_path = get_user_input("Private Key File Path")
        sftp_credentials["SKYY_ROSE_SFTP_PRIVATE_KEY"] = key_path
    else:
        sftp_credentials["SKYY_ROSE_SFTP_PASSWORD"] = get_user_input("SFTP Password", sensitive=True)

    sftp_port = get_user_input("SFTP Port (default: 22)", required=False)
    if sftp_port:
        sftp_credentials["SKYY_ROSE_SFTP_PORT"] = sftp_port

    return sftp_credentials


def update_env_file(credentials: dict[str, str]):
    """Update .env file with credentials."""
    env_file = Path(".env")

    # Read existing .env file
    existing_vars = {}
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_vars[key] = value

    # Update with new credentials
    existing_vars.update(credentials)

    # Write updated .env file
    with open(env_file, "w") as f:
        f.write("# DevSkyy Platform Environment Variables\n")
        f.write(f"# Updated: {os.popen('date').read().strip()}\n\n")

        # WordPress credentials section
        f.write("# ============================================================================\n")
        f.write("# WORDPRESS CREDENTIALS FOR SKYY ROSE COLLECTION\n")
        f.write("# ============================================================================\n\n")

        wp_vars = [k for k in existing_vars if k.startswith("SKYY_ROSE_")]
        for var in sorted(wp_vars):
            f.write(f"{var}={existing_vars[var]}\n")

        # Other variables section
        f.write("\n# ============================================================================\n")
        f.write("# OTHER DEVSKYY CONFIGURATION\n")
        f.write("# ============================================================================\n\n")

        other_vars = [k for k in existing_vars if not k.startswith("SKYY_ROSE_")]
        for var in sorted(other_vars):
            f.write(f"{var}={existing_vars[var]}\n")


def main():
    """Main setup function."""
    print_header()

    try:
        # Collect WordPress credentials
        wp_credentials = collect_wordpress_credentials()

        # Test connection
        test_result = test_wordpress_connection(
            wp_credentials["SKYY_ROSE_SITE_URL"],
            wp_credentials["SKYY_ROSE_USERNAME"],
            wp_credentials["SKYY_ROSE_PASSWORD"],
            wp_credentials.get("SKYY_ROSE_APP_PASSWORD"),
        )

        if test_result["success"]:
            pass
        else:

            continue_anyway = input("Continue with setup anyway? (y/N): ").lower().startswith("y")
            if not continue_anyway:
                return 1

        # Collect optional credentials
        ftp_credentials = collect_ftp_credentials()
        sftp_credentials = collect_sftp_credentials()

        # Combine all credentials
        all_credentials = {**wp_credentials, **ftp_credentials, **sftp_credentials}

        # Update .env file
        update_env_file(all_credentials)

        # Final summary

        return 0

    except KeyboardInterrupt:
        return 1
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())
