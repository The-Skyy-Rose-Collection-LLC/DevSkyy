#!/usr/bin/env python3
"""
DevSkyy Coding Architect Agent (Python SDK)

A full-featured coding architect agent specialized in TypeScript and Python development,
powered by Claude Agent SDK with 17 prompt engineering techniques.

Usage:
    python main.py "Your prompt here"

Example:
    python main.py "Review the code in src/main.py for best practices"
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

# Import Claude Agent SDK
try:
    from claude_agent_sdk import query
except ImportError:
    print("Error: claude-agent-sdk not installed. Run: pip install claude-agent-sdk")
    sys.exit(1)

# Import local modules
from prompts import SYSTEM_PROMPT, TASK_PROMPTS

from tools import PythonTools, TypeScriptTools

# Load environment variables
load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for the coding architect agent."""

    model: str = "claude-sonnet-4-5"
    working_directory: str = "."
    max_budget_usd: float = 10.0
    verbose: bool = False


@dataclass
class AgentResult:
    """Result from an agent query."""

    session_id: str
    result: str
    total_cost_usd: float
    duration_ms: int
    messages: list[dict[str, Any]]


class CodingArchitectAgent:
    """
    Coding Architect Agent specialized in TypeScript and Python.

    Features:
    - 17 prompt engineering techniques
    - TypeScript analysis tools
    - Python analysis tools
    - Code review, architecture design, debugging, refactoring

    Example:
        agent = CodingArchitectAgent(verbose=True)
        result = await agent.query("Review this Python code")
        print(result.result)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        working_directory: str | None = None,
        max_budget_usd: float = 10.0,
        verbose: bool = False,
    ):
        self.config = AgentConfig(
            model=model,
            working_directory=working_directory or os.getcwd(),
            max_budget_usd=max_budget_usd,
            verbose=verbose,
        )
        self.typescript_tools = TypeScriptTools()
        self.python_tools = PythonTools()

    async def query(
        self,
        prompt: str,
        on_message: Any | None = None,
    ) -> AgentResult:
        """
        Execute a query with the coding architect agent.

        Args:
            prompt: The prompt to send to the agent
            on_message: Optional callback for streaming messages

        Returns:
            AgentResult with the response
        """
        messages: list[dict[str, Any]] = []
        session_id = ""
        result_text = ""
        total_cost_usd = 0.0
        duration_ms = 0

        try:
            response = query(
                prompt=prompt,
                options={
                    "model": self.config.model,
                    "system_prompt": SYSTEM_PROMPT,
                    "cwd": self.config.working_directory,
                    "max_budget_usd": self.config.max_budget_usd,
                    "permission_mode": "default",
                    "allowed_tools": [
                        "Read",
                        "Write",
                        "Edit",
                        "Glob",
                        "Grep",
                        "Bash",
                    ],
                },
            )

            async for message in response:
                messages.append(message)
                msg_type = message.get("type", "")

                if msg_type == "system" and message.get("subtype") == "init":
                    session_id = message.get("session_id", "")
                    if self.config.verbose:
                        print(f"[Session] Started: {session_id}")
                        print(f"[Model] {message.get('model', 'unknown')}")

                elif msg_type == "assistant":
                    if self.config.verbose:
                        content = message.get("message", {}).get("content", "")
                        if isinstance(content, str) and content:
                            preview = content[:100] + "..." if len(content) > 100 else content
                            print(f"[Assistant] {preview}")

                elif msg_type == "result":
                    subtype = message.get("subtype", "")
                    if subtype == "success":
                        result_text = message.get("result", "")
                        total_cost_usd = message.get("total_cost_usd", 0.0)
                        duration_ms = message.get("duration_ms", 0)
                    else:
                        errors = message.get("errors", [])
                        print(f"[Error] {subtype}: {errors}")

                if on_message:
                    await on_message(message)

        except Exception as e:
            print(f"[Error] Query failed: {e}")
            raise

        return AgentResult(
            session_id=session_id,
            result=result_text,
            total_cost_usd=total_cost_usd,
            duration_ms=duration_ms,
            messages=messages,
        )

    async def review_code(self, file_path: str) -> AgentResult:
        """Review code with Chain-of-Thought reasoning."""
        prompt = f"""{TASK_PROMPTS['code_review'].template}

Please review the code in: {file_path}"""
        return await self.query(prompt)

    async def design_architecture(self, requirements: str) -> AgentResult:
        """Design architecture with Tree of Thoughts."""
        prompt = f"""{TASK_PROMPTS['architecture_design'].template}

Requirements: {requirements}"""
        return await self.query(prompt)

    async def debug_issue(
        self,
        issue: str,
        context: str | None = None,
    ) -> AgentResult:
        """Debug an issue with ReAct pattern."""
        prompt = f"""{TASK_PROMPTS['debugging'].template}

Issue: {issue}
{f'Context: {context}' if context else ''}"""
        return await self.query(prompt)

    async def refactor_code(
        self,
        file_path: str,
        goals: str | None = None,
    ) -> AgentResult:
        """Refactor code with Constitutional AI principles."""
        prompt = f"""{TASK_PROMPTS['refactoring'].template}

File to refactor: {file_path}
{f'Refactoring goals: {goals}' if goals else ''}"""
        return await self.query(prompt)

    async def analyze_typescript(self, target: str) -> AgentResult:
        """Analyze TypeScript code."""
        prompt = f"""{TASK_PROMPTS['typescript_analysis'].template}

Target: {target}"""
        return await self.query(prompt)

    async def analyze_python(self, target: str) -> AgentResult:
        """Analyze Python code."""
        prompt = f"""{TASK_PROMPTS['python_analysis'].template}

Target: {target}"""
        return await self.query(prompt)


def print_banner():
    """Print the agent banner."""
    print(
        """
╔══════════════════════════════════════════════════════════════════╗
║           DevSkyy Coding Architect Agent (Python)                ║
║   Expert in TypeScript & Python with 17 Prompt Techniques        ║
╚══════════════════════════════════════════════════════════════════╝
"""
    )


def print_usage():
    """Print usage information."""
    print(
        """
Usage:
  python main.py "<your prompt>"

Examples:
  python main.py "Review the code in src/main.py"
  python main.py "Design an architecture for a REST API"
  python main.py "Analyze the TypeScript project in ../src"

Environment:
  ANTHROPIC_API_KEY  - Your Anthropic API key (required)
"""
    )


async def main():
    """Main entry point."""
    args = sys.argv[1:]

    print_banner()

    if not args:
        print_usage()
        return

    prompt = " ".join(args)
    print(f"📝 Prompt: {prompt}\n")
    print("─" * 60)

    agent = CodingArchitectAgent(
        verbose=True,
        working_directory=os.getcwd(),
    )

    try:
        result = await agent.query(prompt)

        print("\n" + "─" * 60)
        print("\n📊 Result:\n")
        print(result.result)
        print("\n" + "─" * 60)
        print(f"💰 Cost: ${result.total_cost_usd:.4f}")
        print(f"⏱️  Duration: {result.duration_ms / 1000:.2f}s")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
