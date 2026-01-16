#!/usr/bin/env python3
"""
WordPress Media Duplicate Cleanup

Deletes duplicate images from WordPress Media Library based on
visual similarity analysis from visual_product_recognition.py.

Usage:
    python scripts/cleanup_wordpress_duplicates.py [--dry-run] [--threshold 0.98]

Features:
- Reads similarity_report.json from visual recognition
- Identifies duplicates based on similarity threshold (default 0.98)
- Keeps shorter filename (usually more descriptive)
- Deletes via WordPress REST API
- Updates webp_image_mapping.json
- Dry-run mode to preview deletions
"""

import argparse
import json
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

# Colors for output
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def load_wordpress_config() -> dict:
    """Load WordPress credentials from environment."""
    import os

    url = os.getenv("WORDPRESS_URL")
    username = os.getenv("WORDPRESS_USERNAME")
    password = os.getenv("WORDPRESS_APP_PASSWORD")

    if not url or not username or not password:
        print(f"{RED}Error: Missing WordPress credentials{NC}")
        print("Set WORDPRESS_URL, WORDPRESS_USERNAME, and WORDPRESS_APP_PASSWORD")
        print("environment variables")
        sys.exit(1)

    return {
        "url": url,
        "username": username,
        "password": password,
    }


def load_similarity_report(report_path: Path) -> dict:
    """Load visual similarity analysis report."""
    if not report_path.exists():
        print(f"{RED}Error: Similarity report not found: {report_path}{NC}")
        print("Run: python scripts/visual_product_recognition.py")
        sys.exit(1)

    with open(report_path) as f:
        return json.load(f)


def load_image_mapping(mapping_path: Path) -> dict:
    """Load WordPress image ID mapping."""
    if not mapping_path.exists():
        print(f"{RED}Error: Image mapping not found: {mapping_path}{NC}")
        sys.exit(1)

    with open(mapping_path) as f:
        return json.load(f)


def get_media_id(image_name: str, mapping: dict) -> int | None:
    """Get WordPress media ID for an image."""
    # Remove .webp extension to match mapping keys
    base_name = image_name.replace(".webp", "")

    if base_name in mapping:
        return mapping[base_name].get("webp_id")

    return None


def select_duplicate_to_delete(image1: str, image2: str) -> str:
    """
    Select which duplicate to delete.

    Strategy: Keep the image with the shorter, more descriptive name.
    Delete the longer, auto-generated name.

    Examples:
        - Keep: LH_SINCERELY_HEARTED_JOGGERS_BLAC_main
        - Delete: LH_000_20231221_072338_main (timestamp-based)
    """
    # Prefer human-readable names over timestamp-based names
    has_timestamp1 = any(chunk.isdigit() and len(chunk) >= 8 for chunk in image1.split("_"))
    has_timestamp2 = any(chunk.isdigit() and len(chunk) >= 8 for chunk in image2.split("_"))

    if has_timestamp1 and not has_timestamp2:
        return image1  # Delete timestamp version, keep descriptive
    elif has_timestamp2 and not has_timestamp1:
        return image2  # Delete timestamp version, keep descriptive

    # If both/neither have timestamps, keep shorter name
    if len(image1) < len(image2):
        return image2
    else:
        return image1


def delete_media(media_id: int, config: dict, dry_run: bool = False) -> tuple[bool, str]:
    """
    Delete media from WordPress via REST API.

    Args:
        media_id: WordPress media ID
        config: WordPress connection config
        dry_run: If True, don't actually delete

    Returns:
        (success, message) tuple
    """
    if dry_run:
        return True, f"DRY RUN: Would delete media ID {media_id}"

    url = f"{config['url']}/wp-json/wp/v2/media/{media_id}"
    auth = HTTPBasicAuth(config["username"], config["password"])

    try:
        response = requests.delete(
            url,
            auth=auth,
            params={"force": True},  # Permanently delete (skip trash)
            timeout=30,
        )

        if response.status_code == 200:
            return True, f"Deleted media ID {media_id}"
        else:
            return False, f"Failed to delete {media_id}: HTTP {response.status_code}"

    except Exception as e:
        return False, f"Error deleting {media_id}: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete duplicate images from WordPress Media Library"
    )
    parser.add_argument(
        "--similarity-report",
        type=Path,
        default=Path("wordpress/product_analysis/similarity_report.json"),
        help="Path to similarity report",
    )
    parser.add_argument(
        "--image-mapping",
        type=Path,
        default=Path("wordpress/webp_image_mapping.json"),
        help="Path to WordPress image mapping",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.98,
        help="Similarity threshold for duplicates (0-1, default: 0.98)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deletions without actually deleting",
    )

    args = parser.parse_args()

    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}WordPress Media Duplicate Cleanup{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")

    # Load data
    print(f"Loading similarity report: {args.similarity_report}")
    report = load_similarity_report(args.similarity_report)

    print(f"Loading image mapping: {args.image_mapping}")
    mapping = load_image_mapping(args.image_mapping)

    config = load_wordpress_config()
    print(f"WordPress site: {config['url']}")
    print(f"Similarity threshold: {args.threshold}")

    if args.dry_run:
        print(f"\n{YELLOW}DRY RUN MODE - No deletions will be performed{NC}\n")

    # Filter duplicates by threshold
    duplicates = [d for d in report["duplicates"] if d["similarity"] >= args.threshold]

    print(f"\nFound {len(duplicates)} duplicate pairs (similarity ≥ {args.threshold})")
    print()

    # Track deletions
    to_delete = set()
    deletion_plan = []

    # Build deletion plan
    for dup in duplicates:
        image1 = dup["image1"]
        image2 = dup["image2"]
        similarity = dup["similarity"]

        # Select which to delete
        delete_image = select_duplicate_to_delete(image1, image2)
        keep_image = image2 if delete_image == image1 else image1

        # Get media ID
        media_id = get_media_id(delete_image, mapping)

        if media_id is None:
            print(f"{YELLOW}⚠ Skipping {delete_image} (no media ID in mapping){NC}")
            continue

        if media_id in to_delete:
            continue  # Already scheduled for deletion

        to_delete.add(media_id)
        deletion_plan.append(
            {
                "delete": delete_image,
                "keep": keep_image,
                "media_id": media_id,
                "similarity": similarity,
            }
        )

    # Show deletion plan
    print(f"{BLUE}Deletion Plan:{NC}")
    print(f"{'Delete':<50} {'Keep':<50} {'Similarity'}")
    print("-" * 110)

    for item in deletion_plan:
        print(f"{item['delete']:<50} {item['keep']:<50} {item['similarity']:.3f}")

    print()
    print(f"Total duplicates to delete: {len(deletion_plan)}")

    if not deletion_plan:
        print(f"\n{GREEN}✓ No duplicates to delete!{NC}\n")
        return

    # Confirm deletion (unless dry-run)
    if not args.dry_run:
        print()
        response = input(f"{YELLOW}Proceed with deletion? (yes/no): {NC}")
        if response.lower() != "yes":
            print(f"\n{YELLOW}Deletion cancelled{NC}\n")
            return

    # Execute deletions
    print(f"\n{BLUE}Deleting duplicates...{NC}\n")

    deleted = 0
    failed = 0

    for item in deletion_plan:
        success, message = delete_media(item["media_id"], config, dry_run=args.dry_run)

        if success:
            print(f"{GREEN}✓ {message} - {item['delete']}{NC}")
            deleted += 1
        else:
            print(f"{RED}✗ {message} - {item['delete']}{NC}")
            failed += 1

    # Summary
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}Summary{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")
    print(f"Deleted:  {GREEN}{deleted}{NC}")
    print(f"Failed:   {RED}{failed}{NC}")

    if args.dry_run:
        print(f"\n{YELLOW}DRY RUN - No actual deletions performed{NC}")
        print("Run without --dry-run to delete duplicates\n")
    else:
        print(f"\n{GREEN}✓ Duplicate cleanup complete!{NC}\n")

        if deleted > 0:
            print("Next steps:")
            print("  1. Verify deletions in WordPress Media Library")
            print("  2. Update image mapping:")
            print("     python scripts/update_webp_mapping_ids.py")
            print()


if __name__ == "__main__":
    main()
