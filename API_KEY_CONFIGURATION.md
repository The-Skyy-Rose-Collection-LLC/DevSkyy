# DevSkyy API Key Configuration

**Generated:** 2025-10-24
**Status:** ✅ Configured and Active

---

## Generated Production API Key

```
sk_live_YOUR_GENERATED_API_KEY_HERE
```

**⚠️ IMPORTANT:** Keep this key secure! Do not share publicly or commit to version control.

---

## Configuration Locations

### 1. ✅ Claude Desktop MCP Configuration
**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "devskyy": {
      "command": "python",
      "args": ["/Users/coreyfoster/DevSkyy/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_KEY": "sk_live_YOUR_GENERATED_API_KEY_HERE",
        "DEVSKYY_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Purpose:** Authenticates MCP server to DevSkyy backend API

### 2. ✅ Backend Environment Configuration
**File:** `/Users/coreyfoster/DevSkyy/.env`

```env
# DevSkyy API Key (for MCP and external integrations)
DEVSKYY_API_KEY=sk_live_YOUR_GENERATED_API_KEY_HERE
```

**Purpose:** Backend validates this key for API authentication

### 3. ✅ Example Configuration
**File:** `/Users/coreyfoster/DevSkyy/claude_desktop_config.json`

Updated with the production key as reference.

---

## API Keys Summary

### Primary API Keys Configured:

| Key Type | Purpose | Platform | Status |
|----------|---------|----------|--------|
| **ANTHROPIC_API_KEY** | Claude AI API access | Anthropic | ✅ Configured |
| **DEVSKYY_API_KEY** | DevSkyy API authentication | Self-generated | ✅ Configured |

### Additional Keys (Optional):

- **OPENAI_API_KEY** - GPT-4, DALL-E access
- **GOOGLE_API_KEY** - Gemini access
- **ELEVENLABS_API_KEY** - Text-to-Speech
- **META_ACCESS_TOKEN** - Social media automation
- **SENDGRID_API_KEY** - Email campaigns
- **TWILIO_AUTH_TOKEN** - SMS campaigns

---

## How to Generate New Keys

If you need to rotate or create additional API keys:

```bash
# Generate new DevSkyy API key
python3 -c "import secrets; print(f'sk_live_{secrets.token_urlsafe(32)}')"
```

**Example output:**
```
sk_live_NEW_RANDOM_STRING_HERE
```

Then update in:
1. Claude Desktop config
2. `.env` file
3. Any external integrations

---

## Security Best Practices

✅ **DO:**
- Keep API keys in environment variables or secure config files
- Rotate keys periodically (every 90 days recommended)
- Use different keys for development and production
- Store keys in password manager or secrets vault

❌ **DON'T:**
- Commit `.env` files to git (already in `.gitignore`)
- Share keys via email or chat
- Use the same key across multiple environments
- Hard-code keys in source code

---

## Testing the Configuration

### 1. Test Backend API
```bash
# Check if backend is running
curl http://localhost:8000/

# Test with API key
curl -H "Authorization: Bearer sk_live_YOUR_GENERATED_API_KEY_HERE" \
     http://localhost:8000/api/v1/system/health
```

### 2. Test MCP Server
After restarting Claude Desktop:
1. Look for 🔌 icon
2. Verify "devskyy" server is listed
3. Test: "Can you list all available DevSkyy agents?"

---

## Troubleshooting

### Issue: "Invalid API key" error

**Solution:**
1. Verify key is correctly set in both locations
2. Check for extra spaces or line breaks
3. Restart Claude Desktop
4. Restart backend API server

### Issue: MCP server not connecting

**Solution:**
1. Check backend is running on port 8000
2. Verify config file JSON syntax
3. Check Claude Desktop logs: `~/Library/Logs/Claude/`

---

## Next Steps

1. ✅ **Restart Claude Desktop** to activate the MCP server with API key
2. ✅ **Test the integration** with sample commands
3. ✅ **Save this key** in your password manager
4. 📝 **Document** any additional keys you add later

---

**Last Updated:** 2025-10-24
**Configuration Status:** Production Ready ✅
