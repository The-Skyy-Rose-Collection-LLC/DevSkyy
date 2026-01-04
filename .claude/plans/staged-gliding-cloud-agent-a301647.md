# DevSkyy State-of-the-Art Transformation Plan

**Status**: Planning Phase
**Created**: 2026-01-03
**Priority**: Round Table → Dashboards → Dependencies
**Execution Model**: Phase-based with user approval gates

---

## 📋 Executive Summary

Transform DevSkyy from B+ (52/100) to A+ (90+) through systematic enhancement of:

1. **Round Table**: Add tool calling, ML-based scoring, statistical rigor, adaptive learning
2. **Dashboard**: WebSocket real-time updates, Three.js integration, missing UI components
3. **Dependencies**: Fix package declarations, ensure ML library availability

### Success Metrics

- All Round Table tests passing with 100% tool calling coverage
- ML-based scoring achieving 85%+ correlation with human judgment
- WebSocket latency <100ms for all real-time updates
- Zero dependency conflicts, Python 3.11-3.12 compatibility documented

---

## 🏗️ Architecture Overview

### Current State Analysis

**Round Table** (`/Users/coreyfoster/DevSkyy/llm/round_table.py`):

- ✅ 6 LLM providers registered (Claude, GPT-4, Gemini, Llama, Mistral, Cohere)
- ✅ PostgreSQL persistence with full schema
- ✅ 5 heuristic scoring metrics
- ✅ A/B testing with judge LLM
- ❌ NO tool calling support - critical gap
- ❌ NO tests (0 Round Table tests found)
- ❌ Heuristic scoring only (keyword matching, structure detection)
- ❌ No ML-based evaluation
- ❌ No statistical analysis beyond basic scoring
- ❌ No adaptive learning/provider profiling

**Dashboard** (`/Users/coreyfoster/DevSkyy/frontend/`):

- ✅ Next.js 15 with SWR hooks
- ✅ Complete API client (`lib/api.ts`)
- ✅ 6 SuperAgents fully connected
- ✅ CopilotKit AI assistant
- ✅ Three.js viewer using Google Model Viewer
- ❌ HTTP polling (2-30s intervals) - inefficient
- ❌ Three.js collections not integrated (5 experiences in `/src/collections/`)
- ❌ Missing UIs: Visual generation, virtual try-on, brand DNA editor

**Dependencies** (`pyproject.toml`, `requirements.txt`):

- ✅ sentence-transformers 5.2.0 installed
- ✅ scipy 1.16.3 installed
- ✅ numpy 2.2.6 installed
- ❌ chromadb in [mcp] extras only, should be main deps
- ❌ prometheus-client marked optional, should be main deps
- ❌ transformers not in main dependencies
- ❌ diffusers not in main dependencies
- ⚠️ Python 3.14 compatibility warning (Cohere SDK issue)

---

## 📦 Phase 1: Foundation - Dependencies & Environment

**Duration**: 1-2 hours
**Complexity**: ~300 LOC (changes to config files)
**Risk**: Low (configuration only)

### Implementation Steps

#### 1.1 Update `pyproject.toml` Dependencies

**File**: `/Users/coreyfoster/DevSkyy/pyproject.toml`

```toml
# Line 85-96: Add to main dependencies (after prometheus-client)
dependencies = [
    # ... existing ...
    "prometheus-client>=0.19",

    # ML & Vector Store (MOVE from optional-dependencies)
    "chromadb>=0.5.23",
    "transformers>=4.53.0",
    "diffusers>=0.25.0",
    "sentence-transformers>=5.2.0",
    "scipy>=1.16.3",
    "numpy>=2.2.6",

    # 3D & Visual Generation
    "Pillow>=10.0",
    "opencv-python>=4.8",
]
```

**Changes**:

- Move `chromadb` from line 158 ([mcp] extras) to main deps
- Move `transformers` from line 152 ([mcp] extras) to main deps
- Add `diffusers>=0.25.0` to main deps
- Keep `sentence-transformers`, `scipy`, `numpy` explicit in main deps
- Remove duplicates from [mcp] extras section

#### 1.2 Update `requirements.txt`

**File**: `/Users/coreyfoster/DevSkyy/requirements.txt`

```python
# Line 52-63: Add ML packages after torchvision
# ML & Evaluation
sentence-transformers>=5.2.0
scipy>=1.16.3
numpy>=2.2.6
transformers>=4.53.0

# Vector Store (REQUIRED for RAG)
chromadb>=0.5.23

# Image Generation (REQUIRED for visual pipeline)
diffusers>=0.25.0
```

**Changes**:

- Move `prometheus-client` from line 78 (optional) to after line 75 (Monitoring section)
- Add ML packages section with explicit versions
- Remove "optional but recommended" comment from prometheus-client

#### 1.3 Document Python Version Requirements

**File**: `/Users/coreyfoster/DevSkyy/README.md` (update existing section)

Add/update Python version requirements:

```markdown
## Requirements

**Python**: 3.11 - 3.12 (REQUIRED)
- ✅ Python 3.11 (recommended)
- ✅ Python 3.12
- ❌ Python 3.13+ (Cohere SDK compatibility issues)

**Note**: If using Python 3.14+, you may encounter dependency conflicts with the Cohere SDK.
Use `pyenv` or `conda` to manage Python versions:

```bash
# Install Python 3.12 with pyenv
pyenv install 3.12.0
pyenv local 3.12.0
```

```

#### 1.4 Verify Installations
**File**: Create `/Users/coreyfoster/DevSkyy/scripts/verify_dependencies.py`

```python
#!/usr/bin/env python3
"""
Verify all required ML dependencies are installed and working.
"""
import sys

def verify_imports():
    """Verify all critical imports work."""
    packages = [
        ("transformers", "transformers"),
        ("diffusers", "diffusers"),
        ("sentence_transformers", "sentence-transformers"),
        ("scipy", "scipy"),
        ("numpy", "numpy"),
        ("chromadb", "chromadb"),
        ("prometheus_client", "prometheus-client"),
    ]

    failed = []
    for module, package in packages:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed.append(package)

    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        print("Run: pip install -e .")
        sys.exit(1)
    else:
        print("\n✅ All dependencies verified!")
        sys.exit(0)

if __name__ == "__main__":
    verify_imports()
```

Make executable: `chmod +x scripts/verify_dependencies.py`

### Success Criteria

- [ ] `pip install -e .` completes without errors
- [ ] `python scripts/verify_dependencies.py` passes all checks
- [ ] No dependency conflicts reported
- [ ] All ML packages importable in Python 3.11/3.12
- [ ] Documentation updated with Python version requirements

### Test Plan

```bash
# In fresh virtual environment
python -m venv test_env
source test_env/bin/activate
pip install -e .
python scripts/verify_dependencies.py
pytest tests/test_llm.py -v  # Verify existing tests still pass
```

---

## 🔧 Phase 2: Round Table - Tool Calling Support (CRITICAL)

**Duration**: 4-6 hours
**Complexity**: ~600 LOC (modifications + tests)
**Risk**: Medium (core functionality change)

### Critical Gap

Current `compete()` method (line 668-766) does NOT accept or pass tools to LLM generators. This breaks agent workflows that require tool calling.

### Implementation Steps

#### 2.1 Update `LLMResponse` Data Class

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 69-80: Add tool_calls field
@dataclass(slots=True)
class LLMResponse:
    """Response from an LLM provider."""

    provider: LLMProvider
    content: str
    latency_ms: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)  # NEW
```

#### 2.2 Update `ResponseScores` for Tool Calling

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 82-102: Add tool_usage metric
@dataclass(slots=True)
class ResponseScores:
    """Scoring breakdown for a response."""

    relevance: float = 0.0
    quality: float = 0.0
    completeness: float = 0.0
    efficiency: float = 0.0
    brand_alignment: float = 0.0
    tool_usage: float = 0.0  # NEW: Tool calling effectiveness

    @property
    def total(self) -> float:
        """Weighted total score"""
        return (
            self.relevance * 0.20
            + self.quality * 0.20
            + self.completeness * 0.20
            + self.efficiency * 0.15
            + self.brand_alignment * 0.15
            + self.tool_usage * 0.10  # NEW: 10% weight
        )
```

#### 2.3 Add Tool Calling to `compete()` Method

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 668-676: Update method signature
async def compete(
    self,
    prompt: str,
    task_id: str | None = None,
    providers: list[LLMProvider] | None = None,
    context: dict | None = None,
    tools: list[dict[str, Any]] | None = None,  # NEW
    persist: bool = True,
) -> RoundTableResult:
    """
    Run Round Table competition.

    Args:
        prompt: The task prompt
        task_id: Optional task identifier
        providers: Providers to include (default: all registered)
        context: Additional context for generation
        tools: Tool definitions for LLM tool calling (NEW)
        persist: Whether to save to database
    """
```

```python
# Line 703: Pass tools to _generate_all
entries = await self._generate_all(prompt, active_providers, context, tools)
```

#### 2.4 Update `_generate_all()` to Support Tools

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 768-770: Update method signature
async def _generate_all(
    self,
    prompt: str,
    providers: list[LLMProvider],
    context: dict | None,
    tools: list[dict[str, Any]] | None = None,  # NEW
) -> list[RoundTableEntry]:
    """Generate responses from all providers in parallel"""
```

```python
# Line 774-822: Update generate_one to pass tools
async def generate_one(provider: LLMProvider) -> RoundTableEntry | None:
    generator = self._providers.get(provider)
    if not generator:
        return None

    start = time.time()
    try:
        # Pass tools to generator
        result = await generator(prompt, context, tools)  # MODIFIED
        latency = (time.time() - start) * 1000

        # Parse tool calls from response
        tool_calls = []
        if isinstance(result, dict):
            content = result.get("content") or result.get("text") or str(result)
            tokens = result.get("tokens_used", 0)
            cost = result.get("cost_usd", 0.0)
            model = result.get("model", "")
            tool_calls = result.get("tool_calls", [])  # NEW
        elif hasattr(result, "content"):
            content = result.content
            tokens = getattr(result, "tokens_used", 0)
            cost = getattr(result, "cost_usd", 0.0)
            model = getattr(result, "model", "")
            tool_calls = getattr(result, "tool_calls", [])  # NEW
        else:
            content = str(result)
            tokens = 0
            cost = 0.0
            model = ""
            tool_calls = []

        response = LLMResponse(
            provider=provider,
            content=content,
            latency_ms=latency,
            tokens_used=tokens,
            cost_usd=cost,
            model=model,
            tool_calls=tool_calls,  # NEW
        )

        return RoundTableEntry(provider=provider, response=response)
```

#### 2.5 Add Tool Usage Scoring

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 440-456: Update score_response method
def score_response(
    self,
    response: LLMResponse,
    prompt: str,
    task_context: dict | None = None,
    expected_tools: list[str] | None = None,  # NEW
) -> ResponseScores:
    """Score a response on all metrics"""
    content = response.content or ""

    if not content.strip() or response.error:
        return ResponseScores()

    return ResponseScores(
        relevance=self._score_relevance(content, prompt),
        quality=self._score_quality(content),
        completeness=self._score_completeness(content, prompt, task_context),
        efficiency=self._score_efficiency(response),
        brand_alignment=self._score_brand_alignment(content),
        tool_usage=self._score_tool_usage(response, expected_tools),  # NEW
    )
```

```python
# After line 600: Add new scoring method
def _score_tool_usage(
    self,
    response: LLMResponse,
    expected_tools: list[str] | None = None
) -> float:
    """
    Score tool calling effectiveness.

    Criteria:
    - Used tools when appropriate (not over/under-using)
    - Tool calls are valid and relevant
    - Correct tool selection
    """
    score = 50.0  # Base score

    if not expected_tools:
        # If no tools expected, penalize tool usage
        if response.tool_calls:
            score -= 20
        return max(0.0, min(100.0, score))

    # Tools were expected
    if not response.tool_calls:
        # No tools used when expected
        score -= 30
        return max(0.0, min(100.0, score))

    # Check tool call validity
    tool_names = [tc.get("name", "") for tc in response.tool_calls]

    # Check if used expected tools
    expected_set = set(expected_tools)
    used_set = set(tool_names)

    if used_set & expected_set:
        # Used at least some expected tools
        overlap = len(used_set & expected_set)
        score += (overlap / len(expected_set)) * 30

    # Penalize excessive tool calls
    if len(response.tool_calls) > len(expected_tools) + 2:
        score -= 10

    # Bonus for using all expected tools
    if expected_set.issubset(used_set):
        score += 10

    return max(0.0, min(100.0, score))
```

#### 2.6 Update Prompt Engineering for Tool Calling

**File**: `/Users/coreyfoster/DevSkyy/agents/base_super_agent.py`

```python
# Around line 276-300: Add tool-calling technique
TECHNIQUE_TOOL_CALLING = """You have access to tools. When a task requires external data or actions:
1. Identify which tool(s) are needed
2. Call tools with complete, accurate parameters
3. Wait for tool results before continuing
4. Integrate tool results into your response

Available tools: {available_tools}
"""

# Update _select_technique method (around line 320-360)
# Add tool-calling to technique mapping
TaskCategory.SEARCH: PromptTechnique.TOOL_CALLING,  # NEW
```

### Success Criteria

- [ ] `compete()` accepts `tools` parameter
- [ ] Tools passed to all LLM generators
- [ ] Tool calls parsed from responses
- [ ] Tool usage metric added to scoring (10% weight)
- [ ] Backward compatible (tools=None works)
- [ ] All existing Round Table tests pass
- [ ] New tool calling tests pass (see Phase 2.7)

### Test Plan

#### 2.7 Create Comprehensive Tests

**File**: Create `/Users/coreyfoster/DevSkyy/tests/test_round_table.py`

```python
"""
Tests for LLM Round Table with Tool Calling
"""
import pytest
from llm.round_table import (
    LLMRoundTable,
    LLMProvider,
    LLMResponse,
    ResponseScorer,
    CompetitionStatus,
)

@pytest.fixture
async def round_table():
    """Create Round Table instance"""
    rt = LLMRoundTable()
    await rt.initialize()

    # Register mock providers
    async def mock_claude(prompt, context, tools=None):
        return {
            "content": "Test response",
            "tokens_used": 100,
            "cost_usd": 0.01,
            "model": "claude-3-sonnet",
            "tool_calls": tools if tools else [],
        }

    async def mock_gpt4(prompt, context, tools=None):
        return {
            "content": "Another response",
            "tokens_used": 120,
            "cost_usd": 0.012,
            "model": "gpt-4",
            "tool_calls": tools if tools else [],
        }

    rt.register_provider(LLMProvider.CLAUDE, mock_claude)
    rt.register_provider(LLMProvider.GPT4, mock_gpt4)

    yield rt
    await rt.close()


@pytest.mark.asyncio
async def test_compete_without_tools(round_table):
    """Test backward compatibility - compete without tools"""
    result = await round_table.compete(
        prompt="Test prompt",
        persist=False
    )

    assert result.status == CompetitionStatus.COMPLETED
    assert result.winner is not None
    assert len(result.entries) == 2


@pytest.mark.asyncio
async def test_compete_with_tools(round_table):
    """Test tool calling integration"""
    tools = [
        {
            "name": "get_product",
            "description": "Get product details",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"}
                },
                "required": ["product_id"]
            }
        }
    ]

    result = await round_table.compete(
        prompt="Get product SKU-123",
        tools=tools,
        persist=False
    )

    assert result.status == CompetitionStatus.COMPLETED
    assert result.winner is not None

    # Check that tool calls were captured
    for entry in result.entries:
        assert hasattr(entry.response, "tool_calls")


def test_score_tool_usage_no_tools_expected():
    """Test tool usage scoring when no tools expected"""
    scorer = ResponseScorer()

    # Response with tool calls when none expected
    response = LLMResponse(
        provider=LLMProvider.CLAUDE,
        content="Test",
        latency_ms=1000,
        tool_calls=[{"name": "test_tool"}]
    )

    score = scorer._score_tool_usage(response, expected_tools=None)
    assert score < 50  # Penalized for unnecessary tool use


def test_score_tool_usage_with_expected_tools():
    """Test tool usage scoring with expected tools"""
    scorer = ResponseScorer()

    # Response using expected tools
    response = LLMResponse(
        provider=LLMProvider.CLAUDE,
        content="Test",
        latency_ms=1000,
        tool_calls=[
            {"name": "get_product"},
            {"name": "update_inventory"}
        ]
    )

    score = scorer._score_tool_usage(
        response,
        expected_tools=["get_product", "update_inventory"]
    )
    assert score >= 80  # High score for correct tool usage


def test_score_tool_usage_missing_tools():
    """Test scoring when expected tools not used"""
    scorer = ResponseScorer()

    # No tool calls when tools expected
    response = LLMResponse(
        provider=LLMProvider.CLAUDE,
        content="Test",
        latency_ms=1000,
        tool_calls=[]
    )

    score = scorer._score_tool_usage(
        response,
        expected_tools=["get_product"]
    )
    assert score < 30  # Low score for missing tools


@pytest.mark.asyncio
async def test_tool_calls_in_database(round_table):
    """Test that tool calls are persisted"""
    tools = [{"name": "test_tool"}]

    result = await round_table.compete(
        prompt="Test with tools",
        tools=tools,
        persist=True
    )

    # Verify in database (if initialized)
    if round_table._db._initialized:
        db_result = await round_table._db.get_result(result.id)
        assert db_result is not None
```

**Run tests**:

```bash
pytest tests/test_round_table.py -v
pytest tests/test_round_table.py::test_compete_with_tools -v
```

---

## 🤖 Phase 3: Round Table - Advanced ML-Based Scoring

**Duration**: 6-8 hours
**Complexity**: ~800 LOC (new module + integration)
**Risk**: Medium (new ML components)

### Implementation Steps

#### 3.1 Create Evaluation Metrics Module

**File**: Create `/Users/coreyfoster/DevSkyy/llm/evaluation_metrics.py`

```python
"""
ML-Based Evaluation Metrics for LLM Responses
==============================================

Advanced scoring using sentence transformers and NLP models.

Metrics:
- Coherence: Semantic similarity and logical flow
- Factuality: Fact-checking and groundedness
- Hallucination: Detection of unsupported claims
- Safety: Toxicity and harmful content detection

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)


@dataclass
class MLScores:
    """ML-based evaluation scores"""

    coherence: float = 0.0  # 0-100
    factuality: float = 0.0  # 0-100
    hallucination: float = 0.0  # 0-100 (lower is better)
    safety: float = 0.0  # 0-100

    @property
    def total(self) -> float:
        """Weighted total (hallucination inverted)"""
        return (
            self.coherence * 0.30
            + self.factuality * 0.30
            + (100 - self.hallucination) * 0.20  # Invert hallucination
            + self.safety * 0.20
        )


class MLEvaluator:
    """
    ML-based evaluator for LLM responses.

    Uses sentence transformers for semantic analysis.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize evaluator.

        Args:
            model_name: SentenceTransformer model name
        """
        self.model = SentenceTransformer(model_name)
        self._cache: dict[str, Any] = {}

        logger.info(f"Initialized MLEvaluator with {model_name}")

    def evaluate(
        self,
        response: str,
        prompt: str,
        context: str | None = None,
        ground_truth: str | None = None,
    ) -> MLScores:
        """
        Evaluate response with ML metrics.

        Args:
            response: LLM response to evaluate
            prompt: Original prompt
            context: Optional context/reference material
            ground_truth: Optional ground truth for factuality check

        Returns:
            MLScores with all metrics
        """
        return MLScores(
            coherence=self._score_coherence(response, prompt),
            factuality=self._score_factuality(response, context, ground_truth),
            hallucination=self._score_hallucination(response, context),
            safety=self._score_safety(response),
        )

    def _score_coherence(self, response: str, prompt: str) -> float:
        """
        Score semantic coherence between prompt and response.

        Uses sentence embeddings and cosine similarity.
        """
        if not response.strip() or not prompt.strip():
            return 0.0

        # Get embeddings
        embeddings = self.model.encode(
            [prompt, response],
            convert_to_tensor=True
        )

        # Compute cosine similarity
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

        # Convert to 0-100 scale
        score = (similarity + 1) * 50  # Cosine sim is -1 to 1

        # Bonus for consistent topic (check sentence-level coherence)
        sentences = response.split(". ")
        if len(sentences) > 1:
            sentence_embeddings = self.model.encode(sentences)
            avg_sim = np.mean([
                util.cos_sim(sentence_embeddings[i], sentence_embeddings[i+1]).item()
                for i in range(len(sentence_embeddings) - 1)
            ])
            score += avg_sim * 10  # Bonus for internal coherence

        return min(100.0, max(0.0, score))

    def _score_factuality(
        self,
        response: str,
        context: str | None,
        ground_truth: str | None
    ) -> float:
        """
        Score factual accuracy.

        If ground_truth provided, compare semantically.
        Otherwise, check grounding in context.
        """
        if not response.strip():
            return 0.0

        score = 50.0  # Base score

        # Check grounding in context
        if context:
            context_embedding = self.model.encode(context, convert_to_tensor=True)
            response_embedding = self.model.encode(response, convert_to_tensor=True)

            grounding = util.cos_sim(context_embedding, response_embedding).item()
            score += grounding * 30  # Up to 30 points for grounding

        # Check against ground truth
        if ground_truth:
            gt_embedding = self.model.encode(ground_truth, convert_to_tensor=True)
            resp_embedding = self.model.encode(response, convert_to_tensor=True)

            accuracy = util.cos_sim(gt_embedding, resp_embedding).item()
            score += accuracy * 20  # Up to 20 points for accuracy

        return min(100.0, max(0.0, score))

    def _score_hallucination(self, response: str, context: str | None) -> float:
        """
        Detect hallucinations (unsupported claims).

        Higher score = more hallucination (BAD)
        Lower score = less hallucination (GOOD)
        """
        if not response.strip():
            return 0.0

        hallucination_score = 0.0

        # If no context, can't check hallucination reliably
        if not context:
            return 50.0  # Neutral score

        # Split response into claims (sentences)
        claims = [s.strip() for s in response.split(". ") if s.strip()]

        if not claims:
            return 0.0

        # Check each claim against context
        context_embedding = self.model.encode(context, convert_to_tensor=True)

        unsupported_count = 0
        for claim in claims:
            claim_embedding = self.model.encode(claim, convert_to_tensor=True)
            support = util.cos_sim(context_embedding, claim_embedding).item()

            # If similarity < 0.3, likely hallucinated
            if support < 0.3:
                unsupported_count += 1

        # Calculate hallucination percentage
        hallucination_score = (unsupported_count / len(claims)) * 100

        return min(100.0, max(0.0, hallucination_score))

    def _score_safety(self, response: str) -> float:
        """
        Score content safety (toxicity, harmful content).

        Basic implementation - can be enhanced with toxicity models.
        """
        if not response.strip():
            return 100.0  # Empty is safe

        score = 100.0  # Start with safe

        # Check for harmful patterns (basic keyword detection)
        harmful_keywords = [
            "kill", "suicide", "bomb", "attack", "illegal", "hack",
            "weapon", "drug", "violence", "abuse"
        ]

        response_lower = response.lower()
        for keyword in harmful_keywords:
            if keyword in response_lower:
                score -= 15  # Penalty for each harmful keyword

        # Check for offensive language (basic)
        offensive_keywords = [
            "damn", "hell", "crap", "stupid", "idiot"
        ]

        for keyword in offensive_keywords:
            if keyword in response_lower:
                score -= 5  # Minor penalty

        return min(100.0, max(0.0, score))


# Factory function
def create_ml_evaluator(model_name: str = "all-MiniLM-L6-v2") -> MLEvaluator:
    """Create ML evaluator instance"""
    return MLEvaluator(model_name)


__all__ = [
    "MLScores",
    "MLEvaluator",
    "create_ml_evaluator",
]
```

#### 3.2 Integrate ML Scoring into Round Table

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 24: Add import
from llm.evaluation_metrics import MLEvaluator, MLScores

# Line 84-103: Add ml_scores field to ResponseScores
@dataclass(slots=True)
class ResponseScores:
    """Scoring breakdown for a response."""

    # Heuristic scores
    relevance: float = 0.0
    quality: float = 0.0
    completeness: float = 0.0
    efficiency: float = 0.0
    brand_alignment: float = 0.0
    tool_usage: float = 0.0

    # ML scores (NEW)
    ml_coherence: float = 0.0
    ml_factuality: float = 0.0
    ml_hallucination: float = 0.0
    ml_safety: float = 0.0

    @property
    def total(self) -> float:
        """Weighted total score"""
        # Heuristic: 60%
        heuristic = (
            self.relevance * 0.15
            + self.quality * 0.15
            + self.completeness * 0.15
            + self.efficiency * 0.05
            + self.brand_alignment * 0.05
            + self.tool_usage * 0.05
        ) * 0.60

        # ML: 40%
        ml = (
            self.ml_coherence * 0.12
            + self.ml_factuality * 0.12
            + (100 - self.ml_hallucination) * 0.08  # Inverted
            + self.ml_safety * 0.08
        ) * 0.40

        return heuristic + ml
```

```python
# Line 403: Add ML evaluator to ResponseScorer
class ResponseScorer:
    """Scores LLM responses on quality metrics"""

    # ... existing brand keywords ...

    def __init__(self, ml_enabled: bool = True):
        """
        Initialize scorer.

        Args:
            ml_enabled: Whether to use ML-based scoring
        """
        self.ml_enabled = ml_enabled
        self._ml_evaluator = None

        if ml_enabled:
            try:
                from llm.evaluation_metrics import create_ml_evaluator
                self._ml_evaluator = create_ml_evaluator()
                logger.info("ML evaluator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ML evaluator: {e}")
                self.ml_enabled = False
```

```python
# Line 440-465: Update score_response
def score_response(
    self,
    response: LLMResponse,
    prompt: str,
    task_context: dict | None = None,
    expected_tools: list[str] | None = None,
) -> ResponseScores:
    """Score a response on all metrics"""
    content = response.content or ""

    if not content.strip() or response.error:
        return ResponseScores()

    # Heuristic scores
    scores = ResponseScores(
        relevance=self._score_relevance(content, prompt),
        quality=self._score_quality(content),
        completeness=self._score_completeness(content, prompt, task_context),
        efficiency=self._score_efficiency(response),
        brand_alignment=self._score_brand_alignment(content),
        tool_usage=self._score_tool_usage(response, expected_tools),
    )

    # ML scores (if enabled)
    if self.ml_enabled and self._ml_evaluator:
        context = task_context.get("context") if task_context else None
        ground_truth = task_context.get("ground_truth") if task_context else None

        ml_scores = self._ml_evaluator.evaluate(
            response=content,
            prompt=prompt,
            context=context,
            ground_truth=ground_truth,
        )

        scores.ml_coherence = ml_scores.coherence
        scores.ml_factuality = ml_scores.factuality
        scores.ml_hallucination = ml_scores.hallucination
        scores.ml_safety = ml_scores.safety

    return scores
```

### Success Criteria

- [ ] ML evaluator initializes with sentence-transformers
- [ ] All 4 ML metrics implemented (coherence, factuality, hallucination, safety)
- [ ] ML scores integrated into total score (40% weight)
- [ ] Graceful fallback if ML disabled
- [ ] Performance acceptable (<500ms per evaluation)
- [ ] Tests pass with ML scoring enabled/disabled

### Test Plan

#### 3.3 Create ML Evaluation Tests

**File**: Create `/Users/coreyfoster/DevSkyy/tests/test_evaluation_metrics.py`

```python
"""
Tests for ML-based evaluation metrics
"""
import pytest
from llm.evaluation_metrics import MLEvaluator, create_ml_evaluator


@pytest.fixture
def evaluator():
    """Create ML evaluator"""
    return create_ml_evaluator()


def test_coherence_high(evaluator):
    """Test coherence with highly related prompt/response"""
    prompt = "What is the capital of France?"
    response = "The capital of France is Paris."

    scores = evaluator.evaluate(response, prompt)
    assert scores.coherence > 70


def test_coherence_low(evaluator):
    """Test coherence with unrelated prompt/response"""
    prompt = "What is the capital of France?"
    response = "I like pizza and ice cream on sunny days."

    scores = evaluator.evaluate(response, prompt)
    assert scores.coherence < 50


def test_factuality_with_ground_truth(evaluator):
    """Test factuality against ground truth"""
    prompt = "What is 2+2?"
    response = "2+2 equals 4"
    ground_truth = "The answer is 4"

    scores = evaluator.evaluate(response, prompt, ground_truth=ground_truth)
    assert scores.factuality > 70


def test_hallucination_detection(evaluator):
    """Test hallucination detection"""
    context = "The product costs $50 and is available in red and blue."
    response = "This product is $50 in red, blue, and green colors."

    scores = evaluator.evaluate(response, "", context=context)
    # Should detect "green" as hallucination
    assert scores.hallucination > 20


def test_safety_harmful_content(evaluator):
    """Test safety scoring with harmful content"""
    response = "You should hack into the system and steal data."

    scores = evaluator.evaluate(response, "")
    assert scores.safety < 50  # Low safety score


def test_safety_safe_content(evaluator):
    """Test safety scoring with safe content"""
    response = "The new product features include improved design and better performance."

    scores = evaluator.evaluate(response, "")
    assert scores.safety > 90


@pytest.mark.asyncio
async def test_round_table_with_ml_scoring():
    """Integration test - Round Table with ML scoring"""
    from llm.round_table import LLMRoundTable, LLMProvider

    rt = LLMRoundTable()
    await rt.initialize()

    # Mock provider
    async def mock_provider(prompt, context, tools=None):
        return {
            "content": "High quality response with good coherence.",
            "tokens_used": 50,
            "cost_usd": 0.005,
            "model": "test",
        }

    rt.register_provider(LLMProvider.CLAUDE, mock_provider)

    result = await rt.compete(
        prompt="Test prompt",
        persist=False
    )

    # Check ML scores are populated
    for entry in result.entries:
        assert entry.scores.ml_coherence >= 0
        assert entry.scores.ml_factuality >= 0
        assert entry.scores.ml_hallucination >= 0
        assert entry.scores.ml_safety >= 0

    await rt.close()
```

**Run tests**:

```bash
pytest tests/test_evaluation_metrics.py -v
pytest tests/test_evaluation_metrics.py::test_round_table_with_ml_scoring -v
```

---

## 📊 Phase 4: Round Table - Statistical Rigor & Adaptive Learning

**Duration**: 6-8 hours
**Complexity**: ~700 LOC (two new modules)
**Risk**: Medium (statistical analysis + persistence)

### Implementation Steps

#### 4.1 Create Statistical Analysis Module

**File**: Create `/Users/coreyfoster/DevSkyy/llm/statistics.py`

```python
"""
Statistical Analysis for A/B Testing and Round Table
=====================================================

Bayesian analysis, p-values, confidence intervals, effect sizes.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class StatisticalResult:
    """Statistical analysis result"""

    mean_a: float
    mean_b: float
    std_a: float
    std_b: float
    effect_size: float  # Cohen's d
    confidence_interval: tuple[float, float]  # 95% CI for difference
    p_value: float
    is_significant: bool  # p < 0.05
    bayesian_probability: float  # P(B > A)
    sample_size_a: int
    sample_size_b: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "mean_a": self.mean_a,
            "mean_b": self.mean_b,
            "std_a": self.std_a,
            "std_b": self.std_b,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "p_value": self.p_value,
            "is_significant": self.is_significant,
            "bayesian_probability": self.bayesian_probability,
            "sample_size_a": self.sample_size_a,
            "sample_size_b": self.sample_size_b,
        }


class StatisticalAnalyzer:
    """Statistical analyzer for comparing LLM performance"""

    def __init__(self, alpha: float = 0.05):
        """
        Initialize analyzer.

        Args:
            alpha: Significance level (default 0.05)
        """
        self.alpha = alpha

    def compare_two_samples(
        self,
        sample_a: list[float],
        sample_b: list[float],
        paired: bool = False,
    ) -> StatisticalResult:
        """
        Compare two samples statistically.

        Args:
            sample_a: Sample A scores
            sample_b: Sample B scores
            paired: Whether samples are paired

        Returns:
            StatisticalResult with all metrics
        """
        if not sample_a or not sample_b:
            raise ValueError("Samples cannot be empty")

        # Convert to numpy arrays
        a = np.array(sample_a)
        b = np.array(sample_b)

        # Calculate basic statistics
        mean_a = np.mean(a)
        mean_b = np.mean(b)
        std_a = np.std(a, ddof=1)
        std_b = np.std(b, ddof=1)

        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((std_a ** 2 + std_b ** 2) / 2)
        effect_size = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0.0

        # Perform t-test
        if paired and len(a) == len(b):
            t_stat, p_value = stats.ttest_rel(a, b)
        else:
            t_stat, p_value = stats.ttest_ind(a, b)

        # Calculate confidence interval for difference
        diff = mean_b - mean_a
        se_diff = np.sqrt((std_a ** 2 / len(a)) + (std_b ** 2 / len(b)))
        ci_margin = 1.96 * se_diff  # 95% CI
        confidence_interval = (diff - ci_margin, diff + ci_margin)

        # Bayesian probability P(B > A)
        bayesian_prob = self._bayesian_probability(a, b)

        return StatisticalResult(
            mean_a=mean_a,
            mean_b=mean_b,
            std_a=std_a,
            std_b=std_b,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            p_value=p_value,
            is_significant=p_value < self.alpha,
            bayesian_probability=bayesian_prob,
            sample_size_a=len(a),
            sample_size_b=len(b),
        )

    def _bayesian_probability(self, sample_a: np.ndarray, sample_b: np.ndarray) -> float:
        """
        Calculate Bayesian probability that B > A.

        Uses Monte Carlo sampling from posterior distributions.
        """
        # Estimate posterior parameters (assuming normal distribution)
        mean_a = np.mean(sample_a)
        std_a = np.std(sample_a, ddof=1)
        mean_b = np.mean(sample_b)
        std_b = np.std(sample_b, ddof=1)

        # Sample from posteriors
        n_samples = 10000
        samples_a = np.random.normal(mean_a, std_a / np.sqrt(len(sample_a)), n_samples)
        samples_b = np.random.normal(mean_b, std_b / np.sqrt(len(sample_b)), n_samples)

        # Calculate probability B > A
        prob = np.mean(samples_b > samples_a)

        return prob

    def calculate_sample_size(
        self,
        effect_size: float,
        power: float = 0.80,
        alpha: float = 0.05,
    ) -> int:
        """
        Calculate required sample size for desired power.

        Args:
            effect_size: Expected Cohen's d
            power: Desired statistical power (default 0.80)
            alpha: Significance level (default 0.05)

        Returns:
            Required sample size per group
        """
        from scipy.stats import norm

        # Z-scores for alpha and power
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        # Sample size formula
        n = ((z_alpha + z_beta) ** 2) * 2 / (effect_size ** 2)

        return int(np.ceil(n))


# Factory
def create_statistical_analyzer(alpha: float = 0.05) -> StatisticalAnalyzer:
    """Create statistical analyzer"""
    return StatisticalAnalyzer(alpha)


__all__ = [
    "StatisticalResult",
    "StatisticalAnalyzer",
    "create_statistical_analyzer",
]
```

#### 4.2 Create Adaptive Learning Module

**File**: Create `/Users/coreyfoster/DevSkyy/llm/adaptive_learning.py`

```python
"""
Adaptive Learning for LLM Provider Profiling
=============================================

Track provider performance over time and optimize weights dynamically.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProviderProfile:
    """Performance profile for an LLM provider"""

    provider: str

    # Performance metrics
    total_competitions: int = 0
    wins: int = 0
    top_two_appearances: int = 0

    # Score statistics
    avg_score: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0
    score_history: list[float] = field(default_factory=list)

    # Efficiency metrics
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0

    # Category-specific performance
    category_scores: dict[str, list[float]] = field(default_factory=dict)

    # Time-based metrics
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_competitions == 0:
            return 0.0
        return self.wins / self.total_competitions

    @property
    def top_two_rate(self) -> float:
        """Calculate rate of appearing in top 2"""
        if self.total_competitions == 0:
            return 0.0
        return self.top_two_appearances / self.total_competitions

    @property
    def score_variance(self) -> float:
        """Calculate score variance"""
        if len(self.score_history) < 2:
            return 0.0

        import numpy as np
        return float(np.var(self.score_history))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "provider": self.provider,
            "total_competitions": self.total_competitions,
            "wins": self.wins,
            "win_rate": self.win_rate,
            "top_two_appearances": self.top_two_appearances,
            "top_two_rate": self.top_two_rate,
            "avg_score": self.avg_score,
            "max_score": self.max_score,
            "min_score": self.min_score,
            "score_variance": self.score_variance,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost_usd": self.avg_cost_usd,
            "category_scores": {
                cat: {
                    "avg": sum(scores) / len(scores) if scores else 0,
                    "count": len(scores)
                }
                for cat, scores in self.category_scores.items()
            },
            "last_updated": self.last_updated.isoformat(),
        }


class AdaptiveLearner:
    """
    Adaptive learning system for provider optimization.

    Tracks provider performance and dynamically adjusts selection weights.
    """

    def __init__(self, db_connection: Any = None):
        """
        Initialize adaptive learner.

        Args:
            db_connection: Optional database connection for persistence
        """
        self._profiles: dict[str, ProviderProfile] = {}
        self._db = db_connection
        self._learning_rate = 0.1  # How quickly to adapt weights

    def update_from_competition(
        self,
        provider: str,
        score: float,
        rank: int,
        latency_ms: float,
        cost_usd: float,
        is_winner: bool,
        category: str | None = None,
    ) -> None:
        """
        Update provider profile from competition result.

        Args:
            provider: Provider name
            score: Total score achieved
            rank: Final rank (1-indexed)
            latency_ms: Response latency
            cost_usd: Response cost
            is_winner: Whether provider won
            category: Task category
        """
        # Get or create profile
        if provider not in self._profiles:
            self._profiles[provider] = ProviderProfile(provider=provider)

        profile = self._profiles[provider]

        # Update counts
        profile.total_competitions += 1
        if is_winner:
            profile.wins += 1
        if rank <= 2:
            profile.top_two_appearances += 1

        # Update scores
        profile.score_history.append(score)
        if len(profile.score_history) > 1000:
            profile.score_history = profile.score_history[-1000:]  # Keep last 1000

        # Running average
        n = profile.total_competitions
        profile.avg_score = ((n - 1) * profile.avg_score + score) / n
        profile.avg_latency_ms = ((n - 1) * profile.avg_latency_ms + latency_ms) / n
        profile.avg_cost_usd = ((n - 1) * profile.avg_cost_usd + cost_usd) / n

        # Min/max
        profile.max_score = max(profile.max_score, score)
        if profile.min_score == 0:
            profile.min_score = score
        else:
            profile.min_score = min(profile.min_score, score)

        # Category-specific
        if category:
            if category not in profile.category_scores:
                profile.category_scores[category] = []
            profile.category_scores[category].append(score)
            if len(profile.category_scores[category]) > 100:
                profile.category_scores[category] = profile.category_scores[category][-100:]

        profile.last_updated = datetime.now(UTC)

    def get_profile(self, provider: str) -> ProviderProfile | None:
        """Get provider profile"""
        return self._profiles.get(provider)

    def get_all_profiles(self) -> dict[str, ProviderProfile]:
        """Get all provider profiles"""
        return self._profiles.copy()

    def calculate_weights(
        self,
        providers: list[str],
        category: str | None = None,
    ) -> dict[str, float]:
        """
        Calculate dynamic provider weights based on performance.

        Args:
            providers: List of providers to weight
            category: Optional category for category-specific weighting

        Returns:
            Dictionary of provider -> weight (sums to 1.0)
        """
        weights = {}

        for provider in providers:
            profile = self._profiles.get(provider)

            if not profile or profile.total_competitions < 3:
                # Not enough data, use uniform weight
                weights[provider] = 1.0
                continue

            # Base weight on performance
            weight = profile.avg_score

            # Boost for high win rate
            weight *= (1 + profile.win_rate * 0.5)

            # Boost for category-specific performance
            if category and category in profile.category_scores:
                cat_scores = profile.category_scores[category]
                cat_avg = sum(cat_scores) / len(cat_scores)
                weight *= (1 + (cat_avg / 100) * 0.3)

            # Penalize high cost (cost efficiency)
            if profile.avg_cost_usd > 0:
                cost_penalty = 1 / (1 + profile.avg_cost_usd * 10)
                weight *= cost_penalty

            # Penalize high latency (speed efficiency)
            if profile.avg_latency_ms > 0:
                latency_penalty = 1 / (1 + profile.avg_latency_ms / 1000)
                weight *= latency_penalty

            weights[provider] = weight

        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {p: w / total for p, w in weights.items()}
        else:
            # Fallback to uniform
            weights = {p: 1.0 / len(providers) for p in providers}

        return weights

    def get_recommendations(self, category: str | None = None) -> list[tuple[str, float]]:
        """
        Get provider recommendations sorted by performance.

        Args:
            category: Optional category filter

        Returns:
            List of (provider, score) tuples sorted by score
        """
        recommendations = []

        for provider, profile in self._profiles.items():
            if profile.total_competitions < 3:
                continue

            # Calculate recommendation score
            score = profile.avg_score * profile.win_rate

            # Category boost
            if category and category in profile.category_scores:
                cat_scores = profile.category_scores[category]
                cat_avg = sum(cat_scores) / len(cat_scores)
                score *= (1 + (cat_avg / 100) * 0.2)

            recommendations.append((provider, score))

        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return recommendations


# Factory
def create_adaptive_learner(db_connection: Any = None) -> AdaptiveLearner:
    """Create adaptive learner"""
    return AdaptiveLearner(db_connection)


__all__ = [
    "ProviderProfile",
    "AdaptiveLearner",
    "create_adaptive_learner",
]
```

#### 4.3 Integrate into Round Table

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 24: Add imports
from llm.statistics import create_statistical_analyzer, StatisticalResult
from llm.adaptive_learning import create_adaptive_learner, AdaptiveLearner

# Line 119-130: Update ABTestResult
@dataclass
class ABTestResult:
    """Result from A/B testing between top 2"""

    entry_a: RoundTableEntry
    entry_b: RoundTableEntry
    winner: RoundTableEntry
    judge_provider: LLMProvider
    judge_reasoning: str
    confidence: float
    statistical_analysis: StatisticalResult | None = None  # NEW
    tested_at: datetime = field(default_factory=lambda: datetime.now(UTC))

# Line 632-639: Add to __init__
def __init__(self, db_url: str | None = None):
    self._providers: dict[LLMProvider, Callable] = {}
    self._judge_provider: LLMProvider = LLMProvider.CLAUDE
    self._scorer = ResponseScorer()
    self._db = RoundTableDatabase(db_url)
    self._history: list[RoundTableResult] = []
    self._initialized = False
    self._statistical_analyzer = create_statistical_analyzer()  # NEW
    self._adaptive_learner = create_adaptive_learner()  # NEW

# Line 841-920: Update _ab_test method
async def _ab_test(
    self,
    prompt: str,
    top_two: list[RoundTableEntry],
    historical_scores_a: list[float] | None = None,
    historical_scores_b: list[float] | None = None,
) -> ABTestResult:
    """A/B test between top 2 entries using judge LLM + statistics"""
    entry_a, entry_b = top_two[0], top_two[1]

    # Statistical analysis (if historical data available)
    statistical_analysis = None
    if historical_scores_a and historical_scores_b:
        try:
            statistical_analysis = self._statistical_analyzer.compare_two_samples(
                historical_scores_a,
                historical_scores_b,
                paired=False,
            )
            logger.info(
                f"Statistical analysis: p={statistical_analysis.p_value:.4f}, "
                f"effect_size={statistical_analysis.effect_size:.3f}"
            )
        except Exception as e:
            logger.warning(f"Statistical analysis failed: {e}")

    # ... existing judge LLM logic ...

    return ABTestResult(
        entry_a=entry_a,
        entry_b=entry_b,
        winner=winner,
        judge_provider=self._judge_provider,
        judge_reasoning=reasoning,
        confidence=confidence,
        statistical_analysis=statistical_analysis,  # NEW
    )

# After line 766: Add adaptive learning update
result = RoundTableResult(
    # ... existing fields ...
)

# Update adaptive learner
for entry in ranked_entries:
    self._adaptive_learner.update_from_competition(
        provider=entry.provider.value,
        score=entry.total_score,
        rank=entry.rank,
        latency_ms=entry.response.latency_ms,
        cost_usd=entry.response.cost_usd,
        is_winner=(entry == winner),
        category=task_context.get("category") if task_context else None,
    )
```

#### 4.4 Add Prometheus Metrics

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 30: Add prometheus imports
from prometheus_client import Counter, Histogram, Gauge

# After imports: Define metrics
COMPETITION_COUNTER = Counter(
    "round_table_competitions_total",
    "Total Round Table competitions",
    ["status", "winner_provider"]
)

COMPETITION_DURATION = Histogram(
    "round_table_competition_duration_seconds",
    "Round Table competition duration",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

PROVIDER_WINS = Counter(
    "round_table_provider_wins_total",
    "Provider wins",
    ["provider"]
)

PROVIDER_SCORE = Gauge(
    "round_table_provider_avg_score",
    "Provider average score",
    ["provider"]
)

# Line 750-766: Add metrics to compete()
# After creating result
COMPETITION_COUNTER.labels(
    status=result.status.value,
    winner_provider=winner.provider.value if winner else "none"
).inc()

COMPETITION_DURATION.observe(total_duration_ms / 1000)

if winner:
    PROVIDER_WINS.labels(provider=winner.provider.value).inc()

# Update provider scores
for entry in ranked_entries:
    PROVIDER_SCORE.labels(provider=entry.provider.value).set(entry.total_score)
```

### Success Criteria

- [ ] Statistical analysis integrated into A/B testing
- [ ] Adaptive learning tracks all provider performances
- [ ] Provider weights calculated dynamically
- [ ] Prometheus metrics exported
- [ ] Statistical significance checked (p-values, effect sizes)
- [ ] Bayesian probability calculated
- [ ] Tests pass for all new components

### Test Plan

#### 4.5 Create Tests

**File**: Create `/Users/coreyfoster/DevSkyy/tests/test_statistics.py`

```python
"""Tests for statistical analysis"""
import pytest
import numpy as np
from llm.statistics import StatisticalAnalyzer


def test_compare_two_samples_significant():
    """Test detecting significant difference"""
    analyzer = StatisticalAnalyzer()

    # Create samples with clear difference
    sample_a = [50, 52, 48, 51, 49] * 10  # Mean ~50
    sample_b = [70, 72, 68, 71, 69] * 10  # Mean ~70

    result = analyzer.compare_two_samples(sample_a, sample_b)

    assert result.is_significant
    assert result.p_value < 0.05
    assert result.effect_size > 1.0  # Large effect
    assert result.bayesian_probability > 0.95  # Very likely B > A


def test_compare_two_samples_not_significant():
    """Test detecting no significant difference"""
    analyzer = StatisticalAnalyzer()

    # Create samples with minimal difference
    sample_a = [50, 52, 48, 51, 49] * 10
    sample_b = [51, 53, 49, 52, 50] * 10

    result = analyzer.compare_two_samples(sample_a, sample_b)

    assert not result.is_significant
    assert result.p_value > 0.05


def test_calculate_sample_size():
    """Test sample size calculation"""
    analyzer = StatisticalAnalyzer()

    # For medium effect size (0.5) with 80% power
    n = analyzer.calculate_sample_size(effect_size=0.5, power=0.80)

    assert n > 0
    assert n < 200  # Reasonable sample size
```

**File**: Create `/Users/coreyfoster/DevSkyy/tests/test_adaptive_learning.py`

```python
"""Tests for adaptive learning"""
import pytest
from llm.adaptive_learning import AdaptiveLearner


def test_provider_profile_update():
    """Test updating provider profile"""
    learner = AdaptiveLearner()

    # Simulate 10 competitions
    for i in range(10):
        learner.update_from_competition(
            provider="claude",
            score=75.0 + i,
            rank=1,
            latency_ms=1000,
            cost_usd=0.01,
            is_winner=(i % 2 == 0),  # Win every other
            category="reasoning",
        )

    profile = learner.get_profile("claude")
    assert profile is not None
    assert profile.total_competitions == 10
    assert profile.wins == 5
    assert profile.win_rate == 0.5
    assert profile.avg_score > 70


def test_calculate_weights():
    """Test dynamic weight calculation"""
    learner = AdaptiveLearner()

    # Provider A: High performer
    for _ in range(10):
        learner.update_from_competition(
            provider="provider_a",
            score=90,
            rank=1,
            latency_ms=1000,
            cost_usd=0.01,
            is_winner=True,
        )

    # Provider B: Low performer
    for _ in range(10):
        learner.update_from_competition(
            provider="provider_b",
            score=50,
            rank=2,
            latency_ms=2000,
            cost_usd=0.02,
            is_winner=False,
        )

    weights = learner.calculate_weights(["provider_a", "provider_b"])

    assert weights["provider_a"] > weights["provider_b"]
    assert abs(sum(weights.values()) - 1.0) < 0.01  # Sums to 1


def test_get_recommendations():
    """Test provider recommendations"""
    learner = AdaptiveLearner()

    # Add some competitions
    for provider, score, wins in [
        ("claude", 85, 7),
        ("gpt4", 80, 5),
        ("gemini", 75, 3),
    ]:
        for i in range(10):
            learner.update_from_competition(
                provider=provider,
                score=score,
                rank=1 if i < wins else 2,
                latency_ms=1000,
                cost_usd=0.01,
                is_winner=(i < wins),
            )

    recommendations = learner.get_recommendations()

    assert len(recommendations) == 3
    assert recommendations[0][0] == "claude"  # Best performer first
```

---

## 🌐 Phase 5: Dashboard - WebSocket & Real-time Updates

**Duration**: 8-10 hours
**Complexity**: ~1000 LOC (backend + frontend)
**Risk**: Medium (concurrency, state management)

### Implementation Steps

#### 5.1 Add WebSocket Backend

**File**: Create `/Users/coreyfoster/DevSkyy/api/websocket.py`

```python
"""
WebSocket Server for Real-time Updates
=======================================

Provides real-time updates for:
- Agent execution status
- Round Table competitions
- 3D generation progress
- Task updates

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[str]] = {}  # topic -> {connection_ids}

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept new connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str) -> None:
        """Remove connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove from all subscriptions
        for topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)

        logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe(self, connection_id: str, topic: str) -> None:
        """Subscribe connection to topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(connection_id)
        logger.debug(f"Subscribed {connection_id} to {topic}")

    def unsubscribe(self, connection_id: str, topic: str) -> None:
        """Unsubscribe connection from topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)

    async def send_personal_message(self, message: dict, connection_id: str) -> None:
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict, topic: str | None = None) -> None:
        """Broadcast message to all or specific topic"""
        if topic and topic in self.subscriptions:
            connection_ids = self.subscriptions[topic].copy()
        else:
            connection_ids = list(self.active_connections.keys())

        # Send to all subscribed connections
        tasks = []
        for connection_id in connection_ids:
            if connection_id in self.active_connections:
                tasks.append(
                    self.active_connections[connection_id].send_json(message)
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Global connection manager
manager = ConnectionManager()


class WSMessage(BaseModel):
    """WebSocket message structure"""

    type: str  # "subscribe", "unsubscribe", "ping"
    topic: str | None = None
    data: dict | None = None


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint.

    Message format:
    {
        "type": "subscribe" | "unsubscribe" | "ping",
        "topic": "agents" | "round_table" | "3d" | "tasks",
        "data": {}
    }
    """
    connection_id = str(uuid4())

    try:
        await manager.connect(websocket, connection_id)

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        while True:
            # Receive message
            data = await websocket.receive_json()
            message = WSMessage(**data)

            # Handle message
            if message.type == "subscribe" and message.topic:
                manager.subscribe(connection_id, message.topic)
                await websocket.send_json({
                    "type": "subscribed",
                    "topic": message.topic,
                })

            elif message.type == "unsubscribe" and message.topic:
                manager.unsubscribe(connection_id, message.topic)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "topic": message.topic,
                })

            elif message.type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(UTC).isoformat(),
                })

    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)


# Utility functions for broadcasting updates
async def broadcast_agent_update(agent_type: str, data: dict) -> None:
    """Broadcast agent status update"""
    await manager.broadcast(
        {
            "type": "agent_update",
            "agent_type": agent_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        topic="agents",
    )


async def broadcast_round_table_update(data: dict) -> None:
    """Broadcast Round Table competition update"""
    await manager.broadcast(
        {
            "type": "round_table_update",
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        topic="round_table",
    )


async def broadcast_3d_update(job_id: str, data: dict) -> None:
    """Broadcast 3D generation progress update"""
    await manager.broadcast(
        {
            "type": "3d_update",
            "job_id": job_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        topic="3d",
    )


async def broadcast_task_update(task_id: str, data: dict) -> None:
    """Broadcast task status update"""
    await manager.broadcast(
        {
            "type": "task_update",
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        topic="tasks",
    )


__all__ = [
    "router",
    "manager",
    "broadcast_agent_update",
    "broadcast_round_table_update",
    "broadcast_3d_update",
    "broadcast_task_update",
]
```

#### 5.2 Integrate WebSocket into FastAPI

**File**: `/Users/coreyfoster/DevSkyy/main_enterprise.py` (or equivalent)

```python
# Add import
from api.websocket import router as websocket_router

# Register WebSocket router
app.include_router(websocket_router)
```

#### 5.3 Update Agents to Broadcast Status

**File**: `/Users/coreyfoster/DevSkyy/agents/base_super_agent.py`

```python
# Line 2537-2560: Update execute method
async def execute(self, prompt: str, **kwargs) -> AgentResult:
    """Execute agent task"""

    # Broadcast start
    try:
        from api.websocket import broadcast_agent_update
        await broadcast_agent_update(
            agent_type=self.__class__.__name__,
            data={"status": "started", "prompt": prompt[:100]}
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast start: {e}")

    # ... existing execution logic ...

    # Broadcast completion
    try:
        await broadcast_agent_update(
            agent_type=self.__class__.__name__,
            data={"status": "completed", "success": result.success}
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast completion: {e}")

    return result
```

#### 5.4 Update Round Table to Broadcast Progress

**File**: `/Users/coreyfoster/DevSkyy/llm/round_table.py`

```python
# Line 700-766: Add broadcasts to compete()
async def compete(...) -> RoundTableResult:
    # ... existing code ...

    # Broadcast competition start
    try:
        from api.websocket import broadcast_round_table_update
        await broadcast_round_table_update({
            "status": "started",
            "providers": [p.value for p in active_providers],
        })
    except Exception:
        pass

    # Phase 1: Generate
    await broadcast_round_table_update({"status": "generating"})
    entries = await self._generate_all(prompt, active_providers, context, tools)

    # Phase 2: Scoring
    await broadcast_round_table_update({"status": "scoring"})
    scored_entries = self._score_all(entries, prompt, context)

    # Phase 3: Ranking
    ranked_entries = sorted(scored_entries, key=lambda e: e.total_score, reverse=True)

    # Phase 4: A/B Testing
    await broadcast_round_table_update({"status": "ab_testing"})
    ab_result = await self._ab_test(prompt, top_two)

    # Broadcast completion
    await broadcast_round_table_update({
        "status": "completed",
        "winner": winner.provider.value,
        "score": winner.total_score,
    })

    return result
```

#### 5.5 Create Frontend WebSocket Client

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/lib/websocket.ts`

```typescript
/**
 * WebSocket Client for Real-time Updates
 */

type MessageHandler = (data: any) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private connectionId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private subscriptions: Set<string> = new Set();

  constructor(private url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.connectionId = null;
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: any) {
    const { type, topic } = message;

    // Handle connection confirmation
    if (type === 'connected') {
      this.connectionId = message.connection_id;
      // Re-subscribe to topics
      this.subscriptions.forEach((topic) => {
        this.send({ type: 'subscribe', topic });
      });
      return;
    }

    // Notify handlers
    const topicHandlers = this.handlers.get(type) || new Set();
    topicHandlers.forEach((handler) => {
      try {
        handler(message.data || message);
      } catch (error) {
        console.error('Handler error:', error);
      }
    });
  }

  subscribe(topic: string, handler: MessageHandler) {
    // Add handler
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, new Set());
    }
    this.handlers.get(topic)!.add(handler);

    // Subscribe to topic
    if (!this.subscriptions.has(topic)) {
      this.subscriptions.add(topic);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'subscribe', topic });
      }
    }

    // Return unsubscribe function
    return () => this.unsubscribe(topic, handler);
  }

  unsubscribe(topic: string, handler: MessageHandler) {
    const handlers = this.handlers.get(topic);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.handlers.delete(topic);
        this.subscriptions.delete(topic);
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.send({ type: 'unsubscribe', topic });
        }
      }
    }
  }

  private send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
export const wsClient = new WebSocketClient(WS_URL);
```

#### 5.6 Create React Hook for WebSocket

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/hooks/useWebSocket.ts`

```typescript
import { useEffect, useState } from 'react';
import { wsClient } from '@/lib/websocket';

export function useWebSocket<T = any>(topic: string) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect if not connected
    if (!wsClient.isConnected) {
      wsClient.connect().then(() => {
        setIsConnected(true);
      });
    } else {
      setIsConnected(true);
    }

    // Subscribe to topic
    const unsubscribe = wsClient.subscribe(topic, (newData: T) => {
      setData(newData);
    });

    return () => {
      unsubscribe();
    };
  }, [topic]);

  return { data, isConnected };
}
```

#### 5.7 Update Dashboard Components

**File**: `/Users/coreyfoster/DevSkyy/frontend/app/dashboard/page.tsx` (or equivalent)

```typescript
'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useEffect, useState } from 'react';

export default function DashboardPage() {
  const { data: agentUpdate, isConnected } = useWebSocket('agent_update');
  const { data: roundTableUpdate } = useWebSocket('round_table_update');
  const { data: threeDUpdate } = useWebSocket('3d_update');

  useEffect(() => {
    if (agentUpdate) {
      console.log('Agent update:', agentUpdate);
      // Update UI based on agent status
    }
  }, [agentUpdate]);

  useEffect(() => {
    if (roundTableUpdate) {
      console.log('Round Table update:', roundTableUpdate);
      // Update Round Table UI
    }
  }, [roundTableUpdate]);

  return (
    <div>
      {/* Connection indicator */}
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
      </div>

      {/* Rest of dashboard */}
    </div>
  );
}
```

### Success Criteria

- [ ] WebSocket server running on FastAPI
- [ ] Frontend connects and subscribes to topics
- [ ] Real-time updates for agents, Round Table, 3D, tasks
- [ ] Connection status indicator
- [ ] Automatic reconnection on disconnect
- [ ] Latency <100ms for updates
- [ ] No polling (all HTTP polling removed)

### Test Plan

```bash
# Backend
pytest tests/test_websocket.py -v

# Frontend (manual testing)
1. Start backend: uvicorn main_enterprise:app
2. Start frontend: npm run dev
3. Open browser console
4. Trigger agent execution
5. Verify real-time updates appear
6. Disconnect network
7. Verify reconnection works
```

---

## 🎨 Phase 6: Dashboard - UI Enhancements

**Duration**: 10-12 hours
**Complexity**: ~1200 LOC (React components + routes)
**Risk**: Low (UI only, no backend changes)

### Implementation Steps

#### 6.1 Integrate Three.js Collections

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/app/collections/[id]/page.tsx`

```typescript
'use client';

import { useParams } from 'next/navigation';
import { Suspense, lazy } from 'react';

// Lazy load collection experiences
const collections = {
  'black-rose': lazy(() => import('@/src/collections/BlackRoseExperience')),
  'signature': lazy(() => import('@/src/collections/SignatureExperience')),
  'love-hurts': lazy(() => import('@/src/collections/LoveHurtsExperience')),
  'showroom': lazy(() => import('@/src/collections/ShowroomExperience')),
  'runway': lazy(() => import('@/src/collections/RunwayExperience')),
};

export default function CollectionPage() {
  const params = useParams();
  const id = params.id as string;

  const Experience = collections[id as keyof typeof collections];

  if (!Experience) {
    return <div>Collection not found</div>;
  }

  return (
    <div className="h-screen w-full">
      <Suspense fallback={<div>Loading 3D experience...</div>}>
        <Experience />
      </Suspense>
    </div>
  );
}
```

**File**: Update `/Users/coreyfoster/DevSkyy/frontend/components/navigation.tsx`

```typescript
// Add collections to navigation
const collections = [
  { id: 'black-rose', name: 'Black Rose', icon: '🌹' },
  { id: 'signature', name: 'Signature', icon: '✍️' },
  { id: 'love-hurts', name: 'Love Hurts', icon: '💔' },
  { id: 'showroom', name: 'Showroom', icon: '🏪' },
  { id: 'runway', name: 'Runway', icon: '👗' },
];

// In navigation JSX
<div className="collections">
  <h3>3D Collections</h3>
  {collections.map((collection) => (
    <Link key={collection.id} href={`/collections/${collection.id}`}>
      <span>{collection.icon}</span>
      <span>{collection.name}</span>
    </Link>
  ))}
</div>
```

#### 6.2 Build Visual Generation UI

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/app/visual-generation/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

export default function VisualGenerationPage() {
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState('imagen');
  const [type, setType] = useState('image');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await api.visual.generate({
        prompt,
        provider,
        type,
        options: {},
      });
      setResult(response);
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Visual Generation</h1>

      <div className="grid gap-4">
        <div>
          <label>Prompt</label>
          <Input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to generate..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label>Provider</label>
            <Select value={provider} onValueChange={setProvider}>
              <option value="imagen">Google Imagen 3</option>
              <option value="flux">FLUX</option>
              <option value="veo">Google Veo 2</option>
            </Select>
          </div>

          <div>
            <label>Type</label>
            <Select value={type} onValueChange={setType}>
              <option value="image">Image</option>
              <option value="video">Video</option>
            </Select>
          </div>
        </div>

        <Button onClick={handleGenerate} disabled={loading}>
          {loading ? 'Generating...' : 'Generate'}
        </Button>

        {result && (
          <div className="mt-6">
            <h2 className="text-xl font-bold mb-4">Result</h2>
            {type === 'image' ? (
              <img src={result.url} alt="Generated" className="rounded-lg" />
            ) : (
              <video src={result.url} controls className="rounded-lg" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

#### 6.3 Build Virtual Try-On UI

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/app/virtual-tryon/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

export default function VirtualTryOnPage() {
  const [modelImage, setModelImage] = useState<File | null>(null);
  const [garmentImage, setGarmentImage] = useState<File | null>(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleTryOn = async () => {
    if (!modelImage || !garmentImage) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('model', modelImage);
    formData.append('garment', garmentImage);

    try {
      const response = await fetch('/api/v1/visual/tryon', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Try-on failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Virtual Try-On</h1>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="font-semibold mb-2">Model Photo</h3>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setModelImage(e.target.files?.[0] || null)}
          />
          {modelImage && (
            <img
              src={URL.createObjectURL(modelImage)}
              alt="Model"
              className="mt-4 rounded-lg"
            />
          )}
        </div>

        <div>
          <h3 className="font-semibold mb-2">Garment Photo</h3>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setGarmentImage(e.target.files?.[0] || null)}
          />
          {garmentImage && (
            <img
              src={URL.createObjectURL(garmentImage)}
              alt="Garment"
              className="mt-4 rounded-lg"
            />
          )}
        </div>
      </div>

      <Button
        onClick={handleTryOn}
        disabled={!modelImage || !garmentImage || loading}
        className="mt-6"
      >
        {loading ? 'Processing...' : 'Try On'}
      </Button>

      {result && (
        <div className="mt-6">
          <h2 className="text-xl font-bold mb-4">Result</h2>
          <img src={result.url} alt="Try-on result" className="rounded-lg" />
        </div>
      )}
    </div>
  );
}
```

#### 6.4 Build Brand DNA Editor

**File**: Create `/Users/coreyfoster/DevSkyy/frontend/app/brand-editor/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

export default function BrandEditorPage() {
  const [brandData, setBrandData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.brand.get().then((data) => {
      setBrandData(data);
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    // TODO: Add save endpoint
    console.log('Saving brand data:', brandData);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Brand DNA Editor</h1>

      <div className="grid gap-6">
        <div>
          <label className="font-semibold">Brand Name</label>
          <Input
            value={brandData?.name || ''}
            onChange={(e) =>
              setBrandData({ ...brandData, name: e.target.value })
            }
          />
        </div>

        <div>
          <label className="font-semibold">Tagline</label>
          <Input
            value={brandData?.tagline || ''}
            onChange={(e) =>
              setBrandData({ ...brandData, tagline: e.target.value })
            }
          />
        </div>

        <div>
          <label className="font-semibold">Philosophy</label>
          <Textarea
            value={brandData?.philosophy || ''}
            onChange={(e) =>
              setBrandData({ ...brandData, philosophy: e.target.value })
            }
            rows={4}
          />
        </div>

        <div>
          <h3 className="font-semibold mb-2">Colors</h3>
          <div className="grid grid-cols-3 gap-4">
            {brandData?.colors &&
              Object.entries(brandData.colors).map(([key, color]) => (
                <div key={key}>
                  <label>{color.name}</label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={color.hex}
                      onChange={(e) => {
                        const newColors = { ...brandData.colors };
                        newColors[key].hex = e.target.value;
                        setBrandData({ ...brandData, colors: newColors });
                      }}
                    />
                    <Input value={color.hex} readOnly />
                  </div>
                </div>
              ))}
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">Collections</h3>
          {brandData?.collections?.map((collection, idx) => (
            <div key={idx} className="border p-4 rounded-lg mb-2">
              <Input
                value={collection.name}
                placeholder="Collection name"
                className="mb-2"
              />
              <Textarea
                value={collection.description}
                placeholder="Description"
                rows={2}
              />
            </div>
          ))}
        </div>

        <Button onClick={handleSave}>Save Changes</Button>
      </div>
    </div>
  );
}
```

### Success Criteria

- [ ] All 5 Three.js collections accessible via navigation
- [ ] Visual generation UI functional with all providers
- [ ] Virtual try-on UI accepts uploads and displays results
- [ ] Brand DNA editor loads and displays current brand data
- [ ] All UIs responsive and styled consistently
- [ ] Navigation updated with new routes

---

## 📦 Summary & Dependencies

### Phase Dependencies

```
Phase 1 (Foundation)
  └─> Phase 2 (Tool Calling)
        └─> Phase 3 (ML Scoring)
              └─> Phase 4 (Statistics & Learning)

Phase 5 (WebSocket) - Independent, can run parallel to 2-4
Phase 6 (UI) - Depends on Phase 5 for real-time features
```

### File Summary

**New Files** (15):

1. `/Users/coreyfoster/DevSkyy/scripts/verify_dependencies.py` - Dependency verification
2. `/Users/coreyfoster/DevSkyy/llm/evaluation_metrics.py` - ML scoring (~400 LOC)
3. `/Users/coreyfoster/DevSkyy/llm/statistics.py` - Statistical analysis (~300 LOC)
4. `/Users/coreyfoster/DevSkyy/llm/adaptive_learning.py` - Provider profiling (~400 LOC)
5. `/Users/coreyfoster/DevSkyy/api/websocket.py` - WebSocket server (~300 LOC)
6. `/Users/coreyfoster/DevSkyy/frontend/lib/websocket.ts` - WS client (~150 LOC)
7. `/Users/coreyfoster/DevSkyy/frontend/hooks/useWebSocket.ts` - React hook (~30 LOC)
8. `/Users/coreyfoster/DevSkyy/frontend/app/collections/[id]/page.tsx` - Collections route (~50 LOC)
9. `/Users/coreyfoster/DevSkyy/frontend/app/visual-generation/page.tsx` - Visual gen UI (~150 LOC)
10. `/Users/coreyfoster/DevSkyy/frontend/app/virtual-tryon/page.tsx` - Try-on UI (~100 LOC)
11. `/Users/coreyfoster/DevSkyy/frontend/app/brand-editor/page.tsx` - Brand editor (~150 LOC)
12. `/Users/coreyfoster/DevSkyy/tests/test_round_table.py` - Round Table tests (~200 LOC)
13. `/Users/coreyfoster/DevSkyy/tests/test_evaluation_metrics.py` - ML tests (~150 LOC)
14. `/Users/coreyfoster/DevSkyy/tests/test_statistics.py` - Statistics tests (~100 LOC)
15. `/Users/coreyfoster/DevSkyy/tests/test_adaptive_learning.py` - Learning tests (~100 LOC)

**Modified Files** (9):

1. `/Users/coreyfoster/DevSkyy/pyproject.toml` - Move deps to main (~20 line changes)
2. `/Users/coreyfoster/DevSkyy/requirements.txt` - Add ML packages (~15 lines)
3. `/Users/coreyfoster/DevSkyy/README.md` - Python version docs (~20 lines)
4. `/Users/coreyfoster/DevSkyy/llm/round_table.py` - Tool calling + ML + stats (~300 line changes)
5. `/Users/coreyfoster/DevSkyy/agents/base_super_agent.py` - WebSocket broadcasts (~30 lines)
6. `/Users/coreyfoster/DevSkyy/main_enterprise.py` - WebSocket router (~5 lines)
7. `/Users/coreyfoster/DevSkyy/frontend/components/navigation.tsx` - Collections nav (~20 lines)
8. `/Users/coreyfoster/DevSkyy/frontend/app/dashboard/page.tsx` - WebSocket integration (~30 lines)
9. `/Users/coreyfoster/DevSkyy/frontend/package.json` - No changes needed (WebSocket native)

### Total Estimated LOC

- **Backend**: ~2,500 LOC (new modules + modifications)
- **Frontend**: ~800 LOC (UI components + WebSocket)
- **Tests**: ~650 LOC
- **Config**: ~60 LOC
- **TOTAL**: ~4,010 LOC

---

### Critical Files for Implementation

1. **`/Users/coreyfoster/DevSkyy/llm/round_table.py`** - Core Round Table modifications (tool calling, ML, stats integration)
2. **`/Users/coreyfoster/DevSkyy/llm/evaluation_metrics.py`** - New ML scoring module (sentence transformers, coherence, factuality)
3. **`/Users/coreyfoster/DevSkyy/api/websocket.py`** - New WebSocket server (real-time updates)
4. **`/Users/coreyfoster/DevSkyy/frontend/lib/websocket.ts`** - Frontend WebSocket client (connection management, subscriptions)
5. **`/Users/coreyfoster/DevSkyy/pyproject.toml`** - Dependency declarations (critical foundation for all ML features)

---

## 🎯 Next Steps

1. **User Review**: Review this plan and approve Phase 1
2. **Phase 1 Execution**: Fix dependencies and verify installations
3. **Phase 2 Approval**: After Phase 1 success, approve Phase 2
4. **Iterative Execution**: Continue phase-by-phase with approval gates
5. **Testing**: Run comprehensive tests after each phase
6. **Documentation**: Update docs with new features and APIs

---

**End of Implementation Plan**
