"""
Reward Verification System

Computes and verifies reward scores for agent executions based on
multiple verification methods.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession


class VerificationMethod(Enum):
    """Types of reward verification."""
    USER_FEEDBACK = "user_feedback"
    TEST_EXECUTION = "test_execution"
    CODE_ANALYSIS = "code_analysis"
    BUSINESS_METRICS = "business_metrics"
    AUTOMATED_CHECK = "automated_check"
    PEER_REVIEW = "peer_review"


class RewardVerifier:
    """
    Verifies and computes reward scores for agent executions.

    Combines multiple verification methods to produce a reliable
    reward signal for reinforcement learning.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_execution(
        self,
        execution_id: uuid.UUID,
        verification_method: VerificationMethod,
        **kwargs
    ) -> dict[str, Any]:
        """
        Verify an agent execution and compute reward score.

        Args:
            execution_id: ID of the agent execution to verify
            verification_method: Method used for verification
            **kwargs: Additional verification-specific parameters

        Returns:
            RewardScore dictionary
        """
        # Compute reward based on verification method
        if verification_method == VerificationMethod.USER_FEEDBACK:
            reward_data = await self._verify_user_feedback(execution_id, **kwargs)
        elif verification_method == VerificationMethod.TEST_EXECUTION:
            reward_data = await self._verify_test_execution(execution_id, **kwargs)
        elif verification_method == VerificationMethod.CODE_ANALYSIS:
            reward_data = await self._verify_code_analysis(execution_id, **kwargs)
        elif verification_method == VerificationMethod.BUSINESS_METRICS:
            reward_data = await self._verify_business_metrics(execution_id, **kwargs)
        elif verification_method == VerificationMethod.AUTOMATED_CHECK:
            reward_data = await self._verify_automated_check(execution_id, **kwargs)
        else:
            raise ValueError(f"Unknown verification method: {verification_method}")

        # Save to database
        reward_score_id = await self._save_reward_score(execution_id, reward_data)
        reward_data['id'] = reward_score_id

        return reward_data

    async def _verify_user_feedback(
        self,
        execution_id: uuid.UUID,
        user_rating: int | None = None,
        user_feedback: str | None = None,
        thumbs_up: bool | None = None,
        user_id: uuid.UUID | None = None
    ) -> dict[str, Any]:
        """Verify based on explicit user feedback."""

        # Convert feedback to score
        if thumbs_up is not None:
            score = 1.0 if thumbs_up else 0.0
        elif user_rating is not None:
            # Convert 1-5 star rating to 0.0-1.0
            score = (user_rating - 1) / 4.0
        else:
            score = 0.5  # Neutral if no explicit feedback

        return {
            "execution_id": execution_id,
            "reward_score": Decimal(str(score)),
            "user_feedback_score": Decimal(str(score)),
            "verification_method": VerificationMethod.USER_FEEDBACK.value,
            "verification_confidence": Decimal("0.9"),
            "user_feedback": user_feedback,
            "user_rating": user_rating,
            "verified_by_user_id": user_id,
            "verified_at": datetime.utcnow()
        }

    async def _verify_test_execution(
        self,
        execution_id: uuid.UUID,
        tests_passed: int,
        tests_total: int,
        test_output: str | None = None
    ) -> dict[str, Any]:
        """Verify based on automated test execution."""

        # Pass rate = reward score
        score = tests_passed / tests_total if tests_total > 0 else 0.0

        return {
            "execution_id": execution_id,
            "reward_score": Decimal(str(score)),
            "objective_score": Decimal(str(score)),
            "verification_method": VerificationMethod.TEST_EXECUTION.value,
            "verification_confidence": Decimal("0.95"),
            "user_feedback": f"Tests: {tests_passed}/{tests_total} passed. {test_output or ''}",
            "verified_at": datetime.utcnow()
        }

    async def _verify_code_analysis(
        self,
        execution_id: uuid.UUID,
        lint_score: float | None = None,
        complexity_score: float | None = None,
        security_score: float | None = None
    ) -> dict[str, Any]:
        """Verify based on static code analysis."""

        # Average of available scores
        scores = [s for s in [lint_score, complexity_score, security_score] if s is not None]
        score = sum(scores) / len(scores) if scores else 0.5

        return {
            "execution_id": execution_id,
            "reward_score": Decimal(str(score)),
            "automated_score": Decimal(str(score)),
            "verification_method": VerificationMethod.CODE_ANALYSIS.value,
            "verification_confidence": Decimal("0.85"),
            "user_feedback": f"Code quality: {score:.2%}",
            "verified_at": datetime.utcnow()
        }

    async def _verify_business_metrics(
        self,
        execution_id: uuid.UUID,
        revenue_impact_usd: float | None = None,
        conversion_rate: float | None = None,
        retention_impact: float | None = None
    ) -> dict[str, Any]:
        """Verify based on business impact metrics."""

        # Normalize business metrics to 0-1 range
        score = 0.5  # Default neutral

        if revenue_impact_usd is not None and revenue_impact_usd > 0:
            # Positive revenue impact = positive reward
            # Cap at $10K for normalization
            score = min(revenue_impact_usd / 10000.0, 1.0)
        elif conversion_rate is not None:
            score = conversion_rate
        elif retention_impact is not None:
            score = retention_impact

        return {
            "execution_id": execution_id,
            "reward_score": Decimal(str(score)),
            "business_score": Decimal(str(score)),
            "verification_method": VerificationMethod.BUSINESS_METRICS.value,
            "verification_confidence": Decimal("0.75"),
            "revenue_impact_usd": revenue_impact_usd,
            "conversion_impact": Decimal(str(conversion_rate)) if conversion_rate else None,
            "verified_at": datetime.utcnow()
        }

    async def _verify_automated_check(
        self,
        execution_id: uuid.UUID,
        check_results: dict[str, bool]
    ) -> dict[str, Any]:
        """Verify based on automated checks (e.g., formatting, compilation)."""

        # Pass rate of all checks
        passed = sum(1 for result in check_results.values() if result)
        total = len(check_results)
        score = passed / total if total > 0 else 0.0

        return {
            "execution_id": execution_id,
            "reward_score": Decimal(str(score)),
            "automated_score": Decimal(str(score)),
            "verification_method": VerificationMethod.AUTOMATED_CHECK.value,
            "verification_confidence": Decimal("0.9"),
            "user_feedback": f"Checks: {passed}/{total} passed",
            "verified_at": datetime.utcnow()
        }

    async def compute_composite_reward(
        self,
        execution_id: uuid.UUID
    ) -> Decimal:
        """
        Compute a composite reward score from all verification methods.

        Uses weighted average of all available reward scores.
        """
        # Get all reward scores for this execution
        query = """
            SELECT reward_score, verification_confidence
            FROM reward_scores
            WHERE execution_id = :execution_id
        """

        result = await self.session.execute(query, {"execution_id": execution_id})
        scores = result.fetchall()

        if not scores:
            return Decimal("0.5")  # Default neutral

        # Weight by confidence
        weighted_sum = sum(
            Decimal(str(score[0])) * Decimal(str(score[1]))
            for score in scores
        )
        confidence_sum = sum(Decimal(str(score[1])) for score in scores)

        composite_reward = weighted_sum / confidence_sum if confidence_sum > 0 else Decimal("0.5")

        return composite_reward

    async def _save_reward_score(
        self,
        execution_id: uuid.UUID,
        reward_data: dict[str, Any]
    ) -> uuid.UUID:
        """Save reward score to database."""
        reward_id = uuid.uuid4()

        query = """
            INSERT INTO reward_scores (
                id, execution_id, reward_score, user_feedback_score,
                objective_score, business_score, automated_score,
                verification_method, verification_confidence,
                user_feedback, user_rating, revenue_impact_usd,
                conversion_impact, verified_at, verified_by_user_id
            ) VALUES (
                :id, :execution_id, :reward_score, :user_feedback_score,
                :objective_score, :business_score, :automated_score,
                :verification_method, :verification_confidence,
                :user_feedback, :user_rating, :revenue_impact_usd,
                :conversion_impact, :verified_at, :verified_by_user_id
            )
        """

        await self.session.execute(query, {
            "id": reward_id,
            **reward_data
        })
        await self.session.commit()

        return reward_id
