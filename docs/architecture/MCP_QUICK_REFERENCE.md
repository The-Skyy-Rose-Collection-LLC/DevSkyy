# MCP Quick Reference Card

**Version:** 5.1.0-enterprise | **Last Updated:** 2025-12-07

---

## Overview

DevSkyy supports multiple MCP (Model Context Protocol) servers when the full set of optional modules is installed. In this trimmed repository snapshot only the FastAPI entrypoint (main.py) is present: many MCP tools/agents are conditionally loaded at runtime and may be unavailable unless those modules and dependencies are installed.

---

## Quick Commands

### Local Claude Desktop (On Your Machine)

```bash
# Add Neon MCP server to Claude Desktop (example)
claude mcp add --transport http neon https://mcp.neon.tech/mcp

# List configured MCP servers
claude mcp list

# Test connection
claude mcp test neon
```

---

## Notes
- Counts of agents/tools (e.g., "54 agents", "11 tools") depend on optional agent modules being present and loaded by main.py at runtime. main.py uses ImportError handling and will operate with reduced functionality if those modules are missing.
- For reliable MCP features, deploy the full repository with required dependencies (mcp SDK, Redis, agent modules) and configure REDIS_URL and other env vars.
