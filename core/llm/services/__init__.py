"""
LLM Services
============

Business logic services for LLM operations.

Currently re-exports from llm module for backward compatibility.
This allows imports from both:
- from llm.router import LLMRouter  # Old path
- from core.llm.services.router import LLMRouter  # New path (future)

Services:
- router: Task-based LLM routing
- round_table: Multi-LLM competition system
- ab_testing: Statistical significance testing

Author: DevSkyy Platform Team
Version: 1.0.0
"""

# Re-export services from original location
# Note: These will be gradually refactored to use domain models
from llm import ab_testing, round_table, router

__all__ = [
    "router",
    "round_table",
    "ab_testing",
]

__version__ = "1.0.0"
