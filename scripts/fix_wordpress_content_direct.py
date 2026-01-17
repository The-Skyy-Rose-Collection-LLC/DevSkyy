#!/usr/bin/env python3
"""
Fix WordPress Content - Direct post_content Update

Directly replaces shortcode text in rendered post_content with inline SVG.
This bypasses Elementor's JSON → HTML rendering and forces the change.

Author: DevSkyy Platform Team
"""

import base64
import html
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

# Inline SVG logo HTML for each variant
SPINNING_LOGO_HTML = {
    "gold": """<style>
@keyframes sr-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes sr-glow { 0%,100% { opacity:1; } 50% { opacity:0.85; } }
.sr-logo:hover .sr-spinner { animation-play-state: paused !important; transform: scale(1.1); }
</style>
<div class="sr-logo" style="display:flex;align-items:center;justify-content:center;margin:0 auto;">
<a href="/" class="sr-spinner" style="display:block;width:80px;height:80px;animation:sr-spin 8s linear infinite, sr-glow 3s ease-in-out infinite;filter:drop-shadow(0 0 20px rgba(212,175,55,0.3)) drop-shadow(0 0 40px rgba(212,175,55,0.2));transition:transform 0.5s;">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<g fill="#D4AF37" opacity="0.95">
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
<path d="M50 75 Q48 85 50 95" stroke="#D4AF37" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</a>
</div>""",
    "silver": """<style>
@keyframes sr-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes sr-glow { 0%,100% { opacity:1; } 50% { opacity:0.85; } }
.sr-logo:hover .sr-spinner { animation-play-state: paused !important; transform: scale(1.1); }
</style>
<div class="sr-logo" style="display:flex;align-items:center;justify-content:center;margin:0 auto;">
<a href="/" class="sr-spinner" style="display:block;width:80px;height:80px;animation:sr-spin 8s linear infinite, sr-glow 3s ease-in-out infinite;filter:drop-shadow(0 0 20px rgba(192,192,192,0.3)) drop-shadow(0 0 40px rgba(192,192,192,0.2));transition:transform 0.5s;">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<g fill="#C0C0C0" opacity="0.95">
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
<path d="M50 75 Q48 85 50 95" stroke="#C0C0C0" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</a>
</div>""",
    "rose-gold": """<style>
@keyframes sr-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes sr-glow { 0%,100% { opacity:1; } 50% { opacity:0.85; } }
.sr-logo:hover .sr-spinner { animation-play-state: paused !important; transform: scale(1.1); }
</style>
<div class="sr-logo" style="display:flex;align-items:center;justify-content:center;margin:0 auto;">
<a href="/" class="sr-spinner" style="display:block;width:80px;height:80px;animation:sr-spin 8s linear infinite, sr-glow 3s ease-in-out infinite;filter:drop-shadow(0 0 20px rgba(183,110,121,0.3)) drop-shadow(0 0 40px rgba(183,110,121,0.2));transition:transform 0.5s;">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<g fill="#B76E79" opacity="0.95">
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
<path d="M50 75 Q48 85 50 95" stroke="#B76E79" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</a>
</div>""",
    "deep-rose": """<style>
@keyframes sr-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes sr-glow { 0%,100% { opacity:1; } 50% { opacity:0.85; } }
.sr-logo:hover .sr-spinner { animation-play-state: paused !important; transform: scale(1.1); }
</style>
<div class="sr-logo" style="display:flex;align-items:center;justify-content:center;margin:0 auto;">
<a href="/" class="sr-spinner" style="display:block;width:80px;height:80px;animation:sr-spin 8s linear infinite, sr-glow 3s ease-in-out infinite;filter:drop-shadow(0 0 20px rgba(212,165,165,0.3)) drop-shadow(0 0 40px rgba(212,165,165,0.2));transition:transform 0.5s;">
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<g fill="#D4A5A5" opacity="0.95">
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
<path d="M50 75 Q48 85 50 95" stroke="#D4A5A5" stroke-width="2" fill="none" opacity="0.5"/>
</svg>
</a>
</div>""",
}


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


def fix_page_content(page_id: int, variant: str = "gold") -> bool:
    """Fix post_content by replacing shortcode with HTML."""
    print(f"\n{'=' * 60}")
    print(f"Processing page {page_id} (variant: {variant})...")

    try:
        # Get current content
        url = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}&context=edit"
        page = make_request(url)

        title = page.get("title", {}).get("rendered", "Unknown")
        print(f"Title: {title}")

        content = page.get("content", {})
        raw_content = content.get("raw", "")

        if not raw_content:
            print("No content found")
            return False

        # Decode HTML entities
        decoded_content = html.unescape(raw_content)

        # Pattern to match the shortcode in any format
        patterns = [
            # Raw shortcode in elementor-shortcode div
            r'(<div class="elementor-shortcode">)\[skyyrose_spinning_logo[^\]]*\](</div>)',
            # Raw shortcode anywhere
            r"\[skyyrose_spinning_logo[^\]]*\]",
        ]

        new_content = decoded_content
        replaced = False

        for pattern in patterns:
            if re.search(pattern, new_content):
                if "(<div" in pattern:
                    # Keep the wrapper div
                    new_content = re.sub(
                        pattern, rf"\1{SPINNING_LOGO_HTML[variant]}\2", new_content
                    )
                else:
                    new_content = re.sub(pattern, SPINNING_LOGO_HTML[variant], new_content)
                replaced = True
                print(f"  Replaced shortcode using pattern: {pattern[:50]}...")
                break

        if not replaced:
            print("  No shortcode found in post_content")
            # Check if it's already fixed
            if "sr-spin" in decoded_content and "sr-logo" in decoded_content:
                print("  Content already appears to have spinning logo HTML")
                return True
            return False

        # Also update Elementor widget type in the content HTML
        # Change widget-shortcode to widget-html
        new_content = new_content.replace("elementor-widget-shortcode", "elementor-widget-html")
        new_content = new_content.replace(
            'data-widget_type="shortcode.default"', 'data-widget_type="html.default"'
        )

        # Update the page
        print("  Updating page content...")

        update_data = {
            "content": new_content,
            "status": "publish",
        }

        result = make_request(
            f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}", method="POST", data=update_data
        )

        if result.get("id") == page_id:
            print("  ✓ Successfully updated page content")
            return True
        else:
            print("  ✗ Update may have failed")
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
    print("WordPress Content Direct Fix")
    print("=" * 60)

    # Pages with their variants
    pages = [
        (8530, "gold"),  # Home
        (152, "rose-gold"),  # Signature
        (153, "silver"),  # Black Rose
        (154, "deep-rose"),  # Love Hurts
    ]

    results = []
    for page_id, variant in pages:
        success = fix_page_content(page_id, variant)
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
