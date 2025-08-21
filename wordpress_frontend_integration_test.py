#!/usr/bin/env python3
"""
WordPress Frontend Integration Test
Tests the exact API endpoints that the frontend will use for WordPress connection
"""

import requests
import json
from datetime import datetime

# Use the same URL that frontend uses
FRONTEND_API_URL = "http://localhost:8001"


def test_frontend_wordpress_integration():
    """Test WordPress integration from frontend perspective."""
    print("🌐 Testing WordPress Frontend Integration")
    print("=" * 60)

    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })

    test_results = []

    # Test 1: WordPress Direct Connection (POST /wordpress/connect-direct)
    print("\n1. Testing WordPress Direct Connection...")
    try:
        response = session.post(f"{FRONTEND_API_URL}/wordpress/connect-direct")
        success = response.status_code == 200

        if success:
            data = response.json()
            status = data.get('status', 'unknown')
            site_url = data.get('site_info', {}).get('site_url', 'unknown')
            agents_count = len(data.get('agents_status', {}))

            print(f"   ✅ SUCCESS: Status={status}, Site={site_url}, Agents={agents_count}")
            test_results.append(("WordPress Direct Connection", True,
                                f"Connected to {site_url} with {agents_count} agents"))
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            test_results.append(("WordPress Direct Connection", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results.append(("WordPress Direct Connection", False, str(e)))

    # Test 2: WordPress Site Info (GET /wordpress/site/info)
    print("\n2. Testing WordPress Site Info...")
    try:
        response = session.get(f"{FRONTEND_API_URL}/wordpress/site/info")
        success = response.status_code == 200

        if success:
            data = response.json()
            agent_status = data.get('agent_status', 'unknown')
            site_info = data.get('site_info', {})

            print(f"   ✅ SUCCESS: Agent status={agent_status}, Site info available={bool(site_info)}")
            test_results.append(("WordPress Site Info", True, f"Agent status: {agent_status}"))
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            test_results.append(("WordPress Site Info", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results.append(("WordPress Site Info", False, str(e)))

    # Test 3: WordPress Site Status (GET /wordpress/site-status)
    print("\n3. Testing WordPress Site Status...")
    try:
        response = session.get(f"{FRONTEND_API_URL}/wordpress/site-status")
        success = response.status_code == 200

        if success:
            data = response.json()
            ai_agents_active = data.get('ai_agents_active', False)
            luxury_score = data.get('luxury_optimization_score', 0)
            woocommerce_status = data.get('woocommerce_status', 'unknown')

            print(
                f"   ✅ SUCCESS: AI agents={ai_agents_active}, Luxury score={luxury_score}%, WooCommerce={woocommerce_status}")
            test_results.append(("WordPress Site Status", True, f"Luxury score: {luxury_score}%"))
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            test_results.append(("WordPress Site Status", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results.append(("WordPress Site Status", False, str(e)))

    # Test 4: WordPress Collection Creation (POST /wordpress/collection/create)
    print("\n4. Testing WordPress Collection Creation...")
    try:
        collection_data = {
            "title": "Test Luxury Collection",
            "collection_type": "luxury_test",
            "description": "Test collection for frontend integration",
            "featured_image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800"
        }

        response = session.post(f"{FRONTEND_API_URL}/wordpress/collection/create", json=collection_data)
        success = response.status_code == 200

        if success:
            data = response.json()
            collection_created = data.get('collection_created', {})
            page_url = data.get('page_url', 'unknown')
            luxury_features = data.get('luxury_features', [])

            print(f"   ✅ SUCCESS: Collection created, URL={page_url}, Features={len(luxury_features)}")
            test_results.append(("WordPress Collection Creation", True, f"Created at {page_url}"))
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            test_results.append(("WordPress Collection Creation", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results.append(("WordPress Collection Creation", False, str(e)))

    # Test 5: WooCommerce Products (GET /woocommerce/products)
    print("\n5. Testing WooCommerce Products Integration...")
    try:
        response = session.get(f"{FRONTEND_API_URL}/woocommerce/products?per_page=5")
        success = response.status_code == 200

        if success:
            data = response.json()
            products_data = data.get('products_data', {})
            luxury_analysis = data.get('luxury_analysis', {})

            print(f"   ✅ SUCCESS: Products data available, Luxury analysis={bool(luxury_analysis)}")
            test_results.append(("WooCommerce Products", True, "Products endpoint working"))
        else:
            print(f"   ❌ FAILED: Status code {response.status_code}")
            test_results.append(("WooCommerce Products", False, f"HTTP {response.status_code}"))

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        test_results.append(("WooCommerce Products", False, str(e)))

    # Generate Summary
    print("\n" + "=" * 60)
    print("📊 FRONTEND INTEGRATION TEST SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(1 for _, success, _ in test_results if success)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for test_name, success, details in test_results:
            if not success:
                print(f"   • {test_name}: {details}")

    print(f"\n🌐 FRONTEND INTEGRATION STATUS:")
    if passed_tests == total_tests:
        print("   ✅ All WordPress endpoints ready for frontend")
        print("   ✅ skyyrose.co connection fully functional")
        print("   ✅ Direct connection method working perfectly")
        print("   ✅ Frontend can safely use all API endpoints")
        return True
    else:
        print("   ❌ Some endpoints need attention")
        print("   ❌ Frontend integration may have issues")
        return False


if __name__ == "__main__":
    success = test_frontend_wordpress_integration()
    exit(0 if success else 1)
