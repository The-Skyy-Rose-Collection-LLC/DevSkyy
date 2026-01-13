#!/usr/bin/env python3
"""
Batch enhance all verified clothing images.
Saves enhanced, high-quality images ready for WordPress upload.
"""

import asyncio
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from imagery.image_processor import BackgroundRemover, ImageProcessor
from scripts.generate_clothing_3d_huggingface import COLLECTIONS, find_clothing_images

load_dotenv()


async def enhance_all_images():
    """Enhance all verified clothing images."""
    processor = ImageProcessor()
    bg_remover = BackgroundRemover()

    output_dir = Path(__file__).parent.parent / "assets/visual-generated/enhanced_clothing"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for collection in COLLECTIONS:
        items = find_clothing_images(collection)
        print(f"\n{'=' * 50}")
        print(f"Processing {collection.upper()}: {len(items)} items")
        print(f"{'=' * 50}")

        for item in items:
            try:
                image = processor.load_image(item["path"])

                # Enhance for high quality
                enhanced = processor.enhance(
                    image, brightness=1.05, contrast=1.1, saturation=1.15, sharpness=1.2
                )

                # Try background removal
                try:
                    final = await bg_remover.remove_background(enhanced)
                except Exception:
                    final = enhanced

                # Resize to production quality (1024x1024)
                final = processor.resize(final, (1024, 1024))

                # Save as PNG for quality
                safe_name = item["name"].replace("/", "_").replace("\\", "_")
                output_name = f"{item['collection']}_{safe_name}.png"
                output_path = output_dir / output_name
                processor.save_image(final, str(output_path))

                size_kb = output_path.stat().st_size / 1024
                print(f"✓ {item['name'][:40]}: {size_kb:.0f}KB")

                results.append(
                    {
                        "name": item["name"],
                        "collection": item["collection"],
                        "path": str(output_path),
                        "size_kb": size_kb,
                    }
                )

            except Exception as e:
                print(f"✗ {item['name']}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Enhanced {len(results)}/32 images")
    print(f"Output: {output_dir}")

    # Save manifest
    import json

    manifest_path = output_dir / "MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Manifest: {manifest_path}")

    return results


if __name__ == "__main__":
    asyncio.run(enhance_all_images())
