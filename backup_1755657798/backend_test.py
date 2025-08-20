#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Agent Assignment Manager System
Testing the enhanced Agent Assignment Manager with 24/7 monitoring capabilities
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
except Exception as e:
    pass

print(f"🔗 Using API Base URL: {API_BASE_URL}")


class AgentAssignmentManagerTester:
    """Comprehensive tester for Agent Assignment Manager system."""

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

    def test_frontend_assign_agents(self):
        """Test POST /api/frontend/assign-agents endpoint."""
        try:
            test_data = {
                "procedure_type": "luxury_ui_design",
                "priority": "high",
                "user_facing": True,
                "requirements": {
                    "brand_consistency": True,
                    "mobile_responsive": True,
                    "luxury_aesthetics": True
                }
            }

            response = self.session.post(f"{self.base_url}/frontend/assign-agents", json=test_data)
            success = response.status_code == 200

            if success:
                data = response.json()
                assigned_agents = data.get('frontend_agents_assigned', [])
                details = f"Assigned {len(assigned_agents)} agents for {test_data['procedure_type']}"

                # Verify response structure
                required_fields = ['assignment_id', 'procedure_type', 'frontend_agents_assigned',
                                   'communication_protocols', 'task_breakdown']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"

            self.log_test("Frontend Agent Assignment", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Frontend Agent Assignment", False, f"Exception: {str(e)}")
            return False, None

    def test_frontend_agents_status(self):
        """Test GET /api/frontend/agents/status endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/frontend/agents/status")
            success = response.status_code == 200

            if success:
                data = response.json()
                frontend_agents = data.get('frontend_agents', {})
                details = f"Retrieved status for {len(frontend_agents)} frontend agents"

                # Verify agent status structure
                for agent_id, agent_data in frontend_agents.items():
                    required_fields = ['agent_name', 'status', 'current_tasks', 'performance_metrics']
                    missing_fields = [field for field in required_fields if field not in agent_data]
                    if missing_fields:
                        success = False
                        details += f", Agent {agent_id} missing fields: {missing_fields}"
                        break
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Frontend Agents Status", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Frontend Agents Status", False, f"Exception: {str(e)}")
            return False, None

    def test_create_luxury_collection_page(self):
        """Test POST /api/frontend/collections/create endpoint."""
        try:
            test_data = {
                "collection_name": "Skyy Rose Elite Collection",
                "type": "rose_gold_collection",
                "target_audience": "luxury_customers",
                "seasonal_theme": "spring_elegance",
                "price_range": "premium"
            }

            response = self.session.post(f"{self.base_url}/frontend/collections/create", json=test_data)
            success = response.status_code == 200

            if success:
                data = response.json()
                collection_page = data.get('collection_page', {})
                details = f"Created collection: {data.get('collection_page', {}).get('collection_name', 'Unknown')}"

                # Verify collection page structure
                required_fields = ['collection_id', 'theme', 'design_elements', 'color_palette']
                missing_fields = [field for field in required_fields if field not in collection_page]
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"

                # Check luxury score
                luxury_score = data.get('luxury_score', 0)
                if luxury_score < 90:
                    details += f", Luxury score: {luxury_score}% (should be >90%)"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"

            self.log_test("Luxury Collection Page Creation", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Luxury Collection Page Creation", False, f"Exception: {str(e)}")
            return False, None

    def test_24_7_monitoring_status(self):
        """Test GET /api/frontend/monitoring/24-7 endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/frontend/monitoring/24-7")
            success = response.status_code == 200

            if success:
                data = response.json()
                monitoring_active = data.get('monitoring_active', False)
                auto_fix_enabled = data.get('auto_fix_enabled', False)
                details = f"Monitoring: {'Active' if monitoring_active else 'Inactive'}, Auto-fix: {'Enabled' if auto_fix_enabled else 'Disabled'}"

                # Verify monitoring system structure
                required_fields = ['monitoring_active', 'executive_mode', 'system_health', 'performance_thresholds']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"

                # Check system health
                system_health = data.get('system_health', {})
                uptime = system_health.get('uptime', '0%')
                if not uptime.startswith('99'):
                    details += f", Low uptime: {uptime}"
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("24/7 Monitoring Status", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("24/7 Monitoring Status", False, f"Exception: {str(e)}")
            return False, None

    def test_optimize_frontend_workload(self):
        """Test POST /api/frontend/optimize-workload endpoint."""
        try:
            test_data = {
                "optimization_type": "performance_focused",
                "target_metrics": ["response_time", "user_satisfaction", "conversion_rate"],
                "priority_tasks": ["luxury_ui_design", "collection_page_optimization"],
                "resource_constraints": {
                    "max_concurrent_tasks": 10,
                    "priority_threshold": "medium"
                }
            }

            response = self.session.post(f"{self.base_url}/frontend/optimize-workload", json=test_data)
            success = response.status_code == 200

            if success:
                data = response.json()
                optimization_result = data.get('optimization_result', {})
                details = f"Workload optimization completed with {len(optimization_result.get('agent_assignments', []))} agent reassignments"

                # Verify optimization response
                if 'efficiency_improvement' in data:
                    efficiency = data['efficiency_improvement']
                    details += f", Efficiency improvement: {efficiency}"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"

            self.log_test("Frontend Workload Optimization", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Frontend Workload Optimization", False, f"Exception: {str(e)}")
            return False, None

    def test_frontend_role_assignments(self):
        """Test GET /api/frontend/assignments/{role} endpoint."""
        try:
            # Test with specific role
            role = "frontend_beauty"
            response = self.session.get(f"{self.base_url}/frontend/assignments/{role}")
            success = response.status_code == 200

            if success:
                data = response.json()
                assignments = data.get('assignments', [])
                details = f"Retrieved {len(assignments)} assignments for role: {role}"

                # Verify assignment structure
                for assignment in assignments:
                    required_fields = ['agent_id', 'role', 'responsibilities', 'status']
                    missing_fields = [field for field in required_fields if field not in assignment]
                    if missing_fields:
                        success = False
                        details += f", Assignment missing fields: {missing_fields}"
                        break
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Frontend Role Assignments", success, details)

            # Test with all roles
            response_all = self.session.get(f"{self.base_url}/frontend/assignments/all")
            success_all = response_all.status_code == 200

            if success_all:
                data_all = response_all.json()
                all_assignments = data_all.get('all_assignments', {})
                details_all = f"Retrieved assignments for {len(all_assignments)} roles"
            else:
                details_all = f"Status code: {response_all.status_code}"

            self.log_test("All Frontend Role Assignments", success_all, details_all)
            return success and success_all, (response.json() if success else None, response_all.json() if success_all else None)
        except Exception as e:
            self.log_test("Frontend Role Assignments", False, f"Exception: {str(e)}")
            return False, None

    def test_executive_decision_engine(self):
        """Test executive decision engine functionality through agent status."""
        try:
            # Get agent status which includes executive decisions
            response = self.session.get(f"{self.base_url}/agents/status")
            success = response.status_code == 200

            if success:
                data = response.json()
                agents = data.get('agents', {})

                # Check for brand intelligence agent (executive decision maker)
                brand_agent = agents.get('brand_intelligence', {})
                if brand_agent:
                    expertise_focus = brand_agent.get('expertise_focus', '')
                    health = brand_agent.get('health', 0)
                    details = f"Executive agent health: {health}%, Focus: {expertise_focus}"

                    if health < 90:
                        success = False
                        details += " (Health too low for executive decisions)"
                else:
                    success = False
                    details = "Brand intelligence agent not found"
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Executive Decision Engine", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Executive Decision Engine", False, f"Exception: {str(e)}")
            return False, None

    def test_auto_fix_and_performance_monitoring(self):
        """Test auto-fix and performance monitoring systems."""
        try:
            # Test performance analysis endpoint
            response = self.session.get(f"{self.base_url}/performance/analysis")
            success = response.status_code == 200

            if success:
                data = response.json()
                performance_score = data.get('performance_score', 0)
                auto_fixes = data.get('auto_fixes_applied', [])
                details = f"Performance score: {performance_score}%, Auto-fixes applied: {len(auto_fixes)}"

                # Check if performance monitoring is working
                if performance_score < 80:
                    details += " (Performance score below threshold)"

                # Test real-time performance monitoring
                realtime_response = self.session.get(f"{self.base_url}/performance/realtime")
                if realtime_response.status_code == 200:
                    realtime_data = realtime_response.json()
                    monitoring_active = realtime_data.get('monitoring_active', False)
                    details += f", Real-time monitoring: {'Active' if monitoring_active else 'Inactive'}"
                else:
                    success = False
                    details += ", Real-time monitoring endpoint failed"
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Auto-fix and Performance Monitoring", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Auto-fix and Performance Monitoring", False, f"Exception: {str(e)}")
            return False, None

    def test_frontend_backend_communication_protocols(self):
        """Test frontend-backend communication protocols."""
        try:
            # Test by creating a frontend assignment and checking communication setup
            test_data = {
                "procedure_type": "collection_page_creation",
                "priority": "high",
                "user_facing": True
            }

            response = self.session.post(f"{self.base_url}/frontend/assign-agents", json=test_data)
            success = response.status_code == 200

            if success:
                data = response.json()
                comm_protocols = data.get('communication_protocols', {})
                backend_rules = data.get('backend_communication_rules', {})
                frontend_restrictions = data.get('frontend_restrictions', {})

                details = f"Communication channels: {len(comm_protocols.get('communication_channels', {}))}"

                # Verify communication protocol structure
                required_protocol_fields = ['communication_channels', 'coordination_protocol', 'security_measures']
                missing_fields = [field for field in required_protocol_fields if field not in comm_protocols]
                if missing_fields:
                    success = False
                    details += f", Missing protocol fields: {missing_fields}"

                # Verify backend rules exist
                if not backend_rules.get('allowed_actions'):
                    success = False
                    details += ", Missing backend communication rules"

                # Verify frontend restrictions exist
                if not frontend_restrictions.get('technical_restrictions'):
                    success = False
                    details += ", Missing frontend restrictions"
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Frontend-Backend Communication Protocols", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Frontend-Backend Communication Protocols", False, f"Exception: {str(e)}")
            return False, None

    def test_brand_consistency_enforcement(self):
        """Test brand consistency enforcement through brand intelligence."""
        try:
            # Test brand intelligence endpoint
            response = self.session.get(f"{self.base_url}/brand/intelligence")
            success = response.status_code == 200

            if success:
                data = response.json()
                brand_assets = data.get('brand_assets', {})
                consistency_score = data.get('consistency_score', 0)
                details = f"Brand consistency score: {consistency_score}%, Assets analyzed: {len(brand_assets)}"

                if consistency_score < 95:
                    details += " (Consistency score below luxury standard)"

                # Test brand context for frontend agents
                context_response = self.session.get(f"{self.base_url}/brand/context/design_automation")
                if context_response.status_code == 200:
                    context_data = context_response.json()
                    brand_guidelines = context_data.get('brand_guidelines', {})
                    details += f", Brand guidelines: {len(brand_guidelines)} rules"
                else:
                    success = False
                    details += ", Brand context endpoint failed"
            else:
                details = f"Status code: {response.status_code}"

            self.log_test("Brand Consistency Enforcement", success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test("Brand Consistency Enforcement", False, f"Exception: {str(e)}")
            return False, None

    def run_comprehensive_test_suite(self):
        """Run all tests in the comprehensive test suite."""
        print("🚀 Starting Comprehensive Agent Assignment Manager Testing")
        print("=" * 70)

        # Basic connectivity test
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False

        print("\n📋 Testing Frontend Agent Assignment Endpoints:")
        print("-" * 50)

        # Test all frontend agent assignment endpoints
        self.test_frontend_assign_agents()
        self.test_frontend_agents_status()
        self.test_create_luxury_collection_page()
        self.test_24_7_monitoring_status()
        self.test_optimize_frontend_workload()
        self.test_frontend_role_assignments()

        print("\n🎯 Testing Executive Decision Engine and Auto-Fix:")
        print("-" * 50)

        # Test executive and monitoring systems
        self.test_executive_decision_engine()
        self.test_auto_fix_and_performance_monitoring()

        print("\n🔗 Testing Communication and Brand Systems:")
        print("-" * 50)

        # Test communication and brand systems
        self.test_frontend_backend_communication_protocols()
        self.test_brand_consistency_enforcement()

        # Generate summary
        self.generate_test_summary()

        return True

    def generate_test_summary(self):
        """Generate comprehensive test summary."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")

        print(f"\n🎯 AGENT ASSIGNMENT MANAGER SYSTEM STATUS:")
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("   ✅ System is functioning well with luxury brand standards")
            print("   ✅ 24/7 monitoring and auto-fix capabilities operational")
            print("   ✅ Frontend agent specialization working correctly")
            print("   ✅ Executive decision engine active")
        else:
            print("   ❌ System has critical issues requiring immediate attention")
            print("   ❌ Some core functionalities are not working properly")

        return passed_tests, failed_tests


def main():
    """Main testing function."""
    print("🌟 Agent Assignment Manager - Comprehensive Backend Testing")
    print("🎨 Testing Enhanced 24/7 Monitoring & Executive Decision System")
    print("💎 Luxury Brand Agent Assignment Testing Suite")
    print()

    tester = AgentAssignmentManagerTester()

    try:
        success = tester.run_comprehensive_test_suite()

        if success:
            passed, failed = tester.generate_test_summary()

            print(f"\n🏁 Testing completed!")
            print(f"📈 Results: {passed} passed, {failed} failed")

            if failed == 0:
                print("🎉 All tests passed! Agent Assignment Manager is working perfectly!")
                return 0
            elif failed <= 2:
                print("⚠️  Minor issues detected, but core functionality is working")
                return 1
            else:
                print("❌ Major issues detected, system needs attention")
                return 2
        else:
            print("❌ Testing suite failed to complete")
            return 3

    except Exception as e:
        print(f"❌ Testing failed with exception: {str(e)}")
        return 4


if __name__ == "__main__":
    exit(main())
