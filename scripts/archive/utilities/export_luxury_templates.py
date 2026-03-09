#!/usr/bin/env python3
"""
Export Luxury Page Templates to Elementor-Compatible JSON.

Generates Elementor template JSON files from Python page builders for:
- Luxury homepage (hero + collections grid)
- Luxury product page (2-column layout)

Usage:
    python scripts/export_luxury_templates.py

Output:
    wordpress/templates/luxury/home-luxury.json
    wordpress/templates/luxury/product-luxury.json
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import page builders directly to avoid pulling in unnecessary dependencies
try:
    from wordpress.page_builders.luxury_home_builder import LuxuryHomePageBuilder
    from wordpress.page_builders.product_builder import ProductPageBuilder
except ModuleNotFoundError:
    # If dependencies are missing, provide helpful error message
    print("ERROR: Missing dependencies. Please install required packages:")
    print("  pip install -e .")
    print("  OR run in virtual environment with dependencies installed")
    sys.exit(1)


def export_templates() -> None:
    """Generate and export all luxury templates to JSON."""
    # Create output directory
    output_dir = Path("wordpress/templates/luxury")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Exporting luxury Elementor templates...")
    print(f"Output directory: {output_dir.absolute()}\n")

    # =========================================================================
    # Homepage Template
    # =========================================================================
    print("1. Generating luxury homepage template...")
    home_builder = LuxuryHomePageBuilder()
    home_template = home_builder.generate()

    home_path = output_dir / "home-luxury.json"
    home_path.write_text(json.dumps(home_template, indent=2))
    print(f"   ✓ Exported: {home_path}")
    print("   - Hero section: full-bleed video background")
    print("   - Collections grid: 3-column with hover effects")
    print("   - Spacing: 48px gaps, 120px section padding\n")

    # =========================================================================
    # Product Page Template
    # =========================================================================
    print("2. Generating luxury product page template...")

    # Sample product data for template generation
    sample_product = {
        "id": 1,
        "name": "Sample Product",
        "price": "$299",
        "description": "Luxury product description",
    }

    product_builder = ProductPageBuilder()
    # Using the new luxury_product_hero method
    product_template = {
        "content": [
            product_builder.build_luxury_product_hero(sample_product),
        ],
        "page_settings": {
            "post_title": "Product Template - Luxury",
            "template": "elementor_header_footer",
        },
    }

    product_path = output_dir / "product-luxury.json"
    product_path.write_text(json.dumps(product_template, indent=2))
    print(f"   ✓ Exported: {product_path}")
    print("   - Layout: 60% gallery left, 40% details right")
    print("   - Gallery: 1200px images with zoom/lightbox/slider")
    print("   - Typography: Playfair Display (titles), Inter (body)")
    print("   - CTA: 'Claim Your Rose' branded button\n")

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("✓ All luxury templates exported successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Import templates via WordPress Admin:")
    print("   - Navigate to: Elementor > Templates > Saved Templates")
    print("   - Click: Import Templates")
    print(f"   - Upload: {home_path.name}")
    print(f"   - Upload: {product_path.name}")
    print("\n2. Assign templates:")
    print("   - Home: Pages > Home > Edit with Elementor > Apply Template")
    print("   - Product: WooCommerce > Settings > Products > Product Template")
    print("\n3. Run Ralph Loop validation:")
    print("   - black scripts/export_luxury_templates.py --check")
    print("   - isort scripts/export_luxury_templates.py --check-only")
    print("   - ruff check scripts/export_luxury_templates.py")
    print("   - mypy scripts/export_luxury_templates.py --strict")


if __name__ == "__main__":
    try:
        export_templates()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error exporting templates: {e}", file=sys.stderr)
        sys.exit(1)
