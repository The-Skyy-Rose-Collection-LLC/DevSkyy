# DevSkyy MCP Server Configuration Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install fastmcp httpx pydantic python-jose[cryptography]
```

### 2. Set Environment Variables

Copy the example environment file:

```bash
cp .env.mcp.example .env
```

Edit `.env` and fill in your credentials:

```bash
# Required
DEVSKYY_API_KEY=your-api-key-here
WORDPRESS_URL=https://skyyrose.co
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...

# Optional
HF_TOKEN=hf_...  # For LoRA training
```

### 3. Test the Server

```bash
python devskyy_mcp.py
```

You should see:

```
╔══════════════════════════════════════════════════════════════╗
║   DevSkyy MCP Server v2.0.0 - Advanced Tool Use             ║
║   Industry-First Multi-Agent AI Platform Integration        ║
╚══════════════════════════════════════════════════════════════╝

✅ Configuration:
   API URL: http://localhost:8000
   API Key: Set ✓

🔧 Tools Available: 21 tools
```

---

## Claude Desktop Integration

### Option 1: macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python3",
      "args": ["/Users/coreyfoster/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8000",
        "DEVSKYY_API_KEY": "your-api-key-here",
        "WORDPRESS_URL": "https://skyyrose.co",
        "WOOCOMMERCE_KEY": "ck_...",
        "WOOCOMMERCE_SECRET": "cs_..."
      }
    }
  }
}
```

### Option 2: Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["C:\\Users\\YourName\\DevSkyy\\devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8000",
        "DEVSKYY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Option 3: Linux

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python3",
      "args": ["/home/username/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8000",
        "DEVSKYY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Restart Claude Desktop

After editing the config file, completely quit and restart Claude Desktop for changes to take effect.

---

## Backend Configuration

The MCP server supports two backends:

### Local DevSkyy Backend (Default)

```bash
export MCP_BACKEND=devskyy
export DEVSKYY_API_URL=http://localhost:8000
export DEVSKYY_API_KEY=your-key
```

Start your local DevSkyy API server:

```bash
cd /Users/coreyfoster/DevSkyy
python main_enterprise.py
```

### FastMCP Hosted Backend

```bash
export MCP_BACKEND=critical-fuchsia-ape
export CRITICAL_FUCHSIA_APE_URL=https://critical-fuchsia-ape.fastmcp.app
export CRITICAL_FUCHSIA_APE_KEY=your-fastmcp-key
```

---

## LoRA Training Configuration

For the 4 new LoRA training tools, you need:

### 1. WooCommerce Credentials

Get these from WordPress Admin → WooCommerce → Settings → Advanced → REST API:

```bash
WORDPRESS_URL=https://skyyrose.co
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
```

### 2. HuggingFace Token (Optional)

For uploading LoRA models to HuggingFace:

```bash
HF_TOKEN=hf_...
```

Get from: <https://huggingface.co/settings/tokens>

### 3. GPU Configuration

LoRA training requires GPU (CUDA or MPS):

```bash
# For NVIDIA GPUs
export CUDA_VISIBLE_DEVICES=0

# For Apple Silicon
# MPS is automatically detected
```

### 4. Storage Configuration

```bash
# Where to store version database
LORA_VERSION_DB_PATH=./models/lora-versions.db

# Where to store training runs
TRAINING_PROGRESS_DIR=./models/training-runs

# Image cache directory
WOOCOMMERCE_IMAGE_CACHE=./assets/woocommerce-cache
```

---

## Tool Categories

The 21 MCP tools are organized into categories:

### Infrastructure (3 tools)

- `devskyy_scan_code` - Code analysis
- `devskyy_fix_code` - Automated fixing
- `devskyy_self_healing` - System monitoring

### AI & ML (8 tools)

- `devskyy_ml_prediction` - ML predictions
- `devskyy_generate_3d_from_description` - Text-to-3D
- `devskyy_generate_3d_from_image` - Image-to-3D
- `devskyy_train_lora_from_products` - LoRA training ⭐ NEW
- `devskyy_lora_dataset_preview` - Dataset preview ⭐ NEW
- `devskyy_lora_version_info` - Version info ⭐ NEW
- `devskyy_lora_product_history` - Product history ⭐ NEW
- `devskyy_generate_ai_model` - AI model generation

### E-Commerce (3 tools)

- `devskyy_manage_products` - Product CRUD
- `devskyy_dynamic_pricing` - Price optimization
- `devskyy_virtual_tryon` - Virtual try-on

### Marketing (1 tool)

- `devskyy_marketing_campaign` - Campaign automation

### Advanced (3 tools)

- `devskyy_generate_wordpress_theme` - Theme generation
- `devskyy_multi_agent_workflow` - Workflow orchestration
- `devskyy_system_monitoring` - Monitoring

### Discovery (1 tool)

- `devskyy_list_agents` - View all 54 agents

---

## Troubleshooting

### "Missing required package" Error

```bash
pip install fastmcp httpx pydantic python-jose[cryptography]
```

### "Authentication failed" Error

Check your API key:

```bash
echo $DEVSKYY_API_KEY
```

Make sure it's set in your Claude Desktop config.

### "Connection refused" Error

Start the DevSkyy API server:

```bash
cd /Users/coreyfoster/DevSkyy
python main_enterprise.py
```

Verify it's running:

```bash
curl http://localhost:8000/health
```

### LoRA Training "WooCommerce error"

Check WooCommerce credentials:

```bash
curl -u "ck_...:cs_..." https://skyyrose.co/wp-json/wc/v3/products
```

### Tools Not Showing in Claude

1. Check Claude Desktop config path is correct
2. Restart Claude Desktop completely (Quit → Reopen)
3. Check MCP server logs for errors
4. Verify Python path: `which python3`

### "Request timed out" Error

Increase timeout:

```bash
export REQUEST_TIMEOUT=120
```

Or in Claude Desktop config:

```json
"env": {
  "REQUEST_TIMEOUT": "120"
}
```

---

## Advanced Configuration

### Using a Virtual Environment

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastmcp httpx pydantic python-jose[cryptography]

# Update Claude Desktop config
{
  "command": "/Users/coreyfoster/DevSkyy/venv/bin/python",
  "args": ["/Users/coreyfoster/DevSkyy/devskyy_mcp.py"]
}
```

### Custom API Endpoints

Override default endpoints:

```bash
export DEVSKYY_API_URL=https://api.devskyy.com
export DEVSKYY_API_ENDPOINT_LORA=/api/v2/lora  # Custom LoRA endpoint
```

### Load Balancing (Multiple MCP Servers)

```json
{
  "mcpServers": {
    "devskyy-primary": {
      "command": "python3",
      "args": ["/path/to/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8000"
      }
    },
    "devskyy-backup": {
      "command": "python3",
      "args": ["/path/to/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_URL": "http://localhost:8001"
      }
    }
  }
}
```

---

## Security Best Practices

### 1. Never Commit Secrets

Add to `.gitignore`:

```
.env
.env.local
.env.mcp
claude_desktop_config.json
*_secret*
*_key*
```

### 2. Use Environment Variables

Never hardcode credentials in code:

```python
# ❌ Bad
API_KEY = "sk-1234567890"

# ✅ Good
API_KEY = os.getenv("DEVSKYY_API_KEY", "")
```

### 3. Rotate Keys Regularly

Update API keys every 90 days:

- WooCommerce keys
- DevSkyy API keys
- HuggingFace tokens

### 4. Use Read-Only Keys When Possible

For monitoring and querying, use read-only credentials:

```bash
WOOCOMMERCE_KEY_READONLY=ck_readonly_...
```

---

## Testing the LoRA Tools

### 1. Preview Dataset

```
Use devskyy_lora_dataset_preview with:
- collections: ["BLACK_ROSE"]
- max_products: 10
```

Expected output:

```
Total Products: 10
Total Images: 45
Collections:
  - BLACK_ROSE: 10 products
Estimated Training Time: ~1.5 hours
```

### 2. Train LoRA

```
Use devskyy_train_lora_from_products with:
- collections: ["BLACK_ROSE"]
- max_products: 10
- epochs: 50
- version: "v1.0.0-test"
```

Expected output:

```
Training Started: v1.0.0-test
Dataset: 10 products, 45 images
Model Path: ./models/skyyrose-luxury-lora
Monitor: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor
```

### 3. Check Version Info

```
Use devskyy_lora_version_info with:
- version: "v1.0.0-test"
```

### 4. Check Product History

```
Use devskyy_lora_product_history with:
- sku: "SRS-BR-001"
```

---

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/devskyy-mcp.service`:

```ini
[Unit]
Description=DevSkyy MCP Server
After=network.target

[Service]
Type=simple
User=devskyy
WorkingDirectory=/opt/devskyy
EnvironmentFile=/opt/devskyy/.env
ExecStart=/opt/devskyy/venv/bin/python /opt/devskyy/devskyy_mcp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable devskyy-mcp
sudo systemctl start devskyy-mcp
sudo systemctl status devskyy-mcp
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY devskyy_mcp.py .
COPY .env .

CMD ["python", "devskyy_mcp.py"]
```

Build and run:

```bash
docker build -t devskyy-mcp .
docker run -p 8000:8000 --env-file .env devskyy-mcp
```

---

## Support

- **Documentation**: <https://docs.devskyy.com/mcp>
- **API Reference**: <http://localhost:8000/docs>
- **Issues**: <https://github.com/devskyy/devskyy/issues>
- **Email**: <support@skyyrose.co>

---

**Version**: 2.0.0
**Last Updated**: 2026-01-03
**Author**: DevSkyy Platform Team
