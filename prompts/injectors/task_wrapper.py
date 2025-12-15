#!/usr/bin/env python3
"""
DevSkyy Task Injector - Dynamic task injection for runtime prompt composition
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base.techniques import FewShot, NegativeConstraints, PromptBuilder, TechniqueRegistry


@dataclass
class TaskContext:
    """Context for a specific task execution."""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_format: Optional[str] = None
    max_length: Optional[int] = None
    required_fields: List[str] = field(default_factory=list)
    use_cot: bool = True
    use_few_shot: bool = False
    use_tree_of_thoughts: bool = False
    use_react: bool = False
    use_self_consistency: bool = False
    use_generated_knowledge: bool = False
    examples: List[tuple] = field(default_factory=list)
    extra_constraints: Optional[NegativeConstraints] = None
    priority: str = "normal"
    deadline: Optional[datetime] = None
    requester: Optional[str] = None


class TaskInjector:
    """Injects task-specific enhancements into base agent prompts."""

    def __init__(self, default_cot: bool = True, default_constraints: Optional[NegativeConstraints] = None):
        self.default_cot = default_cot
        self.default_constraints = default_constraints

    def inject(self, base_prompt: str, context: TaskContext, include_metadata: bool = True) -> str:
        parts = [base_prompt]
        if include_metadata:
            parts.append(self._build_metadata_section(context))
        parts.append(self._build_task_section(context))
        techniques_prompt = self._build_techniques_section(context)
        if techniques_prompt:
            parts.append(techniques_prompt)
        constraints_prompt = self._build_constraints_section(context)
        if constraints_prompt:
            parts.append(constraints_prompt)
        if context.output_format or context.required_fields:
            parts.append(self._build_output_section(context))
        return "\n\n".join(parts)

    def inject_quick(self, base_prompt: str, task_description: str, use_cot: bool = True, use_react: bool = False) -> str:
        context = TaskContext(
            task_id=f"quick-{datetime.utcnow().timestamp()}",
            task_type="quick_task",
            description=task_description,
            use_cot=use_cot,
            use_react=use_react,
        )
        return self.inject(base_prompt, context, include_metadata=False)

    def _build_metadata_section(self, context: TaskContext) -> str:
        lines = [f"{'='*60}", "TASK METADATA", f"{'='*60}", f"Task ID: {context.task_id}", f"Type: {context.task_type}", f"Priority: {context.priority.upper()}"]
        if context.deadline:
            lines.append(f"Deadline: {context.deadline.isoformat()}")
        if context.requester:
            lines.append(f"Requester: {context.requester}")
        return "\n".join(lines)

    def _build_task_section(self, context: TaskContext) -> str:
        lines = [f"{'='*60}", "TASK", f"{'='*60}", context.description]
        if context.input_data:
            lines.append("\nINPUT DATA:")
            for key, value in context.input_data.items():
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    def _build_techniques_section(self, context: TaskContext) -> str:
        builder = PromptBuilder()
        if context.use_cot or self.default_cot:
            builder.add_chain_of_thought()
        if context.use_few_shot and context.examples:
            few_shot = FewShot()
            for inp, out in context.examples:
                few_shot.add_example(inp, out)
            builder.add_few_shot(few_shot)
        if context.use_tree_of_thoughts:
            builder.add_tree_of_thoughts()
        if context.use_react:
            builder.add_react(TechniqueRegistry.react_ecommerce())
        if context.use_self_consistency:
            builder.add_self_consistency()
        if context.use_generated_knowledge:
            builder.add_generated_knowledge()
        techniques_used = builder.get_techniques_used()
        if not techniques_used:
            return ""
        return builder.build()

    def _build_constraints_section(self, context: TaskContext) -> str:
        parts = []
        if self.default_constraints:
            parts.append(self.default_constraints.render())
        if context.extra_constraints:
            parts.append(context.extra_constraints.render())
        return "\n".join(parts) if parts else ""

    def _build_output_section(self, context: TaskContext) -> str:
        lines = [f"{'='*60}", "OUTPUT REQUIREMENTS", f"{'='*60}"]
        if context.output_format:
            lines.append(f"Format: {context.output_format}")
        if context.max_length:
            lines.append(f"Max Length: {context.max_length} characters")
        if context.required_fields:
            lines.append("Required Fields:")
            for field in context.required_fields:
                lines.append(f"  ☐ {field}")
        return "\n".join(lines)


class TaskTemplates:
    """Pre-built task context templates for common operations."""

    @staticmethod
    def inventory_check(collection: str, sku_list: List[str]) -> TaskContext:
        return TaskContext(
            task_id=f"inv-{datetime.utcnow().timestamp()}",
            task_type="inventory_check",
            description=f"Check inventory levels for {collection} collection",
            input_data={"collection": collection, "skus": sku_list},
            use_cot=True,
            use_react=True,
            output_format="JSON with SKU, quantity, status, reorder_needed",
            required_fields=["sku", "quantity", "status"],
        )

    @staticmethod
    def content_generation(content_type: str, topic: str, tone: str = "luxury") -> TaskContext:
        return TaskContext(
            task_id=f"content-{datetime.utcnow().timestamp()}",
            task_type="content_generation",
            description=f"Generate {content_type} about {topic}",
            input_data={"type": content_type, "topic": topic, "tone": tone},
            use_cot=True,
            use_generated_knowledge=True,
            output_format=f"{content_type} matching SkyyRose brand voice",
            extra_constraints=NegativeConstraints(
                do_not=["Use discount language", "Use informal tone", "Include placeholder text"],
                never=["Compromise brand voice", "Make false claims"],
            ),
        )

    @staticmethod
    def code_generation(language: str, task_description: str, include_tests: bool = True) -> TaskContext:
        return TaskContext(
            task_id=f"code-{datetime.utcnow().timestamp()}",
            task_type="code_generation",
            description=f"Generate {language} code: {task_description}",
            input_data={"language": language, "include_tests": include_tests},
            use_cot=True,
            use_tree_of_thoughts=True,
            output_format=f"Complete {language} code with type hints and docstrings",
            extra_constraints=NegativeConstraints(
                do_not=["Include TODO or FIXME comments", "Use deprecated APIs", "Leave functions unimplemented"],
                never=["Hardcode credentials or secrets", "Skip error handling", "Ignore input validation"],
            ),
        )


class ChainBuilder:
    """Build prompt chains for multi-step workflows."""

    def __init__(self):
        self.steps: List[TaskContext] = []

    def add_step(self, context: TaskContext) -> "ChainBuilder":
        self.steps.append(context)
        return self

    def build_sequential_prompts(self, base_prompt: str) -> List[str]:
        injector = TaskInjector()
        prompts = []
        for i, context in enumerate(self.steps):
            prompt = injector.inject(base_prompt, context)
            if i > 0:
                prompt += f"\n\nUSE THE OUTPUT FROM STEP {i} AS INPUT FOR THIS STEP."
            prompts.append(prompt)
        return prompts


__all__ = ["TaskContext", "TaskInjector", "TaskTemplates", "ChainBuilder"]
