"""
Structured Output Validation for AI Agents - 2025 Best Practices

Per Pydantic AI and vLLM Structured Outputs (2025):
- Type-safe LLM responses with Pydantic schemas
- Guaranteed valid JSON with schema adherence
- Output validation at generation time
- Response transformation pipeline

References:
- https://ai.pydantic.dev/agents/
- https://developers.redhat.com/articles/2025/06/03/structured-outputs-vllm-guiding-ai-responses
- https://www.anthropic.com/engineering/writing-tools-for-agents
- Per Truth Protocol Rule #7: Input/Output Validation

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ============================================================================
# OUTPUT STATUS AND ERROR MODELS
# ============================================================================


class OutputStatus(str, Enum):
    """Status of structured output validation."""

    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    PARSING_ERROR = "parsing_error"
    SCHEMA_MISMATCH = "schema_mismatch"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


class OutputValidationError(BaseModel):
    """Detailed error information for validation failures."""

    field: str | None = None
    message: str
    input_value: Any = None
    error_type: str = "validation_error"


class StructuredOutputResult(BaseModel, Generic[T]):
    """
    Result wrapper for structured output validation.

    Per Pydantic AI: "Pydantic performs the output validation, and it'll be
    typed as a bool since its type is derived from the output_type generic
    parameter of the agent."
    """

    status: OutputStatus
    data: T | None = None
    raw_output: str | None = None
    errors: list[OutputValidationError] = Field(default_factory=list)
    validation_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# COMMON AGENT OUTPUT SCHEMAS
# ============================================================================


class AgentThought(BaseModel):
    """
    Structured thought output for chain-of-thought reasoning.

    Per Anthropic: "Giving Claude time to think through its response
    before producing the final answer leads to better performance."
    """

    step: int = Field(ge=1, description="Step number in reasoning chain")
    thought: str = Field(min_length=1, description="The reasoning step")
    confidence: float = Field(ge=0.0, le=1.0, default=0.8, description="Confidence 0-1")


class AgentAction(BaseModel):
    """Structured action output for tool invocation."""

    tool_name: str = Field(min_length=1, description="Name of tool to invoke")
    parameters: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = Field(default="", description="Why this action was chosen")


class AgentObservation(BaseModel):
    """Structured observation from tool execution."""

    tool_name: str
    result: Any
    success: bool = True
    error_message: str | None = None
    execution_time_ms: float = 0.0


class ReActStep(BaseModel):
    """
    A single ReAct (Reasoning + Acting) step.

    Per IBM: "ReAct agents combine chain of thought reasoning with
    external tool use through Reasoning → Action → Observation cycles."
    """

    thought: AgentThought
    action: AgentAction | None = None
    observation: AgentObservation | None = None
    is_final: bool = False


class AgentResponse(BaseModel):
    """
    Standard structured response from an agent.

    Provides consistent output format across all agents.
    """

    success: bool
    message: str
    result: dict[str, Any] | None = None
    reasoning_steps: list[AgentThought] = Field(default_factory=list)
    actions_taken: list[AgentAction] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    model: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeAnalysisOutput(BaseModel):
    """Structured output for code analysis tasks."""

    files_analyzed: int = 0
    issues_found: list[dict[str, Any]] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    quality_score: float = Field(ge=0.0, le=100.0, default=0.0)
    summary: str = ""


class ContentGenerationOutput(BaseModel):
    """Structured output for content generation tasks."""

    content: str
    content_type: str
    word_count: int = 0
    language: str = "en"
    tone: str = ""
    keywords: list[str] = Field(default_factory=list)
    seo_score: float | None = None

    @field_validator("word_count", mode="before")
    @classmethod
    def calculate_word_count(cls, v, info):
        """Auto-calculate word count if not provided."""
        if v == 0 and "content" in info.data:
            return len(info.data["content"].split())
        return v


class TaskPlanOutput(BaseModel):
    """Structured output for task planning."""

    task_name: str
    steps: list[dict[str, Any]]
    estimated_duration_minutes: int | None = None
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


# ============================================================================
# OUTPUT VALIDATOR
# ============================================================================


class OutputValidator:
    """
    Validates and transforms LLM outputs to structured schemas.

    Per vLLM: "Without constraints, LLMs may hallucinate or provide
    overly verbose or ambiguous results. With structured outputs,
    we effectively enforce output conformity at generation time."
    """

    def __init__(self):
        self._registered_schemas: dict[str, type[BaseModel]] = {}
        self._register_default_schemas()

    def _register_default_schemas(self):
        """Register built-in output schemas."""
        self.register_schema("agent_response", AgentResponse)
        self.register_schema("code_analysis", CodeAnalysisOutput)
        self.register_schema("content_generation", ContentGenerationOutput)
        self.register_schema("task_plan", TaskPlanOutput)
        self.register_schema("react_step", ReActStep)

    def register_schema(self, name: str, schema: type[BaseModel]):
        """Register a custom output schema."""
        self._registered_schemas[name] = schema
        logger.debug(f"Registered output schema: {name}")

    def get_schema(self, name: str) -> type[BaseModel] | None:
        """Get a registered schema by name."""
        return self._registered_schemas.get(name)

    def validate(
        self,
        raw_output: str,
        schema: type[T],
        strict: bool = True,
    ) -> StructuredOutputResult[T]:
        """
        Validate raw LLM output against a Pydantic schema.

        Args:
            raw_output: Raw string output from LLM
            schema: Pydantic model class to validate against
            strict: If True, fail on any validation error

        Returns:
            StructuredOutputResult with validated data or errors
        """
        import time

        start_time = time.time()
        errors = []

        try:
            # Try to extract JSON from output
            json_data = self._extract_json(raw_output)

            if json_data is None:
                return StructuredOutputResult(
                    status=OutputStatus.PARSING_ERROR,
                    raw_output=raw_output,
                    errors=[
                        OutputValidationError(
                            message="Could not extract valid JSON from output",
                            error_type="parsing_error",
                        )
                    ],
                    validation_time_ms=(time.time() - start_time) * 1000,
                )

            # Validate against schema
            validated_data = schema.model_validate(json_data)

            return StructuredOutputResult(
                status=OutputStatus.SUCCESS,
                data=validated_data,
                raw_output=raw_output,
                validation_time_ms=(time.time() - start_time) * 1000,
            )

        except ValidationError as e:
            for error in e.errors():
                errors.append(
                    OutputValidationError(
                        field=".".join(str(loc) for loc in error["loc"]),
                        message=error["msg"],
                        input_value=error.get("input"),
                        error_type=error["type"],
                    )
                )

            return StructuredOutputResult(
                status=OutputStatus.VALIDATION_ERROR,
                raw_output=raw_output,
                errors=errors,
                validation_time_ms=(time.time() - start_time) * 1000,
            )

        except json.JSONDecodeError as e:
            return StructuredOutputResult(
                status=OutputStatus.PARSING_ERROR,
                raw_output=raw_output,
                errors=[
                    OutputValidationError(
                        message=f"JSON parsing error: {e}",
                        error_type="json_decode_error",
                    )
                ],
                validation_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return StructuredOutputResult(
                status=OutputStatus.UNKNOWN_ERROR,
                raw_output=raw_output,
                errors=[
                    OutputValidationError(
                        message=str(e),
                        error_type="unknown_error",
                    )
                ],
                validation_time_ms=(time.time() - start_time) * 1000,
            )

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract JSON from LLM output.

        Handles various formats:
        - Pure JSON
        - JSON in code blocks
        - JSON with surrounding text
        """
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code blocks
        code_block_patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"\{[\s\S]*\}",
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        return None

    def create_output_schema_prompt(self, schema: type[BaseModel]) -> str:
        """
        Create a prompt fragment describing the expected output schema.

        Per Anthropic: "Even your tool response structure—for example XML,
        JSON, or Markdown—can have an impact on evaluation performance."
        """
        schema_json = schema.model_json_schema()

        prompt = f"""
## Expected Output Format

You MUST respond with valid JSON that conforms to this schema:

```json
{json.dumps(schema_json, indent=2)}
```

Important:
- Respond ONLY with the JSON object, no additional text
- Ensure all required fields are present
- Use the correct data types as specified
"""
        return prompt


class OutputTransformer:
    """
    Transforms and normalizes agent outputs.

    Provides response transformation pipeline for compatibility.
    """

    def __init__(self):
        self._transformers: dict[str, callable] = {}

    def register_transformer(
        self,
        from_format: str,
        to_format: str,
        transformer: callable,
    ):
        """Register a transformation function."""
        key = f"{from_format}:{to_format}"
        self._transformers[key] = transformer

    def transform(
        self,
        data: BaseModel,
        to_format: str,
    ) -> dict[str, Any] | str:
        """
        Transform output to a different format.

        Args:
            data: Validated Pydantic model
            to_format: Target format (json, xml, markdown, etc.)

        Returns:
            Transformed output
        """
        from_format = type(data).__name__
        key = f"{from_format}:{to_format}"

        if key in self._transformers:
            return self._transformers[key](data)

        # Default transformations
        if to_format == "json":
            return data.model_dump()
        elif to_format == "json_string":
            return data.model_dump_json(indent=2)
        elif to_format == "markdown":
            return self._to_markdown(data)
        else:
            return data.model_dump()

    def _to_markdown(self, data: BaseModel) -> str:
        """Convert Pydantic model to markdown format."""
        lines = [f"# {type(data).__name__}\n"]

        for field_name, field_value in data.model_dump().items():
            if isinstance(field_value, dict):
                lines.append(f"## {field_name}")
                lines.append(f"```json\n{json.dumps(field_value, indent=2)}\n```")
            elif isinstance(field_value, list):
                lines.append(f"## {field_name}")
                for item in field_value:
                    if isinstance(item, dict):
                        lines.append(f"- {json.dumps(item)}")
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(f"**{field_name}**: {field_value}")

            lines.append("")

        return "\n".join(lines)


# Global instances
_output_validator: OutputValidator | None = None
_output_transformer: OutputTransformer | None = None


def get_output_validator() -> OutputValidator:
    """Get global output validator instance."""
    global _output_validator
    if _output_validator is None:
        _output_validator = OutputValidator()
    return _output_validator


def get_output_transformer() -> OutputTransformer:
    """Get global output transformer instance."""
    global _output_transformer
    if _output_transformer is None:
        _output_transformer = OutputTransformer()
    return _output_transformer


# Convenience functions
def validate_output(
    raw_output: str,
    schema: type[T],
    strict: bool = True,
) -> StructuredOutputResult[T]:
    """Validate raw output against a schema."""
    return get_output_validator().validate(raw_output, schema, strict)


def create_schema_prompt(schema: type[BaseModel]) -> str:
    """Create a prompt fragment for expected output schema."""
    return get_output_validator().create_output_schema_prompt(schema)


__all__ = [
    "AgentAction",
    "AgentObservation",
    "AgentResponse",
    "AgentThought",
    "CodeAnalysisOutput",
    "ContentGenerationOutput",
    "OutputStatus",
    "OutputTransformer",
    "OutputValidationError",
    "OutputValidator",
    "ReActStep",
    "StructuredOutputResult",
    "TaskPlanOutput",
    "create_schema_prompt",
    "get_output_transformer",
    "get_output_validator",
    "validate_output",
]
