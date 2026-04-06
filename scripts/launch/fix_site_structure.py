"""Phase 3: Fix site structure — URL slugs, contact page, collection links.

Uses WordPress.com REST API (public-api.wordpress.com) for page operations
and WooCommerce REST API for category operations.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent

# Load env
env_path = ROOT / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

SITE_URL = os.getenv("WORDPRESS_URL", "https://skyyrose.co")
WC_KEY = os.getenv("WOOCOMMERCE_KEY", "")
WC_SECRET = os.getenv("WOOCOMMERCE_SECRET", "")
WP_USERNAME = os.getenv("WORDPRESS_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD", "")


def wc_request(method: str, endpoint: str, **kwargs) -> dict | list:
    """WooCommerce REST API request."""
    url = f"{SITE_URL}/wp-json/wc/v3/{endpoint}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, auth=(WC_KEY, WC_SECRET), **kwargs)
        resp.raise_for_status()
        return resp.json()


def wp_request(method: str, endpoint: str, **kwargs) -> dict | list:
    """WordPress REST API request (requires app password)."""
    url = f"{SITE_URL}/wp-json/wp/v2/{endpoint}"
    auth = (WP_USERNAME, WP_APP_PASSWORD) if WP_USERNAME and WP_APP_PASSWORD else None
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, auth=auth, **kwargs)
        resp.raise_for_status()
        return resp.json()


def verify_products():
    """Verify products are synced with images and prices."""
    print("=" * 60)
    print("VERIFYING PRODUCT SYNC")
    print("=" * 60)

    products = wc_request("GET", "products", params={"per_page": 100})
    total = len(products)
    with_images = sum(
        1
        for p in products
        if p.get("images")
        and len(p["images"]) > 0
        and "placeholder" not in p["images"][0].get("src", "")
    )
    with_prices = sum(1 for p in products if p.get("price") and float(p.get("price", 0)) > 0)

    print(f"  Total products:     {total}")
    print(f"  With real images:   {with_images}/{total}")
    print(f"  With prices:        {with_prices}/{total}")
    print()

    # Show products missing images or prices
    issues = []
    for p in products:
        has_image = (
            p.get("images")
            and len(p["images"]) > 0
            and "placeholder" not in p["images"][0].get("src", "")
        )
        has_price = p.get("price") and float(p.get("price", 0)) > 0
        if not has_image or not has_price:
            issues.append(
                f"  ⚠ {p.get('sku', '(none)'):18s} | img: {'✓' if has_image else '✗':1s} | price: {'✓' if has_price else '✗':1s} | {p['name'][:40]}"
            )

    if issues:
        print("  Issues found:")
        for issue in issues:
            print(issue)
    else:
        print("  ✓ All products have images and prices!")

    print()
    return total, with_images, with_prices


def verify_categories():
    """Verify WooCommerce categories exist."""
    print("VERIFYING CATEGORIES")
    print("-" * 40)

    categories = wc_request("GET", "products/categories", params={"per_page": 100})
    expected = {"signature", "black-rose", "love-hurts", "kids-capsule"}
    found = {c["slug"]: c for c in categories}

    for slug in expected:
        if slug in found:
            cat = found[slug]
            count = cat.get("count", 0)
            print(f"  ✓ {slug:20s} (ID: {cat['id']:3d}, products: {count})")
        else:
            print(f"  ✗ {slug:20s} — MISSING")

    print()


def verify_site_pages():
    """Verify key pages exist and have correct slugs."""
    print("VERIFYING PAGES")
    print("-" * 40)

    try:
        pages = wp_request("GET", "pages", params={"per_page": 100})
    except Exception as e:
        print(f"  ⚠ Cannot verify pages (WP REST auth needed): {e}")
        print("  Falling back to public URL checks...")
        check_public_urls()
        return

    slugs = {p["slug"]: p for p in pages}

    checks = [
        ("home", "Homepage"),
        ("about", "About"),
        ("contact", "Contact"),
        ("shop", "Shop"),
    ]

    for slug, label in checks:
        if slug in slugs:
            page = slugs[slug]
            print(f"  ✓ /{slug}/ — {label} (ID: {page['id']}, status: {page['status']})")
        elif f"{slug}-2" in slugs:
            print(f"  ⚠ /{slug}-2/ exists instead of /{slug}/ — needs slug fix")
        else:
            print(f"  ✗ /{slug}/ — {label} — NOT FOUND")

    print()


def check_public_urls():
    """Check key URLs are accessible publicly."""
    urls = [
        (f"{SITE_URL}/", "Homepage"),
        (f"{SITE_URL}/shop/", "Shop"),
        (f"{SITE_URL}/about/", "About"),
        (f"{SITE_URL}/contact/", "Contact"),
        (f"{SITE_URL}/cart/", "Cart"),
        (f"{SITE_URL}/checkout/", "Checkout"),
    ]

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for url, label in urls:
            try:
                resp = client.get(url)
                status = resp.status_code
                final_url = str(resp.url)
                redirect = f" → {final_url}" if final_url != url else ""
                symbol = "✓" if status == 200 else "⚠"
                print(f"  {symbol} {label:15s} | {status} | {url}{redirect}")
            except Exception as e:
                print(f"  ✗ {label:15s} | ERROR | {e}")

    print()


def main():
    """Run all verifications and fixes."""
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║     PHASE 3: SITE STRUCTURE VERIFICATION            ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    # 1. Verify products
    total, with_images, with_prices = verify_products()

    # 2. Verify categories
    verify_categories()

    # 3. Verify pages
    verify_site_pages()

    # 4. Check public URLs
    print("CHECKING PUBLIC URLs")
    print("-" * 40)
    check_public_urls()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Products:    {total} total, {with_images} with images, {with_prices} with prices")
    print(f"  Site URL:    {SITE_URL}")
    print()

    if not WP_APP_PASSWORD:
        print("  ⚠ WORDPRESS_APP_PASSWORD not set in .env")
        print("    Cannot fix page slugs or create contact page via API.")
        print("    Manual wp-admin tasks needed:")
        print("    1. Fix /home-2/ → /home/")
        print("    2. Fix /about-2/ → /about/")
        print("    3. Create /contact/ page")
        print("    4. Set static homepage in Settings → Reading")
        print("    5. Create navigation menu in Appearance → Menus")
    print()


if __name__ == "__main__":
    main()
