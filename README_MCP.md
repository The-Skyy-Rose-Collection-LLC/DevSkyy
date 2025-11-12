# DevSkyy MCP Server - Quick Start Guide

## 🚀 Industry-First Multi-Agent AI Platform via MCP

The DevSkyy MCP Server exposes 54 specialized AI agents through 11 powerful tools accessible via the Model Context Protocol.

---

## ⚡ Quick Start - One-Click Installation (Recommended)

### Method 1: Deeplink Installation (Fastest - 30 Seconds)

**NEW!** Install DevSkyy MCP Server with a single click using our deeplink installer:

1. **Get your installation link:**
   ```bash
   curl "https://devskyy.com/api/v1/mcp/install?api_key=YOUR_API_KEY"
   ```

   Or visit in your browser:
   ```
   https://devskyy.com/api/v1/mcp/install?api_key=YOUR_API_KEY
   ```

2. **Click the deeplink URL** from the response (looks like `cursor://anysphere.cursor-deeplink/mcp/install?...`)

3. **Done!** Claude Desktop/Cursor will automatically configure DevSkyy MCP Server

**Example Response:**
```json
{
  "deeplink_url": "cursor://anysphere.cursor-deeplink/mcp/install?name=devskyy&config=eyJtY3BTZXJ2ZXJzIjp7ImRldnNreXkiOnsic3...",
  "cursor_url": "cursor://anysphere.cursor-deeplink/mcp/install?...",
  "installation_instructions": "# DevSkyy MCP Server - One-Click Installation..."
}
```

**Custom Installation Options:**
```bash
# Custom API URL
curl "https://devskyy.com/api/v1/mcp/install?api_key=YOUR_KEY&api_url=https://api.devskyy.com"

# Custom server name
curl "https://devskyy.com/api/v1/mcp/install?api_key=YOUR_KEY&server_name=my-devskyy"
```

---

## ⚡ Quick Start - Manual Installation (5 Minutes)

### Method 2: Manual Setup

If you prefer manual installation or the deeplink doesn't work:

### 1. Install Dependencies

```bash
cd ~/DevSkyy
pip install -r requirements_mcp.txt
```

### 2. Configure Environment Variables (.env file)

**IMPORTANT:** Always use environment variables for API keys and secrets!

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env and add your keys:**
   ```bash
   # DevSkyy MCP Server
   DEVSKYY_API_KEY=your-devskyy-api-key-here
   DEVSKYY_API_URL=http://localhost:8000

   # HuggingFace MCP (if using)
   HUGGING_FACE_TOKEN=hf_your_token_here
   ```

3. **The .env file is automatically loaded** by the MCP server
4. **.env is in .gitignore** - never commit secrets!

**Alternative - Export manually:**
```bash
export DEVSKYY_API_KEY="your-api-key-here"
export DEVSKYY_API_URL="http://localhost:8000"
export HUGGING_FACE_TOKEN="hf_your_token_here"
```

### 3. Test the Server

```bash
python devskyy_mcp.py
```

You should see:
```
╔══════════════════════════════════════════════════════════════════╗
║   DevSkyy MCP Server v1.0.0                                     ║
║   Industry-First Multi-Agent AI Platform Integration            ║
╚══════════════════════════════════════════════════════════════════╝

✅ Configuration:
   API URL: http://localhost:8000
   API Key: Set ✓

🔧 Tools Available: 11

Starting MCP server on stdio...
```

---

## 🔌 Claude Desktop Integration

### Step 1: Locate Configuration File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Add DevSkyy Configuration

Edit the file and add:

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["/Users/YOUR_USERNAME/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_KEY": "your-actual-api-key",
        "DEVSKYY_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**⚠️ IMPORTANT:**
- Use the **absolute path** to `devskyy_mcp.py`
- Replace `/Users/YOUR_USERNAME` with your actual path
- Use your real API key

### Step 3: (Optional) Add HuggingFace MCP Server

To use both DevSkyy AND HuggingFace together, add HuggingFace to your configuration:

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["/Users/YOUR_USERNAME/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_KEY": "your-devskyy-api-key",
        "DEVSKYY_API_URL": "http://localhost:8000"
      }
    },
    "hf-mcp-server": {
      "url": "https://huggingface.co/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_HF_TOKEN_FROM_ENV"
      }
    }
  }
}
```

**Best Practice - Use .env file:**
```bash
# In your .env file
DEVSKYY_API_KEY=your-key-here
HUGGING_FACE_TOKEN=hf_your_token_here
```

Then your configuration can reference them:
- For stdio servers (DevSkyy): Use the `env` section (shown above)
- For HTTP servers (HuggingFace): Replace the token manually or use the API

**Quick Way - Use Our API:**
```bash
# Generate combined config automatically
curl "https://devskyy.com/api/v1/mcp/servers/huggingface?hf_token=$HUGGING_FACE_TOKEN&devskyy_api_key=$DEVSKYY_API_KEY"
```

This returns a ready-to-use deeplink with both servers configured!

### Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔌 icon in the interface
4. Click it to see your configured servers:
   - "devskyy" with 14 tools
   - "hf-mcp-server" (if added) with HuggingFace tools

---

## 🛠️ Available Tools

### 1. **devskyy_list_agents**
List all 54 AI agents organized by category.

**Example:**
```
Can you list all available DevSkyy agents?
```

### 2. **devskyy_scan_code**
Scan code for errors, security issues, and performance bottlenecks.

**Parameters:**
- `directory`: Path to scan
- `include_security`: Security scan (default: true)
- `include_performance`: Performance analysis (default: true)
- `include_best_practices`: Best practices check (default: true)

**Example:**
```
Can you scan the ./src directory for code issues?
```

### 3. **devskyy_fix_code**
Automatically fix identified code issues.

**Parameters:**
- `issues_json`: JSON array of issues from scan

**Example:**
```
Can you fix the issues found in the last scan?
```

### 4. **devskyy_self_healing**
Run self-healing system check and auto-repair.

**Example:**
```
Run a self-healing check on the DevSkyy system.
```

### 5. **devskyy_generate_wordpress_theme**
Generate custom WordPress theme with AI.

**Parameters:**
- `brand_name`: Brand name
- `industry`: Industry type (fashion, tech, food, etc.)
- `theme_type`: elementor, gutenberg, or custom
- `color_palette`: Comma-separated hex colors
- `pages`: Comma-separated page list

**Example:**
```
Generate a WordPress theme for "StyleHub" fashion brand with colors #FF5733,#3498DB.
```

### 6. **devskyy_ml_prediction**
Make ML predictions for fashion trends, demand, pricing, or segments.

**Parameters:**
- `prediction_type`: fashion_trends, demand_forecast, price_optimize, customer_segment
- `data_json`: JSON input data

**Example:**
```json
{
  "prediction_type": "fashion_trends",
  "data_json": "{\"season\": \"spring\", \"category\": \"dresses\"}"
}
```

### 7. **devskyy_manage_products**
Manage e-commerce products.

**Parameters:**
- `action`: create, update, delete, optimize_seo, generate_variants
- `product_data_json`: Product data

**Example:**
```
Create a new product with name "Summer Dress" priced at $89.99.
```

### 8. **devskyy_dynamic_pricing**
Optimize pricing with ML.

**Parameters:**
- `product_ids`: Comma-separated IDs
- `strategy`: ml_optimized, competitor_based, demand_based, ab_test

**Example:**
```
Optimize pricing for products PROD123,PROD456 using ML strategy.
```

### 9. **devskyy_marketing_campaign**
Create automated marketing campaigns.

**Parameters:**
- `campaign_type`: email, sms, social_media, multi_channel
- `config_json`: Campaign configuration

**Example:**
```
Create an email campaign for our summer sale.
```

### 10. **devskyy_multi_agent_workflow**
Execute multi-agent workflows.

**Parameters:**
- `workflow_name`: product_launch, content_pipeline, customer_journey
- `parameters_json`: Workflow parameters
- `parallel`: Execute in parallel (default: false)

**Example:**
```
Execute a product_launch workflow for "Summer Collection 2025".
```

### 11. **devskyy_system_monitoring**
Get real-time system metrics.

**Example:**
```
Show DevSkyy system status and health metrics.
```

---

## 💡 Usage Examples

### Example 1: Complete Code Analysis
```
User: Can you scan the ./api directory for security issues and fix any problems you find?

Claude: I'll scan the code and apply fixes.
[Uses devskyy_scan_code]
[Uses devskyy_fix_code]
```

### Example 2: Product Launch Automation
```
User: Launch a new product called "Summer Dress Collection" with automated marketing.

Claude: I'll orchestrate the product launch.
[Uses devskyy_multi_agent_workflow with "product_launch"]
```

### Example 3: WordPress Theme Generation
```
User: Create a WordPress theme for my fashion boutique "Elegant Styles".

Claude: I'll generate a custom theme.
[Uses devskyy_generate_wordpress_theme]
```

---

## 🔧 Troubleshooting

### "Module not found: fastmcp"

```bash
pip install fastmcp httpx pydantic
```

### "Authentication failed"

Check your API key:
```bash
echo $DEVSKYY_API_KEY
# Should print your key
```

### Claude Desktop doesn't show the server

1. Check JSON syntax in config file
2. Verify absolute path to devskyy_mcp.py
3. Restart Claude Desktop
4. Check logs: `~/Library/Logs/Claude/` (macOS)

### Server times out

Increase timeout in `devskyy_mcp.py`:
```python
REQUEST_TIMEOUT = 120.0  # Increase to 120 seconds
```

---

## 📊 What Makes This Special

### Industry Firsts
- ✅ **Only MCP server** exposing a complete multi-agent platform
- ✅ **Only platform** with 54+ specialized AI agents via MCP
- ✅ **Only fashion e-commerce AI** with MCP integration
- ✅ **Only automated WordPress builder** via MCP

### Business Impact
- 🚀 Automate entire product launches
- 💰 ML-powered pricing optimization
- 📧 Complete marketing automation
- 🔧 Self-healing infrastructure
- 🎨 AI WordPress theme generation

---

## 🔗 API Endpoints for Developers

The DevSkyy platform provides REST API endpoints for programmatic MCP configuration management.

### GET /api/v1/mcp/install

Generate a one-click install deeplink for MCP server configuration.

**Parameters:**
- `api_key` (required): Your DevSkyy API key
- `api_url` (optional): Custom API URL (defaults to production)
- `server_name` (optional): Custom server name (defaults to "devskyy")

**Example:**
```bash
curl "https://devskyy.com/api/v1/mcp/install?api_key=YOUR_API_KEY"
```

**Response:**
```json
{
  "config": { ... },
  "deeplink_url": "cursor://anysphere.cursor-deeplink/mcp/install?name=devskyy&config=...",
  "cursor_url": "cursor://anysphere.cursor-deeplink/mcp/install?...",
  "installation_instructions": "..."
}
```

### GET /api/v1/mcp/config

Get MCP server configuration JSON only (without deeplink).

**Example:**
```bash
curl "https://devskyy.com/api/v1/mcp/config?api_key=YOUR_API_KEY"
```

**Response:**
```json
{
  "mcpServers": {
    "devskyy": {
      "command": "uvx",
      "args": ["--from", "devskyy-mcp==1.0.0", "devskyy-mcp"],
      "env": {
        "DEVSKYY_API_URL": "https://devskyy.com",
        "DEVSKYY_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

### GET /api/v1/mcp/status

Get MCP server status and capabilities (no authentication required).

**Example:**
```bash
curl "https://devskyy.com/api/v1/mcp/status"
```

**Response:**
```json
{
  "status": "active",
  "version": "1.0.0",
  "available_tools": 14,
  "agent_count": 54
}
```

### POST /api/v1/mcp/validate

Validate API key for MCP server usage (requires JWT authentication).

**Example:**
```bash
curl -X POST "https://devskyy.com/api/v1/mcp/validate?api_key=YOUR_API_KEY" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "valid": true,
  "user": "your_username",
  "role": "Developer",
  "permissions": ["mcp_access", "agent_execution", "tool_calling"],
  "message": "API key is valid and authorized for MCP server usage"
}
```

**Security Notes:**
- Per Truth Protocol Rule #5: No secrets in code - API keys passed as parameters
- Per Truth Protocol Rule #6: RBAC roles enforced - SuperAdmin, Admin, Developer, APIUser allowed
- Per Truth Protocol Rule #3: Cite standards - RFC 4648 (base64), RFC 7519 (JWT)

---

## 🎯 Next Steps

1. **Test all tools** - Try each of the 11 tools
2. **Create workflows** - Combine agents for complex tasks
3. **Monitor performance** - Use system_monitoring tool
4. **Automate processes** - Set up multi-agent workflows

---

## 📞 Support

**Documentation:**
- Full deployment guide: `MCP_DEPLOYMENT_GUIDE.md`
- Executive summary: `MCP_EXECUTIVE_SUMMARY.md`

**Need Help?**
- Email: support@devskyy.com
- Docs: https://docs.devskyy.com

---

**Version:** 1.0.0
**Last Updated:** 2025-10-24
**Python:** 3.11+
**Status:** Production Ready ✅
