# DevSkyy Enterprise - Complete Documentation

## Overview

DevSkyy Enterprise is a comprehensive AI platform featuring:

- **Industry-Leading WordPress/Elementor Theme Builder**
- **Full-Stack Fashion E-commerce Automation**
- **57 ML-Powered AI Agents**
- **Advanced Machine Learning Framework**
- **Enterprise security best practices (secrets via environment variables)**

---

## New Features in v5.1.0 Enterprise

### 1. WordPress/Elementor Theme Builder

**Module Location (runtime):** `agent.wordpress.theme_builder_orchestrator`

**Capabilities:**
- Automated theme generation from brand guidelines
- Multiple theme templates (luxury, streetwear, minimalist, vintage, sustainable)
- ML-powered color palettes and typography
- Pre-built page layouts (home, shop, product, about, contact, blog)
- WooCommerce integration
- SEO optimization
- Performance optimization
- Export to Elementor JSON or ZIP

**API Endpoint (platform):**
```
POST /api/v1/themes/build-and-deploy
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/v1/themes/build-and-deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_name": "skyy_luxury",
    "theme_type": "luxury_fashion",
    "site_url": "https://example.com",
    "username": "wp_user",
    "password": "<APPLICATION_PASSWORD_OR_USE_CONFIGURED_CREDENTIALS>",
    "auto_deploy": true,
    "activate_after_deploy": false
  }'
```

> Note: The platform now exposes theme workflows through the `/api/v1/themes/*` namespace. Integrations typically call the orchestrator endpoints rather than a single local builder class.

---

### 2. Fashion E-commerce Automation

#### Product Manager (`agent/ecommerce/product_manager.py`)

**Features:**
- ML-generated product descriptions
- Automated categorization
- Variant generation (size/color)
- SEO metadata generation
- Image optimization
- Bulk import

**API Endpoints:**
```
POST /api/v1/ecommerce/products
POST /api/v1/ecommerce/products/bulk
GET  /api/v1/ecommerce/products/{id}/analytics
```

... (unchanged sections omitted for brevity) ...

---

## Architecture

```
DevSkyy/
├── agent/
│   ├── modules/              # Many specialized AI agents
│   ├── ml_models/            # Machine learning engines
│   │   ├── __init__.py
│   │   ├── base_ml_engine.py       # Base ML framework
│   │   ├── fashion_ml.py           # Fashion-specific ML
│   │   └── ...
│   ├── ecommerce/            # E-commerce automation
│   ├── wordpress/            # WordPress automation orchestration
│   │   ├── __init__.py
│   │   ├── theme_builder_orchestrator.py  # Orchestrator for theme builds
│   │   └── ...
│   └── ...
├── api/
│   └── v1/                   # API routers mounted under /api/v1
├── core/
├── docs/
├── main.py
├── requirements.txt
└── docker-compose.yml
```

---

## Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Services started (typical):
# - devskyy-api:8000        # Main API
# - devskyy-redis:6379      # Cache
# - devskyy-postgres:5432   # Database
# - devskyy-prometheus:9090 # Monitoring
# - devskyy-grafana:3000    # Dashboards

# View logs
docker-compose logs -f api

# Scale API
docker-compose up -d --scale api=4
```

### Environment Variables

The application relies on runtime environment configuration. In production ensure required secrets are provided as environment variables (no secrets in code):

```env
# Required
SECRET_KEY=your-secret-key        # REQUIRED in production
ANTHROPIC_API_KEY=your-anthropic-key

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/devskyy

# Cache
REDIS_URL=redis://redis:6379

# Optional
OPENAI_API_KEY=your-openai-key
LOG_LEVEL=info
```

---

## CI/CD Pipeline

**Workflow:** `.github/workflows/ci-cd.yml`

**Stages:**
1. **Test** - Run pytest with coverage
2. **Lint** - Black, isort, ruff, mypy
3. **Security** - Bandit, pip-audit, safety
4. **Build** - Docker image build
5. **Deploy** - Auto-deploy on main branch

---

## API Endpoints (updated highlights)

### Theme Builder

```http
POST /api/v1/themes/build-and-deploy
```
Request should include theme parameters and credentials (or use configured credentials via credential manager). Response returns build id, status and deployment metadata.

### E-commerce

(See above endpoints under `/api/v1/ecommerce`)

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=agent --cov-report=html
```

---

## Troubleshooting

- Ensure `SECRET_KEY` is set in production environments.
- Use configured WordPress credentials (via config/wordpress_credentials) rather than embedding secrets in requests when possible.

---

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/SkyyRoseLLC/DevSkyy/issues)
- **Email:** support@devskyy.com

---

**DevSkyy Enterprise v5.1.0** - Built with advanced AI and ML
