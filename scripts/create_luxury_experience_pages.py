#!/usr/bin/env python3
"""Create Luxury Experience Pages for SkyyRose Collections.

Builds premium, branded experience pages for:
- SIGNATURE Collection: Premium sophistication
- BLACK ROSE Collection: Gothic luxury
- LOVE HURTS Collection: Edgy passion
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "skyyroseco")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")

if not WP_USERNAME or not WP_APP_PASSWORD:
    print("❌ WordPress credentials not found in .env")
    sys.exit(1)

assert WP_USERNAME is not None and WP_APP_PASSWORD is not None

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Installing requests...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests
    from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)


def generate_signature_content() -> str:
    """Generate SIGNATURE Collection page content."""
    return """
<!-- wp:cover {"url":"","dimRatio":50,"overlayColor":"black","minHeight":400,"align":"full"} -->
<div class="wp-block-cover alignfull has-background-dim" style="min-height:400px">
    <div class="wp-block-cover__inner-container">
        <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"4rem"}}} -->
        <h1 class="has-text-align-center" style="font-size:4rem">SIGNATURE Collection</h1>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"1.5rem"}}} -->
        <p class="has-text-align-center" style="font-size:1.5rem">Premium Sophistication Meets Timeless Elegance</p>
        <!-- /wp:paragraph -->
    </div>
</div>
<!-- /wp:cover -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:columns -->
<div class="wp-block-columns">
    <!-- wp:column -->
    <div class="wp-block-column">
        <!-- wp:heading {"level":2} -->
        <h2>The Essence of SIGNATURE</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>The SIGNATURE Collection embodies refined luxury for those who appreciate understated elegance. Each piece is crafted with meticulous attention to detail, featuring premium materials and sophisticated design that transcends fleeting trends.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p><strong>Key Features:</strong></p>
        <!-- /wp:paragraph -->
        
        <!-- wp:list -->
        <ul>
            <li>Premium heavyweight fabrics (300+ GSM)</li>
            <li>Subtle, sophisticated colorways</li>
            <li>Timeless silhouettes</li>
            <li>Minimalist rose emblem</li>
            <li>Versatile day-to-night styling</li>
        </ul>
        <!-- /wp:list -->
    </div>
    <!-- /wp:column -->
    
    <!-- wp:column -->
    <div class="wp-block-column">
        <!-- wp:heading {"level":2} -->
        <h2>Design Philosophy</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>SIGNATURE represents the perfect balance between luxury streetwear and classic sophistication. Inspired by architectural minimalism and high fashion, each piece is designed to be a wardrobe staple that elevates any outfit.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p>The collection features muted earth tones, soft grays, and crisp whites, accented with the iconic SkyyRose logo in subtle placements that speak volumes without shouting.</p>
        <!-- /wp:paragraph -->
    </div>
    <!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:heading {"textAlign":"center","level":2} -->
<h2 class="has-text-align-center">Explore with AI Technology</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center">Experience SIGNATURE Collection through our cutting-edge AI tools below</p>
<!-- /wp:paragraph -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->
"""


def generate_black_rose_content() -> str:
    """Generate BLACK ROSE Collection page content."""
    return """
<!-- wp:cover {"url":"","dimRatio":70,"overlayColor":"black","minHeight":400,"align":"full"} -->
<div class="wp-block-cover alignfull has-background-dim-70" style="min-height:400px">
    <div class="wp-block-cover__inner-container">
        <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"4rem"},"color":{"text":"#B76E79"}}} -->
        <h1 class="has-text-align-center" style="font-size:4rem;color:#B76E79">BLACK ROSE Collection</h1>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"1.5rem"}}} -->
        <p class="has-text-align-center" style="font-size:1.5rem">Gothic Luxury. Dramatic Aesthetic. Rebellious Elegance.</p>
        <!-- /wp:paragraph -->
    </div>
</div>
<!-- /wp:cover -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:columns {"backgroundColor":"black","textColor":"white"} -->
<div class="wp-block-columns has-white-color has-black-background-color has-text-color has-background">
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","right":"2rem","bottom":"2rem","left":"2rem"}}}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-right:2rem;padding-bottom:2rem;padding-left:2rem">
        <!-- wp:heading {"level":2,"textColor":"white"} -->
        <h2 class="has-white-color has-text-color">Darkness Meets Beauty</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>BLACK ROSE is where gothic romance meets contemporary luxury. This collection celebrates the beauty found in darkness, featuring deep blacks, midnight burgundies, and blood reds that command attention.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p><strong>Collection Highlights:</strong></p>
        <!-- /wp:paragraph -->
        
        <!-- wp:list -->
        <ul>
            <li>Dramatic silhouettes & oversized fits</li>
            <li>Gothic rose motifs & thorn details</li>
            <li>Layered textures & mixed materials</li>
            <li>Dark romantic color palette</li>
            <li>Statement pieces for bold personalities</li>
        </ul>
        <!-- /wp:list -->
    </div>
    <!-- /wp:column -->
    
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","right":"2rem","bottom":"2rem","left":"2rem"}}}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-right:2rem;padding-bottom:2rem;padding-left:2rem">
        <!-- wp:heading {"level":2,"textColor":"white"} -->
        <h2 class="has-white-color has-text-color">The Dark Romance</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>Inspired by Victorian gothic architecture and modern dark aesthetics, BLACK ROSE rejects conventional beauty standards. Each piece tells a story of defiance, individuality, and artistic expression.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p>This isn't fashion for the faint of heart—it's for those who embrace their shadows and wear their darkness as armor. From distressed hoodies to statement coats, every piece makes an unforgettable impression.</p>
        <!-- /wp:paragraph -->
    </div>
    <!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:heading {"textAlign":"center","level":2} -->
<h2 class="has-text-align-center">Experience BLACK ROSE with AI</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center">Dive into the dark beauty of BLACK ROSE through our interactive AI experiences below</p>
<!-- /wp:paragraph -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->
"""


def generate_love_hurts_content() -> str:
    """Generate LOVE HURTS Collection page content."""
    return """
<!-- wp:cover {"url":"","dimRatio":60,"overlayColor":"black","minHeight":400,"align":"full"} -->
<div class="wp-block-cover alignfull has-background-dim-60" style="min-height:400px">
    <div class="wp-block-cover__inner-container">
        <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"4rem"},"color":{"text":"#FF0066"}}} -->
        <h1 class="has-text-align-center" style="font-size:4rem;color:#FF0066">LOVE HURTS Collection</h1>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"1.5rem"}}} -->
        <p class="has-text-align-center" style="font-size:1.5rem">Edgy Passion. Emotional Depth. Vulnerable Strength.</p>
        <!-- /wp:paragraph -->
    </div>
</div>
<!-- /wp:cover -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:columns -->
<div class="wp-block-columns">
    <!-- wp:column -->
    <div class="wp-block-column">
        <!-- wp:heading {"level":2} -->
        <h2>Raw Emotion, Refined Style</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>LOVE HURTS captures the beautiful contradiction of love's duality—the ecstasy and agony, the tenderness and pain. This collection channels raw emotional energy into wearable art that resonates with those who feel deeply.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p><strong>Signature Elements:</strong></p>
        <!-- /wp:paragraph -->
        
        <!-- wp:list -->
        <ul>
            <li>Bold graphic designs & provocative messaging</li>
            <li>Broken heart motifs & thorned roses</li>
            <li>Vibrant reds, hot pinks, electric accents</li>
            <li>Distressed & deconstructed details</li>
            <li>Emotional storytelling through design</li>
        </ul>
        <!-- /wp:list -->
    </div>
    <!-- /wp:column -->
    
    <!-- wp:column -->
    <div class="wp-block-column">
        <!-- wp:heading {"level":2} -->
        <h2>Wear Your Heart</h2>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p>LOVE HURTS is for those unafraid to express vulnerability as strength. Inspired by street art, punk culture, and modern romance, this collection transforms heartbreak into haute couture.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p>Each piece features intentional imperfections—rips, fading, asymmetry—that mirror the beautiful mess of human emotion. This isn't polished perfection; it's authentic, rebellious luxury for the passionate soul.</p>
        <!-- /wp:paragraph -->
        
        <!-- wp:quote -->
        <blockquote class="wp-block-quote">
            <p>"The deepest wounds make the most beautiful scars."</p>
            <cite>— SkyyRose Design Philosophy</cite>
        </blockquote>
        <!-- /wp:quote -->
    </div>
    <!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- wp:spacer {"height":"60px"} -->
<div style="height:60px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->

<!-- wp:heading {"textAlign":"center","level":2} -->
<h2 class="has-text-align-center">Feel LOVE HURTS Through AI</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center">Experience the emotional intensity of LOVE HURTS through our AI-powered tools below</p>
<!-- /wp:paragraph -->

<!-- wp:spacer {"height":"40px"} -->
<div style="height:40px" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->
"""


COLLECTION_PAGES = {
    152: {
        "title": "SIGNATURE Collection Experience",
        "slug": "experiences/signature",
        "content_generator": generate_signature_content,
    },
    153: {
        "title": "BLACK ROSE Collection Experience",
        "slug": "experiences/black-rose",
        "content_generator": generate_black_rose_content,
    },
    154: {
        "title": "LOVE HURTS Collection Experience",
        "slug": "experiences/love-hurts",
        "content_generator": generate_love_hurts_content,
    },
}


def update_experience_page(page_id: int, page_config: dict) -> bool:
    """Update experience page with luxury content."""
    print(f"\n📝 Updating Page {page_id}: {page_config['title']}")

    endpoint = f"{WP_URL}/index.php?rest_route=/wp/v2/pages/{page_id}"

    # Get current content to preserve HuggingFace Spaces
    try:
        response = requests.get(endpoint, auth=auth, timeout=30)
        if response.status_code == 200:
            current_content = response.json().get("content", {}).get("raw", "")
            print(f"  ✓ Retrieved current content ({len(current_content)} characters)")

            # Check if HF Spaces are already embedded
            if "hf-tabs" in current_content:
                print("  ℹ HuggingFace Spaces already embedded, preserving them")
                # Extract HF Spaces section
                hf_start = current_content.find("<!-- SkyyRose")
                if hf_start > 0:
                    hf_section = current_content[hf_start:]
                    # Prepend new content before HF Spaces
                    new_content = page_config["content_generator"]() + "\n\n" + hf_section
                else:
                    # Append HF Spaces after new content
                    new_content = page_config["content_generator"]() + "\n\n" + current_content
            else:
                # No HF Spaces yet, just use new content
                new_content = page_config["content_generator"]()

        else:
            print(f"  ⚠ Could not retrieve page, using new content only")
            new_content = page_config["content_generator"]()

    except Exception as e:
        print(f"  ⚠ Error retrieving page: {e}")
        new_content = page_config["content_generator"]()

    # Update page
    update_data = {
        "title": page_config["title"],
        "content": new_content,
        "status": "publish",
    }

    try:
        response = requests.post(
            endpoint,
            json=update_data,
            auth=auth,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"  ✅ Page updated successfully")
            print(f"     URL: {result.get('link', 'N/A')}")
            return True
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"  ❌ Update failed: {e}")
        return False


def main() -> int:
    """Create luxury experience pages for all collections."""
    print("=== Creating Luxury Experience Pages ===\n")
    print(f"Target: {WP_URL}\n")

    success_count = 0

    for page_id, page_config in COLLECTION_PAGES.items():
        if update_experience_page(page_id, page_config):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Updated {success_count}/{len(COLLECTION_PAGES)} Experience Pages")
    print(f"{'='*60}")

    if success_count == len(COLLECTION_PAGES):
        print("\n🌟 Experience Pages Live:")
        print("  • https://skyyrose.co/experiences/signature/")
        print("  • https://skyyrose.co/experiences/black-rose/")
        print("  • https://skyyrose.co/experiences/love-hurts/")
        return 0
    else:
        print(f"\n⚠ {len(COLLECTION_PAGES) - success_count} pages failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
