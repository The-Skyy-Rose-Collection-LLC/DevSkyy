"""DevSkyy MCP Tools Package.

Re-exports the ``mcp`` FastMCP instance and triggers tool registration
via side-effect imports of every tool module.
"""

import mcp_tools.tools  # noqa: F401

# Side-effect: importing tools/ registers all @mcp.tool() handlers
from mcp_tools.server import mcp  # noqa: F401 - public API
