# Ralph Loop Iteration 2 - MCP Server Loading Fix

## Problem Discovered
After Iteration 1 restart, WordPress.com MCP server still not loading.

**Available servers:**
- plugin:serena:serena
- plugin:context7:context7
- plugin:github:github
- plugin:playwright:playwright
- plugin:pinecone:pinecone
- ❌ **NO** wordpress-com

## Root Cause Analysis

### Issue 1: Wrong Directory Structure ✅ FIXED
- Plugin was in `~/.claude/plugins/wordpress-com/`
- Should be in `~/.claude/plugins/cache/[marketplace]/[name]/[version]/`
- **Fix:** Moved to `~/.claude/plugins/cache/automattic/wordpress-com/0.0.1/`

### Issue 2: Wrong MCP Server Configuration ✅ FIXED
**Original (incorrect):**
```json
{
  "mcpServers": {
    "wordpress-com": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/dist/index.js"]
    }
  }
}
```

**Problem:** Tried to run local bundled code, but Claude Code expects npm packages

**Updated (correct):**
```json
{
  "mcpServers": {
    "wordpress-com": {
      "command": "npx",
      "args": ["-y", "@automattic/mcp-wordpress-remote"]
    }
  }
}
```

**Solution:** Use published npm package `@automattic/mcp-wordpress-remote` (version 0.2.19)

## Changes Made

1. ✅ Created cache directory structure:
   ```
   ~/.claude/plugins/cache/automattic/wordpress-com/0.0.1/
   ```

2. ✅ Copied all plugin files to cache directory

3. ✅ Updated `.mcp.json` to use npm package instead of local code

4. ✅ Updated `installed_plugins.json` installPath:
   ```
   From: /Users/coreyfoster/.claude/plugins/wordpress-com
   To:   /Users/coreyfoster/.claude/plugins/cache/automattic/wordpress-com/0.0.1
   ```

## Key Learning

**MCPB bundles vs Claude Code plugins:**
- MCPB (.mcpb files): Standalone bundles for Claude Desktop GUI
- Claude Code: Expects npm-published MCP servers run via `npx`
- Local dist/index.js won't work - must use published package

**Pattern to follow:**
- Pinecone: `npx -y @pinecone-database/mcp`
- WordPress: `npx -y @automattic/mcp-wordpress-remote`

## Next Steps

1. **Restart Claude Code** (required for config reload)
2. Verify wordpress-com appears in ListMcpResourcesTool
3. Test WordPress.com authentication
4. Begin theme sync workflow

## Status
⏳ Configuration updated - awaiting restart for validation

---
**Iteration 2 Duration:** Single iteration
**Root Cause:** npm package vs local code execution
**Next Action:** User restarts Claude Code
