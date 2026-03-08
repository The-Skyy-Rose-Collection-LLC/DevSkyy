# DevSkyy Data Models Codemap

> Freshness: 2026-03-03 | SQLAlchemy 2.0 + Pydantic + GraphQL + gRPC + PHP

## Database Models (`database/db.py`)

### User
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | Auto-increment |
| email | str unique | Indexed with is_active |
| username | str unique | |
| hashed_password | str | |
| role | str | Default: 'user' |
| is_active | bool | Default: True |
| is_verified | bool | Default: False |
| last_login | datetime | Nullable |
| metadata_json | JSON | Flexible metadata |
| created_at, updated_at | datetime | TimestampMixin |

### Product
| Field | Type | Notes |
|-------|------|-------|
| id | int PK | |
| sku | str unique | e.g., 'br-001' |
| name | str | |
| description | text | |
| price, compare_price, cost | decimal | |
| quantity | int | Stock level |
| category | str | Indexed with is_active |
| collection | str | black-rose, love-hurts, signature |
| is_active | bool | |
| variants_json | JSON | Size/color variants |
| images_json | JSON | Image URLs array |
| seo_json | JSON | SEO metadata |

### Order / OrderItem
| Field | Type | Notes |
|-------|------|-------|
| Order.order_number | str unique | |
| Order.user_id | FK → User | |
| Order.status | str | pending, processing, shipped, delivered |
| Order.subtotal/tax/shipping/total | decimal | |
| Order.shipping_address_json | JSON | |
| OrderItem.product_id | FK → Product | |
| OrderItem.quantity, unit_price, total | decimal | |

### EventRecord (Event Sourcing)
| Field | Type | Notes |
|-------|------|-------|
| event_id | str PK | UUID |
| event_type | str | e.g., ProductCreated |
| aggregate_id | str | Indexed with timestamp |
| aggregate_type | str | |
| data_json | JSON | Immutable deep-copy |
| version | int | |
| correlation_id | str | Request tracing |

### Other: AuditLog, AgentTask

## Auth Models (`core/auth/`)

### Enums
| Enum | Values |
|------|--------|
| UserRole | SUPER_ADMIN, ADMIN, DEVELOPER, API_USER, READ_ONLY, GUEST |
| Permission | 24 permissions across USER, PRODUCT, ORDER, ANALYTICS, ADMIN, AGENT |
| TokenType | ACCESS, REFRESH, RESET_PASSWORD, VERIFY_EMAIL, API_KEY |
| AuthStatus | SUCCESS, FAILED, EXPIRED, REVOKED, LOCKED, MFA_REQUIRED |

### Pydantic Models
| Model | Key Fields |
|-------|-----------|
| TokenResponse | access_token, refresh_token, expires_in, scope |
| AuthResult | status, tokens, error_code, user_id, requires_mfa |
| UserCreate | username, email, password (OWASP validated), roles, tier |
| UserInDB | + hashed_password, failed_login_attempts, locked_until |

## Event Sourcing (`core/events/`)

```python
Event:
  event_id: UUID
  event_type: str          # "ProductCreated", "OrderPlaced"
  aggregate_id: str        # Entity ID
  data: dict               # Immutable deep-copy
  timestamp: datetime
  version: int
  correlation_id: str
```

## CQRS (`core/cqrs/`)

```python
Command: command_type, data, user_id, correlation_id
Query:   query_type, parameters, user_id
```

## GraphQL (`api/graphql/`)

```graphql
type ProductType {
  id: String!
  sku: String!
  name: String!
  description: String
  price: Float!
  compare_price: Float
  collection: String
  is_active: Boolean!
  images: [String!]!
}

type Query {
  product(sku: String!): ProductType
  products(collection: String, limit: Int = 20, offset: Int = 0): [ProductType!]!
}
```

DataLoader: Batches SKU lookups, request-scoped cache, prevents N+1.

## gRPC (`grpc_server/proto/product.proto`)

| RPC | Request → Response |
|-----|-------------------|
| GetProduct | GetProductRequest(sku) → ProductResponse |
| ListProducts | ListProductsRequest(collection, limit, offset) → ListProductsResponse |
| CreateProduct | CreateProductRequest(sku, name, price, ...) → ProductResponse |
| UpdateProductPrice | UpdateProductPriceRequest(sku, new_price) → ProductResponse |

## WordPress Catalog (`inc/product-catalog.php`)

```php
$product = array(
    'sku'               => 'br-001',
    'name'              => 'Product Name',
    'price'             => 55.00,
    'collection'        => 'black-rose',  // black-rose|love-hurts|signature
    'description'       => '...',
    'badge'             => 'NEW',         // NEW|Draft|''
    'image'             => $img . '/br-001-render-front.webp',
    'front_model_image' => '',
    'back_image'        => '',
    'back_model_image'  => '',
    'sizes'             => 'S|M|L|XL|2XL|3XL',
    'color'             => 'Teal/Gold',
    'edition_size'      => 250,
    'published'         => true,
    'is_preorder'       => false,
);
```

**30 products**: Black Rose (12), Love Hurts (5), Signature (13)
**6 pre-order**: br-d01, br-d02, br-d03, br-d04, lh-001, sg-d01

## Frontend Types (`frontend/`)

### Auth Context
```typescript
interface User { id, email, name, role: 'admin'|'user'|'viewer' }
interface AuthState { user, token, loading, error }
```

### Cart Store (Zustand)
```typescript
interface CartItem { sku, name, price, quantity, size, color, image }
interface CartStore { items, addItem, removeItem, clearCart, total }
```

## Repository Pattern (`database/db.py`)

| Repository | Special Methods |
|------------|----------------|
| UserRepository | get_by_email, get_by_username, get_active_users |
| ProductRepository | get_by_sku, get_by_collection, search, get_low_stock |
| OrderRepository | get_by_order_number, get_user_orders, get_revenue_summary |
| AuditLogRepository | log, get_user_activity, get_resource_history |
