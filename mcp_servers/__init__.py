"""
DevSkyy MCP Servers

Comprehensive MCP ecosystem for orchestrating all aspects of DevSkyy:
- Frontend MCP: Theme building, Elementor, UI components
- Backend MCP: API operations, database, agents, e-commerce
- Development MCP: Code generation, testing, CI/CD
- RAG MCP: Vector store, embeddings, semantic search
- Master Orchestrator MCP: Coordinates all other MCPs

All servers follow the on-demand tool loading pattern for 98% token reduction.
"""

from mcp_servers.base_mcp_server import BaseMCPServer


__all__ = [
    "BaseMCPServer",
]
__version__ = "1.0.0"
