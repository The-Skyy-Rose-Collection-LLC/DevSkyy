"""
RLVR System Usage Example

This example demonstrates how to use the Reinforcement Learning with Verifiable
Rewards (RLVR) system to continuously improve DevSkyy agents.

Complete workflow:
1. Execute an agent
2. Collect feedback (user, automated tests, code analysis)
3. Collect training data periodically
4. Fine-tune the agent
5. Deploy improved agent
"""

from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ml.rlvr.fine_tuning_orchestrator import FineTuningOrchestrator
from ml.rlvr.reward_verifier import RewardVerifier, VerificationMethod
from ml.rlvr.training_collector import TrainingDataCollector


# ============================================================================
# STEP 1: SIMULATE AGENT EXECUTION
# ============================================================================


async def simulate_agent_execution(session: AsyncSession) -> uuid.UUID:
    """
    Simulate an agent execution.
    In production, this would be your actual agent execution.
    """
    agent_id = uuid.UUID("your-agent-id-here")  # Replace with real agent ID
    execution_id = uuid.uuid4()

    # Insert execution record
    query = """
        INSERT INTO agent_executions (
            id, agent_id, agent_version, input_prompt, output_completion,
            execution_time_ms, tokens_used, cost_usd, status, created_at
        ) VALUES (
            :id, :agent_id, :version, :prompt, :completion,
            :time_ms, :tokens, :cost, :status, :created_at
        )
    """

    await session.execute(
        query,
        {
            "id": execution_id,
            "agent_id": agent_id,
            "version": 1,
            "prompt": "Review this Python code for security issues:\n\ndef process_user_input(data):\n    return eval(data)",
            "completion": "❌ CRITICAL SECURITY ISSUE: Never use eval() with user input!\n\nRecommendation:\nimport ast\ndef process_user_input(data):\n    return ast.literal_eval(data)",
            "time_ms": 1234,
            "tokens": 150,
            "cost": 0.0025,
            "status": "success",
            "created_at": datetime.utcnow(),
        },
    )
    await session.commit()

    return execution_id


# ============================================================================
# STEP 2: COLLECT USER FEEDBACK
# ============================================================================


async def collect_user_feedback(session: AsyncSession, execution_id: uuid.UUID, user_id: uuid.UUID):
    """
    User provides thumbs up/down feedback on agent output.
    """
    verifier = RewardVerifier(session)

    reward = await verifier.verify_execution(
        execution_id=execution_id,
        verification_method=VerificationMethod.USER_FEEDBACK,
        thumbs_up=True,  # User liked the response
        user_feedback="Great catch on the security issue!",
        user_id=user_id,
    )

    return reward


# ============================================================================
# STEP 3: RUN AUTOMATED TESTS
# ============================================================================


async def run_automated_tests(session: AsyncSession, execution_id: uuid.UUID):
    """
    Run automated tests to verify agent output quality.
    """
    verifier = RewardVerifier(session)

    # Simulate running tests on the suggested code
    tests_passed = 8
    tests_total = 10

    reward = await verifier.verify_execution(
        execution_id=execution_id,
        verification_method=VerificationMethod.TEST_EXECUTION,
        tests_passed=tests_passed,
        tests_total=tests_total,
        test_output="2 edge cases failed, but core functionality works",
    )

    return reward


# ============================================================================
# STEP 4: CODE QUALITY ANALYSIS
# ============================================================================


async def analyze_code_quality(session: AsyncSession, execution_id: uuid.UUID):
    """
    Run code quality analysis tools (linting, complexity, security).
    """
    verifier = RewardVerifier(session)

    reward = await verifier.verify_execution(
        execution_id=execution_id,
        verification_method=VerificationMethod.CODE_ANALYSIS,
        lint_score=0.95,  # 95% - excellent
        complexity_score=0.85,  # 85% - good
        security_score=1.0,  # 100% - perfect (caught security issue!)
    )

    return reward


# ============================================================================
# STEP 5: COMPUTE COMPOSITE REWARD
# ============================================================================


async def compute_composite_reward(session: AsyncSession, execution_id: uuid.UUID):
    """
    Combine all reward scores into a single composite score.
    """
    verifier = RewardVerifier(session)

    composite = await verifier.compute_composite_reward(execution_id)

    return composite


# ============================================================================
# STEP 6: COLLECT TRAINING DATA
# ============================================================================


async def collect_training_data(session: AsyncSession, agent_id: uuid.UUID):
    """
    Collect high-quality training examples from verified executions.
    """
    collector = TrainingDataCollector(session)

    result = await collector.collect_training_data(agent_id=agent_id, max_examples=1000, days_lookback=30)


    return result


# ============================================================================
# STEP 7: CHECK TRAINING READINESS
# ============================================================================


async def check_training_readiness(session: AsyncSession, agent_id: uuid.UUID):
    """
    Check if agent has enough training data for fine-tuning.
    """
    collector = TrainingDataCollector(session)

    stats = await collector.get_collection_stats(agent_id)


    for _example_type, _type_stats in stats["by_type"].items():
        pass

    return stats


# ============================================================================
# STEP 8: START FINE-TUNING
# ============================================================================


async def start_fine_tuning(session: AsyncSession, agent_id: uuid.UUID):
    """
    Start a fine-tuning run for the agent.
    """
    orchestrator = FineTuningOrchestrator(session)


    result = await orchestrator.start_fine_tuning(
        agent_id=agent_id,
        provider="openai",  # or 'anthropic' for prompt optimization
        base_model="gpt-3.5-turbo",
        hyperparameters={"epochs": 3, "learning_rate": "auto"},
    )


    return result


# ============================================================================
# STEP 9: DEPLOY FINE-TUNED AGENT
# ============================================================================


async def deploy_fine_tuned_agent(session: AsyncSession, run_id: uuid.UUID):
    """
    Deploy the fine-tuned model to production.
    """
    orchestrator = FineTuningOrchestrator(session)


    result = await orchestrator.deploy_fine_tuned_agent(
        run_id=run_id, deploy_to_production=True  # Set to False for staging first
    )


    return result


# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================


async def complete_workflow_example():
    """
    Run the complete RLVR workflow from execution to deployment.
    """
    # Setup database connection
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/devskyy")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:

        # Replace with your actual agent ID
        agent_id = uuid.UUID("your-agent-id-here")
        user_id = uuid.UUID("your-user-id-here")

        # Step 1: Execute agent
        execution_id = await simulate_agent_execution(session)

        # Step 2: Collect user feedback
        await collect_user_feedback(session, execution_id, user_id)

        # Step 3: Run automated tests
        await run_automated_tests(session, execution_id)

        # Step 4: Code quality analysis
        await analyze_code_quality(session, execution_id)

        # Step 5: Composite reward
        await compute_composite_reward(session, execution_id)

        # Step 6: Collect training data (after many executions)
        await collect_training_data(session, agent_id)

        # Step 7: Check if ready for training
        stats = await check_training_readiness(session, agent_id)

        if stats["ready_for_training"]:
            # Step 8: Start fine-tuning
            await start_fine_tuning(session, agent_id)

            # In production, you'd wait for fine-tuning to complete
            # Then deploy with the run_id
            # run_id = fine_tune_result['run_id']
            # await deploy_fine_tuned_agent(session, run_id)
        else:
            pass



# ============================================================================
# API ENDPOINT USAGE EXAMPLE
# ============================================================================


def api_usage_example():
    """
    Example API calls for RLVR system.
    """


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":

    # Show API examples
    api_usage_example()

    # To run complete workflow:
    # asyncio.run(complete_workflow_example())
