# SkyyRose Virtual Experiences - MCP Integration Guide

## Overview

Three immersive SkyyRose 3D experiences are available on your local WordPress development server at `http://localhost:8882`. These virtual experiences showcase the SkyyRose collections through interactive Three.js-powered environments.

## Virtual Experiences

### 1. Black Rose Collection
**URL**: `http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html`

- **Theme**: Dark elegance and gothic luxury
- **Description**: Limited edition collection with bold, mysterious design
- **Features**: Interactive 3D models, immersive lighting, premium textures
- **Collection Type**: Limited/Premium

### 2. Love Hurts Collection
**URL**: `http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html`

- **Theme**: Emotional expression and vulnerability
- **Description**: Bold, statement-making pieces for self-expression
- **Features**: Dynamic animations, responsive design, unique interactive elements
- **Collection Type**: Statement/Emotional

### 3. Signature Collection
**URL**: `http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html`

- **Theme**: Timeless essentials with luxury details
- **Description**: Core collection with rose gold accents and premium finishes
- **Features**: Clean design, premium materials showcase, interactive details
- **Collection Type**: Essentials/Timeless

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# WordPress Development Server
WORDPRESS_URL=http://localhost:8882

# SkyyRose Virtual Experiences
SKYYROSE_BLACK_ROSE_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
SKYYROSE_LOVE_HURTS_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
SKYYROSE_SIGNATURE_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html
```

### Pre-configured Template

Use the included template:

```bash
cp .env.skyyrose-experiences .env
# Edit .env to add your MCP credentials
```

## Integration with DevSkyy MCP

### Using with Critical Fuchsia Ape Backend

The SkyyRose experiences work seamlessly with the DevSkyy MCP server:

```bash
# Start with both configurations
export CRITICAL_FUCHSIA_APE_KEY="your-key"
export SKYYROSE_BLACK_ROSE_URL="http://localhost:8882/..."
export SKYYROSE_LOVE_HURTS_URL="http://localhost:8882/..."
export SKYYROSE_SIGNATURE_URL="http://localhost:8882/..."

python3 devskyy_mcp.py
```

### MCP Tools for Experiences

These tools work with the SkyyRose experiences:

1. **devskyy_generate_3d_from_description**
   - Generate 3D models for Black Rose, Love Hurts, Signature collections
   - Output integrates with experience files

2. **devskyy_generate_3d_from_image**
   - Create 3D models from product images
   - Deploy to existing experience environments

3. **devskyy_generate_wordpress_theme**
   - Generate landing pages for each collection
   - Link to corresponding virtual experiences

4. **devskyy_marketing_campaign**
   - Create campaigns promoting the experiences
   - Drive traffic to collection pages

## Local Development Setup

### Prerequisites

```bash
# 1. WordPress running on localhost:8882
# 2. skyyrose-virtual-experience plugin installed
# 3. Three.js experiences loaded in /wp-content/plugins/
```

### Verify Experiences

```bash
# Test connectivity to each experience
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
# Should return: 200

curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
# Should return: 200

curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html
# Should return: 200
```

### View in Browser

Open each URL directly:
- **Black Rose**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
- **Love Hurts**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
- **Signature**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html

## File Structure

```
/wp-content/plugins/skyyrose-virtual-experience/
├── experiences/
│   ├── skyyrose-black-rose-final.html    ✓ Available
│   ├── skyyrose-love-hurts-final.html    ✓ Available
│   ├── skyyrose-signature-final.html     ✓ Available
│   ├── assets/
│   │   ├── models/     (3D GLB/GLTF files)
│   │   ├── textures/   (Material textures)
│   │   ├── audio/      (Background music)
│   │   └── fonts/      (Typography)
│   └── scripts/
│       ├── three.js    (3D library)
│       ├── experience.js
│       └── controls.js

src/collections/
├── black-rose/         (Three.js collection code)
├── love-hurts/
├── signature/
├── showroom/
└── runway/
```

## API Integration

### Accessing Experiences via MCP

```python
# Example: Get experience URL from environment
from devskyy_mcp import mcp

black_rose_url = os.getenv("SKYYROSE_BLACK_ROSE_URL")
love_hurts_url = os.getenv("SKYYROSE_LOVE_HURTS_URL")
signature_url = os.getenv("SKYYROSE_SIGNATURE_URL")

# Use with marketing campaigns
campaigns = {
    "black_rose": {
        "name": "Black Rose Collection",
        "experience_url": black_rose_url,
        "collection_id": "BLACK_ROSE"
    },
    "love_hurts": {
        "name": "Love Hurts Collection",
        "experience_url": love_hurts_url,
        "collection_id": "LOVE_HURTS"
    },
    "signature": {
        "name": "Signature Collection",
        "experience_url": signature_url,
        "collection_id": "SIGNATURE"
    }
}
```

## Collection Metadata

### Black Rose
```json
{
  "id": "BLACK_ROSE",
  "name": "Black Rose Collection",
  "description": "Dark elegance limited editions",
  "theme": "Gothic luxury",
  "url": "http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html",
  "brand_color": "#1A1A1A",
  "accent_color": "#B76E79"
}
```

### Love Hurts
```json
{
  "id": "LOVE_HURTS",
  "name": "Love Hurts Collection",
  "description": "Emotional expression through fashion",
  "theme": "Statement pieces",
  "url": "http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html",
  "brand_color": "#8B0000",
  "accent_color": "#FFD700"
}
```

### Signature
```json
{
  "id": "SIGNATURE",
  "name": "Signature Collection",
  "description": "Timeless essentials with luxury details",
  "theme": "Premium essentials",
  "url": "http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html",
  "brand_color": "#B76E79",
  "accent_color": "#C0A080"
}
```

## Troubleshooting

### Experience Not Loading

```bash
# 1. Verify WordPress is running
curl http://localhost:8882/wp-admin/

# 2. Check plugin is activated
curl http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/

# 3. Check file permissions
ls -la /wp-content/plugins/skyyrose-virtual-experience/experiences/

# 4. Clear browser cache
# (Hard refresh: Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
```

### JavaScript Errors

Check browser console (F12) for:
- Three.js library loading issues
- Missing texture files
- CORS errors
- WebGL support

### Performance Issues

- Close other tabs/applications
- Use Chrome for best performance
- Check GPU acceleration is enabled
- Reduce quality settings in experience

## Development Workflow

### 1. Start WordPress
```bash
docker-compose up -d wordpress
# Wait for http://localhost:8882 to be ready
```

### 2. Start DevSkyy MCP
```bash
export CRITICAL_FUCHSIA_APE_KEY="your-key"
python3 devskyy_mcp.py
```

### 3. Access Experiences
- Black Rose: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
- Love Hurts: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
- Signature: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html

### 4. Generate 3D Assets
```bash
# Use MCP to generate new 3D models for collections
curl -X POST http://localhost:8000/api/v1/3d/generate-from-description \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Heart Rose Bomber",
    "collection": "BLACK_ROSE",
    "garment_type": "bomber",
    "additional_details": "Rose gold zipper, embroidered details",
    "output_format": "glb"
  }'
```

## Deployment

For production deployment:

1. **Update WordPress URL**
   ```bash
   export WORDPRESS_URL=https://skyyrose.com
   ```

2. **Update Experience URLs**
   ```bash
   export SKYYROSE_BLACK_ROSE_URL=https://skyyrose.com/experiences/black-rose/
   export SKYYROSE_LOVE_HURTS_URL=https://skyyrose.com/experiences/love-hurts/
   export SKYYROSE_SIGNATURE_URL=https://skyyrose.com/experiences/signature/
   ```

3. **Deploy MCP Server**
   ```bash
   # Use production backend
   export MCP_BACKEND=critical-fuchsia-ape
   export CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app/mcp
   ```

## Resources

- **WordPress Plugin**: `/wp-content/plugins/skyyrose-virtual-experience/`
- **Three.js Collections**: `src/collections/`
- **Brand Guidelines**: `docs/BRAND_GUIDELINES.md`
- **3D Assets**: `generated_assets/`
- **MCP Documentation**: `docs/CRITICAL_FUCHSIA_APE_SETUP.md`

## Support

For issues with:
- **Experiences**: Check `/wp-content/plugins/skyyrose-virtual-experience/`
- **MCP Integration**: See `docs/CRITICAL_FUCHSIA_APE_SETUP.md`
- **3D Generation**: Use `devskyy_generate_3d_from_description` tool
- **WordPress**: See `docs/WORDPRESS_INTEGRATION.md`

---

**Last Updated**: 2025-12-24  
**Status**: ✅ All 3 Experiences Available  
**Collections**: BLACK_ROSE, LOVE_HURTS, SIGNATURE
