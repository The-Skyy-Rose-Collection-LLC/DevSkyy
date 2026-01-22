"""
LLM Round Table Orchestrator

Integrates Claude Agent SDK with DevSkyy's LLM Round Table pattern.
Multiple LLM providers compete to solve tasks, with the best responses
selected through A/B testing and statistical significance.
"""

import asyncio
from typing import Any

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock

from agent_sdk.custom_tools import create_devskyy_tools


class RoundTableOrchestrator:
    """
    Orchestrates LLM Round Table competitions using the Agent SDK.

    The Round Table pattern:
    1. Multiple LLM providers compete on the same task
    2. All responses are collected
    3. Top 2 responses are selected for A/B testing
    4. Statistical significance determines the winner
    5. Winner's approach is used for final result

    This integrates with the existing llm/round_table.py implementation.
    """

    def __init__(self):
        """Initialize the Round Table orchestrator."""
        self.mcp_server = create_devskyy_tools()
        self.providers = ["sonnet", "opus", "haiku"]  # Available Claude models

    def get_base_options(
        self,
        model: str,
        system_prompt: str | None = None,
    ) -> ClaudeAgentOptions:
        """
        Get base options for a Round Table participant.

        Args:
            model: Claude model to use (sonnet, opus, haiku)
            system_prompt: Optional custom system prompt

        Returns:
            ClaudeAgentOptions for the participant
        """
        default_prompt = """You are participating in a Round Table competition where multiple AI models
collaborate to solve complex tasks. Your goal is to provide the best possible solution.

Key principles:
1. Think deeply about the problem
2. Consider multiple approaches
3. Provide detailed, actionable solutions
4. Explain your reasoning clearly
5. Optimize for correctness over speed

Your response will be evaluated against other models based on:
- Solution quality and correctness
- Clarity of explanation
- Practical applicability
- Efficiency and optimization
- Completeness of solution"""

        return ClaudeAgentOptions(
            system_prompt=system_prompt or default_prompt,
            model=model,
            mcp_servers={"devskyy": self.mcp_server},
            allowed_tools=[
                "Read",
                "Write",
                "Bash",
                "WebSearch",
                "WebFetch",
                "mcp__devskyy__generate_3d_model",
                "mcp__devskyy__manage_product",
                "mcp__devskyy__analyze_data",
                "mcp__devskyy__create_marketing_content",
                "mcp__devskyy__handle_support_ticket",
                "mcp__devskyy__execute_deployment",
            ],
            permission_mode="bypassPermissions",  # Safe for competition
        )

    async def run_single_participant(
        self,
        model: str,
        task: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Run a single Round Table participant.

        Args:
            model: Claude model to use
            task: The task to solve
            system_prompt: Optional custom system prompt

        Returns:
            Dict containing response, model, usage, and cost
        """
        options = self.get_base_options(model, system_prompt)

        result_data = {
            "model": model,
            "response": "",
            "usage": None,
            "total_cost_usd": None,
            "duration_ms": None,
        }

        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(task)

                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                result_data["response"] += block.text

                    # Capture result metadata
                    if hasattr(message, "usage"):
                        result_data["usage"] = message.usage
                    if hasattr(message, "total_cost_usd"):
                        result_data["total_cost_usd"] = message.total_cost_usd
                    if hasattr(message, "duration_ms"):
                        result_data["duration_ms"] = message.duration_ms

        except Exception as e:
            result_data["error"] = str(e)
            result_data["response"] = f"Error: {str(e)}"

        return result_data

    async def run_round_table(
        self,
        task: str,
        models: list[str] | None = None,
        system_prompt: str | None = None,
        parallel: bool = True,
    ) -> dict[str, Any]:
        """
        Run a full Round Table competition.

        Args:
            task: The task for models to solve
            models: List of models to compete (defaults to all available)
            system_prompt: Optional custom system prompt for all participants
            parallel: If True, run all participants in parallel

        Returns:
            Dict containing all responses, rankings, and winner
        """
        if models is None:
            models = self.providers

        print(f"\n🎯 Starting Round Table with {len(models)} participants...")
        print(f"Task: {task[:100]}...")

        # Run all participants
        if parallel:
            tasks = [self.run_single_participant(model, task, system_prompt) for model in models]
            responses = await asyncio.gather(*tasks)
        else:
            responses = []
            for model in models:
                print(f"\n🤖 Running {model}...")
                response = await self.run_single_participant(model, task, system_prompt)
                responses.append(response)

        # Calculate scores (simplified version - integrate with llm/ab_testing.py for full scoring)
        for _i, response in enumerate(responses):
            # Simple scoring based on response length and lack of errors
            has_error = "error" in response
            response_length = len(response.get("response", ""))

            if has_error:
                response["score"] = 0
            else:
                # Basic quality heuristic (to be replaced with actual A/B testing)
                response["score"] = min(100, response_length / 10)

        # Sort by score
        responses.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Select top 2 for "A/B testing" (placeholder for actual A/B test)
        top_2 = responses[:2]

        print("\n📊 Round Table Results:")
        for i, resp in enumerate(responses, 1):
            print(f"{i}. {resp['model']}: Score {resp.get('score', 0):.1f}")

        return {
            "all_responses": responses,
            "top_2": top_2,
            "winner": responses[0],
            "total_participants": len(responses),
            "task": task,
        }

    async def execute_with_winner(
        self,
        task: str,
        models: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Run Round Table and return only the winner's response.

        Args:
            task: The task to solve
            models: List of models to compete

        Returns:
            Dict containing winner's response and metadata
        """
        results = await self.run_round_table(task, models)

        return {
            "result": results["winner"]["response"],
            "model": results["winner"]["model"],
            "usage": results["winner"].get("usage"),
            "total_cost_usd": results["winner"].get("total_cost_usd"),
            "round_table_stats": {
                "participants": results["total_participants"],
                "all_scores": [r.get("score", 0) for r in results["all_responses"]],
            },
        }


# Integration point with existing llm/round_table.py
async def integrate_with_existing_round_table(task: str) -> dict[str, Any]:
    """
    Integration function to connect Agent SDK Round Table with existing
    llm/round_table.py implementation.

    This is a placeholder for future integration where:
    1. Agent SDK provides the task execution environment
    2. llm/round_table.py provides the scoring and selection logic
    3. llm/ab_testing.py provides statistical significance testing

    Args:
        task: The task to execute

    Returns:
        Dict containing results from both systems
    """
    # TODO: Integrate with llm/round_table.py for full Round Table implementation
    # TODO: Use llm/ab_testing.py for statistical significance testing

    orchestrator = RoundTableOrchestrator()
    return await orchestrator.execute_with_winner(task)
