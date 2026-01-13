# WordPress/WooCommerce Integration

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2026-01-06

---

## Overview

Complete production-grade integration between DevSkyy backend and WordPress/WooCommerce.

**Capabilities**:
- WooCommerce product management (CRUD)
- Order processing and fulfillment
- Customer management
- Content publishing to WordPress
- Commerce Agent integration
- OAuth 1.0a authentication
- Async/await with connection pooling
- Automatic retries and error handling

---

## Architecture

```
DevSkyy Backend
├── integrations/wordpress_client.py    # Core WordPress/WooCommerce client
├── api/v1/wordpress.py                 # REST API endpoints
├── agents/commerce_agent.py            # Commerce Agent with WP integration
└── tests/test_wordpress_integration.py # Comprehensive test suite
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# WordPress Site
WORDPRESS_URL=https://skyyrose.co

# WooCommerce OAuth 1.0a Credentials
# Get from: WooCommerce → Settings → Advanced → REST API
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...

# WordPress Application Password (for posts/pages)
# Get from: WordPress Admin → Users → Profile → Application Passwords
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### Get WooCommerce API Credentials

1. Login to WordPress Admin
2. Navigate to **WooCommerce → Settings → Advanced → REST API**
3. Click **Add Key**
4. Set:
   - Description: `DevSkyy Backend`
   - User: Select admin user
   - Permissions: `Read/Write`
5. Click **Generate API Key**
6. Copy **Consumer key** and **Consumer secret** (shown only once!)

---

## WordPress/WooCommerce Client

### Features

- **OAuth 1.0a Signature Generation**: Proper WooCommerce authentication
- **Connection Pooling**: Efficient HTTP connection reuse
- **Automatic Retries**: Exponential backoff for failed requests
- **Rate Limit Handling**: Automatic retry after rate limit hit
- **Type Safety**: Full Pydantic models for all data
- **Async/Await**: Non-blocking I/O for all operations

### Basic Usage

```python
from integrations.wordpress_client import WordPressWooCommerceClient, WooCommerceProduct, ProductStatus

# Using context manager (recommended)
async with WordPressWooCommerceClient() as client:
    # List products
    products = await client.list_products(per_page=10, status=ProductStatus.PUBLISH)

    # Create product
    product = WooCommerceProduct(
        name="BLACK ROSE Hoodie",
        regular_price="189.99",
        description="Premium luxury hoodie",
        sku="BR-HOOD-001",
        status=ProductStatus.DRAFT,
        stock_quantity=50,
    )
    created = await client.create_product(product)

    # Update product
    updated = await client.update_product(
        created.id,
        {"stock_quantity": 45}
    )

    # List orders
    orders = await client.list_orders(status=OrderStatus.PROCESSING)
```

### Available Methods

#### Products
- `list_products(per_page, page, status, category, search, sku)`
- `get_product(product_id)`
- `create_product(product)`
- `update_product(product_id, updates)`
- `delete_product(product_id, force)`

#### Orders
- `list_orders(per_page, page, status, customer, after, before)`
- `get_order(order_id)`
- `update_order_status(order_id, status)`

#### Customers
- `list_customers(per_page, page, search, email)`

#### WordPress Content
- `list_posts(per_page, page, status, search)`
- `create_post(title, content, status, **kwargs)`

#### Health
- `test_connection()` - Verify API connectivity

---

## REST API Endpoints

All endpoints require JWT authentication (except `/test-connection`).

### Products

#### List Products
```http
GET /api/v1/wordpress/products?per_page=10&status=publish
Authorization: Bearer <token>
```

#### Get Product
```http
GET /api/v1/wordpress/products/{product_id}
Authorization: Bearer <token>
```

#### Create Product
```http
POST /api/v1/wordpress/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "BLACK ROSE Hoodie",
  "regular_price": "189.99",
  "description": "Premium luxury hoodie",
  "short_description": "Dark elegance meets streetwear",
  "sku": "BR-HOOD-001",
  "status": "draft",
  "stock_quantity": 50,
  "categories": [{"name": "BLACK ROSE"}, {"name": "Hoodies"}],
  "tags": [{"name": "luxury"}, {"name": "streetwear"}],
  "images": [{"src": "https://example.com/image.jpg"}]
}
```

#### Update Product
```http
PUT /api/v1/wordpress/products/{product_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "regular_price": "169.99",
  "stock_quantity": 45
}
```

#### Delete Product
```http
DELETE /api/v1/wordpress/products/{product_id}?force=false
Authorization: Bearer <token>
```

### Orders

#### List Orders
```http
GET /api/v1/wordpress/orders?status=processing&per_page=10
Authorization: Bearer <token>
```

#### Get Order
```http
GET /api/v1/wordpress/orders/{order_id}
Authorization: Bearer <token>
```

#### Update Order Status
```http
PUT /api/v1/wordpress/orders/{order_id}/status?new_status=completed
Authorization: Bearer <token>
```

### Sync

#### Sync Products from WooCommerce
```http
POST /api/v1/wordpress/sync
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "publish",
  "limit": 100
}
```

### Content Publishing

#### Publish to WordPress
```http
POST /api/v1/wordpress/publish
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Collection Launch",
  "content": "<h1>BLACK ROSE Collection</h1><p>...</p>",
  "type": "post",
  "status": "publish",
  "categories": [1, 5],
  "tags": [10, 15]
}
```

### Health

#### Test Connection
```http
GET /api/v1/wordpress/test-connection
```

No authentication required. Returns:
```json
{
  "connected": true,
  "site_url": "https://skyyrose.co",
  "woocommerce_api": true,
  "wordpress_api": true,
  "products_count": 42
}
```

---

## Commerce Agent Integration

The Commerce Agent now has full WordPress/WooCommerce integration.

### Usage

```python
from agents.commerce_agent import CommerceAgent

agent = CommerceAgent()

# Sync product to WooCommerce
result = await agent.sync_product_to_woocommerce(
    name="BLACK ROSE Hoodie",
    price=189.99,
    description="Premium luxury hoodie",
    short_description="Dark elegance meets streetwear",
    sku="BR-HOOD-001",
    stock_quantity=50,
    status="publish",
    categories=["BLACK ROSE", "Hoodies"],
    tags=["luxury", "streetwear"],
    images=["https://example.com/hoodie.jpg"],
)

# Get product from WooCommerce
product = await agent.get_woocommerce_product(product_id=123)

# Update product in WooCommerce
updated = await agent.update_woocommerce_product(
    product_id=123,
    updates={"stock_quantity": 45}
)

# Sync orders from WooCommerce
orders = await agent.sync_orders_from_woocommerce(
    status="processing",
    limit=10
)

# Update order status in WooCommerce
result = await agent.update_order_status_in_woocommerce(
    order_id=456,
    status="completed"
)
```

---

## Testing

### Unit Tests

Run the full test suite:

```bash
pytest tests/test_wordpress_integration.py -v
```

Run specific test class:

```bash
pytest tests/test_wordpress_integration.py::TestProducts -v
```

### Integration Tests

Integration tests require real WooCommerce credentials:

```bash
# Set environment variables
export WORDPRESS_URL=https://skyyrose.co
export WOOCOMMERCE_KEY=ck_...
export WOOCOMMERCE_SECRET=cs_...

# Run integration tests
pytest tests/test_wordpress_integration.py -v -m integration
```

### Manual Connection Test

Quick script to verify connectivity:

```bash
python scripts/test_woocommerce_connection.py
```

This will:
1. Test API connection
2. List sample products
3. List recent orders
4. Optionally create/delete a test product

---

## Error Handling

The client provides specific exception types:

```python
from integrations.wordpress_client import (
    WordPressError,           # Base exception
    AuthenticationError,      # 401 auth failed
    NotFoundError,           # 404 not found
    RateLimitError,          # 429 rate limit
    ValidationError,         # Validation failed
)

try:
    product = await client.get_product(12345)
except NotFoundError as e:
    print(f"Product not found: {e}")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except WordPressError as e:
    print(f"Error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response_data}")
```

---

## Data Models

### WooCommerceProduct

```python
class WooCommerceProduct(BaseModel):
    id: int | None
    name: str
    type: str = "simple"
    status: ProductStatus
    regular_price: str
    sale_price: str | None
    description: str
    short_description: str
    sku: str | None
    manage_stock: bool = True
    stock_quantity: int | None
    stock_status: Literal["instock", "outofstock", "onbackorder"]
    categories: list[dict]
    tags: list[dict]
    images: list[dict]
    attributes: list[dict]
    meta_data: list[dict]
    permalink: str | None
```

### WooCommerceOrder

```python
class WooCommerceOrder(BaseModel):
    id: int
    status: OrderStatus
    currency: str
    total: str
    customer_id: int
    billing: dict
    shipping: dict
    line_items: list[dict]
    shipping_lines: list[dict]
    meta_data: list[dict]
    date_created: str
    date_modified: str
```

### Enums

```python
class ProductStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PRIVATE = "private"
    PUBLISH = "publish"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"
```

---

## Performance Considerations

### Connection Pooling

The client maintains a connection pool:
- Max 100 concurrent connections
- Max 10 connections per host
- DNS cache TTL: 300 seconds

### Rate Limiting

WooCommerce API has rate limits:
- Free/Basic: 25 requests per minute
- Plus: 60 requests per minute
- Premium: 120 requests per minute

The client automatically handles 429 responses with retry-after.

### Retries

Failed requests are retried with exponential backoff:
- Max retries: 3 (configurable)
- Backoff: 2^attempt seconds (1s, 2s, 4s)

---

## Security

### OAuth 1.0a Signature

The client implements proper OAuth 1.0a signature generation:

1. Timestamp + Nonce generation
2. Parameter normalization
3. Base string construction
4. HMAC-SHA256 signature
5. Base64 encoding

### SSL/TLS

All connections use HTTPS with SSL verification enabled by default.

Disable only for local development:

```python
config = WordPressConfig(
    site_url="https://localhost",
    verify_ssl=False  # Only for dev!
)
```

### Credential Management

**Never commit credentials!**

Use environment variables or secrets manager:
- `.env` for local development
- AWS Secrets Manager / HashiCorp Vault for production

---

## Troubleshooting

### Authentication Failures

**Error**: `AuthenticationError: Authentication failed (401)`

**Solutions**:
1. Verify WooCommerce API credentials are correct
2. Check user has proper permissions (Read/Write)
3. Ensure OAuth signature is correct
4. Verify site URL matches exactly (no trailing slashes)

### Rate Limiting

**Error**: `RateLimitError: Rate limit exceeded (429)`

**Solutions**:
1. Implement request throttling in your application
2. Upgrade WooCommerce plan for higher limits
3. Use batch operations where possible
4. Cache frequently accessed data

### SSL Certificate Errors

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:
1. Check site has valid SSL certificate
2. Update system CA certificates
3. For self-signed certs (dev only): `verify_ssl=False`

### Connection Timeouts

**Error**: `asyncio.TimeoutError`

**Solutions**:
1. Increase timeout: `timeout=60.0`
2. Check network connectivity
3. Verify WordPress site is accessible
4. Check for firewall/proxy issues

---

## Future Enhancements

### Planned Features

- [ ] Webhook handler for real-time sync
- [ ] Batch operations for bulk updates
- [ ] Product variant management
- [ ] Advanced order fulfillment workflows
- [ ] Inventory sync automation
- [ ] WooCommerce Analytics integration
- [ ] WordPress Gutenberg block generation
- [ ] Multi-site support

---

## References

- [WooCommerce REST API Documentation](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [OAuth 1.0a Specification](https://oauth.net/core/1.0a/)

---

## Support

For issues or questions:

- **Internal**: DevSkyy Platform Team
- **Email**: support@skyyrose.com
- **Documentation**: `/docs/WORDPRESS_INTEGRATION.md`

---

**Version**: 1.0.0
**Last Updated**: 2026-01-06
**Status**: ✅ Production Ready
