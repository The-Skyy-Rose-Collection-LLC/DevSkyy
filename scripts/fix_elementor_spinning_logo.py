#!/usr/bin/env python3
"""
Fix SkyyRose Spinning Logo in Elementor

Updates Elementor data to replace shortcode widgets with inline HTML,
bypassing the need for WordPress plugin/theme shortcode processing.

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


# Inline SVG spinning logo with inline styles (no external CSS needed)
def get_spinning_logo_html(variant: str = "gold") -> str:
    """Generate inline HTML for spinning logo."""
    colors = {
        "gold": "#D4AF37",
        "silver": "#C0C0C0",
        "rose-gold": "#B76E79",
        "deep-rose": "#D4A5A5",
    }
    color = colors.get(variant, colors["gold"])

    # Calculate glow colors
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    glow_light = f"rgba({r},{g},{b},0.3)"
    glow_med = f"rgba({r},{g},{b},0.2)"

    return f'''<style>
@keyframes sr-spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
@keyframes sr-glow {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.85; }} }}
.sr-logo:hover .sr-spinner {{ animation-play-state: paused !important; transform: scale(1.1); }}
</style>
<div class="sr-logo" style="display:flex;align-items:center;justify-content:center;margin:0 auto;">
<a href="/" class="sr-spinner" style="display:block;width:80px;height:80px;animation:sr-spin 8s linear infinite, sr-glow 3s ease-in-out infinite;filter:drop-shadow(0 0 20px {glow_light}) drop-shadow(0 0 40px {glow_med});transition:transform 0.5s;">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<g fill="{color}" opacity="0.95">
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
<path d="M50 75 Q48 85 50 95" stroke="{color}" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</a>
</div>'''


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


def update_elementor_widget(elementor_data: list, widget_id: str, new_html: str) -> bool:
    """Update a shortcode widget to HTML widget with new content."""

    def update_recursive(elements: list) -> bool:
        for elem in elements:
            if elem.get("id") == widget_id:
                # Found the widget - convert from shortcode to html widget
                elem["widgetType"] = "html"
                elem["settings"] = {"html": new_html}
                print(f"  Updated widget {widget_id} to HTML")
                return True

            # Recurse into children
            children = elem.get("elements", [])
            if update_recursive(children):
                return True

        return False

    return update_recursive(elementor_data)


def detect_variant_from_shortcode(shortcode: str) -> str:
    """Extract variant from shortcode string."""
    match = re.search(r'variant=["\']?(\w+(?:-\w+)?)["\']?', shortcode)
    if match:
        return match.group(1)
    return "gold"


def process_page(page_id: int, default_variant: str = "gold") -> bool:
    """Process a single page to update Elementor data."""
    print(f"\n{'=' * 60}")
    print(f"Processing page {page_id}...")

    try:
        # Get page with context=edit to access meta
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}&context=edit"
        page = make_request(url)

        title = page.get("title", {}).get("rendered", "Unknown")
        print(f"Title: {title}")

        # Get Elementor data
        elementor_data_raw = page.get("meta", {}).get("_elementor_data", "")

        if not elementor_data_raw:
            print("No Elementor data found")
            return False

        # Parse JSON if string
        if isinstance(elementor_data_raw, str):
            elementor_data = json.loads(elementor_data_raw)
        else:
            elementor_data = elementor_data_raw

        # Find and replace shortcode widgets
        updated = False

        def find_and_update(elements: list, depth: int = 0) -> bool:
            nonlocal updated
            for elem in elements:
                widget_type = elem.get("widgetType", "")
                settings = elem.get("settings", {})

                # Check for shortcode widget containing spinning logo
                if widget_type == "shortcode":
                    shortcode = settings.get("shortcode", "")
                    if "skyyrose_spinning_logo" in shortcode:
                        variant = detect_variant_from_shortcode(shortcode) or default_variant
                        print(f"  Found shortcode widget: {elem.get('id')} - variant: {variant}")

                        # Convert to HTML widget
                        elem["widgetType"] = "html"
                        elem["settings"] = {"html": get_spinning_logo_html(variant)}
                        updated = True

                # Check HTML widgets for raw shortcode text
                elif widget_type == "html":
                    html = settings.get("html", "")
                    if "[skyyrose_spinning_logo" in html:
                        variant = detect_variant_from_shortcode(html) or default_variant
                        print(
                            f"  Found shortcode in HTML widget: {elem.get('id')} - variant: {variant}"
                        )

                        # Replace shortcode with actual HTML
                        elem["settings"]["html"] = re.sub(
                            r"\[skyyrose_spinning_logo[^\]]*\]",
                            get_spinning_logo_html(variant),
                            html,
                        )
                        updated = True

                # Recurse into children
                children = elem.get("elements", [])
                find_and_update(children, depth + 1)

            return updated

        find_and_update(elementor_data)

        if not updated:
            print("No shortcode widgets found to update")
            return True

        # Update the page with new Elementor data
        print("Saving updated Elementor data...")

        update_data = {"meta": {"_elementor_data": json.dumps(elementor_data)}}

        result = make_request(
            f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}", method="POST", data=update_data
        )

        if result.get("id") == page_id:
            print("✓ Successfully updated Elementor data")
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
    print("SkyyRose Elementor Spinning Logo Fix")
    print("=" * 60)

    # Pages to process with their default variants
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
