# FastMCP Deployment Guide

## Deploying DevSkyy MCP to critical-fuchsia-ape

This guide covers deploying the full DevSkyy MCP server (17 tools) to the `critical-fuchsia-ape.fastmcp.app` endpoint.

---

## Quick Start

```bash
# Install FastMCP CLI and deploy in one command
./scripts/deploy_to_fastmcp.sh --install-cli

# Or test locally first
./scripts/deploy_to_fastmcp.sh --test-only
```

---

## What Gets Deployed

### Current State

- **critical-fuchsia-ape**: Only has `echo_tool`

### After Deployment

- **critical-fuchsia-ape**: All 17 DevSkyy tools including:
  - `devskyy_scan_code` - Code analysis
  - `devskyy_fix_code` - Automated fixing
  - `devskyy_self_healing` - System health monitoring
  - `devskyy_generate_wordpress_theme` - Theme generation
  - `devskyy_ml_prediction` - ML predictions
  - `devskyy_manage_products` - Product management
  - `devskyy_dynamic_pricing` - Price optimization
  - `devskyy_generate_3d_from_description` - Text-to-3D
  - `devskyy_generate_3d_from_image` - Image-to-3D
  - `devskyy_virtual_tryon` - Virtual try-on
  - `devskyy_batch_virtual_tryon` - Batch try-on
  - `devskyy_generate_ai_model` - AI model generation
  - `devskyy_virtual_tryon_status` - Try-on status
  - `devskyy_marketing_campaign` - Marketing automation
  - `devskyy_multi_agent_workflow` - Multi-agent orchestration
  - `devskyy_system_monitoring` - System monitoring
  - `devskyy_list_agents` - Agent directory

---

## Deployment Methods

### Method 1: Automated Script (Recommended)

```bash
# Full deployment with CLI installation
./scripts/deploy_to_fastmcp.sh --install-cli

# Deploy only (CLI already installed)
./scripts/deploy_to_fastmcp.sh

# Test without deploying
./scripts/deploy_to_fastmcp.sh --test-only
```

### Method 2: FastMCP CLI Manual

```bash
# Install FastMCP CLI
pip3 install fastmcp

# Deploy
fastmcp deploy devskyy_mcp.py \
  --name critical-fuchsia-ape \
  --config fastmcp.config.json

# Check status
fastmcp status critical-fuchsia-ape
```

### Method 3: FastMCP Dashboard

1. Visit: <https://fastmcp.com/dashboard>
2. Click: "New Deployment" or "Update App"
3. Upload: `devskyy_mcp.py`
4. Set app name: `critical-fuchsia-ape`
5. Configure environment variables (see below)
6. Click: "Deploy"

### Method 4: GitHub Integration

1. Connect your GitHub repo at: <https://fastmcp.com/github>
2. Select the `DevSkyy` repository
3. Set deployment file: `devskyy_mcp.py`
4. Set app name: `critical-fuchsia-ape`
5. Auto-deploy on push to `main` branch

---

## Environment Variables

### Required

```bash
CRITICAL_FUCHSIA_APE_KEY=your-api-key-here
MCP_BACKEND=critical-fuchsia-ape
```

### Optional (for backend API access)

```bash
DEVSKYY_API_KEY=sk-xxx              # DevSkyy API access
OPENAI_API_KEY=sk-xxx               # OpenAI integration
ANTHROPIC_API_KEY=sk-ant-xxx        # Anthropic integration
GOOGLE_AI_API_KEY=xxx               # Google AI integration
TRIPO_API_KEY=xxx                   # 3D generation (Tripo3D)
FASHN_API_KEY=xxx                   # Virtual try-on (FASHN)
```

### Setting Environment Variables

#### Via FastMCP Dashboard

1. Go to: <https://fastmcp.com/dashboard/critical-fuchsia-ape/settings>
2. Navigate to: "Environment Variables"
3. Add each variable
4. Save and redeploy

#### Via FastMCP CLI

```bash
fastmcp env set critical-fuchsia-ape CRITICAL_FUCHSIA_APE_KEY "your-key"
fastmcp env set critical-fuchsia-ape DEVSKYY_API_KEY "sk-xxx"
```

---

## Verification

### 1. Health Check

```bash
curl https://critical-fuchsia-ape.fastmcp.app/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "tools": 17
}
```

### 2. List Tools

```bash
curl https://critical-fuchsia-ape.fastmcp.app/tools
```

Should return all 17 tools, not just `echo_tool`.

### 3. Test a Tool

```bash
curl -X POST https://critical-fuchsia-ape.fastmcp.app/tools/devskyy_list_agents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Claude Desktop Configuration

After deployment, update your Claude Desktop config:

### `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["/Users/coreyfoster/DevSkyy/devskyy_mcp.py"],
      "env": {
        "MCP_BACKEND": "critical-fuchsia-ape",
        "CRITICAL_FUCHSIA_APE_URL": "https://critical-fuchsia-ape.fastmcp.app",
        "CRITICAL_FUCHSIA_APE_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or use the `.mcp.json` in this repo:

### `.mcp.json`

```json
{
  "mcpServers": {
    "devskyy-critical-fuchsia-ape": {
      "command": "python",
      "args": ["devskyy_mcp.py"],
      "env": {
        "MCP_BACKEND": "critical-fuchsia-ape",
        "CRITICAL_FUCHSIA_APE_URL": "https://critical-fuchsia-ape.fastmcp.app",
        "CRITICAL_FUCHSIA_APE_KEY": "${CRITICAL_FUCHSIA_APE_KEY}"
      }
    }
  }
}
```

---

## Troubleshooting

### Deployment Fails

```bash
# Check logs
fastmcp logs critical-fuchsia-ape

# Verify Python version (3.11+ required)
python3 --version

# Check for syntax errors
python3 -m py_compile devskyy_mcp.py
```

### Tools Not Appearing

1. Verify deployment succeeded: `fastmcp status critical-fuchsia-ape`
2. Check environment variables are set correctly
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`

### API Authentication Errors

1. Ensure `CRITICAL_FUCHSIA_APE_KEY` is set in FastMCP dashboard
2. Verify the key matches in your Claude Desktop config
3. Check that the backend API (`DEVSKYY_API_URL`) is accessible

### Still Seeing echo_tool Only

This means the old server is still running. To fix:

1. **Redeploy**: Run deployment script again
2. **Force update**: In FastMCP dashboard, click "Redeploy"
3. **Clear cache**: `fastmcp cache clear critical-fuchsia-ape`
4. **Wait**: Deployment can take 1-2 minutes to propagate

---

## Monitoring

### Real-time Logs

```bash
fastmcp logs critical-fuchsia-ape --follow
```

### Metrics

```bash
fastmcp metrics critical-fuchsia-ape
```

### Status Dashboard

<https://fastmcp.com/dashboard/critical-fuchsia-ape>

---

## Rollback

If something goes wrong, rollback to previous version:

```bash
fastmcp rollback critical-fuchsia-ape
```

Or redeploy the previous version:

```bash
git checkout <previous-commit>
./scripts/deploy_to_fastmcp.sh
```

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy-fastmcp.yml`:

```yaml
name: Deploy to FastMCP

on:
  push:
    branches: [main]
    paths:
      - 'devskyy_mcp.py'
      - 'fastmcp.config.json'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install FastMCP CLI
        run: pip install fastmcp

      - name: Deploy to FastMCP
        env:
          FASTMCP_API_KEY: ${{ secrets.FASTMCP_API_KEY }}
        run: |
          fastmcp deploy devskyy_mcp.py \
            --name critical-fuchsia-ape \
            --config fastmcp.config.json

      - name: Verify Deployment
        run: |
          sleep 10
          curl -f https://critical-fuchsia-ape.fastmcp.app/health
```

---

## Cost & Limits

### FastMCP Pricing

- **Free Tier**: 1,000 requests/month
- **Starter**: $29/month - 100,000 requests
- **Pro**: $99/month - 1M requests
- **Enterprise**: Custom pricing

### Rate Limits

- Free: 10 req/min
- Starter: 100 req/min
- Pro: 1,000 req/min

---

## Support

- **FastMCP Docs**: <https://docs.fastmcp.com>
- **DevSkyy Issues**: <https://github.com/damBruh/DevSkyy/issues>
- **Email**: <support@skyyrose.com>

---

## Related Files

- `devskyy_mcp.py` - Main MCP server (17 tools)
- `fastmcp.config.json` - Deployment configuration
- `scripts/deploy_to_fastmcp.sh` - Automated deployment script
- `.mcp.json` - MCP server registry
- `scripts/setup_critical_fuchsia_ape.sh` - Initial setup script

---

**Version**: 1.0.0
**Last Updated**: 2026-01-02
**Status**: Production Ready
