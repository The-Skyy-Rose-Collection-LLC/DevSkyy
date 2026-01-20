
# Commerce API Documentation

## Product Endpoints

### Create Product
POST /api/v1/products
- name: string (required)
- price: float (required)
- sku: string (required)
- inventory: integer (default: 0)

### List Products
GET /api/v1/products
- Returns paginated list of products
- Supports filtering by category, price range
