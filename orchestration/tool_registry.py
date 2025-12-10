"""
DevSkyy Tool Registry
=====================

Comprehensive tool registry with 37 tool definitions for AI agents.

Categories:
- Content: Writing, editing, summarization
- Commerce: Products, orders, inventory
- Media: Images, 3D models, video
- Communication: Email, SMS, notifications
- Analytics: Metrics, reports, forecasting
- Integration: WordPress, WooCommerce, APIs
- System: Files, database, cache

References:
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/tool-use
- JSON Schema: https://json-schema.org/draft/2020-12/json-schema-core.html
"""

import os
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import inspect

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ToolCategory(str, Enum):
    """Tool categories"""
    CONTENT = "content"
    COMMERCE = "commerce"
    MEDIA = "media"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AI = "ai"


class ParameterType(str, Enum):
    """Parameter types"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# =============================================================================
# Models
# =============================================================================

class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types
    
    def to_json_schema(self) -> dict:
        """Convert to JSON Schema format"""
        schema = {
            "type": self.type.value,
            "description": self.description,
        }
        
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.pattern:
            schema["pattern"] = self.pattern
        if self.items:
            schema["items"] = self.items
        if self.properties:
            schema["properties"] = self.properties
        
        return schema


class ToolDefinition(BaseModel):
    """Complete tool definition"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = []
    returns: Optional[Dict[str, Any]] = None
    examples: List[Dict[str, Any]] = []
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # Requests per minute
    timeout: float = 30.0
    enabled: bool = True
    
    # Implementation reference
    handler: Optional[str] = None  # Module path to handler function
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameter names"""
        return [p.name for p in self.parameters if p.required]
    
    def to_openai_function(self) -> dict:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
    
    def to_anthropic_tool(self) -> dict:
        """Convert to Anthropic tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    p.name: p.to_json_schema()
                    for p in self.parameters
                },
                "required": self.get_required_params(),
            },
        }
    
    def to_mcp_tool(self) -> dict:
        """Convert to MCP tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    p.name: p.to_json_schema()
                    for p in self.parameters
                },
                "required": self.get_required_params(),
            },
        }


# =============================================================================
# Tool Registry
# =============================================================================

class ToolRegistry:
    """
    Central registry for all DevSkyy tools.
    
    Usage:
        registry = ToolRegistry()
        
        # Get tool
        tool = registry.get("web_search")
        
        # Get all tools for category
        commerce_tools = registry.get_by_category(ToolCategory.COMMERCE)
        
        # Export for OpenAI
        functions = registry.to_openai_functions()
        
        # Validate call
        is_valid, errors = registry.validate_call("create_product", params)
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._load_builtin_tools()
    
    def _load_builtin_tools(self):
        """Load all built-in tool definitions"""
        for tool in BUILTIN_TOOLS:
            self.register(tool)
    
    def register(self, tool: ToolDefinition, handler: Callable = None):
        """Register a tool"""
        self._tools[tool.name] = tool
        if handler:
            self._handlers[tool.name] = handler
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str):
        """Unregister a tool"""
        if name in self._tools:
            del self._tools[name]
        if name in self._handlers:
            del self._handlers[name]
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler"""
        return self._handlers.get(name)
    
    def list_all(self) -> List[ToolDefinition]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def list_enabled(self) -> List[ToolDefinition]:
        """Get enabled tools only"""
        return [t for t in self._tools.values() if t.enabled]
    
    def get_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Get tools by category"""
        return [t for t in self._tools.values() if t.category == category]
    
    def search(self, query: str) -> List[ToolDefinition]:
        """Search tools by name or description"""
        query = query.lower()
        return [
            t for t in self._tools.values()
            if query in t.name.lower() or query in t.description.lower()
        ]
    
    def validate_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """
        Validate tool call parameters
        
        Returns:
            (is_valid, list_of_errors)
        """
        tool = self.get(tool_name)
        
        if not tool:
            return False, [f"Unknown tool: {tool_name}"]
        
        if not tool.enabled:
            return False, [f"Tool is disabled: {tool_name}"]
        
        errors = []
        
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                errors.append(f"Missing required parameter: {param.name}")
        
        # Validate parameter types and constraints
        for name, value in params.items():
            param = next((p for p in tool.parameters if p.name == name), None)
            
            if not param:
                errors.append(f"Unknown parameter: {name}")
                continue
            
            # Type validation
            expected_type = param.type
            if expected_type == ParameterType.STRING and not isinstance(value, str):
                errors.append(f"Parameter {name} must be string")
            elif expected_type == ParameterType.INTEGER and not isinstance(value, int):
                errors.append(f"Parameter {name} must be integer")
            elif expected_type == ParameterType.NUMBER and not isinstance(value, (int, float)):
                errors.append(f"Parameter {name} must be number")
            elif expected_type == ParameterType.BOOLEAN and not isinstance(value, bool):
                errors.append(f"Parameter {name} must be boolean")
            elif expected_type == ParameterType.ARRAY and not isinstance(value, list):
                errors.append(f"Parameter {name} must be array")
            elif expected_type == ParameterType.OBJECT and not isinstance(value, dict):
                errors.append(f"Parameter {name} must be object")
            
            # Enum validation
            if param.enum and value not in param.enum:
                errors.append(f"Parameter {name} must be one of: {param.enum}")
            
            # Range validation
            if isinstance(value, (int, float)):
                if param.min_value is not None and value < param.min_value:
                    errors.append(f"Parameter {name} must be >= {param.min_value}")
                if param.max_value is not None and value > param.max_value:
                    errors.append(f"Parameter {name} must be <= {param.max_value}")
            
            # Length validation
            if isinstance(value, str):
                if param.min_length is not None and len(value) < param.min_length:
                    errors.append(f"Parameter {name} must be at least {param.min_length} chars")
                if param.max_length is not None and len(value) > param.max_length:
                    errors.append(f"Parameter {name} must be at most {param.max_length} chars")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool"""
        # Validate first
        is_valid, errors = self.validate_call(tool_name, params)
        if not is_valid:
            return {
                "success": False,
                "error": "Validation failed",
                "details": errors,
            }
        
        # Get handler
        handler = self.get_handler(tool_name)
        if not handler:
            return {
                "success": False,
                "error": f"No handler registered for tool: {tool_name}",
            }
        
        # Execute
        try:
            if inspect.iscoroutinefunction(handler):
                result = await handler(**params)
            else:
                result = handler(**params)
            
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    # -------------------------------------------------------------------------
    # Export Formats
    # -------------------------------------------------------------------------
    
    def to_openai_functions(self, enabled_only: bool = True) -> List[dict]:
        """Export as OpenAI function calling format"""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_openai_function() for t in tools]
    
    def to_anthropic_tools(self, enabled_only: bool = True) -> List[dict]:
        """Export as Anthropic tool format"""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_anthropic_tool() for t in tools]
    
    def to_mcp_tools(self, enabled_only: bool = True) -> List[dict]:
        """Export as MCP tool format"""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_mcp_tool() for t in tools]
    
    def export_schema(self) -> dict:
        """Export complete schema"""
        return {
            "version": "1.0",
            "total_tools": len(self._tools),
            "categories": {
                cat.value: len(self.get_by_category(cat))
                for cat in ToolCategory
            },
            "tools": [t.dict() for t in self.list_all()],
        }


# =============================================================================
# Built-in Tool Definitions (37 tools)
# =============================================================================

BUILTIN_TOOLS = [
    # -------------------------------------------------------------------------
    # Content Tools (7)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="generate_product_description",
        description="Generate compelling product description for SkyyRose products",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="product_name", type=ParameterType.STRING, description="Product name", required=True),
            ToolParameter(name="collection", type=ParameterType.STRING, description="Collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)", required=True, enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]),
            ToolParameter(name="features", type=ParameterType.ARRAY, description="Product features", items={"type": "string"}),
            ToolParameter(name="tone", type=ParameterType.STRING, description="Writing tone", default="luxury", enum=["luxury", "casual", "technical"]),
        ],
        examples=[{"product_name": "Heart aRose Bomber", "collection": "BLACK_ROSE", "features": ["Rose gold zipper", "Embroidered back"]}],
    ),
    ToolDefinition(
        name="generate_social_post",
        description="Generate social media post content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="platform", type=ParameterType.STRING, description="Social platform", required=True, enum=["instagram", "tiktok", "twitter", "facebook"]),
            ToolParameter(name="content_type", type=ParameterType.STRING, description="Content type", required=True, enum=["product_launch", "promotion", "lifestyle", "behind_scenes"]),
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Optional product ID"),
            ToolParameter(name="hashtags", type=ParameterType.BOOLEAN, description="Include hashtags", default=True),
        ],
    ),
    ToolDefinition(
        name="generate_email_content",
        description="Generate email marketing content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="email_type", type=ParameterType.STRING, description="Email type", required=True, enum=["welcome", "abandoned_cart", "order_confirmation", "promotion", "newsletter"]),
            ToolParameter(name="customer_name", type=ParameterType.STRING, description="Customer name"),
            ToolParameter(name="products", type=ParameterType.ARRAY, description="Product IDs", items={"type": "integer"}),
            ToolParameter(name="discount_code", type=ParameterType.STRING, description="Discount code if applicable"),
        ],
    ),
    ToolDefinition(
        name="summarize_content",
        description="Summarize text content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="text", type=ParameterType.STRING, description="Text to summarize", required=True, min_length=50),
            ToolParameter(name="max_length", type=ParameterType.INTEGER, description="Maximum summary length", default=200, min_value=50, max_value=1000),
            ToolParameter(name="style", type=ParameterType.STRING, description="Summary style", default="concise", enum=["concise", "detailed", "bullet_points"]),
        ],
    ),
    ToolDefinition(
        name="translate_content",
        description="Translate content to another language",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="text", type=ParameterType.STRING, description="Text to translate", required=True),
            ToolParameter(name="target_language", type=ParameterType.STRING, description="Target language code", required=True),
            ToolParameter(name="preserve_formatting", type=ParameterType.BOOLEAN, description="Preserve formatting", default=True),
        ],
    ),
    ToolDefinition(
        name="edit_text",
        description="Edit and improve text content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="text", type=ParameterType.STRING, description="Text to edit", required=True),
            ToolParameter(name="instructions", type=ParameterType.STRING, description="Editing instructions", required=True),
            ToolParameter(name="preserve_tone", type=ParameterType.BOOLEAN, description="Preserve original tone", default=True),
        ],
    ),
    ToolDefinition(
        name="generate_seo_metadata",
        description="Generate SEO title and meta description",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(name="page_content", type=ParameterType.STRING, description="Page content or summary", required=True),
            ToolParameter(name="keywords", type=ParameterType.ARRAY, description="Target keywords", items={"type": "string"}),
            ToolParameter(name="brand", type=ParameterType.STRING, description="Brand name", default="SkyyRose"),
        ],
    ),
    
    # -------------------------------------------------------------------------
    # Commerce Tools (8)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="create_product",
        description="Create WooCommerce product",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="name", type=ParameterType.STRING, description="Product name", required=True),
            ToolParameter(name="price", type=ParameterType.NUMBER, description="Product price", required=True, min_value=0),
            ToolParameter(name="description", type=ParameterType.STRING, description="Product description", required=True),
            ToolParameter(name="collection", type=ParameterType.STRING, description="Collection", enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]),
            ToolParameter(name="sizes", type=ParameterType.ARRAY, description="Available sizes", items={"type": "string"}),
            ToolParameter(name="images", type=ParameterType.ARRAY, description="Image URLs", items={"type": "string"}),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="update_product",
        description="Update existing product",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID", required=True),
            ToolParameter(name="updates", type=ParameterType.OBJECT, description="Fields to update", required=True),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_product",
        description="Get product details",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID"),
            ToolParameter(name="sku", type=ParameterType.STRING, description="Product SKU"),
        ],
    ),
    ToolDefinition(
        name="search_products",
        description="Search products",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="query", type=ParameterType.STRING, description="Search query"),
            ToolParameter(name="category", type=ParameterType.STRING, description="Category filter"),
            ToolParameter(name="min_price", type=ParameterType.NUMBER, description="Minimum price"),
            ToolParameter(name="max_price", type=ParameterType.NUMBER, description="Maximum price"),
            ToolParameter(name="in_stock", type=ParameterType.BOOLEAN, description="In stock only", default=True),
            ToolParameter(name="limit", type=ParameterType.INTEGER, description="Result limit", default=20, max_value=100),
        ],
    ),
    ToolDefinition(
        name="update_inventory",
        description="Update product inventory",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID", required=True),
            ToolParameter(name="quantity", type=ParameterType.INTEGER, description="New quantity", required=True),
            ToolParameter(name="variation_id", type=ParameterType.INTEGER, description="Variation ID for variable products"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="create_discount",
        description="Create discount code",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="code", type=ParameterType.STRING, description="Discount code", required=True),
            ToolParameter(name="type", type=ParameterType.STRING, description="Discount type", required=True, enum=["percent", "fixed_cart", "fixed_product"]),
            ToolParameter(name="amount", type=ParameterType.NUMBER, description="Discount amount", required=True),
            ToolParameter(name="expiry", type=ParameterType.STRING, description="Expiry date (ISO format)"),
            ToolParameter(name="usage_limit", type=ParameterType.INTEGER, description="Usage limit"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_orders",
        description="Get orders list",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="status", type=ParameterType.STRING, description="Order status", enum=["pending", "processing", "completed", "cancelled", "refunded"]),
            ToolParameter(name="customer_id", type=ParameterType.INTEGER, description="Customer ID"),
            ToolParameter(name="date_from", type=ParameterType.STRING, description="Start date (ISO format)"),
            ToolParameter(name="date_to", type=ParameterType.STRING, description="End date (ISO format)"),
            ToolParameter(name="limit", type=ParameterType.INTEGER, description="Result limit", default=20),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="process_refund",
        description="Process order refund",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="order_id", type=ParameterType.INTEGER, description="Order ID", required=True),
            ToolParameter(name="amount", type=ParameterType.NUMBER, description="Refund amount"),
            ToolParameter(name="reason", type=ParameterType.STRING, description="Refund reason", required=True),
            ToolParameter(name="restock", type=ParameterType.BOOLEAN, description="Restock items", default=True),
        ],
        requires_auth=True,
    ),
    
    # -------------------------------------------------------------------------
    # Media Tools (6)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="upload_image",
        description="Upload image to media library",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="file_path", type=ParameterType.STRING, description="Local file path or URL", required=True),
            ToolParameter(name="title", type=ParameterType.STRING, description="Image title"),
            ToolParameter(name="alt_text", type=ParameterType.STRING, description="Alt text"),
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Attach to product"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="generate_3d_model",
        description="Generate 3D model from description",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="product_name", type=ParameterType.STRING, description="Product name", required=True),
            ToolParameter(name="garment_type", type=ParameterType.STRING, description="Garment type", required=True, enum=["hoodie", "bomber", "tee", "track_pants", "sweatshirt", "jacket"]),
            ToolParameter(name="collection", type=ParameterType.STRING, description="Collection", enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"]),
            ToolParameter(name="details", type=ParameterType.STRING, description="Additional details"),
            ToolParameter(name="output_format", type=ParameterType.STRING, description="Output format", default="glb", enum=["glb", "gltf", "fbx", "obj"]),
        ],
        requires_auth=True,
        timeout=300.0,
    ),
    ToolDefinition(
        name="virtual_tryon",
        description="Generate virtual try-on image",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="model_image", type=ParameterType.STRING, description="Model/person image path", required=True),
            ToolParameter(name="garment_image", type=ParameterType.STRING, description="Garment image path", required=True),
            ToolParameter(name="category", type=ParameterType.STRING, description="Garment category", default="tops", enum=["tops", "bottoms", "outerwear", "full_body"]),
        ],
        requires_auth=True,
        timeout=120.0,
    ),
    ToolDefinition(
        name="remove_background",
        description="Remove image background",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="image_path", type=ParameterType.STRING, description="Image path", required=True),
            ToolParameter(name="output_format", type=ParameterType.STRING, description="Output format", default="png"),
        ],
    ),
    ToolDefinition(
        name="resize_image",
        description="Resize image",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="image_path", type=ParameterType.STRING, description="Image path", required=True),
            ToolParameter(name="width", type=ParameterType.INTEGER, description="Target width"),
            ToolParameter(name="height", type=ParameterType.INTEGER, description="Target height"),
            ToolParameter(name="maintain_aspect", type=ParameterType.BOOLEAN, description="Maintain aspect ratio", default=True),
        ],
    ),
    ToolDefinition(
        name="optimize_image",
        description="Optimize image for web",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(name="image_path", type=ParameterType.STRING, description="Image path", required=True),
            ToolParameter(name="quality", type=ParameterType.INTEGER, description="Quality (1-100)", default=85, min_value=1, max_value=100),
            ToolParameter(name="format", type=ParameterType.STRING, description="Output format", enum=["webp", "jpeg", "png"]),
        ],
    ),
    
    # -------------------------------------------------------------------------
    # Communication Tools (5)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="send_email",
        description="Send email",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(name="to", type=ParameterType.STRING, description="Recipient email", required=True),
            ToolParameter(name="subject", type=ParameterType.STRING, description="Email subject", required=True),
            ToolParameter(name="body", type=ParameterType.STRING, description="Email body (HTML supported)", required=True),
            ToolParameter(name="template", type=ParameterType.STRING, description="Email template name"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="send_sms",
        description="Send SMS message",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(name="to", type=ParameterType.STRING, description="Phone number", required=True),
            ToolParameter(name="message", type=ParameterType.STRING, description="SMS message", required=True, max_length=160),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="create_notification",
        description="Create system notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(name="title", type=ParameterType.STRING, description="Notification title", required=True),
            ToolParameter(name="message", type=ParameterType.STRING, description="Notification message", required=True),
            ToolParameter(name="type", type=ParameterType.STRING, description="Notification type", default="info", enum=["info", "success", "warning", "error"]),
            ToolParameter(name="user_id", type=ParameterType.INTEGER, description="Target user ID"),
        ],
    ),
    ToolDefinition(
        name="schedule_notification",
        description="Schedule future notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(name="title", type=ParameterType.STRING, description="Notification title", required=True),
            ToolParameter(name="message", type=ParameterType.STRING, description="Notification message", required=True),
            ToolParameter(name="send_at", type=ParameterType.STRING, description="Send time (ISO format)", required=True),
            ToolParameter(name="channel", type=ParameterType.STRING, description="Notification channel", enum=["email", "sms", "push", "webhook"]),
        ],
    ),
    ToolDefinition(
        name="send_webhook",
        description="Send webhook notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(name="url", type=ParameterType.STRING, description="Webhook URL", required=True),
            ToolParameter(name="event_type", type=ParameterType.STRING, description="Event type", required=True),
            ToolParameter(name="payload", type=ParameterType.OBJECT, description="Event payload", required=True),
        ],
        requires_auth=True,
    ),
    
    # -------------------------------------------------------------------------
    # Analytics Tools (5)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="get_sales_analytics",
        description="Get sales analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="period", type=ParameterType.STRING, description="Time period", default="30d", enum=["7d", "30d", "90d", "1y", "custom"]),
            ToolParameter(name="start_date", type=ParameterType.STRING, description="Start date for custom period"),
            ToolParameter(name="end_date", type=ParameterType.STRING, description="End date for custom period"),
            ToolParameter(name="group_by", type=ParameterType.STRING, description="Group by", default="day", enum=["hour", "day", "week", "month"]),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_product_analytics",
        description="Get product performance analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID"),
            ToolParameter(name="period", type=ParameterType.STRING, description="Time period", default="30d"),
            ToolParameter(name="metrics", type=ParameterType.ARRAY, description="Metrics to include", items={"type": "string"}),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_customer_analytics",
        description="Get customer analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="metric", type=ParameterType.STRING, description="Metric type", required=True, enum=["acquisition", "retention", "ltv", "segments"]),
            ToolParameter(name="period", type=ParameterType.STRING, description="Time period", default="30d"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="forecast_demand",
        description="Forecast product demand",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="product_ids", type=ParameterType.ARRAY, description="Product IDs", items={"type": "integer"}),
            ToolParameter(name="horizon", type=ParameterType.INTEGER, description="Forecast horizon (days)", default=30, min_value=7, max_value=90),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="generate_report",
        description="Generate analytics report",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="report_type", type=ParameterType.STRING, description="Report type", required=True, enum=["sales", "inventory", "customers", "marketing"]),
            ToolParameter(name="period", type=ParameterType.STRING, description="Time period", required=True),
            ToolParameter(name="format", type=ParameterType.STRING, description="Output format", default="pdf", enum=["pdf", "excel", "json"]),
        ],
        requires_auth=True,
    ),
    
    # -------------------------------------------------------------------------
    # Integration Tools (4)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="wordpress_api_call",
        description="Make WordPress REST API call",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(name="endpoint", type=ParameterType.STRING, description="API endpoint", required=True),
            ToolParameter(name="method", type=ParameterType.STRING, description="HTTP method", default="GET", enum=["GET", "POST", "PUT", "DELETE"]),
            ToolParameter(name="data", type=ParameterType.OBJECT, description="Request data"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="deploy_elementor_template",
        description="Deploy Elementor template",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(name="template_name", type=ParameterType.STRING, description="Template name", required=True),
            ToolParameter(name="page_id", type=ParameterType.INTEGER, description="Target page ID"),
            ToolParameter(name="create_page", type=ParameterType.BOOLEAN, description="Create new page if page_id not provided", default=True),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="sync_inventory",
        description="Sync inventory with external system",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(name="source", type=ParameterType.STRING, description="Data source", required=True, enum=["shopify", "square", "csv", "api"]),
            ToolParameter(name="mode", type=ParameterType.STRING, description="Sync mode", default="update", enum=["update", "replace", "merge"]),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="export_data",
        description="Export data to external format",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(name="data_type", type=ParameterType.STRING, description="Data type", required=True, enum=["products", "orders", "customers", "analytics"]),
            ToolParameter(name="format", type=ParameterType.STRING, description="Export format", default="csv", enum=["csv", "json", "xml"]),
            ToolParameter(name="filters", type=ParameterType.OBJECT, description="Data filters"),
        ],
        requires_auth=True,
    ),
    
    # -------------------------------------------------------------------------
    # System Tools (2)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="clear_cache",
        description="Clear system cache",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(name="cache_type", type=ParameterType.STRING, description="Cache type", default="all", enum=["all", "page", "object", "cdn"]),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="health_check",
        description="Check system health",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(name="components", type=ParameterType.ARRAY, description="Components to check", items={"type": "string"}),
        ],
    ),
]


# Verify we have 37 tools
assert len(BUILTIN_TOOLS) == 37, f"Expected 37 tools, got {len(BUILTIN_TOOLS)}"
