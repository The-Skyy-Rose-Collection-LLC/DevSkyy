# WooCommerce REST API

This skill provides comprehensive knowledge for WooCommerce e-commerce integration. It activates when users mention "woocommerce", "woo api", "products api", "orders api", "woocommerce rest", "cart api", "checkout api", or encounter WooCommerce-related errors.

---

## WooCommerce REST API Setup

### Authentication Methods

**1. Consumer Key/Secret (Recommended for Server-Side)**
```bash
# Generate in WooCommerce > Settings > Advanced > REST API
# Permissions: Read, Write, or Read/Write
```

```typescript
// lib/woocommerce.ts
const WC_API_URL = process.env.WOOCOMMERCE_API_URL
const WC_CONSUMER_KEY = process.env.WC_CONSUMER_KEY
const WC_CONSUMER_SECRET = process.env.WC_CONSUMER_SECRET

async function wcFetch(endpoint: string, options?: RequestInit) {
  const url = new URL(`${WC_API_URL}/wp-json/wc/v3${endpoint}`)
  url.searchParams.set('consumer_key', WC_CONSUMER_KEY!)
  url.searchParams.set('consumer_secret', WC_CONSUMER_SECRET!)

  const response = await fetch(url.toString(), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    }
  })

  if (!response.ok) {
    throw new Error(`WooCommerce API error: ${response.status}`)
  }

  return response.json()
}
```

**2. OAuth 1.0a (For HTTPS sites)**
```typescript
import OAuth from 'oauth-1.0a'
import crypto from 'crypto'

const oauth = new OAuth({
  consumer: {
    key: process.env.WC_CONSUMER_KEY!,
    secret: process.env.WC_CONSUMER_SECRET!
  },
  signature_method: 'HMAC-SHA256',
  hash_function(base_string, key) {
    return crypto.createHmac('sha256', key).update(base_string).digest('base64')
  }
})
```

## Products API

### List Products
```typescript
export async function getProducts(params?: {
  page?: number
  perPage?: number
  category?: number
  search?: string
  featured?: boolean
  onSale?: boolean
}) {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.perPage) searchParams.set('per_page', String(params.perPage))
  if (params?.category) searchParams.set('category', String(params.category))
  if (params?.search) searchParams.set('search', params.search)
  if (params?.featured) searchParams.set('featured', 'true')
  if (params?.onSale) searchParams.set('on_sale', 'true')

  return wcFetch(`/products?${searchParams}`)
}

// Get single product
export async function getProduct(id: number) {
  return wcFetch(`/products/${id}`)
}

// Get product by slug
export async function getProductBySlug(slug: string) {
  const products = await wcFetch(`/products?slug=${slug}`)
  return products[0] || null
}
```

### Product Type Definition
```typescript
export interface WCProduct {
  id: number
  name: string
  slug: string
  permalink: string
  type: 'simple' | 'variable' | 'grouped' | 'external'
  status: string
  description: string
  short_description: string
  sku: string
  price: string
  regular_price: string
  sale_price: string
  on_sale: boolean
  stock_status: 'instock' | 'outofstock' | 'onbackorder'
  stock_quantity: number | null
  categories: Array<{ id: number; name: string; slug: string }>
  images: Array<{ id: number; src: string; alt: string }>
  attributes: Array<{
    id: number
    name: string
    options: string[]
  }>
  variations: number[]
}
```

## Product Variations (Variable Products)

```typescript
// Get variations for a product
export async function getProductVariations(productId: number) {
  return wcFetch(`/products/${productId}/variations`)
}

// Get specific variation
export async function getVariation(productId: number, variationId: number) {
  return wcFetch(`/products/${productId}/variations/${variationId}`)
}
```

## Categories API

```typescript
export async function getCategories(params?: {
  parent?: number
  hideEmpty?: boolean
}) {
  const searchParams = new URLSearchParams()
  if (params?.parent !== undefined) searchParams.set('parent', String(params.parent))
  if (params?.hideEmpty) searchParams.set('hide_empty', 'true')

  return wcFetch(`/products/categories?${searchParams}`)
}
```

## Cart API (WooCommerce Store API)

The Store API is newer and designed for headless use:

```typescript
const STORE_API = `${WC_API_URL}/wp-json/wc/store/v1`

// Get cart
export async function getCart() {
  const response = await fetch(`${STORE_API}/cart`, {
    credentials: 'include'
  })
  return response.json()
}

// Add to cart
export async function addToCart(productId: number, quantity: number = 1) {
  const response = await fetch(`${STORE_API}/cart/add-item`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      id: productId,
      quantity
    })
  })
  return response.json()
}

// Update cart item
export async function updateCartItem(key: string, quantity: number) {
  const response = await fetch(`${STORE_API}/cart/update-item`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ key, quantity })
  })
  return response.json()
}

// Remove from cart
export async function removeFromCart(key: string) {
  const response = await fetch(`${STORE_API}/cart/remove-item`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ key })
  })
  return response.json()
}
```

## Checkout API

```typescript
// Get checkout data
export async function getCheckout() {
  const response = await fetch(`${STORE_API}/checkout`, {
    credentials: 'include'
  })
  return response.json()
}

// Process checkout
export async function processCheckout(data: {
  billing_address: BillingAddress
  shipping_address?: ShippingAddress
  payment_method: string
  payment_data?: Array<{ key: string; value: string }>
}) {
  const response = await fetch(`${STORE_API}/checkout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data)
  })
  return response.json()
}
```

## Orders API

```typescript
// Create order (server-side)
export async function createOrder(orderData: {
  payment_method: string
  payment_method_title: string
  set_paid?: boolean
  billing: BillingAddress
  shipping: ShippingAddress
  line_items: Array<{ product_id: number; quantity: number }>
}) {
  return wcFetch('/orders', {
    method: 'POST',
    body: JSON.stringify(orderData)
  })
}

// Get order
export async function getOrder(orderId: number) {
  return wcFetch(`/orders/${orderId}`)
}

// Update order status
export async function updateOrderStatus(orderId: number, status: string) {
  return wcFetch(`/orders/${orderId}`, {
    method: 'PUT',
    body: JSON.stringify({ status })
  })
}
```

## Webhooks

### Register Webhook
```typescript
await wcFetch('/webhooks', {
  method: 'POST',
  body: JSON.stringify({
    name: 'Order Created',
    topic: 'order.created',
    delivery_url: 'https://your-site.com/api/webhooks/wc-order'
  })
})
```

### Handle Webhook in Next.js
```typescript
// app/api/webhooks/wc-order/route.ts
import { NextResponse } from 'next/server'
import crypto from 'crypto'

export async function POST(request: Request) {
  const signature = request.headers.get('x-wc-webhook-signature')
  const body = await request.text()

  // Verify webhook signature
  const expectedSignature = crypto
    .createHmac('sha256', process.env.WC_WEBHOOK_SECRET!)
    .update(body)
    .digest('base64')

  if (signature !== expectedSignature) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }

  const order = JSON.parse(body)
  // Process order...

  return NextResponse.json({ received: true })
}
```

## Common Errors and Solutions

### "woocommerce_rest_authentication_error"
- Check consumer key and secret are correct
- Verify API keys have correct permissions
- For HTTP sites, must use OAuth 1.0a

### "woocommerce_rest_product_invalid_id"
- Product ID doesn't exist
- Product is in trash
- Product is private and no auth provided

### Cart Session Issues
- Store API requires cookies for cart session
- Set `credentials: 'include'` in fetch requests
- Configure CORS to allow credentials

### "rest_no_route" for Store API
- WooCommerce Blocks plugin required for Store API
- Minimum WooCommerce version 5.0+
- Check endpoint URL format

## Environment Variables
```bash
WOOCOMMERCE_API_URL=https://your-store.com
WC_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxx
WC_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxx
WC_WEBHOOK_SECRET=your_webhook_secret
```

## Autonomous Recovery Steps

When encountering WooCommerce API errors:

1. **Verify credentials** - Test with simple product list request
2. **Check API version** - Use `/wc/v3/` for REST API, `/wc/store/v1/` for Store API
3. **Use Context7** to fetch WooCommerce REST API documentation
4. **Verify HTTPS** - Some auth methods require HTTPS
5. **Check permissions** - API keys need appropriate read/write permissions
6. **Review response headers** - Rate limiting, auth errors have specific headers
7. **Enable WP_DEBUG** - Check WordPress debug.log for server-side errors
