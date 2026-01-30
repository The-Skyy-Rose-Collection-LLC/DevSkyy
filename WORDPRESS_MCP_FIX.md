# WordPress.com MCP Plugin Fix - Complete

## Problem
The WordPress.com MCP plugin was installed as an MCPB bundle (designed for Claude Desktop GUI) but wasn't loading in Claude Code CLI.

## Root Cause
- MCPB bundles and Claude Code plugins use different configuration formats
- Missing required `.claude-plugin/plugin.json` and `.mcp.json` files
- Plugin not registered in `~/.claude/settings.json`

## Solution Implemented

### 1. Created Plugin Structure
```
~/.claude/plugins/wordpress-com/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata for Claude Code
├── .mcp.json                # MCP server configuration
├── dist/
│   └── index.js             # MCP server executable (existing)
├── manifest.json            # MCPB manifest (existing)
├── package.json             # NPM package (existing)
└── README.md                # Documentation (existing)
```

### 2. Configuration Files Created

**`.claude-plugin/plugin.json`**
- Plugin metadata (name, version, description, author)
- Keywords for discoverability

**`.mcp.json`**
```json
{
  "mcpServers": {
    "wordpress-com": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/dist/index.js"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}",
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### 3. Updated Settings

**`~/.claude/settings.json`**
- Added `mcp__plugin_wordpress_com_wordpress-com__*` to `permissions.allow`
- Added `wordpress-com@automattic: true` to `enabledPlugins`

## Next Steps

### 1. Restart Claude Code
The configuration is complete. Exit and restart Claude Code to load the WordPress.com MCP server:

```bash
exit
claude
```

### 2. Verify Installation
After restart, check that WordPress tools are available:

```
ListMcpResourcesTool with server="wordpress-com"
```

You should see WordPress.com tools like:
- User management
- Site analytics
- Content operations
- Site administration

### 3. Authenticate
The WordPress.com MCP will prompt for authentication on first use. You'll need:
- WordPress.com account credentials
- Or API token

### 4. Sync Themes
Once authenticated, you can:
- Fetch current theme from skyyrose.co
- Merge features from `wordpress-theme/skyyrose-2025/`
- Deploy updated theme back to live site

## Testing Checklist
- [ ] Restart Claude Code CLI
- [ ] Verify WordPress.com MCP is loaded
- [ ] Authenticate with WordPress.com
- [ ] List sites (should show skyyrose.co)
- [ ] Fetch current theme files
- [ ] Sync 2025 features (GSAP, Three.js, View Transitions)
- [ ] Test deployment

## Files Modified
- ✅ `/Users/coreyfoster/.claude/plugins/wordpress-com/.claude-plugin/plugin.json` (created)
- ✅ `/Users/coreyfoster/.claude/plugins/wordpress-com/.mcp.json` (created)
- ✅ `/Users/coreyfoster/.claude/settings.json` (modified)
- ✅ `.claude/ralph-loop.local.md` (tracking)
- ✅ `WORDPRESS_MCP_FIX.md` (this file)

## Rollback (if needed)
If something goes wrong, revert with:
```bash
cd ~/.claude/plugins/wordpress-com
git log --oneline
git revert HEAD
```

## Additional Notes
- The MCP server executable (`dist/index.js`) was already present and properly built
- Node.js v20.19.6 is installed (meets ≥18.0.0 requirement)
- Plugin is now version-controlled in its own git repo

---
**Status**: ✅ Configuration complete - awaiting restart for validation
