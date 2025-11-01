from security.jwt_auth import get_current_user

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ml.codex_integration import codex
from ml.codex_orchestrator import codex_orchestrator
from typing import List, Literal, Optional
import ast
import logging

"""
Codex Integration API Endpoints
OpenAI GPT-4/GPT-3.5-turbo powered code generation

Endpoints:
- POST /api/v1/codex/generate - Generate code from description
- POST /api/v1/codex/complete - Complete partial code
- POST /api/v1/codex/explain - Explain code
- POST /api/v1/codex/review - Review code for issues
- POST /api/v1/codex/document - Generate documentation
- POST /api/v1/codex/optimize - Optimize code
- GET /api/v1/codex/models - List available models
- GET /api/v1/codex/languages - List supported languages
"""

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""

    prompt: str = Field(..., description="Natural language description of what to generate")
    language: str = Field(default="python", description="Programming language")
    model: Literal["gpt-4", "gpt-3.5"] = Field(default="gpt-4", description="Model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature (0.0-1.0)")
    context: Optional[List[str]] = Field(default=None, description="Additional context")


class CodeCompletionRequest(BaseModel):
    """Request model for code completion"""

    code_prefix: str = Field(..., description="Partial code to complete")
    language: str = Field(default="python", description="Programming language")
    model: Literal["gpt-4", "gpt-3.5"] = Field(default="gpt-3.5", description="Model to use")


class CodeExplanationRequest(BaseModel):
    """Request model for code explanation"""

    code: str = Field(..., description="Code to explain")
    language: str = Field(default="python", description="Programming language")


class CodeReviewRequest(BaseModel):
    """Request model for code review"""

    code: str = Field(..., description="Code to review")
    language: str = Field(default="python", description="Programming language")


class CodeDocumentationRequest(BaseModel):
    """Request model for documentation generation"""

    code: str = Field(..., description="Code to document")
    language: str = Field(default="python", description="Programming language")


class CodeOptimizationRequest(BaseModel):
    """Request model for code optimization"""

    code: str = Field(..., description="Code to optimize")
    language: str = Field(default="python", description="Programming language")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/codex/generate", tags=["codex"])
async def generate_code(request: CodeGenerationRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate code from natural language description

    Uses GPT-4 or GPT-3.5-turbo to generate production-ready code based on
    your description. Supports multiple programming languages.

    Example:
    ```json
    {
        "prompt": "Create a FastAPI endpoint that returns user profile",
        "language": "python",
        "model": "gpt-4",
        "context": ["Using SQLAlchemy for database", "Include error handling"]
    }
    ```
    """
    try:
        result = await codex.generate_code(
            prompt=request.prompt,
            language=request.language,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            context=request.context,
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/codex/complete", tags=["codex"])
async def complete_code(request: CodeCompletionRequest, current_user: dict = Depends(get_current_user)):
    """
    Complete partial code (like GitHub Copilot)

    Provides intelligent code completion suggestions based on your partial code.
    Returns multiple alternatives to choose from.

    Example:
    ```json
    {
        "code_prefix": "def calculate_fibonacci(n):\\n    ",
        "language": "python",
        "model": "gpt-3.5"
    }
    ```
    """
    try:
        result = await codex.complete_code(
            code_prefix=request.code_prefix,
            language=request.language,
            model=request.model,
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code completion failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/codex/explain", tags=["codex"])
async def explain_code(request: CodeExplanationRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate detailed explanation of code

    Analyzes code and provides a comprehensive explanation of what it does,
    how it works, and any important details.

    Example:
    ```json
    {
        "code": "def quicksort(arr):\\n    if len(arr) <= 1:\\n        return arr",
        "language": "python"
    }
    ```
    """
    try:
        result = await codex.explain_code(code=request.code, language=request.language)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code explanation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/codex/review", tags=["codex"])
async def review_code(request: CodeReviewRequest, current_user: dict = Depends(get_current_user)):
    """
    Review code for bugs, security issues, and improvements

    Performs comprehensive code review checking for:
    - Bugs and logic errors
    - Security vulnerabilities
    - Performance issues
    - Code style and best practices
    - Potential improvements

    Example:
    ```json
    {
        "code": "user_input = request.args.get('query')\\nresult = db.execute(user_input)",
        "language": "python"
    }
    ```
    """
    try:
        result = await codex.review_code(code=request.code, language=request.language)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/codex/document", tags=["codex"])
async def generate_documentation(request: CodeDocumentationRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate comprehensive documentation for code

    Creates detailed documentation including:
    - Docstrings/comments
    - Type hints
    - Usage examples
    - Parameter descriptions
    - Return value documentation

    Example:
    ```json
    {
        "code": "def process_payment(amount, currency, user_id):\\n    pass",
        "language": "python"
    }
    ```
    """
    try:
        result = await codex.generate_documentation(code=request.code, language=request.language)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/codex/optimize", tags=["codex"])
async def optimize_code(request: CodeOptimizationRequest, current_user: dict = Depends(get_current_user)):
    """
    Optimize code for performance and readability

    Analyzes code and provides optimized version with:
    - Better performance
    - Improved readability
    - Best practices applied
    - Explanation of changes

    Example:
    ```json
    {
        "code": "result = []\\nfor i, item in enumerate(items):\\n    result.append(items[i] * 2)",
        "language": "python"
    }
    ```
    """
    try:
        result = await codex.optimize_code(code=request.code, language=request.language)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code optimization failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/codex/models", tags=["codex"])
async def get_available_models(current_user: dict = Depends(get_current_user)):
    """
    Get information about available models

    Returns details about GPT-4 and GPT-3.5-turbo models including:
    - Model names
    - Capabilities
    - Token limits
    - Recommended use cases

    Note: Original Codex API was deprecated in March 2023.
    We now use GPT-4 and GPT-3.5-turbo as superior replacements.
    """
    return codex.get_available_models()


@router.get("/codex/languages", tags=["codex"])
async def get_supported_languages(current_user: dict = Depends(get_current_user)):
    """
    Get list of supported programming languages

    Returns array of supported languages including:
    - Python
    - JavaScript
    - TypeScript
    - Java
    - Go
    - Rust
    - And more...
    """
    return {"languages": codex.get_supported_languages()}


# ============================================================================
# CODE HEALING ORCHESTRATION ENDPOINTS
# ============================================================================


class CodeHealingRequest(BaseModel):
    """Request model for code healing orchestration"""

    code: str = Field(..., description="Code to heal")
    language: str = Field(default="python", description="Programming language")
    context: Optional[dict] = Field(default=None, description="Additional context")
    auto_apply: bool = Field(default=False, description="Automatically apply fixes (use with caution)")


@router.post("/codex/heal", tags=["codex-orchestration"])
async def heal_code(request: CodeHealingRequest, current_user: dict = Depends(get_current_user)):
    """
    AI-Powered Code Healing with Orchestration

    Uses GPT-4 to orchestrate intelligent code healing:
    1. Scans code for issues (security, bugs, performance)
    2. Generates AI-powered healing strategy
    3. Creates optimized fixes using Codex
    4. Validates fixes for safety
    5. Optionally applies fixes automatically

    This endpoint coordinates multiple healing agents:
    - Scanner: Detects code issues
    - Codex: Analyzes and generates fixes
    - Validator: Ensures fixes are safe
    - Self-healing: Applies corrections

    Example:
    ```json
    {
        "code": "def process_user_input(data):\\n    result = ast.literal_eval(data)\\n    return result",
        "language": "python",
        "auto_apply": false,
        "context": {
            "file_path": "app/utils.py",
            "framework": "FastAPI"
        }
    }
    ```

    Returns comprehensive healing report with:
    - Issues found and severity
    - AI-generated healing strategy
    - Proposed fixes with explanations
    - Validation results
    - Healed code (if auto_apply=true)
    """
    try:
        result = await codex_orchestrator.heal_code(
            code=request.code,
            language=request.language,
            context=request.context,
            auto_apply=request.auto_apply,
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code healing failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/codex/healing/stats", tags=["codex-orchestration"])
async def get_healing_stats(current_user: dict = Depends(get_current_user)):
    """
    Get Code Healing Statistics

    Returns statistics about code healing operations:
    - Total healings performed
    - Success rate
    - Recent healing history
    - Common issue patterns

    Useful for monitoring the effectiveness of AI-powered healing.
    """
    return codex_orchestrator.get_healing_stats()


logger.info("✅ Codex API endpoints registered (including orchestration)")
