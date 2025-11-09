#!/usr/bin/env python3
"""
WordPress Integration Testing Script
Test all WordPress credential configurations and theme builder integration
"""

import asyncio
import sys
from pathlib import Path
import tempfile

# Add DevSkyy to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_credential_loading():
    """Test credential loading from environment."""
    print("🔐 Testing Credential Loading")
    print("-" * 40)
    
    try:
        from config.wordpress_credentials import (
            get_skyy_rose_credentials,
            validate_environment_setup
        )
        
        # Test environment validation
        env_validation = validate_environment_setup()
        print(f"Environment validation: {'✅ VALID' if env_validation['valid'] else '❌ INVALID'}")
        
        if env_validation['missing_required']:
            print(f"❌ Missing required variables: {env_validation['missing_required']}")
            return False
        
        if env_validation['configured_vars']:
            print(f"✅ Configured variables: {len(env_validation['configured_vars'])}")
        
        # Test credential loading
        credentials = get_skyy_rose_credentials()
        if credentials:
            print(f"✅ Skyy Rose credentials loaded")
            print(f"   Site URL: {credentials.site_url}")
            print(f"   Username: {credentials.username}")
            print(f"   Has app password: {bool(credentials.application_password)}")
            print(f"   Has FTP: {credentials.has_ftp_credentials()}")
            print(f"   Has SFTP: {credentials.has_sftp_credentials()}")
            return True
        else:
            print("❌ No Skyy Rose credentials found")
            return False
            
    except Exception as e:
        print(f"❌ Credential loading failed: {e}")
        return False

async def test_wordpress_connection():
    """Test WordPress REST API connection."""
    print("\n🌐 Testing WordPress Connection")
    print("-" * 40)
    
    try:
        from config.wordpress_credentials import get_skyy_rose_credentials
        import requests
        import base64
        
        credentials = get_skyy_rose_credentials()
        if not credentials:
            print("❌ No credentials available for testing")
            return False
        
        # Test basic site connectivity
        print(f"🔍 Testing connection to: {credentials.site_url}")
        
        try:
            response = requests.get(f"{credentials.site_url}/wp-json/wp/v2", timeout=10)
            api_accessible = response.status_code == 200
            
            if api_accessible:
                print("✅ WordPress REST API accessible")
            else:
                print(f"❌ WordPress REST API not accessible (Status: {response.status_code})")
                return False
            
        except requests.RequestException as e:
            print(f"❌ Connection failed: {e}")
            return False
        
        # Test authentication
        if credentials.application_password:
            print("🔑 Testing authentication with application password...")
            
            auth_header = base64.b64encode(
                f"{credentials.username}:{credentials.application_password}".encode()
            ).decode()
            
            try:
                auth_response = requests.get(
                    f"{credentials.site_url}/wp-json/wp/v2/users/me",
                    headers={"Authorization": f"Basic {auth_header}"},
                    timeout=10
                )
                
                if auth_response.status_code == 200:
                    user_data = auth_response.json()
                    print(f"✅ Authentication successful")
                    print(f"   Logged in as: {user_data.get('name', 'Unknown')}")
                    print(f"   User roles: {user_data.get('roles', [])}")
                    return True
                else:
                    print(f"❌ Authentication failed (Status: {auth_response.status_code})")
                    print(f"   Response: {auth_response.text[:200]}")
                    return False
                    
            except requests.RequestException as e:
                print(f"❌ Authentication test failed: {e}")
                return False
        else:
            print("⚠️ No application password configured - skipping auth test")
            return True
            
    except Exception as e:
        print(f"❌ WordPress connection test failed: {e}")
        return False

async def test_theme_package_creation():
    """Test theme package creation."""
    print("\n📦 Testing Theme Package Creation")
    print("-" * 40)
    
    try:
        from agent.wordpress.automated_theme_uploader import automated_theme_uploader
        
        # Create a temporary theme directory
        with tempfile.TemporaryDirectory() as temp_dir:
            theme_dir = Path(temp_dir) / "test-theme"
            theme_dir.mkdir()
            
            # Create basic theme files
            (theme_dir / "style.css").write_text("""/*
Theme Name: Test Theme
Description: Test theme for DevSkyy
Version: 1.0.0
Author: DevSkyy Platform
*/""")
            
            (theme_dir / "index.php").write_text("""<?php
// Test theme index
get_header();
echo '<h1>Test Theme</h1>';
get_footer();
?>""")
            
            (theme_dir / "functions.php").write_text("""<?php
// Test theme functions
function test_theme_setup() {
    add_theme_support('post-thumbnails');
}
add_action('after_setup_theme', 'test_theme_setup');
?>""")
            
            print(f"📁 Created test theme at: {theme_dir}")
            
            # Test package creation
            theme_info = {
                "name": "test-theme",
                "version": "1.0.0",
                "description": "Test theme for DevSkyy integration",
                "author": "DevSkyy Platform"
            }
            
            package = await automated_theme_uploader.create_theme_package(
                str(theme_dir), theme_info
            )
            
            print(f"✅ Theme package created successfully")
            print(f"   Package name: {package.name}")
            print(f"   Package size: {package.size_bytes / 1024:.1f} KB")
            print(f"   Files count: {len(package.files)}")
            print(f"   Checksum: {package.checksum[:16]}...")
            
            # Test package validation
            validation_results = await automated_theme_uploader.validate_theme_package(package)
            
            if validation_results["valid"]:
                print("✅ Theme package validation passed")
                if validation_results["warnings"]:
                    print(f"   Warnings: {len(validation_results['warnings'])}")
            else:
                print("❌ Theme package validation failed")
                print(f"   Errors: {validation_results['errors']}")
                return False
            
            # Clean up package file
            if Path(package.package_path).exists():
                Path(package.package_path).unlink()
            
            return True
            
    except Exception as e:
        print(f"❌ Theme package creation failed: {e}")
        return False

async def test_theme_builder_orchestrator():
    """Test theme builder orchestrator."""
    print("\n🎨 Testing Theme Builder Orchestrator")
    print("-" * 40)
    
    try:
        from agent.wordpress.theme_builder_orchestrator import (
            theme_builder_orchestrator,
            ThemeType
        )
        from config.wordpress_credentials import get_skyy_rose_credentials
        
        credentials = get_skyy_rose_credentials()
        if not credentials:
            print("❌ No credentials available for testing")
            return False
        
        # Test creating a build request
        build_request = theme_builder_orchestrator.create_skyy_rose_build_request(
            theme_name="test-skyy-rose-theme",
            theme_type=ThemeType.LUXURY_FASHION,
            auto_deploy=False,  # Don't actually deploy during testing
            customizations={
                "test_mode": True,
                "colors": {
                    "primary": "#1a1a1a",
                    "secondary": "#d4af37"
                }
            }
        )
        
        if build_request:
            print("✅ Theme build request created successfully")
            print(f"   Theme name: {build_request.theme_name}")
            print(f"   Theme type: {build_request.theme_type.value}")
            print(f"   Target site: {build_request.target_site}")
            print(f"   Auto deploy: {build_request.auto_deploy}")
            
            # Test system status
            status = theme_builder_orchestrator.get_system_status()
            print(f"✅ Orchestrator system status retrieved")
            print(f"   Supported theme types: {len(status['supported_theme_types'])}")
            print(f"   Available sites: {status['available_sites']}")
            
            return True
        else:
            print("❌ Failed to create theme build request")
            return False
            
    except Exception as e:
        print(f"❌ Theme builder orchestrator test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints (if server is running)."""
    print("\n🌐 Testing API Endpoints")
    print("-" * 40)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test credentials status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/credentials/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Credentials status endpoint working")
                print(f"   Configured sites: {data.get('configured_sites', [])}")
                print(f"   Has default credentials: {data.get('has_default_credentials', False)}")
            else:
                print(f"⚠️ Credentials status endpoint returned: {response.status_code}")
        except requests.RequestException:
            print("⚠️ API server not running - skipping endpoint tests")
            return True
        
        # Test system status endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/themes/system-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ System status endpoint working")
                print(f"   Available theme types: {len(data.get('available_theme_types', []))}")
                print(f"   Upload methods: {len(data.get('supported_upload_methods', []))}")
            else:
                print(f"⚠️ System status endpoint returned: {response.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ System status endpoint failed: {e}")
        
        # Test WordPress connection endpoint
        try:
            response = requests.post(
                f"{base_url}/api/v1/themes/credentials/test",
                json={"site_key": "skyy_rose"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ WordPress connection test endpoint working")
                print(f"   Connection status: {data.get('status', 'unknown')}")
                print(f"   API accessible: {data.get('api_accessible', False)}")
                print(f"   Auth test: {data.get('authentication_test', False)}")
            else:
                print(f"⚠️ WordPress connection test returned: {response.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ WordPress connection test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint testing failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("🧪 DevSkyy WordPress Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Credential Loading", test_credential_loading),
        ("WordPress Connection", test_wordpress_connection),
        ("Theme Package Creation", test_theme_package_creation),
        ("Theme Builder Orchestrator", test_theme_builder_orchestrator),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! WordPress integration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Check configuration and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
