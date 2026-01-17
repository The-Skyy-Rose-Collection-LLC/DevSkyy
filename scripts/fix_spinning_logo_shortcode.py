#!/usr/bin/env python3
"""
Fix SkyyRose Spinning Logo Shortcode

Replaces [skyyrose_spinning_logo] shortcodes with actual inline HTML
since the WordPress plugin/theme isn't properly executing shortcodes.

Author: DevSkyy Platform Team
"""

import base64
import json
import os
import re
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

# WordPress credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")

# Auth header
credentials = f"{USERNAME}:{PASSWORD}"
AUTH_HEADER = base64.b64encode(credentials.encode()).decode()

# Spinning logo HTML templates for each variant
SPINNING_LOGO_HTML = {
    "gold": """<a href="/" class="skyyrose-logo skyyrose-logo--gold" aria-label="SkyyRose Home" style="display:flex;align-items:center;justify-content:center;">
<div class="skyyrose-logo__spinner" style="width:60px;height:60px;animation:sr-spin 8s linear infinite;filter:drop-shadow(0 0 15px rgba(212,175,55,0.3)) drop-shadow(0 0 30px rgba(212,175,55,0.2));">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="color:#D4AF37;">
<g fill="currentColor" opacity="0.95">
<circle cx="50" cy="50" r="8"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(0 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(72 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(144 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(216 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(288 50 50)"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(36 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(108 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(180 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(252 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(324 50 50)" opacity="0.7"/>
</g>
<path d="M50 75 Q48 85 50 95" stroke="currentColor" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</div>
</a>""",
    "silver": """<a href="/" class="skyyrose-logo skyyrose-logo--silver" aria-label="SkyyRose Home" style="display:flex;align-items:center;justify-content:center;">
<div class="skyyrose-logo__spinner" style="width:60px;height:60px;animation:sr-spin 8s linear infinite;filter:drop-shadow(0 0 15px rgba(192,192,192,0.3)) drop-shadow(0 0 30px rgba(192,192,192,0.2));">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="color:#C0C0C0;">
<g fill="currentColor" opacity="0.95">
<circle cx="50" cy="50" r="8"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(0 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(72 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(144 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(216 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(288 50 50)"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(36 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(108 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(180 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(252 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(324 50 50)" opacity="0.7"/>
</g>
<path d="M50 75 Q48 85 50 95" stroke="currentColor" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</div>
</a>""",
    "rose-gold": """<a href="/" class="skyyrose-logo skyyrose-logo--rose-gold" aria-label="SkyyRose Home" style="display:flex;align-items:center;justify-content:center;">
<div class="skyyrose-logo__spinner" style="width:60px;height:60px;animation:sr-spin 8s linear infinite;filter:drop-shadow(0 0 15px rgba(183,110,121,0.3)) drop-shadow(0 0 30px rgba(183,110,121,0.2));">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="color:#B76E79;">
<g fill="currentColor" opacity="0.95">
<circle cx="50" cy="50" r="8"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(0 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(72 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(144 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(216 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(288 50 50)"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(36 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(108 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(180 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(252 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(324 50 50)" opacity="0.7"/>
</g>
<path d="M50 75 Q48 85 50 95" stroke="currentColor" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</div>
</a>""",
    "deep-rose": """<a href="/" class="skyyrose-logo skyyrose-logo--deep-rose" aria-label="SkyyRose Home" style="display:flex;align-items:center;justify-content:center;">
<div class="skyyrose-logo__spinner" style="width:60px;height:60px;animation:sr-spin 8s linear infinite;filter:drop-shadow(0 0 15px rgba(212,165,165,0.3)) drop-shadow(0 0 30px rgba(212,165,165,0.2));">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="color:#D4A5A5;">
<g fill="currentColor" opacity="0.95">
<circle cx="50" cy="50" r="8"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(0 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(72 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(144 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(216 50 50)"/>
<ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(288 50 50)"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(36 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(108 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(180 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(252 50 50)" opacity="0.7"/>
<ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(324 50 50)" opacity="0.7"/>
</g>
<path d="M50 75 Q48 85 50 95" stroke="currentColor" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</div>
</a>""",
}

# CSS for spinning animation (inject once per page)
SPINNING_LOGO_CSS = """<style id="skyyrose-spinning-logo-keyframes">
@keyframes sr-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
.skyyrose-logo:hover .skyyrose-logo__spinner {
    animation-play-state: paused !important;
    transform: scale(1.1);
}
</style>"""


def make_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    """Make authenticated request to WordPress REST API."""
    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode())


def replace_shortcode(content: str) -> str:
    """Replace [skyyrose_spinning_logo] shortcode with inline HTML."""
    # Pattern to match the shortcode with optional variant
    pattern = r'\[skyyrose_spinning_logo(?:\s+variant=["\']?(\w+(?:-\w+)?)["\']?)?\]'

    def replacement(match):
        variant = match.group(1) or "gold"
        variant = variant.lower()
        if variant not in SPINNING_LOGO_HTML:
            variant = "gold"
        return SPINNING_LOGO_HTML[variant]

    return re.sub(pattern, replacement, content)


def get_elementor_data(page_id: int) -> list[dict] | None:
    """Get Elementor data for a page."""
    try:
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}"
        page = make_request(url)

        # Try to get _elementor_data from the content
        content = page.get("content", {}).get("raw", "")

        # Check if there's Elementor data in the raw content
        # WordPress.com might not expose _elementor_data directly
        return page
    except Exception as e:
        print(f"Error getting page {page_id}: {e}")
        return None


def update_page_content(page_id: int, new_content: str) -> bool:
    """Update page content via WordPress REST API."""
    try:
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}"
        data = {"content": new_content}
        result = make_request(url, method="POST", data=data)
        return result.get("id") == page_id
    except urllib.error.HTTPError as e:
        print(f"HTTP Error updating page {page_id}: {e.code}")
        print(e.read().decode()[:500])
        return False
    except Exception as e:
        print(f"Error updating page {page_id}: {e}")
        return False


def process_page(page_id: int, variant: str = "gold") -> bool:
    """Process a single page to replace shortcodes."""
    print(f"\n{'=' * 60}")
    print(f"Processing page {page_id}...")

    try:
        # Get current content
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}"
        page = make_request(url)

        title = page.get("title", {}).get("rendered", "Unknown")
        print(f"Title: {title}")

        # Get raw content if available, otherwise rendered
        content = page.get("content", {})
        raw_content = content.get("raw", "") or content.get("rendered", "")

        if not raw_content:
            print("No content found")
            return False

        # Check for shortcode
        if "[skyyrose_spinning_logo" in raw_content:
            print("Found spinning logo shortcode - replacing with inline HTML...")
            new_content = replace_shortcode(raw_content)

            # Also ensure CSS is present (add at beginning if not)
            if "sr-spin" not in new_content and "@keyframes sr-spin" not in new_content:
                new_content = SPINNING_LOGO_CSS + new_content

            # Update page
            if update_page_content(page_id, new_content):
                print("✓ Successfully updated page content")
                return True
            else:
                print("✗ Failed to update page content")
                return False
        else:
            print("No spinning logo shortcode found in content")
            # Check if we should inject the logo anyway
            return True

    except Exception as e:
        print(f"Error processing page {page_id}: {e}")
        return False


def main():
    """Main entry point."""
    print("SkyyRose Spinning Logo Fix")
    print("=" * 60)

    # Pages to process with their variants
    pages = [
        (8530, "gold"),  # Home
        (152, "rose-gold"),  # Signature
        (153, "silver"),  # Black Rose
        (154, "deep-rose"),  # Love Hurts
    ]

    results = []
    for page_id, variant in pages:
        success = process_page(page_id, variant)
        results.append((page_id, success))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for page_id, success in results:
        status = "✓ Success" if success else "✗ Failed"
        print(f"Page {page_id}: {status}")


if __name__ == "__main__":
    main()
