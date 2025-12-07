"""
WordPress Theme Orchestrator MCP Server

Full theme orchestration via Model Context Protocol:
- Theme generation with brand guidelines
- Elementor widget creation
- Theme validation and packaging
- Automated deployment to WordPress sites
- Integration with WordPress MCP for site operations

Designed to work alongside @instawp/mcp-wp for complete WordPress automation.
"""

from mcp_servers.theme_orchestrator.server import (
    ThemeOrchestratorMCP,
    create_mcp_server,
    get_server_instance,
    mcp,
    run_server,
)


__all__ = ["ThemeOrchestratorMCP", "create_mcp_server", "get_server_instance", "mcp", "run_server"]
__version__ = "1.0.0"
