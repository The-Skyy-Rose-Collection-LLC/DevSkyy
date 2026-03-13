# AR Stack Configuration Mission

## Mission: Configure Frontend, Backend, and Dashboard Connections for AR Shopping

**Status: IN PROGRESS**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     AR SHOPPING STACK                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  FRONTEND   │    │   BACKEND   │    │  DASHBOARD  │         │
│  │             │    │             │    │             │         │
│  │ Three.js    │◄──►│ FastAPI     │◄──►│ Analytics   │         │
│  │ WebXR       │    │ /api/v1/    │    │ Monitoring  │         │
│  │ ARTryOn     │    │ virtual-tryon│   │ Admin       │         │
│  │ Collections │    │ WooCommerce │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                  │                  │                 │
│         └──────────┬───────┴──────────┬──────┘                 │
│                    │                  │                         │
│              ┌─────▼─────┐     ┌──────▼─────┐                   │
│              │   FASHN   │     │ WooCommerce │                  │
│              │   API     │     │   REST API  │                  │
│              └───────────┘     └─────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Frontend (Three.js/WebXR)

| Module | Location | Purpose |
|--------|----------|---------|
| ARTryOnViewer | `src/collections/ARTryOnViewer.ts` | Webcam-based AR try-on |
| WebXRARViewer | `src/collections/WebXRARViewer.ts` | Native WebXR AR |
| BlackRoseExperience | `src/collections/BlackRoseExperience.ts` | 3D collection page |
| LoveHurtsExperience | `src/collections/LoveHurtsExperience.ts` | 3D collection page |
| SignatureExperience | `src/collections/SignatureExperience.ts` | 3D collection page |
| WooCommerceProductLoader | `src/collections/WooCommerceProductLoader.ts` | Product data |
| EnvironmentTransition | `src/collections/EnvironmentTransition.ts` | Scene transitions |

### 2. Backend (FastAPI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/virtual-tryon` | POST | Process AR try-on request |
| `/api/v1/virtual-tryon/batch` | POST | Batch processing |
| `/api/v1/virtual-tryon/status/{job_id}` | GET | Check job status |
| `/api/v1/virtual-tryon/ai-model` | POST | Generate AI model |
| `/wp-json/wc/v3/products` | GET | WooCommerce products |
| `/wp-json/wc/v3/products/{id}` | GET | Single product |
| `/api/v1/ar/session` | POST | Create AR session |
| `/api/v1/ar/products/{collection}` | GET | AR-ready products |

### 3. Dashboard (Admin/Analytics)

| Feature | Purpose |
|---------|---------|
| AR Usage Analytics | Track try-on sessions, conversions |
| Product Performance | Most-tried products, conversion rates |
| Session Monitoring | Active sessions, errors, latency |
| Cost Tracking | FASHN API usage, credits |

---

## Configuration Required

### Environment Variables

```bash
# Backend
FASHN_API_KEY=...           # Virtual try-on provider
WC_KEY=...                  # WooCommerce consumer key
WC_SECRET=...               # WooCommerce consumer secret
SKYYROSE_BASE_URL=https://skyyrose.com

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WC_API_URL=https://skyyrose.com/wp-json/wc/v3

# Dashboard
DASHBOARD_SECRET_KEY=...
ANALYTICS_ENDPOINT=/api/v1/ar/analytics
```

### API Configuration

```typescript
// frontend/src/config/ar.ts
export const AR_CONFIG = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
  tryOnEndpoint: '/api/v1/virtual-tryon',
  maxRetries: 3,
  timeout: 30000,
  collections: ['black_rose', 'love_hurts', 'signature'],
};
```

---

## Tasks

- [x] Create AR session management endpoint ✅ `api/ar_sessions.py`
- [x] Add AR product metadata to WooCommerce products ✅ `ARProduct` model
- [x] Configure CORS for frontend-backend communication ✅ via FastAPI
- [x] Set up WebSocket for real-time AR status ✅ `/api/v1/ar/ws/{session_id}`
- [x] Create dashboard analytics endpoints ✅ `/api/v1/dashboard/ar/overview`, `/metrics`
- [x] Add AR usage tracking ✅ `TryOnEvent`, `SessionAnalytics`
- [ ] Configure CDN for 3D model assets (optional, use WP uploads)

## Configured Endpoints

### Backend (api/ar_sessions.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/ar/sessions` | POST | Create AR session |
| `/api/v1/ar/sessions/{id}` | GET | Get session |
| `/api/v1/ar/sessions/{id}` | PATCH | Update session |
| `/api/v1/ar/sessions/{id}/tryon` | POST | Record try-on |
| `/api/v1/ar/products/{collection}` | GET | Collection products |
| `/api/v1/ar/products` | GET | All AR products |
| `/api/v1/ar/analytics` | GET | Session analytics |
| `/api/v1/ar/capabilities` | GET | AR capabilities |
| `/api/v1/ar/ws/{session_id}` | WS | Real-time updates |

### Dashboard (api/dashboard.py)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/dashboard/ar/overview` | GET | AR dashboard overview |
| `/api/v1/dashboard/ar/metrics` | GET | Detailed AR metrics |

### Frontend (src/config/ar.ts)
- `ARConfig` interface with all endpoints
- `ARApiClient` class for API calls
- `detectARCapabilities()` for WebXR detection
- Collection-specific settings (black_rose, love_hurts, signature)

---

**Mission Started: 2026-01-18**
