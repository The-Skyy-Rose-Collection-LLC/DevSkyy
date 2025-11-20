"""
Fine-Tuning Orchestration System

Manages the end-to-end fine-tuning process for agents across different model providers.
"""

import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
import openai
from anthropic import Anthropic

from .training_collector import TrainingDataCollector

logger = logging.getLogger(__name__)


class FineTuningOrchestrator:
    """
    Orchestrates fine-tuning runs for DevSkyy agents.

    Supports:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic Claude (prompt optimization)
    - Local models (LoRA fine-tuning)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.collector = TrainingDataCollector(session)

        # API clients
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def start_fine_tuning(
        self,
        agent_id: uuid.UUID,
        provider: str = "openai",
        base_model: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a fine-tuning run for an agent.

        Args:
            agent_id: Agent to fine-tune
            provider: 'openai', 'anthropic', or 'local'
            base_model: Base model to fine-tune (provider-specific)
            hyperparameters: Training hyperparameters

        Returns:
            Fine-tuning run details
        """
        # Check if enough training data
        stats = await self.collector.get_collection_stats(agent_id)
        if not stats['ready_for_training']:
            raise ValueError(
                f"Not enough training data. "
                f"Need {self.collector.min_examples_per_agent}, "
                f"have {stats['total_examples']}"
            )

        # Create fine-tuning run record
        run_id = await self._create_fine_tuning_run(
            agent_id, provider, base_model, stats['total_examples']
        )

        # Start fine-tuning based on provider
        try:
            if provider == "openai":
                result = await self._fine_tune_openai(
                    run_id, agent_id, base_model, hyperparameters
                )
            elif provider == "anthropic":
                result = await self._optimize_anthropic_prompt(
                    run_id, agent_id
                )
            elif provider == "local":
                result = await self._fine_tune_local(
                    run_id, agent_id, base_model, hyperparameters
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            # Update run with results
            await self._update_run_status(
                run_id, "completed", result
            )

            return result

        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            await self._update_run_status(
                run_id, "failed", {"error": str(e)}
            )
            raise

    async def _fine_tune_openai(
        self,
        run_id: uuid.UUID,
        agent_id: uuid.UUID,
        base_model: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune using OpenAI's fine-tuning API.

        Supports: gpt-3.5-turbo, gpt-4
        """
        base_model = base_model or "gpt-3.5-turbo"
        hyperparameters = hyperparameters or {}

        # Export training data
        training_file_path = f"/tmp/training_{agent_id}.jsonl"
        await self.collector.export_for_openai_finetuning(
            agent_id, training_file_path
        )

        # Upload training file
        with open(training_file_path, "rb") as f:
            training_file = self.openai_client.files.create(
                file=f,
                purpose="fine-tune"
            )

        # Create fine-tuning job
        fine_tuning_job = self.openai_client.fine_tuning.jobs.create(
            training_file=training_file.id,
            model=base_model,
            hyperparameters={
                "n_epochs": hyperparameters.get("epochs", 3),
                "learning_rate_multiplier": hyperparameters.get("learning_rate", "auto"),
            }
        )

        # Update run with job ID
        await self._update_run_provider_id(run_id, fine_tuning_job.id)

        # Poll for completion
        logger.info(f"OpenAI fine-tuning job created: {fine_tuning_job.id}")
        await self._poll_openai_job(run_id, fine_tuning_job.id)

        # Get final job status
        final_job = self.openai_client.fine_tuning.jobs.retrieve(fine_tuning_job.id)

        return {
            "provider": "openai",
            "job_id": fine_tuning_job.id,
            "fine_tuned_model": final_job.fine_tuned_model,
            "status": final_job.status,
            "trained_tokens": final_job.trained_tokens,
        }

    async def _poll_openai_job(self, run_id: uuid.UUID, job_id: str):
        """Poll OpenAI job until completion."""
        while True:
            job = self.openai_client.fine_tuning.jobs.retrieve(job_id)

            # Update progress
            await self._update_run_progress(run_id, self._estimate_progress(job.status))

            if job.status in ["succeeded", "failed", "cancelled"]:
                break

            await asyncio.sleep(60)  # Check every minute

    def _estimate_progress(self, status: str) -> int:
        """Estimate progress percentage from job status."""
        status_to_progress = {
            "validating_files": 10,
            "queued": 20,
            "running": 50,
            "succeeded": 100,
            "failed": 0,
            "cancelled": 0
        }
        return status_to_progress.get(status, 0)

    async def _optimize_anthropic_prompt(
        self,
        run_id: uuid.UUID,
        agent_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Optimize Anthropic Claude agent through prompt refinement.

        Since Anthropic doesn't offer fine-tuning, we optimize through:
        1. Few-shot learning (add best examples to prompt)
        2. Prompt engineering (refine system prompt)
        3. Instruction tuning (improve task instructions)
        """
        # Get best examples
        query = """
            SELECT prompt, completion, reward_score
            FROM training_examples
            WHERE agent_id = :agent_id
                AND example_type = 'positive'
            ORDER BY reward_score DESC
            LIMIT 10
        """

        result = await self.session.execute(query, {"agent_id": agent_id})
        best_examples = [
            {"input": row[0], "output": row[1], "score": float(row[2])}
            for row in result.fetchall()
        ]

        # Get agent's current prompt
        agent_query = "SELECT base_prompt FROM agents WHERE id = :agent_id"
        agent_result = await self.session.execute(agent_query, {"agent_id": agent_id})
        current_prompt = agent_result.scalar()

        # Generate optimized prompt using Claude
        optimization_prompt = f"""
You are a prompt engineering expert. Optimize the following agent prompt based on successful examples.

Current Prompt:
{current_prompt}

Top 10 Successful Examples:
{self._format_examples(best_examples)}

Instructions:
1. Analyze what makes the successful examples work well
2. Identify patterns in high-quality outputs
3. Refine the system prompt to encourage these patterns
4. Keep the core functionality but improve clarity and effectiveness
5. Add few-shot examples if beneficial

Return ONLY the optimized prompt, nothing else.
"""

        response = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            messages=[{"role": "user", "content": optimization_prompt}]
        )

        optimized_prompt = response.content[0].text

        # Update agent prompt
        update_query = """
            UPDATE agents
            SET base_prompt = :optimized_prompt,
                version = version + 1,
                updated_at = :updated_at
            WHERE id = :agent_id
        """

        await self.session.execute(update_query, {
            "optimized_prompt": optimized_prompt,
            "updated_at": datetime.utcnow(),
            "agent_id": agent_id
        })
        await self.session.commit()

        return {
            "provider": "anthropic",
            "method": "prompt_optimization",
            "examples_used": len(best_examples),
            "optimized_prompt": optimized_prompt,
        }

    async def _fine_tune_local(
        self,
        run_id: uuid.UUID,
        agent_id: uuid.UUID,
        base_model: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune a local open-source model using LoRA.

        Supports: Llama, Mistral, and other HuggingFace models
        """
        # This would integrate with your local fine-tuning infrastructure
        # Using libraries like: transformers, peft, trl

        # For now, return placeholder
        # TODO: Implement full local fine-tuning pipeline
        return {
            "provider": "local",
            "status": "not_implemented",
            "message": "Local fine-tuning coming in next version"
        }

    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """Format examples for prompt optimization."""
        formatted = []
        for i, ex in enumerate(examples, 1):
            formatted.append(
                f"\nExample {i} (Score: {ex['score']:.2f}):\n"
                f"Input: {ex['input'][:200]}...\n"
                f"Output: {ex['output'][:200]}..."
            )
        return "\n".join(formatted)

    async def _create_fine_tuning_run(
        self,
        agent_id: uuid.UUID,
        provider: str,
        base_model: Optional[str],
        training_count: int
    ) -> uuid.UUID:
        """Create a fine-tuning run record."""
        run_id = uuid.uuid4()

        query = """
            INSERT INTO fine_tuning_runs (
                id, agent_id, base_model, training_examples_count,
                provider, status, progress_percentage, started_at, created_at
            ) VALUES (
                :id, :agent_id, :base_model, :training_count,
                :provider, :status, :progress, :started_at, :created_at
            )
        """

        await self.session.execute(query, {
            "id": run_id,
            "agent_id": agent_id,
            "base_model": base_model or "default",
            "training_count": training_count,
            "provider": provider,
            "status": "running",
            "progress": 0,
            "started_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        })
        await self.session.commit()

        return run_id

    async def _update_run_status(
        self,
        run_id: uuid.UUID,
        status: str,
        result: Dict[str, Any]
    ):
        """Update fine-tuning run status."""
        query = """
            UPDATE fine_tuning_runs
            SET status = :status,
                trained_model_id = :model_id,
                completed_at = :completed_at,
                error_message = :error_message,
                progress_percentage = :progress
            WHERE id = :run_id
        """

        await self.session.execute(query, {
            "run_id": run_id,
            "status": status,
            "model_id": result.get("fine_tuned_model") or result.get("trained_model_id"),
            "completed_at": datetime.utcnow() if status in ["completed", "failed"] else None,
            "error_message": result.get("error"),
            "progress": 100 if status == "completed" else 0
        })
        await self.session.commit()

    async def _update_run_provider_id(self, run_id: uuid.UUID, provider_job_id: str):
        """Update provider job ID."""
        query = """
            UPDATE fine_tuning_runs
            SET provider_job_id = :provider_job_id
            WHERE id = :run_id
        """

        await self.session.execute(query, {
            "run_id": run_id,
            "provider_job_id": provider_job_id
        })
        await self.session.commit()

    async def _update_run_progress(self, run_id: uuid.UUID, progress: int):
        """Update fine-tuning progress."""
        query = """
            UPDATE fine_tuning_runs
            SET progress_percentage = :progress
            WHERE id = :run_id
        """

        await self.session.execute(query, {
            "run_id": run_id,
            "progress": progress
        })
        await self.session.commit()

    async def deploy_fine_tuned_agent(
        self,
        run_id: uuid.UUID,
        deploy_to_production: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy a fine-tuned model to production.

        Args:
            run_id: Fine-tuning run ID
            deploy_to_production: Whether to deploy to production immediately

        Returns:
            Deployment details
        """
        # Get run details
        query = """
            SELECT agent_id, trained_model_id, provider
            FROM fine_tuning_runs
            WHERE id = :run_id AND status = 'completed'
        """

        result = await self.session.execute(query, {"run_id": run_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Fine-tuning run {run_id} not found or not completed")

        agent_id, model_id, provider = row

        # Update agent with new model
        update_query = """
            UPDATE agents
            SET model_name = :model_id,
                version = version + 1,
                updated_at = :updated_at
            WHERE id = :agent_id
        """

        await self.session.execute(update_query, {
            "model_id": model_id,
            "updated_at": datetime.utcnow(),
            "agent_id": agent_id
        })

        # Update fine-tuning run deployment status
        deployment_query = """
            UPDATE fine_tuning_runs
            SET deployed_at = :deployed_at,
                deployed_version = (SELECT version FROM agents WHERE id = :agent_id)
            WHERE id = :run_id
        """

        await self.session.execute(deployment_query, {
            "deployed_at": datetime.utcnow(),
            "agent_id": agent_id,
            "run_id": run_id
        })

        await self.session.commit()

        return {
            "agent_id": str(agent_id),
            "model_id": model_id,
            "provider": provider,
            "deployed_at": datetime.utcnow().isoformat(),
            "status": "deployed"
        }
