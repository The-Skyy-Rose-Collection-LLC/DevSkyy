"""
ReAct (Reasoning + Acting) Pattern for AI Agents - 2025 Best Practices

Per IBM and LangChain 2025 Documentation:
- Combines chain-of-thought (CoT) reasoning with external tool use
- Reasoning → Action → Observation cycles
- Reduces hallucinations through grounded responses
- State machine architecture for reliability

References:
- https://www.ibm.com/think/topics/react-agent
- https://www.digitalapplied.com/blog/langchain-ai-agents-guide-2025
- https://www.marktechpost.com/2025/08/09/9-agentic-ai-workflow-patterns-transforming-ai-agents-in-2025/
- Original paper: "ReACT: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2023)
- Per Truth Protocol Rule #1: Never guess - Pattern from peer-reviewed research

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .structured_output import (
    AgentAction,
    AgentObservation,
    AgentThought,
    ReActStep,
)

logger = logging.getLogger(__name__)

# Configuration via environment (per Truth Protocol Rule #15)
MAX_REASONING_STEPS = int(os.getenv("REACT_MAX_STEPS", "10"))
THOUGHT_CONFIDENCE_THRESHOLD = float(os.getenv("REACT_CONFIDENCE_THRESHOLD", "0.7"))


class ReActState(str, Enum):
    """
    State machine states for ReAct agent.

    Per 2025 best practices: "Explicit states, transitions, retries,
    timeouts, and human-in-the-loop pauses greatly improve reliability."
    """

    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_HUMAN = "waiting_human"  # Human-in-the-loop pause


class ReActTransition(str, Enum):
    """Valid state transitions."""

    START = "start"
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    FINISH = "finish"
    FAIL = "fail"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class ReActContext:
    """
    Context maintained across ReAct cycles.

    Per Anthropic: "Good context engineering means finding the smallest
    possible set of high-signal tokens."
    """

    task: str
    steps: list[ReActStep] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    final_answer: str | None = None
    state: ReActState = ReActState.IDLE
    start_time: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def get_reasoning_trace(self) -> str:
        """Get formatted reasoning trace for context."""
        lines = [f"Task: {self.task}", ""]

        for i, step in enumerate(self.steps, 1):
            lines.append(f"Step {i}:")
            lines.append(f"  Thought: {step.thought.thought}")
            if step.action:
                lines.append(f"  Action: {step.action.tool_name}({json.dumps(step.action.parameters)})")
            if step.observation:
                result_str = str(step.observation.result)[:200]
                lines.append(f"  Observation: {result_str}")
            lines.append("")

        return "\n".join(lines)


class ChainOfThought:
    """
    Chain-of-Thought (CoT) reasoning implementation.

    Per Anthropic: "Giving Claude time to think through its response
    before producing the final answer leads to better performance."
    """

    @staticmethod
    def create_thought_prompt(task: str, context: ReActContext) -> str:
        """
        Create a prompt that encourages step-by-step thinking.

        Implements "Think step by step" pattern.
        """
        prompt_parts = [
            "# Task",
            task,
            "",
            "# Instructions",
            "Think step by step about this task. For each step:",
            "1. State what you're considering",
            "2. Explain your reasoning",
            "3. Decide on an action or conclude",
            "",
        ]

        if context.steps:
            prompt_parts.extend([
                "# Previous Reasoning",
                context.get_reasoning_trace(),
                "",
            ])

        prompt_parts.extend([
            "# Your Response",
            "Provide your next thought in this JSON format:",
            "```json",
            "{",
            '  "step": <step_number>,',
            '  "thought": "<your reasoning>",',
            '  "confidence": <0.0-1.0>,',
            '  "needs_action": true/false,',
            '  "is_final": true/false',
            "}",
            "```",
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def parse_thought(response: str) -> AgentThought | None:
        """Parse thought from LLM response."""
        import re

        # Extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            return None

        try:
            data = json.loads(json_match.group())
            return AgentThought(
                step=data.get("step", 1),
                thought=data.get("thought", ""),
                confidence=data.get("confidence", 0.8),
            )
        except (json.JSONDecodeError, KeyError):
            return None


class ActionSelector:
    """
    Selects and formats actions based on reasoning.

    Per ReAct pattern: After reasoning, determine the appropriate action.
    """

    def __init__(self):
        self.available_tools: dict[str, dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable | None = None,
    ):
        """Register an available tool."""
        self.available_tools[name] = {
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def create_action_prompt(
        self,
        thought: AgentThought,
        context: ReActContext,
    ) -> str:
        """Create prompt for action selection."""
        tools_desc = []
        for name, tool in self.available_tools.items():
            tools_desc.append(f"- **{name}**: {tool['description']}")
            tools_desc.append(f"  Parameters: {json.dumps(tool['parameters'])}")

        return f"""
Based on your reasoning:
"{thought.thought}"

Select an action from available tools:

{chr(10).join(tools_desc)}

Or respond with "FINAL_ANSWER" if you can answer without tools.

Respond in JSON format:
```json
{{
  "tool_name": "<tool_name or FINAL_ANSWER>",
  "parameters": {{}},
  "reasoning": "<why this action>"
}}
```
"""

    def parse_action(self, response: str) -> AgentAction | None:
        """Parse action from LLM response."""
        import re

        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            return None

        try:
            data = json.loads(json_match.group())
            return AgentAction(
                tool_name=data.get("tool_name", ""),
                parameters=data.get("parameters", {}),
                reasoning=data.get("reasoning", ""),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    async def execute_action(self, action: AgentAction) -> AgentObservation:
        """Execute an action and return observation."""
        import time

        start_time = time.time()

        if action.tool_name not in self.available_tools:
            return AgentObservation(
                tool_name=action.tool_name,
                result=None,
                success=False,
                error_message=f"Unknown tool: {action.tool_name}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        tool = self.available_tools[action.tool_name]
        handler = tool.get("handler")

        if handler is None:
            return AgentObservation(
                tool_name=action.tool_name,
                result=None,
                success=False,
                error_message=f"No handler for tool: {action.tool_name}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        try:
            # Execute handler
            if callable(handler):
                import asyncio

                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**action.parameters)
                else:
                    result = handler(**action.parameters)
            else:
                result = None

            return AgentObservation(
                tool_name=action.tool_name,
                result=result,
                success=True,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return AgentObservation(
                tool_name=action.tool_name,
                result=None,
                success=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )


class ReActAgent:
    """
    Full ReAct agent implementation.

    Implements the Reasoning → Action → Observation cycle with:
    - State machine architecture
    - Chain-of-thought reasoning
    - Tool execution
    - Human-in-the-loop support

    Per IBM: "ReAct's combination of CoT with connection to external
    information sources significantly reduces hallucinations."
    """

    # Valid state transitions
    TRANSITIONS = {
        ReActState.IDLE: [ReActTransition.START],
        ReActState.THINKING: [ReActTransition.ACT, ReActTransition.FINISH, ReActTransition.FAIL, ReActTransition.PAUSE],
        ReActState.ACTING: [ReActTransition.OBSERVE, ReActTransition.FAIL],
        ReActState.OBSERVING: [ReActTransition.THINK, ReActTransition.FINISH, ReActTransition.FAIL],
        ReActState.WAITING_HUMAN: [ReActTransition.RESUME, ReActTransition.FAIL],
        ReActState.COMPLETED: [],
        ReActState.FAILED: [],
    }

    def __init__(
        self,
        llm_caller: Callable | None = None,
        max_steps: int = MAX_REASONING_STEPS,
    ):
        """
        Initialize ReAct agent.

        Args:
            llm_caller: Async function to call LLM (prompt -> response)
            max_steps: Maximum reasoning steps before stopping
        """
        self.llm_caller = llm_caller
        self.max_steps = max_steps
        self.cot = ChainOfThought()
        self.action_selector = ActionSelector()
        self.context: ReActContext | None = None

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable | None = None,
    ):
        """Register a tool for the agent to use."""
        self.action_selector.register_tool(name, description, parameters, handler)

    def _validate_transition(self, transition: ReActTransition) -> bool:
        """Validate state transition is allowed."""
        if self.context is None:
            return transition == ReActTransition.START

        allowed = self.TRANSITIONS.get(self.context.state, [])
        return transition in allowed

    def _apply_transition(self, transition: ReActTransition):
        """Apply state transition."""
        if not self._validate_transition(transition):
            raise ValueError(
                f"Invalid transition {transition} from state {self.context.state if self.context else 'None'}"
            )

        state_map = {
            ReActTransition.START: ReActState.THINKING,
            ReActTransition.THINK: ReActState.THINKING,
            ReActTransition.ACT: ReActState.ACTING,
            ReActTransition.OBSERVE: ReActState.OBSERVING,
            ReActTransition.FINISH: ReActState.COMPLETED,
            ReActTransition.FAIL: ReActState.FAILED,
            ReActTransition.PAUSE: ReActState.WAITING_HUMAN,
            ReActTransition.RESUME: ReActState.THINKING,
        }

        if self.context:
            self.context.state = state_map.get(transition, self.context.state)

    async def run(self, task: str) -> ReActContext:
        """
        Run the ReAct loop for a task.

        Returns the context with full reasoning trace.
        """
        # Initialize context
        self.context = ReActContext(task=task)
        self._apply_transition(ReActTransition.START)

        logger.info(f"Starting ReAct agent for task: {task[:100]}...")

        while self.context.state not in [ReActState.COMPLETED, ReActState.FAILED]:
            # Check step limit
            if self.context.step_count >= self.max_steps:
                logger.warning(f"Max steps ({self.max_steps}) reached")
                self._apply_transition(ReActTransition.FAIL)
                break

            try:
                if self.context.state == ReActState.THINKING:
                    await self._thinking_step()
                elif self.context.state == ReActState.ACTING:
                    await self._acting_step()
                elif self.context.state == ReActState.OBSERVING:
                    await self._observing_step()
                elif self.context.state == ReActState.WAITING_HUMAN:
                    # In real implementation, this would wait for human input
                    logger.info("Waiting for human input...")
                    break

            except Exception as e:
                logger.error(f"ReAct loop error: {e}")
                self._apply_transition(ReActTransition.FAIL)
                self.context.metadata["error"] = str(e)

        logger.info(
            f"ReAct completed with state: {self.context.state}, "
            f"steps: {self.context.step_count}"
        )

        return self.context

    async def _thinking_step(self):
        """Execute thinking step."""
        if not self.llm_caller:
            raise ValueError("LLM caller not configured")

        # Generate thought prompt
        prompt = self.cot.create_thought_prompt(self.context.task, self.context)

        # Call LLM
        response = await self.llm_caller(prompt)

        # Parse thought
        thought = self.cot.parse_thought(response)

        if thought is None:
            # Fallback: create basic thought
            thought = AgentThought(
                step=self.context.step_count + 1,
                thought=response[:500],
                confidence=0.5,
            )

        # Create step
        step = ReActStep(thought=thought)

        # Decide next transition
        if thought.confidence >= THOUGHT_CONFIDENCE_THRESHOLD:
            # Check if we need action or can finish
            if "FINAL_ANSWER" in response.upper() or thought.thought.lower().startswith("final answer"):
                step.is_final = True
                self.context.final_answer = thought.thought
                self.context.steps.append(step)
                self._apply_transition(ReActTransition.FINISH)
            else:
                self.context.steps.append(step)
                self._apply_transition(ReActTransition.ACT)
        else:
            # Low confidence, continue thinking
            self.context.steps.append(step)
            # Stay in thinking state but increment step

    async def _acting_step(self):
        """Execute acting step."""
        if not self.context.steps:
            self._apply_transition(ReActTransition.FAIL)
            return

        last_step = self.context.steps[-1]

        # Get action selection
        if not self.llm_caller:
            raise ValueError("LLM caller not configured")

        prompt = self.action_selector.create_action_prompt(
            last_step.thought, self.context
        )
        response = await self.llm_caller(prompt)

        action = self.action_selector.parse_action(response)

        if action is None:
            # Failed to parse action
            self._apply_transition(ReActTransition.FAIL)
            self.context.metadata["error"] = "Failed to parse action"
            return

        # Check for final answer
        if action.tool_name == "FINAL_ANSWER":
            self.context.final_answer = action.reasoning
            last_step.is_final = True
            self._apply_transition(ReActTransition.FINISH)
            return

        # Execute action
        observation = await self.action_selector.execute_action(action)

        # Update step
        last_step.action = action
        last_step.observation = observation

        self._apply_transition(ReActTransition.OBSERVE)

    async def _observing_step(self):
        """Process observation and decide next step."""
        if not self.context.steps:
            self._apply_transition(ReActTransition.FAIL)
            return

        last_step = self.context.steps[-1]

        if last_step.observation:
            # Add observation to context
            obs_str = str(last_step.observation.result)[:500]
            self.context.observations.append(obs_str)

            if last_step.observation.success:
                # Continue reasoning
                self._apply_transition(ReActTransition.THINK)
            else:
                # Action failed, try again or fail
                if self.context.step_count < self.max_steps:
                    self._apply_transition(ReActTransition.THINK)
                else:
                    self._apply_transition(ReActTransition.FAIL)
        else:
            self._apply_transition(ReActTransition.THINK)

    def get_result(self) -> dict[str, Any]:
        """Get the final result of the ReAct run."""
        if self.context is None:
            return {"status": "not_started"}

        return {
            "status": self.context.state.value,
            "task": self.context.task,
            "final_answer": self.context.final_answer,
            "steps": self.context.step_count,
            "reasoning_trace": self.context.get_reasoning_trace(),
            "duration_ms": (datetime.utcnow() - self.context.start_time).total_seconds() * 1000,
            "metadata": self.context.metadata,
        }


# Factory function
def create_react_agent(
    llm_caller: Callable | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_steps: int = MAX_REASONING_STEPS,
) -> ReActAgent:
    """
    Create a configured ReAct agent.

    Args:
        llm_caller: Async function to call LLM
        tools: List of tool definitions
        max_steps: Maximum reasoning steps

    Returns:
        Configured ReActAgent
    """
    agent = ReActAgent(llm_caller=llm_caller, max_steps=max_steps)

    if tools:
        for tool in tools:
            agent.register_tool(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {}),
                handler=tool.get("handler"),
            )

    return agent


__all__ = [
    "ActionSelector",
    "ChainOfThought",
    "ReActAgent",
    "ReActContext",
    "ReActState",
    "ReActTransition",
    "create_react_agent",
]
