import asyncio
from datetime import datetime
import logging

from api_integration.auth_manager import AuthenticationType, auth_manager
from api_integration.core_engine import api_gateway
from api_integration.discovery_engine import APICategory, api_discovery_engine
from api_integration.fashion_apis import fashion_api_integrator
from api_integration.workflow_engine import (
    ActionType,
    TriggerType,
    Workflow,
    WorkflowStep,
    WorkflowTrigger,
    workflow_engine,
)
from fashion.intelligence_engine import (
    FashionCategory,
    FashionSeason,
    fashion_intelligence,
)


"""
API Integration Examples & Templates
Comprehensive examples for fashion e-commerce API integrations
with real-world use cases and implementation patterns
"""

logger = logging.getLogger(__name__)


class FashionAPIExamples:
    """Comprehensive examples for fashion API integrations"""

    def __init__(self):
        self.examples_run = []
        logger.info("Fashion API Examples initialized")

    async def example_1_api_discovery_and_setup(self):
        """Example 1: Discover and setup fashion APIs"""

        logger.info("\n🔍 EXAMPLE 1: API Discovery and Setup")
        logger.info("=" * 50)

        # Step 1: Discover fashion-relevant APIs
        logger.info("Step 1: Discovering fashion APIs...")
        discovered_apis = await api_discovery_engine.discover_apis(
            [
                APICategory.FASHION_TRENDS,
                APICategory.PRODUCT_CATALOG,
                APICategory.CUSTOMER_ANALYTICS,
            ]
        )

        logger.info(f"✅ Discovered {sum(len(apis) for apis in discovered_apis.values())} APIs")

        # Step 2: Get recommendations for fashion trends
        logger.info("\nStep 2: Getting API recommendations...")
        trend_apis = await api_discovery_engine.get_recommended_apis(
            category=APICategory.FASHION_TRENDS, min_score=0.7
        )

        for api in trend_apis[:3]:  # Show top 3
            logger.info(f"  📊 {api.name} (Score: {api.overall_score:.2f})")
            logger.info(f"     Provider: {api.provider}")
            logger.info(f"     Fashion Relevance: {api.fashion_relevance:.2f}")

        # Step 3: Setup authentication for top API
        if trend_apis:
            top_api = trend_apis[0]
            logger.info(f"\nStep 3: Setting up authentication for {top_api.name}...")

            # Store credentials (example with API key)
            success = await auth_manager.store_credentials(
                api_id=top_api.api_id,
                auth_type=AuthenticationType.API_KEY,
                credentials={
                    "api_key": "your_api_key_here",
                    "header_name": "X-API-Key",
                },
            )

            if success:
                logger.info("✅ Authentication configured successfully")
            else:
                logger.info("❌ Authentication setup failed")

        self.examples_run.append("api_discovery_and_setup")
        return discovered_apis

    async def example_2_fashion_trend_analysis(self):
        """Example 2: Automated fashion trend analysis"""

        logger.info("\n👗 EXAMPLE 2: Fashion Trend Analysis")
        logger.info("=" * 50)

        # Step 1: Analyze fashion context from text
        logger.info("Step 1: Analyzing fashion context...")

        fashion_text = """
        Spring 2024 fashion trends are embracing sustainable materials and vibrant colors.
        Organic cotton dresses in coral pink and mint green are dominating runways.
        Consumers are increasingly focused on eco-friendly fashion choices.
        """

        context_analysis = await fashion_intelligence.analyze_fashion_context(fashion_text)

        logger.info(f"  Fashion Relevance Score: {context_analysis['fashion_relevance_score']:.2f}")
        logger.info(f"  Identified Categories: {context_analysis['identified_categories']}")
        logger.info(f"  Sustainability Mentions: {context_analysis['sustainability_mentions']}")
        logger.info(f"  Seasonal Context: {context_analysis['seasonal_context']}")

        # Step 2: Get trend recommendations
        logger.info("\nStep 2: Getting trend recommendations...")

        recommendations = await fashion_intelligence.get_trend_recommendations(
            category=FashionCategory.WOMENS_WEAR,
            season=FashionSeason.SPRING_SUMMER,
            sustainability_focus=True,
        )

        logger.info(f"✅ Generated {len(recommendations)} trend recommendations")

        for rec in recommendations[:2]:  # Show top 2
            logger.info(f"  🌟 {rec['trend_name']}")
            logger.info(f"     Popularity: {rec['popularity_score']:.2f}")
            logger.info(f"     Key Colors: {', '.join(rec['key_elements']['colors'])}")
            logger.info(f"     Materials: {', '.join(rec['key_elements']['materials'])}")

        # Step 3: Sync trends from social media
        logger.info("\nStep 3: Syncing trends from social media...")

        sync_result = await fashion_api_integrator.sync_fashion_trends(
            sources=["pinterest", "instagram"],
            categories=[FashionCategory.WOMENS_WEAR, FashionCategory.ACCESSORIES],
        )

        logger.info(f"✅ Synced {sync_result['trends_synced']} trends from {len(sync_result['sources'])} sources")

        self.examples_run.append("fashion_trend_analysis")
        return context_analysis, recommendations

    async def example_3_automated_workflow_creation(self):
        """Example 3: Create and execute automated workflows"""

        logger.info("\n🔄 EXAMPLE 3: Automated Workflow Creation")
        logger.info("=" * 50)

        # Step 1: Create a fashion inventory sync workflow
        logger.info("Step 1: Creating inventory sync workflow...")

        inventory_trigger = WorkflowTrigger(
            trigger_id="inventory_sync_demo",
            trigger_type=TriggerType.SCHEDULED,
            name="Demo Inventory Sync",
            description="Sync inventory across fashion platforms",
            config={"schedule": "0 */2 * * *", "timezone": "UTC"},  # Every 2 hours
        )

        inventory_steps = [
            WorkflowStep(
                step_id="fetch_shopify_products",
                name="Fetch Shopify Products",
                action_type=ActionType.API_CALL,
                config={
                    "api_id": "shopify_api",
                    "endpoint": "/products.json",
                    "method": "GET",
                    "params": {"limit": 50, "status": "active"},
                },
            ),
            WorkflowStep(
                step_id="analyze_fashion_products",
                name="Analyze Fashion Context",
                action_type=ActionType.FASHION_ANALYSIS,
                config={
                    "analysis_type": "context",
                    "text": "${fetch_shopify_products_result.data}",
                },
                depends_on=["fetch_shopify_products"],
            ),
            WorkflowStep(
                step_id="update_product_cache",
                name="Update Product Cache",
                action_type=ActionType.CACHE_OPERATION,
                config={
                    "operation": "set",
                    "cache_key": "fashion_products_inventory",
                    "ttl": 7200,  # 2 hours
                    "data": "${analyze_fashion_products_result}",
                },
                depends_on=["analyze_fashion_products"],
            ),
            WorkflowStep(
                step_id="notify_inventory_update",
                name="Notify Inventory Update",
                action_type=ActionType.NOTIFICATION,
                config={
                    "template_name": "inventory_update_notification",
                    "webhook_url": "https://hooks.slack.com/your-webhook-url",
                    "priority": "normal",
                },
                depends_on=["update_product_cache"],
            ),
        ]

        inventory_workflow = Workflow(
            workflow_id="demo_inventory_sync",
            name="Demo Fashion Inventory Sync",
            description="Automated inventory synchronization with fashion analysis",
            trigger=inventory_trigger,
            steps=inventory_steps,
            fashion_context=True,
            variables={
                "sync_timestamp": datetime.now().isoformat(),
                "fashion_categories": ["womens_wear", "accessories"],
                "sustainability_check": True,
            },
        )

        # Register the workflow
        success = await workflow_engine.register_workflow(inventory_workflow)

        if success:
            logger.info("✅ Inventory sync workflow registered successfully")

            # Step 2: Trigger the workflow manually for demo
            logger.info("\nStep 2: Triggering workflow execution...")

            execution_id = await workflow_engine.trigger_workflow(
                workflow_id="demo_inventory_sync",
                trigger_data={"demo_mode": True, "source": "api_example"},
            )

            logger.info(f"✅ Workflow triggered with execution ID: {execution_id}")

            # Step 3: Monitor workflow status
            logger.info("\nStep 3: Monitoring workflow status...")

            # Wait a bit for workflow to start
            await asyncio.sleep(2)  # TODO: Move to config

            status = await workflow_engine.get_workflow_status(execution_id)
            logger.info(f"  Workflow Status: {status.get('status', 'unknown')}")

        else:
            logger.info("❌ Failed to register workflow")

        self.examples_run.append("automated_workflow_creation")
        return inventory_workflow

    async def example_4_api_gateway_usage(self):
        """Example 4: Using the API Gateway for external calls"""

        logger.info("\n⚡ EXAMPLE 4: API Gateway Usage")
        logger.info("=" * 50)

        # Step 1: Make a simple API call through the gateway
        logger.info("Step 1: Making API call through gateway...")

        # Example: Fetch fashion trends from a mock API
        result = await api_gateway.make_request(
            api_id="fashion_trends_api",
            endpoint="/trends/current",
            method="GET",
            params={"category": "womens_wear", "season": "spring_summer", "limit": 10},
            use_cache=True,
            transform_response=True,
        )

        logger.info(f"  Success: {result['success']}")
        logger.info(f"  Execution Time: {result['execution_time']:.3f}s")

        if result["success"]:
            logger.info(f"  Data Type: {type(result['data'])}")
            logger.info("✅ API call completed successfully")
        else:
            logger.info(f"  Error: {result['error']}")
            logger.info("❌ API call failed")

        # Step 2: Demonstrate caching
        logger.info("\nStep 2: Testing cache performance...")

        # Make the same call again to test caching
        start_time = datetime.now()
        await api_gateway.make_request(
            api_id="fashion_trends_api",
            endpoint="/trends/current",
            method="GET",
            params={"category": "womens_wear", "season": "spring_summer", "limit": 10},
            use_cache=True,
        )
        end_time = datetime.now()

        cache_time = (end_time - start_time).total_seconds()
        logger.info(f"  Cached Response Time: {cache_time:.3f}s")
        logger.info("✅ Cache performance demonstrated")

        # Step 3: Get API Gateway metrics
        logger.info("\nStep 3: Checking API Gateway metrics...")

        metrics = await api_gateway.get_metrics()

        logger.info(f"  Total Requests: {metrics['gateway_metrics']['total_requests']}")
        logger.info(
            f"  Success Rate: {metrics['gateway_metrics']['successful_requests'] / max(metrics['gateway_metrics']['total_requests'], 1) * 100:.1f}%"
        )
        logger.info(f"  Average Response Time: {metrics['gateway_metrics']['average_response_time']:.3f}s")

        self.examples_run.append("api_gateway_usage")
        return result

    async def example_5_fashion_personalization(self):
        """Example 5: Fashion personalization and recommendations"""

        logger.info("\n🎯 EXAMPLE 5: Fashion Personalization")
        logger.info("=" * 50)

        # Step 1: Analyze customer fashion preferences
        logger.info("Step 1: Analyzing customer preferences...")

        # Analyze fashion context for customer
        customer_text = """
        Customer prefers bohemian and minimalist styles with earth tones and neutral colors.
        Shows strong preference for sustainable and eco-friendly fashion brands.
        Frequently browses dresses and accessories in mid-range price category.
        """

        customer_analysis = await fashion_intelligence.analyze_fashion_context(customer_text)

        logger.info(f"  Fashion Relevance: {customer_analysis['fashion_relevance_score']:.2f}")
        logger.info(f"  Sustainability Focus: {len(customer_analysis['sustainability_mentions'])} mentions")
        logger.info(
            f"  Style Categories: {[cat['category'] for cat in customer_analysis['identified_categories'][:3]]}"
        )

        # Step 2: Generate personalized recommendations
        logger.info("\nStep 2: Generating personalized recommendations...")

        recommendations = await fashion_intelligence.get_trend_recommendations(
            category=FashionCategory.WOMENS_WEAR,
            target_demographic="millennial",
            sustainability_focus=True,
        )

        # Filter recommendations based on customer preferences
        personalized_recs = []
        for rec in recommendations:
            # Simple personalization logic
            if any(color in ["earth", "neutral", "brown"] for color in rec["key_elements"]["colors"]):
                rec["personalization_score"] = rec["popularity_score"] * 1.2  # Boost for preferred colors
                personalized_recs.append(rec)

        logger.info(f"✅ Generated {len(personalized_recs)} personalized recommendations")

        for rec in personalized_recs[:2]:  # Show top 2
            logger.info(f"  🌟 {rec['trend_name']}")
            logger.info(f"     Personalization Score: {rec.get('personalization_score', 0):.2f}")
            logger.info(f"     Matching Colors: {rec['key_elements']['colors']}")

        # Step 3: Create personalization workflow
        logger.info("\nStep 3: Setting up personalization automation...")

        personalization_trigger = WorkflowTrigger(
            trigger_id="customer_personalization",
            trigger_type=TriggerType.EVENT,
            name="Customer Personalization Update",
            description="Update customer personalization based on behavior",
            config={
                "event_types": ["purchase_completed", "browsing_session_ended"],
                "customer_segments": ["fashion_conscious", "sustainability_focused"],
            },
        )

        personalization_steps = [
            WorkflowStep(
                step_id="analyze_customer_behavior",
                name="Analyze Customer Behavior",
                action_type=ActionType.FASHION_ANALYSIS,
                config={
                    "analysis_type": "customer_preferences",
                    "customer_data": "${trigger_data.customer_data}",
                    "include_sustainability": True,
                },
            ),
            WorkflowStep(
                step_id="update_recommendations",
                name="Update Personalized Recommendations",
                action_type=ActionType.FASHION_ANALYSIS,
                config={
                    "analysis_type": "recommendations",
                    "customer_preferences": "${analyze_customer_behavior_result}",
                    "recommendation_types": ["products", "trends", "styles"],
                },
                depends_on=["analyze_customer_behavior"],
            ),
            WorkflowStep(
                step_id="cache_personalization",
                name="Cache Personalization Data",
                action_type=ActionType.CACHE_OPERATION,
                config={
                    "operation": "set",
                    "cache_key": "customer_personalization_${trigger_data.customer_id}",
                    "ttl": 86400,  # 24 hours
                    "data": "${update_recommendations_result}",
                },
                depends_on=["update_recommendations"],
            ),
        ]

        personalization_workflow = Workflow(
            workflow_id="customer_personalization_update",
            name="Customer Personalization Update",
            description="Automated customer personalization based on fashion intelligence",
            trigger=personalization_trigger,
            steps=personalization_steps,
            fashion_context=True,
            variables={
                "personalization_level": "advanced",
                "sustainability_weight": 0.3,
                "trend_weight": 0.4,
                "preference_weight": 0.3,
            },
        )

        success = await workflow_engine.register_workflow(personalization_workflow)

        if success:
            logger.info("✅ Personalization workflow registered successfully")
        else:
            logger.info("❌ Failed to register personalization workflow")

        self.examples_run.append("fashion_personalization")
        return customer_analysis, personalized_recs

    async def example_6_comprehensive_health_check(self):
        """Example 6: Comprehensive system health check"""

        logger.info("\n🏥 EXAMPLE 6: System Health Check")
        logger.info("=" * 50)

        # Check all system components
        health_results = {}

        # API Discovery Engine
        logger.info("Checking API Discovery Engine...")
        discovery_health = await api_discovery_engine.health_check()
        health_results["api_discovery"] = discovery_health
        logger.info(f"  Status: {discovery_health['status']}")
        logger.info(f"  APIs Discovered: {discovery_health.get('total_apis_discovered', 0)}")

        # API Gateway
        logger.info("\nChecking API Gateway...")
        gateway_health = await api_gateway.health_check()
        health_results["api_gateway"] = gateway_health
        logger.info(f"  Status: {gateway_health['status']}")
        logger.info(f"  Success Rate: {gateway_health.get('success_rate', 0) * 100:.1f}%")
        logger.info(f"  Average Response Time: {gateway_health.get('average_response_time', 0):.3f}s")

        # Workflow Engine
        logger.info("\nChecking Workflow Engine...")
        workflow_health = await workflow_engine.health_check()
        health_results["workflow_engine"] = workflow_health
        logger.info(f"  Status: {workflow_health['status']}")
        logger.info(f"  Registered Workflows: {workflow_health.get('registered_workflows', 0)}")
        logger.info(f"  Running Workflows: {workflow_health.get('running_workflows', 0)}")

        # Fashion API Integrator
        logger.info("\nChecking Fashion API Integrator...")
        fashion_health = await fashion_api_integrator.health_check()
        health_results["fashion_apis"] = fashion_health
        logger.info(f"  Status: {fashion_health['status']}")
        logger.info(f"  Fashion APIs Health: {fashion_health.get('fashion_apis_healthy', 'N/A')}")

        # Fashion Intelligence Engine
        logger.info("\nChecking Fashion Intelligence Engine...")
        intelligence_health = await fashion_intelligence.get_fashion_health_check()
        health_results["fashion_intelligence"] = intelligence_health
        logger.info(f"  Status: {intelligence_health['status']}")
        logger.info(f"  Trends Count: {intelligence_health['knowledge_base_stats']['trends_count']}")
        logger.info(
            f"  Market Intelligence: {intelligence_health['knowledge_base_stats']['market_intelligence_count']}"
        )

        # Overall system health
        logger.info("\n📊 OVERALL SYSTEM HEALTH:")
        logger.info("=" * 30)

        healthy_components = sum([1 for health in health_results.values() if health.get("status") == "healthy"])
        total_components = len(health_results)

        overall_health = "healthy" if healthy_components == total_components else "degraded"

        logger.info(f"Overall Status: {overall_health.upper()}")
        logger.info(f"Healthy Components: {healthy_components}/{total_components}")
        logger.info(f"System Readiness: {healthy_components / total_components * 100:.1f}%")

        if overall_health == "healthy":
            logger.info("✅ All systems operational - Ready for production!")
        else:
            logger.info("⚠️ Some components need attention")

        self.examples_run.append("comprehensive_health_check")
        return health_results

    async def run_all_examples(self):
        """Run all API integration examples"""

        logger.info("\n🚀 RUNNING ALL API INTEGRATION EXAMPLES")
        logger.info("=" * 60)
        logger.info("DevSkyy Enterprise Fashion Platform - API Integration System")
        logger.info("Comprehensive demonstration of automated API orchestration")
        logger.info("=" * 60)

        try:
            # Run all examples in sequence
            await self.example_1_api_discovery_and_setup()
            await self.example_2_fashion_trend_analysis()
            await self.example_3_automated_workflow_creation()
            await self.example_4_api_gateway_usage()
            await self.example_5_fashion_personalization()
            await self.example_6_comprehensive_health_check()

            # Summary
            logger.info("\n🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
            logger.info("=" * 50)
            logger.info(f"Examples Run: {len(self.examples_run)}")
            logger.info(f"Components Demonstrated: {', '.join(self.examples_run)}")
            logger.info("\n✅ DevSkyy API Integration System is fully operational!")
            logger.info("🌟 Ready for enterprise fashion e-commerce automation!")

        except Exception as e:
            logger.info(f"\n❌ Error running examples: {e}")
            logger.error(f"Example execution failed: {e}")


# Example usage and demonstration
async def main():
    """Main function to run API integration examples"""

    # Initialize examples
    examples = FashionAPIExamples()

    # Run all examples
    await examples.run_all_examples()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
