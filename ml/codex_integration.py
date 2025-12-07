"""
OpenAI Codex-Style Integration
Modern code generation using GPT-4 and GPT-3.5-turbo

Note: The original Codex API was deprecated in March 2023.
This integration uses GPT-4 and GPT-3.5-turbo as replacements,
which provide superior code generation capabilities.

Features:
- Code generation (functions, classes, full applications)
- Code completion and suggestions
- Code explanation and documentation
- Code review and optimization
- Multi-language support (Python, JavaScript, TypeScript, etc.)
- Context-aware generation with repository understanding
"""

from datetime import datetime
import logging
import os
from typing import Any, Literal


try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from config.unified_config import get_config


logger = logging.getLogger(__name__)


class CodexIntegration:
    """
    Modern code generation using OpenAI GPT-4 and GPT-3.5-turbo.
    Provides Codex-style functionality with improved capabilities.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize Codex integration

        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
        """
        config = get_config()
        self.api_key = api_key or config.ai.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.is_consequential = config.ai.openai_is_consequential
        self.client = None

        if self.api_key and AsyncOpenAI:
            # Set x-openai-isConsequential header for high-stakes operations
            # Per OpenAI safety features: marks requests that could have significant real-world consequences
            default_headers = {"x-openai-isConsequential": str(self.is_consequential).lower()}
            self.client = AsyncOpenAI(api_key=self.api_key, default_headers=default_headers)
            logger.info(
                f"🤖 OpenAI Codex Integration initialized (using GPT-4, consequential={self.is_consequential})"
            )
        else:
            if not self.api_key:
                logger.warning("⚠️  OpenAI API key not configured")
            if not AsyncOpenAI:
                logger.warning("⚠️  OpenAI library not installed - run: pip install openai")

        # Model configurations
        self.models = {
            "gpt-4": {
                "name": "gpt-4-turbo-preview",
                "description": "Most capable code generation model",
                "max_tokens": 4096,
                "temperature": 0.2,
            },
            "gpt-3.5": {
                "name": "gpt-3.5-turbo",
                "description": "Fast and efficient code generation",
                "max_tokens": 2048,
                "temperature": 0.2,
            },
        }

        # Language-specific configurations
        self.language_configs = {
            "python": {
                "extension": ".py",
                "comment_style": "#",
                "framework_hints": ["FastAPI", "Django", "Flask", "SQLAlchemy"],
            },
            "javascript": {
                "extension": ".js",
                "comment_style": "//",
                "framework_hints": ["React", "Node.js", "Express", "Next.js"],
            },
            "typescript": {
                "extension": ".ts",
                "comment_style": "//",
                "framework_hints": ["React", "Angular", "NestJS", "TypeScript"],
            },
            "java": {
                "extension": ".java",
                "comment_style": "//",
                "framework_hints": ["Spring", "Hibernate"],
            },
            "go": {
                "extension": ".go",
                "comment_style": "//",
                "framework_hints": ["Gin", "Echo", "GORM"],
            },
            "rust": {
                "extension": ".rs",
                "comment_style": "//",
                "framework_hints": ["Actix", "Rocket", "Tokio"],
            },
        }

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        model: Literal["gpt-4", "gpt-3.5"] = "gpt-4",
        max_tokens: int | None = None,
        temperature: float | None = None,
        context: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate code based on natural language description

        Args:
            prompt: Natural language description of what to generate
            language: Programming language (python, javascript, typescript, etc.)
            model: Model to use (gpt-4 or gpt-3.5)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            context: Additional context (existing code, dependencies, etc.)

        Returns:
            Dict containing generated code and metadata
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            # Build system message with language-specific context
            system_message = self._build_system_message(language, context)

            # Build user prompt
            user_message = self._build_code_generation_prompt(prompt, language, context)

            # Get model configuration
            model_config = self.models[model]

            # Make API call
            response = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens or model_config["max_tokens"],
                temperature=temperature or model_config["temperature"],
                n=1,
            )

            # Extract generated code
            generated_code = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Parse and clean code
            code = self._extract_code_block(generated_code, language)

            return {
                "status": "success",
                "code": code,
                "raw_response": generated_code,
                "language": language,
                "model": model_config["name"],
                "finish_reason": finish_reason,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def complete_code(
        self,
        code_prefix: str,
        language: str = "python",
        model: Literal["gpt-4", "gpt-3.5"] = "gpt-3.5",
    ) -> dict[str, Any]:
        """
        Complete partial code (like GitHub Copilot)

        Args:
            code_prefix: Partial code to complete
            language: Programming language
            model: Model to use

        Returns:
            Dict containing code completion suggestions
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            system_message = (
                f"You are an expert {language} programmer. Complete the following code naturally and correctly."
            )

            user_message = f"```{language}\n{code_prefix}\n```\n\nComplete this code:"

            model_config = self.models[model]

            response = await self.client.chat.completions.create(
                model=model_config["name"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1024,
                temperature=0.1,  # Low temperature for deterministic completion
                n=3,  # Generate 3 alternatives
            )

            completions = []
            for choice in response.choices:
                code = self._extract_code_block(choice.message.content, language)
                completions.append({"code": code, "finish_reason": choice.finish_reason})

            return {
                "status": "success",
                "completions": completions,
                "language": language,
                "model": model_config["name"],
                "tokens_used": response.usage.total_tokens,
            }

        except Exception as e:
            logger.error(f"Code completion failed: {e}")
            return {"status": "error", "error": str(e)}

    async def explain_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Generate detailed explanation of code

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Dict containing code explanation
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            system_message = "You are an expert programmer who explains code clearly and thoroughly."

            user_message = f"Explain this {language} code in detail:\n\n```{language}\n{code}\n```"

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=2048,
                temperature=0.3,
            )

            explanation = response.choices[0].message.content

            return {
                "status": "success",
                "explanation": explanation,
                "language": language,
                "tokens_used": response.usage.total_tokens,
            }

        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def review_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Review code for issues, bugs, and improvements

        Args:
            code: Code to review
            language: Programming language

        Returns:
            Dict containing code review with suggestions
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            system_message = """You are an expert code reviewer. Analyze code for:
- Bugs and logic errors
- Security vulnerabilities
- Performance issues
- Code style and best practices
- Potential improvements

Provide specific, actionable feedback."""

            user_message = f"Review this {language} code:\n\n```{language}\n{code}\n```"

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=2048,
                temperature=0.2,
            )

            review = response.choices[0].message.content

            return {
                "status": "success",
                "review": review,
                "language": language,
                "tokens_used": response.usage.total_tokens,
            }

        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_documentation(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language

        Returns:
            Dict containing generated documentation
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            system_message = f"Generate comprehensive documentation for {language} code including docstrings, type hints, and usage examples."

            user_message = f"Generate documentation for:\n\n```{language}\n{code}\n```"

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=2048,
                temperature=0.2,
            )

            documentation = response.choices[0].message.content

            return {
                "status": "success",
                "documentation": documentation,
                "language": language,
                "tokens_used": response.usage.total_tokens,
            }

        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return {"status": "error", "error": str(e)}

    async def optimize_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Optimize code for performance and readability

        Args:
            code: Code to optimize
            language: Programming language

        Returns:
            Dict containing optimized code and explanation
        """
        if not self.client:
            return {"status": "error", "error": "OpenAI client not initialized"}

        try:
            system_message = f"Optimize this {language} code for performance, readability, and best practices. Explain what was optimized."

            user_message = f"Optimize this code:\n\n```{language}\n{code}\n```"

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=2048,
                temperature=0.2,
            )

            result = response.choices[0].message.content
            optimized_code = self._extract_code_block(result, language)

            return {
                "status": "success",
                "original_code": code,
                "optimized_code": optimized_code,
                "explanation": result,
                "language": language,
                "tokens_used": response.usage.total_tokens,
            }

        except Exception as e:
            logger.error(f"Code optimization failed: {e}")
            return {"status": "error", "error": str(e)}

    def _build_system_message(self, language: str, context: list[str] | None = None) -> str:
        """Build system message with language-specific context"""
        lang_config = self.language_configs.get(language, {})
        frameworks = lang_config.get("framework_hints", [])

        message = f"You are an expert {language} programmer. "
        message += "Generate clean, well-documented, production-ready code. "

        if frameworks:
            message += f"Prefer using popular frameworks like {', '.join(frameworks[:2])}. "

        if context:
            message += "\n\nAdditional context:\n" + "\n".join(context)

        return message

    def _build_code_generation_prompt(self, prompt: str, language: str, context: list[str] | None = None) -> str:
        """Build user prompt for code generation"""
        message = f"Generate {language} code for: {prompt}\n\n"
        message += "Requirements:\n"
        message += "- Include proper error handling\n"
        message += "- Add type hints (if supported)\n"
        message += "- Include docstrings/comments\n"
        message += "- Follow best practices\n"

        if context:
            message += "\nContext:\n" + "\n".join(context)

        return message

    def _extract_code_block(self, text: str, language: str) -> str:
        """Extract code from markdown code blocks"""
        # Try to find code block with language specifier
        markers = [f"```{language}", "```"]

        for marker in markers:
            if marker in text:
                parts = text.split(marker)
                if len(parts) >= 3:
                    # Get content between first pair of markers
                    code = parts[1].strip()
                    # Remove closing marker if present
                    if "```" in code:
                        code = code.split("```")[0].strip()
                    return code

        # If no code block found, return cleaned text
        return text.strip()

    def get_available_models(self) -> dict[str, Any]:
        """Get information about available models"""
        return {
            "models": self.models,
            "note": "Original Codex API deprecated March 2023. Using GPT-4 and GPT-3.5-turbo as replacements.",
        }

    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages"""
        return list(self.language_configs.keys())


# Global instance
codex = CodexIntegration()

logger.info("🤖 Codex Integration module loaded (GPT-4/GPT-3.5-turbo)")
