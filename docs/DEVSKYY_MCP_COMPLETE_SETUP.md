# DevSkyy MCP - Complete Setup Guide

Complete setup guide for DevSkyy MCP with critical-fuchsia-ape backend and SkyyRose virtual experiences.

## Quick Reference

| Component | Value | Status |
|-----------|-------|--------|
| **MCP Backend** | critical-fuchsia-ape | ✅ Configured |
| **Backend URL** | https://critical-fuchsia-ape.fastmcp.app/mcp | ✅ Active |
| **WordPress Server** | http://localhost:8882 | ✅ Local |
| **Black Rose Experience** | http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html | ✅ Available |
| **Love Hurts Experience** | http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html | ✅ Available |
| **Signature Experience** | http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html | ✅ Available |

## 5-Minute Setup

### Step 1: Configure Environment
```bash
cd /Users/coreyfoster/DevSkyy

# Copy the SkyyRose configuration template
cp .env.skyyrose-experiences .env

# Edit and add your critical-fuchsia-ape API key
nano .env
# Find the line: CRITICAL_FUCHSIA_APE_KEY=
# Replace with your actual key
```

### Step 2: Install Dependencies
```bash
pip3 install -r mcp/requirements.txt
```

### Step 3: Start MCP Server
```bash
python3 devskyy_mcp.py
```

You should see:
```
═══════════════════════════════════════════════════════════
   DevSkyy MCP Server v1.0.0
   Industry-First Multi-Agent AI Platform Integration

✓ Configuration:
   Backend: CRITICAL-FUCHSIA-APE
   API URL: https://critical-fuchsia-ape.fastmcp.app/mcp
   API Key: Set ✓

🔧 Tools Available:
   ✓ 13 DevSkyy Tools Ready
```

### Step 4: Access Experiences
Open in browser:
- **Black Rose**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
- **Love Hurts**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
- **Signature**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html

## Configuration Files

### Main Configuration: `.env`
```bash
# Backend
MCP_BACKEND=critical-fuchsia-ape
CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app/mcp
CRITICAL_FUCHSIA_APE_KEY=your-key-here

# WordPress & Experiences
WORDPRESS_URL=http://localhost:8882
SKYYROSE_BLACK_ROSE_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
SKYYROSE_LOVE_HURTS_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
SKYYROSE_SIGNATURE_URL=http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html
```

### Templates Available

| Template | Purpose | Usage |
|----------|---------|-------|
| `.env.critical-fuchsia-ape` | MCP Backend Config | `cp .env.critical-fuchsia-ape .env` |
| `.env.skyyrose-experiences` | Full Setup Config | `cp .env.skyyrose-experiences .env` |
| `mcp/.env.example` | Reference Template | Reference only |

## MCP Tools

All 13 DevSkyy tools are available:

### Code Management
1. **devskyy_scan_code** - Analyze code quality and security
2. **devskyy_fix_code** - Automated code fixing
3. **devskyy_self_healing** - System health monitoring

### WordPress & Content
4. **devskyy_generate_wordpress_theme** - Theme generation
5. **devskyy_generate_3d_from_description** - 3D model generation (text)
6. **devskyy_generate_3d_from_image** - 3D model generation (image)

### E-Commerce
7. **devskyy_manage_products** - Product management
8. **devskyy_dynamic_pricing** - ML price optimization
9. **devskyy_ml_prediction** - ML predictions (trends, forecasting)

### Marketing & Workflow
10. **devskyy_marketing_campaign** - Campaign automation
11. **devskyy_multi_agent_workflow** - Workflow orchestration
12. **devskyy_system_monitoring** - System monitoring
13. **devskyy_list_agents** - View all 54 agents

## SkyyRose Collections

### Collection 1: Black Rose
- **Description**: Dark elegance, limited editions
- **Theme**: Gothic luxury
- **URL**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
- **Collections Available**: `BLACK_ROSE`

### Collection 2: Love Hurts
- **Description**: Emotional expression, bold statements
- **Theme**: Statement pieces
- **URL**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
- **Collections Available**: `LOVE_HURTS`

### Collection 3: Signature
- **Description**: Timeless essentials with luxury details
- **Theme**: Premium basics
- **URL**: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html
- **Collections Available**: `SIGNATURE`

## Integration Examples

### Generate 3D Model for Black Rose Collection
```bash
# Using MCP tool
curl -X POST http://localhost:8000/api/v1/3d/generate-from-description \
  -H "Authorization: Bearer $CRITICAL_FUCHSIA_APE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Rose Gold Hoodie",
    "collection": "BLACK_ROSE",
    "garment_type": "hoodie",
    "additional_details": "Rose gold threads, embroidered rose motif",
    "output_format": "glb"
  }'
```

### Create Marketing Campaign
```bash
# Link experiences to marketing campaigns
curl -X POST http://localhost:8000/api/v1/marketing/campaign \
  -H "Authorization: Bearer $CRITICAL_FUCHSIA_APE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_type": "multi_channel",
    "target_audience": {"segment": "high_value"},
    "content_template": "Check out our new Black Rose collection: http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html"
  }'
```

## Deployment

### Local Development
```bash
# 1. Ensure WordPress is running
curl http://localhost:8882/wp-admin/

# 2. Start MCP server
python3 devskyy_mcp.py

# 3. Access experiences
open http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
```

### Production
```bash
# 1. Update URLs
export WORDPRESS_URL=https://skyyrose.com
export CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app/mcp

# 2. Update experience URLs to production
export SKYYROSE_BLACK_ROSE_URL=https://skyyrose.com/experiences/black-rose/
export SKYYROSE_LOVE_HURTS_URL=https://skyyrose.com/experiences/love-hurts/
export SKYYROSE_SIGNATURE_URL=https://skyyrose.com/experiences/signature/

# 3. Start server with production backend
python3 devskyy_mcp.py
```

## Troubleshooting

### MCP Server Won't Start
```bash
# Check Python version
python3 --version  # Must be 3.11+

# Check dependencies
pip3 install -r mcp/requirements.txt

# Check configuration
echo $CRITICAL_FUCHSIA_APE_KEY
```

### Can't Connect to Backend
```bash
# Test endpoint
curl -I https://critical-fuchsia-ape.fastmcp.app/mcp
# Should return: HTTP/2 401 (unauthorized is fine, means it's reachable)

# Check API key
curl -H "Authorization: Bearer $CRITICAL_FUCHSIA_APE_KEY" \
     https://critical-fuchsia-ape.fastmcp.app/mcp/health
```

### Experiences Not Loading
```bash
# Check WordPress
curl http://localhost:8882/

# Check plugin
curl http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/

# Check browser console
# Open http://localhost:8882/... in browser, press F12
```

## File Structure

```
DevSkyy/
├── devskyy_mcp.py                           # Main MCP server
├── .env                                     # Your configuration (copy from template)
├── .env.critical-fuchsia-ape                # MCP-only template
├── .env.skyyrose-experiences                # Full config template
├── .mcp.json                                # MCP server registry
│
├── mcp/
│   ├── requirements.txt
│   ├── .env.example                         # Reference template
│   └── [other MCP servers]
│
├── docs/
│   ├── CRITICAL_FUCHSIA_APE_SETUP.md        # MCP setup guide
│   ├── CRITICAL_FUCHSIA_APE_QUICKSTART.md   # Quick start
│   ├── SKYYROSE_EXPERIENCES_INTEGRATION.md  # Experiences guide
│   └── DEVSKYY_MCP_COMPLETE_SETUP.md        # This file
│
└── src/collections/
    ├── black-rose/
    ├── love-hurts/
    └── signature/
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `MCP_BACKEND` | Select backend | `critical-fuchsia-ape` |
| `CRITICAL_FUCHSIA_APE_URL` | API endpoint | `https://critical-fuchsia-ape.fastmcp.app/mcp` |
| `CRITICAL_FUCHSIA_APE_KEY` | API key | Bearer token |
| `WORDPRESS_URL` | WordPress URL | `http://localhost:8882` |
| `SKYYROSE_BLACK_ROSE_URL` | Black Rose experience | URL to HTML file |
| `SKYYROSE_LOVE_HURTS_URL` | Love Hurts experience | URL to HTML file |
| `SKYYROSE_SIGNATURE_URL` | Signature experience | URL to HTML file |

## Next Steps

1. ✅ **Copy configuration**: `cp .env.skyyrose-experiences .env`
2. ✅ **Add API key**: Edit `.env` and set `CRITICAL_FUCHSIA_APE_KEY`
3. ✅ **Start server**: `python3 devskyy_mcp.py`
4. ✅ **Access experiences**: Open URLs in browser
5. ✅ **Use MCP tools**: Call tools via API or Claude
6. ✅ **Deploy**: Update URLs for production

## Support & Documentation

- **MCP Setup**: `docs/CRITICAL_FUCHSIA_APE_SETUP.md`
- **Quick Start**: `docs/CRITICAL_FUCHSIA_APE_QUICKSTART.md`
- **Experiences**: `docs/SKYYROSE_EXPERIENCES_INTEGRATION.md`
- **MCP Specification**: https://modelcontextprotocol.io

## Quick Commands

```bash
# Setup
cp .env.skyyrose-experiences .env
nano .env  # Add API key

# Start
python3 devskyy_mcp.py

# Test
curl https://critical-fuchsia-ape.fastmcp.app/mcp/health

# Access experiences
open http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-black-rose-final.html
open http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-love-hurts-final.html
open http://localhost:8882/wp-content/plugins/skyyrose-virtual-experience/experiences/skyyrose-signature-final.html
```

---

**Setup Date**: 2025-12-24  
**Status**: ✅ Ready to Configure  
**Version**: 1.0.0  
**Last Updated**: 2025-12-24
