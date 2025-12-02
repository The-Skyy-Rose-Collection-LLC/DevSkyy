# WordPress Operations Guide

**Purpose**: Standard procedures for WordPress/Elementor site management on skyyrose.co

---

## Environment

### Site Details
- **Domain**: skyyrose.co (NOT .com)
- **Platform**: WordPress + WooCommerce
- **Page Builder**: Elementor Pro
- **Theme**: Custom SkyyRose theme
- **Hosting**: [Configured in .env]

### Access Levels
| Role | Permissions |
|------|-------------|
| Administrator | Full access |
| Shop Manager | Products, orders, customers |
| Editor | Pages, posts, media |
| Agent | API access only |

---

## Elementor Operations

### Template Structure
```
/elementor-templates/
├── headers/
│   ├── main-header.json
│   └── mobile-header.json
├── footers/
│   └── main-footer.json
├── product-pages/
│   ├── single-product.json
│   └── product-archive.json
├── landing-pages/
│   └── collection-template.json
└── components/
    ├── hero-section.json
    ├── product-grid.json
    └── newsletter-signup.json
```

### Creating New Pages

1. **Use existing templates** whenever possible
2. **Maintain brand consistency** - refer to `brand_voice.md`
3. **Mobile-first design** - test on mobile before desktop
4. **Performance** - optimize images before upload

### Image Guidelines
| Type | Max Size | Format | Dimensions |
|------|----------|--------|------------|
| Hero | 500KB | WebP/JPEG | 1920x1080 |
| Product | 200KB | WebP/JPEG | 1000x1000 |
| Thumbnail | 50KB | WebP/JPEG | 300x300 |
| Logo | 100KB | SVG/PNG | Vector preferred |

---

## Common Operations

### Update Homepage Hero

```python
# API endpoint for hero update
POST /wp-json/skyyrose/v1/hero
{
    "image_url": "https://skyyrose.co/wp-content/uploads/...",
    "headline": "New Collection",
    "subheadline": "Elevated streetwear for the modern wardrobe",
    "cta_text": "Shop Now",
    "cta_link": "/collections/new-arrivals"
}
```

### Add Collection Page

1. Duplicate collection template in Elementor
2. Update collection-specific content
3. Set featured image
4. Configure SEO metadata
5. Publish and verify mobile rendering

### Update Navigation

```python
# Menu structure
wp_nav_menus = {
    "primary": [
        {"title": "Shop", "url": "/shop"},
        {"title": "Collections", "url": "/collections"},
        {"title": "About", "url": "/about"},
        {"title": "Contact", "url": "/contact"}
    ],
    "footer": [
        {"title": "Shipping", "url": "/shipping"},
        {"title": "Returns", "url": "/returns"},
        {"title": "FAQ", "url": "/faq"}
    ]
}
```

---

## SEO Configuration

### Required Metadata
Every page must have:
- **Title**: `{Page Name} | SkyyRose - Luxury Streetwear`
- **Meta Description**: 150-160 characters, include "SkyyRose"
- **OG Image**: 1200x630px branded image
- **Canonical URL**: Always skyyrose.co

### Schema Markup
```json
{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "SkyyRose",
    "url": "https://skyyrose.co",
    "logo": "https://skyyrose.co/logo.png",
    "sameAs": [
        "https://instagram.com/skyyrose",
        "https://twitter.com/skyyrose"
    ]
}
```

---

## Performance Requirements

### Core Web Vitals Targets
| Metric | Target | Action if Failed |
|--------|--------|------------------|
| LCP | < 2.5s | Optimize hero image |
| FID | < 100ms | Defer non-critical JS |
| CLS | < 0.1 | Set image dimensions |

### Caching Strategy
- Page cache: 1 hour
- Browser cache: 1 week for static assets
- CDN: Enabled for all media

---

## Backup & Recovery

### Automated Backups
- **Frequency**: Daily
- **Retention**: 30 days
- **Location**: Off-site storage

### Recovery Procedure
1. Identify restore point needed
2. Notify team of maintenance window
3. Restore from backup
4. Verify functionality
5. Clear all caches
6. Log recovery in `/logs/`

---

## Security Protocols

### Plugin Updates
- Review changelogs before updating
- Test on staging first
- Update during low-traffic periods
- Verify site functionality post-update

### Access Control
- Use strong, unique passwords
- Enable 2FA for all admin accounts
- Review user access quarterly
- Remove unused accounts immediately

---

## Logging Requirements

All WordPress operations must be logged to `/logs/wordpress_ops.log`:

```json
{
    "timestamp": "2025-12-02T10:30:00Z",
    "action": "page_update",
    "page_id": 1234,
    "page_title": "New Collection",
    "agent": "content_agent",
    "changes": ["hero_image", "headline"],
    "status": "success"
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| White screen | PHP error | Check error logs, increase memory |
| Slow load | Large images | Compress and convert to WebP |
| 404 errors | Permalink issue | Resave permalinks |
| Plugin conflict | Update broke site | Deactivate recent plugins |

### Emergency Contacts
- Hosting support: [In .env]
- WordPress expert: [In .env]
- Escalation: See `escalation_protocol.md`

---

**Last Updated**: 2025-12-02
**Owner**: DevOps Team
**Review Cycle**: Monthly
