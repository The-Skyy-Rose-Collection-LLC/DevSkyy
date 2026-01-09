#!/usr/bin/env python3
"""Embed HuggingFace Spaces in WordPress /experiences/ pages with ralph-loop retry."""

import os
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

# Get WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

if not WP_USERNAME or not WP_APP_PASSWORD:
    print("❌ WordPress credentials not found in .env")
    sys.exit(1)

print("✓ WordPress credentials loaded from .env")

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Installing requests...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests
    from requests.auth import HTTPBasicAuth


# Page mappings: page_id -> (collection_name, hf_space_url)
# Updated with actual deployed Space URLs
EXPERIENCES_PAGES = {
    152: ("SIGNATURE", "https://dambruh-skyyrose-virtual-tryon.hf.space"),
    153: ("BLACK_ROSE", "https://dambruh-skyyrose-3d-converter.hf.space"),
    154: ("LOVE_HURTS", "https://dambruh-skyyrose-lora-training-monitor.hf.space"),
}


def generate_embed_html(collection_name: str, space_url: str) -> str:
    """Generate HTML with HuggingFace Space iframe embed."""
    return f"""
<!-- SkyyRose {collection_name} Collection Experience -->
<div class="skyyrose-collection-experience" style="margin: 2rem 0;">
    <h2 style="font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 1rem;">
        {collection_name} Collection Experience
    </h2>

    <!-- HuggingFace Space Embed -->
    <div class="hf-space-container" style="position: relative; width: 100%; max-width: 1200px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <iframe
            src="{space_url}"
            frameborder="0"
            width="100%"
            height="800"
            style="display: block;"
            allow="accelerometer; ambient-light-sensor; camera; encrypted-media; geolocation; gyroscope; hid; microphone; midi; payment; usb; vr; xr-spatial-tracking"
            sandbox="allow-forms allow-modals allow-popups allow-presentation allow-same-origin allow-scripts"
        ></iframe>
    </div>

    <p style="margin-top: 1rem; text-align: center; color: #666; font-size: 0.9rem;">
        Powered by AI | <a href="{space_url}" target="_blank" rel="noopener">Open in HuggingFace →</a>
    </p>
</div>

<!-- Original Collection Content Below -->
"""


def update_page_with_retry(
    page_id: int, collection_name: str, space_url: str, max_retries: int = 3
) -> bool:
    """Update WordPress page with HuggingFace Space embed using ralph-loop retry."""

    auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
    endpoint = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}"

    # First, get current page content (ralph-loop)
    print(f"\nFetching current content for page {page_id} ({collection_name})...")
    current_content = None

    for attempt in range(max_retries):
        try:
            response = requests.get(endpoint, auth=auth, timeout=30)
            if response.status_code == 200:
                current_content = response.json().get("content", {}).get("raw", "")
                print(f"  ✓ Retrieved current content ({len(current_content)} characters)")
                break
            elif response.status_code == 404:
                print(f"  ❌ Page {page_id} not found")
                return False
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  ❌ Failed to retrieve page after {max_retries} attempts: {e}")
                return False
            wait_time = 2**attempt
            print(f"  ⚠ Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    if current_content is None:
        print("  ❌ Could not retrieve current content")
        return False

    # Generate embed HTML
    embed_html = generate_embed_html(collection_name, space_url)

    # Prepend embed to existing content (don't overwrite)
    new_content = embed_html + current_content

    # Update page with new content (ralph-loop)
    print("  Updating page with HuggingFace Space embed...")

    for attempt in range(max_retries):
        try:
            update_data = {"content": new_content}

            response = requests.post(
                endpoint,
                json=update_data,
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code in [200, 201]:
                result = response.json()
                print(f"  ✅ Page {page_id} updated successfully")
                print(f"     URL: {result.get('link', 'N/A')}")
                return True
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    print(f"  ⚠ Rate limited. Retry in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}")

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  ❌ Update failed after {max_retries} attempts: {e}")
                return False
            wait_time = 2**attempt
            print(f"  ⚠ Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    return False


def main():
    """Embed HuggingFace Spaces in all /experiences/ pages."""

    print("=== Embedding HuggingFace Spaces in WordPress ===\n")
    print(f"Target site: {WP_URL}")
    print(f"Pages to update: {len(EXPERIENCES_PAGES)}\n")

    success_count = 0

    for page_id, (collection_name, space_url) in EXPERIENCES_PAGES.items():
        if update_page_with_retry(page_id, collection_name, space_url):
            success_count += 1
            # Rate limiting: wait between pages
            if page_id != list(EXPERIENCES_PAGES.keys())[-1]:
                time.sleep(1)

    print(f"\n{'='*60}")
    print(f"✅ Embedded {success_count}/{len(EXPERIENCES_PAGES)} HuggingFace Spaces")
    print(f"{'='*60}")

    if success_count == len(EXPERIENCES_PAGES):
        print("\n📋 Next Steps:")
        print("  1. Visit https://skyyrose.co/experiences/signature/")
        print("  2. Visit https://skyyrose.co/experiences/black-rose/")
        print("  3. Visit https://skyyrose.co/experiences/love-hurts/")
        print("  4. Verify HuggingFace Spaces load correctly")
        return 0
    else:
        print(f"\n⚠ {len(EXPERIENCES_PAGES) - success_count} pages failed to update")
        return 1


if __name__ == "__main__":
    sys.exit(main())
