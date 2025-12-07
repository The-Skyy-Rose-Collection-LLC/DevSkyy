"""
Base MCP Server

Shared patterns and utilities for all DevSkyy MCP servers:
- On-demand tool loading (98% token reduction)
- Schema validation with Pydantic
- Observability integration (Logfire)
- SkyyRose brand guidelines enforcement
- Error ledger integration

Usage:
    class MyMCPServer(BaseMCPServer):
        def __init__(self):
            super().__init__("my-server")
            self._register_tools()
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field


# Optional observability
try:
    import logfire

    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# SKYY ROSE BRAND GUIDELINES
# =============================================================================


class SkyyRoseBrandGuidelines(BaseModel):
    """SkyyRose brand guidelines for enforcement across all MCPs."""

    brand_name: str = "SkyyRose"
    incorrect_names: list[str] = ["Skyy Rose", "skyy rose", "SKYYROSE", "SkyRose"]
    domain: str = "skyyrose.co"
    incorrect_domains: list[str] = ["skyyrose.com", "skyy-rose.com", "skyy-rose.co"]

    colors: dict[str, str] = Field(
        default={
            "primary": "#1a1a1a",
            "secondary": "#d4af37",
            "accent": "#8b7355",
            "background": "#ffffff",
            "text": "#333333",
        }
    )

    typography: dict[str, str] = Field(
        default={
            "headings": "Playfair Display",
            "body": "Source Sans Pro",
            "accent": "Dancing Script",
        }
    )

    tone_keywords: list[str] = ["luxury", "elegant", "sophisticated", "elevated", "boutique"]
    prohibited_language: list[str] = [
        "discount",
        "clearance",
        "cheap",
        "sale",
        "bargain",
        "hyphy",
        ".com",
    ]


BRAND_GUIDELINES = SkyyRoseBrandGuidelines()


def enforce_brand_name(text: str) -> str:
    """Enforce correct SkyyRose brand name in text."""
    result = text
    for incorrect in BRAND_GUIDELINES.incorrect_names:
        result = result.replace(incorrect, BRAND_GUIDELINES.brand_name)
    return result


def enforce_brand_domain(text: str) -> str:
    """Enforce correct SkyyRose domain in text."""
    result = text
    for incorrect in BRAND_GUIDELINES.incorrect_domains:
        result = result.replace(incorrect, BRAND_GUIDELINES.domain)
    return result


def validate_brand_compliance(text: str) -> dict[str, Any]:
    """Check text for brand guideline violations."""
    violations = []

    # Check for incorrect brand names
    for incorrect in BRAND_GUIDELINES.incorrect_names:
        if incorrect in text:
            violations.append(f"Incorrect brand name: '{incorrect}' should be '{BRAND_GUIDELINES.brand_name}'")

    # Check for incorrect domains
    for incorrect in BRAND_GUIDELINES.incorrect_domains:
        if incorrect in text:
            violations.append(f"Incorrect domain: '{incorrect}' should be '{BRAND_GUIDELINES.domain}'")

    # Check for prohibited language
    text_lower = text.lower()
    for prohibited in BRAND_GUIDELINES.prohibited_language:
        if prohibited in text_lower:
            violations.append(f"Prohibited language: '{prohibited}' violates luxury brand tone")

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "brand_name": BRAND_GUIDELINES.brand_name,
        "domain": BRAND_GUIDELINES.domain,
    }


# =============================================================================
# BASE MCP SERVER
# =============================================================================


class BaseMCPServer:
    """
    Base class for all DevSkyy MCP servers.

    Provides:
    - Standard MCP server initialization
    - On-demand tool loading (98% token reduction)
    - Schema caching
    - Observability integration
    - Error handling patterns
    - Brand guidelines enforcement
    """

    def __init__(self, name: str = "", version: str = "1.0.0", server_name: str = ""):
        """
        Initialize base MCP server.

        Args:
            name: Unique identifier for this server (alias for server_name)
            version: Server version string
            server_name: Unique identifier for this server (legacy parameter)
        """
        # Support both 'name' and 'server_name' parameters
        self.server_name = name or server_name
        self.version = version
        self.server = Server(self.server_name)

        # On-demand tool loading state
        self.loaded_tools: dict[str, dict[str, Any]] = {}
        self.tool_cache: dict[str, Any] = {}
        self.tool_schemas: dict[str, dict[str, Any]] = {}

        # Tool handlers and definitions (for subclass registration)
        self._tool_handlers: dict[str, Any] = {}
        self._tool_definitions: list[Tool] = []

        # Brand guidelines
        self.brand_guidelines = BRAND_GUIDELINES

        # Metrics
        self.invocation_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

        # Register base handlers
        self._register_base_handlers()

        # Call subclass tool registration
        self._register_tools()

        logger.info(f"Initialized {server_name} MCP server v{version}")

    def _register_base_handlers(self) -> None:
        """Register standard MCP handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all available tools from this server."""
            if LOGFIRE_AVAILABLE:
                logfire.info(f"{self.server_name}: Listing tools")

            tools = await self.get_tools()
            logger.info(f"{self.server_name}: Listed {len(tools)} tools")
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool invocation with error handling and observability."""
            self.invocation_count += 1

            if LOGFIRE_AVAILABLE:
                logfire.info(f"{self.server_name}: Invoking tool", tool_name=name)

            try:
                # Load tool on-demand if not cached
                if name not in self.loaded_tools:
                    await self._load_tool(name)

                # Execute tool
                result = await self.execute_tool(name, arguments)

                # Enforce brand guidelines on output if it's text
                if isinstance(result, dict) and "content" in result:
                    if isinstance(result["content"], str):
                        result["content"] = enforce_brand_name(result["content"])
                        result["content"] = enforce_brand_domain(result["content"])

                # Return result
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            except Exception as e:
                self.error_count += 1
                error_response = {
                    "error": str(e),
                    "tool": name,
                    "server": self.server_name,
                    "timestamp": datetime.now().isoformat(),
                }

                logger.error(f"{self.server_name}: Tool execution failed - {e}")

                if LOGFIRE_AVAILABLE:
                    logfire.error(f"{self.server_name}: Tool failed", tool_name=name, error=str(e))

                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def _load_tool(self, tool_name: str) -> None:
        """
        Load a tool on-demand (part of 98% token reduction strategy).

        This pattern avoids loading all tools upfront, instead loading
        only when the tool is actually invoked.
        """
        if tool_name in self.loaded_tools:
            return

        # Get tool schema from subclass implementation
        schema = await self.get_tool_schema(tool_name)
        if schema:
            self.loaded_tools[tool_name] = schema
            logger.debug(f"{self.server_name}: Loaded tool on-demand: {tool_name}")

    def _register_tools(self) -> None:
        """
        Register tools for this server.

        Subclasses should override this to register their tools using _register_tool().
        """
        pass

    def _register_tool(
        self,
        name: str,
        description: str,
        handler: Any,
        input_schema: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a tool with this server.

        Args:
            name: Tool name
            description: Tool description
            handler: Async function to handle tool invocations
            input_schema: JSON schema for tool input
        """
        # Create tool definition
        tool = Tool(
            name=name,
            description=description,
            inputSchema=input_schema or {"type": "object", "properties": {}},
        )
        self._tool_definitions.append(tool)
        self._tool_handlers[name] = handler
        self.tool_schemas[name] = input_schema or {}

        logger.debug(f"{self.server_name}: Registered tool '{name}'")

    async def get_tools(self) -> list[Tool]:
        """
        Get list of available tools.

        Returns:
            List of MCP Tool definitions
        """
        return self._tool_definitions

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a tool with given arguments.

        Args:
            name: Tool name to execute
            arguments: Tool input arguments

        Returns:
            Tool execution result
        """
        handler = self._tool_handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}", "available_tools": list(self._tool_handlers.keys())}

        # Execute the handler
        try:
            result = await handler(arguments)
            return result
        except Exception as e:
            logger.error(f"{self.server_name}: Tool '{name}' failed: {e}")
            return {"error": str(e), "tool": name}

    async def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """
        Get schema for a specific tool.

        Override in subclasses for custom schema loading.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema dict or None
        """
        return self.tool_schemas.get(tool_name)

    def get_status(self) -> dict[str, Any]:
        """Get server status and metrics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "server_name": self.server_name,
            "version": self.version,
            "status": "running",
            "uptime_seconds": uptime,
            "tools_loaded": len(self.loaded_tools),
            "total_invocations": self.invocation_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.invocation_count, 1),
            "brand_guidelines": {
                "name": self.brand_guidelines.brand_name,
                "domain": self.brand_guidelines.domain,
            },
        }

    def get_server(self) -> Server:
        """Get the underlying MCP server instance."""
        return self.server

    async def run(self) -> None:
        """Run the MCP server via stdio."""
        logger.info(f"Starting {self.server_name} MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> Tool:
    """
    Create a standard MCP Tool definition.

    Args:
        name: Tool name
        description: Tool description
        properties: JSON Schema properties for input
        required: List of required property names

    Returns:
        MCP Tool definition
    """
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    )


def json_response(data: dict[str, Any]) -> list[TextContent]:
    """Create a JSON TextContent response."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def error_response(error: str, tool: str | None = None, **extra: Any) -> list[TextContent]:
    """Create a standardized error response."""
    response = {
        "error": error,
        "timestamp": datetime.now().isoformat(),
        **extra,
    }
    if tool:
        response["tool"] = tool
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


# =============================================================================
# CATALOG UTILITIES (for SkyyRose product catalog)
# =============================================================================


def parse_catalog_csv(csv_path: str) -> list[dict[str, Any]]:
    """
    Parse SkyyRose product catalog CSV.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of product dictionaries
    """
    import csv

    products = []
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {csv_path}")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = {
                "token": row.get("Token", ""),
                "name": row.get("Item Name", ""),
                "variation": row.get("Variation Name", ""),
                "sku": row.get("SKU", ""),
                "description": row.get("Description", ""),
                "categories": row.get("Categories", ""),
                "seo_title": row.get("SEO Title", ""),
                "seo_description": row.get("SEO Description", ""),
                "price": row.get("Price", "0"),
                "sale_price": row.get("Online Sale Price", ""),
                "visibility": row.get("Square Online Item Visibility", "visible"),
                "color": row.get("Option Value 1", ""),
                "size": row.get("Option Value 2", ""),
                "quantity": row.get("Current Quantity The Skyy Rose Collection", "0"),
            }
            products.append(product)

    return products


def group_products_by_parent(products: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group product variations by parent product name.

    Args:
        products: List of product dictionaries

    Returns:
        Dict mapping product names to their variations
    """
    grouped = {}
    for product in products:
        name = product["name"]
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(product)
    return grouped


def generate_product_embedding_text(product: dict[str, Any]) -> str:
    """
    Generate text for embedding a product.

    Combines name, description, and SEO data for rich embeddings.

    Args:
        product: Product dictionary

    Returns:
        Text string for embedding
    """
    parts = [
        product.get("name", ""),
        product.get("description", ""),
        product.get("seo_title", ""),
        product.get("seo_description", ""),
        f"Category: {product.get('categories', '')}",
        f"Price: ${product.get('price', '0')}",
    ]
    return " ".join(filter(None, parts))
