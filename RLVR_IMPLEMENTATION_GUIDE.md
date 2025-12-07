# Reinforcement Learning with Verifiable Rewards (RLVR) for DevSkyy Agents

**Version:** 1.0.0
**Date:** 2025-11-20
**Status:** Architecture & Implementation Plan

---

## Executive Summary

Implement a production-grade RLVR system that continuously fine-tunes all DevSkyy agents based on verified task outcomes, user feedback, and objective metrics. This system will automatically improve agent performance over time while maintaining safety and quality standards.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RLVR Fine-Tuning Pipeline                       │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Agent      │      │   Reward     │      │  Training    │      │   Fine-      │
│  Execution   │─────▶│  Verification│─────▶│   Data       │─────▶│   Tuning     │
│              │      │              │      │  Collection  │      │   Pipeline   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
      │                     │                      │                     │
      │                     │                      │                     │
      ▼                     ▼                      ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Execution   │      │   Reward     │      │   Training   │      │   Model      │
│    Logs      │      │   Scores     │      │  Examples    │      │  Registry    │
│ (PostgreSQL) │      │ (PostgreSQL) │      │ (PostgreSQL) │      │ (Pinecone)   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘

                    ┌──────────────────────┐
                    │   Monitoring &       │
                    │   Analytics          │
                    │   (PostHog)          │
                    └──────────────────────┘
```

---

## Core Components

### 1. Reward Verification System

**Verifiable Rewards** are computed from:
- **Objective Metrics**: Task completion, correctness, execution time
- **User Feedback**: Thumbs up/down, ratings, explicit corrections
- **Automated Verification**: Test execution, code analysis, output validation
- **Business Metrics**: Revenue impact, user retention, feature adoption

### 2. Training Data Collection

**What to Collect:**
```python
TrainingExample = {
    "prompt": str,              # Input to agent
    "completion": str,          # Agent's output
    "reward": float,            # Verified reward score (0.0 - 1.0)
    "metadata": {
        "agent_id": str,
        "agent_version": str,
        "execution_time_ms": int,
        "user_feedback": Optional[str],
        "verification_method": str,
        "business_impact": Optional[float]
    }
}
```

### 3. Fine-Tuning Pipeline

**Supported Models:**
- **Anthropic Claude** (via prompt refinement & few-shot learning)
- **OpenAI GPT-4/3.5** (fine-tuning API)
- **Open-source models** (LoRA, QLoRA via PEFT)

---

## Database Schema

### Agents Table (Existing)
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,  -- e.g., 'code-reviewer', 'deployment-assistant'
    model_provider VARCHAR(50),  -- 'anthropic', 'openai', 'local'
    model_name VARCHAR(100),     -- 'claude-3-sonnet-20240229'
    base_prompt TEXT,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_active ON agents(is_active);
```

### Agent Executions (Tracking)
```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    agent_version INTEGER NOT NULL,

    -- Input/Output
    input_prompt TEXT NOT NULL,
    output_completion TEXT,

    -- Execution Metrics
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),

    -- Status
    status VARCHAR(50) NOT NULL,  -- 'success', 'error', 'timeout'
    error_message TEXT,

    -- Context
    user_id UUID,
    session_id UUID,
    request_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_executions_agent ON agent_executions(agent_id);
CREATE INDEX idx_executions_status ON agent_executions(status);
CREATE INDEX idx_executions_created ON agent_executions(created_at DESC);
```

### Reward Scores (Verification)
```sql
CREATE TABLE reward_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- Reward Components
    reward_score DECIMAL(5, 4) NOT NULL,  -- 0.0000 to 1.0000

    -- Verification Methods (multiple can apply)
    user_feedback_score DECIMAL(5, 4),     -- User thumbs up/down, rating
    objective_score DECIMAL(5, 4),         -- Test pass/fail, correctness
    business_score DECIMAL(5, 4),          -- Revenue, retention impact
    automated_score DECIMAL(5, 4),         -- Code quality, linting

    -- Verification Details
    verification_method VARCHAR(100) NOT NULL,  -- 'user_feedback', 'test_execution', 'code_analysis'
    verification_confidence DECIMAL(5, 4),      -- How confident in this reward

    -- Feedback
    user_feedback TEXT,
    user_rating INTEGER,  -- 1-5 stars

    -- Business Impact
    revenue_impact_usd DECIMAL(10, 2),
    conversion_impact DECIMAL(5, 4),

    verified_at TIMESTAMP DEFAULT NOW(),
    verified_by_user_id UUID
);

CREATE INDEX idx_rewards_execution ON reward_scores(execution_id);
CREATE INDEX idx_rewards_score ON reward_scores(reward_score DESC);
CREATE INDEX idx_rewards_verified ON reward_scores(verified_at DESC);
```

### Training Examples (For Fine-Tuning)
```sql
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE SET NULL,

    -- Training Data
    prompt TEXT NOT NULL,
    completion TEXT NOT NULL,
    reward_score DECIMAL(5, 4) NOT NULL,

    -- Metadata
    example_type VARCHAR(50),  -- 'positive', 'negative', 'neutral'
    is_synthetic BOOLEAN DEFAULT FALSE,  -- Generated vs real

    -- Quality Control
    is_validated BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,

    -- Training Status
    used_in_training BOOLEAN DEFAULT FALSE,
    training_run_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_training_agent ON training_examples(agent_id);
CREATE INDEX idx_training_reward ON training_examples(reward_score DESC);
CREATE INDEX idx_training_used ON training_examples(used_in_training);
```

### Fine-Tuning Runs
```sql
CREATE TABLE fine_tuning_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,

    -- Training Configuration
    base_model VARCHAR(100) NOT NULL,
    training_examples_count INTEGER NOT NULL,
    epochs INTEGER,
    learning_rate DECIMAL(10, 8),

    -- Provider-Specific
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'local'
    provider_job_id VARCHAR(255),   -- External fine-tuning job ID

    -- Status
    status VARCHAR(50) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    progress_percentage INTEGER DEFAULT 0,

    -- Results
    trained_model_id VARCHAR(255),
    validation_loss DECIMAL(10, 6),
    validation_accuracy DECIMAL(5, 4),

    -- Metrics
    cost_usd DECIMAL(10, 2),
    training_time_seconds INTEGER,

    -- Deployment
    deployed_at TIMESTAMP,
    deployed_version INTEGER,

    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_finetuning_agent ON fine_tuning_runs(agent_id);
CREATE INDEX idx_finetuning_status ON fine_tuning_runs(status);
CREATE INDEX idx_finetuning_created ON fine_tuning_runs(created_at DESC);
```

---

## Implementation: Core RLVR System

### File: `ml/rlvr/reward_verifier.py`

```python
"""
Reward Verification System

Computes and verifies reward scores for agent executions based on
multiple verification methods.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import select
from infrastructure.database import get_db
from models.agent_execution import AgentExecution, RewardScore


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

    def __init__(self):
        self.db = get_db()

    async def verify_execution(
        self,
        execution_id: uuid.UUID,
        verification_method: VerificationMethod,
        **kwargs
    ) -> RewardScore:
        """
        Verify an agent execution and compute reward score.

        Args:
            execution_id: ID of the agent execution to verify
            verification_method: Method used for verification
            **kwargs: Additional verification-specific parameters

        Returns:
            RewardScore object with computed reward
        """
        # Get execution
        execution = await self._get_execution(execution_id)

        # Compute reward based on verification method
        if verification_method == VerificationMethod.USER_FEEDBACK:
            reward_score = await self._verify_user_feedback(execution, **kwargs)
        elif verification_method == VerificationMethod.TEST_EXECUTION:
            reward_score = await self._verify_test_execution(execution, **kwargs)
        elif verification_method == VerificationMethod.CODE_ANALYSIS:
            reward_score = await self._verify_code_analysis(execution, **kwargs)
        elif verification_method == VerificationMethod.BUSINESS_METRICS:
            reward_score = await self._verify_business_metrics(execution, **kwargs)
        elif verification_method == VerificationMethod.AUTOMATED_CHECK:
            reward_score = await self._verify_automated_check(execution, **kwargs)
        else:
            raise ValueError(f"Unknown verification method: {verification_method}")

        # Save to database
        await self._save_reward_score(reward_score)

        return reward_score

    async def _verify_user_feedback(
        self,
        execution: AgentExecution,
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None,
        thumbs_up: Optional[bool] = None
    ) -> RewardScore:
        """Verify based on explicit user feedback."""

        # Convert feedback to score
        if thumbs_up is not None:
            score = 1.0 if thumbs_up else 0.0
        elif user_rating is not None:
            # Convert 1-5 star rating to 0.0-1.0
            score = (user_rating - 1) / 4.0
        else:
            score = 0.5  # Neutral if no explicit feedback

        return RewardScore(
            execution_id=execution.id,
            reward_score=Decimal(str(score)),
            user_feedback_score=Decimal(str(score)),
            verification_method=VerificationMethod.USER_FEEDBACK.value,
            verification_confidence=Decimal("0.9"),  # High confidence in user feedback
            user_feedback=user_feedback,
            user_rating=user_rating,
            verified_at=datetime.utcnow()
        )

    async def _verify_test_execution(
        self,
        execution: AgentExecution,
        tests_passed: int,
        tests_total: int,
        test_output: Optional[str] = None
    ) -> RewardScore:
        """Verify based on automated test execution."""

        # Pass rate = reward score
        score = tests_passed / tests_total if tests_total > 0 else 0.0

        return RewardScore(
            execution_id=execution.id,
            reward_score=Decimal(str(score)),
            objective_score=Decimal(str(score)),
            verification_method=VerificationMethod.TEST_EXECUTION.value,
            verification_confidence=Decimal("0.95"),  # Very high confidence in tests
            user_feedback=f"Tests: {tests_passed}/{tests_total} passed. {test_output or ''}",
            verified_at=datetime.utcnow()
        )

    async def _verify_code_analysis(
        self,
        execution: AgentExecution,
        lint_score: Optional[float] = None,
        complexity_score: Optional[float] = None,
        security_score: Optional[float] = None
    ) -> RewardScore:
        """Verify based on static code analysis."""

        # Average of available scores
        scores = [s for s in [lint_score, complexity_score, security_score] if s is not None]
        score = sum(scores) / len(scores) if scores else 0.5

        return RewardScore(
            execution_id=execution.id,
            reward_score=Decimal(str(score)),
            automated_score=Decimal(str(score)),
            verification_method=VerificationMethod.CODE_ANALYSIS.value,
            verification_confidence=Decimal("0.85"),
            user_feedback=f"Code quality: {score:.2%}",
            verified_at=datetime.utcnow()
        )

    async def _verify_business_metrics(
        self,
        execution: AgentExecution,
        revenue_impact_usd: Optional[float] = None,
        conversion_rate: Optional[float] = None,
        retention_impact: Optional[float] = None
    ) -> RewardScore:
        """Verify based on business impact metrics."""

        # Normalize business metrics to 0-1 range
        # This is application-specific and should be tuned
        score = 0.5  # Default neutral

        if revenue_impact_usd is not None and revenue_impact_usd > 0:
            # Positive revenue impact = positive reward
            # Cap at $10K for normalization
            score = min(revenue_impact_usd / 10000.0, 1.0)
        elif conversion_rate is not None:
            score = conversion_rate
        elif retention_impact is not None:
            score = retention_impact

        return RewardScore(
            execution_id=execution.id,
            reward_score=Decimal(str(score)),
            business_score=Decimal(str(score)),
            verification_method=VerificationMethod.BUSINESS_METRICS.value,
            verification_confidence=Decimal("0.75"),  # Lower confidence due to attribution challenges
            revenue_impact_usd=revenue_impact_usd,
            conversion_impact=Decimal(str(conversion_rate)) if conversion_rate else None,
            verified_at=datetime.utcnow()
        )

    async def _verify_automated_check(
        self,
        execution: AgentExecution,
        check_results: Dict[str, bool]
    ) -> RewardScore:
        """Verify based on automated checks (e.g., formatting, compilation)."""

        # Pass rate of all checks
        passed = sum(1 for result in check_results.values() if result)
        total = len(check_results)
        score = passed / total if total > 0 else 0.0

        return RewardScore(
            execution_id=execution.id,
            reward_score=Decimal(str(score)),
            automated_score=Decimal(str(score)),
            verification_method=VerificationMethod.AUTOMATED_CHECK.value,
            verification_confidence=Decimal("0.9"),
            user_feedback=f"Checks: {passed}/{total} passed",
            verified_at=datetime.utcnow()
        )

    async def compute_composite_reward(
        self,
        execution_id: uuid.UUID
    ) -> Decimal:
        """
        Compute a composite reward score from all verification methods.

        Uses weighted average of all available reward scores.
        """
        # Get all reward scores for this execution
        scores = await self._get_reward_scores(execution_id)

        if not scores:
            return Decimal("0.5")  # Default neutral

        # Weight by confidence
        weighted_sum = sum(
            score.reward_score * score.verification_confidence
            for score in scores
        )
        confidence_sum = sum(score.verification_confidence for score in scores)

        composite_reward = weighted_sum / confidence_sum if confidence_sum > 0 else Decimal("0.5")

        return composite_reward

    async def _get_execution(self, execution_id: uuid.UUID) -> AgentExecution:
        """Get execution from database."""
        async with self.db.session() as session:
            result = await session.execute(
                select(AgentExecution).where(AgentExecution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            return execution

    async def _save_reward_score(self, reward_score: RewardScore):
        """Save reward score to database."""
        async with self.db.session() as session:
            session.add(reward_score)
            await session.commit()

    async def _get_reward_scores(self, execution_id: uuid.UUID) -> List[RewardScore]:
        """Get all reward scores for an execution."""
        async with self.db.session() as session:
            result = await session.execute(
                select(RewardScore).where(RewardScore.execution_id == execution_id)
            )
            return result.scalars().all()
```

This is part 1 of the RLVR implementation. Should I continue with:
1. Training data collection pipeline
2. Fine-tuning orchestrator
3. API endpoints for feedback
4. Background workers for automated verification
5. Integration examples

Let me know if you want me to continue with the full implementation!
