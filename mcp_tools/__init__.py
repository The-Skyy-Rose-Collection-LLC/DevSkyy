"""DevSkyy MCP Tools Package.

Re-exports the ``mcp`` FastMCP instance and triggers tool registration
via side-effect imports of every tool module.
"""

# Side-effect: importing tools/ registers all @mcp.tool() handlers
import mcp_tools.tools  # noqa: F401
from mcp_tools.server import mcp  # noqa: F401 - public API
