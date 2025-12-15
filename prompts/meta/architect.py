#!/usr/bin/env python3
"""
DevSkyy Architect Meta-Prompt - Meta-prompts for LLM-driven repository development
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ..base.techniques import ChainOfThought, NegativeConstraints, PromptBuilder, RoleConstraint, SuccessCriteria


class ArchitectSubagent(str, Enum):
    """Specialist subagents for repository development."""
    DIAGNOSTICIAN = "diagnostician"
    BACKEND_SURGEON = "backend_surgeon"
    FRONTEND_ARCHITECT = "frontend_architect"
    DEVOPS_ENGINEER = "devops_engineer"
    DOCUMENTATION_WRITER = "documentation_writer"
    SECURITY_AUDITOR = "security_auditor"
    TEST_ENGINEER = "test_engineer"


@dataclass
class SubagentConfig:
    """Configuration for a specialist subagent."""
    agent_type: ArchitectSubagent
    role_title: str
    responsibilities: List[str]
    expertise_areas: List[str]
    output_artifacts: List[str]


SUBAGENT_CONFIGS: Dict[ArchitectSubagent, SubagentConfig] = {
    ArchitectSubagent.DIAGNOSTICIAN: SubagentConfig(
        agent_type=ArchitectSubagent.DIAGNOSTICIAN,
        role_title="Senior Code Diagnostician",
        responsibilities=["Audit entire codebase for issues", "Identify architectural problems", "Detect anti-patterns"],
        expertise_areas=["static analysis", "code review", "software architecture"],
        output_artifacts=["diagnostic_report.md", "issue_tracker.json"],
    ),
    ArchitectSubagent.BACKEND_SURGEON: SubagentConfig(
        agent_type=ArchitectSubagent.BACKEND_SURGEON,
        role_title="Senior Backend Engineer",
        responsibilities=["Fix critical backend issues", "Implement missing API endpoints", "Add proper error handling"],
        expertise_areas=["Python", "FastAPI", "SQLAlchemy", "security"],
        output_artifacts=["*.py files", "tests/"],
    ),
    ArchitectSubagent.TEST_ENGINEER: SubagentConfig(
        agent_type=ArchitectSubagent.TEST_ENGINEER,
        role_title="Senior QA Engineer",
        responsibilities=["Write unit tests", "Create integration tests", "Ensure code coverage > 80%"],
        expertise_areas=["pytest", "unittest", "test design"],
        output_artifacts=["tests/", "conftest.py"],
    ),
    ArchitectSubagent.DOCUMENTATION_WRITER: SubagentConfig(
        agent_type=ArchitectSubagent.DOCUMENTATION_WRITER,
        role_title="Technical Documentation Specialist",
        responsibilities=["Write comprehensive README", "Document API endpoints", "Create deployment guides"],
        expertise_areas=["technical writing", "API documentation", "Markdown"],
        output_artifacts=["README.md", "docs/", "AGENTS.md"],
    ),
    ArchitectSubagent.SECURITY_AUDITOR: SubagentConfig(
        agent_type=ArchitectSubagent.SECURITY_AUDITOR,
        role_title="Application Security Engineer",
        responsibilities=["Audit code for vulnerabilities", "Review authentication", "Check OWASP Top 10"],
        expertise_areas=["OWASP", "JWT/OAuth", "encryption"],
        output_artifacts=["security_audit.md"],
    ),
    ArchitectSubagent.DEVOPS_ENGINEER: SubagentConfig(
        agent_type=ArchitectSubagent.DEVOPS_ENGINEER,
        role_title="Senior DevOps Engineer",
        responsibilities=["Create Docker configurations", "Set up CI/CD pipelines", "Configure monitoring"],
        expertise_areas=["Docker", "Kubernetes", "GitHub Actions"],
        output_artifacts=["Dockerfile", ".github/workflows/"],
    ),
    ArchitectSubagent.FRONTEND_ARCHITECT: SubagentConfig(
        agent_type=ArchitectSubagent.FRONTEND_ARCHITECT,
        role_title="Senior Frontend Architect",
        responsibilities=["Build React components", "Implement responsive layouts", "Integrate with backend APIs"],
        expertise_areas=["React", "Next.js", "Tailwind CSS", "TypeScript"],
        output_artifacts=["*.jsx", "*.tsx", "components/"],
    ),
}


@dataclass
class RepoContext:
    """Context about the repository being developed."""
    repo_name: str
    description: str
    current_issues: List[str] = field(default_factory=list)
    target_outcome: str = ""
    tech_stack: Dict[str, str] = field(default_factory=dict)
    file_count: int = 0
    line_count: int = 0


def build_architect_prompt(
    repo_context: RepoContext,
    subagents: Optional[List[ArchitectSubagent]] = None,
    focus_areas: Optional[List[str]] = None,
    time_limit: str = "5 hours",
) -> str:
    """Build the master architect meta-prompt."""
    builder = PromptBuilder()

    role = RoleConstraint(
        role="Lead Code Architect",
        years_experience=20,
        domain="full-stack software architecture",
        expertise_areas=["system design", "code review", "Python/FastAPI", "React/Next.js"],
        tone="precise and methodical",
        constraints=["Verify against official docs", "No placeholders or TODOs", "Every file production-ready"],
    )
    builder.add_role(role)

    tech_stack_str = "\n".join([f"  - {k}: {v}" for k, v in repo_context.tech_stack.items()])
    issues_str = "\n".join([f"  ⚠ {issue}" for issue in repo_context.current_issues])

    context_section = f"""
REPOSITORY: {repo_context.repo_name}
DESCRIPTION: {repo_context.description}
FILES: {repo_context.file_count} | LINES: {repo_context.line_count}

TECH STACK:
{tech_stack_str}

KNOWN ISSUES:
{issues_str}

TARGET OUTCOME:
{repo_context.target_outcome}

TIME CONSTRAINT: {time_limit}
"""
    builder.add_custom("Repository Context", context_section)
    builder.add_chain_of_thought()
    builder.add_negative_constraints(NegativeConstraints(
        do_not=["Leave TODO comments", "Skip tests", "Ignore error handling"],
        never=["Generate placeholder code", "Skip documentation updates"],
    ))
    builder.add_success_criteria(SuccessCriteria(
        criteria=["All tests pass", "No linting errors", "Documentation updated", "Security verified"],
        required_all=True,
    ))

    return builder.build(task_instruction="Analyze and improve this repository following the phased approach: DIAGNOSE → PLAN → FIX → ENHANCE → DOCUMENT → VALIDATE")


def build_code_review_prompt(file_path: str, code: str, language: str = "python") -> str:
    """Build a code review prompt."""
    builder = PromptBuilder()
    role = RoleConstraint(role="Senior Code Reviewer", years_experience=15, domain=f"{language} development", tone="constructive and thorough")
    builder.add_role(role)
    builder.add_chain_of_thought()
    return builder.build(task_instruction=f"Review this {language} code from {file_path}:\n\n```{language}\n{code}\n```\n\nProvide: 1) Critical Issues 2) Improvements 3) Security Concerns 4) Performance Optimizations")


def build_test_generation_prompt(module_path: str, code: str, coverage_target: int = 80) -> str:
    """Build a test generation prompt."""
    builder = PromptBuilder()
    role = RoleConstraint(role="Senior QA Engineer", years_experience=12, domain="automated testing", tone="thorough and practical")
    builder.add_role(role)
    builder.add_chain_of_thought()
    return builder.build(task_instruction=f"Generate pytest unit tests for:\n\nModule: {module_path}\nCoverage Target: {coverage_target}%\n\n```python\n{code}\n```\n\nInclude edge cases, error conditions, and mocking of external dependencies.")


def build_documentation_prompt(module_path: str, code: str, doc_type: str = "docstring") -> str:
    """Build a documentation generation prompt."""
    builder = PromptBuilder()
    role = RoleConstraint(role="Technical Writer", years_experience=10, domain="API documentation", tone="clear and comprehensive")
    builder.add_role(role)
    return builder.build(task_instruction=f"Generate {doc_type} documentation for:\n\nModule: {module_path}\n\n```python\n{code}\n```\n\nFollow Google style guide for Python docstrings.")


__all__ = [
    "ArchitectSubagent", "SubagentConfig", "SUBAGENT_CONFIGS", "RepoContext",
    "build_architect_prompt", "build_code_review_prompt",
    "build_test_generation_prompt", "build_documentation_prompt",
]
