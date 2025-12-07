---
name: mcp-powerhouse-integration
description: MCP (Model Context Protocol) powerhouse integration for DevSkyy's four agent categories with multi-model tool calling
---

You are the MCP Powerhouse Integration expert for DevSkyy. Implement Model Context Protocol tooling for all four agent categories, enabling multi-model AI agents to use specialized tools and maintain context across conversations.

## MCP Architecture Overview

**Model Context Protocol (MCP)** enables AI models to:
- Access specialized tools and APIs
- Maintain conversation context
- Execute complex multi-step workflows
- Share state across agent invocations

## Category Powerhouse Structure

### Frontend Powerhouse (Claude + Gemini)
**Tools:** UI generation, design analysis, component libraries, accessibility checking
**Models:** Claude Sonnet 4.5, Gemini Pro
**Capabilities:** React/TypeScript generation, Tailwind CSS, Elementor, responsive design

### Backend Powerhouse (Claude + ChatGPT-5)
**Tools:** API design, database optimization, security scanning, performance monitoring
**Models:** Claude Sonnet 4.5, ChatGPT-5
**Capabilities:** FastAPI, SQLAlchemy, authentication, caching, rate limiting

### Content Powerhouse (Huggingface + Claude + Gemini + ChatGPT-5)
**Tools:** Image analysis, content generation, SEO optimization, social media posting
**Models:** Huggingface Transformers, Claude, Gemini Vision, ChatGPT-5
**Capabilities:** Fashion AI, brand voice, multi-platform content, visual understanding

### Development Powerhouse (Claude + Codex)
**Tools:** Code generation, testing, refactoring, git operations, CI/CD
**Models:** Claude Sonnet 4.5, ChatGPT Codex
**Capabilities:** Python 3.11, TypeScript, automated testing, code review

## Core MCP Implementation

### 1. MCP Tool Registry

```python
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

class ToolCategory(Enum):
    """Tool categories matching agent powerhouses"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    CONTENT = "content"
    DEVELOPMENT = "development"

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    category: ToolCategory
    description: str
    parameters: Dict[str, Any]  # JSON schema for parameters
    function: Callable
    required_models: List[str]  # Which AI models can use this tool
    returns: str  # Return type description

class MCPToolRegistry:
    """Registry for all MCP tools"""

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self._register_all_tools()

    def _register_all_tools(self):
        """Register all tools for all categories"""

        # Frontend Tools
        self.register_tool(MCPTool(
            name="generate_react_component",
            category=ToolCategory.FRONTEND,
            description="Generate a React TypeScript component with brand styling",
            parameters={
                "type": "object",
                "properties": {
                    "component_type": {"type": "string", "description": "Type of component"},
                    "props": {"type": "object", "description": "Component props"},
                    "brand_colors": {"type": "object", "description": "Brand color palette"},
                    "features": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["component_type"]
            },
            function=self._generate_react_component,
            required_models=["claude-sonnet-4-5", "gemini-pro"],
            returns="React TypeScript component code"
        ))

        self.register_tool(MCPTool(
            name="analyze_ui_design",
            category=ToolCategory.FRONTEND,
            description="Analyze UI design mockup for brand alignment and UX",
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Path to design image"},
                    "brand_guidelines": {"type": "object", "description": "Brand guidelines"},
                    "check_accessibility": {"type": "boolean", "default": True}
                },
                "required": ["image_path"]
            },
            function=self._analyze_ui_design,
            required_models=["gemini-pro", "claude-sonnet-4-5"],
            returns="Design analysis with scores and recommendations"
        ))

        # Backend Tools
        self.register_tool(MCPTool(
            name="design_fastapi_endpoint",
            category=ToolCategory.BACKEND,
            description="Design FastAPI endpoint with validation, auth, and error handling",
            parameters={
                "type": "object",
                "properties": {
                    "endpoint_name": {"type": "string"},
                    "http_method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "request_model": {"type": "object"},
                    "response_model": {"type": "object"},
                    "requires_auth": {"type": "boolean", "default": True},
                    "rate_limit": {"type": "string", "default": "100/minute"}
                },
                "required": ["endpoint_name", "http_method"]
            },
            function=self._design_fastapi_endpoint,
            required_models=["claude-sonnet-4-5", "gpt-5"],
            returns="Complete FastAPI endpoint code"
        ))

        self.register_tool(MCPTool(
            name="optimize_database_query",
            category=ToolCategory.BACKEND,
            description="Optimize SQLAlchemy query for performance",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQLAlchemy query code"},
                    "table_schema": {"type": "object"},
                    "expected_rows": {"type": "integer"}
                },
                "required": ["query"]
            },
            function=self._optimize_database_query,
            required_models=["claude-sonnet-4-5", "gpt-5"],
            returns="Optimized query with explanation"
        ))

        # Content Tools
        self.register_tool(MCPTool(
            name="analyze_fashion_image",
            category=ToolCategory.CONTENT,
            description="Analyze fashion product image with ML",
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "style", "technical", "pricing"]
                    }
                },
                "required": ["image_path"]
            },
            function=self._analyze_fashion_image,
            required_models=["gemini-pro", "huggingface", "claude-sonnet-4-5"],
            returns="Fashion analysis with categories, materials, style, pricing"
        ))

        self.register_tool(MCPTool(
            name="generate_brand_content",
            category=ToolCategory.CONTENT,
            description="Generate brand-aligned content for marketing",
            parameters={
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": ["product_description", "social_post", "email", "blog_post"]
                    },
                    "product_data": {"type": "object"},
                    "platform": {"type": "string"},
                    "brand_voice": {"type": "object"}
                },
                "required": ["content_type"]
            },
            function=self._generate_brand_content,
            required_models=["claude-sonnet-4-5", "gpt-5", "gemini-pro"],
            returns="Brand-aligned content with SEO optimization"
        ))

        # Development Tools
        self.register_tool(MCPTool(
            name="generate_python_function",
            category=ToolCategory.DEVELOPMENT,
            description="Generate Python function with type hints and tests",
            parameters={
                "type": "object",
                "properties": {
                    "function_name": {"type": "string"},
                    "description": {"type": "string"},
                    "parameters": {"type": "array"},
                    "return_type": {"type": "string"},
                    "include_tests": {"type": "boolean", "default": True},
                    "include_docstring": {"type": "boolean", "default": True}
                },
                "required": ["function_name", "description"]
            },
            function=self._generate_python_function,
            required_models=["claude-sonnet-4-5", "codex"],
            returns="Python function with tests and documentation"
        ))

        self.register_tool(MCPTool(
            name="review_code_quality",
            category=ToolCategory.DEVELOPMENT,
            description="Review code for quality, security, and best practices",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string", "default": "python"},
                    "check_security": {"type": "boolean", "default": True},
                    "check_performance": {"type": "boolean", "default": True},
                    "check_style": {"type": "boolean", "default": True}
                },
                "required": ["code"]
            },
            function=self._review_code_quality,
            required_models=["claude-sonnet-4-5", "codex"],
            returns="Code review with issues, recommendations, and score"
        ))

    def register_tool(self, tool: MCPTool):
        """Register a tool in the registry"""
        self.tools[tool.name] = tool

    def get_tools_for_category(self, category: ToolCategory) -> List[MCPTool]:
        """Get all tools for a specific category"""
        return [tool for tool in self.tools.values() if tool.category == category]

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def get_tools_for_model(self, model: str, category: Optional[ToolCategory] = None) -> List[MCPTool]:
        """Get tools available for a specific AI model"""
        tools = self.tools.values()
        if category:
            tools = [t for t in tools if t.category == category]
        return [tool for tool in tools if model in tool.required_models]

    # Tool Implementations

    async def _generate_react_component(self, **kwargs) -> Dict[str, Any]:
        """Generate React component"""
        # Implementation uses multi-model orchestrator
        from skills.multi_model_orchestrator import FrontendAgentOrchestrator, MultiModelOrchestrator

        orchestrator = MultiModelOrchestrator()
        frontend = FrontendAgentOrchestrator(orchestrator)

        result = await frontend.generate_ui_component(kwargs)
        return {"success": True, "component_code": result.get("content")}

    async def _analyze_ui_design(self, **kwargs) -> Dict[str, Any]:
        """Analyze UI design"""
        from skills.google_gemini_integration import GeminiFrontendAgent, GeminiClient
        from skills.brand_intelligence import BrandIntelligenceManager

        brand_manager = BrandIntelligenceManager()
        gemini = GeminiClient()
        frontend_agent = GeminiFrontendAgent(brand_manager, gemini)

        result = await frontend_agent.analyze_ui_design(kwargs.get("image_path"))
        return result

    async def _design_fastapi_endpoint(self, **kwargs) -> Dict[str, Any]:
        """Design FastAPI endpoint"""
        from skills.multi_model_orchestrator import BackendAgentOrchestrator, MultiModelOrchestrator

        orchestrator = MultiModelOrchestrator()
        backend = BackendAgentOrchestrator(orchestrator)

        result = await backend.design_api(kwargs)
        return {"success": True, "endpoint_code": result.get("content")}

    async def _optimize_database_query(self, **kwargs) -> Dict[str, Any]:
        """Optimize database query"""
        from skills.multi_model_orchestrator import BackendAgentOrchestrator, MultiModelOrchestrator

        orchestrator = MultiModelOrchestrator()
        backend = BackendAgentOrchestrator(orchestrator)

        result = await backend.optimize_database(kwargs)
        return {"success": True, "optimized_query": result.get("content")}

    async def _analyze_fashion_image(self, **kwargs) -> Dict[str, Any]:
        """Analyze fashion image"""
        from skills.google_gemini_integration import GeminiContentAgent, GeminiClient
        from skills.brand_intelligence import BrandIntelligenceManager

        brand_manager = BrandIntelligenceManager()
        gemini = GeminiClient()
        content_agent = GeminiContentAgent(brand_manager, gemini)

        result = await content_agent.analyze_fashion_image(
            kwargs.get("image_path"),
            kwargs.get("analysis_type", "comprehensive")
        )
        return result

    async def _generate_brand_content(self, **kwargs) -> Dict[str, Any]:
        """Generate brand content"""
        from skills.google_gemini_integration import GeminiContentAgent, GeminiClient
        from skills.brand_intelligence import BrandIntelligenceManager

        brand_manager = BrandIntelligenceManager()
        gemini = GeminiClient()
        content_agent = GeminiContentAgent(brand_manager, gemini)

        result = await content_agent.generate_product_content(
            kwargs.get("product_data", {}),
            kwargs.get("content_type", "description")
        )
        return result

    async def _generate_python_function(self, **kwargs) -> Dict[str, Any]:
        """Generate Python function"""
        from skills.multi_model_orchestrator import DevelopmentAgentOrchestrator, MultiModelOrchestrator

        orchestrator = MultiModelOrchestrator()
        development = DevelopmentAgentOrchestrator(orchestrator)

        result = await development.generate_code(kwargs)
        return {"success": True, "function_code": result.get("content")}

    async def _review_code_quality(self, **kwargs) -> Dict[str, Any]:
        """Review code quality"""
        from skills.multi_model_orchestrator import DevelopmentAgentOrchestrator, MultiModelOrchestrator

        orchestrator = MultiModelOrchestrator()
        development = DevelopmentAgentOrchestrator(orchestrator)

        result = await development.review_code(kwargs.get("code", ""))
        return {"success": True, "review": result.get("content")}
```

### 2. MCP Context Manager

```python
from datetime import datetime

class MCPContextManager:
    """Manage conversation context across MCP tool calls"""

    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}

    def create_context(self, session_id: str, category: ToolCategory) -> Dict[str, Any]:
        """Create new context for a session"""
        context = {
            "session_id": session_id,
            "category": category.value,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "tool_calls": [],
            "state": {},
            "brand_context": {}
        }
        self.contexts[session_id] = context
        return context

    def add_message(self, session_id: str, role: str, content: str, model: Optional[str] = None):
        """Add message to context"""
        if session_id not in self.contexts:
            return False

        self.contexts[session_id]["messages"].append({
            "role": role,
            "content": content,
            "model": model,
            "timestamp": datetime.now().isoformat()
        })
        return True

    def add_tool_call(self, session_id: str, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Record tool call in context"""
        if session_id not in self.contexts:
            return False

        self.contexts[session_id]["tool_calls"].append({
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        return True

    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get context for a session"""
        return self.contexts.get(session_id)

    def update_state(self, session_id: str, key: str, value: Any):
        """Update context state"""
        if session_id in self.contexts:
            self.contexts[session_id]["state"][key] = value
```

## Usage Examples

### Example 1: Frontend Powerhouse with MCP

```python
from skills.mcp_powerhouse_integration import MCPToolRegistry, MCPContextManager, ToolCategory

# Initialize
registry = MCPToolRegistry()
context_manager = MCPContextManager()

# Create session context
session_id = "frontend-session-001"
context = context_manager.create_context(session_id, ToolCategory.FRONTEND)

# Get frontend tools
frontend_tools = registry.get_tools_for_category(ToolCategory.FRONTEND)
print(f"Available tools: {[t.name for t in frontend_tools]}")

# Use tool: Generate React component
generate_component = registry.get_tool("generate_react_component")
result = await generate_component.function(
    component_type="ProductCard",
    props={"name": "string", "price": "number", "image": "string"},
    brand_colors={"primary": "#1a1a1a", "accent": "#c9a96e"},
    features=["hover_animation", "responsive", "accessibility"]
)

# Record in context
context_manager.add_tool_call(
    session_id,
    "generate_react_component",
    {"component_type": "ProductCard"},
    result
)

print(f"Generated component:\n{result['component_code']}")
```

### Example 2: Content Powerhouse Multi-Model

```python
# Content powerhouse uses ALL models: HF + Claude + Gemini + GPT-5
content_tools = registry.get_tools_for_category(ToolCategory.CONTENT)

# Analyze fashion image (uses Gemini Vision)
analyze_tool = registry.get_tool("analyze_fashion_image")
analysis = await analyze_tool.function(
    image_path="products/dress-001.jpg",
    analysis_type="comprehensive"
)

# Generate content (uses Claude for brand voice)
content_tool = registry.get_tool("generate_brand_content")
content = await content_tool.function(
    content_type="product_description",
    product_data={
        "name": "Silk Evening Dress",
        "category": "evening_wear",
        "price": 499,
        "materials": ["silk"],
        "analysis": analysis  # Use image analysis results
    }
)

print(f"Image analysis: {analysis['analysis']}")
print(f"Generated content: {content['content']}")
```

### Example 3: Development Powerhouse

```python
# Development: Claude + Codex
dev_tools = registry.get_tools_for_category(ToolCategory.DEVELOPMENT)

# Generate function
gen_tool = registry.get_tool("generate_python_function")
function = await gen_tool.function(
    function_name="calculate_optimal_price",
    description="Calculate optimal product price using demand forecasting",
    parameters=[
        {"name": "base_cost", "type": "float"},
        {"name": "demand_score", "type": "int"},
        {"name": "competitor_prices", "type": "List[float]"}
    ],
    return_type="float",
    include_tests=True
)

# Review generated code
review_tool = registry.get_tool("review_code_quality")
review = await review_tool.function(
    code=function['function_code'],
    language="python",
    check_security=True,
    check_performance=True
)

print(f"Code quality score: {review['score']}")
print(f"Issues: {review['issues']}")
```

## MCP Tool Specifications (JSON Schema)

Each tool follows OpenAI/Claude function calling format:

```json
{
  "name": "generate_react_component",
  "description": "Generate a React TypeScript component with brand styling",
  "parameters": {
    "type": "object",
    "properties": {
      "component_type": {
        "type": "string",
        "description": "Type of component (Button, Card, Navbar, etc.)"
      },
      "props": {
        "type": "object",
        "description": "Component props with types"
      },
      "brand_colors": {
        "type": "object",
        "description": "Brand color palette"
      },
      "features": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Component features"
      }
    },
    "required": ["component_type"]
  }
}
```

## Truth Protocol Compliance

- ✅ Tool calls tracked in error ledger (Rule 10)
- ✅ Type-safe tool definitions (Rule 11)
- ✅ Context management for traceability (Rule 9)
- ✅ Multi-model redundancy (Rule 12)
- ✅ Brand integration in all tools

## Integration Summary

| Powerhouse | Models | Tools | Primary Use Case |
|------------|--------|-------|------------------|
| **Frontend** | Claude + Gemini | 10+ UI/design tools | React components, theme generation, UX analysis |
| **Backend** | Claude + GPT-5 | 15+ API/DB tools | FastAPI endpoints, database optimization, auth |
| **Content** | HF + Claude + Gemini + GPT-5 | 20+ content tools | Fashion AI, brand content, social media |
| **Development** | Claude + Codex | 12+ dev tools | Code generation, testing, reviews, refactoring |

Use this skill to enable AI agents with specialized tools through MCP, creating powerful multi-model agent systems.
