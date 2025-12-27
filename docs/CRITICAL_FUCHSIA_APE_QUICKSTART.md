# Critical Fuchsia Ape - Quick Start Guide

## Endpoint Information

- **URL**: `https://critical-fuchsia-ape.fastmcp.app/mcp`
- **Authentication**: Bearer token (HTTP Authorization header)
- **Server**: CloudFront (CDN) backed by FastMCP
- **Status**: ✅ Active and responding

## Setup Steps

### Step 1: Get Your API Key

Since you've already authenticated to critical-fuchsia-ape via `/mcp`, you should have access to an API key.

**Options:**

- Check your critical-fuchsia-ape dashboard/console
- Look in environment variables or config files
- Contact critical-fuchsia-ape support for your key

### Step 2: Configure DevSkyy MCP

**Option A: Using the template file (Recommended)**

```bash
# Copy the template
cp .env.critical-fuchsia-ape .env

# Edit and add your API key
nano .env
# Or use your preferred editor
```

**Option B: Create a new .env file**

```bash
cat > .env << 'EOF'
MCP_BACKEND=critical-fuchsia-ape
CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app/mcp
CRITICAL_FUCHSIA_APE_KEY=your-api-key-here
EOF
```

**Option C: Use environment variables directly**

```bash
export MCP_BACKEND=critical-fuchsia-ape
export CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app/mcp
export CRITICAL_FUCHSIA_APE_KEY=your-api-key-here
```

### Step 3: Start the MCP Server

```bash
# With .env file
python3 devskyy_mcp.py

# Or with environment variables
export CRITICAL_FUCHSIA_APE_KEY="your-key-here"
python3 devskyy_mcp.py
```

### Step 4: Verify Configuration

You should see output like:

```
═══════════════════════════════════════════════════════════
   DevSkyy MCP Server v1.0.0
   Industry-First Multi-Agent AI Platform Integration

   54 AI Agents • Enterprise Security • Multi-Model AI

═══════════════════════════════════════════════════════════

✓ Configuration:
   Backend: CRITICAL-FUCHSIA-APE
   API URL: https://critical-fuchsia-ape.fastmcp.app/mcp
   API Key: Set ✓

🔧 Tools Available:
   • devskyy_scan_code
   • devskyy_fix_code
   ... (and 11 more tools)

Starting MCP server on stdio...
```

## Configuration Files

### `.env.critical-fuchsia-ape` (Template)

Pre-configured template with the critical-fuchsia-ape endpoint:

```bash
cat .env.critical-fuchsia-ape
```

### `.env` (Your actual configuration)

Copy the template and add your API key:

```bash
cp .env.critical-fuchsia-ape .env
# Edit .env to add CRITICAL_FUCHSIA_APE_KEY
```

## Using with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy-critical-fuchsia-ape": {
      "command": "python",
      "args": ["/absolute/path/to/DevSkyy/devskyy_mcp.py"],
      "env": {
        "MCP_BACKEND": "critical-fuchsia-ape",
        "CRITICAL_FUCHSIA_APE_URL": "https://critical-fuchsia-ape.fastmcp.app/mcp",
        "CRITICAL_FUCHSIA_APE_KEY": "${CRITICAL_FUCHSIA_APE_KEY}"
      }
    }
  }
}
```

Then restart Claude Desktop.

## Troubleshooting

### Connection Refused

```bash
# Verify the endpoint is reachable
curl -I https://critical-fuchsia-ape.fastmcp.app/mcp

# Should return HTTP 401 (which means it's working, just needs auth)
```

### Authentication Failed (401)

```bash
# Verify API key is set
echo $CRITICAL_FUCHSIA_APE_KEY

# Test with curl
curl -H "Authorization: Bearer $CRITICAL_FUCHSIA_APE_KEY" \
     https://critical-fuchsia-ape.fastmcp.app/mcp/health
```

### Invalid API Key

- Check that the key is correct (no extra spaces)
- Ensure it's a valid Bearer token for critical-fuchsia-ape
- Contact support if the key has expired

### Other Issues

See the full guide: `docs/CRITICAL_FUCHSIA_APE_SETUP.md`

## Available Tools

All 13 DevSkyy tools work with critical-fuchsia-ape:

```
✓ devskyy_scan_code
✓ devskyy_fix_code
✓ devskyy_self_healing
✓ devskyy_generate_wordpress_theme
✓ devskyy_ml_prediction
✓ devskyy_manage_products
✓ devskyy_dynamic_pricing
✓ devskyy_generate_3d_from_description
✓ devskyy_generate_3d_from_image
✓ devskyy_marketing_campaign
✓ devskyy_multi_agent_workflow
✓ devskyy_system_monitoring
✓ devskyy_list_agents
```

## Testing

### Manual Test

```bash
# Start the MCP server
python3 devskyy_mcp.py &

# In another terminal, use the MCP client
npx @modelcontextprotocol/inspector python /path/to/devskyy_mcp.py
```

### With Claude

```bash
# Start the server, then ask Claude:
# "Call the devskyy_list_agents tool"
```

## Security Notes

- ⚠️ Keep your `CRITICAL_FUCHSIA_APE_KEY` private
- ⚠️ Don't commit `.env` to git (it's already in `.gitignore`)
- ⚠️ Use environment variables in production, not files
- ⚠️ Rotate API keys regularly

## Next Steps

1. ✅ Get your critical-fuchsia-ape API key
2. ✅ Configure `.env` file
3. ✅ Start the MCP server: `python3 devskyy_mcp.py`
4. ✅ Integrate with Claude Desktop or your MCP client
5. ✅ Start using the 13 DevSkyy tools!

---

**Endpoint**: <https://critical-fuchsia-ape.fastmcp.app/mcp>
**Status**: Active ✅
**Last Updated**: 2025-12-24
