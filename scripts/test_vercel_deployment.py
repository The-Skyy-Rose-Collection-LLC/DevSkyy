#!/usr/bin/env python3
"""
Vercel Deployment Test Script
============================

Tests the Vercel deployment configuration locally before deploying.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from api.index import app, handler, handler_func
        print("✅ API index imports successful")
        
        from main_enterprise import app as main_app
        print("✅ Main application import successful")
        
        import mangum
        print("✅ Mangum ASGI adapter available")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_app_creation():
    """Test that the FastAPI app is properly created"""
    print("\n🔍 Testing app creation...")
    
    try:
        from api.index import app
        
        if app is None:
            print("❌ App is None")
            return False
            
        # Check if it's a FastAPI instance
        from fastapi import FastAPI
        if not isinstance(app, FastAPI):
            print(f"❌ App is not FastAPI instance: {type(app)}")
            return False
            
        print("✅ FastAPI app created successfully")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
        
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False


def test_handler():
    """Test the Mangum handler"""
    print("\n🔍 Testing Mangum handler...")
    
    try:
        from api.index import handler_func
        
        # Create a simple test event (simulating Vercel)
        test_event = {
            "httpMethod": "GET",
            "path": "/api/health",
            "headers": {},
            "body": None
        }
        
        test_context = {}
        
        # This would normally be called by Vercel
        # For testing, we just check if the function exists
        if callable(handler_func):
            print("✅ Handler function is callable")
            return True
        else:
            print("❌ Handler function is not callable")
            return False
            
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        return False


def test_vercel_config():
    """Test vercel.json configuration"""
    print("\n🔍 Testing vercel.json configuration...")
    
    try:
        vercel_config_path = project_root / "vercel.json"
        
        if not vercel_config_path.exists():
            print("❌ vercel.json not found")
            return False
            
        with open(vercel_config_path) as f:
            config = json.load(f)
            
        required_keys = ["version", "builds", "routes"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key in vercel.json: {key}")
                return False
                
        print("✅ vercel.json configuration is valid")
        print(f"   Version: {config.get('version')}")
        print(f"   Builds: {len(config.get('builds', []))}")
        print(f"   Routes: {len(config.get('routes', []))}")
        
        return True
    except Exception as e:
        print(f"❌ vercel.json test failed: {e}")
        return False


def main():
    """Run all deployment tests"""
    print("🚀 DevSkyy Vercel Deployment Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_app_creation,
        test_handler,
        test_vercel_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print()
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Vercel deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
