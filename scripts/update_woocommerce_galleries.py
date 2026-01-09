#!/usr/bin/env python3
"""
Update WooCommerce Product Galleries with 2D/2.5D Visualization Images

Queries WooCommerce products, uses fuzzy name matching to associate uploaded
2D/2.5D visualization images, and updates product galleries.

Follows Context7-researched patterns:
- RapidFuzz for fuzzy string matching (process.extractOne, fuzz.WRatio)
- aiohttp BasicAuth for WooCommerce REST API authentication
- Ralph-loop retry pattern with exponential backoff

Created: 2026-01-08
"""

import asyncio
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import aiohttp
from aiohttp import BasicAuth
from dotenv import load_dotenv
from rapidfuzz import fuzz, process, utils

# Load environment variables
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / ".env")

# WordPress/WooCommerce credentials
WP_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WC_KEY = os.getenv("WOOCOMMERCE_KEY")
WC_SECRET = os.getenv("WOOCOMMERCE_SECRET")

# Validate credentials
if not WC_KEY or not WC_SECRET:
    print("❌ WOOCOMMERCE_KEY or WOOCOMMERCE_SECRET not set in .env")
    sys.exit(1)

# Ralph-loop configuration
MAX_RETRIES = 5  # Increased retries for rate limiting
INITIAL_DELAY = 10  # Wait 10s before starting (let rate limit cool down)
FUZZY_MATCH_THRESHOLD = 70.0  # Minimum similarity score (0-100)


def extract_product_name_from_filepath(filepath: str) -> str:
    """
    Extract clean product name from filepath.

    Examples:
        "The Yay Bridge Set_detail.jpg" → "The Yay Bridge Set"
        "_Signature Collection_ Crop Hoodie back_depth.jpg" → "Signature Collection Crop Hoodie back"
        "Photo Dec 18 2023, 6 09 21 PM (4)_shadow.jpg" → "Photo Dec 18 2023 6 09 21 PM 4"
    """
    filename = Path(filepath).stem  # Remove extension

    # Remove variation suffix (_detail, _shadow, _depth, _parallax)
    for suffix in ["_detail", "_shadow", "_depth", "_parallax"]:
        if filename.endswith(suffix):
            filename = filename[: -len(suffix)]
            break

    # Remove leading/trailing underscores and clean up
    filename = filename.strip("_")
    filename = filename.replace("_", " ")

    # Remove special characters but keep alphanumeric and spaces
    import re

    filename = re.sub(r"[^\w\s-]", "", filename)

    return filename.strip()


async def fetch_all_woocommerce_products(session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch all WooCommerce products using pagination.

    Context7 Pattern:
        GET /wp-json/wc/v3/products with per_page and page parameters
        BasicAuth with consumer_key and consumer_secret
    """
    all_products = []
    page = 1
    per_page = 100

    print(f"\n🔍 Querying WooCommerce products from {WP_URL}...")
    print(f"  ⏳ Waiting {INITIAL_DELAY}s before starting (rate limit cooldown)...")
    await asyncio.sleep(INITIAL_DELAY)

    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "status": "publish",  # Only published products
        }

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                url = f"{WP_URL}/wp-json/wc/v3/products"

                async with session.get(
                    url, params=params, auth=BasicAuth(WC_KEY, WC_SECRET)
                ) as resp:
                    if resp.status == 200:
                        products = await resp.json()

                        if not products:
                            return all_products  # No more products

                        all_products.extend(products)
                        print(
                            f"  ✓ Fetched {len(products)} products (page {page}, total: {len(all_products)})"
                        )

                        # Check if there are more pages
                        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
                        if page >= total_pages:
                            return all_products

                        page += 1
                        break  # Success, continue to next page

                    elif resp.status == 429:
                        # Rate limited - retry with exponential backoff (ralph-loop)
                        retry_count += 1
                        if retry_count < MAX_RETRIES:
                            wait_time = 30 * (2**retry_count)  # 60s, 120s, 240s, 480s
                            print(
                                f"  ⚠ Rate limited (429), waiting {wait_time}s before retry... (attempt {retry_count}/{MAX_RETRIES})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"  ✗ Failed after {MAX_RETRIES} retries due to rate limiting")
                            return all_products

                    else:
                        error_text = await resp.text()
                        print(f"  ✗ Failed to fetch products (page {page}): {resp.status}")
                        return all_products

            except Exception as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    wait_time = 2**retry_count
                    print(
                        f"  ✗ Error: {e}. Retrying in {wait_time}s... (attempt {retry_count}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"  ✗ Failed after {MAX_RETRIES} retries: {e}")
                    return all_products

    print(f"\n✅ Total products fetched: {len(all_products)}")
    return all_products


def match_product_name_fuzzy(
    uploaded_product_name: str, wc_products: list[dict], threshold: float = FUZZY_MATCH_THRESHOLD
) -> tuple[dict, float] | None:
    """
    Match uploaded product name to WooCommerce product using fuzzy matching.

    Context7 Pattern (RapidFuzz):
        process.extractOne() with fuzz.WRatio scorer
        utils.default_process for case-insensitive preprocessing

    Returns:
        (matched_product, similarity_score) or None if no match above threshold
    """
    # Build choices: product names from WooCommerce
    choices = {product["id"]: product["name"] for product in wc_products}

    # Use RapidFuzz to find best match
    result = process.extractOne(
        uploaded_product_name,
        choices,
        scorer=fuzz.WRatio,
        processor=utils.default_process,  # Case-insensitive, remove special chars
        score_cutoff=threshold,
    )

    if not result:
        return None

    matched_name, score, product_id = result

    # Find the full product object
    matched_product = next(p for p in wc_products if p["id"] == product_id)

    return (matched_product, score)


async def update_product_gallery(
    session: aiohttp.ClientSession, product_id: int, new_images: list[dict], product_name: str
) -> bool:
    """
    Update WooCommerce product gallery images.

    Context7 Pattern:
        PUT /wp-json/wc/v3/products/{id}
        Body: {"images": [{"src": "url1"}, {"src": "url2"}, ...]}
        BasicAuth with consumer_key and consumer_secret

    Ralph-loop: Exponential backoff retry on failures
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Prepare images payload
            images_payload = [{"src": img["url"]} for img in new_images]

            async with session.put(
                f"{WP_URL}/wp-json/wc/v3/products/{product_id}",
                json={"images": images_payload},
                auth=BasicAuth(WC_KEY, WC_SECRET),
            ) as resp:
                if resp.status == 200:
                    print(
                        f"  ✓ Updated gallery for '{product_name}' (ID: {product_id}) with {len(new_images)} images"
                    )
                    return True
                elif resp.status == 429:
                    # Rate limited - retry with exponential backoff (ralph-loop)
                    if attempt < MAX_RETRIES - 1:
                        wait_time = 2**attempt  # 1s, 2s, 4s
                        print(
                            f"  ⚠ Rate limited, retrying in {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    error_text = await resp.text()
                    print(
                        f"  ✗ Failed to update product {product_id}: {resp.status} - {error_text}"
                    )
                    return False

        except Exception as e:
            print(f"  ✗ Error updating product {product_id}: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = 2**attempt
                print(f"  ⏳ Retrying in {wait_time}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait_time)
                continue
            return False

    return False


async def main():
    """Main execution flow."""

    # 1. Load upload results JSON
    upload_results_path = (
        project_root / "assets" / "2d-25d-assets" / "wordpress_upload_results.json"
    )

    if not upload_results_path.exists():
        print(f"❌ Upload results not found: {upload_results_path}")
        sys.exit(1)

    with open(upload_results_path) as f:
        upload_data = json.load(f)

    successful_uploads = [r for r in upload_data["upload_results"] if r.get("success")]

    print(f"📊 Loaded {len(successful_uploads)} successful uploads from {upload_results_path.name}")

    # 2. Group uploads by product name
    products_images: dict[str, list[dict]] = defaultdict(list)

    for upload in successful_uploads:
        product_name = extract_product_name_from_filepath(upload["file"])
        products_images[product_name].append(
            {
                "id": upload["id"],
                "url": upload["url"],
                "variation_type": upload["variation_type"],
                "css_class": upload.get("css_class", ""),
            }
        )

    print(f"\n📦 Grouped into {len(products_images)} unique products")

    # 3. Query WooCommerce products
    async with aiohttp.ClientSession() as session:
        wc_products = await fetch_all_woocommerce_products(session)

        if not wc_products:
            print("❌ No WooCommerce products found")
            sys.exit(1)

        # 4. Match and update galleries
        print("\n🔗 Matching uploaded images to WooCommerce products...\n")

        matched_count = 0
        updated_count = 0
        unmatched = []

        for uploaded_name, images in products_images.items():
            match_result = match_product_name_fuzzy(uploaded_name, wc_products)

            if match_result:
                matched_product, similarity = match_result
                print(
                    f"  ✓ '{uploaded_name}' → '{matched_product['name']}' (similarity: {similarity:.1f}%)"
                )

                # Update gallery
                success = await update_product_gallery(
                    session, matched_product["id"], images, matched_product["name"]
                )

                if success:
                    updated_count += 1

                matched_count += 1
            else:
                print(
                    f"  ✗ No match found for '{uploaded_name}' (threshold: {FUZZY_MATCH_THRESHOLD}%)"
                )
                unmatched.append(uploaded_name)

        # 5. Summary
        print(f"\n{'=' * 60}")
        print("📊 SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total uploaded products: {len(products_images)}")
        print(f"Matched to WooCommerce: {matched_count}")
        print(f"Galleries updated: {updated_count}")
        print(f"Unmatched: {len(unmatched)}")

        if unmatched:
            print("\n⚠ Unmatched products:")
            for name in unmatched:
                print(f"  - {name}")

        print("\n✅ Gallery update complete!")


if __name__ == "__main__":
    asyncio.run(main())
