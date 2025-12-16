# DevSkyy OpenAI MCP Server - Quick Start Guide

Get up and running with the DevSkyy OpenAI MCP Server in 5 minutes.

## Prerequisites

- Python 3.11+
- OpenAI API key
- DevSkyy platform access (optional)

## 1. Environment Setup

### Get OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new API key
3. Copy the key (starts with `sk-`)

### Set Environment Variables

**macOS/Linux:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
export DEVSKYY_API_KEY="your-devskyy-key"  # Optional
```

**Windows:**
```cmd
set OPENAI_API_KEY=sk-your-key-here
set DEVSKYY_API_KEY=your-devskyy-key
```

**Or create `.env` file:**
```env
OPENAI_API_KEY=sk-your-key-here
DEVSKYY_API_KEY=your-devskyy-key
```

## 2. Install Dependencies

```bash
pip install openai mcp pydantic python-dotenv
```

## 3. Test the Server

```bash
python server.py
```

You should see:
```
INFO:__main__:Starting DevSkyy OpenAI MCP Server...
```

## 4. Claude Desktop Integration

### Find Config File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Add Server Configuration

```json
{
  "mcpServers": {
    "devskyy-openai": {
      "command": "python",
      "args": ["/full/path/to/server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "DEVSKYY_API_KEY": "your-devskyy-key"
      }
    }
  }
}
```

### Restart Claude Desktop

Close and reopen Claude Desktop to load the new server.

## 5. Test Integration

In Claude Desktop, try:

```
Use the openai_completion tool to explain quantum computing in simple terms using GPT-4o.
```

## 6. Available Tools

| Tool | Description | Best For |
|------|-------------|----------|
| `openai_completion` | Text generation | General tasks, explanations |
| `openai_code_generation` | Code with tests/docs | Development tasks |
| `openai_vision_analysis` | Image analysis | Visual content analysis |
| `openai_function_calling` | Structured outputs | API integrations |
| `openai_model_selector` | Choose optimal model | Task optimization |
| `devskyy_agent_openai` | DevSkyy integration | Platform-specific tasks |
| `openai_capabilities_info` | Model information | Learning about capabilities |

## 7. Example Workflows

### Code Generation
```
Use openai_code_generation to create a Python FastAPI endpoint for user registration with email validation, password hashing, and database storage. Include tests and documentation.
```

### Image Analysis
```
Use openai_vision_analysis to analyze this product image: https://example.com/product.jpg and provide a detailed description for an e-commerce listing.
```

### Smart Model Selection
```
Use openai_model_selector to recommend the best model for "solving complex mathematical word problems involving calculus" with quality priority.
```

## Troubleshooting

### Server Won't Start
- Check `OPENAI_API_KEY` is set correctly
- Verify Python version is 3.11+
- Install missing dependencies: `pip install -r requirements.txt`

### Claude Can't Find Server
- Use absolute path in `claude_desktop_config.json`
- Check file permissions on `server.py`
- Restart Claude Desktop after config changes

### API Errors
- Verify OpenAI API key has credits
- Check internet connection
- Review OpenAI usage limits

### Performance Issues
- Use `gpt-4o-mini` for faster responses
- Reduce `max_tokens` for shorter outputs
- Check OpenAI service status

## Next Steps

1. **Explore Tools**: Try each of the 7 available tools
2. **DevSkyy Integration**: Connect with your DevSkyy agents
3. **Custom Workflows**: Build complex multi-tool workflows
4. **Production Setup**: Configure logging and monitoring

## Support

- **Documentation**: See `SERVER_README.md` for detailed API reference
- **Issues**: Report bugs in the DevSkyy repository
- **DevSkyy Platform**: Contact support for agent integration help

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure key management
- Regularly rotate API keys
- Monitor OpenAI usage and billing

---

**Ready to build with AI?** Start with simple completions and work your way up to complex multi-agent workflows!
