# DevSkyy Dashboard — API Contract

All endpoints require `Authorization: Bearer <token>` unless noted. Responses are validated against Zod schemas defined in `frontend/lib/api/schemas.ts`.

---

## Authentication

### Login

```
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

Body: username=<email>&password=<password>&grant_type=password

Response 200:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Handled by NextAuth — developers don't call this directly. Session tokens are managed automatically.

---

## Health & Monitoring

### System Health

```
GET /api/v1/health

Response 200 (HealthResponseSchema):
{
  "status": "healthy",
  "version": "3.2.0",
  "uptime": 86400
}
```

### Frontend Health (Next.js route)

```
GET /api/monitoring/health
GET /api/monitoring/metrics
```

---

## Round Table (LLM Competitions)

**Base**: `${NEXT_PUBLIC_API_URL}/api/v1/round-table`
**Frontend module**: `lib/api/endpoints/round-table.ts`

### List Providers

```
GET /api/v1/round-table/providers

Response 200 (ProviderInfo[]):
[{
  "name": "claude",
  "display_name": "Claude",
  "enabled": true,
  "avg_latency_ms": 1200,
  "win_rate": 0.72,
  "total_competitions": 150
}]
```

### Provider Stats

```
GET /api/v1/round-table/stats

Response 200 (ProviderStats[]):
[{
  "provider": "claude",
  "total_competitions": 150,
  "wins": 108,
  "win_rate": 0.72,
  "avg_score": 87.3,
  "avg_latency_ms": 1200,
  "total_cost_usd": 4.52
}]
```

### Competition History

```
GET /api/v1/round-table?limit=10&offset=0

Response 200 (HistoryEntry[]):
[{
  "id": "comp_abc123",
  "prompt_preview": "Compare product descriptions...",
  "winner_provider": "claude",
  "winner_score": 92.5,
  "total_cost_usd": 0.03,
  "created_at": "2026-03-01T12:00:00Z"
}]
```

### Run Competition

```
POST /api/v1/round-table/compete
Content-Type: application/json

Body:
{
  "prompt": "Write a product description for...",
  "providers": ["claude", "gpt", "gemini"],       // optional
  "evaluation_criteria": ["relevance", "quality"]   // optional
}

Response 200 (CompetitionResponse):
{
  "id": "comp_abc123",
  "task_id": "task_xyz",
  "prompt_preview": "Write a product...",
  "status": "completed",
  "winner": { "provider": "claude", "rank": 1, "scores": {...}, ... },
  "entries": [...],
  "total_duration_ms": 5200,
  "total_cost_usd": 0.09,
  "created_at": "2026-03-01T12:00:00Z"
}
```

**Validation**: Prompt required, max 10,000 characters.

---

## 3D Pipeline

**Base**: `/api/v1/3d` (Next.js API routes — relative URLs)
**Frontend module**: `lib/api/endpoints/pipeline.ts`

### Pipeline Status

```
GET /api/v1/3d/status

Response 200 (PipelineStatus):
{
  "status": "healthy" | "degraded" | "down",
  "active_jobs": 3,
  "queued_jobs": 12,
  "providers_online": 2,
  "providers_total": 3
}
```

### List 3D Providers

```
GET /api/v1/3d/providers

Response 200 (Provider3D[]):
[{
  "id": "tripo3d",
  "name": "Tripo3D",
  "type": "commercial" | "huggingface" | "local",
  "capabilities": ["text-to-3d", "image-to-3d"],
  "avg_generation_time_s": 45,
  "status": "online" | "offline" | "busy"
}]
```

### List Jobs

```
GET /api/v1/3d/jobs?limit=20

Response 200 (Job3D[]):
[{
  "id": "job_abc",
  "status": "queued" | "processing" | "completed" | "failed",
  "provider": "tripo3d",
  "input_type": "text" | "image",
  "input": "A luxury handbag...",
  "output_url": "https://...",
  "created_at": "2026-03-01T12:00:00Z"
}]
```

### Text-to-3D

```
POST /api/v1/3d/generate/text
Content-Type: application/json

Body:
{
  "prompt": "A luxury leather handbag with gold hardware",
  "provider": "tripo3d",         // optional
  "quality": "standard" | "high" // optional, default: "standard"
}

Response 200 (Job3D): { "id": "job_abc", "status": "queued", ... }
```

**Validation**: Prompt required, max 5,000 characters.

### Image-to-3D

```
POST /api/v1/3d/generate/image

Body:
{
  "image_url": "https://example.com/product.jpg",
  "provider": "meshy",
  "quality": "high"
}

Response 200 (Job3D): { "id": "job_abc", "status": "queued", ... }
```

**Validation**: Valid URL required, max 2,000 characters.

---

## Assets

**Base**: `${NEXT_PUBLIC_API_URL}/api/v1/assets`
**Frontend module**: `lib/api/endpoints/assets.ts`

### List Assets

```
GET /api/v1/assets?collection=black_rose&type=image&search=jersey&page=1&limit=20

Response 200 (AssetListResponse):
{
  "assets": [{
    "id": "asset_abc",
    "filename": "br-d01-render-front.webp",
    "path": "/assets/images/products/br-d01-render-front.webp",
    "collection": "black_rose" | "signature" | "love_hurts" | "showroom" | "runway",
    "type": "image" | "3d_model" | "video" | "texture",
    "metadata": {
      "sku": "br-d01",
      "product_name": "Hockey Jersey (Teal)",
      "tags": ["jersey", "hockey", "teal"],
      "width": 1024,
      "height": 1024,
      "size_bytes": 245000,
      "format": "webp"
    },
    "thumbnail_url": "https://...",
    "created_at": "2026-02-28T12:00:00Z"
  }],
  "total": 80,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

### Get Single Asset

```
GET /api/v1/assets/:id
Response 200 (Asset): { ... }
```

### Update Asset Metadata

```
PATCH /api/v1/assets/:id
Body: { "metadata": { "tags": ["updated", "tags"] } }
Response 200 (Asset): { ... }
```

### Delete Asset

```
DELETE /api/v1/assets/:id
Response 204: (no body)
```

### Upload Asset

```
POST /api/v1/assets/upload
Content-Type: multipart/form-data

Body: file=<binary>, collection=black_rose
Timeout: 120 seconds

Response 200 (Asset): { ... }
```

### Collection Stats

```
GET /api/v1/assets/stats/collections
Response 200: { "black_rose": 45, "love_hurts": 20, "signature": 15 }
```

---

## QA Reviews

**Frontend module**: `lib/api/endpoints/qa.ts`

### List Reviews

```
GET /api/v1/qa/reviews?status=pending

Response 200 (QAReviewListResponse):
{
  "reviews": [{
    "id": "review_abc",
    "asset_id": "asset_xyz",
    "job_id": "job_123",
    "reference_image_url": "https://...",
    "generated_model_url": "https://...",
    "fidelity_score": 87,
    "fidelity_breakdown": {
      "geometry": 90, "materials": 85, "colors": 88,
      "proportions": 92, "branding": 78, "texture_detail": 85
    },
    "status": "pending" | "approved" | "rejected" | "regenerating",
    "created_at": "2026-03-01T12:00:00Z"
  }],
  "total": 15,
  "pending_count": 5,
  "approved_count": 8,
  "rejected_count": 2
}
```

---

## Batch Jobs

**Frontend module**: `lib/api/endpoints/batch.ts`

```
BatchJob schema:
{
  "id": "batch_abc",
  "status": "pending" | "processing" | "completed" | "failed" | "paused",
  "total_assets": 20,
  "processed_assets": 15,
  "failed_assets": 1,
  "progress_percentage": 75,
  "started_at": "2026-03-01T12:00:00Z"
}
```

---

## Social Media

**Base**: `/api/social-media` (Next.js API routes)
**Frontend module**: `lib/api/endpoints/social-media.ts`

```
GET  /api/social-media              — List scheduled posts
POST /api/social-media/generate     — Generate content
POST /api/social-media/schedule     — Schedule post
POST /api/social-media/publish      — Publish post
GET  /api/social-media/analytics    — Engagement metrics
```

---

## WordPress (Proxy Routes)

**Base**: `/api/wordpress/proxy` (Next.js API routes — server-side credentials)

```
POST /api/wordpress/proxy
Body: { "endpoint": "/wp/v2/posts", "method": "GET" }

POST /api/wordpress/proxy/upload
Body: FormData with file attachment
```

**SSRF Protection**: Only endpoints starting with `/wp/` or `/wc/` are allowed.

---

## Error Format

All API errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

The frontend `ApiError` class (`lib/api/errors.ts`) wraps this with `.status`, `.code`, `.details` properties.

## Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Parse response with Zod schema |
| 400 | Bad request | Check input validation |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | User lacks admin role |
| 404 | Not found | Show empty state |
| 429 | Rate limited | Retry with backoff |
| 500 | Server error | Show error state, log details |
