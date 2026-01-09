#!/usr/bin/env python3
"""
Update WooCommerce Product Galleries via WordPress MCP Tools

Alternative approach to bypass REST API rate limiting by using
MCP tools which may have different rate limit quotas.

Created: 2026-01-08
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load upload results
upload_results_path = project_root / "assets" / "2d-25d-assets" / "wordpress_upload_results.json"

with open(upload_results_path) as f:
    upload_data = json.load(f)

successful_uploads = [r for r in upload_data["upload_results"] if r.get("success")]

print(f"📊 Loaded {len(successful_uploads)} successful uploads")

# Group by product name
products_images = defaultdict(list)

for upload in successful_uploads:
    filename = Path(upload["file"]).stem
    # Remove variation suffix
    for suffix in ["_detail", "_shadow", "_depth", "_parallax"]:
        if filename.endswith(suffix):
            filename = filename[: -len(suffix)]
            break

    # Clean up product name
    product_name = filename.strip("_").replace("_", " ")

    products_images[product_name].append(
        {"id": upload["id"], "url": upload["url"], "variation_type": upload["variation_type"]}
    )

print(f"\n📦 Grouped into {len(products_images)} unique products:")
for name in list(products_images.keys())[:5]:
    print(f"  - {name} ({len(products_images[name])} images)")
print(f"  ... and {len(products_images) - 5} more\n")

print("=" * 60)
print("🔧 NEXT STEPS - Use WordPress MCP Tools")
print("=" * 60)
print(
    """
To complete the gallery update using MCP tools:

1. List WooCommerce products:
   mcp__wordpress__list_products(per_page=100, status="publish")

2. For each product, match by name using fuzzy matching

3. Update product gallery:
   mcp__wordpress__update_product(
       id=PRODUCT_ID,
       images=[
           {"src": "https://skyyrose.co/wp-content/uploads/.../shadow.jpg"},
           {"src": "https://skyyrose.co/wp-content/uploads/.../depth.jpg"},
           {"src": "https://skyyrose.co/wp-content/uploads/.../parallax.png"},
           {"src": "https://skyyrose.co/wp-content/uploads/.../detail.jpg"}
       ]
   )

NOTE: This approach may bypass REST API rate limits since MCP
tools use internal WordPress APIs rather than the REST API.
"""
)

# Save product groupings for manual reference
output_file = project_root / "assets" / "2d-25d-assets" / "product_image_mappings.json"
with open(output_file, "w") as f:
    json.dump(products_images, f, indent=2)

print("\n✅ Product-to-image mappings saved to:")
print(f"   {output_file}")
