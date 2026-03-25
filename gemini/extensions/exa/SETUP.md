# Exa MCP Extension - Setup Guide

**Status:** ✅ Files installed, configuration needed
**Version:** 3.1.8

## Quick Setup (3 steps)

### Step 1: Get Exa API Key

1. Go to https://dashboard.exa.ai/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the API key

### Step 2: Configure API Key

Edit the `.env` file:

```bash
nano /Users/coreyfoster/DevSkyy/gemini/exa-mcp-server/.env
```

Replace `your_exa_api_key_here` with your actual API key:

```env
EXA_API_KEY=exa_abc123...
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 3: Connect to Claude Code

**Option A: Hosted MCP (Recommended)**

Run this command in a **new terminal** (not in Claude Code):

```bash
claude mcp add --transport http exa https://mcp.exa.ai/mcp
```

**Option B: Local MCP Server**

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "exa": {
      "command": "node",
      "args": ["/Users/coreyfoster/DevSkyy/gemini/exa-mcp-server/.smithery/stdio/index.cjs"],
      "env": {
        "EXA_API_KEY": "your_exa_api_key_here"
      }
    }
  }
}
```

## Test Installation

```bash
cd /Users/coreyfoster/DevSkyy/gemini/clients/node

node -e "
const { GeminiClient } = require('./gemini-client');
(async () => {
  const client = new GeminiClient();
  const response = await client.generateContent({
    prompt: 'Use Exa to search for latest news about AI and summarize top 3 results'
  });
  console.log(response.text);
})();
"
```

## Usage Examples

Once configured, just prompt naturally:

```
"Search the web for React 19 new features"
"Find technical documentation for PostgreSQL JSON functions"
"Research what companies are building with Gemini API"
"Find recent TechCrunch articles about AI startups"
```

## Available Tools

- ✅ **web_search_exa** - General web search
- ✅ **get_code_context_exa** - Technical docs/code search
- ✅ **company_research_exa** - Company information
- ✅ **web_search_advanced_exa** - Advanced search filters
- ✅ **crawling_exa** - Extract content from URLs
- ✅ **people_search_exa** - Find people/professionals

## Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `exa-mcp-server/.env` | API key configuration | ⚠️  Needs API key |
| `exa-mcp-server/package.json` | Dependencies | ✅ Installed |
| `~/.claude/mcp.json` | Claude Code MCP config | ⚠️  Manual setup |

## Troubleshooting

### "Cannot be launched inside another Claude Code session"

This is normal! The `claude mcp add` command needs to run in a **regular terminal**, not inside Claude Code.

**Solution:**
1. Open a new terminal window (outside Claude Code)
2. Run: `claude mcp add --transport http exa https://mcp.exa.ai/mcp`
3. Restart Claude Code

### "EXA_API_KEY not found"

**Solution:** Set your API key in `.env` file as shown in Step 2 above

### "MCP server not responding"

**Solution:**
1. Check API key is valid
2. Verify internet connection
3. Restart Claude Code
4. Check Exa service status at https://status.exa.ai

## Next Steps

After setup:

1. **Install HuggingFace Skills** (requested)
2. **Install Nanobanana Extension** (requested)
3. **Test all extensions together**
4. **Build custom workflows**

---

**Need Help?**
- Exa Docs: https://docs.exa.ai
- GitHub Issues: https://github.com/exa-labs/exa-mcp-server/issues
- Discord: https://discord.gg/exa
