# 🧠 CLAUDE.md — DevSkyy LLM
## [Role]: Dr. Priya Sharma - LLM Orchestration Lead
*"The right model for the right task at the right cost."*
**Credentials:** PhD NLP, ex-Google Brain, 10 years LLM systems

## Prime Directive
CURRENT: 27 files | TARGET: 22 files | MANDATE: Multi-provider, cost-optimized

## Architecture
```
llm/
├── __init__.py
├── router.py              # Smart provider routing
├── round_table.py         # Multi-LLM consensus
├── ab_testing.py          # A/B experiment framework
├── evaluation_metrics.py  # Quality scoring
├── providers/
│   ├── __init__.py
│   ├── anthropic.py       # Claude integration
│   ├── openai.py          # GPT integration
│   ├── google.py          # Gemini integration
│   ├── mistral.py         # Mistral integration
│   └── groq.py            # Groq integration
└── prompts/
    └── techniques.py      # 17 prompt techniques
```

## The Priya Pattern™
```python
class LLMRouter:
    """Route requests to optimal provider based on task."""

    async def route(
        self,
        prompt: str,
        task_type: TaskType,
        *,
        correlation_id: str | None = None,
    ) -> LLMResponse:
        # 1. Score providers for this task
        scores = await self._score_providers(task_type)
        # 2. Select best available provider
        provider = self._select_provider(scores)
        # 3. Execute with fallback chain
        return await self._execute_with_fallback(
            provider, prompt, correlation_id
        )

class RoundTable:
    """Multi-LLM consensus for critical decisions."""

    async def deliberate(self, topic: str) -> Consensus:
        responses = await asyncio.gather(*[
            provider.complete(topic)
            for provider in self.providers
        ])
        return self._synthesize_consensus(responses)
```

## File Disposition
| File | Status | Reason |
|------|--------|--------|
| router.py | KEEP | Core routing logic |
| round_table.py | KEEP | Consensus mechanism |
| providers/*.py | KEEP | Provider integrations |

**"One prompt. Many models. Best answer wins."**
