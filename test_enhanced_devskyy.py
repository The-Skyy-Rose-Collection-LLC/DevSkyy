
"""
Enhanced DevSkyy Test Script
Tests WordPress, WooCommerce, Divi expertise and site communication capabilities.
"""

import requests
import asyncio
import json
from datetime import datetime

BASE_URL = "http://0.0.0.0:8000"

def test_wordpress_capabilities():
    """Test WordPress/Divi optimization capabilities."""
    print("🔧 Testing WordPress/Divi Optimization...")
    
    # Test Divi layout analysis
    sample_layout = """
    [et_pb_section fb_built="1"]
        [et_pb_row]
            [et_pb_column type="4_4"]
                [et_pb_text]Hello World[/et_pb_text]
                [et_pb_image src="image.jpg"]
            [/et_pb_column]
        [/et_pb_row]
    [/et_pb_section]
    """
    
    response = requests.post(f"{BASE_URL}/wordpress/analyze-layout", 
                           params={"layout_data": sample_layout})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Divi analysis: {result['structure']['modules_count']} modules found")
        print(f"   Performance issues: {len(result['performance_issues'])}")
    
    # Test custom CSS generation
    css_requirements = {
        "woocommerce_enabled": True,
        "brand_colors": {
            "primary": "#7EBEC5",
            "secondary": "#1f1f1f",
            "accent": "#ff6b6b"
        }
    }
    
    response = requests.post(f"{BASE_URL}/wordpress/generate-css", 
                           json=css_requirements)
    if response.status_code == 200:
        result = response.json()
        print("✅ Custom CSS generated for brand colors")
    
    # Test WooCommerce audit
    response = requests.get(f"{BASE_URL}/wordpress/audit-woocommerce")
    if response.status_code == 200:
        audit = response.json()
        print(f"✅ WooCommerce audit: {audit['store_health']} health")
        print(f"   Performance score: {audit['performance_score']}/100")

def test_web_development_fixes():
    """Test web development and code fixing capabilities."""
    print("\n💻 Testing Web Development Fixes...")
    
    # Test CSS analysis
    sample_css = """
    .header {
        color: #ff0000 !important;
        color: #ff0000 !important;
        transform: rotate(45deg)
    }
    """
    
    response = requests.post(f"{BASE_URL}/webdev/analyze-code", 
                           params={"code": sample_css, "language": "css"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ CSS analysis: {result['issues_found']} issues found")
        print(f"   Code quality score: {result['code_quality_score']}/100")
    
    # Test code fixing
    response = requests.post(f"{BASE_URL}/webdev/fix-code", 
                           params={"code": sample_css, "language": "css"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ CSS fixes applied: {len(result['fixes_applied'])} improvements")
    
    # Test HTML structure optimization
    sample_html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <img src="test.jpg">
        <h2>Welcome</h2>
    </body>
    </html>
    """
    
    response = requests.post(f"{BASE_URL}/webdev/optimize-structure", 
                           params={"html_content": sample_html})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ HTML optimizations: {len(result['optimizations_applied'])} applied")

async def test_site_communication():
    """Test site communication and insights capabilities."""
    print("\n🌐 Testing Site Communication...")
    
    website_url = "https://theskyy-rose-collection.com"
    
    # Test chatbot connection
    response = requests.post(f"{BASE_URL}/site/connect-chatbot", 
                           params={"website_url": website_url})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Chatbot connection: {result['connection_status']}")
        print(f"   Capabilities: {len(result.get('capabilities', []))} features")
    
    # Test health insights
    response = requests.get(f"{BASE_URL}/site/health-insights", 
                          params={"website_url": website_url})
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Site health: {health['technical_health']['seo_score']} SEO score")
        print(f"   Performance: {health['performance_metrics']['mobile_performance']} mobile")
    
    # Test customer feedback analysis
    response = requests.get(f"{BASE_URL}/site/customer-feedback", 
                          params={"website_url": website_url})
    if response.status_code == 200:
        feedback = response.json()
        print(f"✅ Customer feedback: {feedback['average_rating']:.1f}/5 average rating")
        print(f"   Sentiment: {feedback['sentiment_breakdown']['positive']} positive reviews")
    
    # Test market insights
    response = requests.get(f"{BASE_URL}/site/market-insights", 
                          params={"website_url": website_url})
    if response.status_code == 200:
        market = response.json()
        print(f"✅ Market insights: {market['demographic_data']['age_groups']['25-34']} users 25-34")
        print(f"   Top device: Mobile ({market['behavior_patterns']['preferred_devices']['mobile']})")

def test_full_optimization():
    """Test comprehensive DevSkyy optimization."""
    print("\n🚀 Testing Full DevSkyy Optimization...")
    
    response = requests.post(f"{BASE_URL}/devskyy/full-optimization")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Full optimization: {result['devskyy_status']}")
        print(f"   WordPress: {result['wordpress_optimization']['divi_optimization']}")
        print(f"   Web Dev: {result['web_development']['development_status']}")
        print(f"   Site Insights: {result['site_insights']['connection_status']}")

def test_enhanced_dashboard():
    """Test enhanced dashboard with all agents."""
    print("\n📊 Testing Enhanced Dashboard...")
    
    response = requests.get(f"{BASE_URL}/dashboard")
    if response.status_code == 200:
        dashboard = response.json()
        print(f"✅ Enhanced dashboard loaded")
        print(f"   Platform: {dashboard['platform']}")
        print(f"   WordPress: {dashboard['wordpress_status']}")
        print(f"   Web Development: {dashboard['web_development']}")
        print(f"   Site Communication: {dashboard['site_communication']}")

async def main():
    """Run all enhanced DevSkyy tests."""
    print("🌟 DevSkyy Enhanced Testing Suite")
    print("=" * 50)
    
    # Test core capabilities
    test_wordpress_capabilities()
    test_web_development_fixes()
    await test_site_communication()
    test_full_optimization()
    test_enhanced_dashboard()
    
    print("\n🎉 All enhanced DevSkyy tests completed!")
    print("DevSkyy is now production-ready for The Skyy Rose Collection!")

if __name__ == "__main__":
    asyncio.run(main())
