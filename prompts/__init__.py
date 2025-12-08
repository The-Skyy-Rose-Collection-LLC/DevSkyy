"""
DevSkyy Prompt Engineering System
Enterprise-grade prompt injection system implementing the Elon Musk Thinking Framework

Techniques Implemented:
1. Role-Based Constraint Prompting
2. Chain-of-Thought (CoT)
3. Few-Shot Prompting
4. Self-Consistency
5. Tree of Thoughts
6. ReAct (Reasoning + Acting)
7. RAG (Retrieval-Augmented Generation)
8. Prompt Chaining
9. Generated Knowledge
10. Negative Prompting

Plus Enterprise Frameworks:
- OpenAI's Six-Strategy Framework
- Anthropic's COSTARD Framework
- Constitutional AI Principles
"""

from .technique_engine import PromptTechniqueEngine
from .base_system_prompt import BaseAgentSystemPrompt
from .meta_prompts import MetaPromptFactory
from .task_templates import TaskTemplateFactory
from .agent_prompts import AgentPromptLibrary
from .chain_orchestrator import PromptChainOrchestrator

__all__ = [
    "PromptTechniqueEngine",
    "BaseAgentSystemPrompt", 
    "MetaPromptFactory",
    "TaskTemplateFactory",
    "AgentPromptLibrary",
    "PromptChainOrchestrator",
]

__version__ = "1.0.0"
