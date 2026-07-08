"""Minimal WooCommerce REST v3 client for the OpenAI feed generator.

Reads credentials from environment variables only (never hardcoded). Loads
`.env.wordpress` at the repo root if present so this script can run the same
way the rest of the WordPress tooling does, without pulling in a
python-dotenv dependency.

Note: WordPress.com's `index.php?rest_route=` convenience form returns 401 for
WooCommerce endpoints on this store — the `/wp-json/wc/v3` path is required
(see CLAUDE.md).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env.wordpress"

REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0
PER_PAGE = 100


class WooCommerceCredentialsError(RuntimeError):
    """Raised when WC REST credentials cannot be resolved."""


class WooCommerceRequestError(RuntimeError):
    """Raised when a WC REST request fails after retries."""


def load_env_file(path: Path = ENV_FILE) -> None:
    """Populate os.environ from a simple KEY=VALUE file, without overwriting
    variables already set in the real environment."""
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_wc_config() -> tuple[str, str, str]:
    """Return (site_url, consumer_key, consumer_secret) from the environment."""
    load_env_file()
    site_url = os.environ.get("WORDPRESS_URL") or os.environ.get("WORDPRESS_SITE_URL")
    key = os.environ.get("WOOCOMMERCE_KEY")
    secret = os.environ.get("WOOCOMMERCE_SECRET")
    if not site_url or not key or not secret:
        missing = [
            name
            for name, value in (
                ("WORDPRESS_URL", site_url),
                ("WOOCOMMERCE_KEY", key),
                ("WOOCOMMERCE_SECRET", secret),
            )
            if not value
        ]
        raise WooCommerceCredentialsError(
            f"Missing WooCommerce credentials in environment / .env.wordpress: {', '.join(missing)}"
        )
    return site_url.rstrip("/"), key, secret


def _get_with_retries(client: httpx.Client, url: str, params: dict[str, Any]) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
        except httpx.HTTPStatusError as exc:
            # 5xx are worth retrying; 4xx are not.
            if exc.response.status_code >= 500 and attempt < MAX_RETRIES:
                last_error = exc
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise WooCommerceRequestError(
                f"WooCommerce request failed ({exc.response.status_code}) for {url}: {exc.response.text[:300]}"
            ) from exc
    raise WooCommerceRequestError(
        f"WooCommerce request failed after {MAX_RETRIES} attempts for {url}"
    ) from last_error


def fetch_all_products(
    client: httpx.Client, base_url: str, *, status: str = "any"
) -> list[dict[str, Any]]:
    """Fetch every product across all pages."""
    products: list[dict[str, Any]] = []
    page = 1
    while True:
        response = _get_with_retries(
            client,
            f"{base_url}/products",
            {"per_page": PER_PAGE, "page": page, "status": status},
        )
        batch = response.json()
        if not batch:
            break
        products.extend(batch)
        total_pages_header = response.headers.get("X-WP-TotalPages")
        if total_pages_header and page >= int(total_pages_header):
            break
        if len(batch) < PER_PAGE:
            break
        page += 1
    return products


def fetch_variations(client: httpx.Client, base_url: str, product_id: int) -> list[dict[str, Any]]:
    """Fetch every variation of a variable product across all pages."""
    variations: list[dict[str, Any]] = []
    page = 1
    while True:
        response = _get_with_retries(
            client,
            f"{base_url}/products/{product_id}/variations",
            {"per_page": PER_PAGE, "page": page},
        )
        batch = response.json()
        if not batch:
            break
        variations.extend(batch)
        if len(batch) < PER_PAGE:
            break
        page += 1
    return variations


def fetch_catalog(
    *, base_url: str | None = None, key: str | None = None, secret: str | None = None
) -> list[dict[str, Any]]:
    """Fetch all products (with variations attached under `_variations_data`
    for variable products) from the live WooCommerce store.

    Read-only: GET requests only. Raises WooCommerceCredentialsError or
    WooCommerceRequestError on failure — callers should let these surface
    rather than silently returning an empty catalog.
    """
    if base_url is None or key is None or secret is None:
        env_url, env_key, env_secret = get_wc_config()
        base_url = base_url or f"{env_url}/wp-json/wc/v3"
        key = key or env_key
        secret = secret or env_secret

    with httpx.Client(auth=(key, secret), timeout=REQUEST_TIMEOUT) as client:
        products = fetch_all_products(client, base_url)
        for product in products:
            if product.get("type") == "variable" and product.get("variations"):
                try:
                    product["_variations_data"] = fetch_variations(client, base_url, product["id"])
                except WooCommerceRequestError as exc:
                    print(
                        f"WARNING: failed to fetch variations for product {product.get('id')} "
                        f"({product.get('sku')}): {exc}",
                        file=sys.stderr,
                    )
                    product["_variations_data"] = []
    return products
