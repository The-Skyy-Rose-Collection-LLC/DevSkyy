"""Prompts module for the Coding Architect Agent."""

from .system_prompt import (
    FEW_SHOT_EXAMPLES,
    SYSTEM_PROMPT,
    TASK_PROMPTS,
    PromptTechnique,
    get_few_shot_examples,
    get_system_prompt,
    get_task_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "TASK_PROMPTS",
    "FEW_SHOT_EXAMPLES",
    "PromptTechnique",
    "get_system_prompt",
    "get_task_prompt",
    "get_few_shot_examples",
]
