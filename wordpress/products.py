"""
WooCommerce Products Module
===========================

Complete WooCommerce product management with:
- Product CRUD operations
- Variable products and variations
- Inventory management
- Category management
- Bulk operations

References:
- WooCommerce REST API: https://woocommerce.github.io/woocommerce-rest-api-docs/
- Products endpoint: https://woocommerce.github.io/woocommerce-rest-api-docs/#products
"""

import builtins
import logging
import os
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ProductStatus(str, Enum):
    """Product status"""

    DRAFT = "draft"
    PENDING = "pending"
    PRIVATE = "private"
    PUBLISH = "publish"


class ProductType(str, Enum):
    """Product type"""

    SIMPLE = "simple"
    GROUPED = "grouped"
    EXTERNAL = "external"
    VARIABLE = "variable"


class StockStatus(str, Enum):
    """Stock status"""

    INSTOCK = "instock"
    OUTOFSTOCK = "outofstock"
    ONBACKORDER = "onbackorder"


class TaxStatus(str, Enum):
    """Tax status"""

    TAXABLE = "taxable"
    SHIPPING = "shipping"
    NONE = "none"


# =============================================================================
# Models
# =============================================================================


class ProductImage(BaseModel):
    """Product image"""

    id: int | None = None
    src: str
    name: str | None = None
    alt: str | None = None
    position: int = 0


class ProductCategory(BaseModel):
    """Product category"""

    id: int
    name: str
    slug: str
    parent: int = 0
    description: str = ""
    display: str = "default"
    image: dict | None = None
    menu_order: int = 0
    count: int = 0


class ProductAttribute(BaseModel):
    """Product attribute"""

    id: int | None = None
    name: str
    position: int = 0
    visible: bool = True
    variation: bool = False
    options: list[str] = []


class ProductVariation(BaseModel):
    """Product variation"""

    id: int | None = None
    sku: str = ""
    price: str = ""
    regular_price: str = ""
    sale_price: str = ""
    stock_status: StockStatus = StockStatus.INSTOCK
    stock_quantity: int | None = None
    manage_stock: bool = False
    attributes: list[dict[str, str]] = []
    image: ProductImage | None = None
    weight: str = ""
    dimensions: dict[str, str] = {}


class Product(BaseModel):
    """WooCommerce product"""

    id: int | None = None
    name: str
    slug: str = ""
    type: ProductType = ProductType.SIMPLE
    status: ProductStatus = ProductStatus.DRAFT
    featured: bool = False
    description: str = ""
    short_description: str = ""
    sku: str = ""
    price: str = ""
    regular_price: str = ""
    sale_price: str = ""
    on_sale: bool = False
    purchasable: bool = True
    total_sales: int = 0
    virtual: bool = False
    downloadable: bool = False
    stock_quantity: int | None = None
    stock_status: StockStatus = StockStatus.INSTOCK
    manage_stock: bool = False
    weight: str = ""
    dimensions: dict[str, str] = {}
    shipping_required: bool = True
    reviews_allowed: bool = True
    average_rating: str = "0"
    rating_count: int = 0
    categories: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    images: list[ProductImage] = []
    attributes: list[ProductAttribute] = []
    variations: list[int] = []
    menu_order: int = 0
    meta_data: list[dict[str, Any]] = []


# =============================================================================
# WooCommerce Products Client
# =============================================================================


class WooCommerceProducts:
    """
    WooCommerce Products API Client

    Usage:
        products = WooCommerceProducts(
            url="https://skyyrose.co",
            consumer_key="ck_xxx",
            consumer_secret="cs_xxx"
        )

        # List products
        all_products = await products.list(per_page=20)

        # Create product
        product = await products.create(
            name="Heart aRose Bomber",
            type=ProductType.VARIABLE,
            regular_price="250.00",
            description="Luxury bomber jacket...",
            categories=[{"id": 15}]
        )

        # Create variation
        variation = await products.create_variation(
            product_id=product.id,
            regular_price="250.00",
            attributes=[{"name": "Size", "option": "M"}]
        )
    """

    def __init__(
        self,
        url: str = None,
        consumer_key: str = None,
        consumer_secret: str = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        self.url = (url or os.getenv("WORDPRESS_URL", "https://skyyrose.co")).rstrip("/")
        self.consumer_key = consumer_key or os.getenv("WOOCOMMERCE_KEY", "")
        self.consumer_secret = consumer_secret or os.getenv("WOOCOMMERCE_SECRET", "")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: httpx.AsyncClient | None = None

        self.base_url = f"{self.url}/wp-json/wc/v3"

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize HTTP client"""
        if self._client is None:
            # WooCommerce uses OAuth 1.0a for HTTP, Basic auth for HTTPS
            auth = (self.consumer_key, self.consumer_secret)

            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
                auth=auth,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "DevSkyy/2.0 WooCommerce-Client",
                },
            )
            logger.info(f"Connected to WooCommerce: {self.url}")

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        params: dict = None,
    ) -> dict | list:
        """Make API request"""
        if self._client is None:
            await self.connect()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        kwargs = {}
        if params:
            kwargs["params"] = params
        if data:
            kwargs["json"] = data

        logger.debug(f"WooCommerce API: {method} {url}")

        response = await self._client.request(method, url, **kwargs)

        if response.status_code >= 400:
            error_data = response.json() if response.text else {}
            message = error_data.get("message", response.text)
            raise Exception(f"WooCommerce API error ({response.status_code}): {message}")

        if response.status_code == 204:
            return {}

        return response.json()

    # -------------------------------------------------------------------------
    # Products CRUD
    # -------------------------------------------------------------------------

    async def list(
        self,
        per_page: int = 10,
        page: int = 1,
        status: ProductStatus = None,
        type: ProductType = None,
        category: int = None,
        tag: int = None,
        sku: str = None,
        search: str = None,
        featured: bool = None,
        on_sale: bool = None,
        min_price: str = None,
        max_price: str = None,
        stock_status: StockStatus = None,
        orderby: str = "date",
        order: str = "desc",
    ) -> list[Product]:
        """List products with filtering"""
        params = {
            "per_page": per_page,
            "page": page,
            "orderby": orderby,
            "order": order,
        }

        if status:
            params["status"] = status.value
        if type:
            params["type"] = type.value
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        if sku:
            params["sku"] = sku
        if search:
            params["search"] = search
        if featured is not None:
            params["featured"] = featured
        if on_sale is not None:
            params["on_sale"] = on_sale
        if min_price:
            params["min_price"] = min_price
        if max_price:
            params["max_price"] = max_price
        if stock_status:
            params["stock_status"] = stock_status.value

        data = await self._request("GET", "/products", params=params)
        return [Product(**p) for p in data]

    async def get(self, product_id: int) -> Product:
        """Get single product"""
        data = await self._request("GET", f"/products/{product_id}")
        return Product(**data)

    async def get_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU"""
        products = await self.list(sku=sku, per_page=1)
        return products[0] if products else None

    async def create(
        self,
        name: str,
        type: ProductType = ProductType.SIMPLE,
        status: ProductStatus = ProductStatus.DRAFT,
        regular_price: str = None,
        sale_price: str = None,
        description: str = "",
        short_description: str = "",
        sku: str = "",
        categories: builtins.list[dict[str, int]] = None,
        tags: builtins.list[dict[str, int]] = None,
        images: builtins.list[dict[str, str]] = None,
        attributes: builtins.list[dict[str, Any]] = None,
        manage_stock: bool = False,
        stock_quantity: int = None,
        stock_status: StockStatus = StockStatus.INSTOCK,
        weight: str = "",
        dimensions: dict[str, str] = None,
        meta_data: builtins.list[dict[str, Any]] = None,
    ) -> Product:
        """Create new product"""
        data = {
            "name": name,
            "type": type.value,
            "status": status.value,
            "description": description,
            "short_description": short_description,
            "manage_stock": manage_stock,
            "stock_status": stock_status.value,
        }

        if regular_price:
            data["regular_price"] = regular_price
        if sale_price:
            data["sale_price"] = sale_price
        if sku:
            data["sku"] = sku
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags
        if images:
            data["images"] = images
        if attributes:
            data["attributes"] = attributes
        if stock_quantity is not None:
            data["stock_quantity"] = stock_quantity
        if weight:
            data["weight"] = weight
        if dimensions:
            data["dimensions"] = dimensions
        if meta_data:
            data["meta_data"] = meta_data

        result = await self._request("POST", "/products", data=data)
        logger.info(f"Created product: {result.get('id')} - {name}")
        return Product(**result)

    async def update(self, product_id: int, **kwargs) -> Product:
        """Update product"""
        # Convert enums to values
        if "status" in kwargs and isinstance(kwargs["status"], ProductStatus):
            kwargs["status"] = kwargs["status"].value
        if "type" in kwargs and isinstance(kwargs["type"], ProductType):
            kwargs["type"] = kwargs["type"].value
        if "stock_status" in kwargs and isinstance(kwargs["stock_status"], StockStatus):
            kwargs["stock_status"] = kwargs["stock_status"].value

        result = await self._request("PUT", f"/products/{product_id}", data=kwargs)
        logger.info(f"Updated product: {product_id}")
        return Product(**result)

    async def delete(self, product_id: int, force: bool = False) -> dict:
        """Delete product"""
        params = {"force": force}
        result = await self._request("DELETE", f"/products/{product_id}", params=params)
        logger.info(f"Deleted product: {product_id}")
        return result

    # -------------------------------------------------------------------------
    # Variations
    # -------------------------------------------------------------------------

    async def list_variations(
        self,
        product_id: int,
        per_page: int = 100,
    ) -> builtins.list[ProductVariation]:
        """List product variations"""
        data = await self._request(
            "GET", f"/products/{product_id}/variations", params={"per_page": per_page}
        )
        return [ProductVariation(**v) for v in data]

    async def get_variation(
        self,
        product_id: int,
        variation_id: int,
    ) -> ProductVariation:
        """Get single variation"""
        data = await self._request("GET", f"/products/{product_id}/variations/{variation_id}")
        return ProductVariation(**data)

    async def create_variation(
        self,
        product_id: int,
        regular_price: str,
        attributes: builtins.list[dict[str, str]],
        sku: str = "",
        sale_price: str = None,
        stock_status: StockStatus = StockStatus.INSTOCK,
        stock_quantity: int = None,
        manage_stock: bool = False,
        weight: str = "",
        dimensions: dict[str, str] = None,
        image: dict[str, str] = None,
    ) -> ProductVariation:
        """Create product variation"""
        data = {
            "regular_price": regular_price,
            "attributes": attributes,
            "stock_status": stock_status.value,
            "manage_stock": manage_stock,
        }

        if sku:
            data["sku"] = sku
        if sale_price:
            data["sale_price"] = sale_price
        if stock_quantity is not None:
            data["stock_quantity"] = stock_quantity
        if weight:
            data["weight"] = weight
        if dimensions:
            data["dimensions"] = dimensions
        if image:
            data["image"] = image

        result = await self._request("POST", f"/products/{product_id}/variations", data=data)
        logger.info(f"Created variation for product {product_id}: {result.get('id')}")
        return ProductVariation(**result)

    async def update_variation(
        self, product_id: int, variation_id: int, **kwargs
    ) -> ProductVariation:
        """Update variation"""
        if "stock_status" in kwargs and isinstance(kwargs["stock_status"], StockStatus):
            kwargs["stock_status"] = kwargs["stock_status"].value

        result = await self._request(
            "PUT", f"/products/{product_id}/variations/{variation_id}", data=kwargs
        )
        return ProductVariation(**result)

    async def delete_variation(
        self,
        product_id: int,
        variation_id: int,
        force: bool = False,
    ) -> dict:
        """Delete variation"""
        return await self._request(
            "DELETE",
            f"/products/{product_id}/variations/{variation_id}",
            params={"force": force},
        )

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    async def list_categories(
        self,
        per_page: int = 100,
        parent: int = None,
    ) -> builtins.list[ProductCategory]:
        """List product categories"""
        params = {"per_page": per_page}
        if parent is not None:
            params["parent"] = parent

        data = await self._request("GET", "/products/categories", params=params)
        return [ProductCategory(**c) for c in data]

    async def get_category(self, category_id: int) -> ProductCategory:
        """Get single category"""
        data = await self._request("GET", f"/products/categories/{category_id}")
        return ProductCategory(**data)

    async def create_category(
        self,
        name: str,
        slug: str = None,
        parent: int = None,
        description: str = "",
        image: dict[str, str] = None,
    ) -> ProductCategory:
        """Create category"""
        data = {"name": name, "description": description}

        if slug:
            data["slug"] = slug
        if parent:
            data["parent"] = parent
        if image:
            data["image"] = image

        result = await self._request("POST", "/products/categories", data=data)
        logger.info(f"Created category: {result.get('id')} - {name}")
        return ProductCategory(**result)

    async def update_category(self, category_id: int, **kwargs) -> ProductCategory:
        """Update category"""
        result = await self._request("PUT", f"/products/categories/{category_id}", data=kwargs)
        return ProductCategory(**result)

    async def delete_category(self, category_id: int, force: bool = False) -> dict:
        """Delete category"""
        return await self._request(
            "DELETE", f"/products/categories/{category_id}", params={"force": force}
        )

    # -------------------------------------------------------------------------
    # Tags
    # -------------------------------------------------------------------------

    async def list_tags(self, per_page: int = 100) -> builtins.list[dict]:
        """List product tags"""
        return await self._request("GET", "/products/tags", params={"per_page": per_page})

    async def create_tag(
        self,
        name: str,
        slug: str = None,
        description: str = "",
    ) -> dict:
        """Create tag"""
        data = {"name": name, "description": description}
        if slug:
            data["slug"] = slug

        return await self._request("POST", "/products/tags", data=data)

    # -------------------------------------------------------------------------
    # Attributes
    # -------------------------------------------------------------------------

    async def list_attributes(self) -> builtins.list[dict]:
        """List product attributes"""
        return await self._request("GET", "/products/attributes")

    async def create_attribute(
        self,
        name: str,
        slug: str = None,
        type: str = "select",
        order_by: str = "menu_order",
        has_archives: bool = False,
    ) -> dict:
        """Create attribute"""
        data = {
            "name": name,
            "type": type,
            "order_by": order_by,
            "has_archives": has_archives,
        }
        if slug:
            data["slug"] = slug

        return await self._request("POST", "/products/attributes", data=data)

    async def list_attribute_terms(
        self,
        attribute_id: int,
        per_page: int = 100,
    ) -> builtins.list[dict]:
        """List attribute terms"""
        return await self._request(
            "GET",
            f"/products/attributes/{attribute_id}/terms",
            params={"per_page": per_page},
        )

    async def create_attribute_term(
        self,
        attribute_id: int,
        name: str,
        slug: str = None,
    ) -> dict:
        """Create attribute term"""
        data = {"name": name}
        if slug:
            data["slug"] = slug

        return await self._request("POST", f"/products/attributes/{attribute_id}/terms", data=data)

    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------

    async def batch_update(
        self,
        create: builtins.list[dict] = None,
        update: builtins.list[dict] = None,
        delete: builtins.list[int] = None,
    ) -> dict:
        """Batch create/update/delete products"""
        data = {}
        if create:
            data["create"] = create
        if update:
            data["update"] = update
        if delete:
            data["delete"] = delete

        return await self._request("POST", "/products/batch", data=data)

    # -------------------------------------------------------------------------
    # Inventory
    # -------------------------------------------------------------------------

    async def update_stock(
        self,
        product_id: int,
        quantity: int,
        status: StockStatus = None,
    ) -> Product:
        """Update product stock"""
        data = {
            "stock_quantity": quantity,
            "manage_stock": True,
        }
        if status:
            data["stock_status"] = status.value

        return await self.update(product_id, **data)

    async def decrease_stock(
        self,
        product_id: int,
        amount: int = 1,
    ) -> Product:
        """Decrease stock by amount"""
        product = await self.get(product_id)
        current = product.stock_quantity or 0
        new_quantity = max(0, current - amount)

        return await self.update_stock(
            product_id,
            new_quantity,
            status=StockStatus.OUTOFSTOCK if new_quantity == 0 else StockStatus.INSTOCK,
        )

    async def increase_stock(
        self,
        product_id: int,
        amount: int = 1,
    ) -> Product:
        """Increase stock by amount"""
        product = await self.get(product_id)
        current = product.stock_quantity or 0
        new_quantity = current + amount

        return await self.update_stock(product_id, new_quantity, status=StockStatus.INSTOCK)

    # -------------------------------------------------------------------------
    # SkyyRose Specific Helpers
    # -------------------------------------------------------------------------

    async def create_skyyrose_product(
        self,
        name: str,
        collection: str,  # "BLACK_ROSE" | "LOVE_HURTS" | "SIGNATURE"
        price: str,
        description: str,
        sizes: builtins.list[str] = None,
        colors: builtins.list[str] = None,
        images: builtins.list[str] = None,
        sku_prefix: str = None,
    ) -> Product:
        """
        Create SkyyRose product with proper structure

        Args:
            name: Product name (e.g., "Heart aRose Bomber")
            collection: Collection name
            price: Regular price
            description: Product description
            sizes: Available sizes ["S", "M", "L", "XL"]
            colors: Available colors ["Onyx", "Ivory"]
            images: Image URLs
            sku_prefix: SKU prefix (auto-generated if not provided)
        """
        # Default sizes for SkyyRose
        sizes = sizes or ["S", "M", "L", "XL", "XXL"]
        colors = colors or ["Onyx"]

        # Generate SKU prefix
        if not sku_prefix:
            # Create from name: "Heart aRose Bomber" -> "HARB"
            words = name.replace("a", "").split()
            sku_prefix = "".join(w[0].upper() for w in words[:4])

        # Collection mapping
        collection_map = {
            "BLACK_ROSE": {"id": 15, "slug": "black-rose"},
            "LOVE_HURTS": {"id": 16, "slug": "love-hurts"},
            "SIGNATURE": {"id": 17, "slug": "signature"},
        }

        category = collection_map.get(collection.upper(), {"id": 17})

        # Determine if variable
        is_variable = len(sizes) > 1 or len(colors) > 1

        # Build attributes
        attributes = []
        if sizes:
            attributes.append(
                {
                    "name": "Size",
                    "visible": True,
                    "variation": True,
                    "options": sizes,
                }
            )
        if colors:
            attributes.append(
                {
                    "name": "Color",
                    "visible": True,
                    "variation": True,
                    "options": colors,
                }
            )

        # Build images
        product_images = []
        if images:
            for i, url in enumerate(images):
                product_images.append(
                    {
                        "src": url,
                        "position": i,
                        "alt": f"{name} - Image {i + 1}",
                    }
                )

        # Create product
        product = await self.create(
            name=name,
            type=ProductType.VARIABLE if is_variable else ProductType.SIMPLE,
            status=ProductStatus.DRAFT,
            regular_price="" if is_variable else price,
            description=description,
            short_description=f"{name} from the {collection.replace('_', ' ').title()} Collection. Where Love Meets Luxury.",
            sku=f"{sku_prefix}-MAIN",
            categories=[{"id": category["id"]}],
            images=product_images,
            attributes=attributes,
            meta_data=[
                {"key": "_skyyrose_collection", "value": collection},
                {"key": "_skyyrose_brand", "value": "SkyyRose"},
            ],
        )

        # Create variations if variable
        if is_variable:
            for color in colors:
                for size in sizes:
                    color_code = color[:3].upper()
                    await self.create_variation(
                        product_id=product.id,
                        regular_price=price,
                        sku=f"{sku_prefix}-{color_code}-{size}",
                        attributes=[
                            {"name": "Size", "option": size},
                            {"name": "Color", "option": color},
                        ],
                        stock_status=StockStatus.INSTOCK,
                    )

        logger.info(f"Created SkyyRose product: {product.id} - {name}")
        return product
