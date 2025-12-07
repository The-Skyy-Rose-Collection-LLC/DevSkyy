"""
Agent Upgrades API Endpoints

Provides REST API for deploying and tracking agent upgrades with RLVR verification.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db_session
from ml.rlvr.agent_upgrade_system import AgentUpgradeSystem
from ml.rlvr.reward_verifier import VerificationMethod
from security.jwt_auth import get_current_user


router = APIRouter(prefix="/api/v1/upgrades", tags=["upgrades", "rlvr"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UpgradeDeployRequest(BaseModel):
    """Request to deploy an upgrade to an agent."""
    agent_type: str = Field(..., description="Agent type (scanner, product_manager, etc.)")
    enable_ab_test: bool = Field(True, description="Enable A/B testing before full deployment")


class UpgradeVerificationRequest(BaseModel):
    """Submit verification data for an upgrade."""
    upgrade_id: uuid.UUID
    verification_method: str = Field(..., pattern="^(user_feedback|test_execution|code_analysis|business_metrics|automated_check)$")

    # Optional verification data fields
    thumbs_up: bool | None = None
    user_rating: int | None = Field(None, ge=1, le=5)
    user_feedback: str | None = None

    tests_passed: int | None = Field(None, ge=0)
    tests_total: int | None = Field(None, gt=0)
    test_output: str | None = None

    lint_score: float | None = Field(None, ge=0.0, le=1.0)
    complexity_score: float | None = Field(None, ge=0.0, le=1.0)
    security_score: float | None = Field(None, ge=0.0, le=1.0)

    revenue_impact_usd: float | None = None
    conversion_impact: float | None = Field(None, ge=0.0, le=1.0)

    passed: bool | None = None


class ABTestResultRequest(BaseModel):
    """Submit A/B test result."""
    ab_test_id: uuid.UUID
    variant: str = Field(..., pattern="^(variant_a|variant_b)$")
    score: float = Field(..., ge=0.0, le=1.0)


# ============================================================================
# DEPLOYMENT ENDPOINTS
# ============================================================================

@router.post("/deploy", status_code=status.HTTP_201_CREATED)
async def deploy_upgrade(
    request: UpgradeDeployRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Deploy an upgrade to a specific agent.

    This will:
    1. Deploy the upgrade feature
    2. Set up RLVR tracking
    3. Optionally start A/B testing
    4. Wait for verification from multiple sources

    The upgrade will be automatically promoted or rolled back based on composite reward score.
    """
    upgrade_system = AgentUpgradeSystem(session)

    try:
        result = await upgrade_system.deploy_upgrade(
            agent_type=request.agent_type,
            user_id=current_user.id,
            enable_ab_test=request.enable_ab_test
        )

        return {
            "success": True,
            "message": f"Upgrade deployed to {request.agent_type}",
            **result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy upgrade: {e!s}"
        )


@router.post("/deploy-all", status_code=status.HTTP_201_CREATED)
async def deploy_all_upgrades(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Deploy upgrades to ALL agent categories.

    This will deploy:
    - Scanner: Real-time code quality scoring
    - Multi-Model Orchestrator: Model performance comparison
    - Product Manager: Competitor price monitoring
    - SEO Marketing: Content gap analysis
    - Customer Service: Sentiment-aware responses
    - WordPress Theme Builder: Real-time preview
    - Predictive Automation: Proactive issue detection
    - Design Automation: Accessibility compliance

    Each upgrade is tracked with RLVR verification.
    """
    upgrade_system = AgentUpgradeSystem(session)

    try:
        result = await upgrade_system.deploy_all_upgrades(
            user_id=current_user.id
        )

        return {
            "success": True,
            "message": f"Deployed upgrades to {result['successful_deployments']} agents",
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy upgrades: {e!s}"
        )


# ============================================================================
# VERIFICATION ENDPOINTS
# ============================================================================

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_upgrade(
    request: UpgradeVerificationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Submit verification data for an upgrade.

    Verification methods:
    - user_feedback: Thumbs up/down, ratings, feedback text
    - test_execution: Automated test results
    - code_analysis: Lint, complexity, security scores
    - business_metrics: Revenue, conversion impact
    - automated_check: Simple pass/fail checks

    The system will compute a composite reward score from all verification sources
    and automatically promote or rollback the upgrade.
    """
    upgrade_system = AgentUpgradeSystem(session)

    try:
        # Parse verification method
        method = VerificationMethod(request.verification_method)

        # Collect verification data
        verification_data = {}

        if method == VerificationMethod.USER_FEEDBACK:
            verification_data.update({
                "thumbs_up": request.thumbs_up,
                "user_rating": request.user_rating,
                "user_feedback": request.user_feedback,
                "user_id": current_user.id
            })

        elif method == VerificationMethod.TEST_EXECUTION:
            if request.tests_passed is None or request.tests_total is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="tests_passed and tests_total are required for test_execution"
                )
            verification_data.update({
                "tests_passed": request.tests_passed,
                "tests_total": request.tests_total,
                "test_output": request.test_output
            })

        elif method == VerificationMethod.CODE_ANALYSIS:
            verification_data.update({
                "lint_score": request.lint_score,
                "complexity_score": request.complexity_score,
                "security_score": request.security_score
            })

        elif method == VerificationMethod.BUSINESS_METRICS:
            verification_data.update({
                "revenue_impact_usd": request.revenue_impact_usd,
                "conversion_impact": request.conversion_impact
            })

        elif method == VerificationMethod.AUTOMATED_CHECK:
            if request.passed is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="passed is required for automated_check"
                )
            verification_data["passed"] = request.passed

        # Submit verification
        result = await upgrade_system.verify_upgrade(
            upgrade_id=request.upgrade_id,
            verification_method=method,
            **verification_data
        )

        return {
            "success": True,
            "message": "Verification submitted successfully",
            **result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify upgrade: {e!s}"
        )


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@router.get("/{upgrade_id}/status")
async def get_upgrade_status(
    upgrade_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get the current status of an upgrade deployment.

    Returns:
    - Deployment details
    - Verification progress
    - Current scores
    - Overall status
    """
    upgrade_system = AgentUpgradeSystem(session)

    try:
        status_data = await upgrade_system.get_upgrade_status(upgrade_id)

        return {
            "success": True,
            **status_data
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upgrade status: {e!s}"
        )


@router.get("/status/all")
async def get_all_upgrades_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get status of all active upgrades.

    Returns summary of all upgrade deployments, verification progress, and overall metrics.
    """
    upgrade_system = AgentUpgradeSystem(session)

    try:
        status_data = await upgrade_system.get_all_upgrades_status()

        return {
            "success": True,
            **status_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upgrades status: {e!s}"
        )


# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@router.post("/ab-test/record", status_code=status.HTTP_200_OK)
async def record_ab_test_result(
    request: ABTestResultRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Record A/B test result for a specific variant.

    Used internally by the system to track performance of baseline vs upgraded agents.
    """
    try:
        query = """
            UPDATE ab_tests
            SET
                variant_a_score = CASE WHEN :variant = 'variant_a' THEN :score ELSE variant_a_score END,
                variant_b_score = CASE WHEN :variant = 'variant_b' THEN :score ELSE variant_b_score END,
                variant_a_count = CASE WHEN :variant = 'variant_a' THEN variant_a_count + 1 ELSE variant_a_count END,
                variant_b_count = CASE WHEN :variant = 'variant_b' THEN variant_b_count + 1 ELSE variant_b_count END
            WHERE ab_test_id = :ab_test_id AND status = 'running'
        """

        await session.execute(query, {
            "ab_test_id": request.ab_test_id,
            "variant": request.variant,
            "score": request.score
        })
        await session.commit()

        return {
            "success": True,
            "message": "A/B test result recorded"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record A/B test result: {e!s}"
        )


@router.get("/ab-test/{ab_test_id}")
async def get_ab_test_status(
    ab_test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get A/B test status and results.

    Returns:
    - Test configuration
    - Current scores for each variant
    - Sample sizes
    - Winner (if determined)
    - Confidence level
    """
    try:
        query = """
            SELECT
                ab_test_id,
                upgrade_id,
                agent_type,
                variant_a,
                variant_b,
                variant_a_score,
                variant_b_score,
                variant_a_count,
                variant_b_count,
                winner,
                confidence_level,
                status,
                started_at,
                completed_at
            FROM ab_tests
            WHERE ab_test_id = :ab_test_id
        """

        result = await session.execute(query, {"ab_test_id": ab_test_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A/B test {ab_test_id} not found"
            )

        return {
            "success": True,
            "ab_test_id": str(row[0]),
            "upgrade_id": str(row[1]),
            "agent_type": row[2],
            "variants": {
                "a": {
                    "name": row[3],
                    "score": float(row[5]) if row[5] else None,
                    "count": row[7]
                },
                "b": {
                    "name": row[4],
                    "score": float(row[6]) if row[6] else None,
                    "count": row[8]
                }
            },
            "winner": row[9],
            "confidence_level": float(row[10]) if row[10] else None,
            "status": row[11],
            "started_at": row[12].isoformat() if row[12] else None,
            "completed_at": row[13].isoformat() if row[13] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get A/B test status: {e!s}"
        )


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/summary")
async def get_upgrade_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get analytics summary for all upgrades.

    Returns:
    - Total upgrades deployed
    - Success rate
    - Average improvement
    - Breakdown by agent type
    - Recent upgrade activity
    """
    try:
        # Get overall statistics
        overall_query = """
            SELECT
                COUNT(*) as total_upgrades,
                COUNT(CASE WHEN status = 'production' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'rolled_back' THEN 1 END) as rolled_back,
                AVG(final_score) as avg_score,
                AVG(expected_improvement) as avg_expected_improvement
            FROM agent_upgrades
            WHERE deployed_at >= NOW() - INTERVAL ':days days'
        """

        overall_result = await session.execute(overall_query, {"days": days})
        overall_row = overall_result.fetchone()

        # Get breakdown by agent type
        breakdown_query = """
            SELECT
                agent_type,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'production' THEN 1 END) as successful,
                AVG(final_score) as avg_score
            FROM agent_upgrades
            WHERE deployed_at >= NOW() - INTERVAL ':days days'
            GROUP BY agent_type
            ORDER BY total DESC
        """

        breakdown_result = await session.execute(breakdown_query, {"days": days})
        breakdown = [
            {
                "agent_type": row[0],
                "total": row[1],
                "successful": row[2],
                "success_rate": f"{(row[2] / row[1] * 100):.1f}%" if row[1] > 0 else "0%",
                "avg_score": float(row[3]) if row[3] else None
            }
            for row in breakdown_result.fetchall()
        ]

        return {
            "success": True,
            "period_days": days,
            "overall": {
                "total_upgrades": overall_row[0],
                "successful": overall_row[1],
                "rolled_back": overall_row[2],
                "success_rate": f"{(overall_row[1] / overall_row[0] * 100):.1f}%" if overall_row[0] > 0 else "0%",
                "avg_score": float(overall_row[3]) if overall_row[3] else None,
                "avg_expected_improvement": float(overall_row[4]) if overall_row[4] else None
            },
            "by_agent_type": breakdown
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upgrade analytics: {e!s}"
        )


@router.get("/catalog")
async def get_upgrade_catalog(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get catalog of available upgrades for all agent types.

    Returns details about each upgrade:
    - Name and description
    - Verification methods required
    - Expected improvement
    - Deployment status
    """
    upgrade_system = AgentUpgradeSystem(session)

    return {
        "success": True,
        "upgrades": upgrade_system.upgrade_catalog
    }
