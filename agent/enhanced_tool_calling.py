"""
Enhanced Tool Calling for AI Agents - 2025 Best Practices

Per Bloomberg ACL 2025 Research:
- Joint optimization of agent instructions and tool descriptions
- 70% reduction in required tool calls
- 47% fewer redundant calls
- Three-stage refinement: Feedback → Suggestion → Context Refiner

References:
- https://www.bloomberg.com/company/stories/bloombergs-ai-engineers-introduce-an-improved-agent-tool-calling-methodology-acl-2025/
- https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms
- Per Truth Protocol Rule #1: Never guess - Methodology from peer-reviewed research

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Configuration via environment (per Truth Protocol Rule #15)
TOOL_CALL_HISTORY_LIMIT = int(os.getenv("TOOL_CALL_HISTORY_LIMIT", "100"))
REDUNDANCY_THRESHOLD = float(os.getenv("TOOL_REDUNDANCY_THRESHOLD", "0.8"))  # 80% similarity


class ToolCallEfficiency(str, Enum):
    """Efficiency classification for tool calls."""

    OPTIMAL = "optimal"  # Necessary and efficient
    REDUNDANT = "redundant"  # Duplicates previous call
    INEFFICIENT = "inefficient"  # Could be combined with other calls
    UNNECESSARY = "unnecessary"  # Not needed for task


@dataclass
class ToolCallMetrics:
    """Metrics for analyzing tool call efficiency."""

    total_calls: int = 0
    redundant_calls: int = 0
    failed_calls: int = 0
    average_response_time_ms: float = 0.0
    total_tokens_used: int = 0

    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (0-1)."""
        if self.total_calls == 0:
            return 1.0
        useful_calls = self.total_calls - self.redundant_calls
        return useful_calls / self.total_calls


class ToolDescription(BaseModel):
    """
    Enhanced tool description with optimization metadata.

    Per Bloomberg: "Systematically refining both agent instructions
    and tool descriptions improves efficiency."
    """

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    returns: dict[str, Any] = Field(default_factory=dict)

    # Optimization metadata
    typical_use_cases: list[str] = Field(default_factory=list)
    avoid_when: list[str] = Field(default_factory=list)
    combine_with: list[str] = Field(default_factory=list)  # Tools often used together
    prerequisites: list[str] = Field(default_factory=list)  # Tools that should run first
    cost_estimate: float = 1.0  # Relative cost (tokens, time)

    def to_prompt_format(self) -> str:
        """
        Generate optimized prompt format for tool description.

        Includes guidance to reduce unnecessary calls.
        """
        lines = [
            f"### {self.name}",
            f"{self.description}",
            "",
            "**Parameters:**",
            f"```json\n{json.dumps(self.parameters, indent=2)}\n```",
        ]

        if self.typical_use_cases:
            lines.append("\n**Use when:**")
            for case in self.typical_use_cases:
                lines.append(f"- {case}")

        if self.avoid_when:
            lines.append("\n**Avoid when:**")
            for case in self.avoid_when:
                lines.append(f"- {case}")

        if self.combine_with:
            lines.append(f"\n**Often used with:** {', '.join(self.combine_with)}")

        return "\n".join(lines)


@dataclass
class ToolCallRecord:
    """Record of a tool call for analysis."""

    tool_name: str
    parameters: dict[str, Any]
    result: Any
    success: bool
    timestamp: datetime
    response_time_ms: float
    tokens_used: int = 0
    efficiency: ToolCallEfficiency = ToolCallEfficiency.OPTIMAL
    feedback: str = ""


class FeedbackGenerator:
    """
    Stage 1 of Bloomberg methodology: Feedback Generator.

    Evaluates effectiveness and efficiency of tool calls.
    """

    def __init__(self):
        self.call_history: list[ToolCallRecord] = []

    def add_call(self, record: ToolCallRecord):
        """Add a tool call to history."""
        self.call_history.append(record)

        # Limit history size
        if len(self.call_history) > TOOL_CALL_HISTORY_LIMIT:
            self.call_history = self.call_history[-TOOL_CALL_HISTORY_LIMIT:]

    def analyze_call(self, record: ToolCallRecord) -> dict[str, Any]:
        """
        Analyze a tool call for efficiency.

        Returns feedback including:
        - Whether call was redundant
        - Suggestions for improvement
        - Efficiency classification
        """
        feedback = {
            "efficiency": ToolCallEfficiency.OPTIMAL,
            "is_redundant": False,
            "similar_previous_calls": [],
            "suggestions": [],
        }

        # Check for redundant calls
        for prev_call in reversed(self.call_history[-20:]):
            if prev_call.tool_name == record.tool_name:
                similarity = self._calculate_similarity(
                    prev_call.parameters, record.parameters
                )
                if similarity > REDUNDANCY_THRESHOLD:
                    feedback["is_redundant"] = True
                    feedback["efficiency"] = ToolCallEfficiency.REDUNDANT
                    feedback["similar_previous_calls"].append({
                        "timestamp": prev_call.timestamp.isoformat(),
                        "similarity": similarity,
                    })
                    feedback["suggestions"].append(
                        f"Consider reusing result from previous {record.tool_name} call"
                    )

        # Check for failed calls
        if not record.success:
            recent_failures = sum(
                1 for c in self.call_history[-10:]
                if c.tool_name == record.tool_name and not c.success
            )
            if recent_failures >= 3:
                feedback["suggestions"].append(
                    f"Tool {record.tool_name} has failed {recent_failures} times recently. "
                    "Consider alternative approach."
                )

        return feedback

    def _calculate_similarity(
        self,
        params1: dict[str, Any],
        params2: dict[str, Any],
    ) -> float:
        """Calculate similarity between two parameter sets."""
        if not params1 and not params2:
            return 1.0
        if not params1 or not params2:
            return 0.0

        # Simple Jaccard similarity on keys
        keys1 = set(params1.keys())
        keys2 = set(params2.keys())
        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)

        if union == 0:
            return 1.0

        key_similarity = intersection / union

        # Check value similarity for common keys
        common_keys = keys1 & keys2
        if common_keys:
            value_matches = sum(
                1 for k in common_keys
                if str(params1.get(k)) == str(params2.get(k))
            )
            value_similarity = value_matches / len(common_keys)
        else:
            value_similarity = 0.0

        return (key_similarity + value_similarity) / 2

    def get_efficiency_report(self) -> dict[str, Any]:
        """Generate efficiency report for recent calls."""
        if not self.call_history:
            return {"message": "No tool calls recorded"}

        metrics = ToolCallMetrics()
        metrics.total_calls = len(self.call_history)
        metrics.redundant_calls = sum(
            1 for c in self.call_history
            if c.efficiency == ToolCallEfficiency.REDUNDANT
        )
        metrics.failed_calls = sum(1 for c in self.call_history if not c.success)

        if self.call_history:
            metrics.average_response_time_ms = sum(
                c.response_time_ms for c in self.call_history
            ) / len(self.call_history)
            metrics.total_tokens_used = sum(
                c.tokens_used for c in self.call_history
            )

        # Group by tool
        by_tool = {}
        for call in self.call_history:
            if call.tool_name not in by_tool:
                by_tool[call.tool_name] = {"total": 0, "failed": 0, "redundant": 0}
            by_tool[call.tool_name]["total"] += 1
            if not call.success:
                by_tool[call.tool_name]["failed"] += 1
            if call.efficiency == ToolCallEfficiency.REDUNDANT:
                by_tool[call.tool_name]["redundant"] += 1

        return {
            "total_calls": metrics.total_calls,
            "redundant_calls": metrics.redundant_calls,
            "failed_calls": metrics.failed_calls,
            "efficiency_score": metrics.efficiency_score,
            "average_response_time_ms": metrics.average_response_time_ms,
            "total_tokens_used": metrics.total_tokens_used,
            "by_tool": by_tool,
            "potential_savings": f"{metrics.redundant_calls / metrics.total_calls * 100:.1f}%"
            if metrics.total_calls > 0 else "0%",
        }


class SuggestionCoordinator:
    """
    Stage 2 of Bloomberg methodology: Suggestion Coordinator.

    Produces improvement suggestions for agent prompts and tool docs.
    """

    def __init__(self, feedback_generator: FeedbackGenerator):
        self.feedback_generator = feedback_generator
        self.improvement_history: list[dict[str, Any]] = []

    def generate_suggestions(
        self,
        tool_descriptions: dict[str, ToolDescription],
    ) -> dict[str, Any]:
        """
        Generate improvement suggestions based on call patterns.

        Returns suggestions for:
        - Tool descriptions that could be clearer
        - Agent prompts that could prevent unnecessary calls
        - Tool combinations that should be recommended
        """
        suggestions = {
            "tool_description_updates": [],
            "agent_prompt_updates": [],
            "tool_combinations": [],
            "deprecation_candidates": [],
        }

        report = self.feedback_generator.get_efficiency_report()

        # Analyze tool usage patterns
        for tool_name, stats in report.get("by_tool", {}).items():
            # High redundancy tools
            if stats["total"] > 0 and stats["redundant"] / stats["total"] > 0.3:
                suggestions["tool_description_updates"].append({
                    "tool": tool_name,
                    "issue": "High redundancy rate",
                    "suggestion": (
                        f"Add to 'avoid_when': 'Result from previous call can be reused'"
                    ),
                })

            # High failure tools
            if stats["total"] > 0 and stats["failed"] / stats["total"] > 0.2:
                suggestions["tool_description_updates"].append({
                    "tool": tool_name,
                    "issue": "High failure rate",
                    "suggestion": (
                        "Add clearer prerequisites and parameter validation guidance"
                    ),
                })

        # Identify common tool sequences
        sequences = self._identify_tool_sequences()
        for seq, count in sequences.items():
            if count >= 3:
                tools = seq.split(" -> ")
                suggestions["tool_combinations"].append({
                    "sequence": tools,
                    "frequency": count,
                    "suggestion": f"Consider combining {tools[0]} and {tools[1]} into single call",
                })

        # Store for tracking
        self.improvement_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": suggestions,
        })

        return suggestions

    def _identify_tool_sequences(self) -> dict[str, int]:
        """Identify common consecutive tool call patterns."""
        sequences = {}
        calls = self.feedback_generator.call_history

        for i in range(len(calls) - 1):
            seq = f"{calls[i].tool_name} -> {calls[i + 1].tool_name}"
            sequences[seq] = sequences.get(seq, 0) + 1

        return sequences


class ContextRefiner:
    """
    Stage 3 of Bloomberg methodology: Context Refiner.

    Processes suggestions to update the context (prompts and docs).
    """

    def __init__(self):
        self.applied_refinements: list[dict[str, Any]] = []

    def apply_refinements(
        self,
        suggestions: dict[str, Any],
        tool_descriptions: dict[str, ToolDescription],
    ) -> dict[str, ToolDescription]:
        """
        Apply refinements to tool descriptions based on suggestions.

        Returns updated tool descriptions.
        """
        updated = dict(tool_descriptions)

        for update in suggestions.get("tool_description_updates", []):
            tool_name = update["tool"]
            if tool_name in updated:
                tool = updated[tool_name]

                # Add to avoid_when based on suggestion
                if "avoid_when" in update["suggestion"].lower():
                    new_avoid = update["suggestion"].split("'")[1]
                    if new_avoid not in tool.avoid_when:
                        tool.avoid_when.append(new_avoid)

                self.applied_refinements.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "tool": tool_name,
                    "refinement": update["suggestion"],
                })

        # Add tool combinations
        for combo in suggestions.get("tool_combinations", []):
            tools = combo["sequence"]
            if tools[0] in updated and tools[1] not in updated[tools[0]].combine_with:
                updated[tools[0]].combine_with.append(tools[1])

        return updated

    def generate_optimized_prompt(
        self,
        task: str,
        tool_descriptions: dict[str, ToolDescription],
    ) -> str:
        """
        Generate an optimized agent prompt with refined tool guidance.

        Per Bloomberg: "Joint optimization framework aims to improve
        the efficiency of tool-augmented LLM agents."
        """
        lines = [
            "# Task Instructions",
            "",
            task,
            "",
            "# Available Tools",
            "",
            "**Important**: Before calling a tool, consider:",
            "1. Have you already called this tool with similar parameters?",
            "2. Can you combine multiple operations into fewer calls?",
            "3. Do you have the prerequisites for this tool?",
            "",
        ]

        for tool in tool_descriptions.values():
            lines.append(tool.to_prompt_format())
            lines.append("")

        lines.extend([
            "# Efficiency Guidelines",
            "",
            "- Reuse results from previous tool calls when possible",
            "- Batch related operations together",
            "- Check tool prerequisites before calling",
            "- Consider tool cost when multiple options exist",
        ])

        return "\n".join(lines)


class EnhancedToolCaller:
    """
    Unified enhanced tool calling system.

    Implements the full Bloomberg three-stage methodology for
    up to 70% reduction in tool calls.
    """

    def __init__(self):
        self.feedback_generator = FeedbackGenerator()
        self.suggestion_coordinator = SuggestionCoordinator(self.feedback_generator)
        self.context_refiner = ContextRefiner()
        self.tool_descriptions: dict[str, ToolDescription] = {}

    def register_tool(self, tool: ToolDescription):
        """Register a tool with enhanced description."""
        self.tool_descriptions[tool.name] = tool
        logger.info(f"Registered enhanced tool: {tool.name}")

    def should_call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Determine if a tool call is necessary.

        Returns (should_call, reason).
        """
        # Check for redundancy
        for prev_call in reversed(self.feedback_generator.call_history[-20:]):
            if prev_call.tool_name == tool_name:
                similarity = self.feedback_generator._calculate_similarity(
                    prev_call.parameters, parameters
                )
                if similarity > REDUNDANCY_THRESHOLD and prev_call.success:
                    return False, (
                        f"Redundant call detected. Previous call with {similarity:.0%} "
                        f"similar parameters succeeded. Reuse that result."
                    )

        # Check prerequisites
        if tool_name in self.tool_descriptions:
            tool = self.tool_descriptions[tool_name]
            for prereq in tool.prerequisites:
                prereq_called = any(
                    c.tool_name == prereq and c.success
                    for c in self.feedback_generator.call_history[-10:]
                )
                if not prereq_called:
                    return False, f"Prerequisite tool '{prereq}' should be called first"

        return True, "Tool call approved"

    def record_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any,
        success: bool,
        response_time_ms: float,
        tokens_used: int = 0,
    ) -> ToolCallRecord:
        """Record a tool call and analyze efficiency."""
        record = ToolCallRecord(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            success=success,
            timestamp=datetime.utcnow(),
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
        )

        # Analyze and update efficiency
        feedback = self.feedback_generator.analyze_call(record)
        record.efficiency = feedback["efficiency"]
        record.feedback = json.dumps(feedback["suggestions"])

        self.feedback_generator.add_call(record)

        return record

    def optimize(self) -> dict[str, Any]:
        """
        Run optimization cycle.

        Returns optimization report with applied changes.
        """
        # Generate suggestions
        suggestions = self.suggestion_coordinator.generate_suggestions(
            self.tool_descriptions
        )

        # Apply refinements
        self.tool_descriptions = self.context_refiner.apply_refinements(
            suggestions, self.tool_descriptions
        )

        return {
            "suggestions": suggestions,
            "refinements_applied": len(self.context_refiner.applied_refinements),
            "efficiency_report": self.feedback_generator.get_efficiency_report(),
        }

    def get_optimized_prompt(self, task: str) -> str:
        """Get optimized prompt for a task."""
        return self.context_refiner.generate_optimized_prompt(
            task, self.tool_descriptions
        )


# Global instance
_enhanced_tool_caller: EnhancedToolCaller | None = None


def get_enhanced_tool_caller() -> EnhancedToolCaller:
    """Get global enhanced tool caller instance."""
    global _enhanced_tool_caller
    if _enhanced_tool_caller is None:
        _enhanced_tool_caller = EnhancedToolCaller()
    return _enhanced_tool_caller


__all__ = [
    "ContextRefiner",
    "EnhancedToolCaller",
    "FeedbackGenerator",
    "SuggestionCoordinator",
    "ToolCallEfficiency",
    "ToolCallMetrics",
    "ToolCallRecord",
    "ToolDescription",
    "get_enhanced_tool_caller",
]
