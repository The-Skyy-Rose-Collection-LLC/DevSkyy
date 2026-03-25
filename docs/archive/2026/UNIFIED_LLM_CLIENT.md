# Unified LLM Client - Usage Guide

## Overview

The Unified LLM Client replaces direct Claude SDK calls with an intelligent system that:

1. **Classifies tasks** using Groq (<100ms) → determines task category
2. **Selects technique** → recommends optimal prompt engineering approach
3. **Routes to provider** → chooses best LLM based on task type
4. **Executes request** → with fallback and error handling

## Architecture

```
User Request
    ↓
Task Classifier (Groq)
    ↓
[TaskCategory + PromptTechnique]
    ↓
LLM Router
    ↓
[Provider Selection]
    ↓
Execution (FAST/BALANCED/ROUND_TABLE)
    ↓
Response
```

## Components

### 1. Task Classifier (`llm/task_classifier.py`)

Classifies tasks into categories using Groq's sub-100ms inference:

- `reasoning` → Chain-of-Thought
- `creative` → Tree of Thoughts
- `code` → ReAct
- `qa` → RAG
- `classification` → Few-Shot
- And 10 more categories...

### 2. Unified LLM Client (`llm/unified_llm_client.py`)

Orchestrates the entire pipeline with three execution modes:

- `FAST`: Single provider, no fallback
- `BALANCED`: Single provider with automatic fallback
- `ROUND_TABLE`: All 6 providers compete, winner selected

### 3. Integration in Agents (`agents/base_super_agent.py`)

All agents now have `self.llm_client` initialized automatically.

## Usage Examples

### Basic Usage (from Agent)

```python
# Inside an agent's execute() method
messages = [
    Message.user("Explain quantum computing in simple terms")
]

response = await self.llm_complete(
    messages=messages,
    task_description="Explain a complex concept simply",
    execution_mode="balanced"  # FAST, BALANCED, or ROUND_TABLE
)

print(response)  # Plain text response
```

### With Task Description for Better Classification

```python
messages = [
    Message.system("You are a creative writing assistant"),
    Message.user("Write a short story about a robot discovering emotions")
]

# Task description helps classifier choose correct category
response = await self.llm_complete(
    messages=messages,
    task_description="Generate creative fiction story",
    execution_mode="balanced",
    temperature=0.9,
    max_tokens=2000
)
```

### High-Stakes Operations (Round Table)

```python
# For financial transactions, security decisions, etc.
messages = [
    Message.user("Process payment of $10,000 for order #12345")
]

response = await self.llm_complete(
    messages=messages,
    task_description="Process financial transaction",
    execution_mode="round_table",  # All providers compete
    temperature=0.1  # Low temperature for deterministic output
)
```

### Direct LLMRequest Usage

```python
from llm.unified_llm_client import UnifiedLLMClient, LLMRequest, ExecutionMode
from llm.base import Message

client = UnifiedLLMClient()

request = LLMRequest(
    messages=[Message.user("Debug this Python error: NameError: name 'x' is not defined")],
    task_description="Debug code error",
    execution_mode=ExecutionMode.BALANCED,
    temperature=0.2,
    max_tokens=1024
)

response = await client.complete(request)

print(f"Provider: {response.provider_used}")
print(f"Task: {response.task_classification.task_category}")
print(f"Technique: {response.technique_used}")
print(f"Latency: {response.total_latency_ms:.2f}ms")
print(f"Response: {response.content}")
```

## Task Categories

| Category | Description | Recommended Technique | Providers |
|----------|-------------|---------------------|-----------|
| `reasoning` | Logical analysis, problem-solving | Chain-of-Thought | Anthropic, OpenAI |
| `creative` | Content creation, brainstorming | Tree of Thoughts | OpenAI, Anthropic |
| `code` | Programming, debugging | ReAct | OpenAI, Anthropic |
| `qa` | Question answering | RAG | Anthropic, Google |
| `classification` | Categorization, labeling | Few-Shot | OpenAI, Anthropic |
| `search` | Information retrieval | ReAct | Google, OpenAI |
| `analysis` | Data analysis, insights | Chain-of-Thought | Anthropic, Google |
| `planning` | Project planning, task breakdown | Tree of Thoughts | Anthropic, OpenAI |
| `debugging` | Code debugging, troubleshooting | ReAct | OpenAI, Anthropic |
| `optimization` | Performance improvements | Self-Consistency | Anthropic, OpenAI |
| `extraction` | Data extraction, parsing | Structured Output | OpenAI, Anthropic |
| `moderation` | Content moderation, safety | Constitutional AI | Anthropic, OpenAI |
| `generation` | Content generation | Role-Based | OpenAI, Anthropic |
| `summarization` | Text summarization | Chain-of-Thought | Anthropic, Google |
| `translation` | Language translation | Structured Output | Google, OpenAI |

## Provider Selection

The router automatically selects providers based on:

1. **Task Category**: Different providers excel at different tasks
2. **Agent Type**: Commerce/Creative/Marketing/Support/Operations/Analytics have preferences
3. **Temperature**: Low temp → cost-optimized, High temp → quality-optimized
4. **Fallback Chain**: Primary → Secondary → Tertiary

### Provider Strengths

- **Anthropic (Claude)**: Reasoning, analysis, empathy, safety
- **OpenAI (GPT-4)**: Creativity, code generation, DALL-E integration
- **Google (Gemini)**: Search, trends, multilingual, cost-effective
- **Groq**: Classification, fast inference (<100ms)
- **Mistral**: European data residency, cost-effective
- **Cohere**: Enterprise retrieval, multilingual
- **DeepSeek**: Cost-optimized ($0.14/1M tokens)

## Configuration

### Environment Variables

```bash
# Required (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...

# Optional
GROQ_API_KEY=...  # For fast classification
MISTRAL_API_KEY=...
COHERE_API_KEY=...
DEEPSEEK_API_KEY=...

# Router settings
ROUTING_STRATEGY=priority  # priority, cost, latency, round_robin
```

### Agent Initialization

Automatic in `agents/base_super_agent.py`:

```python
class EnhancedSuperAgent(BaseDevSkyyAgent):
    async def initialize(self):
        # Router initialized with strategy based on temperature
        strategy = RoutingStrategy.COST if self.config.temperature < 0.5 else RoutingStrategy.PRIORITY
        self._router = LLMRouter(strategy=strategy)

        # Unified LLM Client with task classifier
        classifier = TaskClassifier()
        self.llm_client = UnifiedLLMClient(
            router=self._router,
            classifier=classifier,
            technique_applicator=self.prompt_module
        )
```

## Observability

### Logging

All LLM calls log:
- Task classification results
- Provider selection
- Technique applied
- Latency breakdown (classification + completion)

```python
# Example log output
INFO - Task classified as reasoning (confidence: 0.92, latency: 87.34ms)
INFO - LLM completion: provider=anthropic, model=claude-sonnet-4-20250514, latency=1234.56ms
DEBUG - Task classified as reasoning (technique: chain_of_thought)
```

### Metrics (Prometheus)

- `llm_requests_total{provider, model, task_category}`
- `llm_latency_seconds{provider, stage}` (classification, completion, total)
- `llm_provider_fallbacks_total{from_provider, to_provider}`
- `task_classification_cache_hit_ratio`

## Best Practices

### 1. Always Provide Task Descriptions

```python
# Good
response = await self.llm_complete(
    messages=messages,
    task_description="Analyze customer sentiment from feedback"
)

# Less optimal (classifier must infer from messages)
response = await self.llm_complete(messages=messages)
```

### 2. Use Execution Modes Appropriately

- `FAST`: Simple queries, low latency required
- `BALANCED`: Most use cases (default)
- `ROUND_TABLE`: High-stakes decisions (financial, security, PII)

### 3. Set Temperature Based on Task

```python
# Deterministic tasks (code, classification)
temperature=0.1

# Balanced (analysis, QA)
temperature=0.5

# Creative (content generation, brainstorming)
temperature=0.9
```

### 4. Leverage Classification Caching

Task classifier caches results for 1 hour by default:

```python
# First call: ~100ms classification
response1 = await self.llm_complete(messages, task_description="same task")

# Second call: <1ms (cached)
response2 = await self.llm_complete(messages, task_description="same task")
```

## Migration from Direct SDK Calls

### Before (Direct Claude SDK)

```python
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

content = response.content[0].text
```

### After (Unified LLM Client)

```python
# In agent context
response = await self.llm_complete(
    messages=[Message.user("Hello")],
    task_description="Greeting",
    execution_mode="fast"
)

# response is already the string content
```

## Testing

### Unit Tests

```python
import pytest
from llm.unified_llm_client import UnifiedLLMClient, LLMRequest, ExecutionMode
from llm.base import Message

@pytest.mark.asyncio
async def test_unified_client_classification():
    client = UnifiedLLMClient()

    request = LLMRequest(
        messages=[Message.user("Explain recursion")],
        task_description="Explain programming concept",
        execution_mode=ExecutionMode.BALANCED
    )

    response = await client.complete(request)

    assert response.task_classification is not None
    assert response.task_classification.task_category.value in ["reasoning", "qa", "code"]
    assert response.provider_used is not None
    assert len(response.content) > 0
```

## Troubleshooting

### Issue: Classification Taking Too Long

**Solution**: Ensure Groq API key is configured. Falls back to slower methods without it.

```bash
export GROQ_API_KEY=gsk_...
```

### Issue: All Providers Failing

**Solution**: Check API keys and circuit breaker status:

```python
router = await client._get_router()
status = router.circuit_breaker.get_status()
print(status)
# Shows which providers are in OPEN state
```

### Issue: Wrong Provider Selected

**Solution**: Override with `preferred_provider`:

```python
request = LLMRequest(
    messages=messages,
    preferred_provider=ModelProvider.ANTHROPIC,  # Force Claude
    execution_mode=ExecutionMode.FAST
)
```

## Advanced: Custom Technique Application

```python
from llm.task_classifier import PromptTechnique

response = await self.llm_complete(
    messages=messages,
    force_technique=PromptTechnique.TREE_OF_THOUGHTS,  # Override auto-selection
    skip_classification=True  # Skip classification for speed
)
```

## Performance

- Task classification: 50-100ms (Groq)
- Provider routing: <1ms
- Total overhead: ~100ms
- Caching: First call slow, subsequent <1ms

## Future Enhancements

- [ ] Streaming support
- [ ] Multi-turn conversation optimization
- [ ] Provider cost tracking per agent
- [ ] A/B testing infrastructure
- [ ] Technique performance analytics
- [ ] Custom provider preferences per user

## Support

For issues or questions:
- GitHub Issues: [DevSkyy Repository]
- Email: support@skyyrose.com
- Documentation: `/docs/MCP_ARCHITECTURE.md`

---

**Version**: 1.0.0
**Last Updated**: 2026-01-05
