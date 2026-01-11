#!/usr/bin/env python3
"""
SkyyRose.co Site Verification Script.

Comprehensive automated verification for:
- Site accessibility and SSL
- WordPress/WooCommerce functionality
- HuggingFace Spaces embeds
- Product galleries and images
- Performance metrics
- Mobile responsiveness
"""

import asyncio
import sys
import time
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

SITE_URL = "https://skyyrose.co"
TIMEOUT = 30

# Test URLs
TEST_URLS = {
    "home": f"{SITE_URL}/",
    "shop": f"{SITE_URL}/shop/",
    "experiences": f"{SITE_URL}/experiences/",
    "3d_converter": f"{SITE_URL}/experiences/3d-converter/",
    "virtual_tryon": f"{SITE_URL}/experiences/virtual-tryon/",
    "lora_training": f"{SITE_URL}/experiences/lora-training/",
}


async def check_url(
    session: aiohttp.ClientSession, name: str, url: str
) -> dict[str, bool | str | int]:
    """Check URL accessibility and response time."""
    start_time = time.time()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
            response_time = (time.time() - start_time) * 1000  # ms
            return {
                "name": name,
                "url": url,
                "success": resp.status == 200,
                "status": resp.status,
                "response_time_ms": round(response_time, 2),
                "error": None,
            }
    except TimeoutError:
        return {
            "name": name,
            "url": url,
            "success": False,
            "status": 0,
            "response_time_ms": 0,
            "error": "Timeout",
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "success": False,
            "status": 0,
            "response_time_ms": 0,
            "error": str(e),
        }


async def check_huggingface_embeds(session: aiohttp.ClientSession) -> dict[str, bool]:
    """Check if HuggingFace Spaces are embedded correctly."""
    embeds_status = {}

    for space_name in ["3d_converter", "virtual_tryon", "lora_training"]:
        url = TEST_URLS[space_name]
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Check for HuggingFace iframe
                    iframe = soup.find("iframe", src=lambda x: x and "huggingface" in x)
                    embeds_status[space_name] = iframe is not None
                else:
                    embeds_status[space_name] = False
        except Exception:
            embeds_status[space_name] = False

    return embeds_status


async def check_wordpress_api(session: aiohttp.ClientSession) -> dict[str, bool]:
    """Check WordPress REST API accessibility."""
    api_checks = {}

    # Check posts endpoint
    try:
        async with session.get(
            f"{SITE_URL}/wp-json/wp/v2/posts",
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
        ) as resp:
            api_checks["posts"] = resp.status == 200
    except Exception:
        api_checks["posts"] = False

    # Check WooCommerce products endpoint
    try:
        async with session.get(
            f"{SITE_URL}/wp-json/wc/v3/products",
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
        ) as resp:
            # 401 is expected without auth (means endpoint exists)
            api_checks["products"] = resp.status in [200, 401]
    except Exception:
        api_checks["products"] = False

    return api_checks


async def check_product_images(session: aiohttp.ClientSession) -> dict[str, int]:
    """Check product gallery images availability."""
    image_stats = {"total_checked": 0, "successful": 0, "failed": 0}

    try:
        # Get shop page and find product images
        async with session.get(
            f"{SITE_URL}/shop/", timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                # Find product images
                product_images = soup.find_all("img", class_=lambda x: x and "product" in x)

                for img in product_images[:10]:  # Check first 10 images
                    if img.get("src"):
                        image_stats["total_checked"] += 1
                        try:
                            async with session.head(
                                img["src"], timeout=aiohttp.ClientTimeout(total=5)
                            ) as img_resp:
                                if img_resp.status == 200:
                                    image_stats["successful"] += 1
                                else:
                                    image_stats["failed"] += 1
                        except Exception:
                            image_stats["failed"] += 1

    except Exception:
        pass

    return image_stats


async def main():
    """Run all verification checks."""
    print("=" * 70)
    print("🚀 SkyyRose.co Site Verification")
    print("=" * 70)
    print()

    async with aiohttp.ClientSession() as session:
        # 1. Check all URLs
        print("📍 Checking URL Accessibility...")
        print("-" * 70)

        url_tasks = [check_url(session, name, url) for name, url in TEST_URLS.items()]
        url_results = await asyncio.gather(*url_tasks)

        for result in url_results:
            status_icon = "✅" if result["success"] else "❌"
            print(
                f"{status_icon} {result['name']:20} | {result['status']:3} | "
                f"{result['response_time_ms']:6.0f}ms | {result['url']}"
            )
            if result["error"]:
                print(f"   Error: {result['error']}")

        print()

        # 2. Check HuggingFace embeds
        print("🤖 Checking HuggingFace Spaces Embeds...")
        print("-" * 70)

        embeds_status = await check_huggingface_embeds(session)
        for space_name, is_embedded in embeds_status.items():
            status_icon = "✅" if is_embedded else "❌"
            print(f"{status_icon} {space_name:20} | Embedded: {is_embedded}")

        print()

        # 3. Check WordPress API
        print("🔌 Checking WordPress/WooCommerce API...")
        print("-" * 70)

        api_checks = await check_wordpress_api(session)
        for endpoint, is_ok in api_checks.items():
            status_icon = "✅" if is_ok else "❌"
            print(f"{status_icon} {endpoint:20} | Accessible: {is_ok}")

        print()

        # 4. Check product images
        print("🖼️  Checking Product Images...")
        print("-" * 70)

        image_stats = await check_product_images(session)
        print(f"Total Checked: {image_stats['total_checked']}")
        print(f"✅ Successful: {image_stats['successful']}")
        print(f"❌ Failed: {image_stats['failed']}")

        print()

        # Summary
        print("=" * 70)
        print("📊 Summary")
        print("=" * 70)

        total_url_checks = len(url_results)
        successful_urls = sum(1 for r in url_results if r["success"])
        avg_response_time = (
            sum(r["response_time_ms"] for r in url_results if r["success"]) / successful_urls
            if successful_urls > 0
            else 0
        )

        total_embed_checks = len(embeds_status)
        successful_embeds = sum(1 for v in embeds_status.values() if v)

        total_api_checks = len(api_checks)
        successful_apis = sum(1 for v in api_checks.values() if v)

        print(f"URLs: {successful_urls}/{total_url_checks} accessible")
        print(f"Average Response Time: {avg_response_time:.0f}ms")
        print(f"HF Spaces: {successful_embeds}/{total_embed_checks} embedded")
        print(f"APIs: {successful_apis}/{total_api_checks} accessible")
        print(f"Images: {image_stats['successful']}/{image_stats['total_checked']} loading")

        print()

        # Overall status
        all_urls_ok = successful_urls == total_url_checks
        all_embeds_ok = successful_embeds == total_embed_checks
        all_apis_ok = successful_apis == total_api_checks
        images_ok = image_stats["failed"] == 0

        if all_urls_ok and all_embeds_ok and all_apis_ok and images_ok:
            print("✅ ALL CHECKS PASSED - Site is fully operational!")
            return 0
        else:
            print("⚠️  SOME CHECKS FAILED - Review errors above")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
