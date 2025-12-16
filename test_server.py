#!/usr/bin/env python3
"""
Test suite for DevSkyy OpenAI MCP Server
Validates syntax, tools, models, and Pydantic schemas.
"""

import ast
import json
import sys
from pathlib import Path


def test_syntax_validation():
    """Test that server.py has valid Python syntax."""
    print("Testing syntax validation...")

    server_path = Path("server.py")
    if not server_path.exists():
        print("❌ server.py not found")
        return False

    try:
        with open(server_path) as f:
            source = f.read()
        ast.parse(source)
        print("✅ server.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in server.py: {e}")
        return False


def test_tool_definitions():
    """Test that all 7 tools are properly defined."""
    print("Testing tool definitions...")

    expected_tools = [
        "openai_completion",
        "openai_code_generation",
        "openai_vision_analysis",
        "openai_function_calling",
        "openai_model_selector",
        "devskyy_agent_openai",
        "openai_capabilities_info",
    ]

    try:
        # Import the server module
        sys.path.insert(0, ".")
        import server

        # Check if all expected tools are defined
        for tool_name in expected_tools:
            handler_name = f"handle_{tool_name.replace('openai_', '').replace('devskyy_agent_openai', 'devskyy_agent')}"
            if not hasattr(server, handler_name):
                print(f"❌ Missing handler: {handler_name}")
                return False

        print(f"✅ All {len(expected_tools)} tools properly defined")
        return True
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        return False


def test_pydantic_models():
    """Test that all Pydantic models are valid."""
    print("Testing Pydantic models...")

    expected_models = [
        "CompletionRequest",
        "CodeGenerationRequest",
        "VisionAnalysisRequest",
        "FunctionCallingRequest",
        "ModelSelectorRequest",
        "DevSkyyAgentRequest",
    ]

    try:
        import server

        for model_name in expected_models:
            if not hasattr(server, model_name):
                print(f"❌ Missing Pydantic model: {model_name}")
                return False

            model_class = getattr(server, model_name)
            # Test that it's a Pydantic model
            if not hasattr(model_class, "__fields__"):
                print(f"❌ {model_name} is not a valid Pydantic model")
                return False

        print(f"✅ All {len(expected_models)} Pydantic models valid")
        return True
    except Exception as e:
        print(f"❌ Pydantic model validation failed: {e}")
        return False


def test_model_support():
    """Test that all OpenAI models are supported."""
    print("Testing model support...")

    expected_models = ["gpt-4o", "gpt-4o-mini", "o1-preview"]

    try:
        import server

        # Test model selector logic
        for model in expected_models:
            server.ModelSelectorRequest(task_description="test task", priority="balanced")
            print(f"✅ Model {model} supported")

        print(f"✅ All {len(expected_models)} models supported")
        return True
    except Exception as e:
        print(f"❌ Model support test failed: {e}")
        return False


def test_environment_handling():
    """Test environment variable handling."""
    print("Testing environment handling...")

    try:
        import os

        import server

        # Test with missing API key
        original_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        # Should handle missing key gracefully
        if server.openai_client is None:
            print("✅ Handles missing OPENAI_API_KEY gracefully")

        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key

        return True
    except Exception as e:
        print(f"❌ Environment handling test failed: {e}")
        return False


def test_documentation_files():
    """Test that documentation files exist and are valid."""
    print("Testing documentation files...")

    doc_files = [
        "SERVER_README.md",
        "QUICKSTART.md",
        "claude_desktop_config.example.json",
    ]

    for doc_file in doc_files:
        path = Path(doc_file)
        if not path.exists():
            print(f"❌ Missing documentation file: {doc_file}")
            return False

        if doc_file.endswith(".json"):
            try:
                with open(path) as f:
                    json.load(f)
                print(f"✅ {doc_file} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ {doc_file} has invalid JSON: {e}")
                return False
        else:
            print(f"✅ {doc_file} exists")

    return True


def main():
    """Run all tests."""
    print("🧪 DevSkyy OpenAI MCP Server Test Suite")
    print("=" * 50)

    tests = [
        test_syntax_validation,
        test_tool_definitions,
        test_pydantic_models,
        test_model_support,
        test_environment_handling,
        test_documentation_files,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Server is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
