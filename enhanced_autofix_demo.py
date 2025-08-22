#!/usr/bin/env python3
"""
🤖 DevSkyy Enhanced Auto-Fix - Usage Examples and Demo

This script demonstrates how to use the new enhanced auto-fix functionality.
Run this to see the auto-fix system in action!
"""

import requests
import json
import sys
from datetime import datetime


def demo_enhanced_autofix():
    """Demonstrate the enhanced auto-fix capabilities"""

    print("🚀 DevSkyy Enhanced Auto-Fix Demo")
    print("=" * 50)
    print(f"Demo started at: {datetime.now()}")
    print()

    # Base URL for the API (adjust if needed)
    base_url = "http://localhost:8000"  # Change to your server URL

    print("📋 Available Enhanced Auto-Fix Endpoints:")
    print()

    endpoints = [
        {
            "method": "POST",
            "endpoint": "/autofix/enhanced",
            "description": "Full enhanced auto-fix with branch management",
            "params": {
                "create_branch": True,
                "branch_name": "auto-fix-demo",
                "auto_commit": True,
                "fix_types": ["security", "optimization"]
            }
        },
        {
            "method": "POST",
            "endpoint": "/autofix/quick",
            "description": "Quick fix without branch creation",
            "params": {}
        },
        {
            "method": "POST",
            "endpoint": "/autofix/session",
            "description": "Customizable auto-fix session",
            "params": {
                "create_branch": False,
                "auto_commit": True
            }
        },
        {
            "method": "GET",
            "endpoint": "/autofix/status",
            "description": "Get auto-fix status and capabilities",
            "params": {}
        },
        {
            "method": "POST",
            "endpoint": "/run/enhanced",
            "description": "Enhanced DevSkyy workflow",
            "params": {}
        }
    ]

    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['method']} {endpoint['endpoint']}")
        print(f"   Description: {endpoint['description']}")
        if endpoint['params']:
            print(f"   Example params: {json.dumps(endpoint['params'], indent=6)}")
        print()

    print("🔧 Auto-Fix Capabilities:")
    print()
    capabilities = [
        "🐍 Python Enhancement: Type hints, docstrings, PEP8 formatting, f-string optimization",
        "📜 JavaScript Modernization: ES6+ features, arrow functions, strict mode",
        "🔒 Security Scanning: Hardcoded secrets detection and warnings",
        "🏗️ Project Structure: Missing __init__.py files, configuration improvements",
        "⚡ Performance Optimization: Code pattern improvements and suggestions",
        "🌿 Branch Management: Automatic branch creation for fixes",
        "💬 Smart Commit Messages: Detailed commit messages with fix categorization",
        "🔗 Git Integration: Seamless integration with existing Git workflow"
    ]

    for capability in capabilities:
        print(f"  {capability}")

    print()
    print("💡 Usage Examples:")
    print()

    # Example usage with curl commands
    examples = [
        {
            "title": "Quick Fix (No Branch)",
            "command": f"curl -X POST {base_url}/autofix/quick"
        },
        {
            "title": "Enhanced Fix with Custom Branch",
            "command": f"""curl -X POST {base_url}/autofix/enhanced \\
  -H "Content-Type: application/json" \\
  -d '{{"create_branch": true, "branch_name": "feature/auto-fixes", "auto_commit": true}}'"""
        },
        {
            "title": "Get Auto-Fix Status",
            "command": f"curl -X GET {base_url}/autofix/status"
        },
        {
            "title": "Enhanced DevSkyy Workflow",
            "command": f"curl -X POST {base_url}/run/enhanced"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}:")
        print(f"   {example['command']}")
        print()

    print("🎯 Quick Start:")
    print("1. Start the DevSkyy server: uvicorn main:app --host 0.0.0.0 --port 8000")
    print("2. Run a quick fix: curl -X POST http://localhost:8000/autofix/quick")
    print("3. Check status: curl -X GET http://localhost:8000/autofix/status")
    print("4. For advanced fixes with branching: Use /autofix/enhanced endpoint")
    print()

    print("📊 Expected Results:")
    print("- Comprehensive code scanning and analysis")
    print("- Automatic fixing of Python, JavaScript, HTML, CSS issues")
    print("- Security vulnerability detection and warnings")
    print("- Project structure improvements")
    print("- Professional Git commits with detailed messages")
    print("- Optional branch creation for organized development")
    print()

    print("🎉 The DevSkyy Enhanced Auto-Fix system is ready to help!")
    print("   Enjoy automated code quality improvements! 🤖✨")


def test_server_connection():
    """Test if the DevSkyy server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ DevSkyy server is running!")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to DevSkyy server")
        print("💡 Start the server with: uvicorn main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False


if __name__ == "__main__":
    demo_enhanced_autofix()

    print("\n" + "="*50)
    print("🔍 Server Connection Test:")
    test_server_connection()
