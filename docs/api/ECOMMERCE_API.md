# E-Commerce API Documentation

Complete API reference for SkyyRose e-commerce functionality, including cart management, checkout, WooCommerce synchronization, and Stripe integration.

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Cart API](#cart-api)
4. [Checkout API](#checkout-api)
5. [WooCommerce Sync](#woocommerce-sync)
6. [Stripe Integration](#stripe-integration)
7. [Error Handling](#error-handling)
8. [Webhooks](#webhooks)

---

## Authentication

All API endpoints require JWT authentication via the `Authorization` header.

```http
Authorization: Bearer <jwt_token>
```

### Getting a Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### Refreshing a Token

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## Rate Limiting

Rate limits are enforced per user and per IP address.

| Endpoint Category | Rate Limit | Window |
|------------------|------------|---------|
| Cart Operations | 100 requests | 1 minute |
| Checkout | 10 requests | 1 minute |
| Product Sync | 50 requests | 1 minute |
| Webhooks | 1000 requests | 1 minute |

**Rate Limit Headers:**

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703001600
```

**Rate Limit Exceeded Response:**

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please retry after 60 seconds.",
  "retry_after": 60
}
```

---

## Cart API

### Get Cart

Retrieve the current user's cart or a guest cart by session ID.

```bash
GET /api/cart
GET /api/cart?session_id=<session_id>  # For guest carts
Authorization: Bearer <token>  # Optional for guest carts
```

**Response:**

```json
{
  "cart_id": "cart_123456",
  "user_id": "user_789",
  "session_id": "sess_abc123",
  "items": [
    {
      "product_id": "prod_rose_001",
      "variant_id": "var_black_rose",
      "name": "Black Rose - Limited Edition",
      "price": 299.99,
      "quantity": 1,
      "image_url": "https://cdn.skyyrose.com/products/black-rose.jpg",
      "metadata": {
        "collection": "Black Rose Collection",
        "size": "Standard",
        "color": "Midnight Black"
      }
    }
  ],
  "subtotal": 299.99,
  "tax": 29.99,
  "shipping": 15.00,
  "total": 344.98,
  "currency": "USD",
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:15:00Z"
}
```

---

### Add Item to Cart

Add a product to the cart from a Three.js experience or standard interface.

```bash
POST /api/cart/items
Content-Type: application/json
Authorization: Bearer <token>

{
  "product_id": "prod_signature_002",
  "variant_id": "var_signature_gold",
  "quantity": 2,
  "metadata": {
    "source": "3d_experience",
    "scene": "signature_collection",
    "interaction": "product_hotspot_click"
  }
}
```

**Response:**

```json
{
  "success": true,
  "cart": {
    "cart_id": "cart_123456",
    "items": [...],
    "total": 644.98
  },
  "added_item": {
    "product_id": "prod_signature_002",
    "quantity": 2,
    "price": 150.00
  }
}
```

**Error Response (Out of Stock):**

```json
{
  "error": "insufficient_inventory",
  "message": "Only 1 item available in stock",
  "available_quantity": 1,
  "requested_quantity": 2
}
```

---

### Update Cart Item

Update the quantity of an item in the cart.

```bash
PATCH /api/cart/items/<item_id>
Content-Type: application/json
Authorization: Bearer <token>

{
  "quantity": 3
}
```

**Response:**

```json
{
  "success": true,
  "cart": {
    "cart_id": "cart_123456",
    "items": [...],
    "total": 944.97
  },
  "updated_item": {
    "item_id": "item_abc123",
    "product_id": "prod_signature_002",
    "quantity": 3
  }
}
```

---

### Remove Cart Item

Remove an item from the cart.

```bash
DELETE /api/cart/items/<item_id>
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "cart": {
    "cart_id": "cart_123456",
    "items": [...],
    "total": 344.98
  },
  "removed_item_id": "item_abc123"
}
```

---

### Clear Cart

Remove all items from the cart.

```bash
DELETE /api/cart
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "message": "Cart cleared successfully",
  "cart": {
    "cart_id": "cart_123456",
    "items": [],
    "total": 0.00
  }
}
```

---

## Checkout API

### Create Checkout Session

Initiate a Stripe Checkout session (redirect or embedded).

```bash
POST /api/checkout/session
Content-Type: application/json
Authorization: Bearer <token>

{
  "mode": "embedded",  # or "redirect"
  "success_url": "https://skyyrose.com/order/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://skyyrose.com/cart",
  "metadata": {
    "source": "3d_experience",
    "collection": "black_rose"
  }
}
```

**Response (Redirect Mode):**

```json
{
  "session_id": "cs_test_abc123",
  "url": "https://checkout.stripe.com/c/pay/cs_test_abc123#fidkdWxOYH...",
  "expires_at": "2025-12-19T11:00:00Z"
}
```

**Response (Embedded Mode):**

```json
{
  "session_id": "cs_test_abc123",
  "client_secret": "cs_test_abc123_secret_xyz789",
  "publishable_key": "pk_test_51...",
  "expires_at": "2025-12-19T11:00:00Z"
}
```

---

### Get Checkout Session Status

Retrieve the status of a checkout session.

```bash
GET /api/checkout/session/<session_id>
Authorization: Bearer <token>
```

**Response:**

```json
{
  "session_id": "cs_test_abc123",
  "status": "complete",  # or "open", "expired"
  "payment_status": "paid",  # or "unpaid", "no_payment_required"
  "amount_total": 34498,
  "currency": "usd",
  "customer_email": "customer@example.com",
  "order_id": "order_xyz789",
  "metadata": {
    "source": "3d_experience",
    "collection": "black_rose"
  }
}
```

---

### Create Payment Intent (Custom Flow)

For custom payment flows that don't use Stripe Checkout.

```bash
POST /api/checkout/payment-intent
Content-Type: application/json
Authorization: Bearer <token>

{
  "amount": 34498,
  "currency": "usd",
  "payment_method_types": ["card"],
  "metadata": {
    "cart_id": "cart_123456",
    "source": "3d_experience"
  }
}
```

**Response:**

```json
{
  "payment_intent_id": "pi_test_abc123",
  "client_secret": "pi_test_abc123_secret_xyz789",
  "amount": 34498,
  "currency": "usd",
  "status": "requires_payment_method"
}
```

---

## WooCommerce Sync

### Sync Product to WooCommerce

Synchronize a product from the platform to WooCommerce.

```bash
POST /api/woocommerce/products/sync
Content-Type: application/json
Authorization: Bearer <token>

{
  "product_id": "prod_rose_001",
  "sync_inventory": true,
  "sync_images": true,
  "sync_metadata": true
}
```

**Response:**

```json
{
  "success": true,
  "woocommerce_product_id": 12345,
  "product_id": "prod_rose_001",
  "synced_fields": [
    "name",
    "description",
    "price",
    "inventory",
    "images",
    "metadata"
  ],
  "sync_timestamp": "2025-12-19T10:30:00Z"
}
```

---

### Sync Inventory

Update inventory levels between platform and WooCommerce.

```bash
POST /api/woocommerce/inventory/sync
Content-Type: application/json
Authorization: Bearer <token>

{
  "product_id": "prod_rose_001",
  "variant_id": "var_black_rose",
  "quantity": 50,
  "sync_direction": "to_woocommerce"  # or "from_woocommerce", "bidirectional"
}
```

**Response:**

```json
{
  "success": true,
  "product_id": "prod_rose_001",
  "variant_id": "var_black_rose",
  "platform_quantity": 50,
  "woocommerce_quantity": 50,
  "sync_direction": "to_woocommerce",
  "sync_timestamp": "2025-12-19T10:35:00Z"
}
```

---

### Create Order in WooCommerce

Create an order in WooCommerce after successful payment.

```bash
POST /api/woocommerce/orders
Content-Type: application/json
Authorization: Bearer <token>

{
  "stripe_session_id": "cs_test_abc123",
  "cart_id": "cart_123456",
  "customer": {
    "email": "customer@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone": "+1234567890"
  },
  "shipping": {
    "address_1": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "postcode": "90001",
    "country": "US"
  }
}
```

**Response:**

```json
{
  "success": true,
  "woocommerce_order_id": 98765,
  "order_number": "SKY-2025-001",
  "status": "processing",
  "total": "344.98",
  "currency": "USD",
  "order_url": "https://skyyrose.com/wp-admin/post.php?post=98765&action=edit",
  "created_at": "2025-12-19T10:40:00Z"
}
```

---

## Stripe Integration

### Webhook Events

Stripe webhooks are handled at `/api/webhooks/stripe`.

**Supported Events:**

- `checkout.session.completed`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`

**Webhook Signature Verification:**

All webhook requests are verified using Stripe's webhook signature:

```python
stripe.Webhook.construct_event(
    payload, signature, endpoint_secret
)
```

---

### Webhook: checkout.session.completed

Fired when a customer completes a Stripe Checkout session.

**Webhook Payload:**

```json
{
  "id": "evt_abc123",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_abc123",
      "amount_total": 34498,
      "currency": "usd",
      "customer_email": "customer@example.com",
      "payment_status": "paid",
      "metadata": {
        "cart_id": "cart_123456",
        "user_id": "user_789",
        "source": "3d_experience"
      }
    }
  }
}
```

**Automated Actions:**

1. Create order in database
2. Sync order to WooCommerce
3. Update inventory
4. Send confirmation email
5. Clear user's cart

---

### Webhook: payment_intent.payment_failed

Fired when a payment fails.

**Webhook Payload:**

```json
{
  "id": "evt_xyz789",
  "type": "payment_intent.payment_failed",
  "data": {
    "object": {
      "id": "pi_test_abc123",
      "amount": 34498,
      "currency": "usd",
      "last_payment_error": {
        "message": "Your card was declined.",
        "code": "card_declined"
      },
      "metadata": {
        "cart_id": "cart_123456",
        "user_id": "user_789"
      }
    }
  }
}
```

**Automated Actions:**

1. Log payment failure
2. Notify user via email
3. Preserve cart for retry
4. Update analytics

---

## Error Handling

All API errors follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "request_id": "req_abc123",
  "timestamp": "2025-12-19T10:00:00Z"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `authentication_required` | 401 | Missing or invalid JWT token |
| `rate_limit_exceeded` | 429 | Too many requests |
| `insufficient_inventory` | 400 | Product out of stock |
| `cart_not_found` | 404 | Cart does not exist |
| `invalid_product` | 400 | Product ID invalid or discontinued |
| `payment_failed` | 402 | Payment processing failed |
| `woocommerce_sync_failed` | 500 | WooCommerce sync error |
| `webhook_verification_failed` | 400 | Invalid webhook signature |

---

## Best Practices

### Performance Optimization

1. **Cart Persistence**: Use localStorage for guest carts to minimize API calls
2. **Debouncing**: Debounce quantity updates to reduce API traffic
3. **Caching**: Cache product data for 5 minutes
4. **Batch Operations**: Use batch endpoints when syncing multiple products

### Security

1. **HTTPS Only**: All API requests must use HTTPS
2. **Token Expiration**: JWT tokens expire after 1 hour
3. **Webhook Verification**: Always verify Stripe webhook signatures
4. **Rate Limiting**: Implement client-side rate limiting to avoid 429 errors

### Error Recovery

1. **Retry Logic**: Implement exponential backoff for failed requests
2. **Cart Recovery**: Save cart state before checkout to allow recovery
3. **Idempotency**: Use idempotency keys for payment operations
4. **Graceful Degradation**: Show cached data when API is unavailable

---

## Code Examples

### JavaScript: Add to Cart from Three.js Scene

```javascript
import { addToCart } from '@/lib/ecommerce/cart';

async function handleProductClick(productId, variantId) {
  try {
    const result = await addToCart({
      product_id: productId,
      variant_id: variantId,
      quantity: 1,
      metadata: {
        source: '3d_experience',
        scene: 'black_rose_collection',
        interaction: 'product_hotspot_click'
      }
    });

    console.log('Added to cart:', result.added_item);
    // Update UI to show cart count
    updateCartBadge(result.cart.items.length);
  } catch (error) {
    if (error.code === 'insufficient_inventory') {
      alert(`Only ${error.available_quantity} available`);
    } else {
      console.error('Failed to add to cart:', error);
    }
  }
}
```

### Python: Sync Product to WooCommerce

```python
from runtime.tools import sync_product_to_woocommerce

async def sync_all_products():
    """Sync all products to WooCommerce."""
    products = await get_all_products()

    for product in products:
        try:
            result = await sync_product_to_woocommerce(
                product_id=product.id,
                sync_inventory=True,
                sync_images=True
            )
            print(f"Synced {product.name}: WooCommerce ID {result['woocommerce_product_id']}")
        except Exception as e:
            print(f"Failed to sync {product.name}: {e}")
```

---

## API Versioning

Current version: `v1`

All endpoints are prefixed with `/api/v1/`. Future versions will be supported alongside existing versions.

---

## Support

For API support, contact:

- **Email**: <dev@skyyrose.com>
- **Docs**: <https://docs.skyyrose.com>
- **GitHub**: <https://github.com/skyyrose/platform/issues>

---

**Last Updated**: 2025-12-19
**API Version**: 1.0.0
