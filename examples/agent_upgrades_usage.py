"""
Agent Upgrades Usage Examples

Complete workflow for deploying and verifying agent upgrades using RLVR system.

This example demonstrates:
1. Deploying upgrades to all agents
2. Collecting verification data from multiple sources
3. Tracking upgrade performance
4. Automatic promotion or rollback based on composite scores
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ml.rlvr.agent_upgrade_system import AgentUpgradeSystem
from ml.rlvr.agent_upgrades_implementations import (
    AutomatedModelComparison,
    CompetitorPriceMonitor,
    ContentGapAnalyzer,
    RealTimeCodeQualityScorer,
)
from ml.rlvr.reward_verifier import VerificationMethod


# ============================================================================
# EXAMPLE 1: Deploy Single Upgrade
# ============================================================================

async def example_deploy_single_upgrade():
    """Deploy an upgrade to a single agent."""
    # Setup database connection
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/devskyy")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "="*80)
        print("EXAMPLE 1: Deploy Single Upgrade")
        print("="*80 + "\n")

        upgrade_system = AgentUpgradeSystem(session)

        # Deploy upgrade to scanner agent
        result = await upgrade_system.deploy_upgrade(
            agent_type="scanner",
            user_id=uuid.UUID("your-user-id-here"),
            enable_ab_test=True
        )

        print(f"✅ Upgrade deployed: {result['upgrade_name']}")
        print(f"   Agent Type: {result['agent_type']}")
        print(f"   Expected Improvement: {result['expected_improvement']}")
        print(f"   Verification Methods: {result['verification_methods']}")
        print(f"   Tracking URL: {result['tracking_url']}")


# ============================================================================
# EXAMPLE 2: Deploy All Upgrades
# ============================================================================

async def example_deploy_all_upgrades():
    """Deploy upgrades to all agent categories."""
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/devskyy")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "="*80)
        print("EXAMPLE 2: Deploy All Upgrades")
        print("="*80 + "\n")

        upgrade_system = AgentUpgradeSystem(session)
        user_id = uuid.UUID("your-user-id-here")

        # Deploy upgrades to ALL agents
        result = await upgrade_system.deploy_all_upgrades(user_id)

        print("✅ Deployment Summary:")
        print(f"   Total Agents: {result['total_agents']}")
        print(f"   Successful: {result['successful_deployments']}")
        print(f"   Failed: {result['failed_deployments']}")
        print("\nDeployments:")

        for deployment in result['deployments']:
            status_icon = "✅" if deployment['status'] == 'success' else "❌"
            print(f"   {status_icon} {deployment['agent_type']}: {deployment.get('upgrade_name', 'N/A')}")


# ============================================================================
# EXAMPLE 3: Verify Upgrade with Multiple Sources
# ============================================================================

async def example_verify_upgrade_multi_source():
    """Verify an upgrade using multiple verification methods."""
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/devskyy")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "="*80)
        print("EXAMPLE 3: Multi-Source Verification")
        print("="*80 + "\n")

        upgrade_system = AgentUpgradeSystem(session)
        upgrade_id = uuid.UUID("your-upgrade-id-here")

        # Verification 1: Code Analysis
        print("📊 Submitting Code Analysis verification...")
        code_analysis_result = await upgrade_system.verify_upgrade(
            upgrade_id=upgrade_id,
            verification_method=VerificationMethod.CODE_ANALYSIS,
            lint_score=0.95,
            complexity_score=0.88,
            security_score=1.0
        )
        print(f"   Reward Score: {code_analysis_result['reward_score']}")

        # Verification 2: Test Execution
        print("\n🧪 Submitting Test Execution verification...")
        test_result = await upgrade_system.verify_upgrade(
            upgrade_id=upgrade_id,
            verification_method=VerificationMethod.TEST_EXECUTION,
            tests_passed=95,
            tests_total=100,
            test_output="5 edge cases failed, core functionality works"
        )
        print(f"   Reward Score: {test_result['reward_score']}")
        print(f"   Verifications Pending: {test_result['verifications_pending']}")

        # Verification 3: User Feedback
        print("\n👤 Submitting User Feedback verification...")
        user_feedback_result = await upgrade_system.verify_upgrade(
            upgrade_id=upgrade_id,
            verification_method=VerificationMethod.USER_FEEDBACK,
            thumbs_up=True,
            user_rating=5,
            user_feedback="The real-time quality scoring is amazing! Much faster than before."
        )
        print(f"   Reward Score: {user_feedback_result['reward_score']}")

        if user_feedback_result['all_verifications_complete']:
            print("\n🎉 All verifications complete!")
            print(f"   Status: {user_feedback_result['status']}")
            print(f"   Composite Score: {user_feedback_result['composite_score']}")
            print(f"   Threshold: {user_feedback_result['threshold']}")


# ============================================================================
# EXAMPLE 4: Use Specific Upgrade Implementation
# ============================================================================

async def example_use_scanner_upgrade():
    """Use the Scanner Agent upgrade (Real-Time Code Quality Scoring)."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Scanner Upgrade - Real-Time Code Quality")
    print("="*80 + "\n")

    scorer = RealTimeCodeQualityScorer()

    # Test code snippet
    code_snippet = """
def calculate_total(items):
    total = 0
    for item in items:
        if item['price'] > 0 and item['quantity'] > 0:
            total += item['price'] * item['quantity']
    return total

# Helper function
def apply_discount(total, discount_percentage):
    if discount_percentage > 0 and discount_percentage <= 100:
        return total * (1 - discount_percentage / 100)
    return total
"""

    # Score the code
    result = await scorer.score_code_realtime(code_snippet)

    print(f"✅ Code Quality Score: {result['quality_score']:.1f}/100")
    print("\nFeatures Analyzed:")
    for feature, value in result['features'].items():
        print(f"   - {feature}: {value}")

    print("\nRecommendations:")
    for rec in result['recommendations']:
        priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
        print(f"   {priority_icon} [{rec['category']}] {rec['message']}")
        print(f"      Fix: {rec['fix']}")

    print(f"\n⏱️  Estimated Fix Time: {result['estimated_fix_time']}")
    print(f"🚨 Priority Issues: {len(result['priority_issues'])}")


# ============================================================================
# EXAMPLE 5: Model Performance Comparison
# ============================================================================

async def example_model_comparison():
    """Use the Multi-Model Orchestrator upgrade."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Multi-Model Orchestrator - Performance Comparison")
    print("="*80 + "\n")

    comparator = AutomatedModelComparison()

    prompt = "Analyze the following fashion trend data and predict Q4 2025 trends..."

    # Compare all models
    result = await comparator.compare_models(
        prompt=prompt,
        task_type="trend_analysis"
    )

    print(f"🏆 Best Model: {result['best_model']}")
    print(f"📊 Reasoning: {result['reasoning']}")

    print("\nModel Comparison:")
    for model_name, comparison in result['model_comparisons'].items():
        if comparison.get('status') == 'success':
            print(f"   {model_name}:")
            print(f"      Quality: {comparison['quality_score']:.3f}")
            print(f"      Latency: {comparison['latency_ms']:.0f}ms")
            print(f"      Cost: ${comparison['cost_usd']:.4f}")
        else:
            print(f"   {model_name}: ❌ {comparison.get('error', 'Unknown error')}")

    print(f"\n🔄 Fallback Order: {' → '.join(result['fallback_order'])}")


# ============================================================================
# EXAMPLE 6: Competitor Price Monitoring
# ============================================================================

async def example_price_monitoring():
    """Use the Product Manager upgrade."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Product Manager - Competitor Price Monitoring")
    print("="*80 + "\n")

    monitor = CompetitorPriceMonitor()

    product_id = "PROD-12345"
    competitor_urls = [
        "https://competitor1.com/product/silk-dress",
        "https://competitor2.com/product/silk-dress",
        "https://competitor3.com/product/luxury-dress"
    ]

    # Monitor competitors
    result = await monitor.monitor_competitors(
        product_id=product_id,
        competitor_urls=competitor_urls
    )

    print(f"📊 Competitor Price Analysis for {result['product_id']}")

    print("\nCompetitor Prices:")
    for comp in result['competitor_prices']:
        stock_status = "✅ In Stock" if comp['in_stock'] else "❌ Out of Stock"
        print(f"   {comp['competitor']}: ${comp['price']:.2f} {comp['currency']} - {stock_status}")

    analysis = result['analysis']
    print(f"\nPricing Position: {analysis['position'].upper()}")
    print(f"   Current Price: ${analysis['current_price']:.2f}")
    print(f"   Competitor Range: ${analysis['competitor_min']:.2f} - ${analysis['competitor_max']:.2f}")
    print(f"   Market Average: ${analysis['competitor_avg']:.2f}")
    print(f"   Price Gap: ${analysis['price_gap']:.2f}")

    print("\nRecommendations:")
    for rec in result['recommendations']:
        priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
        print(f"   {priority_icon} {rec['action'].replace('_', ' ').title()}")
        print(f"      Target: ${rec.get('target_price', 0):.2f}")
        print(f"      Reason: {rec['reasoning']}")
        print(f"      Impact: {rec['expected_impact']}")


# ============================================================================
# EXAMPLE 7: Content Gap Analysis
# ============================================================================

async def example_content_gap_analysis():
    """Use the SEO Marketing Agent upgrade."""
    print("\n" + "="*80)
    print("EXAMPLE 7: SEO Marketing - Content Gap Analysis")
    print("="*80 + "\n")

    analyzer = ContentGapAnalyzer()

    domain = "yourbrand.com"
    competitors = [
        "competitor1.com",
        "competitor2.com",
        "competitor3.com"
    ]
    target_keywords = [
        "luxury silk dress",
        "designer evening gown",
        "sustainable fashion",
        "vintage leather jacket",
        "custom tailoring"
    ]

    # Analyze content gaps
    result = await analyzer.analyze_content_gaps(
        domain=domain,
        competitors=competitors,
        target_keywords=target_keywords
    )

    print(f"📊 Content Gap Analysis for {result['domain']}")
    print(f"   Competitors Analyzed: {result['competitors_analyzed']}")
    print(f"   Keywords Analyzed: {result['keywords_analyzed']}")
    print(f"   Content Gaps Found: {result['content_gaps_found']}")

    print("\n🎯 Top Content Opportunities:")
    for i, opportunity in enumerate(result['top_opportunities'][:5], 1):
        priority_icon = "🔴" if opportunity['priority'] == 'high' else "🟡"
        print(f"\n   {i}. {opportunity['keyword']} {priority_icon}")
        print(f"      Gap Type: {opportunity['gap_type'].replace('_', ' ').title()}")
        print(f"      Search Volume: {opportunity['search_volume']:,}/month")
        print(f"      Opportunity Score: {opportunity['opportunity_score']:.1f}")

        if opportunity['gap_type'] == 'missing_content':
            print(f"      Competitors Covering: {opportunity['competitors_covering']}")
        elif opportunity['gap_type'] == 'quality_gap':
            print(f"      Quality Difference: {opportunity['quality_difference']:.2f}")

    traffic_potential = result['estimated_traffic_potential']
    print("\n📈 Traffic Potential:")
    print(f"   Estimated Monthly Visits: {traffic_potential['estimated_monthly_visits']:,}")
    print(f"   Estimated Annual Visits: {traffic_potential['estimated_annual_visits']:,}")
    print(f"   Confidence: {traffic_potential['confidence'].upper()}")


# ============================================================================
# EXAMPLE 8: Track All Upgrades Status
# ============================================================================

async def example_track_all_upgrades():
    """Track status of all active upgrades."""
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/devskyy")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("\n" + "="*80)
        print("EXAMPLE 8: Track All Upgrades Status")
        print("="*80 + "\n")

        upgrade_system = AgentUpgradeSystem(session)

        # Get all upgrades status
        status = await upgrade_system.get_all_upgrades_status()

        print("📊 Overall Upgrade Status")
        print(f"   Total Upgrades: {status['total_upgrades']}")
        print(f"   Completed Verifications: {status['completed_verifications']}")
        print(f"   In Progress: {status['in_progress']}")
        print(f"   Average Progress: {status['average_progress']}")

        print("\n📋 Individual Upgrades:")
        for upgrade in status['upgrades']:
            progress_bar = "█" * int(upgrade['progress'] / 10) + "░" * (10 - int(upgrade['progress'] / 10))
            print(f"\n   {upgrade['agent_type']}:")
            print(f"      Name: {upgrade['upgrade_name']}")
            print(f"      Status: {upgrade['status']}")
            print(f"      Progress: [{progress_bar}] {upgrade['progress']:.0f}%")
            print(f"      Verifications Pending: {', '.join(upgrade['verifications_pending'])}")


# ============================================================================
# API USAGE EXAMPLES
# ============================================================================

def api_usage_examples():
    """
    Example API calls for agent upgrades system.
    """
    print("""
# ============================================================================
# API ENDPOINT USAGE
# ============================================================================

# 1. Deploy Single Upgrade
curl -X POST http://localhost:8000/api/v1/upgrades/deploy \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_type": "scanner",
    "enable_ab_test": true
  }'

# 2. Deploy All Upgrades
curl -X POST http://localhost:8000/api/v1/upgrades/deploy-all \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Submit Verification (User Feedback)
curl -X POST http://localhost:8000/api/v1/upgrades/verify \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "upgrade_id": "550e8400-e29b-41d4-a716-446655440000",
    "verification_method": "user_feedback",
    "thumbs_up": true,
    "user_rating": 5,
    "user_feedback": "Great improvement!"
  }'

# 4. Submit Verification (Test Results)
curl -X POST http://localhost:8000/api/v1/upgrades/verify \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "upgrade_id": "550e8400-e29b-41d4-a716-446655440000",
    "verification_method": "test_execution",
    "tests_passed": 95,
    "tests_total": 100
  }'

# 5. Get Upgrade Status
curl -X GET http://localhost:8000/api/v1/upgrades/550e8400-e29b-41d4-a716-446655440000/status \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 6. Get All Upgrades Status
curl -X GET http://localhost:8000/api/v1/upgrades/status/all \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 7. Get Upgrade Analytics
curl -X GET http://localhost:8000/api/v1/upgrades/analytics/summary?days=30 \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 8. Get Upgrade Catalog
curl -X GET http://localhost:8000/api/v1/upgrades/catalog \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Agent Upgrades Usage Examples")
    print("=" * 80)
    print()

    # Show API examples
    api_usage_examples()

    # To run individual examples:
    # asyncio.run(example_deploy_single_upgrade())
    # asyncio.run(example_deploy_all_upgrades())
    # asyncio.run(example_verify_upgrade_multi_source())
    # asyncio.run(example_use_scanner_upgrade())
    # asyncio.run(example_model_comparison())
    # asyncio.run(example_price_monitoring())
    # asyncio.run(example_content_gap_analysis())
    # asyncio.run(example_track_all_upgrades())
