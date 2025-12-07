#!/usr/bin/env python3
"""
WordPress Integration Testing Script
Test all WordPress credential configurations and theme builder integration
"""

import asyncio
from pathlib import Path
import sys
import tempfile


# Add DevSkyy to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_credential_loading():
    """Test credential loading from environment."""

    try:
        from config.wordpress_credentials import get_skyy_rose_credentials, validate_environment_setup

        # Test environment validation
        env_validation = validate_environment_setup()

        if env_validation["missing_required"]:
            return False

        if env_validation["configured_vars"]:
            pass

        # Test credential loading
        credentials = get_skyy_rose_credentials()
        return bool(credentials)

    except Exception:
        return False


async def test_wordpress_connection():
    """Test WordPress REST API connection."""

    try:
        import base64

        import requests

        from config.wordpress_credentials import get_skyy_rose_credentials

        credentials = get_skyy_rose_credentials()
        if not credentials:
            return False

        # Test basic site connectivity

        try:
            response = requests.get(f"{credentials.site_url}/wp-json/wp/v2", timeout=10)
            api_accessible = response.status_code == 200

            if api_accessible:
                pass
            else:
                return False

        except requests.RequestException:
            return False

        # Test authentication
        if credentials.application_password:

            auth_header = base64.b64encode(
                f"{credentials.username}:{credentials.application_password}".encode()
            ).decode()

            try:
                auth_response = requests.get(
                    f"{credentials.site_url}/wp-json/wp/v2/users/me",
                    headers={"Authorization": f"Basic {auth_header}"},
                    timeout=10,
                )

                if auth_response.status_code == 200:
                    auth_response.json()
                    return True
                else:
                    return False

            except requests.RequestException:
                return False
        else:
            return True

    except Exception:
        return False


async def test_theme_package_creation():
    """Test theme package creation."""

    try:
        from agent.wordpress.automated_theme_uploader import automated_theme_uploader

        # Create a temporary theme directory
        with tempfile.TemporaryDirectory() as temp_dir:
            theme_dir = Path(temp_dir) / "test-theme"
            theme_dir.mkdir()

            # Create basic theme files
            (theme_dir / "style.css").write_text(
                """/*
Theme Name: Test Theme
Description: Test theme for DevSkyy
Version: 1.0.0
Author: DevSkyy Platform
*/"""
            )

            (theme_dir / "index.php").write_text(
                """<?php
// Test theme index
get_header();
echo '<h1>Test Theme</h1>';
get_footer();
?>"""
            )

            (theme_dir / "functions.php").write_text(
                """<?php
// Test theme functions
function test_theme_setup() {
    add_theme_support('post-thumbnails');
}
add_action('after_setup_theme', 'test_theme_setup');
?>"""
            )

            # Test package creation
            theme_info = {
                "name": "test-theme",
                "version": "1.0.0",
                "description": "Test theme for DevSkyy integration",
                "author": "DevSkyy Platform",
            }

            package = await automated_theme_uploader.create_theme_package(str(theme_dir), theme_info)

            # Test package validation
            validation_results = await automated_theme_uploader.validate_theme_package(package)

            if validation_results["valid"]:
                if validation_results["warnings"]:
                    pass
            else:
                return False

            # Clean up package file
            if Path(package.package_path).exists():
                Path(package.package_path).unlink()

            return True

    except Exception:
        return False


async def test_theme_builder_orchestrator():
    """Test theme builder orchestrator."""

    try:
        from agent.wordpress.theme_builder_orchestrator import ThemeType, theme_builder_orchestrator
        from config.wordpress_credentials import get_skyy_rose_credentials

        credentials = get_skyy_rose_credentials()
        if not credentials:
            return False

        # Test creating a build request
        build_request = theme_builder_orchestrator.create_skyy_rose_build_request(
            theme_name="test-skyy-rose-theme",
            theme_type=ThemeType.LUXURY_FASHION,
            auto_deploy=False,  # Don't actually deploy during testing
            customizations={"test_mode": True, "colors": {"primary": "#1a1a1a", "secondary": "#d4af37"}},
        )

        if build_request:

            # Test system status
            theme_builder_orchestrator.get_system_status()

            return True
        else:
            return False

    except Exception:
        return False


async def test_api_endpoints():
    """Test API endpoints (if server is running)."""

    try:
        import requests

        base_url = "http://localhost:8000"

        # Test credentials status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/credentials/status", timeout=5)
            if response.status_code == 200:
                response.json()
            else:
                pass
        except requests.RequestException:
            return True

        # Test system status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/system-status", timeout=5)
            if response.status_code == 200:
                response.json()
            else:
                pass
        except requests.RequestException:
            pass

        # Test WordPress connection endpoint
        try:
            response = requests.post(
                f"{base_url}/api/v1/themes/credentials/test", json={"site_key": "skyy_rose"}, timeout=10
            )
            if response.status_code == 200:
                response.json()
            else:
                pass
        except requests.RequestException:
            pass

        return True

    except Exception:
        return False


async def main():
    """Run all integration tests."""

    tests = [
        ("Credential Loading", test_credential_loading),
        ("WordPress Connection", test_wordpress_connection),
        ("Theme Package Creation", test_theme_package_creation),
        ("Theme Builder Orchestrator", test_theme_builder_orchestrator),
        ("API Endpoints", test_api_endpoints),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception:
            results.append((test_name, False))

    # Summary

    passed = 0
    total = len(results)

    for test_name, result in results:
        if result:
            passed += 1

    if passed == total:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
