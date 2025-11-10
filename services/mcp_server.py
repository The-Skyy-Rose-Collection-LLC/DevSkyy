"""
DevSkyy MCP Server

WHY: Expose DevSkyy AI tools via standard MCP protocol for external clients
HOW: Use official claude-agent-sdk to serve custom MCP tools
IMPACT: External tools can use DevSkyy's AI capabilities via OpenAI-compatible API

Architecture:
- MCP Server exposes tools via SSE (Server-Sent Events)
- Internal calls use custom mcp_client.py (98% token reduction)
- External clients use standard MCP protocol
- Logfire observability for all requests

Truth Protocol: Standard MCP compliance, full observability, secure access
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from services.mcp_client import MCPToolClient, get_mcp_client

# Logfire for observability
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

logger = logging.getLogger(__name__)


class DevSkyyMCPServer:
    """
    MCP Server for DevSkyy AI Tools

    Exposes custom MCP tools via standard protocol:
    - Content review tools (brand, SEO, security)
    - WordPress automation (post categorization)
    - E-commerce automation (product SEO)
    """

    def __init__(self, mcp_client: Optional[MCPToolClient] = None):
        """
        Create a DevSkyy MCP server instance that exposes DevSkyy AI tools over the MCP protocol.
        
        Parameters:
            mcp_client (Optional[MCPToolClient]): Optional custom MCP client to use. If not provided, the module singleton returned by `get_mcp_client()` will be used.
        """
        self.mcp_client = mcp_client or get_mcp_client()
        self.server = Server("devskyy-mcp-server")
        self._register_handlers()

        logger.info("✅ DevSkyy MCP Server initialized")

    def _register_handlers(self):
        """
        Register MCP handlers that expose available DevSkyy tools and handle tool invocations.
        
        This sets up two MCP endpoints on the server:
        - A tool-listing handler that returns the Tool definitions for the available DevSkyy tools (brand_intelligence_reviewer, seo_marketing_reviewer, security_compliance_reviewer, post_categorizer, product_seo_optimizer).
        - A call-tool handler that routes an invocation by tool name to the appropriate DevSkyy category, invokes the configured MCP tool client, and returns the tool result as a list containing a single TextContent with a JSON-formatted payload. For unknown tool names or execution errors the handler returns a TextContent containing a JSON-formatted error message.
        """

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """
            Provide Tool definitions for the DevSkyy MCP tools exposed by the server.
            
            Returns:
                List[Tool]: Tool definitions for brand_intelligence_reviewer, seo_marketing_reviewer,
                security_compliance_reviewer, post_categorizer, and product_seo_optimizer.
            """
            if LOGFIRE_AVAILABLE:
                logfire.info("MCP Server: Listing tools")

            tools = [
                # Content Review Tools
                Tool(
                    name="brand_intelligence_reviewer",
                    description="Reviews content for brand consistency, tone, and quality standards using AI analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Content title"},
                            "content": {"type": "string", "description": "Full content text"},
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Target keywords",
                            },
                            "word_count": {"type": "integer", "description": "Content word count"},
                            "brand_config": {
                                "type": "object",
                                "properties": {
                                    "keywords": {"type": "array", "items": {"type": "string"}},
                                    "tone": {
                                        "type": "string",
                                        "enum": ["professional", "casual", "friendly", "formal", "conversational"],
                                    },
                                    "min_word_count": {"type": "integer", "default": 600},
                                },
                            },
                        },
                        "required": ["title", "content", "brand_config"],
                    },
                ),
                Tool(
                    name="seo_marketing_reviewer",
                    description="Reviews content for SEO effectiveness, keyword optimization, and marketing impact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Content title"},
                            "content": {"type": "string", "description": "Full content text"},
                            "meta_description": {"type": "string", "description": "Meta description for search engines"},
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Target SEO keywords",
                            },
                        },
                        "required": ["title", "content", "meta_description"],
                    },
                ),
                Tool(
                    name="security_compliance_reviewer",
                    description="Reviews content for security issues, PII exposure, and compliance violations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Full content text to scan"},
                            "compliance_standards": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["GDPR", "CCPA", "HIPAA", "PCI-DSS", "SOC2"],
                                },
                                "default": ["GDPR"],
                            },
                        },
                        "required": ["content"],
                    },
                ),
                # WordPress Automation
                Tool(
                    name="post_categorizer",
                    description="Categorizes WordPress posts using AI with confidence scoring and reasoning",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "post_title": {"type": "string", "description": "WordPress post title"},
                            "post_content": {"type": "string", "description": "WordPress post content (optional)"},
                            "available_categories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "slug": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                },
                                "description": "Available WordPress categories",
                            },
                        },
                        "required": ["post_title", "available_categories"],
                    },
                ),
                # E-commerce Automation
                Tool(
                    name="product_seo_optimizer",
                    description="Optimizes WooCommerce product titles, descriptions, and metadata for SEO",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "integer", "description": "WooCommerce product ID"},
                            "product_data": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"},
                                    "short_description": {"type": "string"},
                                    "categories": {"type": "array", "items": {"type": "string"}},
                                    "price": {"type": "number"},
                                    "sku": {"type": "string"},
                                },
                                "required": ["title", "description"],
                            },
                            "target_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Target SEO keywords",
                            },
                        },
                        "required": ["product_id", "product_data"],
                    },
                ),
            ]

            logger.info(f"✅ Listed {len(tools)} MCP tools")
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """
            Handle invocation of a DevSkyy MCP tool and return its result as JSON text content.
            
            Routes the provided tool name to the appropriate internal category, invokes the configured MCP tool client with the given inputs, and returns the tool's output serialized as a single JSON-formatted TextContent. If the tool name is unknown or an error occurs during execution, returns a JSON-formatted error message as TextContent.
            
            Parameters:
                name (str): The tool identifier (e.g., "brand_intelligence_reviewer", "post_categorizer", "product_seo_optimizer").
                arguments (Dict[str, Any]): Inputs to pass to the tool; structure depends on the tool's input schema.
            
            Returns:
                List[TextContent]: A list containing one TextContent whose `text` is a JSON string of the tool result or an error object.
            """
            if LOGFIRE_AVAILABLE:
                logfire.info("MCP Server: Tool invocation", tool_name=name)

            try:
                # Determine category based on tool name
                if name in ["brand_intelligence_reviewer", "seo_marketing_reviewer", "security_compliance_reviewer"]:
                    category = "content_review"
                elif name == "post_categorizer":
                    category = "wordpress_automation"
                elif name == "product_seo_optimizer":
                    category = "ecommerce_automation"
                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    if LOGFIRE_AVAILABLE:
                        logfire.error("MCP Server: Unknown tool", tool_name=name)
                    return [TextContent(type="text", text=f'{{"error": "{error_msg}"}}')]

                # Invoke tool via custom MCP client (98% token reduction)
                result = await self.mcp_client.invoke_tool(
                    tool_name=name,
                    category=category,
                    inputs=arguments,
                )

                # Log success
                if LOGFIRE_AVAILABLE:
                    logfire.info("MCP Server: Tool completed", tool_name=name, result_keys=list(result.keys()))

                # Return result as TextContent
                import json
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(f"❌ {error_msg}")

                if LOGFIRE_AVAILABLE:
                    logfire.error("MCP Server: Tool execution failed", tool_name=name, error=str(e))

                return [TextContent(type="text", text=f'{{"error": "{error_msg}", "tool": "{name}"}}')]

    def get_server(self) -> Server:
        """
        Return the configured MCP server instance.
        
        Returns:
            Server: The configured MCP Server instance.
        """
        return self.server


# Singleton instance
_mcp_server: Optional[DevSkyyMCPServer] = None


def get_mcp_server() -> DevSkyyMCPServer:
    """
    Get singleton MCP server instance

    Returns:
        Shared DevSkyyMCPServer instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = DevSkyyMCPServer()
        logger.info("✅ MCP Server singleton created")
    return _mcp_server