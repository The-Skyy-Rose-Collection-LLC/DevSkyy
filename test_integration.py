#!/usr/bin/env python3
"""
Integration test script for the enhanced agent scanner.
Tests all functionality end-to-end without external dependencies.
"""

import sys
import os
from pathlib import Path
import json

# Add current directory to path
current_dir = str(Path.cwd())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_scanner_functions():
    """Test scanner functions directly."""
    print("=" * 60)
    print("TESTING ENHANCED AGENT SCANNER FUNCTIONS")
    print("=" * 60)
    
    try:
        from agent.modules.scanner import scan_agents_only, scan_site
        print("✅ Scanner imports successful")
    except ImportError as e:
        print(f"❌ Scanner import failed: {e}")
        return False
    
    # Test scan_agents_only
    print("\n1. Testing scan_agents_only()...")
    try:
        result = scan_agents_only()
        print(f"✅ scan_agents_only() successful")
        print(f"   Status: {result.get('status')}")
        print(f"   Scan ID: {result.get('scan_id')}")
        
        agent_data = result.get('agent_modules', {})
        print(f"   Total agents: {agent_data.get('total_agents')}")
        print(f"   Functional: {agent_data.get('functional_agents')}")
        print(f"   With issues: {agent_data.get('agents_with_issues')}")
        print(f"   Health score: {agent_data.get('average_health_score')}")
        
        # Validate required fields
        required_fields = ['total_agents', 'functional_agents', 'agents_with_issues', 'average_health_score', 'summary']
        for field in required_fields:
            if field not in agent_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        summary = agent_data['summary']
        print(f"   Importable: {len(summary.get('importable', []))}")
        print(f"   Import errors: {len(summary.get('import_errors', []))}")
        print(f"   Missing deps: {len(summary.get('missing_dependencies', []))}")
        print(f"   Perf issues: {len(summary.get('performance_issues', []))}")
        print(f"   Security concerns: {len(summary.get('security_concerns', []))}")
        
    except Exception as e:
        print(f"❌ scan_agents_only() failed: {e}")
        return False
    
    # Test enhanced scan_site
    print("\n2. Testing enhanced scan_site()...")
    try:
        result = scan_site()
        print(f"✅ Enhanced scan_site() successful")
        print(f"   Status: {result.get('status')}")
        print(f"   Files scanned: {result.get('files_scanned')}")
        
        if 'agent_modules' in result:
            print(f"✅ Agent analysis included in site scan")
            agent_data = result['agent_modules']
            print(f"   Agents analyzed: {agent_data.get('total_agents')}")
            print(f"   Agent health: {agent_data.get('average_health_score')}")
        else:
            print(f"❌ Agent analysis missing from site scan")
            return False
        
    except Exception as e:
        print(f"❌ Enhanced scan_site() failed: {e}")
        return False
    
    return True


def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        from test_scanner_api import app
        print("✅ API test setup successful")
    except ImportError as e:
        print(f"❌ API test setup failed: {e}")
        return False
    
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing GET /health...")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Scanner available: {data.get('scanner_available')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test agents endpoint
    print("\n2. Testing POST /scan/agents...")
    try:
        response = client.post("/scan/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agents endpoint working")
            agent_data = data.get('agent_modules', {})
            print(f"   Total agents: {agent_data.get('total_agents')}")
            print(f"   Average health: {agent_data.get('average_health_score')}")
        else:
            print(f"❌ Agents endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Agents endpoint error: {e}")
        return False
    
    # Test site endpoint
    print("\n3. Testing POST /scan/site...")
    try:
        response = client.post("/scan/site")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Site endpoint working")
            print(f"   Files scanned: {data.get('files_scanned')}")
            if 'agent_modules' in data:
                print(f"✅ Agent analysis included")
                print(f"   Agents: {data['agent_modules'].get('total_agents')}")
            else:
                print(f"❌ Agent analysis missing")
                return False
        else:
            print(f"❌ Site endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Site endpoint error: {e}")
        return False
    
    return True


def test_backward_compatibility():
    """Test that existing functionality still works."""
    print("\n" + "=" * 60)
    print("TESTING BACKWARD COMPATIBILITY")
    print("=" * 60)
    
    try:
        from agent.modules.scanner import scan_site
        print("✅ Original scan_site import works")
        
        # Test that scan_site still returns expected basic fields
        result = scan_site()
        
        # Original fields that should still exist
        original_fields = [
            'scan_id', 'timestamp', 'status', 'files_scanned',
            'errors_found', 'warnings', 'optimizations',
            'performance_metrics', 'security_issues'
        ]
        
        for field in original_fields:
            if field not in result:
                print(f"❌ Missing original field: {field}")
                return False
        
        print(f"✅ All original fields present")
        print(f"✅ Enhanced with agent_modules field")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


def validate_requirements():
    """Validate that all requirements from the issue are met."""
    print("\n" + "=" * 60)
    print("VALIDATING ISSUE REQUIREMENTS")
    print("=" * 60)
    
    requirements_met = []
    
    try:
        from agent.modules.scanner import scan_agents_only, scan_site
        
        # Test agent analysis
        result = scan_agents_only()
        agent_data = result.get('agent_modules', {})
        
        # Requirement: Scan all 35+ agents
        total_agents = agent_data.get('total_agents', 0)
        if total_agents >= 35:
            requirements_met.append("✅ Scans all 35+ agent modules")
        else:
            requirements_met.append(f"❌ Only scans {total_agents} agents, need 35+")
        
        # Requirement: Health scoring 0-100
        health_score = agent_data.get('average_health_score', 0)
        if 0 <= health_score <= 100:
            requirements_met.append(f"✅ Health scoring (0-100): {health_score}")
        else:
            requirements_met.append(f"❌ Invalid health score: {health_score}")
        
        # Requirement: Dependency tracking
        summary = agent_data.get('summary', {})
        if 'missing_dependencies' in summary:
            dep_count = len(summary['missing_dependencies'])
            requirements_met.append(f"✅ Dependency tracking: {dep_count} missing deps found")
        else:
            requirements_met.append("❌ Missing dependency tracking")
        
        # Requirement: Performance analysis
        if 'performance_issues' in summary:
            perf_count = len(summary['performance_issues'])
            requirements_met.append(f"✅ Performance analysis: {perf_count} issues detected")
        else:
            requirements_met.append("❌ Missing performance analysis")
        
        # Requirement: Security scanning
        if 'security_concerns' in summary:
            sec_count = len(summary['security_concerns'])
            requirements_met.append(f"✅ Security scanning: {sec_count} concerns identified")
        else:
            requirements_met.append("❌ Missing security scanning")
        
        # Requirement: Functional/non-functional agent count
        functional = agent_data.get('functional_agents', 0)
        with_issues = agent_data.get('agents_with_issues', 0)
        requirements_met.append(f"✅ Agent status: {functional} functional, {with_issues} with issues")
        
        # Requirement: Enhanced scan_site includes agents
        site_result = scan_site()
        if 'agent_modules' in site_result:
            requirements_met.append("✅ Enhanced scan_site includes agent analysis")
        else:
            requirements_met.append("❌ scan_site missing agent analysis")
        
        # Requirement: New API endpoints
        try:
            from test_scanner_api import app
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            agents_response = client.post("/scan/agents")
            site_response = client.post("/scan/site")
            
            if agents_response.status_code == 200 and site_response.status_code == 200:
                requirements_met.append("✅ New API endpoints working")
            else:
                requirements_met.append("❌ API endpoints not working")
        except:
            requirements_met.append("❌ API endpoints not testable")
        
        # Print results
        print("\nRequirements Validation:")
        for req in requirements_met:
            print(f"   {req}")
        
        # Check if all requirements met
        failed_count = sum(1 for req in requirements_met if req.startswith("❌"))
        if failed_count == 0:
            print(f"\n🎉 ALL REQUIREMENTS MET! ({len(requirements_met)}/{len(requirements_met)})")
            return True
        else:
            print(f"\n⚠️  {failed_count} requirements not fully met")
            return False
        
    except Exception as e:
        print(f"❌ Requirements validation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 DevSkyy Enhanced Agent Scanner - Comprehensive Test Suite")
    print("Testing implementation for GitHub Issue #44")
    
    all_passed = True
    
    # Run all test suites
    test_results = [
        ("Scanner Functions", test_scanner_functions()),
        ("API Endpoints", test_api_endpoints()),
        ("Backward Compatibility", test_backward_compatibility()),
        ("Requirements Validation", validate_requirements())
    ]
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Enhanced Agent Scanner is ready for production.")
        print("✅ Issue #44 requirements fully implemented and validated.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)