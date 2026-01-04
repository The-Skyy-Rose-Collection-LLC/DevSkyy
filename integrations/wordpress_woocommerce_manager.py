# wordpress_woocommerce_manager.py

import requests
from requests.auth import HTTPBasicAuth


class WordPressWooCommerceManager:
    """
    Complete WordPress/WooCommerce REST API integration
    Handles products, media, SEO, and automation
    """

    def __init__(self, site_url: str, username: str, app_password: str, verify_ssl: bool = True):
        """
        Initialize WordPress API client

        Setup Application Password:
        1. Login to WordPress Admin
        2. Users → Profile
        3. Scroll to "Application Passwords"
        4. Enter name: "SkyyRose Automation"
        5. Click "Add New Application Password"
        6. Save the generated password (only shown once)

        Args:
            site_url: https://skyyrose.co
            username: WordPress admin username
            app_password: Application password (NOT regular password)
        """

        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.verify_ssl = verify_ssl

        # API endpoints
        self.api_base = f"{self.site_url}/wp-json"
        self.wc_base = f"{self.api_base}/wc/v3"
        self.wp_base = f"{self.api_base}/wp/v2"

        # Auth
        self.auth = HTTPBasicAuth(username, app_password)

        # Test connection
        self._test_connection()

        print(f"✅ WordPress Manager initialized for {site_url}")

    def _test_connection(self):
        """Test API connection and authentication"""

        try:
            response = requests.get(
                f"{self.wp_base}/users/me", auth=self.auth, verify=self.verify_ssl, timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Connected as: {user_data['name']} ({user_data['email']})")
            else:
                raise Exception(f"Authentication failed: {response.status_code}")

        except Exception as e:
            raise Exception(f"WordPress connection test failed: {e}")

    def create_product(
        self,
        name: str,
        price: float,
        description: str,
        short_description: str,
        sku: str,
        images: list[str],
        categories: list[str],
        tags: list[str],
        meta_data: list[dict] | None = None,
        status: str = "draft",
        **kwargs,
    ) -> dict:
        """
        Create WooCommerce product

        Args:
            name: Product name
            price: Regular price
            description: Full product description (HTML supported)
            short_description: Short description for product cards
            sku: Stock Keeping Unit
            images: List of image URLs (first is featured image)
            categories: List of category names
            tags: List of tag names
            meta_data: Custom meta fields
            status: 'publish' or 'draft'
            **kwargs: Additional WooCommerce product fields

        Returns:
            {
                'id': 123,
                'permalink': 'https://skyyrose.co/product/essential-black-hoodie',
                'slug': 'essential-black-hoodie',
                'sku': 'SRS-SIG-001',
                'status': 'draft'
            }
        """

        print(f"  → Creating product: {name}")

        # Prepare product data
        product_data = {
            "name": name,
            "type": "simple",
            "regular_price": str(price),
            "description": description,
            "short_description": short_description,
            "sku": sku,
            "status": status,
            "catalog_visibility": "visible",
            "manage_stock": True,
            "stock_quantity": 100,  # Default stock
            "stock_status": "instock",
            "backorders": "no",
            "sold_individually": False,
            # Images (first is featured)
            "images": [{"src": url} for url in images],
            # Categories
            "categories": [{"name": cat} for cat in categories],
            # Tags
            "tags": [{"name": tag} for tag in tags],
            # Custom meta data
            "meta_data": meta_data or [],
            # Additional kwargs
            **kwargs,
        }

        # Create product
        response = requests.post(
            f"{self.wc_base}/products",
            json=product_data,
            auth=self.auth,
            verify=self.verify_ssl,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 201:
            product = response.json()
            print(f"    ✓ Product created: {product['permalink']}")

            return {
                "id": product["id"],
                "permalink": product["permalink"],
                "slug": product["slug"],
                "sku": product["sku"],
                "status": product["status"],
            }
        else:
            error_msg = response.json().get("message", "Unknown error")
            raise Exception(f"Product creation failed: {error_msg}")

    def update_product(self, product_id: int, updates: dict) -> dict:
        """
        Update existing product

        Args:
            product_id: WooCommerce product ID
            updates: Fields to update

        Returns:
            Updated product data
        """

        print(f"  → Updating product ID: {product_id}")

        response = requests.put(
            f"{self.wc_base}/products/{product_id}",
            json=updates,
            auth=self.auth,
            verify=self.verify_ssl,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            product = response.json()
            print("    ✓ Product updated")
            return product
        else:
            error_msg = response.json().get("message", "Unknown error")
            raise Exception(f"Product update failed: {error_msg}")

    def update_seo_meta(
        self,
        product_id: int,
        seo_title: str,
        seo_description: str,
        focus_keyword: str,
        canonical_url: str | None = None,
    ):
        """
        Update Yoast SEO meta data

        Requires: Yoast SEO plugin installed
        """

        print(f"  → Updating SEO meta for product {product_id}")

        seo_meta = [
            {"key": "_yoast_wpseo_title", "value": seo_title},
            {"key": "_yoast_wpseo_metadesc", "value": seo_description},
            {"key": "_yoast_wpseo_focuskw", "value": focus_keyword},
        ]

        if canonical_url:
            seo_meta.append({"key": "_yoast_wpseo_canonical", "value": canonical_url})

        self.update_product(product_id, {"meta_data": seo_meta})

        print("    ✓ SEO meta updated")

    def upload_media(
        self, image_url: str, filename: str, alt_text: str | None = None, caption: str | None = None
    ) -> int:
        """
        Upload media to WordPress media library

        Args:
            image_url: URL of image to upload
            filename: Filename for uploaded image
            alt_text: Alt text for accessibility
            caption: Image caption

        Returns:
            Media attachment ID
        """

        print(f"  → Uploading media: {filename}")

        # Download image
        img_response = requests.get(image_url)
        img_response.raise_for_status()

        # Upload to WordPress
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": img_response.headers.get("Content-Type", "image/webp"),
        }

        response = requests.post(
            f"{self.wp_base}/media",
            data=img_response.content,
            headers=headers,
            auth=self.auth,
            verify=self.verify_ssl,
        )

        if response.status_code == 201:
            media = response.json()
            media_id = media["id"]

            # Update alt text and caption if provided
            if alt_text or caption:
                updates = {}
                if alt_text:
                    updates["alt_text"] = alt_text
                if caption:
                    updates["caption"] = caption

                requests.post(
                    f"{self.wp_base}/media/{media_id}",
                    json=updates,
                    auth=self.auth,
                    verify=self.verify_ssl,
                )

            print(f"    ✓ Media uploaded: ID {media_id}")
            return media_id
        else:
            error_msg = response.json().get("message", "Unknown error")
            raise Exception(f"Media upload failed: {error_msg}")

    def get_product(self, product_id: int) -> dict:
        """Get product details"""

        response = requests.get(
            f"{self.wc_base}/products/{product_id}", auth=self.auth, verify=self.verify_ssl
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Product not found: {product_id}")

    def list_products(
        self,
        per_page: int = 10,
        page: int = 1,
        status: str | None = None,
        category: int | None = None,
    ) -> list[dict]:
        """
        List products with pagination

        Args:
            per_page: Results per page (max 100)
            page: Page number
            status: Filter by status (publish, draft, pending)
            category: Filter by category ID

        Returns:
            List of products
        """

        params = {"per_page": min(per_page, 100), "page": page}

        if status:
            params["status"] = status

        if category:
            params["category"] = category

        response = requests.get(
            f"{self.wc_base}/products", params=params, auth=self.auth, verify=self.verify_ssl
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list products: {response.status_code}")

    def delete_product(self, product_id: int, force: bool = False):
        """
        Delete product

        Args:
            product_id: Product ID
            force: If True, permanently delete. If False, move to trash.
        """

        print(f"  → Deleting product ID: {product_id}")

        params = {"force": force}

        response = requests.delete(
            f"{self.wc_base}/products/{product_id}",
            params=params,
            auth=self.auth,
            verify=self.verify_ssl,
        )

        if response.status_code == 200:
            print("    ✓ Product deleted")
        else:
            raise Exception(f"Product deletion failed: {response.status_code}")

    def create_category(self, name: str, description: str = "") -> dict:
        """Create product category"""

        data = {"name": name, "description": description}

        response = requests.post(
            f"{self.wc_base}/products/categories", json=data, auth=self.auth, verify=self.verify_ssl
        )

        if response.status_code == 201:
            return response.json()
        else:
            # Category might already exist
            if "term_exists" in response.text:
                # Get existing category
                categories = self.list_categories()
                for cat in categories:
                    if cat["name"] == name:
                        return cat

            raise Exception(f"Category creation failed: {response.text}")

    def list_categories(self) -> list[dict]:
        """List all product categories"""

        response = requests.get(
            f"{self.wc_base}/products/categories",
            params={"per_page": 100},
            auth=self.auth,
            verify=self.verify_ssl,
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list categories: {response.status_code}")

    def batch_update_products(self, updates: list[dict]) -> dict:
        """
        Batch update multiple products

        Args:
            updates: List of {id, ...fields to update...}

        Returns:
            Batch operation results
        """

        print(f"  → Batch updating {len(updates)} products")

        batch_data = {"update": updates}

        response = requests.post(
            f"{self.wc_base}/products/batch",
            json=batch_data,
            auth=self.auth,
            verify=self.verify_ssl,
        )

        if response.status_code == 200:
            result = response.json()
            print("    ✓ Batch update complete")
            return result
        else:
            raise Exception(f"Batch update failed: {response.status_code}")


def setup_wordpress_api():
    """
    First-time setup and test for WordPress API
    """

    print("🌹 SkyyRose WordPress API Setup")
    print("=" * 80)

    site_url = input("Enter WordPress URL (e.g., https://skyyrose.co): ")
    username = input("Enter WordPress username: ")
    print("\nGenerate Application Password:")
    print("1. Login to WordPress Admin")
    print("2. Users → Profile")
    print("3. Scroll to 'Application Passwords'")
    print("4. Enter name: 'SkyyRose Automation'")
    print("5. Click 'Add New Application Password'")
    print("6. Copy the generated password\n")
    app_password = input("Enter Application Password: ")

    # Test connection
    wp = WordPressWooCommerceManager(
        site_url=site_url, username=username, app_password=app_password
    )

    # List existing products
    print("\n📦 Existing Products:")
    products = wp.list_products(per_page=5)
    for p in products:
        print(f"  - {p['name']} (${p['price']}) - {p['status']}")

    print("\n✅ WordPress API Setup Complete!")
    print("\nAdd these to your .env file:")
    print(f"WORDPRESS_URL={site_url}")
    print(f"WP_USERNAME={username}")
    print(f"WP_APP_PASSWORD={app_password}")


if __name__ == "__main__":
    setup_wordpress_api()
