#!/usr/bin/env python3
"""
WordPress REST API Diagnostic Tool

Tests WordPress REST API connectivity and authentication step-by-step.
Helps identify configuration issues before running full media upload.

Usage:
    python scripts/diagnose_wordpress_api.py

Requirements:
    - .env file with WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD
"""

import os
import sys

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

# Colors for output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def print_test(name: str, status: str, details: str = "") -> None:
    """Print formatted test result."""
    status_color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
    print(f"{status_color}[{status}]{NC} {name}")
    if details:
        print(f"       {details}")


def test_1_base_url() -> bool:
    """Test 1: Verify WordPress base URL is accessible."""
    print(f"\n{BLUE}Test 1: Base URL Accessibility{NC}")
    print(f"URL: {WP_URL}")

    try:
        response = requests.get(WP_URL, timeout=10)
        if response.status_code == 200:
            print_test("Base URL accessible", "PASS", f"Status: {response.status_code}")
            return True
        else:
            print_test(
                "Base URL accessible",
                "WARN",
                f"Status: {response.status_code} (not 200, but may still work)",
            )
            return True
    except Exception as e:
        print_test("Base URL accessible", "FAIL", f"Error: {e}")
        return False


def test_2_rest_api_enabled() -> bool:
    """Test 2: Verify WordPress REST API is enabled."""
    print(f"\n{BLUE}Test 2: REST API Enabled{NC}")
    endpoint = f"{WP_URL}/wp-json/"

    try:
        response = requests.get(endpoint, timeout=10)
        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200:
            # Check if response is JSON
            if "application/json" in content_type:
                data = response.json()
                print_test("REST API enabled", "PASS", f"Namespace: {data.get('namespaces', [])}")
                return True
            else:
                # Got HTML or other non-JSON response
                print_test(
                    "REST API enabled", "FAIL", f"Got {content_type}, expected application/json"
                )
                print(f"       Response preview: {response.text[:300]}")
                print("       This usually means REST API is disabled or blocked")
                return False
        else:
            print_test("REST API enabled", "FAIL", f"Status: {response.status_code}")
            print(f"       Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_test("REST API enabled", "FAIL", f"Error: {e}")
        return False


def test_3_credentials_configured() -> bool:
    """Test 3: Verify credentials are configured in .env."""
    print(f"\n{BLUE}Test 3: Credentials Configuration{NC}")

    if not WP_USERNAME:
        print_test("Username configured", "FAIL", "WORDPRESS_USERNAME not in .env")
        return False
    else:
        print_test("Username configured", "PASS", f"Username: {WP_USERNAME}")

    if not WP_APP_PASSWORD:
        print_test("App Password configured", "FAIL", "WORDPRESS_APP_PASSWORD not in .env")
        return False
    else:
        # Mask password for security
        masked = f"{WP_APP_PASSWORD[:4]}...{WP_APP_PASSWORD[-4:]}"
        print_test("App Password configured", "PASS", f"Password: {masked}")

    return True


def test_4_authentication() -> bool:
    """Test 4: Test authentication with a simple GET request."""
    print(f"\n{BLUE}Test 4: Authentication Test{NC}")
    endpoint = f"{WP_URL}/wp-json/wp/v2/users/me"

    if not WP_USERNAME or not WP_APP_PASSWORD:
        print_test("Authentication", "SKIP", "Credentials not configured")
        return False

    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.get(endpoint, auth=auth, timeout=10)
        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200:
            # Check if response is JSON
            if "application/json" in content_type:
                data = response.json()
                print_test(
                    "Authentication",
                    "PASS",
                    f"Logged in as: {data.get('name')} (ID: {data.get('id')})",
                )
                return True
            else:
                print_test("Authentication", "FAIL", f"Got {content_type}, expected JSON")
                print(f"       Response preview: {response.text[:300]}")
                print("       Hint: REST API may be disabled or returning login page")
                return False
        elif response.status_code == 401:
            print_test("Authentication", "FAIL", "401 Unauthorized - Check credentials")
            print(f"       Response: {response.text[:200]}")
            return False
        else:
            print_test("Authentication", "FAIL", f"Status: {response.status_code}")
            print(f"       Content-Type: {content_type}")
            print(f"       Response: {response.text[:300]}")
            return False
    except Exception as e:
        print_test("Authentication", "FAIL", f"Error: {e}")
        print("       This usually means response is not valid JSON")
        return False


def test_5_media_endpoint() -> bool:
    """Test 5: Test media endpoint accessibility (GET request)."""
    print(f"\n{BLUE}Test 5: Media Endpoint Access{NC}")
    endpoint = f"{WP_URL}/wp-json/wp/v2/media"

    if not WP_USERNAME or not WP_APP_PASSWORD:
        print_test("Media endpoint", "SKIP", "Credentials not configured")
        return False

    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.get(endpoint, auth=auth, timeout=10)
        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200:
            if "application/json" in content_type:
                data = response.json()
                print_test("Media endpoint", "PASS", f"Found {len(data)} media items")
                return True
            else:
                print_test("Media endpoint", "FAIL", f"Got {content_type}, expected JSON")
                print(f"       Response preview: {response.text[:300]}")
                return False
        elif response.status_code == 401:
            print_test("Media endpoint", "FAIL", "401 Unauthorized")
            return False
        else:
            print_test(
                "Media endpoint",
                "WARN",
                f"Status: {response.status_code} (may still work for POST)",
            )
            return True
    except Exception as e:
        print_test("Media endpoint", "FAIL", f"Error: {e}")
        return False


def test_6_media_upload_capability() -> bool:
    """Test 6: Check user capabilities for media upload."""
    print(f"\n{BLUE}Test 6: Media Upload Capability{NC}")
    endpoint = f"{WP_URL}/wp-json/wp/v2/users/me"

    if not WP_USERNAME or not WP_APP_PASSWORD:
        print_test("Upload capability", "SKIP", "Credentials not configured")
        return False

    try:
        auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
        response = requests.get(endpoint, auth=auth, params={"context": "edit"}, timeout=10)
        content_type = response.headers.get("Content-Type", "")

        if response.status_code == 200:
            if "application/json" in content_type:
                data = response.json()
                capabilities = data.get("capabilities", {})
                has_upload = capabilities.get("upload_files", False)

                if has_upload:
                    print_test("Upload capability", "PASS", "User has 'upload_files' capability")
                    return True
                else:
                    print_test("Upload capability", "FAIL", "User lacks 'upload_files' capability")
                    print(f"       Capabilities: {list(capabilities.keys())}")
                    return False
            else:
                print_test("Upload capability", "FAIL", f"Got {content_type}, expected JSON")
                print(f"       Response preview: {response.text[:300]}")
                return False
        else:
            print_test(
                "Upload capability", "WARN", f"Could not verify (status: {response.status_code})"
            )
            return True
    except Exception as e:
        print_test("Upload capability", "FAIL", f"Error: {e}")
        return False


def main() -> None:
    """Run all diagnostic tests."""
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}WordPress REST API Diagnostic Tool{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")

    tests = [
        test_1_base_url,
        test_2_rest_api_enabled,
        test_3_credentials_configured,
        test_4_authentication,
        test_5_media_endpoint,
        test_6_media_upload_capability,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print_test(test.__name__, "ERROR", f"Unexpected error: {e}")
            results.append(False)

    # Summary
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}Summary{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")

    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print(f"\n{GREEN}✓ All tests passed! WordPress REST API is ready for media uploads.{NC}")
        print("\nNext step: Run integrate_webp_wordpress.py")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Some tests failed. Fix issues before uploading media.{NC}")
        print("\nTroubleshooting:")
        print("  1. Verify WordPress Application Password is correct")
        print("  2. Check user has 'upload_files' capability (Administrator or Editor role)")
        print("  3. Ensure REST API is enabled in WordPress settings")
        print("  4. Check for security plugins blocking API access")
        sys.exit(1)


if __name__ == "__main__":
    main()
