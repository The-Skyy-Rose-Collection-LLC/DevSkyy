"""WordPress Bridge Agent — connects dashboard pipelines to WordPress/WooCommerce."""


def __getattr__(name: str):
    """Lazy imports to avoid circular/missing module errors during incremental development."""
    if name == "WordPressBridgeAgent":
        from agents.wordpress_bridge.agent import WordPressBridgeAgent

        return WordPressBridgeAgent
    if name == "run_agent":
        from agents.wordpress_bridge.agent import run_agent

        return run_agent
    if name == "create_wordpress_tools":
        from agents.wordpress_bridge.mcp_server import create_wordpress_tools

        return create_wordpress_tools
    if name == "SYSTEM_PROMPT":
        from agents.wordpress_bridge.prompts import SYSTEM_PROMPT

        return SYSTEM_PROMPT
    raise AttributeError(f"module 'agents.wordpress_bridge' has no attribute {name!r}")


__all__ = [
    "WordPressBridgeAgent",
    "run_agent",
    "create_wordpress_tools",
    "SYSTEM_PROMPT",
]
