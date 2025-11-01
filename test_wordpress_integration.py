#!/usr/bin/env python3
import logging

logger = logging.getLogger(__name__)

"""
WordPress Integration Testing Script
Test all WordPress credential configurations and theme builder integration
"""

import asyncio
import sys
import os
from pathlib import Path
import json
import tempfile
import shutil

# Add DevSkyy to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_credential_loading():
    """Test credential loading from environment."""
    logger.info("🔐 Testing Credential Loading")
    logger.info("-" * 40)

    try:
        from config.wordpress_credentials import (
            wordpress_credentials_manager,
            get_skyy_rose_credentials,
            validate_environment_setup,
            list_configured_sites,
        )

        # Test environment validation
        env_validation = validate_environment_setup()
        logger.info(f"Environment validation: {'✅ VALID' if env_validation['valid'] else '❌ INVALID'}")

        if env_validation["missing_required"]:
            logger.info(f"❌ Missing required variables: {env_validation['missing_required']}")
            return False

        if env_validation["configured_vars"]:
            logger.info(f"✅ Configured variables: {len(env_validation['configured_vars'])}")

        # Test credential loading
        credentials = get_skyy_rose_credentials()
        if credentials:
            logger.info(f"✅ Skyy Rose credentials loaded")
            logger.info(f"   Site URL: {credentials.site_url}")
            logger.info(f"   Username: {credentials.username}")
            logger.info(f"   Has app password: {bool(credentials.application_password)}")
            logger.info(f"   Has FTP: {credentials.has_ftp_credentials()}")
            logger.info(f"   Has SFTP: {credentials.has_sftp_credentials()}")
            return True
        else:
            logger.info("❌ No Skyy Rose credentials found")
            return False

    except Exception as e:
        logger.error(f"❌ Credential loading failed: {e}")
        return False


async def test_wordpress_connection():
    """Test WordPress REST API connection."""
    logger.info("\n🌐 Testing WordPress Connection")
    logger.info("-" * 40)

    try:
        from config.wordpress_credentials import get_skyy_rose_credentials
        import requests
        import base64

        credentials = get_skyy_rose_credentials()
        if not credentials:
            logger.info("❌ No credentials available for testing")
            return False

        # Test basic site connectivity
        logger.info(f"🔍 Testing connection to: {credentials.site_url}")

        try:
            response = requests.get(f"{credentials.site_url}/wp-json/wp/v2", timeout=10)
            api_accessible = response.status_code == 200

            if api_accessible:
                logger.info("✅ WordPress REST API accessible")
            else:
                logger.info(f"❌ WordPress REST API not accessible (Status: {response.status_code})")
                return False

        except requests.RequestException as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

        # Test authentication
        if credentials.application_password:
            logger.info("🔑 Testing authentication with application password...")

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
                    user_data = auth_response.json()
                    logger.info(f"✅ Authentication successful")
                    logger.info(f"   Logged in as: {user_data.get('name', 'Unknown')}")
                    logger.info(f"   User roles: {user_data.get('roles', [])}")
                    return True
                else:
                    logger.error(f"❌ Authentication failed (Status: {auth_response.status_code})")
                    logger.info(f"   Response: {auth_response.text[:200]}")
                    return False

            except requests.RequestException as e:
                logger.error(f"❌ Authentication test failed: {e}")
                return False
        else:
            logger.info("⚠️ No application password configured - skipping auth test")
            return True

    except Exception as e:
        logger.error(f"❌ WordPress connection test failed: {e}")
        return False


async def test_theme_package_creation():
    """Test theme package creation."""
    logger.info("\n📦 Testing Theme Package Creation")
    logger.info("-" * 40)

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

            logger.info(f"📁 Created test theme at: {theme_dir}")

            # Test package creation
            theme_info = {
                "name": "test-theme",
                "version": "1.0.0",
                "description": "Test theme for DevSkyy integration",
                "author": "DevSkyy Platform",
            }

            package = await automated_theme_uploader.create_theme_package(str(theme_dir), theme_info)

            logger.info(f"✅ Theme package created successfully")
            logger.info(f"   Package name: {package.name}")
            logger.info(f"   Package size: {package.size_bytes / 1024:.1f} KB")
            logger.info(f"   Files count: {len(package.files)}")
            logger.info(f"   Checksum: {package.checksum[:16]}...")

            # Test package validation
            validation_results = await automated_theme_uploader.validate_theme_package(package)

            if validation_results["valid"]:
                logger.info("✅ Theme package validation passed")
                if validation_results["warnings"]:
                    logger.warning(f"   Warnings: {len(validation_results['warnings'])}")
            else:
                logger.error("❌ Theme package validation failed")
                logger.error(f"   Errors: {validation_results['errors']}")
                return False

            # Clean up package file
            if Path(package.package_path).exists():
                Path(package.package_path).unlink()

            return True

    except Exception as e:
        logger.error(f"❌ Theme package creation failed: {e}")
        return False


async def test_theme_builder_orchestrator():
    """Test theme builder orchestrator."""
    logger.info("\n🎨 Testing Theme Builder Orchestrator")
    logger.info("-" * 40)

    try:
        from agent.wordpress.theme_builder_orchestrator import theme_builder_orchestrator, ThemeType
        from config.wordpress_credentials import get_skyy_rose_credentials

        credentials = get_skyy_rose_credentials()
        if not credentials:
            logger.info("❌ No credentials available for testing")
            return False

        # Test creating a build request
        build_request = theme_builder_orchestrator.create_skyy_rose_build_request(
            theme_name="test-skyy-rose-theme",
            theme_type=ThemeType.LUXURY_FASHION,
            auto_deploy=False,  # Don't actually deploy during testing
            customizations={"test_mode": True, "colors": {"primary": "#1a1a1a", "secondary": "#d4af37"}},
        )

        if build_request:
            logger.info("✅ Theme build request created successfully")
            logger.info(f"   Theme name: {build_request.theme_name}")
            logger.info(f"   Theme type: {build_request.theme_type.value}")
            logger.info(f"   Target site: {build_request.target_site}")
            logger.info(f"   Auto deploy: {build_request.auto_deploy}")

            # Test system status
            status = theme_builder_orchestrator.get_system_status()
            logger.info(f"✅ Orchestrator system status retrieved")
            logger.info(f"   Supported theme types: {len(status['supported_theme_types'])}")
            logger.info(f"   Available sites: {status['available_sites']}")

            return True
        else:
            logger.error("❌ Failed to create theme build request")
            return False

    except Exception as e:
        logger.error(f"❌ Theme builder orchestrator test failed: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoints (if server is running)."""
    logger.info("\n🌐 Testing API Endpoints")
    logger.info("-" * 40)

    try:
        import requests

        base_url = "http://localhost:8000"

        # Test credentials status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/credentials/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Credentials status endpoint working")
                logger.info(f"   Configured sites: {data.get('configured_sites', [])}")
                logger.info(f"   Has default credentials: {data.get('has_default_credentials', False)}")
            else:
                logger.info(f"⚠️ Credentials status endpoint returned: {response.status_code}")
        except requests.RequestException:
            logger.info("⚠️ API server not running - skipping endpoint tests")
            return True

        # Test system status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/system-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ System status endpoint working")
                logger.info(f"   Available theme types: {len(data.get('available_theme_types', []))}")
                logger.info(f"   Upload methods: {len(data.get('supported_upload_methods', []))}")
            else:
                logger.info(f"⚠️ System status endpoint returned: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"⚠️ System status endpoint failed: {e}")

        # Test WordPress connection endpoint
        try:
            response = requests.post(
                f"{base_url}/api/v1/themes/credentials/test", json={"site_key": "skyy_rose"}, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ WordPress connection test endpoint working")
                logger.info(f"   Connection status: {data.get('status', 'unknown')}")
                logger.info(f"   API accessible: {data.get('api_accessible', False)}")
                logger.info(f"   Auth test: {data.get('authentication_test', False)}")
            else:
                logger.info(f"⚠️ WordPress connection test returned: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"⚠️ WordPress connection test failed: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ API endpoint testing failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    logger.info("🧪 DevSkyy WordPress Integration Test Suite")
    logger.info("=" * 60)

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
        except Exception as e:
            logger.info(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1

    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        logger.info("🎉 All tests passed! WordPress integration is ready.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Check configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
