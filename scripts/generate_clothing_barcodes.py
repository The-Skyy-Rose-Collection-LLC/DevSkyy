#!/usr/bin/env python3
"""
Generate UPC-A Barcode Images for SkyyRose Clothing

Reads barcode numbers from skyyrose_clothing_barcodes.txt and generates
high-resolution PNG barcode images suitable for printing on clothing labels.

Each barcode is 12 digits starting with 782 (UPC-A format).

Created: 2026-01-08
"""

from pathlib import Path

import barcode
from barcode.writer import ImageWriter

# Setup paths
project_root = Path(__file__).parent.parent
barcodes_file = project_root / "skyyrose_clothing_barcodes.txt"
output_dir = project_root / "assets" / "clothing_barcodes"

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)


def generate_barcode_image(barcode_number: str, output_path: Path):
    """
    Generate a UPC-A barcode image.

    Args:
        barcode_number: 12-digit UPC barcode (e.g., "782003255051")
        output_path: Path to save PNG image (without extension)
    """
    # Create UPC-A barcode
    upc = barcode.get("upca", barcode_number, writer=ImageWriter())

    # Configure image writer for high-quality printing
    options = {
        "module_width": 0.4,  # Width of narrowest bar (mm)
        "module_height": 15.0,  # Height of bars (mm)
        "font_size": 10,  # Font size for text
        "text_distance": 3,  # Distance between barcode and text
        "quiet_zone": 6.5,  # White space around barcode (mm)
        "dpi": 300,  # High resolution for printing
        "write_text": True,  # Include barcode number as text
    }

    # Generate and save barcode image
    upc.save(str(output_path), options=options)


def main():
    """Generate all barcode images."""

    print("🏷️ SkyyRose Clothing Barcode Generator")
    print(f"{'='*60}\n")

    # Read barcode numbers
    if not barcodes_file.exists():
        print(f"❌ Barcode file not found: {barcodes_file}")
        return

    with open(barcodes_file) as f:
        barcode_numbers = [line.strip() for line in f if line.strip()]

    print(f"📊 Found {len(barcode_numbers)} barcodes to generate")
    print(f"📁 Output directory: {output_dir}\n")

    # Generate barcodes
    generated = 0
    errors = 0

    for i, barcode_number in enumerate(barcode_numbers, 1):
        try:
            output_path = output_dir / barcode_number
            generate_barcode_image(barcode_number, output_path)
            print(f"  [{i}/{len(barcode_numbers)}] ✓ Generated: {barcode_number}.png")
            generated += 1
        except Exception as e:
            print(f"  [{i}/{len(barcode_numbers)}] ✗ Failed {barcode_number}: {e}")
            errors += 1

    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Generated: {generated}")
    print(f"Errors: {errors}")
    print(f"Total: {len(barcode_numbers)}")
    print(f"\n✅ Barcode images saved to: {output_dir}")
    print("\nℹ️  Specifications:")
    print("   - Format: UPC-A (12 digits)")
    print("   - Resolution: 300 DPI (print-ready)")
    print("   - Size: ~40mm x 25mm")
    print("   - File format: PNG with transparency")


if __name__ == "__main__":
    main()
