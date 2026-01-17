#!/usr/bin/env python3
"""
WordPress Media Duplicate Cleanup Script
Identifies and removes duplicate/obsolete uploads from WordPress media library.

Strategy:
- KEEP: ai-enhanced-v2 (IDs 8278-8529) - Latest AI pipeline results
- KEEP: 2d-25d (IDs 7528-7621) - Unique parallax/depth/shadow assets
- DELETE: enhanced_products (IDs 7170-7208) - Replaced by ai-enhanced-v2
- DELETE: ai-models (IDs 7622-7646) - Replaced by ai-enhanced-v2
"""

import argparse
import base64
import json
import time
from pathlib import Path

import requests

# WordPress configuration
WP_URL = "https://skyyrose.co"
WP_USER = "skyyroseco"
WP_PASS = "IQb3KFqFA76vhMJmsyT1tCTC"
MEDIA_ENDPOINT = f"{WP_URL}/index.php?rest_route=/wp/v2/media"

# Upload result files
RESULT_FILES = {
    "enhanced_products": Path(
        "/Users/coreyfoster/DevSkyy/assets/enhanced_products/all/wordpress_upload_results.json"
    ),
    "2d_25d": Path("/Users/coreyfoster/DevSkyy/assets/2d-25d-assets/wordpress_upload_results.json"),
    "ai_models": Path(
        "/Users/coreyfoster/DevSkyy/assets/ai-models-with-products/wordpress_upload_results.json"
    ),
    "ai_enhanced_v2": Path(
        "/Users/coreyfoster/DevSkyy/assets/ai-enhanced-images/WP_UPLOAD_RESULTS_v2.json"
    ),
}

# IDs to DELETE (obsolete uploads replaced by ai-enhanced-v2)
DELETE_BATCHES = ["enhanced_products", "ai_models"]

# IDs to KEEP
KEEP_BATCHES = ["2d_25d", "ai_enhanced_v2"]


def get_auth_header() -> dict:
    """Create Basic auth header."""
    auth_string = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    return {"Authorization": f"Basic {auth_string}"}


def load_upload_results(batch_name: str) -> list[dict]:
    """Load upload results from JSON file."""
    filepath = RESULT_FILES.get(batch_name)
    if not filepath or not filepath.exists():
        return []

    with open(filepath) as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("upload_results", data.get("results", []))
    return []


def get_ids_to_delete() -> list[int]:
    """Collect all media IDs that should be deleted."""
    ids_to_delete = []

    for batch in DELETE_BATCHES:
        results = load_upload_results(batch)
        for item in results:
            if item.get("success") and item.get("id"):
                ids_to_delete.append(item["id"])

    return sorted(ids_to_delete)


def get_ids_to_keep() -> list[int]:
    """Collect all media IDs that should be kept."""
    ids_to_keep = []

    for batch in KEEP_BATCHES:
        results = load_upload_results(batch)
        for item in results:
            if item.get("success") and item.get("id"):
                ids_to_keep.append(item["id"])

    return sorted(ids_to_keep)


def verify_media_exists(media_id: int, headers: dict) -> bool:
    """Check if media item exists in WordPress."""
    try:
        resp = requests.get(f"{MEDIA_ENDPOINT}&include={media_id}", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return len(data) > 0 and data[0].get("id") == media_id
        return False
    except Exception:
        return False


def delete_media(media_id: int, headers: dict) -> tuple[bool, str]:
    """Delete a single media item from WordPress."""
    try:
        # Use index.php?rest_route format with force=true
        delete_url = f"{WP_URL}/index.php?rest_route=/wp/v2/media/{media_id}&force=true"

        resp = requests.delete(delete_url, headers=headers, timeout=60)

        if resp.status_code in (200, 201):
            result = resp.json()
            if result.get("deleted"):
                return True, "Deleted successfully"
            return True, f"Deleted (id: {result.get('id', media_id)})"
        elif resp.status_code == 404:
            return True, "Already deleted (404)"
        else:
            error = resp.text[:100] if resp.text else str(resp.status_code)
            return False, f"Failed: {resp.status_code} - {error}"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Clean up duplicate WordPress media uploads")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--verify", action="store_true", help="Verify each item exists before deleting"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("WordPress Media Duplicate Cleanup")
    print("=" * 60)

    # Load IDs
    ids_to_delete = get_ids_to_delete()
    ids_to_keep = get_ids_to_keep()

    print(f"\nBatches to DELETE: {DELETE_BATCHES}")
    print(f"Batches to KEEP: {KEEP_BATCHES}")
    print(f"\nIDs to delete: {len(ids_to_delete)} items")
    print(f"IDs to keep: {len(ids_to_keep)} items")

    if not ids_to_delete:
        print("\nNo items to delete. Exiting.")
        return

    # Show ID ranges
    print(f"\nDelete range: {min(ids_to_delete)} - {max(ids_to_delete)}")
    print(f"Keep range: {min(ids_to_keep)} - {max(ids_to_keep)}")

    # Safety check: ensure no overlap
    overlap = set(ids_to_delete) & set(ids_to_keep)
    if overlap:
        print(f"\nWARNING: Overlap detected! IDs in both delete and keep: {sorted(overlap)}")
        print("Removing overlapping IDs from delete list...")
        ids_to_delete = [i for i in ids_to_delete if i not in overlap]

    headers = get_auth_header()

    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - No deletions will be performed")
        print("=" * 60)

        for batch in DELETE_BATCHES:
            results = load_upload_results(batch)
            print(f"\n{batch} ({len(results)} items):")
            for item in results[:5]:  # Show first 5
                print(f"  - ID {item.get('id')}: {item.get('title', item.get('url', 'N/A'))[:50]}")
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more")

        print(f"\nTotal to delete: {len(ids_to_delete)} media items")
        print("\nRun without --dry-run to execute deletion.")
        return

    # Execute deletions
    print("\n" + "=" * 60)
    print("EXECUTING DELETIONS")
    print("=" * 60)

    success_count = 0
    fail_count = 0
    already_deleted = 0

    for i, media_id in enumerate(ids_to_delete):
        # Verify exists first if requested
        if args.verify:
            if not verify_media_exists(media_id, headers):
                print(f"[{i + 1}/{len(ids_to_delete)}] ID {media_id}: Already deleted/missing")
                already_deleted += 1
                continue

        success, message = delete_media(media_id, headers)

        if success:
            if "Already deleted" in message:
                already_deleted += 1
            else:
                success_count += 1
            print(f"[{i + 1}/{len(ids_to_delete)}] ID {media_id}: {message}")
        else:
            fail_count += 1
            print(f"[{i + 1}/{len(ids_to_delete)}] ID {media_id}: {message}")

        # Rate limiting
        time.sleep(0.3)

        # Progress checkpoint
        if (i + 1) % 20 == 0:
            print(f"Progress: {i + 1}/{len(ids_to_delete)} processed")

    # Summary
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Successfully deleted: {success_count}")
    print(f"Already deleted/missing: {already_deleted}")
    print(f"Failed: {fail_count}")
    print(f"Total processed: {len(ids_to_delete)}")


if __name__ == "__main__":
    main()
