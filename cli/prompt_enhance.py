"""
Prompt Enhancer CLI
===================

A CLI tool that transforms natural language prompts into optimized,
executive-level prompts for Claude with adaptive technique selection
and context injection.

Usage:
    prompt-enhance "my messy prompt"
    echo "my prompt" | prompt-enhance
    prompt-enhance --preview "fix the bug"
    prompt-enhance --mode code --format json "refactor this function"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import click
import yaml

if TYPE_CHECKING:
    from typing import Any

__version__ = "0.1.0"

# =============================================================================
# Configuration Loading
# =============================================================================

CONFIG_DIR = Path.home() / ".prompt-enhance"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "default_mode": "auto",
    "default_format": "plain",
    "context_budget": 2000,
    "api": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
    },
    "logging": {
        "enabled": True,
        "history_file": str(CONFIG_DIR / "history.jsonl"),
    },
}


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.prompt-enhance/config.yaml."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE) as f:
            user_config = yaml.safe_load(f) or {}

        # Merge with defaults (user config takes precedence)
        config = DEFAULT_CONFIG.copy()
        for key, value in user_config.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                config[key] = {**config[key], **value}
            else:
                config[key] = value
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


# Global config loaded once
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """Get cached configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


# =============================================================================
# Enums and Constants
# =============================================================================


class TaskMode(str, Enum):
    """Detected or specified task mode."""

    CODE = "code"
    WRITING = "writing"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    DEBUG = "debug"
    REFACTOR = "refactor"
    AUTO = "auto"


class OutputFormat(str, Enum):
    """Output format for enhanced prompts."""

    PLAIN = "plain"
    MARKDOWN = "md"
    JSON = "json"


class PromptTechnique(str, Enum):
    """Prompt engineering techniques."""

    CHAIN_OF_THOUGHT = "chain-of-thought"
    TREE_OF_THOUGHTS = "tree-of-thoughts"
    FEW_SHOT = "few-shot"
    ROLE_ASSIGNMENT = "role-assignment"
    SELF_CONSISTENCY = "self-consistency"
    METACOGNITION = "metacognition"
    STEP_BY_STEP = "step-by-step"
    CONSTRAINTS_FIRST = "constraints-first"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PromptAnalysis:
    """Result of analyzing a prompt."""

    original: str
    task_type: TaskMode
    clarity_score: int  # 0-100
    missing_elements: list[str] = field(default_factory=list)
    detected_keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TechniqueSelection:
    """Selected techniques for enhancement."""

    techniques: list[PromptTechnique]
    reasoning: str
    task_type: TaskMode


@dataclass
class EnhancedPrompt:
    """Result of prompt enhancement."""

    original: str
    enhanced: str
    analysis: PromptAnalysis
    techniques: TechniqueSelection
    context_used: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "original": self.original,
            "enhanced": self.enhanced,
            "analysis": {
                "task_type": self.analysis.task_type.value,
                "clarity_score": self.analysis.clarity_score,
                "missing_elements": self.analysis.missing_elements,
                "confidence": self.analysis.confidence,
            },
            "techniques": {
                "applied": [t.value for t in self.techniques.techniques],
                "reasoning": self.techniques.reasoning,
            },
            "context_files": self.context_used,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
        }


# =============================================================================
# CLI Application
# =============================================================================


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="""
Examples:
  prompt-enhance "fix the login bug"
  prompt-enhance --mode code "add error handling to the API"
  prompt-enhance --preview "refactor the database module"
  prompt-enhance --format json "analyze this code" > analysis.json
  echo "explain this function" | prompt-enhance --auto
  prompt-enhance --context src/main.py "improve this module"
  prompt-enhance --stats
  prompt-enhance --init
""",
)
@click.argument("prompt", required=False)
@click.option(
    "-m",
    "--mode",
    type=click.Choice([m.value for m in TaskMode], case_sensitive=False),
    default=None,
    help="Task mode (auto-detected if not specified). Default from config.",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice([f.value for f in OutputFormat], case_sensitive=False),
    default=None,
    help="Output format. Default from config.",
)
@click.option(
    "-p",
    "--preview",
    is_flag=True,
    help="Show side-by-side comparison of original vs enhanced.",
)
@click.option(
    "-a",
    "--auto",
    "auto_mode",
    is_flag=True,
    help="Output only the enhanced prompt (for piping).",
)
@click.option(
    "-c",
    "--copy",
    "copy_clipboard",
    is_flag=True,
    help="Copy enhanced prompt to clipboard.",
)
@click.option(
    "--context",
    "context_files",
    multiple=True,
    help="Files to include as context (can specify multiple).",
)
@click.option(
    "--no-context",
    is_flag=True,
    help="Disable auto-scanning for context.",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show enhancement analytics and history stats.",
)
@click.option(
    "--init",
    "init_config",
    is_flag=True,
    help="Create default configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed processing information.",
)
@click.option(
    "--no-log",
    is_flag=True,
    help="Disable logging this enhancement to history.",
)
@click.option(
    "--model",
    "model_override",
    default=None,
    help="Claude model to use (e.g., claude-opus-4-20250514). Default from config.",
)
@click.version_option(version=__version__, prog_name="prompt-enhance")
def main(
    prompt: str | None,
    mode: str | None,
    output_format: str | None,
    preview: bool,
    auto_mode: bool,
    copy_clipboard: bool,
    context_files: tuple[str, ...],
    no_context: bool,
    stats: bool,
    init_config: bool,
    verbose: bool,
    no_log: bool,
    model_override: str | None,
) -> None:
    """
    Transform natural language prompts into optimized, executive-level prompts.

    PROMPT is your natural language input. If not provided, reads from stdin.

    The enhancer analyzes your prompt, detects the task type, selects optimal
    prompt engineering techniques, and generates an enhanced version optimized
    for Claude.
    """
    # Load configuration
    config = get_config()

    # Apply config defaults for unspecified options
    if mode is None:
        mode = config.get("default_mode", "auto")
    if output_format is None:
        output_format = config.get("default_format", "plain")

    # Handle special commands first
    if stats:
        _show_stats()
        return

    if init_config:
        _init_config()
        return

    # Get prompt from argument or stdin
    if prompt is None:
        if sys.stdin.isatty():
            raise click.UsageError(
                "No prompt provided. Use: prompt-enhance 'your prompt' "
                "or pipe input: echo 'prompt' | prompt-enhance"
            )
        prompt = sys.stdin.read().strip()

    if not prompt:
        raise click.UsageError("Empty prompt provided.")

    # Parse options
    task_mode = TaskMode(mode)
    fmt = OutputFormat(output_format)

    # Get model from config (CLI override takes precedence)
    model = model_override or config.get("api", {}).get("model", "claude-sonnet-4-20250514")
    context_budget = config.get("context_budget", 2000)

    # Process the prompt
    if verbose:
        click.echo(f"Mode: {task_mode.value}", err=True)
        click.echo(f"Format: {fmt.value}", err=True)
        click.echo(f"Model: {model}", err=True)
        click.echo(f"Context files: {context_files or 'auto'}", err=True)

    try:
        result = _enhance_prompt(
            prompt=prompt,
            mode=task_mode,
            context_files=list(context_files) if context_files else None,
            no_context=no_context,
            verbose=verbose,
            model=model,
            context_budget=context_budget,
        )
    except EnhancementError as e:
        raise click.ClickException(str(e)) from e

    # Output the result
    _output_result(
        result=result,
        output_format=fmt,
        preview=preview,
        auto_mode=auto_mode,
        copy_clipboard=copy_clipboard,
    )

    # Log to history unless disabled
    if not no_log:
        _log_enhancement(result)


# =============================================================================
# Core Classes - US-002: PromptAnalyzer
# =============================================================================


class EnhancementError(Exception):
    """Error during prompt enhancement."""

    pass


# Keyword patterns for task detection
TASK_KEYWORDS: dict[TaskMode, list[str]] = {
    TaskMode.CODE: [
        "implement",
        "code",
        "function",
        "class",
        "api",
        "endpoint",
        "module",
        "library",
        "script",
        "program",
        "algorithm",
        "data structure",
        "write",
        "create",
        "build",
    ],
    TaskMode.DEBUG: [
        "fix",
        "bug",
        "error",
        "issue",
        "broken",
        "failing",
        "crash",
        "exception",
        "traceback",
        "not working",
        "debug",
        "troubleshoot",
    ],
    TaskMode.REFACTOR: [
        "refactor",
        "improve",
        "optimize",
        "clean up",
        "restructure",
        "simplify",
        "modernize",
        "upgrade",
        "performance",
    ],
    TaskMode.ANALYSIS: [
        "analyze",
        "review",
        "explain",
        "understand",
        "what does",
        "how does",
        "why",
        "evaluate",
        "assess",
        "compare",
    ],
    TaskMode.WRITING: [
        "write",
        "document",
        "readme",
        "documentation",
        "comment",
        "describe",
        "summarize",
        "blog",
        "article",
    ],
    TaskMode.CREATIVE: [
        "design",
        "brainstorm",
        "idea",
        "creative",
        "innovative",
        "suggest",
        "propose",
        "concept",
    ],
}

# Technique mappings per task type
TECHNIQUE_MAPPINGS: dict[TaskMode, list[PromptTechnique]] = {
    TaskMode.CODE: [
        PromptTechnique.ROLE_ASSIGNMENT,
        PromptTechnique.STEP_BY_STEP,
        PromptTechnique.CONSTRAINTS_FIRST,
    ],
    TaskMode.DEBUG: [
        PromptTechnique.CHAIN_OF_THOUGHT,
        PromptTechnique.STEP_BY_STEP,
        PromptTechnique.METACOGNITION,
    ],
    TaskMode.REFACTOR: [
        PromptTechnique.ROLE_ASSIGNMENT,
        PromptTechnique.CHAIN_OF_THOUGHT,
        PromptTechnique.CONSTRAINTS_FIRST,
    ],
    TaskMode.ANALYSIS: [
        PromptTechnique.CHAIN_OF_THOUGHT,
        PromptTechnique.TREE_OF_THOUGHTS,
        PromptTechnique.METACOGNITION,
    ],
    TaskMode.WRITING: [
        PromptTechnique.ROLE_ASSIGNMENT,
        PromptTechnique.FEW_SHOT,
        PromptTechnique.CONSTRAINTS_FIRST,
    ],
    TaskMode.CREATIVE: [
        PromptTechnique.TREE_OF_THOUGHTS,
        PromptTechnique.SELF_CONSISTENCY,
        PromptTechnique.METACOGNITION,
    ],
}


class PromptAnalyzer:
    """Analyzes prompts to detect task type and assess clarity (US-002)."""

    def analyze(self, prompt: str) -> PromptAnalysis:
        """Analyze a prompt and return structured analysis."""
        prompt_lower = prompt.lower()

        # Detect task type
        task_type, confidence = self._detect_task_type(prompt_lower)

        # Assess clarity
        clarity_score = self._assess_clarity(prompt)

        # Find missing elements
        missing = self._find_missing_elements(prompt)

        # Extract keywords
        keywords = self._extract_keywords(prompt_lower)

        return PromptAnalysis(
            original=prompt,
            task_type=task_type,
            clarity_score=clarity_score,
            missing_elements=missing,
            detected_keywords=keywords,
            confidence=confidence,
        )

    def _detect_task_type(self, prompt_lower: str) -> tuple[TaskMode, float]:
        """Detect task type from prompt keywords."""
        scores: dict[TaskMode, int] = {}

        for mode, keywords in TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            if score > 0:
                scores[mode] = score

        if not scores:
            return TaskMode.CODE, 0.3  # Default to code with low confidence

        best_mode = max(scores, key=lambda m: scores[m])
        confidence = min(scores[best_mode] / 5, 1.0)  # Cap at 1.0

        return best_mode, confidence

    def _assess_clarity(self, prompt: str) -> int:
        """Assess prompt clarity on a 0-100 scale."""
        score = 50  # Base score

        # Length checks
        word_count = len(prompt.split())
        if word_count < 5:
            score -= 20
        elif word_count > 10:
            score += 10
        if word_count > 30:
            score += 10

        # Structure checks
        if "?" in prompt:
            score += 5  # Has a question
        if any(c in prompt for c in [".", ":", "-"]):
            score += 5  # Has punctuation/structure
        if "\n" in prompt:
            score += 10  # Multi-line, structured

        # Specificity checks
        if any(word in prompt.lower() for word in ["specific", "exactly", "must", "should"]):
            score += 10
        if any(word in prompt.lower() for word in ["file", "function", "class", "module", "api"]):
            score += 5  # References specific code elements

        return min(max(score, 0), 100)

    def _find_missing_elements(self, prompt: str) -> list[str]:
        """Identify missing elements that would improve the prompt."""
        missing = []
        prompt_lower = prompt.lower()

        # Check for context
        if not any(
            word in prompt_lower for word in ["file", "code", "function", "class", "in the"]
        ):
            missing.append("context")

        # Check for constraints
        if not any(
            word in prompt_lower
            for word in ["must", "should", "require", "constraint", "limit", "only"]
        ):
            missing.append("constraints")

        # Check for output format
        if not any(
            word in prompt_lower
            for word in ["format", "output", "return", "response", "json", "markdown"]
        ):
            missing.append("output_format")

        # Check for examples
        if not any(word in prompt_lower for word in ["example", "like", "such as", "e.g."]):
            missing.append("examples")

        return missing

    def _extract_keywords(self, prompt_lower: str) -> list[str]:
        """Extract relevant keywords from the prompt."""
        keywords = []
        for mode_keywords in TASK_KEYWORDS.values():
            for kw in mode_keywords:
                if kw in prompt_lower and kw not in keywords:
                    keywords.append(kw)
        return keywords[:10]  # Limit to top 10


# =============================================================================
# Core Classes - US-003: TechniqueSelector
# =============================================================================


class TechniqueSelector:
    """Selects optimal prompt engineering techniques (US-003)."""

    def select(self, analysis: PromptAnalysis) -> TechniqueSelection:
        """Select techniques based on prompt analysis."""
        task_type = analysis.task_type
        techniques = TECHNIQUE_MAPPINGS.get(
            task_type,
            [PromptTechnique.ROLE_ASSIGNMENT, PromptTechnique.CHAIN_OF_THOUGHT],
        )

        # Adjust based on clarity
        if analysis.clarity_score < 40:
            # Low clarity - add metacognition to help clarify
            if PromptTechnique.METACOGNITION not in techniques:
                techniques = [PromptTechnique.METACOGNITION, *techniques[:2]]

        # Adjust based on missing elements
        if "examples" in analysis.missing_elements and PromptTechnique.FEW_SHOT not in techniques:
            techniques.append(PromptTechnique.FEW_SHOT)

        reasoning = self._generate_reasoning(task_type, techniques, analysis)

        return TechniqueSelection(
            techniques=techniques[:4],  # Limit to 4 techniques
            reasoning=reasoning,
            task_type=task_type,
        )

    def _generate_reasoning(
        self,
        task_type: TaskMode,
        techniques: list[PromptTechnique],
        analysis: PromptAnalysis,
    ) -> str:
        """Generate human-readable reasoning for technique selection."""
        parts = [
            f"Task type '{task_type.value}' detected with {analysis.confidence:.0%} confidence."
        ]

        tech_reasons = {
            PromptTechnique.ROLE_ASSIGNMENT: "Role assignment establishes expertise context.",
            PromptTechnique.CHAIN_OF_THOUGHT: "Chain-of-thought enables step-by-step reasoning.",
            PromptTechnique.TREE_OF_THOUGHTS: "Tree-of-thoughts explores multiple solution paths.",
            PromptTechnique.FEW_SHOT: "Few-shot examples clarify expected format.",
            PromptTechnique.STEP_BY_STEP: "Step-by-step ensures methodical execution.",
            PromptTechnique.CONSTRAINTS_FIRST: "Constraints-first establishes boundaries.",
            PromptTechnique.METACOGNITION: "Metacognition adds self-reflection.",
            PromptTechnique.SELF_CONSISTENCY: "Self-consistency validates through multiple approaches.",
        }

        for tech in techniques[:3]:
            if tech in tech_reasons:
                parts.append(tech_reasons[tech])

        return " ".join(parts)


# =============================================================================
# Core Classes - US-004: ContextScanner
# =============================================================================


class ContextScanner:
    """Scans and injects relevant codebase context (US-004)."""

    def __init__(self, token_budget: int = 2000):
        self.token_budget = token_budget

    def scan(
        self,
        prompt: str,
        explicit_files: list[str] | None = None,
        no_context: bool = False,
    ) -> tuple[str, list[str]]:
        """
        Scan for relevant context.

        Returns:
            Tuple of (context_string, list_of_files_used)
        """
        if no_context:
            return "", []

        files_used = []
        context_parts = []
        chars_used = 0
        char_budget = self.token_budget * 4  # Rough token-to-char estimate

        # Use explicit files if provided
        if explicit_files:
            for file_path in explicit_files:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    try:
                        content = path.read_text()
                        if chars_used + len(content) <= char_budget:
                            context_parts.append(f"### File: {file_path}\n```\n{content}\n```")
                            files_used.append(file_path)
                            chars_used += len(content)
                    except Exception:
                        pass  # Skip unreadable files
            if context_parts:
                return "\n\n".join(context_parts), files_used

        # Auto-scan current directory for relevant files
        keywords = self._extract_file_keywords(prompt)
        if not keywords:
            return "", []

        cwd = Path.cwd()
        candidate_files = []

        # Find Python files that might be relevant
        for pattern in ["*.py", "**/*.py"]:
            for py_file in cwd.glob(pattern):
                if self._is_relevant(py_file, keywords):
                    candidate_files.append(py_file)
                if len(candidate_files) >= 5:
                    break

        # Read relevant files up to budget
        for file_path in candidate_files[:3]:
            try:
                content = file_path.read_text()
                # Take first 500 chars if file is large
                if len(content) > 500:
                    content = content[:500] + "\n... (truncated)"
                if chars_used + len(content) <= char_budget:
                    rel_path = file_path.relative_to(cwd)
                    context_parts.append(f"### File: {rel_path}\n```python\n{content}\n```")
                    files_used.append(str(rel_path))
                    chars_used += len(content)
            except Exception:
                pass

        return "\n\n".join(context_parts), files_used

    def _extract_file_keywords(self, prompt: str) -> list[str]:
        """Extract keywords that might match file names."""
        import re

        # Find potential file/module names
        words = re.findall(r"\b[a-z_][a-z0-9_]*\b", prompt.lower())
        # Filter to likely file-related words
        keywords = [w for w in words if len(w) > 3 and w not in {"this", "that", "with", "from"}]
        return keywords[:5]

    def _is_relevant(self, file_path: Path, keywords: list[str]) -> bool:
        """Check if a file is relevant based on keywords."""
        name = file_path.stem.lower()
        return any(kw in name for kw in keywords)


# =============================================================================
# Core Classes - US-005: PromptEnhancer
# =============================================================================


class PromptEnhancer:
    """Enhances prompts using Claude API (US-005)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self._client = None

    @property
    def client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic

                self._client = Anthropic()
            except ImportError as e:
                raise EnhancementError(
                    "anthropic package not installed. Run: pip install anthropic"
                ) from e
            except Exception as e:
                raise EnhancementError(f"Failed to initialize Anthropic client: {e}") from e
        return self._client

    def enhance(
        self,
        prompt: str,
        analysis: PromptAnalysis,
        techniques: TechniqueSelection,
        context: str,
    ) -> str:
        """Enhance a prompt using Claude API."""
        import os

        # Check for API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            # Fall back to local enhancement without API
            return self._enhance_locally(prompt, analysis, techniques, context)

        meta_prompt = self._build_meta_prompt(prompt, analysis, techniques, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": meta_prompt}],
            )
            return response.content[0].text
        except Exception:
            # Fall back to local enhancement on API error
            return self._enhance_locally(prompt, analysis, techniques, context)

    def _build_meta_prompt(
        self,
        prompt: str,
        analysis: PromptAnalysis,
        techniques: TechniqueSelection,
        context: str,
    ) -> str:
        """Build the meta-prompt for enhancement."""
        technique_instructions = self._get_technique_instructions(techniques.techniques)

        meta = f"""You are an elite prompt engineer. Transform the following prompt into an optimized, executive-level prompt that will get the best possible response from Claude.

## Original Prompt
{prompt}

## Analysis
- Task Type: {analysis.task_type.value}
- Clarity Score: {analysis.clarity_score}/100
- Missing Elements: {', '.join(analysis.missing_elements) or 'None'}

## Techniques to Apply
{technique_instructions}

{f"## Available Context{chr(10)}{context}" if context else ""}

## Enhancement Guidelines
1. Preserve the user's core intent completely
2. Add clear structure with markdown headers
3. Apply the specified techniques naturally
4. Add specific constraints and requirements
5. Specify the desired output format
6. Add relevant examples if beneficial
7. Be concise but comprehensive

## Output
Return ONLY the enhanced prompt. No explanations, no meta-commentary. Just the improved prompt ready to use."""

        return meta

    def _get_technique_instructions(self, techniques: list[PromptTechnique]) -> str:
        """Get instructions for applying techniques."""
        instructions = {
            PromptTechnique.ROLE_ASSIGNMENT: "- **Role Assignment**: Start with 'You are an expert [role]...' to establish context",
            PromptTechnique.CHAIN_OF_THOUGHT: "- **Chain of Thought**: Include 'Think step by step' or 'Let's work through this systematically'",
            PromptTechnique.TREE_OF_THOUGHTS: "- **Tree of Thoughts**: Ask to 'Consider multiple approaches before selecting the best'",
            PromptTechnique.FEW_SHOT: "- **Few-Shot**: Include 1-2 examples of expected input/output format",
            PromptTechnique.STEP_BY_STEP: "- **Step by Step**: Structure the task as numbered steps",
            PromptTechnique.CONSTRAINTS_FIRST: "- **Constraints First**: Lead with requirements and limitations",
            PromptTechnique.METACOGNITION: "- **Metacognition**: Ask to 'Reflect on your approach' or 'Verify your reasoning'",
            PromptTechnique.SELF_CONSISTENCY: "- **Self-Consistency**: Request 'Generate multiple solutions and compare'",
        }
        return "\n".join(instructions.get(t, "") for t in techniques if t in instructions)

    def _enhance_locally(
        self,
        prompt: str,
        analysis: PromptAnalysis,
        techniques: TechniqueSelection,
        context: str,
    ) -> str:
        """Enhance prompt locally without API (fallback)."""
        parts = []

        # Role assignment
        if PromptTechnique.ROLE_ASSIGNMENT in techniques.techniques:
            role = self._get_role_for_task(analysis.task_type)
            parts.append(f"You are {role}.")

        # Main task
        parts.append(f"\n## Task\n{prompt}")

        # Add context if available
        if context:
            parts.append(f"\n## Context\n{context}")

        # Requirements based on task type
        requirements = self._get_requirements(analysis.task_type)
        parts.append(f"\n## Requirements\n{requirements}")

        # Chain of thought
        if PromptTechnique.CHAIN_OF_THOUGHT in techniques.techniques:
            parts.append("\nThink through this step by step, explaining your reasoning.")

        # Output format
        parts.append(
            "\n## Output Format\nProvide a clear, structured response with sections as needed."
        )

        return "\n".join(parts)

    def _get_role_for_task(self, task_type: TaskMode) -> str:
        """Get appropriate role for task type."""
        roles = {
            TaskMode.CODE: "an expert software engineer with deep knowledge of best practices and design patterns",
            TaskMode.DEBUG: "a senior debugging specialist skilled at root cause analysis",
            TaskMode.REFACTOR: "a code quality expert focused on clean architecture and maintainability",
            TaskMode.ANALYSIS: "a technical analyst with expertise in code review and system design",
            TaskMode.WRITING: "a technical writer skilled at clear, concise documentation",
            TaskMode.CREATIVE: "a creative technologist who thinks outside the box",
        }
        return roles.get(task_type, "an expert assistant")

    def _get_requirements(self, task_type: TaskMode) -> str:
        """Get requirements for task type."""
        reqs = {
            TaskMode.CODE: "- Write clean, maintainable code\n- Follow best practices\n- Include error handling\n- Add brief comments for complex logic",
            TaskMode.DEBUG: "- Identify the root cause\n- Explain why the bug occurs\n- Provide a fix with explanation\n- Suggest how to prevent similar issues",
            TaskMode.REFACTOR: "- Improve code quality without changing behavior\n- Explain each change\n- Maintain backwards compatibility\n- Consider performance implications",
            TaskMode.ANALYSIS: "- Provide thorough analysis\n- Support conclusions with evidence\n- Consider multiple perspectives\n- Highlight key insights",
            TaskMode.WRITING: "- Be clear and concise\n- Use appropriate technical level\n- Structure with headers and lists\n- Include examples where helpful",
            TaskMode.CREATIVE: "- Think innovatively\n- Consider feasibility\n- Explain the reasoning\n- Suggest implementation approaches",
        }
        return reqs.get(
            task_type, "- Be thorough and accurate\n- Explain your reasoning\n- Consider edge cases"
        )


# =============================================================================
# Main Enhancement Function
# =============================================================================


def _enhance_prompt(
    prompt: str,
    mode: TaskMode,
    context_files: list[str] | None,
    no_context: bool,
    verbose: bool,
    model: str = "claude-sonnet-4-20250514",
    context_budget: int = 2000,
) -> EnhancedPrompt:
    """
    Enhance a prompt using analysis, technique selection, and Claude API.

    Orchestrates US-002 through US-005.
    """
    import time

    start_time = time.time()

    # US-002: Analyze the prompt
    analyzer = PromptAnalyzer()
    analysis = analyzer.analyze(prompt)

    # Override task type if explicitly specified
    if mode != TaskMode.AUTO:
        analysis.task_type = mode
        analysis.confidence = 1.0

    if verbose:
        click.echo(
            f"Detected task: {analysis.task_type.value} ({analysis.confidence:.0%})", err=True
        )

    # US-003: Select techniques
    selector = TechniqueSelector()
    techniques = selector.select(analysis)

    if verbose:
        click.echo(f"Techniques: {', '.join(t.value for t in techniques.techniques)}", err=True)

    # US-004: Scan for context
    scanner = ContextScanner(token_budget=context_budget)
    context, files_used = scanner.scan(prompt, context_files, no_context)

    if verbose and files_used:
        click.echo(f"Context from: {', '.join(files_used)}", err=True)

    # US-005: Enhance the prompt
    enhancer = PromptEnhancer(model=model)
    enhanced = enhancer.enhance(prompt, analysis, techniques, context)

    latency_ms = (time.time() - start_time) * 1000

    return EnhancedPrompt(
        original=prompt,
        enhanced=enhanced,
        analysis=analysis,
        techniques=techniques,
        context_used=files_used,
        latency_ms=latency_ms,
    )


def _output_result(
    result: EnhancedPrompt,
    output_format: OutputFormat,
    preview: bool,
    auto_mode: bool,
    copy_clipboard: bool,
) -> None:
    """Output the enhanced prompt in the specified format."""
    import json

    if auto_mode:
        # Just output the enhanced prompt for piping
        click.echo(result.enhanced)
        return

    if output_format == OutputFormat.JSON:
        click.echo(json.dumps(result.to_dict(), indent=2))
        return

    if preview:
        # Side-by-side comparison
        click.echo(click.style("═" * 60, fg="blue"))
        click.echo(click.style(" ORIGINAL ", fg="yellow", bold=True))
        click.echo(click.style("═" * 60, fg="blue"))
        click.echo(result.original)
        click.echo()
        click.echo(click.style("═" * 60, fg="green"))
        click.echo(click.style(" ENHANCED ", fg="green", bold=True))
        click.echo(click.style("═" * 60, fg="green"))
        click.echo(result.enhanced)
        click.echo()
        click.echo(click.style("─" * 60, fg="blue"))
        click.echo(
            f"Task: {result.analysis.task_type.value} | "
            f"Clarity: {result.analysis.clarity_score}/100 | "
            f"Techniques: {', '.join(t.value for t in result.techniques.techniques)}"
        )
        return

    if output_format == OutputFormat.MARKDOWN:
        click.echo("# Enhanced Prompt\n")
        click.echo(f"**Task Type:** {result.analysis.task_type.value}")
        click.echo(f"**Techniques:** {', '.join(t.value for t in result.techniques.techniques)}")
        click.echo("\n## Prompt\n")
        click.echo(result.enhanced)
        return

    # Plain text (default)
    click.echo(result.enhanced)

    if copy_clipboard:
        try:
            import subprocess

            subprocess.run(
                ["pbcopy"],
                input=result.enhanced.encode(),
                check=True,
            )
            click.echo(click.style("\n✓ Copied to clipboard", fg="green"), err=True)
        except Exception:
            click.echo(click.style("\n✗ Could not copy to clipboard", fg="red"), err=True)


def _show_stats() -> None:
    """Show enhancement analytics and history stats."""
    config_dir = Path.home() / ".prompt-enhance"
    history_file = config_dir / "history.jsonl"

    if not history_file.exists():
        click.echo("No enhancement history found.")
        click.echo(f"History will be stored at: {history_file}")
        return

    import json

    entries = []
    with open(history_file) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    if not entries:
        click.echo("No enhancements recorded yet.")
        return

    # Calculate stats
    total = len(entries)
    modes: dict[str, int] = {}
    techniques: dict[str, int] = {}

    for entry in entries:
        mode = entry.get("analysis", {}).get("task_type", "unknown")
        modes[mode] = modes.get(mode, 0) + 1

        for tech in entry.get("techniques", {}).get("applied", []):
            techniques[tech] = techniques.get(tech, 0) + 1

    click.echo(click.style("═" * 50, fg="blue"))
    click.echo(click.style(" Prompt Enhancement Stats ", fg="blue", bold=True))
    click.echo(click.style("═" * 50, fg="blue"))
    click.echo(f"\nTotal enhancements: {total}")
    click.echo("\nBy task type:")
    for mode, count in sorted(modes.items(), key=lambda x: -x[1]):
        click.echo(f"  {mode}: {count} ({count*100//total}%)")

    click.echo("\nTechniques used:")
    for tech, count in sorted(techniques.items(), key=lambda x: -x[1]):
        click.echo(f"  {tech}: {count}")


def _init_config() -> None:
    """Create default configuration file."""
    config_dir = Path.home() / ".prompt-enhance"
    config_file = config_dir / "config.yaml"

    if config_file.exists():
        if not click.confirm(f"Config exists at {config_file}. Overwrite?"):
            return

    config_dir.mkdir(parents=True, exist_ok=True)

    default_config = """# Prompt Enhancer Configuration
# ~/.prompt-enhance/config.yaml

# Default task mode (auto, code, writing, analysis, creative, debug, refactor)
default_mode: auto

# Default output format (plain, md, json)
default_format: plain

# Maximum tokens for context injection
context_budget: 2000

# API configuration
api:
  provider: anthropic
  model: claude-sonnet-4-20250514
  # API key is read from ANTHROPIC_API_KEY environment variable

# Logging
logging:
  enabled: true
  history_file: ~/.prompt-enhance/history.jsonl
"""

    config_file.write_text(default_config)
    click.echo(f"✓ Created config at {config_file}")
    click.echo("\nDefault configuration written. Edit as needed.")


def _log_enhancement(result: EnhancedPrompt) -> None:
    """Log enhancement to history file."""
    import json

    config_dir = Path.home() / ".prompt-enhance"
    config_dir.mkdir(parents=True, exist_ok=True)
    history_file = config_dir / "history.jsonl"

    entry = result.to_dict()

    with open(history_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


# =============================================================================
# Entry Point
# =============================================================================


def cli() -> None:
    """Entry point for console script."""
    main()


if __name__ == "__main__":
    cli()
