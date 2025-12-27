# Quick Start Guide: OpenAI MCP Server

Get started with the DevSkyy OpenAI MCP Server in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- DevSkyy API key (optional, for agent integration)

## Step 1: Clone Repository

```bash
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy
```

## Step 2: Install Dependencies

### Option A: Using pip (recommended)

```bash
pip install fastmcp httpx pydantic openai python-jose[cryptography]
```

### Option B: Using project dependencies

```bash
pip install -e ".[all]"
```

### Option C: Using uv (fastest)

```bash
uv pip install fastmcp httpx pydantic openai python-jose[cryptography]
```

## Step 3: Set Environment Variables

### Linux/macOS

```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
export DEVSKYY_API_KEY="your-devskyy-key-here"  # Optional
```

### Windows (PowerShell)

```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key-here"
$env:DEVSKYY_API_KEY="your-devskyy-key-here"  # Optional
```

### Windows (Command Prompt)

```cmd
set OPENAI_API_KEY=sk-your-openai-api-key-here
set DEVSKYY_API_KEY=your-devskyy-key-here
```

## Step 4: Test the Server

### Validate installation

```bash
python test_server.py
```

You should see:

```
✅ All validation checks passed!
```

### Run the server

```bash
python server.py
```

You should see:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   DevSkyy OpenAI MCP Server v1.0.0                          ║
║   Model Context Protocol for OpenAI Integration             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

✅ Configuration:
   DevSkyy API: http://localhost:8000
   DevSkyy Key: Not Set ⚠️
   OpenAI Key: Set ✓

🔧 Available Tools: 7 tools ready
📚 Supported Models: GPT-4o, GPT-4o-mini, o1-preview

Starting OpenAI MCP server on stdio...
```

## Step 5: Configure Claude Desktop

### macOS

1. Locate config file:

   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. Edit or create the file:

   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Add server configuration:

   ```json
   {
     "mcpServers": {
       "devskyy-openai": {
         "command": "python",
         "args": ["/absolute/path/to/DevSkyy/server.py"],
         "env": {
           "OPENAI_API_KEY": "sk-your-key-here",
           "DEVSKYY_API_KEY": "your-key-here"
         }
       }
     }
   }
   ```

### Windows

1. Locate config file:

   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. Edit or create the file with the same configuration as macOS.

### Linux

1. Locate config file:

   ```bash
   ~/.config/Claude/claude_desktop_config.json
   ```

2. Edit or create the file with the same configuration as macOS.

## Step 6: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔨 (hammer) icon in the bottom right
4. You should see "devskyy-openai" in the list of servers

## Step 7: Test in Claude

Try these example prompts:

### Text Generation

```
Use openai_completion to explain quantum computing
```

### Code Generation

```
Use openai_code_generation to create a FastAPI endpoint for user authentication in Python
```

### Vision Analysis

```
Use openai_vision_analysis to analyze this image: [paste image URL]
```

### Model Selection

```
Use openai_model_selector to recommend the best model for complex mathematical proofs
```

### DevSkyy Agent

```
Use devskyy_agent_openai to scan code in the ./src directory
```

## Common Issues

### "Module not found: httpx"

**Solution:** Install dependencies

```bash
pip install fastmcp httpx pydantic openai python-jose[cryptography]
```

### "Authentication failed"

**Solution:** Check your API key

```bash
echo $OPENAI_API_KEY
```

### "Server not showing in Claude"

**Solution:**

1. Check the config file path is correct
2. Verify the absolute path to server.py
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### "Permission denied"

**Solution:** Make server.py executable (Linux/macOS)

```bash
chmod +x server.py
```

## Advanced Configuration

### Custom API URL

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "env": {
        "DEVSKYY_API_URL": "https://your-custom-api.com"
      }
    }
  }
}
```

### Multiple Servers

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {"OPENAI_API_KEY": "sk-key1"}
    },
    "devskyy-main": {
      "command": "python",
      "args": ["/path/to/devskyy_mcp.py"],
      "env": {"DEVSKYY_API_KEY": "key2"}
    }
  }
}
```

## Next Steps

- Read the [full documentation](SERVER_README.md)
- Explore [available tools](#available-tools)
- Check out [example use cases](#examples)
- Join our [community](#community)

## Available Tools

1. **openai_completion** - Text generation with OpenAI models
2. **openai_code_generation** - Generate code with tests and docs
3. **openai_vision_analysis** - Analyze images
4. **openai_function_calling** - Structured function calls
5. **openai_model_selector** - Intelligent model selection
6. **devskyy_agent_openai** - Access 54 DevSkyy agents
7. **openai_capabilities_info** - Get server capabilities

## Examples

### Generate Production Code

```json
{
  "description": "Create a REST API endpoint for user registration with email validation",
  "language": "python",
  "include_tests": true,
  "include_docs": true
}
```

### Analyze Product Images

```json
{
  "image_url": "https://example.com/product.jpg",
  "prompt": "Describe this product, suggest categories, and identify the brand",
  "detail_level": "high"
}
```

### Smart Model Selection

```json
{
  "task_description": "Review and optimize a complex algorithm",
  "task_type": "code_analysis",
  "optimize_for": "quality"
}
```

## Community

- GitHub: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy>
- Issues: <https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues>
- Docs: <https://docs.devskyy.com>

## Support

Having trouble? Check:

1. [Common Issues](#common-issues) above
2. [Full documentation](SERVER_README.md)
3. [GitHub Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues)

---

**Last Updated:** December 2024
**Version:** 1.0.0
**License:** Copyright © 2025 The Skyy Rose Collection LLC
