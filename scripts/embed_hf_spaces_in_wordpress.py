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
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# Get WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

if not WP_USERNAME or not WP_APP_PASSWORD:
    print("❌ WordPress credentials not found in .env")
    sys.exit(1)

assert WP_USERNAME is not None and WP_APP_PASSWORD is not None
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


# All HuggingFace Spaces (available on all collection pages)
ALL_SPACES = [
    {
        "name": "Virtual Try-On",
        "description": "Try on SkyyRose merchandise using AI-powered virtual fitting",
        "url": "https://dambruh-skyyrose-virtual-tryon.hf.space",
        "icon": "👗",
    },
    {
        "name": "3D Product Viewer",
        "description": "Explore products in immersive 3D with real-time visualization",
        "url": "https://dambruh-skyyrose-3d-converter.hf.space",
        "icon": "🔮",
    },
    {
        "name": "Brand Style Explorer",
        "description": "Discover how SkyyRose's AI learns and evolves our signature style",
        "url": "https://dambruh-skyyrose-lora-training-monitor.hf.space",
        "icon": "🎨",
    },
]

# Page mappings: page_id -> collection_name
EXPERIENCES_PAGES = {
    152: "SIGNATURE",
    153: "BLACK_ROSE",
    154: "LOVE_HURTS",
}


def generate_all_spaces_html(collection_name: str) -> str:
    """Generate HTML with all 3 HuggingFace Spaces in a tabbed interface."""
    # Generate tab buttons
    tabs_html = '<div class="hf-tabs" style="display: flex; gap: 1rem; margin-bottom: 2rem; border-bottom: 2px solid #ddd;">'
    for idx, space in enumerate(ALL_SPACES):
        active_class = "active" if idx == 0 else ""
        tabs_html += f"""
        <button class="hf-tab-btn {active_class}"
                data-tab="space-{idx}"
                style="padding: 1rem 2rem; background: {"#B76E79" if idx == 0 else "transparent"};
                       color: {"white" if idx == 0 else "#333"}; border: none; cursor: pointer;
                       font-size: 1rem; border-radius: 8px 8px 0 0; transition: all 0.3s;">
            {space["icon"]} {space["name"]}
        </button>
        """
    tabs_html += "</div>"

    # Generate tab content panels
    panels_html = ""
    for idx, space in enumerate(ALL_SPACES):
        display_style = "block" if idx == 0 else "none"
        panels_html += f"""
<div class="hf-tab-panel" id="space-{idx}" style="display: {display_style};">
    <div class="skyyrose-space-experience" style="margin: 2rem 0;">
        <h3 style="font-family: 'Playfair Display', serif; font-size: 1.8rem; margin-bottom: 0.5rem;">
            {space["icon"]} {space["name"]}
        </h3>
        <p style="color: #666; margin-bottom: 1.5rem; font-size: 1.1rem;">
            {space["description"]}
        </p>

        <div class="hf-space-container" style="position: relative; width: 100%; max-width: 1200px;
                                                margin: 0 auto; border: 2px solid #B76E79; border-radius: 12px;
                                                overflow: hidden; box-shadow: 0 8px 16px rgba(183,110,121,0.2);">
            <iframe
                src="{space["url"]}"
                frameborder="0"
                width="100%"
                height="800"
                style="display: block;"
                allow="accelerometer; ambient-light-sensor; camera; encrypted-media; geolocation; gyroscope; hid; microphone; midi; payment; usb; vr; xr-spatial-tracking"
                sandbox="allow-forms allow-modals allow-popups allow-presentation allow-same-origin allow-scripts"
            ></iframe>
        </div>

        <p style="margin-top: 1rem; text-align: center; color: #666; font-size: 0.9rem;">
            Powered by AI | <a href="{space["url"]}" target="_blank" rel="noopener" style="color: #B76E79; text-decoration: none;">Open in HuggingFace →</a>
        </p>
    </div>
</div>
        """

    # JavaScript for tab switching
    script = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.hf-tab-btn');
    const tabPanels = document.querySelectorAll('.hf-tab-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Update button styles
            tabButtons.forEach(btn => {
                btn.style.background = 'transparent';
                btn.style.color = '#333';
            });
            this.style.background = '#B76E79';
            this.style.color = 'white';

            // Update panel visibility
            tabPanels.forEach(panel => {
                panel.style.display = 'none';
            });
            document.getElementById(targetTab).style.display = 'block';
        });
    });
});
</script>
    """

    return f"""
<!-- SkyyRose {collection_name} Collection - AI Experiences -->
<div class="skyyrose-experiences-hub" style="margin: 3rem 0; padding: 2rem; background: linear-gradient(135deg, #f5f5f5 0%, #fff 100%); border-radius: 16px;">
    <h2 style="font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 0.5rem; text-align: center;">
        Explore {collection_name} with AI
    </h2>
    <p style="text-align: center; color: #666; margin-bottom: 2rem; font-size: 1.1rem;">
        Experience SkyyRose through cutting-edge AI technology
    </p>

    {tabs_html}
    {panels_html}
    {script}
</div>

<!-- Original Collection Content Below -->
"""


def update_page_with_retry(page_id: int, collection_name: str, max_retries: int = 3) -> bool:
    """Update WordPress page with HuggingFace Space embed using ralph-loop retry."""
    auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)  # type: ignore[arg-type]
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
    embed_html = generate_all_spaces_html(collection_name)

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


def main() -> int:
    """Embed HuggingFace Spaces in all /experiences/ pages."""
    print("=== Embedding HuggingFace Spaces in WordPress ===\n")
    print(f"Target site: {WP_URL}")
    print(f"Pages to update: {len(EXPERIENCES_PAGES)}\n")

    success_count = 0

    for page_id, collection_name in EXPERIENCES_PAGES.items():
        if update_page_with_retry(page_id, collection_name):
            success_count += 1
            # Rate limiting: wait between pages
            if page_id != list(EXPERIENCES_PAGES.keys())[-1]:
                time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"✅ Embedded {success_count}/{len(EXPERIENCES_PAGES)} HuggingFace Spaces")
    print(f"{'=' * 60}")

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
