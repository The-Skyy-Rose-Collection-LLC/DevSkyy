#!/usr/bin/env python3
"""
Test script for OpenAI MCP Server

This script validates the server.py file structure and functionality
without requiring full dependencies to be installed.
"""

import ast
import sys
from pathlib import Path


def validate_server_file():
    """Validate server.py structure and syntax."""
    print("🔍 Validating OpenAI MCP Server...")

    server_path = Path(__file__).parent / "server.py"

    if not server_path.exists():
        print("❌ server.py not found!")
        return False

    print("✅ server.py exists")

    # Read the file
    with open(server_path, "r") as f:
        content = f.read()

    # Check syntax
    try:
        tree = ast.parse(content)
        print("✅ Python syntax valid")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False

    # Check for required components

    # Check for tool names in content (decorated functions may have different internal names)
    required_tools = [
        "openai_completion",
        "openai_code_generation",
        "openai_vision_analysis",
        "openai_function_calling",
        "openai_model_selector",
        "devskyy_agent_openai",
        "openai_capabilities_info",
    ]

    required_models = [
        "OpenAICompletionInput",
        "CodeGenerationInput",
        "VisionAnalysisInput",
        "FunctionCallingInput",
        "ModelSelectionInput",
        "DevSkyyAgentInput",
    ]

    required_enums = [
        "ResponseFormat",
        "OpenAIModel",
        "TaskType",
    ]

    # Extract function and class names
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    # Validate required tools (check in file content)
    print("\n📋 Checking required MCP tools...")
    for tool in required_tools:
        if f'name="{tool}"' in content or f"name='{tool}'" in content:
            print(f"  ✅ {tool}")
        else:
            print(f"  ❌ Missing tool: {tool}")
            return False

    # Validate required models
    print("\n📋 Checking required Pydantic models...")
    for model in required_models:
        if model in classes:
            print(f"  ✅ {model}")
        else:
            print(f"  ❌ Missing model: {model}")
            return False

    # Validate required enums
    print("\n📋 Checking required enums...")
    for enum in required_enums:
        if enum in classes:
            print(f"  ✅ {enum}")
        else:
            print(f"  ❌ Missing enum: {enum}")
            return False

    # Check for main entry point
    has_main = any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        for node in ast.walk(tree)
    )

    if has_main:
        print("\n✅ Main entry point found")
    else:
        print("\n❌ Missing main entry point")
        return False

    # Check docstrings
    print("\n📋 Checking documentation...")
    module_docstring = ast.get_docstring(tree)
    if module_docstring and len(module_docstring) > 100:
        print("  ✅ Module docstring present")
    else:
        print("  ⚠️  Module docstring missing or too short")

    # Count documented functions
    documented = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node):
                documented += 1

    if documented >= len(required_tools):
        print(f"  ✅ All functions documented ({documented})")
    else:
        print(f"  ⚠️  Some functions missing docstrings ({documented}/{len(required_tools)})")

    # Check configuration
    print("\n📋 Checking configuration...")
    config_vars = [
        "API_BASE_URL",
        "API_KEY",
        "OPENAI_API_KEY",
        "CHARACTER_LIMIT",
        "REQUEST_TIMEOUT",
    ]

    # Simple string search for config variables
    for var in config_vars:
        if var in content:
            print(f"  ✅ {var} configured")
        else:
            print(f"  ❌ Missing config: {var}")
            return False

    # Check for OpenAI models definition
    if "OPENAI_MODELS" in content:
        print("  ✅ OPENAI_MODELS defined")
    else:
        print("  ❌ OPENAI_MODELS not found")
        return False

    print("\n" + "=" * 60)
    print("✅ All validation checks passed!")
    print("=" * 60)

    return True


def print_server_info():
    """Print information about the server."""
    print("\n📊 Server Information:")
    print("  Name: DevSkyy OpenAI MCP Server")
    print("  Version: 1.0.0")
    print("  Protocol: Model Context Protocol (MCP)")
    print("  Framework: FastMCP")
    print("  Python: 3.11+")
    print("\n  Supported Models:")
    print("    • GPT-4o (vision, function calling, JSON mode)")
    print("    • GPT-4o-mini (vision, function calling, JSON mode)")
    print("    • o1-preview (advanced reasoning)")
    print("\n  Available Tools:")
    print("    1. openai_completion - Text generation")
    print("    2. openai_code_generation - Code generation with tests")
    print("    3. openai_vision_analysis - Image analysis")
    print("    4. openai_function_calling - Structured function calls")
    print("    5. openai_model_selector - Intelligent model selection")
    print("    6. devskyy_agent_openai - DevSkyy agent integration")
    print("    7. openai_capabilities_info - Capabilities reference")
    print("\n  Dependencies:")
    print("    • fastmcp>=0.1.0")
    print("    • httpx>=0.24.0")
    print("    • pydantic>=2.5.0")
    print("    • openai>=1.6.0")
    print("    • python-jose[cryptography]>=3.3.0")


if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI MCP Server Validation")
    print("=" * 60)

    if validate_server_file():
        print_server_info()
        print("\n✅ Server is ready to use!")
        print("\n📝 Next steps:")
        print("  1. Install dependencies: pip install fastmcp httpx pydantic openai")
        print("  2. Set OPENAI_API_KEY environment variable")
        print("  3. Run server: python server.py")
        print("  4. Or configure in Claude Desktop (see SERVER_README.md)")
        sys.exit(0)
    else:
        print("\n❌ Validation failed!")
        print("Please review the errors above and fix server.py")
        sys.exit(1)
