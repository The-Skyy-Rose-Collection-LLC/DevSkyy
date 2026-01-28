# WordPress.com Integration Guide

> Modern WordPress.com and WooCommerce integration for SkyyRose collections

## Overview

Clean, production-ready WordPress.com integration with WooCommerce support. Replaces legacy WordPress code with modern architecture.

## Quick Start

```bash
# 1. Configure environment
cp .env.wordpress.example .env
# Edit .env with your credentials

# 2. Test integration
curl http://localhost:8000/api/v1/wordpress/health

# 3. Sync products
curl -X POST "http://localhost:8000/api/v1/wordpress/products/sync-collection" \
  -H "Content-Type: application/json" \
  -d '{"collection": "signature", "products": [...]}'
```

## Documentation

See full documentation in this file for:
- Environment setup
- API endpoints
- Product sync
- Webhook configuration
- Error handling
- Migration guide

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Updated**: 2026-01-27
