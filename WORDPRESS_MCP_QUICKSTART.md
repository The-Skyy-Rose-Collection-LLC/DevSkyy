# WordPress.com MCP - Quick Start Guide

## ✅ Configuration Complete

The WordPress.com MCP plugin is now properly configured for Claude Code CLI.

## 🚀 Next Steps

### 1. Restart Claude Code
```bash
exit
claude
```

### 2. Verify Installation
```
# In the new Claude session, check available MCP servers:
ListMcpResourcesTool
```

You should see `wordpress-com` in the available servers list.

### 3. Authenticate (First Time Only)
The WordPress.com MCP will prompt for authentication when first used. Prepare:
- WordPress.com account email/password
- OR WordPress.com API token

### 4. Test Connection
```
# List your WordPress.com sites
wpcom-mcp-me
wpcom-mcp-sites
```

You should see `skyyrose.co` in your sites list.

## 🎯 Theme Sync Workflow

Once authenticated, you can sync themes:

### Step 1: Fetch Current Theme
```
# Get current active theme on skyyrose.co
wpcom-mcp-site-settings site=skyyrose.co
wpcom-mcp-posts-search site=skyyrose.co
```

### Step 2: Review Reference Theme
Local reference theme is at:
```
wordpress-theme/skyyrose-2025/
├── style.css
├── functions.php
├── header.php
├── footer.php
├── index.php
├── page.php
├── single.php
└── woocommerce.php
```

Features to integrate:
- ✨ GSAP scroll animations
- 🌊 View Transitions API
- 💎 Glassmorphism styling
- 🎨 Three.js 3D model viewer
- 🔌 DevSkyy API integration

### Step 3: Merge & Deploy
1. Copy current theme files from skyyrose.co
2. Merge 2025 features from reference theme
3. Test locally in WordPress Playground
4. Deploy via WordPress.com MCP tools

## 📚 Available WordPress.com Tools

Once loaded, you'll have access to:

- **wpcom-mcp-me** - Get your WordPress.com profile
- **wpcom-mcp-sites** - List all your sites
- **wpcom-mcp-site-settings** - Get/update site settings
- **wpcom-mcp-posts-search** - Search posts across sites
- **wpcom-mcp-post-get** - Get specific post content
- **wpcom-mcp-comments** - Manage comments
- **wpcom-mcp-plugins** - List/manage plugins
- **wpcom-mcp-themes** - List/manage themes

## 🔧 Troubleshooting

### MCP Server Not Loading
```bash
# Check plugin installation
ls -la ~/.claude/plugins/wordpress-com/

# Verify configuration files exist
cat ~/.claude/plugins/wordpress-com/.mcp.json
cat ~/.claude/plugins/wordpress-com/.claude-plugin/plugin.json
```

### Authentication Issues
```bash
# Clear auth cache (if needed)
rm -rf ~/.config/wordpress-com-mcp/
```

### Permission Errors
Check `~/.claude/settings.json` includes:
```json
{
  "permissions": {
    "allow": ["mcp__plugin_wordpress_com_wordpress-com__*"]
  },
  "enabledPlugins": {
    "wordpress-com@automattic": true
  }
}
```

## 📖 Documentation

- Full details: `WORDPRESS_MCP_FIX.md`
- Ralph Loop tracking: `.claude/ralph-loop.local.md`
- MCP manifest: `~/.claude/plugins/wordpress-com/manifest.json`

---
**Ready to restart!** 🎉
