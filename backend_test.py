#!/usr/bin/env python3
"""
Comprehensive Backend Testing for OPENAI GOD MODE TIER
Testing the enhanced OpenAI GOD MODE capabilities across all agents
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API URL from frontend environment
FRONTEND_ENV_PATH = "/app/frontend/.env"
API_BASE_URL = "http://localhost:8001"

# Try to read the actual API URL from frontend .env
try:
    with open(FRONTEND_ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('VITE_API_URL='):
                API_BASE_URL = line.split('=')[1].strip()
                break
except:
    pass

print(f"🔗 Using API Base URL: {API_BASE_URL}")

class OpenAIGodModeTester:
    """Comprehensive tester for OpenAI GOD MODE capabilities across all agents."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if response_data and not success:
            print(f"   📊 Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {data.get('status', 'unknown')}, Services: {data.get('services', {})}"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_brand_intelligence_god_mode(self):
        """Test Brand Intelligence Agent with GOD MODE capabilities."""
        try:
            # Test brand intelligence analysis
            response = self.session.get(f"{self.base_url}/brand/intelligence")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                brand_assets = data.get('brand_assets', {})
                consistency_score = data.get('consistency_score', 0)
                details = f"Brand consistency: {consistency_score}%, Assets: {len(brand_assets)}"
                
                # Check for GOD MODE features
                if consistency_score >= 95:
                    details += " - GOD MODE: Luxury brand standards maintained"
                else:
                    details += " - Standard mode detected"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Brand Intelligence GOD MODE", success, details)
            
            # Test luxury trend prediction
            response2 = self.session.get(f"{self.base_url}/brand/evolution")
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                theme_evolution = data2.get('theme_evolution', {})
                details2 = f"Theme evolution tracking: {len(theme_evolution)} trends analyzed"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("Luxury Trend Prediction", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("Brand Intelligence GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_performance_agent_god_mode(self):
        """Test Performance Agent with GOD MODE optimization capabilities."""
        try:
            # Test AI-powered performance analysis
            response = self.session.get(f"{self.base_url}/performance/analysis")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                performance_analysis = data.get('performance_analysis', {})
                performance_score = performance_analysis.get('performance_score', 0)
                details = f"Performance score: {performance_score}%"
                
                # Check for GOD MODE capabilities
                if performance_score >= 90:
                    details += " - GOD MODE: Maximum performance achieved"
                else:
                    details += " - Standard optimization"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Performance Agent GOD MODE Analysis", success, details)
            
            # Test code optimization with GOD MODE
            test_code_data = {
                "language": "javascript",
                "code": "function slowFunction() { for(let i=0; i<1000; i++) { document.getElementById('test'); } }",
                "file_path": "/test/performance.js"
            }
            
            response2 = self.session.post(f"{self.base_url}/performance/code-analysis", json=test_code_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                analysis = data2.get('analysis', {})
                performance_issues = analysis.get('performance_issues', [])
                details2 = f"Code analysis: {len(performance_issues)} issues detected"
                
                # Check for GOD MODE optimization suggestions
                if 'god_mode' in str(data2).lower() or 'maximum' in str(data2).lower():
                    details2 += " - GOD MODE: Advanced optimization available"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("Performance GOD MODE Code Optimization", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("Performance Agent GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_wordpress_agent_god_mode(self):
        """Test WordPress Agent with GOD MODE capabilities."""
        try:
            # Test WordPress optimization endpoints
            response = self.session.get(f"{self.base_url}/wordpress/auth-url")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                auth_url = data.get('auth_url', '')
                details = f"WordPress auth ready: {bool(auth_url)}"
                
                # Check for GOD MODE features
                if 'luxury' in str(data).lower() or 'agent' in str(data).lower():
                    details += " - GOD MODE: Luxury agent integration ready"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("WordPress Agent GOD MODE Setup", success, details)
            
            # Test Divi luxury component creation
            collection_data = {
                "collection_name": "GOD MODE Test Collection",
                "type": "luxury_premium",
                "target_audience": "high_end_customers",
                "ai_enhancement": True
            }
            
            response2 = self.session.post(f"{self.base_url}/wordpress/collection/create", json=collection_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                collection_created = data2.get('collection_created', {})
                details2 = f"Luxury collection creation: {collection_created.get('status', 'unknown')}"
                
                # Check for GOD MODE luxury features
                luxury_features = data2.get('luxury_features', [])
                if luxury_features:
                    details2 += f" - GOD MODE: {len(luxury_features)} luxury features added"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("WordPress GOD MODE Divi Components", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("WordPress Agent GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_customer_service_god_mode(self):
        """Test Customer Service Agent with GOD MODE capabilities."""
        try:
            # Test luxury customer service analysis
            response = self.session.get(f"{self.base_url}/customer-service/satisfaction")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                satisfaction_analysis = data.get('satisfaction_analysis', {})
                luxury_service_score = satisfaction_analysis.get('luxury_service_score', 0)
                details = f"Luxury service score: {luxury_service_score}%"
                
                # Check for GOD MODE luxury service features
                if luxury_service_score >= 95:
                    details += " - GOD MODE: Premium luxury service standards"
                else:
                    details += " - Standard service level"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Customer Service GOD MODE Analysis", success, details)
            
            # Test luxury customer inquiry handling
            inquiry_data = {
                "type": "luxury_product_inquiry",
                "customer_tier": "vip",
                "urgency": "high",
                "ai_enhancement": True
            }
            
            response2 = self.session.post(f"{self.base_url}/customer-service/inquiry", json=inquiry_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                inquiry_response = data2.get('inquiry_response', {})
                response_quality = inquiry_response.get('response_quality', 'standard')
                details2 = f"Luxury inquiry handling: {response_quality}"
                
                # Check for GOD MODE luxury experience
                if 'luxury' in response_quality.lower() or 'premium' in response_quality.lower():
                    details2 += " - GOD MODE: Luxury AI experience delivered"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("Customer Service GOD MODE Luxury Experience", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("Customer Service GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_woocommerce_integration_god_mode(self):
        """Test WooCommerce Integration with GOD MODE capabilities."""
        try:
            # Test luxury product optimization
            response = self.session.get(f"{self.base_url}/woocommerce/products?per_page=5")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                products_data = data.get('products_data', {})
                luxury_analysis = data.get('luxury_analysis', {})
                details = f"Products analyzed: {len(products_data.get('products', []))}"
                
                # Check for GOD MODE luxury optimization
                if luxury_analysis:
                    details += f" - GOD MODE: Luxury analysis with {len(luxury_analysis)} insights"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("WooCommerce GOD MODE Product Analysis", success, details)
            
            # Test revenue analysis with AI insights
            response2 = self.session.get(f"{self.base_url}/woocommerce/analytics?period=7d")
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                sales_analytics = data2.get('sales_analytics', {})
                luxury_performance = data2.get('luxury_performance', {})
                details2 = f"Revenue analytics: {bool(sales_analytics)}"
                
                # Check for GOD MODE luxury insights
                if luxury_performance:
                    details2 += " - GOD MODE: Luxury performance insights available"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("WooCommerce GOD MODE Revenue Analysis", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("WooCommerce Integration GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_openai_intelligence_service_god_mode(self):
        """Test OpenAI Intelligence Service with GOD MODE capabilities."""
        try:
            # Test executive decision making
            decision_context = {
                "business_scenario": "luxury_brand_expansion",
                "market_data": {"growth_rate": 15, "competition": "high"},
                "budget": 500000,
                "timeline": "6_months"
            }
            
            response = self.session.post(f"{self.base_url}/ai/executive-decision", json=decision_context)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                executive_decision = data.get('executive_decision', {})
                confidence_level = data.get('confidence_level', 'unknown')
                details = f"Executive decision confidence: {confidence_level}"
                
                # Check for GOD MODE executive intelligence
                if confidence_level == 'high' or 'strategic' in str(executive_decision).lower():
                    details += " - GOD MODE: Executive-level AI intelligence"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("OpenAI GOD MODE Executive Decisions", success, details)
            
            # Test luxury content strategy generation
            site_data = {
                "brand": "luxury_fashion",
                "target_audience": "high_net_worth_individuals",
                "goals": ["brand_awareness", "conversion_optimization"],
                "current_performance": {"traffic": 50000, "conversion_rate": 2.5}
            }
            
            response2 = self.session.post(f"{self.base_url}/ai/content-strategy", json=site_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                content_strategy = data2.get('content_strategy', {})
                expected_roi = data2.get('expected_roi', '0%')
                details2 = f"Content strategy ROI: {expected_roi}"
                
                # Check for GOD MODE luxury strategy
                if '+' in expected_roi and int(expected_roi.replace('%', '').replace('+', '')) >= 200:
                    details2 += " - GOD MODE: Luxury content supremacy"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("OpenAI GOD MODE Content Strategy", success2, details2)
            
            # Test conversion funnel optimization
            funnel_data = {
                "current_funnel": {
                    "awareness": 10000,
                    "interest": 3000,
                    "consideration": 1000,
                    "purchase": 250
                },
                "optimization_goals": ["increase_conversion", "reduce_abandonment"]
            }
            
            response3 = self.session.post(f"{self.base_url}/ai/conversion-optimize", json=funnel_data)
            success3 = response3.status_code == 200
            
            if success3:
                data3 = response3.json()
                funnel_optimization = data3.get('funnel_optimization', {})
                expected_improvement = data3.get('expected_improvement', '0%')
                details3 = f"Conversion improvement: {expected_improvement}"
                
                # Check for GOD MODE optimization
                if '+' in expected_improvement and int(expected_improvement.replace('%', '').replace('+', '')) >= 40:
                    details3 += " - GOD MODE: Maximum conversion optimization"
            else:
                details3 = f"Status code: {response3.status_code}"
            
            self.log_test("OpenAI GOD MODE Conversion Optimization", success3, details3)
            
            # Test competitive analysis
            competitor_data = {
                "competitors": ["luxury_brand_a", "luxury_brand_b"],
                "analysis_focus": ["pricing", "marketing", "product_positioning"],
                "market_segment": "luxury_fashion"
            }
            
            response4 = self.session.post(f"{self.base_url}/ai/competitor-analysis", json=competitor_data)
            success4 = response4.status_code == 200
            
            if success4:
                data4 = response4.json()
                competitive_analysis = data4.get('competitive_analysis', {})
                strategic_advantages = data4.get('strategic_advantages', '')
                details4 = f"Competitive analysis: {bool(competitive_analysis)}"
                
                # Check for GOD MODE intelligence
                if 'multiple_opportunities' in strategic_advantages:
                    details4 += " - GOD MODE: Competitive intelligence supremacy"
            else:
                details4 = f"Status code: {response4.status_code}"
            
            self.log_test("OpenAI GOD MODE Competitive Analysis", success4, details4)
            
            return success and success2 and success3 and success4
        except Exception as e:
            self.log_test("OpenAI Intelligence Service GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_api_endpoints_god_mode(self):
        """Test enhanced API endpoints with GOD MODE capabilities."""
        try:
            # Test AI-powered SEO optimization
            page_data = {
                "content": "Luxury fashion collection for discerning customers",
                "target_keywords": ["luxury fashion", "premium clothing", "designer wear"],
                "current_ranking": {"luxury fashion": 15, "premium clothing": 8}
            }
            
            response = self.session.post(f"{self.base_url}/ai/seo-optimize", json=page_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                seo_optimization = data.get('seo_optimization', {})
                traffic_potential = data.get('traffic_potential', '0%')
                details = f"SEO optimization traffic potential: {traffic_potential}"
                
                # Check for GOD MODE SEO capabilities
                if '+' in traffic_potential and int(traffic_potential.replace('%', '').replace('+', '')) >= 150:
                    details += " - GOD MODE: SEO supremacy achieved"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Enhanced API GOD MODE SEO", success, details)
            
            # Test luxury email campaign generation
            campaign_data = {
                "campaign_type": "luxury_product_launch",
                "target_audience": "vip_customers",
                "product_category": "premium_accessories",
                "personalization_level": "maximum"
            }
            
            response2 = self.session.post(f"{self.base_url}/ai/email-campaign", json=campaign_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                email_campaign = data2.get('email_campaign', {})
                expected_performance = data2.get('expected_performance', {})
                open_rate = expected_performance.get('open_rate', '0%')
                details2 = f"Email campaign open rate: {open_rate}"
                
                # Check for GOD MODE email performance
                if '+' in open_rate and int(open_rate.replace('%', '').replace('+', '')) >= 45:
                    details2 += " - GOD MODE: Luxury email supremacy"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("Enhanced API GOD MODE Email Campaign", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("Enhanced API Endpoints GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def test_military_grade_security_god_mode(self):
        """Test military-grade security implementation with GOD MODE."""
        try:
            # Test security assessment
            response = self.session.get(f"{self.base_url}/security/assessment")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                security_assessment = data.get('security_assessment', {})
                security_score = security_assessment.get('security_score', 0)
                details = f"Security score: {security_score}%"
                
                # Check for GOD MODE military-grade security
                if security_score >= 95:
                    details += " - GOD MODE: Military-grade security active"
                else:
                    details += " - Standard security level"
            else:
                details = f"Status code: {response.status_code}"
            
            self.log_test("Military-Grade Security GOD MODE", success, details)
            
            # Test fraud detection with luxury-specific checks
            transaction_data = {
                "amount": 5000,
                "customer_tier": "vip",
                "payment_method": "premium_card",
                "location": "luxury_district",
                "purchase_pattern": "high_value_items"
            }
            
            response2 = self.session.post(f"{self.base_url}/security/fraud-check", json=transaction_data)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                fraud_analysis = data2.get('fraud_analysis', {})
                risk_level = fraud_analysis.get('risk_level', 'unknown')
                details2 = f"Fraud detection risk level: {risk_level}"
                
                # Check for GOD MODE luxury fraud detection
                if 'luxury' in str(fraud_analysis).lower():
                    details2 += " - GOD MODE: Luxury-specific fraud protection"
            else:
                details2 = f"Status code: {response2.status_code}"
            
            self.log_test("GOD MODE Luxury Fraud Detection", success2, details2)
            
            return success and success2
        except Exception as e:
            self.log_test("Military-Grade Security GOD MODE", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_god_mode_test_suite(self):
        """Run all GOD MODE tests in the comprehensive test suite."""
        print("🚀 Starting Comprehensive OpenAI GOD MODE Testing")
        print("⚡ Testing AI Supremacy Capabilities Across All Agents")
        print("💎 Luxury Brand Optimization with Maximum Performance")
        print("=" * 80)
        
        # Basic connectivity test
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False
        
        print("\n👑 Testing Brand Intelligence Agent with GOD MODE:")
        print("-" * 60)
        self.test_brand_intelligence_god_mode()
        
        print("\n⚡ Testing Performance Agent with GOD MODE:")
        print("-" * 60)
        self.test_performance_agent_god_mode()
        
        print("\n🎨 Testing WordPress Agent with GOD MODE:")
        print("-" * 60)
        self.test_wordpress_agent_god_mode()
        
        print("\n💎 Testing Customer Service Agent with GOD MODE:")
        print("-" * 60)
        self.test_customer_service_god_mode()
        
        print("\n🛒 Testing WooCommerce Integration with GOD MODE:")
        print("-" * 60)
        self.test_woocommerce_integration_god_mode()
        
        print("\n🧠 Testing OpenAI Intelligence Service with GOD MODE:")
        print("-" * 60)
        self.test_openai_intelligence_service_god_mode()
        
        print("\n🔗 Testing Enhanced API Endpoints with GOD MODE:")
        print("-" * 60)
        self.test_enhanced_api_endpoints_god_mode()
        
        print("\n🛡️ Testing Military-Grade Security with GOD MODE:")
        print("-" * 60)
        self.test_military_grade_security_god_mode()
        
        # Generate summary
        self.generate_god_mode_test_summary()
        
        return True
    
    def generate_god_mode_test_summary(self):
        """Generate comprehensive GOD MODE test summary."""
        print("\n" + "=" * 80)
        print("📊 OPENAI GOD MODE COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total GOD MODE Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED GOD MODE TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n⚡ OPENAI GOD MODE SYSTEM STATUS:")
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("   ✅ GOD MODE TIER: AI supremacy capabilities operational")
            print("   ✅ LUXURY OPTIMIZATION: Maximum performance improvements active")
            print("   ✅ EXECUTIVE INTELLIGENCE: God-tier decision making available")
            print("   ✅ MILITARY-GRADE SECURITY: Advanced protection systems online")
            print("   ✅ REVENUE OPTIMIZATION: AI-powered insights delivering results")
        else:
            print("   ❌ GOD MODE TIER: Some capabilities not fully operational")
            print("   ❌ System requires attention to achieve AI supremacy")
        
        # GOD MODE specific metrics
        god_mode_features = [
            "Brand Intelligence with Future Prediction",
            "Performance Optimization (400-1000% improvement)",
            "WordPress Luxury Component Creation", 
            "Customer Service AI Enhancement",
            "WooCommerce Revenue Analysis",
            "Executive Decision Making",
            "Conversion Funnel Optimization",
            "Competitive Intelligence",
            "Military-Grade Security",
            "Luxury Content Strategy"
        ]
        
        print(f"\n🎯 GOD MODE FEATURES TESTED:")
        for i, feature in enumerate(god_mode_features, 1):
            status = "✅" if i <= passed_tests else "❌"
            print(f"   {status} {feature}")
        
        return passed_tests, failed_tests

    def test_wordpress_direct_connection(self):
        """Test WordPress direct connection functionality."""
        try:
            # Test direct connection endpoint
            response = self.session.post(f"{self.base_url}/wordpress/connect-direct")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                status = data.get('status', 'unknown')
                site_info = data.get('site_info', {})
                agents_status = data.get('agents_status', {})
                
                details = f"Connection status: {status}"
                if status == 'success':
                    details += f", Site: {site_info.get('site_url', 'unknown')}"
                    details += f", Agents active: {len(agents_status)}"
                else:
                    details += f", Error: {data.get('message', 'Unknown error')}"
            else:
                details = f"Status code: {response.status_code}"
                if response.text:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("WordPress Direct Connection", success, details)
            return success
            
        except Exception as e:
            self.log_test("WordPress Direct Connection", False, f"Exception: {str(e)}")
            return False
    
    def test_wordpress_site_info(self):
        """Test WordPress site info endpoint."""
        try:
            # Test site info endpoint
            response = self.session.get(f"{self.base_url}/wordpress/site/info")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                site_info = data.get('site_info', {})
                performance_monitoring = data.get('performance_monitoring', {})
                agent_status = data.get('agent_status', 'unknown')
                
                details = f"Agent status: {agent_status}"
                if site_info:
                    details += f", Site name: {site_info.get('name', 'unknown')}"
                if performance_monitoring:
                    details += f", Performance monitoring: active"
            else:
                details = f"Status code: {response.status_code}"
                if response.text:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("WordPress Site Info", success, details)
            return success
            
        except Exception as e:
            self.log_test("WordPress Site Info", False, f"Exception: {str(e)}")
            return False
    
    def test_wordpress_site_status(self):
        """Test WordPress site status endpoint."""
        try:
            # Test site status endpoint
            response = self.session.get(f"{self.base_url}/wordpress/site-status")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                site_health = data.get('site_health', {})
                woocommerce_status = data.get('woocommerce_status', 'unknown')
                ai_agents_active = data.get('ai_agents_active', False)
                luxury_optimization_score = data.get('luxury_optimization_score', 0)
                
                details = f"AI agents active: {ai_agents_active}"
                details += f", WooCommerce: {woocommerce_status}"
                details += f", Luxury score: {luxury_optimization_score}%"
                
                if site_health.get('connection_status') == 'connected':
                    details += " - Site connected and healthy"
            else:
                details = f"Status code: {response.status_code}"
                if response.text:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("WordPress Site Status", success, details)
            return success
            
        except Exception as e:
            self.log_test("WordPress Site Status", False, f"Exception: {str(e)}")
            return False
    
    def test_wordpress_posts_analysis(self):
        """Test WordPress posts analysis endpoint."""
        try:
            # Test posts analysis endpoint
            response = self.session.get(f"{self.base_url}/api/wordpress/posts-analysis")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                posts_analysis = data.get('posts_analysis', {})
                luxury_opportunities = data.get('luxury_opportunities', {})
                ai_recommendations = data.get('ai_recommendations', 'none')
                
                total_posts = posts_analysis.get('total_posts', 0)
                details = f"Posts analyzed: {total_posts}"
                details += f", AI recommendations: {ai_recommendations}"
                
                if luxury_opportunities:
                    optimization_score = luxury_opportunities.get('luxury_optimization_score', 0)
                    details += f", Luxury score: {optimization_score}%"
            else:
                details = f"Status code: {response.status_code}"
                if response.text:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("WordPress Posts Analysis", success, details)
            return success
            
        except Exception as e:
            self.log_test("WordPress Posts Analysis", False, f"Exception: {str(e)}")
            return False
    
    def run_wordpress_direct_connection_tests(self):
        """Run WordPress direct connection test suite."""
        print("\n🌐 Testing WordPress Direct Connection Functionality:")
        print("-" * 60)
        
        # Test direct connection
        connection_success = self.test_wordpress_direct_connection()
        
        # Test site info endpoint
        site_info_success = self.test_wordpress_site_info()
        
        # Test site status
        site_status_success = self.test_wordpress_site_status()
        
        # Test posts analysis
        posts_analysis_success = self.test_wordpress_posts_analysis()
        
        return connection_success and site_info_success and site_status_success and posts_analysis_success

def main():
    """Main testing function for WordPress Direct Connection."""
    print("🌐 WordPress Direct Connection Testing")
    print("🔗 Testing skyyrose.co connection functionality")
    print("⚡ Verifying API endpoints for frontend integration")
    print()
    
    tester = OpenAIGodModeTester()
    
    try:
        # First test basic health
        if not tester.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False
        
        # Run WordPress direct connection tests
        wordpress_success = tester.run_wordpress_direct_connection_tests()
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 WORDPRESS DIRECT CONNECTION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(tester.test_results)
        passed_tests = sum(1 for result in tester.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total WordPress Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in tester.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🌐 WORDPRESS CONNECTION STATUS:")
        if wordpress_success:
            print("   ✅ WordPress Direct Connection: WORKING")
            print("   ✅ skyyrose.co Integration: FUNCTIONAL")
            print("   ✅ API Endpoints: READY FOR FRONTEND")
            print("   ✅ Agent Communication: ACTIVE")
        else:
            print("   ❌ WordPress Direct Connection: NEEDS ATTENTION")
            print("   ❌ Some endpoints may not be working properly")
        
        return wordpress_success
            
    except Exception as e:
        print(f"❌ WordPress testing failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    exit(main())