# WooCommerce REST API v3 — Data Schemas

> Project context: skyyrose.co runs on WordPress.com Atomic. The REST API is accessed via
> `?rest_route=/wc/v3/...` (not `/wp-json/wc/v3/...` — the latter returns 401 on WP.com Atomic).
> Auth: HTTP Basic with consumer key + secret from `.env.wordpress`.

---

## Product

The core object for all 33 SKUs in the SkyyRose catalog.

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `id` | integer | WC internal post ID |
| `name` | string | Display name, e.g. `"Black Rose Sherpa Jacket"` |
| `slug` | string | URL-safe, e.g. `"black-rose-sherpa-jacket"` |
| `sku` | string | Catalog SKU, e.g. `"br-006"` |
| `status` | string | `"publish"` \| `"draft"` \| `"private"` |
| `type` | string | `"simple"` \| `"variable"` |
| `regular_price` | string | Decimal string, e.g. `"195.00"` |
| `sale_price` | string | Decimal string or `""` when no sale |
| `price` | string | Effective price (sale or regular) |
| `stock_status` | string | `"instock"` \| `"outofstock"` \| `"onbackorder"` |
| `manage_stock` | boolean | Whether WC tracks quantity |
| `stock_quantity` | integer \| null | null when `manage_stock` is false |
| `categories` | array | See Category object below |
| `images` | array | See Image object below |
| `attributes` | array | Size, color, etc. — see Attribute object |
| `meta_data` | array | Custom meta — see Meta object |
| `description` | string | Full HTML product description |
| `short_description` | string | HTML excerpt shown on archive/PDP |
| `date_created` | string | ISO 8601 |
| `permalink` | string | Full storefront URL |

**JSON example — minimal product read:**

```json
{
  "id": 9876,
  "name": "Black Rose Sherpa Jacket",
  "slug": "black-rose-sherpa-jacket",
  "sku": "br-006",
  "status": "publish",
  "type": "simple",
  "regular_price": "245.00",
  "sale_price": "",
  "price": "245.00",
  "stock_status": "instock",
  "manage_stock": false,
  "stock_quantity": null,
  "categories": [
    { "id": 42, "name": "Black Rose", "slug": "black-rose" }
  ],
  "images": [
    {
      "id": 1001,
      "src": "https://skyyrose.co/wp-content/uploads/br-006-front.webp",
      "name": "br-006-front",
      "alt": "Black Rose Sherpa Jacket — front view"
    }
  ],
  "attributes": [
    {
      "id": 1,
      "name": "Size",
      "options": ["XS", "S", "M", "L", "XL", "XXL"],
      "variation": true,
      "visible": true
    }
  ],
  "meta_data": [
    { "id": 201, "key": "_is_preorder", "value": "1" }
  ],
  "description": "<p>Armor for the concrete. ...</p>",
  "short_description": "<p>Hooded sherpa, silver rose embroidery.</p>",
  "date_created": "2026-04-01T12:00:00",
  "permalink": "https://skyyrose.co/product/black-rose-sherpa-jacket/"
}
```

### Nested: Category

```json
{ "id": 42, "name": "Black Rose", "slug": "black-rose" }
```

### Nested: Image

```json
{
  "id": 1001,
  "src": "https://skyyrose.co/wp-content/uploads/br-006-front.webp",
  "name": "br-006-front",
  "alt": "Black Rose Sherpa Jacket — front view"
}
```

### Nested: Meta (`meta_data[]`)

```json
{ "id": 201, "key": "_is_preorder", "value": "1" }
```

Common project meta keys: `_is_preorder`, `_render_stage`, `_approved_render`.

---

## Order

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `id` | integer | WC order ID |
| `status` | string | `"pending"` \| `"processing"` \| `"on-hold"` \| `"completed"` \| `"cancelled"` \| `"refunded"` \| `"failed"` |
| `currency` | string | `"USD"` |
| `total` | string | Decimal string including tax + shipping |
| `discount_total` | string | Total discount applied to the order |
| `total_tax` | string | Tax amount |
| `shipping_total` | string | Shipping cost |
| `line_items` | array | See LineItem below |
| `billing` | object | See Address below |
| `shipping` | object | See Address below |
| `payment_method` | string | e.g. `"stripe"` |
| `date_created` | string | ISO 8601 |
| `date_modified` | string | ISO 8601 |
| `customer_id` | integer | 0 for guest orders |
| `customer_note` | string | Buyer note at checkout |

**JSON example:**

```json
{
  "id": 5001,
  "status": "processing",
  "currency": "USD",
  "total": "262.00",
  "discount_total": "0.00",
  "total_tax": "0.00",
  "shipping_total": "17.00",
  "line_items": [
    {
      "id": 11,
      "product_id": 9876,
      "variation_id": 0,
      "name": "Black Rose Sherpa Jacket",
      "sku": "br-006",
      "quantity": 1,
      "price": 245.0,
      "subtotal": "245.00",
      "total": "245.00"
    }
  ],
  "billing": {
    "first_name": "Jordan",
    "last_name": "Rivera",
    "email": "jordan@example.com",
    "phone": "5105550100",
    "address_1": "100 Broadway",
    "address_2": "",
    "city": "Oakland",
    "state": "CA",
    "postcode": "94607",
    "country": "US"
  },
  "shipping": {
    "first_name": "Jordan",
    "last_name": "Rivera",
    "address_1": "100 Broadway",
    "city": "Oakland",
    "state": "CA",
    "postcode": "94607",
    "country": "US"
  },
  "payment_method": "stripe",
  "date_created": "2026-06-01T09:15:00",
  "customer_id": 0,
  "customer_note": ""
}
```

### Nested: LineItem

```json
{
  "id": 11,
  "product_id": 9876,
  "variation_id": 0,
  "name": "Black Rose Sherpa Jacket",
  "sku": "br-006",
  "quantity": 1,
  "price": 245.0,
  "subtotal": "245.00",
  "total": "245.00"
}
```

### Nested: Address (billing + shipping share schema)

```json
{
  "first_name": "Jordan",
  "last_name": "Rivera",
  "company": "",
  "address_1": "100 Broadway",
  "address_2": "",
  "city": "Oakland",
  "state": "CA",
  "postcode": "94607",
  "country": "US",
  "email": "jordan@example.com",
  "phone": "5105550100"
}
```

---

## Customer

**Key fields:**

| Field | Type | Notes |
|---|---|---|
| `id` | integer | WC customer ID |
| `email` | string | Unique identifier |
| `first_name` | string | |
| `last_name` | string | |
| `username` | string | WP login slug |
| `role` | string | `"customer"` \| `"subscriber"` |
| `date_created` | string | ISO 8601 |
| `orders_count` | integer | Lifetime order count |
| `total_spent` | string | Decimal string |
| `billing` | object | Address schema (same as Order) |
| `shipping` | object | Address schema (same as Order) |
| `meta_data` | array | Custom meta |

**JSON example:**

```json
{
  "id": 304,
  "email": "jordan@example.com",
  "first_name": "Jordan",
  "last_name": "Rivera",
  "username": "jordan.rivera",
  "role": "customer",
  "date_created": "2026-03-12T18:00:00",
  "orders_count": 2,
  "total_spent": "440.00",
  "billing": { "city": "Oakland", "state": "CA", "country": "US" },
  "shipping": { "city": "Oakland", "state": "CA", "country": "US" },
  "meta_data": []
}
```

---

## Webhook Payload Envelope

WooCommerce webhooks POST a JSON body to the configured delivery URL. The envelope wraps the
relevant resource object (product, order, customer, etc.) and includes these HTTP headers:

**Headers sent with every webhook:**

| Header | Value |
|---|---|
| `X-WC-Webhook-Source` | Store URL, e.g. `https://skyyrose.co/` |
| `X-WC-Webhook-Topic` | e.g. `order.created`, `product.updated` |
| `X-WC-Webhook-Resource` | `order` \| `product` \| `customer` \| `coupon` |
| `X-WC-Webhook-Event` | `created` \| `updated` \| `deleted` \| `restored` |
| `X-WC-Webhook-Signature` | HMAC-SHA256 of raw body, base64-encoded |
| `X-WC-Webhook-ID` | Numeric webhook ID |
| `X-WC-Webhook-Delivery-ID` | Unique delivery attempt ID |
| `Content-Type` | `application/json` |

**Payload body** is the full resource object (same shape as the REST API GET response). Example
for `order.created`:

```json
{
  "id": 5001,
  "status": "pending",
  "total": "262.00",
  "line_items": [ { "sku": "br-006", "quantity": 1 } ],
  "billing": { "email": "jordan@example.com" }
}
```

**Signature verification** (Python):

```python
import hmac, hashlib, base64

def verify_woo_webhook(body_bytes: bytes, secret: str, signature_header: str) -> bool:
    digest = hmac.new(secret.encode(), body_bytes, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature_header)
```

---

## Common REST Endpoints (WP.com Atomic pattern)

```
GET  ?rest_route=/wc/v3/products              # list products
GET  ?rest_route=/wc/v3/products/{id}         # single product
POST ?rest_route=/wc/v3/products              # create product
PUT  ?rest_route=/wc/v3/products/{id}         # update product
GET  ?rest_route=/wc/v3/orders                # list orders
GET  ?rest_route=/wc/v3/orders/{id}           # single order
PUT  ?rest_route=/wc/v3/orders/{id}           # update order status
GET  ?rest_route=/wc/v3/customers             # list customers
GET  ?rest_route=/wc/v3/products/categories   # list categories
GET  ?rest_route=/wc/v3/products/attributes   # list attributes
```

All write operations require `STOP AND SHOW` confirmation per `CLAUDE.md` before execution.
