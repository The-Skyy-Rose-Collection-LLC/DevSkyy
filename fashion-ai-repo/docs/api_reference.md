# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently using API-based access. JWT authentication can be enabled via configuration.

## Response Format

All API responses follow this format:

```json
{
  "status": 200,
  "message": "ok",
  "payload": { ... }
}
```

## Design Endpoints

### Generate Design

```http
POST /api/design/generate
```

**Request Body:**
```json
{
  "style": "modern",
  "color": "crimson",
  "season": "spring"
}
```

**Response:**
```json
{
  "status": 200,
  "message": "Design generation queued",
  "payload": {
    "design_id": "design_1234567890",
    "style": "modern",
    "color": "crimson"
  }
}
```

### Get Design Feed

```http
GET /api/design/feed?limit=10
```

### Get Design by ID

```http
GET /api/design/{design_id}
```

## Commerce Endpoints

### List Products

```http
GET /api/products?limit=20&offset=0
```

### Get Product

```http
GET /api/products/{sku}
```

### Create Order

```http
POST /api/orders
```

## Marketing Endpoints

### Create Campaign

```http
POST /api/marketing/campaign
```

### Get Analytics

```http
GET /api/analytics?period=week
```

## Finance Endpoints

### Get Financial Summary

```http
GET /api/finance/summary?period=month
```

### Get Ledger

```http
GET /api/finance/ledger?limit=50
```

## System Endpoints

### System Status

```http
GET /api/system/status
```

**Response:**
```json
{
  "status": 200,
  "payload": {
    "api": "healthy",
    "agents": {
      "designer": "active",
      "commerce": "active"
    }
  }
}
```

### Health Check

```http
GET /api/system/health
```

### Metrics

```http
GET /api/system/metrics
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.
