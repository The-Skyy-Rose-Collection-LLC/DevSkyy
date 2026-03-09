#!/usr/bin/env python3
"""
Generate WordPress MCP upload commands for all AI-enhanced images.

Outputs a list of image URLs and titles for batch upload.
"""

import json
from pathlib import Path

from huggingface_hub import list_repo_files

REPO_ID = "damBruh/skyyrose-lora-dataset-v2"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"
MANIFEST_PATH = Path("assets/ai-enhanced-images/AI_ENHANCEMENT_MANIFEST.json")


def extract_collection(filename: str) -> str:
    """Extract collection from filename."""
    if "signature" in filename.lower():
        return "Signature"
    elif "black" in filename.lower():
        return "Black Rose"
    elif "love" in filename.lower():
        return "Love Hurts"
    return "SkyyRose"


def clean_title(filename: str) -> str:
    """Create clean title from filename."""
    # Remove prefix numbers and extension
    name = filename.split("_", 2)[-1] if "_" in filename else filename
    name = name.rsplit(".", 1)[0]  # Remove extension
    name = name.replace("_", " ").replace("-", " ")
    # Clean up extra spaces
    name = " ".join(name.split())
    return f"SkyyRose {name}"


def main():
    print("=" * 70)
    print("WordPress Upload URLs for AI-Enhanced Images")
    print("=" * 70)

    # Get all images from HuggingFace dataset
    files = list(list_repo_files(REPO_ID, repo_type="dataset"))
    image_files = sorted(
        [f for f in files if f.startswith("images/") and f.endswith((".jpg", ".png"))]
    )

    print(f"\nTotal images: {len(image_files)}")
    print("\nGenerating upload data...\n")

    uploads = []
    for img_path in image_files:
        filename = img_path.split("/")[-1]
        url = f"{BASE_URL}/{img_path}"
        title = clean_title(filename)
        collection = extract_collection(filename)
        alt_text = f"{title} - {collection} Collection - Premium Luxury Streetwear by SkyyRose"

        uploads.append(
            {
                "url": url,
                "title": title,
                "alt_text": alt_text,
                "collection": collection,
            }
        )

    # Save upload manifest
    output_path = Path("assets/ai-enhanced-images/WORDPRESS_UPLOAD_MANIFEST.json")
    with open(output_path, "w") as f:
        json.dump(uploads, f, indent=2)

    print(f"✓ Generated {len(uploads)} upload entries")
    print(f"✓ Saved to: {output_path}")

    # Print sample
    print("\nSample entries:")
    for u in uploads[:3]:
        print(f"  - {u['title'][:40]}...")
        print(f"    URL: {u['url'][:60]}...")

    print(f"\n{'=' * 70}")
    print("To upload, run the following for each image:")
    print("  mcp__wordpress__create_media(")
    print("    title='...',")
    print("    source_url='...',")
    print("    alt_text='...'")
    print("  )")


if __name__ == "__main__":
    main()
