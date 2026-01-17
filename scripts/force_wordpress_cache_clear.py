#!/usr/bin/env python3
"""
Force WordPress Cache Clear for Elementor Pages

Triggers multiple cache invalidation methods:
1. Re-saves page with modified timestamp
2. Updates _elementor_edit_mode meta
3. Triggers Elementor CSS regeneration signal
4. Updates post_content to force CDN invalidation

Author: DevSkyy Platform Team
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime

from dotenv import load_dotenv

load_dotenv()

# WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")

# Auth header
credentials = f"{USERNAME}:{PASSWORD}"
AUTH_HEADER = base64.b64encode(credentials.encode()).decode()


def make_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    """Make authenticated request to WordPress REST API."""
    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode())


def force_cache_clear(page_id: int) -> bool:
    """Force cache clear for a single page."""
    print(f"\n{'=' * 60}")
    print(f"Force cache clear for page {page_id}...")

    try:
        # Get current page
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}&context=edit"
        page = make_request(url)

        title = page.get("title", {}).get("rendered", "Unknown")
        print(f"Title: {title}")

        # Current timestamps
        modified = page.get("modified", "")
        print(f"Current modified: {modified}")

        # Generate new timestamp
        now = datetime.now(UTC)
        new_modified = now.strftime("%Y-%m-%dT%H:%M:%S")

        # Get current content and add cache-bust comment
        content = page.get("content", {})
        raw_content = content.get("raw", "") or content.get("rendered", "")

        # Add timestamp comment to force content change
        cache_bust = f"<!-- cache-bust: {int(time.time())} -->"

        # If content already has cache-bust, update it
        import re

        if "<!-- cache-bust:" in raw_content:
            new_content = re.sub(r"<!-- cache-bust: \d+ -->", cache_bust, raw_content)
        else:
            new_content = cache_bust + "\n" + raw_content

        # Update page with multiple signals
        update_data = {
            "content": new_content,
            "date": new_modified,
            "modified": new_modified,
            "status": "publish",  # Ensure published
            "meta": {
                "_elementor_edit_mode": "builder",
                "_elementor_version": "3.32.2",  # Force version update
                "_elementor_css": "",  # Clear CSS cache signal
            },
        }

        print(f"Updating page with cache-bust timestamp: {new_modified}")

        result = make_request(
            f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}", method="POST", data=update_data
        )

        if result.get("id") == page_id:
            new_modified_result = result.get("modified", "")
            print(f"✓ Page updated, new modified: {new_modified_result}")
            return True
        else:
            print("✗ Update may have failed")
            return False

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        error_body = e.read().decode()
        print(error_body[:500])
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    print("WordPress Cache Clear - Force Page Regeneration")
    print("=" * 60)

    # Pages to clear
    pages = [
        8530,  # Home
        152,  # Signature
        153,  # Black Rose
        154,  # Love Hurts
    ]

    results = []
    for page_id in pages:
        success = force_cache_clear(page_id)
        results.append((page_id, success))
        time.sleep(1)  # Small delay between updates

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for page_id, success in results:
        status = "✓ Success" if success else "✗ Failed"
        print(f"Page {page_id}: {status}")

    print("\nNote: CDN cache may take 5-10 minutes to fully clear.")
    print("Visit pages with ?nocache=1 parameter to bypass edge cache.")


if __name__ == "__main__":
    main()
