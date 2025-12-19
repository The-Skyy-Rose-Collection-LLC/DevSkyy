# WordPress 3D Media Sync

Sync 3D assets (GLB/USDZ) with WordPress WooCommerce products.

## Overview

The `WordPress3DMediaSync` module enables seamless integration of 3D models with WooCommerce products. It manages custom product meta fields for WebGL models (GLB), AR models (USDZ), AR toggles, and 3D thumbnails.

## Features

- **3D Model Sync**: Attach GLB and USDZ models to products
- **AR Support**: Enable/disable AR viewing per product
- **Thumbnail Management**: Associate preview images with 3D models
- **Bulk Operations**: Sync multiple products in parallel
- **Error Handling**: Comprehensive validation and error recovery
- **Cleanup Tools**: Remove orphaned 3D assets
- **Async/Await**: Built on modern async Python with aiohttp

## Installation

```bash
pip install aiohttp structlog
```

## Quick Start

```python
import asyncio
from wordpress import WordPress3DMediaSync

async def main():
    # Initialize sync client
    sync = WordPress3DMediaSync(
        wp_url="https://skyyrose.com",
        username="admin",
        app_password="xxxx xxxx xxxx xxxx",
    )

    async with sync:
        # Sync 3D model to product
        result = await sync.sync_3d_model(
            product_id=123,
            glb_url="https://cdn.skyyrose.com/models/product.glb",
            usdz_url="https://cdn.skyyrose.com/models/product.usdz",
            thumbnail_url="https://cdn.skyyrose.com/thumbs/product.jpg",
        )

        print(f"Synced: {result['name']}")

asyncio.run(main())
```

## Custom Meta Fields

The module manages four custom WooCommerce product meta fields:

| Field Name | Type | Description |
|------------|------|-------------|
| `_skyyrose_glb_url` | string | WebGL model URL (GLB format) |
| `_skyyrose_usdz_url` | string | AR model URL (USDZ format for iOS) |
| `_skyyrose_ar_enabled` | boolean | Toggle AR viewing |
| `_skyyrose_3d_thumbnail` | string | Preview image URL |

## API Reference

### `WordPress3DMediaSync`

#### Constructor

```python
sync = WordPress3DMediaSync(
    wp_url: str,           # WordPress site URL
    username: str,         # WordPress username
    app_password: str,     # WordPress application password
    config: WordPress3DConfig | None = None,
)
```

#### Methods

##### `sync_3d_model()`

Sync 3D model to WooCommerce product.

```python
result = await sync.sync_3d_model(
    product_id: int,              # WooCommerce product ID
    glb_url: str,                 # WebGL model URL (required)
    usdz_url: str | None = None,  # AR model URL (optional)
    thumbnail_url: str | None = None,  # Preview image URL (optional)
) -> dict[str, Any]
```

**Returns:** Updated product data with meta fields

**Raises:**
- `ProductNotFoundError`: Product doesn't exist
- `InvalidAssetURLError`: Invalid URL format
- `WordPress3DSyncError`: Sync operation failed

**Example:**

```python
result = await sync.sync_3d_model(
    product_id=123,
    glb_url="https://cdn.skyyrose.com/models/rose-earrings.glb",
    usdz_url="https://cdn.skyyrose.com/models/rose-earrings.usdz",
    thumbnail_url="https://cdn.skyyrose.com/thumbs/rose-earrings.jpg",
)
```

##### `enable_ar()`

Enable or disable AR for product.

```python
result = await sync.enable_ar(
    product_id: int,       # WooCommerce product ID
    enabled: bool = True,  # Enable AR (default: True)
) -> dict[str, Any]
```

**Returns:** Updated product data

**Example:**

```python
# Enable AR
await sync.enable_ar(product_id=123, enabled=True)

# Disable AR
await sync.enable_ar(product_id=123, enabled=False)
```

##### `get_3d_assets()`

Get 3D assets for product.

```python
assets = await sync.get_3d_assets(
    product_id: int,  # WooCommerce product ID
) -> dict[str, Any]
```

**Returns:**

```python
{
    "product_id": 123,
    "product_name": "Rose Earrings",
    "glb_url": "https://...",
    "usdz_url": "https://..." or None,
    "ar_enabled": True/False,
    "thumbnail_url": "https://..." or None,
}
```

**Example:**

```python
assets = await sync.get_3d_assets(product_id=123)
print(f"GLB: {assets['glb_url']}")
print(f"USDZ: {assets['usdz_url']}")
print(f"AR Enabled: {assets['ar_enabled']}")
```

##### `bulk_sync()`

Bulk sync 3D models to multiple products.

```python
results = await sync.bulk_sync(
    products: list[dict],  # List of product configs
) -> list[dict]
```

**Product Config:**

```python
{
    "product_id": 123,
    "glb_url": "https://...",
    "usdz_url": "https://..." (optional),
    "thumbnail_url": "https://..." (optional),
}
```

**Returns:**

```python
[
    {
        "product_id": 123,
        "status": "success",  # or "failed"
        "data": {...},        # if success
        "error": "...",       # if failed
    },
    ...
]
```

**Example:**

```python
products = [
    {
        "product_id": 123,
        "glb_url": "https://cdn.skyyrose.com/models/product-123.glb",
    },
    {
        "product_id": 124,
        "glb_url": "https://cdn.skyyrose.com/models/product-124.glb",
        "usdz_url": "https://cdn.skyyrose.com/models/product-124.usdz",
    },
]

results = await sync.bulk_sync(products)
success_count = sum(1 for r in results if r["status"] == "success")
print(f"Synced {success_count}/{len(products)} products")
```

##### `cleanup_orphaned_assets()`

Cleanup orphaned 3D assets.

Removes 3D meta fields from products with missing or invalid GLB URLs.

```python
count = await sync.cleanup_orphaned_assets() -> int
```

**Returns:** Number of products cleaned up

**Example:**

```python
count = await sync.cleanup_orphaned_assets()
print(f"Cleaned up {count} products")
```

## Configuration

### Environment Variables

```bash
# WordPress credentials
export WP_SITE_URL="https://skyyrose.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

### Custom Configuration

```python
from wordpress import WordPress3DConfig

config = WordPress3DConfig(
    wp_url="https://skyyrose.com",
    username="admin",
    app_password="xxxx xxxx xxxx xxxx",
    api_version="wc/v3",      # WooCommerce API version
    timeout=30.0,             # Request timeout (seconds)
    max_retries=3,            # Max retry attempts
    verify_ssl=True,          # SSL verification
)

sync = WordPress3DMediaSync(
    wp_url=config.wp_url,
    username=config.username,
    app_password=config.app_password,
    config=config,
)
```

## Error Handling

```python
from wordpress import (
    WordPress3DSyncError,
    ProductNotFoundError,
    InvalidAssetURLError,
)

async with sync:
    try:
        result = await sync.sync_3d_model(
            product_id=123,
            glb_url="https://cdn.skyyrose.com/models/product.glb",
        )
    except ProductNotFoundError as e:
        print(f"Product not found: {e.product_id}")
    except InvalidAssetURLError as e:
        print(f"Invalid URL: {e}")
    except WordPress3DSyncError as e:
        print(f"Sync failed: {e}")
```

## Logging

The module uses `structlog` for structured logging. Configure logging in your application:

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)
```

**Log Events:**

- `connected`: Session established
- `disconnected`: Session closed
- `sync_3d_model_start`: Starting model sync
- `sync_3d_model_success`: Model sync completed
- `sync_3d_model_failed`: Model sync failed
- `enable_ar`: AR toggle changed
- `get_3d_assets`: Retrieved assets
- `bulk_sync_start`: Bulk operation started
- `bulk_sync_complete`: Bulk operation finished
- `cleanup_orphaned_assets_start`: Cleanup started
- `cleanup_orphaned_assets_complete`: Cleanup finished

## Integration with Asset Pipeline

Integrate with DevSkyy's automated 3D asset generation:

```python
from orchestration import AssetPipeline
from wordpress import WordPress3DMediaSync

async def generate_and_sync(product_id: int, description: str):
    # Generate 3D assets
    pipeline = AssetPipeline()
    assets = await pipeline.generate_3d_asset(
        description=description,
        format="glb",
    )

    # Sync to WordPress
    sync = WordPress3DMediaSync(...)
    async with sync:
        await sync.sync_3d_model(
            product_id=product_id,
            glb_url=assets["glb_url"],
            usdz_url=assets.get("usdz_url"),
            thumbnail_url=assets.get("thumbnail_url"),
        )
```

## WordPress Setup

### Generate Application Password

1. Login to WordPress admin
2. Navigate to **Users** → **Profile**
3. Scroll to **Application Passwords**
4. Enter name: "DevSkyy 3D Sync"
5. Click **Add New Application Password**
6. Copy the generated password (format: `xxxx xxxx xxxx xxxx`)

### WooCommerce API Access

Ensure WooCommerce REST API is enabled:

1. **WooCommerce** → **Settings** → **Advanced** → **REST API**
2. Click **Add key**
3. Description: "DevSkyy 3D Sync"
4. User: Your admin user
5. Permissions: **Read/Write**
6. Click **Generate API Key**

## Frontend Integration

### Model Viewer

Display 3D models on product pages:

```html
<model-viewer
    src="{{ product.meta._skyyrose_glb_url }}"
    ios-src="{{ product.meta._skyyrose_usdz_url }}"
    poster="{{ product.meta._skyyrose_3d_thumbnail }}"
    ar
    ar-modes="webxr scene-viewer quick-look"
    camera-controls
    auto-rotate
></model-viewer>
```

### AR Quick Look (iOS)

```html
{% if product.meta._skyyrose_ar_enabled %}
<a href="{{ product.meta._skyyrose_usdz_url }}" rel="ar">
    <img src="/images/ar-icon.png" alt="View in AR">
</a>
{% endif %}
```

## Performance

- **Bulk Sync**: Processes 5 products in parallel (configurable via semaphore)
- **Retry Logic**: Exponential backoff (1s, 2s, 4s)
- **Timeout**: 30 seconds per request (configurable)
- **Connection Pooling**: Single session reused for all requests

## Best Practices

1. **Always use async context manager**: Ensures proper cleanup
   ```python
   async with sync:
       await sync.sync_3d_model(...)
   ```

2. **Validate URLs before sync**: Catch errors early
   ```python
   if not glb_url.startswith("https://"):
       raise ValueError("Must use HTTPS")
   ```

3. **Use bulk operations**: More efficient than individual syncs
   ```python
   await sync.bulk_sync(products)  # Better than loop
   ```

4. **Handle errors gracefully**: Don't fail entire batch on single error
   ```python
   results = await sync.bulk_sync(products)
   for result in results:
       if result["status"] == "failed":
           logger.error(f"Failed: {result['product_id']}")
   ```

5. **Regular cleanup**: Remove orphaned assets monthly
   ```python
   # Cron job: 0 0 1 * *
   await sync.cleanup_orphaned_assets()
   ```

## Troubleshooting

### Authentication Errors

**Problem:** `401 Unauthorized`

**Solution:**
- Verify application password is correct
- Ensure user has admin/shop_manager role
- Check WooCommerce API is enabled

### SSL Verification Errors

**Problem:** SSL certificate errors

**Solution:**
```python
config = WordPress3DConfig(..., verify_ssl=False)  # Development only!
```

### Timeout Errors

**Problem:** Requests timing out

**Solution:**
```python
config = WordPress3DConfig(..., timeout=60.0)  # Increase timeout
```

### Invalid URLs

**Problem:** `InvalidAssetURLError`

**Solution:**
- Ensure URLs use `https://` protocol
- Verify file extensions (`.glb`, `.usdz`)
- Check URLs are publicly accessible

## Examples

See `/examples/wordpress_3d_sync_demo.py` for comprehensive examples:

```bash
python examples/wordpress_3d_sync_demo.py
```

## License

Part of the DevSkyy Platform.

## Support

For issues or questions, contact the DevSkyy Platform Team.
