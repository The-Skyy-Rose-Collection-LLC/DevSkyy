# Ralph Loop - WordPress MCP Plugin Fix

## Iteration 1

### Task
Fix WordPress.com MCP plugin to work with Claude Code CLI. The plugin is installed at ~/.claude/plugins/wordpress-com/ and registered in installed_plugins.json but not loading as an MCP server.

### Diagnosis
- WordPress plugin was installed as an MCPB bundle (for Claude Desktop GUI)
- MCPB bundles are different from Claude Code plugins
- Missing required `.claude-plugin/plugin.json` and `.mcp.json` files
- Not registered in settings.json enabledPlugins or permissions

### Solution Implemented

1. Created `.claude-plugin/plugin.json` with plugin metadata
2. Created `.mcp.json` with MCP server configuration:
   - Command: `node ${CLAUDE_PLUGIN_ROOT}/dist/index.js`
   - Environment: production
3. Updated `~/.claude/settings.json`:
   - Added `mcp__plugin_wordpress_com_wordpress-com__*` to permissions.allow
   - Added `wordpress-com@automattic: true` to enabledPlugins

### Files Created/Modified
- ✅ `/Users/coreyfoster/.claude/plugins/wordpress-com/.claude-plugin/plugin.json` (created)
- ✅ `/Users/coreyfoster/.claude/plugins/wordpress-com/.mcp.json` (created)
- ✅ `/Users/coreyfoster/.claude/settings.json` (modified - added permissions and enabled plugin)

### Next Steps
1. Restart Claude Code CLI to load the new MCP server
2. Verify WordPress.com tools are available via ListMcpResourcesTool
3. Test theme sync functionality

### Status
✅ CONFIGURATION COMPLETE

All required files created and settings updated. WordPress.com MCP plugin is now properly configured for Claude Code CLI.

**Configuration verified:**
- Plugin structure matches Pinecone plugin pattern
- MCP server configuration points to executable dist/index.js
- Permissions and enabledPlugins updated in settings.json
- Git repository initialized with commit

**User action required:**
1. Exit Claude Code CLI: `exit`
2. Restart: `claude`
3. Verify with: `ListMcpResourcesTool` (should show wordpress-com server)

See `WORDPRESS_MCP_FIX.md` for complete documentation.
